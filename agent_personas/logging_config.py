"""
Comprehensive logging configuration for agent_personas package.
"""

import logging
import logging.handlers
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import json


class PersonaFormatter(logging.Formatter):
    """Custom formatter for persona-related logs."""
    
    def __init__(self, include_context: bool = True):
        self.include_context = include_context
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        # Base format
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        name = record.name
        message = record.getMessage()
        
        # Add context information if available
        context_info = ""
        if self.include_context and hasattr(record, 'persona_context'):
            ctx = record.persona_context
            context_parts = []
            
            if 'persona_id' in ctx:
                context_parts.append(f"persona={ctx['persona_id']}")
            if 'operation' in ctx:
                context_parts.append(f"op={ctx['operation']}")
            if 'user_id' in ctx:
                context_parts.append(f"user={ctx['user_id']}")
            
            if context_parts:
                context_info = f" [{', '.join(context_parts)}]"
        
        # Format exception info if present
        exc_text = ""
        if record.exc_info:
            exc_text = f"\n{self.formatException(record.exc_info)}"
        
        return f"{timestamp} | {level:8s} | {name:20s}{context_info} | {message}{exc_text}"


class ContextLogger:
    """Logger wrapper that adds persona context to log records."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set context information for logging."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context information."""
        self.context.clear()
    
    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add context to extra parameters."""
        result = {'persona_context': self.context.copy()}
        if extra:
            result.update(extra)
        return result
    
    def debug(self, msg, *args, **kwargs):
        kwargs['extra'] = self._add_context(kwargs.get('extra'))
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        kwargs['extra'] = self._add_context(kwargs.get('extra'))
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        kwargs['extra'] = self._add_context(kwargs.get('extra'))
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        kwargs['extra'] = self._add_context(kwargs.get('extra'))
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        kwargs['extra'] = self._add_context(kwargs.get('extra'))
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        kwargs['extra'] = self._add_context(kwargs.get('extra'))
        self.logger.exception(msg, *args, **kwargs)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context if available
        if hasattr(record, 'persona_context'):
            log_data['context'] = record.persona_context
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'exc_info', 'exc_text',
                          'stack_info', 'persona_context', 'msg', 'args']:
                log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = False,
    console_output: bool = True,
    include_context: bool = True
) -> ContextLogger:
    """
    Setup comprehensive logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        json_format: Use JSON formatting for structured logs
        console_output: Enable console output
        include_context: Include persona context in logs
    
    Returns:
        ContextLogger instance
    """
    # Create root logger for agent_personas
    logger = logging.getLogger('agent_personas')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Choose formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = PersonaFormatter(include_context=include_context)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent duplicate logs from parent loggers
    logger.propagate = False
    
    return ContextLogger(logger)


def get_logger(name: str) -> ContextLogger:
    """Get a context logger for a specific module."""
    logger = logging.getLogger(f'agent_personas.{name}')
    return ContextLogger(logger)


def configure_third_party_logging(level: str = "WARNING"):
    """Configure logging for third-party libraries."""
    # Reduce noise from common third-party libraries
    noisy_loggers = [
        'urllib3',
        'requests',
        'httpx',
        'httpcore',
        'asyncio',
        'concurrent.futures',
        'multiprocessing'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(getattr(logging, level.upper()))


# Performance logging utilities
def log_performance(operation: str, duration: float, context: Optional[Dict[str, Any]] = None):
    """Log performance information."""
    perf_logger = get_logger('performance')
    
    if context:
        perf_logger.set_context(**context)
    
    perf_logger.set_context(operation=operation, duration_ms=duration * 1000)
    
    if duration > 1.0:  # Log slow operations
        perf_logger.warning(f"Slow operation: {operation} took {duration:.3f}s")
    else:
        perf_logger.info(f"Operation {operation} completed in {duration:.3f}s")


def log_memory_usage(operation: str, memory_mb: float, context: Optional[Dict[str, Any]] = None):
    """Log memory usage information."""
    memory_logger = get_logger('memory')
    
    if context:
        memory_logger.set_context(**context)
    
    memory_logger.set_context(operation=operation, memory_mb=memory_mb)
    
    if memory_mb > 100:  # Log high memory usage
        memory_logger.warning(f"High memory usage: {operation} used {memory_mb:.1f}MB")
    else:
        memory_logger.debug(f"Memory usage for {operation}: {memory_mb:.1f}MB")


# Default logger instance
default_logger = get_logger('main')


# Convenience functions
def debug(msg, *args, **kwargs):
    default_logger.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    default_logger.info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    default_logger.warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    default_logger.error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    default_logger.critical(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    default_logger.exception(msg, *args, **kwargs)