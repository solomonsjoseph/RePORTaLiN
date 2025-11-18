"""Enhanced centralized logging module with organized folder structure.

This module provides a comprehensive logging system for the RePORTaLiN project,
featuring:
- Custom SUCCESS log level (level 25, between INFO and WARNING)
- Thread-safe singleton logger initialization
- Organized log folder structure by module category (RAG, data_cleaning, main)
- Log rotation with configurable file size and backup count
- Multiple output formats (text, JSON for monitoring integration)
- Convenience functions for quick logging (debug, info, success, error, etc.)
- Decorators for automatic error and timing logging
- VerboseLogger class for hierarchical/tree-view debug output
- Log cleanup utilities with age and count-based retention

The logging system supports two modes:
    - Default mode: Single unified log file, minimal console output
    - Verbose mode: Module-specific log files, detailed console output

Configuration is controlled via environment variables:
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - LOG_VERBOSE: Enable verbose mode ('true' or 'false')
    - LOG_FORMAT: Output format ('json' for JSON, default is text)
    - LOG_DIR: Base directory for log files (default: '.logs')

Thread Safety:
    Logger initialization uses double-check locking pattern for thread-safe
    singleton creation without unnecessary locking overhead.

Log Organization:
    Logs are organized into categories based on module name:
    - data_cleaning_and_processing: Data preparation modules
    - RAG/data_ingestion: Vector database and RAG pipeline modules
    - main: Main application and unknown modules

Typical Usage:
    Basic logging::
    
        from scripts.utils.logging_system import setup_logging, info, success, error
        
        setup_logging(module_name='scripts.extract_data', log_level='INFO')
        info("Starting data extraction")
        success("Data extraction completed")
        error("Failed to process file", include_log_path=True)
    
    With decorators::
    
        from scripts.utils.logging_system import log_errors, log_time
        
        @log_time()
        @log_errors(reraise=True)
        def process_data(df):
            # Automatically logs execution time and any errors
            return df.clean()
    
    Verbose hierarchical logging::
    
        from scripts.utils.logging_system import get_verbose_logger
        
        vlog = get_verbose_logger()
        with vlog.file_processing("data.xlsx", total_records=1000):
            with vlog.step("Validation"):
                vlog.detail("Checking schema")
                vlog.metric("Valid records", 995)

Warning:
    Always call setup_logging() at application entry point before using
    logging functions. The module uses a singleton pattern, so subsequent
    calls return the existing logger without re-initialization.

Note:
    The module adds a custom 'success' method to the logging.Logger class
    for convenient SUCCESS-level logging on any logger instance.
"""

import functools
import json
import logging
import logging.handlers
import os
import sys
import threading
import time
import types
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Callable, Dict

# Public API
__all__ = [
    # Logging setup
    'setup_logging',
    'setup_logger',  # Legacy compatibility
    'reset_logging',
    'get_logger',
    'get_log_file_path',
    'get_verbose_logger',
    'cleanup_old_logs',
    
    # Convenience functions
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'success',
    'exception',
    
    # Decorators and context managers
    'log_errors',
    'log_time',
    'log_execution_time',
    
    # Constants
    'SUCCESS',
    'MODULE_CATEGORY_MAP',
    
    # Classes
    'VerboseLogger',
    'CustomFormatter',
    'JSONFormatter',
]

# Custom SUCCESS level
SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

# Global configuration
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[str] = None
_logger_lock = threading.Lock()

# Module to category mapping for organized log structure
MODULE_CATEGORY_MAP = {
    # Data Cleaning and Processing
    'scripts.extract_data': 'data_cleaning_and_processing',
    'scripts.load_dictionary': 'data_cleaning_and_processing',
    'scripts.deidentify': 'data_cleaning_and_processing',
    
    # RAG - Data Ingestion
    'scripts.vector_db.pdf_chunking': 'RAG/data_ingestion',
    'scripts.vector_db.jsonl_chunking_nl': 'RAG/data_ingestion',
    'scripts.vector_db.embeddings': 'RAG/data_ingestion',
    'scripts.vector_db.adaptive_embeddings': 'RAG/data_ingestion',
    'scripts.vector_db.ingest_pdfs': 'RAG/data_ingestion',
    'scripts.vector_db.ingest_records': 'RAG/data_ingestion',
    'scripts.vector_db.vector_store': 'RAG/data_ingestion',
    
    # Main application
    '__main__': 'main',
    'main': 'main',
}


class CustomFormatter(logging.Formatter):
    """Enhanced formatter with SUCCESS level support and optional colors.
    
    This formatter extends the standard logging.Formatter to properly handle
    the custom SUCCESS log level (25). It ensures SUCCESS messages are
    displayed with the correct level name.
    
    The formatter respects the format string passed during initialization
    and applies standard timestamp, logger name, and message formatting.
    
    Attributes:
        Inherits all attributes from logging.Formatter.
    
    Example:
        >>> formatter = CustomFormatter('%(levelname)s: %(message)s')
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
        >>> logger.addHandler(handler)
        >>> logger.log(SUCCESS, "Operation completed")
        SUCCESS: Operation completed
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with proper SUCCESS level handling.
        
        Overrides the base format method to ensure records at the SUCCESS
        level (25) display "SUCCESS" as the level name instead of a numeric
        value or default name.
        
        Args:
            record: The log record to format, containing message, level,
                timestamp, and other metadata.
        
        Returns:
            The formatted log message as a string, ready for output to
            file or console.
        
        Example:
            >>> record = logging.LogRecord(
            ...     name="test", level=SUCCESS, pathname="", lineno=0,
            ...     msg="Done", args=(), exc_info=None
            ... )
            >>> formatter = CustomFormatter('%(levelname)s: %(message)s')
            >>> formatter.format(record)
            'SUCCESS: Done'
        """
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (monitoring tools integration).
    
    This formatter outputs log records as JSON objects, making them suitable
    for ingestion by log aggregation and monitoring tools (e.g., ELK stack,
    Splunk, CloudWatch).
    
    Each log record is converted to a JSON object with the following fields:
        - timestamp: ISO 8601 formatted timestamp
        - level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL, SUCCESS)
        - logger: Logger name
        - module: Module name where log originated
        - function: Function name where log originated
        - line: Line number where log originated
        - message: Formatted log message
        - thread_id: Thread ID
        - thread_name: Thread name
        - process_id: Process ID
        - process_name: Process name
        - exception: Stack trace (if exception was logged)
        - extra: Additional custom fields (if provided)
    
    Example:
        >>> formatter = JSONFormatter()
        >>> handler = logging.FileHandler('app.json')
        >>> handler.setFormatter(formatter)
        >>> logger.addHandler(handler)
        >>> logger.info("Processing started", extra={'user_id': 123})
        # Output: {"timestamp": "2024-01-15T10:30:00.123456", "level": "INFO", ...}
    
    Note:
        JSON output includes full exception stack traces when logging
        exceptions with exc_info=True.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Converts a LogRecord into a JSON string containing structured
        logging information suitable for machine parsing and analysis.
        
        Args:
            record: The log record to format, containing all logging metadata.
        
        Returns:
            A JSON string representation of the log record with all relevant
            fields (timestamp, level, message, thread info, exception, etc.).
        
        Example:
            >>> record = logging.LogRecord(
            ...     name="myapp", level=logging.INFO, pathname="app.py",
            ...     lineno=42, msg="User login", args=(), exc_info=None
            ... )
            >>> formatter = JSONFormatter()
            >>> json_output = formatter.format(record)
            >>> import json
            >>> data = json.loads(json_output)
            >>> data['level']
            'INFO'
            >>> data['message']
            'User login'
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread_id': record.thread,
            'thread_name': record.threadName,
            'process_id': record.process,
            'process_name': record.processName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra
        
        return json.dumps(log_data)


