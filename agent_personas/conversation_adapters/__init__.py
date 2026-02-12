"""
Advanced Conversation Style Adapters

Sophisticated conversation style adaptation system with context-aware
communication patterns, dynamic style switching, and personalized responses.
"""

from .style_adapter import ConversationStyleAdapter, StyleProfile
from .context_analyzer import ConversationContext, ContextAnalyzer
from .response_generator import ResponseGenerator, ResponseStyle
from .linguistic_patterns import LinguisticPattern, PatternApplier
from .dynamic_style_switcher import DynamicStyleSwitcher, StyleTransition

__all__ = [
    "ConversationStyleAdapter",
    "StyleProfile",
    "ConversationContext", 
    "ContextAnalyzer",
    "ResponseGenerator",
    "ResponseStyle",
    "LinguisticPattern",
    "PatternApplier",
    "DynamicStyleSwitcher",
    "StyleTransition"
]