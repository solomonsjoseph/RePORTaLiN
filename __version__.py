"""
Version Information for RePORTaLiN
===================================

Single source of truth for version number used across the project.

This module is imported by multiple components (setup.py, docs/conf.py, main.py,
and all package __init__.py files) to ensure consistent version reporting throughout
the application.

.. note::
   When bumping versions, update **only this file**. The change will automatically
   propagate to all components that import from here.

Attributes
----------
__version__ : str
    Current semantic version following MAJOR.MINOR.PATCH format.
    
    - **MAJOR**: Incompatible API changes
    - **MINOR**: New features (backward compatible)
    - **PATCH**: Bug fixes (backward compatible)

Version History
---------------
Recent versions (see docs/sphinx/changelog.rst for complete history):

- **0.8.1** (Oct 23, 2025): Enhanced version tracking and documentation
- **0.0.12** (Oct 2025): Added verbose logging, auto-rebuild docs, VerboseLogger class
- **0.0.11** (Oct 2025): Enhanced main.py with comprehensive docstring (162 lines)
- **0.0.10** (Oct 2025): Enhanced scripts/utils/__init__.py package API
- **0.0.9** (Oct 2025): Enhanced scripts/__init__.py with integration examples
- **0.0.8** (Oct 2025): Enhanced load_dictionary.py with public API and algorithms
- **0.0.7** (Oct 2025): Enhanced extract_data.py with type hints and examples
- **0.0.6** (Oct 2025): Enhanced deidentify.py with return type annotations
- **0.0.5** (Oct 2025): Enhanced country_regulations.py with public API
- **0.0.4** (Oct 2025): Enhanced logging.py with performance optimizations
- **0.0.3** (Oct 2025): Enhanced config.py with utility functions

See Also
--------
- :doc:`../docs/sphinx/changelog` - Complete version history with detailed changes
- :mod:`main` - Main pipeline entry point using this version
- :mod:`config` - Configuration module using this version

Examples
--------
Import and use the version string::

    from __version__ import __version__
    
    print(f"RePORTaLiN version {__version__}")
    # Output: RePORTaLiN version 0.8.1

Access from command line::

    $ python main.py --version
    RePORTaLiN 0.8.1
"""

__version__ = "0.8.1"

__all__ = ['__version__']
