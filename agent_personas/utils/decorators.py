"""
Utility decorators for agent_personas package.
"""

import functools
import time
import signal
import logging
from typing import Any, Callable, Dict, Optional
from ..exceptions import PersonaError

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempts}/{max_attempts}): {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


def timeout(seconds: int):
    """Timeout decorator."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Reset the alarm and handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        return wrapper
    return decorator


def validate_input(**validations):
    """Input validation decorator."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get function signature for parameter mapping
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name, validator in validations.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise PersonaError(f"Validation failed for parameter {param_name}: {value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_execution_time(logger_name: Optional[str] = None):
    """Log execution time decorator."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            log = logging.getLogger(logger_name) if logger_name else logger
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                log.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log.error(f"Function {func.__name__} failed after {execution_time:.4f} seconds: {e}")
                raise
        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """Simple result caching decorator with TTL."""
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Dict[str, Any]] = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if cache_key in cache:
                cached_data = cache[cache_key]
                if current_time - cached_data['timestamp'] < ttl:
                    logger.debug(f"Returning cached result for {func.__name__}")
                    return cached_data['result']
                else:
                    # Remove expired cache entry
                    del cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = {
                'result': result,
                'timestamp': current_time
            }
            
            return result
        return wrapper
    return decorator