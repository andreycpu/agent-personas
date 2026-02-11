"""
Behavior engine for managing and executing behavior rules.
"""

from typing import Dict, List, Any, Optional, Callable, Set
import logging
from datetime import datetime

from .behavior_rule import BehaviorRule, BehaviorCondition, BehaviorAction


class BehaviorEngine:
    """
    Engine for managing and executing behavior rules based on context.
    """
    
    def __init__(self):
        self._rules: Dict[str, BehaviorRule] = {}
        self._rule_groups: Dict[str, List[str]] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._context_processors: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
        self._modification_handlers: Dict[str, Callable[[Any, Dict[str, Any]], Any]] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Register default modification handlers
        self._register_default_handlers()
        
    def add_rule(self, rule: BehaviorRule) -> None:
        """Add a behavior rule to the engine."""
        if rule.name in self._rules:
            raise ValueError(f"Rule '{rule.name}' already exists")
        self._rules[rule.name] = rule
        self.logger.debug(f"Added behavior rule: {rule.name}")
        
    def remove_rule(self, rule_name: str) -> Optional[BehaviorRule]:
        """Remove a behavior rule from the engine."""
        rule = self._rules.pop(rule_name, None)
        if rule:
            self.logger.debug(f"Removed behavior rule: {rule_name}")
        return rule
        
    def get_rule(self, rule_name: str) -> Optional[BehaviorRule]:
        """Get a behavior rule by name."""
        return self._rules.get(rule_name)
        
    def list_rules(self) -> List[BehaviorRule]:
        """Get all behavior rules."""
        return list(self._rules.values())
        
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a specific rule."""
        rule = self._rules.get(rule_name)
        if rule:
            rule.enabled = True
            return True
        return False
        
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a specific rule."""
        rule = self._rules.get(rule_name)
        if rule:
            rule.enabled = False
            return True
        return False
        
    def create_rule_group(self, group_name: str, rule_names: List[str]) -> None:
        """Create a group of rules for batch operations."""
        # Validate that all rules exist
        for rule_name in rule_names:
            if rule_name not in self._rules:
                raise ValueError(f"Rule '{rule_name}' not found")
        self._rule_groups[group_name] = rule_names.copy()
        
    def enable_rule_group(self, group_name: str) -> bool:
        """Enable all rules in a group."""
        if group_name not in self._rule_groups:
            return False
        for rule_name in self._rule_groups[group_name]:
            self.enable_rule(rule_name)
        return True
        
    def disable_rule_group(self, group_name: str) -> bool:
        """Disable all rules in a group."""
        if group_name not in self._rule_groups:
            return False
        for rule_name in self._rule_groups[group_name]:
            self.disable_rule(rule_name)
        return True
        
    def add_context_processor(self, processor: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Add a context processor that can modify context before rule evaluation."""
        self._context_processors.append(processor)
        
    def add_modification_handler(
        self, 
        modification_key: str, 
        handler: Callable[[Any, Dict[str, Any]], Any]
    ) -> None:
        """
        Add a handler for processing specific types of modifications.
        
        Args:
            modification_key: Key in modifications dict to handle
            handler: Function that takes (current_value, context) and returns new value
        """
        self._modification_handlers[modification_key] = handler
        
    def process_context(
        self, 
        context: Dict[str, Any], 
        apply_modifications: bool = True
    ) -> Dict[str, Any]:
        """
        Process context through behavior rules and return modifications.
        
        Args:
            context: Current context including traits, user input, etc.
            apply_modifications: Whether to apply modifications to context
            
        Returns:
            Dictionary containing applied modifications
        """
        # Process context through processors
        processed_context = context.copy()
        for processor in self._context_processors:
            processed_context = processor(processed_context)
            
        # Find applicable rules
        applicable_rules = []
        for rule in self._rules.values():
            if rule.evaluate(processed_context):
                applicable_rules.append(rule)
                
        # Sort by priority (higher first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Execute rules and collect modifications
        all_modifications = {}
        executed_rules = []
        
        for rule in applicable_rules:
            try:
                modifications = rule.trigger(processed_context)
                if modifications:
                    executed_rules.append({
                        "rule_name": rule.name,
                        "modifications": modifications.copy()
                    })
                    
                    # Merge modifications
                    self._merge_modifications(all_modifications, modifications)
                    
                    # Update context with modifications for subsequent rules
                    if apply_modifications:
                        processed_context = self._apply_modifications_to_context(
                            processed_context, modifications
                        )
                        
            except Exception as e:
                self.logger.error(f"Error executing rule '{rule.name}': {e}")
                
        # Record execution history
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "original_context": context,
            "processed_context": processed_context,
            "executed_rules": executed_rules,
            "total_modifications": all_modifications
        }
        self._execution_history.append(execution_record)
        
        # Keep history size manageable
        if len(self._execution_history) > 100:
            self._execution_history = self._execution_history[-50:]
            
        return all_modifications
        
    def _merge_modifications(
        self, 
        target: Dict[str, Any], 
        source: Dict[str, Any]
    ) -> None:
        """Merge source modifications into target."""
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    target[key].update(value)
                elif isinstance(value, list) and isinstance(target[key], list):
                    target[key].extend(value)
                else:
                    target[key] = value
            else:
                target[key] = value
                
    def _apply_modifications_to_context(
        self, 
        context: Dict[str, Any], 
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply modifications to context using registered handlers."""
        updated_context = context.copy()
        
        for key, value in modifications.items():
            if key in self._modification_handlers:
                # Use custom handler
                handler = self._modification_handlers[key]
                try:
                    updated_context[key] = handler(value, updated_context)
                except Exception as e:
                    self.logger.error(f"Error in modification handler for '{key}': {e}")
            else:
                # Default behavior: direct assignment
                updated_context[key] = value
                
        return updated_context
        
    def simulate_rules(
        self, 
        context: Dict[str, Any], 
        rule_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Simulate rule execution without actually applying modifications.
        
        Args:
            context: Context to simulate against
            rule_names: Optional list of specific rules to test
            
        Returns:
            Simulation results
        """
        rules_to_test = []
        
        if rule_names:
            for name in rule_names:
                rule = self._rules.get(name)
                if rule:
                    rules_to_test.append(rule)
        else:
            rules_to_test = list(self._rules.values())
            
        simulation_results = {
            "triggered_rules": [],
            "modifications": {},
            "rule_evaluations": {}
        }
        
        for rule in rules_to_test:
            try:
                would_trigger = rule.evaluate(context)
                simulation_results["rule_evaluations"][rule.name] = {
                    "would_trigger": would_trigger,
                    "enabled": rule.enabled,
                    "trigger_count": rule.trigger_count,
                    "conditions": [
                        {
                            "description": condition.description,
                            "result": condition.evaluate(context)
                        }
                        for condition in rule.conditions
                    ]
                }
                
                if would_trigger:
                    # Simulate without actually triggering
                    temp_count = rule.trigger_count
                    temp_turn = rule.last_triggered_turn
                    
                    modifications = rule.trigger(context)
                    
                    # Restore state
                    rule.trigger_count = temp_count
                    rule.last_triggered_turn = temp_turn
                    
                    if modifications:
                        simulation_results["triggered_rules"].append(rule.name)
                        self._merge_modifications(simulation_results["modifications"], modifications)
                        
            except Exception as e:
                simulation_results["rule_evaluations"][rule.name] = {
                    "error": str(e)
                }
                
        return simulation_results
        
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get execution history."""
        history = self._execution_history.copy()
        if limit:
            history = history[-limit:]
        return history
        
    def clear_execution_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()
        
    def reset_all_rules(self) -> None:
        """Reset trigger tracking for all rules."""
        for rule in self._rules.values():
            rule.reset()
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        total_rules = len(self._rules)
        enabled_rules = sum(1 for rule in self._rules.values() if rule.enabled)
        
        rule_stats = {}
        for rule in self._rules.values():
            rule_stats[rule.name] = {
                "enabled": rule.enabled,
                "trigger_count": rule.trigger_count,
                "conditions": len(rule.conditions),
                "actions": len(rule.actions)
            }
            
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": total_rules - enabled_rules,
            "rule_groups": len(self._rule_groups),
            "context_processors": len(self._context_processors),
            "modification_handlers": len(self._modification_handlers),
            "execution_history_size": len(self._execution_history),
            "rule_statistics": rule_stats
        }
        
    def _register_default_handlers(self) -> None:
        """Register default modification handlers."""
        
        def handle_trait_adjustments(adjustments: Dict[str, float], context: Dict[str, Any]) -> Dict[str, float]:
            current_traits = context.get("traits", {})
            updated_traits = current_traits.copy()
            updated_traits.update(adjustments)
            return updated_traits
            
        def handle_response_modifiers(modifiers: Dict[str, str], context: Dict[str, Any]) -> Dict[str, str]:
            current_modifiers = context.get("response_modifiers", {})
            updated_modifiers = current_modifiers.copy()
            updated_modifiers.update(modifiers)
            return updated_modifiers
            
        self.add_modification_handler("trait_adjustments", handle_trait_adjustments)
        self.add_modification_handler("response_modifiers", handle_response_modifiers)