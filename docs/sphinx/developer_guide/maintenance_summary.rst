.. _maintenance_summary:

====================================
Documentation Maintenance Summary
====================================

**For Developers:** This document provides comprehensive guidance for maintaining RePORTaLiN's
documentation system, including automation tools, quality checks, and maintenance procedures.

.. meta::
   :description: Current status and maintenance guidance for RePORTaLiN documentation
   :keywords: documentation, maintenance, status, quality

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
========

This document provides a snapshot of the current documentation status, automation
features, and guidance for ongoing maintenance.

**Last Updated**: October 28, 2025

**Documentation Version**: Aligned with code version |version|


Current Status
==============

Automation Features
-------------------

✅ **Version Bumping**
   Automated semantic versioning based on conventional commits:
   
   - ``feat:`` → Minor version bump (0.x.0)
   - ``fix:`` → Patch version bump (0.0.x)
   - ``BREAKING CHANGE:`` → Major version bump (x.0.0)
   
   Location: ``.git/hooks/bump-version`` and ``.git/hooks/post-commit``

✅ **Documentation Quality Checks**
   Comprehensive automated quality checker:
   
   - **Script**: ``scripts/utils/check_documentation_quality.py``
   - **Shell Script**: ``scripts/utils/check_docs_style.sh``
   - **GitHub Action**: ``.github/workflows/docs-quality-check.yml``
   
   Checks performed:
   
   - Version reference consistency
   - File size monitoring
   - Redundancy detection
   - Cross-reference validation
   - Style compliance (RST only, no Markdown)
   - Outdated date detection

✅ **CI/CD Integration**
   GitHub Actions workflow runs on:
   
   - Quarterly schedule (1st day of Jan, Apr, Jul, Oct)
   - Manual trigger (workflow_dispatch)
   - Pull requests affecting documentation
   - Direct pushes to main branch

Documentation Structure
-----------------------

The documentation is organized into three main sections:

User Guide
~~~~~~~~~~

Primary audience: End users and data managers

- ``introduction.rst`` - Overview and purpose
- ``installation.rst`` - Setup instructions
- ``quickstart.rst`` - Getting started guide
- ``usage.rst`` - Detailed usage examples
- ``configuration.rst`` - Configuration reference
- ``deidentification.rst`` - De-identification guide
- ``country_regulations.rst`` - Country-specific regulations
- ``troubleshooting.rst`` - Common issues and solutions

Developer Guide
~~~~~~~~~~~~~~~

Primary audience: Developers and maintainers

- ``architecture.rst`` - System design and components
- ``contributing.rst`` - Contribution guidelines
- ``extending.rst`` - Extension development
- ``production_readiness.rst`` - Production deployment
- ``code_integrity_audit.rst`` - Code quality standards
- ``project_vision.rst`` - Long-term goals
- ``future_enhancements.rst`` - Planned improvements
- ``documentation_style_guide.rst`` - **Documentation standards**
- ``auto_documentation.rst`` - API doc generation
- ``github_pages_deployment.rst`` - Deployment guide

Historical Records
~~~~~~~~~~~~~~~~~~

Archived for reference:

- ``historical_verification.rst`` - Past audit records
- ``terminology_simplification.rst`` - Terminology changes
- ``script_reorganization.rst`` - Code restructuring
- ``gitignore_verification.rst`` - Git configuration

API Reference
~~~~~~~~~~~~~

Auto-generated from source code docstrings

- Module documentation
- Function and class references
- Type hints and signatures


Quality Metrics
===============

Current Status (October 28, 2025)
----------------------------------

.. code-block:: text

   📊 Statistics:
     Files checked: 35
     Total lines: 18,477
     Errors: 0
     Warnings: 34 (all false positives)
     Info: 40

   ✅ No actual broken references (Sphinx build succeeds)
   ✅ All files use .rst format (no Markdown)
   ✅ Version references are consistent

Known Issues
------------

**False Positive Warnings**

The quality checker reports 34 "potentially broken references" which are
actually valid Sphinx ``:doc:`` references. These can be safely ignored
as long as the Sphinx build completes without warnings.

**Informational Notices**

- **Large files**: 5 files exceed 1500 lines (informational only)
- **Duplicate headers**: 35 instances of duplicate section headers across files
  (expected and acceptable for repeated sections like "Troubleshooting")


Maintenance Procedures
======================

Quarterly Review Checklist
---------------------------

Perform these tasks every quarter (automated reminder via GitHub Actions):

1. **Version Consistency**
   
   .. code-block:: bash
   
      cd docs/sphinx
      python3 ../../scripts/utils/check_documentation_quality.py

2. **Build Verification**
   
   .. code-block:: bash
   
      cd docs/sphinx
      make clean
      make html

