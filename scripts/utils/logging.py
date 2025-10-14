"""
Centralized Logging Module
===========================

Comprehensive logging system with custom SUCCESS level, dual output (file + console),
colored output, and intelligent filtering. Features timestamped files and automatic 
log directory creation.
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

_logger: Optional[logging.Logger] = None
_log_file_path: Optional[str] = None

# ANSI Color Codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Check if output is a terminal
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    
    # Windows systems
    if sys.platform == 'win32':
        # Enable ANSI escape codes on Windows 10+
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    
    # Unix-like systems
    return True

class ColoredFormatter(logging.Formatter):
    """Custom log formatter with color support for console output."""
    
    # Color mapping for different log levels
    LEVEL_COLORS = {
        logging.DEBUG: Colors.BRIGHT_BLACK,
        logging.INFO: Colors.CYAN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.BG_RED + Colors.WHITE,
        SUCCESS: Colors.BOLD + Colors.GREEN,
    }
    
    def __init__(self, *args, use_color: bool = True, **kwargs):
        """Initialize formatter with optional color support."""
        super().__init__(*args, **kwargs)
        self.use_color = use_color and _supports_color()
    
    def format(self, record):
        """Format log record with colors if enabled."""
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        
        if self.use_color:
            # Add color to level name
            levelname_color = self.LEVEL_COLORS.get(record.levelno, '')
            record.levelname = f"{levelname_color}{record.levelname}{Colors.RESET}"
            
            # Add color to message based on level
            if record.levelno == SUCCESS:
                record.msg = f"{Colors.BOLD}{Colors.GREEN}{record.msg}{Colors.RESET}"
            elif record.levelno >= logging.ERROR:
                record.msg = f"{Colors.RED}{record.msg}{Colors.RESET}"
            elif record.levelno == logging.WARNING:
                record.msg = f"{Colors.YELLOW}{record.msg}{Colors.RESET}"
            elif record.levelno == logging.INFO:
                record.msg = f"{Colors.BRIGHT_CYAN}{record.msg}{Colors.RESET}"
            elif record.levelno == logging.DEBUG:
                record.msg = f"{Colors.DIM}{record.msg}{Colors.RESET}"
        
        return super().format(record)

class CustomFormatter(logging.Formatter):
    """Custom log formatter that properly handles the SUCCESS log level (no color for file output)."""
    def format(self, record):
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        return super().format(record)

def setup_logger(name: str = "reportalin", log_level: int = logging.INFO, use_color: bool = True) -> logging.Logger:
    """
    Set up central logger with file and console handlers.
    
    Args:
        name: Logger name
        log_level: Minimum log level to capture
        use_color: Enable colored console output (default: True)
    
    Returns:
        Configured logger instance
    """
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
    
    # File handler: No color, plain text for file output
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Console handler: Colored output, show only SUCCESS, ERROR, and CRITICAL
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)  # Only ERROR (40) and above on console
    console_handler.setFormatter(ColoredFormatter('%(levelname)s: %(message)s', use_color=use_color))
    
    # Add custom filter to allow SUCCESS messages on console
    class SuccessOrErrorFilter(logging.Filter):
        """Allow SUCCESS (25), ERROR (40), and CRITICAL (50) but suppress WARNING (30)."""
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == SUCCESS or record.levelno >= logging.ERROR
    
    console_handler.addFilter(SuccessOrErrorFilter())
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    # Log initialization message (goes to file only due to filter)
    if use_color and _supports_color():
        _logger.info(f"Logging initialized with colored output. Log file: {log_file}")
    else:
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

