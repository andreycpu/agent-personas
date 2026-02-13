"""
Tests for validation modules.
"""

import pytest
from agent_personas.validation import (
    validate_persona_name,
    validate_persona_traits,
    validate_context_data,
    validate_memory_entries,
    validate_conversation_history,
    validate_json_schema,
    validate_data_types,
    validate_required_fields,
    validate_field_constraints,
    sanitize_input_data,
    validate_persona_consistency,
    validate_trait_compatibility,
    validate_conversation_flow,
    validate_memory_coherence
)
from agent_personas.exceptions import PersonaValidationError


class TestInputValidators:
    """Test input validation functions."""
    
    def test_validate_persona_name_valid(self):
        """Test valid persona name validation."""
        assert validate_persona_name("John Doe") == True
        assert validate_persona_name("AI Assistant") == True
        assert validate_persona_name("test-persona_123") == True
    
    def test_validate_persona_name_invalid(self):
        """Test invalid persona name validation."""
        with pytest.raises(PersonaValidationError):
            validate_persona_name("")  # Empty name
        
        with pytest.raises(PersonaValidationError):
            validate_persona_name("   ")  # Only whitespace
        
        with pytest.raises(PersonaValidationError):
            validate_persona_name("A" * 101)  # Too long
        
        with pytest.raises(PersonaValidationError):
            validate_persona_name("Invalid@Name")  # Invalid characters
    
    def test_validate_persona_traits_valid(self):
        """Test valid persona traits validation."""
        valid_traits = {
            "personality": {"extroversion": 0.7, "openness": 0.5},
            "communication_style": "friendly",
            "knowledge_areas": ["technology", "science"]
        }
        assert validate_persona_traits(valid_traits) == True
    
    def test_validate_persona_traits_invalid(self):
        """Test invalid persona traits validation."""
        # Missing required fields
        with pytest.raises(PersonaValidationError):
            validate_persona_traits({"personality": {}})
        
        # Invalid communication style
        with pytest.raises(PersonaValidationError):
            validate_persona_traits({
                "personality": {},
                "communication_style": "invalid_style",
                "knowledge_areas": ["tech"]
            })
        
        # Empty knowledge areas
        with pytest.raises(PersonaValidationError):
            validate_persona_traits({
                "personality": {},
                "communication_style": "formal",
                "knowledge_areas": []
            })
    
    def test_validate_context_data_valid(self):
        """Test valid context data validation."""
        valid_context = {
            "timestamp": 1234567890.0,
            "user_id": "user123",
            "session_id": "sess456"
        }
        assert validate_context_data(valid_context) == True
    
    def test_validate_context_data_invalid(self):
        """Test invalid context data validation."""
        # Invalid timestamp
        with pytest.raises(PersonaValidationError):
            validate_context_data({"timestamp": "invalid"})
        
        # Empty user_id
        with pytest.raises(PersonaValidationError):
            validate_context_data({"user_id": ""})
        
        # Too large context
        with pytest.raises(PersonaValidationError):
            validate_context_data({"data": "x" * 60000})


