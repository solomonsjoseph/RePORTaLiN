"""
RePORTaLiN Utilities Package
=============================

Utility modules for clinical data processing: logging, de-identification, and privacy compliance.

This package provides cross-cutting functionality supporting the main data processing pipeline.

Public API
----------
Exports 10 logging functions via ``__all__`` for convenient access:

**Logging (from scripts.utils.logging):**
- ``get_logger``, ``setup_logging``, ``setup_logger`` (legacy), ``get_log_file_path``
- ``debug``, ``info``, ``warning``, ``error``, ``critical``, ``success``

**Specialized functionality (import from submodules):**
- ``scripts.utils.logging`` - Enhanced logging (11 exports)
- ``scripts.deidentify`` - De-identification engine (10 exports)
- ``scripts.utils.country_regulations`` - Privacy regulations (6 exports)

Usage
-----

Basic logging (from utils package)::

    from scripts.utils import get_logger, success
    logger = get_logger(__name__)
    success("Processing complete!")

Specialized features (from submodules)::

    from scripts.deidentify import deidentify_dataset
    from scripts.utils.country_regulations import get_supported_countries
    
    # See individual module documentation for complete examples

See Also
--------
- :mod:`scripts.utils.logging_system` - Logging utilities
- :mod:`scripts.deidentify` - De-identification
- :mod:`scripts.utils.country_regulations` - Privacy compliance
"""

from .logging_system import get_logger, setup_logging, setup_logger, get_log_file_path, debug, info, warning, error, critical, success
from __version__ import __version__

__all__ = ['get_logger', 'setup_logging', 'setup_logger', 'get_log_file_path', 'debug', 'info', 'warning', 'error', 'critical', 'success']
