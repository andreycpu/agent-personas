"""
Emotion model for representing and managing emotional states.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import math
import random


class BasicEmotion(Enum):
    """Basic emotional categories based on psychological research."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"


class EmotionalDimension(Enum):
    """Dimensional model of emotions (valence-arousal model)."""
    VALENCE = "valence"      # Positive to negative
    AROUSAL = "arousal"      # High to low energy
    DOMINANCE = "dominance"   # Control/power


@dataclass
class EmotionalState:
    """
    Represents a complete emotional state with multiple dimensions.
    """
    # Basic emotion intensities (0.0-1.0)
    basic_emotions: Dict[BasicEmotion, float] = field(default_factory=dict)
    
    # Dimensional values (-1.0 to 1.0)
    valence: float = 0.0      # Positive/negative feeling
    arousal: float = 0.0      # Energy/activation level
    dominance: float = 0.0    # Sense of control
    
    # Meta information
    intensity: float = 0.5    # Overall emotional intensity
    stability: float = 0.5    # How stable this state is
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[timedelta] = None
    
    # Context
    triggers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Initialize basic emotions if empty
        if not self.basic_emotions:
            self.basic_emotions = {emotion: 0.0 for emotion in BasicEmotion}
            
        # Ensure all values are in valid ranges
        self._normalize_values()
        
    def _normalize_values(self) -> None:
        """Ensure all emotional values are in valid ranges."""
        # Clamp dimensional values
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
        
        # Clamp intensity and stability
        self.intensity = max(0.0, min(1.0, self.intensity))
        self.stability = max(0.0, min(1.0, self.stability))
        
        # Normalize basic emotions
        for emotion in self.basic_emotions:
            self.basic_emotions[emotion] = max(0.0, min(1.0, self.basic_emotions[emotion]))
            
    def get_dominant_emotion(self) -> Tuple[BasicEmotion, float]:
        """
        Get the most prominent emotion.
        
        Returns:
            Tuple of (emotion, intensity)
        """
        if not self.basic_emotions:
            return BasicEmotion.JOY, 0.0
            
        dominant_emotion = max(self.basic_emotions, key=self.basic_emotions.get)
        return dominant_emotion, self.basic_emotions[dominant_emotion]
        
    def get_emotion_strength(self, emotion: BasicEmotion) -> float:
        """Get the intensity of a specific emotion."""
        return self.basic_emotions.get(emotion, 0.0)
        
    def set_emotion(self, emotion: BasicEmotion, intensity: float) -> None:
        """Set the intensity of a specific emotion."""
        self.basic_emotions[emotion] = max(0.0, min(1.0, intensity))
        self._update_dimensions_from_emotions()
        
    def add_emotion(self, emotion: BasicEmotion, intensity: float) -> None:
        """Add to the current intensity of an emotion."""
        current = self.basic_emotions.get(emotion, 0.0)
        new_intensity = min(1.0, current + intensity)
        self.basic_emotions[emotion] = new_intensity
        self._update_dimensions_from_emotions()
        
    def blend_with(self, other: "EmotionalState", weight: float = 0.5) -> "EmotionalState":
        """
        Blend this emotional state with another.
        
        Args:
            other: Other emotional state
            weight: Weight of the other state (0.0-1.0)
            
        Returns:
            New blended emotional state
        """
        weight = max(0.0, min(1.0, weight))
        self_weight = 1.0 - weight
        
        # Blend basic emotions
        blended_emotions = {}
        for emotion in BasicEmotion:
            self_intensity = self.basic_emotions.get(emotion, 0.0)
            other_intensity = other.basic_emotions.get(emotion, 0.0)
            blended_emotions[emotion] = self_intensity * self_weight + other_intensity * weight
            
        # Blend dimensions
        blended_valence = self.valence * self_weight + other.valence * weight
        blended_arousal = self.arousal * self_weight + other.arousal * weight
        blended_dominance = self.dominance * self_weight + other.dominance * weight
        
        # Blend meta properties
        blended_intensity = self.intensity * self_weight + other.intensity * weight
        blended_stability = self.stability * self_weight + other.stability * weight
        
        return EmotionalState(
            basic_emotions=blended_emotions,
            valence=blended_valence,
            arousal=blended_arousal,
            dominance=blended_dominance,
            intensity=blended_intensity,
            stability=blended_stability,
            triggers=self.triggers + other.triggers
        )
        
    def decay(self, decay_rate: float = 0.1) -> "EmotionalState":
        """
        Create a decayed version of this emotional state.
        
        Args:
            decay_rate: Rate of emotional decay (0.0-1.0)
            
        Returns:
            New emotional state with reduced intensities
        """
        decayed_emotions = {}
        for emotion, intensity in self.basic_emotions.items():
            # Decay toward neutral (0.0)
            decayed_emotions[emotion] = intensity * (1.0 - decay_rate)
            
        # Decay dimensions toward neutral
        decayed_valence = self.valence * (1.0 - decay_rate)
        decayed_arousal = self.arousal * (1.0 - decay_rate)
        decayed_dominance = self.dominance * (1.0 - decay_rate)
        
        # Decay overall intensity
        decayed_intensity = self.intensity * (1.0 - decay_rate)
        
        return EmotionalState(
            basic_emotions=decayed_emotions,
            valence=decayed_valence,
            arousal=decayed_arousal,
            dominance=decayed_dominance,
            intensity=decayed_intensity,
            stability=self.stability,  # Stability doesn't decay
            triggers=self.triggers.copy()
        )
        
    def get_mood_label(self) -> str:
        """
        Get a human-readable label for the current emotional state.
        
        Returns:
            Mood label string
        """
        # Find dominant emotion
        dominant_emotion, dominant_intensity = self.get_dominant_emotion()
        
        if dominant_intensity < 0.2:
            return "neutral"
            
        # Combine dominant emotion with dimensional information
        emotion_base = dominant_emotion.value
        
        # Modify based on arousal and valence
        if self.arousal > 0.5:
            if self.valence > 0.5:
                modifiers = ["excited", "energetic", "enthusiastic"]
            else:
                modifiers = ["agitated", "intense", "worked up"]
        elif self.arousal < -0.5:
            if self.valence > 0.5:
                modifiers = ["calm", "peaceful", "content"]
            else:
                modifiers = ["dejected", "subdued", "low"]
        else:
            # Medium arousal
            if self.valence > 0.5:
                modifiers = ["positive", "pleasant"]
            elif self.valence < -0.5:
                modifiers = ["negative", "unpleasant"]
            else:
                modifiers = ["neutral"]
                
        if dominant_intensity > 0.7:
            intensity_prefix = "very "
        elif dominant_intensity > 0.4:
            intensity_prefix = "somewhat "
        else:
            intensity_prefix = "mildly "
            
        if modifiers and modifiers[0] != "neutral":
            return f"{intensity_prefix}{modifiers[0]} {emotion_base}"
        else:
            return f"{intensity_prefix}{emotion_base}"
            
    def calculate_similarity(self, other: "EmotionalState") -> float:
        """
        Calculate similarity to another emotional state.
        
        Args:
            other: Other emotional state
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Compare basic emotions
        emotion_differences = []
        for emotion in BasicEmotion:
            self_intensity = self.basic_emotions.get(emotion, 0.0)
            other_intensity = other.basic_emotions.get(emotion, 0.0)
            emotion_differences.append(abs(self_intensity - other_intensity))
            
        avg_emotion_diff = sum(emotion_differences) / len(emotion_differences)
        
        # Compare dimensions
        valence_diff = abs(self.valence - other.valence) / 2.0
        arousal_diff = abs(self.arousal - other.arousal) / 2.0
        dominance_diff = abs(self.dominance - other.dominance) / 2.0
        
        # Weight the comparisons
        total_difference = (
            avg_emotion_diff * 0.6 +
            valence_diff * 0.15 +
            arousal_diff * 0.15 +
            dominance_diff * 0.1
        )
        
        return 1.0 - total_difference
        
    def _update_dimensions_from_emotions(self) -> None:
        """Update dimensional values based on basic emotion intensities."""
        # Mapping of emotions to dimensional values (approximate)
        emotion_mappings = {
            BasicEmotion.JOY: (0.8, 0.6, 0.3),
            BasicEmotion.SADNESS: (-0.7, -0.4, -0.3),
            BasicEmotion.ANGER: (-0.6, 0.7, 0.6),
            BasicEmotion.FEAR: (-0.8, 0.5, -0.7),
            BasicEmotion.SURPRISE: (0.1, 0.8, 0.0),
            BasicEmotion.DISGUST: (-0.7, 0.3, 0.2),
            BasicEmotion.TRUST: (0.5, -0.2, 0.4),
            BasicEmotion.ANTICIPATION: (0.3, 0.6, 0.2)
        }
        
        # Weighted average based on emotion intensities
        total_valence = 0.0
        total_arousal = 0.0
        total_dominance = 0.0
        total_weight = 0.0
        
        for emotion, intensity in self.basic_emotions.items():
            if intensity > 0 and emotion in emotion_mappings:
                valence, arousal, dominance = emotion_mappings[emotion]
                weight = intensity
                
                total_valence += valence * weight
                total_arousal += arousal * weight
                total_dominance += dominance * weight
                total_weight += weight
                
        if total_weight > 0:
            self.valence = total_valence / total_weight
            self.arousal = total_arousal / total_weight
            self.dominance = total_dominance / total_weight
            
        self._normalize_values()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert emotional state to dictionary."""
        return {
            "basic_emotions": {emotion.value: intensity for emotion, intensity in self.basic_emotions.items()},
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "intensity": self.intensity,
            "stability": self.stability,
            "timestamp": self.timestamp.isoformat(),
            "duration": str(self.duration) if self.duration else None,
            "triggers": self.triggers,
            "metadata": self.metadata,
            "mood_label": self.get_mood_label()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalState":
        """Create emotional state from dictionary."""
        basic_emotions = {
            BasicEmotion(emotion): intensity 
            for emotion, intensity in data.get("basic_emotions", {}).items()
        }
        
        duration = None
        if data.get("duration"):
            # Parse duration string if present
            duration_str = data["duration"]
            # Simple parsing - this could be more sophisticated
            if ":" in duration_str:
                parts = duration_str.split(":")
                if len(parts) == 3:
                    hours, minutes, seconds = map(float, parts)
                    duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    
        return cls(
            basic_emotions=basic_emotions,
            valence=data.get("valence", 0.0),
            arousal=data.get("arousal", 0.0),
            dominance=data.get("dominance", 0.0),
            intensity=data.get("intensity", 0.5),
            stability=data.get("stability", 0.5),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            duration=duration,
            triggers=data.get("triggers", []),
            metadata=data.get("metadata", {})
        )


class EmotionModel:
    """
    Model for managing emotional states and transitions.
    """
    
    def __init__(self, baseline_state: Optional[EmotionalState] = None):
        self.baseline_state = baseline_state or self._create_neutral_state()
        self.current_state = self.baseline_state
        self._state_history: List[EmotionalState] = []
        self._transition_rules: List[Dict[str, Any]] = []
        
        # Emotional parameters
        self.emotional_sensitivity = 0.5  # How readily emotions change
        self.decay_rate = 0.1  # How quickly emotions return to baseline
        self.stability_factor = 0.7  # How stable emotions are
        
    def set_current_state(self, state: EmotionalState) -> None:
        """Set the current emotional state."""
        # Record previous state in history
        if self.current_state:
            self._state_history.append(self.current_state)
            
        self.current_state = state
        
        # Keep history manageable
        if len(self._state_history) > 20:
            self._state_history = self._state_history[-10:]
            
    def update_emotion(
        self, 
        trigger: str, 
        emotion_changes: Dict[BasicEmotion, float],
        intensity_multiplier: float = 1.0
    ) -> EmotionalState:
        """
        Update emotions based on a trigger event.
        
        Args:
            trigger: Description of what caused the emotion change
            emotion_changes: Dictionary of emotion changes to apply
            intensity_multiplier: Global multiplier for emotion changes
            
        Returns:
            New emotional state
        """
        # Create new state based on current
        new_emotions = self.current_state.basic_emotions.copy()
        
        # Apply changes with sensitivity and multiplier
        for emotion, change in emotion_changes.items():
            current_intensity = new_emotions.get(emotion, 0.0)
            adjusted_change = change * self.emotional_sensitivity * intensity_multiplier
            
            # Apply change
            new_intensity = current_intensity + adjusted_change
            new_emotions[emotion] = max(0.0, min(1.0, new_intensity))
            
        # Create new state
        new_state = EmotionalState(
            basic_emotions=new_emotions,
            intensity=min(1.0, self.current_state.intensity + 0.1 * intensity_multiplier),
            stability=max(0.1, self.current_state.stability - 0.1 * abs(intensity_multiplier)),
            triggers=[trigger]
        )
        
        self.set_current_state(new_state)
        return new_state
        
    def apply_decay(self) -> EmotionalState:
        """Apply emotional decay toward baseline."""
        # Blend current state with baseline
        decay_strength = self.decay_rate * (1.0 - self.current_state.stability)
        decayed_state = self.current_state.blend_with(self.baseline_state, decay_strength)
        
        # Increase stability as we approach baseline
        decayed_state.stability = min(1.0, decayed_state.stability + 0.05)
        
        self.set_current_state(decayed_state)
        return decayed_state
        
    def get_emotional_trajectory(self, lookback_steps: int = 5) -> List[EmotionalState]:
        """Get recent emotional history."""
        history = self._state_history[-lookback_steps:] if self._state_history else []
        if self.current_state:
            history.append(self.current_state)
        return history
        
    def analyze_emotional_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in emotional history."""
        if len(self._state_history) < 3:
            return {"message": "Not enough emotional history for analysis"}
            
        # Calculate average emotional intensities
        emotion_averages = {emotion: [] for emotion in BasicEmotion}
        
        for state in self._state_history:
            for emotion, intensity in state.basic_emotions.items():
                emotion_averages[emotion].append(intensity)
                
        avg_intensities = {
            emotion.value: sum(intensities) / len(intensities)
            for emotion, intensities in emotion_averages.items()
            if intensities
        }
        
        # Find most volatile emotions
        emotion_volatility = {}
        for emotion, intensities in emotion_averages.items():
            if len(intensities) > 1:
                variance = sum((x - sum(intensities)/len(intensities))**2 for x in intensities) / len(intensities)
                emotion_volatility[emotion.value] = variance
                
        # Overall emotional stability
        stability_scores = [state.stability for state in self._state_history]
        avg_stability = sum(stability_scores) / len(stability_scores)
        
        return {
            "average_emotions": avg_intensities,
            "emotion_volatility": emotion_volatility,
            "average_stability": avg_stability,
            "dominant_emotions": sorted(avg_intensities.items(), key=lambda x: x[1], reverse=True)[:3],
            "most_volatile_emotions": sorted(emotion_volatility.items(), key=lambda x: x[1], reverse=True)[:3]
        }
        
    def _create_neutral_state(self) -> EmotionalState:
        """Create a neutral baseline emotional state."""
        return EmotionalState(
            basic_emotions={emotion: 0.0 for emotion in BasicEmotion},
            valence=0.0,
            arousal=0.0,
            dominance=0.0,
            intensity=0.2,
            stability=0.8
        )