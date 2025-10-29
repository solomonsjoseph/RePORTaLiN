scripts.utils.check\_documentation\_quality module
===================================================

.. module:: scripts.utils.check_documentation_quality
   :synopsis: Automated documentation quality checker for quarterly maintenance

**For Developers:** This module provides comprehensive automated quality checks for Sphinx documentation.

Overview
--------

The documentation quality checker performs automated validation of documentation following
the quarterly maintenance checklist defined in :doc:`../developer_guide/documentation_style_guide`.

**Key Features**:

- Version reference consistency checks
- File size monitoring and recommendations
- Redundant content detection across files
- Cross-reference validation (`:doc:`, `:ref:` directives)
- Style compliance verification
- Outdated date detection
- Comprehensive reporting with severity levels

**Integration Points**:

- **Command-line**: Direct execution for manual checks
- **Makefile**: ``make docs-quality`` target
- **GitHub Actions**: Automated quarterly runs via ``.github/workflows/docs-quality-check.yml``
- **Pre-commit**: Optional hook for continuous validation

Usage
-----

Basic Usage
~~~~~~~~~~~

Run all quality checks:

.. code-block:: bash

   python3 scripts/utils/check_documentation_quality.py

The script will:

1. Check version references for outdated version directives
2. Analyze file sizes and recommend splitting large files
3. Detect redundant content across documentation
4. Validate cross-references between documents
5. Verify style compliance (user/developer guide headers)
6. Find potentially outdated date references
7. Generate comprehensive report with recommendations

Exit Codes
~~~~~~~~~~

The script uses standard exit codes:

- ``0`` - All checks passed successfully
- ``1`` - Warnings found (should be addressed)
- ``2`` - Critical errors found (must be fixed)

Example Output:

.. code-block:: text

   📁 Documentation root: /path/to/docs/sphinx
   🚀 Starting Documentation Quality Check
   
   🔍 Checking version references...
   📏 Checking file sizes...
   🔄 Checking for redundant content...
   🔗 Checking cross-references...
   ✨ Checking style compliance...
   📅 Checking for outdated dates...
   
   ================================================================================
   📋 DOCUMENTATION QUALITY REPORT
   ================================================================================
   
   📊 Statistics:
     Files checked: 36
     Total lines: 18,996
     Errors: 0
     Warnings: 36
     Info: 45

Integration Examples
~~~~~~~~~~~~~~~~~~~~

**Makefile Integration**:

.. code-block:: makefile

   docs-quality:
       @echo "Running comprehensive documentation quality check..."
       python3 scripts/utils/check_documentation_quality.py

**GitHub Actions**:

.. code-block:: yaml

   name: Documentation Quality Check
   on:
     schedule:
       - cron: '0 0 1 */3 *'  # Quarterly
   jobs:
     quality-check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Run quality check
           run: python3 scripts/utils/check_documentation_quality.py

**Shell Script**:

.. code-block:: bash

   #!/bin/bash
   # Run quality check and capture exit code
   if python3 scripts/utils/check_documentation_quality.py; then
       echo "✅ Quality check passed"
   else
       echo "❌ Quality check failed"
       exit 1
   fi

Logging
-------

The quality checker uses file-based logging for audit trails:

**Log File Location**: ``docs/sphinx/quality_check.log``

**Log Format**:

.. code-block:: text

   2025-10-28 18:06:54,544 - doc_quality_checker - INFO - Documentation Quality Checker v0.8.4
   2025-10-28 18:06:54,544 - doc_quality_checker - INFO - Documentation root: /path/to/docs
   2025-10-28 18:06:54,545 - doc_quality_checker - INFO - Initialized DocumentationQualityChecker v0.8.4
   2025-10-28 18:06:54,576 - doc_quality_checker - WARNING - [BROKEN_REFERENCE] api/config.rst:439 - Potentially broken reference: ../user_guide/configuration

**Log Levels**:

- ``INFO`` - Normal operations and progress updates
- ``WARNING`` - Issues that should be reviewed but aren't critical
- ``ERROR`` - Critical issues that must be fixed

The log file is automatically created and appended to with each run, providing a complete audit trail
of all quality checks over time.

.. note::
   The log file (``quality_check.log``) is automatically excluded from version control via
   ``.gitignore`` (``*.log`` pattern).

Quality Checks Performed
-------------------------

1. Version References
~~~~~~~~~~~~~~~~~~~~~

**Check**: Detects outdated version directives in present-tense documentation.

