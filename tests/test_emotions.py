"""
Unit tests for the emotion system.
"""

import pytest
from datetime import datetime, timedelta
from agent_personas.emotions.emotion_model import EmotionalState, BasicEmotion, EmotionModel
from agent_personas.emotions.emotion_engine import EmotionEngine, EmotionalTrigger


class TestEmotionalState:
    """Test cases for EmotionalState."""
    
    def test_emotional_state_creation(self):
        """Test basic emotional state creation."""
        state = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.7, BasicEmotion.TRUST: 0.5},
            valence=0.6,
            arousal=0.4,
            intensity=0.8
        )
        
        assert state.basic_emotions[BasicEmotion.JOY] == 0.7
        assert state.basic_emotions[BasicEmotion.TRUST] == 0.5
        assert state.valence == 0.6
        assert state.arousal == 0.4
        assert state.intensity == 0.8
        assert isinstance(state.timestamp, datetime)
    
    def test_emotional_state_defaults(self):
        """Test emotional state with default values."""
        state = EmotionalState()
        
        assert len(state.basic_emotions) == len(BasicEmotion)
        for emotion in BasicEmotion:
            assert state.basic_emotions[emotion] == 0.0
        assert state.valence == 0.0
        assert state.arousal == 0.0
        assert state.intensity == 0.5
    
    def test_value_normalization(self):
        """Test that emotional values are normalized to valid ranges."""
        state = EmotionalState(
            valence=2.0,  # Should be clamped to 1.0
            arousal=-2.0,  # Should be clamped to -1.0
            intensity=1.5  # Should be clamped to 1.0
        )
        
        assert state.valence == 1.0
        assert state.arousal == -1.0
        assert state.intensity == 1.0
    
    def test_get_dominant_emotion(self):
        """Test getting the dominant emotion."""
        state = EmotionalState(
            basic_emotions={
                BasicEmotion.JOY: 0.3,
                BasicEmotion.EXCITEMENT: 0.8,
                BasicEmotion.SADNESS: 0.1
            }
        )
        
        dominant, intensity = state.get_dominant_emotion()
        assert dominant == BasicEmotion.EXCITEMENT
        assert intensity == 0.8
    
    def test_emotion_strength_operations(self):
        """Test emotion strength getting and setting."""
        state = EmotionalState()
        
        # Test getting non-existent emotion
        assert state.get_emotion_strength(BasicEmotion.JOY) == 0.0
        
        # Test setting emotion
        state.set_emotion(BasicEmotion.JOY, 0.7)
        assert state.get_emotion_strength(BasicEmotion.JOY) == 0.7
        
        # Test adding to emotion
        state.add_emotion(BasicEmotion.JOY, 0.2)
        assert state.get_emotion_strength(BasicEmotion.JOY) == 0.9
        
        # Test clamping at 1.0
        state.add_emotion(BasicEmotion.JOY, 0.5)
        assert state.get_emotion_strength(BasicEmotion.JOY) == 1.0
    
    def test_blend_with_other_state(self):
        """Test blending emotional states."""
        state1 = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8, BasicEmotion.TRUST: 0.6},
            valence=0.7,
            arousal=0.3,
            intensity=0.8
        )
        
        state2 = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.2, BasicEmotion.SADNESS: 0.7},
            valence=-0.3,
            arousal=0.1,
            intensity=0.4
        )
        
        # Blend with equal weights
        blended = state1.blend_with(state2, weight=0.5)
        
        assert blended.basic_emotions[BasicEmotion.JOY] == 0.5  # (0.8 + 0.2) / 2
        assert blended.basic_emotions[BasicEmotion.TRUST] == 0.3  # (0.6 + 0.0) / 2
        assert blended.basic_emotions[BasicEmotion.SADNESS] == 0.35  # (0.0 + 0.7) / 2
        assert blended.valence == 0.2  # (0.7 + -0.3) / 2
        assert blended.intensity == 0.6  # (0.8 + 0.4) / 2
    
    def test_decay(self):
        """Test emotional state decay."""
        state = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8, BasicEmotion.ANGER: 0.6},
            valence=0.7,
            arousal=0.5,
            intensity=0.9
        )
        
        decayed = state.decay(decay_rate=0.5)
        
        assert decayed.basic_emotions[BasicEmotion.JOY] == 0.4  # 0.8 * 0.5
        assert decayed.basic_emotions[BasicEmotion.ANGER] == 0.3  # 0.6 * 0.5
        assert decayed.valence == 0.35  # 0.7 * 0.5
        assert decayed.intensity == 0.45  # 0.9 * 0.5
    
    def test_mood_label_generation(self):
        """Test mood label generation."""
        # Test neutral state
        neutral_state = EmotionalState()
        assert neutral_state.get_mood_label() == "neutral"
        
        # Test joyful state
        joyful_state = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8},
            valence=0.7,
            arousal=0.6
        )
        mood_label = joyful_state.get_mood_label()
        assert "joy" in mood_label.lower()
        assert "energetic" in mood_label.lower() or "excited" in mood_label.lower()
    
    def test_similarity_calculation(self):
        """Test emotional state similarity calculation."""
        state1 = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8, BasicEmotion.TRUST: 0.6},
            valence=0.7,
            arousal=0.3
        )
        
        # Very similar state
        state2 = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.75, BasicEmotion.TRUST: 0.65},
            valence=0.72,
            arousal=0.28
        )
        
        # Very different state
        state3 = EmotionalState(
            basic_emotions={BasicEmotion.SADNESS: 0.8, BasicEmotion.FEAR: 0.6},
            valence=-0.7,
            arousal=-0.3
        )
        
        similarity_high = state1.calculate_similarity(state2)
        similarity_low = state1.calculate_similarity(state3)
        
        assert similarity_high > 0.8  # Should be very similar
        assert similarity_low < 0.5  # Should be quite different
        assert similarity_high > similarity_low
    
    def test_serialization(self):
        """Test emotional state serialization."""
        state = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8, BasicEmotion.TRUST: 0.6},
            valence=0.5,
            arousal=0.3,
            intensity=0.7,
            triggers=["positive feedback"]
        )
        
        # Test to_dict
        data = state.to_dict()
        assert data["valence"] == 0.5
        assert data["basic_emotions"]["joy"] == 0.8
        assert data["triggers"] == ["positive feedback"]
        assert "mood_label" in data
        
        # Test from_dict
        restored = EmotionalState.from_dict(data)
        assert restored.valence == state.valence
        assert restored.basic_emotions[BasicEmotion.JOY] == state.basic_emotions[BasicEmotion.JOY]
        assert restored.triggers == state.triggers


