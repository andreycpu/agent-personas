"""
Custom exceptions for agent_personas package.
"""


class PersonaError(Exception):
    """Base exception for all persona-related errors."""
    pass


class PersonaValidationError(PersonaError):
    """Raised when persona data fails validation."""
    pass


class PersonaNotFoundError(PersonaError):
    """Raised when a requested persona cannot be found."""
    pass


class PersonaConfigError(PersonaError):
    """Raised when there are configuration issues."""
    pass


class PersonaMemoryError(PersonaError):
    """Raised when memory operations fail."""
    pass


class PersonaCacheError(PersonaError):
    """Raised when cache operations fail."""
    pass


class PersonaSerializationError(PersonaError):
    """Raised when serialization/deserialization fails."""
    pass


class PersonaVersionError(PersonaError):
    """Raised when there are version compatibility issues."""
    pass


class PersonaTraitError(PersonaError):
    """Raised when trait operations fail."""
    pass


class PersonaContextError(PersonaError):
    """Raised when context operations fail."""
    pass