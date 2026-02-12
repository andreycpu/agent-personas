"""
Persona Templates and Archetypes Module

Provides pre-defined persona templates and archetype systems for rapid persona creation.
"""

from .archetype import ArchetypeManager, Archetype
from .template import PersonaTemplate, TemplateManager
from .presets import PRESET_ARCHETYPES, PRESET_TEMPLATES
from .builder import PersonaBuilder

__all__ = [
    "ArchetypeManager",
    "Archetype", 
    "PersonaTemplate",
    "TemplateManager",
    "PRESET_ARCHETYPES",
    "PRESET_TEMPLATES",
    "PersonaBuilder"
]