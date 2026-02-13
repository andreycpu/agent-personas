"""
Tests for exception classes.
"""

import pytest
from agent_personas.exceptions import (
    PersonaError,
    PersonaValidationError,
    PersonaNotFoundError,
    PersonaConfigError,
    PersonaMemoryError,
    PersonaCacheError,
    PersonaSerializationError,
    PersonaVersionError,
    PersonaTraitError,
    PersonaContextError
)


class TestPersonaExceptions:
    """Test persona exception hierarchy."""
    
    def test_base_persona_error(self):
        """Test base PersonaError functionality."""
        error = PersonaError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_persona_validation_error(self):
        """Test PersonaValidationError."""
        error = PersonaValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, PersonaError)
    
    def test_persona_not_found_error(self):
        """Test PersonaNotFoundError."""
        error = PersonaNotFoundError("Persona not found")
        assert str(error) == "Persona not found"
        assert isinstance(error, PersonaError)
    
    def test_persona_config_error(self):
        """Test PersonaConfigError."""
        error = PersonaConfigError("Config error")
        assert str(error) == "Config error"
        assert isinstance(error, PersonaError)
    
    def test_persona_memory_error(self):
        """Test PersonaMemoryError."""
        error = PersonaMemoryError("Memory error")
        assert str(error) == "Memory error"
        assert isinstance(error, PersonaError)
    
    def test_persona_cache_error(self):
        """Test PersonaCacheError."""
        error = PersonaCacheError("Cache error")
        assert str(error) == "Cache error"
        assert isinstance(error, PersonaError)
    
    def test_persona_serialization_error(self):
        """Test PersonaSerializationError."""
        error = PersonaSerializationError("Serialization error")
        assert str(error) == "Serialization error"
        assert isinstance(error, PersonaError)
    
    def test_persona_version_error(self):
        """Test PersonaVersionError."""
        error = PersonaVersionError("Version error")
        assert str(error) == "Version error"
        assert isinstance(error, PersonaError)
    
    def test_persona_trait_error(self):
        """Test PersonaTraitError."""
        error = PersonaTraitError("Trait error")
        assert str(error) == "Trait error"
        assert isinstance(error, PersonaError)
    
    def test_persona_context_error(self):
        """Test PersonaContextError."""
        error = PersonaContextError("Context error")
        assert str(error) == "Context error"
        assert isinstance(error, PersonaError)
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from PersonaError."""
        exception_classes = [
            PersonaValidationError,
            PersonaNotFoundError,
            PersonaConfigError,
            PersonaMemoryError,
            PersonaCacheError,
            PersonaSerializationError,
            PersonaVersionError,
            PersonaTraitError,
            PersonaContextError
        ]
        
        for exc_class in exception_classes:
            error = exc_class("Test error")
            assert isinstance(error, PersonaError)
            assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__])