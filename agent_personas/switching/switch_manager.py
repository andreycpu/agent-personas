"""
Switch manager for coordinating persona transitions and state management.
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from ..core.persona import Persona
from ..core.manager import PersonaManager


class SwitchType(Enum):
    """Types of persona switches."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    TRIGGERED = "triggered"
    EMERGENCY = "emergency"


class SwitchReason(Enum):
    """Reasons for persona switches."""
    USER_REQUEST = "user_request"
    CONTEXT_CHANGE = "context_change"
    TIME_BASED = "time_based"
    EMOTIONAL_STATE = "emotional_state"
    CONVERSATION_FLOW = "conversation_flow"
    ERROR_RECOVERY = "error_recovery"
    POLICY_ENFORCEMENT = "policy_enforcement"


@dataclass
class SwitchContext:
    """Context information for a persona switch."""
    from_persona: Optional[str]
    to_persona: str
    switch_type: SwitchType
    switch_reason: SwitchReason
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Context preservation
    preserved_context: Dict[str, Any] = field(default_factory=dict)
    transition_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    user_initiated: bool = False
    confidence: float = 1.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert switch context to dictionary."""
        return {
            "from_persona": self.from_persona,
            "to_persona": self.to_persona,
            "switch_type": self.switch_type.value,
            "switch_reason": self.switch_reason.value,
            "timestamp": self.timestamp.isoformat(),
            "preserved_context": self.preserved_context,
            "transition_data": self.transition_data,
            "user_initiated": self.user_initiated,
            "confidence": self.confidence,
            "notes": self.notes
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwitchContext":
        """Create switch context from dictionary."""
        return cls(
            from_persona=data.get("from_persona"),
            to_persona=data["to_persona"],
            switch_type=SwitchType(data["switch_type"]),
            switch_reason=SwitchReason(data["switch_reason"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            preserved_context=data.get("preserved_context", {}),
            transition_data=data.get("transition_data", {}),
            user_initiated=data.get("user_initiated", False),
            confidence=data.get("confidence", 1.0),
            notes=data.get("notes", "")
        )


@dataclass
class SwitchPolicy:
    """Policy governing when and how persona switches can occur."""
    name: str
    description: str
    
    # Timing constraints
    min_time_between_switches: timedelta = timedelta(minutes=1)
    max_switches_per_hour: int = 10
    cooldown_periods: Dict[str, timedelta] = field(default_factory=dict)
    
    # Context constraints
    required_context_keys: List[str] = field(default_factory=list)
    forbidden_contexts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Persona constraints
    allowed_transitions: Dict[str, List[str]] = field(default_factory=dict)
    blocked_personas: List[str] = field(default_factory=list)
    
    # Override conditions
    emergency_override: bool = True
    user_override: bool = True
    
    def can_switch(
        self, 
        from_persona: Optional[str],
        to_persona: str,
        switch_context: SwitchContext,
        recent_switches: List[SwitchContext]
    ) -> Tuple[bool, str]:
        """
        Check if a switch is allowed under this policy.
        
        Args:
            from_persona: Current persona (if any)
            to_persona: Target persona
            switch_context: Switch context
            recent_switches: Recent switch history
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Emergency override
        if switch_context.switch_type == SwitchType.EMERGENCY and self.emergency_override:
            return True, "Emergency override"
            
        # User override
        if switch_context.user_initiated and self.user_override:
            return True, "User override"
            
        # Check blocked personas
        if to_persona in self.blocked_personas:
            return False, f"Persona '{to_persona}' is blocked"
            
        # Check allowed transitions
        if (from_persona and from_persona in self.allowed_transitions and
            to_persona not in self.allowed_transitions[from_persona]):
            return False, f"Transition from '{from_persona}' to '{to_persona}' not allowed"
            
        # Check timing constraints
        now = datetime.now()
        
        # Min time between switches
        recent_switches_in_period = [
            s for s in recent_switches
            if now - s.timestamp < self.min_time_between_switches
        ]
        if recent_switches_in_period:
            return False, f"Must wait {self.min_time_between_switches} between switches"
            
        # Max switches per hour
        hour_ago = now - timedelta(hours=1)
        switches_last_hour = [
            s for s in recent_switches
            if s.timestamp > hour_ago
        ]
        if len(switches_last_hour) >= self.max_switches_per_hour:
            return False, f"Max {self.max_switches_per_hour} switches per hour exceeded"
            
        # Persona-specific cooldowns
        if to_persona in self.cooldown_periods:
            cooldown = self.cooldown_periods[to_persona]
            recent_to_persona_switches = [
                s for s in recent_switches
                if s.to_persona == to_persona and now - s.timestamp < cooldown
            ]
            if recent_to_persona_switches:
                return False, f"Persona '{to_persona}' in cooldown for {cooldown}"
                
        # Check required context
        for key in self.required_context_keys:
            if key not in switch_context.preserved_context:
                return False, f"Required context key '{key}' missing"
                
        # Check forbidden contexts
        for forbidden_context in self.forbidden_contexts:
            if all(
                switch_context.preserved_context.get(k) == v
                for k, v in forbidden_context.items()
            ):
                return False, "Switch forbidden in current context"
                
        return True, "Policy check passed"


