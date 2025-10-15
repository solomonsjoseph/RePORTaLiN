Troubleshooting
===============

This guide provides solutions to common issues you might encounter with RePORTaLiN.

Installation Issues
-------------------

Module Import Errors
~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``ModuleNotFoundError: No module named 'pandas'`` or similar

**Solution 1**: Install dependencies

.. code-block:: bash

   pip install -r requirements.txt

**Solution 2**: Verify virtual environment

.. code-block:: bash

   # Check if virtual environment is activated
   which python
   
   # Should show path to .venv/bin/python
   # If not, activate:
   source .venv/bin/activate

**Solution 3**: Reinstall dependencies

.. code-block:: bash

   pip install --force-reinstall -r requirements.txt

Python Version Issues
~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``SyntaxError`` or version compatibility errors

**Solution**: Ensure Python 3.13+ is installed

.. code-block:: bash

   python --version
   # Should show Python 3.13.x or higher

If you have multiple Python versions:

.. code-block:: bash

   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

Permission Errors
~~~~~~~~~~~~~~~~~

**Problem**: ``Permission denied`` when installing packages

**Solution 1**: Use virtual environment (recommended)

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

**Solution 2**: Install for user only

.. code-block:: bash

   pip install --user -r requirements.txt

Data Processing Issues
----------------------

Debugging with Verbose Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Need to understand what the pipeline is doing or troubleshoot issues

**Solution**: Enable verbose (DEBUG) logging

.. code-block:: bash

   # Enable verbose logging
   python main.py -v
   
   # View log file in real-time
   tail -f .logs/reportalin_*.log
   
   # Filter for specific issues
   python main.py -v 2>&1 | grep -E "ERROR|WARNING|DEBUG.*Processing"

**What you'll see in verbose mode:**

1. **File Discovery**
   
   .. code-block:: text
   
      DEBUG - Excel files: ['10_TST.xlsx', '11_IGRA.xlsx', '12A_FUA.xlsx', ...]
      DEBUG - Processing 10_TST.xlsx

2. **Table Detection**
   
   .. code-block:: text
   
      DEBUG - Excel file loaded successfully. Found 17 sheets: ['Codelists', 'Notes', ...]
      DEBUG - Processing 3 tables from sheet 'Codelists'

3. **De-identification Details**
   
   .. code-block:: text
   
      DEBUG - Initialized DeidentificationEngine with config: countries=['IN'], encryption=True
      DEBUG - Files to process: ['1A_ICScreening.jsonl', '1B_HCScreening.jsonl', ...]
      DEBUG - Processed 1000 records from 1A_ICScreening.jsonl
      DEBUG - Detected 42 PHI/PII items: ['person_name', 'phone', 'email', ...]

No Excel Files Found
~~~~~~~~~~~~~~~~~~~~

**Problem**: ``Found 0 Excel files to process``

**Diagnosis**: Check if files exist

