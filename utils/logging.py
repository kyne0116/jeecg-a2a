"""
Logging configuration for JEECG A2A Platform.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from config.settings import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Setup logging configuration for the platform.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
    """
    
    # Use settings if not provided
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    if log_file is None:
        log_file = "logs/jeecg-a2a.log"
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_third_party_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, Console: {enable_console}, File: {enable_file}")


def configure_third_party_loggers():
    """Configure logging levels for third-party libraries."""
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    # Set specific levels based on debug mode
    if settings.DEBUG:
        logging.getLogger("jeecg_a2a").setLevel(logging.DEBUG)
    else:
        logging.getLogger("jeecg_a2a").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"jeecg_a2a.{name}")


class StructuredLogger:
    """
    Structured logger for better log analysis.
    """
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = get_logger(name)
    
    def log_event(self, event_type: str, message: str, **kwargs):
        """
        Log a structured event.
        
        Args:
            event_type: Type of event (e.g., 'agent_registered', 'task_completed')
            message: Human-readable message
            **kwargs: Additional structured data
        """
        structured_data = {
            "event_type": event_type,
            "message": message,
            **kwargs
        }
        
        # Format as key=value pairs for easy parsing
        structured_msg = " ".join([f"{k}={v}" for k, v in structured_data.items()])
        self.logger.info(f"[STRUCTURED] {structured_msg}")
    
    def log_agent_event(self, agent_id: str, event: str, **kwargs):
        """Log agent-related event."""
        self.log_event(
            event_type="agent_event",
            message=f"Agent {agent_id}: {event}",
            agent_id=agent_id,
            event=event,
            **kwargs
        )
    
    def log_task_event(self, task_id: str, event: str, **kwargs):
        """Log task-related event."""
        self.log_event(
            event_type="task_event",
            message=f"Task {task_id}: {event}",
            task_id=task_id,
            event=event,
            **kwargs
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        self.log_event(
            event_type="performance",
            message=f"Operation {operation} took {duration:.3f}s",
            operation=operation,
            duration=duration,
            **kwargs
        )
    
    def log_error(self, error_type: str, message: str, **kwargs):
        """Log error with structured data."""
        self.log_event(
            event_type="error",
            message=f"Error: {message}",
            error_type=error_type,
            **kwargs
        )
        self.logger.error(message)


# Global structured logger instances
platform_logger = StructuredLogger("platform")
agent_logger = StructuredLogger("agent")
task_logger = StructuredLogger("task")
api_logger = StructuredLogger("api")
