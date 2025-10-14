config module
=============

.. automodule:: config
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``config`` module provides centralized configuration management for RePORTaLiN.
All paths, settings, and parameters are defined here to ensure consistency across
all pipeline components.

Configuration Variables
-----------------------

Directory Paths
~~~~~~~~~~~~~~~

ROOT_DIR
^^^^^^^^

.. code-block:: python

   ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

Absolute path to the project root directory. All other paths are relative to this.

DATA_DIR
^^^^^^^^

.. code-block:: python

   DATA_DIR = os.path.join(ROOT_DIR, "data")

Path to the data directory containing input files.

RESULTS_DIR
^^^^^^^^^^^

.. code-block:: python

   RESULTS_DIR = os.path.join(ROOT_DIR, "results")

Path to the results directory for output files.

Dataset Paths
~~~~~~~~~~~~~

DATASET_BASE_DIR
^^^^^^^^^^^^^^^^

.. code-block:: python

   DATASET_BASE_DIR = os.path.join(DATA_DIR, "dataset")

Base directory containing dataset folders.

DATASET_DIR
^^^^^^^^^^^

.. code-block:: python

   DATASET_DIR = get_dataset_folder()

Path to the current dataset directory (auto-detected).

DATASET_NAME
^^^^^^^^^^^^

.. code-block:: python

   DATASET_NAME = (DATASET_FOLDER_NAME.replace('_csv_files', '').replace('_files', '') 
                   if DATASET_FOLDER_NAME else "RePORTaLiN_sample")

Name of the current dataset (e.g., "Indo-vap"), extracted by removing common suffixes
from the dataset folder name.

Output Paths
~~~~~~~~~~~~

CLEAN_DATASET_DIR
^^^^^^^^^^^^^^^^^

.. code-block:: python

   CLEAN_DATASET_DIR = os.path.join(RESULTS_DIR, "dataset", DATASET_NAME)

Output directory for extracted JSONL files.

DICTIONARY_JSON_OUTPUT_DIR
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DICTIONARY_JSON_OUTPUT_DIR = os.path.join(RESULTS_DIR, "data_dictionary_mappings")

Output directory for data dictionary tables.

Dictionary File
~~~~~~~~~~~~~~~

DICTIONARY_EXCEL_FILE
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DICTIONARY_EXCEL_FILE = os.path.join(
       DATA_DIR,
       "data_dictionary_and_mapping_specifications",
       "RePORT_DEB_to_Tables_mapping.xlsx"
   )

Path to the data dictionary Excel file.

Logging Settings
~~~~~~~~~~~~~~~~

LOG_LEVEL
^^^^^^^^^

.. code-block:: python

   LOG_LEVEL = logging.INFO

Logging verbosity level. Options:

- ``logging.DEBUG``: Detailed diagnostic information
- ``logging.INFO``: General informational messages (default)
- ``logging.WARNING``: Warning messages
- ``logging.ERROR``: Error messages only

LOG_NAME
^^^^^^^^

.. code-block:: python

   LOG_NAME = "reportalin"

Logger instance name used throughout the application.

Functions
---------

get_dataset_folder
~~~~~~~~~~~~~~~~~~

.. autofunction:: config.get_dataset_folder
   :no-index:

Automatically detect the dataset folder from the file system.

**Example**:

.. code-block:: python

   from config import get_dataset_folder
   
   folder = get_dataset_folder()
   print(f"Detected dataset: {folder}")

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   import config
   
   # Access configuration
   print(f"Dataset: {config.DATASET_NAME}")
   print(f"Input: {config.DATASET_DIR}")
   print(f"Output: {config.CLEAN_DATASET_DIR}")

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # config.py modifications
   import os
   
   # Use environment variable
   DATA_DIR = os.getenv("REPORTALIN_DATA", os.path.join(ROOT_DIR, "data"))
   
   # Custom logging
   import logging
   LOG_LEVEL = logging.DEBUG

Directory Structure
-------------------

The configuration defines this structure:

.. code-block:: text

   RePORTaLiN/
   ├── data/                           (DATA_DIR)
   │   ├── dataset/                    (DATASET_BASE_DIR)
   │   │   └── <dataset_name>/         (DATASET_DIR)
   │   └── data_dictionary_and_mapping_specifications/
   │       └── RePORT_DEB_to_Tables_mapping.xlsx  (DICTIONARY_EXCEL_FILE)
   │
   └── results/                        (RESULTS_DIR)
       ├── dataset/
       │   └── <dataset_name>/         (CLEAN_DATASET_DIR)
       └── data_dictionary_mappings/   (DICTIONARY_JSON_OUTPUT_DIR)

See Also
--------

:doc:`../user_guide/configuration`
   User guide for configuration

:mod:`main`
   Main pipeline that uses configuration

:mod:`scripts.extract_data`
   Data extraction using configuration paths
