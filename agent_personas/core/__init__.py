"""
Core persona functionality.
"""

from .persona import Persona
from .manager import PersonaManager
from .registry import PersonaRegistry

__all__ = ["Persona", "PersonaManager", "PersonaRegistry"]