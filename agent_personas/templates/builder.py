"""
Guided persona builder for step-by-step persona creation.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..core.persona import Persona
from .archetype import Archetype, ArchetypeManager
from .template import PersonaTemplate, TemplateManager

logger = logging.getLogger(__name__)


class BuilderStep(Enum):
    """Steps in the persona building process."""
    BASIC_INFO = "basic_info"
    ARCHETYPE_SELECTION = "archetype_selection"
    TRAIT_CUSTOMIZATION = "trait_customization"
    CONVERSATION_STYLE = "conversation_style"
    EMOTIONAL_BASELINE = "emotional_baseline"
    ADVANCED_OPTIONS = "advanced_options"
    VALIDATION = "validation"
    COMPLETE = "complete"


@dataclass
class BuilderState:
    """Tracks the current state of the persona builder."""
    current_step: BuilderStep = BuilderStep.BASIC_INFO
    data: Dict[str, Any] = field(default_factory=dict)
    selected_archetypes: List[str] = field(default_factory=list)
    selected_template: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    completed_steps: set = field(default_factory=set)


class PersonaBuilder:
    """
    Interactive builder for creating personas with guidance and validation.
    
    Provides a step-by-step process for creating well-formed personas
    with appropriate trait combinations and consistency checks.
    """
    
    def __init__(
        self,
        archetype_manager: Optional[ArchetypeManager] = None,
        template_manager: Optional[TemplateManager] = None
    ):
        self.archetype_manager = archetype_manager or ArchetypeManager()
        self.template_manager = template_manager or TemplateManager()
        self.logger = logging.getLogger(__name__)
        self._state = BuilderState()
        self._step_handlers = {
            BuilderStep.BASIC_INFO: self._handle_basic_info,
            BuilderStep.ARCHETYPE_SELECTION: self._handle_archetype_selection,
            BuilderStep.TRAIT_CUSTOMIZATION: self._handle_trait_customization,
            BuilderStep.CONVERSATION_STYLE: self._handle_conversation_style,
            BuilderStep.EMOTIONAL_BASELINE: self._handle_emotional_baseline,
            BuilderStep.ADVANCED_OPTIONS: self._handle_advanced_options,
            BuilderStep.VALIDATION: self._handle_validation
        }
    
    def reset(self) -> None:
        """Reset the builder to start fresh."""
        self._state = BuilderState()
        self.logger.info("Builder reset to initial state")
    
    def get_current_step(self) -> BuilderStep:
        """Get the current step in the building process."""
        return self._state.current_step
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get available options for the current step."""
        handler = self._step_handlers.get(self._state.current_step)
        if handler:
            return handler("get_options", {})
        return {}
    
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input for the current step and advance if valid.
        
        Args:
            input_data: Data for the current step
            
        Returns:
            Dictionary with step result, errors, and next step info
        """
        handler = self._step_handlers.get(self._state.current_step)
        if not handler:
            return {
                "success": False,
                "error": f"No handler for step: {self._state.current_step}",
                "current_step": self._state.current_step
            }
        
        try:
            result = handler("process", input_data)
            
            if result.get("success", False):
                self._state.completed_steps.add(self._state.current_step)
                self._advance_step()
            
            result["current_step"] = self._state.current_step
            result["progress"] = len(self._state.completed_steps) / len(BuilderStep)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing step {self._state.current_step}: {e}")
            return {
                "success": False,
                "error": str(e),
                "current_step": self._state.current_step
            }
    
    def _advance_step(self) -> None:
        """Advance to the next step in the building process."""
        steps = list(BuilderStep)
        current_index = steps.index(self._state.current_step)
        
        if current_index < len(steps) - 1:
            self._state.current_step = steps[current_index + 1]
            self.logger.debug(f"Advanced to step: {self._state.current_step}")
    
    def _handle_basic_info(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle basic information step."""
        if action == "get_options":
            return {
                "required_fields": ["name", "description"],
                "optional_fields": ["category", "use_template"],
                "available_templates": list(self.template_manager._templates.keys()),
                "suggested_categories": ["assistant", "creative", "technical", "support", "education"]
            }
        
        elif action == "process":
            errors = []
            
            # Validate required fields
            name = data.get("name", "").strip()
            if not name:
                errors.append("Name is required")
            elif len(name) > 100:
                errors.append("Name must be 100 characters or less")
            
            description = data.get("description", "").strip()
            if not description:
                errors.append("Description is required")
            elif len(description) > 1000:
                errors.append("Description must be 1000 characters or less")
            
            # Handle template selection
            template_name = data.get("use_template")
            if template_name and template_name not in self.template_manager._templates:
                errors.append(f"Template not found: {template_name}")
            
            if errors:
                return {"success": False, "errors": errors}
            
            # Store data
            self._state.data.update({
                "name": name,
                "description": description,
                "category": data.get("category", "assistant")
            })
            
            if template_name:
                self._state.selected_template = template_name
                template = self.template_manager.get_template(template_name)
                if template:
                    # Pre-populate with template defaults
                    self._state.data.update({
                        "traits": template.base_traits.copy(),
                        "conversation_style": template.default_conversation_style,
                        "emotional_baseline": template.default_emotional_baseline
                    })
            
            return {"success": True, "message": "Basic information saved"}
    
    def _handle_archetype_selection(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle archetype selection step."""
        if action == "get_options":
            archetypes = self.archetype_manager.list_archetypes()
            return {
                "available_archetypes": [
                    {
                        "name": arch.name,
                        "description": arch.description,
                        "category": arch.category.value,
                        "core_traits": arch.core_traits
                    }
                    for arch in archetypes
                ],
                "max_selections": 3,
                "can_skip": True
            }
        
        elif action == "process":
            selected = data.get("archetypes", [])
            
            if len(selected) > 3:
                return {"success": False, "errors": ["Maximum 3 archetypes allowed"]}
            
            # Validate archetype names
            invalid_archetypes = []
            for arch_name in selected:
                if not self.archetype_manager.get_archetype(arch_name):
                    invalid_archetypes.append(arch_name)
            
            if invalid_archetypes:
                return {
                    "success": False,
                    "errors": [f"Invalid archetypes: {', '.join(invalid_archetypes)}"]
                }
            
            # Check for conflicts
            conflicts = []
            archetypes = [self.archetype_manager.get_archetype(name) for name in selected]
            for i, arch1 in enumerate(archetypes):
                for arch2 in archetypes[i+1:]:
                    if arch1.conflicts_with(arch2):
                        conflicts.append(f"{arch1.name} conflicts with {arch2.name}")
            
            if conflicts:
                return {
                    "success": False,
                    "errors": conflicts,
                    "suggestion": "Consider selecting compatible archetypes or reduce conflicts"
                }
            
            self._state.selected_archetypes = selected
            
            # Blend archetype traits if multiple selected
            if len(selected) > 1:
                self._blend_archetypes()
            elif len(selected) == 1:
                archetype = self.archetype_manager.get_archetype(selected[0])
                self._state.data.setdefault("traits", {}).update(archetype.core_traits)
            
            return {"success": True, "message": f"Selected {len(selected)} archetype(s)"}
    
    def _handle_trait_customization(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trait customization step."""
        if action == "get_options":
            current_traits = self._state.data.get("traits", {})
            template = None
            if self._state.selected_template:
                template = self.template_manager.get_template(self._state.selected_template)
            
            options = {
                "current_traits": current_traits,
                "suggested_traits": [
                    "helpful", "creative", "analytical", "empathetic", "patient",
                    "confident", "friendly", "professional", "curious", "wise"
                ],
                "trait_descriptions": {
                    "helpful": "Tendency to assist and support others",
                    "creative": "Ability to generate novel ideas and solutions",
                    "analytical": "Systematic approach to problem-solving",
                    "empathetic": "Understanding and sharing others' emotions",
                    "patient": "Ability to remain calm and persistent"
                }
            }
            
            if template:
                options["template_ranges"] = template.trait_ranges
                options["template_suggestions"] = template.base_traits
            
            return options
        
        elif action == "process":
            traits = data.get("traits", {})
            errors = []
            
            # Validate trait values
            for trait_name, value in traits.items():
                if not isinstance(value, (int, float)):
                    errors.append(f"Trait '{trait_name}' must be a number")
                elif not 0.0 <= value <= 1.0:
                    errors.append(f"Trait '{trait_name}' must be between 0.0 and 1.0")
            
            # Check template constraints if using template
            if self._state.selected_template:
                template = self.template_manager.get_template(self._state.selected_template)
                if template:
                    template_errors = template.validate_customization({"traits": traits})
                    errors.extend(template_errors)
            
            if errors:
                return {"success": False, "errors": errors}
            
            self._state.data["traits"] = traits
            return {"success": True, "message": f"Customized {len(traits)} traits"}
    
    def _handle_conversation_style(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation style selection."""
        if action == "get_options":
            return {
                "available_styles": [
                    "professional", "casual", "friendly", "formal", "creative",
                    "supportive", "analytical", "enthusiastic", "calm", "playful"
                ],
                "style_descriptions": {
                    "professional": "Formal and business-appropriate communication",
                    "casual": "Relaxed and informal conversation style",
                    "friendly": "Warm and approachable communication",
                    "supportive": "Encouraging and understanding tone"
                },
                "current_selection": self._state.data.get("conversation_style")
            }
        
        elif action == "process":
            style = data.get("conversation_style", "").strip()
            if not style:
                return {"success": False, "errors": ["Conversation style is required"]}
            
            self._state.data["conversation_style"] = style
            return {"success": True, "message": f"Set conversation style to '{style}'"}
    
    def _handle_emotional_baseline(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emotional baseline selection."""
        if action == "get_options":
            return {
                "available_baselines": [
                    "calm", "enthusiastic", "focused", "cheerful", "serious",
                    "compassionate", "confident", "curious", "patient", "energetic"
                ],
                "baseline_descriptions": {
                    "calm": "Stable and peaceful emotional state",
                    "enthusiastic": "High energy and excitement",
                    "focused": "Concentrated and goal-oriented",
                    "compassionate": "Caring and understanding"
                },
                "current_selection": self._state.data.get("emotional_baseline")
            }
        
        elif action == "process":
            baseline = data.get("emotional_baseline", "").strip()
            if not baseline:
                return {"success": False, "errors": ["Emotional baseline is required"]}
            
            self._state.data["emotional_baseline"] = baseline
            return {"success": True, "message": f"Set emotional baseline to '{baseline}'"}
    
    def _handle_advanced_options(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle advanced options."""
        if action == "get_options":
            return {
                "optional_fields": ["metadata", "tags", "version"],
                "current_metadata": self._state.data.get("metadata", {}),
                "suggested_tags": ["assistant", "creative", "professional", "support"]
            }
        
        elif action == "process":
            # Handle metadata
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                return {"success": False, "errors": ["Metadata must be a dictionary"]}
            
            self._state.data["metadata"] = {**self._state.data.get("metadata", {}), **metadata}
            
            # Handle tags
            tags = data.get("tags", [])
            if tags:
                self._state.data.setdefault("metadata", {})["tags"] = tags
            
            return {"success": True, "message": "Advanced options saved"}
    
    def _handle_validation(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle final validation."""
        if action == "get_options":
            return {
                "current_data": self._state.data,
                "validation_required": True,
                "can_modify": True
            }
        
        elif action == "process":
            errors = []
            
            # Validate required fields
            required = ["name", "description", "traits", "conversation_style", "emotional_baseline"]
            for field in required:
                if field not in self._state.data:
                    errors.append(f"Missing required field: {field}")
            
            # Additional validation
            if not self._state.data.get("traits"):
                errors.append("At least one trait must be defined")
            
            if errors:
                return {"success": False, "errors": errors}
            
            return {"success": True, "message": "Validation passed", "ready_to_create": True}
    
    def _blend_archetypes(self) -> None:
        """Blend selected archetypes into combined traits."""
        if len(self._state.selected_archetypes) < 2:
            return
        
        # Start with first archetype
        base_archetype = self.archetype_manager.get_archetype(self._state.selected_archetypes[0])
        if not base_archetype:
            return
        
        blended_traits = base_archetype.core_traits.copy()
        
        # Blend with remaining archetypes
        for arch_name in self._state.selected_archetypes[1:]:
            archetype = self.archetype_manager.get_archetype(arch_name)
            if archetype:
                # Average the traits
                for trait, value in archetype.core_traits.items():
                    current_value = blended_traits.get(trait, 0.0)
                    blended_traits[trait] = (current_value + value) / 2
        
        self._state.data.setdefault("traits", {}).update(blended_traits)
    
    def create_persona(self) -> Persona:
        """Create the final persona from the builder state."""
        if self._state.current_step != BuilderStep.COMPLETE:
            raise ValueError("Builder not complete - call process_input through all steps first")
        
        # Use template if selected
        if self._state.selected_template:
            template = self.template_manager.get_template(self._state.selected_template)
            if template:
                return template.create_persona(
                    self._state.data["name"],
                    description=self._state.data["description"],
                    traits=self._state.data["traits"],
                    conversation_style=self._state.data["conversation_style"],
                    emotional_baseline=self._state.data["emotional_baseline"],
                    metadata=self._state.data.get("metadata", {})
                )
        
        # Create persona directly
        persona = Persona(
            name=self._state.data["name"],
            description=self._state.data["description"],
            traits=self._state.data["traits"],
            conversation_style=self._state.data["conversation_style"],
            emotional_baseline=self._state.data["emotional_baseline"],
            metadata=self._state.data.get("metadata", {})
        )
        
        # Add builder metadata
        persona.metadata["created_with_builder"] = True
        persona.metadata["selected_archetypes"] = self._state.selected_archetypes
        if self._state.selected_template:
            persona.metadata["base_template"] = self._state.selected_template
        
        self.logger.info(f"Created persona '{persona.name}' using builder")
        return persona