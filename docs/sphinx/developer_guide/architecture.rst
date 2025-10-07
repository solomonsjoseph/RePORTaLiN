Architecture
============

This document describes the architecture and design of the RePORTaLiN data processing pipeline.

System Overview
---------------

RePORTaLiN is designed as a modular, pipeline-based system for processing medical research 
data from Excel to JSONL format. The architecture emphasizes:

- **Simplicity**: Single entry point (``main.py``)
- **Modularity**: Clear separation of concerns
- **Robustness**: Comprehensive error handling
- **Transparency**: Detailed logging at every step

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
              │ logging_utils  │
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
- Progress tracking

**Key Functions**:

- ``extract_excel_to_jsonl()``: Batch processing
- ``process_excel_file()``: Single file processing
- ``convert_dataframe_to_jsonl()``: DataFrame conversion
- ``clean_record_for_json()``: Type conversion
- ``is_dataframe_empty()``: Empty detection
- ``find_excel_files()``: File discovery

**Design Pattern**: Pipeline pattern with functional composition

4. scripts/load_dictionary.py - Dictionary Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Process data dictionary Excel file

**Responsibilities**:

- Sheet processing
- Table detection and splitting
- Duplicate column handling
- Table serialization

**Key Functions**:

- ``load_study_dictionary()``: High-level API
- ``process_excel_file()``: Sheet processing
- ``_split_sheet_into_tables()``: Table detection
- ``_process_and_save_tables()``: Table output
- ``_deduplicate_columns()``: Column name handling

**Design Pattern**: Strategy pattern for table detection

5. scripts/utils/logging_utils.py - Logging System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Centralized logging infrastructure

**Responsibilities**:

- Create timestamped log files
- Dual output (console + file)
- Custom SUCCESS log level
- Structured logging

**Key Features**:

- Custom SUCCESS level (between INFO and WARNING)
- Timestamped log files
- Console and file handlers
- UTF-8 encoding for international characters

**Design Pattern**: Singleton logger instance

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

- Long-running operations need feedback
- Users want to know time remaining
- Helps identify slow operations

**Implementation**: tqdm library for standard progress bars

5. Centralized Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rationale**:

- Single source of truth
- Easy to modify paths
- Reduces coupling
- Testability

**Alternative Considered**: Environment variables
**Rejected Because**: More complex for non-technical users

Module Dependencies
-------------------

.. code-block:: text

   main.py
   ├── scripts.load_dictionary
   │   └── scripts.utils.logging_utils
   ├── scripts.extract_data
   │   └── scripts.utils.logging_utils
   └── config
       └── scripts.utils.logging_utils

   Dependencies are minimal and unidirectional (no circular deps)

External Dependencies
~~~~~~~~~~~~~~~~~~~~~

- **pandas**: DataFrame operations, Excel I/O
- **openpyxl**: Excel 2007+ file format support
- **numpy**: Numerical operations, NaN handling
- **tqdm**: Progress bar display
- **sphinx** (optional): Documentation generation

Error Handling Strategy
-----------------------

Layered Error Handling:

1. **Function Level**: Validate inputs, handle expected errors
2. **Module Level**: Catch and log module-specific errors  
3. **Pipeline Level**: Catch and report step failures
4. **Main Level**: Last resort error handling

Example:

.. code-block:: python

   # Function level
   def process_file(file_path):
       if not file_path.exists():
           raise FileNotFoundError(f"File not found: {file_path}")
       try:
           return pd.read_excel(file_path)
       except Exception as e:
           log.error(f"Error reading {file_path}: {e}")
           raise

   # Pipeline level (main.py)
   def run_step(step_name, func):
       try:
           result = func()
           log.success(f"{step_name} completed")
           return result
       except Exception as e:
           log.error(f"Error in {step_name}: {e}", exc_info=True)
           sys.exit(1)

Extensibility Points
--------------------

The architecture supports extension in several ways:

1. **New Processing Steps**: Add to ``main.py`` pipeline
2. **Custom Data Types**: Extend ``clean_record_for_json()``
3. **New Output Formats**: Create new conversion functions
4. **Custom Table Detection**: Modify ``_split_sheet_into_tables()``
5. **Additional Logging**: Use ``logging_utils`` in new modules

Example - Adding a New Step:

.. code-block:: python

   # main.py
   def step_2_validate_data():
       """New validation step"""
       # Your code here
       pass

   def main():
       # ... existing steps ...
       run_step("Step 2: Validating Data", step_2_validate_data)

Performance Characteristics
---------------------------

**Time Complexity**:

- File discovery: O(n) where n = number of files
- Excel reading: O(m) where m = file size
- Type conversion: O(r × c) where r = rows, c = columns
- Overall: Linear in data size

**Space Complexity**:

- One file in memory at a time
- Peak memory: Size of largest Excel file
- Output: Streaming to disk (constant memory)

**Typical Performance**:

- 43 files, ~50,000 total records: 15-20 seconds
- Approximately 2-3 files/second
- Minimal memory usage (<500 MB)

Testing Strategy
----------------

The architecture supports testing at multiple levels:

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test module interactions
3. **End-to-End Tests**: Test full pipeline

See :doc:`testing` for detailed testing guide.

Security Considerations
-----------------------

1. **File Access**: Only reads from configured directories
2. **Path Traversal**: Uses absolute paths, no user input in paths
3. **Code Injection**: No eval() or exec() usage
4. **Data Validation**: Type checking for all conversions

Future Architecture Considerations
-----------------------------------

Potential improvements (not yet implemented):

1. **Plugin System**: Dynamic loading of processing modules
2. **Parallel Processing**: Process multiple files concurrently
3. **Database Output**: Direct database writes
4. **Incremental Updates**: Process only changed files
5. **Data Validation**: Schema-based validation

See Also
--------

- :doc:`contributing`: How to contribute
- :doc:`extending`: Extending the pipeline
- :doc:`testing`: Testing guide
- :doc:`../api/modules`: API reference
