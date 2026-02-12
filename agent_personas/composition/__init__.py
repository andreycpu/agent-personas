"""
Persona Composition Module

Advanced system for blending, merging, and creating composite personas
from multiple source personas with sophisticated mixing algorithms.
"""

from .blender import PersonaBlender, BlendStrategy
from .compositor import PersonaCompositor, CompositionRule
from .merger import PersonaMerger, MergeStrategy
from .analyzer import PersonaCompatibilityAnalyzer

__all__ = [
    "PersonaBlender",
    "BlendStrategy", 
    "PersonaCompositor",
    "CompositionRule",
    "PersonaMerger",
    "MergeStrategy",
    "PersonaCompatibilityAnalyzer"
]