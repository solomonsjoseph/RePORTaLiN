scripts.utils package
=====================

.. module:: scripts.utils
   :synopsis: Utility modules for RePORTaLiN project

**For Developers:** This package contains utility modules that provide shared functionality
across the RePORTaLiN project.

Overview
--------

The ``scripts.utils`` package provides reusable utility components for:

- **Centralized Logging**: Structured logging with file output and custom levels
- **Country Regulations**: Country-specific de-identification rules and compliance
- **Documentation Maintenance**: Unified quality checking, style validation, and build system

**Package Structure**:

.. code-block:: text

   scripts/utils/
   ├── __init__.py                          # Package initialization and exports
   ├── logging.py                           # Centralized logging system
   ├── country_regulations.py               # Country-specific regulations
   ├── migrate_data_structure.py            # Data structure migration system
   ├── doc_maintenance_toolkit.py           # ✅ Unified documentation maintenance tool
   ├── smart-commit.sh                      # Git commit with version bumping
   └── (old doc scripts archived to tmp/)   # See tmp/archive_old_doc_scripts/README.rst

Modules
-------

Core Utilities
~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated
   
   scripts.utils.logging
   scripts.utils.country_regulations
   scripts.utils.migrate_data_structure

Documentation Tools
~~~~~~~~~~~~~~~~~~~

.. important::
   **Consolidation Complete (2025-10-30)**: All documentation maintenance tools
   have been unified into :doc:`doc_maintenance_toolkit`.
   
   **Old scripts ARCHIVED**: The following scripts have been moved to
   ``tmp/archive_old_doc_scripts/`` and are **no longer in active use**:
   
   - ❌ ``check_docs_style.sh`` → Use ``--mode style``
   - ❌ ``check_documentation_quality.py`` → Use ``--mode quality``
   - ❌ ``doc_maintenance_commands.sh`` → Use CLI commands
   
   See the migration guide in :doc:`doc_maintenance_toolkit` for command equivalents.

Logging Module
^^^^^^^^^^^^^^

:mod:`scripts.utils.logging` - Centralized logging system with custom SUCCESS level.

**Key Features**:

- Custom SUCCESS log level (severity between INFO and WARNING)
- File-based logging with automatic log file creation
- Console and file output with configurable formatting
- Color-coded console output for better readability
- Performance optimizations for high-volume logging

**Common Usage**:

.. code-block:: python

   from scripts.utils import logging as log
   
   logger = log.get_logger(__name__)
   logger.info("Processing data...")
   logger.success("Operation completed successfully!")
   logger.warning("Potential issue detected")
   logger.error("Operation failed")

**Quick Access Functions**:

.. code-block:: python

   from scripts.utils.logging import info, success, warning, error
   
   info("Starting process...")
   success("Process completed!")

See :doc:`scripts.utils.logging` for complete documentation.

Migration Module
^^^^^^^^^^^^^^^^

:mod:`scripts.utils.migrate_data_structure` - Data structure migration system.

**Key Features**:

- Dynamic study name detection from dataset folders
- Automatic backup creation with timestamps
- Dry-run mode for safe testing
- Comprehensive pre and post-migration validation
- Detailed migration logging and audit trails
- Cross-platform compatibility (macOS, Linux, Windows)

**Common Usage**:

.. code-block:: python

   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Test with dry-run first
   manager = DataMigrationManager(dry_run=True)
   manager.run_migration()
   
   # Run actual migration
   manager = DataMigrationManager(dry_run=False)
   success = manager.run_migration()

**Command-Line Usage**:

.. code-block:: bash

   # Dry-run (test mode)
   python -m scripts.utils.migrate_data_structure --dry-run
   
   # Actual migration
   python -m scripts.utils.migrate_data_structure

**Quick Access**:

- **User Guide**: :doc:`/user_guide/data_migration`
- **Developer Guide**: :doc:`/developer_guide/migration_system`
- **API Reference**: :doc:`scripts.utils.migrate_data_structure`

See :doc:`scripts.utils.migrate_data_structure` for complete API documentation.

