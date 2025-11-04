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
   **Major refactoring**: Removed legacy dataset detection logic. Added dynamic study
   detection with ``detect_study_name()``. Introduced standardized folder structure
   with ``datasets/``, ``annotated_pdfs/``, and ``data_dictionary/`` subdirectories.
   Removed backward compatibility with old folder naming.

Module Metadata
---------------

__version__
~~~~~~~~~~~

.. code-block:: python

   __version__ = '0.3.0'

Module version string.

__all__
~~~~~~~

.. code-block:: python

   __all__ = [
       'BASE_DIR', 'DATA_DIR', 'OUTPUT_DIR', 'LOGS_DIR', 'TMP_DIR',
       'STUDY_NAME', 'STUDY_DATA_DIR',
       'DATASETS_DIR', 'ANNOTATED_PDFS_DIR', 'DATA_DICTIONARY_DIR',
       'DICTIONARY_EXCEL_FILE', 'DICTIONARY_JSON_OUTPUT_DIR',
       'LOG_LEVEL', 'LOG_NAME',
       'ensure_directories', 'validate_config', 'detect_study_name',
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

   DEFAULT_DATASET_NAME = "Indo-VAP"

Default dataset name used when no study folder is detected.

.. versionchanged:: 0.3.0
   Changed from "RePORTaLiN_sample" to "Indo-VAP".

Directory Paths
~~~~~~~~~~~~~~~

BASE_DIR
^^^^^^^^

.. code-block:: python

   BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

Absolute path to the project root directory. All other paths are relative to this.

.. versionchanged:: 0.3.0
   Renamed from ``ROOT_DIR`` to ``BASE_DIR`` for clarity.

DATA_DIR
^^^^^^^^

.. code-block:: python

   DATA_DIR = os.path.join(BASE_DIR, "data")

Path to the data directory containing all study data.

Study Configuration
~~~~~~~~~~~~~~~~~~~

STUDY_NAME
^^^^^^^^^^

.. code-block:: python

   STUDY_NAME = detect_study_name()

Name of the current study, automatically detected by scanning the data directory.
Falls back to ``DEFAULT_DATASET_NAME`` if no study folders are found.

.. versionadded:: 0.3.0
   Dynamic study detection replaces hardcoded dataset name.

STUDY_DATA_DIR
^^^^^^^^^^^^^^

.. code-block:: python

   STUDY_DATA_DIR = os.path.join(DATA_DIR, STUDY_NAME)

Base directory for the current study's data (e.g., ``data/Indo-VAP/``).

.. versionadded:: 0.3.0

Study Data Directories
~~~~~~~~~~~~~~~~~~~~~~

DATASETS_DIR
^^^^^^^^^^^^

.. code-block:: python

   DATASETS_DIR = os.path.join(STUDY_DATA_DIR, "datasets")

Directory containing study dataset files (Excel/CSV files).

**Example structure**:

.. code-block:: text

   data/Indo-VAP/datasets/
   ├── 1A_ICScreening.xlsx
   ├── 1B_HCScreening.xlsx
   └── ...

.. versionadded:: 0.3.0
   Replaces ``DATASET_DIR`` with standardized naming.

ANNOTATED_PDFS_DIR
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   ANNOTATED_PDFS_DIR = os.path.join(STUDY_DATA_DIR, "annotated_pdfs")

Directory containing annotated PDF files for the study.

**Example structure**:

.. code-block:: text

   data/Indo-VAP/annotated_pdfs/
   ├── 1A Index Case Screening v1.0.pdf
   ├── 1B HHC Screening v1.0.pdf
   └── ...

.. versionadded:: 0.3.0

DATA_DICTIONARY_DIR
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DATA_DICTIONARY_DIR = os.path.join(STUDY_DATA_DIR, "data_dictionary")

Directory containing data dictionary and mapping specification files.

**Example structure**:

.. code-block:: text

   data/Indo-VAP/data_dictionary/
   └── RePORT_DEB_to_Tables_mapping.xlsx

.. versionadded:: 0.3.0

Output Paths
~~~~~~~~~~~~

OUTPUT_DIR
^^^^^^^^^^

.. code-block:: python

   OUTPUT_DIR = os.path.join(BASE_DIR, "output")

Base directory for all output files.

.. versionadded:: 0.3.0
   Replaces ``RESULTS_DIR``.

LOGS_DIR
^^^^^^^^

.. code-block:: python

   LOGS_DIR = os.path.join(BASE_DIR, ".logs")

Directory for log files.

.. versionadded:: 0.3.0

TMP_DIR
^^^^^^^

.. code-block:: python

   TMP_DIR = os.path.join(BASE_DIR, "tmp")

Directory for temporary files.

.. versionadded:: 0.3.0

DICTIONARY_JSON_OUTPUT_DIR
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DICTIONARY_JSON_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "data_dictionary_mappings")

