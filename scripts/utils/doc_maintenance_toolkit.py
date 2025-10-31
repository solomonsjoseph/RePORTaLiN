#!/usr/bin/env python3
"""
Documentation Maintenance Toolkit - Consolidated Quality & Build System
========================================================================

**For Developers:**

This module consolidates all documentation checking, building, and maintenance
functionality into one comprehensive, unified tool. It replaces three separate
scripts while preserving all original functionality.

Consolidates:
    - check_docs_style.sh (Style compliance checking)
    - check_documentation_quality.py (Comprehensive quality analysis)
    - doc_maintenance_commands.sh (Build and utility functions)

Does NOT include:
    - smart_commit.sh (Git operations remain separate)

Modes:
    style    - Quick style compliance check (fast, for pre-commit hooks)
    quality  - Comprehensive quality analysis (quarterly maintenance)
    build    - Build and verify Sphinx documentation
    full     - Run all checks and build documentation

Usage Examples:
    # Quick style compliance check
    python doc_maintenance_toolkit.py --mode style
    
    # Comprehensive quality check
    python doc_maintenance_toolkit.py --mode quality
    
    # Build documentation
    python doc_maintenance_toolkit.py --mode build
    
    # Build and open in browser
    python doc_maintenance_toolkit.py --mode build --open
    
    # Full maintenance suite
    python doc_maintenance_toolkit.py --mode full
    
    # Quiet mode (errors only)
    python doc_maintenance_toolkit.py --mode style --quiet
    
    # Verbose mode (detailed output)
    python doc_maintenance_toolkit.py --mode quality --verbose

Exit Codes:
    0 - All checks passed successfully
    1 - Warnings found (non-critical issues)
    2 - Errors found (must be fixed)

Logging:
    All operations logged to .logs/ directory:
    - style mode:   .logs/doc_style_check.log
    - quality mode: .logs/doc_quality_check.log
    - build mode:   .logs/doc_build.log
    - full mode:    .logs/doc_full_maintenance.log

Author: RePORTaLiN Development Team
Version: 1.0.0
Last Updated: October 30, 2025
License: MIT

Security:
    - Input validation on all file paths
    - No arbitrary code execution
    - Safe subprocess handling
    - Proper error handling and logging
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
    """ANSI color codes for terminal output.
    
    Provides the same color-coded output as the original bash scripts
    for consistency and user familiarity.
    """
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def red(text: str) -> str:
        """Return text in red color."""
        return f"{Colors.RED}{text}{Colors.NC}"
    
    @staticmethod
    def green(text: str) -> str:
        """Return text in green color."""
        return f"{Colors.GREEN}{text}{Colors.NC}"
    
    @staticmethod
    def yellow(text: str) -> str:
        """Return text in yellow color."""
        return f"{Colors.YELLOW}{text}{Colors.NC}"
    
    @staticmethod
    def blue(text: str) -> str:
        """Return text in blue color."""
        return f"{Colors.BLUE}{text}{Colors.NC}"


@dataclass
class QualityIssue:
    """Represents a documentation quality issue.
    
    Attributes:
        severity: Issue severity level ('info', 'warning', 'error')
        category: Issue category (e.g., 'style_compliance', 'version_reference')
        file_path: Relative path to the file with the issue
        line_number: Line number where issue occurs (0 if not applicable)
        message: Human-readable description of the issue
    """
    severity: str
    category: str
    file_path: str
    line_number: int
    message: str


class MaintenanceLogger:
    """Centralized logging system for all maintenance operations.
    
    Provides consistent logging across all maintenance operations with
    proper file handling, formatting, and log rotation support.
    
    All logs are saved to the .logs/ directory in the repository root.
    
    Attributes:
        log_dir: Path to the .logs directory
        _loggers: Cache of created logger instances
    """
    
    def __init__(self, repo_root: Path):
        """Initialize the logging system.
        
        Args:
            repo_root: Path to repository root directory
        """
        self.log_dir = repo_root / '.logs'
        self.log_dir.mkdir(exist_ok=True)
        self._loggers: Dict[str, std_logging.Logger] = {}
    
    def get_logger(self, name: str, log_file: Optional[str] = None) -> std_logging.Logger:
        """Get or create a logger for a specific operation.
        
        Args:
            name: Logger name (typically module or operation name)
            log_file: Optional specific log file name (defaults to name.log)
        
        Returns:
            Configured logger instance
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
    """Documentation style compliance checker.
    
    Checks documentation files for compliance with the project's style guide:
    - User guide files must start with "**For Users:**"
    - Developer guide files must start with "**For Developers:**"
    - User guide files should not contain technical jargon
    - Sphinx builds must complete without warnings or errors
    
    This class replicates functionality from check_docs_style.sh.
    """
    
    def __init__(self, docs_root: Path, logger: std_logging.Logger, quiet: bool = False):
        """Initialize the style checker.
        
        Args:
            docs_root: Path to docs/sphinx directory
            logger: Logger instance for this checker
            quiet: If True, suppress non-error output
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
        """Check user guide files for required headers.
        
        Returns:
            List of files missing the required header
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
        """Check developer guide files for required headers.
        
        Returns:
            List of files missing the required header
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
        """Check user guide for technical jargon.
        
        Returns:
            Dictionary mapping file names to list of found jargon terms
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
        """Run Sphinx build and check for warnings/errors.
        
        Returns:
            Tuple of (exit_code, output)
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
        """Run all style compliance checks.
        
        Returns:
            Exit code (0=success, 1=failure)
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
    """Comprehensive documentation quality analyzer.
    
    Performs deep analysis of documentation quality including:
    - Outdated version references
    - File size analysis
    - Redundant content detection
    - Broken cross-references
    - Outdated date references
    
    This class replicates and enhances functionality from
    check_documentation_quality.py.
    """
    
    def __init__(self, docs_root: Path, logger: std_logging.Logger, 
                 quick_mode: bool = False, verbose: bool = False):
        """Initialize the quality checker.
        
        Args:
            docs_root: Path to docs/sphinx directory
            logger: Logger instance for this checker
            quick_mode: If True, run only basic checks
            verbose: If True, provide detailed output
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
        """Add a quality issue to the tracking list.
        
        Args:
            severity: Issue severity ('info', 'warning', 'error')
            category: Issue category
            file_path: File where issue was found
            line_number: Line number (0 if not applicable)
            message: Description of the issue
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
        """Check for outdated version references."""
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
        """Check for files exceeding size recommendations."""
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
        """Check for potential redundant content across files."""
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
        """Check for potentially broken cross-references."""
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
        """Check for potentially outdated date references."""
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
        """Check for style compliance issues.
        
        Verifies that documentation files have the required headers:
        - User guide files must start with "**For Users:**"
        - Developer guide files must start with "**For Developers:**"
        
        This check ensures consistency with the project's documentation
        style guide and matches the original check_documentation_quality.py
        behavior.
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
        """Generate and print the quality check report.
        
        Returns:
            Exit code (0=success, 1=warnings, 2=errors)
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
        """Run all quality checks.
        
        Returns:
            Exit code (0=success, 1=warnings, 2=errors)
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
    """Documentation building and verification system.
    
    Handles Sphinx documentation building with proper error handling
    and verification. Supports clean builds, incremental builds, and
    opening built documentation in the browser.
    
    This class replicates functionality from doc_maintenance_commands.sh.
    """
    
    def __init__(self, docs_root: Path, logger: std_logging.Logger, quiet: bool = False):
        """Initialize the documentation builder.
        
        Args:
            docs_root: Path to docs/sphinx directory
            logger: Logger instance for this builder
            quiet: If True, suppress non-error output
        """
        self.docs_root = docs_root
        self.logger = logger
        self.quiet = quiet
    
    def build_docs(self, clean: bool = True) -> bool:
        """Build Sphinx documentation.
        
        Args:
            clean: If True, run 'make clean' before building
        
        Returns:
            True if build succeeded, False otherwise
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
        """Open built documentation in the default browser.
        
        Returns:
            True if successful, False otherwise
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
    
    Coordinates all maintenance tools and provides a unified interface
    for running different maintenance modes.
    """
    
    def __init__(self, repo_root: Path, args: argparse.Namespace):
        """Initialize the maintenance runner.
        
        Args:
            repo_root: Path to repository root
            args: Parsed command-line arguments
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
        """Run style compliance check.
        
        Returns:
            Exit code
        """
        checker = StyleChecker(
            self.docs_root,
            self.logger,
            quiet=self.args.quiet
        )
        return checker.run_all_checks()
    
    def run_quality_check(self) -> int:
        """Run comprehensive quality check.
        
        Returns:
            Exit code
        """
        checker = QualityChecker(
            self.docs_root,
            self.logger,
            quick_mode=self.args.quick,
            verbose=self.args.verbose
        )
        return checker.run_all_checks()
    
    def run_build(self) -> int:
        """Run documentation build.
        
        Returns:
            Exit code
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
        """Run full maintenance suite.
        
        Returns:
            Exit code (worst of all checks)
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
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
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
    """Main entry point.
    
    Returns:
        Exit code
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
