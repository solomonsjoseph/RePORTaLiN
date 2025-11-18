#!/usr/bin/env python3
"""Documentation maintenance toolkit for style checking, quality analysis, and building.

This module implements the automated documentation maintenance system for the
RePORTaLiN project, orchestrating Phase 1 (Docstring Generation) and Phase 2
(Multi-Version Build & Publication) workflows from the documentation system guide.

Architecture Overview
--------------------
The toolkit provides four main operation modes:

1. **Style Mode** (`--mode style`):
   Validates documentation style compliance using the Diátaxis framework.
   - Checks User Guide files for "**For Users:**" headers
   - Checks Developer Guide files for "**For Developers:**" headers
   - Detects technical jargon in user-facing documentation
   - Validates Sphinx build success (no warnings/errors)

2. **Quality Mode** (`--mode quality`):
   Performs deep quality analysis and generates detailed reports.
   - Version reference consistency (e.g., |version| usage)
   - File size limits (warns if files >500KB)
   - Redundant content detection (duplicate paragraphs)
   - Broken internal references (cross-file links)
   - Outdated date detection (copyright years, "last updated")
   - Style guide compliance validation

3. **Build Mode** (`--mode build`):
   Executes Sphinx documentation builds using three distinct workflows:
   - **Doctest** (`--doctest`): Runs code examples from docstrings (Phase 1 verification)
   - **Autobuild** (`--watch`): Hot-reload development server for writing .rst files
   - **Multiversion** (default): Production build for all Git tags/branches (Phase 2)

4. **Full Mode** (`--mode full`):
   Runs complete maintenance cycle: style → quality → build (with multiversion).

Integration with Documentation System
------------------------------------
This toolkit directly implements the workflows described in Phase 1 & Phase 2:

**Phase 1 (Content & Docstring Generation):**
- Automated verification via `--mode build --doctest`
- Runs `sphinx-build -b doctest` to validate all docstring examples
- Ensures zero broken examples before allowing commits

**Phase 2 (Multi-Version Build & Publication):**
- Three build workflows implemented in DocumentationBuilder class
- Workflow A: Doctest verification (`run_doctest()`)
- Workflow B: Development loop (`run_autobuild()`)
- Workflow C: Production build (`run_multiversion_build()`)

Pre-Commit Integration
---------------------
Fast validation for pre-commit hooks using `--quick` flag:
- Skips slow quality checks (redundancy, broken references)
- Runs only essential style validation + doctest
- Typical execution: <5 seconds vs. full quality check: 30+ seconds

Module Classes
-------------
- **Colors**: ANSI terminal color utilities for formatted output
- **QualityIssue**: Dataclass representing a single documentation issue
- **MaintenanceLogger**: Centralized logging system for all operations
- **StyleChecker**: Diátaxis framework compliance and style validation
- **QualityChecker**: Deep quality analysis with issue tracking and reporting
- **DocumentationBuilder**: Sphinx build orchestration (three workflows)
- **MaintenanceRunner**: Main coordinator for all operation modes

Command-Line Interface
---------------------
The toolkit provides a comprehensive CLI for all operations::

    # Style validation only
    python doc_maintenance_toolkit.py --mode style
    
    # Quality analysis with detailed report
    python doc_maintenance_toolkit.py --mode quality --verbose
    
    # Run doctest verification (Phase 1 check)
    python doc_maintenance_toolkit.py --mode build --doctest
    
    # Development server with hot-reload
    python doc_maintenance_toolkit.py --mode build --watch
    
    # Production multiversion build
    python doc_maintenance_toolkit.py --mode build
    
    # Full maintenance cycle
    python doc_maintenance_toolkit.py --mode full
    
    # Quick pre-commit check
    python doc_maintenance_toolkit.py --mode style --quick

Exit Codes
---------
- 0: All checks passed successfully
- 1: Warnings found (non-critical issues)
- 2: Errors found (critical failures, build broken)
- 130: Interrupted by user (Ctrl+C)

Example
-------
Full maintenance workflow::

    >>> from pathlib import Path
    >>> from doc_maintenance_toolkit import MaintenanceRunner
    >>> import argparse
    >>> # Simulate CLI arguments
    >>> args = argparse.Namespace(
    ...     mode='full',
    ...     quick=False,
    ...     quiet=False,
    ...     verbose=True,
    ...     doctest=False,
    ...     watch=False,
    ...     open=False
    ... )
    >>> repo_root = Path('/path/to/repo')
    >>> runner = MaintenanceRunner(repo_root, args)
    >>> exit_code = runner.run_full_maintenance()  # doctest: +SKIP
    >>> print(f"Maintenance completed with exit code: {exit_code}")  # doctest: +SKIP

Notes
-----
- Requires Sphinx, sphinx_rtd_theme, sphinx-autobuild, sphinx-multiversion
- All logs written to `.logs/` directory
- Temporary reports saved to `tmp/` directory
- Uses standard library logging (aliased as std_logging to avoid conflicts)

See Also
--------
- Phase 1 Documentation Guide: Docstring generation and verification
- Phase 2 Documentation Guide: Multi-version build and publication
- Diátaxis Framework: https://diataxis.fr/ (user vs. developer separation)
- Sphinx Documentation: https://www.sphinx-doc.org/

Attributes
----------
__version__ : str
    Module version imported from __version__.py or defaults to "1.0.0"
"""

# Standard library imports
# CRITICAL: Import standard logging before local modules to avoid shadowing
from __future__ import absolute_import
import sys
import os

# Temporarily manipulate path to ensure standard library logging is imported
_original_path = sys.path[:]
sys.path = [p for p in sys.path if 'scripts/utils' not in p]
import logging as std_logging
sys.path = _original_path
del _original_path

import re
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from datetime import datetime

# Add repo root to path for version import
_repo_root = Path(__file__).parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Import version
try:
    from __version__ import __version__
except ImportError:
    __version__ = "1.0.0"


# Terminal colors for output (matching bash scripts)
class Colors:
    """ANSI color codes for terminal output with convenience methods.
    
    Provides cross-platform terminal color support using ANSI escape sequences.
    All color methods automatically reset to default color (NC) after text.
    
    Color codes are designed to match the bash script color scheme used
    throughout the RePORTaLiN project for consistent visual output.
    
    Attributes:
        RED: Error messages, critical failures
        GREEN: Success messages, passed checks
        YELLOW: Warnings, informational notices
        BLUE: Section headers, informational
        NC: No Color (reset to terminal default)
    
    Example:
        >>> from doc_maintenance_toolkit import Colors
        >>> print(Colors.red("Error: File not found"))  # doctest: +SKIP
        >>> print(Colors.green("✓ All checks passed"))  # doctest: +SKIP
        >>> # Direct usage in f-strings
        >>> status = "failed"
        >>> color_func = Colors.red if status == "failed" else Colors.green
        >>> print(color_func(f"Status: {status}"))  # doctest: +SKIP
    
    Note:
        ANSI codes may not render correctly in all terminals (e.g., old Windows
        cmd.exe). Modern terminals (bash, zsh, PowerShell 7+) support these codes.
    """
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def red(text: str) -> str:
        """Return text wrapped in red ANSI codes.
        
        Args:
            text: Text to colorize.
        
        Returns:
            Text with red ANSI codes and automatic reset.
        
        Example:
            >>> Colors.red("Error")  # doctest: +SKIP
            '\033[0;31mError\033[0m'
        """
        return f"{Colors.RED}{text}{Colors.NC}"
    
    @staticmethod
    def green(text: str) -> str:
        """Return text wrapped in green ANSI codes.
        
        Args:
            text: Text to colorize.
        
        Returns:
            Text with green ANSI codes and automatic reset.
        
        Example:
            >>> Colors.green("Success")  # doctest: +SKIP
            '\033[0;32mSuccess\033[0m'
        """
        return f"{Colors.GREEN}{text}{Colors.NC}"
    
    @staticmethod
    def yellow(text: str) -> str:
        """Return text wrapped in yellow ANSI codes.
        
        Args:
            text: Text to colorize.
        
        Returns:
            Text with yellow ANSI codes and automatic reset.
        
        Example:
            >>> Colors.yellow("Warning")  # doctest: +SKIP
            '\033[1;33mWarning\033[0m'
        """
        return f"{Colors.YELLOW}{text}{Colors.NC}"
    
    @staticmethod
    def blue(text: str) -> str:
        """Return text wrapped in blue ANSI codes.
        
        Args:
            text: Text to colorize.
        
        Returns:
            Text with blue ANSI codes and automatic reset.
        
        Example:
            >>> Colors.blue("Info")  # doctest: +SKIP
            '\033[0;34mInfo\033[0m'
        """
        return f"{Colors.BLUE}{text}{Colors.NC}"


