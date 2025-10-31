.. _doc_maintenance_toolkit:

==========================================
Documentation Maintenance Toolkit API
==========================================

**For Developers:**

This module provides a unified, comprehensive system for documentation maintenance,
quality checking, and building operations. It consolidates functionality from
multiple scripts into a single, well-structured Python tool.

.. module:: scripts.utils.doc_maintenance_toolkit
   :synopsis: Unified documentation maintenance and quality assurance system

.. moduleauthor:: RePORTaLiN Development Team

Overview
========

The Documentation Maintenance Toolkit is a consolidation of three separate scripts:

* ``check_docs_style.sh`` - Style compliance checking
* ``check_documentation_quality.py`` - Comprehensive quality analysis  
* ``doc_maintenance_commands.sh`` - Build and utility functions

This unified approach eliminates code duplication, provides consistent error handling,
and offers a more maintainable codebase.

Quick Start
===========

Basic usage examples::

    # Style compliance check (fast - for pre-commit hooks)
    python scripts/utils/doc_maintenance_toolkit.py --mode style
    
    # Comprehensive quality analysis
    python scripts/utils/doc_maintenance_toolkit.py --mode quality
    
    # Build documentation
    python scripts/utils/doc_maintenance_toolkit.py --mode build
    
    # Full maintenance suite
    python scripts/utils/doc_maintenance_toolkit.py --mode full

Migration from Old Scripts
===========================

This toolkit consolidates three previously separate scripts. If you were using
the old scripts, here's how to migrate:

Command Equivalents
-------------------

**Style Checking**::

    # Old
    bash scripts/utils/check_docs_style.sh
    
    # New
    python3 scripts/utils/doc_maintenance_toolkit.py --mode style

**Quality Checking**::

    # Old
    python3 scripts/utils/check_documentation_quality.py
    
    # New
    python3 scripts/utils/doc_maintenance_toolkit.py --mode quality

**Build Documentation**::

    # Old
    bash scripts/utils/doc_maintenance_commands.sh build
    
    # New
    python3 scripts/utils/doc_maintenance_toolkit.py --mode build

**Full Maintenance**::

    # Old (run all scripts separately)
    bash scripts/utils/check_docs_style.sh
    python3 scripts/utils/check_documentation_quality.py
    bash scripts/utils/doc_maintenance_commands.sh build
    
    # New (single command)
    python3 scripts/utils/doc_maintenance_toolkit.py --mode full

Key Improvements
----------------

* **Unified Interface**: One command instead of three separate scripts
* **Consistent Logging**: All logs centralized in ``.logs/`` directory
* **Better Error Handling**: Robust Python error handling vs shell scripts
* **Type Safety**: Type hints for improved code quality
* **Enhanced Options**: More control with ``--quick``, ``--quiet``, ``--verbose``
* **Exit Codes**: Standardized exit codes (0=success, 1=warnings, 2=errors)
* **Maintainability**: Single codebase easier to enhance and debug

Backward Compatibility
----------------------

.. note::
   **Old scripts are archived** in ``scripts/utils/archived_*/`` for reference
   and emergency rollback. They are no longer actively maintained.
   
   All functionality from the old scripts has been preserved in the new toolkit.
   No breaking changes have been introduced.

Common Migration Scenarios
---------------------------

**Pre-Commit Hooks**::

    # Update your .git/hooks/pre-commit
    # Old
    bash scripts/utils/check_docs_style.sh || exit 1
    
    # New
    python3 scripts/utils/doc_maintenance_toolkit.py --mode style || exit 1

**CI/CD Pipelines**::

    # Update your .github/workflows/*.yml
    # Old
    - name: Check documentation quality
      run: python3 scripts/utils/check_documentation_quality.py
    
    # New
    - name: Check documentation quality
      run: python3 scripts/utils/doc_maintenance_toolkit.py --mode quality

**Makefile Targets**::

    # Update your Makefile
    # Old
    docs-quality:
        @python3 scripts/utils/check_documentation_quality.py
    
    # New
    docs-quality:
        @python3 scripts/utils/doc_maintenance_toolkit.py --mode quality

Troubleshooting Migration
--------------------------

**Import Errors**:
    The new toolkit properly handles the logging module import to avoid
    shadowing issues. If you encounter import errors, ensure you're using
    Python 3.7+.

**Different Output Format**:
    The output format is functionally identical but may have minor cosmetic
    differences (file paths shown as basenames, alphabetical sorting). These
    are intentional improvements for cleaner output.

**Log Location**:
    All logs now go to ``.logs/`` directory by default. Update any scripts
    that parse log files to use the new location.

**Exit Codes**:
    Exit codes are now standardized: 0 (success), 1 (warnings), 2 (errors).
    Update any automation that relies on specific exit codes.

Operation Modes
===============

The toolkit supports four primary operation modes:

style
    Quick style compliance check. Verifies that documentation follows
    project style guidelines including required headers and technical
    jargon detection. Ideal for pre-commit hooks.

quality
    Comprehensive quality analysis. Performs deep analysis including
    version reference checking, file size analysis, redundancy detection,
    and cross-reference validation. Recommended for quarterly maintenance.

