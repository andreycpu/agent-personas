"""
Multilingual Persona Support Module

Comprehensive multilingual support for personas including 
culture-aware personality adaptation and cross-language consistency.
"""

from .multilingual_persona import MultilingualPersona, LanguageProfile
from .cultural_adapter import CulturalAdapter, CulturalDimension
from .translation_manager import TranslationManager, TranslationQuality
from .cross_language_consistency import CrossLanguageConsistencyChecker
from .locale_manager import LocaleManager, LocaleData

__all__ = [
    "MultilingualPersona",
    "LanguageProfile",
    "CulturalAdapter",
    "CulturalDimension",
    "TranslationManager", 
    "TranslationQuality",
    "CrossLanguageConsistencyChecker",
    "LocaleManager",
    "LocaleData"
]