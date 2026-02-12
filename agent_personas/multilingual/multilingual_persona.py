"""
Multilingual persona support with culture-aware adaptations.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from copy import deepcopy

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class LanguageFormality(Enum):
    """Formality levels across languages."""
    VERY_INFORMAL = 1
    INFORMAL = 2
    NEUTRAL = 3
    FORMAL = 4
    VERY_FORMAL = 5


class CommunicationContext(Enum):
    """Communication contexts that affect language use."""
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    CASUAL = "casual"
    CEREMONIAL = "ceremonial"
    TECHNICAL = "technical"


@dataclass
class LanguageProfile:
    """
    Language-specific profile for a persona.
    
    Contains language-specific traits, communication patterns,
    and cultural adaptations.
    """
    language_code: str  # ISO 639-1 code (e.g., 'en', 'es', 'zh')
    language_name: str  # Human-readable name
    proficiency_level: float  # 0.0-1.0, fluency level
    
    # Language-specific traits (may differ from base persona)
    language_traits: Dict[str, float] = field(default_factory=dict)
    
    # Communication patterns
    formality_preference: LanguageFormality = LanguageFormality.NEUTRAL
    directness_level: float = 0.5  # 0.0 = very indirect, 1.0 = very direct
    emotional_expressiveness: float = 0.5  # How emotionally expressive in this language
    humor_usage: float = 0.3  # Tendency to use humor
    
    # Cultural adaptations
    cultural_context_sensitivity: float = 0.7  # Adaptation to cultural contexts
    honorific_usage: bool = False  # Use of honorifics/formal titles
    relationship_hierarchy_awareness: float = 0.5  # Awareness of social hierarchies
    
    # Language-specific conversation elements
    greeting_styles: List[str] = field(default_factory=list)
    farewell_styles: List[str] = field(default_factory=list)
    politeness_markers: List[str] = field(default_factory=list)
    cultural_references: List[str] = field(default_factory=list)
    
    # Response patterns per context
    context_adaptations: Dict[CommunicationContext, Dict[str, Any]] = field(default_factory=dict)
    
    # Metadata
    region_code: Optional[str] = None  # ISO 3166-1 code for region
    dialect: Optional[str] = None
    translation_notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate language profile."""
        if not 0.0 <= self.proficiency_level <= 1.0:
            raise ValueError("Proficiency level must be between 0.0 and 1.0")
        if not 0.0 <= self.directness_level <= 1.0:
            raise ValueError("Directness level must be between 0.0 and 1.0")
        if not 0.0 <= self.emotional_expressiveness <= 1.0:
            raise ValueError("Emotional expressiveness must be between 0.0 and 1.0")


