"""
Conversation style management for adaptive communication.
"""

from .style_manager import ConversationStyleManager, ConversationStyle
from .language_patterns import LanguagePatternEngine
from .dialogue_flow import DialogueFlowManager
from .tone_adapter import ToneAdapter

__all__ = [
    "ConversationStyleManager",
    "ConversationStyle", 
    "LanguagePatternEngine",
    "DialogueFlowManager",
    "ToneAdapter"
]