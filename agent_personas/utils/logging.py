"""
Logging utilities for persona framework events and debugging.
"""

import logging
import json
import sys
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from ..core.persona import Persona


# Custom log levels
PERSONA_EVENT_LEVEL = 25
EMOTION_EVENT_LEVEL = 26
BEHAVIOR_EVENT_LEVEL = 27

# Add custom levels to logging module
logging.addLevelName(PERSONA_EVENT_LEVEL, "PERSONA")
logging.addLevelName(EMOTION_EVENT_LEVEL, "EMOTION")
logging.addLevelName(BEHAVIOR_EVENT_LEVEL, "BEHAVIOR")


class PersonaLogger(logging.Logger):
    """Custom logger with persona-specific logging methods."""
    
    def persona(self, message: str, *args, **kwargs):
        """Log a persona-related event."""
        if self.isEnabledFor(PERSONA_EVENT_LEVEL):
            self._log(PERSONA_EVENT_LEVEL, message, args, **kwargs)
    
    def emotion(self, message: str, *args, **kwargs):
        """Log an emotion-related event."""
        if self.isEnabledFor(EMOTION_EVENT_LEVEL):
            self._log(EMOTION_EVENT_LEVEL, message, args, **kwargs)
    
    def behavior(self, message: str, *args, **kwargs):
        """Log a behavior-related event."""
        if self.isEnabledFor(BEHAVIOR_EVENT_LEVEL):
            self._log(BEHAVIOR_EVENT_LEVEL, message, args, **kwargs)


# Set the custom logger class
logging.setLoggerClass(PersonaLogger)


class PersonaFormatter(logging.Formatter):
    """Custom formatter for persona framework logs."""
    
    def __init__(self, include_persona_context: bool = True):
        self.include_persona_context = include_persona_context
        super().__init__()
    
    def format(self, record):
        # Basic formatting
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if hasattr(record, 'persona_name'):
            log_format = f"%(asctime)s - [%(persona_name)s] - %(levelname)s - %(message)s"
        
        formatter = logging.Formatter(log_format)
        return formatter.format(record)


class PersonaJSONFormatter(logging.Formatter):
    """JSON formatter for structured persona logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add persona-specific fields if available
        if hasattr(record, 'persona_name'):
            log_entry['persona_name'] = record.persona_name
        
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        if hasattr(record, 'traits'):
            log_entry['traits'] = record.traits
        
        return json.dumps(log_entry)


def get_persona_logger(
    name: str = "agent_personas",
    level: Union[str, int] = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = False
) -> PersonaLogger:
    """
    Get a configured persona logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file to log to
        json_format: Whether to use JSON formatting
        
    Returns:
        Configured PersonaLogger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set level
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)
    
    # Create formatter
    if json_format:
        formatter = PersonaJSONFormatter()
    else:
        formatter = PersonaFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_persona_event(
    logger: PersonaLogger,
    event_type: str,
    persona: Optional[Persona] = None,
    message: str = "",
    context: Optional[Dict[str, Any]] = None,
    level: int = PERSONA_EVENT_LEVEL
):
    """
    Log a persona-related event with structured data.
    
    Args:
        logger: Logger instance
        event_type: Type of event (created, activated, switched, etc.)
        persona: Persona instance involved
        message: Human-readable message
        context: Additional context data
        level: Log level to use
    """
    extra_data = {
        'event_type': event_type,
        'context': context or {}
    }
    
    if persona:
        extra_data['persona_name'] = persona.name
        extra_data['traits'] = persona.traits
    
    if not message:
        if event_type == "created" and persona:
            message = f"Persona '{persona.name}' created"
        elif event_type == "activated" and persona:
            message = f"Persona '{persona.name}' activated"
        elif event_type == "deactivated" and persona:
            message = f"Persona '{persona.name}' deactivated"
        else:
            message = f"Persona event: {event_type}"
    
    logger.log(level, message, extra=extra_data)


