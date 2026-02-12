"""
Advanced conversation style adapter with dynamic adaptation capabilities.
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from copy import deepcopy

logger = logging.getLogger(__name__)


class FormalityLevel(Enum):
    """Levels of formality in conversation."""
    VERY_INFORMAL = 0.0
    INFORMAL = 0.25
    NEUTRAL = 0.5
    FORMAL = 0.75
    VERY_FORMAL = 1.0


class ToneType(Enum):
    """Types of conversational tone."""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    AUTHORITATIVE = "authoritative"
    SUPPORTIVE = "supportive"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    EMPATHETIC = "empathetic"
    ANALYTICAL = "analytical"
    ENTHUSIASTIC = "enthusiastic"


class CommunicationStyle(Enum):
    """Communication styles."""
    DIRECT = "direct"
    INDIRECT = "indirect"
    COLLABORATIVE = "collaborative"
    ASSERTIVE = "assertive"
    ACCOMMODATING = "accommodating"
    QUESTIONING = "questioning"
    EXPLAINING = "explaining"


@dataclass
class StyleProfile:
    """
    Defines a complete conversation style profile.
    """
    name: str
    description: str
    formality_level: FormalityLevel
    primary_tone: ToneType
    secondary_tones: List[ToneType] = field(default_factory=list)
    communication_style: CommunicationStyle = CommunicationStyle.COLLABORATIVE
    
    # Language characteristics
    vocabulary_complexity: float = 0.5  # 0.0 = simple, 1.0 = complex
    sentence_length_preference: float = 0.5  # 0.0 = short, 1.0 = long
    use_contractions: bool = True
    use_slang: bool = False
    use_technical_terms: bool = False
    use_metaphors: bool = False
    use_humor: bool = False
    use_questions: bool = True
    
    # Response patterns
    greeting_style: str = "standard"  # standard, warm, casual, formal
    question_handling: str = "direct"  # direct, exploratory, deflecting
    disagreement_style: str = "respectful"  # gentle, direct, respectful, avoiding
    compliment_style: str = "gracious"  # humble, gracious, deflecting
    
    # Emotional characteristics
    emotional_expressiveness: float = 0.5  # 0.0 = reserved, 1.0 = very expressive
    empathy_level: float = 0.7
    enthusiasm_level: float = 0.5
    
    # Context adaptations
    context_sensitivity: float = 0.8  # How much to adapt based on context
    user_mirroring: float = 0.3  # How much to mirror user's style
    consistency_priority: float = 0.7  # How much to maintain consistent style
    
    # Custom adaptations
    custom_patterns: Dict[str, Any] = field(default_factory=dict)
    adaptation_rules: List[Callable] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate style profile parameters."""
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate that all parameters are within acceptable ranges."""
        float_params = [
            "vocabulary_complexity", "sentence_length_preference", 
            "emotional_expressiveness", "empathy_level", "enthusiasm_level",
            "context_sensitivity", "user_mirroring", "consistency_priority"
        ]
        
        for param in float_params:
            value = getattr(self, param)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{param} must be between 0.0 and 1.0, got {value}")
    
    def get_adaptation_strength(self, context: Dict[str, Any]) -> float:
        """Calculate how strongly to adapt based on context."""
        base_adaptation = self.context_sensitivity
        
        # Increase adaptation for mismatched contexts
        context_formality = context.get("formality_level", 0.5)
        style_formality = self.formality_level.value
        formality_mismatch = abs(context_formality - style_formality)
        
        adaptation_boost = formality_mismatch * 0.3
        
        return min(1.0, base_adaptation + adaptation_boost)


class ConversationStyleAdapter:
    """
    Advanced adapter for dynamically adjusting conversation styles based on context.
    
    Provides sophisticated style adaptation including formality adjustment,
    tone modification, and pattern application based on conversation context.
    """
    
    def __init__(self):
        self.style_profiles: Dict[str, StyleProfile] = {}
        self.current_profile: Optional[StyleProfile] = None
        self.adaptation_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize common style profiles
        self._initialize_common_profiles()
        
        # Response transformation functions
        self.transformers = {
            "formality": self._adjust_formality,
            "tone": self._adjust_tone,
            "vocabulary": self._adjust_vocabulary,
            "structure": self._adjust_structure,
            "emotional": self._adjust_emotional_expression
        }
    
    def _initialize_common_profiles(self):
        """Initialize common conversation style profiles."""
        profiles = [
            StyleProfile(
                name="professional",
                description="Professional business communication",
                formality_level=FormalityLevel.FORMAL,
                primary_tone=ToneType.PROFESSIONAL,
                secondary_tones=[ToneType.SERIOUS, ToneType.ANALYTICAL],
                communication_style=CommunicationStyle.DIRECT,
                vocabulary_complexity=0.7,
                sentence_length_preference=0.6,
                use_contractions=False,
                use_technical_terms=True,
                greeting_style="formal",
                question_handling="direct",
                emotional_expressiveness=0.3
            ),
            
            StyleProfile(
                name="friendly_casual",
                description="Warm and approachable casual communication",
                formality_level=FormalityLevel.INFORMAL,
                primary_tone=ToneType.FRIENDLY,
                secondary_tones=[ToneType.CASUAL, ToneType.SUPPORTIVE],
                communication_style=CommunicationStyle.COLLABORATIVE,
                vocabulary_complexity=0.4,
                sentence_length_preference=0.4,
                use_contractions=True,
                use_slang=True,
                use_humor=True,
                greeting_style="warm",
                question_handling="exploratory",
                emotional_expressiveness=0.8
            ),
            
            StyleProfile(
                name="supportive_mentor",
                description="Encouraging and guidance-focused communication",
                formality_level=FormalityLevel.NEUTRAL,
                primary_tone=ToneType.SUPPORTIVE,
                secondary_tones=[ToneType.EMPATHETIC, ToneType.FRIENDLY],
                communication_style=CommunicationStyle.COLLABORATIVE,
                vocabulary_complexity=0.5,
                use_questions=True,
                use_metaphors=True,
                empathy_level=0.9,
                emotional_expressiveness=0.6,
                greeting_style="warm",
                question_handling="exploratory"
            ),
            
            StyleProfile(
                name="technical_expert",
                description="Precise and knowledgeable technical communication",
                formality_level=FormalityLevel.NEUTRAL,
                primary_tone=ToneType.ANALYTICAL,
                secondary_tones=[ToneType.PROFESSIONAL, ToneType.SERIOUS],
                communication_style=CommunicationStyle.EXPLAINING,
                vocabulary_complexity=0.8,
                sentence_length_preference=0.7,
                use_technical_terms=True,
                use_questions=False,
                question_handling="direct",
                emotional_expressiveness=0.2
            ),
            
            StyleProfile(
                name="creative_enthusiastic",
                description="Imaginative and energetic communication",
                formality_level=FormalityLevel.INFORMAL,
                primary_tone=ToneType.ENTHUSIASTIC,
                secondary_tones=[ToneType.PLAYFUL, ToneType.FRIENDLY],
                communication_style=CommunicationStyle.COLLABORATIVE,
                vocabulary_complexity=0.6,
                use_metaphors=True,
                use_humor=True,
                enthusiasm_level=0.9,
                emotional_expressiveness=0.8,
                greeting_style="casual"
            )
        ]
        
        for profile in profiles:
            self.register_profile(profile)
    
    def register_profile(self, profile: StyleProfile) -> None:
        """Register a new style profile."""
        self.style_profiles[profile.name] = profile
        self.logger.debug(f"Registered style profile: {profile.name}")
    
    def set_active_profile(self, profile_name: str) -> bool:
        """Set the active conversation style profile."""
        if profile_name in self.style_profiles:
            self.current_profile = self.style_profiles[profile_name]
            self.logger.info(f"Set active profile: {profile_name}")
            return True
        return False
    
    def adapt_response(
        self,
        response: str,
        context: Dict[str, Any],
        target_profile: Optional[str] = None,
        adaptation_strength: Optional[float] = None
    ) -> str:
        """
        Adapt a response according to the conversation style.
        
        Args:
            response: Original response text
            context: Conversation context
            target_profile: Specific profile to use (overrides current)
            adaptation_strength: Override adaptation strength (0.0-1.0)
            
        Returns:
            Adapted response text
        """
        if target_profile and target_profile in self.style_profiles:
            profile = self.style_profiles[target_profile]
        else:
            profile = self.current_profile
        
        if not profile:
            self.logger.warning("No active profile set, returning original response")
            return response
        
        # Calculate adaptation strength
        if adaptation_strength is None:
            adaptation_strength = profile.get_adaptation_strength(context)
        
        adapted_response = response
        
        # Apply transformations in order
        transformation_order = ["formality", "tone", "vocabulary", "structure", "emotional"]
        
        for transformation in transformation_order:
            transformer = self.transformers.get(transformation)
            if transformer:
                adapted_response = transformer(adapted_response, profile, context, adaptation_strength)
        
        # Record adaptation
        self._record_adaptation(response, adapted_response, profile.name, context, adaptation_strength)
        
        return adapted_response
    
    def _adjust_formality(
        self,
        response: str,
        profile: StyleProfile,
        context: Dict[str, Any],
        strength: float
    ) -> str:
        """Adjust formality level of the response."""
        target_formality = profile.formality_level.value
        
        # Simple formality adjustments
        if target_formality >= 0.75:  # Formal
            # Make more formal
            response = re.sub(r"\bcan't\b", "cannot", response, flags=re.IGNORECASE)
            response = re.sub(r"\bwon't\b", "will not", response, flags=re.IGNORECASE)
            response = re.sub(r"\bdon't\b", "do not", response, flags=re.IGNORECASE)
            response = re.sub(r"\bisn't\b", "is not", response, flags=re.IGNORECASE)
            response = re.sub(r"\blet's\b", "let us", response, flags=re.IGNORECASE)
            
            # Replace casual phrases
            response = re.sub(r"\bkinda\b", "somewhat", response, flags=re.IGNORECASE)
            response = re.sub(r"\bsorta\b", "somewhat", response, flags=re.IGNORECASE)
            response = re.sub(r"\byeah\b", "yes", response, flags=re.IGNORECASE)
            response = re.sub(r"\bok\b", "acceptable", response, flags=re.IGNORECASE)
            
        elif target_formality <= 0.25:  # Informal
            # Make more casual
            response = re.sub(r"\bcannot\b", "can't", response, flags=re.IGNORECASE)
            response = re.sub(r"\bwill not\b", "won't", response, flags=re.IGNORECASE)
            response = re.sub(r"\bdo not\b", "don't", response, flags=re.IGNORECASE)
            response = re.sub(r"\bis not\b", "isn't", response, flags=re.IGNORECASE)
            
            # Add casual elements
            if profile.use_slang and strength > 0.5:
                response = re.sub(r"\bvery\b", "really", response, flags=re.IGNORECASE)
                response = re.sub(r"\bexcellent\b", "awesome", response, flags=re.IGNORECASE)
        
        return response
    
    def _adjust_tone(
        self,
        response: str,
        profile: StyleProfile,
        context: Dict[str, Any],
        strength: float
    ) -> str:
        """Adjust the tone of the response."""
        primary_tone = profile.primary_tone
        
        # Tone-specific adjustments
        if primary_tone == ToneType.ENTHUSIASTIC:
            if strength > 0.3:
                response = self._add_enthusiasm_markers(response)
        
        elif primary_tone == ToneType.SUPPORTIVE:
            response = self._add_supportive_language(response)
        
        elif primary_tone == ToneType.PROFESSIONAL:
            response = self._add_professional_markers(response)
        
        elif primary_tone == ToneType.FRIENDLY:
            response = self._add_friendly_markers(response)
        
        elif primary_tone == ToneType.ANALYTICAL:
            response = self._add_analytical_markers(response)
        
        return response
    
    def _adjust_vocabulary(
        self,
        response: str,
        profile: StyleProfile,
        context: Dict[str, Any],
        strength: float
    ) -> str:
        """Adjust vocabulary complexity and style."""
        complexity = profile.vocabulary_complexity
        
        if complexity >= 0.7:  # Complex vocabulary
            replacements = {
                r"\bhelp\b": "assist",
                r"\bshow\b": "demonstrate", 
                r"\bmake\b": "create",
                r"\bfix\b": "resolve",
                r"\bfind\b": "locate",
                r"\buse\b": "utilize",
                r"\bget\b": "obtain",
                r"\bbig\b": "substantial",
                r"\bsmall\b": "minimal"
            }
        else:  # Simple vocabulary
            replacements = {
                r"\bassist\b": "help",
                r"\bdemonstrate\b": "show",
                r"\butilize\b": "use",
                r"\bobtain\b": "get",
                r"\bsubstantial\b": "big",
                r"\bminimal\b": "small",
                r"\bfacilitate\b": "help with",
                r"\bcommence\b": "start"
            }
        
        for pattern, replacement in replacements.items():
            if strength > 0.4:  # Only apply if strong enough adaptation
                response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _adjust_structure(
        self,
        response: str,
        profile: StyleProfile,
        context: Dict[str, Any],
        strength: float
    ) -> str:
        """Adjust sentence structure and length."""
        target_length = profile.sentence_length_preference
        
        # Simple structural adjustments
        if target_length <= 0.3 and strength > 0.5:  # Short sentences preferred
            # Break long sentences
            response = re.sub(r',\s*and\s+', '. ', response)
            response = re.sub(r';\s*', '. ', response)
        
        elif target_length >= 0.7 and strength > 0.5:  # Long sentences preferred
            # Connect short sentences
            response = re.sub(r'\.\s+([a-z])', r', \1', response)
        
        # Question handling
        if profile.use_questions and profile.question_handling == "exploratory":
            if "?" not in response and strength > 0.6:
                # Add exploratory questions
                exploratory_questions = [
                    " What do you think?",
                    " Does that make sense?",
                    " How does that sound?",
                    " What's your take on this?"
                ]
                import random
                response += random.choice(exploratory_questions)
        
        return response
    
    def _adjust_emotional_expression(
        self,
        response: str,
        profile: StyleProfile,
        context: Dict[str, Any],
        strength: float
    ) -> str:
        """Adjust emotional expressiveness of the response."""
        expressiveness = profile.emotional_expressiveness
        
        if expressiveness >= 0.7 and strength > 0.4:  # High expressiveness
            # Add emotional markers
            response = self._add_emotional_markers(response)
        
        elif expressiveness <= 0.3 and strength > 0.4:  # Low expressiveness
            # Remove emotional markers
            response = self._remove_emotional_markers(response)
        
        return response
    
    def _add_enthusiasm_markers(self, response: str) -> str:
        """Add enthusiasm markers to response."""
        # Add exclamation points (but not too many)
        if "!" not in response and len(response) > 20:
            response = response.rstrip('.') + "!"
        
        # Add enthusiastic words
        enthusiasm_words = {
            r"\bgood\b": "great",
            r"\bnice\b": "fantastic", 
            r"\byes\b": "absolutely",
            r"\bsure\b": "definitely"
        }
        
        for pattern, replacement in enthusiasm_words.items():
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _add_supportive_language(self, response: str) -> str:
        """Add supportive language elements."""
        supportive_prefixes = [
            "I understand that ",
            "That makes sense, ",
            "I can see why "
        ]
        
        # Add supportive acknowledgment
        if not any(prefix.lower() in response.lower() for prefix in supportive_prefixes):
            import random
            if len(response.split()) > 5:  # Only for longer responses
                prefix = random.choice(supportive_prefixes)
                response = prefix + response.lower()
        
        return response
    
    def _add_professional_markers(self, response: str) -> str:
        """Add professional communication markers."""
        # Add formal closings
        if len(response) > 50 and not response.endswith((".", "!", "?")):
            response += "."
        
        # Use more measured language
        professional_replacements = {
            r"\bI think\b": "I believe",
            r"\bmaybe\b": "perhaps",
            r"\bprobably\b": "likely"
        }
        
        for pattern, replacement in professional_replacements.items():
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _add_friendly_markers(self, response: str) -> str:
        """Add friendly communication markers."""
        # Add warm greetings if appropriate
        greeting_patterns = [
            r"^(Hi|Hello|Hey)",
            r"^(Good morning|Good afternoon|Good evening)"
        ]
        
        has_greeting = any(re.search(pattern, response, re.IGNORECASE) for pattern in greeting_patterns)
        
        if not has_greeting and len(response.split()) > 3:
            friendly_starters = ["Hi there! ", "Hey! ", "Hello! "]
            import random
            response = random.choice(friendly_starters) + response
        
        return response
    
    def _add_analytical_markers(self, response: str) -> str:
        """Add analytical communication markers."""
        # Add structured thinking markers
        analytical_connectors = {
            r"\bSo\b": "Therefore",
            r"\bbut\b": "however",
            r"\balso\b": "additionally"
        }
        
        for pattern, replacement in analytical_connectors.items():
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _add_emotional_markers(self, response: str) -> str:
        """Add emotional expression markers."""
        # Add emotional punctuation and words
        if random.random() < 0.3:  # 30% chance
            emotional_additions = [" 😊", " 🙂", " 👍"]
            import random
            response += random.choice(emotional_additions)
        
        return response
    
    def _remove_emotional_markers(self, response: str) -> str:
        """Remove emotional expression markers."""
        # Remove excessive punctuation
        response = re.sub(r'!+', '.', response)
        response = re.sub(r'\?+', '?', response)
        
        # Remove emotional words
        emotional_removals = {
            r"\bso excited\b": "pleased",
            r"\blove it\b": "find it satisfactory",
            r"\bamazing\b": "notable"
        }
        
        for pattern, replacement in emotional_removals.items():
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _record_adaptation(
        self,
        original: str,
        adapted: str,
        profile_name: str,
        context: Dict[str, Any],
        strength: float
    ) -> None:
        """Record an adaptation for analysis and learning."""
        adaptation_record = {
            "timestamp": context.get("timestamp"),
            "original_length": len(original),
            "adapted_length": len(adapted),
            "profile_name": profile_name,
            "adaptation_strength": strength,
            "context_keys": list(context.keys()),
            "changed": original != adapted
        }
        
        self.adaptation_history.append(adaptation_record)
        
        # Keep history manageable
        if len(self.adaptation_history) > 1000:
            self.adaptation_history = self.adaptation_history[-500:]
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get statistics about adaptations performed."""
        if not self.adaptation_history:
            return {"total_adaptations": 0}
        
        total = len(self.adaptation_history)
        changed = sum(1 for record in self.adaptation_history if record["changed"])
        
        profile_usage = {}
        for record in self.adaptation_history:
            profile = record["profile_name"]
            profile_usage[profile] = profile_usage.get(profile, 0) + 1
        
        avg_strength = sum(record["adaptation_strength"] for record in self.adaptation_history) / total
        
        return {
            "total_adaptations": total,
            "successful_adaptations": changed,
            "adaptation_rate": changed / total if total > 0 else 0,
            "average_adaptation_strength": round(avg_strength, 3),
            "profile_usage": profile_usage,
            "registered_profiles": len(self.style_profiles)
        }