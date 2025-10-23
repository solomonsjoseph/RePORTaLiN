Documentation Policy
====================

**For Developers: Documentation Standards and Guidelines**

This document establishes the documentation standards and policies for the RePORTaLiN project
to ensure consistency, maintainability, and professional quality across all documentation.

**Last Updated:** October 23, 2025  
**Version:** |version|  
**Status:** Active Policy

Core Principles
---------------

1. **Single Source of Truth**: All project documentation lives in Sphinx (``.rst`` files)
2. **No Markdown Proliferation**: Avoid creating ``.md`` files except README.md
3. **Audience-Specific Content**: Clear separation between user and developer documentation
4. **Version Accuracy**: All documentation matches current codebase version
5. **Quality Standards**: Concise, robust, accurate, and production-ready

Documentation Structure
-----------------------

File Organization
~~~~~~~~~~~~~~~~~

.. code-block:: text

   docs/sphinx/
   ├── index.rst                      # Main documentation index
   ├── changelog.rst                  # Version history (historical markers preserved)
   ├── license.rst                    # Project license
   ├── user_guide/                    # FOR USERS (simple, straightforward)
   │   ├── introduction.rst
   │   ├── installation.rst
   │   ├── quickstart.rst
   │   ├── configuration.rst
   │   ├── usage.rst
   │   ├── deidentification.rst
   │   ├── country_regulations.rst
   │   └── troubleshooting.rst
   ├── api/                           # API Reference (technical)
   │   ├── modules.rst
   │   ├── config.rst
   │   ├── main.rst
   │   └── scripts.*.rst
   └── developer_guide/               # FOR DEVELOPERS (technical jargon)
       ├── architecture.rst
       ├── contributing.rst
       ├── extending.rst
       ├── code_integrity_audit.rst
       ├── production_readiness.rst
       ├── future_enhancements.rst
       ├── documentation_audit.rst
       ├── documentation_policy.rst   # This file
       └── documentation_style_guide.rst

**Exception:** ``README.md`` in project root (required by GitHub, mirrors introduction.rst)

Mandatory Requirements
----------------------

All User Guide Files MUST
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Start with "For Users" Header**:
   
   .. code-block:: rst
   
      Introduction
      ============
      
      **For Users: Simple and Straightforward Guide**

2. **Use Simple Language**:
   - ✅ "Click the button to start"
   - ❌ "Execute the initialization routine via CLI invocation"

3. **Avoid Technical Jargon**:
   - ✅ "detailed logging mode"
   - ❌ "DEBUG-level logging with stack traces"

4. **Include Examples**:
   - Real-world use cases
   - Step-by-step instructions
   - Expected output examples

5. **Use Friendly Tone**:
   - Emojis where appropriate (✅, 🚀, 📊, etc.)
   - "You" language (second person)
   - Encouraging and helpful

All Developer Guide Files MUST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Start with "For Developers" Header**:
   
   .. code-block:: rst
   
      Architecture
      ============
      
      **For Developers: Comprehensive Technical Documentation**

2. **Use Technical Precision**:
   - Full technical terminology
   - Architecture diagrams
   - Algorithm explanations
   - Data structure details
   - Performance metrics

3. **Include Implementation Details**:
   - Code snippets with explanations
   - Design patterns used
   - Edge cases and handling
   - Testing strategies

4. **Reference Code Directly**:
   - Module names, function signatures
   - Class hierarchies
   - Dependency chains

Version Directive Standards
----------------------------

Present-Tense Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

All ``.. versionadded::`` and ``.. versionchanged::`` directives in present-tense
documentation (user guide, API reference, current developer docs) MUST use the
**current release version**:

.. code-block:: rst

   .. versionadded:: 0.3.0
      New feature description
   
   .. versionchanged:: 0.3.0
      Change description

Historical Documentation
~~~~~~~~~~~~~~~~~~~~~~~~

Preserve historical version markers ONLY in:

- ``changelog.rst`` - Complete version history (v0.0.1 through current)
- Enhancement notes - Historical tracking of improvements
- Audit records - Dated assessments and reviews

Assessment Metadata Standards
------------------------------

All Assessment Documents MUST Include
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

   **Assessment Date**: October 23, 2025  
   **Version**: |version|  
   **Status**: Current Status
   **Reviewer**: Team/Individual Name

Update assessment dates when:
- Content is substantially revised
- New version is released
- Major findings change

NO Markdown Files Policy
-------------------------

Prohibited Actions
~~~~~~~~~~~~~~~~~~

❌ **DO NOT CREATE**:
- ``FIXES.md``
- ``AUDIT.md``
- ``VERIFICATION.md``
- ``STATUS.md``
- ``CHANGES.md``
- ``NOTES.md``
- Any other ``.md`` files in project root or docs/

✅ **INSTEAD, UPDATE**:
- Relevant ``.rst`` files in ``docs/sphinx/``
- Create new ``.rst`` in appropriate guide section
- Add to existing documentation where content fits