.. code-block:: bash

   ls -la data/dataset/*/
   # Should show .xlsx files

**Solution 1**: Verify directory structure

.. code-block:: text

   data/
   └── dataset/
       └── <dataset_name>/     # Must have a folder here
           ├── file1.xlsx
           └── file2.xlsx

**Solution 2**: Check file extensions

.. code-block:: bash

   # Excel files must have .xlsx extension (not .xls)
   # Convert .xls to .xlsx if needed
   
**Solution 3**: Verify configuration

.. code-block:: python

   python -c "import config; print(config.DATASET_DIR)"
   # Should print correct path

Empty Output Files
~~~~~~~~~~~~~~~~~~

**Problem**: JSONL files are created but contain no data

**Diagnosis**: Check if Excel sheets have data

.. code-block:: python

   import pandas as pd
   df = pd.read_excel('data/dataset/myfile.xlsx')
   print(df.shape)  # Should show (rows, columns)
   print(df.head())

**Solution**: RePORTaLiN automatically skips empty sheets. This is expected behavior. 
Check logs for details:

.. code-block:: bash

   cat .logs/reportalin_*.log | grep "empty"

Memory Errors
~~~~~~~~~~~~~

**Problem**: ``MemoryError`` when processing large files

**Solution 1**: Process files one at a time

.. code-block:: python

   from scripts.extract_data import process_excel_file
   
   # Process individually instead of batch
   for excel_file in excel_files:
       process_excel_file(excel_file, output_dir)

**Solution 2**: Increase available memory

.. code-block:: bash

   # Close other applications
   # Or run on a machine with more RAM

**Solution 3**: Process in chunks (for very large files)

.. code-block:: python

   import pandas as pd
   
   # Read in chunks
   for chunk in pd.read_excel('large_file.xlsx', chunksize=1000):
       # Process chunk
       pass

Date/Time Conversion Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Dates not converting correctly or appearing as numbers

**Explanation**: Excel stores dates as numbers (days since 1900-01-01). 
RePORTaLiN automatically handles this conversion.

**Solution**: If dates still appear incorrect:

.. code-block:: python

   import pandas as pd
   
   # Read with explicit date columns
   df = pd.read_excel(
       'file.xlsx',
       parse_dates=['date_column1', 'date_column2']
   )

Logging Issues
--------------

.. versionchanged:: 0.0.4
   Logging module enhanced for better reliability and performance.

No Log Files Created
~~~~~~~~~~~~~~~~~~~~

**Problem**: ``.logs/`` directory empty after running pipeline

**Solution 1**: Check permissions

.. code-block:: bash

   chmod 755 .logs/
   python main.py

**Solution 2**: Verify logging configuration

.. code-block:: python

   python -c "import config; print(config.LOG_LEVEL)"

**Solution 3**: Check for errors early in execution

.. code-block:: bash

   # Run with verbose output
   python main.py 2>&1 | tee output.log

**Technical Note** (v0.0.4): The logging system is thread-safe and optimized for performance.
If logs are missing, check for early import errors or permission issues.

Log Files Too Large
~~~~~~~~~~~~~~~~~~~

**Problem**: Log files consuming too much disk space

**Solution**: Implement log rotation

.. code-block:: python

   # In config.py or logging.py
   from logging.handlers import RotatingFileHandler
   
   handler = RotatingFileHandler(
       log_file,
       maxBytes=10*1024*1024,  # 10 MB
       backupCount=5
   )

Console Output Issues
~~~~~~~~~~~~~~~~~~~~~

**Problem**: Console shows too much or too little output

**Solution**: The console handler is filtered to show only SUCCESS, ERROR, and CRITICAL messages by default.

.. code-block:: python

   # To see all messages (including INFO and DEBUG), check the log files
   cat .logs/reportalin_*.log
   
   # Or modify the console filter in scripts/utils/logging.py

**Technical Note** (v0.0.4): Console output uses colored formatting for better readability.
If colors don't display correctly, check your terminal's ANSI support.

Configuration Issues
--------------------

Quick Configuration Check (v0.0.3+)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.0.3

**Use the built-in validation utility:**

.. code-block:: python

   from config import validate_config
   
   warnings = validate_config()
   if warnings:
       print("Configuration issues found:")
       for warning in warnings:
           print(f"  ⚠️  {warning}")
   else:
       print("✓ Configuration is valid!")

This automatically checks for:
  - Missing data directory
  - Missing dataset directory
  - Missing data dictionary file

Dataset Not Auto-Detected
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Pipeline doesn't detect dataset folder

**Diagnosis**: Check what's being detected

.. code-block:: python

   python -c "import config; print(config.DATASET_NAME)"

**Solution 1**: Use validation utility (v0.0.3+)

.. code-block:: python

   from config import validate_config, ensure_directories
   
   # Check for issues
   warnings = validate_config()
   for warning in warnings:
       print(warning)
   
   # Ensure directories exist
   ensure_directories()

**Solution 2**: Ensure folder exists in correct location

.. code-block:: bash

   mkdir -p data/dataset/my_dataset
   cp *.xlsx data/dataset/my_dataset/

**Solution 3**: Check for hidden folders

.. code-block:: bash

   ls -la data/dataset/
   # Should show folders (not starting with '.')

**Solution 4**: Manually specify in config.py

.. code-block:: python

   # config.py
   from config import DEFAULT_DATASET_NAME
   
   DATASET_NAME = "my_dataset"  # Or use DEFAULT_DATASET_NAME
   DATASET_DIR = os.path.join(DATA_DIR, "dataset", DATASET_NAME)

Wrong Output Directory
~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Results appear in unexpected location

**Solution**: Check configuration

.. code-block:: python

   python -c "import config; print(config.CLEAN_DATASET_DIR)"

The output should be: ``results/dataset/<dataset_name>/``

Path Issues
~~~~~~~~~~~

**Problem**: ``FileNotFoundError`` for data dictionary or other files

**Solution 1**: Verify you're in project root

.. code-block:: bash

   pwd
   # Should show /path/to/RePORTaLiN
   
   # If not:
   cd /path/to/RePORTaLiN
   python main.py

**Solution 2**: Check if files exist

.. code-block:: bash

   ls data/data_dictionary_and_mapping_specifications/*.xlsx

**Solution 3**: Update paths in config.py if files are elsewhere

Performance Issues
------------------

Slow Processing
~~~~~~~~~~~~~~~

**Problem**: Pipeline takes much longer than expected (~15-20 seconds)

**Diagnosis**: Check file count and sizes

.. code-block:: bash

   find data/dataset/ -name "*.xlsx" | wc -l
   du -sh data/dataset/

**Solution 1**: Verify no network drives

.. code-block:: bash

   # Process locally, not on network drives
   cp -r /network/drive/data ./data

**Solution 2**: Check system resources

.. code-block:: bash

   # macOS
   top
   
   # Linux
   htop

**Solution 3**: Disable antivirus temporarily

Antivirus software can slow file operations significantly.

Progress Bar Not Showing
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Progress bars don't display

**Solution 1**: Ensure tqdm is installed

.. code-block:: bash

   pip install tqdm

**Solution 2**: Check if running in proper terminal

Some IDEs don't support progress bars. Run in regular terminal:

.. code-block:: bash

   python main.py

Data Quality Issues
-------------------

Duplicate Column Names
~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Warning about duplicate columns in data dictionary

**Explanation**: This is handled automatically. RePORTaLiN renames duplicates 
to ``column_name_2``, ``column_name_3``, etc.

**No Action Needed**: This is expected behavior for some Excel files.

Missing Data/NaN Values
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``null`` values in JSONL output

**Explanation**: This is correct. Empty cells in Excel are converted to ``null`` 
in JSON format.

**If You Need Different Behavior**:

.. code-block:: python

   import pandas as pd
   
   # Read JSONL and fill nulls
   df = pd.read_json('output.jsonl', lines=True)
   df.fillna('', inplace=True)  # or other value
   
   # Save back
   df.to_json('output_cleaned.jsonl', orient='records', lines=True)

Incorrect Data Types
~~~~~~~~~~~~~~~~~~~~

**Problem**: Numbers stored as strings or vice versa

**Solution**: The pipeline automatically infers types. If you need specific types:

.. code-block:: python

   import pandas as pd
   
   df = pd.read_json('output.jsonl', lines=True)
   
   # Convert specific columns
   df['age'] = df['age'].astype(int)
   df['date'] = pd.to_datetime(df['date'])

Advanced Troubleshooting
------------------------

Enable Debug Logging
~~~~~~~~~~~~~~~~~~~~

For detailed diagnostic information:

.. code-block:: python

   # config.py
   import logging
   LOG_LEVEL = logging.DEBUG

Then run:

.. code-block:: bash

   python main.py 2>&1 | tee debug.log

Inspect Intermediate Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check what's happening at each stage:

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   from scripts.extract_data import process_excel_file
   import config
   
   # Test dictionary loading
   load_study_dictionary(
       config.DICTIONARY_EXCEL_FILE,
       config.DICTIONARY_JSON_OUTPUT_DIR
   )
   
   # Check output
   import os
   print(os.listdir(config.DICTIONARY_JSON_OUTPUT_DIR))

Test Single File
~~~~~~~~~~~~~~~~

Process one file in isolation:

.. code-block:: python

   from scripts.extract_data import process_excel_file
   from pathlib import Path
   
   test_file = Path("data/dataset/Indo-vap/10_TST.xlsx")
   output_dir = Path("test_output")
   output_dir.mkdir(exist_ok=True)
   
   result = process_excel_file(str(test_file), str(output_dir))
   print(result)

Verify Dependencies
~~~~~~~~~~~~~~~~~~~

Ensure all dependencies are correctly installed:

.. code-block:: bash

   pip list | grep -E 'pandas|openpyxl|numpy|tqdm'

Should show:

.. code-block:: text

   numpy      2.x.x
   openpyxl   3.x.x
   pandas     2.x.x
   tqdm       4.x.x

Getting Help
------------

If you're still experiencing issues:

1. **Check the logs**:

   .. code-block:: bash

      cat .logs/reportalin_*.log

2. **Search existing issues**: Check the GitHub repository

3. **Create a minimal reproducible example**

4. **Include diagnostic information**:

   .. code-block:: bash

      python --version
      pip list
      python -c "import config; print(config.DATASET_DIR)"

Common Error Messages
---------------------

``TypeError: Object of type 'Timestamp' is not JSON serializable``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: Date conversion issue

**Solution**: Already handled in the pipeline. If you see this, update to latest version.

``UnicodeDecodeError``
~~~~~~~~~~~~~~~~~~~~~~

**Cause**: File encoding issue

**Solution**: Ensure Excel files are saved in standard format (Excel 2007+ .xlsx)

``PermissionError: [Errno 13] Permission denied``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause**: File in use or insufficient permissions

**Solution**:

.. code-block:: bash

   # Close Excel files
   # Check permissions
   chmod -R 755 data/ results/

See Also
--------

- :doc:`configuration`: Configuration options
- :doc:`usage`: Usage examples
- :doc:`../developer_guide/architecture`: System architecture
- GitHub Issues: Report new problems
