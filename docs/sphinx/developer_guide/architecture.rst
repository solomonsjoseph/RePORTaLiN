Architecture
============

**For Developers: Comprehensive Technical Documentation**

This document provides in-depth technical details about RePORTaLiN's architecture, internal
algorithms, data structures, dependencies, design patterns, and extension points to enable
effective maintenance, debugging, and feature development.

**Last Updated:** October 23, 2025  
**Current Version:** 0.3.0  
**Code Optimization:** 35% reduction (640 lines) while maintaining 100% functionality  
**Historical Enhancements:** Enhanced modules from v0.0.1 through v0.0.12

System Overview
---------------

RePORTaLiN is designed as a modular, pipeline-based system for processing sensitive medical 
research data from Excel to JSONL format with optional PHI/PII de-identification. The architecture 
emphasizes:

- **Simplicity**: Single entry point (``main.py``) with clear pipeline stages
- **Modularity**: Clear separation of concerns with dedicated modules
- **Robustness**: Comprehensive error handling with graceful degradation
- **Transparency**: Detailed logging at every step with audit trails
- **Security**: Encryption-by-default for de-identification mappings
- **Compliance**: Multi-country privacy regulation support (14 countries)
- **Performance**: Optimized for high throughput (benchmarks pending)

Architecture Diagram
--------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                         main.py                             │
   │                   (Pipeline Orchestrator)                   │
   │                                                             │
   │  • Command-line argument parsing                           │
   │  • Step execution coordination                             │
   │  • High-level error handling                              │
   └───────────────────┬─────────────────────────────────────────┘
                       │
            ┌──────────┴───────────┐
            │                      │
            ▼                      ▼
   ┌────────────────┐     ┌──────────────────┐
   │  load_dict.py  │     │ extract_data.py  │
   │                │     │                  │
   │ • Sheet split  │     │ • File discovery │
   │ • Table detect │     │ • Type convert   │
   │ • Duplicate    │     │ • JSONL export   │
   │   handling     │     │ • Progress track │
   └────────┬───────┘     └────────┬─────────┘
            │                      │
            └──────────┬───────────┘
                       │
                       ▼
              ┌────────────────┐
              │   config.py    │
              │                │
              │ • Paths        │
              │ • Settings     │
              │ • Dynamic      │
              │   detection    │
              └────────┬───────┘
                       │
                       ▼
              ┌────────────────┐
              │ logging  │
              │                │
              │ • Log files    │
              │ • Console out  │
              │ • SUCCESS lvl  │
              └────────────────┘

Core Components
---------------

1. main.py - Pipeline Orchestrator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Central entry point and workflow coordinator

**Responsibilities**:

- Parse command-line arguments
- Execute pipeline steps in sequence
- Handle top-level errors
- Coordinate logging

**Key Functions**:

- ``main()``: Entry point, orchestrates full pipeline
- ``run_step()``: Wrapper for step execution with error handling

**Design Pattern**: Command pattern with error handling decorator

2. config.py - Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Centralized configuration

**Responsibilities**:

- Define all file paths
- Manage settings
- Dynamic dataset detection
- Path resolution

**Key Features**:

- Automatic dataset folder detection
- Relative path resolution
- Environment-agnostic configuration
- Type hints for IDE support

**Design Pattern**: Module-level singleton

3. scripts/extract_data.py - Data Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Convert Excel files to JSONL

**Responsibilities**:

- File discovery and validation
- Excel reading and parsing
- Data type conversion
- JSONL serialization
- Progress tracking with tqdm

**Key Functions**:

- ``extract_excel_to_jsonl()``: Batch processing with progress bars
- ``process_excel_file()``: Single file processing
- ``convert_dataframe_to_jsonl()``: DataFrame conversion
- ``clean_record_for_json()``: Type conversion
- ``is_dataframe_empty()``: Empty detection
- ``find_excel_files()``: File discovery

