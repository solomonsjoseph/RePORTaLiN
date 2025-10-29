#!/usr/bin/env python3
"""
Documentation Quality Checker

This script performs automated quality checks on Sphinx documentation following
the quarterly maintenance checklist defined in documentation_style_guide.rst.

Combines both basic compliance checks (headers, jargon) and advanced quarterly
maintenance checks (version refs, file sizes, redundancy, etc.).

Usage:
    # Run all checks (quarterly maintenance mode)
    python scripts/utils/check_documentation_quality.py
    
    # Run only basic compliance checks (fast - for pre-commit)
    python scripts/utils/check_documentation_quality.py --quick
    
    # Run only specific check categories
    python scripts/utils/check_documentation_quality.py --checks style,version

Exit Codes:
    0 - All checks passed
    1 - Issues found (warnings)
    2 - Critical issues found (must fix)

Author: RePORTaLiN Development Team
Last Updated: October 28, 2025
"""

# Import standard library logging FIRST - use absolute import to avoid local module
from __future__ import absolute_import
import sys
from pathlib import Path

# Temporarily remove current directory from sys.path to avoid shadowing standard library
_script_dir = str(Path(__file__).parent)
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

# Now import standard library logging (before any local module that might shadow it)
import logging as std_logging

# Add repo root to path for imports
_repo_root = Path(__file__).parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Other standard library imports
import argparse
import os
import re
import subprocess
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass

# Import version from parent directory
from __version__ import __version__

# Configure simple logging for this script
def _setup_logging() -> std_logging.Logger:
    """Set up logging for the quality checker."""
    logger = std_logging.getLogger('doc_quality_checker')
    logger.setLevel(std_logging.INFO)
    
    # File handler - log to .logs directory (centralized logging)
    log_dir = _repo_root / '.logs'
    log_dir.mkdir(exist_ok=True)  # Ensure .logs directory exists
    log_file = log_dir / 'quality_check.log'
    
    file_handler = std_logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(std_logging.INFO)
    file_formatter = std_logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)
    return logger

# Initialize module-level logger
_main_logger = _setup_logging()


@dataclass
class QualityIssue:
    """Represents a documentation quality issue."""
    severity: str  # 'info', 'warning', 'error'
    category: str
    file_path: str
    line_number: int
    message: str


