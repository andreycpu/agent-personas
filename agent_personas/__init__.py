"""
Agent Personas Framework

A comprehensive framework for defining and managing AI agent personalities and behaviors.
"""

__version__ = "0.1.0"
__author__ = "Agent Personas Contributors"
__email__ = "contact@example.com"

from .core.persona import Persona
from .core.manager import PersonaManager
from .core.registry import PersonaRegistry

__all__ = [
    "Persona",
    "PersonaManager", 
    "PersonaRegistry",
    "__version__"
]