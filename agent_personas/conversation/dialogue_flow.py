"""
Dialogue flow management for conversation state and transitions.
"""

from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json


class FlowState(Enum):
    """States in a dialogue flow."""
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    PROBLEM_SOLVING = "problem_solving"
    EXPLANATION = "explanation"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    CLOSURE = "closure"
    SMALL_TALK = "small_talk"
    ERROR_HANDLING = "error_handling"
    WAITING_INPUT = "waiting_input"


class TransitionTrigger(Enum):
    """Types of triggers for state transitions."""
    USER_INTENT = "user_intent"
    KEYWORD = "keyword"
    EMOTION = "emotion"
    TIME_BASED = "time_based"
    COMPLETION = "completion"
    ERROR = "error"
    CONTEXT_CHANGE = "context_change"


@dataclass
class DialogueTransition:
    """Represents a transition between dialogue states."""
    from_state: FlowState
    to_state: FlowState
    trigger_type: TransitionTrigger
    trigger_condition: str
    probability: float = 1.0
    requirements: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    description: str = ""
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if this transition should trigger given the context."""
        if self.trigger_type == TransitionTrigger.USER_INTENT:
            user_intent = context.get("user_intent", "")
            return user_intent == self.trigger_condition
            
        elif self.trigger_type == TransitionTrigger.KEYWORD:
            user_input = context.get("user_input", "").lower()
            keywords = self.trigger_condition.lower().split(",")
            return any(keyword.strip() in user_input for keyword in keywords)
            
        elif self.trigger_type == TransitionTrigger.EMOTION:
            user_emotion = context.get("user_emotion", "")
            return user_emotion == self.trigger_condition
            
        elif self.trigger_type == TransitionTrigger.TIME_BASED:
            elapsed_time = context.get("state_duration", 0)
            max_time = int(self.trigger_condition)
            return elapsed_time >= max_time
            
        elif self.trigger_type == TransitionTrigger.COMPLETION:
            task_completed = context.get("task_completed", False)
            return task_completed == (self.trigger_condition.lower() == "true")
            
        elif self.trigger_type == TransitionTrigger.ERROR:
            error_occurred = context.get("error_occurred", False)
            return error_occurred
            
        elif self.trigger_type == TransitionTrigger.CONTEXT_CHANGE:
            key, expected_value = self.trigger_condition.split("=")
            return context.get(key.strip()) == expected_value.strip()
            
        return False
        
    def check_requirements(self, context: Dict[str, Any]) -> bool:
        """Check if all requirements are met for this transition."""
        for key, expected in self.requirements.items():
            actual = context.get(key)
            if actual != expected:
                return False
        return True


@dataclass
class FlowStateConfig:
    """Configuration for a dialogue flow state."""
    state: FlowState
    name: str
    description: str
    entry_actions: List[str] = field(default_factory=list)
    exit_actions: List[str] = field(default_factory=list)
    max_duration: Optional[int] = None  # Maximum time in this state (seconds)
    response_templates: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DialogueFlowManager:
    """
    Manages dialogue flow states and transitions.
    """
    
    def __init__(self):
        self._states: Dict[FlowState, FlowStateConfig] = {}
        self._transitions: List[DialogueTransition] = []
        self._current_state: Optional[FlowState] = None
        self._state_history: List[Tuple[FlowState, datetime]] = []
        self._state_entry_time: Optional[datetime] = None
        self._context_memory: Dict[str, Any] = {}
        self._action_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        
        # Load default flow configuration
        self._load_default_flow()
        
    def add_state(self, config: FlowStateConfig) -> None:
        """Add a dialogue state configuration."""
        self._states[config.state] = config
        
    def add_transition(self, transition: DialogueTransition) -> None:
        """Add a dialogue transition."""
        self._transitions.append(transition)
        
    def set_current_state(self, state: FlowState, context: Dict[str, Any] = None) -> None:
        """Set the current dialogue state."""
        if context is None:
            context = {}
            
        # Execute exit actions for current state
        if self._current_state and self._current_state in self._states:
            current_config = self._states[self._current_state]
            for action in current_config.exit_actions:
                self._execute_action(action, context)
                
        # Update state
        previous_state = self._current_state
        self._current_state = state
        self._state_entry_time = datetime.now()
        
        # Record in history
        if previous_state:
            self._state_history.append((previous_state, datetime.now()))
            
        # Execute entry actions for new state
        if state in self._states:
            new_config = self._states[state]
            for action in new_config.entry_actions:
                self._execute_action(action, context)
                
    def get_current_state(self) -> Optional[FlowState]:
        """Get the current dialogue state."""
        return self._current_state
        
    def get_state_duration(self) -> int:
        """Get the duration in current state (seconds)."""
        if self._state_entry_time:
            return int((datetime.now() - self._state_entry_time).total_seconds())
        return 0
        
    def process_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a conversation turn and handle state transitions.
        
        Args:
            context: Current conversation context
            
        Returns:
            Updated context with flow information
        """
        # Add flow context
        flow_context = context.copy()
        flow_context.update({
            "current_state": self._current_state,
            "state_duration": self.get_state_duration(),
            "state_history": self._state_history.copy()
        })
        
        # Check for transitions
        triggered_transition = self._check_transitions(flow_context)
        
        if triggered_transition:
            # Execute transition actions
            for action in triggered_transition.actions:
                self._execute_action(action, flow_context)
                
            # Change state
            self.set_current_state(triggered_transition.to_state, flow_context)
            flow_context["state_changed"] = True
            flow_context["previous_state"] = triggered_transition.from_state
            flow_context["current_state"] = self._current_state
        else:
            flow_context["state_changed"] = False
            
        # Add current state information
        if self._current_state in self._states:
            state_config = self._states[self._current_state]
            flow_context.update({
                "state_name": state_config.name,
                "state_description": state_config.description,
                "response_templates": state_config.response_templates,
                "follow_up_questions": state_config.follow_up_questions
            })
            
        return flow_context
        
    def _check_transitions(self, context: Dict[str, Any]) -> Optional[DialogueTransition]:
        """Check if any transitions should trigger."""
        if not self._current_state:
            return None
            
        # Find applicable transitions from current state
        applicable_transitions = [
            t for t in self._transitions 
            if t.from_state == self._current_state
        ]
        
        # Sort by probability (highest first) for deterministic behavior
        applicable_transitions.sort(key=lambda t: t.probability, reverse=True)
        
        for transition in applicable_transitions:
            if (transition.matches(context) and 
                transition.check_requirements(context)):
                return transition
                
        return None
        
    def get_possible_transitions(self) -> List[DialogueTransition]:
        """Get all possible transitions from the current state."""
        if not self._current_state:
            return []
            
        return [
            t for t in self._transitions
            if t.from_state == self._current_state
        ]
        
    def get_suggested_responses(self) -> List[str]:
        """Get suggested responses for the current state."""
        if not self._current_state or self._current_state not in self._states:
            return []
            
        state_config = self._states[self._current_state]
        return state_config.response_templates.copy()
        
    def get_follow_up_questions(self) -> List[str]:
        """Get follow-up questions for the current state."""
        if not self._current_state or self._current_state not in self._states:
            return []
            
        state_config = self._states[self._current_state]
        return state_config.follow_up_questions.copy()
        
    def add_action_handler(self, action_name: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add a handler for a specific action."""
        self._action_handlers[action_name] = handler
        
    def _execute_action(self, action: str, context: Dict[str, Any]) -> None:
        """Execute a dialogue action."""
        if action in self._action_handlers:
            try:
                self._action_handlers[action](context)
            except Exception as e:
                # Log error but don't break flow
                print(f"Error executing action '{action}': {e}")
        else:
            # Default action handling
            if action == "reset_context":
                self._context_memory.clear()
            elif action == "save_context":
                self._context_memory.update(context)
            elif action.startswith("set_"):
                # Set a context variable
                parts = action.split("_", 2)
                if len(parts) == 3:
                    key = parts[1]
                    value = parts[2]
                    context[key] = value
                    
    def analyze_conversation_flow(self) -> Dict[str, Any]:
        """Analyze the conversation flow patterns."""
        if len(self._state_history) < 2:
            return {"message": "Not enough flow history for analysis"}
            
        # Count state frequencies
        state_counts = {}
        for state, _ in self._state_history:
            state_counts[state.value] = state_counts.get(state.value, 0) + 1
            
        # Calculate transition patterns
        transition_patterns = {}
        for i in range(len(self._state_history) - 1):
            from_state = self._state_history[i][0]
            to_state = self._state_history[i + 1][0]
            transition_key = f"{from_state.value} -> {to_state.value}"
            transition_patterns[transition_key] = transition_patterns.get(transition_key, 0) + 1
            
        # Calculate average time in states
        state_durations = {}
        for i in range(len(self._state_history) - 1):
            state = self._state_history[i][0]
            duration = (self._state_history[i + 1][1] - self._state_history[i][1]).total_seconds()
            if state.value not in state_durations:
                state_durations[state.value] = []
            state_durations[state.value].append(duration)
            
        avg_durations = {}
        for state, durations in state_durations.items():
            avg_durations[state] = sum(durations) / len(durations)
            
        return {
            "total_state_changes": len(self._state_history),
            "state_frequencies": state_counts,
            "transition_patterns": transition_patterns,
            "average_state_durations": avg_durations,
            "current_state": self._current_state.value if self._current_state else None,
            "current_state_duration": self.get_state_duration()
        }
        
    def reset_flow(self) -> None:
        """Reset the dialogue flow to initial state."""
        self._current_state = None
        self._state_history.clear()
        self._state_entry_time = None
        self._context_memory.clear()
        
    def export_flow_config(self) -> Dict[str, Any]:
        """Export the current flow configuration."""
        return {
            "states": {
                state.value: {
                    "name": config.name,
                    "description": config.description,
                    "entry_actions": config.entry_actions,
                    "exit_actions": config.exit_actions,
                    "max_duration": config.max_duration,
                    "response_templates": config.response_templates,
                    "follow_up_questions": config.follow_up_questions,
                    "metadata": config.metadata
                }
                for state, config in self._states.items()
            },
            "transitions": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "trigger_type": t.trigger_type.value,
                    "trigger_condition": t.trigger_condition,
                    "probability": t.probability,
                    "requirements": t.requirements,
                    "actions": t.actions,
                    "description": t.description
                }
                for t in self._transitions
            ]
        }
        
    def _load_default_flow(self) -> None:
        """Load default dialogue flow configuration."""
        
        # Define states
        greeting_state = FlowStateConfig(
            state=FlowState.GREETING,
            name="Greeting",
            description="Initial greeting and welcome",
            response_templates=[
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Welcome! How may I assist you?"
            ],
            follow_up_questions=[
                "What brings you here today?",
                "Is there something specific you'd like help with?"
            ],
            max_duration=30
        )
        
        info_gathering_state = FlowStateConfig(
            state=FlowState.INFORMATION_GATHERING,
            name="Information Gathering",
            description="Collecting information from the user",
            response_templates=[
                "Could you tell me more about that?",
                "I'd like to understand better. Can you provide more details?",
                "That's interesting. What else can you tell me?"
            ],
            follow_up_questions=[
                "When did this happen?",
                "How did that make you feel?",
                "What would you like to see happen?"
            ]
        )
        
        problem_solving_state = FlowStateConfig(
            state=FlowState.PROBLEM_SOLVING,
            name="Problem Solving",
            description="Working on solving the user's problem",
            response_templates=[
                "Let me help you work through this.",
                "Here's what I suggest we try:",
                "Based on what you've told me, I think we should..."
            ],
            follow_up_questions=[
                "Does that make sense to you?",
                "Would you like me to explain any part in more detail?",
                "Are there any concerns about this approach?"
            ]
        )
        
        closure_state = FlowStateConfig(
            state=FlowState.CLOSURE,
            name="Closure",
            description="Wrapping up the conversation",
            response_templates=[
                "Is there anything else I can help you with?",
                "I hope I've been able to help you today.",
                "Thank you for the conversation!"
            ],
            follow_up_questions=[
                "Do you have any other questions?",
                "Is there anything else on your mind?"
            ]
        )
        
        # Add states
        for state in [greeting_state, info_gathering_state, problem_solving_state, closure_state]:
            self.add_state(state)
            
        # Define transitions
        transitions = [
            # From greeting
            DialogueTransition(
                from_state=FlowState.GREETING,
                to_state=FlowState.INFORMATION_GATHERING,
                trigger_type=TransitionTrigger.USER_INTENT,
                trigger_condition="question",
                description="User asks a question"
            ),
            
            DialogueTransition(
                from_state=FlowState.GREETING,
                to_state=FlowState.SMALL_TALK,
                trigger_type=TransitionTrigger.KEYWORD,
                trigger_condition="how are you,nice day,weather",
                description="User initiates small talk"
            ),
            
            # From information gathering
            DialogueTransition(
                from_state=FlowState.INFORMATION_GATHERING,
                to_state=FlowState.PROBLEM_SOLVING,
                trigger_type=TransitionTrigger.COMPLETION,
                trigger_condition="true",
                description="Enough information gathered"
            ),
            
            DialogueTransition(
                from_state=FlowState.INFORMATION_GATHERING,
                to_state=FlowState.CLARIFICATION,
                trigger_type=TransitionTrigger.KEYWORD,
                trigger_condition="confused,what do you mean,unclear",
                description="User needs clarification"
            ),
            
            # From problem solving
            DialogueTransition(
                from_state=FlowState.PROBLEM_SOLVING,
                to_state=FlowState.CLOSURE,
                trigger_type=TransitionTrigger.COMPLETION,
                trigger_condition="true",
                description="Problem resolved"
            ),
            
            DialogueTransition(
                from_state=FlowState.PROBLEM_SOLVING,
                to_state=FlowState.EXPLANATION,
                trigger_type=TransitionTrigger.KEYWORD,
                trigger_condition="why,how does,explain",
                description="User needs explanation"
            ),
            
            # General transitions
            DialogueTransition(
                from_state=FlowState.GREETING,
                to_state=FlowState.CLOSURE,
                trigger_type=TransitionTrigger.KEYWORD,
                trigger_condition="goodbye,bye,thanks,thank you",
                description="User says goodbye"
            )
        ]
        
        for transition in transitions:
            self.add_transition(transition)
            
        # Set initial state
        self.set_current_state(FlowState.GREETING)