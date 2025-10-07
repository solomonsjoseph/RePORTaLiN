Quick Start
===========

This guide will walk you through your first data extraction with RePORTaLiN in just a few minutes.

Running Your First Extraction
------------------------------

The simplest way to run the pipeline:

.. code-block:: bash

   python main.py

That's it! This single command will:

1. ✅ Load and process the data dictionary (14 sheets)
2. ✅ Extract data from all Excel files in your dataset
3. ✅ Generate JSONL output files in ``results/dataset/<dataset_name>/``
4. ✅ Create timestamped logs in ``.logs/``

Expected Output
---------------

You should see output similar to:

.. code-block:: text

   Processing sheets: 100%|██████████| 14/14 [00:00<00:00, 122.71sheet/s]
   SUCCESS: Excel processing complete!
   SUCCESS: Step 0: Loading Data Dictionary completed successfully.
   Found 43 Excel files to process...
   Processing files: 100%|██████████| 43/43 [00:15<00:00, 2.87file/s]
   SUCCESS: Step 1: Extracting Raw Data to JSONL completed successfully.
   RePORTaLiN pipeline finished.

Understanding the Output
------------------------

After the pipeline completes, you'll find:

1. **Extracted Data** in ``results/dataset/<dataset_name>/``

   .. code-block:: text

      results/dataset/Indo-vap/
      ├── original/                 (All columns preserved)
      │   ├── 10_TST.jsonl          (631 records)
      │   ├── 11_IGRA.jsonl         (262 records)
      │   ├── 12A_FUA.jsonl         (2,831 records)
      │   └── ...                   (43 files total)
      └── cleaned/                  (Duplicate columns removed)
          ├── 10_TST.jsonl          (631 records)
          ├── 11_IGRA.jsonl         (262 records)
          ├── 12A_FUA.jsonl         (2,831 records)
          └── ...                   (43 files total)

   **Note:** Each extraction creates two versions in separate subdirectories:
   
   - **original/** - All columns preserved as-is from Excel files
   - **cleaned/** - Duplicate columns removed (e.g., SUBJID2, SUBJID3)

2. **Data Dictionary Mappings** in ``results/data_dictionary_mappings/``

   .. code-block:: text

      results/data_dictionary_mappings/
      ├── Codelists/
      │   ├── Codelists_table_1.jsonl
      │   └── Codelists_table_2.jsonl
      ├── tblENROL/
      │   └── tblENROL_table.jsonl
      └── ...                       (14 sheets)

3. **De-identified Data** (if ``--enable-deidentification`` is used) in ``results/deidentified/<dataset_name>/``

   .. code-block:: text

      results/deidentified/Indo-vap/
      ├── original/                 (De-identified original files)
      │   ├── 10_TST.jsonl
      │   └── ...
      ├── cleaned/                  (De-identified cleaned files)
      │   ├── 10_TST.jsonl
      │   └── ...
      └── _deidentification_audit.json

4. **Execution Logs** in ``.logs/``

   .. code-block:: text

      .logs/
      └── reportalin_20251002_132124.log

Viewing the Results
-------------------

JSONL files can be viewed in several ways:

**Using a text editor:**

.. code-block:: bash

   # View first few lines
   head results/dataset/Indo-vap/original/10_TST.jsonl

**Using Python:**

.. code-block:: python

   import pandas as pd
   
   # Read JSONL file
   df = pd.read_json('results/dataset/Indo-vap/original/10_TST.jsonl', lines=True)
   print(df.head())

**Using jq (command-line JSON processor):**

.. code-block:: bash

   # Pretty-print first record
   head -n 1 results/dataset/Indo-vap/original/10_TST.jsonl | jq

Command-Line Options
--------------------

Skip Specific Steps
~~~~~~~~~~~~~~~~~~~

You can skip individual pipeline steps:

.. code-block:: bash

   # Skip data dictionary loading
   python main.py --skip-dictionary

   # Skip data extraction
   python main.py --skip-extraction

   # Skip both (useful for testing)
   python main.py --skip-dictionary --skip-extraction

View Help
~~~~~~~~~

.. code-block:: bash

   python main.py --help

Using Make Commands
-------------------

For convenience, you can use Make commands:

.. code-block:: bash

   # Run the pipeline
   make run

   # Clean cache files
   make clean

   # Run tests (if available)
   make test

Working with Different Datasets
--------------------------------

RePORTaLiN automatically detects your dataset:

1. Place your Excel files in ``data/dataset/<your_dataset_name>/``
2. Run ``python main.py``
3. Results appear in ``results/dataset/<your_dataset_name>/``

Example:

.. code-block:: text

   # Your data structure
   data/dataset/
   └── my_research_data/
       ├── file1.xlsx
       ├── file2.xlsx
       └── ...

   # Automatically creates
   results/dataset/
   └── my_research_data/
       ├── file1.jsonl
       ├── file2.jsonl
       └── ...

Checking the Logs
-----------------

Logs provide detailed information about the extraction process:

.. code-block:: bash

   # View the latest log
   ls -lt .logs/ | head -n 2
   cat .logs/reportalin_20251002_132124.log

Logs include:

- Timestamp for each operation
- Files processed and record counts
- Warnings and errors (if any)
- Success confirmations

Common First-Run Issues
-----------------------

**Issue**: "No Excel files found"

**Solution**: Ensure your Excel files are in ``data/dataset/<folder_name>/``

.. code-block:: bash

   ls data/dataset/*/

---

**Issue**: "Permission denied" when creating logs

**Solution**: Ensure the ``.logs`` directory is writable:

.. code-block:: bash

   chmod 755 .logs/

---

**Issue**: "Module not found"

**Solution**: Ensure dependencies are installed:

.. code-block:: bash

   pip install -r requirements.txt

Next Steps
----------

Now that you've run your first extraction:

- :doc:`configuration`: Learn how to customize the pipeline
- :doc:`usage`: Explore advanced usage patterns
- :doc:`troubleshooting`: Solutions to common problems
- :doc:`../api/modules`: Dive into the API documentation
