"""Utility modules for clinical data processing and infrastructure.

This subpackage provides cross-cutting concerns and infrastructure utilities
used throughout the RePORTaLiN pipeline. It includes centralized logging,
country-specific regulations, documentation maintenance tools, and data
migration utilities.

Subpackage Architecture:
    **Logging Infrastructure** (logging_system.py):
        Centralized logging with dual output (console + file), color-coded
        severity levels, and configurable verbosity modes.
    
    **Country Regulations** (country_regulations.py):
        Country-specific PHI/PII patterns (Aadhaar, SSN, CURP, etc.) with
        validation regex for de-identification operations.
    
    **Documentation Tools** (doc_maintenance_toolkit.py):
        Automated documentation maintenance, docstring generation helpers,
        and Sphinx integration utilities.
    
    **Data Migration** (migrate_data_structure.py):
        Version-specific data structure migration logic for upgrading
        between RePORTaLiN versions without data loss.

Public API:
    The utils package exposes the centralized logging system at the top level
    for easy access from any module:
    
    **Logging Functions**:
        - setup_logger: Configure logger instance
        - get_logger: Retrieve existing logger
        - setup_logging: Legacy setup function (deprecated)
        - get_log_file_path: Get path to log file
        - debug, info, warning, error, critical, success: Direct log functions
    
    **Note**: Country regulations, doc tools, and migration utilities must
    be imported explicitly from their respective modules.

Module Attributes:
    __version__ (str): Current package version
    __all__ (list): Exported logging functions

Example:
    >>> # Import logging utilities
    >>> from scripts.utils import setup_logger, info, error
    >>> import logging
    >>> 
    >>> # Setup centralized logger
    >>> setup_logger(name='my_pipeline', log_level=logging.INFO, simple_mode=True)
    >>> 
    >>> # Log messages
    >>> info("Starting data processing...")  # doctest: +SKIP
    >>> error("File not found: data.xlsx")  # doctest: +SKIP
    >>> 
    >>> # Import country regulations explicitly
    >>> from scripts.utils.country_regulations import get_country_patterns
    >>> patterns = get_country_patterns('IN')  # doctest: +SKIP

Notes:
    - Only logging functions are in __all__ (most commonly used)
    - Other utilities require explicit imports from their modules
    - All utilities share the same logger via logging_system
    - Country patterns are loaded lazily on first access

See Also:
    scripts.utils.logging_system: Centralized logging implementation
    scripts.utils.country_regulations: Country-specific patterns
    main.py: Sets up logging using setup_logger()
"""

from .logging_system import get_logger, setup_logging, setup_logger, get_log_file_path, debug, info, warning, error, critical, success
from __version__ import __version__

__all__ = ['get_logger', 'setup_logging', 'setup_logger', 'get_log_file_path', 'debug', 'info', 'warning', 'error', 'critical', 'success']
