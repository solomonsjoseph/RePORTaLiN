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

**Recent Enhancement (October 14, 2025):**
✅ Added colored output support for logs and progress bars

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
   user_guide/colored_output
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
   developer_guide/colored_output_implementation
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
   
   - **User Mode** (``make html-user``): Shows only user-facing documentation
   - **Developer Mode** (``make html-dev``): Includes developer guides and API documentation
   
   To switch modes, edit ``conf.py`` and set ``developer_mode = True`` or ``False``.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

