"""
Persona template system for creating personas from predefined templates.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class TemplateValidationError(Exception):
    """Exception raised for template validation errors."""
    pass


@dataclass
class PersonaTemplate:
    """
    A template for creating personas with predefined characteristics.
    
    Templates provide a blueprint for creating consistent personas with
    specific trait combinations, behaviors, and conversation styles.
    """
    
    name: str
    description: str
    category: str
    base_traits: Dict[str, float] = field(default_factory=dict)
    default_conversation_style: str = "neutral"
    default_emotional_baseline: str = "calm"
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    trait_ranges: Dict[str, tuple] = field(default_factory=dict)  # (min, max) for each trait
    customization_hooks: Dict[str, Callable] = field(default_factory=dict)
    example_personas: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    author: str = "unknown"
    
    def __post_init__(self):
        """Initialize template after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()
        self._validate_template()
    
    def _validate_template(self):
        """Validate the template configuration."""
        # Validate trait values
        for trait, value in self.base_traits.items():
            if not 0.0 <= value <= 1.0:
                raise TemplateValidationError(f"Trait '{trait}' must be between 0.0 and 1.0")
        
        # Validate trait ranges
        for trait, (min_val, max_val) in self.trait_ranges.items():
            if not (0.0 <= min_val <= max_val <= 1.0):
                raise TemplateValidationError(f"Invalid range for trait '{trait}': ({min_val}, {max_val})")
    
    def create_persona(self, name: str, **customizations) -> Persona:
        """
        Create a persona from this template.
        
        Args:
            name: Name for the new persona
            **customizations: Custom values to override template defaults
        
        Returns:
            A new Persona instance based on this template
        """
        # Start with base traits
        traits = self.base_traits.copy()
        
        # Apply customizations within allowed ranges
        for trait, value in customizations.get("traits", {}).items():
            if trait in self.trait_ranges:
                min_val, max_val = self.trait_ranges[trait]
                if not min_val <= value <= max_val:
                    logger.warning(f"Trait '{trait}' value {value} outside allowed range [{min_val}, {max_val}]")
                    value = max(min_val, min(max_val, value))  # Clamp to range
            traits[trait] = value
        
        # Handle conversation style
        conversation_style = customizations.get("conversation_style", self.default_conversation_style)
        
        # Handle emotional baseline
        emotional_baseline = customizations.get("emotional_baseline", self.default_emotional_baseline)
        
        # Create description
        description = customizations.get("description", f"Created from template: {self.name}")
        
        # Apply customization hooks
        for field, hook in self.customization_hooks.items():
            if field in customizations:
                try:
                    customizations[field] = hook(customizations[field])
                except Exception as e:
                    logger.error(f"Customization hook for '{field}' failed: {e}")
        
        # Validate required fields
        for field in self.required_fields:
            if field not in customizations:
                raise TemplateValidationError(f"Required field '{field}' not provided")
        
        # Create metadata
        metadata = {
            "template_name": self.name,
            "template_version": self.version,
            "created_from_template": True,
            "template_category": self.category,
            **customizations.get("metadata", {})
        }
        
        # Create and return persona
        persona = Persona(
            name=name,
            description=description,
            traits=traits,
            conversation_style=conversation_style,
            emotional_baseline=emotional_baseline,
            metadata=metadata
        )
        
        logger.info(f"Created persona '{name}' from template '{self.name}'")
        return persona
    
    def get_trait_suggestion(self, trait: str) -> Optional[float]:
        """Get the suggested value for a trait."""
        return self.base_traits.get(trait)
    
    def get_trait_range(self, trait: str) -> Optional[tuple]:
        """Get the allowed range for a trait."""
        return self.trait_ranges.get(trait)
    
    def validate_customization(self, customizations: Dict[str, Any]) -> List[str]:
        """
        Validate customization parameters.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in customizations:
                errors.append(f"Required field '{field}' missing")
        
        # Check trait ranges
        traits = customizations.get("traits", {})
        for trait, value in traits.items():
            if trait in self.trait_ranges:
                min_val, max_val = self.trait_ranges[trait]
                if not min_val <= value <= max_val:
                    errors.append(f"Trait '{trait}' value {value} outside range [{min_val}, {max_val}]")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "base_traits": self.base_traits,
            "default_conversation_style": self.default_conversation_style,
            "default_emotional_baseline": self.default_emotional_baseline,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "trait_ranges": {k: list(v) for k, v in self.trait_ranges.items()},
            "example_personas": self.example_personas,
            "tags": self.tags,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": self.author
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonaTemplate":
        """Create template from dictionary representation."""
        template = cls(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            base_traits=data.get("base_traits", {}),
            default_conversation_style=data.get("default_conversation_style", "neutral"),
            default_emotional_baseline=data.get("default_emotional_baseline", "calm"),
            required_fields=data.get("required_fields", []),
            optional_fields=data.get("optional_fields", []),
            trait_ranges={k: tuple(v) for k, v in data.get("trait_ranges", {}).items()},
            example_personas=data.get("example_personas", []),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "unknown")
        )
        
        if data.get("created_at"):
            template.created_at = datetime.fromisoformat(data["created_at"])
        
        return template


class TemplateManager:
    """Manages persona templates and provides creation utilities."""
    
    def __init__(self):
        self._templates: Dict[str, PersonaTemplate] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_template(self, template: PersonaTemplate) -> None:
        """Register a new template."""
        if template.name in self._templates:
            self.logger.warning(f"Overwriting existing template: {template.name}")
        
        self._templates[template.name] = template
        self.logger.info(f"Registered template: {template.name}")
    
    def get_template(self, name: str) -> Optional[PersonaTemplate]:
        """Get a template by name."""
        return self._templates.get(name)
    
    def list_templates(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[PersonaTemplate]:
        """
        List templates, optionally filtered by category or tags.
        
        Args:
            category: Filter by category
            tags: Filter by tags (must have all specified tags)
        
        Returns:
            List of matching templates
        """
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if all(tag in t.tags for tag in tags)]
        
        return sorted(templates, key=lambda t: t.name)
    
    def create_persona_from_template(self, template_name: str, persona_name: str, **customizations) -> Persona:
        """Create a persona from a registered template."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return template.create_persona(persona_name, **customizations)
    
    def validate_template_customization(self, template_name: str, customizations: Dict[str, Any]) -> List[str]:
        """Validate customizations for a template."""
        template = self.get_template(template_name)
        if not template:
            return [f"Template not found: {template_name}"]
        
        return template.validate_customization(customizations)
    
    def export_templates(self, file_path: str) -> None:
        """Export all templates to a JSON file."""
        data = {name: template.to_dict() for name, template in self._templates.items()}
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(self._templates)} templates to {file_path}")
    
    def import_templates(self, file_path: str) -> None:
        """Import templates from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for name, template_data in data.items():
            template = PersonaTemplate.from_dict(template_data)
            self.register_template(template)
        
        self.logger.info(f"Imported {len(data)} templates from {file_path}")
    
    def search_templates(self, query: str) -> List[PersonaTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for template in self._templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return sorted(results, key=lambda t: t.name)
    
    def get_categories(self) -> List[str]:
        """Get all available template categories."""
        return sorted(list(set(t.category for t in self._templates.values())))
    
    def get_tags(self) -> List[str]:
        """Get all available tags."""
        all_tags = set()
        for template in self._templates.values():
            all_tags.update(template.tags)
        return sorted(list(all_tags))