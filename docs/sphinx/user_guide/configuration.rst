Configuration
=============

RePORTaLiN uses a centralized configuration system through the ``config.py`` module. 
This guide explains all configuration options and how to customize them.

Configuration File
------------------

The main configuration file is ``config.py`` in the project root. It defines all paths, 
settings, and parameters used throughout the pipeline.

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

Configuration Variables
-----------------------

Project Root
~~~~~~~~~~~~

.. code-block:: python

   ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

- **Purpose**: Absolute path to project root directory
- **Usage**: All other paths are relative to this
- **Modification**: Not recommended (auto-detected)

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
   DATASET_DIR = get_dataset_folder()  # Auto-detected
   DATASET_NAME = extract_dataset_name(DATASET_DIR)

- **DATASET_BASE_DIR**: Parent directory for all datasets
- **DATASET_DIR**: Path to current dataset (auto-detected)
- **DATASET_NAME**: Name of current dataset (e.g., "Indo-vap")

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

- :doc:`usage`: How to use configuration in practice
- :mod:`config`: API documentation for configuration module
- :doc:`troubleshooting`: More troubleshooting tips
