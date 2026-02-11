"""
Configuration validation utilities for the persona framework.
"""

from typing import Dict, Any, List, Union, Optional
import re


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, errors: Optional[List[str]] = None):
        self.message = message
        self.field = field
        self.errors = errors or []
        super().__init__(self.message)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate complete configuration dictionary.
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if valid
        
    Raises:
        ConfigValidationError: If validation fails
    """
    errors = []
    
    # Validate each section
    sections = [
        ("framework", validate_framework_config),
        ("personas", validate_personas_config),
        ("traits", validate_traits_config),
        ("behaviors", validate_behaviors_config),
        ("emotions", validate_emotions_config),
        ("conversation", validate_conversation_config),
        ("switching", validate_switching_config),
        ("performance", validate_performance_config),
        ("logging", validate_logging_config),
        ("storage", validate_storage_config),
        ("security", validate_security_config)
    ]
    
    for section_name, validator in sections:
        if section_name in config:
            try:
                validator(config[section_name])
            except ConfigValidationError as e:
                errors.extend([f"{section_name}.{error}" for error in e.errors])
    
    if errors:
        raise ConfigValidationError("Configuration validation failed", errors=errors)
    
    return True


def validate_framework_config(config: Dict[str, Any]) -> bool:
    """Validate framework configuration section."""
    errors = []
    
    if "version" in config:
        if not isinstance(config["version"], str):
            errors.append("version must be a string")
        elif not re.match(r'^\d+\.\d+\.\d+', config["version"]):
            errors.append("version must follow semantic versioning (x.y.z)")
    
    if "max_history_size" in config:
        if not isinstance(config["max_history_size"], int) or config["max_history_size"] <= 0:
            errors.append("max_history_size must be a positive integer")
    
    if errors:
        raise ConfigValidationError("Framework config validation failed", errors=errors)
    
    return True


def validate_personas_config(config: Dict[str, Any]) -> bool:
    """Validate personas configuration section."""
    errors = []
    
    if "min_traits" in config:
        if not isinstance(config["min_traits"], int) or config["min_traits"] < 0:
            errors.append("min_traits must be a non-negative integer")
    
    if "max_traits" in config:
        if not isinstance(config["max_traits"], int) or config["max_traits"] <= 0:
            errors.append("max_traits must be a positive integer")
    
    if "min_traits" in config and "max_traits" in config:
        if config["min_traits"] > config["max_traits"]:
            errors.append("min_traits cannot be greater than max_traits")
    
    if errors:
        raise ConfigValidationError("Personas config validation failed", errors=errors)
    
    return True


def validate_traits_config(config: Dict[str, Any]) -> bool:
    """Validate traits configuration section."""
    errors = []
    
    if "default_trait_value" in config:
        value = config["default_trait_value"]
        if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
            errors.append("default_trait_value must be a number between 0.0 and 1.0")
    
    if "trait_bounds" in config:
        bounds = config["trait_bounds"]
        if not isinstance(bounds, dict):
            errors.append("trait_bounds must be a dictionary")
        else:
            if "min" in bounds and "max" in bounds:
                if bounds["min"] >= bounds["max"]:
                    errors.append("trait_bounds.min must be less than trait_bounds.max")
            
            if "min" in bounds:
                if not isinstance(bounds["min"], (int, float)):
                    errors.append("trait_bounds.min must be a number")
            
            if "max" in bounds:
                if not isinstance(bounds["max"], (int, float)):
                    errors.append("trait_bounds.max must be a number")
    
    if errors:
        raise ConfigValidationError("Traits config validation failed", errors=errors)
    
    return True


def validate_behaviors_config(config: Dict[str, Any]) -> bool:
    """Validate behaviors configuration section."""
    errors = []
    
    if "max_rules" in config:
        if not isinstance(config["max_rules"], int) or config["max_rules"] <= 0:
            errors.append("max_rules must be a positive integer")
    
    if "execution_timeout" in config:
        timeout = config["execution_timeout"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("execution_timeout must be a positive number")
    
    if "priority_range" in config:
        priority_range = config["priority_range"]
        if not isinstance(priority_range, list) or len(priority_range) != 2:
            errors.append("priority_range must be a list with exactly 2 elements")
        elif not all(isinstance(x, int) for x in priority_range):
            errors.append("priority_range elements must be integers")
        elif priority_range[0] >= priority_range[1]:
            errors.append("priority_range[0] must be less than priority_range[1]")
    
    if errors:
        raise ConfigValidationError("Behaviors config validation failed", errors=errors)
    
    return True


def validate_emotions_config(config: Dict[str, Any]) -> bool:
    """Validate emotions configuration section."""
    errors = []
    
    if "decay_rate" in config:
        rate = config["decay_rate"]
        if not isinstance(rate, (int, float)) or not 0.0 <= rate <= 1.0:
            errors.append("decay_rate must be a number between 0.0 and 1.0")
    
    if "sensitivity" in config:
        sensitivity = config["sensitivity"]
        if not isinstance(sensitivity, (int, float)) or not 0.0 <= sensitivity <= 1.0:
            errors.append("sensitivity must be a number between 0.0 and 1.0")
    
    if "decay_interval_minutes" in config:
        interval = config["decay_interval_minutes"]
        if not isinstance(interval, (int, float)) or interval <= 0:
            errors.append("decay_interval_minutes must be a positive number")
    
    if "max_intensity" in config:
        intensity = config["max_intensity"]
        if not isinstance(intensity, (int, float)) or intensity <= 0:
            errors.append("max_intensity must be a positive number")
    
    if errors:
        raise ConfigValidationError("Emotions config validation failed", errors=errors)
    
    return True


def validate_conversation_config(config: Dict[str, Any]) -> bool:
    """Validate conversation configuration section."""
    errors = []
    
    if "context_memory_size" in config:
        size = config["context_memory_size"]
        if not isinstance(size, int) or size <= 0:
            errors.append("context_memory_size must be a positive integer")
    
    if "max_conversation_length" in config:
        length = config["max_conversation_length"]
        if not isinstance(length, int) or length <= 0:
            errors.append("max_conversation_length must be a positive integer")
    
    if "response_timeout" in config:
        timeout = config["response_timeout"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("response_timeout must be a positive number")
    
    if errors:
        raise ConfigValidationError("Conversation config validation failed", errors=errors)
    
    return True


def validate_switching_config(config: Dict[str, Any]) -> bool:
    """Validate switching configuration section."""
    errors = []
    
    if "max_switches_per_hour" in config:
        max_switches = config["max_switches_per_hour"]
        if not isinstance(max_switches, int) or max_switches <= 0:
            errors.append("max_switches_per_hour must be a positive integer")
    
    if "cooldown_seconds" in config:
        cooldown = config["cooldown_seconds"]
        if not isinstance(cooldown, (int, float)) or cooldown < 0:
            errors.append("cooldown_seconds must be a non-negative number")
    
    if errors:
        raise ConfigValidationError("Switching config validation failed", errors=errors)
    
    return True


def validate_performance_config(config: Dict[str, Any]) -> bool:
    """Validate performance configuration section."""
    errors = []
    
    if "cache_size" in config:
        size = config["cache_size"]
        if not isinstance(size, int) or size <= 0:
            errors.append("cache_size must be a positive integer")
    
    if "batch_size" in config:
        size = config["batch_size"]
        if not isinstance(size, int) or size <= 0:
            errors.append("batch_size must be a positive integer")
    
    if "memory_limit_mb" in config:
        limit = config["memory_limit_mb"]
        if not isinstance(limit, (int, float)) or limit <= 0:
            errors.append("memory_limit_mb must be a positive number")
    
    if "timeout_seconds" in config:
        timeout = config["timeout_seconds"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("timeout_seconds must be a positive number")
    
    if errors:
        raise ConfigValidationError("Performance config validation failed", errors=errors)
    
    return True


def validate_logging_config(config: Dict[str, Any]) -> bool:
    """Validate logging configuration section."""
    errors = []
    
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    if "level" in config:
        level = config["level"].upper() if isinstance(config["level"], str) else config["level"]
        if level not in valid_levels:
            errors.append(f"level must be one of {valid_levels}")
    
    if "max_file_size_mb" in config:
        size = config["max_file_size_mb"]
        if not isinstance(size, (int, float)) or size <= 0:
            errors.append("max_file_size_mb must be a positive number")
    
    if "backup_count" in config:
        count = config["backup_count"]
        if not isinstance(count, int) or count < 0:
            errors.append("backup_count must be a non-negative integer")
    
    if errors:
        raise ConfigValidationError("Logging config validation failed", errors=errors)
    
    return True


def validate_storage_config(config: Dict[str, Any]) -> bool:
    """Validate storage configuration section."""
    errors = []
    
    if "backup_frequency_hours" in config:
        frequency = config["backup_frequency_hours"]
        if not isinstance(frequency, (int, float)) or frequency <= 0:
            errors.append("backup_frequency_hours must be a positive number")
    
    valid_formats = ["json", "yaml", "yml", "pickle"]
    if "format" in config:
        fmt = config["format"]
        if not isinstance(fmt, str) or fmt not in valid_formats:
            errors.append(f"format must be one of {valid_formats}")
    
    if errors:
        raise ConfigValidationError("Storage config validation failed", errors=errors)
    
    return True


def validate_security_config(config: Dict[str, Any]) -> bool:
    """Validate security configuration section."""
    errors = []
    
    if "max_input_length" in config:
        length = config["max_input_length"]
        if not isinstance(length, int) or length <= 0:
            errors.append("max_input_length must be a positive integer")
    
    if "allowed_file_types" in config:
        file_types = config["allowed_file_types"]
        if not isinstance(file_types, list):
            errors.append("allowed_file_types must be a list")
        elif not all(isinstance(ft, str) and ft.startswith('.') for ft in file_types):
            errors.append("allowed_file_types must be a list of file extensions starting with '.'")
    
    if errors:
        raise ConfigValidationError("Security config validation failed", errors=errors)
    
    return True


def validate_persona_definition(persona_data: Dict[str, Any]) -> bool:
    """
    Validate a persona definition dictionary.
    
    Args:
        persona_data: Persona definition to validate
        
    Returns:
        True if valid
        
    Raises:
        ConfigValidationError: If validation fails
    """
    errors = []
    
    # Required fields
    if "name" not in persona_data:
        errors.append("name is required")
    elif not isinstance(persona_data["name"], str) or not persona_data["name"].strip():
        errors.append("name must be a non-empty string")
    
    # Optional but validated fields
    if "description" in persona_data:
        if not isinstance(persona_data["description"], str):
            errors.append("description must be a string")
        elif len(persona_data["description"]) > 1000:
            errors.append("description cannot exceed 1000 characters")
    
    if "traits" in persona_data:
        traits = persona_data["traits"]
        if not isinstance(traits, dict):
            errors.append("traits must be a dictionary")
        else:
            for trait_name, trait_value in traits.items():
                if not isinstance(trait_name, str):
                    errors.append(f"trait name '{trait_name}' must be a string")
                elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', trait_name):
                    errors.append(f"trait name '{trait_name}' contains invalid characters")
                
                if not isinstance(trait_value, (int, float)):
                    errors.append(f"trait value for '{trait_name}' must be a number")
                elif not 0.0 <= trait_value <= 1.0:
                    errors.append(f"trait value for '{trait_name}' must be between 0.0 and 1.0")
    
    if "conversation_style" in persona_data:
        style = persona_data["conversation_style"]
        if not isinstance(style, str) or not style.strip():
            errors.append("conversation_style must be a non-empty string")
    
    if "emotional_baseline" in persona_data:
        baseline = persona_data["emotional_baseline"]
        if not isinstance(baseline, str) or not baseline.strip():
            errors.append("emotional_baseline must be a non-empty string")
    
    if "metadata" in persona_data:
        if not isinstance(persona_data["metadata"], dict):
            errors.append("metadata must be a dictionary")
    
    if errors:
        raise ConfigValidationError("Persona definition validation failed", errors=errors)
    
    return True


def validate_behavior_rule(rule_data: Dict[str, Any]) -> bool:
    """
    Validate a behavior rule definition.
    
    Args:
        rule_data: Behavior rule to validate
        
    Returns:
        True if valid
        
    Raises:
        ConfigValidationError: If validation fails
    """
    errors = []
    
    # Required fields
    if "name" not in rule_data:
        errors.append("name is required")
    elif not isinstance(rule_data["name"], str) or not rule_data["name"].strip():
        errors.append("name must be a non-empty string")
    
    if "conditions" in rule_data:
        conditions = rule_data["conditions"]
        if not isinstance(conditions, list):
            errors.append("conditions must be a list")
        else:
            for i, condition in enumerate(conditions):
                if not isinstance(condition, dict):
                    errors.append(f"condition[{i}] must be a dictionary")
                elif "type" not in condition:
                    errors.append(f"condition[{i}] must have a 'type' field")
    
    if "actions" in rule_data:
        actions = rule_data["actions"]
        if not isinstance(actions, list):
            errors.append("actions must be a list")
        else:
            for i, action in enumerate(actions):
                if not isinstance(action, dict):
                    errors.append(f"action[{i}] must be a dictionary")
                elif "type" not in action:
                    errors.append(f"action[{i}] must have a 'type' field")
    
    if "priority" in rule_data:
        priority = rule_data["priority"]
        if not isinstance(priority, int):
            errors.append("priority must be an integer")
    
    if errors:
        raise ConfigValidationError("Behavior rule validation failed", errors=errors)
    
    return True


def get_validation_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a validation summary for configuration.
    
    Args:
        config: Configuration to analyze
        
    Returns:
        Validation summary with scores and recommendations
    """
    summary = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "completeness_score": 0.0,
        "sections": {}
    }
    
    try:
        validate_config(config)
        summary["valid"] = True
    except ConfigValidationError as e:
        summary["valid"] = False
        summary["errors"] = e.errors
    
    # Calculate completeness
    expected_sections = [
        "framework", "personas", "traits", "behaviors", 
        "emotions", "conversation", "switching", "performance",
        "logging", "storage", "security"
    ]
    
    present_sections = [section for section in expected_sections if section in config]
    summary["completeness_score"] = len(present_sections) / len(expected_sections)
    
    # Analyze each section
    for section in expected_sections:
        summary["sections"][section] = {
            "present": section in config,
            "valid": True,
            "errors": []
        }
        
        if section in config:
            try:
                validator_map = {
                    "framework": validate_framework_config,
                    "personas": validate_personas_config,
                    "traits": validate_traits_config,
                    "behaviors": validate_behaviors_config,
                    "emotions": validate_emotions_config,
                    "conversation": validate_conversation_config,
                    "switching": validate_switching_config,
                    "performance": validate_performance_config,
                    "logging": validate_logging_config,
                    "storage": validate_storage_config,
                    "security": validate_security_config
                }
                
                if section in validator_map:
                    validator_map[section](config[section])
            except ConfigValidationError as e:
                summary["sections"][section]["valid"] = False
                summary["sections"][section]["errors"] = e.errors
    
    # Generate recommendations
    if summary["completeness_score"] < 0.8:
        summary["recommendations"].append("Consider adding missing configuration sections")
    
    if summary["errors"]:
        summary["recommendations"].append("Fix validation errors before using configuration")
    
    return summary