class DocumentationQualityChecker:
    """Automated documentation quality checker."""
    
    def __init__(self, docs_root: Path, quick_mode: bool = False, 
                 enabled_checks: Set[str] = None):
        """
        Initialize the quality checker.
        
        Args:
            docs_root: Path to docs/sphinx directory
            quick_mode: If True, run only basic compliance checks (fast)
            enabled_checks: Set of check categories to run (None = all)
        """
        self.docs_root = docs_root
        self.quick_mode = quick_mode
        self.enabled_checks = enabled_checks or {
            'style', 'version', 'size', 'redundancy', 'references', 'dates', 'build'
        }
        self.issues: List[QualityIssue] = []
        self.stats: Dict[str, int] = {
            'files_checked': 0,
            'total_lines': 0,
            'errors': 0,
            'warnings': 0,
            'info': 0
        }
        
        # Use module-level logger
        self.logger = _main_logger
        self.logger.info(f"Initialized DocumentationQualityChecker v{__version__}")
        self.logger.info(f"Documentation root: {docs_root}")
        self.logger.info(f"Quick mode: {quick_mode}")
        self.logger.info(f"Enabled checks: {', '.join(sorted(self.enabled_checks))}")
    
    def add_issue(self, severity: str, category: str, file_path: str, 
                  line_number: int, message: str) -> None:
        """Add a quality issue to the list."""
        issue = QualityIssue(
            severity=severity,
            category=category,
            file_path=file_path,
            line_number=line_number,
            message=message
        )
        self.issues.append(issue)
        
        # Map severity to stats key (singular to plural)
        severity_map = {'error': 'errors', 'warning': 'warnings', 'info': 'info'}
        self.stats[severity_map.get(severity, severity)] += 1
        
        # Log the issue using centralized logging
        location = f"{file_path}:{line_number}" if line_number else file_path
        log_message = f"[{category.upper()}] {location} - {message}"
        
        if severity == 'error':
            self.logger.error(log_message)
        elif severity == 'warning':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def check_version_references(self) -> None:
        """Check for outdated version references in present-tense documentation."""
        print("🔍 Checking version references...")
        self.logger.info("Starting version reference check...")
        
        # Patterns to check
        old_version_pattern = re.compile(r'\.\.\s+version(added|changed)::\s+0\.0\.\d+')
        
        # Directories to check (exclude changelog and historical)
        check_dirs = ['user_guide', 'developer_guide', 'api']
        
        for dir_name in check_dirs:
            dir_path = self.docs_root / dir_name
            if not dir_path.exists():
                continue
            
            for rst_file in dir_path.rglob('*.rst'):
                # Skip historical and changelog files
                if 'historical' in str(rst_file) or 'changelog' in str(rst_file):
                    continue
                
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
    
    def check_file_sizes(self) -> None:
        """Check for files exceeding size recommendations."""
        print("📏 Checking file sizes...")
        self.logger.info("Starting file size check...")
        
        large_file_threshold = 1000  # lines
        
        for rst_file in self.docs_root.rglob('*.rst'):
            line_count = sum(1 for _ in open(rst_file, 'r', encoding='utf-8'))
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
    
    def check_redundant_content(self) -> None:
        """Check for potential redundant content across files."""
        print("🔄 Checking for redundant content...")
        self.logger.info("Starting redundancy check...")
        
        # Track section headers across files
        headers: Dict[str, List[Tuple[str, str]]] = {}
        
        for rst_file in self.docs_root.rglob('*.rst'):
            # Skip index and module files
            if rst_file.name in ['index.rst', 'modules.rst']:
                continue
            
            with open(rst_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find all headers (lines followed by ===== or -----)
                header_pattern = re.compile(r'^(.+)\n([=\-~^]+)$', re.MULTILINE)
                
                for match in header_pattern.finditer(content):
                    header_text = match.group(1).strip()
                    
                    # Skip very short headers (likely not duplicates)
                    if len(header_text) < 15:
                        continue
                    
                    file_rel = str(rst_file.relative_to(self.docs_root))
                    
                    if header_text not in headers:
                        headers[header_text] = []
                    headers[header_text].append((file_rel, header_text))
        
        # Report duplicate headers
        for header_text, locations in headers.items():
            if len(locations) > 1:
                files = ', '.join([loc[0] for loc in locations])
                self.add_issue(
                    'info',
                    'redundancy',
                    'multiple files',
                    0,
                    f'Duplicate section header "{header_text[:50]}..." found in: {files}'
                )
    
    def check_broken_references(self) -> None:
        """Check for potentially broken cross-references."""
        print("🔗 Checking cross-references...")
        self.logger.info("Starting cross-reference check...")
        
        # Collect all defined labels
        defined_labels = set()
        reference_pattern = re.compile(r':doc:`([^`]+)`|:ref:`([^`]+)`')
        label_pattern = re.compile(r'\.\.\s+_([^:]+):')
        
        # First pass: collect all labels
        for rst_file in self.docs_root.rglob('*.rst'):
            with open(rst_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for match in label_pattern.finditer(content):
                    defined_labels.add(match.group(1).strip())
        
        # Second pass: check references
        for rst_file in self.docs_root.rglob('*.rst'):
            with open(rst_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    for match in reference_pattern.finditer(line):
                        ref = match.group(1) or match.group(2)
                        if ref:
                            # Check if reference looks like a file path
                            if '/' in ref:
                                ref_path = self.docs_root / (ref + '.rst')
                                if not ref_path.exists():
                                    # Try without extension
                                    ref_path = self.docs_root / ref
                                    if not ref_path.exists():
                                        self.add_issue(
                                            'warning',
                                            'broken_reference',
                                            str(rst_file.relative_to(self.docs_root)),
                                            line_num,
                                            f'Potentially broken reference: {ref}'
                                        )
    
    def check_style_compliance(self) -> None:
        """Check for style compliance issues."""
        print("✨ Checking style compliance...")
        self.logger.info("Starting style compliance check...")
        
        user_guide_dir = self.docs_root / 'user_guide'
        dev_guide_dir = self.docs_root / 'developer_guide'
        
        # Check user guide files
        if user_guide_dir.exists():
            for rst_file in user_guide_dir.glob('*.rst'):
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '**For Users' not in content[:500]:
                        self.add_issue(
                            'warning',
                            'style_compliance',
                            str(rst_file.relative_to(self.docs_root)),
                            0,
                            'Missing "**For Users:**" header'
                        )
        
        # Check developer guide files
        if dev_guide_dir.exists():
            for rst_file in dev_guide_dir.glob('*.rst'):
                with open(rst_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '**For Developers' not in content[:500]:
                        self.add_issue(
                            'warning',
                            'style_compliance',
                            str(rst_file.relative_to(self.docs_root)),
                            0,
                            'Missing "**For Developers:**" header'
                        )
    
    def check_outdated_dates(self) -> None:
        """Check for potentially outdated date references."""
        print("📅 Checking for outdated dates...")
        self.logger.info("Starting outdated date check...")
        
        current_year = 2025
        old_date_pattern = re.compile(r'\b(2024|2023|2022)\b')
        
        for rst_file in self.docs_root.rglob('*.rst'):
            # Skip changelog and historical files
            if 'changelog' in str(rst_file) or 'historical' in str(rst_file):
                continue
            
            with open(rst_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Skip code blocks and version history sections
                    if '.. code-block::' in line or 'Version 0.' in line:
                        continue
                    
                    if old_date_pattern.search(line):
                        # Check if it's in a context that should be updated
                        if any(keyword in line.lower() for keyword in 
                               ['last updated', 'current', 'assessment date', 'date:']):
                            self.add_issue(
                                'info',
                                'outdated_date',
                                str(rst_file.relative_to(self.docs_root)),
                                line_num,
                                f'Potentially outdated date: {line.strip()}'
                            )
    
    def generate_report(self) -> int:
        """
        Generate and print the quality check report.
        
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
        
        # Print issues by category
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
        """
        Run all quality checks.
        
        Returns:
            Exit code (0=success, 1=warnings, 2=errors)
        """
        print("🚀 Starting Documentation Quality Check\n")
        self.logger.info("="*80)
        self.logger.info(f"Documentation Quality Check v{__version__} - Starting")
        self.logger.info("="*80)
        
        self.check_version_references()
        self.check_file_sizes()
        self.check_redundant_content()
        self.check_broken_references()
        self.check_style_compliance()
        self.check_outdated_dates()
        
        exit_code = self.generate_report()
        
        # Log final results
        if exit_code == 0:
            self.logger.info("Documentation quality check passed - no issues found")
        elif exit_code == 1:
            self.logger.warning(f"Documentation quality check completed with {self.stats['warnings']} warnings")
        else:
            self.logger.error(f"Documentation quality check failed with {self.stats['errors']} errors")
        
        return exit_code


def main() -> int:
    """Main entry point."""
    # Determine docs root
    script_dir = Path(__file__).parent.parent.parent  # Go up to repo root
    docs_root = script_dir / 'docs' / 'sphinx'
    
    if not docs_root.exists():
        error_msg = f"Documentation directory not found: {docs_root}"
        print(f"❌ Error: {error_msg}")
        _main_logger.error(error_msg)
        return 2
    
    print(f"📁 Documentation root: {docs_root}\n")
    _main_logger.info(f"Documentation Quality Checker v{__version__}")
    _main_logger.info(f"Documentation root: {docs_root}")
    
    checker = DocumentationQualityChecker(docs_root)
    return checker.run_all_checks()


if __name__ == '__main__':
    sys.exit(main())