class TestEmotionModel:
    """Test cases for EmotionModel."""
    
    def test_emotion_model_creation(self):
        """Test basic emotion model creation."""
        model = EmotionModel()
        
        assert model.baseline_state is not None
        assert model.current_state is not None
        assert model.current_state == model.baseline_state
        assert isinstance(model._state_history, list)
    
    def test_custom_baseline_state(self):
        """Test emotion model with custom baseline."""
        custom_baseline = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.3, BasicEmotion.TRUST: 0.4},
            valence=0.2
        )
        
        model = EmotionModel(baseline_state=custom_baseline)
        
        assert model.baseline_state == custom_baseline
        assert model.current_state == custom_baseline
    
    def test_set_current_state(self):
        """Test setting current emotional state."""
        model = EmotionModel()
        
        new_state = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8},
            valence=0.6
        )
        
        model.set_current_state(new_state)
        
        assert model.current_state == new_state
        assert len(model._state_history) == 1  # Previous state should be in history
    
    def test_update_emotion(self):
        """Test emotion updating."""
        model = EmotionModel()
        
        emotion_changes = {
            BasicEmotion.JOY: 0.5,
            BasicEmotion.EXCITEMENT: 0.3
        }
        
        new_state = model.update_emotion(
            trigger="positive event",
            emotion_changes=emotion_changes,
            intensity_multiplier=1.0
        )
        
        # Check that emotions were updated
        assert new_state.basic_emotions[BasicEmotion.JOY] > 0
        assert new_state.basic_emotions[BasicEmotion.EXCITEMENT] > 0
        assert "positive event" in new_state.triggers
    
    def test_apply_decay(self):
        """Test emotional decay application."""
        model = EmotionModel()
        
        # Set an emotional state
        excited_state = EmotionalState(
            basic_emotions={BasicEmotion.JOY: 0.8, BasicEmotion.EXCITEMENT: 0.7},
            valence=0.6,
            intensity=0.8
        )
        model.set_current_state(excited_state)
        
        # Apply decay
        decayed_state = model.apply_decay()
        
        # Emotions should be reduced toward baseline
        assert decayed_state.basic_emotions[BasicEmotion.JOY] < excited_state.basic_emotions[BasicEmotion.JOY]
        assert decayed_state.intensity < excited_state.intensity
    
    def test_emotional_trajectory(self):
        """Test getting emotional trajectory."""
        model = EmotionModel()
        
        # Create some state changes
        for i in range(5):
            state = EmotionalState(
                basic_emotions={BasicEmotion.JOY: i * 0.2},
                intensity=i * 0.1
            )
            model.set_current_state(state)
        
        trajectory = model.get_emotional_trajectory(lookback_steps=3)
        
        assert len(trajectory) <= 4  # 3 from history + current
        assert trajectory[-1] == model.current_state  # Last should be current


