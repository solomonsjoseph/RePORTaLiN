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

Cross-Reference Best Practices (Updated October 2025)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.2.0
   Advanced cross-reference patterns to eliminate documentation duplication.

**Primary Principle: Single Source of Truth**

Always prefer cross-references over duplicating content. This ensures:

* ✅ No synchronization issues when code or examples change
* ✅ Clear authority for each topic
* ✅ Reduced maintenance burden
* ✅ Consistent information across documentation

**Creating Reference Targets**

To enable deep linking to specific sections, add reference targets:

.. code-block:: restructuredtext

   .. _deid-basic-example:

   Basic De-identification Example
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   This example shows how to de-identify patient data...

**Referencing Targets**

From another file, reference the target:

.. code-block:: restructuredtext

   For a complete example, see :ref:`deid-basic-example`.

**Cross-Reference Hierarchy**

Follow this hierarchy when deciding where content should live:

1. **User Guide** = Authoritative source for features and usage
   - Comprehensive examples
   - Step-by-step instructions
   - Troubleshooting
   
2. **API Documentation** = Reference for code details
   - Function signatures
   - Parameter descriptions
   - Return values
   - Minimal usage examples (1-3 lines)
   
3. **Developer Guide** = Technical architecture and extension
   - Cross-reference user guide for features
   - Cross-reference API for code details
   - Focus on "how to extend" not "how to use"

**Practical Examples**

**❌ BAD - Duplicate content:**

.. code-block:: restructuredtext

   # In api/scripts.rst
   De-identification Manager
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   The DeidManager class handles de-identification.

   Example:

   .. code-block:: python

      from scripts.deidentify import DeidManager
      
      manager = DeidManager()
      manager.load_config('config.py')
      manager.deidentify_data(df)

   # In user_guide/deidentification.rst
   Using De-identification
   ~~~~~~~~~~~~~~~~~~~~~~~

   Example:

   .. code-block:: python

      from scripts.deidentify import DeidManager
      
      manager = DeidManager()
      manager.load_config('config.py')
      manager.deidentify_data(df)

**✅ GOOD - Cross-references:**

.. code-block:: restructuredtext

   # In user_guide/deidentification.rst
   .. _deid-basic-example:

   Basic De-identification Example
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   The following example shows how to de-identify patient data:

   .. code-block:: python

      from scripts.deidentify import DeidManager
      
      manager = DeidManager()
      manager.load_config('config.py')
      manager.deidentify_data(df)

   # In api/scripts.rst
   De-identification Manager
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   For usage examples, see :ref:`deid-basic-example` in the user guide.

**Reference Naming Conventions**

Use clear, descriptive reference target names:

* Format: ``section-topic-type``
* Examples:
  - ``deid-basic-example``
  - ``country-regulations-india``
  - ``extract-data-advanced``
  - ``config-encryption-options``

**When to Create Reference Targets**

Create reference targets for:

* ✅ Code examples that might be referenced elsewhere
* ✅ Important conceptual sections
* ✅ Configuration examples
* ✅ Country-specific regulations or procedures
* ✅ Troubleshooting solutions

**Do NOT create targets for:**

* ❌ Every subsection (creates noise)
* ❌ Temporary/version-specific content
* ❌ Minor notes or tips

**Maintaining Cross-References**

When refactoring documentation:

1. Search for all references to the content being moved
2. Update cross-references to point to new location
3. Add reference targets if moving content requires deep linking
4. Build documentation and verify all links work
5. Update any related index entries

Link Validation
----------------

**3. Link Validation** (10 minutes)

   .. code-block:: bash

      # Build docs and check for broken references
      cd docs/sphinx
      make clean
      make html
      
      # Run link checker
      make linkcheck

   ✅ No broken cross-references (``WARNING: undefined label``)  
   ✅ No missing documents (``WARNING: document isn't included``)  
   ✅ External links are still valid  
   ✅ Internal reference targets resolve correctly

   The ``linkcheck`` target validates all external URLs and reports broken links.
   Review ``_build/linkcheck/output.txt`` for detailed results.