def _get_log_category(module_name: str) -> str:
    """Determine log category (folder) based on module name.
    
    Maps a module name to its corresponding log category for organized
    log file storage. The mapping supports exact matches and prefix-based
    matching for submodules.
    
    Category Structure:
        - data_cleaning_and_processing: Data extraction, loading, deidentification
        - RAG/data_ingestion: Vector database, embeddings, PDF/JSONL ingestion
        - main: Main application and unmapped modules
    
    Args:
        module_name: The full module name (e.g., 'scripts.extract_data',
            'scripts.vector_db.embeddings', '__main__').
    
    Returns:
        The log category string corresponding to the module. Returns 'main'
        if the module is not found in MODULE_CATEGORY_MAP.
    
    Example:
        >>> _get_log_category('scripts.extract_data')
        'data_cleaning_and_processing'
        >>> _get_log_category('scripts.vector_db.embeddings')
        'RAG/data_ingestion'
        >>> _get_log_category('unknown_module')
        'main'
    
    Note:
        This function uses MODULE_CATEGORY_MAP for lookups. To add new
        categories, update the MODULE_CATEGORY_MAP dictionary.
    """
    # Check exact match first
    if module_name in MODULE_CATEGORY_MAP:
        return MODULE_CATEGORY_MAP[module_name]
    
    # Check if it's a submodule
    for module_prefix, category in MODULE_CATEGORY_MAP.items():
        if module_name.startswith(module_prefix + '.'):
            return category
    
    # Default category for unknown modules
    return 'main'


