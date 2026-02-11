"""
Behavior rule definitions for contextual agent behavior.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import re


class ConditionType(Enum):
    """Types of behavior conditions."""
    TRAIT_THRESHOLD = "trait_threshold"
    CONTEXT_VALUE = "context_value"
    USER_INPUT = "user_input"
    EMOTIONAL_STATE = "emotional_state"
    TIME_BASED = "time_based"
    CONVERSATION_LENGTH = "conversation_length"
    CUSTOM = "custom"


class ActionType(Enum):
    """Types of behavior actions."""
    SET_RESPONSE_STYLE = "set_response_style"
    ADJUST_TRAIT = "adjust_trait"
    CHANGE_EMOTION = "change_emotion"
    ADD_RESPONSE_PREFIX = "add_response_prefix"
    ADD_RESPONSE_SUFFIX = "add_response_suffix"
    SET_VERBOSITY = "set_verbosity"
    TRIGGER_BEHAVIOR = "trigger_behavior"
    CUSTOM = "custom"


@dataclass
class BehaviorCondition:
    """
    Represents a condition that triggers behavior changes.
    """
    condition_type: ConditionType
    parameters: Dict[str, Any]
    weight: float = 1.0
    description: str = ""
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if this condition is met in the given context.
        
        Args:
            context: Current context including traits, user input, etc.
            
        Returns:
            True if condition is met
        """
        if self.condition_type == ConditionType.TRAIT_THRESHOLD:
            trait_name = self.parameters.get("trait")
            threshold = self.parameters.get("threshold", 0.5)
            operator = self.parameters.get("operator", ">=")
            
            trait_value = context.get("traits", {}).get(trait_name, 0.0)
            
            if operator == ">=":
                return trait_value >= threshold
            elif operator == ">":
                return trait_value > threshold
            elif operator == "<=":
                return trait_value <= threshold
            elif operator == "<":
                return trait_value < threshold
            elif operator == "==":
                return abs(trait_value - threshold) < 0.01
                
        elif self.condition_type == ConditionType.CONTEXT_VALUE:
            key = self.parameters.get("key")
            expected_value = self.parameters.get("value")
            operator = self.parameters.get("operator", "==")
            
            actual_value = context.get(key)
            
            if operator == "==":
                return actual_value == expected_value
            elif operator == "!=":
                return actual_value != expected_value
            elif operator == "in":
                return actual_value in expected_value
            elif operator == "contains":
                return expected_value in str(actual_value)
                
        elif self.condition_type == ConditionType.USER_INPUT:
            user_input = context.get("user_input", "")
            pattern = self.parameters.get("pattern", "")
            case_sensitive = self.parameters.get("case_sensitive", False)
            
            if not case_sensitive:
                user_input = user_input.lower()
                pattern = pattern.lower()
                
            match_type = self.parameters.get("match_type", "contains")
            
            if match_type == "contains":
                return pattern in user_input
            elif match_type == "starts_with":
                return user_input.startswith(pattern)
            elif match_type == "ends_with":
                return user_input.endswith(pattern)
            elif match_type == "regex":
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(pattern, user_input, flags))
            elif match_type == "exact":
                return user_input == pattern
                
        elif self.condition_type == ConditionType.EMOTIONAL_STATE:
            current_emotion = context.get("emotional_state", "neutral")
            target_emotions = self.parameters.get("emotions", [])
            
            if isinstance(target_emotions, str):
                target_emotions = [target_emotions]
                
            return current_emotion in target_emotions
            
        elif self.condition_type == ConditionType.CONVERSATION_LENGTH:
            turn_count = context.get("conversation_turn_count", 0)
            threshold = self.parameters.get("threshold", 5)
            operator = self.parameters.get("operator", ">=")
            
            if operator == ">=":
                return turn_count >= threshold
            elif operator == ">":
                return turn_count > threshold
            elif operator == "<=":
                return turn_count <= threshold
            elif operator == "<":
                return turn_count < threshold
                
        elif self.condition_type == ConditionType.CUSTOM:
            evaluator = self.parameters.get("evaluator")
            if callable(evaluator):
                return evaluator(context, self.parameters)
                
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert condition to dictionary."""
        return {
            "condition_type": self.condition_type.value,
            "parameters": self.parameters,
            "weight": self.weight,
            "description": self.description
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorCondition":
        """Create condition from dictionary."""
        return cls(
            condition_type=ConditionType(data["condition_type"]),
            parameters=data["parameters"],
            weight=data.get("weight", 1.0),
            description=data.get("description", "")
        )


@dataclass
class BehaviorAction:
    """
    Represents an action to take when behavior conditions are met.
    """
    action_type: ActionType
    parameters: Dict[str, Any]
    priority: int = 0
    description: str = ""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this action and return modifications to apply.
        
        Args:
            context: Current context
            
        Returns:
            Dictionary of modifications to apply
        """
        modifications = {}
        
        if self.action_type == ActionType.SET_RESPONSE_STYLE:
            style = self.parameters.get("style", "neutral")
            modifications["response_style"] = style
            
        elif self.action_type == ActionType.ADJUST_TRAIT:
            trait_name = self.parameters.get("trait")
            adjustment = self.parameters.get("adjustment", 0.0)
            adjustment_type = self.parameters.get("type", "relative")  # relative or absolute
            
            current_traits = context.get("traits", {})
            current_value = current_traits.get(trait_name, 0.5)
            
            if adjustment_type == "relative":
                new_value = max(0.0, min(1.0, current_value + adjustment))
            else:  # absolute
                new_value = max(0.0, min(1.0, adjustment))
                
            if "trait_adjustments" not in modifications:
                modifications["trait_adjustments"] = {}
            modifications["trait_adjustments"][trait_name] = new_value
            
        elif self.action_type == ActionType.CHANGE_EMOTION:
            new_emotion = self.parameters.get("emotion", "neutral")
            intensity = self.parameters.get("intensity", 0.5)
            modifications["emotional_state"] = new_emotion
            modifications["emotional_intensity"] = intensity
            
        elif self.action_type == ActionType.ADD_RESPONSE_PREFIX:
            prefix = self.parameters.get("prefix", "")
            if "response_modifiers" not in modifications:
                modifications["response_modifiers"] = {}
            modifications["response_modifiers"]["prefix"] = prefix
            
        elif self.action_type == ActionType.ADD_RESPONSE_SUFFIX:
            suffix = self.parameters.get("suffix", "")
            if "response_modifiers" not in modifications:
                modifications["response_modifiers"] = {}
            modifications["response_modifiers"]["suffix"] = suffix
            
        elif self.action_type == ActionType.SET_VERBOSITY:
            verbosity = self.parameters.get("level", 0.5)
            modifications["verbosity_level"] = verbosity
            
        elif self.action_type == ActionType.TRIGGER_BEHAVIOR:
            behavior_name = self.parameters.get("behavior")
            if "triggered_behaviors" not in modifications:
                modifications["triggered_behaviors"] = []
            modifications["triggered_behaviors"].append(behavior_name)
            
        elif self.action_type == ActionType.CUSTOM:
            executor = self.parameters.get("executor")
            if callable(executor):
                result = executor(context, self.parameters)
                if isinstance(result, dict):
                    modifications.update(result)
                    
        return modifications
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        return {
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "priority": self.priority,
            "description": self.description
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorAction":
        """Create action from dictionary."""
        return cls(
            action_type=ActionType(data["action_type"]),
            parameters=data["parameters"],
            priority=data.get("priority", 0),
            description=data.get("description", "")
        )


@dataclass
class BehaviorRule:
    """
    Represents a complete behavior rule with conditions and actions.
    """
    name: str
    description: str
    conditions: List[BehaviorCondition] = field(default_factory=list)
    actions: List[BehaviorAction] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    require_all_conditions: bool = True  # If False, any condition can trigger
    cooldown_turns: int = 0  # Turns to wait before rule can trigger again
    max_triggers: Optional[int] = None  # Maximum times rule can trigger
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.trigger_count = 0
        self.last_triggered_turn = -1
        
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if this rule should trigger in the given context.
        
        Args:
            context: Current context
            
        Returns:
            True if rule should trigger
        """
        if not self.enabled:
            return False
            
        # Check cooldown
        current_turn = context.get("conversation_turn_count", 0)
        if self.cooldown_turns > 0:
            turns_since_trigger = current_turn - self.last_triggered_turn
            if turns_since_trigger < self.cooldown_turns:
                return False
                
        # Check max triggers
        if self.max_triggers is not None and self.trigger_count >= self.max_triggers:
            return False
            
        # Evaluate conditions
        if not self.conditions:
            return True
            
        condition_results = [condition.evaluate(context) for condition in self.conditions]
        
        if self.require_all_conditions:
            return all(condition_results)
        else:
            return any(condition_results)
            
    def trigger(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger this rule and return the combined modifications.
        
        Args:
            context: Current context
            
        Returns:
            Dictionary of modifications to apply
        """
        if not self.evaluate(context):
            return {}
            
        # Update trigger tracking
        self.trigger_count += 1
        self.last_triggered_turn = context.get("conversation_turn_count", 0)
        
        # Execute all actions
        all_modifications = {}
        sorted_actions = sorted(self.actions, key=lambda a: a.priority, reverse=True)
        
        for action in sorted_actions:
            modifications = action.execute(context)
            
            # Merge modifications (later actions can override earlier ones)
            for key, value in modifications.items():
                if isinstance(value, dict) and key in all_modifications:
                    all_modifications[key].update(value)
                elif isinstance(value, list) and key in all_modifications:
                    all_modifications[key].extend(value)
                else:
                    all_modifications[key] = value
                    
        return all_modifications
        
    def reset(self) -> None:
        """Reset trigger tracking for this rule."""
        self.trigger_count = 0
        self.last_triggered_turn = -1
        
    def add_condition(self, condition: BehaviorCondition) -> None:
        """Add a condition to this rule."""
        self.conditions.append(condition)
        
    def add_action(self, action: BehaviorAction) -> None:
        """Add an action to this rule."""
        self.actions.append(action)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "priority": self.priority,
            "require_all_conditions": self.require_all_conditions,
            "cooldown_turns": self.cooldown_turns,
            "max_triggers": self.max_triggers,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorRule":
        """Create rule from dictionary."""
        conditions = [BehaviorCondition.from_dict(c) for c in data.get("conditions", [])]
        actions = [BehaviorAction.from_dict(a) for a in data.get("actions", [])]
        
        return cls(
            name=data["name"],
            description=data["description"],
            conditions=conditions,
            actions=actions,
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            require_all_conditions=data.get("require_all_conditions", True),
            cooldown_turns=data.get("cooldown_turns", 0),
            max_triggers=data.get("max_triggers"),
            metadata=data.get("metadata", {})
        )