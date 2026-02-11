"""
Trait system for personality management.
"""

from .trait import Trait
from .trait_group import TraitGroup
from .trait_manager import TraitManager
from .trait_conflicts import TraitConflictResolver

__all__ = ["Trait", "TraitGroup", "TraitManager", "TraitConflictResolver"]