scripts.load_dictionary module
==============================

.. automodule:: scripts.load_dictionary
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``load_dictionary`` module processes Excel-based data dictionaries with
intelligent table detection, automatic splitting, and duplicate column handling.

Functions
---------

load_study_dictionary
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.load_dictionary.load_study_dictionary

High-level API for loading a data dictionary Excel file.

**Parameters**:

- ``file_path`` (str, optional): Path to data dictionary Excel file (defaults to ``config.DICTIONARY_EXCEL_FILE``)
- ``json_output_dir`` (str, optional): Directory for output JSONL files (defaults to ``config.DICTIONARY_JSON_OUTPUT_DIR``)
- ``preserve_na`` (bool, optional): If True, preserve empty cells as None (default: True)

**Returns**:

- ``bool``: True if processing was successful, False otherwise

**Example**:

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   
   # Use config defaults
   success = load_study_dictionary()
   
   # Or specify custom paths
   success = load_study_dictionary(
       file_path="data/data_dictionary.xlsx",
       json_output_dir="results/data_dictionary_mappings"
   )

process_excel_file
~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.load_dictionary.process_excel_file

Process all sheets in a data dictionary Excel file.

**Parameters**:

- ``excel_path`` (str): Path to Excel file
- ``output_dir`` (str): Directory for output files
- ``preserve_na`` (bool, optional): If True, preserve empty cells as None (default: True)

**Returns**:

- ``bool``: True if processing was successful, False otherwise

**Example**:

.. code-block:: python

   from scripts.load_dictionary import process_excel_file
   
   success = process_excel_file(
       excel_path="data/dictionary.xlsx",
       output_dir="results/dictionary_output"
   )

Table Detection
---------------

_split_sheet_into_tables
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.load_dictionary._split_sheet_into_tables

Automatically detect and split tables within a sheet.

**Algorithm**:

1. Find maximum consecutive empty rows/columns
2. Use as threshold for splitting
3. Handle special "Ignore below" markers
4. Split at boundaries
5. Return list of tables

**Parameters**:

- ``df`` (pd.DataFrame): Input DataFrame (one sheet)

**Returns**:

- ``list``: List of DataFrames (one per table)

**Example**:

.. code-block:: python

   import pandas as pd
   from scripts.load_dictionary import _split_sheet_into_tables
   
   df = pd.read_excel("sheet.xlsx")
   tables = _split_sheet_into_tables(df)
   print(f"Found {len(tables)} tables")

Table Processing
----------------

_process_and_save_tables
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.load_dictionary._process_and_save_tables

Process and save detected tables to JSONL files.

**Parameters**:

- ``tables`` (list): List of DataFrames
- ``sheet_name`` (str): Original sheet name
- ``output_dir`` (str): Output directory

**Output Files**:

- Single table: ``{sheet_name}_table.jsonl``
- Multiple tables: ``{sheet_name}_table_1.jsonl``, ``{sheet_name}_table_2.jsonl``, etc.

Column Handling
---------------

_deduplicate_columns
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.load_dictionary._deduplicate_columns

Handle duplicate column names by adding numeric suffixes.

**Algorithm**:

1. Track column name occurrences
2. First occurrence: Keep original name
3. Subsequent occurrences: Add ``_1``, ``_2``, ``_3``, etc.

**Parameters**:

- ``columns`` (list): List of column names

**Returns**:

- ``list``: Deduplicated column names

**Example**:

.. code-block:: python

   from scripts.load_dictionary import _deduplicate_columns
   
   columns = ['id', 'name', 'id', 'value', 'name']
   result = _deduplicate_columns(columns)
   print(result)
   # Output: ['id', 'name', 'id_1', 'value', 'name_1']

Processing Flow
---------------

The dictionary loading follows this flow:

.. code-block:: text

   1. load_study_dictionary(file_path, json_output_dir)
      │
      └── process_excel_file(excel_path, output_dir)
          │
          ├── For each sheet in Excel file:
          │   │
          │   ├── Read sheet: pd.read_excel(sheet_name=sheet)
          │   │
          │   ├── _split_sheet_into_tables(df)
          │   │   │
          │   │   ├── Find empty row/column boundaries
          │   │   │
          │   │   ├── Check for "Ignore below" markers
          │   │   │
          │   │   └── Return: [table1, table2, ...]
          │   │
          │   └── _process_and_save_tables(tables, sheet_name, output_dir)
          │       │
          │       └── For each table:
          │           │
          │           ├── _deduplicate_columns(table.columns)
          │           │
          │           ├── Create output directory: {output_dir}/{sheet_name}/
          │           │
          │           └── Save as JSONL: {sheet_name}_table_N.jsonl

Table Detection Algorithm
-------------------------

The automatic table detection uses this algorithm:

1. **Find Empty Boundaries**:

   .. code-block:: python

      # Find max consecutive empty rows
      max_empty_rows = 0
      for each row:
          if row is all empty:
              count_empty += 1
          else:
              max_empty_rows = max(max_empty_rows, count_empty)
              count_empty = 0

2. **Split at Boundaries**:

   .. code-block:: python

      # Use threshold to split
      threshold = max(max_empty_rows - 1, 1)
      current_empty = 0
      for each row:
          if row is all empty:
              current_empty += 1
              if current_empty >= threshold:
                  # Split here
          else:
              current_empty = 0

3. **Handle Special Markers**:

   .. code-block:: python

      # Check for "Ignore below" marker
      for each row:
          if "ignore below" in row (case-insensitive):
              # Discard everything after this row
              break

Output Structure
----------------

The module creates this output structure:

.. code-block:: text

   results/data_dictionary_mappings/
   ├── Sheet1/
   │   └── Sheet1_table.jsonl          # Single table
   │
   ├── Sheet2/
   │   ├── Sheet2_table_1.jsonl        # Multiple tables
   │   └── Sheet2_table_2.jsonl
   │
   └── Codelists/
       ├── Codelists_table_1.jsonl
       ├── Codelists_table_2.jsonl
       └── Codelists_table_3.jsonl

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   import config
   
   # Use config defaults
   success = load_study_dictionary()
   
   # Or specify custom paths
   success = load_study_dictionary(
       file_path=config.DICTIONARY_EXCEL_FILE,
       json_output_dir=config.DICTIONARY_JSON_OUTPUT_DIR
   )

Process Custom Dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scripts.load_dictionary import load_study_dictionary
   
   success = load_study_dictionary(
       file_path="my_dictionary.xlsx",
       json_output_dir="output/dictionary"
   )
   
   if success:
       print("Dictionary processing completed successfully!")
   else:
       print("Dictionary processing failed!")

Read Output Tables
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   
   # Read a dictionary table
   df = pd.read_json(
       'results/data_dictionary_mappings/tblENROL/tblENROL_table.jsonl',
       lines=True
   )
   print(df.head())

Error Handling
--------------

The module handles:

1. **Missing Sheets**: Logs warning and skips
2. **Empty Sheets**: Skips silently
3. **Duplicate Columns**: Automatically renames
4. **Excel Format Errors**: Logs error and raises
5. **Write Errors**: Logs error and raises

Performance
-----------

Typical performance:

- **14 sheets**: < 1 second
- **Multiple tables per sheet**: Automatic detection
- **Memory efficient**: One sheet at a time

See Also
--------

:func:`scripts.extract_data.extract_excel_to_jsonl`
   Data extraction

:doc:`../user_guide/usage`
   Usage examples

:doc:`../developer_guide/architecture`
   Architecture details
