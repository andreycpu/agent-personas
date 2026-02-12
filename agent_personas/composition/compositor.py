"""
Persona compositor for rule-based persona composition and layering.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging
from copy import deepcopy

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class CompositionOperation(Enum):
    """Types of composition operations."""
    LAYER = "layer"  # Layer one persona on top of another
    MERGE = "merge"  # Merge specific traits
    REPLACE = "replace"  # Replace traits completely
    ENHANCE = "enhance"  # Enhance existing traits
    SUPPRESS = "suppress"  # Reduce trait values
    CONDITIONAL = "conditional"  # Apply rules conditionally
    TEMPORAL = "temporal"  # Time-based modifications


class RulePriority(Enum):
    """Priority levels for composition rules."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class CompositionRule:
    """
    Defines a rule for persona composition operations.
    """
    name: str
    operation: CompositionOperation
    priority: RulePriority = RulePriority.NORMAL
    target_traits: Optional[List[str]] = None  # Specific traits to target
    condition: Optional[Callable[[Persona], bool]] = None  # Condition function
    parameters: Dict[str, Any] = field(default_factory=dict)
    source_persona_filter: Optional[str] = None  # Filter for source personas
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def applies_to(self, persona: Persona) -> bool:
        """Check if this rule applies to the given persona."""
        if not self.active:
            return False
        
        if self.condition:
            return self.condition(persona)
        
        return True


class CompositionContext:
    """Context for a composition operation."""
    
    def __init__(self):
        self.source_personas: List[Persona] = []
        self.target_persona: Optional[Persona] = None
        self.applied_rules: List[str] = []
        self.rule_results: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        
    def add_source_persona(self, persona: Persona, role: str = "default") -> None:
        """Add a source persona with optional role."""
        self.source_personas.append(persona)
        self.metadata[f"source_{len(self.source_personas)}"] = {
            "name": persona.name,
            "role": role
        }
        
    def record_rule_application(self, rule_name: str, result: Any) -> None:
        """Record that a rule was applied with its result."""
        self.applied_rules.append(rule_name)
        self.rule_results[rule_name] = result