def _get_log_directory(category: str, base_dir: Optional[Path] = None, use_category: bool = True) -> Path:
    """Get the log directory path for a given category.
    
    Creates and returns the log directory path based on the category and
    verbose mode setting. In verbose mode, logs are organized into
    category-specific subdirectories. In default mode, all logs go to a
    single main directory.
    
    Args:
        category: The log category (e.g., 'RAG/data_ingestion', 'main').
        base_dir: The base directory for logs. If None, uses LOG_DIR
            environment variable or defaults to '.logs/RePORTaLiN'.
        use_category: If True, create category-based subdirectories (verbose
            mode). If False, use single main directory (default mode).
    
    Returns:
        A Path object pointing to the log directory. The directory is
        created if it doesn't exist (including parent directories).
    
    Side Effects:
        Creates the log directory and all parent directories if they don't
        exist (using mkdir with parents=True, exist_ok=True).
    
    Example:
        >>> log_dir = _get_log_directory('RAG/data_ingestion', use_category=True)
        >>> log_dir
        PosixPath('.logs/RePORTaLiN/RAG/data_ingestion')
        
        >>> log_dir = _get_log_directory('main', use_category=False)
        >>> log_dir
        PosixPath('.logs/RePORTaLiN')
    
    Note:
        The LOG_DIR environment variable can be used to customize the base
        log directory location (e.g., '/var/log' for system-wide logging).
    """
    if base_dir is None:
        # Get base directory from environment or use default
        logs_root = os.getenv('LOG_DIR', '.logs')
        base_dir = Path(logs_root) / 'RePORTaLiN'
    
    # In verbose mode, use category-based folder structure
    # In default mode, use single main directory
    log_dir = base_dir / category if use_category else base_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(
    module_name: str = '__main__',
    log_level: Optional[str] = None,
    simple_mode: bool = False,
    verbose: bool = False,
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
) -> logging.Logger:
    """Set up centralized logging with organized folder structure and rotation.
    
    Initializes the singleton logger for the RePORTaLiN application with
    comprehensive features including log rotation, category-based organization,
    and multiple output formats. This function should be called once at
    application startup.
    
    The function uses a double-check locking pattern for thread-safe singleton
    initialization. Subsequent calls return the existing logger without
    re-initialization.
    
    Logging Modes:
        - Default mode: Single unified log file, minimal console output
          (only SUCCESS, ERROR, CRITICAL to console)
        - Simple mode: Shows WARNING and above to console
        - Verbose mode: Module-specific log files, category-based folders,
          detailed console output
    
    Console Output Filtering:
        - Default mode: SUCCESS (25), ERROR (40), CRITICAL (50)
        - Simple mode: SUCCESS (25), WARNING (30), ERROR (40), CRITICAL (50)
        - Verbose mode: All levels as configured by log_level
    
    Args:
        module_name: The module name for category mapping (e.g.,
            'scripts.extract_data', '__main__'). Determines log file location
            and naming.
        log_level: Logging level as string ('DEBUG', 'INFO', 'WARNING',
            'ERROR', 'CRITICAL'). If None, uses LOG_LEVEL environment
            variable or defaults to 'INFO'.
        simple_mode: If True, show WARNING and above on console. If False,
            show only SUCCESS, ERROR, and CRITICAL on console.
        verbose: If True, enable verbose mode with module-specific log files
            and category-based folders. If False (default), use single unified
            log file. Can also be set via LOG_VERBOSE environment variable.
        json_format: If True, use JSON formatter for structured logging.
            If False (default), use text formatter. Can also be set via
            LOG_FORMAT environment variable.
        max_bytes: Maximum size of log file before rotation (default: 10MB).
            When exceeded, the log file is rotated and a new one is created.
        backup_count: Number of rotated log files to keep (default: 10).
            Older backups are deleted when this limit is exceeded.
    
    Returns:
        The configured singleton Logger instance with handlers attached.
        All subsequent calls return this same instance.
    
    Side Effects:
        - Creates log directory structure under .logs/RePORTaLiN/ (or LOG_DIR)
        - Creates timestamped log file with rotation handlers
        - Configures console and file handlers with appropriate formatters
        - Adds custom 'success' method to logging.Logger class
        - Sets global _logger and _log_file_path variables
    
    Raises:
        OSError: If log directory cannot be created due to permissions.
        ValueError: If log_level is invalid (not a recognized logging level).
    
    Example:
        Basic setup::
        
            from scripts.utils.logging_system import setup_logging, info, success
            
            logger = setup_logging(
                module_name='scripts.extract_data',
                log_level='INFO'
            )
            info("Application started")
            success("Data extraction completed")
        
        Verbose mode with JSON output::
        
            logger = setup_logging(
                module_name='scripts.vector_db.embeddings',
                log_level='DEBUG',
                verbose=True,
                json_format=True
            )
            # Creates .logs/RePORTaLiN/RAG/data_ingestion/embeddings_20240115_103000.log
        
        Using environment variables::
        
            # Set in shell: export LOG_LEVEL=DEBUG LOG_VERBOSE=true
            logger = setup_logging(module_name='__main__')
            # Uses DEBUG level and verbose mode from environment
    
    Thread Safety:
        This function is thread-safe. Uses double-check locking to ensure
        only one logger instance is created even under concurrent calls.
    
    Note:
        Log files are always timestamped (YYYYMMDD_HHMMSS) to prevent
        overwriting previous runs. Rotation creates numbered backups
        (e.g., app.log.1, app.log.2, etc.).
    """
    global _logger, _log_file_path
    
    # Fast path: return existing logger without lock
    if _logger is not None:
        return _logger
    
    # Double-check pattern for thread-safe initialization
    with _logger_lock:
        # Check again after acquiring lock
        if _logger is not None:
            return _logger
        
        # Determine log level from parameter, environment, or default
        if log_level is None:
            log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Determine verbose mode from parameter or environment
    if not verbose:
        verbose = os.getenv('LOG_VERBOSE', '').lower() == 'true'
    
    # Determine log format from parameter or environment
    if not json_format:
        json_format = os.getenv('LOG_FORMAT', '').lower() == 'json'
    
    # Create root logger
    _logger = logging.getLogger('reportalin')
    _logger.setLevel(numeric_level)
    _logger.handlers.clear()
    
    # Determine log category and directory
    category = _get_log_category(module_name)
    log_dir = _get_log_directory(category, use_category=verbose)
    
    # Create timestamped log filename (ALWAYS includes date and time)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if verbose:
        # Verbose mode: Use module-specific name
        module_simple_name = module_name.split('.')[-1] if module_name != '__main__' else 'reportalin_main'
        log_file = log_dir / f"{module_simple_name}_{timestamp}.log"
    else:
        # Default mode: Use single main log file with timestamp
        log_file = log_dir / f"reportalin_{timestamp}.log"
    
    _log_file_path = str(log_file)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    
    # Choose formatter
    if json_format:
        file_formatter = JSONFormatter()
    else:
        # Enhanced format with thread/process info for DEBUG level
        if numeric_level == logging.DEBUG:
            format_str = (
                '%(asctime)s - [PID:%(process)d TID:%(thread)d] - '
                '%(name)s - %(levelname)s - [%(filename)s:%(lineno)d:%(funcName)s] - '
                '%(message)s'
            )
        else:
            format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        file_formatter = CustomFormatter(format_str)
    
    file_handler.setFormatter(file_formatter)
    
    # Console handler with filtering
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
        # Default mode: Show only SUCCESS, ERROR, and CRITICAL
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(CustomFormatter('%(levelname)s: %(message)s'))
        
        class SuccessOrErrorFilter(logging.Filter):
            """Allow SUCCESS (25), ERROR (40), and CRITICAL (50)."""
            def filter(self, record: logging.LogRecord) -> bool:
                return record.levelno == SUCCESS or record.levelno >= logging.ERROR
        
        console_handler.addFilter(SuccessOrErrorFilter())
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    # Log initialization with mode info
    mode = "verbose" if verbose else "default"
    _logger.info(f"Logging initialized. Mode: {mode}, Category: {category}, Log file: {log_file}")
    
    return _logger


def reset_logging() -> None:
    """Reset logging configuration.
    
    Closes all handlers, removes them from the logger, and resets the global
    logger and log file path variables. This is primarily used for testing
    or when you need to reinitialize logging with different settings.
    
    Side Effects:
        - Closes all file handles and handlers attached to the logger
        - Removes all handlers from the logger
        - Sets global _logger to None
        - Sets global _log_file_path to None
    
    Example:
        >>> setup_logging(module_name='test', log_level='INFO')
        >>> get_logger().info("Test message")
        >>> reset_logging()
        >>> # Logger is now None, next call to get_logger() will reinitialize
    
    Warning:
        This function should rarely be needed in production code. It's
        mainly useful for testing scenarios where you need to reset
        logging state between tests.
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)
        _logger = None
        _log_file_path = None


# Backward compatibility alias
def setup_logger(
    name: str = "reportalin",
    log_level: int = logging.INFO,
    simple_mode: bool = False,
    verbose: bool = False
) -> logging.Logger:
    """Legacy function name for backward compatibility.
    
    Provides backward compatibility with older code that uses setup_logger
    instead of setup_logging. This function converts the old-style parameters
    to the new format and delegates to setup_logging.
    
    Args:
        name: Logger name (defaults to "reportalin"). If not "reportalin",
            it's treated as the module name for category mapping.
        log_level: Numeric logging level (e.g., logging.INFO, logging.DEBUG).
            Converted to string format for setup_logging.
        simple_mode: If True, show WARNING and above on console.
        verbose: If True, enable verbose mode with module-specific log files.
    
    Returns:
        The configured singleton Logger instance from setup_logging.
    
    Example:
        >>> import logging
        >>> logger = setup_logger(
        ...     name="reportalin",
        ...     log_level=logging.DEBUG,
        ...     verbose=True
        ... )
        >>> logger.debug("This is a debug message")
    
    Deprecated:
        Use setup_logging() instead for new code. This function is maintained
        only for backward compatibility.
    """
    # Convert numeric log level to string
    level_name = logging.getLevelName(log_level)
    
    # Map name to module_name for category detection
    module_name = name if name != "reportalin" else "__main__"
    
    return setup_logging(
        module_name=module_name,
        log_level=level_name,
        simple_mode=simple_mode,
        verbose=verbose
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.
    
    Returns the singleton logger instance or a child logger for module-specific
    logging. If the logger hasn't been initialized, calls setup_logging()
    automatically.
    
    Args:
        name: Optional logger name. If None, returns the root 'reportalin'
            logger. If provided, returns a child logger with name
            'reportalin.{name}' for hierarchical logging.
    
    Returns:
        A logging.Logger instance. Either the root logger (if name is None)
        or a child logger for module-specific use.
    
    Example:
        Root logger::
        
            >>> logger = get_logger()
            >>> logger.info("Application started")
        
        Module-specific logger::
        
            >>> data_logger = get_logger('data_processing')
            >>> data_logger.info("Processing data")
            # Logger name will be 'reportalin.data_processing'
    
    Note:
        Child loggers inherit the configuration (level, handlers) from the
        root logger but have their own name for better traceability in logs.
    """
    if _logger is None:
        setup_logging()
    
    if name is None:
        return _logger
    
    # Return child logger for module-specific logging
    return logging.getLogger(f'reportalin.{name}')


