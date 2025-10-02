scripts.extract_data module
===========================

.. automodule:: scripts.extract_data
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``extract_data`` module converts Excel files to JSONL format with intelligent
type conversion, progress tracking, and comprehensive error handling.

Functions
---------

extract_excel_to_jsonl
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.extract_data.extract_excel_to_jsonl

Batch process all Excel files in a directory.

**Parameters**:

- ``input_dir`` (str): Directory containing Excel files
- ``output_dir`` (str): Directory for JSONL output files

**Example**:

.. code-block:: python

   from scripts.extract_data import extract_excel_to_jsonl
   
   extract_excel_to_jsonl(
       input_dir="data/dataset/Indo-vap",
       output_dir="results/dataset/Indo-vap"
   )

process_excel_file
~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.extract_data.process_excel_file

Process a single Excel file.

**Parameters**:

- ``input_file`` (str): Path to Excel file
- ``output_dir`` (str): Directory for output JSONL file

**Returns**:

- ``dict``: Processing results with keys:
  - ``records`` (int): Number of records processed
  - ``file`` (str): Output file path

**Example**:

.. code-block:: python

   from scripts.extract_data import process_excel_file
   
   result = process_excel_file(
       "data/dataset/Indo-vap/10_TST.xlsx",
       "results/dataset/Indo-vap"
   )
   print(f"Processed {result['records']} records")

convert_dataframe_to_jsonl
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.extract_data.convert_dataframe_to_jsonl

Convert a pandas DataFrame to JSONL format.

**Parameters**:

- ``df`` (pd.DataFrame): DataFrame to convert
- ``output_file`` (str): Path to output JSONL file
- ``source_file`` (str): Original source file name (for metadata)

**Example**:

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import convert_dataframe_to_jsonl
   
   df = pd.read_excel("input.xlsx")
   convert_dataframe_to_jsonl(
       df=df,
       output_file="output.jsonl",
       source_file="input.xlsx"
   )

clean_record_for_json
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.extract_data.clean_record_for_json

Clean a record for JSON serialization.

Handles:

- ``pd.Timestamp`` → string
- ``pd.NA`` / ``np.nan`` → ``None``
- ``float('nan')`` → ``None``
- Other types → preserved

**Parameters**:

- ``record`` (dict): Record to clean

**Returns**:

- ``dict``: Cleaned record

**Example**:

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import clean_record_for_json
   
   record = {
       'date': pd.Timestamp('2025-01-01'),
       'value': 42,
       'missing': pd.NA
   }
   
   cleaned = clean_record_for_json(record)
   # Result: {'date': '2025-01-01 00:00:00', 'value': 42, 'missing': None}

find_excel_files
~~~~~~~~~~~~~~~~

.. autofunction:: scripts.extract_data.find_excel_files

Find all Excel files (.xlsx) in a directory.

**Parameters**:

- ``directory`` (str): Directory to search

**Returns**:

- ``list``: List of Excel file paths (sorted)

**Example**:

.. code-block:: python

   from scripts.extract_data import find_excel_files
   
   files = find_excel_files("data/dataset/Indo-vap")
   print(f"Found {len(files)} Excel files")
   for file in files:
       print(f"  - {file}")

is_dataframe_empty
~~~~~~~~~~~~~~~~~~

.. autofunction:: scripts.extract_data.is_dataframe_empty

Check if a DataFrame is empty or contains only NaN values.

**Parameters**:

- ``df`` (pd.DataFrame): DataFrame to check

**Returns**:

- ``bool``: True if empty, False otherwise

**Example**:

.. code-block:: python

   import pandas as pd
   from scripts.extract_data import is_dataframe_empty
   
   df1 = pd.DataFrame()
   print(is_dataframe_empty(df1))  # True
   
   df2 = pd.DataFrame({'a': [1, 2, 3]})
   print(is_dataframe_empty(df2))  # False

Data Flow
---------

The extraction process follows this flow:

.. code-block:: text

   1. extract_excel_to_jsonl(input_dir, output_dir)
      │
      ├── find_excel_files(input_dir)
      │   └── Returns: [file1.xlsx, file2.xlsx, ...]
      │
      └── For each file:
          └── process_excel_file(file, output_dir)
              │
              ├── Read Excel: pd.read_excel(file)
              │
              ├── Check if empty: is_dataframe_empty(df)
              │   └── If empty: Skip file
              │
              └── convert_dataframe_to_jsonl(df, output_file, source)
                  │
                  └── For each record:
                      ├── clean_record_for_json(record)
                      │   └── Convert types for JSON
                      │
                      └── Write to JSONL file

Type Conversions
----------------

The module handles these type conversions:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Input Type
     - Output Type
     - Notes
   * - ``pd.Timestamp``
     - ``str``
     - ISO format
   * - ``pd.NA``
     - ``None``
     - Null value
   * - ``np.nan``
     - ``None``
     - Null value
   * - ``float('nan')``
     - ``None``
     - Null value
   * - ``int``, ``float``
     - Preserved
     - As-is
   * - ``str``
     - Preserved
     - As-is
   * - ``bool``
     - Preserved
     - As-is

Error Handling
--------------

The module handles these error scenarios:

1. **File Not Found**: Logs error and skips file
2. **Excel Read Error**: Logs error with details
3. **Empty DataFrame**: Skips silently (not an error)
4. **Type Conversion Error**: Logs warning, converts to None
5. **Write Error**: Logs error and raises exception

Progress Tracking
-----------------

Uses ``tqdm`` for progress bars:

- File-level progress: ``Processing files: 100%|██| 43/43 [00:15<00:00]``
- Real-time file count and processing rate
- Estimated time remaining

Performance
-----------

Typical performance:

- **43 files**: ~15-20 seconds
- **~50,000 records**: ~2-3 files/second
- **Memory usage**: One file in memory at a time

See Also
--------

:func:`scripts.load_dictionary.load_study_dictionary`
   Dictionary processing

:mod:`config`
   Configuration for paths

:doc:`../user_guide/usage`
   Usage examples
