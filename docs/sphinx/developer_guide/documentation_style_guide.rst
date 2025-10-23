Documentation Style Guide
==========================

**For Developers: Writing Standards and Best Practices**

This guide provides detailed style guidelines for writing and maintaining documentation
in the RePORTaLiN project. All contributors must follow these standards to ensure
consistency and quality.

**Last Updated:** October 23, 2025  
**Version:** |version|  
**Status:** Active Guide

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

Resources
---------

* **Sphinx Documentation:** https://www.sphinx-doc.org/
* **reStructuredText Primer:** https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
* **Google Developer Documentation Style Guide:** https://developers.google.com/style
* **Write the Docs:** https://www.writethedocs.org/guide/

Related Documentation
---------------------

* :doc:`documentation_policy` - Documentation standards and policies
* :doc:`contributing` - How to contribute to the project
* :doc:`architecture` - Technical architecture overview

---

**Questions?** Contact the documentation team or open an issue on GitHub.