Where to Put Different Content Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Content Type
     - Destination
     - File
   * - Bug fixes
     - Developer Guide
     - ``code_integrity_audit.rst`` or ``changelog.rst``
   * - New features
     - User Guide + Developer Guide
     - Appropriate guide files + ``changelog.rst``
   * - Architecture changes
     - Developer Guide
     - ``architecture.rst``
   * - Code audits
     - Developer Guide
     - ``code_integrity_audit.rst``
   * - Documentation updates
     - Developer Guide
     - ``documentation_audit.rst``
   * - Production readiness
     - Developer Guide
     - ``production_readiness.rst``
   * - Future plans
     - Developer Guide
     - ``future_enhancements.rst``
   * - Contributing guidelines
     - Developer Guide
     - ``contributing.rst``
   * - User instructions
     - User Guide
     - Appropriate user guide file
   * - API changes
     - API Reference
     - Relevant ``api/*.rst`` file

Automation and Verification
----------------------------

Style Checker Script
~~~~~~~~~~~~~~~~~~~~

Use the automated documentation style checker:

.. code-block:: bash

   python docs/check_doc_style.py

This verifies:
- ✅ All user guide files have "For Users" headers
- ✅ All developer guide files have "For Developers" headers
- ✅ No present-tense v0.0.x version directives
- ✅ No outdated date references
- ✅ All required files present

Run Before Every Commit
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Check documentation style
   python docs/check_doc_style.py
   
   # 2. Build Sphinx documentation
   cd docs/sphinx && make clean html
   
   # 3. Verify no warnings/errors
   # Expected: "build succeeded" with 0 warnings

Git Pre-commit Hook
~~~~~~~~~~~~~~~~~~~

Optionally install the pre-commit hook to automate checks:

.. code-block:: bash

   cp docs/pre-commit-hook.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit

Sphinx Build Requirements
--------------------------

All Documentation Changes MUST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Build Successfully**:
   - 0 warnings
   - 0 errors
   - All pages generate HTML

2. **Pass Style Checks**:
   - Correct headers for audience
   - Appropriate language level
   - Proper version directives

3. **Maintain Consistency**:
   - Follow existing file structure
   - Match tone of similar documents
   - Use consistent formatting

Common Patterns
---------------

Adding New User Feature
~~~~~~~~~~~~~~~~~~~~~~~

1. Update ``docs/sphinx/user_guide/usage.rst`` or appropriate file
2. Add simple example with screenshot/output
3. Update ``changelog.rst`` with user-facing description
4. Update ``README.md`` if major feature
5. Build and verify

Adding Developer Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Update ``docs/sphinx/developer_guide/architecture.rst`` or appropriate file
2. Include technical details, code references
3. Update ``changelog.rst`` with technical details
4. Update API documentation if needed
5. Build and verify

Reporting Bugs/Issues
~~~~~~~~~~~~~~~~~~~~~

1. Add to ``docs/sphinx/developer_guide/code_integrity_audit.rst``
2. Create GitHub issue (if applicable)
3. Update ``changelog.rst`` when fixed
4. DO NOT create separate .md file

Version Bumps
~~~~~~~~~~~~~

1. Update ``pyproject.toml`` version
2. Update all present-tense ``.. versionadded::/.. versionchanged::`` directives
3. Update assessment dates in developer docs
4. Add new section to ``changelog.rst``
5. Update ``README.md`` version badge (if present)
6. Build and verify all documentation

Quality Checklist
-----------------

Before Committing Documentation Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   [ ] All user guide files have "For Users" headers
   [ ] All developer guide files have "For Developers" headers
   [ ] User guide uses simple, friendly language
   [ ] Developer guide has sufficient technical detail
   [ ] Version directives match current version (|version|)
   [ ] Assessment dates are current
   [ ] No .md files created (except README.md)
   [ ] Sphinx builds with 0 warnings/0 errors
   [ ] Style checker passes
   [ ] Content is concise and robust
   [ ] No redundant information
   [ ] All code examples tested

Review Process
--------------

Self-Review
~~~~~~~~~~~

1. Read documentation as target audience
2. Verify all links work
3. Test all code examples
4. Check spelling and grammar
5. Ensure consistency with existing docs

Automated Checks
~~~~~~~~~~~~~~~~

1. Run style checker: ``python docs/check_doc_style.py``
2. Build documentation: ``cd docs/sphinx && make clean html``
3. Verify output: Check for warnings/errors
4. Review generated HTML: Open in browser

Enforcement
-----------

This policy is **mandatory** for all documentation changes. Pull requests that:

- ❌ Create new .md files (except README.md)
- ❌ Use incorrect headers ("For Users" vs "For Developers")
- ❌ Have outdated version references
- ❌ Fail Sphinx build
- ❌ Fail style checker

Will be **rejected** until corrected.

Exceptions
----------

The only approved exceptions are:

1. ``README.md`` in project root (GitHub requirement)
2. Historical version markers in ``changelog.rst``
3. Temporary development notes (must be in ``.gitignore``)

Contact
-------

For questions about this policy, see:

- :doc:`documentation_style_guide` - Detailed style guidelines
- :doc:`contributing` - General contribution guidelines
- :doc:`documentation_audit` - Latest audit results

**This is a living document. Update as standards evolve.**

.. versionadded:: 0.3.0
   Initial documentation policy established
