Configuration
=============

RePORTaLiN uses a centralized configuration system through the ``config.py`` module. 
This guide explains all configuration options and how to customize them.

.. versionchanged:: 0.0.3
   Added new utility functions (``ensure_directories()``, ``validate_config()``), 
   improved error handling, and fixed suffix removal bugs.

Configuration File
------------------

The main configuration file is ``config.py`` in the project root. It defines all paths, 
settings, and parameters used throughout the pipeline.

What's New in v0.0.3
~~~~~~~~~~~~~~~~~~~~~

✨ **New Features**:
   - ``ensure_directories()`` - Automatically creates all required directories
   - ``validate_config()`` - Validates configuration and returns warnings
   - Enhanced error handling for missing files and directories
   - Better suffix normalization (handles overlapping suffixes correctly)
   - REPL/Jupyter notebook compatibility

Dynamic Dataset Detection
-------------------------

RePORTaLiN automatically detects your dataset folder:

.. code-block:: python

   # config.py automatically finds the first folder in data/dataset/
   DATASET_DIR = os.path.join(DATA_DIR, "dataset", dataset_folder)

This means you can work with any dataset without modifying code:

.. code-block:: text

   data/dataset/
   └── my_study_data/         # Automatically detected
       ├── file1.xlsx
       └── file2.xlsx

.. versionchanged:: 0.0.3
   Improved detection algorithm with better error handling and edge case coverage.

Configuration Variables
-----------------------

Project Root
~~~~~~~~~~~~

.. code-block:: python

   ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

- **Purpose**: Absolute path to project root directory
- **Usage**: All other paths are relative to this
- **Modification**: Not recommended (auto-detected)

.. versionchanged:: 0.0.3
   Added fallback to ``os.getcwd()`` for REPL/notebook compatibility.

Data Directories
~~~~~~~~~~~~~~~~

.. code-block:: python

   DATA_DIR = os.path.join(ROOT_DIR, "data")
   RESULTS_DIR = os.path.join(ROOT_DIR, "results")

- **DATA_DIR**: Location of raw input data
- **RESULTS_DIR**: Location for processed outputs
- **Modification**: Can be changed if you want different locations

Dataset Paths
~~~~~~~~~~~~~

.. code-block:: python

   DATASET_BASE_DIR = os.path.join(DATA_DIR, "dataset")
   DATASET_FOLDER_NAME = get_dataset_folder()  # Auto-detected
   DATASET_DIR = os.path.join(DATASET_BASE_DIR, DATASET_FOLDER_NAME or DEFAULT_DATASET_NAME)
   DATASET_NAME = normalize_dataset_name(DATASET_FOLDER_NAME)

- **DATASET_BASE_DIR**: Parent directory for all datasets
- **DATASET_FOLDER_NAME**: Name of detected folder (returned by ``get_dataset_folder()``)
- **DATASET_DIR**: Full path to current dataset (auto-detected)
- **DATASET_NAME**: Cleaned dataset name (e.g., "Indo-vap_csv_files" → "Indo-vap")

.. versionchanged:: 0.0.3
   Now uses ``normalize_dataset_name()`` function with improved suffix handling.
   Uses ``DEFAULT_DATASET_NAME`` constant instead of hardcoded string.

Output Directories
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   CLEAN_DATASET_DIR = os.path.join(RESULTS_DIR, "dataset", DATASET_NAME)
   DICTIONARY_JSON_OUTPUT_DIR = os.path.join(RESULTS_DIR, "data_dictionary_mappings")

- **CLEAN_DATASET_DIR**: Where extracted JSONL files are saved
- **DICTIONARY_JSON_OUTPUT_DIR**: Where dictionary tables are saved

Data Dictionary
~~~~~~~~~~~~~~~

.. code-block:: python

   DICTIONARY_EXCEL_FILE = os.path.join(
       DATA_DIR, 
       "data_dictionary_and_mapping_specifications",
       "RePORT_DEB_to_Tables_mapping.xlsx"
   )

- **Purpose**: Path to the data dictionary Excel file
- **Modification**: Change filename if your dictionary has a different name

Logging Settings
~~~~~~~~~~~~~~~~

.. code-block:: python

   LOG_LEVEL = logging.INFO
   LOG_NAME = "reportalin"

- **LOG_LEVEL**: Controls verbosity (INFO, DEBUG, WARNING, ERROR)
- **LOG_NAME**: Logger instance name