Output directory for processed data dictionary files.

.. versionchanged:: 0.3.0
   Now uses ``OUTPUT_DIR`` instead of ``RESULTS_DIR``.

Dictionary File
~~~~~~~~~~~~~~~

DICTIONARY_EXCEL_FILE
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DICTIONARY_EXCEL_FILE = os.path.join(
       DATA_DICTIONARY_DIR,
       "RePORT_DEB_to_Tables_mapping.xlsx"
   )

Path to the data dictionary Excel file.

.. versionchanged:: 0.3.0
   Now uses ``DATA_DICTIONARY_DIR`` for standardized path.

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

detect_study_name
~~~~~~~~~~~~~~~~~

.. autofunction:: config.detect_study_name
   :no-index:

Automatically detect the study name by scanning the data directory structure.

**Returns**:
  - ``str``: Name of the first valid study folder found, or ``DEFAULT_DATASET_NAME`` if none exist

**Algorithm**:
  1. Lists all subdirectories in ``DATA_DIR``
  2. Excludes hidden folders (starting with '.')
  3. Returns the first folder found (alphabetically sorted)
  4. Falls back to ``DEFAULT_DATASET_NAME`` if no folders exist

**Example**:

.. code-block:: python

   from config import detect_study_name
   
   study = detect_study_name()
   print(f"Detected study: {study}")  # Output: "Indo-VAP"

.. versionadded:: 0.3.0
   Replaces ``get_dataset_folder()`` with simplified logic.

ensure_directories
~~~~~~~~~~~~~~~~~~

.. autofunction:: config.ensure_directories
   :no-index:

Create necessary output directories if they don't exist. Creates:
  - ``OUTPUT_DIR``
  - ``LOGS_DIR``
  - ``TMP_DIR``
  - ``DICTIONARY_JSON_OUTPUT_DIR``

**Example**:

.. code-block:: python

   from config import ensure_directories
   
   # Create all required directories
   ensure_directories()

.. versionchanged:: 0.3.0
   Now creates ``OUTPUT_DIR``, ``LOGS_DIR``, and ``TMP_DIR`` instead of legacy paths.

validate_config
~~~~~~~~~~~~~~~

.. autofunction:: config.validate_config
   :no-index:

Validate configuration and raise errors if critical paths are missing.

**Raises**:
  - ``FileNotFoundError``: If any required directory or file doesn't exist

**Validates**:
  - ``DATA_DIR`` exists
  - ``STUDY_DATA_DIR`` exists
  - ``DATASETS_DIR`` exists
  - ``ANNOTATED_PDFS_DIR`` exists
  - ``DATA_DICTIONARY_DIR`` exists
  - ``DICTIONARY_EXCEL_FILE`` exists

**Example**:

.. code-block:: python

   from config import validate_config
   
   try:
       validate_config()
       print("Configuration is valid!")
   except FileNotFoundError as e:
       print(f"Configuration error: {e}")

.. versionchanged:: 0.3.0
   Now raises exceptions instead of returning warnings. Validates new directory structure.

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from config import (
       STUDY_NAME,
       DATASETS_DIR,
       ANNOTATED_PDFS_DIR,
       DATA_DICTIONARY_DIR,
       validate_config
   )
   
   # Validate configuration on startup
   validate_config()
   
   # Access study-specific paths
   print(f"Current study: {STUDY_NAME}")
   print(f"Datasets location: {DATASETS_DIR}")
   print(f"Annotated PDFs location: {ANNOTATED_PDFS_DIR}")
   
   # List all datasets for current study
   import os
   datasets = [f for f in os.listdir(DATASETS_DIR) if f.endswith('.xlsx')]
   print(f"Found {len(datasets)} dataset files")

Dynamic Study Detection
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from config import detect_study_name, DATA_DIR
   import os
   
   # Detect available studies
   study = detect_study_name()
   print(f"Auto-detected study: {study}")
   
   # List all available studies
   studies = [d for d in os.listdir(DATA_DIR) 
              if os.path.isdir(os.path.join(DATA_DIR, d)) 
              and not d.startswith('.')]
   print(f"Available studies: {studies}")

