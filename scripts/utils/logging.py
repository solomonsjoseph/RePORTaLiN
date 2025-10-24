"""
Centralized Logging Module
===========================

Comprehensive logging system with custom SUCCESS level, dual output (file + console),
and intelligent filtering. Features timestamped files and automatic log directory creation.

New in v0.0.12:
- Enhanced verbose logging with detailed formatter
- VerboseLogger class for tree-view, step-by-step debugging
- Better error context and stack traces
- Timing information for all operations

Key Features
------------
- **Custom SUCCESS Level**: Between INFO and WARNING for successful operations
- **Dual Output**: Console (clean) and file (detailed) with independent filtering
- **Verbose Mode**: Tree-view logging with context managers (DEBUG level)
- **Timestamped Logs**: Automatic log file creation in ``.logs/`` directory
- **UTF-8 Support**: International character encoding
- **Progress Bar Integration**: Works seamlessly with tqdm

Log Levels
----------
- DEBUG (10): Verbose mode only - detailed file processing, timing, metrics
- INFO (20): Default - major steps and summaries
- SUCCESS (25): Custom level - successful completions (console + file)
- WARNING (30): Potential issues
- ERROR (40): Failures
- CRITICAL (50): Fatal errors

Console vs. File Output
-----------------------
- **Console**: Only SUCCESS, ERROR, and CRITICAL (keeps terminal clean)
- **File**: INFO or DEBUG (depending on --verbose flag) and above

Verbose Logging (VerboseLogger)
--------------------------------
The VerboseLogger class provides tree-view formatted output for detailed debugging:

Usage Example:
    >>> from scripts.utils import logging as log
    >>> vlog = log.get_verbose_logger()
    >>> 
    >>> with vlog.file_processing("data.xlsx", total_records=100):
    ...     vlog.metric("Total rows", 100)
    ...     with vlog.step("Loading data"):
    ...         vlog.detail("Reading sheet 1...")
    ...         vlog.timing("Load time", 0.45)

Output Format:
    ├─ Processing: data.xlsx (100 records)
    │  ├─ Total rows: 100
    │  ├─ Loading data
    │  │  │  Reading sheet 1...
    │  │  │  ⏱ Load time: 0.45s
    │  └─ ✓ Complete

VerboseLogger Methods:
    - file_processing(filename, total_records): Context manager for file-level operations
    - step(step_name): Context manager for processing steps
    - detail(message): Log detailed information
    - metric(label, value): Log metrics/statistics
    - timing(operation, seconds): Log operation timing
    - items_list(label, items, max_show): Log lists with truncation

Integration
-----------
Used by all pipeline modules:
    - scripts/load_dictionary.py: Sheet and table processing
    - scripts/extract_data.py: File extraction and duplicate column removal
    - scripts/deidentify.py: De-identification and validation

See Also
--------
- User Guide: docs/sphinx/user_guide/usage.rst (Verbose Logging Details section)
- Developer Guide: docs/sphinx/developer_guide/architecture.rst (Logging System section)
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

def setup_logger(name: str = "reportalin", log_level: int = logging.INFO, simple_mode: bool = False) -> logging.Logger:
    """Set up central logger with file and console handlers.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, etc.)
        simple_mode: If True, minimal console output (success/errors only)
    
    Note:
        This function is idempotent - if called multiple times, it returns
        the same logger instance. Parameters from subsequent calls are ignored.
        To reconfigure, manually reset the global _logger variable.
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        # Log a debug message if parameters differ from initial setup
        if _logger.level != log_level:
            _logger.debug(f"setup_logger called with different log_level ({log_level}), but logger already initialized with level {_logger.level}")
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
    
    # Console handler: behavior depends on simple_mode
    console_handler = logging.StreamHandler(sys.stdout)
    
    if simple_mode:
        # Simple mode: only show SUCCESS, WARNING, ERROR, and CRITICAL
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(CustomFormatter('%(levelname)s: %(message)s'))
        
        class SimpleFilter(logging.Filter):
            """Allow SUCCESS (25), WARNING (30), ERROR (40), and CRITICAL (50)."""
            def filter(self, record: logging.LogRecord) -> bool:
                return record.levelno == SUCCESS or record.levelno >= logging.WARNING
        
        console_handler.addFilter(SimpleFilter())
    else:
        # Default mode: Show only SUCCESS, ERROR, and CRITICAL (suppress DEBUG, INFO, WARNING)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(CustomFormatter('%(levelname)s: %(message)s'))
        
        class SuccessOrErrorFilter(logging.Filter):
            """Allow SUCCESS (25), ERROR (40), and CRITICAL (50) but suppress WARNING (30)."""
            def filter(self, record: logging.LogRecord) -> bool:
                return record.levelno == SUCCESS or record.levelno >= logging.ERROR
        
        console_handler.addFilter(SuccessOrErrorFilter())
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    _logger.info(f"Logging initialized. Log file: {log_file}")
    
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get the configured logger instance or set it up if not already done.
    
    Args:
        name: Logger name (optional). Accepted for API compatibility with
              standard Python logging patterns (e.g., ``logging.getLogger(__name__)``),
              but currently ignored as this returns a singleton logger instance
              shared by all modules.
    
    Returns:
        The global 'reportalin' logger instance
        
    Note:
        This function implements a singleton pattern - all modules share the same
        logger instance. The name parameter is accepted for compatibility with
        standard Python logging but is currently ignored. A debug message is
        logged if a name is provided and the logger is already initialized.
        
    Examples:
        Standard usage (singleton pattern)::
        
            from scripts.utils import get_logger
            logger = get_logger()
            logger.info("Processing data...")
        
        Compatible with Python logging pattern::
        
            logger = get_logger(__name__)  # Works but returns singleton logger
            logger.info("Message logged")
    
    See Also:
        :func:`setup_logger` - Configure the singleton logger with custom settings
    """
    # Log a debug message if name is provided (helps users understand singleton behavior)
    if name is not None and _logger is not None:
        _logger.debug(
            f"get_logger(name='{name}') called but returning singleton logger instance. "
            f"All modules share the same 'reportalin' logger."
        )
    
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

# Verbose Logging Utilities (for detailed debugging across all steps)
# ====================================================================

class VerboseLogger:
    """Centralized verbose logging for detailed output in DEBUG mode.
    
    Provides formatted tree-view output for file processing, step execution,
    and operation timing. Only logs when logger is in DEBUG mode.
    
    Usage:
        vlog = VerboseLogger(log)
        with vlog.file_processing("file.xlsx", total_records=412):
            with vlog.step("Processing step"):
                vlog.detail("Details here")
    """
    
    def __init__(self, logger_module):
        """Initialize with logger module."""
        self.log = logger_module
        self._indent = 0
    
    def _is_verbose(self) -> bool:
        """Check if verbose (DEBUG) logging is enabled."""
        return get_logger().level == logging.DEBUG
    
    def _log_tree(self, prefix: str, message: str) -> None:
        """Log with tree-view formatting."""
        if self._is_verbose():
            indent = "  " * self._indent
            self.log.debug(f"{indent}{prefix}{message}")
    
    class _ContextManager:
        """Context manager for tree-view logging blocks."""
        def __init__(self, vlog: 'VerboseLogger', prefix: str, header: str, footer: str = None):
            self.vlog = vlog
            self.prefix = prefix
            self.header = header
            self.footer = footer
        
        def __enter__(self):
            self.vlog._log_tree(self.prefix, self.header)
            self.vlog._indent += 1
            return self
        
        def __exit__(self, *args):
            self.vlog._indent -= 1
            if self.footer:
                # Use └─ for footer instead of ├─ to show the final item
                self.vlog._log_tree("└─ ", self.footer)
    
    def file_processing(self, filename: str, total_records: int = None):
        """Context manager for processing a file."""
        header = f"Processing: {filename}"
        if total_records is not None:
            header += f" ({total_records} records)"
        return self._ContextManager(self, "├─ ", header, "✓ Complete")
    
    def step(self, step_name: str):
        """Context manager for a processing step."""
        return self._ContextManager(self, "├─ ", step_name)
    
    def detail(self, message: str) -> None:
        """Log a detail message within a step."""
        self._log_tree("│  ", message)
    
    def metric(self, label: str, value: Any) -> None:
        """Log a metric/statistic."""
        self._log_tree("├─ ", f"{label}: {value}")
    
    def timing(self, operation: str, seconds: float) -> None:
        """Log operation timing."""
        self._log_tree("├─ ", f"⏱ {operation}: {seconds:.2f}s")
    
    def items_list(self, label: str, items: list, max_show: int = 5) -> None:
        """Log a list of items with truncation if too long."""
        if not self._is_verbose():
            return
        
        if len(items) <= max_show:
            self.detail(f"{label}: {', '.join(str(i) for i in items)}")
        else:
            self.detail(f"{label}: {', '.join(str(i) for i in items[:max_show])} ... (+{len(items)-max_show} more)")


# Create a global VerboseLogger instance for use across modules
_verbose_logger: Optional[VerboseLogger] = None

def get_verbose_logger() -> VerboseLogger:
    """Get or create the global VerboseLogger instance."""
    global _verbose_logger
    if _verbose_logger is None:
        _verbose_logger = VerboseLogger(sys.modules[__name__])
    return _verbose_logger

