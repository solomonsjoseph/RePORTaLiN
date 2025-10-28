Usage Guide
===========

**For Users: Working with RePORTaLiN**

This guide shows you different ways to use RePORTaLiN for your daily tasks.

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

Detailed Logging Mode
~~~~~~~~~~~~~~~~~~~~~

Want to see exactly what's happening during processing? Use verbose mode to get detailed tree-view logs for each step:

.. code-block:: bash

   # Enable detailed logging
   python main.py --verbose
   
   # Short form
   python main.py -v
   
   # With privacy protection enabled
   python main.py -v --enable-deidentification --countries IN US

**Verbose Mode Output**: When running with ``--verbose``, you get detailed step-by-step logs in the format:

::

    DEBUG: ├─ Processing: Data dictionary loading (N sheets)
    DEBUG:   ├─ Total sheets: N
    DEBUG:   ├─ Sheet 1/N: 'sheet_name'
    DEBUG:   │  ├─ Tables detected: 2
    DEBUG:   │  ├─ Table 1 (sheet_table_1)
    DEBUG:   │  │  ├─ Rows: 100
    DEBUG:   │  │  ├─ Columns: 25
    DEBUG:   │  │  ├─ Saved to: /path/to/output.jsonl
    DEBUG:   │  │  └─ ⏱ Table processing time: 0.23s
    DEBUG:   └─ ⏱ Overall processing time: 2.45s

**What you'll see in the log file:**

- **File-level details**: Which files are being processed and their locations
- **Sheet/Table details**: How many sheets/tables found, rows/columns per table
- **Processing phases**: Load, save, clean, validate operations
- **Metrics**: Counts, totals, and statistics for each operation
- **Timing information**: Duration for each step and overall processing time
- **Error context**: Detailed error messages with processing state
- **Progress updates**: Real-time updates for large datasets

**Where to find logs:** Look in the ``.logs/`` folder for files named ``reportalin_YYYYMMDD_HHMMSS.log``

**Impact on speed:** Minimal - your processing will be just as fast

**Log File Structure**: The log file captures all verbose output with timestamps:

.. code-block:: text

    2024-10-23 14:30:45,123 - reportalin - DEBUG - ├─ Processing: Data dictionary loading (43 sheets)
    2024-10-23 14:30:45,125 - reportalin - DEBUG -   ├─ Total sheets: 43
    2024-10-23 14:30:45,200 - reportalin - DEBUG -   ├─ Sheet 1/43: 'TST Screening'
    2024-10-23 14:30:45,250 - reportalin - DEBUG -   │  ├─ Tables detected: 1
    2024-10-23 14:30:45,260 - reportalin - DEBUG -   │  ├─ Table 1 (TST Screening_table)
    2024-10-23 14:30:45,270 - reportalin - DEBUG -   │  │  ├─ Rows: 50
    2024-10-23 14:30:45,271 - reportalin - DEBUG -   │  │  ├─ Columns: 12
    2024-10-23 14:30:45,280 - reportalin - DEBUG -   │  │  └─ ⏱ Table processing time: 0.08s

.. note::
   Console output remains unchanged (only SUCCESS/ERROR messages shown).
   All verbose output goes to the log file for detailed analysis without cluttering the terminal.

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


De-identification Workflows
----------------------------

Running De-identification
~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable de-identification in the main pipeline:

.. code-block:: bash

   # Basic de-identification (uses default: India)
   python main.py --enable-deidentification

   # Specify countries
   python main.py --enable-deidentification --countries IN US ID

   # Use all supported countries
   python main.py --enable-deidentification --countries ALL

   # Disable encryption (testing only - NOT recommended)
   python main.py --enable-deidentification --no-encryption

Country-Specific De-identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The system supports 14 countries with specific privacy regulations:

.. code-block:: bash

   # India (default)
   python main.py --enable-deidentification --countries IN

   # Multiple countries (for international studies)
   python main.py --enable-deidentification --countries IN US ID BR

   # All countries (detects identifiers from all 14 supported countries)
   python main.py --enable-deidentification --countries ALL