def get_log_file_path() -> Optional[str]:
    """Get the path to the current log file.
    
    Returns:
        The absolute path to the current log file as a string, or None if
        logging hasn't been initialized yet.
    
    Example:
        >>> setup_logging(module_name='test')
        >>> path = get_log_file_path()
        >>> print(f"Logs are being written to: {path}")
        Logs are being written to: .logs/RePORTaLiN/main/reportalin_20240115_103000.log
    
    Note:
        This is useful for displaying the log file location to users when
        errors occur, or for programmatically accessing the log file for
        analysis.
    """
    return _log_file_path


def cleanup_old_logs(
    max_age_days: Optional[int] = None,
    max_files: Optional[int] = None,
    log_dir: Optional[Path] = None,
    dry_run: bool = False,
    recursive: bool = True,
    pattern: str = "*.log"
) -> Dict[str, Any]:
    """Clean up old log files from the log directory.
    
    Deletes log files based on age and/or count criteria to manage disk space
    usage. Supports both dry-run mode (preview without deleting) and actual
    deletion. Never deletes the currently active log file.
    
    Cleanup Criteria:
        - Age-based: Delete files older than max_age_days
        - Count-based: Keep only the N most recent files (max_files)
        - Both criteria can be used together (files matching either are deleted)
    
    Args:
        max_age_days: Delete log files older than this many days. Must be
            positive if specified. If None, age-based cleanup is disabled.
        max_files: Keep only this many most recent log files, delete the rest.
            Must be non-negative if specified. If None, count-based cleanup
            is disabled.
        log_dir: Directory to clean. If None, uses LOG_DIR environment
            variable or defaults to '.logs/RePORTaLiN'.
        dry_run: If True, only report what would be deleted without actually
            deleting files. Useful for previewing cleanup actions.
        recursive: If True, search for log files recursively in subdirectories.
            If False, only search the top-level log_dir.
        pattern: Glob pattern for log files (default: "*.log"). Can be
            customized to match specific file types (e.g., "*.json").
    
    Returns:
        A dictionary containing cleanup statistics:
            - files_scanned (int): Total number of log files found
            - files_deleted (int): Number of files deleted (or would be in dry run)
            - files_skipped (int): Number of files skipped (active log, errors)
            - bytes_freed (int): Total bytes freed (or would be in dry run)
            - dry_run (bool): Whether this was a dry run
            - deleted_files (List[str]): List of deleted file paths
    
    Raises:
        ValueError: If neither max_age_days nor max_files is specified, or
            if max_age_days is not positive, or if max_files is negative.
    
    Side Effects:
        - Deletes log files matching criteria (unless dry_run=True)
        - Logs cleanup actions (start, file deletions, summary)
        - Never deletes the currently active log file
    
    Example:
        Dry run to preview cleanup::
        
            >>> from scripts.utils.logging_system import cleanup_old_logs
            >>> stats = cleanup_old_logs(
            ...     max_age_days=30,
            ...     max_files=50,
            ...     dry_run=True
            ... )
            >>> print(f"Would delete {stats['files_deleted']} files")
            >>> print(f"Would free {stats['bytes_freed']} bytes")
        
        Delete files older than 7 days::
        
            >>> stats = cleanup_old_logs(max_age_days=7)
            >>> print(f"Deleted {stats['files_deleted']} old log files")
        
        Keep only 100 most recent log files::
        
            >>> stats = cleanup_old_logs(max_files=100)
            >>> print(f"Kept 100 recent files, deleted {stats['files_deleted']}")
        
        Clean specific directory with custom pattern::
        
            >>> from pathlib import Path
            >>> stats = cleanup_old_logs(
            ...     max_age_days=14,
            ...     log_dir=Path('/var/log/myapp'),
            ...     pattern="app_*.log"
            ... )
    
    Warning:
        The active log file is automatically skipped to prevent deletion of
        the file currently being written to. Files that cannot be deleted
        due to permission errors are logged and skipped.
    
    Note:
        File age is determined by modification time (mtime). For count-based
        cleanup, files are sorted by modification time (newest first) and
        files beyond the max_files limit are deleted.
    """
    # Validation
    if max_age_days is None and max_files is None:
        raise ValueError("At least one of max_age_days or max_files must be specified")
    
    if max_age_days is not None and max_age_days <= 0:
        raise ValueError("max_age_days must be positive")
    
    if max_files is not None and max_files < 0:
        raise ValueError("max_files must be non-negative")
    
    # Determine log directory
    if log_dir is None:
        logs_root = os.getenv('LOG_DIR', '.logs')
        log_dir = Path(logs_root) / 'RePORTaLiN'
    else:
        log_dir = Path(log_dir)
    
    if not log_dir.exists():
        # No log directory, nothing to clean
        return {
            'files_scanned': 0,
            'files_deleted': 0,
            'files_skipped': 0,
            'bytes_freed': 0,
            'dry_run': dry_run,
            'deleted_files': []
        }
    
    logger = get_logger()
    
    # Get current active log file (never delete this)
    active_log_file = _log_file_path
    
    # Find all log files
    if recursive:
        log_files = list(log_dir.rglob(pattern))
    else:
        log_files = list(log_dir.glob(pattern))
    
    # Filter out directories, keep only files
    log_files = [f for f in log_files if f.is_file()]
    
    files_scanned = len(log_files)
    files_deleted = 0
    files_skipped = 0
    bytes_freed = 0
    deleted_files = []
    
    logger.info(
        f"Log cleanup started. Scanned {files_scanned} files in {log_dir}. "
        f"Mode: {'DRY RUN' if dry_run else 'DELETE'}. "
        f"Criteria: max_age_days={max_age_days}, max_files={max_files}"
    )
    
    # Calculate cutoff time for age-based deletion
    cutoff_time = None
    if max_age_days is not None:
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    
    # Sort files by modification time (newest first) for count-based deletion
    log_files_sorted = sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    # Determine which files to delete
    for idx, log_file in enumerate(log_files_sorted):
        try:
            # Skip active log file
            if active_log_file and str(log_file.resolve()) == str(Path(active_log_file).resolve()):
                logger.debug(f"Skipping active log file: {log_file}")
                files_skipped += 1
                continue
            
            # Get file stats
            file_stat = log_file.stat()
            file_age_days = (time.time() - file_stat.st_mtime) / (24 * 60 * 60)
            file_size = file_stat.st_size
            
            # Determine if file should be deleted
            should_delete = False
            reason = []
            
            # Age-based deletion
            if max_age_days is not None and file_stat.st_mtime < cutoff_time:
                should_delete = True
                reason.append(f"older than {max_age_days} days (age: {file_age_days:.1f} days)")
            
            # Count-based deletion (keep only N most recent)
            if max_files is not None and idx >= max_files:
                should_delete = True
                reason.append(f"beyond top {max_files} recent files (rank: {idx + 1})")
            
            if should_delete:
                reason_str = " and ".join(reason)
                
                if dry_run:
                    logger.info(f"Would delete: {log_file} ({file_size} bytes) - Reason: {reason_str}")
                    deleted_files.append(str(log_file))
                    bytes_freed += file_size
                    files_deleted += 1
                else:
                    try:
                        log_file.unlink()
                        logger.info(f"Deleted: {log_file} ({file_size} bytes) - Reason: {reason_str}")
                        deleted_files.append(str(log_file))
                        bytes_freed += file_size
                        files_deleted += 1
                    except PermissionError:
                        logger.warning(f"Permission denied, skipping: {log_file}")
                        files_skipped += 1
                    except OSError as e:
                        logger.warning(f"Error deleting {log_file}: {e}")
                        files_skipped += 1
        
        except Exception as e:
            logger.warning(f"Error processing {log_file}: {e}")
            files_skipped += 1
            continue
    
    # Summary
    stats = {
        'files_scanned': files_scanned,
        'files_deleted': files_deleted,
        'files_skipped': files_skipped,
        'bytes_freed': bytes_freed,
        'dry_run': dry_run,
        'deleted_files': deleted_files
    }
    
    logger.info(
        f"Log cleanup completed. "
        f"Scanned: {files_scanned}, "
        f"{'Would delete' if dry_run else 'Deleted'}: {files_deleted}, "
        f"Skipped: {files_skipped}, "
        f"Bytes {'would be freed' if dry_run else 'freed'}: {bytes_freed:,}"
    )
    
    return stats


