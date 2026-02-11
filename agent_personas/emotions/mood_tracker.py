"""
Mood tracker for monitoring long-term emotional patterns and trends.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
import json
import statistics
from collections import defaultdict

from .emotion_model import EmotionalState, BasicEmotion


@dataclass
class MoodEntry:
    """Represents a mood entry at a specific point in time."""
    timestamp: datetime
    emotional_state: EmotionalState
    context: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mood entry to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "emotional_state": self.emotional_state.to_dict(),
            "context": self.context,
            "notes": self.notes
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoodEntry":
        """Create mood entry from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            emotional_state=EmotionalState.from_dict(data["emotional_state"]),
            context=data.get("context", {}),
            notes=data.get("notes", "")
        )


@dataclass
class MoodSummary:
    """Summary of mood data for a time period."""
    period_start: datetime
    period_end: datetime
    average_valence: float
    average_arousal: float
    average_intensity: float
    dominant_emotions: List[Tuple[str, float]]
    mood_volatility: float
    total_entries: int
    most_common_context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mood summary to dictionary."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "average_valence": self.average_valence,
            "average_arousal": self.average_arousal,
            "average_intensity": self.average_intensity,
            "dominant_emotions": self.dominant_emotions,
            "mood_volatility": self.mood_volatility,
            "total_entries": self.total_entries,
            "most_common_context": self.most_common_context
        }


