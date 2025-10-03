Usage Guide
===========

This guide covers advanced usage patterns and common workflows for RePORTaLiN.

Basic Usage
-----------

Run Complete Pipeline
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py

This executes both pipeline steps:
1. Data dictionary loading
2. Data extraction

Skip Specific Steps
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Skip dictionary loading (useful if already processed)
   python main.py --skip-dictionary

   # Skip data extraction
   python main.py --skip-extraction

   # Run neither (useful for testing configuration)
   python main.py --skip-dictionary --skip-extraction

Working with Multiple Datasets
-------------------------------

RePORTaLiN can process different datasets by simply changing the data directory:

Scenario 1: Sequential Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Process multiple datasets one at a time:

.. code-block:: bash

   # Process first dataset
   # Ensure data/dataset/ contains only Indo-vap_csv_files
   python main.py

   # Move results to backup
   mv results/dataset/Indo-vap results/dataset/Indo-vap_backup

   # Process second dataset
   # Replace data/dataset/ contents with new dataset
   python main.py

Scenario 2: Parallel Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use separate project directories for parallel processing:

.. code-block:: bash

   # Terminal 1
   cd /path/to/RePORTaLiN_project1
   python main.py

   # Terminal 2
   cd /path/to/RePORTaLiN_project2
   python main.py

Using as a Python Module
-------------------------

Import and Use Functions
~~~~~~~~~~~~~~~~~~~~~~~~~

You can use RePORTaLiN functions in your own Python scripts:

.. code-block:: python

   from scripts.extract_data import extract_excel_to_jsonl
   from scripts.load_dictionary import load_study_dictionary
   import config

   # Load data dictionary
   load_study_dictionary(
       excel_file=config.DICTIONARY_EXCEL_FILE,
       output_dir=config.DICTIONARY_JSON_OUTPUT_DIR
   )

   # Extract specific files
   extract_excel_to_jsonl(
       input_dir=config.DATASET_DIR,
       output_dir=config.CLEAN_DATASET_DIR
   )

Process Single File
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import process_excel_file
   import config

   # Process one specific Excel file
   input_file = config.DATASET_DIR / "10_TST.xlsx"
   output_dir = config.CLEAN_DATASET_DIR

   result = process_excel_file(input_file, output_dir)
   print(f"Processed {result['records']} records")

Custom Processing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import convert_dataframe_to_jsonl

   # Custom data processing
   df = pd.read_excel("my_data.xlsx")
   
   # Filter or transform data
   df = df[df['age'] > 18]
   
   # Convert to JSONL
   convert_dataframe_to_jsonl(
       df=df,
       output_file="filtered_data.jsonl",
       source_file="my_data.xlsx"
   )

Batch Processing
----------------

Process Multiple Dictionary Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   from pathlib import Path

   dictionary_dir = Path("data/dictionaries")
   output_base = Path("results/dictionaries")

   for dict_file in dictionary_dir.glob("*.xlsx"):
       output_dir = output_base / dict_file.stem
       output_dir.mkdir(parents=True, exist_ok=True)
       
       load_study_dictionary(
           excel_file=str(dict_file),
           output_dir=str(output_dir)
       )
       print(f"Processed {dict_file.name}")

Process Files Matching Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import find_excel_files, process_excel_file
   from pathlib import Path

   input_dir = Path("data/dataset/Indo-vap")
   output_dir = Path("results/partial")

   # Process only files matching pattern
   for excel_file in input_dir.glob("1*_*.xlsx"):  # Files starting with "1"
       process_excel_file(str(excel_file), str(output_dir))
       print(f"Processed {excel_file.name}")

Working with Output Files
--------------------------

Understanding Original vs Cleaned Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each extraction creates two versions of every file:

- **Original** (``<filename>.jsonl``): All columns from Excel, including duplicates
- **Cleaned** (``clean_<filename>.jsonl``): Duplicate columns removed (e.g., SUBJID2, SUBJID3)

.. code-block:: text

   results/dataset/Indo-vap/
   ├── 10_TST.jsonl              # Original: has SUBJID, SUBJID2, SUBJID3
   ├── clean_10_TST.jsonl        # Cleaned: only SUBJID (duplicates removed)
   ├── 11_IGRA.jsonl             # Original
   ├── clean_11_IGRA.jsonl       # Cleaned
   └── ...

**When to use each version:**

- **Original files**: Use for data validation, debugging, or when you need all source columns
- **Cleaned files**: Use for analysis, reporting, or database loading (recommended for most use cases)

Reading Cleaned Files:

.. code-block:: python

   import pandas as pd

   # Read cleaned version (recommended)
   df = pd.read_json('results/dataset/Indo-vap/clean_10_TST.jsonl', lines=True)
   
   # Verify no duplicate columns
   print("Columns:", df.columns.tolist())
   # Output: ['SUBJID', 'TST_RESULT', ...] (no SUBJID2, SUBJID3)

Comparing Original vs Cleaned:

.. code-block:: python

   import pandas as pd

   # Load both versions
   df_original = pd.read_json('results/dataset/Indo-vap/10_TST.jsonl', lines=True)
   df_cleaned = pd.read_json('results/dataset/Indo-vap/clean_10_TST.jsonl', lines=True)
   
   # Compare columns
   print(f"Original columns: {len(df_original.columns)}")
   print(f"Cleaned columns: {len(df_cleaned.columns)}")
   
   # Find removed columns
   removed = set(df_original.columns) - set(df_cleaned.columns)
   print(f"Removed duplicate columns: {removed}")

Reading JSONL Files
~~~~~~~~~~~~~~~~~~~

Using Pandas:

.. code-block:: python

   import pandas as pd

   # Read JSONL file
   df = pd.read_json('results/dataset/Indo-vap/10_TST.jsonl', lines=True)
   
   # View summary
   print(df.shape)
   print(df.columns)
   print(df.head())

