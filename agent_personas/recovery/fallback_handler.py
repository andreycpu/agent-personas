"""
Fallback handling for graceful degradation.
"""

import functools
import logging
from typing import Any, Callable, Optional, Union, Dict, List
from ..exceptions import PersonaError

logger = logging.getLogger(__name__)


class FallbackError(PersonaError):
    """Raised when all fallback options are exhausted."""
    pass


class FallbackHandler:
    """Handles fallback strategies for failed operations."""
    
    def __init__(self, primary_func: Callable):
        """Initialize with primary function."""
        self.primary_func = primary_func
        self.fallbacks: List[Callable] = []
        self.exception_map: Dict[type, List[Callable]] = {}
        self.global_fallback: Optional[Callable] = None
        self.max_attempts: int = 3
        
    def add_fallback(
        self,
        fallback_func: Callable,
        exceptions: Optional[Union[type, tuple]] = None,
        priority: int = 0
    ) -> 'FallbackHandler':
        """
        Add a fallback function.
        
        Args:
            fallback_func: Function to call on failure
            exceptions: Specific exceptions to handle (None for all)
            priority: Priority order (lower = higher priority)
        
        Returns:
            Self for chaining
        """
        if exceptions is None:
            self.fallbacks.append(fallback_func)
        else:
            if not isinstance(exceptions, tuple):
                exceptions = (exceptions,)
            
            for exc_type in exceptions:
                if exc_type not in self.exception_map:
                    self.exception_map[exc_type] = []
                self.exception_map[exc_type].append(fallback_func)
        
        return self
    
    def set_global_fallback(self, fallback_func: Callable) -> 'FallbackHandler':
        """Set a global fallback for when all else fails."""
        self.global_fallback = fallback_func
        return self
    
    def set_max_attempts(self, max_attempts: int) -> 'FallbackHandler':
        """Set maximum number of fallback attempts."""
        self.max_attempts = max_attempts
        return self
    
    def __call__(self, *args, **kwargs) -> Any:
        """Execute primary function with fallback handling."""
        attempts = 0
        last_exception = None
        
        # Try primary function first
        try:
            logger.debug(f"Executing primary function: {self.primary_func.__name__}")
            return self.primary_func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Primary function failed: {e}")
        
        # Try specific exception fallbacks
        for exc_type, fallback_funcs in self.exception_map.items():
            if isinstance(last_exception, exc_type):
                for fallback_func in fallback_funcs:
                    if attempts >= self.max_attempts:
                        break
                    
                    try:
                        attempts += 1
                        logger.info(f"Trying fallback {fallback_func.__name__} for {exc_type.__name__}")
                        return fallback_func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"Fallback {fallback_func.__name__} failed: {e}")
        
        # Try general fallbacks
        for fallback_func in self.fallbacks:
            if attempts >= self.max_attempts:
                break
            
            try:
                attempts += 1
                logger.info(f"Trying general fallback: {fallback_func.__name__}")
                return fallback_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"General fallback {fallback_func.__name__} failed: {e}")
        
        # Try global fallback as last resort
        if self.global_fallback and attempts < self.max_attempts:
            try:
                attempts += 1
                logger.info(f"Trying global fallback: {self.global_fallback.__name__}")
                return self.global_fallback(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.error(f"Global fallback failed: {e}")
        
        # All fallbacks exhausted
        raise FallbackError(
            f"All fallback options exhausted after {attempts} attempts. "
            f"Last error: {last_exception}"
        ) from last_exception
    
    def with_fallback(self, fallback_func: Callable, **kwargs) -> 'FallbackHandler':
        """Fluent interface for adding fallback."""
        return self.add_fallback(fallback_func, **kwargs)


def with_fallback(*fallback_funcs, exceptions=None, max_attempts=3):
    """
    Decorator to add fallback handling to a function.
    
    Args:
        *fallback_funcs: Fallback functions to try
        exceptions: Specific exceptions to handle
        max_attempts: Maximum fallback attempts
    
    Returns:
        Decorated function with fallback handling
    """
    def decorator(primary_func: Callable) -> Callable:
        handler = FallbackHandler(primary_func)
        handler.set_max_attempts(max_attempts)
        
        for fallback_func in fallback_funcs:
            handler.add_fallback(fallback_func, exceptions)
        
        @functools.wraps(primary_func)
        def wrapper(*args, **kwargs):
            return handler(*args, **kwargs)
        
        # Add methods to access handler
        wrapper.fallback_handler = handler
        wrapper.add_fallback = handler.add_fallback
        wrapper.set_global_fallback = handler.set_global_fallback
        
        return wrapper
    
    return decorator


def create_fallback_chain(*functions, max_attempts=None):
    """
    Create a fallback chain from multiple functions.
    
    Args:
        *functions: Functions to try in order
        max_attempts: Maximum attempts (defaults to number of functions)
    
    Returns:
        FallbackHandler instance
    """
    if not functions:
        raise ValueError("At least one function required")
    
    primary = functions[0]
    fallbacks = functions[1:]
    
    handler = FallbackHandler(primary)
    
    if max_attempts is not None:
        handler.set_max_attempts(max_attempts)
    else:
        handler.set_max_attempts(len(functions))
    
    for fallback in fallbacks:
        handler.add_fallback(fallback)
    
    return handler


def safe_fallback(default_value=None):
    """
    Decorator that provides a safe fallback returning a default value.
    
    Args:
        default_value: Value to return on failure
    
    Returns:
        Decorated function that never raises exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Function {func.__name__} failed, returning default: {e}")
                return default_value
        
        return wrapper
    
    return decorator


def conditional_fallback(condition_func: Callable[[Exception], bool]):
    """
    Decorator that applies fallback only when condition is met.
    
    Args:
        condition_func: Function that takes exception and returns bool
    
    Returns:
        Decorator function
    """
    def decorator(fallback_func: Callable):
        def fallback_wrapper(*args, **kwargs):
            def inner(primary_func: Callable):
                @functools.wraps(primary_func)
                def wrapper(*args, **kwargs):
                    try:
                        return primary_func(*args, **kwargs)
                    except Exception as e:
                        if condition_func(e):
                            logger.info(f"Condition met for fallback: {e}")
                            return fallback_func(*args, **kwargs)
                        else:
                            raise
                
                return wrapper
            return inner
        
        return fallback_wrapper
    
    return decorator


# Common fallback strategies

def null_fallback(*args, **kwargs) -> None:
    """Fallback that returns None."""
    return None


def empty_list_fallback(*args, **kwargs) -> list:
    """Fallback that returns empty list."""
    return []


def empty_dict_fallback(*args, **kwargs) -> dict:
    """Fallback that returns empty dictionary."""
    return {}


def zero_fallback(*args, **kwargs) -> int:
    """Fallback that returns zero."""
    return 0


def empty_string_fallback(*args, **kwargs) -> str:
    """Fallback that returns empty string."""
    return ""


def cached_result_fallback(cache_key: str, cache_store: dict):
    """
    Create a fallback that returns cached results.
    
    Args:
        cache_key: Key for cached result
        cache_store: Dictionary to use as cache
    
    Returns:
        Fallback function
    """
    def fallback(*args, **kwargs):
        if cache_key in cache_store:
            logger.info(f"Returning cached result for {cache_key}")
            return cache_store[cache_key]
        else:
            raise FallbackError(f"No cached result available for {cache_key}")
    
    return fallback


def log_and_reraise_fallback(message: str = "Fallback failed"):
    """
    Create a fallback that logs and re-raises the exception.
    
    Args:
        message: Log message
    
    Returns:
        Fallback function that always fails
    """
    def fallback(*args, **kwargs):
        logger.error(message)
        raise FallbackError(message)
    
    return fallback


def notification_fallback(notify_func: Callable, default_value=None):
    """
    Create a fallback that sends notifications and returns default.
    
    Args:
        notify_func: Function to call for notifications
        default_value: Value to return after notification
    
    Returns:
        Fallback function
    """
    def fallback(*args, **kwargs):
        try:
            notify_func(f"Fallback activated for operation with args: {args[:2]}...")
        except Exception as e:
            logger.error(f"Notification failed: {e}")
        
        return default_value
    
    return fallback


# Example usage and patterns

def create_persona_fallback_chain():
    """Example: Create a fallback chain for persona operations."""
    
    def primary_persona_load(persona_id: str):
        # Primary method - load from database
        raise NotImplementedError("Database loading")
    
    def cache_persona_load(persona_id: str):
        # Fallback - load from cache
        raise NotImplementedError("Cache loading")
    
    def default_persona_load(persona_id: str):
        # Last resort - return default persona
        return {
            "name": "Default Assistant",
            "traits": {"communication_style": "neutral"},
            "knowledge_areas": ["general"]
        }
    
    return create_fallback_chain(
        primary_persona_load,
        cache_persona_load,
        default_persona_load
    )