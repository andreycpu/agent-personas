"""
Circuit breaker pattern implementation for fault tolerance.
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional, Dict, Union
from dataclasses import dataclass
from ..exceptions import PersonaError


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 60.0      # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    timeout: Optional[float] = None     # Request timeout in seconds
    expected_exceptions: tuple = ()     # Exceptions to count as failures


@dataclass
class CircuitMetrics:
    """Circuit breaker metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


class CircuitBreakerError(PersonaError):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, config: Optional[CircuitConfig] = None):
        """Initialize circuit breaker."""
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self._lock = threading.Lock()
        self._last_state_change = time.time()
    
    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self._lock:
            self.metrics.total_requests += 1
            
            # Check if we should attempt the call
            if not self._should_allow_request():
                raise CircuitBreakerError(f"Circuit breaker is {self.state.value}")
            
            # If half-open, limit concurrent requests
            if self.state == CircuitState.HALF_OPEN:
                if self.metrics.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
        
        # Execute the function outside the lock
        try:
            if self.config.timeout:
                result = self._execute_with_timeout(func, *args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Handle success
            with self._lock:
                self._record_success()
            
            return result
            
        except Exception as e:
            # Handle failure
            with self._lock:
                self._record_failure(e)
            raise
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.metrics.last_failure_time:
                if time.time() - self.metrics.last_failure_time >= self.config.recovery_timeout:
                    self._transition_to_half_open()
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests to test recovery
            return True
        
        return False
    
    def _record_success(self):
        """Record successful execution."""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = time.time()
        
        # If half-open and enough successes, close the circuit
        if (self.state == CircuitState.HALF_OPEN and 
            self.metrics.consecutive_successes >= self.config.success_threshold):
            self._transition_to_closed()
    
    def _record_failure(self, exception: Exception):
        """Record failed execution."""
        # Only count certain exceptions as failures if specified
        if (self.config.expected_exceptions and 
            not isinstance(exception, self.config.expected_exceptions)):
            return
        
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = time.time()
        
        # Check if we should open the circuit
        if (self.state == CircuitState.CLOSED and 
            self.metrics.consecutive_failures >= self.config.failure_threshold):
            self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state goes back to open
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition circuit to open state."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.metrics.state_changes += 1
            self._last_state_change = time.time()
    
    def _transition_to_half_open(self):
        """Transition circuit to half-open state."""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.metrics.state_changes += 1
            self.metrics.consecutive_successes = 0
            self.metrics.consecutive_failures = 0
            self._last_state_change = time.time()
    
    def _transition_to_closed(self):
        """Transition circuit to closed state."""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.metrics.state_changes += 1
            self.metrics.consecutive_failures = 0
            self._last_state_change = time.time()
    
    def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Function {func.__name__} timed out after {self.config.timeout} seconds")
        
        # Set timeout signal
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.config.timeout))
        
        try:
            result = func(*args, **kwargs)
        finally:
            # Restore previous signal handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        
        return result
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_metrics(self) -> CircuitMetrics:
        """Get circuit metrics."""
        return self.metrics
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitMetrics()
            self._last_state_change = time.time()
    
    def force_open(self):
        """Force circuit to open state."""
        with self._lock:
            self._transition_to_open()
    
    def force_close(self):
        """Force circuit to closed state."""
        with self._lock:
            self._transition_to_closed()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        return {
            'state': self.state.value,
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'consecutive_failures': self.metrics.consecutive_failures,
                'consecutive_successes': self.metrics.consecutive_successes,
                'state_changes': self.metrics.state_changes,
                'last_failure_time': self.metrics.last_failure_time,
                'last_success_time': self.metrics.last_success_time
            },
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout
            },
            'last_state_change': self._last_state_change,
            'uptime_since_last_change': time.time() - self._last_state_change
        }


# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(name: str, config: Optional[CircuitConfig] = None) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(config)
        return _circuit_breakers[name]


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3,
    timeout: Optional[float] = None,
    expected_exceptions: tuple = ()
):
    """Decorator for adding circuit breaker protection."""
    def decorator(func: Callable) -> Callable:
        circuit_name = name or f"{func.__module__}.{func.__name__}"
        config = CircuitConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exceptions=expected_exceptions
        )
        
        breaker = get_circuit_breaker(circuit_name, config)
        
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Add circuit breaker methods to wrapper
        wrapper.circuit_breaker = breaker
        wrapper.get_circuit_state = breaker.get_state
        wrapper.get_circuit_metrics = breaker.get_metrics
        wrapper.reset_circuit = breaker.reset
        
        return wrapper
    
    return decorator


def get_all_circuits() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    with _registry_lock:
        return _circuit_breakers.copy()


def reset_all_circuits():
    """Reset all circuit breakers."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()


def get_circuits_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers."""
    with _registry_lock:
        return {name: breaker.get_status() for name, breaker in _circuit_breakers.items()}