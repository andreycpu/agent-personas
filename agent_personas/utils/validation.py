"""
Validation utilities for persona data and configurations.
"""

from typing import Dict, List, Any, Tuple, Optional
import re
from ..core.persona import Persona


def validate_trait_values(
    traits: Dict[str, float], 
    allow_empty: bool = True,
    min_value: float = 0.0,
    max_value: float = 1.0
) -> Tuple[bool, List[str]]:
    """
    Validate trait values against standard constraints.
    
    Args:
        traits: Dictionary of trait names to values
        allow_empty: Whether empty trait dictionaries are valid
        min_value: Minimum allowed trait value
        max_value: Maximum allowed trait value
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not traits and not allow_empty:
        errors.append("Trait dictionary cannot be empty")
        return False, errors
    
    for trait_name, value in traits.items():
        # Validate trait name
        if not isinstance(trait_name, str):
            errors.append(f"Trait name must be string, got {type(trait_name)}")
            continue
            
        if not trait_name.strip():
            errors.append("Trait name cannot be empty or whitespace")
            continue
            
        # Validate trait name format (letters, numbers, underscores only)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', trait_name):
            errors.append(f"Invalid trait name format: '{trait_name}' (must start with letter, contain only letters, numbers, underscores)")
        
        # Validate trait value
        if not isinstance(value, (int, float)):
            errors.append(f"Trait value for '{trait_name}' must be numeric, got {type(value)}")
            continue
            
        if not min_value <= value <= max_value:
            errors.append(f"Trait value for '{trait_name}' ({value}) must be between {min_value} and {max_value}")
    
    return len(errors) == 0, errors


def validate_persona_data(persona_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate persona data dictionary for completeness and correctness.
    
    Args:
        persona_data: Dictionary containing persona configuration
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = ["name"]
    for field in required_fields:
        if field not in persona_data:
            errors.append(f"Required field '{field}' is missing")
        elif not persona_data[field]:
            errors.append(f"Required field '{field}' cannot be empty")
    
    # Validate name
    if "name" in persona_data:
        name = persona_data["name"]
        if not isinstance(name, str):
            errors.append(f"Persona name must be string, got {type(name)}")
        elif len(name.strip()) == 0:
            errors.append("Persona name cannot be empty")
        elif len(name) > 100:
            errors.append("Persona name cannot exceed 100 characters")
        elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_\- ]*$', name):
            errors.append("Persona name contains invalid characters")
    
    # Validate description
    if "description" in persona_data:
        description = persona_data["description"]
        if not isinstance(description, str):
            errors.append(f"Description must be string, got {type(description)}")
        elif len(description) > 1000:
            errors.append("Description cannot exceed 1000 characters")
    
    # Validate traits
    if "traits" in persona_data:
        traits = persona_data["traits"]
        if not isinstance(traits, dict):
            errors.append(f"Traits must be dictionary, got {type(traits)}")
        else:
            trait_valid, trait_errors = validate_trait_values(traits)
            errors.extend(trait_errors)
    
    # Validate conversation_style
    if "conversation_style" in persona_data:
        style = persona_data["conversation_style"]
        if not isinstance(style, str):
            errors.append(f"Conversation style must be string, got {type(style)}")
        elif not style.strip():
            errors.append("Conversation style cannot be empty")
    
    # Validate emotional_baseline
    if "emotional_baseline" in persona_data:
        baseline = persona_data["emotional_baseline"]
        if not isinstance(baseline, str):
            errors.append(f"Emotional baseline must be string, got {type(baseline)}")
        elif not baseline.strip():
            errors.append("Emotional baseline cannot be empty")
    
    # Validate metadata
    if "metadata" in persona_data:
        metadata = persona_data["metadata"]
        if not isinstance(metadata, dict):
            errors.append(f"Metadata must be dictionary, got {type(metadata)}")
    
    return len(errors) == 0, errors


def validate_persona_instance(persona: Persona) -> Tuple[bool, List[str]]:
    """
    Validate a Persona instance for completeness and consistency.
    
    Args:
        persona: Persona instance to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate using persona data
    persona_data = persona.to_dict()
    data_valid, data_errors = validate_persona_data(persona_data)
    errors.extend(data_errors)
    
    # Additional instance-specific validations
    
    # Check timestamps
    if persona.created_at > persona.last_modified:
        errors.append("Last modified timestamp cannot be before created timestamp")
    
    # Check trait consistency
    for trait_name, value in persona.traits.items():
        # Test getter consistency
        if persona.get_trait(trait_name) != value:
            errors.append(f"Trait getter/setter inconsistency for '{trait_name}'")
    
    return len(errors) == 0, errors