**Progress Tracking**:

- Uses tqdm for all file and row processing
- Status messages via tqdm.write() for clean output
- Summary statistics after completion

**Design Pattern**: Pipeline pattern with functional composition

4. scripts/load_dictionary.py - Dictionary Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Process data dictionary Excel file

**Responsibilities**:

- Sheet processing with progress tracking
- Table detection and splitting
- Duplicate column handling
- Table serialization

**Key Functions**:

- ``load_study_dictionary()``: High-level API with tqdm progress bars
- ``process_excel_file()``: Sheet processing
- ``_split_sheet_into_tables()``: Table detection
- ``_process_and_save_tables()``: Table output
- ``_deduplicate_columns()``: Column name handling

**Progress Tracking**:

- tqdm progress bars for sheet processing
- tqdm.write() for status messages
- Clean console output during processing

**Design Pattern**: Functional composition with table detection algorithm

**Design Pattern**: Strategy pattern for table detection

5. scripts/utils/logging.py - Logging System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Centralized logging infrastructure

**Responsibilities**:

- Create timestamped log files
- Dual output (console + file)
- Custom SUCCESS log level
- Structured logging with configurable verbosity

**Key Features**:

- Custom SUCCESS level (between INFO and WARNING)
- Timestamped log files in ``.logs/`` directory
- Console and file handlers with different filtering
- UTF-8 encoding for international characters
- Works alongside tqdm for clean progress bar output
- **Verbose mode**: DEBUG-level logging via ``-v`` flag

**Log Levels**:

.. code-block:: python

   DEBUG (10)    # Verbose mode only: file processing, patterns, details
   INFO (20)     # Default: major steps, summaries
   SUCCESS (25)  # Custom: successful completions
   WARNING (30)  # Potential issues
   ERROR (40)    # Failures
   CRITICAL (50) # Fatal errors

**Console vs. File Output**:

- **Console**: Only SUCCESS, ERROR, and CRITICAL (keeps terminal clean)
- **File**: INFO or DEBUG (depending on ``--verbose`` flag) and above

**Verbose Logging**:

When ``--verbose`` or ``-v`` flag is used:

- Log level set to DEBUG in ``main.py``
- Additional details logged throughout pipeline:
  
  - File lists and processing order
  - Sheet/table detection details
  - Duplicate column detection
  - PHI/PII pattern matches
  - Record-level progress (every 1000 records)

**Usage**:

.. code-block:: python

   from scripts.utils import logging as log
   
   # Standard (INFO level)
   python main.py
   
   # Verbose (DEBUG level)
   python main.py -v
   
   # In code
   log.debug("Detailed processing info")  # Only in verbose mode
   log.info("Major step completed")       # Always logged to file
   log.success("Pipeline completed")      # Console + file

**Design Pattern**: Singleton logger instance with configurable formatting

6. scripts/deidentify.py - De-identification Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Remove PHI/PII from text data with pseudonymization

**Responsibilities**:

- Detect PHI/PII using regex patterns
- Generate consistent pseudonyms
- Encrypt and store mappings
- Validate de-identified output
- Support country-specific regulations
- Progress tracking for large datasets

**Key Classes**:

- ``DeidentificationEngine``: Main orchestrator
- ``PseudonymGenerator``: Creates deterministic placeholders
- ``MappingStore``: Secure encrypted storage
- ``DateShifter``: Consistent date shifting
- ``PatternLibrary``: Detection patterns

**Progress Tracking**:

- tqdm progress bars for processing batches
- tqdm.write() for status messages during processing
- Summary statistics upon completion

**Design Pattern**: Strategy pattern for detection, Builder pattern for configuration

7. scripts/utils/country_regulations.py - Country-Specific Regulations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Manage country-specific data privacy regulations

**Responsibilities**:

- Define country-specific data fields
- Provide detection patterns for local identifiers
- Document regulatory requirements
- Support multiple jurisdictions simultaneously

