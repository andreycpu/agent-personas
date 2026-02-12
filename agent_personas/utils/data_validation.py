"""
Advanced data validation utilities for persona framework.
"""

from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Represents a validation rule."""
    name: str
    validator_function: Callable[[Any], bool]
    error_message: str
    severity: str = "error"  # error, warning, info
    required: bool = True


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    field_results: Dict[str, bool] = field(default_factory=dict)


class PersonaValidator:
    """Validates persona data against defined rules."""
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        self.logger = logging.getLogger(__name__)
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules."""
        # Name validation
        self.add_rule("name", ValidationRule(
            name="name_not_empty",
            validator_function=lambda x: isinstance(x, str) and len(x.strip()) > 0,
            error_message="Name cannot be empty",
            required=True
        ))
        
        self.add_rule("name", ValidationRule(
            name="name_length",
            validator_function=lambda x: len(x) <= 100,
            error_message="Name must be 100 characters or less",
            required=True
        ))
        
        self.add_rule("name", ValidationRule(
            name="name_format",
            validator_function=lambda x: re.match(r'^[a-zA-Z0-9_\-\s]+$', x) is not None,
            error_message="Name can only contain letters, numbers, spaces, hyphens, and underscores",
            severity="warning"
        ))
        
        # Description validation
        self.add_rule("description", ValidationRule(
            name="description_length",
            validator_function=lambda x: len(x) <= 1000,
            error_message="Description must be 1000 characters or less",
            required=True
        ))
        
        # Traits validation
        self.add_rule("traits", ValidationRule(
            name="traits_is_dict",
            validator_function=lambda x: isinstance(x, dict),
            error_message="Traits must be a dictionary",
            required=True
        ))
        
        self.add_rule("traits", ValidationRule(
            name="trait_values_valid",
            validator_function=self._validate_trait_values,
            error_message="All trait values must be between 0.0 and 1.0",
            required=True
        ))
        
        self.add_rule("traits", ValidationRule(
            name="minimum_traits",
            validator_function=lambda x: len(x) >= 1,
            error_message="Persona should have at least one trait",
            severity="warning"
        ))
        
        self.add_rule("traits", ValidationRule(
            name="trait_names_valid",
            validator_function=self._validate_trait_names,
            error_message="Trait names should only contain letters, numbers, and underscores",
            severity="warning"
        ))
        
        # Conversation style validation
        self.add_rule("conversation_style", ValidationRule(
            name="conversation_style_valid",
            validator_function=lambda x: isinstance(x, str) and len(x.strip()) > 0,
            error_message="Conversation style must be a non-empty string",
            required=True
        ))
        
        # Emotional baseline validation
        self.add_rule("emotional_baseline", ValidationRule(
            name="emotional_baseline_valid",
            validator_function=lambda x: isinstance(x, str) and len(x.strip()) > 0,
            error_message="Emotional baseline must be a non-empty string",
            required=True
        ))
    
    def add_rule(self, field: str, rule: ValidationRule):
        """Add a validation rule for a field."""
        if field not in self.rules:
            self.rules[field] = []
        self.rules[field].append(rule)
    
    def remove_rule(self, field: str, rule_name: str) -> bool:
        """Remove a validation rule."""
        if field in self.rules:
            self.rules[field] = [r for r in self.rules[field] if r.name != rule_name]
            return True
        return False
    
    def validate_persona_data(self, persona_data: Dict[str, Any]) -> ValidationResult:
        """Validate persona data dictionary."""
        result = ValidationResult(is_valid=True)
        
        for field, rules in self.rules.items():
            field_value = persona_data.get(field)
            field_valid = True
            
            for rule in rules:
                try:
                    if field_value is None and rule.required:
                        result.errors.append(f"Required field '{field}' is missing")
                        field_valid = False
                        continue
                    
                    if field_value is not None and not rule.validator_function(field_value):
                        message = f"{field}: {rule.error_message}"
                        
                        if rule.severity == "error":
                            result.errors.append(message)
                            field_valid = False
                        elif rule.severity == "warning":
                            result.warnings.append(message)
                        elif rule.severity == "info":
                            result.info.append(message)
                            
                except Exception as e:
                    result.errors.append(f"Validation error for {field}.{rule.name}: {e}")
                    field_valid = False
            
            result.field_results[field] = field_valid
            if not field_valid:
                result.is_valid = False
        
        return result
    
    def _validate_trait_values(self, traits: Dict[str, Any]) -> bool:
        """Validate that all trait values are in valid range."""
        if not isinstance(traits, dict):
            return False
        
        for trait_name, trait_value in traits.items():
            if not isinstance(trait_value, (int, float)):
                return False
            if not 0.0 <= trait_value <= 1.0:
                return False
        
        return True
    
    def _validate_trait_names(self, traits: Dict[str, Any]) -> bool:
        """Validate that trait names follow naming conventions."""
        if not isinstance(traits, dict):
            return False
        
        for trait_name in traits.keys():
            if not isinstance(trait_name, str):
                return False
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', trait_name):
                return False
        
        return True


