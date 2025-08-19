"""
Centralized logging module for the RePORTaLiN project.
This module provides a common logging setup for all script files.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Define a custom SUCCESS log level (between INFO and WARNING)
SUCCESS = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(SUCCESS, "SUCCESS")

# Global logger object
_logger = None
_log_file_path = None  # Store the log file path for reference

# Custom formatter to properly display SUCCESS level
class CustomFormatter(logging.Formatter):
    """Custom formatter that correctly shows SUCCESS level in logs"""
    
    def format(self, record):
        # Save original levelname
        original_levelname = record.levelname
        
        # Apply custom formatting for SUCCESS level
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        
        # Format the record
        result = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return result

def setup_logger(name="reportalin", log_level=logging.INFO):
    """
    Set up the central logger for the project.
    
    Args:
        name (str): The name of the logger
        log_level (int): The logging level (e.g., logging.INFO, logging.DEBUG)
        
    Returns:
        logging.Logger: Configured logger object
    """
    global _logger, _log_file_path
    
    # If logger is already set up, return it
    if _logger is not None:
        return _logger
    
    # Create logger
    _logger = logging.getLogger(name)
    _logger.setLevel(log_level)
    
    # Clear any existing handlers to prevent duplicates
    if _logger.handlers:
        _logger.handlers.clear()
    
    # Create .logs directory in parent directory if it doesn't exist
    project_root = Path(os.path.abspath(__file__)).parents[2]  # Go up 2 levels from utils/logging_utils.py
    logs_dir = project_root / ".logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create a log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{name}_{timestamp}.log"
    _log_file_path = str(log_file)  # Store for reference
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create console handler with higher level for less verbosity
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(min(SUCCESS, logging.WARNING))  # SUCCESS and above go to console
    
    # Create formatters with custom formatter class
    file_formatter = CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = CustomFormatter('%(levelname)s: %(message)s')
    
    # Add formatters to handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    # Log setup completion to file only
    _logger.info(f"Logging initialized. Log file: {log_file}")
    
    return _logger

def get_logger():
    """
    Get the configured logger or set it up if not already done.
    
    Returns:
        logging.Logger: The configured logger
    """
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger

def get_log_file_path():
    """
    Get the path to the current log file.
    
    Returns:
        str: The path to the log file or None if logger not initialized
    """
    global _log_file_path
    return _log_file_path

# Convenience functions that map directly to logger methods
def debug(msg, *args, **kwargs):
    """Log a debug message"""
    get_logger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    """Log an info message"""
    get_logger().info(msg, *args, **kwargs)

def warning(msg, *args, include_log_path=False, **kwargs):
    """
    Log a warning message
    
    Args:
        msg: The warning message
        include_log_path: If True, append log file location to the message
    """
    if include_log_path and get_log_file_path():
        msg = f"{msg}\nFor more details, check the log file at: {get_log_file_path()}"
    get_logger().warning(msg, *args, **kwargs)

def error(msg, *args, include_log_path=True, **kwargs):
    """
    Log an error message
    
    Args:
        msg: The error message
        include_log_path: If True, append log file location to the message (default: True)
    """
    if include_log_path and get_log_file_path():
        msg = f"{msg}\nFor more details, check the log file at: {get_log_file_path()}"
    get_logger().error(msg, *args, **kwargs)

def critical(msg, *args, include_log_path=True, **kwargs):
    """
    Log a critical message
    
    Args:
        msg: The critical error message
        include_log_path: If True, append log file location to the message (default: True)
    """
    if include_log_path and get_log_file_path():
        msg = f"{msg}\nFor more details, check the log file at: {get_log_file_path()}"
    get_logger().critical(msg, *args, **kwargs)

def success(msg, *args, **kwargs):
    """
    Log a success message at the custom SUCCESS level.
    This will be shown in the console with a SUCCESS prefix.
    """
    logger = get_logger()
    # Use the custom SUCCESS level
    logger.log(SUCCESS, msg, *args, **kwargs)

# Add the success method to the Logger class for convenience
def _success_method(self, msg, *args, **kwargs):
    """Success level logging method for Logger instances"""
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, msg, args, **kwargs)

# Add the success method to the Logger class
logging.Logger.success = _success_method