**Key Classes**:

- ``CountryRegulationManager``: Orchestrates regulations
- ``CountryRegulation``: Single country configuration
- ``DataField``: Field definition with validation
- ``PrivacyLevel`` / ``DataFieldType``: Enumerations

**Supported Countries**: US, EU, GB, CA, AU, IN, ID, BR, PH, ZA, KE, NG, GH, UG

**Design Pattern**: Registry pattern for country lookup, Factory pattern for regulation creation

Data Flow
---------

Step-by-Step Data Flow:

.. code-block:: text

   1. User invokes: python main.py
                    │
                    ▼
   2. main.py initializes logging
                    │
                    ▼
   3. Step 0: load_study_dictionary()
                    │
      ┌─────────────┴──────────────┐
      │                            │
      ▼                            ▼
   Read Excel           Split sheets into tables
   Dictionary                     │
                                  ▼
                        Deduplicate columns
                                  │
                                  ▼
                        Save as JSONL in:
                        results/data_dictionary_mappings/
                    │
                    ▼
   4. Step 1: extract_excel_to_jsonl()
                    │
      ┌─────────────┴──────────────┐
      │                            │
      ▼                            ▼
   Find Excel files    Process each file
   in dataset/                    │
                      ┌───────────┴────────────┐
                      │                        │
                      ▼                        ▼
              Read Excel sheets    Convert data types
                      │                        │
                      ▼                        ▼
              Clean records        Handle NaN/dates
                      │                        │
                      └───────────┬────────────┘
                                  │
                                  ▼
                        Save as JSONL in:
                        results/dataset/<dataset_name>/
                            ├── original/  (all columns)
                            └── cleaned/   (duplicates removed)
                    │
                    ▼
   5. Step 2: deidentify_dataset() [OPTIONAL]
                    │
      ┌─────────────┴──────────────┐
      │                            │
      ▼                            ▼
   Recursively find      Process each file
   JSONL files                    │
   in subdirs         ┌───────────┴────────────┐
                      │                        │
                      ▼                        ▼
              Detect PHI/PII       Generate pseudonyms
                      │                        │
                      ▼                        ▼
              Replace sensitive    Maintain mappings
                   data                        │
                      └───────────┬────────────┘
                                  │
                                  ▼
                        Save de-identified in:
                        results/deidentified/<dataset_name>/
                            ├── original/  (de-identified)
                            ├── cleaned/   (de-identified)
                            └── _deidentification_audit.json
                        
                        Store encrypted mappings:
                        results/deidentified/mappings/
                            └── mappings.enc

Data Flow Architecture
----------------------

The system processes data through three primary pipelines:

**Pipeline 1: Data Dictionary Processing**

.. code-block:: text

   Excel File (Dictionary) → pd.read_excel() → Table Detection → Split Tables 
   → Column Deduplication → "Ignore Below" Filter → JSONL Export (per table)
   
   Algorithm: Two-Phase Table Detection
   1. Horizontal Split: Identify empty rows as boundaries
   2. Vertical Split: Within horizontal strips, identify empty columns
   3. Result: NxM tables from single sheet

**Pipeline 2: Data Extraction**

.. code-block:: text

   Excel Files (Dataset) → find_excel_files() → pd.read_excel() 
   → Type Conversion → Duplicate Column Removal → JSONL Export
   → File Integrity Check → Statistics Collection
   
   Outputs: Two versions (original/, cleaned/) for validation

**Pipeline 3: De-identification** *(Optional)*

.. code-block:: text

   JSONL Files → Pattern Matching (Regex + Country-Specific) 
   → PHI/PII Detection → Pseudonym Generation (Cryptographic Hash) 
   → Mapping Storage (Encrypted) → Date Shifting (Consistent Offset)
   → Validation → Encrypted JSONL Output + Audit Log
   
   Security: Fernet encryption, deterministic pseudonyms, audit trails

