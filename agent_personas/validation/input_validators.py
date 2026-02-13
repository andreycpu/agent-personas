"""
Input validation functions for persona-related data.
"""

import re
from typing import Any, Dict, List, Optional, Union
from ..exceptions import PersonaValidationError


def validate_persona_name(name: str) -> bool:
    """Validate persona name format and constraints."""
    if not isinstance(name, str):
        raise PersonaValidationError("Persona name must be a string")
    
    if not name.strip():
        raise PersonaValidationError("Persona name cannot be empty")
    
    if len(name) > 100:
        raise PersonaValidationError("Persona name cannot exceed 100 characters")
    
    # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        raise PersonaValidationError("Persona name contains invalid characters")
    
    return True


def validate_persona_traits(traits: Dict[str, Any]) -> bool:
    """Validate persona traits structure and values."""
    if not isinstance(traits, dict):
        raise PersonaValidationError("Traits must be a dictionary")
    
    required_traits = ['personality', 'communication_style', 'knowledge_areas']
    for trait in required_traits:
        if trait not in traits:
            raise PersonaValidationError(f"Required trait '{trait}' is missing")
    
    # Validate personality traits
    if not isinstance(traits['personality'], dict):
        raise PersonaValidationError("Personality must be a dictionary")
    
    # Validate communication style
    valid_styles = ['formal', 'casual', 'friendly', 'professional', 'technical']
    if traits['communication_style'] not in valid_styles:
        raise PersonaValidationError(f"Invalid communication style. Must be one of: {valid_styles}")
    
    # Validate knowledge areas
    if not isinstance(traits['knowledge_areas'], list):
        raise PersonaValidationError("Knowledge areas must be a list")
    
    if len(traits['knowledge_areas']) == 0:
        raise PersonaValidationError("At least one knowledge area must be specified")
    
    return True


def validate_context_data(context: Dict[str, Any]) -> bool:
    """Validate context data structure."""
    if not isinstance(context, dict):
        raise PersonaValidationError("Context must be a dictionary")
    
    # Check for maximum context size (prevent memory issues)
    if len(str(context)) > 50000:  # 50KB limit
        raise PersonaValidationError("Context data too large (max 50KB)")
    
    # Validate common context fields
    if 'timestamp' in context:
        if not isinstance(context['timestamp'], (int, float)):
            raise PersonaValidationError("Timestamp must be numeric")
    
    if 'user_id' in context:
        if not isinstance(context['user_id'], str) or not context['user_id'].strip():
            raise PersonaValidationError("User ID must be a non-empty string")
    
    return True


def validate_memory_entries(memories: List[Dict[str, Any]]) -> bool:
    """Validate memory entries format."""
    if not isinstance(memories, list):
        raise PersonaValidationError("Memories must be a list")
    
    for i, memory in enumerate(memories):
        if not isinstance(memory, dict):
            raise PersonaValidationError(f"Memory entry {i} must be a dictionary")
        
        required_fields = ['content', 'timestamp', 'importance']
        for field in required_fields:
            if field not in memory:
                raise PersonaValidationError(f"Memory entry {i} missing required field: {field}")
        
        # Validate importance score
        if not isinstance(memory['importance'], (int, float)) or not 0 <= memory['importance'] <= 1:
            raise PersonaValidationError(f"Memory entry {i} importance must be between 0 and 1")
        
        # Validate content length
        if len(memory['content']) > 10000:
            raise PersonaValidationError(f"Memory entry {i} content too long (max 10KB)")
    
    return True


def validate_conversation_history(history: List[Dict[str, Any]]) -> bool:
    """Validate conversation history format."""
    if not isinstance(history, list):
        raise PersonaValidationError("Conversation history must be a list")
    
    for i, message in enumerate(history):
        if not isinstance(message, dict):
            raise PersonaValidationError(f"Message {i} must be a dictionary")
        
        required_fields = ['role', 'content', 'timestamp']
        for field in required_fields:
            if field not in message:
                raise PersonaValidationError(f"Message {i} missing required field: {field}")
        
        # Validate role
        valid_roles = ['user', 'assistant', 'system']
        if message['role'] not in valid_roles:
            raise PersonaValidationError(f"Message {i} has invalid role: {message['role']}")
        
        # Validate content
        if not isinstance(message['content'], str) or not message['content'].strip():
            raise PersonaValidationError(f"Message {i} content must be non-empty string")
        
        # Validate timestamp
        if not isinstance(message['timestamp'], (int, float)):
            raise PersonaValidationError(f"Message {i} timestamp must be numeric")
    
    return True