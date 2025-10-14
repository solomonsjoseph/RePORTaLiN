scripts package
===============

.. automodule:: scripts
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``scripts`` package contains the core processing modules for RePORTaLiN.

Submodules
----------

.. toctree::
   :maxdepth: 2

   scripts.extract_data
   scripts.load_dictionary
   scripts.utils.logging
   scripts.utils.deidentify
   scripts.utils.country_regulations

Module Summary
--------------

extract_data
~~~~~~~~~~~~

.. currentmodule:: scripts.extract_data

Main data extraction module for converting Excel files to JSONL format.

Key functions:

- :func:`extract_excel_to_jsonl`: Batch processing of Excel files
- :func:`process_excel_file`: Single file processing
- :func:`convert_dataframe_to_jsonl`: DataFrame to JSONL conversion
- :func:`clean_record_for_json`: Type conversion for JSON serialization
- :func:`find_excel_files`: File discovery
- :func:`is_dataframe_empty`: Empty DataFrame detection

See: :doc:`scripts.extract_data`

load_dictionary
~~~~~~~~~~~~~~~

.. currentmodule:: scripts.load_dictionary

Data dictionary processing module with intelligent table detection.

Key functions:

- :func:`load_study_dictionary`: High-level API for dictionary loading
- :func:`process_excel_file`: Excel file processing
- :func:`_split_sheet_into_tables`: Automatic table detection
- :func:`_process_and_save_tables`: Table output
- :func:`_deduplicate_columns`: Duplicate column handling

See: :doc:`scripts.load_dictionary`

utils
~~~~~

Utility modules including de-identification and logging.

De-identification (``scripts.utils.deidentify``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: scripts.utils.deidentify

PHI/PII de-identification module with pseudonymization and encryption.

Key classes:

- :class:`DeidentificationEngine`: Main processing engine
- :class:`PseudonymGenerator`: Cryptographic pseudonym generation
- :class:`DateShifter`: Date shifting with interval preservation
- :class:`MappingStore`: Encrypted mapping storage
- :class:`PatternLibrary`: PHI/PII detection patterns

Key functions:

- :func:`deidentify_dataset`: Batch dataset de-identification
- :func:`validate_dataset`: Dataset validation

See: :doc:`scripts.utils.deidentify`

Logging (``scripts.utils.logging``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: scripts.utils.logging

Centralized logging module with custom SUCCESS level.

Key features:

- Custom SUCCESS log level
- Timestamped log files
- Dual output (console + file)
- Structured logging

See: :doc:`scripts.utils.logging`

Country Regulations (``scripts.utils.country_regulations``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: scripts.utils.country_regulations

Country-specific data privacy regulations module for compliance.

Key features:

- Multi-country support (14 countries)
- Privacy frameworks (PUBLIC to CRITICAL levels)
- Identifier detection and validation
- Regulatory requirements management
- Configuration export/import

See: :doc:`scripts.utils.country_regulations`

Quick Examples
--------------

Data Extraction
~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import extract_excel_to_jsonl
   import config
   
   # Extract all Excel files
   extract_excel_to_jsonl(
       input_dir=config.DATASET_DIR,
       output_dir=config.CLEAN_DATASET_DIR
   )

Dictionary Loading
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   import config
   
   # Load data dictionary
   load_study_dictionary(
       excel_file=config.DICTIONARY_EXCEL_FILE,
       output_dir=config.DICTIONARY_JSON_OUTPUT_DIR
   )

De-identification
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.deidentify import DeidentificationEngine
   
   # Initialize engine
   engine = DeidentificationEngine()
   
   # De-identify text
   original = "Patient John Doe, MRN: 123456, SSN: 123-45-6789"
   deidentified = engine.deidentify_text(original)
   
   # Save mappings
   engine.save_mappings()

Batch De-identification
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.deidentify import deidentify_dataset
   
   # Process entire dataset (maintains directory structure)
   stats = deidentify_dataset(
       input_dir="results/dataset/Indo-vap",
       output_dir="results/deidentified/Indo-vap",
       process_subdirs=True
   )
   
   print(f"Processed {stats['texts_processed']} texts")

Single File Processing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import process_excel_file
   from pathlib import Path
   
   # Process one file
   input_file = Path("data/dataset/Indo-vap/10_TST.xlsx")
   output_dir = Path("results/dataset/Indo-vap")
   
   result = process_excel_file(str(input_file), str(output_dir))
   print(f"Processed {result['records']} records")

Custom Logging
~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils import logging as log
   
   # Use custom logger
   log.info("Processing started")
   log.success("Operation completed successfully")
   log.warning("Potential issue detected")
   log.error("An error occurred", exc_info=True)

Country-Specific De-identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.country_regulations import CountryRegulationManager
   
   # Initialize for India
   manager = CountryRegulationManager()
   manager.set_country("IN")
   
   # Get identifiers
   identifiers = manager.get_identifiers()
   print(f"Found {len(identifiers)} identifiers for India")
   
   # Validate Aadhaar number
   is_valid = manager.validate_identifier("AADHAAR", "1234 5678 9012")

Module Dependencies
-------------------

.. code-block:: text

   scripts/
   ├── extract_data.py
   │   └── uses: logging, config
   │
   ├── load_dictionary.py
   │   └── uses: logging, config
   │
   └── utils/
       ├── logging.py
       │   └── uses: config
       ├── deidentify.py
       │   └── uses: config, country_regulations, cryptography (optional)
       └── country_regulations.py
           └── uses: re, json, dataclasses

See Also
--------

:doc:`../user_guide/usage`
   Usage examples

:doc:`../developer_guide/architecture`
   Architecture documentation

:doc:`main`
   Main module that orchestrates scripts
