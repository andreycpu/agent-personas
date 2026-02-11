"""
Persona switching system for seamless personality transitions.
"""

from .switch_manager import SwitchManager, SwitchContext
from .transition_engine import TransitionEngine, TransitionTrigger
from .context_preservation import ContextPreservationManager
from .switching_policies import SwitchingPolicyManager

__all__ = [
    "SwitchManager",
    "SwitchContext",
    "TransitionEngine", 
    "TransitionTrigger",
    "ContextPreservationManager",
    "SwitchingPolicyManager"
]