Using Standard Library:

.. code-block:: python

   import json

   records = []
   with open('results/dataset/Indo-vap/10_TST.jsonl', 'r') as f:
       for line in f:
           records.append(json.loads(line))
   
   print(f"Loaded {len(records)} records")

Combining Multiple JSONL Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from pathlib import Path

   # Combine all JSONL files
   dfs = []
   results_dir = Path("results/dataset/Indo-vap")
   
   for jsonl_file in results_dir.glob("*.jsonl"):
       df = pd.read_json(jsonl_file, lines=True)
       df['source_file'] = jsonl_file.stem
       dfs.append(df)
   
   combined_df = pd.concat(dfs, ignore_index=True)
   print(f"Combined {len(dfs)} files: {len(combined_df)} total records")

Converting to Other Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd

   # Read JSONL
   df = pd.read_json('results/dataset/Indo-vap/10_TST.jsonl', lines=True)

   # Convert to CSV
   df.to_csv('output.csv', index=False)

   # Convert to Excel
   df.to_excel('output.xlsx', index=False)

   # Convert to Parquet
   df.to_parquet('output.parquet')

Logging and Monitoring
-----------------------

View Real-Time Logs
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # In one terminal, run the pipeline
   python main.py

   # In another terminal, watch the log
   tail -f .logs/reportalin_*.log

Parse Log Files
~~~~~~~~~~~~~~~

.. code-block:: python

   import re
   from pathlib import Path

   # Find latest log
   log_dir = Path(".logs")
   latest_log = max(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime)

   # Extract error messages
   with open(latest_log, 'r') as f:
       for line in f:
           if 'ERROR' in line or 'WARNING' in line:
               print(line.strip())

Custom Logging
~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils import logging_utils as log

   # Use the custom logger
   log.info("Processing started")
   log.success("Operation completed successfully")
   log.warning("Potential issue detected")
   log.error("An error occurred")

Performance Optimization
------------------------

Process Large Files
~~~~~~~~~~~~~~~~~~~

For very large Excel files, consider processing in chunks:

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import convert_dataframe_to_jsonl

   # Read in chunks
   chunk_size = 10000
   chunks = pd.read_excel(
       'large_file.xlsx',
       chunksize=chunk_size
   )

   # Process each chunk
   for i, chunk in enumerate(chunks):
       output_file = f'output_chunk_{i}.jsonl'
       convert_dataframe_to_jsonl(chunk, output_file, 'large_file.xlsx')

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Process multiple files in parallel:

.. code-block:: python

   from concurrent.futures import ThreadPoolExecutor
   from scripts.extract_data import process_excel_file
   from pathlib import Path

   def process_file(file_path):
       process_excel_file(file_path, output_dir)
       return file_path.name

   input_dir = Path("data/dataset/Indo-vap")
   output_dir = Path("results/dataset/Indo-vap")
   excel_files = list(input_dir.glob("*.xlsx"))

   # Process 4 files at a time
   with ThreadPoolExecutor(max_workers=4) as executor:
       results = list(executor.map(process_file, excel_files))

   print(f"Processed {len(results)} files")

Error Handling
--------------

Graceful Error Handling
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.extract_data import process_excel_file
   from scripts.utils import logging_utils as log

   excel_files = find_excel_files(input_dir)
   failed_files = []

   for excel_file in excel_files:
       try:
           process_excel_file(excel_file, output_dir)
           log.success(f"Processed {excel_file}")
       except Exception as e:
           log.error(f"Failed to process {excel_file}: {e}")
           failed_files.append((excel_file, str(e)))

   if failed_files:
       print(f"\nFailed files ({len(failed_files)}):")
       for file, error in failed_files:
           print(f"  - {file}: {error}")

Integration with Other Tools
-----------------------------

Use with Jupyter Notebooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # In Jupyter Notebook
   import sys
   sys.path.append('/path/to/RePORTaLiN')

   from scripts.extract_data import extract_excel_to_jsonl
   import config

   # Run extraction
   extract_excel_to_jsonl(config.DATASET_DIR, config.CLEAN_DATASET_DIR)

Use with Data Analysis Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   import matplotlib.pyplot as plt

   # Load extracted data
   df = pd.read_json('results/dataset/Indo-vap/10_TST.jsonl', lines=True)

   # Analyze
   df['date'].value_counts().plot(kind='bar')
   plt.title('Records by Date')
   plt.show()

Automation
----------

Scheduled Execution
~~~~~~~~~~~~~~~~~~~

Using cron (Linux/macOS):

.. code-block:: bash

   # Edit crontab
   crontab -e

   # Add line to run daily at 2 AM
   0 2 * * * cd /path/to/RePORTaLiN && /path/to/venv/bin/python main.py

Using Task Scheduler (Windows):

.. code-block:: batch

   # Create a batch file run_pipeline.bat
   cd C:\path\to\RePORTaLiN
   .venv\Scripts\python.exe main.py

Then schedule it using Windows Task Scheduler.

Script Wrapper
~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # run_pipeline.sh
   
   cd /path/to/RePORTaLiN
   source .venv/bin/activate
   
   # Run pipeline
   python main.py
   
   # Archive results
   timestamp=$(date +%Y%m%d_%H%M%S)
   tar -czf "backup_${timestamp}.tar.gz" results/
   
   # Send notification
   echo "Pipeline completed at $(date)" | mail -s "RePORTaLiN Complete" user@example.com

See Also
--------

- :doc:`configuration`: Configuration options
- :doc:`troubleshooting`: Problem solving
- :doc:`../api/modules`: API reference
- :doc:`../developer_guide/extending`: Extending the pipeline
