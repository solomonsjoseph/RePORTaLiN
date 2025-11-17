"""Enhanced centralized logging module with organized folder structure."""

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
    """Enhanced formatter with SUCCESS level support and optional colors."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with proper SUCCESS level handling."""
        if record.levelno == SUCCESS:
            record.levelname = "SUCCESS"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (monitoring tools integration)."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
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
    """Determine log category (folder) based on module name."""
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
    """Get the log directory path for a given category."""
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
    """Set up centralized logging with organized folder structure and rotation."""
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
    """Reset logging configuration."""
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
    """Legacy function name for backward compatibility."""
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
    """
    Get a logger instance."""
    if _logger is None:
        setup_logging()
    
    if name is None:
        return _logger
    
    # Return child logger for module-specific logging
    return logging.getLogger(f'reportalin.{name}')


def get_log_file_path() -> Optional[str]:
    """Get the path to the current log file."""
    return _log_file_path


def cleanup_old_logs(
    max_age_days: Optional[int] = None,
    max_files: Optional[int] = None,
    log_dir: Optional[Path] = None,
    dry_run: bool = False,
    recursive: bool = True,
    pattern: str = "*.log"
) -> Dict[str, Any]:
    """Clean up old log files from the log directory."""
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
    """Helper to append log file path to messages."""
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


def exception(msg: str, *args: Any, include_log_path: bool = True, **kwargs: Any) -> None:
    """Log an exception with full stack trace."""
    kwargs.setdefault('exc_info', True)
    get_logger().error(_append_log_path(msg, include_log_path), *args, **kwargs)


# Add success method to Logger class
def _success_method(self: logging.Logger, msg: str, *args: Any, **kwargs: Any) -> None:
    """Custom success logging method for Logger instances."""
    if self.isEnabledFor(SUCCESS):
        self.log(SUCCESS, msg, *args, **kwargs)


logging.Logger.success = _success_method  # type: ignore[attr-defined]


# ============================================================================
# Decorators and Context Managers
# ============================================================================

def log_errors(logger_name: Optional[str] = None, reraise: bool = True):
    """Decorator to automatically log exceptions with full stack trace."""
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
    """Decorator to automatically log function execution time."""
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
    """Context manager to log execution time of a code block."""
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
    """Centralized verbose logging for detailed output in DEBUG mode."""
    
    def __init__(self, logger_module: types.ModuleType) -> None:
        """Initialize with logger module."""
        self.log = logger_module
        self._indent = 0
    
    def __call__(self, message: str) -> None:
        """Allow VerboseLogger to be called as a simple function."""
        if self._is_verbose():
            self.log.debug(message)
    
    def _is_verbose(self) -> bool:
        """Check if verbose (DEBUG) logging is enabled."""
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
        """Log with tree-view formatting."""
        if self._is_verbose():
            try:
                indent = "  " * self._indent
                self.log.debug(f"{indent}{prefix}{message}")
            except Exception:
                # Silently ignore if logging fails during import
                pass
    
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
        try:
            self._log_tree("│  ", message)
        except Exception:
            pass
    
    def metric(self, label: str, value: Any) -> None:
        """Log a metric/statistic."""
        try:
            self._log_tree("├─ ", f"{label}: {value}")
        except Exception:
            pass
    
    def timing(self, operation: str, seconds: float) -> None:
        """Log operation timing."""
        try:
            self._log_tree("├─ ", f"⏱ {operation}: {seconds:.2f}s")
        except Exception:
            pass
    
    def items_list(self, label: str, items: list, max_show: int = 5) -> None:
        """Log a list of items with truncation if too long."""
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
    """Get or create the global VerboseLogger instance."""
    global _verbose_logger
    if _verbose_logger is None:
        _verbose_logger = VerboseLogger(sys.modules[__name__])
    return _verbose_logger
