"""
Data validation utilities for schema and type checking.
"""

import json
from typing import Any, Dict, List, Optional, Set, Type, Union
from jsonschema import validate, ValidationError
from ..exceptions import PersonaValidationError


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against JSON schema."""
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        raise PersonaValidationError(f"Schema validation failed: {e.message}")


def validate_data_types(data: Dict[str, Any], type_spec: Dict[str, Type]) -> bool:
    """Validate data types according to specification."""
    for field, expected_type in type_spec.items():
        if field in data:
            if not isinstance(data[field], expected_type):
                raise PersonaValidationError(
                    f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}"
                )
    return True


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate that all required fields are present."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise PersonaValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    return True


def validate_field_constraints(data: Dict[str, Any], constraints: Dict[str, Dict[str, Any]]) -> bool:
    """Validate field values against constraints."""
    for field, constraint_spec in constraints.items():
        if field not in data:
            continue
        
        value = data[field]
        
        # Check min/max length for strings
        if isinstance(value, str):
            if 'min_length' in constraint_spec and len(value) < constraint_spec['min_length']:
                raise PersonaValidationError(f"Field '{field}' is too short (min: {constraint_spec['min_length']})")
            
            if 'max_length' in constraint_spec and len(value) > constraint_spec['max_length']:
                raise PersonaValidationError(f"Field '{field}' is too long (max: {constraint_spec['max_length']})")
        
        # Check min/max value for numbers
        if isinstance(value, (int, float)):
            if 'min_value' in constraint_spec and value < constraint_spec['min_value']:
                raise PersonaValidationError(f"Field '{field}' is too small (min: {constraint_spec['min_value']})")
            
            if 'max_value' in constraint_spec and value > constraint_spec['max_value']:
                raise PersonaValidationError(f"Field '{field}' is too large (max: {constraint_spec['max_value']})")
        
        # Check allowed values
        if 'allowed_values' in constraint_spec:
            allowed = constraint_spec['allowed_values']
            if value not in allowed:
                raise PersonaValidationError(f"Field '{field}' must be one of: {allowed}")
        
        # Check pattern for strings
        if 'pattern' in constraint_spec and isinstance(value, str):
            import re
            if not re.match(constraint_spec['pattern'], value):
                raise PersonaValidationError(f"Field '{field}' does not match required pattern")
    
    return True


def sanitize_input_data(data: Dict[str, Any], sanitization_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sanitize input data according to rules."""
    if sanitization_rules is None:
        sanitization_rules = {
            'strip_whitespace': True,
            'remove_html': True,
            'escape_special_chars': False,
            'normalize_unicode': True
        }
    
    sanitized = data.copy()
    
    def sanitize_string(value: str) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return value
        
        result = value
        
        # Strip whitespace
        if sanitization_rules.get('strip_whitespace', True):
            result = result.strip()
        
        # Remove HTML tags
        if sanitization_rules.get('remove_html', True):
            import re
            result = re.sub(r'<[^>]+>', '', result)
        
        # Escape special characters
        if sanitization_rules.get('escape_special_chars', False):
            import html
            result = html.escape(result)
        
        # Normalize unicode
        if sanitization_rules.get('normalize_unicode', True):
            import unicodedata
            result = unicodedata.normalize('NFKC', result)
        
        return result
    
    def sanitize_recursive(obj: Any) -> Any:
        """Recursively sanitize nested data structures."""
        if isinstance(obj, dict):
            return {k: sanitize_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return sanitize_string(obj)
        else:
            return obj
    
    return sanitize_recursive(sanitized)


# Common validation schemas
PERSONA_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "traits": {
            "type": "object",
            "properties": {
                "personality": {"type": "object"},
                "communication_style": {"type": "string"},
                "knowledge_areas": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["personality", "communication_style", "knowledge_areas"]
        },
        "version": {"type": "string"},
        "created_at": {"type": "number"},
        "updated_at": {"type": "number"}
    },
    "required": ["name", "traits"]
}

MEMORY_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "minLength": 1},
        "timestamp": {"type": "number"},
        "importance": {"type": "number", "minimum": 0, "maximum": 1},
        "tags": {"type": "array", "items": {"type": "string"}},
        "metadata": {"type": "object"}
    },
    "required": ["content", "timestamp", "importance"]
}

CONVERSATION_MESSAGE_SCHEMA = {
    "type": "object", 
    "properties": {
        "role": {"type": "string", "enum": ["user", "assistant", "system"]},
        "content": {"type": "string", "minLength": 1},
        "timestamp": {"type": "number"},
        "metadata": {"type": "object"}
    },
    "required": ["role", "content", "timestamp"]
}