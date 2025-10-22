main module
===========

.. automodule:: main
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``main`` module serves as the central entry point for the RePORTaLiN pipeline. 
It orchestrates the execution of data processing steps and provides command-line 
interface functionality.

**Enhanced in v0.0.12:**

- ✅ Added ``-v`` / ``--verbose`` flag for DEBUG-level logging
- ✅ Enhanced logging throughout pipeline for detailed troubleshooting
- ✅ Version updated to 0.0.12

**Enhanced in v0.0.11:**

- ✅ Enhanced module docstring with comprehensive usage examples (162 lines, 2,214% increase)
- ✅ Added explicit public API definition via ``__all__`` (2 exports)
- ✅ Complete command-line arguments documentation
- ✅ Pipeline steps explanation with detailed features
- ✅ Four usage examples (basic, custom, de-identification, advanced)
- ✅ Output structure with directory tree
- ✅ Error handling and return codes documented

Public API
~~~~~~~~~~

The module exports 2 functions via ``__all__``:

1. **main** - Main pipeline orchestrator with command-line interface
2. **run_step** - Pipeline step executor with error handling

**Quick Start:**

.. code-block:: bash

   # Run complete pipeline
   python3 main.py
   
   # With de-identification
   python3 main.py --enable-deidentification --countries IN US
   
   # Custom execution
   python3 main.py --skip-dictionary --enable-deidentification

Functions
---------

run_step
~~~~~~~~

.. autofunction:: main.run_step
   :no-index:

Execute a pipeline step with comprehensive error handling and logging.

**Example**:

.. code-block:: python

   from main import run_step
   
   def my_processing_step():
       print("Processing...")
       return True
   
   result = run_step("My Step", my_processing_step)

main
~~~~

.. autofunction:: main.main
   :no-index:

Main entry point for the pipeline.

**Command-line usage**:

.. code-block:: bash

   # Run full pipeline
   python main.py
   
   # Skip dictionary loading
   python main.py --skip-dictionary
   
   # Skip data extraction
   python main.py --skip-extraction
   
   # Enable de-identification with encryption (default)
   python main.py --enable-deidentification
   
   # Enable de-identification without encryption (testing only)
   python main.py --enable-deidentification --no-encryption
   
   # Skip de-identification step
   python main.py --skip-deidentification
   
   # Specify country codes for de-identification
   python main.py --enable-deidentification -c IN US BR
   python main.py --enable-deidentification --countries ALL
   
   # Show version
   python main.py --version

**Programmatic usage**:

.. code-block:: python

   # Import and run
   import main
   main.main()

Pipeline Steps
--------------

The main function executes these steps in order:

1. **Step 0**: Load Data Dictionary
   
   Processes the Excel-based data dictionary using :func:`scripts.load_dictionary.load_study_dictionary`.
   Can be skipped with ``--skip-dictionary``.

2. **Step 1**: Extract Raw Data
   
   Extracts data from Excel files using :func:`scripts.extract_data.extract_excel_to_jsonl`.
   Can be skipped with ``--skip-extraction``.

3. **Step 2**: De-identify Data (Optional)
   
   De-identifies PHI/PII from extracted data using :func:`scripts.deidentify.deidentify_dataset`.
   Must be explicitly enabled with ``--enable-deidentification``.
   
   - Encryption enabled by default for security
   - Can disable encryption with ``--no-encryption`` (testing only)
   - Can specify country codes with ``-c`` or ``--countries``
   - Can be skipped with ``--skip-deidentification``

Error Handling
--------------

All steps are wrapped with error handling:

- Exceptions are caught and logged
- Detailed error messages with traceback
- Program exits with code 1 on error
- Ensures clean shutdown

Logging
-------

The module uses centralized logging:

- Step execution logged at INFO level
- Success logged at SUCCESS level (custom)
- Errors logged at ERROR level with traceback
- All logs written to timestamped file

See Also
--------

:mod:`config`
   Configuration management

:mod:`scripts.extract_data`
   Data extraction functionality

:mod:`scripts.load_dictionary`
   Dictionary loading functionality

:mod:`scripts.deidentify`
   De-identification utilities

:mod:`scripts.utils.logging`
   Logging utilities
