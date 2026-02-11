"""
Response pattern management for conversation styles.
"""

from typing import Dict, List, Any, Optional, Callable, Pattern
import re
import random
from dataclasses import dataclass, field
from enum import Enum


class PatternType(Enum):
    """Types of response patterns."""
    PREFIX = "prefix"
    SUFFIX = "suffix"
    WRAPPER = "wrapper"
    REPLACEMENT = "replacement"
    ENHANCEMENT = "enhancement"
    FILTER = "filter"


@dataclass
class ResponsePattern:
    """
    Represents a response modification pattern.
    """
    name: str
    pattern_type: PatternType
    description: str = ""
    
    # Pattern-specific data
    text_patterns: List[str] = field(default_factory=list)
    replacements: Dict[str, str] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Configuration
    probability: float = 1.0  # Chance of applying (0.0-1.0)
    priority: int = 0
    enabled: bool = True
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def apply(self, response: str, context: Dict[str, Any]) -> str:
        """
        Apply this pattern to a response.
        
        Args:
            response: Original response text
            context: Current context
            
        Returns:
            Modified response
        """
        if not self.enabled or random.random() > self.probability:
            return response
            
        if not self._check_conditions(context):
            return response
            
        if self.pattern_type == PatternType.PREFIX:
            return self._apply_prefix(response, context)
        elif self.pattern_type == PatternType.SUFFIX:
            return self._apply_suffix(response, context)
        elif self.pattern_type == PatternType.WRAPPER:
            return self._apply_wrapper(response, context)
        elif self.pattern_type == PatternType.REPLACEMENT:
            return self._apply_replacement(response, context)
        elif self.pattern_type == PatternType.ENHANCEMENT:
            return self._apply_enhancement(response, context)
        elif self.pattern_type == PatternType.FILTER:
            return self._apply_filter(response, context)
            
        return response
        
    def _check_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if conditions are met for applying this pattern."""
        for key, expected in self.conditions.items():
            actual = context.get(key)
            
            if isinstance(expected, dict):
                operator = expected.get("operator", "==")
                value = expected.get("value")
                
                if operator == "==" and actual != value:
                    return False
                elif operator == "!=" and actual == value:
                    return False
                elif operator == ">" and actual <= value:
                    return False
                elif operator == "<" and actual >= value:
                    return False
                elif operator == "in" and actual not in value:
                    return False
                elif operator == "contains" and value not in str(actual):
                    return False
            else:
                if actual != expected:
                    return False
                    
        return True
        
    def _apply_prefix(self, response: str, context: Dict[str, Any]) -> str:
        """Apply prefix pattern."""
        if self.text_patterns:
            prefix = random.choice(self.text_patterns)
            prefix = self._interpolate_variables(prefix, context)
            return f"{prefix} {response}"
        return response
        
    def _apply_suffix(self, response: str, context: Dict[str, Any]) -> str:
        """Apply suffix pattern."""
        if self.text_patterns:
            suffix = random.choice(self.text_patterns)
            suffix = self._interpolate_variables(suffix, context)
            return f"{response} {suffix}"
        return response
        
    def _apply_wrapper(self, response: str, context: Dict[str, Any]) -> str:
        """Apply wrapper pattern."""
        if self.text_patterns:
            wrapper = random.choice(self.text_patterns)
            wrapper = self._interpolate_variables(wrapper, context)
            if "{response}" in wrapper:
                return wrapper.replace("{response}", response)
            else:
                # Default wrapper behavior
                parts = wrapper.split("|")
                if len(parts) == 2:
                    return f"{parts[0]} {response} {parts[1]}"
                else:
                    return f"{wrapper} {response}"
        return response
        
    def _apply_replacement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply replacement pattern."""
        modified = response
        
        for pattern, replacement in self.replacements.items():
            replacement = self._interpolate_variables(replacement, context)
            
            # Support both string and regex patterns
            if pattern.startswith("regex:"):
                regex_pattern = pattern[6:]  # Remove "regex:" prefix
                modified = re.sub(regex_pattern, replacement, modified)
            else:
                modified = modified.replace(pattern, replacement)
                
        return modified
        
    def _apply_enhancement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply enhancement pattern (modify style/tone)."""
        # This is a placeholder for more sophisticated enhancements
        # Could include things like:
        # - Adding emotional expressions
        # - Adjusting formality
        # - Adding personality quirks
        
        enhancements = {
            "enthusiasm": ["!", " 😊", " That's great!"],
            "formality": ["Indeed,", "Certainly,", "I must say,"],
            "casualness": [" tbh", " honestly", " for real"],
            "empathy": [" I understand how you feel.", " That must be difficult."],
            "humor": [" 😄", " (that's what she said)", " *ba dum tss*"]
        }
        
        enhancement_type = self.metadata.get("enhancement_type")
        if enhancement_type and enhancement_type in enhancements:
            additions = enhancements[enhancement_type]
            if random.random() < 0.3:  # 30% chance to add enhancement
                addition = random.choice(additions)
                return response + addition
                
        return response
        
    def _apply_filter(self, response: str, context: Dict[str, Any]) -> str:
        """Apply filter pattern (remove or modify content)."""
        filtered = response
        
        # Remove patterns
        remove_patterns = self.metadata.get("remove_patterns", [])
        for pattern in remove_patterns:
            if pattern.startswith("regex:"):
                regex_pattern = pattern[6:]
                filtered = re.sub(regex_pattern, "", filtered)
            else:
                filtered = filtered.replace(pattern, "")
                
        # Clean up extra spaces
        filtered = re.sub(r'\s+', ' ', filtered).strip()
        
        return filtered
        
    def _interpolate_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Replace variables in text with context values."""
        # Simple variable interpolation
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))
                
        return text
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "name": self.name,
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "text_patterns": self.text_patterns,
            "replacements": self.replacements,
            "conditions": self.conditions,
            "probability": self.probability,
            "priority": self.priority,
            "enabled": self.enabled,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponsePattern":
        """Create pattern from dictionary."""
        return cls(
            name=data["name"],
            pattern_type=PatternType(data["pattern_type"]),
            description=data.get("description", ""),
            text_patterns=data.get("text_patterns", []),
            replacements=data.get("replacements", {}),
            conditions=data.get("conditions", {}),
            probability=data.get("probability", 1.0),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {})
        )


