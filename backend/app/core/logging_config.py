"""
Structured logging configuration with file rotation and JSON formatting.

This module configures application-wide logging with:
- File rotation (10MB per file, 10 backup files)
- Console and file handlers
- Structured JSON logging for file output
- Human-readable console output
- Log levels per module
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs log records as JSON with the following fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level name (INFO, ERROR, etc.)
    - logger: Logger name (module path)
    - message: Log message
    - extra: Any extra fields passed to the log call
    - exception: Exception info if present
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # Add custom fields from extra parameter
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, default=str)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 10
):
    """
    Configure application logging with file rotation and structured output.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files (relative to project root)
        enable_file_logging: Enable file logging with rotation
        enable_console_logging: Enable console logging
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep

    Creates three log files:
        - app.log: All application logs (JSON format)
        - error.log: Only ERROR and CRITICAL logs (JSON format)
        - access.log: HTTP access logs (JSON format)
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (human-readable format)
    if enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handlers (JSON format)
    if enable_file_logging:
        json_formatter = JSONFormatter()

        # Main application log (all levels)
        app_log_path = log_path / "app.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        app_handler.setLevel(numeric_level)
        app_handler.setFormatter(json_formatter)
        root_logger.addHandler(app_handler)

        # Error log (ERROR and CRITICAL only)
        error_log_path = log_path / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        root_logger.addHandler(error_handler)

    # Configure module-specific log levels
    _configure_module_loggers()

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={log_level}, "
        f"file_logging={enable_file_logging}, "
        f"console_logging={enable_console_logging}, "
        f"log_dir={log_dir}"
    )


def _configure_module_loggers():
    """
    Configure log levels for specific modules.

    Reduces verbosity for third-party libraries and noisy modules.
    """
    # Reduce verbosity of third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)

    # Application-specific modules (keep at INFO or DEBUG)
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("app.services").setLevel(logging.INFO)
    logging.getLogger("app.api").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Operation completed", extra_data={"records": 100})
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter for adding context to all log messages.

    Example:
        adapter = LoggerAdapter(logger, {"request_id": "abc123"})
        adapter.info("Processing request")  # Will include request_id in all logs
    """

    def process(self, msg, kwargs):
        """Add extra context to log records."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["extra_data"] = self.extra
        return msg, kwargs
