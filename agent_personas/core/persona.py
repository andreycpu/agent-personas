"""
Core Persona class definition.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class Persona:
    """
    Represents an AI agent persona with personality traits, behaviors, and characteristics.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        traits: Optional[Dict[str, float]] = None,
        conversation_style: str = "neutral",
        emotional_baseline: str = "calm",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new persona.
        
        Args:
            name: Unique identifier for the persona
            description: Human-readable description of the persona
            traits: Dictionary of trait names to strength values (0.0-1.0)
            conversation_style: Default conversation style identifier
            emotional_baseline: Default emotional state
            metadata: Additional metadata for the persona
        """
        self.name = name
        self.description = description
        self.traits = traits or {}
        self.conversation_style = conversation_style
        self.emotional_baseline = emotional_baseline
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        
    def get_trait(self, trait_name: str) -> float:
        """Get the strength of a specific trait."""
        return self.traits.get(trait_name, 0.0)
        
    def set_trait(self, trait_name: str, strength: float) -> None:
        """Set the strength of a specific trait."""
        if not 0.0 <= strength <= 1.0:
            raise ValueError("Trait strength must be between 0.0 and 1.0")
        self.traits[trait_name] = strength
        self.last_modified = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "traits": self.traits,
            "conversation_style": self.conversation_style,
            "emotional_baseline": self.emotional_baseline,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat()
        }
        
    def to_json(self) -> str:
        """Convert persona to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        """Create persona from dictionary."""
        persona = cls(
            name=data["name"],
            description=data.get("description", ""),
            traits=data.get("traits", {}),
            conversation_style=data.get("conversation_style", "neutral"),
            emotional_baseline=data.get("emotional_baseline", "calm"),
            metadata=data.get("metadata", {})
        )
        
        if "created_at" in data:
            persona.created_at = datetime.fromisoformat(data["created_at"])
        if "last_modified" in data:
            persona.last_modified = datetime.fromisoformat(data["last_modified"])
            
        return persona
        
    @classmethod
    def from_json(cls, json_str: str) -> "Persona":
        """Create persona from JSON string."""
        return cls.from_dict(json.loads(json_str))
        
    def __str__(self) -> str:
        return f"Persona(name='{self.name}', traits={len(self.traits)})"
        
    def __repr__(self) -> str:
        return f"Persona(name='{self.name}', description='{self.description[:50]}...')"