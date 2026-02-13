"""
Interactive configuration builder for creating persona configurations.
"""

import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from .exceptions import PersonaValidationError
from .validation import validate_persona_traits, validate_persona_name
from .templates import template_registry


@dataclass
class ConfigSection:
    """A section of configuration with validation."""
    name: str
    description: str
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required: bool = False
    validator: Optional[Callable] = None


class PersonaConfigBuilder:
    """Interactive builder for persona configurations."""
    
    def __init__(self):
        """Initialize config builder."""
        self.config: Dict[str, Any] = {}
        self.sections: Dict[str, ConfigSection] = {}
        self._setup_sections()
    
    def _setup_sections(self):
        """Setup configuration sections."""
        
        # Basic Information Section
        basic_section = ConfigSection(
            name="basic",
            description="Basic persona information",
            required=True
        )
        basic_section.fields = {
            "name": {
                "type": "string",
                "description": "Persona name (1-100 characters)",
                "required": True,
                "validator": validate_persona_name,
                "example": "Technical Assistant"
            },
            "description": {
                "type": "string", 
                "description": "Brief description of the persona",
                "required": False,
                "example": "A helpful technical assistant for programming tasks"
            },
            "version": {
                "type": "string",
                "description": "Persona version",
                "default": "1.0",
                "example": "1.0"
            }
        }
        self.sections["basic"] = basic_section
        
        # Personality Section
        personality_section = ConfigSection(
            name="personality",
            description="Personality traits (values between 0.0 and 1.0)",
            required=True
        )
        personality_section.fields = {
            "extroversion": {
                "type": "float",
                "description": "How outgoing and social (0.0 = introverted, 1.0 = extroverted)",
                "range": [0.0, 1.0],
                "default": 0.5,
                "example": 0.7
            },
            "openness": {
                "type": "float",
                "description": "Openness to new experiences (0.0 = conventional, 1.0 = innovative)",
                "range": [0.0, 1.0],
                "default": 0.7,
                "example": 0.8
            },
            "conscientiousness": {
                "type": "float",
                "description": "Organization and dependability (0.0 = spontaneous, 1.0 = organized)",
                "range": [0.0, 1.0],
                "default": 0.6,
                "example": 0.8
            },
            "agreeableness": {
                "type": "float",
                "description": "Cooperation and trust (0.0 = competitive, 1.0 = cooperative)",
                "range": [0.0, 1.0],
                "default": 0.7,
                "example": 0.8
            },
            "neuroticism": {
                "type": "float",
                "description": "Emotional stability (0.0 = stable, 1.0 = anxious)",
                "range": [0.0, 1.0],
                "default": 0.3,
                "example": 0.2
            }
        }
        self.sections["personality"] = personality_section
        
        # Communication Section
        communication_section = ConfigSection(
            name="communication",
            description="Communication style and preferences"
        )
        communication_section.fields = {
            "style": {
                "type": "choice",
                "description": "Primary communication style",
                "choices": ["formal", "casual", "friendly", "professional", "technical"],
                "required": True,
                "example": "professional"
            },
            "verbosity": {
                "type": "float",
                "description": "How verbose responses should be (0.0 = concise, 1.0 = detailed)",
                "range": [0.0, 1.0],
                "default": 0.6,
                "example": 0.7
            },
            "formality": {
                "type": "float",
                "description": "Level of formality (0.0 = informal, 1.0 = very formal)",
                "range": [0.0, 1.0],
                "default": 0.5,
                "example": 0.6
            },
            "empathy": {
                "type": "float",
                "description": "Empathetic response level (0.0 = logical, 1.0 = emotional)",
                "range": [0.0, 1.0],
                "default": 0.5,
                "example": 0.8
            }
        }
        self.sections["communication"] = communication_section
        
        # Knowledge Section
        knowledge_section = ConfigSection(
            name="knowledge",
            description="Areas of knowledge and expertise"
        )
        knowledge_section.fields = {
            "areas": {
                "type": "list",
                "description": "List of knowledge areas",
                "item_type": "string",
                "required": True,
                "example": ["technology", "programming", "software_engineering"]
            },
            "expertise_level": {
                "type": "choice",
                "description": "Overall expertise level",
                "choices": ["beginner", "intermediate", "advanced", "expert"],
                "default": "intermediate",
                "example": "advanced"
            },
            "specializations": {
                "type": "list",
                "description": "Specific specializations within knowledge areas",
                "item_type": "string",
                "required": False,
                "example": ["web_development", "machine_learning"]
            }
        }
        self.sections["knowledge"] = knowledge_section
    
    def start_interactive_build(self) -> Dict[str, Any]:
        """Start interactive configuration building."""
        print("🤖 Persona Configuration Builder")
        print("=" * 40)
        print("Let's build your persona configuration step by step.\n")
        
        # Check if user wants to use a template
        use_template = self._ask_yes_no("Would you like to start with a template?")
        
        if use_template:
            template_config = self._select_template()
            if template_config:
                self.config = template_config
                print("\n✅ Template loaded! You can now customize the configuration.\n")
        
        # Go through each section
        for section_name, section in self.sections.items():
            self._build_section(section)
        
        # Validate final configuration
        try:
            self._validate_configuration()
            print("\n✅ Configuration is valid!")
        except Exception as e:
            print(f"\n❌ Configuration validation failed: {e}")
            if self._ask_yes_no("Would you like to review and fix the issues?"):
                return self.start_interactive_build()
        
        return self.config
    
    def _select_template(self) -> Optional[Dict[str, Any]]:
        """Allow user to select a template."""
        templates = template_registry.list_templates()
        
        if not templates:
            print("No templates available.")
            return None
        
        print("\nAvailable templates:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template['name']}: {template['description']}")
        
        while True:
            try:
                choice = input(f"\nSelect template (1-{len(templates)}) or 'skip': ").strip()
                
                if choice.lower() == 'skip':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    template_name = templates[index]['name']
                    
                    # Get template variables
                    from .templates import get_template_info, _extract_template_variables
                    template = template_registry.get(template_name)
                    variables = _extract_template_variables(template.template_data)
                    
                    if variables:
                        print(f"\nTemplate '{template_name}' requires these variables:")
                        var_values = {}
                        for var in variables:
                            value = input(f"  {var}: ").strip()
                            if value:
                                var_values[var] = value
                        
                        return template.render(var_values)
                    else:
                        return template.render()
                else:
                    print("Invalid selection.")
                    
            except ValueError:
                print("Please enter a valid number or 'skip'.")
            except Exception as e:
                print(f"Error loading template: {e}")
                return None
    
    def _build_section(self, section: ConfigSection):
        """Build a configuration section interactively."""
        print(f"\n📋 {section.name.title()} Section")
        print("-" * 30)
        print(f"{section.description}\n")
        
        section_config = self.config.get(section.name, {})
        
        for field_name, field_info in section.fields.items():
            current_value = self._get_nested_value(field_name, section_config)
            new_value = self._get_field_value(field_name, field_info, current_value)
            
            if new_value is not None:
                self._set_nested_value(section.name, field_name, new_value)
    
    def _get_field_value(self, field_name: str, field_info: Dict[str, Any], current_value: Any = None) -> Any:
        """Get value for a configuration field."""
        field_type = field_info.get("type", "string")
        description = field_info.get("description", "")
        required = field_info.get("required", False)
        default = field_info.get("default")
        example = field_info.get("example")
        
        # Show current value if available
        current_display = f" (current: {current_value})" if current_value is not None else ""
        default_display = f" [default: {default}]" if default else ""
        example_display = f" (example: {example})" if example else ""
        
        prompt = f"{field_name}: {description}{current_display}{default_display}{example_display}"
        
        if required:
            prompt += " *required*"
        
        print(prompt)
        
        if field_type == "string":
            return self._get_string_value(field_info, current_value, default)
        elif field_type == "float":
            return self._get_float_value(field_info, current_value, default)
        elif field_type == "choice":
            return self._get_choice_value(field_info, current_value, default)
        elif field_type == "list":
            return self._get_list_value(field_info, current_value, default)
        else:
            # Fallback to string input
            return self._get_string_value(field_info, current_value, default)
    
    def _get_string_value(self, field_info: Dict[str, Any], current_value: Any, default: Any) -> Optional[str]:
        """Get string value from user input."""
        while True:
            value = input("  > ").strip()
            
            if not value:
                if current_value is not None:
                    return current_value
                elif default is not None:
                    return default
                elif field_info.get("required", False):
                    print("  This field is required.")
                    continue
                else:
                    return None
            
            # Validate if validator is provided
            validator = field_info.get("validator")
            if validator:
                try:
                    validator(value)
                    return value
                except Exception as e:
                    print(f"  Invalid value: {e}")
                    continue
            
            return value
    
    def _get_float_value(self, field_info: Dict[str, Any], current_value: Any, default: Any) -> Optional[float]:
        """Get float value from user input."""
        range_info = field_info.get("range", [])
        
        while True:
            value_str = input("  > ").strip()
            
            if not value_str:
                if current_value is not None:
                    return current_value
                elif default is not None:
                    return default
                elif field_info.get("required", False):
                    print("  This field is required.")
                    continue
                else:
                    return None
            
            try:
                value = float(value_str)
                
                # Check range
                if range_info and len(range_info) >= 2:
                    min_val, max_val = range_info[0], range_info[1]
                    if not (min_val <= value <= max_val):
                        print(f"  Value must be between {min_val} and {max_val}")
                        continue
                
                return value
                
            except ValueError:
                print("  Please enter a valid number.")
    
    def _get_choice_value(self, field_info: Dict[str, Any], current_value: Any, default: Any) -> Optional[str]:
        """Get choice value from user input."""
        choices = field_info.get("choices", [])
        
        print(f"    Choices: {', '.join(choices)}")
        
        while True:
            value = input("  > ").strip().lower()
            
            if not value:
                if current_value is not None:
                    return current_value
                elif default is not None:
                    return default
                elif field_info.get("required", False):
                    print("  This field is required.")
                    continue
                else:
                    return None
            
            # Find matching choice (case insensitive)
            for choice in choices:
                if choice.lower() == value:
                    return choice
            
            print(f"  Invalid choice. Please select from: {', '.join(choices)}")
    
    def _get_list_value(self, field_info: Dict[str, Any], current_value: Any, default: Any) -> Optional[List[str]]:
        """Get list value from user input."""
        print("    Enter items one per line. Press Enter on empty line to finish.")
        
        if current_value:
            print(f"    Current items: {', '.join(current_value)}")
            if self._ask_yes_no("    Keep current items and add more?"):
                items = list(current_value)
            else:
                items = []
        else:
            items = []
        
        while True:
            item = input("    + ").strip()
            
            if not item:
                break
            
            if item not in items:
                items.append(item)
            else:
                print("      Item already added.")
        
        if not items:
            if default:
                return default
            elif field_info.get("required", False):
                print("  At least one item is required.")
                return self._get_list_value(field_info, current_value, default)
        
        return items if items else None
    
    def _get_nested_value(self, key_path: str, config: Dict[str, Any]) -> Any:
        """Get nested value from config using dot notation."""
        keys = key_path.split(".")
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, section: str, key_path: str, value: Any):
        """Set nested value in config using dot notation."""
        if section not in self.config:
            self.config[section] = {}
        
        keys = key_path.split(".")
        target = self.config[section]
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
    
    def _ask_yes_no(self, question: str) -> bool:
        """Ask a yes/no question."""
        while True:
            answer = input(f"{question} (y/n): ").strip().lower()
            if answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'.")
    
    def _validate_configuration(self):
        """Validate the final configuration."""
        # Transform config to expected format
        persona_config = self._transform_config_format()
        
        # Validate using existing validators
        if "name" in persona_config:
            validate_persona_name(persona_config["name"])
        
        if "traits" in persona_config:
            validate_persona_traits(persona_config["traits"])
    
    def _transform_config_format(self) -> Dict[str, Any]:
        """Transform builder config to standard persona format."""
        persona_config = {}
        
        # Basic info
        if "basic" in self.config:
            basic = self.config["basic"]
            if "name" in basic:
                persona_config["name"] = basic["name"]
            if "description" in basic:
                persona_config["description"] = basic["description"]
            if "version" in basic:
                persona_config["version"] = basic["version"]
        
        # Traits
        traits = {}
        
        # Personality traits
        if "personality" in self.config:
            traits["personality"] = self.config["personality"]
        
        # Communication style
        if "communication" in self.config:
            comm = self.config["communication"]
            if "style" in comm:
                traits["communication_style"] = comm["style"]
            
            # Add other communication traits to personality
            if "personality" not in traits:
                traits["personality"] = {}
            
            for key in ["verbosity", "formality", "empathy"]:
                if key in comm:
                    traits["personality"][key] = comm[key]
        
        # Knowledge areas
        if "knowledge" in self.config:
            knowledge = self.config["knowledge"]
            if "areas" in knowledge:
                traits["knowledge_areas"] = knowledge["areas"]
            if "expertise_level" in knowledge:
                traits["expertise_level"] = knowledge["expertise_level"]
            if "specializations" in knowledge:
                traits["specializations"] = knowledge["specializations"]
        
        if traits:
            persona_config["traits"] = traits
        
        return persona_config
    
    def save_config(self, file_path: str):
        """Save configuration to file."""
        persona_config = self._transform_config_format()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(persona_config, f, indent=2, ensure_ascii=False)
    
    def load_config(self, file_path: str):
        """Load configuration from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            persona_config = json.load(f)
        
        # Transform to builder format
        self.config = self._reverse_transform_config(persona_config)
    
    def _reverse_transform_config(self, persona_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform standard persona config to builder format."""
        builder_config = {}
        
        # Basic info
        basic = {}
        for key in ["name", "description", "version"]:
            if key in persona_config:
                basic[key] = persona_config[key]
        if basic:
            builder_config["basic"] = basic
        
        # Process traits
        if "traits" in persona_config:
            traits = persona_config["traits"]
            
            # Personality
            if "personality" in traits:
                builder_config["personality"] = traits["personality"].copy()
            
            # Communication
            communication = {}
            if "communication_style" in traits:
                communication["style"] = traits["communication_style"]
            
            # Extract communication traits from personality
            if "personality" in traits:
                for key in ["verbosity", "formality", "empathy"]:
                    if key in traits["personality"]:
                        communication[key] = traits["personality"][key]
                        # Remove from personality copy
                        if "personality" in builder_config:
                            builder_config["personality"].pop(key, None)
            
            if communication:
                builder_config["communication"] = communication
            
            # Knowledge
            knowledge = {}
            for key in ["knowledge_areas", "expertise_level", "specializations"]:
                if key in traits:
                    if key == "knowledge_areas":
                        knowledge["areas"] = traits[key]
                    else:
                        knowledge[key] = traits[key]
            
            if knowledge:
                builder_config["knowledge"] = knowledge
        
        return builder_config