def log_emotion_event(
    logger: PersonaLogger,
    emotion_type: str,
    intensity: float,
    trigger: str = "",
    persona_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log an emotion-related event.
    
    Args:
        logger: Logger instance
        emotion_type: Type of emotion
        intensity: Emotion intensity
        trigger: What triggered the emotion
        persona_name: Name of involved persona
        context: Additional context
    """
    extra_data = {
        'event_type': 'emotion_change',
        'emotion_type': emotion_type,
        'intensity': intensity,
        'trigger': trigger,
        'context': context or {}
    }
    
    if persona_name:
        extra_data['persona_name'] = persona_name
    
    message = f"Emotion {emotion_type} (intensity: {intensity:.2f})"
    if trigger:
        message += f" triggered by: {trigger}"
    
    logger.emotion(message, extra=extra_data)


def log_behavior_event(
    logger: PersonaLogger,
    behavior_type: str,
    rule_name: str = "",
    modifications: Optional[Dict[str, Any]] = None,
    persona_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log a behavior-related event.
    
    Args:
        logger: Logger instance
        behavior_type: Type of behavior event
        rule_name: Name of behavior rule involved
        modifications: Behavior modifications applied
        persona_name: Name of involved persona
        context: Additional context
    """
    extra_data = {
        'event_type': 'behavior_change',
        'behavior_type': behavior_type,
        'rule_name': rule_name,
        'modifications': modifications or {},
        'context': context or {}
    }
    
    if persona_name:
        extra_data['persona_name'] = persona_name
    
    message = f"Behavior event: {behavior_type}"
    if rule_name:
        message += f" (rule: {rule_name})"
    
    logger.behavior(message, extra=extra_data)


def setup_file_logging(
    log_dir: Union[str, Path],
    base_filename: str = "agent_personas",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = False
) -> logging.Handler:
    """
    Set up rotating file logging for personas.
    
    Args:
        log_dir: Directory to store log files
        base_filename: Base name for log files
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
        json_format: Whether to use JSON formatting
        
    Returns:
        Configured file handler
    """
    from logging.handlers import RotatingFileHandler
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{base_filename}.log"
    
    handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_file_size,
        backupCount=backup_count
    )
    
    if json_format:
        formatter = PersonaJSONFormatter()
    else:
        formatter = PersonaFormatter()
    
    handler.setFormatter(formatter)
    return handler


def create_debug_logger(log_file: Optional[str] = None) -> PersonaLogger:
    """Create a debug-level logger for development."""
    return get_persona_logger(
        name="agent_personas.debug",
        level=logging.DEBUG,
        log_file=log_file,
        json_format=False
    )


def create_production_logger(log_dir: Union[str, Path]) -> PersonaLogger:
    """Create a production-ready logger with file rotation."""
    logger = get_persona_logger(
        name="agent_personas.prod",
        level=logging.INFO,
        json_format=True
    )
    
    # Add rotating file handler
    file_handler = setup_file_logging(log_dir, json_format=True)
    logger.addHandler(file_handler)
    
    return logger


class PersonaLogContext:
    """Context manager for adding persona context to logs."""
    
    def __init__(self, logger: PersonaLogger, persona: Persona):
        self.logger = logger
        self.persona = persona
        self.old_filters = []
    
    def __enter__(self):
        # Add persona context filter
        def add_persona_context(record):
            record.persona_name = self.persona.name
            return True
        
        for handler in self.logger.handlers:
            self.old_filters.append(handler.filters.copy())
            handler.addFilter(add_persona_context)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove persona context filter
        for i, handler in enumerate(self.logger.handlers):
            handler.filters = self.old_filters[i]


def analyze_log_patterns(log_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Analyze patterns in persona logs.
    
    Args:
        log_file: Path to log file to analyze
        
    Returns:
        Analysis results
    """
    log_file = Path(log_file)
    
    if not log_file.exists():
        return {"error": f"Log file not found: {log_file}"}
    
    patterns = {
        "total_entries": 0,
        "event_types": {},
        "persona_activity": {},
        "error_count": 0,
        "warning_count": 0,
        "time_range": {},
        "most_active_persona": None,
        "common_errors": []
    }
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                patterns["total_entries"] += 1
                
                # Try to parse as JSON first
                try:
                    log_entry = json.loads(line.strip())
                    
                    # Count event types
                    if "event_type" in log_entry:
                        event_type = log_entry["event_type"]
                        patterns["event_types"][event_type] = patterns["event_types"].get(event_type, 0) + 1
                    
                    # Count persona activity
                    if "persona_name" in log_entry:
                        persona_name = log_entry["persona_name"]
                        patterns["persona_activity"][persona_name] = patterns["persona_activity"].get(persona_name, 0) + 1
                    
                    # Count errors and warnings
                    if log_entry.get("level") == "ERROR":
                        patterns["error_count"] += 1
                        patterns["common_errors"].append(log_entry.get("message", "Unknown error"))
                    elif log_entry.get("level") == "WARNING":
                        patterns["warning_count"] += 1
                    
                    # Track time range
                    if "timestamp" in log_entry:
                        timestamp = log_entry["timestamp"]
                        if not patterns["time_range"]:
                            patterns["time_range"] = {"earliest": timestamp, "latest": timestamp}
                        else:
                            if timestamp < patterns["time_range"]["earliest"]:
                                patterns["time_range"]["earliest"] = timestamp
                            if timestamp > patterns["time_range"]["latest"]:
                                patterns["time_range"]["latest"] = timestamp
                
                except json.JSONDecodeError:
                    # Handle non-JSON log entries
                    if "ERROR" in line:
                        patterns["error_count"] += 1
                    elif "WARNING" in line:
                        patterns["warning_count"] += 1
    
        # Find most active persona
        if patterns["persona_activity"]:
            patterns["most_active_persona"] = max(
                patterns["persona_activity"].items(),
                key=lambda x: x[1]
            )
        
        # Limit common errors list
        patterns["common_errors"] = patterns["common_errors"][:10]
        
    except Exception as e:
        patterns["error"] = f"Failed to analyze log file: {e}"
    
    return patterns


# Global logger instance
default_logger = get_persona_logger()