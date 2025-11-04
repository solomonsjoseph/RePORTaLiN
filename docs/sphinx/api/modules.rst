API Reference
=============

This section provides detailed API documentation for all modules in the RePORTaLiN codebase.

Overview
--------

RePORTaLiN's API is organized into several modules:

.. toctree::
   :maxdepth: 2

   __version__
   main
   config
   scripts
   scripts.utils

Core Modules
------------

:mod:`__version__`
~~~~~~~~~~~~~~~~~~

Single source of truth for version information.

See: :doc:`__version__`

:mod:`main`
~~~~~~~~~~~

Main pipeline orchestrator and entry point.

See: :doc:`main`

:mod:`config`
~~~~~~~~~~~~~

Configuration management and path resolution.

See: :doc:`config`

:mod:`scripts`
~~~~~~~~~~~~~~

Core processing modules for data extraction and dictionary loading.

See: :doc:`scripts`

:mod:`scripts.utils`
~~~~~~~~~~~~~~~~~~~~

Utility functions and classes used across the RePORTaLiN pipeline.

See: :doc:`scripts.utils`

Quick Reference
---------------

Common Functions
~~~~~~~~~~~~~~~~

**Data Extraction**:

.. code-block:: python

   from scripts.extract_data import extract_excel_to_jsonl, process_excel_file
   
   # Extract all files
   extract_excel_to_jsonl(input_dir, output_dir)
   
   # Process single file
   process_excel_file(file_path, output_dir)

**Dictionary Loading**:

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   
   # Load data dictionary
   load_study_dictionary(excel_file, output_dir)

**Configuration**:

.. code-block:: python

   import config
   
   # Access paths
   print(config.DATASET_DIR)
   print(config.CLEAN_DATASET_DIR)

**Logging**:

.. code-block:: python

   from scripts.utils import logging as log
   
   logger = log.get_logger(__name__)
   logger.info("Processing...")
   logger.success("Complete!")

**Data Migration**:

.. code-block:: python

   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Test migration
   manager = DataMigrationManager(dry_run=True)
   manager.run_migration()
   
   # Run actual migration
   manager = DataMigrationManager(dry_run=False)
   manager.run_migration()
   log.info("Information message")
   log.success("Success message")
   log.warning("Warning message")
   log.error("Error message")

Common Patterns
---------------

Process All Files
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import find_excel_files, process_excel_file
   from pathlib import Path
   
   input_dir = Path("data/dataset/my_data")
   output_dir = Path("output/my_data")
   
   files = find_excel_files(input_dir)
   for file in files:
       process_excel_file(file, output_dir)

Read JSONL Output
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   
   # Read JSONL file
   df = pd.read_json('output.jsonl', lines=True)

Custom Processing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import convert_dataframe_to_jsonl
   
   # Read and transform
   df = pd.read_excel('input.xlsx')
   df['new_column'] = df['old_column'].apply(lambda x: x * 2)
   
   # Export
   convert_dataframe_to_jsonl(df, 'output.jsonl', 'input.xlsx')

**Logging (scripts.utils)**:

.. code-block:: python

   from scripts.utils import logging as log
   
   # Get logger for your module
   logger = log.get_logger(__name__)
   logger.info("Processing started")
   logger.success("Processing completed successfully!")
   
   # Or use quick access functions
   from scripts.utils.logging import info, success, warning, error
   info("Quick logging message")
   success("Operation successful!")

**Country Regulations (scripts.utils)**:

.. code-block:: python

   from scripts.utils.country_regulations import get_country_config
   
   # Get country-specific configuration
   config = get_country_config('India')
   print(f"PII fields: {config.pii_fields}")
   print(f"Date format: {config.date_format}")

Module Index
------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