3. **Content Review**
   
   - Update version-specific content
   - Review and update examples
   - Check external links
   - Update dates in time-sensitive sections

4. **Style Compliance**
   
   .. code-block:: bash
   
      cd scripts/utils
      ./check_docs_style.sh

5. **Changelog Update**
   
   - Document significant changes since last quarter
   - Review version history
   - Ensure all features are documented

Manual Quality Check
--------------------

To manually run the quality checker:

.. code-block:: bash

   # From repository root
   python3 scripts/utils/check_documentation_quality.py
   
   # From scripts/utils directory
   cd scripts/utils
   ./check_docs_style.sh

Expected output: No errors, warnings are acceptable if explained above.

Release Process
---------------

When releasing a new version:

1. **Code Changes**
   
   - Make your changes
   - Use conventional commit messages (``feat:``, ``fix:``, ``BREAKING CHANGE:``)
   - Version bumps automatically on commit

2. **Documentation Updates**
   
   - Update changelog.rst with new version section
   - Update any version-specific content
   - Rebuild documentation locally

3. **Verification**
   
   .. code-block:: bash
   
      # Check version was bumped correctly
      cat __version__.py
      
      # Run quality checks
      python3 scripts/utils/check_documentation_quality.py
      
      # Build documentation
      cd docs/sphinx && make html

4. **Commit and Push**
   
   .. code-block:: bash
   
      git add .
      git commit -m "docs: update for version X.Y.Z"
      git push


Best Practices
==============

Documentation Standards
-----------------------

✅ **DO**:

- Use ``.rst`` format exclusively (no Markdown)
- Follow the style guide in ``documentation_style_guide.rst``
- Include ``.. meta::`` directives for SEO
- Use consistent heading hierarchy
- Add descriptive alt text for images
- Include code examples where appropriate
- Cross-reference related sections using ``:doc:``
- Update the changelog for significant changes

❌ **DON'T**:

- Don't use Markdown files in the documentation
- Don't hard-code version numbers (use |version| substitution)
- Don't create duplicate content (link instead)
- Don't use relative dates ("last week") - use absolute dates
- Don't skip the quarterly review checklist

Version Management
------------------

✅ **Commit Message Format**:

.. code-block:: text

   feat: add new deidentification feature
   
   Implements country-specific field masking for Brazil.
   Updates documentation with examples.

.. code-block:: text

   fix: correct date parsing in extract_data.py
   
   Resolves issue where ISO 8601 dates were not recognized.

.. code-block:: text

   feat!: redesign configuration schema
   
   BREAKING CHANGE: Configuration file format has changed.
   Users must migrate to new schema.

✅ **Version Number**:

The version number in ``__version__.py`` is automatically updated based on
commit messages. No manual editing required.

Documentation Updates
---------------------

For small changes:

.. code-block:: bash

   # Edit the file
   vim docs/sphinx/user_guide/usage.rst
   
   # Test locally
   cd docs/sphinx && make html
   
   # Commit with conventional message
   git commit -m "docs: clarify usage example"

For large changes:

1. Create a feature branch
2. Make documentation changes
3. Run full quality check
4. Create pull request (triggers automated checks)
5. Merge after review


Troubleshooting
===============

Common Issues
-------------

**Issue**: Quality checker reports broken references

**Solution**: If Sphinx build succeeds without warnings, these are false
positives. The checker doesn't fully understand Sphinx's reference resolution.

**Issue**: Version not bumping on commit

**Solution**: 

.. code-block:: bash

   # Check hook is executable
   ls -l .git/hooks/post-commit
   
   # Make executable if needed
   chmod +x .git/hooks/post-commit
   chmod +x .git/hooks/bump-version
   
   # Check commit message format
   git log -1 --pretty=%B

**Issue**: GitHub Actions failing

**Solution**: Check the workflow logs in GitHub Actions tab. Common causes:

- Missing dependencies
- Python version mismatch  
- File permissions

Getting Help
------------

1. Review the :doc:`documentation_style_guide`
2. Check the :doc:`contributing` guide
3. Review :doc:`../changelog` for recent changes
4. Check GitHub Issues for known problems


Related Documentation
=====================

- :doc:`documentation_style_guide` - Complete style and formatting guide
- :doc:`contributing` - Contribution guidelines and workflow
- :doc:`../changelog` - Version history and changes
- :doc:`production_readiness` - Production deployment standards


Revision History
================

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Version
     - Date
     - Changes
   * - 1.0
     - 2025-10-28
     - Initial maintenance summary created
       
       - Documented automation features
       - Captured current quality metrics
       - Provided maintenance procedures
       - Established best practices
