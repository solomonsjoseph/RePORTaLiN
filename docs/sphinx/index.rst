.. RePORTaLiN documentation master file

Welcome to RePORTaLiN Documentation
===================================

**RePORTaLiN** is a robust data extraction pipeline for processing medical research data 
from Excel files to JSONL format with advanced PHI/PII de-identification capabilities.

**Recent Optimization (October 13, 2025):**  
✅ 68% code reduction (1,235 lines removed) while maintaining 100% functionality  
✅ Comprehensive developer and user documentation added  
✅ All edge cases and algorithms thoroughly documented

.. image:: https://img.shields.io/badge/python-3.13+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.13+

.. image:: https://img.shields.io/badge/code%20style-optimized-brightgreen.svg
   :alt: Code Optimized 68%

Quick Start
-----------

Install and run in 3 simple steps:

.. code-block:: bash

   # 1. Install dependencies
   pip install -r requirements.txt

   # 2. Run the pipeline
   python3 main.py

   # 3. View results in results/dataset/<dataset_name>/

Code Optimization Summary
--------------------------

**Files Optimized (October 2025):**

==================  ==============  ==============  ===========
File                Original Lines  Optimized Lines Reduction
==================  ==============  ==============  ===========
config.py           146             47              68%
main.py             284             136             52%
extract_data.py     554             176             68%
load_dictionary.py  449             129             71%
logging.py          387             97              75%
**TOTAL**           **1,820**       **585**         **68%**
==================  ==============  ==============  ===========

**Result:** 1,235 lines removed, 100% functionality preserved

**Files Retained (Security/Compliance):**

- ``deidentify.py`` (1,129 lines) - HIPAA/GDPR compliance documentation
- ``country_regulations.py`` (1,280 lines) - 14 country privacy regulations

**Recent Enhancements (October 15, 2025):**

- **v0.0.12** (Latest): Added verbose logging and auto-rebuild features:
  
  * **Verbose Logging**: Added ``-v`` / ``--verbose`` command-line flag for DEBUG-level logging
  * Enhanced logging in all core modules (load_dictionary, extract_data, deidentify)
  * Detailed file processing information, duplicate detection, and PHI/PII counts
  * **Auto-Rebuild Docs**: Added ``make docs-watch`` for live documentation preview
  * Automatic rebuild on file changes with browser auto-refresh
  * Added ``sphinx-autobuild>=2021.3.14`` to dependencies
  * Updated documentation (README, user guide, troubleshooting, architecture, contributing)
  * Minimal performance impact (<2% slowdown)
  * Console output remains clean (verbose details only in log file)

- **v0.0.11**: Enhanced ``main.py`` pipeline entry point with:
  
  * Enhanced module docstring with comprehensive usage examples (162 lines, 2,214% increase)
  * Added explicit public API via ``__all__`` (2 exports: ``main``, ``run_step``)
  * Complete command-line arguments documentation
  * Pipeline steps explanation (Dictionary → Extraction → De-identification)
  * Four usage examples (basic, custom, de-identification, advanced)
  * Output structure with directory tree
  * Error handling and return codes documented
  * Version synchronized to 0.0.11
  * Backward compatible with zero breaking changes

- **v0.0.10**: Enhanced ``scripts/utils/__init__.py`` package-level API with:
  
  * Enhanced package docstring with comprehensive usage examples (150 lines, 4,900% increase)
  * Version tracking added (v0.0.10) with version history
  * Complete integration examples (logging, de-identification, privacy compliance)
  * Module structure documentation with visual tree
  * Five complete usage examples for all utility modules
  * Cross-references to all 3 submodules
  * Backward compatible with zero breaking changes

- **v0.0.9**: Enhanced ``scripts/__init__.py`` package-level API with:
  
  * Enhanced package docstring with comprehensive usage examples (127 lines, 2,440% increase)
  * Version synchronized to 0.0.9 (aligned with latest module enhancements)
  * Complete integration examples (pipeline, custom processing, de-identification)
  * Module structure documentation with visual tree
  * Version history tracking and cross-references
  * Backward compatible with zero breaking changes
  * Clear API guidance (package vs submodule imports)

**Recent Enhancements (October 14, 2025):**

- **v0.0.8**: Enhanced ``scripts/load_dictionary.py`` with:
  
  * Explicit public API definition via ``__all__`` (2 exports)
  * Enhanced module docstring with comprehensive usage examples (97 lines, 1,400% increase)
  * Algorithm documentation (7-step table detection process)
  * Return type hints on all functions and robust error handling verified
  * Backward compatible with zero breaking changes
  * Code quality verified with code density 44.4%

- **v0.0.7**: Enhanced ``scripts/extract_data.py`` with:
  
  * Explicit public API definition via ``__all__`` (6 exports)
  * Enhanced module docstring with comprehensive usage examples (40 lines, 790% increase)
  * Complete type hint coverage verified and robust error handling
  * Backward compatible with zero breaking changes
  * Code quality verified with code density 64.2%

- **v0.0.6**: Enhanced ``scripts/deidentify.py`` with:
  
  * Explicit public API definition via ``__all__`` (10 exports)
  * Enhanced module docstring with comprehensive usage examples (48 lines)
  * Complete return type annotations for improved type safety
  * Backward compatible with zero breaking changes
  * Code quality verified with robust error handling

- **v0.0.5**: Enhanced ``scripts/utils/country_regulations.py`` with explicit public API (6 exports) and comprehensive usage examples in docstring
- **v0.0.4**: Enhanced ``scripts/utils/logging.py`` module with improved type hints, optimized performance (no record mutation), and explicit public API (12 exports)
- **v0.0.3**: Enhanced ``config.py`` module with utility functions, bug fixes, and improved robustness

See :doc:`changelog` for complete details.

Documentation Sections
----------------------

👥 **For Users** - Learn how to install and use RePORTaLiN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: 👥 User Guide

   user_guide/introduction
   user_guide/installation
   user_guide/quickstart
   user_guide/configuration
   user_guide/usage
   user_guide/deidentification
   user_guide/country_regulations
   user_guide/troubleshooting

🔧 **For Developers** - Contribute to RePORTaLiN development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: 🔧 Developer Guide

   developer_guide/architecture
   developer_guide/contributing
   developer_guide/extending
   developer_guide/code_integrity_audit
   developer_guide/production_readiness
   developer_guide/future_enhancements

📚 **API Reference** - Technical documentation for all modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 3
   :caption: 📚 API Reference

   api/modules
   api/main
   api/config
   api/scripts

📋 **Additional Information**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1
   :caption: 📋 Additional Information

   changelog
   license

.. note::
   
   **📖 Documentation Modes**
   
   This documentation can be built in two modes:
   
   - **User Mode** (``make user-mode``): Shows only user-facing documentation
   - **Developer Mode** (``make dev-mode``): Includes developer guides and API documentation
   
   Alternatively, set the ``DEVELOPER_MODE`` environment variable (``True``/``False``) 
   or edit ``conf.py`` and set ``developer_mode = True`` or ``False``.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