Design Decisions
----------------

1. JSONL Format
~~~~~~~~~~~~~~~

**Rationale**: 

- Line-oriented: Each record is independent
- Streaming friendly: Can process files line-by-line
- Easy to merge: Just concatenate files
- Human-readable: Each line is valid JSON
- Standard format: Wide tool support

**Alternative Considered**: CSV
**Rejected Because**: CSV doesn't handle nested structures well

2. Automatic Table Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rationale**:

- Excel sheets often contain multiple logical tables
- Empty rows/columns serve as natural separators
- Preserves semantic structure of data

**Algorithm**:

1. Find maximum consecutive empty rows/columns
2. Split at these boundaries
3. Handle special "Ignore below" markers

3. Dynamic Dataset Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rationale**:

- Avoid hardcoding dataset names
- Enable working with multiple datasets
- Reduce configuration burden

**Implementation**: Scan ``data/dataset/`` for first subdirectory

4. Progress Tracking
~~~~~~~~~~~~~~~~~~~~

**Rationale**:

- Long-running operations need real-time feedback
- Users want to know progress and time remaining
- Helps identify slow operations
- Clean console output is essential

**Implementation**:

- **tqdm** library for all progress bars (required dependency)
- **tqdm.write()** for status messages during progress tracking
- Consistent usage across all processing modules:
  
  - ``extract_data.py``: File and row processing
  - ``load_dictionary.py``: Sheet processing
  - ``deidentify.py``: Batch de-identification

**Design Decision**: tqdm is a required dependency, not optional, ensuring consistent user experience

5. Centralized Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rationale**:

- Single source of truth
- Easy to modify paths
- Reduces coupling
- Testability

**Alternative Considered**: Environment variables
**Rejected Because**: More complex for non-technical users

Algorithms and Data Structures
-------------------------------

**Algorithm 1: Two-Phase Table Detection**

Located in: ``scripts/load_dictionary.py`` → ``_split_sheet_into_tables()``

**Purpose:** Intelligently split Excel sheets containing multiple logical tables into separate tables

**Algorithm:**

.. code-block:: text

   Phase 1: Horizontal Splitting
   1. Identify rows where ALL cells are null/empty
   2. Use these rows as boundaries to split sheet into horizontal strips
   3. Each strip potentially contains one or more tables side-by-side
   
   Phase 2: Vertical Splitting (within each horizontal strip)
   1. Identify columns where ALL cells are null/empty
   2. Use these columns as boundaries to split strip into tables
   3. Remove completely empty tables
   4. Drop rows that are entirely null
   
   Result: NxM independent tables from single sheet

**Data Structures:**

.. code-block:: python

   # Input: Raw DataFrame (no assumptions about structure)
   df: pd.DataFrame  # header=None, all data preserved
   
   # Intermediate: List of horizontal strips
   horizontal_strips: List[pd.DataFrame]
   
   # Output: List of independent tables
   all_tables: List[pd.DataFrame]

**Edge Cases Handled:**

- Empty rows between tables (common in medical research data dictionaries)
- Empty columns between tables (side-by-side table layouts)
- Tables with no data rows (only headers) - preserved with metadata
- "ignore below" markers - subsequent tables saved to separate directory
- Duplicate column names - automatically suffixed with "_1", "_2", etc.

**Complexity:** O(r × c) where r = rows, c = columns

---

**Algorithm 2: JSON Type Conversion**

Located in: ``scripts/extract_data.py`` → ``clean_record_for_json()``

**Purpose:** Convert pandas/numpy types to JSON-serializable Python types

**Algorithm:**

.. code-block:: text

   For each key-value pair in record:
   1. If value is pd.isna(value) → None (JSON null)
   2. If value is np.integer or np.floating → call .item() to get Python int/float
   3. If value is pd.Timestamp, np.datetime64, datetime, date → convert to string
   4. Otherwise → keep as-is
   
   Return cleaned dictionary