class MoodTracker:
    """
    Tracks and analyzes long-term emotional patterns and moods.
    """
    
    def __init__(self, max_entries: int = 1000):
        self._entries: List[MoodEntry] = []
        self.max_entries = max_entries
        self._daily_summaries: Dict[date, MoodSummary] = {}
        
    def record_mood(
        self, 
        emotional_state: EmotionalState,
        context: Optional[Dict[str, Any]] = None,
        notes: str = ""
    ) -> None:
        """
        Record a new mood entry.
        
        Args:
            emotional_state: Current emotional state
            context: Optional context information
            notes: Optional notes about the mood
        """
        entry = MoodEntry(
            timestamp=datetime.now(),
            emotional_state=emotional_state,
            context=context or {},
            notes=notes
        )
        
        self._entries.append(entry)
        
        # Maintain size limit
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries//2:]
            
        # Update daily summary
        self._update_daily_summary(entry.timestamp.date())
        
    def get_mood_history(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MoodEntry]:
        """
        Get mood history for a specific time period.
        
        Args:
            start_date: Start of time period (None for beginning)
            end_date: End of time period (None for now)
            limit: Maximum number of entries
            
        Returns:
            List of mood entries
        """
        filtered_entries = self._entries.copy()
        
        if start_date:
            filtered_entries = [
                entry for entry in filtered_entries
                if entry.timestamp >= start_date
            ]
            
        if end_date:
            filtered_entries = [
                entry for entry in filtered_entries
                if entry.timestamp <= end_date
            ]
            
        if limit:
            filtered_entries = filtered_entries[-limit:]
            
        return filtered_entries
        
    def get_daily_summary(self, target_date: date) -> Optional[MoodSummary]:
        """Get mood summary for a specific date."""
        return self._daily_summaries.get(target_date)
        
    def get_weekly_summary(self, week_start: date) -> MoodSummary:
        """Get mood summary for a week starting from given date."""
        week_end = week_start + timedelta(days=6)
        start_datetime = datetime.combine(week_start, datetime.min.time())
        end_datetime = datetime.combine(week_end, datetime.max.time())
        
        entries = self.get_mood_history(start_datetime, end_datetime)
        return self._calculate_period_summary(entries, start_datetime, end_datetime)
        
    def get_monthly_summary(self, year: int, month: int) -> MoodSummary:
        """Get mood summary for a specific month."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
            
        entries = self.get_mood_history(start_date, end_date)
        return self._calculate_period_summary(entries, start_date, end_date)
        
    def analyze_mood_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze mood patterns over the specified period.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Analysis results
        """
        start_date = datetime.now() - timedelta(days=days_back)
        entries = self.get_mood_history(start_date)
        
        if not entries:
            return {"message": "No mood data available for analysis"}
            
        # Extract emotional dimensions
        valence_values = [entry.emotional_state.valence for entry in entries]
        arousal_values = [entry.emotional_state.arousal for entry in entries]
        intensity_values = [entry.emotional_state.intensity for entry in entries]
        
        # Emotional distribution
        emotion_counts = defaultdict(int)
        for entry in entries:
            dominant_emotion, _ = entry.emotional_state.get_dominant_emotion()
            emotion_counts[dominant_emotion.value] += 1
            
        # Time-based patterns
        hourly_mood = defaultdict(list)
        daily_mood = defaultdict(list)
        
        for entry in entries:
            hour = entry.timestamp.hour
            day_name = entry.timestamp.strftime("%A")
            
            hourly_mood[hour].append(entry.emotional_state.valence)
            daily_mood[day_name].append(entry.emotional_state.valence)
            
        # Calculate average mood by hour and day
        avg_hourly_mood = {
            hour: statistics.mean(valences) if valences else 0
            for hour, valences in hourly_mood.items()
        }
        
        avg_daily_mood = {
            day: statistics.mean(valences) if valences else 0
            for day, valences in daily_mood.items()
        }
        
        # Volatility analysis
        volatility = self._calculate_volatility(valence_values)
        
        # Trend analysis
        trend = self._analyze_trend(valence_values)
        
        # Context analysis
        context_analysis = self._analyze_contexts(entries)
        
        return {
            "analysis_period": f"{days_back} days",
            "total_mood_entries": len(entries),
            "average_valence": statistics.mean(valence_values),
            "average_arousal": statistics.mean(arousal_values),
            "average_intensity": statistics.mean(intensity_values),
            "valence_range": (min(valence_values), max(valence_values)),
            "mood_volatility": volatility,
            "mood_trend": trend,
            "emotion_distribution": dict(emotion_counts),
            "most_common_emotion": max(emotion_counts.items(), key=lambda x: x[1]) if emotion_counts else None,
            "hourly_mood_pattern": avg_hourly_mood,
            "daily_mood_pattern": avg_daily_mood,
            "best_time_of_day": max(avg_hourly_mood.items(), key=lambda x: x[1]) if avg_hourly_mood else None,
            "best_day_of_week": max(avg_daily_mood.items(), key=lambda x: x[1]) if avg_daily_mood else None,
            "context_insights": context_analysis
        }
        
    def identify_mood_triggers(self, days_back: int = 14) -> Dict[str, Any]:
        """
        Identify patterns in mood triggers and context.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Trigger analysis results
        """
        start_date = datetime.now() - timedelta(days=days_back)
        entries = self.get_mood_history(start_date)
        
        if len(entries) < 5:
            return {"message": "Not enough mood data to identify triggers"}
            
        # Group entries by significant mood changes
        positive_triggers = []
        negative_triggers = []
        
        for i in range(1, len(entries)):
            prev_entry = entries[i-1]
            curr_entry = entries[i]
            
            valence_change = curr_entry.emotional_state.valence - prev_entry.emotional_state.valence
            
            if valence_change > 0.3:  # Significant positive change
                positive_triggers.append({
                    "timestamp": curr_entry.timestamp.isoformat(),
                    "context": curr_entry.context,
                    "notes": curr_entry.notes,
                    "valence_change": valence_change,
                    "resulting_mood": curr_entry.emotional_state.get_mood_label()
                })
                
            elif valence_change < -0.3:  # Significant negative change
                negative_triggers.append({
                    "timestamp": curr_entry.timestamp.isoformat(),
                    "context": curr_entry.context,
                    "notes": curr_entry.notes,
                    "valence_change": valence_change,
                    "resulting_mood": curr_entry.emotional_state.get_mood_label()
                })
                
        # Analyze common trigger patterns
        positive_contexts = self._extract_context_patterns([t["context"] for t in positive_triggers])
        negative_contexts = self._extract_context_patterns([t["context"] for t in negative_triggers])
        
        return {
            "analysis_period": f"{days_back} days",
            "positive_mood_triggers": positive_triggers,
            "negative_mood_triggers": negative_triggers,
            "positive_trigger_count": len(positive_triggers),
            "negative_trigger_count": len(negative_triggers),
            "common_positive_contexts": positive_contexts,
            "common_negative_contexts": negative_contexts,
            "trigger_ratio": len(positive_triggers) / max(len(negative_triggers), 1)
        }
        
    def predict_mood_trend(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """
        Predict mood trend based on historical patterns.
        
        Args:
            hours_ahead: Number of hours to predict
            
        Returns:
            Mood prediction
        """
        if len(self._entries) < 10:
            return {"message": "Not enough data for prediction"}
            
        # Get recent trend
        recent_entries = self._entries[-20:]  # Last 20 entries
        recent_valences = [entry.emotional_state.valence for entry in recent_entries]
        
        # Simple linear trend
        x_values = list(range(len(recent_valences)))
        if len(x_values) >= 2:
            # Calculate simple trend slope
            slope = (recent_valences[-1] - recent_valences[0]) / len(recent_valences)
            
            # Predict future valence
            future_valence = recent_valences[-1] + slope * (hours_ahead / 24)
            future_valence = max(-1.0, min(1.0, future_valence))  # Clamp to valid range
        else:
            slope = 0
            future_valence = recent_valences[-1] if recent_valences else 0
            
        # Predict mood category
        if future_valence > 0.5:
            predicted_mood = "positive"
        elif future_valence < -0.5:
            predicted_mood = "negative"
        else:
            predicted_mood = "neutral"
            
        # Confidence based on recent stability
        recent_volatility = self._calculate_volatility(recent_valences)
        confidence = max(0.1, 1.0 - recent_volatility)
        
        return {
            "prediction_horizon": f"{hours_ahead} hours",
            "predicted_valence": future_valence,
            "predicted_mood": predicted_mood,
            "trend_direction": "improving" if slope > 0 else "declining" if slope < 0 else "stable",
            "confidence": confidence,
            "based_on_entries": len(recent_entries)
        }
        
    def _update_daily_summary(self, target_date: date) -> None:
        """Update daily summary for the given date."""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        day_entries = [
            entry for entry in self._entries
            if start_datetime <= entry.timestamp <= end_datetime
        ]
        
        if day_entries:
            summary = self._calculate_period_summary(day_entries, start_datetime, end_datetime)
            self._daily_summaries[target_date] = summary
            
    def _calculate_period_summary(
        self, 
        entries: List[MoodEntry],
        period_start: datetime,
        period_end: datetime
    ) -> MoodSummary:
        """Calculate summary statistics for a period."""
        if not entries:
            return MoodSummary(
                period_start=period_start,
                period_end=period_end,
                average_valence=0.0,
                average_arousal=0.0,
                average_intensity=0.0,
                dominant_emotions=[],
                mood_volatility=0.0,
                total_entries=0,
                most_common_context={}
            )
            
        # Calculate averages
        valence_values = [entry.emotional_state.valence for entry in entries]
        arousal_values = [entry.emotional_state.arousal for entry in entries]
        intensity_values = [entry.emotional_state.intensity for entry in entries]
        
        avg_valence = statistics.mean(valence_values)
        avg_arousal = statistics.mean(arousal_values)
        avg_intensity = statistics.mean(intensity_values)
        
        # Calculate dominant emotions
        emotion_totals = defaultdict(float)
        for entry in entries:
            for emotion, intensity in entry.emotional_state.basic_emotions.items():
                emotion_totals[emotion.value] += intensity
                
        dominant_emotions = sorted(
            emotion_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Calculate volatility
        volatility = self._calculate_volatility(valence_values)
        
        # Find most common context
        context_analysis = self._analyze_contexts(entries)
        most_common_context = context_analysis.get("most_common", {})
        
        return MoodSummary(
            period_start=period_start,
            period_end=period_end,
            average_valence=avg_valence,
            average_arousal=avg_arousal,
            average_intensity=avg_intensity,
            dominant_emotions=dominant_emotions,
            mood_volatility=volatility,
            total_entries=len(entries),
            most_common_context=most_common_context
        )
        
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation) of values."""
        if len(values) < 2:
            return 0.0
        return statistics.stdev(values)
        
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend direction in values."""
        if len(values) < 3:
            return "insufficient_data"
            
        # Compare first and last thirds
        first_third = values[:len(values)//3]
        last_third = values[-len(values)//3:]
        
        if not first_third or not last_third:
            return "stable"
            
        first_avg = statistics.mean(first_third)
        last_avg = statistics.mean(last_third)
        
        diff = last_avg - first_avg
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
            
    def _analyze_contexts(self, entries: List[MoodEntry]) -> Dict[str, Any]:
        """Analyze context patterns in mood entries."""
        context_counts = defaultdict(int)
        context_valences = defaultdict(list)
        
        for entry in entries:
            for key, value in entry.context.items():
                context_key = f"{key}:{value}"
                context_counts[context_key] += 1
                context_valences[context_key].append(entry.emotional_state.valence)
                
        # Find most impactful contexts
        context_impacts = {}
        for context_key, valences in context_valences.items():
            if len(valences) >= 2:  # Need multiple data points
                avg_valence = statistics.mean(valences)
                context_impacts[context_key] = avg_valence
                
        most_positive_contexts = sorted(
            context_impacts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        most_negative_contexts = sorted(
            context_impacts.items(),
            key=lambda x: x[1]
        )[:3]
        
        return {
            "most_common": dict(sorted(context_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "most_positive_contexts": most_positive_contexts,
            "most_negative_contexts": most_negative_contexts
        }
        
    def _extract_context_patterns(self, contexts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract common patterns from context dictionaries."""
        pattern_counts = defaultdict(int)
        
        for context in contexts:
            for key, value in context.items():
                pattern = f"{key}:{value}"
                pattern_counts[pattern] += 1
                
        # Return only patterns that appear multiple times
        return {
            pattern: count for pattern, count in pattern_counts.items()
            if count >= 2
        }
        
    def export_data(self, filepath: str, include_daily_summaries: bool = True) -> None:
        """Export mood tracking data to JSON file."""
        data = {
            "entries": [entry.to_dict() for entry in self._entries],
            "max_entries": self.max_entries
        }
        
        if include_daily_summaries:
            data["daily_summaries"] = {
                date_str: summary.to_dict()
                for date_str, summary in self._daily_summaries.items()
            }
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
    def import_data(self, filepath: str) -> None:
        """Import mood tracking data from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Import entries
        self._entries = [
            MoodEntry.from_dict(entry_data)
            for entry_data in data.get("entries", [])
        ]
        
        # Import settings
        self.max_entries = data.get("max_entries", 1000)
        
        # Import daily summaries if present
        daily_summaries_data = data.get("daily_summaries", {})
        for date_str, summary_data in daily_summaries_data.items():
            date_obj = datetime.fromisoformat(summary_data["period_start"]).date()
            # Note: This is a simplified reconstruction of MoodSummary
            # In a production system, you'd want proper deserialization