Available log levels:

- ``logging.DEBUG``: Detailed diagnostic information
- ``logging.INFO``: General informational messages (default)
- ``logging.WARNING``: Warning messages
- ``logging.ERROR``: Error messages only

De-identification Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.0.6
   De-identification configuration is now documented with comprehensive examples.

De-identification is configured through ``DeidentificationConfig`` dataclass:

.. code-block:: python

   from scripts.utils.deidentify import DeidentificationConfig
   
   config = DeidentificationConfig(
       # Pseudonym templates
       pseudonym_templates={
           PHIType.NAME_FULL: "PATIENT-{id}",
           PHIType.MRN: "MRN-{id}",
           # ... other templates
       },
       
       # Date shifting
       enable_date_shifting=True,
       date_shift_range_days=365,
       preserve_date_intervals=True,
       
       # Security
       enable_encryption=True,
       encryption_key=None,  # Auto-generated if None
       
       # Validation
       enable_validation=True,
       strict_mode=True,
       
       # Logging
       log_detections=True,
       log_level=logging.INFO,
       
       # Country-specific regulations
       countries=['IN', 'US'],  # None for default (IN)
       enable_country_patterns=True
   )

**Key Parameters**:

- **pseudonym_templates**: Custom format for pseudonyms (e.g., "PATIENT-{id}")
- **enable_date_shifting**: Shift dates by consistent offset
- **date_shift_range_days**: Maximum shift range (±365 days default)
- **preserve_date_intervals**: Keep time intervals consistent
- **enable_encryption**: Encrypt mapping files with Fernet
- **encryption_key**: Custom encryption key (auto-generated if None)
- **enable_validation**: Validate de-identified output
- **strict_mode**: Fail on validation errors
- **log_detections**: Log detected PHI/PII items
- **countries**: List of country codes for country-specific patterns
- **enable_country_patterns**: Use country-specific detection patterns

**Example Configurations**:

Basic de-identification (India-specific):

.. code-block:: python

   config = DeidentificationConfig()  # Uses defaults

Multi-country de-identification:

.. code-block:: python

   config = DeidentificationConfig(
       countries=['US', 'IN', 'BR', 'ID'],
       enable_encryption=True
   )

Testing/development (no encryption):

.. code-block:: python

   config = DeidentificationConfig(
       enable_encryption=False,
       log_level=logging.DEBUG
   )

See :doc:`deidentification` for complete de-identification guide.

Utility Functions (v0.0.3+)
---------------------------

.. versionadded:: 0.0.3

The configuration module now provides utility functions for common tasks.

ensure_directories()
~~~~~~~~~~~~~~~~~~~~

Automatically creates all required directories if they don't exist.

.. code-block:: python

   from config import ensure_directories
   
   # Create all necessary directories
   ensure_directories()

**What it creates**:
   - ``RESULTS_DIR``
   - ``CLEAN_DATASET_DIR``
   - ``DICTIONARY_JSON_OUTPUT_DIR``

**When to use**: 
   - At the start of your pipeline
   - Before writing any output files
   - When setting up a new environment

validate_config()
~~~~~~~~~~~~~~~~~

Validates the configuration and returns a list of warnings.

.. code-block:: python

   from config import validate_config
   
   warnings = validate_config()
   if warnings:
       print("Configuration warnings:")
       for warning in warnings:
           print(f"  - {warning}")
   else:
       print("Configuration is valid!")

**What it checks**:
   - ``DATA_DIR`` exists
   - ``DATASET_DIR`` exists
   - ``DICTIONARY_EXCEL_FILE`` exists

**Returns**: 
   - Empty list if all valid
   - List of warning strings if issues found

**When to use**: 
   - Before starting the pipeline
   - For debugging configuration issues
   - In automated testing

normalize_dataset_name()
~~~~~~~~~~~~~~~~~~~~~~~~

Normalize a dataset folder name by removing common suffixes.

.. code-block:: python

   from config import normalize_dataset_name
   
   name = normalize_dataset_name("Indo-vap_csv_files")
   print(name)  # Output: "Indo-vap"

**Parameters**:
   - ``folder_name`` (Optional[str]): Dataset folder name

**Returns**: 
   - Normalized name, or ``DEFAULT_DATASET_NAME`` if None

**Examples**:

.. code-block:: python

   normalize_dataset_name("study_csv_files")  # → "study"
   normalize_dataset_name("test_files")       # → "test"
   normalize_dataset_name(None)               # → "RePORTaLiN_sample"

Customizing Configuration
--------------------------

Example 1: Change Log Level
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To see more detailed debug information:

.. code-block:: python

   # config.py
   import logging
   
   LOG_LEVEL = logging.DEBUG  # More verbose logging

Example 2: Custom Data Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use a different data directory:

.. code-block:: python

   # config.py
   DATA_DIR = "/path/to/my/data"
   RESULTS_DIR = "/path/to/my/results"

Example 3: Different Dictionary File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your data dictionary has a different name:

.. code-block:: python

   # config.py
   DICTIONARY_EXCEL_FILE = os.path.join(
       DATA_DIR,
       "data_dictionary_and_mapping_specifications",
       "MyCustomDictionary.xlsx"
   )

Environment Variables
---------------------

You can also use environment variables for configuration:

.. code-block:: python

   # config.py
   import os
   
   # Use environment variable with fallback
   DATA_DIR = os.getenv("REPORTALIN_DATA_DIR", os.path.join(ROOT_DIR, "data"))

Then set the environment variable:

.. code-block:: bash

   export REPORTALIN_DATA_DIR="/my/custom/data/path"
   python main.py

Configuration Best Practices
-----------------------------

1. **Don't Hardcode Paths**
   
   ❌ Bad:
   
   .. code-block:: python
   
      file_path = "/Users/john/data/file.xlsx"
   
   ✅ Good:
   
   .. code-block:: python
   
      file_path = os.path.join(config.DATA_DIR, "file.xlsx")

2. **Use Path Objects**
   
   For more robust path handling:
   
   .. code-block:: python
   
      from pathlib import Path
      
      DATA_DIR = Path(ROOT_DIR) / "data"
      DATASET_DIR = DATA_DIR / "dataset" / dataset_name

3. **Keep Configuration Separate**
   
   Don't mix configuration with business logic:
   
   ❌ Bad: Hardcoding paths in processing functions
   
   ✅ Good: Import from config module

4. **Document Changes**
   
   If you modify ``config.py``, document why:
   
   .. code-block:: python
   
      # Changed to use external storage per project requirements
      DATA_DIR = "/mnt/shared/research_data"

Accessing Configuration
-----------------------

In Your Code
~~~~~~~~~~~~

.. code-block:: python

   import config
   
   # Access configuration variables
   print(f"Dataset: {config.DATASET_NAME}")
   print(f"Input dir: {config.DATASET_DIR}")
   print(f"Output dir: {config.CLEAN_DATASET_DIR}")

From Command Line
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Print current configuration
   python -c "import config; print(f'Dataset: {config.DATASET_NAME}')"

Directory Structure
-------------------

The configuration creates this structure:

.. code-block:: text

   RePORTaLiN/
   ├── data/
   │   ├── dataset/
   │   │   └── <dataset_name>/          # Auto-detected
   │   └── data_dictionary_and_mapping_specifications/
   │       └── RePORT_DEB_to_Tables_mapping.xlsx
   │
   └── results/
       ├── dataset/
       │   └── <dataset_name>/          # Mirrors input structure
       └── data_dictionary_mappings/
           ├── Codelists/
           ├── tblENROL/
           └── ...

Troubleshooting Configuration
------------------------------

Problem: "Dataset not found"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: No folder exists in ``data/dataset/``

**Solution**: Create a dataset folder:

.. code-block:: bash

   mkdir -p data/dataset/my_dataset
   # Add Excel files to this directory

Problem: "Permission denied"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Output directories not writable

**Solution**: Check permissions:

.. code-block:: bash

   chmod -R 755 results/
   chmod 755 .logs/

Problem: "Module not found: config"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Not running from project root

**Solution**: Ensure you're in the correct directory:

.. code-block:: bash

   cd /path/to/RePORTaLiN
   python main.py

See Also
--------

- :doc:`quickstart`: Quick start guide with validation examples
- :doc:`usage`: How to use configuration in practice
- :doc:`troubleshooting`: Configuration troubleshooting with ``validate_config()``
- :doc:`../api/config`: Complete API documentation for configuration module
- :doc:`../developer_guide/extending`: Extending configuration for custom needs
- :doc:`../changelog`: Version 0.0.3 configuration enhancements