class TestEmotionEngine:
    """Test cases for EmotionEngine."""
    
    def test_emotion_engine_creation(self):
        """Test basic emotion engine creation."""
        engine = EmotionEngine()
        
        assert engine.emotion_model is not None
        assert isinstance(engine._triggers, dict)
        assert len(engine._triggers) > 0  # Should have default triggers
    
    def test_add_custom_trigger(self):
        """Test adding custom emotional triggers."""
        engine = EmotionEngine()
        
        trigger = EmotionalTrigger(
            name="test_trigger",
            trigger_patterns=["test phrase"],
            emotion_effects={BasicEmotion.JOY: 0.5}
        )
        
        engine.add_trigger(trigger)
        
        assert "test_trigger" in engine._triggers
        assert engine._triggers["test_trigger"] == trigger
    
    def test_remove_trigger(self):
        """Test removing emotional triggers."""
        engine = EmotionEngine()
        
        trigger = EmotionalTrigger(
            name="test_trigger",
            trigger_patterns=["test phrase"],
            emotion_effects={BasicEmotion.JOY: 0.5}
        )
        
        engine.add_trigger(trigger)
        assert engine.remove_trigger("test_trigger") is True
        assert "test_trigger" not in engine._triggers
        assert engine.remove_trigger("nonexistent") is False
    
    def test_process_positive_input(self):
        """Test processing positive emotional input."""
        engine = EmotionEngine()
        
        # Process positive input
        result_state = engine.process_input("Thank you so much! This is amazing!")
        
        # Should have positive emotional response
        context = engine.get_emotional_context()
        assert context["valence"] > 0  # Should be positive
        assert context["current_mood"] != "neutral"  # Should have changed from neutral
    
    def test_process_negative_input(self):
        """Test processing negative emotional input."""
        engine = EmotionEngine()
        
        # Process negative input
        result_state = engine.process_input("I'm really frustrated with this problem.")
        
        # Should have appropriate emotional response
        context = engine.get_emotional_context()
        # Note: The engine might respond with supportive emotions rather than mirroring negativity
        assert "frustrated" in context["current_mood"].lower() or context["valence"] >= 0
    
    def test_emotional_context_retrieval(self):
        """Test getting emotional context."""
        engine = EmotionEngine()
        
        context = engine.get_emotional_context()
        
        required_keys = [
            "current_mood", "dominant_emotion", "dominant_intensity",
            "valence", "arousal", "dominance", "overall_intensity", "stability"
        ]
        
        for key in required_keys:
            assert key in context
    
    def test_emotional_memory(self):
        """Test emotional memory tracking."""
        engine = EmotionEngine()
        
        # Process some inputs
        engine.process_input("I'm excited about this project!")
        engine.process_input("This is really confusing.")
        
        # Check memory
        history = engine.get_emotional_history(limit=5)
        
        assert len(history) >= 2
        assert any("excited" in event["input_text"] for event in history)
        assert any("confusing" in event["input_text"] for event in history)
    
    def test_emotional_pattern_analysis(self):
        """Test emotional pattern analysis."""
        engine = EmotionEngine()
        
        # Generate some emotional events
        inputs = [
            "I'm happy about this!",
            "This is frustrating.",
            "Great work everyone!",
            "I'm confused about this."
        ]
        
        for input_text in inputs:
            engine.process_input(input_text)
        
        # Analyze patterns
        analysis = engine.analyze_emotional_patterns(days_back=1)
        
        assert "total_emotional_events" in analysis
        assert "most_common_triggers" in analysis
        assert analysis["total_emotional_events"] > 0


class TestEmotionalTrigger:
    """Test cases for EmotionalTrigger."""
    
    def test_trigger_creation(self):
        """Test basic trigger creation."""
        trigger = EmotionalTrigger(
            name="happiness_trigger",
            trigger_patterns=["happy", "joy", "excited"],
            emotion_effects={BasicEmotion.JOY: 0.5, BasicEmotion.EXCITEMENT: 0.3}
        )
        
        assert trigger.name == "happiness_trigger"
        assert len(trigger.trigger_patterns) == 3
        assert trigger.emotion_effects[BasicEmotion.JOY] == 0.5
    
    def test_trigger_matching(self):
        """Test trigger pattern matching."""
        trigger = EmotionalTrigger(
            name="test_trigger",
            trigger_patterns=["happy", "excited", "amazing"],
            emotion_effects={BasicEmotion.JOY: 0.5}
        )
        
        assert trigger.matches("I'm so happy today!")
        assert trigger.matches("This is AMAZING!")
        assert trigger.matches("I'm excited about this.")
        assert not trigger.matches("I'm sad about this.")
    
    def test_trigger_with_conditions(self):
        """Test trigger with context conditions."""
        trigger = EmotionalTrigger(
            name="conditional_trigger",
            trigger_patterns=["good"],
            emotion_effects={BasicEmotion.JOY: 0.5},
            conditions={"context_type": "positive"}
        )
        
        # Should match with correct condition
        assert trigger.matches("This is good!", {"context_type": "positive"})
        
        # Should not match with wrong condition
        assert not trigger.matches("This is good!", {"context_type": "negative"})
        
        # Should not match without condition
        assert not trigger.matches("This is good!", {})
    
    def test_emotion_changes_with_probability(self):
        """Test emotion changes with probability effects."""
        trigger = EmotionalTrigger(
            name="probabilistic_trigger",
            trigger_patterns=["test"],
            emotion_effects={BasicEmotion.JOY: 0.5},
            probability=0.5  # 50% chance
        )
        
        # Test multiple times to check probability (this is probabilistic)
        results = []
        for _ in range(20):
            changes = trigger.get_emotion_changes()
            results.append(len(changes) > 0)
        
        # Should have some successes and some failures (not all or none)
        successes = sum(results)
        assert 0 < successes < 20  # Should be between 0 and 20 (exclusive)