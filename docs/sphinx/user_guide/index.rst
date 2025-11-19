User Guide
==========

Welcome to the RePORTaLiN user guide! This guide will help you get started with using RePORTaLiN for clinical trial data extraction and harmonization.

.. note::
   This is the **user documentation**. If you're a developer looking to contribute or extend RePORTaLiN, see the :doc:`../developer_guide/index`.

What is RePORTaLiN?
-------------------

RePORTaLiN (Regional Prospective Observational Research for Tuberculosis Analysis in India) is a comprehensive data extraction and harmonization pipeline for tuberculosis research studies.

**Key Features:**

- **Automated Data Extraction**: Extract structured data from PDF forms and Excel datasets
- **Privacy-Preserving Deidentification**: Remove PII according to HIPAA, GDPR, and other regulations
- **AI-Powered Analysis**: Use LLMs for intelligent document understanding
- **Vector Database Storage**: Enable semantic search across clinical trial data
- **Configurable Pipeline**: Customize every step of the data processing workflow

Who Should Use This Guide?
---------------------------

This guide is for:

- **Researchers** who want to extract and analyze clinical trial data
- **Data Managers** who need to harmonize data from multiple sources
- **Clinicians** who want to deidentify and store patient data safely
- **Anyone** working with tuberculosis research data

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   overview
   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Documentation

   configuration
   data_pipeline
   faq

Quick Start Guide
-----------------

New to RePORTaLiN? Start here:

1. **Read the** :doc:`overview` to understand what RePORTaLiN does
2. **Follow the** :doc:`installation` guide to install RePORTaLiN
3. **Try the** :doc:`quickstart` tutorial to run your first pipeline
4. **Configure** your pipeline with :doc:`configuration`
5. **Learn** the full pipeline in :doc:`data_pipeline`

Common User Tasks
-----------------

Need to accomplish a specific task? Jump to:

- **Extract data from PDFs**: See :doc:`data_pipeline`
- **Deidentify patient data**: See :doc:`data_pipeline`
- **Configure LLM providers**: See :doc:`configuration`
- **Load data dictionaries**: See :doc:`data_pipeline`
- **Store data in vector database**: See :doc:`data_pipeline`
- **Troubleshoot issues**: See :doc:`faq`

Getting Help
------------

If you need help:

- Check the :doc:`faq` for common questions
- Review the :doc:`data_pipeline` documentation
- Open an issue on GitHub
- Check the :doc:`../developer_guide/index` for technical details

Next Steps
----------

Ready to get started? Head to:

- :doc:`installation` - Install RePORTaLiN on your system
- :doc:`quickstart` - Run your first data extraction pipeline
- :doc:`configuration` - Customize RePORTaLiN for your needs
