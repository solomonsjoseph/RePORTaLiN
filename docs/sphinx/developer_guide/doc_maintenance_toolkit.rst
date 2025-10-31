.. _developer_guide_doc_maintenance:

========================================================
Developer Guide: Documentation Maintenance Toolkit
========================================================

**For Developers:**

This guide provides comprehensive information for developers working with
or extending the Documentation Maintenance Toolkit.

Overview
========

The Documentation Maintenance Toolkit is a consolidated Python-based system
that replaces three separate scripts while preserving all functionality and
adding enhanced features.

Architecture
============

The toolkit follows object-oriented design principles with clear separation
of concerns:

.. code-block:: text

   doc_maintenance_toolkit.py
   │
   ├── Utility Classes
   │   ├── Colors - Terminal color formatting
   │   ├── QualityIssue - Issue data structure
   │   └── MaintenanceLogger - Centralized logging
   │
   ├── Core Functionality
   │   ├── StyleChecker - Style compliance verification
   │   ├── QualityChecker - Quality analysis
   │   └── DocumentationBuilder - Sphinx build management
   │
   ├── Orchestration
   │   └── MaintenanceRunner - Mode coordination
   │
   └── Entry Point
       └── main() - CLI interface

Design Principles
=================

The toolkit adheres to several key design principles:

Single Responsibility
    Each class has one clear purpose. StyleChecker handles style,
    QualityChecker handles quality, etc.

