Data Pipeline
=============

The RePORTaLiN pipeline processes clinical trial data through three main stages:

1. Dictionary Loading
2. Data Extraction
3. De-identification

This document provides detailed information about each stage.

Pipeline Architecture
---------------------

.. code-block:: text

   ┌─────────────────────┐
   │  Data Dictionary    │
   │  (Excel Files)      │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  Stage 1:           │
   │  Load Dictionary    │
   │  (load_dictionary)  │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐      ┌─────────────────┐
   │  Annotated PDFs     │      │  Excel Datasets │
   └──────────┬──────────┘      └────────┬────────┘
              │                          │
              └──────────┬───────────────┘
                         ▼
              ┌─────────────────────┐
              │  Stage 2:           │
              │  Extract Data       │
              │  (extract_data)     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Stage 3:           │
              │  De-identify        │
              │  (deidentify)       │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Output:            │
              │  Clean, De-ID Data  │
              └─────────────────────┘

Stage 1: Dictionary Loading
----------------------------

Purpose
~~~~~~~

Load and parse data dictionary files to understand the structure and validation rules for the data.

Input
~~~~~

* Excel files containing field definitions
* Column mappings and data types
* Validation rules and constraints

Process
~~~~~~~

1. Read Excel files from the dictionary directory
2. Parse field definitions and metadata
3. Extract validation rules
4. Create structured dictionary objects
5. Save parsed dictionaries for downstream use

Output
~~~~~~

* Structured data dictionary (JSON/DataFrame)
* Field validation rules
* Type mappings

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

   from scripts.load_dictionary import load_data_dictionary
   
   # Load dictionary from Excel file
   dictionary = load_data_dictionary(
       dict_path="data/Indo-VAP/data_dictionary/RePORT_DEB_to_Tables_mapping.xlsx"
   )
   
   # Access field definitions
   for field in dictionary.fields:
       print(f"{field.name}: {field.type}")

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

* ``DICT_PATH``: Path to dictionary files
* ``DICT_FORMAT``: Format of dictionary files ("excel", "csv")
* ``SHEET_NAME``: Sheet name in Excel files

Stage 2: Data Extraction
-------------------------

Purpose
~~~~~~~

Extract structured data from PDF case report forms and Excel datasets using LLM-based extraction.

Input
~~~~~

* Annotated PDF forms
* Excel datasets
* Data dictionary from Stage 1

Process
~~~~~~~

1. Read PDF files and parse content
2. Chunk documents for processing
3. Use LLM to extract structured data
4. Validate against data dictionary
5. Merge data from multiple sources
6. Handle missing or invalid data

Output
~~~~~~

* Extracted data in structured format
* Validation reports
* Error logs for problematic records

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import extract_from_pdfs
   
   # Extract data from PDF forms
   extracted_data = extract_from_pdfs(
       pdf_dir="data/Indo-VAP/annotated_pdfs",
       dictionary=dictionary,
       output_format="excel"
   )
   
   # Review extraction results
   print(f"Extracted {len(extracted_data)} records")

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

* ``INPUT_PATH``: Path to source PDF/Excel files
* ``LLM_PROVIDER``: LLM provider for extraction
* ``LLM_MODEL``: Specific model to use
* ``EXTRACTION_BATCH_SIZE``: Number of records per batch

Extraction Strategies
~~~~~~~~~~~~~~~~~~~~~

**PDF Extraction**

* Text-based extraction for searchable PDFs
* OCR for scanned documents
* LLM-based field identification

**Excel Extraction**

* Direct column mapping
* Fuzzy matching for field names
* Data type conversion

**Validation**

* Required field checks
* Data type validation
* Range and constraint validation
* Cross-field validation rules

Stage 3: De-identification
---------------------------

Purpose
~~~~~~~

Remove or pseudonymize personally identifiable information (PII) to comply with privacy regulations.

Input
~~~~~

* Extracted data from Stage 2
* De-identification rules
* Compliance region configuration

Process
~~~~~~~