class TemplateValidator:
    """Validates template data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_template_data(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate template data."""
        result = ValidationResult(is_valid=True)
        
        # Required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                result.errors.append(f"Required field '{field}' is missing or empty")
                result.is_valid = False
        
        # Validate base traits
        if "base_traits" in template_data:
            traits = template_data["base_traits"]
            if not isinstance(traits, dict):
                result.errors.append("base_traits must be a dictionary")
                result.is_valid = False
            else:
                for trait_name, trait_value in traits.items():
                    if not isinstance(trait_value, (int, float)):
                        result.errors.append(f"Trait value for '{trait_name}' must be numeric")
                        result.is_valid = False
                    elif not 0.0 <= trait_value <= 1.0:
                        result.errors.append(f"Trait value for '{trait_name}' must be between 0.0 and 1.0")
                        result.is_valid = False
        
        # Validate trait ranges
        if "trait_ranges" in template_data:
            ranges = template_data["trait_ranges"]
            if not isinstance(ranges, dict):
                result.errors.append("trait_ranges must be a dictionary")
                result.is_valid = False
            else:
                for trait_name, trait_range in ranges.items():
                    if not isinstance(trait_range, (list, tuple)) or len(trait_range) != 2:
                        result.errors.append(f"Trait range for '{trait_name}' must be a list/tuple of 2 values")
                        result.is_valid = False
                    else:
                        min_val, max_val = trait_range
                        if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                            result.errors.append(f"Trait range values for '{trait_name}' must be numeric")
                            result.is_valid = False
                        elif not 0.0 <= min_val <= max_val <= 1.0:
                            result.errors.append(f"Invalid trait range for '{trait_name}': [{min_val}, {max_val}]")
                            result.is_valid = False
        
        return result