class TestDataValidators:
    """Test data validation functions."""
    
    def test_validate_required_fields_valid(self):
        """Test valid required fields validation."""
        data = {"name": "test", "age": 25, "email": "test@example.com"}
        required = ["name", "age"]
        assert validate_required_fields(data, required) == True
    
    def test_validate_required_fields_invalid(self):
        """Test invalid required fields validation."""
        data = {"name": "test"}
        required = ["name", "age", "email"]
        
        with pytest.raises(PersonaValidationError, match="Missing required fields"):
            validate_required_fields(data, required)
    
    def test_validate_data_types_valid(self):
        """Test valid data types validation."""
        data = {"name": "test", "age": 25, "active": True}
        types = {"name": str, "age": int, "active": bool}
        assert validate_data_types(data, types) == True
    
    def test_validate_data_types_invalid(self):
        """Test invalid data types validation."""
        data = {"name": "test", "age": "25"}  # age should be int
        types = {"name": str, "age": int}
        
        with pytest.raises(PersonaValidationError, match="must be of type"):
            validate_data_types(data, types)
    
    def test_validate_field_constraints_valid(self):
        """Test valid field constraints validation."""
        data = {"name": "Alice", "age": 30, "score": 85.5}
        constraints = {
            "name": {"min_length": 2, "max_length": 50},
            "age": {"min_value": 0, "max_value": 150},
            "score": {"min_value": 0.0, "max_value": 100.0}
        }
        assert validate_field_constraints(data, constraints) == True
    
    def test_validate_field_constraints_invalid(self):
        """Test invalid field constraints validation."""
        data = {"name": "A"}  # Too short
        constraints = {"name": {"min_length": 2}}
        
        with pytest.raises(PersonaValidationError, match="too short"):
            validate_field_constraints(data, constraints)
    
    def test_sanitize_input_data(self):
        """Test input data sanitization."""
        data = {
            "name": "  John Doe  ",
            "bio": "<p>Hello <script>alert('xss')</script>world</p>",
            "nested": {"description": "  Test  "}
        }
        
        sanitized = sanitize_input_data(data)
        
        assert sanitized["name"] == "John Doe"
        assert "<script>" not in sanitized["bio"]
        assert sanitized["nested"]["description"] == "Test"


class TestBusinessValidators:
    """Test business logic validation functions."""
    
    def test_validate_persona_consistency_valid(self):
        """Test valid persona consistency validation."""
        persona = {
            "traits": {
                "personality": {"extroversion": 0.8, "formality": 0.3},
                "communication_style": "friendly",
                "knowledge_areas": ["psychology", "communication"],
                "expertise_level": "intermediate"
            }
        }
        assert validate_persona_consistency(persona) == True
    
    def test_validate_persona_consistency_invalid(self):
        """Test invalid persona consistency validation."""
        # Inconsistent personality and communication style
        persona = {
            "traits": {
                "personality": {"extroversion": 0.1, "formality": 0.9},
                "communication_style": "bubbly",
                "knowledge_areas": ["tech"],
                "expertise_level": "expert"
            }
        }
        
        with pytest.raises(PersonaValidationError, match="inconsistent"):
            validate_persona_consistency(persona)
    
    def test_validate_trait_compatibility_valid(self):
        """Test valid trait compatibility validation."""
        traits = {
            "personality": {
                "creativity": 0.7,
                "analytical_thinking": 0.4,
                "enthusiasm": 0.6
            }
        }
        assert validate_trait_compatibility(traits) == True
    
    def test_validate_trait_compatibility_invalid(self):
        """Test invalid trait compatibility validation."""
        # Contradictory traits
        traits = {
            "personality": {
                "creativity": 0.9,
                "analytical_thinking": 0.9  # Too high for both
            }
        }
        
        with pytest.raises(PersonaValidationError, match="Contradictory traits"):
            validate_trait_compatibility(traits)
    
    def test_validate_conversation_flow_valid(self):
        """Test valid conversation flow validation."""
        conversation = [
            {"role": "user", "content": "Hello", "timestamp": 1000},
            {"role": "assistant", "content": "Hi there!", "timestamp": 1001},
            {"role": "user", "content": "How are you?", "timestamp": 1002}
        ]
        assert validate_conversation_flow(conversation) == True
    
    def test_validate_conversation_flow_invalid(self):
        """Test invalid conversation flow validation."""
        # Wrong chronological order
        conversation = [
            {"role": "user", "content": "Hello", "timestamp": 1002},
            {"role": "assistant", "content": "Hi there!", "timestamp": 1001}  # Earlier timestamp
        ]
        
        with pytest.raises(PersonaValidationError, match="timestamp earlier"):
            validate_conversation_flow(conversation)


if __name__ == "__main__":
    pytest.main([__file__])