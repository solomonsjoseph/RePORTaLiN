Overview
========

What is RePORTaLiN?
-------------------

RePORTaLiN (Regional Prospective Observational Research for Tuberculosis Analysis in India) is a comprehensive data extraction and harmonization pipeline designed for tuberculosis research studies. The toolkit provides:

* **Automated Data Extraction**: Extract structured data from PDF case report forms (CRFs)
* **Data Dictionary Management**: Load and validate data dictionaries from Excel files
* **Data Validation**: Ensure data integrity across multiple sources
* **De-identification**: Automated removal of personally identifiable information (PII)
* **Vector Database**: Store and query extracted data using semantic search
* **Country-Specific Compliance**: Built-in support for HIPAA, GDPR, and PDPA regulations

Key Features
------------

Pipeline Architecture
~~~~~~~~~~~~~~~~~~~~~

RePORTaLiN follows a three-stage data processing pipeline:

1. **Dictionary Loading**: Load and parse data dictionaries from Excel files
2. **Data Extraction**: Extract data from PDF forms using LLM-based extraction
3. **De-identification**: Remove PII according to regulatory requirements

Vector Database Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The toolkit includes a sophisticated vector database system for:

* Semantic search across extracted data
* PDF document chunking and embedding
* Adaptive embedding strategies for optimal retrieval

LLM Integration
~~~~~~~~~~~~~~~

RePORTaLiN supports multiple LLM providers through a flexible adapter pattern:

* Configurable LLM backends
* Streaming response support
* JSON mode for structured extraction

Use Cases
---------

RePORTaLiN is designed for:

* Clinical research teams conducting TB studies
* Data managers handling multi-center trials
* Researchers requiring de-identified datasets
* Organizations needing regulatory-compliant data processing

Project Status
--------------

Current Version: |version|

The project is under active development with ongoing improvements to:

* Data extraction accuracy
* Vector database performance
* Documentation coverage
* Test coverage and validation
