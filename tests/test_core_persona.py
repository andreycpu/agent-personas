"""
Unit tests for the core Persona class.
"""

import pytest
from datetime import datetime
from agent_personas.core.persona import Persona


class TestPersona:
    """Test cases for the Persona class."""
    
    def test_persona_creation(self):
        """Test basic persona creation."""
        persona = Persona(
            name="TestPersona",
            description="A test persona",
            traits={"helpfulness": 0.8, "formality": 0.6},
            conversation_style="friendly",
            emotional_baseline="calm"
        )
        
        assert persona.name == "TestPersona"
        assert persona.description == "A test persona"
        assert persona.traits["helpfulness"] == 0.8
        assert persona.traits["formality"] == 0.6
        assert persona.conversation_style == "friendly"
        assert persona.emotional_baseline == "calm"
        assert isinstance(persona.created_at, datetime)
        assert isinstance(persona.last_modified, datetime)
    
    def test_persona_creation_with_defaults(self):
        """Test persona creation with default values."""
        persona = Persona(name="MinimalPersona")
        
        assert persona.name == "MinimalPersona"
        assert persona.description == ""
        assert persona.traits == {}
        assert persona.conversation_style == "neutral"
        assert persona.emotional_baseline == "calm"
        assert persona.metadata == {}
    
    def test_get_trait(self):
        """Test getting trait values."""
        persona = Persona(
            name="TestPersona",
            traits={"confidence": 0.7, "empathy": 0.9}
        )
        
        assert persona.get_trait("confidence") == 0.7
        assert persona.get_trait("empathy") == 0.9
        assert persona.get_trait("nonexistent") == 0.0
    
    def test_set_trait(self):
        """Test setting trait values."""
        persona = Persona(name="TestPersona")
        
        persona.set_trait("helpfulness", 0.8)
        assert persona.get_trait("helpfulness") == 0.8
        
        # Test bounds checking
        persona.set_trait("confidence", 1.5)
        assert persona.get_trait("confidence") == 1.0
        
        persona.set_trait("patience", -0.5)
        assert persona.get_trait("patience") == 0.0
    
    def test_set_trait_invalid_range(self):
        """Test that setting invalid trait values raises an error."""
        persona = Persona(name="TestPersona")
        
        with pytest.raises(ValueError):
            persona.set_trait("invalid", 1.5)
        
        with pytest.raises(ValueError):
            persona.set_trait("invalid", -0.5)
    
    def test_trait_modification_updates_timestamp(self):
        """Test that modifying traits updates the last_modified timestamp."""
        persona = Persona(name="TestPersona")
        original_time = persona.last_modified
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        persona.set_trait("helpfulness", 0.8)
        assert persona.last_modified > original_time
    
    def test_to_dict_serialization(self):
        """Test persona serialization to dictionary."""
        persona = Persona(
            name="TestPersona",
            description="A test persona",
            traits={"helpfulness": 0.8, "formality": 0.6},
            conversation_style="friendly",
            emotional_baseline="calm",
            metadata={"test_key": "test_value"}
        )
        
        data = persona.to_dict()
        
        assert data["name"] == "TestPersona"
        assert data["description"] == "A test persona"
        assert data["traits"]["helpfulness"] == 0.8
        assert data["conversation_style"] == "friendly"
        assert data["emotional_baseline"] == "calm"
        assert data["metadata"]["test_key"] == "test_value"
        assert "created_at" in data
        assert "last_modified" in data
    
    def test_to_json_serialization(self):
        """Test persona serialization to JSON."""
        persona = Persona(
            name="TestPersona",
            traits={"helpfulness": 0.8}
        )
        
        json_str = persona.to_json()
        assert isinstance(json_str, str)
        assert "TestPersona" in json_str
        assert "helpfulness" in json_str
    
    def test_from_dict_deserialization(self):
        """Test persona creation from dictionary."""
        data = {
            "name": "TestPersona",
            "description": "A test persona",
            "traits": {"helpfulness": 0.8, "formality": 0.6},
            "conversation_style": "friendly",
            "emotional_baseline": "calm",
            "metadata": {"test_key": "test_value"}
        }
        
        persona = Persona.from_dict(data)
        
        assert persona.name == "TestPersona"
        assert persona.description == "A test persona"
        assert persona.traits["helpfulness"] == 0.8
        assert persona.conversation_style == "friendly"
        assert persona.emotional_baseline == "calm"
        assert persona.metadata["test_key"] == "test_value"
    
    def test_from_json_deserialization(self):
        """Test persona creation from JSON."""
        original_persona = Persona(
            name="TestPersona",
            traits={"helpfulness": 0.8}
        )
        
        json_str = original_persona.to_json()
        restored_persona = Persona.from_json(json_str)
        
        assert restored_persona.name == original_persona.name
        assert restored_persona.traits == original_persona.traits
    
    def test_roundtrip_serialization(self):
        """Test that serialization and deserialization preserve data."""
        original = Persona(
            name="TestPersona",
            description="A test persona",
            traits={"helpfulness": 0.8, "confidence": 0.7},
            conversation_style="professional",
            emotional_baseline="focused",
            metadata={"category": "assistant", "version": "1.0"}
        )
        
        # Test dict roundtrip
        data = original.to_dict()
        restored = Persona.from_dict(data)
        
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.traits == original.traits
        assert restored.conversation_style == original.conversation_style
        assert restored.emotional_baseline == original.emotional_baseline
        assert restored.metadata == original.metadata
        
        # Test JSON roundtrip
        json_str = original.to_json()
        json_restored = Persona.from_json(json_str)
        
        assert json_restored.name == original.name
        assert json_restored.traits == original.traits
    
    def test_string_representation(self):
        """Test string representation of personas."""
        persona = Persona(
            name="TestPersona",
            description="A test persona for unit testing",
            traits={"helpfulness": 0.8, "confidence": 0.7}
        )
        
        str_repr = str(persona)
        assert "TestPersona" in str_repr
        assert "2" in str_repr  # Number of traits
        
        repr_str = repr(persona)
        assert "TestPersona" in repr_str
        assert "A test persona for unit testing" in repr_str