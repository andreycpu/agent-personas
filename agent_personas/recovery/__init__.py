"""
Error recovery and fault tolerance utilities.
"""

from .circuit_breaker import CircuitBreaker, circuit_breaker
from .fallback_handler import FallbackHandler, with_fallback
from .retry_handler import RetryHandler, with_retry, RetryPolicy
from .graceful_degradation import GracefulDegradation, degrade_gracefully
from .state_recovery import StateRecovery, recoverable_state

__all__ = [
    'CircuitBreaker',
    'circuit_breaker',
    'FallbackHandler', 
    'with_fallback',
    'RetryHandler',
    'with_retry',
    'RetryPolicy',
    'GracefulDegradation',
    'degrade_gracefully',
    'StateRecovery',
    'recoverable_state'
]