1. Identify PII fields from data dictionary
2. Apply de-identification transformations:
   
   * Date shifting
   * Name removal/pseudonymization
   * Location generalization
   * Identifier hashing
   * Free-text redaction

3. Generate de-identification report
4. Validate de-identified data

Output
~~~~~~

* De-identified dataset
* De-identification mapping (secure storage)
* Audit trail

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

   from scripts.deidentify import deidentify_dataset
   
   # De-identify extracted data
   deidentified_data = deidentify_dataset(
       data=extracted_data,
       compliance_region="USA",  # HIPAA compliance
       date_shift_days=365
   )
   
   # Verify de-identification
   print(f"Removed {deidentified_data.pii_removed_count} PII fields")

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

* ``DEIDENTIFY_ENABLED``: Enable/disable de-identification
* ``COMPLIANCE_REGION``: "USA" (HIPAA), "EU" (GDPR), "Singapore" (PDPA)
* ``DATE_SHIFT_DAYS``: Days to shift dates (random offset)
* ``HASH_SALT``: Salt for identifier hashing

De-identification Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Direct Identifiers**

* Names: Removed or replaced with pseudonyms
* IDs: Hashed with secure salt
* Contact info: Removed

**Quasi-Identifiers**

* Dates: Shifted by random offset
* Ages: Binned (e.g., <18, 18-64, 65+)
* Locations: Generalized (e.g., ZIP to region)

**Free Text**

* NER-based PII detection
* Pattern matching for IDs
* Redaction or replacement

Running the Full Pipeline
--------------------------

Automated Execution
~~~~~~~~~~~~~~~~~~~

Run all three stages in sequence:

.. code-block:: bash

   python main.py

Or use the Makefile:

.. code-block:: bash

   make all

Manual Step-by-Step
~~~~~~~~~~~~~~~~~~~~

Run each stage individually:

.. code-block:: bash

   # Stage 1: Load dictionary
   python scripts/load_dictionary.py
   
   # Stage 2: Extract data
   python scripts/extract_data.py
   
   # Stage 3: De-identify
   python scripts/deidentify.py

Pipeline Monitoring
-------------------

Logging
~~~~~~~

All pipeline operations are logged to:

* Console output (configurable)
* Log files in ``logs/`` directory
* Structured logs with timestamps and levels

Progress Tracking
~~~~~~~~~~~~~~~~~

Monitor pipeline progress:

.. code-block:: python

   from scripts.utils.logging_system import get_logger
   
   logger = get_logger(__name__)
   logger.info("Starting extraction...")

Error Handling
~~~~~~~~~~~~~~

The pipeline includes comprehensive error handling:

* Graceful failures with detailed error messages
* Partial results saved on error
* Recovery from interrupted execution

Performance Optimization
------------------------

Batch Processing
~~~~~~~~~~~~~~~~

Process records in batches for efficiency:

.. code-block:: python

   EXTRACTION_BATCH_SIZE = 100  # Records per batch

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Use multiprocessing for CPU-bound tasks:

.. code-block:: python

   NUM_WORKERS = 4  # Parallel workers

Caching
~~~~~~~

Cache intermediate results:

* LLM responses
* Parsed PDF content
* Validation results

Best Practices
--------------

1. **Validate inputs**: Check data dictionary and source files before processing
2. **Monitor logs**: Review logs for errors and warnings
3. **Test on subset**: Run on small dataset first
4. **Backup data**: Keep original data secure
5. **Document changes**: Track pipeline configuration changes
6. **Review de-identification**: Manually verify PII removal

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Extraction Errors**

* Check PDF readability
* Verify LLM API connectivity
* Review data dictionary mapping

**Validation Failures**

* Check field types in dictionary
* Review validation rules
* Inspect source data quality

**De-identification Issues**

* Verify compliance region configuration
* Check date shift configuration
* Review PII detection patterns

Next Steps
----------

* See :doc:`configuration` for detailed configuration options
* See :doc:`../developer_guide/api_reference` for API documentation
* See :doc:`faq` for frequently asked questions
