"""
Centralized Logging Module
===========================

Comprehensive logging system with custom SUCCESS level, dual output (file + console),
and intelligent filtering. Features timestamped files and automatic log directory creation.

New in v0.0.12:
- Enhanced verbose logging with detailed formatter
- Better error context and stack traces
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

_logger: Optional[logging.Logger] = None
_log_file_path: Optional[str] = None

class CustomFormatter(logging.Formatter):
    """Custom log formatter that properly handles the SUCCESS log level."""
    def format(self, record):
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        return super().format(record)

def setup_logger(name: str = "reportalin", log_level: int = logging.INFO) -> logging.Logger:
    """Set up central logger with file and console handlers."""
    global _logger, _log_file_path
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger(name)
    _logger.setLevel(log_level)
    _logger.handlers.clear()
    
    logs_dir = Path(__file__).parents[2] / ".logs"
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{name}_{timestamp}.log"
    _log_file_path = str(log_file)
    
    # Use detailed format for verbose (DEBUG) logging
    if log_level == logging.DEBUG:
        file_formatter = CustomFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
    else:
        file_formatter = CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Console handler: Show only SUCCESS, ERROR, and CRITICAL (suppress DEBUG, INFO, WARNING)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(CustomFormatter('%(levelname)s: %(message)s'))
    
    # Add custom filter to allow SUCCESS messages on console
    class SuccessOrErrorFilter(logging.Filter):
        """Allow SUCCESS (25), ERROR (40), and CRITICAL (50) but suppress WARNING (30)."""
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == SUCCESS or record.levelno >= logging.ERROR
    
    console_handler.addFilter(SuccessOrErrorFilter())
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    _logger.info(f"Logging initialized. Log file: {log_file}")
    
    return _logger

def get_logger() -> logging.Logger:
    """Get the configured logger instance or set it up if not already done."""
    return _logger if _logger else setup_logger()

def get_log_file_path() -> Optional[str]:
    """Get the path to the current log file."""
    return _log_file_path

def _append_log_path(msg: str, include_log_path: bool) -> str:
    """Helper function to append log file path to error/warning messages."""
    if include_log_path and get_log_file_path():
        return f"{msg}\nFor more details, check the log file at: {get_log_file_path()}"
    return msg

def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a DEBUG level message."""
    get_logger().debug(msg, *args, **kwargs)

def info(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log an INFO level message."""
    get_logger().info(msg, *args, **kwargs)

def warning(msg: str, *args: Any, include_log_path: bool = False, **kwargs: Any) -> None:
    """Log a WARNING level message."""
    get_logger().warning(_append_log_path(msg, include_log_path), *args, **kwargs)

def error(msg: str, *args: Any, include_log_path: bool = True, **kwargs: Any) -> None:
    """Log an ERROR level message with optional log file path."""
    get_logger().error(_append_log_path(msg, include_log_path), *args, **kwargs)

def critical(msg: str, *args: Any, include_log_path: bool = True, **kwargs: Any) -> None:
    """Log a CRITICAL level message with optional log file path."""
    get_logger().critical(_append_log_path(msg, include_log_path), *args, **kwargs)

def success(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a SUCCESS level message (custom level 25)."""
    get_logger().log(SUCCESS, msg, *args, **kwargs)

# Add success method to Logger class properly
def _success_method(self: logging.Logger, msg: str, *args: Any, **kwargs: Any) -> None:
    """Custom success logging method for Logger instances."""
    if self.isEnabledFor(SUCCESS):
        self.log(SUCCESS, msg, *args, **kwargs)

logging.Logger.success = _success_method  # type: ignore[attr-defined]

