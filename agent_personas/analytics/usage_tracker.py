"""
Usage tracking system for persona analytics.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of usage events."""
    PERSONA_CREATED = "persona_created"
    PERSONA_ACCESSED = "persona_accessed"
    PERSONA_MODIFIED = "persona_modified"
    TRAIT_CHANGED = "trait_changed"
    CONVERSATION_STARTED = "conversation_started"
    EVALUATION_PERFORMED = "evaluation_performed"
    BLENDING_PERFORMED = "blending_performed"
    LANGUAGE_SWITCHED = "language_switched"
    VERSION_CREATED = "version_created"
    TEMPLATE_USED = "template_used"
    ARCHETYPE_APPLIED = "archetype_applied"


@dataclass
class UsageEvent:
    """Represents a usage event for analytics."""
    event_type: EventType
    persona_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "persona_id": self.persona_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message
        }


class UsageTracker:
    """
    Tracks persona usage patterns and generates analytics.
    """
    
    def __init__(self, max_events: int = 10000):
        self.events: List[UsageEvent] = []
        self.max_events = max_events
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Aggregated statistics
        self._stats_cache: Dict[str, Any] = {}
        self._last_stats_update = datetime.now()
        self._stats_cache_ttl = timedelta(minutes=5)
    
    def track_event(
        self,
        event_type: EventType,
        persona_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Track a usage event."""
        event = UsageEvent(
            event_type=event_type,
            persona_id=persona_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        self.events.append(event)
        
        # Maintain max events limit
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Update session cache
        if session_id:
            self._update_session_cache(session_id, event)
        
        # Invalidate stats cache
        self._stats_cache.clear()
        
        self.logger.debug(f"Tracked event: {event_type.value} for persona {persona_id}")
    
    def _update_session_cache(self, session_id: str, event: UsageEvent) -> None:
        """Update session-specific cache."""
        if session_id not in self.session_cache:
            self.session_cache[session_id] = {
                "start_time": event.timestamp,
                "last_activity": event.timestamp,
                "event_count": 0,
                "personas_used": set(),
                "event_types": set()
            }
        
        session = self.session_cache[session_id]
        session["last_activity"] = event.timestamp
        session["event_count"] += 1
        session["personas_used"].add(event.persona_id)
        session["event_types"].add(event.event_type.value)
    
    def get_usage_statistics(self, 
                           time_window: Optional[timedelta] = None,
                           persona_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage statistics."""
        # Check cache
        cache_key = f"{time_window}_{persona_id}"
        if (cache_key in self._stats_cache and 
            datetime.now() - self._last_stats_update < self._stats_cache_ttl):
            return self._stats_cache[cache_key]
        
        # Filter events
        events = self.events
        
        if time_window:
            cutoff_time = datetime.now() - time_window
            events = [e for e in events if e.timestamp >= cutoff_time]
        
        if persona_id:
            events = [e for e in events if e.persona_id == persona_id]
        
        if not events:
            return {"total_events": 0}
        
        # Calculate statistics
        stats = {
            "total_events": len(events),
            "time_range": {
                "start": min(e.timestamp for e in events).isoformat(),
                "end": max(e.timestamp for e in events).isoformat()
            },
            "event_types": dict(Counter(e.event_type.value for e in events)),
            "unique_personas": len(set(e.persona_id for e in events)),
            "unique_users": len(set(e.user_id for e in events if e.user_id)),
            "unique_sessions": len(set(e.session_id for e in events if e.session_id)),
            "success_rate": sum(1 for e in events if e.success) / len(events),
            "average_duration_ms": None,
            "most_active_personas": self._get_most_active_personas(events),
            "hourly_distribution": self._get_hourly_distribution(events),
            "error_analysis": self._get_error_analysis(events)
        }
        
        # Calculate average duration for events that have it
        durations = [e.duration_ms for e in events if e.duration_ms is not None]
        if durations:
            stats["average_duration_ms"] = sum(durations) / len(durations)
        
        # Cache results
        self._stats_cache[cache_key] = stats
        self._last_stats_update = datetime.now()
        
        return stats
    
    def _get_most_active_personas(self, events: List[UsageEvent], limit: int = 10) -> List[Dict[str, Any]]:
        """Get most actively used personas."""
        persona_counts = Counter(e.persona_id for e in events)
        
        return [
            {"persona_id": persona_id, "event_count": count}
            for persona_id, count in persona_counts.most_common(limit)
        ]
    
    def _get_hourly_distribution(self, events: List[UsageEvent]) -> Dict[int, int]:
        """Get hourly distribution of events."""
        hourly_counts = defaultdict(int)
        
        for event in events:
            hour = event.timestamp.hour
            hourly_counts[hour] += 1
        
        # Fill in missing hours with 0
        return {hour: hourly_counts.get(hour, 0) for hour in range(24)}
    
    def _get_error_analysis(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """Analyze errors in events."""
        error_events = [e for e in events if not e.success]
        
        if not error_events:
            return {"total_errors": 0, "error_rate": 0.0}
        
        error_types = Counter(e.event_type.value for e in error_events)
        error_messages = Counter(e.error_message for e in error_events if e.error_message)
        
        return {
            "total_errors": len(error_events),
            "error_rate": len(error_events) / len(events),
            "error_types": dict(error_types),
            "common_error_messages": dict(error_messages.most_common(5))
        }
    
    def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific session."""
        if session_id not in self.session_cache:
            return None
        
        session = self.session_cache[session_id].copy()
        
        # Convert sets to lists for JSON serialization
        session["personas_used"] = list(session["personas_used"])
        session["event_types"] = list(session["event_types"])
        
        # Calculate session duration
        if "start_time" in session and "last_activity" in session:
            duration = session["last_activity"] - session["start_time"]
            session["duration_minutes"] = duration.total_seconds() / 60
        
        # Get session events
        session_events = [e for e in self.events if e.session_id == session_id]
        session["events"] = [e.to_dict() for e in session_events]
        
        return session
    
    def get_persona_usage_trends(self, 
                                persona_id: str,
                                days: int = 30) -> Dict[str, Any]:
        """Get usage trends for a specific persona."""
        cutoff_time = datetime.now() - timedelta(days=days)
        persona_events = [
            e for e in self.events 
            if e.persona_id == persona_id and e.timestamp >= cutoff_time
        ]
        
        if not persona_events:
            return {"persona_id": persona_id, "events": 0, "trend": "no_data"}
        
        # Group events by day
        daily_counts = defaultdict(int)
        for event in persona_events:
            day = event.timestamp.date()
            daily_counts[day] += 1
        
        # Calculate trend
        dates = sorted(daily_counts.keys())
        if len(dates) > 1:
            early_avg = sum(daily_counts[d] for d in dates[:len(dates)//2]) / (len(dates)//2)
            late_avg = sum(daily_counts[d] for d in dates[len(dates)//2:]) / (len(dates) - len(dates)//2)
            
            if late_avg > early_avg * 1.1:
                trend = "increasing"
            elif late_avg < early_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "persona_id": persona_id,
            "total_events": len(persona_events),
            "unique_sessions": len(set(e.session_id for e in persona_events if e.session_id)),
            "date_range": {
                "start": min(e.timestamp for e in persona_events).isoformat(),
                "end": max(e.timestamp for e in persona_events).isoformat()
            },
            "daily_counts": {str(date): count for date, count in daily_counts.items()},
            "trend": trend,
            "average_daily_usage": sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
        }
    
    def export_events(self, 
                     output_format: str = "json",
                     time_window: Optional[timedelta] = None,
                     persona_filter: Optional[str] = None) -> str:
        """Export events in specified format."""
        # Filter events
        events = self.events
        
        if time_window:
            cutoff_time = datetime.now() - time_window
            events = [e for e in events if e.timestamp >= cutoff_time]
        
        if persona_filter:
            events = [e for e in events if e.persona_id == persona_filter]
        
        if output_format.lower() == "json":
            return json.dumps([e.to_dict() for e in events], indent=2)
        elif output_format.lower() == "csv":
            return self._export_to_csv(events)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _export_to_csv(self, events: List[UsageEvent]) -> str:
        """Export events to CSV format."""
        if not events:
            return "No events to export"
        
        # CSV headers
        headers = [
            "event_type", "persona_id", "timestamp", "user_id", "session_id",
            "duration_ms", "success", "error_message"
        ]
        
        lines = [",".join(headers)]
        
        for event in events:
            row = [
                event.event_type.value,
                event.persona_id,
                event.timestamp.isoformat(),
                event.user_id or "",
                event.session_id or "",
                str(event.duration_ms) if event.duration_ms else "",
                str(event.success),
                event.error_message or ""
            ]
            lines.append(",".join(f'"{item}"' for item in row))
        
        return "\n".join(lines)
    
    def clear_old_events(self, older_than: timedelta) -> int:
        """Clear events older than specified time."""
        cutoff_time = datetime.now() - older_than
        initial_count = len(self.events)
        
        self.events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        # Clear old session cache
        old_sessions = [
            session_id for session_id, data in self.session_cache.items()
            if data["last_activity"] < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.session_cache[session_id]
        
        cleared_count = initial_count - len(self.events)
        
        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} old events")
        
        return cleared_count