**Type Mappings:**

==================  ======================  ====================
Pandas/Numpy Type   Python Type             JSON Type
==================  ======================  ====================
pd.NA, np.nan       None                    null
np.int64            int                     number
np.float64          float                   number
pd.Timestamp        str                     string (ISO format)
datetime            str                     string
==================  ======================  ====================

**Edge Cases:**

- Mixed-type columns → handled by pandas during read_excel()
- Unicode characters → preserved with ensure_ascii=False
- Large integers → may lose precision if > 2^53 (JSON limitation)

---

**Algorithm 3: Duplicate Column Detection and Removal**

Located in: ``scripts/extract_data.py`` → ``clean_duplicate_columns()``

**Purpose:** Remove duplicate columns with numeric suffixes (e.g., SUBJID2, SUBJID3)

**Algorithm:**

.. code-block:: text

   For each column in DataFrame:
   1. Match pattern: column_name ends with "_?" followed by digits
   2. Extract base_name (everything before the suffix)
   3. If base_name exists as a column:
      - Mark current column for removal (it's a duplicate)
      - Keep the base column
   4. Otherwise:
      - Keep the column
   
   Return DataFrame with only non-duplicate columns

**Regex Pattern:** ``^(.+?)_?(\d+)$``

**Examples:**

- ``SUBJID`` (base) + ``SUBJID2``, ``SUBJID3`` → Keep ``SUBJID``, remove others
- ``NAME_1`` (numbered) + ``NAME`` (base) → Keep ``NAME``, remove ``NAME_1``
- ``ID3`` (numbered) + ``ID`` (base) → Keep ``ID``, remove ``ID3``

---

**Algorithm 4: Cryptographic Pseudonymization**

Located in: ``scripts/deidentify.py`` → ``PseudonymGenerator.generate()``

**Purpose:** Generate deterministic, unique pseudonyms for PHI/PII values

**Algorithm:**

.. code-block:: text

   Input: (value, phi_type, template)
   
   1. Check cache: If (phi_type, value.lower()) already pseudonymized:
      - Return cached pseudonym (ensures consistency)
   
   2. Generate deterministic ID:
      a. Create hash_input = "{salt}:{phi_type}:{value}"
      b. hash_digest = SHA256(hash_input)
      c. Take first 4 bytes of digest
      d. Encode as base32, strip padding, take first 6 chars
      e. Result: Alphanumeric ID (e.g., "A4B8C3")
   
   3. Apply template:
      - Replace {id} placeholder with generated ID
      - Example: "PATIENT-{id}" → "PATIENT-A4B8C3"
   
   4. Cache and return pseudonym

**Security Properties:**

- **Deterministic:** Same input always produces same output (required for data consistency)
- **One-way:** Cannot reverse SHA256 without salt
- **Salt-dependent:** Different salt produces different pseudonyms
- **Collision-resistant:** SHA256 ensures uniqueness

**Data Structure:**

.. code-block:: python

   class PseudonymGenerator:
       salt: str  # Cryptographic salt (32 bytes hex)
       _cache: Dict[Tuple[PHIType, str], str]  # Memoization
       _counter: Dict[PHIType, int]  # Statistics

---

**Algorithm 5: Consistent Date Shifting (Country-Aware)**

Located in: ``scripts/deidentify.py`` → ``DateShifter.shift_date()``

**Purpose:** Shift all dates by consistent offset to preserve temporal relationships,
with intelligent multi-format detection and country-specific priority

**Algorithm:**

.. code-block:: text

   Input: date_string, country_code
   
   1. Determine format priority based on country:
      - DD/MM/YYYY priority: IN, ID, BR, ZA, EU, GB, AU, KE, NG, GH, UG
      - MM/DD/YYYY priority: US, PH, CA
   
   2. Check cache: If date_string already shifted:
      - Return cached shifted date
   
   3. Generate consistent offset (first time only):
      a. hash_digest = SHA256(seed)
      b. offset_int = first 4 bytes as integer
      c. offset_days = (offset_int % (2 * range + 1)) - range
      d. Cache offset for all future shifts
   
   4. Try parsing with multiple formats (in priority order):
      Country with DD/MM/YYYY priority:
         a. Try DD/MM/YYYY
         b. Try YYYY-MM-DD (ISO 8601)
         c. Try DD-MM-YYYY
         d. Try DD.MM.YYYY
      
      Country with MM/DD/YYYY priority:
         a. Try MM/DD/YYYY
         b. Try YYYY-MM-DD (ISO 8601)
         c. Try MM-DD-YYYY
   
   5. Apply shift with successful format:
      a. Parse date_string to datetime object
      b. shifted_date = original_date + timedelta(days=offset_days)
      c. Format back to string in SAME format as input
   
   5. Cache and return shifted date

**Properties:**

- **Consistent:** All dates shifted by SAME offset (preserves intervals)
- **Deterministic:** Seed determines offset (reproducible)
- **Country-aware:** Correct interpretation of DD/MM vs MM/DD formats
- **Format-preserving:** Output format matches input format
- **HIPAA-compliant:** Dates obscured while relationships preserved

**Example:**

.. code-block:: python

   # For India (DD/MM/YYYY format):
   shifter_in = DateShifter(country_code="IN", seed="abc123")
   "04/09/2014" → "14/12/2013"  # Sept 4, 2014 → Dec 14, 2013 (-265 days)
   "09/09/2014" → "19/12/2013"  # Sept 9, 2014 → Dec 19, 2013 (-265 days)
   # Interval preserved: 5 days apart in both

   # For United States (MM/DD/YYYY format):
   shifter_us = DateShifter(country_code="US", seed="abc123")
   "04/09/2014" → "07/17/2013"  # Apr 9, 2014 → July 17, 2013 (-265 days)
   "04/14/2014" → "07/22/2013"  # Apr 14, 2014 → July 22, 2013 (-265 days)
   # Interval preserved: 5 days apart in both
   # Interval preserved: 64 days in both cases

---

**Data Structure: Mapping Store (Encrypted)**

Located in: ``scripts/deidentify.py`` → ``MappingStore``

**Purpose:** Securely store original → pseudonym mappings

**Structure:**

.. code-block:: python

   # In-memory structure
   mappings: Dict[str, Dict[str, Any]] = {
       "PHI_TYPE:original_value": {
           "original": "John Doe",  # Original sensitive value
           "pseudonym": "PATIENT-A4B8C3",  # Generated pseudonym
           "phi_type": "NAME_FULL",  # Type of PHI
           "created_at": "2025-10-13T14:32:15",  # Timestamp
           "metadata": {"pattern": "Full name pattern"}
       },
       ...
   }
   
   # On-disk structure (encrypted with Fernet)
   File: mappings.enc
   Content: Fernet.encrypt(JSON.dumps(mappings))

**Encryption:** Fernet (symmetric encryption, 128-bit AES in CBC mode with HMAC)

**Security:**

- Encryption key stored separately
- Keys never committed to version control
- Audit log exports WITHOUT original values by default

---

**Data Structure: JSONL File Format**

**Structure:**

Each line is a valid JSON object (one record per line):

.. code-block:: json

   {"SUBJID": "INV001", "VISIT": 1, "TST_RESULT": "Positive", "source_file": "10_TST.xlsx"}
   {"SUBJID": "INV002", "VISIT": 1, "TST_RESULT": "Negative", "source_file": "10_TST.xlsx"}
   {"SUBJID": "INV003", "VISIT": 1, "TST_RESULT": "Positive", "source_file": "10_TST.xlsx"}

**Advantages:**

- Streamable: Can process without loading entire file into memory
- Line-oriented: Easy to split, merge, or process in parallel
- JSON-compatible: Works with standard JSON parsers
- Human-readable: Can inspect with `head`, `tail`, `grep`

**Metadata Fields:**

- ``source_file``: Original Excel filename for traceability
- ``_metadata``: Optional metadata (e.g., for empty files with structure)

---

**Data Structure: Progress Tracking with tqdm**

**Integration Pattern:**

.. code-block:: python

   from tqdm import tqdm
   import sys
   
   # File-level progress
   for file in tqdm(files, desc="Processing", unit="file", 
                    file=sys.stdout, dynamic_ncols=True, leave=True):
       # Use tqdm.write() instead of print() for clean output
       tqdm.write(f"Processing: {file.name}")
       
       # Row-level progress (if needed)
       for row in tqdm(rows, desc="Rows", leave=False):
           process(row)
   
   # Result: Clean progress bars without interfering with logging

**Why tqdm.write():**

- Ensures messages don't corrupt progress bar display
- Automatically repositions progress bar after message
- Works with logging system

Dependencies and Their Roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**pandas (>= 2.0.0)**

- Role: DataFrame manipulation, Excel reading, data analysis
- Key functions used:
  - ``pd.read_excel()``: Excel file parsing
  - ``df.to_json()``: JSONL export
  - ``pd.isna()``: Null value detection
- Why chosen: Industry standard for data manipulation in Python

**openpyxl (>= 3.1.0)**

- Role: Excel file format (.xlsx) support for pandas
- Used by: ``pd.read_excel(engine='openpyxl')``
- Why chosen: Pure Python, no external dependencies, handles modern Excel formats

**numpy (>= 1.24.0)**

- Role: Numerical operations, type handling
- Key types used:
  - ``np.int64``, ``np.float64``: Numeric types from pandas
  - ``np.datetime64``: Datetime types
  - ``np.nan``: Missing value representation
- Why chosen: Required by pandas, efficient numerical operations

**tqdm (>= 4.66.0)**

- Role: Progress bars and user feedback
- Key features:
  - Real-time progress tracking
  - ETA calculations
  - Clean console output with ``tqdm.write()``
- Why chosen: Most popular Python progress bar library, excellent integration

**cryptography (>= 41.0.0)**

- Role: Encryption for de-identification mappings
- Key components:
  - ``Fernet``: Symmetric encryption
  - ``hashlib.sha256()``: Cryptographic hashing
  - ``secrets``: Secure random number generation
- Why chosen: Industry-standard cryptography library, HIPAA-compliant algorithms

**sphinx (>= 7.0.0) + extensions**

- Role: Documentation generation
- Extensions used:
  - ``sphinx.ext.autodoc``: Automatic API documentation from docstrings
  - ``sphinx.ext.napoleon``: Google/NumPy style docstring support
  - ``sphinx_autodoc_typehints``: Type hint documentation
  - ``sphinx-autobuild``: Live documentation preview (dev dependency)
- Why chosen: Standard for Python project documentation

**Documentation Workflow**:

.. versionadded:: 0.3.0
   Added ``make docs-watch`` for automatic documentation rebuilding.

- **Autodoc is ENABLED**: Sphinx automatically extracts documentation from Python docstrings
- **NOT Automatic by Default**: Documentation does NOT rebuild automatically on every code change
- **Manual Build**: Run ``make docs`` to regenerate documentation after changes
- **Auto-Rebuild (Development)**: Use ``make docs-watch`` for live preview during documentation development

**How Autodoc Works**:

1. Write Google-style docstrings in Python code
2. Use ``.. automodule::`` directives in ``.rst`` files
3. Run ``make docs`` - Sphinx extracts docstrings and generates HTML
4. Or use ``make docs-watch`` - Server auto-rebuilds on file changes

**Important**: While autodoc **extracts** documentation automatically from code, 
you must **build** the documentation manually (or use watch mode) to see the changes.
