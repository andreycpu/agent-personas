"""
Advanced Emotional Modeling Module

Comprehensive emotional state modeling with dynamic transitions, 
emotional intelligence, and sophisticated mood management.
"""

from .emotional_state import EmotionalState, EmotionIntensity
from .emotion_engine import AdvancedEmotionEngine, EmotionTrigger
from .mood_system import MoodSystem, MoodState, MoodTransition
from .emotional_memory import EmotionalMemory, EmotionalEvent
from .sentiment_analyzer import SentimentAnalyzer, EmotionalContext

__all__ = [
    "EmotionalState",
    "EmotionIntensity",
    "AdvancedEmotionEngine",
    "EmotionTrigger", 
    "MoodSystem",
    "MoodState",
    "MoodTransition",
    "EmotionalMemory",
    "EmotionalEvent",
    "SentimentAnalyzer",
    "EmotionalContext"
]