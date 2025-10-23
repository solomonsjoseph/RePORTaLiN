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

.. versionchanged:: 0.3.0
   Added ``ensure_directories()``, ``validate_config()``, and ``normalize_dataset_name()`` functions.
   Enhanced error handling and type safety. Fixed suffix removal bug.

Module Metadata
---------------

__version__
~~~~~~~~~~~

.. code-block:: python

   __version__ = '1.0.0'

Module version string.

__all__
~~~~~~~

.. code-block:: python

   __all__ = [
       'ROOT_DIR', 'DATA_DIR', 'RESULTS_DIR', 'DATASET_BASE_DIR',
       'DATASET_FOLDER_NAME', 'DATASET_DIR', 'DATASET_NAME', 'CLEAN_DATASET_DIR',
       'DICTIONARY_EXCEL_FILE', 'DICTIONARY_JSON_OUTPUT_DIR',
       'LOG_LEVEL', 'LOG_NAME',
       'ensure_directories', 'validate_config',
       'DEFAULT_DATASET_NAME'
   ]

Public API exports. Only these symbols are exported with ``from config import *``.

Configuration Variables
-----------------------

Constants
~~~~~~~~~

DEFAULT_DATASET_NAME
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DEFAULT_DATASET_NAME = "RePORTaLiN_sample"

Default dataset name used when no dataset folder is detected.

.. versionadded:: 0.3.0
   Extracted as a public constant.

DATASET_SUFFIXES
^^^^^^^^^^^^^^^^

.. code-block:: python

   DATASET_SUFFIXES = ('_csv_files', '_files')

Tuple of common suffixes removed from dataset folder names during normalization.

.. versionadded:: 0.3.0
   Internal constant (not in __all__).

Directory Paths
~~~~~~~~~~~~~~~

ROOT_DIR
^^^^^^^^

.. code-block:: python

   ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

Absolute path to the project root directory. All other paths are relative to this.

.. versionchanged:: 0.3.0
   Added fallback to ``os.getcwd()`` when ``__file__`` is not available (REPL environments).

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

   DATASET_NAME = normalize_dataset_name(DATASET_FOLDER_NAME)

Name of the current dataset (e.g., "Indo-vap"), extracted by removing common suffixes
from the dataset folder name using the ``normalize_dataset_name()`` function.

.. versionchanged:: 0.3.0
   Now uses ``normalize_dataset_name()`` function for improved suffix handling.

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

Automatically detect the dataset folder from the file system. Returns the first
alphabetically sorted folder in ``data/dataset/``, excluding hidden folders
(those starting with '.').

**Returns**:
  - ``str``: Name of the detected dataset folder
  - ``None``: If no folders exist or directory is inaccessible

**Example**:

.. code-block:: python

   from config import get_dataset_folder
   
   folder = get_dataset_folder()
   if folder:
       print(f"Detected dataset: {folder}")
   else:
       print("No dataset folder found")

.. versionchanged:: 0.3.0
   Removed faulty ``'..' not in f`` check. Added explicit empty list validation.

normalize_dataset_name
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: config.normalize_dataset_name
   :no-index:

Normalize dataset folder name by removing common suffixes.

**Parameters**:
  - ``folder_name`` (``Optional[str]``): The dataset folder name to normalize

**Returns**:
  - ``str``: Normalized dataset name

**Algorithm**:
  Removes the longest matching suffix from ``DATASET_SUFFIXES`` to handle
  overlapping suffixes correctly (e.g., ``_csv_files`` vs ``_files``).

**Examples**:

.. code-block:: python

   from config import normalize_dataset_name
   
   # Remove suffix
   name = normalize_dataset_name("Indo-vap_csv_files")
   print(name)  # Output: "Indo-vap"
   
   # Handle overlapping suffixes
   name = normalize_dataset_name("test_files")
   print(name)  # Output: "test"
   
   # Fallback to default
   name = normalize_dataset_name(None)
   print(name)  # Output: "RePORTaLiN_sample"

.. versionadded:: 0.3.0
   Extracted from inline code. Uses longest-match algorithm.

ensure_directories
~~~~~~~~~~~~~~~~~~

.. autofunction:: config.ensure_directories
   :no-index:

Create necessary directories if they don't exist. Creates:
  - ``RESULTS_DIR``
  - ``CLEAN_DATASET_DIR``
  - ``DICTIONARY_JSON_OUTPUT_DIR``

**Example**:

.. code-block:: python

   from config import ensure_directories
   
   # Create all required directories
   ensure_directories()

.. versionadded:: 0.3.0
   New utility function for directory management.

validate_config
~~~~~~~~~~~~~~~

.. autofunction:: config.validate_config
   :no-index:

Validate configuration and return list of warnings for missing or invalid paths.

**Returns**:
  - ``List[str]``: List of warning messages (empty if all valid)

**Validates**:
  - ``DATA_DIR`` exists
  - ``DATASET_DIR`` exists
  - ``DICTIONARY_EXCEL_FILE`` exists

**Example**:

.. code-block:: python

   from config import validate_config
   
   warnings = validate_config()
   if warnings:
       print("Configuration warnings:")
       for warning in warnings:
           print(f"  - {warning}")
   else:
       print("Configuration is valid!")

.. versionadded:: 0.3.0
   New utility function for configuration validation.

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

Using New Utility Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from config import ensure_directories, validate_config
   
   # Ensure all directories exist
   ensure_directories()
   
   # Validate configuration
   warnings = validate_config()
   if warnings:
       for warning in warnings:
           print(f"Warning: {warning}")

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

Best Practices
--------------

1. **Always call ensure_directories()** before file operations:

   .. code-block:: python

      from config import ensure_directories, CLEAN_DATASET_DIR
      
      ensure_directories()
      # Now safe to write to CLEAN_DATASET_DIR

2. **Validate configuration at startup**:

   .. code-block:: python

      from config import validate_config
      
      warnings = validate_config()
      if warnings:
          logger.warning("Configuration issues detected:")
          for warning in warnings:
              logger.warning(f"  {warning}")

3. **Use constants instead of hardcoded values**:

   .. code-block:: python

      from config import DEFAULT_DATASET_NAME
      
      # Good
      dataset = folder_name or DEFAULT_DATASET_NAME
      
      # Avoid
      dataset = folder_name or "RePORTaLiN_sample"

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
   User guide for configuration and utility functions

:doc:`../user_guide/quickstart`
   Quick start guide with configuration validation

:doc:`../user_guide/troubleshooting`
   Troubleshooting with validation utilities

:doc:`../developer_guide/extending`
   Extending the configuration module

:doc:`../developer_guide/contributing`
   Configuration module contribution guidelines

:doc:`../changelog`
   Version 0.0.3 changes and enhancements

:mod:`main`
   Main pipeline that uses configuration

:mod:`scripts.extract_data`
   Data extraction using configuration paths