Country Regulations Module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

:mod:`scripts.utils.country_regulations` - Country-specific de-identification rules.

**Key Features**:

- GDPR compliance for European Union countries
- HIPAA compliance for United States
- PDPA compliance for India
- Custom regex patterns for each country
- Extensible framework for adding new countries

**Common Usage**:

.. code-block:: python

   from scripts.utils.country_regulations import get_country_config
   
   config = get_country_config('India')
   print(f"PII fields: {config.pii_fields}")
   print(f"Date format: {config.date_format}")

See :doc:`scripts.utils.country_regulations` for complete documentation.

Documentation Maintenance Toolkit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:doc:`doc_maintenance_toolkit` - Unified documentation quality, style, and build system.

**Key Features**:

- Style compliance checking (fast, for pre-commit hooks)
- Comprehensive quality analysis (version refs, redundancy, cross-refs)
- Sphinx documentation building
- Full maintenance suite combining all checks
- Centralized logging to ``.logs/`` directory
- Multiple output modes (quiet, normal, verbose)

**Common Usage**:

.. code-block:: bash

   # Quick style check (for pre-commit hooks)
   python3 scripts/utils/doc_maintenance_toolkit.py --mode style
   
   # Comprehensive quality analysis
   python3 scripts/utils/doc_maintenance_toolkit.py --mode quality --verbose
   
   # Build documentation
   python3 scripts/utils/doc_maintenance_toolkit.py --mode build --open
   
   # Full maintenance suite
   python3 scripts/utils/doc_maintenance_toolkit.py --mode full

**Replaces** (archived to ``tmp/archive_old_doc_scripts/``):

- ``check_docs_style.sh`` - Shell-based style checker (**ARCHIVED**)
- ``check_documentation_quality.py`` - Python quality checker (**ARCHIVED**)
- ``doc_maintenance_commands.sh`` - Build and utility commands (**ARCHIVED**)

See :doc:`doc_maintenance_toolkit` for complete documentation and migration guide.

.. warning::
   **DEPRECATED**: The old documentation maintenance scripts have been **archived**
   to ``tmp/archive_old_doc_scripts/`` and should no longer be used.  
   
   Use :doc:`doc_maintenance_toolkit` instead. See the migration guide for
   command equivalents.

Package API
-----------

Exported Symbols
~~~~~~~~~~~~~~~~

The package ``__init__.py`` exports commonly used functions for convenience:

.. code-block:: python

   from scripts.utils import (
       # Logging functions
       get_logger, setup_logger, get_log_file_path,
       debug, info, warning, error, critical, success,
       
       # Version info
       __version__
   )

**Example**:

.. code-block:: python

   from scripts.utils import info, success, get_logger
   
   # Quick logging
   info("Starting data extraction...")
   
   # Custom logger
   logger = get_logger('my_module')
   logger.debug("Detailed information")
   success("Extraction completed!")

Module Imports
~~~~~~~~~~~~~~

Each utility module can be imported individually:

.. code-block:: python

   # Import specific module
   from scripts.utils import logging
   from scripts.utils import country_regulations
   
   # Import specific classes/functions
   from scripts.utils.logging import VerboseLogger
   from scripts.utils.country_regulations import CountryConfig, get_country_config

Best Practices
--------------

When to Use What
~~~~~~~~~~~~~~~~

**For Logging**:

- **Simple logging**: Use quick access functions (``info()``, ``success()``)
- **Module-specific**: Use ``get_logger(__name__)`` for proper logger hierarchy
- **Custom formatting**: Use ``setup_logger()`` with custom configuration

**For Country Regulations**:

- **Single country**: Use ``get_country_config('CountryName')``
- **Multiple countries**: Load configs in loop or use dictionary comprehension
- **Custom rules**: Extend ``CountryConfig`` dataclass

**For Documentation Quality**:

