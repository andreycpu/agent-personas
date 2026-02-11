"""
Emotion engine for processing emotional triggers and managing state transitions.
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
import re
import random
from datetime import datetime, timedelta

from .emotion_model import EmotionModel, EmotionalState, BasicEmotion


class EmotionalTrigger:
    """Represents a trigger that can cause emotional changes."""
    
    def __init__(
        self,
        name: str,
        trigger_patterns: List[str],
        emotion_effects: Dict[BasicEmotion, float],
        intensity_factor: float = 1.0,
        probability: float = 1.0,
        conditions: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.trigger_patterns = trigger_patterns
        self.emotion_effects = emotion_effects
        self.intensity_factor = intensity_factor
        self.probability = probability
        self.conditions = conditions or {}
        
    def matches(self, text: str, context: Dict[str, Any] = None) -> bool:
        """Check if this trigger matches the given text and context."""
        if context is None:
            context = {}
            
        # Check conditions first
        for key, expected_value in self.conditions.items():
            if context.get(key) != expected_value:
                return False
                
        # Check text patterns
        text_lower = text.lower()
        return any(
            pattern.lower() in text_lower 
            for pattern in self.trigger_patterns
        )
        
    def get_emotion_changes(self, intensity_multiplier: float = 1.0) -> Dict[BasicEmotion, float]:
        """Get the emotion changes this trigger would cause."""
        if random.random() > self.probability:
            return {}
            
        total_multiplier = self.intensity_factor * intensity_multiplier
        return {
            emotion: effect * total_multiplier
            for emotion, effect in self.emotion_effects.items()
        }


class EmotionEngine:
    """
    Engine for processing emotional triggers and managing emotional states.
    """
    
    def __init__(self, emotion_model: Optional[EmotionModel] = None):
        self.emotion_model = emotion_model or EmotionModel()
        self._triggers: Dict[str, EmotionalTrigger] = {}
        self._processors: List[Callable[[str, Dict[str, Any]], Dict[BasicEmotion, float]]] = []
        self._emotional_memory: List[Dict[str, Any]] = []
        
        # Engine settings
        self.auto_decay_interval = timedelta(minutes=5)
        self.last_decay_time = datetime.now()
        self.memory_decay_rate = 0.05
        
        # Load default triggers
        self._load_default_triggers()
        
    def add_trigger(self, trigger: EmotionalTrigger) -> None:
        """Add an emotional trigger."""
        self._triggers[trigger.name] = trigger
        
    def remove_trigger(self, name: str) -> bool:
        """Remove an emotional trigger."""
        if name in self._triggers:
            del self._triggers[name]
            return True
        return False
        
    def add_processor(self, processor: Callable[[str, Dict[str, Any]], Dict[BasicEmotion, float]]) -> None:
        """Add a custom emotion processor function."""
        self._processors.append(processor)
        
    def process_input(
        self, 
        text: str, 
        context: Dict[str, Any] = None,
        user_emotion: Optional[str] = None
    ) -> EmotionalState:
        """
        Process text input and update emotional state.
        
        Args:
            text: Input text to process
            context: Additional context information
            user_emotion: Detected emotion from user (if any)
            
        Returns:
            Updated emotional state
        """
        if context is None:
            context = {}
            
        # Apply automatic decay if enough time has passed
        self._apply_auto_decay()
        
        # Collect all emotion changes
        all_emotion_changes = {}
        triggered_events = []
        
        # Process triggers
        for trigger in self._triggers.values():
            if trigger.matches(text, context):
                emotion_changes = trigger.get_emotion_changes()
                if emotion_changes:
                    triggered_events.append(trigger.name)
                    self._merge_emotion_changes(all_emotion_changes, emotion_changes)
                    
        # Process with custom processors
        for processor in self._processors:
            try:
                emotion_changes = processor(text, context)
                if emotion_changes:
                    self._merge_emotion_changes(all_emotion_changes, emotion_changes)
            except Exception as e:
                # Log error but don't break processing
                print(f"Error in emotion processor: {e}")
                
        # Process user emotion if provided
        if user_emotion:
            user_emotion_changes = self._process_user_emotion(user_emotion, context)
            self._merge_emotion_changes(all_emotion_changes, user_emotion_changes)
            
        # Apply emotion changes if any were detected
        if all_emotion_changes:
            trigger_description = f"Input processing: {', '.join(triggered_events) if triggered_events else 'custom processors'}"
            new_state = self.emotion_model.update_emotion(
                trigger=trigger_description,
                emotion_changes=all_emotion_changes
            )
            
            # Record in emotional memory
            self._record_emotional_event(text, triggered_events, all_emotion_changes, new_state)
        else:
            new_state = self.emotion_model.current_state
            
        return new_state
        
    def _merge_emotion_changes(
        self, 
        target: Dict[BasicEmotion, float], 
        source: Dict[BasicEmotion, float]
    ) -> None:
        """Merge emotion changes, combining effects."""
        for emotion, change in source.items():
            if emotion in target:
                # Combine changes (but cap at reasonable values)
                combined = target[emotion] + change
                target[emotion] = max(-1.0, min(1.0, combined))
            else:
                target[emotion] = change
                
    def _process_user_emotion(self, user_emotion: str, context: Dict[str, Any]) -> Dict[BasicEmotion, float]:
        """Process detected user emotion and generate appropriate response emotions."""
        user_emotion_lower = user_emotion.lower()
        
        # Empathetic responses - mirror some emotions, respond appropriately to others
        empathy_responses = {
            "happy": {BasicEmotion.JOY: 0.4, BasicEmotion.TRUST: 0.2},
            "joy": {BasicEmotion.JOY: 0.5, BasicEmotion.TRUST: 0.3},
            "excited": {BasicEmotion.JOY: 0.3, BasicEmotion.ANTICIPATION: 0.4},
            "sad": {BasicEmotion.SADNESS: 0.2, BasicEmotion.TRUST: 0.4},  # Mild sadness, high trust/support
            "angry": {BasicEmotion.TRUST: 0.5, BasicEmotion.JOY: -0.2},  # Supportive, less joyful
            "frustrated": {BasicEmotion.TRUST: 0.4, BasicEmotion.ANTICIPATION: 0.2},
            "worried": {BasicEmotion.TRUST: 0.6, BasicEmotion.FEAR: -0.1},  # Reassuring
            "anxious": {BasicEmotion.TRUST: 0.5, BasicEmotion.FEAR: -0.2},
            "confused": {BasicEmotion.TRUST: 0.3, BasicEmotion.ANTICIPATION: 0.3},
            "grateful": {BasicEmotion.JOY: 0.3, BasicEmotion.TRUST: 0.4},
            "disappointed": {BasicEmotion.TRUST: 0.4, BasicEmotion.SADNESS: 0.1}
        }
        
        # Check for direct matches
        for emotion_key, response in empathy_responses.items():
            if emotion_key in user_emotion_lower:
                return response
                
        # Default neutral empathetic response
        return {BasicEmotion.TRUST: 0.2}
        
    def _apply_auto_decay(self) -> None:
        """Apply emotional decay if enough time has passed."""
        now = datetime.now()
        if now - self.last_decay_time >= self.auto_decay_interval:
            self.emotion_model.apply_decay()
            self.last_decay_time = now
            
    def _record_emotional_event(
        self, 
        text: str, 
        triggers: List[str], 
        changes: Dict[BasicEmotion, float],
        resulting_state: EmotionalState
    ) -> None:
        """Record an emotional event in memory."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "input_text": text[:100],  # Truncate for memory efficiency
            "triggered_by": triggers,
            "emotion_changes": {emotion.value: change for emotion, change in changes.items()},
            "resulting_mood": resulting_state.get_mood_label(),
            "valence": resulting_state.valence,
            "arousal": resulting_state.arousal,
            "intensity": resulting_state.intensity
        }
        
        self._emotional_memory.append(event)
        
        # Keep memory size manageable
        if len(self._emotional_memory) > 100:
            self._emotional_memory = self._emotional_memory[-50:]
            
    def get_emotional_context(self) -> Dict[str, Any]:
        """Get current emotional context for other systems."""
        current_state = self.emotion_model.current_state
        dominant_emotion, dominant_intensity = current_state.get_dominant_emotion()
        
        return {
            "current_mood": current_state.get_mood_label(),
            "dominant_emotion": dominant_emotion.value,
            "dominant_intensity": dominant_intensity,
            "valence": current_state.valence,
            "arousal": current_state.arousal,
            "dominance": current_state.dominance,
            "overall_intensity": current_state.intensity,
            "stability": current_state.stability,
            "recent_triggers": current_state.triggers
        }
        
    def get_emotional_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emotional history."""
        return self._emotional_memory[-limit:] if self._emotional_memory else []
        
    def analyze_emotional_patterns(self, days_back: int = 7) -> Dict[str, Any]:
        """Analyze emotional patterns over time."""
        # Filter recent events
        cutoff_time = datetime.now() - timedelta(days=days_back)
        recent_events = [
            event for event in self._emotional_memory
            if datetime.fromisoformat(event["timestamp"]) > cutoff_time
        ]
        
        if not recent_events:
            return {"message": "No recent emotional events to analyze"}
            
        # Analyze trigger frequencies
        trigger_counts = {}
        for event in recent_events:
            for trigger in event["triggered_by"]:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
                
        # Analyze emotion trends
        valence_trend = [event["valence"] for event in recent_events]
        arousal_trend = [event["arousal"] for event in recent_events]
        intensity_trend = [event["intensity"] for event in recent_events]
        
        # Calculate averages and trends
        avg_valence = sum(valence_trend) / len(valence_trend)
        avg_arousal = sum(arousal_trend) / len(arousal_trend)
        avg_intensity = sum(intensity_trend) / len(intensity_trend)
        
        # Simple trend calculation (difference between first and last half)
        mid_point = len(recent_events) // 2
        if mid_point > 0:
            early_valence = sum(valence_trend[:mid_point]) / mid_point
            late_valence = sum(valence_trend[mid_point:]) / (len(valence_trend) - mid_point)
            valence_direction = "improving" if late_valence > early_valence else "declining" if late_valence < early_valence else "stable"
        else:
            valence_direction = "stable"
            
        return {
            "period_analyzed": f"{days_back} days",
            "total_emotional_events": len(recent_events),
            "most_common_triggers": sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "average_valence": avg_valence,
            "average_arousal": avg_arousal,
            "average_intensity": avg_intensity,
            "valence_trend": valence_direction,
            "emotional_volatility": self._calculate_emotional_volatility(recent_events)
        }
        
    def _calculate_emotional_volatility(self, events: List[Dict[str, Any]]) -> float:
        """Calculate emotional volatility from event history."""
        if len(events) < 2:
            return 0.0
            
        # Calculate variance in valence changes
        valence_changes = []
        for i in range(1, len(events)):
            change = events[i]["valence"] - events[i-1]["valence"]
            valence_changes.append(abs(change))
            
        return sum(valence_changes) / len(valence_changes) if valence_changes else 0.0
        
    def simulate_emotional_response(
        self, 
        text: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Simulate emotional response without actually changing state.
        
        Args:
            text: Input text to simulate response for
            context: Additional context
            
        Returns:
            Simulation results
        """
        if context is None:
            context = {}
            
        # Save current state
        original_state = self.emotion_model.current_state
        
        # Process input
        simulated_state = self.process_input(text, context)
        
        # Calculate differences
        emotion_diffs = {}
        for emotion in BasicEmotion:
            original_intensity = original_state.basic_emotions.get(emotion, 0.0)
            simulated_intensity = simulated_state.basic_emotions.get(emotion, 0.0)
            diff = simulated_intensity - original_intensity
            if abs(diff) > 0.01:  # Only report significant changes
                emotion_diffs[emotion.value] = diff
                
        # Restore original state
        self.emotion_model.current_state = original_state
        
        return {
            "original_mood": original_state.get_mood_label(),
            "simulated_mood": simulated_state.get_mood_label(),
            "emotion_changes": emotion_diffs,
            "valence_change": simulated_state.valence - original_state.valence,
            "arousal_change": simulated_state.arousal - original_state.arousal,
            "intensity_change": simulated_state.intensity - original_state.intensity,
            "would_be_triggered": len(emotion_diffs) > 0
        }
        
    def reset_emotional_state(self, new_baseline: Optional[EmotionalState] = None) -> None:
        """Reset emotional state to baseline or new state."""
        if new_baseline:
            self.emotion_model.baseline_state = new_baseline
            self.emotion_model.current_state = new_baseline
        else:
            self.emotion_model.current_state = self.emotion_model.baseline_state
            
        self._emotional_memory.clear()
        
    def _load_default_triggers(self) -> None:
        """Load default emotional triggers."""
        
        # Positive triggers
        positive_triggers = [
            EmotionalTrigger(
                name="compliments",
                trigger_patterns=["great job", "well done", "excellent", "amazing work", "fantastic"],
                emotion_effects={BasicEmotion.JOY: 0.3, BasicEmotion.TRUST: 0.2}
            ),
            
            EmotionalTrigger(
                name="gratitude",
                trigger_patterns=["thank you", "thanks", "grateful", "appreciate"],
                emotion_effects={BasicEmotion.JOY: 0.2, BasicEmotion.TRUST: 0.3}
            ),
            
            EmotionalTrigger(
                name="excitement",
                trigger_patterns=["excited", "can't wait", "looking forward", "thrilled"],
                emotion_effects={BasicEmotion.JOY: 0.4, BasicEmotion.ANTICIPATION: 0.3}
            )
        ]
        
        # Negative triggers
        negative_triggers = [
            EmotionalTrigger(
                name="criticism",
                trigger_patterns=["terrible", "awful", "horrible", "worst", "hate this"],
                emotion_effects={BasicEmotion.SADNESS: 0.3, BasicEmotion.ANGER: 0.2}
            ),
            
            EmotionalTrigger(
                name="frustration",
                trigger_patterns=["frustrated", "annoyed", "irritated", "fed up"],
                emotion_effects={BasicEmotion.ANGER: 0.4, BasicEmotion.SADNESS: 0.1}
            ),
            
            EmotionalTrigger(
                name="concern",
                trigger_patterns=["worried", "concerned", "anxious", "scared"],
                emotion_effects={BasicEmotion.FEAR: 0.3, BasicEmotion.SADNESS: 0.2}
            )
        ]
        
        # Social triggers
        social_triggers = [
            EmotionalTrigger(
                name="welcome",
                trigger_patterns=["hello", "hi", "good morning", "good evening"],
                emotion_effects={BasicEmotion.JOY: 0.1, BasicEmotion.TRUST: 0.2}
            ),
            
            EmotionalTrigger(
                name="farewell",
                trigger_patterns=["goodbye", "bye", "see you later", "take care"],
                emotion_effects={BasicEmotion.SADNESS: 0.1, BasicEmotion.TRUST: 0.1}
            )
        ]
        
        # Add all triggers
        all_triggers = positive_triggers + negative_triggers + social_triggers
        for trigger in all_triggers:
            self.add_trigger(trigger)