build
    Build Sphinx documentation. Compiles HTML documentation with proper
    error handling and verification. Optionally opens in browser.

full
    Complete maintenance suite. Runs all checks and builds documentation.
    Provides comprehensive quality report.

Command-Line Options
====================

.. option:: --mode {style,quality,build,full}

   **Required.** Operation mode to execute.

.. option:: --quick

   Run only basic checks. Faster execution for pre-commit scenarios.
   Primarily affects quality mode.

.. option:: --quiet

   Suppress non-error output. Useful for CI/CD integration.

.. option:: --verbose

   Provide detailed output. Helpful for debugging and understanding
   what checks are being performed.

.. option:: --open

   Open documentation in browser after successful build.
   Only applicable with ``--mode build``.

.. option:: --version

   Display version information and exit.

Exit Codes
==========

The toolkit uses standard exit codes for integration with CI/CD pipelines:

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Code
     - Meaning
   * - 0
     - Success - all checks passed
   * - 1
     - Warnings - non-critical issues found
   * - 2
     - Errors - critical issues that must be fixed

Logging
=======

All operations are logged to the ``.logs/`` directory with detailed
timestamp, level, and message information:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Log File
     - Contents
   * - ``doc_style_check.log``
     - Style mode operation logs
   * - ``doc_quality_check.log``
     - Quality mode operation logs
   * - ``doc_build.log``
     - Build mode operation logs
   * - ``doc_full_maintenance.log``
     - Full maintenance mode logs

Log Format
----------

All log entries follow this format::

    YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message

Example::

    2025-10-30 14:23:45 - doc_maintenance - INFO - Documentation style check started

Module Structure
================

The toolkit is organized into several key classes:

.. autosummary::
   :toctree: generated/
   
   Colors
   QualityIssue
   MaintenanceLogger
   StyleChecker
   QualityChecker
   DocumentationBuilder
   MaintenanceRunner

Classes
=======

Colors
------

.. autoclass:: Colors
   :members:
   :undoc-members:
   :show-inheritance:

   Terminal color formatting utilities for consistent, readable output.
   
   Provides ANSI color codes matching the original bash scripts for
   user familiarity and visual consistency.
   
   **Example Usage**::
   
       print(Colors.green("Success!"))
       print(Colors.red("Error occurred"))
       print(Colors.yellow("Warning: Check this"))

QualityIssue
------------

.. autoclass:: QualityIssue
   :members:
   :undoc-members:
   :show-inheritance:

   Data class representing a documentation quality issue.
   
   **Attributes:**
   
   .. attribute:: severity
      :type: str
      
      Issue severity level: 'info', 'warning', or 'error'
   
   .. attribute:: category
      :type: str
      
      Issue category (e.g., 'style_compliance', 'version_reference')
   
   .. attribute:: file_path
      :type: str
      
      Relative path to file containing the issue
   
   .. attribute:: line_number
      :type: int
      
      Line number where issue occurs (0 if not applicable)
   
   .. attribute:: message
      :type: str
      
      Human-readable description of the issue

MaintenanceLogger
-----------------

.. autoclass:: MaintenanceLogger
   :members:
   :undoc-members:
   :show-inheritance:

   Centralized logging system for all maintenance operations.
   
   Provides consistent logging with proper file handling, formatting,
   and separation of concerns. All logs are written to the ``.logs/``
   directory.
   
   **Example Usage**::
   
       logger_system = MaintenanceLogger(repo_root)
       logger = logger_system.get_logger('my_operation', 'custom.log')
       logger.info("Operation started")
       logger.error("Something went wrong")

StyleChecker
------------

.. autoclass:: StyleChecker
   :members:
   :undoc-members:
   :show-inheritance:

   Documentation style compliance checker.
   
   Verifies that documentation follows project style guidelines:
   
   * User guide files start with "**For Users:**"
   * Developer guide files start with "**For Developers:**"
   * User guide avoids technical jargon
   * Sphinx builds complete without warnings
   
   **Example Usage**::
   
       checker = StyleChecker(docs_root, logger, quiet=False)
       exit_code = checker.run_all_checks()
       if exit_code == 0:
           print("All style checks passed!")

QualityChecker
--------------

.. autoclass:: QualityChecker
   :members:
   :undoc-members:
   :show-inheritance:

   Comprehensive documentation quality analyzer.
   
   Performs deep analysis of documentation quality:
   
   * Outdated version references
   * File size analysis (warns if >1000 lines)
   * Redundant content detection
   * Broken cross-references
   * Outdated date references
   
   **Example Usage**::
   
       checker = QualityChecker(docs_root, logger, quick_mode=False)
       exit_code = checker.run_all_checks()
       # Detailed report printed to console

DocumentationBuilder
--------------------

.. autoclass:: DocumentationBuilder
   :members:
   :undoc-members:
   :show-inheritance:

   Documentation building and verification system.
   
   Handles Sphinx documentation building with:
   
   * Clean builds (``make clean && make html``)
   * Incremental builds
   * Browser integration
   * Comprehensive error handling
   
   **Example Usage**::
   
       builder = DocumentationBuilder(docs_root, logger)
       success = builder.build_docs(clean=True)
       if success:
           builder.open_docs()