- **Daily dev**: Use ``doc_maintenance_toolkit.py --mode style`` (fast, ~10s)
- **Pre-commit**: Use ``doc_maintenance_toolkit.py --mode style --quick``
- **Full check**: Use ``doc_maintenance_toolkit.py --mode quality`` (comprehensive)
- **Quarterly**: Use ``doc_maintenance_toolkit.py --mode full`` via GitHub Actions

Logging Best Practices
~~~~~~~~~~~~~~~~~~~~~~~

**DO**:

.. code-block:: python

   # Use appropriate log levels
   logger.debug("Detailed debugging info")      # For development
   logger.info("Normal operation")              # Progress updates
   logger.success("Operation completed")        # Successful completion
   logger.warning("Something unexpected")       # Potential issues
   logger.error("Operation failed", exc_info=True)  # Errors
   
   # Include context
   logger.info(f"Processing file: {filename}")
   logger.error(f"Failed to process {filename}: {error}")

**DON'T**:

.. code-block:: python

   # Don't log sensitive data
   logger.info(f"Password: {password}")  # BAD!
   
   # Don't use print() in library code
   print("Processing...")  # Use logger.info() instead
   
   # Don't log at wrong level
   logger.error("File processed successfully")  # Should be success/info

Country Regulations Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DO**:

.. code-block:: python

   # Get config once, reuse
   config = get_country_config('India')
   for record in records:
       deidentify(record, config)
   
   # Validate country name
   try:
       config = get_country_config(country_name)
   except ValueError:
       logger.error(f"Unknown country: {country_name}")
   
   # Use config attributes explicitly
   date_format = config.date_format
   pii_fields = config.pii_fields

**DON'T**:

.. code-block:: python

   # Don't get config repeatedly
   for record in records:
       config = get_country_config('India')  # Inefficient!
   
   # Don't assume country exists
   config = get_country_config(user_input)  # May raise ValueError
   
   # Don't hardcode values
   date_format = '%d-%m-%Y'  # Use config.date_format instead

Documentation Quality Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DO**:

.. code-block:: bash

   # Run before committing (fast)
   python3 scripts/utils/doc_maintenance_toolkit.py --mode style
   
   # Comprehensive quality review
   python3 scripts/utils/doc_maintenance_toolkit.py --mode quality > review.txt
   
   # Full maintenance suite
   python3 scripts/utils/doc_maintenance_toolkit.py --mode full
   
   # Integrate into CI/CD
   # See doc_maintenance_toolkit documentation

**DON'T**:

.. code-block:: bash

   # Don't skip quality checks
   # They catch issues early
   
   # Don't ignore all warnings
   # Review and fix legitimate issues
   
   # Don't run only at release time
   # Integrate into regular workflow

Development Guidelines
----------------------

Adding New Utilities
~~~~~~~~~~~~~~~~~~~~

When adding a new utility module to ``scripts/utils/``:

1. **Create the module file** with proper docstring:

   .. code-block:: python
   
      """
      Module Name - Brief Description
      
      Detailed description of what this module does and why it exists.
      """

2. **Follow naming conventions**:

   - Use ``snake_case`` for filenames
   - Use descriptive names (e.g., ``data_validator.py``, not ``utils2.py``)

3. **Export public API** in ``__init__.py``:

   .. code-block:: python
   
      from .new_module import public_function, PublicClass

4. **Add documentation** in ``docs/sphinx/api/``:

   - Create ``scripts.utils.new_module.rst``
   - Follow existing documentation patterns

5. **Add tests** (when test framework exists):

   .. code-block:: python
   
      # tests/test_utils_new_module.py
      def test_public_function():
          assert public_function() == expected_result

Module Dependencies
~~~~~~~~~~~~~~~~~~~

**Internal Dependencies**:

.. code-block:: python

   # scripts.utils modules can depend on:
   - Standard library (always available)
   - __version__.py (for version info)
   - Other scripts.utils modules (with care to avoid circular imports)

**External Dependencies**:

Minimize external dependencies in utility modules. If required:

1. Add to ``requirements.txt``
2. Document in module docstring
3. Handle import errors gracefully:

   .. code-block:: python
   
      try:
          import optional_package
          HAS_OPTIONAL = True
      except ImportError:
          HAS_OPTIONAL = False
          # Provide fallback or raise informative error

