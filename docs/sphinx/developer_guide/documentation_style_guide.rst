Documentation Style Guide
==========================

**For Developers: Writing Standards and Best Practices**

This guide provides detailed style guidelines and documentation policies for writing and maintaining 
documentation in the RePORTaLiN project. All contributors must follow these standards to ensure
consistency and quality.

**Last Updated:** October 28, 2025  
**Version:** |version|  
**Status:** Active Guide

.. contents:: Table of Contents
   :local:
   :depth: 3

Core Documentation Principles
------------------------------

1. **Single Source of Truth**: All project documentation lives in Sphinx (``.rst`` files)
2. **No Markdown Proliferation**: Avoid creating ``.md`` files except README.md
3. **Audience-Specific Content**: Clear separation between user and developer documentation
4. **Version Accuracy**: All documentation matches current codebase version
5. **Quality Standards**: Concise, robust, accurate, and production-ready

Overview
--------

Documentation is critical for project success. This guide ensures all documentation:

* Uses reStructuredText (``.rst``) format exclusively (except README.md)
* Clearly separates user and developer audiences
* Maintains consistent formatting and style
* Stays current with codebase changes
* Follows professional technical writing standards

File Format Standards
----------------------

ReStructuredText (.rst) Required
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**All documentation must be in .rst format:**