def interactive_config_builder() -> Dict[str, Any]:
    """Start interactive configuration builder."""
    builder = PersonaConfigBuilder()
    return builder.start_interactive_build()


def quick_build_from_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Build configuration from pre-defined answers."""
    builder = PersonaConfigBuilder()
    
    # Set values from answers
    for section_name, section_data in answers.items():
        for field_name, value in section_data.items():
            builder._set_nested_value(section_name, field_name, value)
    
    return builder._transform_config_format()


# Preset builders for common personas

def build_technical_assistant(
    name: str = "Tech Assistant",
    specialization: str = "programming",
    expertise_level: str = "expert"
) -> Dict[str, Any]:
    """Build a technical assistant configuration."""
    return quick_build_from_answers({
        "basic": {
            "name": name,
            "version": "1.0"
        },
        "personality": {
            "extroversion": 0.6,
            "openness": 0.9,
            "conscientiousness": 0.8,
            "agreeableness": 0.7,
            "neuroticism": 0.2
        },
        "communication": {
            "style": "professional",
            "verbosity": 0.7,
            "formality": 0.6
        },
        "knowledge": {
            "areas": ["programming", "software_engineering", "technology", specialization],
            "expertise_level": expertise_level
        }
    })


def build_friendly_helper(
    name: str = "Friendly Helper",
    specialty: str = "general",
    enthusiasm_level: float = 0.8
) -> Dict[str, Any]:
    """Build a friendly helper configuration."""
    return quick_build_from_answers({
        "basic": {
            "name": name,
            "version": "1.0"
        },
        "personality": {
            "extroversion": 0.8,
            "openness": 0.7,
            "conscientiousness": 0.6,
            "agreeableness": 0.9,
            "neuroticism": 0.2
        },
        "communication": {
            "style": "friendly",
            "verbosity": 0.6,
            "empathy": 0.9
        },
        "knowledge": {
            "areas": ["general_knowledge", "lifestyle", "entertainment", specialty],
            "expertise_level": "intermediate"
        }
    })