Avoiding Circular Imports
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``scripts/utils/logging.py`` shadows Python's ``logging`` module.

**Solution** (when importing standard ``logging`` elsewhere):

.. code-block:: python

   # Option 1: Use absolute import
   from __future__ import absolute_import
   import logging as std_logging
   
   # Option 2: Manipulate sys.path
   import sys
   script_dir = str(Path(__file__).parent)
   if script_dir in sys.path:
       sys.path.remove(script_dir)
   import logging
   
   # Option 3: Import from centralized wrapper
   from scripts.utils import logging as log  # Use wrapper

**Best Practice**: Consider renaming ``scripts/utils/logging.py`` to ``scripts/utils/log_utils.py``
to avoid shadowing in future refactoring.

Testing
-------

Unit Testing
~~~~~~~~~~~~

When test framework is added:

.. code-block:: python

   # tests/test_utils_logging.py
   from scripts.utils import logging as log
   
   def test_get_logger():
       logger = log.get_logger('test')
       assert logger is not None
       assert logger.name == 'test'
   
   def test_success_level():
       assert hasattr(log, 'SUCCESS')
       assert log.SUCCESS > log.logging.INFO

Integration Testing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/test_utils_integration.py
   def test_logging_with_country_regulations():
       from scripts.utils import logging as log
       from scripts.utils.country_regulations import get_country_config
       
       logger = log.get_logger(__name__)
       config = get_country_config('India')
       logger.info(f"Loaded config for India: {len(config.pii_fields)} PII fields")

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Import Error: "Cannot import name 'logging'"**

**Cause**: Circular import or shadowing issue.

**Solution**:

.. code-block:: python

   # Instead of:
   import logging  # May find scripts/utils/logging.py
   
   # Use:
   from scripts.utils import logging as log

**AttributeError: "module 'logging' has no attribute 'addLevelName'"**

**Cause**: Local ``logging.py`` module is shadowing Python's standard ``logging``.

**Solution**: See "Avoiding Circular Imports" section above.

**ValueError: "Unknown country"**

**Cause**: Country name not in supported countries list.

**Solution**:

.. code-block:: python

   from scripts.utils.country_regulations import get_country_config
   
   try:
       config = get_country_config(country_name)
   except ValueError as e:
       print(f"Error: {e}")
       print("Supported countries: India, United States, European Union")

See Also
--------

Related Documentation
~~~~~~~~~~~~~~~~~~~~~

- :doc:`scripts.utils.logging` - Logging module detailed docs
- :doc:`scripts.utils.country_regulations` - Country regulations detailed docs
- :doc:`doc_maintenance_toolkit` - Documentation maintenance toolkit (NEW)
- :doc:`../developer_guide/architecture` - Overall project architecture
- :doc:`../developer_guide/extending` - Extending the project

Related Modules
~~~~~~~~~~~~~~~

- :mod:`config` - Project configuration management
- :mod:`main` - Main pipeline orchestrator
- :mod:`scripts.deidentify` - De-identification implementation

Version History
---------------

.. versionadded:: 0.0.3
   Initial ``scripts.utils`` package with logging and country regulations modules.

.. versionadded:: 0.8.2
   Added ``check_documentation_quality.py`` for automated quality checks.

.. versionchanged:: 0.8.4
   Enhanced logging integration and resolved circular import issues.

.. versionadded:: 0.0.13
   **Documentation Consolidation**: Added unified ``doc_maintenance_toolkit.py`` 
   consolidating ``check_docs_style.sh``, ``check_documentation_quality.py``, 
   and ``doc_maintenance_commands.sh`` into single tool. Old scripts archived for reference.

Submodules
----------

.. toctree::
   :maxdepth: 1

   scripts.utils.logging
   scripts.utils.country_regulations
   doc_maintenance_toolkit

Module Contents
---------------

.. automodule:: scripts.utils
   :members:
   :undoc-members:
   :show-inheritance:
   :imported-members:
