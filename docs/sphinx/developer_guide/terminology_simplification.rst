Terminology Simplification Audit
=================================

**For Developers: Documentation Language Review**

This document tracks the simplification of technical terminology in user-facing documentation
to ensure users have an easy-to-understand experience while developers retain access to
precise technical details.

**Date:** October 23, 2025  
**Version:** 0.3.0

Overview
--------

The documentation has been audited to ensure:

1. **User guides** use simple, non-technical language
2. **Developer guides** maintain technical precision
3. Code examples preserve technical accuracy
4. Cross-references appropriately label technical content

Changes Made
------------

Terminology Replacements in User Guides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following technical terms were replaced with user-friendly alternatives:

**General Technical Terms**

* ``module`` → ``tool`` / ``script`` (context-dependent)
* ``function`` → kept only in code examples
* ``API`` → ``technical documentation`` / ``using in Python code``
* ``parameter`` → ``setting`` / ``option``
* ``algorithm`` → ``method``
* ``architecture`` → ``design`` / ``technical design``
* ``parse`` → ``recognize`` / ``read``
* ``pattern`` → ``detection rule`` / kept in code examples
* ``compile`` → kept only in code examples
* ``REPL`` → ``interactive environments``
* ``dataclass`` → ``configuration options``
* ``thread-safe`` → ``designed to work reliably``

**Specific Replacements**

1. **troubleshooting.rst**
   
   * ``Module Import Errors`` → ``Missing Package Errors``
   * ``ModuleNotFoundError`` → Error message saying a package is not found
   * ``Logging module enhanced`` → ``Logging system enhanced``
   * ``thread-safe and optimized`` → ``designed to work reliably``
   * ``System architecture`` link → ``Technical system design``

2. **introduction.rst**
   
   * ``Dynamic dataset detection`` → ``Works with any dataset folder automatically``
   * ``Modular architecture`` → ``Easy to customize``
   * ``Command-line options`` → ``Options to run specific parts``

3. **configuration.rst**
   
   * ``detection algorithm`` → ``automatic detection``
   * ``REPL/notebook compatibility`` → ``interactive environments like Jupyter``
   * ``normalize_dataset_name() function`` → ``automatically cleans up dataset names``
   * ``DeidentificationConfig dataclass`` → ``configuration options``
   * ``Utility Functions`` section → ``Helper Tools``
   * ``Import from config module`` → ``Use the configuration file``
   * ``Module not found`` → ``Config file not found``
   * ``API documentation`` → ``technical documentation``

4. **installation.rst**
   
   * ``De-identification module`` → ``De-identification script``
   * ``ModuleNotFoundError`` → ``Package not found``

5. **quickstart.rst**
   
   * ``Module not found`` → ``Package not found``
   * ``ModuleNotFoundError`` → ``Package not found``

6. **deidentification.rst**
   
   * ``pattern detection`` → ``detection`` / ``smart detection``
   * ``Extensible pattern support`` → ``Easy to extend with new detection rules``
   * ``module automatically processes`` → ``tool automatically processes``
   * ``Algorithm: AES-128`` → ``Encryption method: AES-128``
   * ``Algorithm: SHA-256`` → ``Hash method: SHA-256``
   * ``Regular pattern updates`` → ``Regular updates to detection rules``
   * ``module implements`` → ``tool follows``
   * ``Pattern Matching`` → ``Detection Speed``
   * ``Pattern Priority`` → ``Detection Order``
   * ``pattern priorities`` → ``detection order``
   * ``intelligent multi-format date parsing`` → ``smart multi-format date recognition``
   * ``API Reference`` section → ``Technical Reference``

7. **country_regulations.rst**
   
   * ``parsed`` → ``recognized``
   * ``Python API`` section → ``Using in Python Code``
   * ``API Reference`` section → ``Technical Reference``

Preserved Technical Terms
~~~~~~~~~~~~~~~~~~~~~~~~~~

The following remain in user guides as they appear only in:

1. **Code examples** - Necessary for accurate Python code
   
   * ``pattern=re.compile()``
   * ``DetectionPattern``
   * ``custom_pattern``
   * Variable and function names in code blocks

2. **Error messages** - Exact Python error text for searchability
   
   * Kept in quotes for user recognition

3. **File/directory names** - Exact system paths
   
   * ``.logs/``
   * ``config.py``
   * ``__pycache__``

4. **Cross-references to developer docs** - Labeled appropriately
   
   * Links to ``../api/`` sections
   * Links to ``../developer_guide/`` sections

Style Checker Enhancements
---------------------------

Updated ``scripts/utils/check_docs_style.sh`` to detect technical jargon:

