"""
Context manager for handling conversation context and state.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json


class ContextScope(Enum):
    """Scopes for context information."""
    SESSION = "session"      # Current conversation session
    TURN = "turn"           # Single conversation turn
    PERSISTENT = "persistent"  # Across all sessions
    TEMPORARY = "temporary"    # Short-lived, expires automatically


@dataclass
class ContextEntry:
    """Represents a single context entry."""
    key: str
    value: Any
    scope: ContextScope
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if this context entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            scope=ContextScope(data["scope"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            metadata=data.get("metadata", {})
        )


class ContextManager:
    """
    Manages conversation context across different scopes and time periods.
    """
    
    def __init__(self):
        self._contexts: Dict[ContextScope, Dict[str, ContextEntry]] = {
            scope: {} for scope in ContextScope
        }
        self._conversation_history: List[Dict[str, Any]] = []
        self._session_id: Optional[str] = None
        self._turn_count: int = 0
        self._session_start: Optional[datetime] = None
        
    def start_session(self, session_id: str) -> None:
        """Start a new conversation session."""
        self._session_id = session_id
        self._session_start = datetime.now()
        self._turn_count = 0
        
        # Clear session and turn contexts
        self._contexts[ContextScope.SESSION].clear()
        self._contexts[ContextScope.TURN].clear()
        
    def end_session(self) -> None:
        """End the current conversation session."""
        # Archive session data if needed
        if self._session_id:
            session_data = {
                "session_id": self._session_id,
                "start_time": self._session_start.isoformat() if self._session_start else None,
                "end_time": datetime.now().isoformat(),
                "turn_count": self._turn_count,
                "session_context": {
                    key: entry.to_dict() 
                    for key, entry in self._contexts[ContextScope.SESSION].items()
                }
            }
            # Could save this to persistent storage if needed
            
        self._session_id = None
        self._session_start = None
        self._turn_count = 0
        
        # Clear session contexts
        self._contexts[ContextScope.SESSION].clear()
        
    def start_turn(self) -> None:
        """Start a new conversation turn."""
        self._turn_count += 1
        
        # Clear turn-scoped context
        self._contexts[ContextScope.TURN].clear()
        
        # Clean up expired entries
        self._cleanup_expired_entries()
        
    def set_context(
        self, 
        key: str, 
        value: Any, 
        scope: ContextScope = ContextScope.SESSION,
        expires_in: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Set a context value.
        
        Args:
            key: Context key
            value: Context value
            scope: Context scope
            expires_in: Optional expiration time
            metadata: Additional metadata
        """
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + expires_in
            
        entry = ContextEntry(
            key=key,
            value=value,
            scope=scope,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self._contexts[scope][key] = entry
        
    def get_context(
        self, 
        key: str, 
        scope: Optional[ContextScope] = None,
        default: Any = None
    ) -> Any:
        """
        Get a context value.
        
        Args:
            key: Context key
            scope: Optional specific scope to search
            default: Default value if not found
            
        Returns:
            Context value or default
        """
        if scope:
            # Search specific scope
            entry = self._contexts[scope].get(key)
            if entry and not entry.is_expired():
                return entry.value
        else:
            # Search all scopes in priority order
            search_order = [ContextScope.TURN, ContextScope.SESSION, 
                          ContextScope.TEMPORARY, ContextScope.PERSISTENT]
            for search_scope in search_order:
                entry = self._contexts[search_scope].get(key)
                if entry and not entry.is_expired():
                    return entry.value
                    
        return default
        
    def has_context(self, key: str, scope: Optional[ContextScope] = None) -> bool:
        """Check if a context key exists and is not expired."""
        if scope:
            entry = self._contexts[scope].get(key)
            return entry is not None and not entry.is_expired()
        else:
            search_order = [ContextScope.TURN, ContextScope.SESSION, 
                          ContextScope.TEMPORARY, ContextScope.PERSISTENT]
            for search_scope in search_order:
                entry = self._contexts[search_scope].get(key)
                if entry and not entry.is_expired():
                    return True
            return False
            
    def remove_context(self, key: str, scope: Optional[ContextScope] = None) -> bool:
        """
        Remove a context entry.
        
        Args:
            key: Context key
            scope: Optional specific scope
            
        Returns:
            True if entry was removed
        """
        removed = False
        
        if scope:
            if key in self._contexts[scope]:
                del self._contexts[scope][key]
                removed = True
        else:
            for context_scope in self._contexts:
                if key in self._contexts[context_scope]:
                    del self._contexts[context_scope][key]
                    removed = True
                    
        return removed
        
    def get_all_context(
        self, 
        scope: Optional[ContextScope] = None,
        include_expired: bool = False
    ) -> Dict[str, Any]:
        """
        Get all context values.
        
        Args:
            scope: Optional specific scope
            include_expired: Whether to include expired entries
            
        Returns:
            Dictionary of all context values
        """
        result = {}
        
        if scope:
            scopes_to_search = [scope]
        else:
            scopes_to_search = [ContextScope.PERSISTENT, ContextScope.SESSION, 
                              ContextScope.TEMPORARY, ContextScope.TURN]
            
        for search_scope in scopes_to_search:
            for key, entry in self._contexts[search_scope].items():
                if include_expired or not entry.is_expired():
                    if key not in result:  # First found takes precedence
                        result[key] = entry.value
                        
        return result
        
    def add_to_history(
        self, 
        user_input: str, 
        agent_response: str, 
        context_snapshot: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an interaction to the conversation history.
        
        Args:
            user_input: What the user said
            agent_response: How the agent responded
            context_snapshot: Optional snapshot of context at this point
        """
        history_entry = {
            "turn": self._turn_count,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_response": agent_response,
            "context_snapshot": context_snapshot or {}
        }
        
        self._conversation_history.append(history_entry)
        
        # Keep history manageable
        if len(self._conversation_history) > 50:
            self._conversation_history = self._conversation_history[-25:]
            
    def get_history(
        self, 
        limit: Optional[int] = None,
        since_turn: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            limit: Maximum number of entries to return
            since_turn: Only return entries after this turn number
            
        Returns:
            List of history entries
        """
        history = self._conversation_history.copy()
        
        if since_turn is not None:
            history = [entry for entry in history if entry["turn"] > since_turn]
            
        if limit:
            history = history[-limit:]
            
        return history
        
    def get_recent_messages(self, count: int = 5) -> List[str]:
        """Get recent user messages."""
        recent_history = self.get_history(limit=count)
        return [entry["user_input"] for entry in recent_history]
        
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context state."""
        summary = {
            "session_id": self._session_id,
            "turn_count": self._turn_count,
            "session_duration": None,
            "context_counts": {},
            "active_contexts": self.get_all_context(),
            "history_length": len(self._conversation_history)
        }
        
        if self._session_start:
            duration = datetime.now() - self._session_start
            summary["session_duration"] = str(duration)
            
        for scope in ContextScope:
            active_count = sum(
                1 for entry in self._contexts[scope].values() 
                if not entry.is_expired()
            )
            total_count = len(self._contexts[scope])
            summary["context_counts"][scope.value] = {
                "active": active_count,
                "total": total_count
            }
            
        return summary
        
    def analyze_conversation_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in the conversation history."""
        if not self._conversation_history:
            return {"error": "No conversation history available"}
            
        # Basic statistics
        total_turns = len(self._conversation_history)
        avg_user_length = sum(
            len(entry["user_input"]) for entry in self._conversation_history
        ) / total_turns
        avg_response_length = sum(
            len(entry["agent_response"]) for entry in self._conversation_history
        ) / total_turns
        
        # Topic persistence (very basic)
        recent_messages = self.get_recent_messages(10)
        common_words = {}
        for message in recent_messages:
            words = message.lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    common_words[word] = common_words.get(word, 0) + 1
                    
        top_topics = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_turns": total_turns,
            "avg_user_message_length": avg_user_length,
            "avg_agent_response_length": avg_response_length,
            "session_duration": str(datetime.now() - self._session_start) if self._session_start else None,
            "top_topics": [word for word, count in top_topics],
            "conversation_pace": total_turns / max(1, (datetime.now() - self._session_start).total_seconds() / 60) if self._session_start else 0
        }
        
    def _cleanup_expired_entries(self) -> None:
        """Remove expired context entries."""
        for scope_dict in self._contexts.values():
            expired_keys = [
                key for key, entry in scope_dict.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del scope_dict[key]
                
    def clear_scope(self, scope: ContextScope) -> None:
        """Clear all context in a specific scope."""
        self._contexts[scope].clear()
        
    def export_context(self, include_history: bool = False) -> Dict[str, Any]:
        """Export context data for persistence."""
        export_data = {
            "session_id": self._session_id,
            "turn_count": self._turn_count,
            "session_start": self._session_start.isoformat() if self._session_start else None,
            "contexts": {}
        }
        
        for scope in ContextScope:
            export_data["contexts"][scope.value] = {
                key: entry.to_dict() 
                for key, entry in self._contexts[scope].items()
                if not entry.is_expired()
            }
            
        if include_history:
            export_data["conversation_history"] = self._conversation_history.copy()
            
        return export_data
        
    def import_context(self, data: Dict[str, Any]) -> None:
        """Import context data from persistent storage."""
        self._session_id = data.get("session_id")
        self._turn_count = data.get("turn_count", 0)
        
        if data.get("session_start"):
            self._session_start = datetime.fromisoformat(data["session_start"])
            
        # Import contexts
        contexts_data = data.get("contexts", {})
        for scope_name, scope_data in contexts_data.items():
            try:
                scope = ContextScope(scope_name)
                for key, entry_data in scope_data.items():
                    entry = ContextEntry.from_dict(entry_data)
                    if not entry.is_expired():
                        self._contexts[scope][key] = entry
            except ValueError:
                # Unknown scope, skip
                continue
                
        # Import history if present
        if "conversation_history" in data:
            self._conversation_history = data["conversation_history"].copy()