✅ **REQUIRED:**
   - User guide files (``docs/sphinx/user_guide/*.rst``)
   - Developer guide files (``docs/sphinx/developer_guide/*.rst``)
   - API documentation (``docs/sphinx/api/*.rst``)
   - Changelog (``docs/sphinx/changelog.rst``)
   - All technical reports and audits

❌ **PROHIBITED:**
   - Markdown (``.md``) files (except ``README.md`` in project root)
   - Plain text (``.txt``) for documentation
   - Word documents (``.doc``, ``.docx``)
   - PDFs for source documentation

**Why .rst?**

* **Sphinx Integration**: Native format for Sphinx documentation generator
* **Advanced Features**: Better support for cross-references, directives, and roles
* **Extensibility**: Easy to add custom directives and extensions
* **PDF Generation**: Superior PDF output via LaTeX
* **Professional**: Industry standard for Python projects

README.md Exception
~~~~~~~~~~~~~~~~~~~

The only permitted ``.md`` file is ``README.md`` in the project root because:

* GitHub displays it automatically on repository homepage
* Quick overview for new contributors and users
* Links to full Sphinx documentation

Audience-Specific Headers
--------------------------

Every documentation file MUST start with an audience-specific header immediately
after the title.

User Guide Header
~~~~~~~~~~~~~~~~~

**All files in** ``docs/sphinx/user_guide/`` **must begin with:**

.. code-block:: restructuredtext

   File Title
   ==========

   **For Users: [Brief description of what users will learn]**

**Example:**

.. code-block:: restructuredtext

   Installation Guide
   ==================

   **For Users: How to install RePORTaLiN and set up your environment**

Developer Guide Header
~~~~~~~~~~~~~~~~~~~~~~~

**All files in** ``docs/sphinx/developer_guide/`` **must begin with:**

.. code-block:: restructuredtext

   File Title
   ==========

   **For Developers: [Brief description of technical content]**

**Example:**

.. code-block:: restructuredtext

   Architecture Overview
   =====================

   **For Developers: Technical architecture, design patterns, and system components**

Language and Tone
-----------------

User Documentation
~~~~~~~~~~~~~~~~~~

**Target Audience:** Researchers, data analysts, project managers (non-programmers)

**Writing Style:**

✅ **DO:**
   - Use simple, clear language
   - Define technical terms when necessary
   - Provide step-by-step instructions
   - Use concrete examples
   - Focus on "what" and "how" (not "why" technical details)
   - Write in active voice
   - Use short sentences and paragraphs

❌ **AVOID:**
   - Technical jargon (API, regex, module, class, function)
   - Implementation details
   - Code architecture discussions
   - Overly technical explanations
   - Passive voice constructions

**Example - User Documentation:**

.. code-block:: restructuredtext

   To protect patient privacy, the system removes all personal information:

   1. Names are replaced with random IDs
   2. Dates are shifted by a random number of days
   3. Addresses are removed completely

Developer Documentation
~~~~~~~~~~~~~~~~~~~~~~~~

**Target Audience:** Software developers, maintainers, contributors (programmers)

**Writing Style:**

✅ **DO:**
   - Use precise technical terminology
   - Explain architectural decisions
   - Include code examples
   - Reference specific modules, classes, functions
   - Discuss implementation details
   - Link to related code files
   - Explain "why" decisions were made

❌ **AVOID:**
   - Oversimplification
   - Omitting technical details
   - Vague descriptions
   - Missing code references

**Example - Developer Documentation:**

.. code-block:: restructuredtext

   The ``DeidManager`` class implements deterministic de-identification using:

   * SHA-256 cryptographic hashing for stable pseudonymization
   * Date shifting with consistent offsets per patient (via hash-based seeding)
   * Regex patterns for PII detection (see ``patterns.py``)
   * Configurable retention policies per field type

Formatting Standards
--------------------

Section Headers
~~~~~~~~~~~~~~~

Use consistent header hierarchy:

.. code-block:: restructuredtext

   Document Title
   ==============

   Major Section
   -------------

   Subsection
   ~~~~~~~~~~

   Sub-subsection
   ^^^^^^^^^^^^^^

Code Blocks
~~~~~~~~~~~

**For shell commands:**

.. code-block:: restructuredtext

   .. code-block:: bash

      python3 main.py --verbose
      make docs

**For Python code:**

.. code-block:: restructuredtext

   .. code-block:: python

      from scripts.extract_data import extract_all_data
      
      results = extract_all_data(config)

**For configuration files:**

.. code-block:: restructuredtext

   .. code-block:: yaml

      de_identification:
         enabled: true
         method: deterministic

Lists
~~~~~

**Bullet lists:**

.. code-block:: restructuredtext

   * First item
   * Second item
   * Third item

**Numbered lists:**

.. code-block:: restructuredtext

   1. First step
   2. Second step
   3. Third step

**Definition lists:**

.. code-block:: restructuredtext

   Term 1
      Definition of term 1

   Term 2
      Definition of term 2

Admonitions
~~~~~~~~~~~

Use Sphinx admonitions for important information:

.. code-block:: restructuredtext

   .. note::
      This is a note for additional information.

   .. warning::
      This is a warning about potential issues.

   .. danger::
      This is a critical warning about serious issues.

   .. tip::
      This is a helpful tip or best practice.

Cross-References
~~~~~~~~~~~~~~~~

**Link to other documentation:**

.. code-block:: restructuredtext

   See :doc:`installation` for setup instructions.
   See :doc:`../developer_guide/architecture` for technical details.

**Link to sections:**

.. code-block:: restructuredtext

   See `Configuration Options`_ below.

**Link to code:**

.. code-block:: restructuredtext

   See :py:func:`scripts.extract_data.extract_all_data`
   See :py:class:`scripts.deidentify.DeidManager`

Version Information
-------------------

Version Directives
~~~~~~~~~~~~~~~~~~

**Current Version (Present Tense):**

All **present-tense** version references MUST use the current version number:

.. code-block:: restructuredtext

   **Version:** |version|
   **Last Updated:** October 23, 2025
   **Current Version: |version|** (at top of index.rst)

**Historical Markers (Past Tense):**

Historical version markers should only appear in:

* ``changelog.rst`` - version history
* When explicitly discussing past versions (e.g., "Added in v0.0.12")

**Example in changelog:**

.. code-block:: restructuredtext

   Version 0.0.12 (December 2024)
   ------------------------------
   
   * Added verbose logging flag
   * Enhanced documentation

Last Updated Dates
~~~~~~~~~~~~~~~~~~

All documentation files should include:

.. code-block:: restructuredtext

   **Last Updated:** [Month Day, Year]
   **Version:** [Current version number]

Update these dates when making substantive changes to the file.

Maintenance Standards
---------------------

When to Update Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Documentation must be updated when:

* Adding new features
* Changing existing behavior
* Deprecating functionality
* Fixing bugs that affect documented behavior
* Updating configuration options
* Changing command-line arguments
* Modifying file formats or schemas

Review Checklist
~~~~~~~~~~~~~~~~

Before committing documentation changes, verify:

☑ File uses ``.rst`` format (not ``.md``)  
☑ Correct audience header present (For Users / For Developers)  
☑ Appropriate language/tone for target audience  
☑ All code examples tested and working  
☑ Cross-references are valid  
☑ Version information is current  
☑ No broken links or references  
☑ Sphinx builds without warnings/errors  
☑ Grammar and spelling checked  

Automated Compliance
--------------------

Style Checker Script
~~~~~~~~~~~~~~~~~~~~

Run the automated style checker before committing:

.. code-block:: bash

   ./scripts/utils/check_docs_style.sh

This script verifies:

* All user guide files have "For Users:" headers
* All developer guide files have "For Developers:" headers
* User guide files don't contain technical jargon
* Sphinx builds without warnings/errors

Git Pre-Commit Hook
~~~~~~~~~~~~~~~~~~~~

The ``.gitignore`` file blocks accidental ``.md`` commits:

.. code-block:: text

   # Block all Markdown files except README.md
   *.md
   !README.md

Common Patterns
---------------

Installation Instructions
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: restructuredtext

   Installation
   ------------

   1. Clone the repository:

      .. code-block:: bash

         git clone https://github.com/org/reportalin.git
         cd reportalin

   2. Install dependencies:

      .. code-block:: bash

         pip install -r requirements.txt

Configuration Examples
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: restructuredtext

   Configuration
   -------------

   Edit ``config.py`` to customize behavior:

   .. code-block:: python

      # Enable de-identification
      ENABLE_DEID = True
      
      # Set output format
      OUTPUT_FORMAT = "jsonl"

Troubleshooting
~~~~~~~~~~~~~~~

.. code-block:: restructuredtext

   Troubleshooting
   ---------------

   **Problem:** Error message XYZ

   **Solution:**
   
   1. Check that...
   2. Verify that...
   3. Try running...

   **Still not working?** See :doc:`../developer_guide/architecture` 
   for technical details.

API Documentation
~~~~~~~~~~~~~~~~~

.. code-block:: restructuredtext

   .. autofunction:: scripts.extract_data.extract_all_data
      :noindex:

   Example usage:

   .. code-block:: python

      from scripts.extract_data import extract_all_data
      
      results = extract_all_data(config)

Documentation Policy & Enforcement
-----------------------------------

Mandatory Requirements
~~~~~~~~~~~~~~~~~~~~~~~

All User Guide Files MUST
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Start with "For Users" Header**
2. **Use Simple Language** - No technical jargon
3. **Include Examples** - Real-world use cases with step-by-step instructions
4. **Use Friendly Tone** - Emojis where appropriate, "you" language

All Developer Guide Files MUST
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Start with "For Developers" Header**
2. **Use Technical Precision** - Full terminology, architecture diagrams, algorithms
3. **Include Implementation Details** - Code snippets, design patterns, edge cases
4. **Reference Code Directly** - Module names, function signatures, class hierarchies

NO Markdown Files Policy
~~~~~~~~~~~~~~~~~~~~~~~~~

❌ **PROHIBITED - DO NOT CREATE:**
   - ``FIXES.md``, ``AUDIT.md``, ``VERIFICATION.md``, ``STATUS.md``
   - ``CHANGES.md``, ``NOTES.md``
   - Any other ``.md`` files in project root or ``docs/``

✅ **INSTEAD, UPDATE:**
   - Relevant ``.rst`` files in ``docs/sphinx/``
   - Create new ``.rst`` in appropriate guide section
   - Add to existing documentation where content fits

Content Placement Guide
~~~~~~~~~~~~~~~~~~~~~~~

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
   * - User instructions
     - User Guide
     - Appropriate user guide file
   * - API changes
     - API Reference
     - Relevant ``api/*.rst`` file

Quality Checklist
~~~~~~~~~~~~~~~~~

**Before Committing Documentation Changes:**

.. code-block:: text

   [ ] All user guide files have "For Users" headers
   [ ] All developer guide files have "For Developers" headers
   [ ] User guide uses simple, friendly language
   [ ] Developer guide has sufficient technical detail
   [ ] Version directives use |version| substitution
   [ ] Assessment dates are current
   [ ] No .md files created (except README.md)
   [ ] Sphinx builds with 0 warnings/0 errors
   [ ] All code examples tested
   [ ] No redundant information

Automated Verification
~~~~~~~~~~~~~~~~~~~~~~

**Run before every commit:**

.. code-block:: bash

   # 1. Check documentation style
   bash scripts/utils/check_docs_style.sh
   
   # 2. Build Sphinx documentation
   cd docs/sphinx && make clean html
   
   # 3. Verify no warnings/errors
   # Expected: "build succeeded" with 0 warnings

Documentation Maintenance Checklist
------------------------------------

**For Developers: Quarterly Documentation Review**

To prevent documentation bloat and maintain quality, perform these checks quarterly:

Quarterly Review Tasks
~~~~~~~~~~~~~~~~~~~~~~

**1. Version Reference Audit** (15 minutes)

   .. code-block:: bash

      # Check for outdated version references
      cd docs/sphinx
      grep -r "versionadded:: 0\." user_guide/ developer_guide/ api/
      grep -r "versionchanged:: 0\." user_guide/ developer_guide/ api/

   ✅ Update version directives to current version  
   ✅ Archive old version markers to changelog if needed

**2. Redundancy Check** (30 minutes)

   Review for duplicate content across files:

   - [ ] Check if multiple files explain the same concept
   - [ ] Verify cross-references are used instead of content duplication
   - [ ] Consolidate overlapping content where possible
   - [ ] Update or remove outdated historical verification documents

**3. Link Validation** (10 minutes)

   .. code-block:: bash

      # Build docs and check for broken references
      cd docs/sphinx
      make clean
      make html

   ✅ No broken cross-references (``WARNING: undefined label``)  
   ✅ No missing documents (``WARNING: document isn't included``)  
   ✅ External links are still valid

**4. File Organization Review** (20 minutes)

   - [ ] All files have clear, unique purposes
   - [ ] Historical/archived content is in ``historical_verification.rst``
   - [ ] No orphaned files (not in any toctree)
   - [ ] Directory structure makes logical sense

**5. Style Compliance Check** (10 minutes)

   .. code-block:: bash

      # Run style checker
      bash scripts/utils/check_docs_style.sh

   ✅ All user docs have "**For Users:**" headers  
   ✅ All developer docs have "**For Developers:**" headers  
   ✅ No .md files except README.md  
   ✅ Consistent formatting throughout

**6. Content Freshness** (15 minutes)

   - [ ] Installation instructions match current dependencies
   - [ ] Code examples run without errors
   - [ ] Screenshots/examples reflect current UI/output
   - [ ] Troubleshooting section addresses current issues

**7. Size Management** (10 minutes)

   .. code-block:: bash

      # Check documentation size
      wc -l docs/sphinx/**/*.rst | tail -1
      
      # List largest files
      wc -l docs/sphinx/**/*.rst | sort -rn | head -10

   ✅ Total line count is reasonable (< 15,000 lines)  
   ✅ No single file exceeds 1,000 lines without good reason  
   ✅ Large files can be split or archived if needed

Archival Guidelines
~~~~~~~~~~~~~~~~~~~

Move content to ``historical_verification.rst`` if:

- ✅ It's a verification/audit from a past release
- ✅ It documents completed migration/reorganization work
- ✅ It's referenced in changelog but no longer needs active visibility
- ✅ It's valuable for audit trails but not for current development

**Example:** October 2025 verification documents were archived to reduce active 
documentation from ~15,000 to ~13,000 lines while preserving historical records.

When to Create New Files
~~~~~~~~~~~~~~~~~~~~~~~~~

Only create new documentation files when:

1. **New major feature** requires comprehensive guide (> 200 lines)
2. **New audience segment** needs dedicated content (e.g., data analysts)
3. **Complex topic** deserves standalone treatment (e.g., performance tuning)
4. **Regulatory requirement** mandates separate documentation

**Default:** Add content to existing files using new sections instead of new files.

Enforcement Policy
~~~~~~~~~~~~~~~~~~~

This policy is **mandatory** for all documentation changes. Pull requests that:

❌ Create new .md files (except README.md)  
❌ Use incorrect headers ("For Users" vs "For Developers")  
❌ Have outdated version references  
❌ Fail Sphinx build  
❌ Fail style checker  

Will be **rejected** until corrected.

**Exceptions:** Only ``README.md`` in project root, historical markers in ``changelog.rst``

Resources
---------

* **Sphinx Documentation:** https://www.sphinx-doc.org/
* **reStructuredText Primer:** https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
* **Google Developer Documentation Style Guide:** https://developers.google.com/style
* **Write the Docs:** https://www.writethedocs.org/guide/

Related Documentation
---------------------

* :doc:`contributing` - How to contribute to the project
* :doc:`architecture` - Technical architecture overview
* :doc:`historical_verification` - Archived verification and audit records

---

**Questions?** Contact the documentation team or open an issue on GitHub.
