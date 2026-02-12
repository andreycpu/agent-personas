"""
Advanced emotion engine for dynamic emotional response generation.
"""

from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import random
import math
from datetime import datetime, timedelta

from .emotional_state import EmotionalState, Emotion, EmotionCategory, EmotionIntensity

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of emotional triggers."""
    KEYWORD = "keyword"
    SENTIMENT = "sentiment"
    CONTEXT = "context"
    INTERACTION = "interaction"
    TEMPORAL = "temporal"
    THRESHOLD = "threshold"
    PATTERN = "pattern"


class TriggerCondition(Enum):
    """Conditions for trigger activation."""
    EQUALS = "equals"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    RANGE = "range"
    REGEX = "regex"


@dataclass
class EmotionTrigger:
    """
    Defines a trigger that can activate specific emotions.
    """
    name: str
    trigger_type: TriggerType
    condition: TriggerCondition
    pattern: str  # The pattern to match (keyword, regex, etc.)
    target_emotions: Dict[str, float]  # Emotions to activate with intensities
    threshold: float = 0.5  # Threshold for activation
    cooldown_minutes: float = 5.0  # Minimum time between activations
    decay_rate: float = 0.1  # How quickly the trigger effect decays
    context_requirements: List[str] = field(default_factory=list)  # Required context
    inhibitors: List[str] = field(default_factory=list)  # Conditions that prevent activation
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_activated: Optional[datetime] = None
    activation_count: int = 0
    
    def can_activate(self, current_time: Optional[datetime] = None) -> bool:
        """Check if this trigger can currently activate."""
        if current_time is None:
            current_time = datetime.now()
        
        if self.last_activated:
            time_since_last = current_time - self.last_activated
            if time_since_last.total_seconds() / 60 < self.cooldown_minutes:
                return False
        
        return True
    
    def activate(self, context: Dict[str, Any], current_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        Activate the trigger and return emotion adjustments.
        
        Returns:
            Dictionary of emotion names to intensity adjustments
        """
        if current_time is None:
            current_time = datetime.now()
        
        if not self.can_activate(current_time):
            return {}
        
        # Check context requirements
        for requirement in self.context_requirements:
            if requirement not in context:
                logger.debug(f"Trigger {self.name} context requirement not met: {requirement}")
                return {}
        
        # Check inhibitors
        for inhibitor in self.inhibitors:
            if inhibitor in context and context[inhibitor]:
                logger.debug(f"Trigger {self.name} inhibited by: {inhibitor}")
                return {}
        
        # Update activation tracking
        self.last_activated = current_time
        self.activation_count += 1
        
        logger.debug(f"Trigger {self.name} activated (count: {self.activation_count})")
        return self.target_emotions.copy()


class EmotionRule:
    """Defines a rule for emotional response generation."""
    
    def __init__(
        self,
        name: str,
        condition_function: Callable[[Dict[str, Any]], bool],
        emotion_adjustments: Dict[str, float],
        priority: int = 1
    ):
        self.name = name
        self.condition_function = condition_function
        self.emotion_adjustments = emotion_adjustments
        self.priority = priority
        self.application_count = 0
    
    def applies(self, context: Dict[str, Any]) -> bool:
        """Check if this rule applies to the given context."""
        try:
            return self.condition_function(context)
        except Exception as e:
            logger.error(f"Error evaluating rule {self.name}: {e}")
            return False
    
    def apply(self) -> Dict[str, float]:
        """Apply the rule and return emotion adjustments."""
        self.application_count += 1
        return self.emotion_adjustments.copy()