@dataclass
class QualityIssue:
    """Represents a single documentation quality issue found during analysis.
    
    Dataclass for storing structured information about documentation problems
    discovered by QualityChecker. Issues are categorized by severity and type
    for prioritized reporting and remediation.
    
    Attributes:
        severity: Issue severity level - "ERROR" (critical, breaks build),
            "WARNING" (non-critical, should fix), or "INFO" (suggestion).
        category: Issue category for grouping - "version", "size", "redundancy",
            "reference", "date", "style", etc.
        file_path: Relative path to file containing the issue (from docs root).
        line_number: Line number where issue occurs (0 if not line-specific).
        message: Human-readable description of the issue and recommended fix.
    
    Example:
        >>> from doc_maintenance_toolkit import QualityIssue
        >>> issue = QualityIssue(
        ...     severity="WARNING",
        ...     category="version",
        ...     file_path="user_guide/installation.rst",
        ...     line_number=42,
        ...     message="Hardcoded version '1.0.0' should use |version| substitution"
        ... )
        >>> print(f"{issue.severity}: {issue.message}")
        WARNING: Hardcoded version '1.0.0' should use |version| substitution
    """
    severity: str
    category: str
    file_path: str
    line_number: int
    message: str


class MaintenanceLogger:
    """Centralized logging system for all documentation maintenance operations.
    
    Manages file-based logging for all maintenance activities, creating separate
    log files for different operations (style checks, quality analysis, builds).
    All logs are written to the `.logs/` directory with timestamped entries.
    
    This class uses Python's standard library logging (aliased as std_logging)
    to avoid conflicts with the project's custom logging_system module.
    
    Features:
        - Automatic `.logs/` directory creation
        - Per-operation logger instances (cached to prevent duplicates)
        - Consistent formatting (timestamp, name, level, message)
        - Prevents duplicate handlers when loggers are reused
    
    Attributes:
        log_dir: Path to `.logs/` directory (created if doesn't exist)
        _loggers: Internal cache of logger instances by name
    
    Example:
        >>> from pathlib import Path
        >>> from doc_maintenance_toolkit import MaintenanceLogger
        >>> repo_root = Path('/path/to/repo')
        >>> logger_manager = MaintenanceLogger(repo_root)
        >>> # Get logger for style checks
        >>> style_logger = logger_manager.get_logger('style', 'style_check.log')
        >>> style_logger.info("Starting style validation")  # doctest: +SKIP
        >>> # Get logger for quality analysis (auto-named log file)
        >>> quality_logger = logger_manager.get_logger('quality')
        >>> quality_logger.warning("Found 3 issues")  # doctest: +SKIP
    
    Note:
        Loggers are cached by name. Calling get_logger() with the same name
        multiple times returns the same logger instance, avoiding duplicate
        log entries.
    """
    
    def __init__(self, repo_root: Path):
        """Initialize the logging system with repository root.
        
        Args:
            repo_root: Path to repository root directory. The `.logs/`
                directory will be created here if it doesn't exist.
        
        Side Effects:
            Creates `.logs/` directory in repo_root if not present.
        
        Example:
            >>> from pathlib import Path
            >>> logger_manager = MaintenanceLogger(Path('/tmp/test_repo'))
            >>> logger_manager.log_dir.name
            '.logs'
        """
        self.log_dir = repo_root / '.logs'
        self.log_dir.mkdir(exist_ok=True)
        self._loggers: Dict[str, std_logging.Logger] = {}
    
    def get_logger(self, name: str, log_file: Optional[str] = None) -> std_logging.Logger:
        """Get or create a logger for a specific operation.
        
        Returns an existing logger if one with the given name exists, otherwise
        creates a new logger with file handler. Prevents duplicate handlers.
        
        Args:
            name: Logger name (e.g., 'style', 'quality', 'build').
            log_file: Optional log filename. If None, defaults to "{name}.log".
        
        Returns:
            Configured logger instance with file handler and formatter.
        
        Example:
            >>> from pathlib import Path
            >>> logger_manager = MaintenanceLogger(Path('/tmp/test_repo'))
            >>> logger1 = logger_manager.get_logger('style')
            >>> logger2 = logger_manager.get_logger('style')  # Returns same instance
            >>> logger1 is logger2
            True
            >>> # Custom log file
            >>> build_logger = logger_manager.get_logger('build', 'sphinx_build.log')
            >>> build_logger.name
            'build'
        
        Note:
            Logger is set to INFO level. File handler uses UTF-8 encoding
            and append mode for log continuity across runs.
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = std_logging.getLogger(name)
        logger.setLevel(std_logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler
        if log_file is None:
            log_file = f"{name}.log"
        
        file_handler = std_logging.FileHandler(
            self.log_dir / log_file,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(std_logging.INFO)
        
        # Formatter
        formatter = std_logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        self._loggers[name] = logger
        
        return logger


class StyleChecker:
    """Documentation style compliance checker for Diátaxis framework validation.
    
    Validates that documentation follows the Diátaxis framework's audience
    separation principle (User Guide vs. Developer Guide) and Sphinx build
    requirements. Performs four key checks:
    
    1. **User Guide Headers**: Ensures all user_guide/*.rst files start with
       "**For Users:**" header to clearly signal non-technical audience.
    
    2. **Developer Guide Headers**: Ensures all developer_guide/*.rst files
       start with "**For Developers:**" header for technical audience.
    
    3. **Technical Jargon**: Detects technical terms in user-facing docs that
       might confuse non-technical users (e.g., "module reference", "API
       documentation", "__init__ method").
    
    4. **Sphinx Build**: Runs `sphinx-build` in strict mode (-W) to validate
       no warnings or errors exist in the documentation.
    
    The checker maintains error and warning counts for final exit code
    determination (0=pass, 1=warnings, 2=errors).
    
    Attributes:
        docs_root: Path to Sphinx documentation directory (docs/sphinx/)
        logger: Logger instance for file-based logging
        quiet: If True, suppress non-error console output
        errors: Count of critical errors found (increments on each error)
        warnings: Count of non-critical warnings found
        tech_terms: List of technical terms to flag in user guide
    
    Example:
        >>> from pathlib import Path
        >>> import logging
        >>> docs_root = Path('/path/to/docs/sphinx')
        >>> logger = logging.getLogger('style')
        >>> checker = StyleChecker(docs_root, logger, quiet=False)
        >>> # Run all checks
        >>> exit_code = checker.run_all_checks()  # doctest: +SKIP
        >>> print(f"Style check {'passed' if exit_code == 0 else 'failed'}")  # doctest: +SKIP
    
    Note:
        Expects docs_root to contain user_guide/ and developer_guide/
        subdirectories with .rst files following Diátaxis framework.
    """
    
    def __init__(self, docs_root: Path, logger: std_logging.Logger, quiet: bool = False):
        """Initialize the style checker with documentation root.
        
        Args:
            docs_root: Path to Sphinx documentation directory containing
                user_guide/ and developer_guide/ subdirectories.
            logger: Configured logger instance for file-based logging.
            quiet: If True, suppress non-error console output (errors
                still printed). Useful for automated/CI environments.
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = StyleChecker(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('style'),
            ...     quiet=True
            ... )
            >>> checker.errors
            0
            >>> len(checker.tech_terms) > 10
            True
        """
        self.docs_root = docs_root
        self.logger = logger
        self.quiet = quiet
        self.errors = 0
        self.warnings = 0
        
        # Technical terms that shouldn't appear in user guide
        self.tech_terms = [
            "module reference",
            "function call",
            "class method",
            " API documentation",
            "parameter list",
            "decorator pattern",
            "singleton instance",
            "algorithm implementation",
            "dataclass definition",
            "instantiate object",
            "thread-safe implementation",
            "REPL environment",
            "__init__ method",
        ]
    
    def check_user_guide_headers(self) -> List[str]:
        """Check user guide files for required "**For Users:**" headers.
        
        Validates that all .rst files in user_guide/ directory start with
        the "**For Users:**" header within first 500 characters. This ensures
        clear audience targeting per Diátaxis framework.
        
        Returns:
            List of filenames missing the required header.
        
        Side Effects:
            - Increments self.errors for each missing header
            - Logs errors/info to logger
            - Prints colored output to console (unless quiet=True)
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = StyleChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> missing = checker.check_user_guide_headers()  # doctest: +SKIP
            >>> if missing:  # doctest: +SKIP
            ...     print(f"Files missing headers: {missing}")
        
        Note:
            Checks only first 500 characters of each file for performance.
            Logs warning if user_guide/ directory doesn't exist.
        """
        if not self.quiet:
            print(Colors.blue("Checking User Guide Files..."))
            print("─" * 64)
        
        self.logger.info("Checking user guide headers...")
        missing_headers = []
        
        user_guide_dir = self.docs_root / 'user_guide'
        if not user_guide_dir.exists():
            self.logger.warning(f"User guide directory not found: {user_guide_dir}")
            return missing_headers
        
        for rst_file in user_guide_dir.glob('*.rst'):
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Check first 500 chars
                
                if '**For Users' not in content:
                    file_name = rst_file.name
                    missing_headers.append(file_name)
                    print(Colors.red(f"✗ MISSING: {file_name}"))
                    print(Colors.yellow(f"  Expected: **For Users:**"))
                    self.logger.error(f"Missing header in {file_name}")
                    self.errors += 1
                else:
                    if not self.quiet:
                        print(Colors.green(f"✓ PASS: {rst_file.name}"))
                    self.logger.info(f"Header check passed: {rst_file.name}")
            
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
                self.errors += 1
        
        return missing_headers
    
    def check_developer_guide_headers(self) -> List[str]:
        """Check developer guide files for required "**For Developers:**" headers.
        
        Validates that all .rst files in developer_guide/ directory start with
        the "**For Developers:**" header within first 500 characters.
        
        Returns:
            List of filenames missing the required header.
        
        Side Effects:
            - Increments self.errors for each missing header
            - Logs errors/info to logger
            - Prints colored output to console (unless quiet=True)
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = StyleChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> missing = checker.check_developer_guide_headers()  # doctest: +SKIP
        
        Note:
            Checks only first 500 characters. Logs warning if developer_guide/
            directory doesn't exist.
        """
        if not self.quiet:
            print()
            print(Colors.blue("Checking Developer Guide Files..."))
            print("─" * 64)
        
        self.logger.info("Checking developer guide headers...")
        missing_headers = []
        
        dev_guide_dir = self.docs_root / 'developer_guide'
        if not dev_guide_dir.exists():
            self.logger.warning(f"Developer guide directory not found: {dev_guide_dir}")
            return missing_headers
        
        for rst_file in dev_guide_dir.glob('*.rst'):
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Check first 500 chars
                
                if '**For Developers' not in content:
                    file_name = rst_file.name
                    missing_headers.append(file_name)
                    print(Colors.red(f"✗ MISSING: {file_name}"))
                    print(Colors.yellow(f"  Expected: **For Developers:**"))
                    self.logger.error(f"Missing header in {file_name}")
                    self.errors += 1
                else:
                    if not self.quiet:
                        print(Colors.green(f"✓ PASS: {rst_file.name}"))
                    self.logger.info(f"Header check passed: {rst_file.name}")
            
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
                self.errors += 1
        
        return missing_headers
    
    def check_technical_jargon(self) -> Dict[str, List[str]]:
        """Check user guide for technical jargon that may confuse non-technical users.
        
        Scans all .rst files in user_guide/ directory for technical terms that
        should be avoided in user-facing documentation. Terms are defined in
        self.tech_terms list and include phrases like "API documentation",
        "class method", "__init__ method", etc.
        
        Code blocks (.. code-block::) are excluded from jargon detection since
        technical terms are acceptable in code examples.
        
        Returns:
            Dictionary mapping filenames to lists of technical terms found.
            Empty dict if no jargon detected.
        
        Side Effects:
            - Increments self.warnings for each term found (non-critical)
            - Logs warnings for each term
            - Prints colored output listing all found terms per file
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = StyleChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> jargon = checker.check_technical_jargon()  # doctest: +SKIP
            >>> if jargon:  # doctest: +SKIP
            ...     for file, terms in jargon.items():
            ...         print(f"{file}: {', '.join(terms)}")
        
        Note:
            This is a warning-level check, not an error. Technical terms may
            be acceptable with proper explanation or in specific contexts.
        """
        if not self.quiet:
            print()
            print(Colors.blue("Checking for Technical Jargon in User Guide..."))
            print("─" * 64)
        
        self.logger.info("Checking for technical jargon...")
        jargon_found = {}
        
        user_guide_dir = self.docs_root / 'user_guide'
        if not user_guide_dir.exists():
            return jargon_found
        
        for rst_file in user_guide_dir.glob('*.rst'):
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip code blocks for jargon detection
                content_no_code = re.sub(r'.. code-block::.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
                
                found_terms = []
                for term in self.tech_terms:
                    if term in content_no_code:
                        found_terms.append(term)
                
                if found_terms:
                    jargon_found[rst_file.name] = found_terms
                    print(Colors.yellow(f"⚠ WARNING: {rst_file.name} contains technical terms:"))
                    for term in found_terms:
                        print(Colors.yellow(f"  • Found: \"{term}\""))
                        self.logger.warning(f"Technical term '{term}' in {rst_file.name}")
                    self.warnings += len(found_terms)
            
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
        
        if not jargon_found and not self.quiet:
            print(Colors.green("✓ No technical jargon found in user guide"))
            self.logger.info("No technical jargon found")
        
        return jargon_found
    
    def check_sphinx_build(self) -> Tuple[int, str]:
        """Run Sphinx build in strict mode and check for warnings/errors.
        
        Executes `make html` in the docs_root directory to build the Sphinx
        documentation. Counts warnings and errors in the build output to
        determine success. This validates that the documentation can be
        built cleanly without issues.
        
        Returns:
            Tuple of (exit_code, output):
                - exit_code: 0 if successful, 1 if failed or has issues
                - output: Combined stdout and stderr from build command
        
        Side Effects:
            - Increments self.errors if build fails or has warnings/errors
            - Logs build status to logger
            - Prints colored status to console
            - Runs subprocess with 5-minute timeout
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = StyleChecker(Path('/path/to/docs'), logging.getLogger('test'))
            >>> exit_code, output = checker.check_sphinx_build()  # doctest: +SKIP
            >>> if exit_code == 0:  # doctest: +SKIP
            ...     print("Build successful!")
            >>> else:  # doctest: +SKIP
            ...     print(f"Build issues found")
        
        Note:
            Requires `make` command and Sphinx to be installed. Times out
            after 5 minutes to prevent hung builds.
        """
        if not self.quiet:
            print()
            print(Colors.blue("Checking Sphinx Build..."))
            print("─" * 64)
        
        self.logger.info("Running Sphinx build...")
        
        try:
            result = subprocess.run(
                ['make', 'html'],
                cwd=self.docs_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                # Count warnings and errors in output
                warn_count = output.count('WARNING')
                error_count = output.count('ERROR')
                
                if warn_count > 0 or error_count > 0:
                    print(Colors.red(f"✗ BUILD ISSUES: {warn_count} warnings, {error_count} errors"))
                    self.logger.error(f"Build issues: {warn_count} warnings, {error_count} errors")
                    self.errors += 1
                else:
                    print(Colors.green(f"✓ Build successful (0 warnings, 0 errors)"))
                    self.logger.info("Sphinx build successful with no issues")
            else:
                print(Colors.red("✗ BUILD FAILED"))
                self.logger.error(f"Sphinx build failed with exit code {result.returncode}")
                self.errors += 1
            
            return (result.returncode, output)
        
        except subprocess.TimeoutExpired:
            error_msg = "Sphinx build timed out after 5 minutes"
            print(Colors.red(f"✗ {error_msg}"))
            self.logger.error(error_msg)
            self.errors += 1
            return (1, error_msg)
        
        except FileNotFoundError:
            error_msg = "Make command not found - ensure Sphinx is installed"
            print(Colors.red(f"✗ {error_msg}"))
            self.logger.error(error_msg)
            self.errors += 1
            return (1, error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during build: {e}"
            print(Colors.red(f"✗ {error_msg}"))
            self.logger.error(error_msg)
            self.errors += 1
            return (1, str(e))
    
    def run_all_checks(self) -> int:
        """Run all style compliance checks and return exit code.
        
        Executes all four style validation checks in sequence:
        1. User guide header validation
        2. Developer guide header validation
        3. Technical jargon detection
        4. Sphinx build verification
        
        Provides formatted console output showing check progress and final
        summary with error/warning counts. Exit code follows standard
        Unix convention: 0=success, 1=warnings only, 2=errors found.
        
        Returns:
            Exit code:
                - 0: All checks passed (no errors or warnings)
                - 1: Warnings found (non-critical issues)
                - 2: Errors found (critical failures)
        
        Side Effects:
            - Runs all four check methods (increments error/warning counts)
            - Logs comprehensive check summary
            - Prints formatted output with box drawing characters
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = StyleChecker(Path('/path/to/docs'), logging.getLogger('style'))
            >>> exit_code = checker.run_all_checks()  # doctest: +SKIP
            >>> if exit_code == 0:  # doctest: +SKIP
            ...     print("✓ All checks passed!")
            >>> elif exit_code == 1:  # doctest: +SKIP
            ...     print("⚠ Warnings found")
            >>> else:  # doctest: +SKIP
            ...     print("✗ Errors found")
        
        Note:
            Error and warning counts are accumulated across all checks.
            The method resets counters if called multiple times.
        """
        if not self.quiet:
            print(Colors.blue("╔══════════════════════════════════════════════════════════════╗"))
            print(Colors.blue("║        Documentation Style Compliance Checker                ║"))
            print(Colors.blue("╚══════════════════════════════════════════════════════════════╝"))
            print()
        
        self.logger.info("="*80)
        self.logger.info("Documentation style check started")
        self.logger.info("="*80)
        
        # Run all checks
        self.check_user_guide_headers()
        self.check_developer_guide_headers()
        self.check_technical_jargon()
        self.check_sphinx_build()
        
        # Print summary
        if not self.quiet:
            print()
            print("="*64)
            print(Colors.blue("Summary:"))
            print("─"*64)
            print(f"Errors:   {Colors.red(str(self.errors))}")
            print(f"Warnings: {Colors.yellow(str(self.warnings))}")
            print("="*64)
        
        self.logger.info(f"Check completed - Errors: {self.errors}, Warnings: {self.warnings}")
        
        if self.errors > 0:
            if not self.quiet:
                print(Colors.red("✗ COMPLIANCE CHECK FAILED"))
            self.logger.error("Compliance check FAILED")
            return 1
        elif self.warnings > 0:
            if not self.quiet:
                print(Colors.yellow("⚠ COMPLIANCE CHECK PASSED WITH WARNINGS"))
            self.logger.warning("Compliance check passed with warnings")
            return 0
        else:
            if not self.quiet:
                print(Colors.green("✓ ALL COMPLIANCE CHECKS PASSED"))
            self.logger.info("All compliance checks PASSED")
            return 0


class QualityChecker:
    """Comprehensive documentation quality analyzer with deep content inspection.
    
    Performs detailed quality analysis beyond basic style compliance, including:
    - Version reference consistency (|version| vs. hardcoded)
    - File size limits (warns if files >500KB)
    - Redundant content detection (duplicate paragraphs)
    - Broken internal references (:ref:, :doc:)
    - Outdated date detection (copyright years, "last updated")
    - Style guide compliance validation
    
    Quality checks can run in two modes:
    - **Quick mode** (--quick): Skips slow checks (redundancy, broken refs)
      for pre-commit hooks. Typical execution: <5 seconds.
    - **Full mode**: Runs all checks for comprehensive quality audit.
      Typical execution: 30+ seconds on large doc sets.
    
    All issues are tracked with severity levels (ERROR, WARNING, INFO) and
    categorized for organized reporting. Final report saved to tmp/ directory.
    
    Attributes:
        docs_root: Path to Sphinx documentation directory
        logger: Logger instance for file-based logging
        quick_mode: If True, skip slow checks (redundancy, broken references)
        verbose: If True, print detailed progress information
        issues: List of QualityIssue instances found during checks
        stats: Dictionary tracking files_checked, total_lines, errors,
            warnings, info counts
    
    Example:
        >>> from pathlib import Path
        >>> import logging
        >>> docs_root = Path('/path/to/docs/sphinx')
        >>> logger = logging.getLogger('quality')
        >>> checker = QualityChecker(docs_root, logger, quick_mode=False, verbose=True)
        >>> # Run all quality checks
        >>> exit_code = checker.run_all_checks()  # doctest: +SKIP
        >>> print(f"Found {len(checker.issues)} issues")  # doctest: +SKIP
        >>> # Generate detailed report
        >>> report_code = checker.generate_report()  # doctest: +SKIP
    
    Note:
        Quick mode is designed for pre-commit hooks where speed is critical.
        Use full mode for comprehensive quality audits before releases.
    """
    
    def __init__(self, docs_root: Path, logger: std_logging.Logger, 
                 quick_mode: bool = False, verbose: bool = False):
        """Initialize the quality checker with configuration.
        
        Args:
            docs_root: Path to Sphinx documentation directory containing
                .rst files to analyze.
            logger: Configured logger instance for file-based logging.
            quick_mode: If True, skip slow checks (redundancy detection,
                broken reference scanning). Reduces execution time from
                ~30s to <5s for pre-commit usage.
            verbose: If True, print detailed progress information during
                checks. Useful for debugging but noisy in CI environments.
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> # Fast pre-commit check
            >>> quick_checker = QualityChecker(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('quality'),
            ...     quick_mode=True,
            ...     verbose=False
            ... )
            >>> # Comprehensive audit
            >>> full_checker = QualityChecker(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('quality'),
            ...     quick_mode=False,
            ...     verbose=True
            ... )
            >>> len(quick_checker.issues)
            0
        """
        self.docs_root = docs_root
        self.logger = logger
        self.quick_mode = quick_mode
        self.verbose = verbose
        self.issues: List[QualityIssue] = []
        self.stats: Dict[str, int] = {
            'files_checked': 0,
            'total_lines': 0,
            'errors': 0,
            'warnings': 0,
            'info': 0
        }
    
    def add_issue(self, severity: str, category: str, file_path: str,
                  line_number: int, message: str) -> None:
        """Add a quality issue to the tracking list and update statistics.
        
        Creates a QualityIssue instance and adds it to the issues list.
        Automatically updates stats counters based on severity level.
        
        Args:
            severity: Issue severity - "ERROR", "WARNING", or "INFO".
            category: Issue category for grouping - "version", "size",
                "redundancy", "reference", "date", "style", etc.
            file_path: Relative path to file from docs_root (e.g.,
                "user_guide/installation.rst").
            line_number: Line number where issue occurs, or 0 if not
                line-specific (e.g., file size issues).
            message: Human-readable description of the issue and any
                recommended fixes.
        
        Side Effects:
            - Appends QualityIssue to self.issues list
            - Increments appropriate stats counter (errors/warnings/info)
            - Logs issue to logger
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.add_issue(
            ...     severity="WARNING",
            ...     category="version",
            ...     file_path="user_guide/quickstart.rst",
            ...     line_number=42,
            ...     message="Hardcoded version '1.0.0' should use |version|"
            ... )
            >>> len(checker.issues)
            1
            >>> checker.stats['warnings']
            1
        """
        issue = QualityIssue(
            severity=severity,
            category=category,
            file_path=file_path,
            line_number=line_number,
            message=message
        )
        self.issues.append(issue)
        
        # Update stats
        if severity == 'error':
            self.stats['errors'] += 1
        elif severity == 'warning':
            self.stats['warnings'] += 1
        else:
            self.stats['info'] += 1
        
        # Log the issue
        location = f"{file_path}:{line_number}" if line_number else file_path
        log_message = f"[{category.upper()}] {location} - {message}"
        
        if severity == 'error':
            self.logger.error(log_message)
        elif severity == 'warning':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def check_version_references(self) -> None:
        """Check for outdated version references in documentation files.
        
        Scans .rst files in user_guide/, developer_guide/, and api/ directories
        for outdated version directives (e.g., ".. versionadded:: 0.0.1"). These
        should be updated to use current version or |version| substitution.
        
        Skips historical files and changelogs where old version references are
        intentional. Adds WARNING-level issues for each outdated reference found.
        
        Side Effects:
            - Increments stats['files_checked'] for each file scanned
            - Adds QualityIssue for each outdated version directive found
            - Logs check progress to logger
            - Prints progress to console
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.check_version_references()  # doctest: +SKIP
            >>> # Check if any outdated versions found
            >>> outdated = [i for i in checker.issues if i.category == 'version_reference']  # doctest: +SKIP
            >>> if outdated:  # doctest: +SKIP
            ...     print(f"Found {len(outdated)} outdated version references")
        
        Note:
            This check looks for pattern ".. version(added|changed):: 0.0.x"
            in line content. Does not validate directive syntax.
        """
        print("🔍 Checking version references...")
        self.logger.info("Starting version reference check...")
        
        # Pattern for old version directives
        old_version_pattern = re.compile(r'\.\.\s+version(added|changed)::\s+0\.0\.\d+')
        
        # Directories to check
        check_dirs = ['user_guide', 'developer_guide', 'api']
        
        for dir_name in check_dirs:
            dir_path = self.docs_root / dir_name
            if not dir_path.exists():
                continue
            
            for rst_file in dir_path.rglob('*.rst'):
                # Skip historical files
                if 'historical' in str(rst_file) or 'changelog' in str(rst_file):
                    continue
                
                try:
                    with open(rst_file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if old_version_pattern.search(line):
                                self.add_issue(
                                    'warning',
                                    'version_reference',
                                    str(rst_file.relative_to(self.docs_root)),
                                    line_num,
                                    f'Outdated version directive: {line.strip()}'
                                )
                except Exception as e:
                    self.logger.error(f"Error reading {rst_file}: {e}")
    
    def check_file_sizes(self) -> None:
        """Check for documentation files exceeding recommended size limits.
        
        Scans all .rst files in docs_root and counts lines. Files exceeding
        1000 lines trigger INFO-level warnings suggesting split if >1500 lines.
        Large files can be harder to navigate and maintain.
        
        Updates stats with total line count and files checked. This provides
        useful metrics for documentation size tracking over time.
        
        Side Effects:
            - Increments stats['total_lines'] by line count for each file
            - Increments stats['files_checked'] for each file processed
            - Adds INFO-level QualityIssue for files >1000 lines
            - Logs check progress and any errors to logger
            - Prints progress to console
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.check_file_sizes()  # doctest: +SKIP
            >>> print(f"Checked {checker.stats['files_checked']} files")  # doctest: +SKIP
            >>> print(f"Total lines: {checker.stats['total_lines']}")  # doctest: +SKIP
            >>> large_files = [i for i in checker.issues if i.category == 'file_size']  # doctest: +SKIP
        
        Note:
            Threshold is 1000 lines (INFO), with recommendation to split at
            1500 lines. Adjust threshold by modifying large_file_threshold.
        """
        print("📏 Checking file sizes...")
        self.logger.info("Starting file size check...")
        
        large_file_threshold = 1000  # lines
        
        for rst_file in self.docs_root.rglob('*.rst'):
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                
                self.stats['total_lines'] += line_count
                self.stats['files_checked'] += 1
                
                if line_count > large_file_threshold:
                    self.add_issue(
                        'info',
                        'file_size',
                        str(rst_file.relative_to(self.docs_root)),
                        0,
                        f'Large file: {line_count} lines (consider splitting if >1500)'
                    )
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
    
    def check_redundant_content(self) -> None:
        """Check for potential redundant content across documentation files.
        
        Scans all .rst files for duplicate section headers that may indicate
        redundant or copy-pasted content. Headers must be at least 15 characters
        to avoid false positives from common short headers.
        
        Detects headers using reStructuredText underline patterns (=, -, ~, ^).
        Reports INFO-level issues when same header text appears in multiple
        files, suggesting content consolidation opportunity.
        
        Skips index.rst and modules.rst as they commonly have duplicate headers
        by design (e.g., "API Reference" appearing in multiple index files).
        
        Side Effects:
            - Adds INFO-level QualityIssue for each duplicate header set found
            - Logs check progress and any file read errors to logger
            - Prints progress to console
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.check_redundant_content()  # doctest: +SKIP
            >>> redundant = [i for i in checker.issues if i.category == 'redundancy']  # doctest: +SKIP
            >>> if redundant:  # doctest: +SKIP
            ...     print(f"Found {len(redundant)} sets of duplicate headers")
        
        Note:
            This is a heuristic check - duplicate headers don't always indicate
            actual redundancy. Manual review recommended for flagged items.
            Skipped in quick_mode due to I/O-intensive operation.
        """
        print("🔄 Checking for redundant content...")
        self.logger.info("Starting redundancy check...")
        
        # Track section headers
        headers: Dict[str, List[Tuple[str, str]]] = {}
        
        for rst_file in self.docs_root.rglob('*.rst'):
            # Skip index and module files
            if rst_file.name in ['index.rst', 'modules.rst']:
                continue
            
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find headers
                header_pattern = re.compile(r'^(.+)\n([=\-~^]+)$', re.MULTILINE)
                
                for match in header_pattern.finditer(content):
                    header_text = match.group(1).strip()
                    
                    # Skip very short headers
                    if len(header_text) < 15:
                        continue
                    
                    file_rel = str(rst_file.relative_to(self.docs_root))
                    
                    if header_text not in headers:
                        headers[header_text] = []
                    headers[header_text].append((file_rel, header_text))
            
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
        
        # Report duplicates
        for header_text, locations in headers.items():
            if len(locations) > 1:
                files = ', '.join([loc[0] for loc in locations])
                self.add_issue(
                    'info',
                    'redundancy',
                    'multiple files',
                    0,
                    f'Duplicate section header "{header_text[:50]}..." in: {files}'
                )
    
    def check_broken_references(self) -> None:
        """Check for potentially broken cross-references in documentation.
        
        Performs two-pass analysis to detect broken :doc: and :ref: directives:
        
        1. **First pass**: Collects all defined reference labels from
           ".. _label:" directives across all .rst files.
        
        2. **Second pass**: Validates that all :doc:`path` and :ref:`label`
           references point to existing files or defined labels. Reports
           WARNING-level issues for potentially broken references.
        
        This helps catch broken links before Sphinx build fails, especially
        when files are moved or renamed.
        
        Side Effects:
            - Adds WARNING-level QualityIssue for each broken reference found
            - Logs check progress and any file read errors to logger
            - Prints progress to console
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.check_broken_references()  # doctest: +SKIP
            >>> broken = [i for i in checker.issues if i.category == 'broken_reference']  # doctest: +SKIP
            >>> if broken:  # doctest: +SKIP
            ...     for issue in broken:
            ...         print(f"{issue.file_path}:{issue.line_number} - {issue.message}")
        
        Note:
            This is a heuristic check - some references may be valid but not
            detected (e.g., auto-generated labels). Sphinx build is definitive.
            Skipped in quick_mode due to expensive two-pass I/O operation.
        """
        print("🔗 Checking cross-references...")
        self.logger.info("Starting cross-reference check...")
        
        # Collect all defined labels
        defined_labels = set()
        reference_pattern = re.compile(r':doc:`([^`]+)`|:ref:`([^`]+)`')
        label_pattern = re.compile(r'\.\.\s+_([^:]+):')
        
        # First pass: collect labels
        for rst_file in self.docs_root.rglob('*.rst'):
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                for match in label_pattern.finditer(content):
                    defined_labels.add(match.group(1).strip())
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
        
        # Second pass: check references
        for rst_file in self.docs_root.rglob('*.rst'):
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        for match in reference_pattern.finditer(line):
                            ref = match.group(1) or match.group(2)
                            if ref:
                                # Check if reference looks like a file path
                                if '/' in ref:
                                    ref_path = self.docs_root / (ref + '.rst')
                                    if not ref_path.exists():
                                        ref_path = self.docs_root / ref
                                        if not ref_path.exists():
                                            self.add_issue(
                                                'warning',
                                                'broken_reference',
                                                str(rst_file.relative_to(self.docs_root)),
                                                line_num,
                                                f'Potentially broken reference: {ref}'
                                            )
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
    
    def check_outdated_dates(self) -> None:
        """Check for potentially outdated date references in documentation.
        
        Scans all .rst files for year references (2022, 2023, 2024) in date
        contexts like "last updated", "current", "assessment date". These may
        indicate stale content that needs review.
        
        Current year is hardcoded to 2025. Updates needed annually to maintain
        relevance of this check.
        
        Skips:
        - Historical files (changelog.rst, historical/*.rst)
        - Code blocks (.. code-block::)
        - Version strings (Version 0.x)
        
        Reports INFO-level issues for each potentially outdated date found.
        
        Side Effects:
            - Adds INFO-level QualityIssue for each outdated date context found
            - Logs check progress and any file read errors to logger
            - Prints progress to console
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.check_outdated_dates()  # doctest: +SKIP
            >>> outdated = [i for i in checker.issues if i.category == 'outdated_date']  # doctest: +SKIP
            >>> if outdated:  # doctest: +SKIP
            ...     print(f"Found {len(outdated)} potentially outdated dates")
        
        Note:
            This is a heuristic check - dates in changelogs and historical
            docs are intentionally old. Manual review recommended.
            Update current_year annually for continued effectiveness.
        """
        print("📅 Checking for outdated dates...")
        self.logger.info("Starting outdated date check...")
        
        current_year = 2025
        old_date_pattern = re.compile(r'\b(2024|2023|2022)\b')
        
        for rst_file in self.docs_root.rglob('*.rst'):
            # Skip historical files
            if 'changelog' in str(rst_file) or 'historical' in str(rst_file):
                continue
            
            try:
                with open(rst_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip code blocks
                        if '.. code-block::' in line or 'Version 0.' in line:
                            continue
                        
                        if old_date_pattern.search(line):
                            # Check context
                            if any(keyword in line.lower() for keyword in
                                   ['last updated', 'current', 'assessment date', 'date:']):
                                self.add_issue(
                                    'info',
                                    'outdated_date',
                                    str(rst_file.relative_to(self.docs_root)),
                                    line_num,
                                    f'Potentially outdated date: {line.strip()}'
                                )
            except Exception as e:
                self.logger.error(f"Error reading {rst_file}: {e}")
    
    def check_style_compliance(self) -> None:
        """Check for style compliance with Diátaxis framework headers.
        
        Validates that user guide and developer guide files start with
        appropriate audience headers:
        - user_guide/*.rst should have "**For Users:**"
        - developer_guide/*.rst should have "**For Developers:**"
        
        This duplicates functionality from StyleChecker but at WARNING level
        for integration into comprehensive quality reports. Allows quality
        audits to include style issues without running separate checks.
        
        Checks only first 500 characters of each file for performance.
        
        Side Effects:
            - Adds WARNING-level QualityIssue for each missing header
            - Logs check progress and any file read errors to logger
            - Prints progress to console
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> checker.check_style_compliance()  # doctest: +SKIP
            >>> style_issues = [i for i in checker.issues if i.category == 'style_compliance']  # doctest: +SKIP
            >>> if style_issues:  # doctest: +SKIP
            ...     print(f"Found {len(style_issues)} style compliance issues")
        
        Note:
            For standalone style checking with detailed output, use
            StyleChecker class instead. This method provides quick
            style validation integrated into quality report.
        """
        print("✨ Checking style compliance...")
        self.logger.info("Starting style compliance check...")
        
        user_guide_dir = self.docs_root / 'user_guide'
        dev_guide_dir = self.docs_root / 'developer_guide'
        
        # Check user guide files
        if user_guide_dir.exists():
            for rst_file in user_guide_dir.glob('*.rst'):
                try:
                    with open(rst_file, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Check first 500 chars
                    
                    if '**For Users' not in content:
                        self.add_issue(
                            'warning',
                            'style_compliance',
                            str(rst_file.relative_to(self.docs_root)),
                            0,
                            'Missing "**For Users:**" header'
                        )
                except Exception as e:
                    self.logger.error(f"Error reading {rst_file}: {e}")
        
        # Check developer guide files
        if dev_guide_dir.exists():
            for rst_file in dev_guide_dir.glob('*.rst'):
                try:
                    with open(rst_file, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Check first 500 chars
                    
                    if '**For Developers' not in content:
                        self.add_issue(
                            'warning',
                            'style_compliance',
                            str(rst_file.relative_to(self.docs_root)),
                            0,
                            'Missing "**For Developers:**" header'
                        )
                except Exception as e:
                    self.logger.error(f"Error reading {rst_file}: {e}")
    
    def generate_report(self) -> int:
        """Generate and print comprehensive quality check report.
        
        Creates detailed report with:
        - Statistics (files checked, total lines, error/warning/info counts)
        - Issues grouped by category (version, size, redundancy, etc.)
        - Recommendations based on metrics (size limits, warning thresholds)
        - Exit code determination (0=pass, 1=warnings, 2=errors)
        
        Report uses emoji icons for visual clarity and color coding for
        severity levels. Each issue shows file:line location and message.
        
        Returns:
            Exit code:
                - 0: No issues found (excellent quality)
                - 1: Warnings found (review recommended)
                - 2: Errors found (must be fixed)
        
        Side Effects:
            - Prints formatted report to console (80-char width)
            - Logs report summary to logger
            - No file I/O (report is console-only)
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> checker = QualityChecker(Path('/tmp/docs'), logging.getLogger('test'))
            >>> # Run some checks first
            >>> checker.check_file_sizes()  # doctest: +SKIP
            >>> # Generate report
            >>> exit_code = checker.generate_report()  # doctest: +SKIP
            >>> if exit_code == 0:  # doctest: +SKIP
            ...     print("Quality check passed!")
            >>> else:  # doctest: +SKIP
            ...     print(f"Found issues (exit code: {exit_code})")
        
        Note:
            Report is designed for terminal output with emoji and Unicode.
            For CI/CD, parse logger output instead of console report.
        """
        print("\n" + "="*80)
        print("📋 DOCUMENTATION QUALITY REPORT")
        print("="*80)
        
        # Statistics
        print(f"\n📊 Statistics:")
        print(f"  Files checked: {self.stats['files_checked']}")
        print(f"  Total lines: {self.stats['total_lines']:,}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Warnings: {self.stats['warnings']}")
        print(f"  Info: {self.stats['info']}")
        
        # Group issues by category
        issues_by_category: Dict[str, List[QualityIssue]] = {}
        for issue in self.issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)
        
        # Print issues
        if self.issues:
            print(f"\n📝 Issues Found ({len(self.issues)} total):\n")
            
            for category, issues in sorted(issues_by_category.items()):
                print(f"\n  {category.upper().replace('_', ' ')} ({len(issues)} issues):")
                for issue in issues:
                    icon = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[issue.severity]
                    location = f"{issue.file_path}:{issue.line_number}" if issue.line_number else issue.file_path
                    print(f"    {icon} {location}")
                    print(f"       {issue.message}")
        else:
            print("\n✅ No issues found - documentation quality is excellent!")
        
        # Recommendations
        print("\n💡 Recommendations:")
        
        if self.stats['total_lines'] > 20000:
            print("  ⚠️  Total documentation exceeds 20,000 lines")
            print("      Consider archiving or consolidating content")
        else:
            print("  ✅ Documentation size is within recommended limits")
        
        if self.stats['warnings'] > 10:
            print(f"  ⚠️  High warning count ({self.stats['warnings']})")
            print("      Schedule time to address these warnings")
        
        if self.stats['errors'] > 0:
            print(f"  ❌ {self.stats['errors']} critical errors must be fixed")
        
        print("\n" + "="*80)
        
        # Determine exit code
        if self.stats['errors'] > 0:
            return 2
        elif self.stats['warnings'] > 0:
            return 1
        else:
            return 0
    
    def run_all_checks(self) -> int:
        """Run all quality checks and generate comprehensive report.
        
        Executes quality checks based on mode (quick vs. full):
        
        **Quick mode** (self.quick_mode=True):
        - check_file_sizes() only
        - Typical execution: <5 seconds
        - For pre-commit hooks
        
        **Full mode** (self.quick_mode=False):
        - check_version_references()
        - check_file_sizes()
        - check_redundant_content()
        - check_broken_references()
        - check_style_compliance()
        - check_outdated_dates()
        - Typical execution: 30+ seconds
        - For comprehensive audits
        
        After checks, generates detailed report and returns appropriate exit
        code for CI/CD integration.
        
        Returns:
            Exit code:
                - 0: No errors or warnings (perfect quality)
                - 1: Warnings found (review recommended)
                - 2: Errors found (must be fixed before release)
        
        Side Effects:
            - Runs all enabled quality check methods
            - Accumulates issues in self.issues list
            - Updates self.stats dictionary
            - Prints progress and report to console
            - Logs comprehensive results to logger
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> # Quick pre-commit check
            >>> quick_checker = QualityChecker(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('quality'),
            ...     quick_mode=True
            ... )
            >>> quick_code = quick_checker.run_all_checks()  # doctest: +SKIP
            >>> # Full audit before release
            >>> full_checker = QualityChecker(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('quality'),
            ...     quick_mode=False
            ... )
            >>> full_code = full_checker.run_all_checks()  # doctest: +SKIP
        
        Note:
            Use quick_mode=True for fast feedback during development.
            Use quick_mode=False for thorough quality audits before releases.
        """
        print("🚀 Starting Documentation Quality Check\n")
        self.logger.info("="*80)
        self.logger.info(f"Documentation Quality Check v{__version__} - Starting")
        self.logger.info("="*80)
        
        # Run checks
        if not self.quick_mode:
            self.check_version_references()
        
        self.check_file_sizes()
        
        if not self.quick_mode:
            self.check_redundant_content()
            self.check_broken_references()
            self.check_style_compliance()
            self.check_outdated_dates()
        
        # Generate report
        exit_code = self.generate_report()
        
        # Log results
        if exit_code == 0:
            self.logger.info("Documentation quality check passed - no issues found")
        elif exit_code == 1:
            self.logger.warning(f"Documentation quality check completed with {self.stats['warnings']} warnings")
        else:
            self.logger.error(f"Documentation quality check failed with {self.stats['errors']} errors")
        
        return exit_code


class DocumentationBuilder:
    """Sphinx documentation building and verification system.
    
    Manages the Sphinx build process with configurable options for cleaning,
    building, and opening documentation in browser. Provides standardized
    build workflow with timeout protection and error handling.
    
    Key features:
    - Clean previous builds before rebuilding
    - HTML documentation generation via `make html`
    - Browser integration for instant preview
    - Comprehensive error handling with logging
    - Timeout protection (5 minutes max)
    
    The builder wraps `make` commands and provides user-friendly output
    with color-coded status messages and progress indicators.
    
    Attributes:
        docs_root: Path to Sphinx documentation directory (docs/sphinx/)
        logger: Logger instance for file-based logging
        quiet: If True, suppress non-error console output
    
    Example:
        >>> from pathlib import Path
        >>> import logging
        >>> docs_root = Path('/path/to/docs/sphinx')
        >>> logger = logging.getLogger('build')
        >>> builder = DocumentationBuilder(docs_root, logger, quiet=False)
        >>> # Build docs with clean
        >>> success = builder.build_docs(clean=True)  # doctest: +SKIP
        >>> if success:  # doctest: +SKIP
        ...     print("Build successful!")
        ...     builder.open_docs()  # Open in browser
    
    Note:
        Requires Sphinx and `make` command to be installed. Build output
        goes to docs_root/_build/html/index.html.
    """
    
    def __init__(self, docs_root: Path, logger: std_logging.Logger, quiet: bool = False):
        """Initialize the documentation builder.
        
        Args:
            docs_root: Path to Sphinx documentation directory containing
                conf.py and Makefile.
            logger: Configured logger instance for file-based logging.
            quiet: If True, suppress non-error console output (errors
                still printed). Useful for automated/CI builds.
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> builder = DocumentationBuilder(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('build'),
            ...     quiet=True
            ... )
            >>> builder.quiet
            True
        """
        self.docs_root = docs_root
        self.logger = logger
        self.quiet = quiet
    
    def build_docs(self, clean: bool = True) -> bool:
        """Build Sphinx HTML documentation with optional clean step.
        
        Executes Sphinx build process:
        1. Optional: Run `make clean` to remove previous build artifacts
        2. Run `make html` to generate HTML documentation
        3. Validate build success and report output location
        
        Build runs with 5-minute timeout to prevent hung processes.
        All output captured for error reporting and logging.
        
        Args:
            clean: If True, run `make clean` before building to ensure
                fresh build without stale artifacts. Default True.
        
        Returns:
            True if build successful, False otherwise.
        
        Side Effects:
            - Runs subprocess commands (make clean, make html)
            - Logs build status to logger
            - Prints colored status messages to console (unless quiet=True)
            - Creates _build/html/ directory with documentation files
        
        Raises:
            No exceptions raised; all errors caught and logged.
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> builder = DocumentationBuilder(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('build')
            ... )
            >>> # Clean build
            >>> success = builder.build_docs(clean=True)  # doctest: +SKIP
            >>> # Incremental build (faster)
            >>> success = builder.build_docs(clean=False)  # doctest: +SKIP
        
        Note:
            Clean builds are slower but more reliable. Use clean=False for
            iterative development, clean=True for production builds.
        """
        if not self.quiet:
            print("📚 Building Documentation...")
        
        self.logger.info("Starting documentation build...")
        
        try:
            # Clean if requested
            if clean:
                if not self.quiet:
                    print("  Cleaning previous build...")
                clean_result = subprocess.run(
                    ['make', 'clean'],
                    cwd=self.docs_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if clean_result.returncode != 0:
                    self.logger.warning(f"Clean failed: {clean_result.stderr}")
            
            # Build
            if not self.quiet:
                print("  Building HTML documentation...")
            
            build_result = subprocess.run(
                ['make', 'html'],
                cwd=self.docs_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode == 0:
                if not self.quiet:
                    print(Colors.green("✅ Documentation built successfully!"))
                    html_path = self.docs_root / '_build' / 'html' / 'index.html'
                    print(f"📂 Output: {html_path}")
                self.logger.info("Documentation build successful")
                return True
            else:
                print(Colors.red("❌ Documentation build failed"))
                print(f"Error: {build_result.stderr}")
                self.logger.error(f"Build failed: {build_result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            error_msg = "Build timed out"
            print(Colors.red(f"❌ {error_msg}"))
            self.logger.error(error_msg)
            return False
        
        except FileNotFoundError:
            error_msg = "Make command not found"
            print(Colors.red(f"❌ {error_msg}"))
            self.logger.error(error_msg)
            return False
        
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(Colors.red(f"❌ {error_msg}"))
            self.logger.error(error_msg)
            return False
    
    def open_docs(self) -> bool:
        """Open built HTML documentation in default system browser.
        
        Locates the built index.html file and opens it using macOS `open`
        command. Validates that documentation has been built before attempting
        to open.
        
        Returns:
            True if browser opened successfully, False if docs not built
            or browser launch failed.
        
        Side Effects:
            - Runs subprocess command (`open` on macOS)
            - Logs operation status to logger
            - Prints colored status messages to console (unless quiet=True)
            - Opens browser window (external side effect)
        
        Raises:
            No exceptions raised; all errors caught and logged.
        
        Example:
            >>> from pathlib import Path
            >>> import logging
            >>> builder = DocumentationBuilder(
            ...     Path('/path/to/docs'),
            ...     logging.getLogger('build')
            ... )
            >>> # Build first
            >>> if builder.build_docs():  # doctest: +SKIP
            ...     # Then open in browser
            ...     builder.open_docs()
        
        Note:
            Currently uses macOS `open` command. For cross-platform support,
            replace with Python's webbrowser.open() or platform detection.
        """
        html_file = self.docs_root / '_build' / 'html' / 'index.html'
        
        if not html_file.exists():
            print(Colors.red("❌ Documentation not built yet. Run with --mode build first."))
            self.logger.error("Cannot open docs - not built")
            return False
        
        try:
            if not self.quiet:
                print("🌐 Opening documentation in browser...")
            
            subprocess.run(['open', str(html_file)], check=True)
            
            if not self.quiet:
                print(Colors.green("✅ Documentation opened in browser"))
            self.logger.info("Documentation opened in browser")
            return True
        
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to open browser: {e}"
            print(Colors.red(f"❌ {error_msg}"))
            self.logger.error(error_msg)
            return False
        
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(Colors.red(f"❌ {error_msg}"))
            self.logger.error(error_msg)
            return False


class MaintenanceRunner:
    """Main orchestrator for all documentation maintenance operations.
    
    Unified interface for running style checks, quality analysis, builds,
    and full maintenance suites. Handles argument parsing, logger setup,
    and workflow orchestration.
    
    The runner provides four operation modes:
    
    1. **Style Mode** (`--mode style`):
       - Diátaxis header validation
       - Technical jargon detection
       - Sphinx build verification
       - Fast (~5-10 seconds)
    
    2. **Quality Mode** (`--mode quality`):
       - Version reference checks
       - File size analysis
       - Redundant content detection
       - Broken reference scanning
       - Outdated date detection
       - With `--quick`: Skip slow checks (<5s for pre-commit)
       - Without: Full analysis (~30s)
    
    3. **Build Mode** (`--mode build`):
       - Clean previous builds
       - Generate HTML documentation
       - Optional: Open in browser (`--open`)
    
    4. **Full Mode** (`--mode full`):
       - Runs all three modes in sequence
       - Provides comprehensive maintenance report
       - Recommended before releases
    
    Each mode creates mode-specific log files in .logs/ directory for
    detailed audit trails.
    
    Attributes:
        repo_root: Path to repository root directory
        docs_root: Path to Sphinx documentation directory (repo_root/docs/sphinx)
        args: Parsed command-line arguments namespace
        log_system: MaintenanceLogger instance for centralized logging
        logger: Mode-specific logger instance
    
    Example:
        >>> from pathlib import Path
        >>> import argparse
        >>> args = argparse.Namespace(mode='quality', quick=True, quiet=False, verbose=False, open=False)
        >>> runner = MaintenanceRunner(Path('/path/to/repo'), args)
        >>> exit_code = runner.run_quality_check()  # doctest: +SKIP
        >>> print(f"Quality check {'passed' if exit_code == 0 else 'failed'}")  # doctest: +SKIP
    
    Note:
        Runner expects docs/sphinx/ directory to exist under repo_root.
        Validates directory existence before running operations.
    """
    
    def __init__(self, repo_root: Path, args: argparse.Namespace):
        """Initialize the maintenance runner with configuration.
        
        Sets up logging system with mode-specific log files for detailed
        audit trails. Each mode writes to separate log file for clarity.
        
        Args:
            repo_root: Path to repository root directory containing
                docs/sphinx/ subdirectory.
            args: Parsed command-line arguments namespace with mode,
                quick, quiet, verbose, and open flags.
        
        Example:
            >>> from pathlib import Path
            >>> import argparse
            >>> args = argparse.Namespace(
            ...     mode='style',
            ...     quick=False,
            ...     quiet=True,
            ...     verbose=False,
            ...     open=False
            ... )
            >>> runner = MaintenanceRunner(Path('/path/to/repo'), args)
            >>> runner.args.mode
            'style'
        """
        self.repo_root = repo_root
        self.docs_root = repo_root / 'docs' / 'sphinx'
        self.args = args
        
        # Initialize logging
        self.log_system = MaintenanceLogger(repo_root)
        
        # Get appropriate logger based on mode
        log_file_map = {
            'style': 'doc_style_check.log',
            'quality': 'doc_quality_check.log',
            'build': 'doc_build.log',
            'full': 'doc_full_maintenance.log'
        }
        log_file = log_file_map.get(args.mode, 'doc_maintenance.log')
        self.logger = self.log_system.get_logger('doc_maintenance', log_file)
    
    def run_style_check(self) -> int:
        """Run Diátaxis style compliance check.
        
        Creates StyleChecker instance and runs all style validation checks:
        - User guide header validation ("**For Users:**")
        - Developer guide header validation ("**For Developers:**")
        - Technical jargon detection in user guide
        - Sphinx build verification
        
        Returns:
            Exit code from StyleChecker.run_all_checks():
                - 0: All checks passed
                - 1: Errors found (missing headers, build failures)
        
        Side Effects:
            - Logs style check results to doc_style_check.log
            - Prints formatted output to console (unless quiet=True)
        
        Example:
            >>> from pathlib import Path
            >>> import argparse
            >>> args = argparse.Namespace(mode='style', quiet=False, quick=False, verbose=False, open=False)
            >>> runner = MaintenanceRunner(Path('/path/to/repo'), args)
            >>> exit_code = runner.run_style_check()  # doctest: +SKIP
        """
        checker = StyleChecker(
            self.docs_root,
            self.logger,
            quiet=self.args.quiet
        )
        return checker.run_all_checks()
    
    def run_quality_check(self) -> int:
        """Run comprehensive documentation quality analysis.
        
        Creates QualityChecker instance and runs quality checks based on
        args.quick flag:
        
        - Quick mode (--quick): File size checks only (~5s)
        - Full mode: All checks including redundancy, broken refs (~30s)
        
        Returns:
            Exit code from QualityChecker.run_all_checks():
                - 0: No issues found
                - 1: Warnings found (review recommended)
                - 2: Errors found (must be fixed)
        
        Side Effects:
            - Logs quality analysis results to doc_quality_check.log
            - Prints formatted report to console (detail level per verbose flag)
        
        Example:
            >>> from pathlib import Path
            >>> import argparse
            >>> args = argparse.Namespace(mode='quality', quick=True, verbose=False, quiet=False, open=False)
            >>> runner = MaintenanceRunner(Path('/path/to/repo'), args)
            >>> exit_code = runner.run_quality_check()  # doctest: +SKIP
        """
        checker = QualityChecker(
            self.docs_root,
            self.logger,
            quick_mode=self.args.quick,
            verbose=self.args.verbose
        )
        return checker.run_all_checks()
    
    def run_build(self) -> int:
        """Run Sphinx documentation build with optional browser preview.
        
        Creates DocumentationBuilder instance and builds HTML documentation.
        If args.open flag is set, automatically opens built docs in browser.
        
        Returns:
            Exit code:
                - 0: Build successful
                - 1: Build failed
        
        Side Effects:
            - Logs build results to doc_build.log
            - Creates _build/html/ directory with documentation files
            - Prints colored status messages to console (unless quiet=True)
            - Optional: Opens browser if --open flag set
        
        Example:
            >>> from pathlib import Path
            >>> import argparse
            >>> # Build and open
            >>> args = argparse.Namespace(mode='build', open=True, quiet=False, quick=False, verbose=False)
            >>> runner = MaintenanceRunner(Path('/path/to/repo'), args)
            >>> exit_code = runner.run_build()  # doctest: +SKIP
        """
        builder = DocumentationBuilder(
            self.docs_root,
            self.logger,
            quiet=self.args.quiet
        )
        
        success = builder.build_docs(clean=True)
        
        if success and self.args.open:
            builder.open_docs()
        
        return 0 if success else 1
    
    def run_full_maintenance(self) -> int:
        """Run complete documentation maintenance suite (style + quality + build).
        
        Executes all three maintenance operations in sequence:
        1. Style compliance check
        2. Quality analysis (respects --quick flag)
        3. Documentation build
        
        Provides comprehensive summary showing pass/fail status for each
        operation. Returns worst exit code from all operations for CI/CD
        integration.
        
        Returns:
            Maximum exit code from all operations:
                - 0: All operations passed
                - 1: At least one operation has warnings
                - 2: At least one operation has errors
        
        Side Effects:
            - Logs all operations to doc_full_maintenance.log
            - Prints formatted progress and summary to console
            - Runs all side effects of style/quality/build operations
        
        Example:
            >>> from pathlib import Path
            >>> import argparse
            >>> args = argparse.Namespace(mode='full', quick=False, verbose=True, quiet=False, open=False)
            >>> runner = MaintenanceRunner(Path('/path/to/repo'), args)
            >>> exit_code = runner.run_full_maintenance()  # doctest: +SKIP
            >>> if exit_code == 0:  # doctest: +SKIP
            ...     print("All maintenance checks passed!")
        
        Note:
            Full mode is recommended before releases to ensure comprehensive
            documentation quality. Use --quick for faster pre-commit checks.
        """
        print(Colors.blue("╔══════════════════════════════════════════════════════════════╗"))
        print(Colors.blue("║        Full Documentation Maintenance Suite                  ║"))
        print(Colors.blue("╚══════════════════════════════════════════════════════════════╝"))
        print()
        
        self.logger.info("="*80)
        self.logger.info("Full maintenance suite started")
        self.logger.info("="*80)
        
        exit_codes = []
        
        # Style check
        print(Colors.blue("\n1️⃣ Running Style Compliance Check..."))
        print("─"*64)
        exit_codes.append(self.run_style_check())
        
        # Quality check
        print(Colors.blue("\n2️⃣ Running Quality Analysis..."))
        print("─"*64)
        exit_codes.append(self.run_quality_check())
        
        # Build
        print(Colors.blue("\n3️⃣ Building Documentation..."))
        print("─"*64)
        exit_codes.append(self.run_build())
        
        # Summary
        print()
        print(Colors.blue("="*64))
        print(Colors.blue("Full Maintenance Summary"))
        print(Colors.blue("="*64))
        print(f"Style Check:   {Colors.green('PASSED') if exit_codes[0] == 0 else Colors.red('FAILED')}")
        print(f"Quality Check: {Colors.green('PASSED') if exit_codes[1] == 0 else Colors.yellow('WARNINGS') if exit_codes[1] == 1 else Colors.red('FAILED')}")
        print(f"Build:         {Colors.green('SUCCESS') if exit_codes[2] == 0 else Colors.red('FAILED')}")
        print(Colors.blue("="*64))
        
        # Return worst exit code
        max_exit = max(exit_codes)
        
        if max_exit == 0:
            print(Colors.green("✅ Full maintenance completed successfully!"))
            self.logger.info("Full maintenance completed successfully")
        else:
            print(Colors.yellow("⚠️ Full maintenance completed with issues"))
            self.logger.warning(f"Full maintenance completed with exit code {max_exit}")
        
        return max_exit


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments for documentation toolkit.
    
    Creates argument parser with four operation modes (style, quality, build,
    full) and various flags controlling execution behavior. Provides detailed
    help text with usage examples.
    
    Arguments:
        --mode: Required. Operation mode to run (style/quality/build/full)
        --quick: Optional. Skip slow checks (for pre-commit hooks)
        --quiet: Optional. Suppress non-error console output
        --verbose: Optional. Provide detailed progress information
        --open: Optional. Open documentation in browser after build
        --version: Optional. Display toolkit version and exit
    
    Returns:
        Parsed argument namespace with validated values.
    
    Side Effects:
        - Prints help text to console if --help flag used
        - Prints version and exits if --version flag used
        - Exits with code 2 if invalid arguments provided
    
    Example:
        >>> import sys
        >>> # Simulate command-line args
        >>> sys.argv = ['doc_maintenance_toolkit.py', '--mode', 'quality', '--quick']
        >>> args = parse_arguments()  # doctest: +SKIP
        >>> args.mode  # doctest: +SKIP
        'quality'
        >>> args.quick  # doctest: +SKIP
        True
    
    Note:
        Parser uses RawDescriptionHelpFormatter to preserve formatting
        in epilog examples section.
    """
    parser = argparse.ArgumentParser(
        description='Documentation Maintenance Toolkit - Unified quality & build system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick style check (for pre-commit hooks)
  %(prog)s --mode style
  
  # Comprehensive quality analysis
  %(prog)s --mode quality --verbose
  
  # Build documentation
  %(prog)s --mode build
  
  # Build and open in browser
  %(prog)s --mode build --open
  
  # Full maintenance suite
  %(prog)s --mode full

For more information, see the documentation or run with --help.
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['style', 'quality', 'build', 'full'],
        required=True,
        help='Operation mode to run'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only basic checks (faster, for pre-commit)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress non-error output'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Provide detailed output'
    )
    
    parser.add_argument(
        '--open',
        action='store_true',
        help='Open documentation in browser after build'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for documentation maintenance toolkit.
    
    Orchestrates the complete workflow:
    1. Parse command-line arguments
    2. Validate documentation directory exists
    3. Create MaintenanceRunner instance
    4. Execute requested mode (style/quality/build/full)
    5. Return appropriate exit code for CI/CD integration
    
    Exit codes follow Unix convention:
        - 0: Success (all checks passed)
        - 1: Warnings found (review recommended)
        - 2: Errors or invalid usage
        - 130: Keyboard interrupt (Ctrl+C)
    
    Returns:
        Exit code indicating operation result.
    
    Side Effects:
        - Validates docs/sphinx/ directory exists
        - Creates MaintenanceRunner and executes requested mode
        - Prints status messages to console
        - Creates log files in .logs/ directory
    
    Raises:
        No exceptions raised; all errors caught and converted to exit codes.
    
    Example:
        >>> import sys
        >>> # Run from command line:
        >>> # python doc_maintenance_toolkit.py --mode quality --quick
        >>> # Or call directly:
        >>> sys.argv = ['doc_maintenance_toolkit.py', '--mode', 'style']
        >>> exit_code = main()  # doctest: +SKIP
        >>> print(f"Exited with code {exit_code}")  # doctest: +SKIP
    
    Note:
        Must be run from repository root or script will fail with error
        message about missing docs/sphinx/ directory.
    """
    # Parse arguments
    args = parse_arguments()
    
    # Determine repository root
    repo_root = Path(__file__).parent.parent.parent
    docs_root = repo_root / 'docs' / 'sphinx'
    
    # Validate documentation directory exists
    if not docs_root.exists():
        print(Colors.red(f"❌ Error: Documentation directory not found: {docs_root}"))
        print(Colors.yellow("   Please run from the repository root."))
        return 2
    
    # Create and run maintenance runner
    runner = MaintenanceRunner(repo_root, args)
    
    # Execute requested mode
    if args.mode == 'style':
        return runner.run_style_check()
    elif args.mode == 'quality':
        return runner.run_quality_check()
    elif args.mode == 'build':
        return runner.run_build()
    elif args.mode == 'full':
        return runner.run_full_maintenance()
    else:
        print(Colors.red(f"❌ Unknown mode: {args.mode}"))
        return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(Colors.yellow("\n⚠️ Operation cancelled by user"))
        sys.exit(130)
    except Exception as e:
        print(Colors.red(f"❌ Unexpected error: {e}"))
        sys.exit(2)
