"""Logging setup for SWARM-LITE-."""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_config


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log messages."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add context."""
        # Extract any kwargs that aren't standard logging params
        standard_params = {'exc_info', 'stack_info', 'stacklevel', 'extra'}
        extra_fields = {}
        
        # Move non-standard kwargs to extra_fields
        keys_to_remove = []
        for key, value in list(kwargs.items()):
            if key not in standard_params:
                extra_fields[key] = value
                keys_to_remove.append(key)
        
        # Remove non-standard kwargs from kwargs
        for key in keys_to_remove:
            kwargs.pop(key)
        
        # Initialize extra dict if not present
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        if "extra_fields" not in kwargs["extra"]:
            kwargs["extra"]["extra_fields"] = {}

        # Merge context and extra fields
        if self.extra:
            kwargs["extra"]["extra_fields"].update(self.extra)
        kwargs["extra"]["extra_fields"].update(extra_fields)

        return msg, kwargs


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    log_rotation_size_mb: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ContextAdapter:
    """Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
        log_file: Path to log file (optional)
        log_rotation_size_mb: Log rotation size in MB
        context: Additional context to add to all log messages

    Returns:
        Logger adapter with context
    """
    config = get_config()

    # Use config defaults if not specified
    log_level = log_level or config.log_level
    log_format = log_format or config.log_format
    log_file = log_file or config.log_file
    log_rotation_size_mb = log_rotation_size_mb or config.log_rotation_size_mb

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_rotation_size_mb * 1024 * 1024,
            backupCount=config.log_retention_days,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Create logger with context
    logger = logging.getLogger("swarm")
    return ContextAdapter(logger, context or {})


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> ContextAdapter:
    """Get a logger with optional context.

    Args:
        name: Logger name
        context: Additional context to add to all log messages

    Returns:
        Logger adapter with context
    """
    logger = logging.getLogger(f"swarm.{name}")
    return ContextAdapter(logger, context or {})


def add_context(logger: ContextAdapter, **kwargs: Any) -> ContextAdapter:
    """Add context to existing logger.

    Args:
        logger: Logger adapter
        **kwargs: Context key-value pairs

    Returns:
        New logger adapter with updated context
    """
    new_context = dict(logger.extra)
    new_context.update(kwargs)
    return ContextAdapter(logger.logger, new_context)


def log_with_context(
    logger: ContextAdapter,
    level: str,
    message: str,
    **kwargs: Any,
) -> None:
    """Log message with additional context.

    Args:
        logger: Logger adapter
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context key-value pairs
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra={"extra_fields": kwargs})


# Module-level logger
_module_logger: Optional[ContextAdapter] = None


def get_module_logger() -> ContextAdapter:
    """Get module-level logger."""
    global _module_logger
    if _module_logger is None:
        _module_logger = get_logger("main")
    return _module_logger
