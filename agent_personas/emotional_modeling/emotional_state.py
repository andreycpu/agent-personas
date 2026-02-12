"""
Advanced emotional state modeling with multi-dimensional emotions.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import math
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EmotionIntensity(Enum):
    """Intensity levels for emotions."""
    MINIMAL = 0.1
    SLIGHT = 0.25
    MODERATE = 0.5
    STRONG = 0.75
    INTENSE = 1.0


class EmotionCategory(Enum):
    """Categories of emotions for organization."""
    PRIMARY = "primary"  # Basic emotions: joy, sadness, anger, fear, etc.
    SECONDARY = "secondary"  # Complex emotions: guilt, pride, shame, etc.
    SOCIAL = "social"  # Social emotions: empathy, compassion, envy, etc.
    COGNITIVE = "cognitive"  # Cognitive emotions: curiosity, confusion, satisfaction, etc.


@dataclass
class Emotion:
    """Represents a single emotion with intensity and metadata."""
    name: str
    intensity: float  # 0.0 to 1.0
    category: EmotionCategory
    valence: float  # -1.0 (negative) to 1.0 (positive)
    arousal: float  # 0.0 (calm) to 1.0 (excited)
    dominance: float  # 0.0 (submissive) to 1.0 (dominant)
    duration_minutes: Optional[float] = None  # How long this emotion typically lasts
    triggers: List[str] = field(default_factory=list)  # What can trigger this emotion
    
    def __post_init__(self):
        """Validate emotion parameters."""
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("Intensity must be between 0.0 and 1.0")
        if not -1.0 <= self.valence <= 1.0:
            raise ValueError("Valence must be between -1.0 and 1.0")
        if not 0.0 <= self.arousal <= 1.0:
            raise ValueError("Arousal must be between 0.0 and 1.0")
        if not 0.0 <= self.dominance <= 1.0:
            raise ValueError("Dominance must be between 0.0 and 1.0")
    
    def get_energy_level(self) -> float:
        """Calculate overall energy level from arousal and intensity."""
        return (self.arousal * self.intensity) ** 0.5
    
    def get_positivity(self) -> float:
        """Calculate positivity score combining valence and intensity."""
        return self.valence * self.intensity
    
    def is_compatible_with(self, other: "Emotion") -> bool:
        """Check if this emotion can coexist with another."""
        # Emotions with opposite valences at high intensity typically conflict
        if (self.valence * other.valence < 0 and 
            self.intensity > 0.6 and other.intensity > 0.6):
            return False
        
        # Very high arousal emotions may conflict with very low arousal
        if abs(self.arousal - other.arousal) > 0.8:
            return False
        
        return True


@dataclass
class EmotionalState:
    """
    Complete emotional state containing multiple concurrent emotions.
    
    Represents a snapshot of emotional experience including primary emotions,
    mood influences, and contextual factors.
    """
    
    emotions: Dict[str, Emotion] = field(default_factory=dict)
    baseline_mood: str = "neutral"
    energy_level: float = 0.5  # 0.0 to 1.0
    emotional_stability: float = 0.7  # 0.0 (very unstable) to 1.0 (very stable)
    social_context: str = "neutral"  # Social situation affecting emotions
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize emotional state."""
        self._validate_parameters()
        self._update_derived_metrics()
    
    def _validate_parameters(self):
        """Validate emotional state parameters."""
        if not 0.0 <= self.energy_level <= 1.0:
            raise ValueError("Energy level must be between 0.0 and 1.0")
        if not 0.0 <= self.emotional_stability <= 1.0:
            raise ValueError("Emotional stability must be between 0.0 and 1.0")
    
    def _update_derived_metrics(self):
        """Update derived metrics from current emotions."""
        if not self.emotions:
            return
        
        # Calculate overall energy from emotions
        emotion_energies = [emotion.get_energy_level() for emotion in self.emotions.values()]
        if emotion_energies:
            # Use weighted average based on intensity
            weights = [emotion.intensity for emotion in self.emotions.values()]
            total_weight = sum(weights)
            if total_weight > 0:
                weighted_energy = sum(e * w for e, w in zip(emotion_energies, weights)) / total_weight
                # Blend with existing energy level
                self.energy_level = (self.energy_level + weighted_energy) / 2
    
    def add_emotion(self, emotion: Emotion) -> bool:
        """
        Add an emotion to the current state.
        
        Returns True if successfully added, False if conflicts prevent addition.
        """
        # Check compatibility with existing emotions
        for existing_emotion in self.emotions.values():
            if not emotion.is_compatible_with(existing_emotion):
                # Try to resolve conflict by reducing intensities
                if emotion.intensity > existing_emotion.intensity:
                    # New emotion is stronger, reduce existing
                    existing_emotion.intensity *= 0.7
                else:
                    # Existing emotion is stronger, reduce new emotion
                    emotion.intensity *= 0.7
                
                logger.debug(f"Resolved emotion conflict between {emotion.name} and {existing_emotion.name}")
        
        self.emotions[emotion.name] = emotion
        self._update_derived_metrics()
        
        logger.debug(f"Added emotion {emotion.name} with intensity {emotion.intensity}")
        return True
    
    def remove_emotion(self, emotion_name: str) -> bool:
        """Remove an emotion from the current state."""
        if emotion_name in self.emotions:
            del self.emotions[emotion_name]
            self._update_derived_metrics()
            logger.debug(f"Removed emotion {emotion_name}")
            return True
        return False
    
    def get_emotion_intensity(self, emotion_name: str) -> float:
        """Get the intensity of a specific emotion."""
        emotion = self.emotions.get(emotion_name)
        return emotion.intensity if emotion else 0.0
    
    def get_dominant_emotion(self) -> Optional[Emotion]:
        """Get the emotion with the highest intensity."""
        if not self.emotions:
            return None
        
        return max(self.emotions.values(), key=lambda e: e.intensity)
    
    def get_emotion_blend(self) -> Dict[str, float]:
        """Get a blend of all current emotions with their intensities."""
        return {name: emotion.intensity for name, emotion in self.emotions.items()}
    
    def calculate_overall_valence(self) -> float:
        """Calculate the overall emotional valence (-1.0 to 1.0)."""
        if not self.emotions:
            return 0.0
        
        weighted_valences = []
        total_weight = 0
        
        for emotion in self.emotions.values():
            weight = emotion.intensity
            weighted_valences.append(emotion.valence * weight)
            total_weight += weight
        
        return sum(weighted_valences) / total_weight if total_weight > 0 else 0.0
    
    def calculate_overall_arousal(self) -> float:
        """Calculate the overall arousal level (0.0 to 1.0)."""
        if not self.emotions:
            return 0.5  # Neutral arousal
        
        weighted_arousals = []
        total_weight = 0
        
        for emotion in self.emotions.values():
            weight = emotion.intensity
            weighted_arousals.append(emotion.arousal * weight)
            total_weight += weight
        
        return sum(weighted_arousals) / total_weight if total_weight > 0 else 0.5
    
    def calculate_emotional_complexity(self) -> float:
        """Calculate how complex the current emotional state is."""
        if len(self.emotions) <= 1:
            return 0.0
        
        # Complexity based on number of emotions and their intensity variance
        intensities = [emotion.intensity for emotion in self.emotions.values()]
        intensity_variance = sum((i - sum(intensities)/len(intensities))**2 for i in intensities) / len(intensities)
        
        # Normalize complexity score
        base_complexity = min(1.0, len(self.emotions) / 5)  # More emotions = more complex
        variance_factor = min(1.0, intensity_variance * 4)  # Higher variance = more complex
        
        return (base_complexity + variance_factor) / 2
    
    def decay_emotions(self, time_delta: timedelta) -> None:
        """Apply natural decay to emotions over time."""
        minutes_passed = time_delta.total_seconds() / 60
        
        emotions_to_remove = []
        
        for emotion_name, emotion in self.emotions.items():
            # Calculate decay rate
            if emotion.duration_minutes:
                # Use emotion-specific duration
                decay_rate = minutes_passed / emotion.duration_minutes
            else:
                # Use default decay based on intensity and arousal
                base_duration = 30  # Base duration in minutes
                actual_duration = base_duration * (1 + emotion.arousal)  # Higher arousal = longer lasting
                decay_rate = minutes_passed / actual_duration
            
            # Apply exponential decay
            new_intensity = emotion.intensity * math.exp(-decay_rate * 0.5)
            
            # Remove very weak emotions
            if new_intensity < 0.05:
                emotions_to_remove.append(emotion_name)
            else:
                emotion.intensity = new_intensity
        
        # Clean up weak emotions
        for emotion_name in emotions_to_remove:
            self.remove_emotion(emotion_name)
        
        # Update timestamp
        self.timestamp = datetime.now()
        self._update_derived_metrics()
    
    def apply_mood_influence(self, mood_adjustment: Dict[str, float]) -> None:
        """Apply mood-based adjustments to current emotions."""
        for emotion_name, adjustment in mood_adjustment.items():
            if emotion_name in self.emotions:
                emotion = self.emotions[emotion_name]
                # Apply adjustment with stability factor
                actual_adjustment = adjustment * (1 - self.emotional_stability * 0.5)
                emotion.intensity = max(0.0, min(1.0, emotion.intensity + actual_adjustment))
    
    def get_emotional_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the emotional state."""
        dominant_emotion = self.get_dominant_emotion()
        
        return {
            "dominant_emotion": dominant_emotion.name if dominant_emotion else None,
            "emotion_count": len(self.emotions),
            "overall_valence": round(self.calculate_overall_valence(), 3),
            "overall_arousal": round(self.calculate_overall_arousal(), 3),
            "energy_level": round(self.energy_level, 3),
            "emotional_complexity": round(self.calculate_emotional_complexity(), 3),
            "emotional_stability": round(self.emotional_stability, 3),
            "baseline_mood": self.baseline_mood,
            "social_context": self.social_context,
            "active_emotions": self.get_emotion_blend(),
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert emotional state to dictionary representation."""
        return {
            "emotions": {
                name: {
                    "name": emotion.name,
                    "intensity": emotion.intensity,
                    "category": emotion.category.value,
                    "valence": emotion.valence,
                    "arousal": emotion.arousal,
                    "dominance": emotion.dominance,
                    "duration_minutes": emotion.duration_minutes,
                    "triggers": emotion.triggers
                }
                for name, emotion in self.emotions.items()
            },
            "baseline_mood": self.baseline_mood,
            "energy_level": self.energy_level,
            "emotional_stability": self.emotional_stability,
            "social_context": self.social_context,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalState":
        """Create emotional state from dictionary representation."""
        emotions = {}
        for name, emotion_data in data.get("emotions", {}).items():
            emotions[name] = Emotion(
                name=emotion_data["name"],
                intensity=emotion_data["intensity"],
                category=EmotionCategory(emotion_data["category"]),
                valence=emotion_data["valence"],
                arousal=emotion_data["arousal"],
                dominance=emotion_data["dominance"],
                duration_minutes=emotion_data.get("duration_minutes"),
                triggers=emotion_data.get("triggers", [])
            )
        
        state = cls(
            emotions=emotions,
            baseline_mood=data.get("baseline_mood", "neutral"),
            energy_level=data.get("energy_level", 0.5),
            emotional_stability=data.get("emotional_stability", 0.7),
            social_context=data.get("social_context", "neutral"),
            metadata=data.get("metadata", {})
        )
        
        if "timestamp" in data:
            state.timestamp = datetime.fromisoformat(data["timestamp"])
        
        return state