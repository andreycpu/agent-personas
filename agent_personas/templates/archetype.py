"""
Archetype system for defining persona patterns and behavioral templates.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class ArchetypeCategory(Enum):
    """Categories for organizing archetypes."""
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    SOCIAL = "social"
    TECHNICAL = "technical"
    SUPPORTIVE = "supportive"
    ANALYTICAL = "analytical"
    EMOTIONAL = "emotional"
    ADVENTUROUS = "adventurous"


@dataclass
class Archetype:
    """
    Represents a behavioral archetype that can be applied to personas.
    
    Archetypes define core personality patterns, communication styles,
    and behavioral tendencies that can be mixed and matched.
    """
    
    name: str
    description: str
    category: ArchetypeCategory
    core_traits: Dict[str, float] = field(default_factory=dict)
    conversation_preferences: Dict[str, Any] = field(default_factory=dict)
    emotional_tendencies: Dict[str, float] = field(default_factory=dict)
    behavioral_patterns: List[str] = field(default_factory=list)
    compatible_archetypes: Set[str] = field(default_factory=set)
    conflicting_archetypes: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate archetype after initialization."""
        self._validate_traits()
        self._validate_emotional_tendencies()
    
    def _validate_traits(self):
        """Validate that trait values are in valid range."""
        for trait, value in self.core_traits.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Trait '{trait}' must be between 0.0 and 1.0, got {value}")
    
    def _validate_emotional_tendencies(self):
        """Validate emotional tendency values."""
        for emotion, value in self.emotional_tendencies.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Emotional tendency '{emotion}' must be between 0.0 and 1.0, got {value}")
    
    def is_compatible_with(self, other: "Archetype") -> bool:
        """Check if this archetype is compatible with another."""
        return (
            other.name in self.compatible_archetypes and
            self.name not in other.conflicting_archetypes
        )
    
    def conflicts_with(self, other: "Archetype") -> bool:
        """Check if this archetype conflicts with another."""
        return (
            other.name in self.conflicting_archetypes or
            self.name in other.conflicting_archetypes
        )
    
    def blend_with(self, other: "Archetype", ratio: float = 0.5) -> Dict[str, Any]:
        """
        Blend this archetype with another to create a hybrid personality.
        
        Args:
            other: The archetype to blend with
            ratio: Blend ratio (0.0 = all this, 1.0 = all other)
        
        Returns:
            Dictionary containing blended traits and properties
        """
        if self.conflicts_with(other):
            logger.warning(f"Blending conflicting archetypes: {self.name} and {other.name}")
        
        # Blend traits
        blended_traits = {}
        all_traits = set(self.core_traits.keys()) | set(other.core_traits.keys())
        
        for trait in all_traits:
            self_value = self.core_traits.get(trait, 0.0)
            other_value = other.core_traits.get(trait, 0.0)
            blended_traits[trait] = self_value * (1 - ratio) + other_value * ratio
        
        # Blend emotional tendencies
        blended_emotions = {}
        all_emotions = set(self.emotional_tendencies.keys()) | set(other.emotional_tendencies.keys())
        
        for emotion in all_emotions:
            self_value = self.emotional_tendencies.get(emotion, 0.0)
            other_value = other.emotional_tendencies.get(emotion, 0.0)
            blended_emotions[emotion] = self_value * (1 - ratio) + other_value * ratio
        
        # Combine behavioral patterns
        blended_patterns = list(set(self.behavioral_patterns + other.behavioral_patterns))
        
        # Merge conversation preferences
        blended_conversation = {**self.conversation_preferences}
        for key, value in other.conversation_preferences.items():
            if key in blended_conversation:
                # For conflicting preferences, use weighted average or other's value based on ratio
                if isinstance(value, (int, float)) and isinstance(blended_conversation[key], (int, float)):
                    blended_conversation[key] = (
                        blended_conversation[key] * (1 - ratio) + value * ratio
                    )
                elif ratio > 0.5:
                    blended_conversation[key] = value
            else:
                blended_conversation[key] = value
        
        return {
            "traits": blended_traits,
            "emotional_tendencies": blended_emotions,
            "behavioral_patterns": blended_patterns,
            "conversation_preferences": blended_conversation,
            "source_archetypes": [self.name, other.name],
            "blend_ratio": ratio
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert archetype to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "core_traits": self.core_traits,
            "conversation_preferences": self.conversation_preferences,
            "emotional_tendencies": self.emotional_tendencies,
            "behavioral_patterns": self.behavioral_patterns,
            "compatible_archetypes": list(self.compatible_archetypes),
            "conflicting_archetypes": list(self.conflicting_archetypes),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Archetype":
        """Create archetype from dictionary representation."""
        return cls(
            name=data["name"],
            description=data["description"],
            category=ArchetypeCategory(data["category"]),
            core_traits=data.get("core_traits", {}),
            conversation_preferences=data.get("conversation_preferences", {}),
            emotional_tendencies=data.get("emotional_tendencies", {}),
            behavioral_patterns=data.get("behavioral_patterns", []),
            compatible_archetypes=set(data.get("compatible_archetypes", [])),
            conflicting_archetypes=set(data.get("conflicting_archetypes", [])),
            metadata=data.get("metadata", {})
        )


class ArchetypeManager:
    """Manages archetypes and provides composition functionality."""
    
    def __init__(self):
        self._archetypes: Dict[str, Archetype] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_archetype(self, archetype: Archetype) -> None:
        """Register a new archetype."""
        if archetype.name in self._archetypes:
            self.logger.warning(f"Overwriting existing archetype: {archetype.name}")
        
        self._archetypes[archetype.name] = archetype
        self.logger.info(f"Registered archetype: {archetype.name}")
    
    def get_archetype(self, name: str) -> Optional[Archetype]:
        """Get an archetype by name."""
        return self._archetypes.get(name)
    
    def list_archetypes(self, category: Optional[ArchetypeCategory] = None) -> List[Archetype]:
        """List all archetypes, optionally filtered by category."""
        archetypes = list(self._archetypes.values())
        if category:
            archetypes = [a for a in archetypes if a.category == category]
        return sorted(archetypes, key=lambda a: a.name)
    
    def find_compatible_archetypes(self, archetype_name: str) -> List[Archetype]:
        """Find archetypes compatible with the given archetype."""
        base_archetype = self.get_archetype(archetype_name)
        if not base_archetype:
            return []
        
        compatible = []
        for archetype in self._archetypes.values():
            if archetype.name != archetype_name and base_archetype.is_compatible_with(archetype):
                compatible.append(archetype)
        
        return compatible
    
    def create_blend(self, archetype1_name: str, archetype2_name: str, ratio: float = 0.5) -> Dict[str, Any]:
        """Create a blend of two archetypes."""
        arch1 = self.get_archetype(archetype1_name)
        arch2 = self.get_archetype(archetype2_name)
        
        if not arch1:
            raise ValueError(f"Archetype not found: {archetype1_name}")
        if not arch2:
            raise ValueError(f"Archetype not found: {archetype2_name}")
        
        return arch1.blend_with(arch2, ratio)
    
    def export_archetypes(self, file_path: str) -> None:
        """Export all archetypes to a JSON file."""
        data = {name: archetype.to_dict() for name, archetype in self._archetypes.items()}
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(self._archetypes)} archetypes to {file_path}")
    
    def import_archetypes(self, file_path: str) -> None:
        """Import archetypes from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for name, archetype_data in data.items():
            archetype = Archetype.from_dict(archetype_data)
            self.register_archetype(archetype)
        
        self.logger.info(f"Imported {len(data)} archetypes from {file_path}")