class MultilingualPersona:
    """
    Persona with multilingual support and cultural adaptations.
    
    Extends the base persona concept to support multiple languages
    with culture-aware trait adjustments and communication patterns.
    """
    
    def __init__(
        self,
        base_persona: Persona,
        primary_language: str = "en"
    ):
        self.base_persona = base_persona
        self.primary_language = primary_language
        self.language_profiles: Dict[str, LanguageProfile] = {}
        self.active_language = primary_language
        self.cultural_adaptations: Dict[str, Any] = {}
        self.translation_mappings: Dict[str, Dict[str, str]] = {}  # lang -> {original: translation}
        self.logger = logging.getLogger(__name__)
        
        # Initialize with primary language profile
        self._initialize_primary_language_profile()
        
        # Cultural dimension mappings for different cultures
        self._initialize_cultural_mappings()
    
    def _initialize_primary_language_profile(self):
        """Initialize the primary language profile from base persona."""
        primary_profile = LanguageProfile(
            language_code=self.primary_language,
            language_name=self._get_language_name(self.primary_language),
            proficiency_level=1.0,
            language_traits=self.base_persona.traits.copy()
        )
        
        # Set default communication patterns based on persona traits
        primary_profile.formality_preference = self._determine_formality_preference()
        primary_profile.directness_level = self.base_persona.get_trait("direct") or 0.5
        primary_profile.emotional_expressiveness = self.base_persona.get_trait("expressive") or 0.5
        
        self.language_profiles[self.primary_language] = primary_profile
    
    def _initialize_cultural_mappings(self):
        """Initialize cultural adaptation mappings."""
        self.cultural_adaptations = {
            # High-context cultures (indirect communication)
            "high_context": {
                "cultures": ["ja", "zh", "ko", "ar", "th"],
                "adaptations": {
                    "directness_level": -0.3,
                    "formality_preference": 1,  # More formal
                    "relationship_hierarchy_awareness": 0.3
                }
            },
            
            # Low-context cultures (direct communication)
            "low_context": {
                "cultures": ["de", "nl", "fi", "no"],
                "adaptations": {
                    "directness_level": 0.2,
                    "formality_preference": 0,  # Less formal
                    "emotional_expressiveness": -0.1
                }
            },
            
            # Individualistic cultures
            "individualistic": {
                "cultures": ["en", "de", "fr", "au", "ca"],
                "adaptations": {
                    "assertiveness": 0.2,
                    "independence": 0.3,
                    "personal_achievement_focus": 0.2
                }
            },
            
            # Collectivistic cultures
            "collectivistic": {
                "cultures": ["ja", "zh", "kr", "th", "ph"],
                "adaptations": {
                    "group_harmony": 0.3,
                    "consensus_seeking": 0.2,
                    "relationship_hierarchy_awareness": 0.3
                }
            },
            
            # Romance languages (typically more emotionally expressive)
            "romance_expressive": {
                "cultures": ["es", "it", "pt", "fr", "ro"],
                "adaptations": {
                    "emotional_expressiveness": 0.2,
                    "warmth": 0.2,
                    "humor_usage": 0.1
                }
            }
        }
    
    def add_language_profile(
        self,
        language_code: str,
        proficiency_level: float = 0.7,
        cultural_adaptation: bool = True,
        custom_traits: Optional[Dict[str, float]] = None
    ) -> LanguageProfile:
        """
        Add a new language profile with optional cultural adaptations.
        
        Args:
            language_code: ISO 639-1 language code
            proficiency_level: Fluency level (0.0-1.0)
            cultural_adaptation: Whether to apply cultural adaptations
            custom_traits: Custom trait overrides for this language
            
        Returns:
            The created language profile
        """
        if language_code in self.language_profiles:
            self.logger.warning(f"Language profile for {language_code} already exists")
            return self.language_profiles[language_code]
        
        # Start with base persona traits
        language_traits = self.base_persona.traits.copy()
        
        # Apply cultural adaptations
        if cultural_adaptation:
            language_traits = self._apply_cultural_adaptations(language_traits, language_code)
        
        # Apply custom trait overrides
        if custom_traits:
            language_traits.update(custom_traits)
        
        # Create language profile
        profile = LanguageProfile(
            language_code=language_code,
            language_name=self._get_language_name(language_code),
            proficiency_level=proficiency_level,
            language_traits=language_traits
        )
        
        # Set culture-specific communication patterns
        self._set_cultural_communication_patterns(profile, language_code)
        
        self.language_profiles[language_code] = profile
        
        self.logger.info(f"Added language profile for {language_code}")
        return profile
    
    def _apply_cultural_adaptations(
        self,
        base_traits: Dict[str, float],
        language_code: str
    ) -> Dict[str, float]:
        """Apply cultural adaptations to traits based on language/culture."""
        adapted_traits = base_traits.copy()
        
        # Apply adaptations from cultural mappings
        for adaptation_type, config in self.cultural_adaptations.items():
            if language_code in config["cultures"]:
                adaptations = config["adaptations"]
                
                for trait, adjustment in adaptations.items():
                    current_value = adapted_traits.get(trait, 0.5)
                    
                    if isinstance(adjustment, (int, float)):
                        # Numeric adjustment
                        new_value = max(0.0, min(1.0, current_value + adjustment))
                        adapted_traits[trait] = new_value
                    else:
                        # Direct assignment
                        adapted_traits[trait] = adjustment
                
                self.logger.debug(f"Applied {adaptation_type} adaptations for {language_code}")
        
        return adapted_traits
    
    def _set_cultural_communication_patterns(
        self,
        profile: LanguageProfile,
        language_code: str
    ):
        """Set culture-specific communication patterns."""
        
        # Language-specific defaults
        patterns = {
            "ja": {  # Japanese
                "formality_preference": LanguageFormality.FORMAL,
                "honorific_usage": True,
                "relationship_hierarchy_awareness": 0.9,
                "directness_level": 0.2,
                "greeting_styles": ["こんにちは", "おはようございます", "失礼いたします"],
                "politeness_markers": ["です", "ます", "でございます"]
            },
            
            "de": {  # German
                "formality_preference": LanguageFormality.FORMAL,
                "directness_level": 0.8,
                "emotional_expressiveness": 0.4,
                "greeting_styles": ["Guten Tag", "Hallo", "Guten Morgen"],
                "politeness_markers": ["bitte", "danke", "entschuldigung"]
            },
            
            "es": {  # Spanish
                "formality_preference": LanguageFormality.NEUTRAL,
                "emotional_expressiveness": 0.7,
                "humor_usage": 0.6,
                "directness_level": 0.6,
                "greeting_styles": ["Hola", "Buenos días", "¿Cómo está?"],
                "cultural_references": ["familia", "comunidad", "respeto"]
            },
            
            "fr": {  # French
                "formality_preference": LanguageFormality.FORMAL,
                "directness_level": 0.4,
                "emotional_expressiveness": 0.6,
                "greeting_styles": ["Bonjour", "Bonsoir", "Salut"],
                "politeness_markers": ["s'il vous plaît", "merci", "excusez-moi"]
            },
            
            "zh": {  # Chinese
                "formality_preference": LanguageFormality.FORMAL,
                "relationship_hierarchy_awareness": 0.8,
                "directness_level": 0.3,
                "honorific_usage": True,
                "greeting_styles": ["你好", "您好", "早上好"],
                "cultural_references": ["和谐", "面子", "关系"]
            },
            
            "ar": {  # Arabic
                "formality_preference": LanguageFormality.FORMAL,
                "relationship_hierarchy_awareness": 0.8,
                "cultural_context_sensitivity": 0.9,
                "directness_level": 0.4,
                "greeting_styles": ["السلام عليكم", "أهلا وسهلا", "مرحبا"],
                "honorific_usage": True
            }
        }
        
        # Apply language-specific patterns
        if language_code in patterns:
            lang_patterns = patterns[language_code]
            
            for attr, value in lang_patterns.items():
                if hasattr(profile, attr):
                    setattr(profile, attr, value)
    
    def switch_language(self, language_code: str) -> bool:
        """
        Switch to a different language profile.
        
        Args:
            language_code: Target language code
            
        Returns:
            True if switch successful, False otherwise
        """
        if language_code not in self.language_profiles:
            self.logger.warning(f"Language profile for {language_code} not found")
            return False
        
        self.active_language = language_code
        self.logger.info(f"Switched to language: {language_code}")
        return True
    
    def get_active_persona(self) -> Persona:
        """
        Get a persona instance adapted for the current active language.
        
        Returns:
            Persona adapted for active language
        """
        active_profile = self.language_profiles.get(self.active_language)
        if not active_profile:
            self.logger.warning(f"No profile for active language {self.active_language}")
            return self.base_persona
        
        # Create adapted persona
        adapted_persona = Persona(
            name=f"{self.base_persona.name}_{self.active_language}",
            description=self._get_localized_description(),
            traits=active_profile.language_traits.copy(),
            conversation_style=self._adapt_conversation_style(),
            emotional_baseline=self.base_persona.emotional_baseline,
            metadata={
                **self.base_persona.metadata,
                "language": self.active_language,
                "language_profile": active_profile.language_code,
                "is_multilingual": True
            }
        )
        
        return adapted_persona
    
    def get_trait_in_language(self, trait_name: str, language_code: Optional[str] = None) -> float:
        """Get trait value for specific language (or active language)."""
        lang_code = language_code or self.active_language
        profile = self.language_profiles.get(lang_code)
        
        if profile:
            return profile.language_traits.get(trait_name, 0.0)
        else:
            return self.base_persona.get_trait(trait_name)
    
    def set_trait_in_language(
        self,
        trait_name: str,
        value: float,
        language_code: Optional[str] = None
    ) -> bool:
        """Set trait value for specific language (or active language)."""
        lang_code = language_code or self.active_language
        profile = self.language_profiles.get(lang_code)
        
        if profile:
            profile.language_traits[trait_name] = value
            return True
        else:
            self.logger.warning(f"No profile found for language {lang_code}")
            return False
    
    def compare_traits_across_languages(self, trait_name: str) -> Dict[str, float]:
        """Compare a trait across all language profiles."""
        comparison = {}
        
        for lang_code, profile in self.language_profiles.items():
            comparison[lang_code] = profile.language_traits.get(trait_name, 0.0)
        
        return comparison
    
    def get_cultural_adaptation_score(self, language_code: str) -> float:
        """Calculate how well adapted the persona is to a specific culture."""
        if language_code not in self.language_profiles:
            return 0.0
        
        profile = self.language_profiles[language_code]
        
        # Calculate adaptation based on various factors
        factors = []
        
        # Proficiency factor
        factors.append(profile.proficiency_level)
        
        # Cultural sensitivity factor
        factors.append(profile.cultural_context_sensitivity)
        
        # Appropriate formality for culture
        expected_formality = self._get_expected_formality(language_code)
        formality_match = 1.0 - abs(profile.formality_preference.value - expected_formality) / 4
        factors.append(formality_match)
        
        # Communication style appropriateness
        expected_directness = self._get_expected_directness(language_code)
        directness_match = 1.0 - abs(profile.directness_level - expected_directness)
        factors.append(directness_match)
        
        return sum(factors) / len(factors)
    
    def _get_localized_description(self) -> str:
        """Get description adapted for active language."""
        # This would ideally use proper translation
        # For now, return base description with language note
        base_desc = self.base_persona.description
        
        if self.active_language != self.primary_language:
            return f"{base_desc} (Adapted for {self.active_language} culture)"
        
        return base_desc
    
    def _adapt_conversation_style(self) -> str:
        """Adapt conversation style for active language."""
        base_style = self.base_persona.conversation_style
        active_profile = self.language_profiles.get(self.active_language)
        
        if not active_profile:
            return base_style
        
        # Map formality preference to style
        formality_style_map = {
            LanguageFormality.VERY_INFORMAL: "very_casual",
            LanguageFormality.INFORMAL: "casual",
            LanguageFormality.NEUTRAL: "neutral",
            LanguageFormality.FORMAL: "formal",
            LanguageFormality.VERY_FORMAL: "very_formal"
        }
        
        adapted_style = formality_style_map.get(
            active_profile.formality_preference,
            base_style
        )
        
        # Add cultural markers
        if active_profile.cultural_context_sensitivity > 0.7:
            adapted_style += "_culturally_aware"
        
        return adapted_style
    
    def _get_language_name(self, language_code: str) -> str:
        """Get human-readable language name from code."""
        language_names = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "th": "Thai",
            "vi": "Vietnamese",
            "tr": "Turkish",
            "pl": "Polish",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish"
        }
        
        return language_names.get(language_code, language_code.upper())
    
    def _determine_formality_preference(self) -> LanguageFormality:
        """Determine formality preference from base persona traits."""
        formal_score = (
            self.base_persona.get_trait("professional") +
            self.base_persona.get_trait("formal") +
            self.base_persona.get_trait("polite")
        ) / 3
        
        if formal_score >= 0.8:
            return LanguageFormality.VERY_FORMAL
        elif formal_score >= 0.6:
            return LanguageFormality.FORMAL
        elif formal_score >= 0.4:
            return LanguageFormality.NEUTRAL
        elif formal_score >= 0.2:
            return LanguageFormality.INFORMAL
        else:
            return LanguageFormality.VERY_INFORMAL
    
    def _get_expected_formality(self, language_code: str) -> int:
        """Get expected formality level for a language/culture."""
        high_formality = ["ja", "ko", "de", "fr", "ar"]
        medium_formality = ["en", "es", "it", "pt", "zh"]
        low_formality = ["nl", "sv", "no", "da"]
        
        if language_code in high_formality:
            return 4  # Formal
        elif language_code in medium_formality:
            return 3  # Neutral
        else:
            return 2  # Informal
    
    def _get_expected_directness(self, language_code: str) -> float:
        """Get expected directness level for a language/culture."""
        high_directness = ["de", "nl", "fi", "no"]  # Germanic cultures
        medium_directness = ["en", "fr", "es", "it"]
        low_directness = ["ja", "ko", "zh", "ar", "th"]  # High-context cultures
        
        if language_code in high_directness:
            return 0.8
        elif language_code in medium_directness:
            return 0.5
        else:
            return 0.3
    
    def get_language_statistics(self) -> Dict[str, Any]:
        """Get statistics about the multilingual persona."""
        total_languages = len(self.language_profiles)
        
        # Proficiency distribution
        proficiency_levels = [p.proficiency_level for p in self.language_profiles.values()]
        avg_proficiency = sum(proficiency_levels) / len(proficiency_levels) if proficiency_levels else 0
        
        # Cultural adaptation scores
        adaptation_scores = {}
        for lang_code in self.language_profiles:
            adaptation_scores[lang_code] = self.get_cultural_adaptation_score(lang_code)
        
        # Language families represented
        language_families = {
            "Romance": ["es", "fr", "it", "pt", "ro"],
            "Germanic": ["en", "de", "nl", "sv", "no", "da"],
            "Sino-Tibetan": ["zh"],
            "Japonic": ["ja"],
            "Koreanic": ["ko"],
            "Semitic": ["ar"],
            "Indo-Iranian": ["hi"],
            "Tai-Kadai": ["th"]
        }
        
        represented_families = set()
        for lang_code in self.language_profiles:
            for family, languages in language_families.items():
                if lang_code in languages:
                    represented_families.add(family)
        
        return {
            "total_languages": total_languages,
            "primary_language": self.primary_language,
            "active_language": self.active_language,
            "average_proficiency": round(avg_proficiency, 3),
            "supported_languages": list(self.language_profiles.keys()),
            "cultural_adaptation_scores": {k: round(v, 3) for k, v in adaptation_scores.items()},
            "language_families": list(represented_families),
            "total_language_families": len(represented_families)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert multilingual persona to dictionary representation."""
        return {
            "base_persona": self.base_persona.to_dict(),
            "primary_language": self.primary_language,
            "active_language": self.active_language,
            "language_profiles": {
                lang_code: {
                    "language_code": profile.language_code,
                    "language_name": profile.language_name,
                    "proficiency_level": profile.proficiency_level,
                    "language_traits": profile.language_traits,
                    "formality_preference": profile.formality_preference.value,
                    "directness_level": profile.directness_level,
                    "emotional_expressiveness": profile.emotional_expressiveness,
                    "humor_usage": profile.humor_usage,
                    "cultural_context_sensitivity": profile.cultural_context_sensitivity,
                    "honorific_usage": profile.honorific_usage,
                    "relationship_hierarchy_awareness": profile.relationship_hierarchy_awareness,
                    "greeting_styles": profile.greeting_styles,
                    "farewell_styles": profile.farewell_styles,
                    "politeness_markers": profile.politeness_markers,
                    "cultural_references": profile.cultural_references,
                    "region_code": profile.region_code,
                    "dialect": profile.dialect,
                    "translation_notes": profile.translation_notes
                }
                for lang_code, profile in self.language_profiles.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultilingualPersona":
        """Create multilingual persona from dictionary representation."""
        base_persona = Persona.from_dict(data["base_persona"])
        
        multilingual_persona = cls(
            base_persona=base_persona,
            primary_language=data.get("primary_language", "en")
        )
        
        # Load language profiles
        for lang_code, profile_data in data.get("language_profiles", {}).items():
            profile = LanguageProfile(
                language_code=profile_data["language_code"],
                language_name=profile_data["language_name"],
                proficiency_level=profile_data["proficiency_level"],
                language_traits=profile_data["language_traits"],
                formality_preference=LanguageFormality(profile_data["formality_preference"]),
                directness_level=profile_data["directness_level"],
                emotional_expressiveness=profile_data["emotional_expressiveness"],
                humor_usage=profile_data.get("humor_usage", 0.3),
                cultural_context_sensitivity=profile_data.get("cultural_context_sensitivity", 0.7),
                honorific_usage=profile_data.get("honorific_usage", False),
                relationship_hierarchy_awareness=profile_data.get("relationship_hierarchy_awareness", 0.5),
                greeting_styles=profile_data.get("greeting_styles", []),
                farewell_styles=profile_data.get("farewell_styles", []),
                politeness_markers=profile_data.get("politeness_markers", []),
                cultural_references=profile_data.get("cultural_references", []),
                region_code=profile_data.get("region_code"),
                dialect=profile_data.get("dialect"),
                translation_notes=profile_data.get("translation_notes", [])
            )
            
            multilingual_persona.language_profiles[lang_code] = profile
        
        # Set active language
        multilingual_persona.active_language = data.get("active_language", multilingual_persona.primary_language)
        
        return multilingual_persona