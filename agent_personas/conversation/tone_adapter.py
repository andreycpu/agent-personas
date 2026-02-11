"""
Tone adapter for fine-tuning conversational tone and emotional expression.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import random


class ToneCategory(Enum):
    """Categories of conversational tone."""
    WARMTH = "warmth"
    CONFIDENCE = "confidence" 
    ENTHUSIASM = "enthusiasm"
    PROFESSIONALISM = "professionalism"
    EMPATHY = "empathy"
    HUMOR = "humor"
    ASSERTIVENESS = "assertiveness"
    SUPPORTIVENESS = "supportiveness"


@dataclass
class ToneModifier:
    """Represents a tone modification technique."""
    name: str
    category: ToneCategory
    intensity_range: Tuple[float, float] = (0.0, 1.0)  # Valid intensity range
    
    # Text modification patterns
    word_substitutions: Dict[str, List[str]] = field(default_factory=dict)
    phrase_additions: List[str] = field(default_factory=list)
    punctuation_changes: Dict[str, str] = field(default_factory=dict)
    structural_changes: List[str] = field(default_factory=list)
    
    # Application conditions
    min_intensity: float = 0.1
    max_applications_per_text: int = 3
    
    def apply(self, text: str, intensity: float, context: Dict[str, Any] = None) -> str:
        """
        Apply this tone modifier to text.
        
        Args:
            text: Original text
            intensity: Intensity of modification (0.0-1.0)
            context: Optional context information
            
        Returns:
            Modified text
        """
        if intensity < self.min_intensity:
            return text
            
        # Clamp intensity to valid range
        intensity = max(self.intensity_range[0], min(self.intensity_range[1], intensity))
        
        modified_text = text
        applications = 0
        
        # Apply word substitutions
        if self.word_substitutions and random.random() < intensity:
            modified_text = self._apply_word_substitutions(modified_text, intensity)
            applications += 1
            
        # Apply phrase additions
        if (self.phrase_additions and 
            random.random() < intensity and 
            applications < self.max_applications_per_text):
            modified_text = self._apply_phrase_additions(modified_text, intensity)
            applications += 1
            
        # Apply punctuation changes
        if (self.punctuation_changes and 
            random.random() < intensity and 
            applications < self.max_applications_per_text):
            modified_text = self._apply_punctuation_changes(modified_text, intensity)
            applications += 1
            
        # Apply structural changes
        if (self.structural_changes and 
            random.random() < intensity * 0.5 and  # Less frequent
            applications < self.max_applications_per_text):
            modified_text = self._apply_structural_changes(modified_text, intensity)
            
        return modified_text
        
    def _apply_word_substitutions(self, text: str, intensity: float) -> str:
        """Apply word substitutions based on intensity."""
        words = text.split()
        
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in self.word_substitutions:
                replacements = self.word_substitutions[clean_word]
                if replacements and random.random() < intensity:
                    replacement = random.choice(replacements)
                    # Preserve original casing and punctuation
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    words[i] = re.sub(re.escape(clean_word), replacement, word, flags=re.IGNORECASE)
                    
        return " ".join(words)
        
    def _apply_phrase_additions(self, text: str, intensity: float) -> str:
        """Add phrases to enhance tone."""
        if not self.phrase_additions:
            return text
            
        addition = random.choice(self.phrase_additions)
        
        # Decide placement based on intensity
        if intensity > 0.7:
            # High intensity: add to both ends sometimes
            if random.random() < 0.3:
                return f"{addition} {text} {addition}"
            elif random.random() < 0.5:
                return f"{addition} {text}"
            else:
                return f"{text} {addition}"
        elif intensity > 0.4:
            # Medium intensity: add to one end
            if random.random() < 0.5:
                return f"{addition} {text}"
            else:
                return f"{text} {addition}"
        else:
            # Low intensity: occasional addition at end
            return f"{text} {addition}"
            
    def _apply_punctuation_changes(self, text: str, intensity: float) -> str:
        """Apply punctuation modifications."""
        modified = text
        
        for old_punct, new_punct in self.punctuation_changes.items():
            if random.random() < intensity:
                modified = modified.replace(old_punct, new_punct)
                
        return modified
        
    def _apply_structural_changes(self, text: str, intensity: float) -> str:
        """Apply structural text changes."""
        # This is a placeholder for more complex structural modifications
        # Could include sentence reordering, breaking/combining sentences, etc.
        return text


class ToneAdapter:
    """
    Adapts text tone based on desired emotional and stylistic characteristics.
    """
    
    def __init__(self):
        self._modifiers: Dict[str, ToneModifier] = {}
        self._tone_profiles: Dict[str, Dict[ToneCategory, float]] = {}
        
        # Load default tone modifiers
        self._load_default_modifiers()
        self._load_default_profiles()
        
    def add_modifier(self, modifier: ToneModifier) -> None:
        """Add a tone modifier."""
        self._modifiers[modifier.name] = modifier
        
    def remove_modifier(self, name: str) -> bool:
        """Remove a tone modifier."""
        if name in self._modifiers:
            del self._modifiers[name]
            return True
        return False
        
    def add_tone_profile(self, name: str, profile: Dict[ToneCategory, float]) -> None:
        """
        Add a named tone profile.
        
        Args:
            name: Profile name
            profile: Dictionary mapping tone categories to intensity values (0.0-1.0)
        """
        # Validate intensities
        validated_profile = {}
        for category, intensity in profile.items():
            validated_profile[category] = max(0.0, min(1.0, intensity))
        self._tone_profiles[name] = validated_profile
        
    def adapt_tone(
        self, 
        text: str, 
        target_tone: Dict[ToneCategory, float],
        context: Dict[str, Any] = None
    ) -> str:
        """
        Adapt text tone to match target characteristics.
        
        Args:
            text: Original text
            target_tone: Dictionary of tone categories and desired intensities
            context: Optional context information
            
        Returns:
            Tone-adapted text
        """
        if context is None:
            context = {}
            
        adapted_text = text
        
        # Apply modifiers for each requested tone category
        for category, intensity in target_tone.items():
            if intensity > 0:
                category_modifiers = [
                    modifier for modifier in self._modifiers.values()
                    if modifier.category == category
                ]
                
                # Apply modifiers in random order to avoid predictable patterns
                random.shuffle(category_modifiers)
                
                for modifier in category_modifiers:
                    if random.random() < 0.7:  # Don't apply all modifiers
                        adapted_text = modifier.apply(adapted_text, intensity, context)
                        
        return adapted_text
        
    def apply_profile(
        self, 
        text: str, 
        profile_name: str,
        intensity_multiplier: float = 1.0,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Apply a named tone profile to text.
        
        Args:
            text: Original text
            profile_name: Name of the tone profile to apply
            intensity_multiplier: Global intensity multiplier (0.0-2.0)
            context: Optional context information
            
        Returns:
            Tone-adapted text
        """
        if profile_name not in self._tone_profiles:
            return text
            
        profile = self._tone_profiles[profile_name]
        
        # Apply intensity multiplier
        adjusted_profile = {
            category: intensity * intensity_multiplier
            for category, intensity in profile.items()
        }
        
        return self.adapt_tone(text, adjusted_profile, context)
        
    def analyze_current_tone(self, text: str) -> Dict[ToneCategory, float]:
        """
        Analyze the current tone characteristics of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of detected tone characteristics
        """
        analysis = {category: 0.0 for category in ToneCategory}
        
        text_lower = text.lower()
        
        # Warmth indicators
        warmth_indicators = ['thank', 'please', 'kind', 'wonderful', 'lovely', 'dear']
        warmth_score = sum(1 for indicator in warmth_indicators if indicator in text_lower)
        analysis[ToneCategory.WARMTH] = min(1.0, warmth_score / 5.0)
        
        # Confidence indicators
        confidence_indicators = ['will', 'definitely', 'certainly', 'confident', 'sure']
        confidence_score = sum(1 for indicator in confidence_indicators if indicator in text_lower)
        analysis[ToneCategory.CONFIDENCE] = min(1.0, confidence_score / 3.0)
        
        # Enthusiasm indicators
        enthusiasm_indicators = ['!', 'amazing', 'fantastic', 'great', 'excited', 'awesome']
        enthusiasm_score = sum(1 for indicator in enthusiasm_indicators if indicator in text_lower)
        enthusiasm_score += text.count('!') * 0.2
        analysis[ToneCategory.ENTHUSIASM] = min(1.0, enthusiasm_score / 4.0)
        
        # Professionalism indicators
        professional_indicators = ['however', 'furthermore', 'therefore', 'regarding', 'pursuant']
        professional_score = sum(1 for indicator in professional_indicators if indicator in text_lower)
        analysis[ToneCategory.PROFESSIONALISM] = min(1.0, professional_score / 3.0)
        
        # Empathy indicators
        empathy_indicators = ['understand', 'feel', 'sorry', 'care', 'support', 'here for you']
        empathy_score = sum(1 for indicator in empathy_indicators if indicator in text_lower)
        analysis[ToneCategory.EMPATHY] = min(1.0, empathy_score / 4.0)
        
        # Humor indicators
        humor_indicators = ['haha', 'lol', ':)', 'funny', 'joke', 'kidding']
        humor_score = sum(1 for indicator in humor_indicators if indicator in text_lower)
        analysis[ToneCategory.HUMOR] = min(1.0, humor_score / 3.0)
        
        return analysis
        
    def suggest_tone_adjustments(
        self, 
        text: str, 
        target_profile: str,
        current_analysis: Optional[Dict[ToneCategory, float]] = None
    ) -> List[str]:
        """
        Suggest specific adjustments to reach target tone profile.
        
        Args:
            text: Current text
            target_profile: Name of target tone profile
            current_analysis: Optional pre-computed current tone analysis
            
        Returns:
            List of tone adjustment suggestions
        """
        if target_profile not in self._tone_profiles:
            return ["Unknown tone profile"]
            
        if current_analysis is None:
            current_analysis = self.analyze_current_tone(text)
            
        target = self._tone_profiles[target_profile]
        suggestions = []
        
        for category, target_intensity in target.items():
            current_intensity = current_analysis.get(category, 0.0)
            difference = target_intensity - current_intensity
            
            if abs(difference) > 0.2:  # Significant difference
                if difference > 0:
                    # Need to increase this tone
                    suggestions.append(self._get_increase_suggestion(category, difference))
                else:
                    # Need to decrease this tone  
                    suggestions.append(self._get_decrease_suggestion(category, -difference))
                    
        return suggestions
        
    def _get_increase_suggestion(self, category: ToneCategory, amount: float) -> str:
        """Get suggestion for increasing a tone category."""
        intensity_desc = "slightly" if amount < 0.4 else "significantly" if amount < 0.7 else "dramatically"
        
        suggestions = {
            ToneCategory.WARMTH: f"Add {intensity_desc} more warmth with words like 'thank you', 'please', or 'wonderful'",
            ToneCategory.CONFIDENCE: f"Express {intensity_desc} more confidence with words like 'certainly', 'definitely', or 'will'",
            ToneCategory.ENTHUSIASM: f"Show {intensity_desc} more enthusiasm with exclamation points or words like 'amazing', 'fantastic'",
            ToneCategory.PROFESSIONALISM: f"Increase professionalism {intensity_desc} with formal transitions like 'however', 'furthermore'",
            ToneCategory.EMPATHY: f"Express {intensity_desc} more empathy with phrases like 'I understand', 'I care about'",
            ToneCategory.HUMOR: f"Add {intensity_desc} more humor with light expressions or playful language",
            ToneCategory.ASSERTIVENESS: f"Be {intensity_desc} more assertive with direct statements and strong verbs",
            ToneCategory.SUPPORTIVENESS: f"Be {intensity_desc} more supportive with encouraging and affirming language"
        }
        
        return suggestions.get(category, f"Increase {category.value} {intensity_desc}")
        
    def _get_decrease_suggestion(self, category: ToneCategory, amount: float) -> str:
        """Get suggestion for decreasing a tone category."""
        intensity_desc = "slightly" if amount < 0.4 else "significantly" if amount < 0.7 else "dramatically"
        
        suggestions = {
            ToneCategory.WARMTH: f"Reduce warmth {intensity_desc} by using more neutral language",
            ToneCategory.CONFIDENCE: f"Soften confidence {intensity_desc} with qualifying words like 'might', 'could'",
            ToneCategory.ENTHUSIASM: f"Tone down enthusiasm {intensity_desc} by removing exclamation points and strong positive words",
            ToneCategory.PROFESSIONALISM: f"Make language {intensity_desc} less formal and more conversational",
            ToneCategory.EMPATHY: f"Use {intensity_desc} less emotional language and more neutral expressions",
            ToneCategory.HUMOR: f"Reduce humor {intensity_desc} and use more serious language",
            ToneCategory.ASSERTIVENESS: f"Soften assertiveness {intensity_desc} with more tentative language",
            ToneCategory.SUPPORTIVENESS: f"Use {intensity_desc} more neutral language instead of encouraging expressions"
        }
        
        return suggestions.get(category, f"Decrease {category.value} {intensity_desc}")
        
    def list_available_profiles(self) -> List[str]:
        """Get list of available tone profiles."""
        return list(self._tone_profiles.keys())
        
    def get_profile_details(self, profile_name: str) -> Optional[Dict[ToneCategory, float]]:
        """Get details of a specific tone profile."""
        return self._tone_profiles.get(profile_name, {}).copy()
        
    def _load_default_modifiers(self) -> None:
        """Load default tone modifiers."""
        
        # Warmth modifier
        warmth_modifier = ToneModifier(
            name="warmth_basic",
            category=ToneCategory.WARMTH,
            word_substitutions={
                "good": ["wonderful", "lovely", "nice"],
                "okay": ["perfectly fine", "absolutely fine"],
                "yes": ["absolutely", "of course", "certainly"]
            },
            phrase_additions=[
                "Thank you so much!",
                "I really appreciate that.",
                "You're very kind.",
                "That's wonderful to hear."
            ]
        )
        
        # Confidence modifier
        confidence_modifier = ToneModifier(
            name="confidence_basic",
            category=ToneCategory.CONFIDENCE,
            word_substitutions={
                "think": ["know", "believe", "am confident"],
                "maybe": ["definitely", "certainly"],
                "might": ["will", "am going to"]
            },
            punctuation_changes={".": "."},  # Keep strong periods
            phrase_additions=[
                "I'm confident that",
                "Without a doubt",
                "I'm certain"
            ]
        )
        
        # Enthusiasm modifier
        enthusiasm_modifier = ToneModifier(
            name="enthusiasm_basic",
            category=ToneCategory.ENTHUSIASM,
            word_substitutions={
                "good": ["amazing", "fantastic", "awesome"],
                "nice": ["incredible", "wonderful", "brilliant"],
                "okay": ["great", "perfect", "excellent"]
            },
            punctuation_changes={".": "!", "?": "?!"},
            phrase_additions=[
                "That's fantastic!",
                "How exciting!",
                "Amazing!",
                "Wonderful!"
            ]
        )
        
        # Empathy modifier
        empathy_modifier = ToneModifier(
            name="empathy_basic",
            category=ToneCategory.EMPATHY,
            phrase_additions=[
                "I understand how you feel.",
                "That must be difficult.",
                "I'm here to help.",
                "Your feelings are valid."
            ],
            word_substitutions={
                "see": ["understand", "recognize"],
                "know": ["can imagine", "understand"]
            }
        )
        
        # Add modifiers
        modifiers = [warmth_modifier, confidence_modifier, enthusiasm_modifier, empathy_modifier]
        for modifier in modifiers:
            self.add_modifier(modifier)
            
    def _load_default_profiles(self) -> None:
        """Load default tone profiles."""
        
        profiles = {
            "friendly": {
                ToneCategory.WARMTH: 0.7,
                ToneCategory.ENTHUSIASM: 0.5,
                ToneCategory.SUPPORTIVENESS: 0.6
            },
            
            "professional": {
                ToneCategory.PROFESSIONALISM: 0.8,
                ToneCategory.CONFIDENCE: 0.6,
                ToneCategory.ASSERTIVENESS: 0.5
            },
            
            "empathetic": {
                ToneCategory.EMPATHY: 0.9,
                ToneCategory.WARMTH: 0.7,
                ToneCategory.SUPPORTIVENESS: 0.8
            },
            
            "enthusiastic": {
                ToneCategory.ENTHUSIASM: 0.9,
                ToneCategory.WARMTH: 0.6,
                ToneCategory.CONFIDENCE: 0.7
            },
            
            "calm_confident": {
                ToneCategory.CONFIDENCE: 0.8,
                ToneCategory.PROFESSIONALISM: 0.6,
                ToneCategory.SUPPORTIVENESS: 0.5
            },
            
            "playful": {
                ToneCategory.HUMOR: 0.7,
                ToneCategory.ENTHUSIASM: 0.6,
                ToneCategory.WARMTH: 0.5
            }
        }
        
        for name, profile in profiles.items():
            self.add_tone_profile(name, profile)