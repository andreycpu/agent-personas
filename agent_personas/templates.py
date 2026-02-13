"""
Template system for creating standard persona configurations and examples.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .exceptions import PersonaError


class PersonaTemplate:
    """Template for creating persona configurations."""
    
    def __init__(self, name: str, description: str, template_data: Dict[str, Any]):
        """
        Initialize persona template.
        
        Args:
            name: Template name
            description: Template description
            template_data: Base template configuration
        """
        self.name = name
        self.description = description
        self.template_data = template_data.copy()
        self.variables: Dict[str, Any] = {}
    
    def set_variable(self, key: str, value: Any) -> 'PersonaTemplate':
        """Set a template variable."""
        self.variables[key] = value
        return self
    
    def set_variables(self, variables: Dict[str, Any]) -> 'PersonaTemplate':
        """Set multiple template variables."""
        self.variables.update(variables)
        return self
    
    def render(self, custom_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Render template with variables.
        
        Args:
            custom_variables: Additional variables for this render
        
        Returns:
            Rendered persona configuration
        """
        # Merge variables
        render_vars = self.variables.copy()
        if custom_variables:
            render_vars.update(custom_variables)
        
        # Deep copy template data
        rendered = self._deep_copy_with_substitution(self.template_data, render_vars)
        
        # Add metadata
        rendered['template_name'] = self.name
        rendered['created_from_template'] = datetime.now().isoformat()
        
        return rendered
    
    def _deep_copy_with_substitution(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in template."""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                # Substitute in key
                new_key = self._substitute_string(key, variables) if isinstance(key, str) else key
                # Substitute in value
                result[new_key] = self._deep_copy_with_substitution(value, variables)
            return result
        
        elif isinstance(obj, list):
            return [self._deep_copy_with_substitution(item, variables) for item in obj]
        
        elif isinstance(obj, str):
            return self._substitute_string(obj, variables)
        
        else:
            return obj
    
    def _substitute_string(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in a string using {variable} syntax."""
        try:
            return text.format(**variables)
        except KeyError as e:
            raise PersonaError(f"Template variable not found: {e}")
        except Exception as e:
            raise PersonaError(f"Error substituting template variables: {e}")


class TemplateRegistry:
    """Registry for persona templates."""
    
    def __init__(self):
        """Initialize template registry."""
        self.templates: Dict[str, PersonaTemplate] = {}
        self._load_builtin_templates()
    
    def register(self, template: PersonaTemplate):
        """Register a template."""
        self.templates[template.name] = template
    
    def get(self, name: str) -> PersonaTemplate:
        """Get a template by name."""
        if name not in self.templates:
            raise PersonaError(f"Template not found: {name}")
        return self.templates[name]
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates."""
        return [
            {"name": template.name, "description": template.description}
            for template in self.templates.values()
        ]
    
    def create_persona_from_template(
        self, 
        template_name: str, 
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create persona from template."""
        template = self.get(template_name)
        return template.render(variables)
    
    def _load_builtin_templates(self):
        """Load built-in templates."""
        
        # Technical Assistant Template
        tech_assistant = PersonaTemplate(
            name="technical_assistant",
            description="Technical assistant for programming and engineering topics",
            template_data={
                "name": "{assistant_name}",
                "traits": {
                    "personality": {
                        "extroversion": 0.6,
                        "openness": 0.9,
                        "conscientiousness": 0.8,
                        "agreeableness": 0.7,
                        "neuroticism": 0.2,
                        "analytical_thinking": 0.9,
                        "creativity": 0.7
                    },
                    "communication_style": "professional",
                    "knowledge_areas": [
                        "software_engineering",
                        "programming",
                        "system_architecture",
                        "data_structures",
                        "algorithms",
                        "{specialization}"
                    ],
                    "response_preferences": {
                        "length": "detailed",
                        "technical_depth": "high",
                        "include_examples": True,
                        "include_code": True
                    }
                },
                "version": "1.0",
                "expertise_level": "expert"
            }
        )
        self.register(tech_assistant)
        
        # Friendly Helper Template
        friendly_helper = PersonaTemplate(
            name="friendly_helper",
            description="Friendly, approachable assistant for general tasks",
            template_data={
                "name": "{helper_name}",
                "traits": {
                    "personality": {
                        "extroversion": 0.8,
                        "openness": 0.7,
                        "conscientiousness": 0.6,
                        "agreeableness": 0.9,
                        "neuroticism": 0.2,
                        "enthusiasm": 0.8,
                        "empathy": 0.9
                    },
                    "communication_style": "friendly",
                    "knowledge_areas": [
                        "general_knowledge",
                        "daily_tasks",
                        "lifestyle",
                        "entertainment",
                        "{specialty_area}"
                    ],
                    "response_preferences": {
                        "length": "medium",
                        "tone": "warm",
                        "use_emojis": True,
                        "encouragement": True
                    }
                },
                "version": "1.0",
                "expertise_level": "intermediate"
            }
        )
        self.register(friendly_helper)
        
        # Academic Researcher Template
        researcher = PersonaTemplate(
            name="academic_researcher",
            description="Academic researcher focused on scholarly work",
            template_data={
                "name": "{researcher_name}",
                "traits": {
                    "personality": {
                        "extroversion": 0.4,
                        "openness": 0.95,
                        "conscientiousness": 0.9,
                        "agreeableness": 0.6,
                        "neuroticism": 0.3,
                        "analytical_thinking": 0.95,
                        "attention_to_detail": 0.9
                    },
                    "communication_style": "formal",
                    "knowledge_areas": [
                        "research_methodology",
                        "academic_writing",
                        "data_analysis",
                        "literature_review",
                        "{research_field}"
                    ],
                    "response_preferences": {
                        "length": "comprehensive",
                        "citation_style": "{citation_format}",
                        "evidence_based": True,
                        "critical_thinking": True
                    }
                },
                "version": "1.0",
                "expertise_level": "expert"
            }
        )
        self.register(researcher)
        
        # Customer Service Template
        customer_service = PersonaTemplate(
            name="customer_service",
            description="Professional customer service representative",
            template_data={
                "name": "{agent_name}",
                "traits": {
                    "personality": {
                        "extroversion": 0.7,
                        "openness": 0.6,
                        "conscientiousness": 0.8,
                        "agreeableness": 0.95,
                        "neuroticism": 0.1,
                        "patience": 0.9,
                        "problem_solving": 0.8
                    },
                    "communication_style": "professional",
                    "knowledge_areas": [
                        "customer_service",
                        "conflict_resolution",
                        "product_knowledge",
                        "{company_domain}",
                        "policies_procedures"
                    ],
                    "response_preferences": {
                        "length": "concise",
                        "politeness": "high",
                        "solution_oriented": True,
                        "empathetic": True
                    }
                },
                "version": "1.0",
                "expertise_level": "professional"
            }
        )
        self.register(customer_service)
        
        # Creative Assistant Template
        creative = PersonaTemplate(
            name="creative_assistant",
            description="Creative assistant for artistic and imaginative tasks",
            template_data={
                "name": "{creative_name}",
                "traits": {
                    "personality": {
                        "extroversion": 0.7,
                        "openness": 0.95,
                        "conscientiousness": 0.5,
                        "agreeableness": 0.8,
                        "neuroticism": 0.4,
                        "creativity": 0.95,
                        "imagination": 0.9,
                        "artistic_sense": 0.9
                    },
                    "communication_style": "casual",
                    "knowledge_areas": [
                        "creative_writing",
                        "visual_arts",
                        "design",
                        "storytelling",
                        "brainstorming",
                        "{artistic_medium}"
                    ],
                    "response_preferences": {
                        "length": "varied",
                        "creative_language": True,
                        "metaphors": True,
                        "inspiration": True
                    }
                },
                "version": "1.0",
                "expertise_level": "advanced"
            }
        )
        self.register(creative)


# Global template registry
template_registry = TemplateRegistry()


def create_persona_from_template(
    template_name: str, 
    **variables
) -> Dict[str, Any]:
    """
    Create persona from template with variables.
    
    Args:
        template_name: Name of template to use
        **variables: Template variables as keyword arguments
    
    Returns:
        Persona configuration dictionary
    """
    return template_registry.create_persona_from_template(template_name, variables)


def list_available_templates() -> List[Dict[str, str]]:
    """List all available persona templates."""
    return template_registry.list_templates()


def get_template_info(template_name: str) -> Dict[str, Any]:
    """Get information about a template."""
    template = template_registry.get(template_name)
    return {
        "name": template.name,
        "description": template.description,
        "variables": list(template.variables.keys()),
        "required_variables": _extract_template_variables(template.template_data)
    }


def _extract_template_variables(obj: Any, variables: Optional[set] = None) -> List[str]:
    """Extract template variables from template data."""
    if variables is None:
        variables = set()
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                variables.update(_find_variables_in_string(key))
            _extract_template_variables(value, variables)
    
    elif isinstance(obj, list):
        for item in obj:
            _extract_template_variables(item, variables)
    
    elif isinstance(obj, str):
        variables.update(_find_variables_in_string(obj))
    
    return sorted(list(variables))


def _find_variables_in_string(text: str) -> List[str]:
    """Find template variables in a string."""
    import re
    pattern = r'\{([^}]+)\}'
    matches = re.findall(pattern, text)
    return matches


# Template examples and presets

def create_technical_assistant(
    name: str = "Tech Assistant",
    specialization: str = "web_development"
) -> Dict[str, Any]:
    """Create a technical assistant persona."""
    return create_persona_from_template(
        "technical_assistant",
        assistant_name=name,
        specialization=specialization
    )


def create_friendly_helper(
    name: str = "Helper",
    specialty_area: str = "lifestyle"
) -> Dict[str, Any]:
    """Create a friendly helper persona."""
    return create_persona_from_template(
        "friendly_helper",
        helper_name=name,
        specialty_area=specialty_area
    )


def create_researcher(
    name: str = "Dr. Research",
    research_field: str = "computer_science",
    citation_format: str = "APA"
) -> Dict[str, Any]:
    """Create an academic researcher persona."""
    return create_persona_from_template(
        "academic_researcher",
        researcher_name=name,
        research_field=research_field,
        citation_format=citation_format
    )


def create_customer_service_agent(
    name: str = "Support Agent",
    company_domain: str = "technology"
) -> Dict[str, Any]:
    """Create a customer service agent persona."""
    return create_persona_from_template(
        "customer_service",
        agent_name=name,
        company_domain=company_domain
    )


def create_creative_assistant(
    name: str = "Creative",
    artistic_medium: str = "writing"
) -> Dict[str, Any]:
    """Create a creative assistant persona."""
    return create_persona_from_template(
        "creative_assistant",
        creative_name=name,
        artistic_medium=artistic_medium
    )


# Template validation and testing

def validate_template(template_data: Dict[str, Any]) -> bool:
    """
    Validate a template configuration.
    
    Args:
        template_data: Template data to validate
    
    Returns:
        True if valid
    
    Raises:
        PersonaError: If template is invalid
    """
    from .validation import validate_persona_traits
    
    required_fields = ["name", "traits"]
    
    for field in required_fields:
        if field not in template_data:
            raise PersonaError(f"Template missing required field: {field}")
    
    # Validate traits structure (skip variable substitution for validation)
    traits = template_data["traits"]
    if isinstance(traits, dict):
        # Create a temporary traits dict with dummy values for validation
        test_traits = _substitute_template_variables_for_test(traits)
        validate_persona_traits(test_traits)
    
    return True


def _substitute_template_variables_for_test(obj: Any) -> Any:
    """Substitute template variables with test values for validation."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            new_key = _substitute_test_variables(key) if isinstance(key, str) else key
            result[new_key] = _substitute_template_variables_for_test(value)
        return result
    
    elif isinstance(obj, list):
        return [_substitute_template_variables_for_test(item) for item in obj]
    
    elif isinstance(obj, str):
        return _substitute_test_variables(obj)
    
    else:
        return obj


def _substitute_test_variables(text: str) -> str:
    """Substitute template variables with test values."""
    import re
    
    # Common test substitutions
    substitutions = {
        'assistant_name': 'Test Assistant',
        'helper_name': 'Test Helper',
        'researcher_name': 'Test Researcher',
        'agent_name': 'Test Agent',
        'creative_name': 'Test Creative',
        'specialization': 'general',
        'specialty_area': 'general',
        'research_field': 'general',
        'citation_format': 'APA',
        'company_domain': 'general',
        'artistic_medium': 'general'
    }
    
    def replace_var(match):
        var_name = match.group(1)
        return substitutions.get(var_name, f'test_{var_name}')
    
    return re.sub(r'\{([^}]+)\}', replace_var, text)


def export_template_to_file(template_name: str, file_path: str):
    """Export a template to a JSON file."""
    template = template_registry.get(template_name)
    
    template_export = {
        "name": template.name,
        "description": template.description,
        "template_data": template.template_data,
        "exported_at": datetime.now().isoformat()
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(template_export, f, indent=2, ensure_ascii=False)


def import_template_from_file(file_path: str):
    """Import a template from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        template_data = json.load(f)
    
    template = PersonaTemplate(
        name=template_data["name"],
        description=template_data["description"],
        template_data=template_data["template_data"]
    )
    
    template_registry.register(template)