MaintenanceRunner
-----------------

.. autoclass:: MaintenanceRunner
   :members:
   :undoc-members:
   :show-inheritance:

   Main orchestrator for all maintenance operations.
   
   Coordinates all maintenance tools and provides unified interface
   for running different modes. Handles logging setup, mode execution,
   and result reporting.
   
   **Example Usage**::
   
       args = parse_arguments()
       runner = MaintenanceRunner(repo_root, args)
       exit_code = runner.run_full_maintenance()

Functions
=========

parse_arguments
---------------

.. autofunction:: parse_arguments

   Parse and validate command-line arguments.
   
   **Returns:**
       argparse.Namespace: Parsed arguments with validated values
   
   **Raises:**
       SystemExit: If invalid arguments provided

main
----

.. autofunction:: main

   Main entry point for the toolkit.
   
   Coordinates argument parsing, validation, and execution of the
   requested maintenance mode.
   
   **Returns:**
       int: Exit code (0=success, 1=warnings, 2=errors)
   
   **Example:**
   
   When run as a script::
   
       if __name__ == '__main__':
           sys.exit(main())

Security Considerations
=======================

The toolkit implements several security best practices:

Input Validation
    All file paths are validated before use. No arbitrary paths accepted.

Safe Subprocess Execution
    All subprocess calls use timeouts and capture output safely.
    No shell injection vulnerabilities.

Logging Security
    Logs written only to controlled ``.logs/`` directory.
    No sensitive data logged.

Error Handling
    Comprehensive error handling prevents information leakage.
    All exceptions logged appropriately.

Migration from Old Scripts
==========================

If you're migrating from the old separate scripts, here's the mapping:

From ``check_docs_style.sh``
-----------------------------

.. code-block:: bash

   # Old way
   ./scripts/utils/check_docs_style.sh
   
   # New way
   python scripts/utils/doc_maintenance_toolkit.py --mode style

From ``check_documentation_quality.py``
---------------------------------------

.. code-block:: bash

   # Old way
   python scripts/utils/check_documentation_quality.py
   
   # New way
   python scripts/utils/doc_maintenance_toolkit.py --mode quality

From ``doc_maintenance_commands.sh``
------------------------------------

.. code-block:: bash

   # Old way (sourcing and calling function)
   source scripts/utils/doc_maintenance_commands.sh
   doc_build
   
   # New way
   python scripts/utils/doc_maintenance_toolkit.py --mode build

Full Maintenance
----------------

.. code-block:: bash

   # Old way (manual)
   ./scripts/utils/check_docs_style.sh
   python scripts/utils/check_documentation_quality.py
   source scripts/utils/doc_maintenance_commands.sh && doc_build
   
   # New way (one command)
   python scripts/utils/doc_maintenance_toolkit.py --mode full

Troubleshooting
===============

Script Won't Execute
--------------------

Ensure the script is executable::

    chmod +x scripts/utils/doc_maintenance_toolkit.py

Check Python version (requires 3.6+)::

    python3 --version

Import Errors
-------------

Run from repository root::

    cd /path/to/RePORTaLiN
    python3 scripts/utils/doc_maintenance_toolkit.py --mode style

Verify ``__version__.py`` exists::

    ls -la __version__.py

Logs Not Created
----------------

Check ``.logs`` directory exists::

    ls -la .logs/

Create if missing::

    mkdir -p .logs

Ensure write permissions::

    chmod 755 .logs

Sphinx Build Fails
------------------

Verify Sphinx is installed::

    pip list | grep -i sphinx

Check ``make`` is available::

    which make

Verify docs directory structure::

    ls -la docs/sphinx/

Performance Notes
=================

The toolkit is optimized for different use cases:

Quick Checks (Pre-Commit)
    Use ``--mode style --quick`` for fastest execution.
    Typical runtime: 2-5 seconds.

Comprehensive Analysis
    Use ``--mode quality`` for thorough checking.
    Typical runtime: 10-30 seconds depending on doc size.

Full Maintenance
    Use ``--mode full`` for complete verification.
    Typical runtime: 30-60 seconds including build.

CI/CD Integration
    Use ``--quiet`` flag to reduce output noise.
    Exit codes enable proper pipeline integration.

Related Documentation
=====================

.. seealso::

   :doc:`../developer_guide/documentation_style_guide`
      Project documentation style guidelines
   
   :doc:`../user_guide/getting_started`
      Getting started with RePORTaLiN documentation
   
   :doc:`smart_commit`
      Git commit tool (separate, unchanged)

Version History
===============

.. versionadded:: 1.0.0
   Initial consolidated release combining three separate scripts.

.. note::
   This tool replaces ``check_docs_style.sh``, ``check_documentation_quality.py``,
   and ``doc_maintenance_commands.sh``. The old scripts are archived but
   available in ``tmp/backups_*/`` for reference.

See Also
========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
