.. RePORTaLiN documentation master file

Welcome to RePORTaLiN Documentation
===================================

**RePORTaLiN** is a robust data extraction pipeline for processing medical research data 
from Excel files to JSONL format. It features intelligent table detection, comprehensive 
logging, progress tracking, and robust error handling.

.. image:: https://img.shields.io/badge/python-3.13+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.13+

.. image:: https://img.shields.io/badge/code%20style-clean-brightgreen.svg
   :alt: Code Style

Quick Start
-----------

Install and run in 3 simple steps:

.. code-block:: bash

   # 1. Install dependencies
   pip install -r requirements.txt

   # 2. Run the pipeline
   python main.py

   # 3. View results in results/dataset/<dataset_name>/

Key Features
------------

🚀 **Fast & Efficient**
   Process 43 Excel files in ~15-20 seconds

📊 **Smart Table Detection**
   Automatically splits Excel sheets into multiple tables

� **De-identification**
   HIPAA-compliant PHI/PII removal with pseudonymization

�📝 **Comprehensive Logging**
   Timestamped logs with detailed operation tracking

📈 **Progress Tracking**
   Real-time progress bars for all operations

🔧 **Configurable**
   Centralized configuration management

📖 **Well Documented**
   Comprehensive user and developer documentation

🔒 **Secure**
   Encrypted mapping storage for de-identification

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
   developer_guide/testing
   developer_guide/extending
   developer_guide/production_readiness

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
   
   - **User Mode** (``make html-user``): Shows only user-facing documentation
   - **Developer Mode** (``make html-dev``): Includes developer guides and API documentation
   
   To switch modes, edit ``conf.py`` and set ``developer_mode = True`` or ``False``.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