def validate_conversation_context(context: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate conversation context dictionary.
    
    Args:
        context: Context dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for common context keys and their types
    type_expectations = {
        "user_input": str,
        "user_emotion": str,
        "topic": str,
        "urgency": str,
        "formality": (int, float),
        "conversation_turn_count": int,
        "session_id": str
    }
    
    for key, expected_type in type_expectations.items():
        if key in context:
            value = context[key]
            if not isinstance(value, expected_type):
                errors.append(f"Context '{key}' expected {expected_type.__name__}, got {type(value).__name__}")
    
    # Validate specific values
    if "urgency" in context:
        valid_urgency = ["low", "normal", "high", "critical"]
        if context["urgency"] not in valid_urgency:
            errors.append(f"Invalid urgency value: {context['urgency']}. Must be one of {valid_urgency}")
    
    if "formality" in context:
        formality = context["formality"]
        if isinstance(formality, (int, float)) and not -1.0 <= formality <= 1.0:
            errors.append(f"Formality value {formality} must be between -1.0 and 1.0")
    
    if "conversation_turn_count" in context:
        turn_count = context["conversation_turn_count"]
        if turn_count < 0:
            errors.append(f"Conversation turn count cannot be negative: {turn_count}")
    
    return len(errors) == 0, errors


def validate_trait_constraints(
    traits: Dict[str, float],
    constraints: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate traits against custom constraints.
    
    Args:
        traits: Trait values to validate
        constraints: Custom constraint definitions
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not constraints:
        return True, errors
    
    # Check mutual exclusions
    mutual_exclusions = constraints.get("mutual_exclusions", [])
    for exclusion_group in mutual_exclusions:
        high_traits = [
            trait for trait in exclusion_group 
            if traits.get(trait, 0) > 0.7
        ]
        if len(high_traits) > 1:
            errors.append(f"Mutually exclusive traits cannot both be high: {', '.join(high_traits)}")
    
    # Check dependencies
    dependencies = constraints.get("dependencies", {})
    for trait, required_traits in dependencies.items():
        if traits.get(trait, 0) > 0.5:  # If trait is present
            for required in required_traits:
                if traits.get(required, 0) < 0.3:  # Required trait is absent
                    errors.append(f"Trait '{trait}' requires trait '{required}' to be present")
    
    # Check minimum totals
    min_totals = constraints.get("minimum_totals", {})
    for group_name, (trait_list, min_total) in min_totals.items():
        total = sum(traits.get(trait, 0) for trait in trait_list)
        if total < min_total:
            errors.append(f"Trait group '{group_name}' total ({total:.2f}) below minimum ({min_total})")
    
    # Check maximum totals
    max_totals = constraints.get("maximum_totals", {})
    for group_name, (trait_list, max_total) in max_totals.items():
        total = sum(traits.get(trait, 0) for trait in trait_list)
        if total > max_total:
            errors.append(f"Trait group '{group_name}' total ({total:.2f}) exceeds maximum ({max_total})")
    
    return len(errors) == 0, errors


def suggest_trait_fixes(
    traits: Dict[str, float], 
    errors: List[str]
) -> Dict[str, Any]:
    """
    Suggest fixes for trait validation errors.
    
    Args:
        traits: Original trait values
        errors: Validation errors
        
    Returns:
        Dictionary with suggested fixes
    """
    suggestions = {
        "fixes": [],
        "adjusted_traits": traits.copy(),
        "warnings": []
    }
    
    # Analyze errors and suggest fixes
    for error in errors:
        if "must be between" in error:
            # Extract trait name and suggested range
            parts = error.split("'")
            if len(parts) >= 2:
                trait_name = parts[1]
                if trait_name in traits:
                    current_value = traits[trait_name]
                    if current_value > 1.0:
                        suggestions["fixes"].append(f"Clamp {trait_name} to 1.0 (was {current_value})")
                        suggestions["adjusted_traits"][trait_name] = 1.0
                    elif current_value < 0.0:
                        suggestions["fixes"].append(f"Clamp {trait_name} to 0.0 (was {current_value})")
                        suggestions["adjusted_traits"][trait_name] = 0.0
        
        elif "Mutually exclusive traits" in error:
            # Suggest reducing conflicting traits
            suggestions["warnings"].append("Consider adjusting conflicting traits to avoid mutual exclusions")
        
        elif "requires" in error and "to be present" in error:
            # Suggest adding required traits
            suggestions["warnings"].append("Consider adding required traits for dependencies")
    
    return suggestions


def get_validation_summary(
    persona_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get a comprehensive validation summary for persona data.
    
    Args:
        persona_data: Persona data to analyze
        
    Returns:
        Validation summary with scores and recommendations
    """
    summary = {
        "overall_valid": True,
        "validation_score": 1.0,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "completeness_score": 0.0
    }
    
    # Validate data
    is_valid, errors = validate_persona_data(persona_data)
    summary["overall_valid"] = is_valid
    summary["errors"] = errors
    
    # Calculate validation score
    if errors:
        summary["validation_score"] = max(0.0, 1.0 - len(errors) * 0.1)
    
    # Calculate completeness score
    optional_fields = ["description", "traits", "conversation_style", "emotional_baseline", "metadata"]
    completed_fields = sum(1 for field in optional_fields if field in persona_data and persona_data[field])
    summary["completeness_score"] = completed_fields / len(optional_fields)
    
    # Generate recommendations
    if summary["completeness_score"] < 0.7:
        summary["recommendations"].append("Consider adding more persona details for richer personality")
    
    if "traits" in persona_data and len(persona_data["traits"]) < 3:
        summary["recommendations"].append("Consider adding more traits to define personality more clearly")
    
    if summary["validation_score"] < 1.0:
        summary["recommendations"].append("Fix validation errors before using persona")
    
    return summary