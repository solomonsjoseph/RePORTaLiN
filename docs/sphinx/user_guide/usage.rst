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

Verbose Logging
~~~~~~~~~~~~~~~

Enable detailed DEBUG-level logging for troubleshooting and monitoring:

.. code-block:: bash

   # Enable verbose logging
   python main.py --verbose
   
   # Short form
   python main.py -v
   
   # With de-identification
   python main.py -v --enable-deidentification --countries IN US

**What verbose mode shows:**

- List of files found and their processing order
- Sheet names and table counts for dictionary files
- Individual file processing status
- Duplicate column detection details
- De-identification pattern matches and PHI/PII detection counts
- Progress updates every 1000 records for large files

**Log file location:** ``.logs/reportalin_YYYYMMDD_HHMMSS.log``

**Performance impact:** Minimal (<2% slowdown), increases log file size by 3-5x

.. note::
   Console output remains unchanged (only SUCCESS/ERROR messages).
   Verbose output goes to the log file for detailed analysis.

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

See Also
--------

For additional information:

- :doc:`quickstart`: Quick start guide
- :doc:`configuration`: Configuration options
- :doc:`deidentification`: Complete de-identification guide
- :doc:`country_regulations`: Country-specific privacy regulations
- :doc:`troubleshooting`: Common issues and solutions