class PersonaCompositor:
    """
    Advanced compositor for creating complex persona compositions using rules.
    
    Supports layered composition, conditional modifications, and sophisticated
    trait manipulation based on configurable rules and contexts.
    """
    
    def __init__(self):
        self.rules: List[CompositionRule] = []
        self.rule_processors: Dict[CompositionOperation, Callable] = {
            CompositionOperation.LAYER: self._process_layer_rule,
            CompositionOperation.MERGE: self._process_merge_rule,
            CompositionOperation.REPLACE: self._process_replace_rule,
            CompositionOperation.ENHANCE: self._process_enhance_rule,
            CompositionOperation.SUPPRESS: self._process_suppress_rule,
            CompositionOperation.CONDITIONAL: self._process_conditional_rule,
            CompositionOperation.TEMPORAL: self._process_temporal_rule
        }
        self.logger = logging.getLogger(__name__)
    
    def add_rule(self, rule: CompositionRule) -> None:
        """Add a composition rule."""
        self.rules.append(rule)
        self.logger.debug(f"Added composition rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                self.logger.debug(f"Removed composition rule: {rule_name}")
                return True
        return False
    
    def compose_persona(
        self,
        base_persona: Persona,
        source_personas: List[Persona],
        target_name: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Persona:
        """
        Create a composed persona from a base persona and source personas.
        
        Args:
            base_persona: The base persona to start with
            source_personas: Additional personas to compose from
            target_name: Name for the resulting persona
            context_metadata: Additional context information
            
        Returns:
            A new composed persona
        """
        # Create composition context
        context = CompositionContext()
        context.target_persona = deepcopy(base_persona)
        
        if target_name:
            context.target_persona.name = target_name
        
        for persona in source_personas:
            context.add_source_persona(persona)
        
        if context_metadata:
            context.metadata.update(context_metadata)
        
        # Sort rules by priority
        active_rules = [r for r in self.rules if r.active]
        active_rules.sort(key=lambda r: r.priority.value, reverse=True)
        
        # Apply rules
        for rule in active_rules:
            if rule.applies_to(context.target_persona):
                try:
                    processor = self.rule_processors.get(rule.operation)
                    if processor:
                        result = processor(rule, context)
                        context.record_rule_application(rule.name, result)
                        self.logger.debug(f"Applied rule: {rule.name}")
                    else:
                        self.logger.warning(f"No processor for operation: {rule.operation}")
                except Exception as e:
                    self.logger.error(f"Error applying rule {rule.name}: {e}")
        
        # Update metadata with composition information
        context.target_persona.metadata.update({
            "composition_source_personas": [p.name for p in source_personas],
            "composition_base_persona": base_persona.name,
            "applied_composition_rules": context.applied_rules,
            "composition_context": context.metadata,
            "is_composed_persona": True
        })
        
        self.logger.info(f"Composed persona '{context.target_persona.name}' using {len(context.applied_rules)} rules")
        return context.target_persona
    
    def _process_layer_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process a layering rule."""
        source_persona = self._find_matching_source_persona(rule, context)
        if not source_persona:
            return {"status": "skipped", "reason": "no_matching_source"}
        
        # Layer traits from source onto target
        layer_strength = rule.parameters.get("layer_strength", 0.5)
        preserve_base = rule.parameters.get("preserve_base", True)
        
        target_traits = rule.target_traits or list(source_persona.traits.keys())
        
        for trait in target_traits:
            source_value = source_persona.get_trait(trait)
            current_value = context.target_persona.get_trait(trait)
            
            if source_value > 0:
                if preserve_base and current_value > 0:
                    # Blend the values
                    new_value = current_value * (1 - layer_strength) + source_value * layer_strength
                else:
                    # Use source value with strength multiplier
                    new_value = source_value * layer_strength
                
                context.target_persona.set_trait(trait, min(1.0, new_value))
        
        return {
            "status": "applied",
            "source_persona": source_persona.name,
            "traits_layered": target_traits,
            "layer_strength": layer_strength
        }
    
    def _process_merge_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process a merge rule."""
        merge_strategy = rule.parameters.get("merge_strategy", "average")
        target_traits = rule.target_traits or []
        
        if not target_traits:
            return {"status": "skipped", "reason": "no_target_traits"}
        
        merged_count = 0
        
        for trait in target_traits:
            values = []
            
            # Collect values from all relevant sources
            current_value = context.target_persona.get_trait(trait)
            if current_value > 0:
                values.append(current_value)
            
            for source_persona in context.source_personas:
                source_value = source_persona.get_trait(trait)
                if source_value > 0:
                    values.append(source_value)
            
            if len(values) > 1:
                # Apply merge strategy
                if merge_strategy == "average":
                    new_value = sum(values) / len(values)
                elif merge_strategy == "max":
                    new_value = max(values)
                elif merge_strategy == "min":
                    new_value = min(values)
                elif merge_strategy == "weighted":
                    weights = rule.parameters.get("weights", [1.0] * len(values))
                    weighted_sum = sum(v * w for v, w in zip(values, weights))
                    weight_sum = sum(weights)
                    new_value = weighted_sum / weight_sum if weight_sum > 0 else 0
                else:
                    new_value = sum(values) / len(values)  # Default to average
                
                context.target_persona.set_trait(trait, new_value)
                merged_count += 1
        
        return {
            "status": "applied",
            "merge_strategy": merge_strategy,
            "traits_merged": merged_count
        }
    
    def _process_replace_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process a replacement rule."""
        source_persona = self._find_matching_source_persona(rule, context)
        if not source_persona:
            return {"status": "skipped", "reason": "no_matching_source"}
        
        target_traits = rule.target_traits or list(source_persona.traits.keys())
        replacement_factor = rule.parameters.get("replacement_factor", 1.0)
        
        replaced_count = 0
        
        for trait in target_traits:
            source_value = source_persona.get_trait(trait)
            if source_value > 0:
                new_value = source_value * replacement_factor
                context.target_persona.set_trait(trait, min(1.0, new_value))
                replaced_count += 1
        
        return {
            "status": "applied", 
            "source_persona": source_persona.name,
            "traits_replaced": replaced_count,
            "replacement_factor": replacement_factor
        }
    
    def _process_enhance_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process an enhancement rule."""
        enhancement_factor = rule.parameters.get("enhancement_factor", 1.2)
        max_value = rule.parameters.get("max_value", 1.0)
        
        target_traits = rule.target_traits or list(context.target_persona.traits.keys())
        enhanced_count = 0
        
        for trait in target_traits:
            current_value = context.target_persona.get_trait(trait)
            if current_value > 0:
                new_value = min(max_value, current_value * enhancement_factor)
                context.target_persona.set_trait(trait, new_value)
                enhanced_count += 1
        
        return {
            "status": "applied",
            "traits_enhanced": enhanced_count,
            "enhancement_factor": enhancement_factor
        }
    
    def _process_suppress_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process a suppression rule."""
        suppression_factor = rule.parameters.get("suppression_factor", 0.8)
        min_value = rule.parameters.get("min_value", 0.0)
        
        target_traits = rule.target_traits or list(context.target_persona.traits.keys())
        suppressed_count = 0
        
        for trait in target_traits:
            current_value = context.target_persona.get_trait(trait)
            if current_value > 0:
                new_value = max(min_value, current_value * suppression_factor)
                context.target_persona.set_trait(trait, new_value)
                suppressed_count += 1
        
        return {
            "status": "applied",
            "traits_suppressed": suppressed_count,
            "suppression_factor": suppression_factor
        }
    
    def _process_conditional_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process a conditional rule."""
        # Conditional rules are processed by their condition function in applies_to()
        # The actual operation is specified in nested_operation parameter
        nested_operation = rule.parameters.get("nested_operation")
        nested_params = rule.parameters.get("nested_params", {})
        
        if not nested_operation:
            return {"status": "skipped", "reason": "no_nested_operation"}
        
        # Create a temporary rule for the nested operation
        temp_rule = CompositionRule(
            name=f"{rule.name}_nested",
            operation=nested_operation,
            target_traits=rule.target_traits,
            parameters=nested_params
        )
        
        processor = self.rule_processors.get(nested_operation)
        if processor and processor != self._process_conditional_rule:  # Avoid recursion
            result = processor(temp_rule, context)
            result["conditional_rule"] = rule.name
            return result
        
        return {"status": "skipped", "reason": "invalid_nested_operation"}
    
    def _process_temporal_rule(self, rule: CompositionRule, context: CompositionContext) -> Dict[str, Any]:
        """Process a temporal rule."""
        # Temporal rules modify traits based on time or sequence
        temporal_pattern = rule.parameters.get("temporal_pattern", "linear_decay")
        time_factor = rule.parameters.get("time_factor", 1.0)
        
        target_traits = rule.target_traits or list(context.target_persona.traits.keys())
        modified_count = 0
        
        for trait in target_traits:
            current_value = context.target_persona.get_trait(trait)
            if current_value > 0:
                if temporal_pattern == "linear_decay":
                    new_value = current_value * (1.0 - time_factor * 0.1)
                elif temporal_pattern == "exponential_decay":
                    new_value = current_value * (0.9 ** time_factor)
                elif temporal_pattern == "oscillating":
                    import math
                    oscillation = 0.1 * math.sin(time_factor)
                    new_value = current_value * (1.0 + oscillation)
                else:
                    new_value = current_value  # No change for unknown patterns
                
                context.target_persona.set_trait(trait, max(0.0, min(1.0, new_value)))
                modified_count += 1
        
        return {
            "status": "applied",
            "temporal_pattern": temporal_pattern,
            "time_factor": time_factor,
            "traits_modified": modified_count
        }
    
    def _find_matching_source_persona(
        self,
        rule: CompositionRule,
        context: CompositionContext
    ) -> Optional[Persona]:
        """Find a source persona that matches the rule's filter."""
        if not context.source_personas:
            return None
        
        if not rule.source_persona_filter:
            # Return the first source persona if no filter
            return context.source_personas[0]
        
        # Simple name-based filtering
        for persona in context.source_personas:
            if rule.source_persona_filter.lower() in persona.name.lower():
                return persona
        
        return None
    
    def create_layered_composition(
        self,
        base_persona: Persona,
        layers: List[Dict[str, Any]]
    ) -> Persona:
        """
        Create a composition using a simplified layering approach.
        
        Args:
            base_persona: The foundation persona
            layers: List of layer configurations with 'persona' and 'strength'
            
        Returns:
            A new layered persona
        """
        result_persona = deepcopy(base_persona)
        result_persona.name = f"layered_{base_persona.name}"
        
        layer_info = []
        
        for i, layer_config in enumerate(layers):
            layer_persona = layer_config["persona"]
            strength = layer_config.get("strength", 0.5)
            target_traits = layer_config.get("traits", list(layer_persona.traits.keys()))
            
            for trait in target_traits:
                layer_value = layer_persona.get_trait(trait)
                current_value = result_persona.get_trait(trait)
                
                if layer_value > 0:
                    # Blend with current value
                    new_value = current_value * (1 - strength) + layer_value * strength
                    result_persona.set_trait(trait, min(1.0, new_value))
            
            layer_info.append({
                "persona": layer_persona.name,
                "strength": strength,
                "traits": target_traits
            })
        
        # Update metadata
        result_persona.metadata.update({
            "layered_composition": True,
            "base_persona": base_persona.name,
            "layers": layer_info
        })
        
        return result_persona