class AdvancedEmotionEngine:
    """
    Advanced engine for generating dynamic emotional responses.
    
    Processes input context through triggers and rules to generate
    appropriate emotional states and transitions.
    """
    
    def __init__(self):
        self.triggers: List[EmotionTrigger] = []
        self.rules: List[EmotionRule] = []
        self.emotion_library: Dict[str, Emotion] = {}
        self.baseline_emotions: Dict[str, float] = {}
        self.personality_modifiers: Dict[str, float] = {}
        self.context_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        self.logger = logging.getLogger(__name__)
        
        # Initialize with common emotions
        self._initialize_emotion_library()
    
    def _initialize_emotion_library(self):
        """Initialize the library with common emotions."""
        common_emotions = [
            # Primary emotions
            Emotion("joy", 0.0, EmotionCategory.PRIMARY, 0.8, 0.7, 0.6, 20, ["success", "achievement", "love"]),
            Emotion("sadness", 0.0, EmotionCategory.PRIMARY, -0.8, 0.3, 0.2, 45, ["loss", "failure", "rejection"]),
            Emotion("anger", 0.0, EmotionCategory.PRIMARY, -0.6, 0.9, 0.8, 15, ["frustration", "injustice", "threat"]),
            Emotion("fear", 0.0, EmotionCategory.PRIMARY, -0.7, 0.8, 0.1, 25, ["danger", "uncertainty", "threat"]),
            Emotion("surprise", 0.0, EmotionCategory.PRIMARY, 0.0, 0.9, 0.5, 5, ["unexpected", "novel", "sudden"]),
            Emotion("disgust", 0.0, EmotionCategory.PRIMARY, -0.9, 0.4, 0.6, 30, ["unpleasant", "offensive", "rejection"]),
            
            # Secondary emotions
            Emotion("pride", 0.0, EmotionCategory.SECONDARY, 0.7, 0.6, 0.8, 30, ["achievement", "recognition"]),
            Emotion("guilt", 0.0, EmotionCategory.SECONDARY, -0.6, 0.5, 0.2, 60, ["mistake", "harm", "regret"]),
            Emotion("shame", 0.0, EmotionCategory.SECONDARY, -0.8, 0.3, 0.1, 90, ["exposure", "inadequacy"]),
            Emotion("excitement", 0.0, EmotionCategory.SECONDARY, 0.9, 0.9, 0.7, 15, ["anticipation", "novelty"]),
            
            # Social emotions
            Emotion("empathy", 0.0, EmotionCategory.SOCIAL, 0.3, 0.4, 0.4, 40, ["others_emotion", "connection"]),
            Emotion("compassion", 0.0, EmotionCategory.SOCIAL, 0.5, 0.3, 0.5, 50, ["suffering", "care"]),
            Emotion("envy", 0.0, EmotionCategory.SOCIAL, -0.4, 0.6, 0.3, 35, ["comparison", "lack"]),
            
            # Cognitive emotions
            Emotion("curiosity", 0.0, EmotionCategory.COGNITIVE, 0.4, 0.6, 0.6, 25, ["unknown", "learning"]),
            Emotion("confusion", 0.0, EmotionCategory.COGNITIVE, -0.2, 0.7, 0.3, 20, ["complexity", "ambiguity"]),
            Emotion("satisfaction", 0.0, EmotionCategory.COGNITIVE, 0.6, 0.4, 0.6, 35, ["completion", "fulfillment"])
        ]
        
        for emotion in common_emotions:
            self.emotion_library[emotion.name] = emotion
    
    def add_trigger(self, trigger: EmotionTrigger) -> None:
        """Add an emotion trigger."""
        self.triggers.append(trigger)
        self.logger.debug(f"Added trigger: {trigger.name}")
    
    def add_rule(self, rule: EmotionRule) -> None:
        """Add an emotion rule."""
        self.rules.append(rule)
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.debug(f"Added rule: {rule.name}")
    
    def add_emotion_definition(self, emotion: Emotion) -> None:
        """Add or update an emotion definition."""
        self.emotion_library[emotion.name] = emotion
        self.logger.debug(f"Added emotion definition: {emotion.name}")
    
    def set_baseline_emotions(self, emotions: Dict[str, float]) -> None:
        """Set baseline emotion levels."""
        self.baseline_emotions = emotions.copy()
        self.logger.debug(f"Set baseline emotions: {list(emotions.keys())}")
    
    def set_personality_modifiers(self, modifiers: Dict[str, float]) -> None:
        """Set personality-based emotion modifiers."""
        self.personality_modifiers = modifiers.copy()
        self.logger.debug(f"Set personality modifiers: {list(modifiers.keys())}")
    
    def process_input(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
        current_emotional_state: Optional[EmotionalState] = None
    ) -> EmotionalState:
        """
        Process input and generate emotional response.
        
        Args:
            input_text: The input text to process
            context: Additional context information
            current_emotional_state: Current emotional state (if any)
            
        Returns:
            New or updated emotional state
        """
        if context is None:
            context = {}
        
        # Add input to context
        context["input_text"] = input_text
        context["input_length"] = len(input_text)
        context["timestamp"] = datetime.now()
        
        # Initialize emotional state if not provided
        if current_emotional_state is None:
            current_emotional_state = EmotionalState()
        
        # Store context in history
        self._add_to_history(context)
        
        # Process triggers
        triggered_emotions = self._process_triggers(context)
        
        # Process rules
        rule_emotions = self._process_rules(context)
        
        # Combine triggered emotions and rule emotions
        combined_emotions = {}
        for emotion_name, intensity in triggered_emotions.items():
            combined_emotions[emotion_name] = combined_emotions.get(emotion_name, 0) + intensity
        
        for emotion_name, intensity in rule_emotions.items():
            combined_emotions[emotion_name] = combined_emotions.get(emotion_name, 0) + intensity
        
        # Apply personality modifiers
        for emotion_name in combined_emotions:
            if emotion_name in self.personality_modifiers:
                combined_emotions[emotion_name] *= self.personality_modifiers[emotion_name]
        
        # Apply baseline emotions
        for emotion_name, baseline_intensity in self.baseline_emotions.items():
            combined_emotions[emotion_name] = combined_emotions.get(emotion_name, 0) + baseline_intensity
        
        # Update emotional state
        self._update_emotional_state(current_emotional_state, combined_emotions)
        
        self.logger.info(f"Processed input, generated {len(combined_emotions)} emotion adjustments")
        return current_emotional_state
    
    def _process_triggers(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Process all triggers against the context."""
        triggered_emotions = {}
        
        for trigger in self.triggers:
            if self._trigger_matches(trigger, context):
                emotion_adjustments = trigger.activate(context)
                for emotion_name, intensity in emotion_adjustments.items():
                    triggered_emotions[emotion_name] = triggered_emotions.get(emotion_name, 0) + intensity
        
        return triggered_emotions
    
    def _trigger_matches(self, trigger: EmotionTrigger, context: Dict[str, Any]) -> bool:
        """Check if a trigger matches the given context."""
        if trigger.trigger_type == TriggerType.KEYWORD:
            input_text = context.get("input_text", "").lower()
            pattern = trigger.pattern.lower()
            
            if trigger.condition == TriggerCondition.CONTAINS:
                return pattern in input_text
            elif trigger.condition == TriggerCondition.EQUALS:
                return pattern == input_text.strip()
        
        elif trigger.trigger_type == TriggerType.SENTIMENT:
            # Simple sentiment analysis based on keywords
            sentiment_score = self._calculate_sentiment_score(context.get("input_text", ""))
            
            if trigger.condition == TriggerCondition.GREATER_THAN:
                return sentiment_score > trigger.threshold
            elif trigger.condition == TriggerCondition.LESS_THAN:
                return sentiment_score < trigger.threshold
        
        elif trigger.trigger_type == TriggerType.CONTEXT:
            context_value = context.get(trigger.pattern)
            
            if trigger.condition == TriggerCondition.EQUALS:
                return context_value == trigger.threshold
            elif trigger.condition == TriggerCondition.GREATER_THAN:
                return isinstance(context_value, (int, float)) and context_value > trigger.threshold
        
        elif trigger.trigger_type == TriggerType.THRESHOLD:
            # Check if any emotion in current state exceeds threshold
            current_emotions = context.get("current_emotions", {})
            target_emotion_intensity = current_emotions.get(trigger.pattern, 0)
            
            if trigger.condition == TriggerCondition.GREATER_THAN:
                return target_emotion_intensity > trigger.threshold
            elif trigger.condition == TriggerCondition.LESS_THAN:
                return target_emotion_intensity < trigger.threshold
        
        return False
    
    def _process_rules(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Process all rules against the context."""
        rule_emotions = {}
        
        for rule in self.rules:
            if rule.applies(context):
                emotion_adjustments = rule.apply()
                for emotion_name, intensity in emotion_adjustments.items():
                    rule_emotions[emotion_name] = rule_emotions.get(emotion_name, 0) + intensity
                
                logger.debug(f"Applied rule: {rule.name}")
        
        return rule_emotions
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Simple sentiment analysis (can be replaced with more sophisticated methods)."""
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "love", "happy", "joy", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "hate", "sad", "angry", "frustrated", "disappointed", "horrible"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_emotional_words = positive_count + negative_count
        if total_emotional_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_emotional_words
    
    def _update_emotional_state(self, state: EmotionalState, emotion_adjustments: Dict[str, float]) -> None:
        """Update the emotional state with new emotion adjustments."""
        for emotion_name, intensity_adjustment in emotion_adjustments.items():
            if emotion_name in self.emotion_library:
                # Create a new emotion instance with adjusted intensity
                base_emotion = self.emotion_library[emotion_name]
                adjusted_emotion = Emotion(
                    name=base_emotion.name,
                    intensity=min(1.0, max(0.0, intensity_adjustment)),
                    category=base_emotion.category,
                    valence=base_emotion.valence,
                    arousal=base_emotion.arousal,
                    dominance=base_emotion.dominance,
                    duration_minutes=base_emotion.duration_minutes,
                    triggers=base_emotion.triggers.copy()
                )
                
                # Add or update emotion in state
                if emotion_name in state.emotions:
                    # Blend with existing emotion
                    existing_intensity = state.emotions[emotion_name].intensity
                    blended_intensity = (existing_intensity + adjusted_emotion.intensity) / 2
                    state.emotions[emotion_name].intensity = min(1.0, blended_intensity)
                else:
                    # Add new emotion
                    state.add_emotion(adjusted_emotion)
    
    def _add_to_history(self, context: Dict[str, Any]) -> None:
        """Add context to processing history."""
        self.context_history.append(context)
        
        # Maintain history size limit
        if len(self.context_history) > self.max_history_size:
            self.context_history.pop(0)
    
    def create_common_triggers(self) -> List[EmotionTrigger]:
        """Create a set of common emotion triggers."""
        triggers = [
            # Positive triggers
            EmotionTrigger(
                name="joy_keywords",
                trigger_type=TriggerType.KEYWORD,
                condition=TriggerCondition.CONTAINS,
                pattern="happy|joy|excited|wonderful|amazing|great",
                target_emotions={"joy": 0.6, "excitement": 0.4}
            ),
            
            # Negative triggers
            EmotionTrigger(
                name="sadness_keywords",
                trigger_type=TriggerType.KEYWORD,
                condition=TriggerCondition.CONTAINS,
                pattern="sad|depressed|unhappy|miserable|grief",
                target_emotions={"sadness": 0.7}
            ),
            
            EmotionTrigger(
                name="anger_keywords",
                trigger_type=TriggerType.KEYWORD,
                condition=TriggerCondition.CONTAINS,
                pattern="angry|furious|mad|frustrated|irritated",
                target_emotions={"anger": 0.8}
            ),
            
            # Question triggers curiosity
            EmotionTrigger(
                name="question_curiosity",
                trigger_type=TriggerType.KEYWORD,
                condition=TriggerCondition.CONTAINS,
                pattern="?",
                target_emotions={"curiosity": 0.3}
            ),
            
            # Uncertainty triggers anxiety
            EmotionTrigger(
                name="uncertainty_anxiety",
                trigger_type=TriggerType.KEYWORD,
                condition=TriggerCondition.CONTAINS,
                pattern="uncertain|confused|worried|anxious|nervous",
                target_emotions={"anxiety": 0.5, "confusion": 0.4}
            ),
        ]
        
        return triggers
    
    def create_personality_rules(self, personality_traits: Dict[str, float]) -> List[EmotionRule]:
        """Create emotion rules based on personality traits."""
        rules = []
        
        # Extraversion affects social emotions
        if personality_traits.get("extraversion", 0.5) > 0.7:
            rules.append(EmotionRule(
                name="extraverted_social_boost",
                condition_function=lambda ctx: "social" in ctx.get("context_type", ""),
                emotion_adjustments={"joy": 0.2, "excitement": 0.3}
            ))
        
        # Neuroticism affects negative emotions
        neuroticism = personality_traits.get("neuroticism", 0.5)
        if neuroticism > 0.6:
            rules.append(EmotionRule(
                name="neurotic_negative_amplification",
                condition_function=lambda ctx: any(neg in ctx.get("input_text", "").lower() 
                                                 for neg in ["problem", "issue", "wrong", "error"]),
                emotion_adjustments={"anxiety": neuroticism * 0.4, "worry": neuroticism * 0.3}
            ))
        
        # Conscientiousness affects achievement emotions
        if personality_traits.get("conscientiousness", 0.5) > 0.7:
            rules.append(EmotionRule(
                name="conscientious_achievement_pride",
                condition_function=lambda ctx: any(ach in ctx.get("input_text", "").lower() 
                                                  for ach in ["completed", "finished", "achieved", "accomplished"]),
                emotion_adjustments={"pride": 0.5, "satisfaction": 0.4}
            ))
        
        return rules
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get statistics about the emotion engine."""
        return {
            "total_triggers": len(self.triggers),
            "total_rules": len(self.rules),
            "emotion_library_size": len(self.emotion_library),
            "baseline_emotions": len(self.baseline_emotions),
            "personality_modifiers": len(self.personality_modifiers),
            "history_size": len(self.context_history),
            "trigger_activations": {t.name: t.activation_count for t in self.triggers},
            "rule_applications": {r.name: r.application_count for r in self.rules}
        }