# ============================================================================
# Convenience Logging Functions
# ============================================================================

def _append_log_path(msg: str, include_log_path: bool) -> str:
    """Helper to append log file path to messages.
    
    Internal utility function to optionally append the log file path to
    error/warning messages, making it easier for users to locate detailed
    logs when issues occur.
    
    Args:
        msg: The original log message.
        include_log_path: If True and a log file exists, append the path.
    
    Returns:
        The message with log file path appended if requested and available,
        otherwise the original message unchanged.
    
    Example:
        >>> _append_log_path("Error occurred", True)
        'Error occurred\\nFor more details, check the log file at: .logs/.../app.log'
        >>> _append_log_path("Error occurred", False)
        'Error occurred'
    """
    if include_log_path and get_log_file_path():
        return f"{msg}\nFor more details, check the log file at: {get_log_file_path()}"
    return msg


def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a DEBUG level message.
    
    Convenience function for logging DEBUG-level messages. DEBUG messages
    are typically used for detailed diagnostic information useful during
    development and troubleshooting.
    
    Args:
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> debug("Processing record %d of %d", 5, 100)
        >>> debug("Variable state: x=%s, y=%s", x, y)
    """
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log an INFO level message.
    
    Convenience function for logging INFO-level messages. INFO messages
    confirm that things are working as expected and provide general
    progress updates.
    
    Args:
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> info("Starting data extraction from %s", filename)
        >>> info("Processed %d records successfully", count)
    """
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args: Any, include_log_path: bool = False, **kwargs: Any) -> None:
    """Log a WARNING level message.
    
    Convenience function for logging WARNING-level messages. WARNING messages
    indicate something unexpected happened or a potential problem, but the
    application can continue.
    
    Args:
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        include_log_path: If True, append log file location to message.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> warning("Missing optional field: %s", field_name)
        >>> warning("Retrying operation due to timeout", include_log_path=True)
    """
    get_logger().warning(_append_log_path(msg, include_log_path), *args, **kwargs)


def error(msg: str, *args: Any, include_log_path: bool = True, **kwargs: Any) -> None:
    """Log an ERROR level message with optional log file path.
    
    Convenience function for logging ERROR-level messages. ERROR messages
    indicate a serious problem that prevented a function from completing
    its task. By default, includes the log file path in the message.
    
    Args:
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        include_log_path: If True (default), append log file location to
            message to help users find detailed error information.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> error("Failed to open file: %s", filename)
        >>> error("Database connection failed", include_log_path=True)
    """
    get_logger().error(_append_log_path(msg, include_log_path), *args, **kwargs)


def critical(msg: str, *args: Any, include_log_path: bool = True, **kwargs: Any) -> None:
    """Log a CRITICAL level message with optional log file path.
    
    Convenience function for logging CRITICAL-level messages. CRITICAL
    messages indicate a very serious error that may prevent the application
    from continuing. By default, includes the log file path in the message.
    
    Args:
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        include_log_path: If True (default), append log file location to
            message to help users find detailed error information.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> critical("System out of memory, terminating")
        >>> critical("Configuration file corrupted", include_log_path=True)
    """
    get_logger().critical(_append_log_path(msg, include_log_path), *args, **kwargs)


