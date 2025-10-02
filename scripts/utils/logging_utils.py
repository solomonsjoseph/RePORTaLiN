"""
Centralized Logging Module
===========================

This module provides a comprehensive, centralized logging system for the RePORTaLiN
project. It implements a custom logging infrastructure with both file and console
output, featuring a custom SUCCESS log level and intelligent log path management.

Features:
    - **Custom SUCCESS Level**: 25-point level between INFO and WARNING for success messages
    - **Dual Output**: Logs to both timestamped file and console simultaneously
    - **Smart Console Filtering**: Only SUCCESS and WARNING+ shown on console
    - **Comprehensive File Logging**: All levels (DEBUG+) written to file
    - **Automatic Log Directory**: Creates ``.logs/`` directory automatically
    - **Timestamped Files**: Each run gets a unique log file with timestamp

Architecture:
    The logging system uses a singleton pattern to ensure consistent logging across
    all modules. It configures:
    
    - **File Handler**: Captures all log levels (DEBUG and above)
    - **Console Handler**: Shows only important messages (SUCCESS, WARNING, ERROR, CRITICAL)
    - **Custom Formatter**: Formats SUCCESS level messages properly

Log Levels (from lowest to highest):
    - DEBUG (10): Detailed diagnostic information
    - INFO (20): General informational messages
    - **SUCCESS (25)**: Custom level for successful operations
    - WARNING (30): Warning messages
    - ERROR (40): Error messages
    - CRITICAL (50): Critical errors

Usage:
    Basic logging::

        from scripts.utils import logging_utils as log
        
        # Setup (usually done in main.py)
        log.setup_logger(name="myproject", log_level=log.logging.INFO)
        
        # Log messages
        log.info("Processing started")
        log.success("Operation completed successfully")
        log.warning("Potential issue detected")
        log.error("An error occurred")

    With log path in error messages::

        log.error("Failed to process file", include_log_path=True)

Functions:
    setup_logger: Initialize the logging system
    get_logger: Get the configured logger instance
    get_log_file_path: Get path to current log file
    debug, info, warning, error, critical, success: Convenience logging functions

Constants:
    SUCCESS (int): Custom log level value (25)

Example:
    Complete usage in a module::

        from scripts.utils import logging_utils as log
        import config
        
        # Initialize logger (in main.py)
        log.setup_logger(name=config.LOG_NAME, log_level=config.LOG_LEVEL)
        
        # Use throughout the application
        log.info("Starting process")
        try:
            # ... do work ...
            log.success("Process completed")
        except Exception as e:
            log.error(f"Process failed: {e}", include_log_path=True, exc_info=True)

See Also:
    :mod:`main`: Main pipeline that initializes logging
    :mod:`config`: Configuration including log settings

Author:
    RePORTaLiN Development Team

Version:
    1.0.0
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

_logger = None
_log_file_path = None

class CustomFormatter(logging.Formatter):
    """
    Custom log formatter that properly handles the SUCCESS log level.

    This formatter extends the standard logging.Formatter to ensure that custom
    log levels (specifically SUCCESS) are displayed with their correct names in
    log output.

    Methods:
        format: Override to set SUCCESS levelname correctly
    """
    def format(self, record):
        """
        Format a log record, ensuring SUCCESS level is properly labeled.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message string.
        """
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        return super().format(record)

def setup_logger(name="reportalin", log_level=logging.INFO):
    """
    Set up the central logger for the project with file and console handlers.

    This function configures a singleton logger that writes to both a timestamped
    log file and the console. It should be called once at application startup.

    Configuration Details:
        - **File Handler**: 
            - Location: ``.logs/<name>_<timestamp>.log``
            - Level: Same as ``log_level`` parameter
            - Format: ``%(asctime)s - %(name)s - %(levelname)s - %(message)s``
        
        - **Console Handler**:
            - Output: stdout
            - Level: Minimum of SUCCESS or WARNING (whichever is lower)
            - Format: ``%(levelname)s: %(message)s`` (simplified)

    Args:
        name (str, optional): Name for the logger instance. Used in log messages
            and log filename. Default is "reportalin".
        log_level (int, optional): Minimum logging level for file output. Use
            logging module constants (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Default is logging.INFO.

    Returns:
        logging.Logger: The configured logger instance.

    Example:
        Basic setup::

            from scripts.utils import logging_utils as log
            logger = log.setup_logger()

        Custom configuration::

            logger = log.setup_logger(
                name="my_pipeline",
                log_level=log.logging.DEBUG
            )

        With config::

            import config
            from scripts.utils import logging_utils as log
            logger = log.setup_logger(
                name=config.LOG_NAME,
                log_level=config.LOG_LEVEL
            )

    Note:
        - Only the first call to setup_logger() configures the logger
        - Subsequent calls return the already-configured logger
        - The ``.logs/`` directory is created automatically
        - Each run creates a new log file with timestamp
        - Console shows only SUCCESS, WARNING, ERROR, CRITICAL messages
        - File contains all messages at or above ``log_level``

    See Also:
        :func:`get_logger`: Get the configured logger
        :func:`get_log_file_path`: Get path to log file
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
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(min(SUCCESS, logging.WARNING))
    console_handler.setFormatter(CustomFormatter('%(levelname)s: %(message)s'))
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    _logger.info(f"Logging initialized. Log file: {log_file}")
    
    return _logger

def get_logger():
    """
    Get the configured logger instance or set it up if not already done.

    This function provides access to the global logger. If the logger hasn't been
    configured yet, it automatically calls setup_logger() with default settings.

    Returns:
        logging.Logger: The configured logger instance.

    Example:
        >>> from scripts.utils import logging_utils as log
        >>> logger = log.get_logger()
        >>> logger.info("This is a message")

    Note:
        - Automatically initializes logger if not already set up
        - Uses default settings if auto-initialized
        - Prefer explicit setup_logger() call for custom configuration
    """
    return _logger if _logger else setup_logger()

def get_log_file_path():
    """
    Get the path to the current log file.

    Returns:
        str or None: The absolute path to the current log file, or None if
            the logger hasn't been initialized yet.

    Example:
        >>> from scripts.utils import logging_utils as log
        >>> log.setup_logger()
        >>> path = log.get_log_file_path()
        >>> print(path)
        '/path/to/project/.logs/reportalin_20231201_143022.log'

    Note:
        Returns None if setup_logger() hasn't been called yet.
    """
    return _log_file_path

# Convenience functions
def _append_log_path(msg, include_log_path):
    """
    Helper function to append log file path to error/warning messages.

    This internal function optionally adds the log file location to messages,
    making it easier for users to find detailed logs when errors occur.

    Args:
        msg (str): The original message.
        include_log_path (bool): Whether to append the log file path.

    Returns:
        str: The message, potentially with log path appended.

    Note:
        Used internally by error, warning, and critical functions.
    """
    if include_log_path and get_log_file_path():
        return f"{msg}\nFor more details, check the log file at: {get_log_file_path()}"
    return msg

def debug(msg, *args, **kwargs):
    """
    Log a DEBUG level message.

    Args:
        msg (str): The message to log.
        *args: Positional arguments for message formatting.
        **kwargs: Keyword arguments passed to the logger.

    Example:
        >>> log.debug("Processing item %d of %d", 5, 10)
    """
    get_logger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    """
    Log an INFO level message.

    Args:
        msg (str): The message to log.
        *args: Positional arguments for message formatting.
        **kwargs: Keyword arguments passed to the logger.

    Example:
        >>> log.info("Starting data processing")
        >>> log.info("Processed %d records", count)
    """
    get_logger().info(msg, *args, **kwargs)

def warning(msg, *args, include_log_path=False, **kwargs):
    """
    Log a WARNING level message.

    Args:
        msg (str): The message to log.
        *args: Positional arguments for message formatting.
        include_log_path (bool, optional): If True, appends log file path to message.
            Default is False.
        **kwargs: Keyword arguments passed to the logger.

    Example:
        >>> log.warning("Data quality issue detected")
        >>> log.warning("Missing %d values", count, include_log_path=True)
    """
    get_logger().warning(_append_log_path(msg, include_log_path), *args, **kwargs)

def error(msg, *args, include_log_path=True, **kwargs):
    """
    Log an ERROR level message.

    By default, error messages include the log file path to help users find
    detailed error information.

    Args:
        msg (str): The message to log.
        *args: Positional arguments for message formatting.
        include_log_path (bool, optional): If True, appends log file path to message.
            Default is True.
        **kwargs: Keyword arguments passed to the logger (e.g., exc_info=True).

    Example:
        >>> log.error("Failed to process file")
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log.error("Operation failed: %s", e, exc_info=True)
    """
    get_logger().error(_append_log_path(msg, include_log_path), *args, **kwargs)

def critical(msg, *args, include_log_path=True, **kwargs):
    """
    Log a CRITICAL level message.

    By default, critical messages include the log file path for detailed debugging.

    Args:
        msg (str): The message to log.
        *args: Positional arguments for message formatting.
        include_log_path (bool, optional): If True, appends log file path to message.
            Default is True.
        **kwargs: Keyword arguments passed to the logger.

    Example:
        >>> log.critical("System failure - cannot continue")
    """
    get_logger().critical(_append_log_path(msg, include_log_path), *args, **kwargs)

def success(msg, *args, **kwargs):
    """
    Log a SUCCESS level message (custom level 25).

    The SUCCESS level is between INFO and WARNING, used to highlight successful
    completion of major operations.

    Args:
        msg (str): The message to log.
        *args: Positional arguments for message formatting.
        **kwargs: Keyword arguments passed to the logger.

    Example:
        >>> log.success("Data extraction completed successfully")
        >>> log.success("Processed %d files", file_count)
    """
    get_logger().log(SUCCESS, msg, *args, **kwargs)

logging.Logger.success = lambda self, msg, *args, **kwargs: self.isEnabledFor(SUCCESS) and self._log(SUCCESS, msg, args, **kwargs)