class SwitchManager:
    """
    Manages persona switches with policy enforcement and state preservation.
    """
    
    def __init__(self, persona_manager: PersonaManager):
        self.persona_manager = persona_manager
        self._switch_history: List[SwitchContext] = []
        self._policies: Dict[str, SwitchPolicy] = {}
        self._switch_callbacks: List[Callable[[SwitchContext], None]] = []
        
        # State management
        self._transition_state: Optional[Dict[str, Any]] = None
        self._preserved_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Load default policies
        self._load_default_policies()
        
    def add_policy(self, policy: SwitchPolicy) -> None:
        """Add a switching policy."""
        self._policies[policy.name] = policy
        
    def remove_policy(self, name: str) -> bool:
        """Remove a switching policy."""
        if name in self._policies:
            del self._policies[name]
            return True
        return False
        
    def add_switch_callback(self, callback: Callable[[SwitchContext], None]) -> None:
        """Add a callback to be called after switches."""
        self._switch_callbacks.append(callback)
        
    def can_switch_to(self, persona_name: str, reason: SwitchReason) -> Tuple[bool, str]:
        """
        Check if switching to a persona is allowed.
        
        Args:
            persona_name: Name of target persona
            reason: Reason for the switch
            
        Returns:
            Tuple of (allowed, reason_message)
        """
        current_persona = self.persona_manager.active_persona_name
        
        # Create temporary switch context for policy checking
        temp_context = SwitchContext(
            from_persona=current_persona,
            to_persona=persona_name,
            switch_type=SwitchType.MANUAL,
            switch_reason=reason
        )
        
        # Check all policies
        for policy in self._policies.values():
            allowed, message = policy.can_switch(
                current_persona, persona_name, temp_context, self._switch_history
            )
            if not allowed:
                return False, f"Policy '{policy.name}': {message}"
                
        return True, "All policies allow switch"
        
    def switch_persona(
        self, 
        persona_name: str,
        reason: SwitchReason = SwitchReason.USER_REQUEST,
        switch_type: SwitchType = SwitchType.MANUAL,
        preserved_context: Optional[Dict[str, Any]] = None,
        user_initiated: bool = False,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Switch to a different persona.
        
        Args:
            persona_name: Name of target persona
            reason: Reason for the switch
            switch_type: Type of switch
            preserved_context: Context to preserve across switch
            user_initiated: Whether user initiated the switch
            notes: Optional notes about the switch
            
        Returns:
            Tuple of (success, message)
        """
        current_persona = self.persona_manager.active_persona_name
        
        # Create switch context
        switch_context = SwitchContext(
            from_persona=current_persona,
            to_persona=persona_name,
            switch_type=switch_type,
            switch_reason=reason,
            preserved_context=preserved_context or {},
            user_initiated=user_initiated,
            notes=notes
        )
        
        # Check if switch is allowed
        if switch_type != SwitchType.EMERGENCY:
            for policy in self._policies.values():
                allowed, message = policy.can_switch(
                    current_persona, persona_name, switch_context, self._switch_history
                )
                if not allowed:
                    return False, f"Switch denied by policy '{policy.name}': {message}"
                    
        # Preserve current context if we have an active persona
        if current_persona and current_persona not in self._preserved_contexts:
            self._preserved_contexts[current_persona] = {}
            
        # Perform the switch
        success = self.persona_manager.activate_persona(persona_name)
        
        if not success:
            return False, f"Failed to activate persona '{persona_name}'"
            
        # Record the switch
        self._switch_history.append(switch_context)
        
        # Keep history manageable
        if len(self._switch_history) > 100:
            self._switch_history = self._switch_history[-50:]
            
        # Notify callbacks
        for callback in self._switch_callbacks:
            try:
                callback(switch_context)
            except Exception as e:
                print(f"Error in switch callback: {e}")
                
        return True, f"Successfully switched to '{persona_name}'"
        
    def emergency_switch(
        self, 
        persona_name: str,
        reason: str = "Emergency override"
    ) -> Tuple[bool, str]:
        """
        Perform an emergency persona switch bypassing most policies.
        
        Args:
            persona_name: Name of target persona
            reason: Reason for emergency switch
            
        Returns:
            Tuple of (success, message)
        """
        return self.switch_persona(
            persona_name=persona_name,
            reason=SwitchReason.ERROR_RECOVERY,
            switch_type=SwitchType.EMERGENCY,
            notes=reason
        )
        
    def schedule_switch(
        self, 
        persona_name: str,
        scheduled_time: datetime,
        reason: str = "Scheduled switch"
    ) -> bool:
        """
        Schedule a persona switch for a future time.
        
        Args:
            persona_name: Name of target persona
            scheduled_time: When to perform the switch
            reason: Reason for the switch
            
        Returns:
            True if scheduled successfully
        """
        # This is a placeholder for scheduled switching functionality
        # In a full implementation, this would integrate with a task scheduler
        return True
        
    def get_switch_recommendations(
        self, 
        current_context: Dict[str, Any]
    ) -> List[Tuple[str, float, str]]:
        """
        Get persona switch recommendations based on current context.
        
        Args:
            current_context: Current conversation/environment context
            
        Returns:
            List of (persona_name, confidence, reason) tuples
        """
        recommendations = []
        current_persona = self.persona_manager.active_persona_name
        
        # Get all available personas
        available_personas = self.persona_manager.list_personas()
        
        for persona_name in available_personas:
            if persona_name == current_persona:
                continue
                
            # Check if switch is allowed
            can_switch, _ = self.can_switch_to(persona_name, SwitchReason.CONTEXT_CHANGE)
            if not can_switch:
                continue
                
            # Calculate recommendation score based on context
            score = self._calculate_recommendation_score(persona_name, current_context)
            if score > 0.3:  # Only recommend if confidence is reasonable
                reason = self._get_recommendation_reason(persona_name, current_context)
                recommendations.append((persona_name, score, reason))
                
        # Sort by confidence score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
        
    def _calculate_recommendation_score(
        self, 
        persona_name: str, 
        context: Dict[str, Any]
    ) -> float:
        """Calculate how well a persona fits the current context."""
        # This is a simplified scoring system
        # In practice, this would use more sophisticated matching
        
        score = 0.0
        
        # Context-based scoring
        if "topic" in context:
            topic = context["topic"].lower()
            
            # Simple topic matching (would be more sophisticated in reality)
            topic_matches = {
                "technical": ["engineer", "developer", "expert", "technical"],
                "creative": ["artist", "creative", "writer", "designer"],
                "supportive": ["counselor", "helper", "support", "friend"],
                "professional": ["professional", "business", "formal", "executive"]
            }
            
            for topic_key, matching_terms in topic_matches.items():
                if topic_key in topic:
                    for term in matching_terms:
                        if term in persona_name.lower():
                            score += 0.3
                            break
                            
        # Emotional context
        if "user_emotion" in context:
            emotion = context["user_emotion"].lower()
            
            emotion_matches = {
                "sad": ["counselor", "support", "empathetic"],
                "happy": ["cheerful", "enthusiastic", "positive"],
                "frustrated": ["patient", "calm", "understanding"],
                "excited": ["energetic", "enthusiastic", "upbeat"]
            }
            
            for emotion_key, matching_terms in emotion_matches.items():
                if emotion_key in emotion:
                    for term in matching_terms:
                        if term in persona_name.lower():
                            score += 0.4
                            break
                            
        # Time-based context
        if "time_of_day" in context:
            hour = context.get("hour", 12)
            
            if 6 <= hour <= 10:  # Morning
                if "morning" in persona_name.lower() or "energetic" in persona_name.lower():
                    score += 0.2
            elif 22 <= hour or hour <= 6:  # Night
                if "calm" in persona_name.lower() or "gentle" in persona_name.lower():
                    score += 0.2
                    
        return min(1.0, score)  # Cap at 1.0
        
    def _get_recommendation_reason(self, persona_name: str, context: Dict[str, Any]) -> str:
        """Get a human-readable reason for the recommendation."""
        reasons = []
        
        if "topic" in context:
            topic = context["topic"]
            reasons.append(f"Good fit for {topic} topic")
            
        if "user_emotion" in context:
            emotion = context["user_emotion"]
            reasons.append(f"Appropriate for user's {emotion} mood")
            
        if not reasons:
            reasons.append("General contextual match")
            
        return "; ".join(reasons)
        
    def get_switch_history(self, limit: Optional[int] = None) -> List[SwitchContext]:
        """Get recent switch history."""
        history = self._switch_history.copy()
        if limit:
            history = history[-limit:]
        return history
        
    def analyze_switch_patterns(self, days_back: int = 7) -> Dict[str, Any]:
        """Analyze persona switching patterns."""
        cutoff_time = datetime.now() - timedelta(days=days_back)
        recent_switches = [
            switch for switch in self._switch_history
            if switch.timestamp > cutoff_time
        ]
        
        if not recent_switches:
            return {"message": "No recent switches to analyze"}
            
        # Count switches by type, reason, persona
        type_counts = {}
        reason_counts = {}
        persona_counts = {}
        
        for switch in recent_switches:
            type_counts[switch.switch_type.value] = type_counts.get(switch.switch_type.value, 0) + 1
            reason_counts[switch.switch_reason.value] = reason_counts.get(switch.switch_reason.value, 0) + 1
            persona_counts[switch.to_persona] = persona_counts.get(switch.to_persona, 0) + 1
            
        # Calculate average time between switches
        if len(recent_switches) > 1:
            time_diffs = []
            for i in range(1, len(recent_switches)):
                diff = recent_switches[i].timestamp - recent_switches[i-1].timestamp
                time_diffs.append(diff.total_seconds() / 60)  # Convert to minutes
            avg_time_between = sum(time_diffs) / len(time_diffs)
        else:
            avg_time_between = 0
            
        return {
            "analysis_period": f"{days_back} days",
            "total_switches": len(recent_switches),
            "switch_types": type_counts,
            "switch_reasons": reason_counts,
            "persona_usage": persona_counts,
            "most_used_persona": max(persona_counts.items(), key=lambda x: x[1]) if persona_counts else None,
            "most_common_reason": max(reason_counts.items(), key=lambda x: x[1]) if reason_counts else None,
            "avg_time_between_switches_minutes": avg_time_between,
            "user_initiated_ratio": len([s for s in recent_switches if s.user_initiated]) / len(recent_switches)
        }
        
    def _load_default_policies(self) -> None:
        """Load default switching policies."""
        
        # Basic policy with reasonable constraints
        basic_policy = SwitchPolicy(
            name="basic",
            description="Basic switching policy with standard constraints",
            min_time_between_switches=timedelta(seconds=30),
            max_switches_per_hour=20,
            emergency_override=True,
            user_override=True
        )
        
        # Conservative policy for production use
        conservative_policy = SwitchPolicy(
            name="conservative",
            description="Conservative policy limiting frequent switches",
            min_time_between_switches=timedelta(minutes=2),
            max_switches_per_hour=10,
            cooldown_periods={
                "emergency": timedelta(minutes=5),
                "critical": timedelta(minutes=3)
            },
            emergency_override=True,
            user_override=False  # Require policy compliance even for users
        )
        
        self.add_policy(basic_policy)