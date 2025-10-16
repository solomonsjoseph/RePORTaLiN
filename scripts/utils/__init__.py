"""
RePORTaLiN Utilities Package
=============================

Utility modules for clinical data processing: logging, de-identification, and privacy compliance.

This package provides cross-cutting functionality supporting the main data processing pipeline.

Public API
----------
Exports 9 logging functions via ``__all__`` for convenient access:

**Logging (from scripts.utils.logging):**
- ``get_logger``, ``setup_logger``, ``get_log_file_path``
- ``debug``, ``info``, ``warning``, ``error``, ``critical``, ``success``

**Specialized functionality (import from submodules):**
- ``scripts.utils.logging`` - Enhanced logging (11 exports)
- ``scripts.utils.deidentify`` - De-identification engine (10 exports)
- ``scripts.utils.country_regulations`` - Privacy regulations (6 exports)

Usage
-----

Basic logging (from utils package)::

    from scripts.utils import get_logger, success
    logger = get_logger(__name__)
    success("Processing complete!")

Specialized features (from submodules)::

    from scripts.utils.deidentify import deidentify_dataset
    from scripts.utils.country_regulations import get_supported_countries
    
    # See individual module documentation for complete examples

See Also
--------
- :mod:`scripts.utils.logging` - Logging utilities
- :mod:`scripts.utils.deidentify` - De-identification
- :mod:`scripts.utils.country_regulations` - Privacy compliance
"""

from .logging import get_logger, setup_logger, get_log_file_path, debug, info, warning, error, critical, success

__all__ = ['get_logger', 'setup_logger', 'get_log_file_path', 'debug', 'info', 'warning', 'error', 'critical', 'success']
__version__ = '0.0.10'
