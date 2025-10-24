__version__ module
==================

The ``__version__`` module serves as the single source of truth for RePORTaLiN's
version number. This ensures consistent version reporting across all components
of the application.

.. automodule:: __version__
   :members:
   :undoc-members:
   :show-inheritance:

Usage
-----

The version string can be imported and used in any Python code::

    from __version__ import __version__
    
    print(f"Running RePORTaLiN version {__version__}")

This module is automatically imported by:

- ``main.py`` - For command-line ``--version`` flag
- ``docs/sphinx/conf.py`` - For documentation version display
- ``scripts/__init__.py`` - For package version tracking
- ``scripts/utils/__init__.py`` - For utilities version tracking

Version Format
--------------

RePORTaLiN follows `Semantic Versioning 2.0.0 <https://semver.org/>`_:

**MAJOR.MINOR.PATCH**

- **MAJOR**: Incremented for incompatible API changes
- **MINOR**: Incremented for new features (backward compatible)
- **PATCH**: Incremented for bug fixes (backward compatible)

See Also
--------
- :doc:`../changelog` - Complete version history
- :mod:`main` - Main pipeline entry point
- :mod:`config` - Configuration module