**Previous Detection:**

* Only checked for "For Users:" and "For Developers:" headers
* Limited technical term detection

**Enhanced Detection:**

* Checks for specific technical term phrases
* Excludes code blocks from jargon detection
* Provides detailed warnings with term locations
* Focus on prose text, not code examples

**New Technical Terms List:**

.. code-block:: bash

   TECH_TERMS=(
       "module reference"
       "function call"
       "class method"
       " API documentation"
       "parameter list"
       "decorator pattern"
       "singleton instance"
       "algorithm implementation"
       "dataclass definition"
       "instantiate object"
       "thread-safe implementation"
       "REPL environment"
       "__init__ method"
   )

Verification Results
--------------------

**Sphinx Build Status:**

* Build succeeded: ✓
* Warnings: 0
* Errors: 0
* HTML pages generated: 39

**Style Checker Results:**

* User guide headers: ✓ All pass (8/8 files)
* Developer guide headers: ✓ All pass (9/9 files)
* Technical jargon in user guides: ✓ None found
* Sphinx build: ✓ Success

**Files Modified:**

1. ``docs/sphinx/user_guide/troubleshooting.rst``
2. ``docs/sphinx/user_guide/introduction.rst``
3. ``docs/sphinx/user_guide/configuration.rst``
4. ``docs/sphinx/user_guide/installation.rst``
5. ``docs/sphinx/user_guide/quickstart.rst``
6. ``docs/sphinx/user_guide/deidentification.rst``
7. ``docs/sphinx/user_guide/country_regulations.rst``
8. ``scripts/utils/check_docs_style.sh``

Best Practices
--------------

Guidelines for Future Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**For User Guide Content:**

1. **Use plain language**
   
   * ❌ "The module instantiates a singleton pattern"
   * ✅ "The tool creates one instance automatically"

2. **Explain technical concepts simply**
   
   * ❌ "Uses SHA-256 cryptographic hashing algorithm"
   * ✅ "Uses SHA-256 hash method for security"

3. **Avoid jargon in headings**
   
   * ❌ "API Reference"
   * ✅ "Technical Reference" (in user guides)

4. **Code examples can use technical terms**
   
   * Keep variable names and Python keywords as-is
   * Add explanatory text in plain language

**For Developer Guide Content:**

1. **Use precise technical terminology**
   
   * ✅ "Implements singleton pattern with lazy initialization"
   * ✅ "Uses decorator pattern for cross-cutting concerns"

2. **Include implementation details**
   
   * Algorithm names, complexity analysis
   * Design patterns, architectural decisions
   * API contracts, type signatures

3. **Reference specific code elements**
   
   * Module names, class names, function signatures
   * Parameter types, return values

Testing Documentation Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before committing documentation changes:

1. **Run style checker:**
   
   .. code-block:: bash
   
      bash scripts/utils/check_docs_style.sh

2. **Build documentation:**
   
   .. code-block:: bash
   
      cd docs/sphinx
      make clean
      make html

3. **Verify no warnings/errors:**
   
   * Check build output for 0 warnings
   * Verify HTML generates correctly

4. **Manual review:**
   
   * Read as a non-technical user
   * Check code examples still work
   * Verify cross-references are accurate

Automation
----------

The style checker now runs automatically to enforce standards:

**What It Checks:**

1. ✓ All user guides have "**For Users:**" header
2. ✓ All developer guides have "**For Developers:**" header
3. ✓ User guides don't contain technical jargon (except in code)
4. ✓ Sphinx builds without warnings or errors

**How to Run:**

.. code-block:: bash

   # From project root
   bash scripts/utils/check_docs_style.sh

**Exit Codes:**

* ``0`` - All checks passed
* ``1`` - Errors found (must fix)
* Warnings reported but don't fail the check

Compliance Status
-----------------

**Current Status:** ✅ FULLY COMPLIANT

* All user guides use simple, accessible language
* All developer guides maintain technical precision
* Automated enforcement in place
* Documentation builds without errors
* Style guide documented and followed

**Enforcement Layers:**

1. **Policy** - ``documentation_policy.rst`` defines requirements
2. **Style Guide** - ``documentation_style_guide.rst`` provides examples
3. **Automation** - ``scripts/utils/check_docs_style.sh`` validates compliance
4. **Git Control** - ``.gitignore`` blocks non-compliant file types

See Also
--------

* :doc:`documentation_policy` - Documentation enforcement policy
* :doc:`documentation_style_guide` - Detailed style guide with examples
* :doc:`documentation_audit` - Comprehensive documentation audit
* :doc:`../changelog` - Version history and changes