**Pattern**: ``.. versionadded:: 0.0.x`` or ``.. versionchanged:: 0.0.x``

**Exclusions**: ``changelog.rst`` and files with ``historical`` in the path

**Severity**: WARNING

**Example Issue**:

.. code-block:: restructuredtext

   .. versionadded:: 0.0.5
      This feature was added in early development

**Recommendation**: Update to current version or remove if feature is now standard.

2. File Size Analysis
~~~~~~~~~~~~~~~~~~~~~

**Check**: Monitors documentation file sizes and recommends splitting large files.

**Threshold**: 1000 lines (informational), 1500 lines (recommend splitting)

**Severity**: INFO

**Example**:

.. code-block:: text

   ℹ️ changelog.rst
      Large file: 1686 lines (consider splitting if >1500)

**Recommendation**: Consider splitting large files into:

- Historical archives (``changelog_archive.rst``)
- Separate sections (``changelog_2025.rst``, ``changelog_2024.rst``)
- Thematic divisions

3. Redundant Content Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Check**: Identifies duplicate section headers across files.

**Minimum Header Length**: 15 characters (to avoid false positives)

**Exclusions**: ``index.rst``, ``modules.rst``

**Severity**: INFO

**Example**:

.. code-block:: text

   ℹ️ multiple files
      Duplicate section header "Getting Started..." found in: 
      user_guide/quickstart.rst, developer_guide/contributing.rst

**Note**: Some duplication is intentional (e.g., "Troubleshooting" in multiple contexts).

4. Cross-Reference Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Check**: Validates ``:doc:`` and ``:ref:`` directives point to existing files.

**Patterns Checked**:

- ``:doc:`../path/to/file```
- ``:ref:`label-name```

**Severity**: WARNING

**Common Issues**:

- File moved without updating references
- Typos in file paths
- Missing ``.rst`` extension handling

**Example**:

.. code-block:: text

   ⚠️ api/config.rst:439
      Potentially broken reference: ../user_guide/configuration

.. note::
   Many warnings are **false positives** - the checker is conservative and flags references
   that appear broken but may actually resolve correctly during Sphinx build.

5. Style Compliance
~~~~~~~~~~~~~~~~~~~

**Check**: Verifies user guide and developer guide files follow header conventions.

**Requirements**:

- User guide files should contain ``**For Users:**`` in first 500 characters
- Developer guide files should contain ``**For Developers:**`` in first 500 characters

**Severity**: WARNING

**Purpose**: Ensures consistent audience targeting per :doc:`../developer_guide/documentation_style_guide`

6. Outdated Dates
~~~~~~~~~~~~~~~~~

**Check**: Detects potentially outdated date references.

**Pattern**: Years 2022, 2023, 2024 in specific contexts

**Contexts Checked**:

- "Last Updated"
- "Current"
- "Assessment Date"
- "Date:"

**Exclusions**: 

- Code blocks (``.. code-block::``)
- Version history sections
- ``changelog.rst``
- Historical files

**Severity**: INFO

Module Reference
----------------

Classes
~~~~~~~

.. autoclass:: QualityIssue
   :members:
   :undoc-members:
   :show-inheritance:

   Dataclass representing a single documentation quality issue.
   
   **Attributes**:
   
   - ``severity`` (str): Issue severity - 'info', 'warning', or 'error'
   - ``category`` (str): Issue category (e.g., 'broken_reference', 'file_size')
   - ``file_path`` (str): Relative path to the file with the issue
   - ``line_number`` (int): Line number where issue occurs (0 if file-level)
   - ``message`` (str): Human-readable description of the issue

.. autoclass:: DocumentationQualityChecker
   :members:
   :undoc-members:
   :show-inheritance:

   Main quality checker class that performs all validation checks.
   
   **Key Methods**:
   
   - ``check_version_references()`` - Validate version directives
   - ``check_file_sizes()`` - Analyze file sizes
   - ``check_redundant_content()`` - Detect duplicate content
   - ``check_broken_references()`` - Validate cross-references
   - ``check_style_compliance()`` - Verify style guide compliance
   - ``check_outdated_dates()`` - Find outdated dates
   - ``run_all_checks()`` - Execute complete quality check
   - ``generate_report()`` - Create formatted report

Functions
~~~~~~~~~

.. autofunction:: main

   Script entry point that:
   
   1. Determines documentation root (``docs/sphinx/``)
   2. Validates directory exists
   3. Initializes quality checker
   4. Runs all checks
   5. Returns appropriate exit code

Best Practices
--------------

When to Run
~~~~~~~~~~~

