Quick Start
===========

**For Users: Simplified Execution Guide**

This guide provides clear, step-by-step instructions to get you started with RePORTaLiN
in just a few minutes. No technical expertise required!

What Does RePORTaLiN Do?
-------------------------

RePORTaLiN is a tool that:

1. 📊 **Converts** Excel files to a simpler JSON format (JSONL)
2. 🔍 **Organizes** data dictionary information into structured tables
3. 🔒 **Protects** sensitive patient information (optional de-identification)
4. ✅ **Validates** data integrity and generates detailed logs

Think of it as an automated data processing assistant that handles tedious file conversions safely and efficiently.

Prerequisites
-------------

Before you begin, ensure you have:

✅ **Python 3.13 or higher** installed  
   Check version: ``python3 --version``

✅ **Project files** downloaded or cloned to your computer

✅ **Excel data files** in the ``data/dataset/`` folder

✅ **5-10 minutes** of time for initial setup

Verify Configuration (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before running the pipeline, validate your setup:

.. code-block:: python

   from config import validate_config
   
   warnings = validate_config()
   if warnings:
       for warning in warnings:
           print(warning)
   else:
       print("Configuration is valid")

See :doc:`configuration` for details.

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

**Issue**: "Package not found"

**Solution**: Ensure dependencies are installed:

.. code-block:: bash

   pip install -r requirements.txt

Step-by-Step Execution
-----------------------

**Step 1: Install Dependencies** (One-time setup)

Open your terminal/command prompt and navigate to the RePORTaLiN project folder:

.. code-block:: bash

   cd /path/to/RePORTaLiN
   
Install required Python packages:

.. code-block:: bash

   pip install -r requirements.txt

You should see packages being installed (pandas, openpyxl, tqdm, etc.). This takes 1-2 minutes.

✅ **Expected Output:** "Successfully installed pandas-2.0.0 openpyxl-3.1.0..." (versions may vary)

---

**Step 2: Verify Your Data Files**

Check that your Excel files are in the right location:

.. code-block:: bash

   ls data/dataset/

✅ **Expected Output:** You should see a folder (e.g., ``Indo-vap_csv_files/``) containing .xlsx files

If you don't see any folders, create one and place your Excel files there:

.. code-block:: bash

   mkdir -p data/dataset/my_dataset/
   cp /path/to/your/excel/files/*.xlsx data/dataset/my_dataset/

---

**Step 3: Run the Basic Pipeline**

Execute the main pipeline with this simple command:

.. code-block:: bash

   python3 main.py

✅ **Expected Output:** You'll see two progress bars:

.. code-block:: text

   Processing sheets: 100%|██████████| 14/14 [00:01<00:00, 12.71sheet/s]
   SUCCESS: Step 0: Loading Data Dictionary completed successfully.
   
   Found 43 Excel files to process...
   Processing files: 100%|██████████| 43/43 [00:15<00:00, 2.87file/s]
   SUCCESS: Step 1: Extracting Raw Data to JSONL completed successfully.
   
   RePORTaLiN pipeline finished.

⏱️ **Time:** Usually 15-30 seconds depending on file size

---

**Step 4: Check Your Results**

Navigate to the results folder:

.. code-block:: bash

   cd results/dataset/
   ls

✅ **Expected Output:** You'll see a folder with your dataset name (e.g., ``Indo-vap/``)

Look inside:

.. code-block:: bash

   ls results/dataset/Indo-vap/

✅ **Expected Output:**

.. code-block:: text

   original/    (Contains .jsonl files with all original columns)
   cleaned/     (Contains .jsonl files with duplicate columns removed)

Each folder contains the same files but with different processing levels:
- **original/** = Exact Excel data, just converted to JSONL
- **cleaned/** = Duplicate columns (like SUBJID2, SUBJID3) removed for cleaner data

---

**Step 5: View Your Converted Data** (Optional)

Open any .jsonl file to see the converted data:

.. code-block:: bash

   head -n 5 results/dataset/Indo-vap/original/10_TST.jsonl

✅ **Expected Output:** You'll see JSON-formatted data, one record per line:

.. code-block:: text

   {"SUBJID": "INV001", "VISIT": 1, "TST_RESULT": "Positive", "source_file": "10_TST.xlsx"}
   {"SUBJID": "INV002", "VISIT": 1, "TST_RESULT": "Negative", "source_file": "10_TST.xlsx"}
   ...

🎉 **Congratulations!** Your data has been successfully converted!

Advanced Usage: De-identification
----------------------------------

If you need to remove sensitive patient information (PHI/PII), use the de-identification feature:

**Step 1: Run with De-identification Enabled**

.. code-block:: bash

   python3 main.py --enable-deidentification

✅ **Expected Output:** Additional processing step for de-identification:

.. code-block:: text

   De-identifying dataset: results/dataset/Indo-vap -> results/deidentified/Indo-vap
   Processing both 'original' and 'cleaned' subdirectories...
   Countries: IN (default)
   De-identifying files: 100%|██████████| 43/43 [00:25<00:00, 1.72file/s]
   
   De-identification complete:
     Texts processed: 15,234
     Total detections: 1,250
     Countries: IN (default)
     Unique mappings: 485

⏱️ **Time:** Additional 20-40 seconds for de-identification

---

**Step 2: Specify Countries** (For multi-country studies)

.. code-block:: bash

   python3 main.py --enable-deidentification --countries IN US ID BR

This applies privacy regulations for India, United States, Indonesia, and Brazil.

✅ **Supported Countries:** US, IN, ID, BR, PH, ZA, EU, GB, CA, AU, KE, NG, GH, UG

---

**Step 3: View De-identified Results**

.. code-block:: bash

   head -n 3 results/deidentified/Indo-vap/original/10_TST.jsonl

✅ **Expected Output:** Sensitive data replaced with placeholders:

.. code-block:: text

   {"SUBJID": "[MRN-X7Y2A9]", "PATIENT_NAME": "[PATIENT-A4B8C3]", "DOB": "[DATE-1]", ...}
   {"SUBJID": "[MRN-K2M5P1]", "PATIENT_NAME": "[PATIENT-D9F2G7]", "DOB": "[DATE-2]", ...}

**Note:** Original → Pseudonym mappings are encrypted and stored securely in:
``results/deidentified/mappings/mappings.enc``

Troubleshooting
---------------

**Problem:** "No Excel files found"

**Solution:** Check that your Excel files (.xlsx) are in ``data/dataset/<folder_name>/``

.. code-block:: bash

   ls data/dataset/*/

---

**Problem:** "Package 'pandas' not found"

**Solution:** Install dependencies:

.. code-block:: bash

   pip install -r requirements.txt

---

**Problem:** "Permission denied" when accessing files

**Solution:** Run with appropriate permissions:

.. code-block:: bash

   # On macOS/Linux
   chmod +x main.py
   python3 main.py
   
   # On Windows (run as Administrator)
   python main.py

---

**Problem:** Files are being skipped

**Solution:** This is normal! The pipeline skips files that were already processed successfully.
To reprocess, delete the output folder:

.. code-block:: bash

   rm -rf results/dataset/my_dataset/
   python3 main.py

---

**Problem:** "Validation found potential PHI" warning after de-identification

**Solution:** This is a cautious warning. Review the log file for details:

.. code-block:: bash

   cat .logs/reportalin_*.log | grep "potential PHI"

If it's a false positive (like "[MRN-ABC123]" being detected), you can safely proceed.

Common Use Cases
----------------

**Use Case 1: Process only data dictionary, skip extraction**

.. code-block:: bash

   python3 main.py --skip-extraction

---

**Use Case 2: Process only data extraction, skip dictionary**

.. code-block:: bash

   python3 main.py --skip-dictionary

---

**Use Case 3: Reprocess everything from scratch**

.. code-block:: bash

   rm -rf results/
   python3 main.py

---

**Use Case 4: De-identify for multiple countries without encryption** (testing only)

.. code-block:: bash

   python3 main.py --enable-deidentification --countries ALL --no-encryption

**⚠️ Warning:** ``--no-encryption`` should only be used for testing! Always use encryption in production.

---

Next Steps
----------

✅ **You're done!** Your data has been successfully processed.

**What's next?**

1. 📊 **Analyze your data:** Use the .jsonl files with pandas, jq, or any JSON tool
2. 📖 **Read the full documentation:** Learn about advanced configuration options
3. 🔒 **Review de-identification:** Check the audit log at ``results/deidentified/_deidentification_audit.json``
4. 📝 **Check logs:** Detailed operation logs are in ``.logs/reportalin_<timestamp>.log``

**Need help?** See the :doc:`troubleshooting` guide or review the logs for detailed error messages.