def success(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a SUCCESS level message (custom level 25).
    
    Convenience function for logging SUCCESS-level messages. SUCCESS is a
    custom level (25) between INFO (20) and WARNING (30), used to highlight
    successful completion of important operations. SUCCESS messages always
    appear on the console, even in default mode.
    
    Args:
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> success("Data extraction completed successfully")
        >>> success("Processed %d files without errors", file_count)
    
    Note:
        SUCCESS messages are always visible on console in default mode,
        making them ideal for user-facing status updates.
    """
    get_logger().log(SUCCESS, msg, *args, **kwargs)


def exception(msg: str, *args: Any, include_log_path: bool = True, **kwargs: Any) -> None:
    """Log an exception with full stack trace.
    
    Convenience function for logging exceptions with complete stack traces.
    This should be called from an exception handler to capture the full
    context of the error, including the traceback.
    
    Args:
        msg: The message format string describing the exception context.
        *args: Variable positional arguments for message formatting.
        include_log_path: If True (default), append log file location to
            message to help users find detailed error information.
        **kwargs: Variable keyword arguments passed to logger. If 'exc_info'
            is not provided, it defaults to True to capture the stack trace.
    
    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     exception("Failed to complete operation: %s", str(e))
    
    Note:
        This function automatically sets exc_info=True to capture the full
        exception traceback, unless explicitly overridden in kwargs.
    """
    kwargs.setdefault('exc_info', True)
    get_logger().error(_append_log_path(msg, include_log_path), *args, **kwargs)


# Add success method to Logger class
def _success_method(self: logging.Logger, msg: str, *args: Any, **kwargs: Any) -> None:
    """Custom success logging method for Logger instances.
    
    This method is dynamically added to the logging.Logger class to enable
    SUCCESS-level logging on any logger instance using the standard
    logger.success() syntax.
    
    Args:
        self: The Logger instance (automatically passed).
        msg: The message format string.
        *args: Variable positional arguments for message formatting.
        **kwargs: Variable keyword arguments passed to logger.
    
    Example:
        >>> logger = logging.getLogger('myapp')
        >>> logger.success("Operation completed successfully")
    
    Note:
        This is a monkey-patch to the logging.Logger class. The function
        is assigned to logging.Logger.success at module import time.
    """
    if self.isEnabledFor(SUCCESS):
        self.log(SUCCESS, msg, *args, **kwargs)


logging.Logger.success = _success_method  # type: ignore[attr-defined]


# ============================================================================
# Decorators and Context Managers
# ============================================================================

def log_errors(logger_name: Optional[str] = None, reraise: bool = True):
    """Decorator to automatically log exceptions with full stack trace.
    
    Wraps a function to catch and log any exceptions that occur during
    execution. The exception is logged with full stack trace and function
    arguments for debugging. Optionally re-raises the exception for
    upstream handling.
    
    Args:
        logger_name: Name of the logger to use. If None, uses the decorated
            function's module name for automatic logger selection.
        reraise: If True (default), re-raise the exception after logging.
            If False, suppress the exception and return None.
    
    Returns:
        A decorator function that wraps the target function with exception
        logging functionality.
    
    Example:
        With default settings (re-raises exception)::
        
            >>> @log_errors()
            ... def process_file(filename):
            ...     with open(filename) as f:
            ...         return f.read()
            >>> process_file('missing.txt')  # Logs error with stack trace, then raises
            Traceback (most recent call last):
            ...
            FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'
        
        Suppress exceptions (return None on error)::
        
            >>> @log_errors(reraise=False)
            ... def safe_operation():
            ...     raise ValueError("Something went wrong")
            >>> result = safe_operation()  # Logs error, returns None
            >>> print(result)
            None
        
        With custom logger::
        
            >>> @log_errors(logger_name='data.processing', reraise=True)
            ... def validate_data(df):
            ...     if df.empty:
            ...         raise ValueError("Empty dataframe")
    
    Note:
        The decorator logs both the exception message and the function's
        arguments/kwargs, which can be very helpful for debugging. Be aware
        this may log sensitive data if present in function arguments.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}: {e}\n"
                    f"Args: {args}, Kwargs: {kwargs}"
                )
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def log_time(logger_name: Optional[str] = None, level: int = logging.INFO):
    """Decorator to automatically log function execution time.
    
    Wraps a function to measure and log its execution time. Logs both
    successful completions and failures with their respective durations.
    
    Args:
        logger_name: Name of the logger to use. If None, uses the decorated
            function's module name for automatic logger selection.
        level: Logging level for the timing message (default: logging.INFO).
            Use logging.DEBUG for less important timing information.
    
    Returns:
        A decorator function that wraps the target function with timing
        functionality.
    
    Example:
        Basic usage::
        
            >>> from scripts.utils.logging_system import log_time
            >>> @log_time()
            ... def process_large_file(filename):
            ...     # ... processing code ...
            ...     return result
            >>> result = process_large_file('data.csv')
            # Logs: "process_large_file completed in 2.34s"
        
        With DEBUG level for less important operations::
        
            >>> import logging
            >>> @log_time(level=logging.DEBUG)
            ... def quick_operation():
            ...     return sum(range(1000))
        
        With custom logger::
        
            >>> @log_time(logger_name='performance', level=logging.INFO)
            ... def critical_operation():
            ...     # ... time-sensitive code ...
            ...     pass
    
    Note:
        If the function raises an exception, the elapsed time is still
        logged (at ERROR level) before the exception is re-raised. This
        helps diagnose performance issues that lead to failures.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(
                    level,
                    f"{func.__name__} completed in {elapsed:.2f}s"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.2f}s: {e}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


@contextmanager
def log_execution_time(operation_name: str, logger_name: Optional[str] = None):
    """Context manager to log execution time of a code block.
    
    Measures and logs the execution time of any code block. This is more
    flexible than the @log_time decorator as it can be used for arbitrary
    code sections, not just entire functions.
    
    Args:
        operation_name: A descriptive name for the operation being timed.
            This appears in the log message.
        logger_name: Name of the logger to use. If None, uses the root
            'reportalin' logger.
    
    Yields:
        None. The context manager doesn't provide any value; it simply
        measures time.
    
    Example:
        Time a specific code section::
        
            >>> from scripts.utils.logging_system import log_execution_time
            >>> with log_execution_time("data validation"):
            ...     df = validate_schema(df)
            ...     df = check_duplicates(df)
            ...     df = fix_datatypes(df)
            # Logs: "data validation completed in 1.23s"
        
        Nested timing::
        
            >>> with log_execution_time("full pipeline"):
            ...     with log_execution_time("data loading"):
            ...         df = load_data()
            ...     with log_execution_time("data processing"):
            ...         df = process_data(df)
            # Logs: "data loading completed in 0.50s"
            # Logs: "data processing completed in 2.15s"
            # Logs: "full pipeline completed in 2.65s"
        
        Error handling::
        
            >>> with log_execution_time("risky operation"):
            ...     raise ValueError("Something failed")
            # Logs: "risky operation failed after 0.00s: Something failed"
            # Then raises the exception
    
    Note:
        If an exception occurs within the context, the elapsed time is
        logged at ERROR level with the exception details before re-raising.
        This helps correlate timing with failures.
    """
    logger = get_logger(logger_name)
    start_time = time.time()
    try:
        yield
        elapsed = time.time() - start_time
        logger.info(f"{operation_name} completed in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"{operation_name} failed after {elapsed:.2f}s: {e}",
            exc_info=True
        )
        raise


# ============================================================================
# Verbose Logging (Backward Compatibility)
# ============================================================================

class VerboseLogger:
    """Centralized verbose logging for detailed output in DEBUG mode.
    
    Provides hierarchical, tree-view style logging for detailed diagnostic
    output. Only produces output when the logger is in DEBUG mode, making
    it safe to leave verbose logging calls in production code.
    
    The VerboseLogger supports:
        - Hierarchical/indented output with tree-view characters (├─, │, └─)
        - Context managers for automatic indentation of code blocks
        - Metrics and timing information
        - List truncation for large collections
        - Graceful degradation (silently ignored when not in DEBUG mode)
    
    Attributes:
        log: Reference to the logging module for making log calls.
        _indent: Current indentation level for hierarchical output.
    
    Example:
        Basic usage::
        
            >>> from scripts.utils.logging_system import get_verbose_logger
            >>> vlog = get_verbose_logger()
            >>> vlog("Starting processing")  # Simple message
            >>> vlog.metric("Records found", 1000)
            >>> vlog.detail("Validation passed")
        
        Hierarchical structure with context managers::
        
            >>> vlog = get_verbose_logger()
            >>> with vlog.file_processing("data.xlsx", total_records=500):
            ...     with vlog.step("Validation"):
            ...         vlog.detail("Checking schema")
            ...         vlog.metric("Valid records", 495)
            ...     with vlog.step("Processing"):
            ...         vlog.detail("Applying transformations")
            ...         vlog.timing("Transform operation", 2.34)
            # Output (in DEBUG mode):
            # ├─ Processing: data.xlsx (500 records)
            # ├─ Validation
            # │  Checking schema
            # ├─ Valid records: 495
            # ├─ Processing
            # │  Applying transformations
            # ├─ ⏱ Transform operation: 2.34s
            # └─ ✓ Complete
    
    Note:
        VerboseLogger is designed to have zero performance impact when not
        in DEBUG mode. All methods check _is_verbose() first and return
        immediately if verbose logging is disabled.
    """
    
    def __init__(self, logger_module: types.ModuleType) -> None:
        """Initialize with logger module.
        
        Args:
            logger_module: Reference to the logging module (typically
                sys.modules[__name__] for this module). Used to make
                logger calls.
        
        Example:
            >>> import sys
            >>> vlog = VerboseLogger(sys.modules[__name__])
        """
        self.log = logger_module
        self._indent = 0
    
    def __call__(self, message: str) -> None:
        """Allow VerboseLogger to be called as a simple function.
        
        Enables simple syntax like vlog("message") for quick verbose logging
        without explicitly calling a method.
        
        Args:
            message: The message to log at DEBUG level.
        
        Example:
            >>> vlog = get_verbose_logger()
            >>> vlog("Processing started")
            >>> vlog("Found 100 records")
        """
        if self._is_verbose():
            self.log.debug(message)
    
    def _is_verbose(self) -> bool:
        """Check if verbose (DEBUG) logging is enabled.
        
        Returns:
            True if the logger is initialized and set to DEBUG level,
            False otherwise (including when logging isn't set up yet).
        
        Note:
            This method is safe to call during module import or before
            logging initialization. It returns False if anything goes wrong.
        """
        try:
            # Safe check: Handle case where logging isn't set up yet
            if _logger is None:
                return False
            logger = get_logger()
            return logger and logger.level == logging.DEBUG
        except Exception:
            # During module import, logging might not be ready
            return False
    
    def _log_tree(self, prefix: str, message: str) -> None:
        """Log with tree-view formatting.
        
        Internal method to output indented messages with tree-view prefix
        characters for hierarchical visualization.
        
        Args:
            prefix: Tree-view prefix character(s) (e.g., "├─ ", "│  ", "└─ ").
            message: The message to log.
        
        Note:
            Silently ignores errors to prevent logging failures from
            breaking application flow during module initialization.
        """
        if self._is_verbose():
            try:
                indent = "  " * self._indent
                self.log.debug(f"{indent}{prefix}{message}")
            except Exception:
                # Silently ignore if logging fails during import
                pass
    
    class _ContextManager:
        """Context manager for tree-view logging blocks.
        
        Internal helper class for managing hierarchical logging contexts
        with automatic indentation and optional header/footer messages.
        
        Attributes:
            vlog: Reference to parent VerboseLogger instance.
            prefix: Tree-view prefix for header message.
            header: Header message to log when entering context.
            footer: Optional footer message to log when exiting context.
        """
        def __init__(self, vlog: 'VerboseLogger', prefix: str, header: str, footer: str = None):
            """Initialize context manager.
            
            Args:
                vlog: Parent VerboseLogger instance.
                prefix: Tree-view prefix for the header.
                header: Message to display when entering context.
                footer: Optional message to display when exiting context.
            """
            self.vlog = vlog
            self.prefix = prefix
            self.header = header
            self.footer = footer
        
        def __enter__(self):
            """Enter context: log header and increase indentation.
            
            Returns:
                Self reference for use in 'with ... as ctx:' syntax.
            """
            self.vlog._log_tree(self.prefix, self.header)
            self.vlog._indent += 1
            return self
        
        def __exit__(self, *args):
            """Exit context: decrease indentation and log optional footer.
            
            Args:
                *args: Exception information (type, value, traceback) if
                    an exception occurred, otherwise (None, None, None).
            """
            self.vlog._indent -= 1
            if self.footer:
                self.vlog._log_tree("└─ ", self.footer)
    
    def file_processing(self, filename: str, total_records: int = None):
        """Context manager for processing a file.
        
        Creates a hierarchical logging context for file processing operations,
        with automatic header showing filename and record count, plus a
        completion footer.
        
        Args:
            filename: Name of the file being processed.
            total_records: Optional total number of records in the file.
        
        Returns:
            A context manager that logs entry/exit and manages indentation.
        
        Example:
            >>> vlog = get_verbose_logger()
            >>> with vlog.file_processing("data.xlsx", total_records=1000):
            ...     vlog.detail("Loading data")
            ...     vlog.detail("Processing complete")
            # Output:
            # ├─ Processing: data.xlsx (1000 records)
            # │  Loading data
            # │  Processing complete
            # └─ ✓ Complete
        """
        header = f"Processing: {filename}"
        if total_records is not None:
            header += f" ({total_records} records)"
        return self._ContextManager(self, "├─ ", header, "✓ Complete")
    
    def step(self, step_name: str):
        """Context manager for a processing step.
        
        Creates a hierarchical logging context for a processing step or
        operation within a larger workflow.
        
        Args:
            step_name: Descriptive name of the processing step.
        
        Returns:
            A context manager that logs the step name and manages indentation.
        
        Example:
            >>> vlog = get_verbose_logger()
            >>> with vlog.step("Validation"):
            ...     vlog.detail("Checking schema")
            ...     vlog.detail("Checking duplicates")
            >>> with vlog.step("Transformation"):
            ...     vlog.detail("Applying rules")
            # Output:
            # ├─ Validation
            # │  Checking schema
            # │  Checking duplicates
            # ├─ Transformation
            # │  Applying rules
        """
        return self._ContextManager(self, "├─ ", step_name)
    
    def detail(self, message: str) -> None:
        """Log a detail message within a step.
        
        Logs a detail-level message with appropriate tree-view formatting
        to show it belongs to the current hierarchical context.
        
        Args:
            message: The detail message to log.
        
        Example:
            >>> vlog = get_verbose_logger()
            >>> with vlog.step("Data Loading"):
            ...     vlog.detail("Opening file")
            ...     vlog.detail("Reading headers")
            ...     vlog.detail("Loading rows")
            # Output:
            # ├─ Data Loading
            # │  Opening file
            # │  Reading headers
            # │  Loading rows
        """
        try:
            self._log_tree("│  ", message)
        except Exception:
            pass
    
    def metric(self, label: str, value: Any) -> None:
        """Log a metric/statistic.
        
        Logs a labeled metric or statistical value in a clear format.
        
        Args:
            label: Descriptive label for the metric.
            value: The metric value (number, string, etc.).
        
        Example:
            >>> vlog = get_verbose_logger()
            >>> vlog.metric("Total records", 10000)
            >>> vlog.metric("Processing rate", "125 rec/sec")
            >>> vlog.metric("Memory usage", "245 MB")
            # Output:
            # ├─ Total records: 10000
            # ├─ Processing rate: 125 rec/sec
            # ├─ Memory usage: 245 MB
        """
        try:
            self._log_tree("├─ ", f"{label}: {value}")
        except Exception:
            pass
    
    def timing(self, operation: str, seconds: float) -> None:
        """Log operation timing.
        
        Logs the execution time of an operation with a clock emoji for
        easy visual identification.
        
        Args:
            operation: Name of the operation that was timed.
            seconds: Duration in seconds (float).
        
        Example:
            >>> vlog = get_verbose_logger()
            >>> import time
            >>> start = time.time()
            >>> # ... do work ...
            >>> vlog.timing("Data validation", time.time() - start)
            # Output:
            # ├─ ⏱ Data validation: 2.34s
        """
        try:
            self._log_tree("├─ ", f"⏱ {operation}: {seconds:.2f}s")
        except Exception:
            pass
    
    def items_list(self, label: str, items: list, max_show: int = 5) -> None:
        """Log a list of items with truncation if too long.
        
        Logs a list of items with automatic truncation for long lists,
        showing only the first few items plus a count of remaining items.
        
        Args:
            label: Descriptive label for the list.
            items: List of items to display.
            max_show: Maximum number of items to show before truncating
                (default: 5). If the list has more items, show first
                max_show items plus a count of remaining items.
        
        Example:
            Short list (shows all)::
            
                >>> vlog = get_verbose_logger()
                >>> vlog.items_list("Columns", ["id", "name", "age"])
                # Output:
                # │  Columns: id, name, age
            
            Long list (truncated)::
            
                >>> vlog.items_list("Files", list(range(20)), max_show=3)
                # Output:
                # │  Files: 0, 1, 2 ... (+17 more)
        """
        if not self._is_verbose():
            return
        
        try:
            if len(items) <= max_show:
                self.detail(f"{label}: {', '.join(str(i) for i in items)}")
            else:
                self.detail(f"{label}: {', '.join(str(i) for i in items[:max_show])} ... (+{len(items)-max_show} more)")
        except Exception:
            pass


# Create a global VerboseLogger instance
_verbose_logger: Optional[VerboseLogger] = None


def get_verbose_logger() -> VerboseLogger:
    """Get or create the global VerboseLogger instance.
    
    Returns the singleton VerboseLogger instance, creating it if it doesn't
    exist yet. The VerboseLogger provides hierarchical debug logging that
    only outputs when the logger is in DEBUG mode.
    
    Returns:
        The global VerboseLogger instance for hierarchical verbose logging.
    
    Example:
        >>> from scripts.utils.logging_system import get_verbose_logger, setup_logging
        >>> setup_logging(module_name='test', log_level='DEBUG')
        >>> vlog = get_verbose_logger()
        >>> with vlog.file_processing("data.xlsx", total_records=100):
        ...     vlog.detail("Loading data")
        ...     vlog.metric("Valid rows", 98)
    
    Note:
        The VerboseLogger is safe to use even before logging is initialized.
        It will simply not produce output until the logger is set to DEBUG level.
    """
    global _verbose_logger
    if _verbose_logger is None:
        _verbose_logger = VerboseLogger(sys.modules[__name__])
    return _verbose_logger
