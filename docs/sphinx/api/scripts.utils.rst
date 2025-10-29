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
- **Documentation Quality**: Automated documentation validation and quality checks

**Package Structure**:

.. code-block:: text

   scripts/utils/
   ├── __init__.py                          # Package initialization and exports
   ├── logging.py                           # Centralized logging system
   ├── country_regulations.py               # Country-specific regulations
   ├── check_documentation_quality.py       # Documentation quality checker
   ├── check_docs_style.sh                  # Shell-based style checker
   └── doc_maintenance_commands.sh          # Maintenance convenience functions

Modules
-------

Core Utilities
~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated
   
   scripts.utils.logging
   scripts.utils.country_regulations
   scripts.utils.check_documentation_quality

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

Documentation Quality Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:mod:`scripts.utils.check_documentation_quality` - Automated documentation validation.

**Key Features**:

- Version reference consistency checks
- File size monitoring
- Redundant content detection
- Cross-reference validation
- Style compliance verification
- Comprehensive reporting

**Common Usage**:

.. code-block:: bash

   # Command-line execution
   python3 scripts/utils/check_documentation_quality.py
   
   # Makefile integration
   make docs-quality

See :doc:`scripts.utils.check_documentation_quality` for complete documentation.

Shell Utilities
~~~~~~~~~~~~~~~

Documentation Style Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``scripts/utils/check_docs_style.sh`` - Fast shell-based style compliance checker.

**Purpose**: Quick validation (~10 seconds) for daily development.

**Checks**:

- User guide files have ``**For Users:**`` header
- Developer guide files have ``**For Developers:**`` header
- No technical jargon in user guide
- Sphinx build succeeds without warnings

**Usage**:

.. code-block:: bash

   ./scripts/utils/check_docs_style.sh
   # or
   make docs-check

Documentation Maintenance Commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``scripts/utils/doc_maintenance_commands.sh`` - Convenience shell functions.

**Functions**:

- ``check_version`` - Display current version
- ``quick_commit <msg>`` - Commit with automatic version bump
- ``full_maintenance`` - Complete maintenance workflow

**Usage**:

.. code-block:: bash

   source scripts/utils/doc_maintenance_commands.sh
   check_version
   quick_commit "docs: update getting started guide"

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

- **Daily dev**: Use ``check_docs_style.sh`` (fast)
- **Pre-commit**: Use ``check_documentation_quality.py`` (comprehensive)
- **Quarterly**: Automated via GitHub Actions

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

   # Run before committing
   make docs-quality
   
   # Review warnings periodically
   python3 scripts/utils/check_documentation_quality.py > review.txt
   
   # Integrate into CI/CD
   # See .github/workflows/docs-quality-check.yml

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
- :doc:`scripts.utils.check_documentation_quality` - Quality checker detailed docs
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

Submodules
----------

.. toctree::
   :maxdepth: 1

   scripts.utils.logging
   scripts.utils.country_regulations
   scripts.utils.check_documentation_quality

Module Contents
---------------

.. automodule:: scripts.utils
   :members:
   :undoc-members:
   :show-inheritance:
   :imported-members:
