"""
Core Persona class definition.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging


logger = logging.getLogger(__name__)


class PersonaValidationError(Exception):
    """Exception raised for persona validation errors."""
    pass


class PersonaSerializationError(Exception):
    """Exception raised for persona serialization errors."""
    pass


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
        try:
            if not isinstance(trait_name, str):
                raise PersonaValidationError(f"Trait name must be a string, got {type(trait_name)}")
            
            if not trait_name.strip():
                raise PersonaValidationError("Trait name cannot be empty")
            
            if not isinstance(strength, (int, float)):
                raise PersonaValidationError(f"Trait strength must be numeric, got {type(strength)}")
            
            if not 0.0 <= strength <= 1.0:
                raise PersonaValidationError(f"Trait strength must be between 0.0 and 1.0, got {strength}")
            
            self.traits[trait_name] = float(strength)
            self.last_modified = datetime.now()
            logger.debug(f"Set trait '{trait_name}' to {strength} for persona '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to set trait '{trait_name}' for persona '{self.name}': {e}")
            raise
        
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
        try:
            data = self.to_dict()
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            logger.debug(f"Successfully serialized persona '{self.name}' to JSON")
            return json_str
        except Exception as e:
            logger.error(f"Failed to serialize persona '{self.name}' to JSON: {e}")
            raise PersonaSerializationError(f"Failed to serialize persona to JSON: {e}") from e
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        """Create persona from dictionary."""
        try:
            if not isinstance(data, dict):
                raise PersonaValidationError(f"Expected dictionary, got {type(data)}")
            
            if "name" not in data:
                raise PersonaValidationError("Missing required field: 'name'")
            
            name = data["name"]
            if not isinstance(name, str) or not name.strip():
                raise PersonaValidationError("Name must be a non-empty string")
            
            # Validate traits if provided
            traits = data.get("traits", {})
            if not isinstance(traits, dict):
                raise PersonaValidationError("Traits must be a dictionary")
            
            for trait_name, trait_value in traits.items():
                if not isinstance(trait_name, str):
                    raise PersonaValidationError(f"Trait name must be string, got {type(trait_name)}")
                if not isinstance(trait_value, (int, float)):
                    raise PersonaValidationError(f"Trait value must be numeric, got {type(trait_value)}")
                if not 0.0 <= trait_value <= 1.0:
                    raise PersonaValidationError(f"Trait value must be between 0.0 and 1.0, got {trait_value}")
            
            persona = cls(
                name=name,
                description=data.get("description", ""),
                traits=traits,
                conversation_style=data.get("conversation_style", "neutral"),
                emotional_baseline=data.get("emotional_baseline", "calm"),
                metadata=data.get("metadata", {})
            )
            
            # Handle timestamps with error handling
            if "created_at" in data:
                try:
                    persona.created_at = datetime.fromisoformat(data["created_at"])
                except ValueError as e:
                    logger.warning(f"Invalid created_at format, using current time: {e}")
                    
            if "last_modified" in data:
                try:
                    persona.last_modified = datetime.fromisoformat(data["last_modified"])
                except ValueError as e:
                    logger.warning(f"Invalid last_modified format, using current time: {e}")
            
            logger.debug(f"Successfully created persona '{name}' from dictionary")
            return persona
            
        except Exception as e:
            logger.error(f"Failed to create persona from dictionary: {e}")
            raise PersonaValidationError(f"Failed to create persona: {e}") from e
        
    @classmethod
    def from_json(cls, json_str: str) -> "Persona":
        """Create persona from JSON string."""
        try:
            if not isinstance(json_str, str):
                raise PersonaSerializationError(f"Expected string, got {type(json_str)}")
            
            if not json_str.strip():
                raise PersonaSerializationError("JSON string cannot be empty")
            
            data = json.loads(json_str)
            logger.debug("Successfully parsed JSON for persona creation")
            return cls.from_dict(data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise PersonaSerializationError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            logger.error(f"Failed to create persona from JSON: {e}")
            raise
        
    def __str__(self) -> str:
        return f"Persona(name='{self.name}', traits={len(self.traits)})"
        
    def validate(self) -> bool:
        """
        Validate the persona configuration.
        
        Returns:
            True if valid
            
        Raises:
            PersonaValidationError: If validation fails
        """
        try:
            if not self.name or not self.name.strip():
                raise PersonaValidationError("Persona name cannot be empty")
            
            if len(self.name) > 100:
                raise PersonaValidationError("Persona name cannot exceed 100 characters")
            
            if len(self.description) > 1000:
                raise PersonaValidationError("Persona description cannot exceed 1000 characters")
            
            # Validate traits
            for trait_name, trait_value in self.traits.items():
                if not isinstance(trait_name, str) or not trait_name.strip():
                    raise PersonaValidationError(f"Invalid trait name: '{trait_name}'")
                
                if not isinstance(trait_value, (int, float)):
                    raise PersonaValidationError(f"Trait value must be numeric: '{trait_name}'")
                
                if not 0.0 <= trait_value <= 1.0:
                    raise PersonaValidationError(f"Trait value out of range [0.0, 1.0]: '{trait_name}' = {trait_value}")
            
            if not isinstance(self.conversation_style, str):
                raise PersonaValidationError("Conversation style must be a string")
            
            if not isinstance(self.emotional_baseline, str):
                raise PersonaValidationError("Emotional baseline must be a string")
            
            if not isinstance(self.metadata, dict):
                raise PersonaValidationError("Metadata must be a dictionary")
            
            logger.debug(f"Persona '{self.name}' validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Persona '{self.name}' validation failed: {e}")
            raise

    def __repr__(self) -> str:
        return f"Persona(name='{self.name}', description='{self.description[:50]}...')"