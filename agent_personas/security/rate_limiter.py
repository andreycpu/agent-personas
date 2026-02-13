"""
Rate limiting utilities for API protection.
"""

import time
import threading
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from ..exceptions import PersonaError


@dataclass
class RateLimitInfo:
    """Information about rate limit status."""
    limit: int
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens were available and consumed
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
    
    def get_info(self) -> RateLimitInfo:
        """Get current rate limit information."""
        with self._lock:
            self._refill()
            return RateLimitInfo(
                limit=self.capacity,
                remaining=int(self.tokens),
                reset_time=time.time() + ((self.capacity - self.tokens) / self.refill_rate)
            )


class SlidingWindowRateLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self, limit: int, window_seconds: int):
        """
        Initialize sliding window rate limiter.
        
        Args:
            limit: Maximum requests per window
            window_seconds: Size of sliding window in seconds
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        with self._lock:
            # Remove old requests outside window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()
            
            # Check if we're under the limit
            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True
            
            return False
    
    def get_info(self) -> RateLimitInfo:
        """Get current rate limit information."""
        now = time.time()
        
        with self._lock:
            # Clean old requests
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()
            
            remaining = max(0, self.limit - len(self.requests))
            
            # Calculate when the oldest request will expire
            reset_time = now
            if self.requests and remaining == 0:
                reset_time = self.requests[0] + self.window_seconds
            
            return RateLimitInfo(
                limit=self.limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=max(0, reset_time - now) if remaining == 0 else None
            )


class RateLimiter:
    """Multi-key rate limiter with different strategies."""
    
    def __init__(
        self,
        strategy: str = 'token_bucket',
        default_limit: int = 100,
        default_window: int = 3600,  # 1 hour
        refill_rate: Optional[float] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            strategy: Rate limiting strategy ('token_bucket' or 'sliding_window')
            default_limit: Default rate limit
            default_window: Default time window in seconds
            refill_rate: Token refill rate (for token bucket only)
        """
        self.strategy = strategy
        self.default_limit = default_limit
        self.default_window = default_window
        self.refill_rate = refill_rate or (default_limit / default_window)
        
        self.limiters: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def _get_limiter(self, key: str, limit: Optional[int] = None, window: Optional[int] = None):
        """Get or create rate limiter for key."""
        limit = limit or self.default_limit
        window = window or self.default_window
        
        limiter_key = f"{key}:{limit}:{window}"
        
        if limiter_key not in self.limiters:
            if self.strategy == 'token_bucket':
                self.limiters[limiter_key] = TokenBucket(limit, self.refill_rate)
            elif self.strategy == 'sliding_window':
                self.limiters[limiter_key] = SlidingWindowRateLimiter(limit, window)
            else:
                raise PersonaError(f"Unknown rate limiting strategy: {self.strategy}")
        
        return self.limiters[limiter_key]
    
    def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        tokens: int = 1
    ) -> bool:
        """
        Check if request is allowed for key.
        
        Args:
            key: Unique identifier for rate limit tracking
            limit: Custom rate limit
            window: Custom time window
            tokens: Number of tokens to consume (token bucket only)
        
        Returns:
            True if request is allowed
        """
        with self._lock:
            limiter = self._get_limiter(key, limit, window)
            
            if self.strategy == 'token_bucket':
                return limiter.consume(tokens)
            else:
                return limiter.is_allowed()
    
    def get_info(self, key: str, limit: Optional[int] = None, window: Optional[int] = None) -> RateLimitInfo:
        """Get rate limit information for key."""
        with self._lock:
            limiter = self._get_limiter(key, limit, window)
            return limiter.get_info()
    
    def reset(self, key: str):
        """Reset rate limiter for key."""
        with self._lock:
            # Remove all limiters for this key
            keys_to_remove = [k for k in self.limiters.keys() if k.startswith(f"{key}:")]
            for k in keys_to_remove:
                del self.limiters[k]
    
    def cleanup(self, max_age: int = 3600):
        """Clean up old unused limiters."""
        now = time.time()
        
        with self._lock:
            keys_to_remove = []
            
            for key, limiter in self.limiters.items():
                if hasattr(limiter, 'last_refill'):
                    # Token bucket
                    if now - limiter.last_refill > max_age:
                        keys_to_remove.append(key)
                elif hasattr(limiter, 'requests'):
                    # Sliding window
                    if not limiter.requests or now - limiter.requests[-1] > max_age:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.limiters[key]


# Global rate limiter instances
_global_rate_limiter = RateLimiter()
_user_rate_limiter = RateLimiter(strategy='sliding_window', default_limit=1000, default_window=3600)
_api_rate_limiter = RateLimiter(strategy='token_bucket', default_limit=100, default_window=60)


def rate_limit(
    key_func: Optional[Callable] = None,
    limit: int = 100,
    window: int = 3600,
    limiter: Optional[RateLimiter] = None
):
    """
    Decorator for rate limiting function calls.
    
    Args:
        key_func: Function to generate rate limit key from arguments
        limit: Rate limit
        window: Time window in seconds
        limiter: Custom rate limiter instance
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__module__}.{func.__name__}"
            
            # Use provided limiter or global default
            rate_limiter = limiter or _global_rate_limiter
            
            # Check rate limit
            if not rate_limiter.is_allowed(key, limit, window):
                info = rate_limiter.get_info(key, limit, window)
                raise PersonaError(
                    f"Rate limit exceeded for {key}. "
                    f"Limit: {info.limit}, Remaining: {info.remaining}, "
                    f"Reset: {info.reset_time}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_rate_limit(
    key: str,
    limit: int = 100,
    window: int = 3600,
    limiter: Optional[RateLimiter] = None
) -> RateLimitInfo:
    """
    Check rate limit status for a key without consuming.
    
    Args:
        key: Rate limit key
        limit: Rate limit
        window: Time window in seconds
        limiter: Custom rate limiter instance
    
    Returns:
        Rate limit information
    """
    rate_limiter = limiter or _global_rate_limiter
    return rate_limiter.get_info(key, limit, window)


def enforce_user_rate_limit(user_id: str, operation: str = 'general') -> bool:
    """
    Enforce rate limiting for user operations.
    
    Args:
        user_id: User identifier
        operation: Operation type
    
    Returns:
        True if operation is allowed
    
    Raises:
        PersonaError: If rate limit is exceeded
    """
    key = f"user:{user_id}:{operation}"
    
    if not _user_rate_limiter.is_allowed(key):
        info = _user_rate_limiter.get_info(key)
        raise PersonaError(
            f"User rate limit exceeded for {user_id}:{operation}. "
            f"Try again in {info.retry_after:.0f} seconds."
        )
    
    return True


def enforce_api_rate_limit(api_key: str, endpoint: str = 'general') -> bool:
    """
    Enforce rate limiting for API operations.
    
    Args:
        api_key: API key identifier
        endpoint: API endpoint
    
    Returns:
        True if operation is allowed
    
    Raises:
        PersonaError: If rate limit is exceeded
    """
    key = f"api:{api_key}:{endpoint}"
    
    if not _api_rate_limiter.is_allowed(key):
        info = _api_rate_limiter.get_info(key)
        raise PersonaError(
            f"API rate limit exceeded for {api_key}:{endpoint}. "
            f"Limit: {info.limit} requests per minute."
        )