Supported countries: US, EU, GB, CA, AU, IN, ID, BR, PH, ZA, KE, NG, GH, UG

For detailed information, see :doc:`country_regulations`.

De-identification Output Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The de-identified data maintains the same directory structure:

.. code-block:: text

   results/deidentified/Indo-vap/
   ├── original/
   │   ├── 10_TST.jsonl          # De-identified original files
   │   ├── 11_IGRA.jsonl
   │   └── ...
   ├── cleaned/
   │   ├── 10_TST.jsonl          # De-identified cleaned files
   │   ├── 11_IGRA.jsonl
   │   └── ...
   └── _deidentification_audit.json  # Audit log

   results/deidentified/mappings/
   └── mappings.enc                   # Encrypted mapping table

Standalone De-identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also run de-identification separately:

.. code-block:: bash

   # De-identify existing dataset
   python -m scripts.deidentify \
       --input-dir results/dataset/Indo-vap \
       --output-dir results/deidentified/Indo-vap \
       --countries IN US

   # List supported countries
   python -m scripts.deidentify --list-countries

   # Validate de-identified output
   python -m scripts.deidentify \
       --input-dir results/dataset/Indo-vap \
       --output-dir results/deidentified/Indo-vap \
       --validate

Working with De-identified Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd

   # Read de-identified file
   df = pd.read_json('results/deidentified/Indo-vap/cleaned/10_TST.jsonl', lines=True)
   
   # PHI/PII has been replaced with pseudonyms
   print(df.head())
   # Shows: [PATIENT-X7Y2], [SSN-A4B8], [DATE-1], etc.

For complete de-identification documentation, see :doc:`deidentification`.

Understanding Progress Output
------------------------------

Progress Bars and Status Messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RePORTaLiN provides real-time feedback during processing using progress bars:

.. code-block:: text

   Processing Files: 100%|████████████████| 43/43 [00:15<00:00,  2.87files/s]
   ✓ Processing 10_TST.xlsx: 1,234 rows
   ✓ Processing 11_IGRA.xlsx: 2,456 rows
   ...
   
   Summary:
   --------
   Successfully processed: 43 files
   Total records: 50,123
   Time elapsed: 15.2 seconds

**Key Features**:

- **tqdm progress bars**: Show percentage, speed, and time remaining
- **Clean output**: Status messages use ``tqdm.write()`` to avoid interfering with progress bars
- **Real-time updates**: Instant feedback on current operation
- **Summary statistics**: Final counts and timing information

**Modules with Progress Tracking**:

1. **Data Dictionary Loading** (``load_dictionary.py``):
   
   - Progress bar for processing sheets
   - Status messages for each table extracted
   - Summary of tables created

2. **Data Extraction** (``extract_data.py``):
   
   - Progress bar for files being processed
   - Per-file row counts
   - Final summary with totals

3. **De-identification** (``deidentify.py``):
   
   - Progress bar for batch processing
   - Detection statistics per file
   - Final summary with replacement counts

**Note**: Progress bars require the ``tqdm`` library, which is installed automatically with ``pip install -r requirements.txt``.

Verbose Logging Details
-----------------------

Understanding Verbose Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each pipeline step (Dictionary Loading, Data Extraction, De-identification) produces detailed tree-view logs when ``--verbose`` is enabled.

**Step 0: Data Dictionary Loading**

Verbose output shows the processing of Excel sheets and detected tables:

.. code-block:: text

    ├─ Processing: dictionary_file.xlsx (43 sheets)
    │  ├─ Total sheets: 43
    │  ├─ Sheet 1/43: 'TST Screening v1.0'
    │  │  ├─ Loading Excel file
    │  │  │  ├─ Rows: 45
    │  │  │  ├─ Columns: 15
    │  │  ├─ Tables detected: 1
    │  │  ├─ Table 1 (TST_Screening_table)
    │  │  │  ├─ Rows: 44
    │  │  │  ├─ Columns: 15
    │  │  │  ├─ Saved to: /path/to/TST_Screening/TST_Screening_table.jsonl
    │  │  │  └─ ⏱ Table processing time: 0.15s
    │  │  └─ ⏱ Sheet processing time: 0.18s
    │  └─ ⏱ Overall processing time: 45.23s