DRY (Don't Repeat Yourself)
    Common functionality (logging, colors, error handling) is
    centralized and reused.

Open/Closed Principle
    Classes are open for extension but closed for modification.
    Easy to add new checks without changing existing code.

Fail-Safe
    Comprehensive error handling ensures graceful degradation.
    Timeouts prevent hanging operations.

Logging First
    All operations logged for audit trail and debugging.

Extending the Toolkit
======================

Adding New Checks
-----------------

To add a new quality check:

1. **Add method to QualityChecker class**::

       def check_new_feature(self) -> None:
           """Check for new feature compliance.
           
           Detailed description of what this check does.
           """
           print("🔍 Checking new feature...")
           self.logger.info("Starting new feature check...")
           
           for rst_file in self.docs_root.rglob('*.rst'):
               # Your check logic here
               if issue_found:
                   self.add_issue(
                       'warning',
                       'new_feature',
                       str(rst_file.relative_to(self.docs_root)),
                       line_number,
                       'Description of issue'
                   )

2. **Add call in run_all_checks()**::

       def run_all_checks(self) -> int:
           # ...existing checks...
           if not self.quick_mode:
               self.check_new_feature()  # Add your check
           # ...rest of code...

3. **Update documentation**:
   
   - Add to this file's "Available Checks" section
   - Update API documentation
   - Add to changelog

Adding New Modes
----------------

To add a new operation mode:

1. **Add mode to argument parser**::

       parser.add_argument(
           '--mode',
           choices=['style', 'quality', 'build', 'full', 'newmode'],
           required=True,
           help='Operation mode to run'
       )

2. **Add handler in MaintenanceRunner**::

       def run_new_mode(self) -> int:
           """Run new mode operations.
           
           Returns:
               Exit code
           """
           # Your mode logic here
           return 0

3. **Add case in main()**::

       elif args.mode == 'newmode':
           return runner.run_new_mode()

4. **Update log file mapping** in MaintenanceRunner.__init__()

Code Style Guidelines
=====================

The toolkit follows strict coding standards:

PEP 8 Compliance
----------------

All code must comply with PEP 8::

    # Good
    def check_user_guide_headers(self) -> List[str]:
        """Check user guide files for required headers."""
        missing_headers = []
        # ...
        return missing_headers
    
    # Bad
    def CheckUserGuideHeaders(self):  # Wrong naming
        missingHeaders=[]  # Wrong spacing
        return missingHeaders

Type Hints
----------

Use type hints for all function signatures::

    from typing import List, Dict, Optional, Tuple
    
    def process_files(
        self, 
        file_paths: List[Path],
        options: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str]:
        """Process multiple files."""
        # ...

Docstrings
----------

All classes, methods, and functions require comprehensive docstrings::

    def check_sphinx_build(self) -> Tuple[int, str]:
        """Run Sphinx build and check for warnings/errors.
        
        Executes 'make html' in the docs directory and analyzes
        the output for warning and error messages.
        
        Returns:
            Tuple of (exit_code, output_text)
            
        Raises:
            subprocess.TimeoutExpired: If build exceeds 5 minutes
            FileNotFoundError: If make command not available
        
        Example:
            >>> builder = DocumentationBuilder(docs_root, logger)
            >>> exit_code, output = builder.check_sphinx_build()
            >>> if exit_code == 0:
            ...     print("Build successful!")
        """
        # Implementation...

Error Handling
--------------

Always use try-except blocks with specific exceptions::

    try:
        with open(rst_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        self.logger.error(f"File not found: {rst_file}")
        self.errors += 1
    except PermissionError:
        self.logger.error(f"Permission denied: {rst_file}")
        self.errors += 1
    except Exception as e:
        self.logger.error(f"Unexpected error reading {rst_file}: {e}")
        self.errors += 1

Logging Best Practices
======================

Logging Levels
--------------

Use appropriate log levels:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Level
     - Usage
   * - DEBUG
     - Detailed diagnostic information (not currently used)
   * - INFO
     - General informational messages
   * - WARNING
     - Non-critical issues that should be reviewed
   * - ERROR
     - Critical issues that prevent operation

Example::

    self.logger.info("Starting quality check...")
    self.logger.warning(f"Large file detected: {line_count} lines")
    self.logger.error(f"Build failed with exit code {exit_code}")

Log Messages
------------

Write clear, actionable log messages::

    # Good
    self.logger.info(f"Checking {len(files)} documentation files")
    self.logger.error(f"Missing header in {file_name} - Expected: **For Users:**")
    
    # Bad
    self.logger.info("Starting")  # Too vague
    self.logger.error("Error")  # No context

Testing Guidelines
==================

Unit Testing
------------

Write tests for all new functionality::

    import unittest
    from pathlib import Path
    from doc_maintenance_toolkit import StyleChecker
    
    class TestStyleChecker(unittest.TestCase):
        def setUp(self):
            self.docs_root = Path('test_docs')
            self.logger = logging.getLogger('test')
            self.checker = StyleChecker(
                self.docs_root,
                self.logger,
                quiet=True
            )
        
        def test_user_guide_header_detection(self):
            """Test that user guide headers are detected correctly."""
            # Create test file
            test_file = self.docs_root / 'user_guide' / 'test.rst'
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text('**For Users:** Test content')
            
            # Run check
            missing = self.checker.check_user_guide_headers()
            
            # Verify
            self.assertEqual(len(missing), 0)
        
        def tearDown(self):
            # Cleanup test files
            shutil.rmtree(self.docs_root)

Integration Testing
-------------------

Test mode interactions::

    def test_full_maintenance_mode(self):
        """Test that full maintenance runs all checks."""
        args = argparse.Namespace(
            mode='full',
            quick=False,
            quiet=True,
            verbose=False,
            open=False
        )
        
        runner = MaintenanceRunner(repo_root, args)
        exit_code = runner.run_full_maintenance()
        
        # Verify all logs created
        self.assertTrue((repo_root / '.logs' / 'doc_full_maintenance.log').exists())

Performance Considerations
==========================

File Reading
------------

Read files efficiently::

    # Good - Read once
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Process content...
    
    # Bad - Multiple reads
    with open(file_path, 'r') as f:
        lines = f.readlines()
    with open(file_path, 'r') as f:
        content = f.read()

Subprocess Timeouts
-------------------

Always set timeouts on subprocess calls::

    result = subprocess.run(
        ['make', 'html'],
        timeout=300,  # 5 minute maximum
        capture_output=True
    )

Caching
-------

Cache expensive operations::

    class MaintenanceLogger:
        def __init__(self, repo_root: Path):
            self._loggers: Dict[str, logging.Logger] = {}
        
        def get_logger(self, name: str) -> logging.Logger:
            if name in self._loggers:
                return self._loggers[name]  # Return cached
            
            logger = self._create_logger(name)
            self._loggers[name] = logger
            return logger

Security Best Practices
=======================

Path Validation
---------------

Always validate paths before use::

    def _validate_path(self, path: Path) -> bool:
        """Validate that path is within allowed directory."""
        try:
            # Resolve to absolute path
            abs_path = path.resolve()
            
            # Check it's within docs_root
            if not str(abs_path).startswith(str(self.docs_root.resolve())):
                self.logger.error(f"Path outside docs root: {path}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Invalid path: {path} - {e}")
            return False

Subprocess Safety
-----------------

Use list form, not string form::

    # Good - List form prevents shell injection
    subprocess.run(['make', 'html'], cwd=docs_root)
    
    # Bad - String form vulnerable to injection
    subprocess.run('make html', shell=True)  # NEVER DO THIS

Input Sanitization
------------------

Sanitize all user input::

    def parse_arguments(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--mode',
            choices=['style', 'quality', 'build', 'full'],  # Whitelist
            required=True
        )
        return parser.parse_args()

Common Pitfalls
===============

File Encoding
-------------

Always specify encoding::

    # Good
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Bad - Platform dependent
    with open(file, 'r') as f:
        content = f.read()

Path Separators
---------------

Use Path objects, not string concatenation::

    # Good
    file_path = docs_root / 'user_guide' / 'file.rst'
    
    # Bad - Won't work on Windows
    file_path = docs_root + '/user_guide/file.rst'

Exception Handling
------------------

Don't catch all exceptions blindly::

    # Good - Specific exceptions
    try:
        result = risky_operation()
    except ValueError as e:
        self.logger.error(f"Invalid value: {e}")
    except FileNotFoundError:
        self.logger.error("File not found")
    
    # Bad - Hides bugs
    try:
        result = risky_operation()
    except:  # Too broad
        pass  # Swallows all errors

Debugging Tips
==============

Enable Verbose Mode
-------------------

Use ``--verbose`` for detailed output::

    python doc_maintenance_toolkit.py --mode quality --verbose

Check Log Files
---------------

Always check logs for detailed information::

    tail -f .logs/doc_quality_check.log

Add Debug Statements
--------------------

Temporarily add debug logging::

    self.logger.debug(f"Processing file: {file_path}")
    self.logger.debug(f"Current state: {self.stats}")

Use Python Debugger
-------------------

Insert breakpoints for investigation::

    import pdb
    
    def check_quality(self):
        pdb.set_trace()  # Debugger will stop here
        # ... rest of code

Contributing
============

To contribute to the toolkit:

1. **Fork and Clone**
   
   Fork the repository and clone your fork

2. **Create Feature Branch**
   
   ::
   
       git checkout -b feature/new-check

3. **Make Changes**
   
   - Follow code style guidelines
   - Add comprehensive docstrings
   - Include type hints
   - Write unit tests

4. **Test Thoroughly**
   
   ::
   
       python -m pytest tests/
       python doc_maintenance_toolkit.py --mode full

5. **Update Documentation**
   
   - Update this developer guide
   - Update API documentation
   - Add changelog entry

6. **Submit Pull Request**
   
   Include:
   
   - Clear description of changes
   - Test results
   - Documentation updates

Related Documentation
=====================

.. seealso::

   :doc:`../api/doc_maintenance_toolkit`
      Complete API reference
   
   :doc:`documentation_style_guide`
      Project documentation standards
   
   :doc:`../user_guide/documentation_quickstart`
      User guide for documentation

Changelog
=========

Version 1.0.0 (2025-10-30)
--------------------------

Initial consolidated release:

- Merged check_docs_style.sh functionality
- Merged check_documentation_quality.py functionality
- Merged doc_maintenance_commands.sh functionality
- Added enhanced logging system
- Added multiple operation modes
- Added command-line options (quiet, verbose, quick)
- Comprehensive Sphinx documentation
- 100% docstring coverage
- Full type hint coverage

Future Enhancements
===================

Planned features for future versions:

- JSON output format for machine parsing
- Parallel file processing for large doc sets
- Configuration file support (.docmaintrc)
- Plugin system for custom checks
- Integration with git hooks
- HTML report generation
- Metrics dashboard

Questions or Issues?
====================

For questions, issues, or contributions:

- Check existing documentation
- Review code comments
- Check log files
- Contact: RePORTaLiN Development Team

Version
=======

.. versionadded:: 1.0.0
   Initial developer guide for consolidated toolkit.

See Also
========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