Working with Multiple Studies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import os
   from config import DATA_DIR
   
   # Process all available studies
   for study in os.listdir(DATA_DIR):
       study_path = os.path.join(DATA_DIR, study)
       if os.path.isdir(study_path) and not study.startswith('.'):
           datasets_dir = os.path.join(study_path, "datasets")
           if os.path.exists(datasets_dir):
               print(f"Processing study: {study}")
               # Process datasets...

Using Utility Functions
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from config import ensure_directories, validate_config
   
   # Ensure all output directories exist
   ensure_directories()
   
   # Validate configuration before processing
   try:
       validate_config()
       print("All required directories and files exist")
   except FileNotFoundError as e:
       print(f"Configuration error: {e}")
       exit(1)

Best Practices
--------------

1. **Always validate configuration at startup**:

   .. code-block:: python

      from config import validate_config, ensure_directories
      
      # Validate input paths
      validate_config()
      
      # Create output directories
      ensure_directories()

2. **Use constants instead of hardcoded values**:

   .. code-block:: python

      from config import DATASETS_DIR, STUDY_NAME
      
      # Good
      dataset_path = os.path.join(DATASETS_DIR, "1A_ICScreening.xlsx")
      
      # Avoid
      dataset_path = f"data/{STUDY_NAME}/datasets/1A_ICScreening.xlsx"

3. **Handle missing directories gracefully**:

   .. code-block:: python

      from config import validate_config
      
      try:
          validate_config()
      except FileNotFoundError as e:
          logger.error(f"Configuration error: {e}")
          logger.info("Please ensure data structure follows the standard layout")
          exit(1)

Directory Structure
-------------------

The configuration defines this standardized structure:

.. code-block:: text

   RePORTaLiN/
   ├── data/                              (DATA_DIR)
   │   └── {STUDY_NAME}/                  (STUDY_DATA_DIR)
   │       ├── datasets/                  (DATASETS_DIR)
   │       │   ├── 1A_ICScreening.xlsx
   │       │   ├── 1B_HCScreening.xlsx
   │       │   └── ...
   │       ├── annotated_pdfs/            (ANNOTATED_PDFS_DIR)
   │       │   ├── 1A Index Case Screening v1.0.pdf
   │       │   └── ...
   │       └── data_dictionary/           (DATA_DICTIONARY_DIR)
   │           └── RePORT_DEB_to_Tables_mapping.xlsx
   │
   ├── output/                            (OUTPUT_DIR)
   │   └── data_dictionary_mappings/      (DICTIONARY_JSON_OUTPUT_DIR)
   ├── .logs/                             (LOGS_DIR)
   └── tmp/                               (TMP_DIR)

Migration from v0.2.x
---------------------

**Breaking Changes**:

The following constants and functions have been **removed**:

- ``ROOT_DIR`` → Use ``BASE_DIR``
- ``RESULTS_DIR`` → Use ``OUTPUT_DIR``
- ``DATASET_BASE_DIR`` → No longer needed (use ``STUDY_DATA_DIR``)
- ``DATASET_FOLDER_NAME`` → Use ``STUDY_NAME``
- ``DATASET_DIR`` → Use ``DATASETS_DIR``
- ``DATASET_NAME`` → Use ``STUDY_NAME``
- ``CLEAN_DATASET_DIR`` → Build path dynamically with ``OUTPUT_DIR``
- ``DATASET_SUFFIXES`` → No longer needed
- ``get_dataset_folder()`` → Use ``detect_study_name()``
- ``normalize_dataset_name()`` → No longer needed

**Migration example**:

.. code-block:: python

   # Old (v0.2.x)
   from config import DATASET_DIR, DATASET_NAME, CLEAN_DATASET_DIR
   
   # New (v0.3.0)
   from config import DATASETS_DIR, STUDY_NAME, OUTPUT_DIR
   
   # Old path construction
   input_path = os.path.join(DATASET_DIR, "file.xlsx")
   output_path = os.path.join(CLEAN_DATASET_DIR, "file.jsonl")
   
   # New path construction
   input_path = os.path.join(DATASETS_DIR, "file.xlsx")
   output_path = os.path.join(OUTPUT_DIR, "dataset", STUDY_NAME, "file.jsonl")

See Also
--------

:doc:`../user_guide/data_migration`
   User guide for data structure and migration

:doc:`../developer_guide/migration_system`
   Technical details on migration system

:doc:`../changelog`
   Version 0.3.0 changes and breaking changes

:mod:`main`
   Main pipeline that uses configuration

:mod:`scripts.extract_data`
   Data extraction using configuration paths
