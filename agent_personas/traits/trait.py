"""
Base trait implementation.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class TraitType(Enum):
    """Types of personality traits."""
    PERSONALITY = "personality"
    BEHAVIORAL = "behavioral" 
    COGNITIVE = "cognitive"
    EMOTIONAL = "emotional"
    SOCIAL = "social"
    COMMUNICATION = "communication"


@dataclass
class Trait:
    """
    Represents a single personality trait.
    """
    name: str
    description: str
    trait_type: TraitType
    min_value: float = 0.0
    max_value: float = 1.0
    default_value: float = 0.5
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
        # Validate value ranges
        if not self.min_value <= self.default_value <= self.max_value:
            raise ValueError("Default value must be between min and max values")
            
    def validate_value(self, value: float) -> bool:
        """Check if a value is valid for this trait."""
        return self.min_value <= value <= self.max_value
        
    def normalize_value(self, value: float) -> float:
        """Normalize a value to the trait's valid range."""
        return max(self.min_value, min(self.max_value, value))
        
    def get_description_for_value(self, value: float) -> str:
        """Get a descriptive text for a specific trait value."""
        if not self.validate_value(value):
            return f"Invalid value {value} for trait {self.name}"
            
        # Simple descriptive mapping
        normalized = (value - self.min_value) / (self.max_value - self.min_value)
        
        if normalized < 0.2:
            intensity = "Very Low"
        elif normalized < 0.4:
            intensity = "Low"
        elif normalized < 0.6:
            intensity = "Moderate"
        elif normalized < 0.8:
            intensity = "High"
        else:
            intensity = "Very High"
            
        return f"{intensity} {self.name}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert trait to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "trait_type": self.trait_type.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "default_value": self.default_value,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trait":
        """Create trait from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            trait_type=TraitType(data["trait_type"]),
            min_value=data.get("min_value", 0.0),
            max_value=data.get("max_value", 1.0),
            default_value=data.get("default_value", 0.5),
            metadata=data.get("metadata", {})
        )
        
    def __str__(self) -> str:
        return f"Trait({self.name}, {self.trait_type.value})"
        
    def __hash__(self) -> int:
        return hash(self.name)