**What this tells you:**
- Total sheets and which sheet is being processed
- Number of tables found in each sheet
- Rows/columns for each table
- Time taken for each table and sheet
- Output file locations

**Step 1: Data Extraction**

Verbose output shows file processing with duplicate column removal:

.. code-block:: text

    ├─ Processing: Data extraction (65 files)
    │  ├─ Total files to process: 65
    │  ├─ File 1/65: 10_TST.xlsx
    │  │  ├─ Loading Excel file
    │  │  │  ├─ Rows: 412
    │  │  │  ├─ Columns: 28
    │  │  ├─ Saving original version
    │  │  │  ├─ Created: 10_TST.jsonl (412 records)
    │  │  ├─ Cleaning duplicate columns
    │  │  │  ├─ Marking SUBJID2 for removal (duplicate of SUBJID)
    │  │  │  ├─ Keeping NAME_ALT (different from NAME)
    │  │  │  ├─ Removed 3 duplicate columns: SUBJID2, AGE_2, PHONE_3
    │  │  ├─ Saving cleaned version
    │  │  │  ├─ Created: 10_TST.jsonl (412 records)
    │  │  │  └─ ⏱ Total processing time: 0.45s
    │  │  ├─ File 2/65: 11_IGRA.xlsx
    │  │  │  ...
    │  └─ ⏱ Overall extraction time: 32.15s

**What this tells you:**
- Which file is being processed and current progress
- Rows/columns in the source file
- Duplicate column detection and removal
- Records created for original and cleaned versions
- Processing time per file

**Step 2: De-identification** (when ``--enable-deidentification`` is used)

Verbose output shows de-identification and validation details:

.. code-block:: text

    ├─ Processing: De-identification (65 files)
    │  ├─ Total files to process: 65
    │  ├─ File 1/65: results/dataset/original/10_TST.jsonl
    │  │  ├─ Reading and de-identifying records
    │  │  │  ├─ Processed 100 records...
    │  │  │  ├─ Processed 200 records...
    │  │  │  ├─ Processed 412 records
    │  │  ├─ Records processed: 412
    │  │  └─ ⏱ File processing time: 0.89s
    │  ├─ File 2/65: results/dataset/original/11_IGRA.jsonl
    │  │  ...
    │  └─ ⏱ Overall de-identification time: 78.34s
    │
    ├─ Processing: Dataset validation (65 files)
    │  ├─ Total files to validate: 65
    │  ├─ File 1/65: 10_TST.jsonl
    │  │  ├─ Records validated: 412
    │  │  └─ ⏱ File validation time: 0.12s
    │  └─ ⏱ Overall validation time: 8.45s

**What this tells you:**
- De-identification progress with record counts
- Validation results per file
- Processing and validation times
- Any PHI/PII issues detected during validation

**Analyzing Log Files**

When processing completes, analyze the log file in `.logs/`:

.. code-block:: bash

    # View the latest log file
    tail -f .logs/reportalin_*.log
    
    # Search for specific errors
    grep "ERROR" .logs/reportalin_*.log
    
    # Count operations
    grep "✓ Complete" .logs/reportalin_*.log | wc -l
    
    # Extract timing information
    grep "⏱" .logs/reportalin_*.log

**Performance Tuning**: Use verbose logs to identify bottlenecks:

- If table processing is slow: Check for large tables or memory issues
- If file extraction is slow: Check for duplicate column detection overhead
- If de-identification is slow: Check for slow pattern matching or encryption

See Also
--------

For additional information:

- :doc:`quickstart`: Quick start guide
- :doc:`configuration`: Configuration options
- :doc:`deidentification`: Complete de-identification guide
- :doc:`country_regulations`: Country-specific privacy regulations
- :doc:`troubleshooting`: Common issues and solutions