class ConfigValidator:
    """Validates configuration data."""
    
    def validate_config(self, config: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate configuration against optional schema."""
        result = ValidationResult(is_valid=True)
        
        if schema is None:
            # Basic validation without schema
            return self._validate_basic_config(config)
        
        # Schema-based validation
        return self._validate_against_schema(config, schema)
    
    def _validate_basic_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Basic configuration validation."""
        result = ValidationResult(is_valid=True)
        
        # Check for common configuration issues
        for key, value in config.items():
            if value is None:
                result.warnings.append(f"Configuration key '{key}' has null value")
            elif isinstance(value, str) and len(value) == 0:
                result.warnings.append(f"Configuration key '{key}' has empty string value")
        
        return result
    
    def _validate_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema."""
        result = ValidationResult(is_valid=True)
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                result.errors.append(f"Required configuration field '{field}' is missing")
                result.is_valid = False
        
        # Check field types and constraints
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in config:
                field_result = self._validate_field_against_schema(config[field], field_schema, field)
                if field_result.errors:
                    result.errors.extend(field_result.errors)
                    result.is_valid = False
                result.warnings.extend(field_result.warnings)
        
        return result
    
    def _validate_field_against_schema(self, value: Any, schema: Dict[str, Any], field_name: str) -> ValidationResult:
        """Validate a single field against its schema."""
        result = ValidationResult(is_valid=True)
        
        # Type validation
        expected_type = schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                result.errors.append(f"Field '{field_name}' must be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                result.errors.append(f"Field '{field_name}' must be an integer")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                result.errors.append(f"Field '{field_name}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                result.errors.append(f"Field '{field_name}' must be a boolean")
            elif expected_type == "array" and not isinstance(value, list):
                result.errors.append(f"Field '{field_name}' must be an array")
            elif expected_type == "object" and not isinstance(value, dict):
                result.errors.append(f"Field '{field_name}' must be an object")
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            if "minimum" in schema and value < schema["minimum"]:
                result.errors.append(f"Field '{field_name}' must be >= {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                result.errors.append(f"Field '{field_name}' must be <= {schema['maximum']}")
        
        # Length validation for strings and arrays
        if isinstance(value, (str, list)):
            if "minLength" in schema and len(value) < schema["minLength"]:
                result.errors.append(f"Field '{field_name}' must have length >= {schema['minLength']}")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                result.errors.append(f"Field '{field_name}' must have length <= {schema['maxLength']}")
        
        # Pattern validation for strings
        if isinstance(value, str) and "pattern" in schema:
            if not re.match(schema["pattern"], value):
                result.errors.append(f"Field '{field_name}' does not match required pattern")
        
        # Enum validation
        if "enum" in schema and value not in schema["enum"]:
            result.errors.append(f"Field '{field_name}' must be one of: {schema['enum']}")
        
        return result


def validate_persona_compatibility(persona1_data: Dict[str, Any], 
                                  persona2_data: Dict[str, Any]) -> ValidationResult:
    """Validate compatibility between two personas."""
    result = ValidationResult(is_valid=True)
    
    # Check for trait conflicts
    traits1 = persona1_data.get("traits", {})
    traits2 = persona2_data.get("traits", {})
    
    # Define conflicting trait pairs
    conflicts = [
        ("introverted", "extroverted"),
        ("calm", "anxious"),
        ("organized", "chaotic"),
        ("confident", "insecure"),
        ("trusting", "suspicious")
    ]
    
    for trait1, trait2 in conflicts:
        val1 = traits1.get(trait1, 0)
        val2 = traits1.get(trait2, 0)
        val3 = traits2.get(trait1, 0)
        val4 = traits2.get(trait2, 0)
        
        # Check for high values in conflicting traits within same persona
        if val1 > 0.7 and val2 > 0.7:
            result.warnings.append(f"Persona 1 has conflicting traits: {trait1} and {trait2}")
        
        if val3 > 0.7 and val4 > 0.7:
            result.warnings.append(f"Persona 2 has conflicting traits: {trait1} and {trait2}")
        
        # Check for conflicts between personas
        if (val1 > 0.7 and val4 > 0.7) or (val2 > 0.7 and val3 > 0.7):
            result.warnings.append(f"Personas have conflicting traits: {trait1}/{trait2}")
    
    # Check conversation style compatibility
    style1 = persona1_data.get("conversation_style", "")
    style2 = persona2_data.get("conversation_style", "")
    
    incompatible_styles = [
        ("formal", "casual"),
        ("professional", "playful"),
        ("analytical", "emotional")
    ]
    
    for style_a, style_b in incompatible_styles:
        if (style_a in style1.lower() and style_b in style2.lower()) or \
           (style_b in style1.lower() and style_a in style2.lower()):
            result.warnings.append(f"Incompatible conversation styles: {style1} vs {style2}")
    
    return result