**Daily Development** (Quick Check):

Use :doc:`check_docs_style <../developer_guide/maintenance_summary>` instead:

.. code-block:: bash

   make docs-check  # Fast - only basic checks

**Before Major Commits** (Comprehensive):

.. code-block:: bash

   make docs-quality  # Full quality check

**Quarterly Maintenance** (Automated):

GitHub Actions runs automatically on the 1st of January, April, July, and October.

**Manual Quarterly Review**:

.. code-block:: bash

   make docs-maintenance  # Full workflow: check + quality + build

Interpreting Results
~~~~~~~~~~~~~~~~~~~~

**No Issues Found**:

.. code-block:: text

   ✅ No issues found - documentation quality is excellent!

Action: None required.

**Warnings Only**:

.. code-block:: text

   ⚠️ High warning count (36)
   Schedule time to address these warnings

Action: Review warnings and address as time permits. Many may be false positives.

**Errors Found**:

.. code-block:: text

   ❌ 5 critical errors must be fixed

Action: Fix errors immediately before committing.

Customization
~~~~~~~~~~~~~

To modify check behavior, edit ``DocumentationQualityChecker`` class:

.. code-block:: python

   class DocumentationQualityChecker:
       def __init__(self, docs_root: Path, quick_mode: bool = False, 
                    enabled_checks: Set[str] = None):
           """
           Args:
               docs_root: Path to docs/sphinx directory
               quick_mode: If True, run only basic checks (fast)
               enabled_checks: Set of check categories to run
           """

**Example - Enable Only Specific Checks**:

.. code-block:: python

   checker = DocumentationQualityChecker(
       docs_root,
       enabled_checks={'version', 'references'}  # Only these checks
   )

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue**: "Documentation directory not found"

**Solution**: Ensure you're running from repository root or adjust path:

.. code-block:: bash

   cd /path/to/RePORTaLiN
   python3 scripts/utils/check_documentation_quality.py

**Issue**: "Import errors with logging module"

**Solution**: The script uses Python's standard ``logging`` library directly to avoid
circular imports. Ensure you're running with Python 3.7+.

**Issue**: "Too many false positive warnings"

**Solution**: This is expected behavior. The checker is conservative and flags potential
issues. Review the Sphinx build output for actual errors:

.. code-block:: bash

   make -C docs/sphinx html 2>&1 | grep WARNING

Performance
~~~~~~~~~~~

**Typical Performance**:

- Files checked: 36
- Total lines: ~19,000
- Execution time: ~1 second
- Memory usage: Minimal (<50MB)

**Optimization**: For very large documentation sets (100+ files, 100,000+ lines):

- Consider enabling quick mode
- Run only specific checks
- Use file-level caching

See Also
--------

Related Tools
~~~~~~~~~~~~~

- :doc:`../developer_guide/maintenance_summary` - Complete maintenance workflow
- ``scripts/utils/check_docs_style.sh`` - Quick style compliance checker (shell)
- ``scripts/utils/doc_maintenance_commands.sh`` - Convenience shell functions
- :doc:`../developer_guide/documentation_style_guide` - Complete style guide

Related Documentation
~~~~~~~~~~~~~~~~~~~~~

- :doc:`../changelog` - Version history and changes
- :doc:`../developer_guide/contributing` - Contribution guidelines
- :doc:`../developer_guide/github_pages_deployment` - CI/CD integration
- :doc:`../user_guide/troubleshooting` - General troubleshooting

Version History
---------------

.. versionadded:: 0.8.2
   Initial implementation of comprehensive documentation quality checker.

.. versionchanged:: 0.8.4
   Added comprehensive file-based logging and resolved circular import issues.

Notes
-----

**Design Philosophy**:

The quality checker follows a "trust but verify" approach:

- **Conservative warnings**: Better to flag false positives than miss real issues
- **Informational focus**: Most issues are INFO or WARNING, not ERROR
- **Non-blocking**: Quality checks shouldn't prevent development
- **Audit trail**: All checks logged for historical analysis

**Analogy**: Think of this tool as a **spell-checker for documentation** 📝. It highlights
potential issues but doesn't automatically fix them, leaving final decisions to humans
who understand context.

**Security Note**: The script reads documentation files but never modifies them.
All operations are read-only, making it safe to run at any time.

Module Source
-------------

.. literalinclude:: ../../../scripts/utils/check_documentation_quality.py
   :language: python
   :linenos:
   :lines: 1-50

Full source code: ``scripts/utils/check_documentation_quality.py``