class ResponsePatternManager:
    """
    Manages response patterns for different conversation styles.
    """
    
    def __init__(self):
        self._patterns: Dict[str, ResponsePattern] = {}
        self._style_patterns: Dict[str, List[str]] = {}  # style -> pattern names
        self._global_patterns: List[str] = []  # Always apply these
        
        # Load default patterns
        self._load_default_patterns()
        
    def add_pattern(self, pattern: ResponsePattern) -> None:
        """Add a response pattern."""
        self._patterns[pattern.name] = pattern
        
    def remove_pattern(self, name: str) -> bool:
        """Remove a pattern by name."""
        if name in self._patterns:
            del self._patterns[name]
            
            # Remove from style mappings
            for style_patterns in self._style_patterns.values():
                if name in style_patterns:
                    style_patterns.remove(name)
                    
            # Remove from global patterns
            if name in self._global_patterns:
                self._global_patterns.remove(name)
                
            return True
        return False
        
    def get_pattern(self, name: str) -> Optional[ResponsePattern]:
        """Get a pattern by name."""
        return self._patterns.get(name)
        
    def list_patterns(self) -> List[ResponsePattern]:
        """Get all patterns."""
        return list(self._patterns.values())
        
    def assign_pattern_to_style(self, pattern_name: str, style: str) -> bool:
        """Assign a pattern to a conversation style."""
        if pattern_name not in self._patterns:
            return False
            
        if style not in self._style_patterns:
            self._style_patterns[style] = []
            
        if pattern_name not in self._style_patterns[style]:
            self._style_patterns[style].append(pattern_name)
            
        return True
        
    def remove_pattern_from_style(self, pattern_name: str, style: str) -> bool:
        """Remove a pattern from a conversation style."""
        if style in self._style_patterns and pattern_name in self._style_patterns[style]:
            self._style_patterns[style].remove(pattern_name)
            return True
        return False
        
    def set_global_pattern(self, pattern_name: str) -> bool:
        """Set a pattern to always apply regardless of style."""
        if pattern_name not in self._patterns:
            return False
            
        if pattern_name not in self._global_patterns:
            self._global_patterns.append(pattern_name)
            
        return True
        
    def apply_patterns(
        self, 
        response: str, 
        context: Dict[str, Any],
        style: Optional[str] = None
    ) -> str:
        """
        Apply relevant patterns to a response.
        
        Args:
            response: Original response text
            context: Current context
            style: Optional conversation style
            
        Returns:
            Modified response
        """
        # Collect applicable patterns
        applicable_patterns = []
        
        # Add global patterns
        applicable_patterns.extend(self._global_patterns)
        
        # Add style-specific patterns
        if style and style in self._style_patterns:
            applicable_patterns.extend(self._style_patterns[style])
            
        # Sort patterns by priority (higher first)
        pattern_objects = []
        for pattern_name in applicable_patterns:
            pattern = self._patterns.get(pattern_name)
            if pattern and pattern.enabled:
                pattern_objects.append(pattern)
                
        pattern_objects.sort(key=lambda p: p.priority, reverse=True)
        
        # Apply patterns in order
        modified_response = response
        for pattern in pattern_objects:
            modified_response = pattern.apply(modified_response, context)
            
        return modified_response
        
    def create_style_preset(self, style_name: str, patterns: List[Dict[str, Any]]) -> None:
        """
        Create a preset conversation style with multiple patterns.
        
        Args:
            style_name: Name of the style
            patterns: List of pattern definitions
        """
        pattern_names = []
        
        for pattern_data in patterns:
            pattern = ResponsePattern.from_dict(pattern_data)
            self.add_pattern(pattern)
            pattern_names.append(pattern.name)
            
        self._style_patterns[style_name] = pattern_names
        
    def get_style_patterns(self, style: str) -> List[ResponsePattern]:
        """Get all patterns for a specific style."""
        pattern_names = self._style_patterns.get(style, [])
        return [self._patterns[name] for name in pattern_names if name in self._patterns]
        
    def list_styles(self) -> List[str]:
        """Get all defined conversation styles."""
        return list(self._style_patterns.keys())
        
    def analyze_response_modifications(
        self, 
        original: str, 
        modified: str
    ) -> Dict[str, Any]:
        """Analyze what modifications were made to a response."""
        return {
            "original_length": len(original),
            "modified_length": len(modified),
            "length_change": len(modified) - len(original),
            "character_change_percent": ((len(modified) - len(original)) / len(original) * 100) if original else 0,
            "added_prefix": modified.startswith(original) and len(modified) > len(original),
            "added_suffix": modified.endswith(original) and len(modified) > len(original),
            "substantial_change": len(set(original.split()) & set(modified.split())) / max(len(original.split()), 1) < 0.8
        }
        
    def _load_default_patterns(self) -> None:
        """Load default response patterns."""
        
        # Enthusiasm patterns
        enthusiasm_pattern = ResponsePattern(
            name="enthusiasm",
            pattern_type=PatternType.ENHANCEMENT,
            description="Adds enthusiastic expressions",
            metadata={"enhancement_type": "enthusiasm"}
        )
        self.add_pattern(enthusiasm_pattern)
        
        # Formal patterns
        formal_prefix = ResponsePattern(
            name="formal_prefix",
            pattern_type=PatternType.PREFIX,
            text_patterns=["Indeed,", "Certainly,", "I must say,", "Allow me to suggest,"],
            conditions={"formality": {"operator": ">", "value": 0.6}}
        )
        self.add_pattern(formal_prefix)
        
        # Casual patterns
        casual_suffix = ResponsePattern(
            name="casual_suffix",
            pattern_type=PatternType.SUFFIX,
            text_patterns=["tbh", "honestly", "for real", "you know?"],
            conditions={"formality": {"operator": "<", "value": 0.4}},
            probability=0.3
        )
        self.add_pattern(casual_suffix)
        
        # Empathy patterns
        empathy_wrapper = ResponsePattern(
            name="empathy_wrapper",
            pattern_type=PatternType.PREFIX,
            text_patterns=[
                "I understand this might be challenging.",
                "I can see why you'd feel that way.",
                "That sounds difficult."
            ],
            conditions={"emotional_state": "sad"},
            probability=0.7
        )
        self.add_pattern(empathy_wrapper)
        
        # Humor filter (removes serious language in humorous contexts)
        humor_replacements = ResponsePattern(
            name="humor_replacements",
            pattern_type=PatternType.REPLACEMENT,
            replacements={
                "I apologize": "Oops",
                "Unfortunately": "Well, darn",
                "It appears that": "Looks like",
                "Furthermore": "Also",
                "However": "But"
            },
            conditions={"humor": {"operator": ">", "value": 0.7}}
        )
        self.add_pattern(humor_replacements)
        
        # Create some default style presets
        self._style_patterns = {
            "formal": ["formal_prefix"],
            "casual": ["casual_suffix", "humor_replacements"],
            "empathetic": ["empathy_wrapper"],
            "enthusiastic": ["enthusiasm"]
        }