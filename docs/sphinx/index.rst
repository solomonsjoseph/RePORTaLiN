.. RePORTaLiN documentation master file

Welcome to RePORTaLiN Documentation
===================================

**RePORTaLiN** is a robust data extraction pipeline for processing medical research data 
from Excel files to JSONL format with advanced PHI/PII de-identification capabilities.

**Current Version: |version| (October 28, 2025)**

.. image:: https://img.shields.io/badge/python-3.13+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.13+

.. image:: https://img.shields.io/badge/code%20style-optimized-brightgreen.svg
   :alt: Code Optimized 68%

.. image:: https://img.shields.io/badge/Privacy-Aware-blue.svg
   :target: https://www.hhs.gov/hipaa/index.html
   :alt: Privacy-Aware

Quick Links
-----------

📚 **New to RePORTaLiN?** Start here:
   - :doc:`user_guide/quickstart` - Get started in 5 minutes
   - :doc:`user_guide/installation` - Complete installation guide
   - :doc:`user_guide/usage` - Detailed usage instructions

🔧 **For Developers:**
   - :doc:`developer_guide/contributing` - How to contribute
   - :doc:`developer_guide/architecture` - Technical architecture
   - :doc:`api/modules` - Complete API reference

📋 **Reference:**
   - :doc:`changelog` - Version history and updates
   - :doc:`developer_guide/code_integrity_audit` - Code quality metrics

Key Features
------------

🌍 **Multi-Country Privacy Compliance**
   - 14 countries supported (US, IN, ID, BR, PH, ZA, EU, GB, CA, AU, KE, NG, GH, UG)
   - HIPAA, GDPR, LGPD, DPDPA, POPIA compliance
   - 21 PHI/PII identifier types detected and pseudonymized

🔒 **Security & Performance**
   - Encryption by default (AES-128)
   - Fast processing with optimized algorithms
   - Date shifting with temporal relationship preservation
   - Audit trails for compliance validation

📊 **Data Processing**
   - Multi-table detection from complex Excel layouts
   - JSONL output for efficient streaming
   - Progress tracking with real-time feedback
   - Duplicate detection and intelligent column handling

🔧 **Robust Configuration**
   - Enhanced error handling
   - Auto-detection of dataset folders
   - Type-safe with full type hints
   - Cross-platform support (macOS, Linux, Windows)

What's New in |version|
------------------------

See :doc:`changelog` for complete version history and detailed release notes.

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
   developer_guide/project_vision
   developer_guide/contributing
   developer_guide/extending
   developer_guide/auto_documentation
   developer_guide/code_integrity_audit
   developer_guide/production_readiness
   developer_guide/github_pages_deployment
   developer_guide/documentation_style_guide
   developer_guide/maintenance_summary
   developer_guide/historical_verification
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

