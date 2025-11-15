"""
Version Information for RePORTaLiN
===================================

Single source of truth for version number used across the project.

This module is imported by multiple components (setup.py, docs/conf.py, main.py,
and all package __init__.py files) to ensure consistent version reporting throughout
the application.

.. note::
   When bumping versions, update **only** the ``__version__`` string. The version
   tuple (``__version_info__``) is automatically derived, and the format is validated
   to ensure semantic versioning compliance.

Version Format Validation
--------------------------

.. versionadded:: 0.8.8

The module automatically validates that ``__version__`` follows semantic versioning
format (MAJOR.MINOR.PATCH) using regex pattern ``^\\d+\\.\\d+\\.\\d+$``.

**Valid formats:**
    - ``"1.0.0"`` ✅ (major release - breaking changes)
    - ``"0.9.0"`` ✅ (minor release - new features)
    - ``"0.8.11"`` ✅ (patch/fix release - bug fixes)

**Invalid formats** (raise ValueError at import time):
    - ``"0.8.8a"`` ❌ (alpha suffix not allowed)
    - ``"v0.8.8"`` ❌ (prefix not allowed)
    - ``"0.8"`` ❌ (must have three components)
    - ``"0.8.8-rc1"`` ❌ (release candidate suffix not allowed)

This validation catches typos early in development, before deployment.

Attributes
----------
__version__ : str
    Current semantic version following MAJOR.MINOR.PATCH format.
    
    - **MAJOR**: Incompatible API changes
    - **MINOR**: New features (backward compatible)
    - **PATCH**: Bug fixes (backward compatible)
    
    .. versionadded:: 0.8.8
       Added automatic validation to ensure version follows semantic versioning format.
       Invalid formats (e.g., "0.8.8a", "v0.8.8", "0.8") raise ValueError at import time.

__version_info__ : tuple[int, int, int]
    Version information as a tuple of integers (MAJOR, MINOR, PATCH).
    
    .. versionadded:: 0.8.8
       Auto-derived from ``__version__`` string to ensure consistency.
       Previously maintained manually, which risked version/version_info mismatch.
    
    This tuple is automatically calculated from ``__version__`` by splitting on '.'
    and converting to integers. This guarantees that ``__version__`` and 
    ``__version_info__`` are always synchronized, eliminating the need to update
    both values manually when bumping versions.

Version History
---------------
Recent versions (see docs/sphinx/changelog.rst for complete history):

- **0.8.5** (Oct 28, 2025): Complete API documentation and tmp/ cleanup
- **0.8.4** (Oct 28, 2025): Logging integration and import consistency fixes
- **0.8.3** (Oct 28, 2025): Project-wide documentation updates and Makefile enhancements
- **0.8.2** (Oct 28, 2025): Documentation redundancy removal and reorganization
- **0.8.1** (Oct 23, 2025): Enhanced version tracking and documentation
- **0.0.12** (Oct 2025): Added verbose logging, auto-rebuild docs, VerboseLogger class
- **0.0.11** (Oct 2025): Enhanced main.py with comprehensive docstring (162 lines)
- **0.0.10** (Oct 2025): Enhanced scripts/utils/__init__.py package API
- **0.0.9** (Oct 2025): Enhanced scripts/__init__.py with integration workflows
- **0.0.8** (Oct 2025): Enhanced load_dictionary.py with public API and algorithms
- **0.0.7** (Oct 2025): Enhanced extract_data.py with type hints and documentation
- **0.0.6** (Oct 2025): Enhanced deidentify.py with return type annotations
- **0.0.5** (Oct 2025): Enhanced country_regulations.py with public API
- **0.0.4** (Oct 2025): Enhanced logging.py with performance optimizations
- **0.0.3** (Oct 2025): Enhanced config.py with utility functions

See Also
--------
- :doc:`../docs/sphinx/changelog` - Complete version history with detailed changes
- :mod:`main` - Main pipeline entry point using this version
- :mod:`config` - Configuration module using this version

Usage
-----
Import and use the version string::

    from __version__ import __version__
    
    print(f"RePORTaLiN version {__version__}")
    # Output: RePORTaLiN version 0.8.8

Access from command line::

    $ python main.py --version
    RePORTaLiN 0.8.8

Version tuple is auto-derived from version string::

    from __version__ import __version__, __version_info__
    
    print(f"Version: {__version__}")
    # Output: Version: 0.8.8
    
    print(f"Version tuple: {__version_info__}")
    # Output: Version tuple: (0, 8, 8)
    
    # The tuple is automatically derived, so they're always in sync
    assert __version_info__ == tuple(map(int, __version__.split('.')))

Version format is validated at import time::

    # This would raise ValueError if uncommented:
    # __version__ = "0.8.8a"  # Invalid format
    # → ValueError: Invalid version format: 0.8.8a. 
    #   Must follow semantic versioning: MAJOR.MINOR.PATCH
"""

import re

__version__: str = "0.8.12"

# Validate semantic versioning format (MAJOR.MINOR.PATCH)
if not re.match(r'^\d+\.\d+\.\d+$', __version__):
    raise ValueError(
        f"Invalid version format: {__version__}. "
        f"Must follow semantic versioning: MAJOR.MINOR.PATCH"
    )

# Auto-derive version tuple from version string to ensure consistency
__version_info__: tuple[int, int, int] = tuple(map(int, __version__.split('.')))

__all__ = ['__version__', '__version_info__']
