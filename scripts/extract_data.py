#!/usr/bin/env python3
"""
Data Extraction Module
======================

This module provides comprehensive functionality for extracting raw data from Excel
files and converting them to JSONL (JSON Lines) format. It handles various data types,
performs data cleaning, and provides robust error handling.

The extraction process includes:
    - Automatic discovery of Excel files in the dataset directory
    - Smart handling of empty DataFrames (preserving column structure)
    - Type conversion for JSON serialization (NaN, datetime, numpy types)
    - Progress tracking with real-time feedback
    - Duplicate file detection to prevent reprocessing

Key Features:
    - **Type Safety**: Converts pandas/numpy types to JSON-compatible formats
    - **Empty File Handling**: Creates metadata records for files with headers but no data
    - **Progress Tracking**: Visual progress bars for batch processing
    - **Error Recovery**: Continues processing even if individual files fail
    - **Idempotent**: Skips files that have already been processed

Functions:
    clean_record_for_json: Convert pandas record to JSON-serializable format
    find_excel_files: Discover all Excel files in a directory
    is_dataframe_empty: Check if DataFrame has any data or structure
    convert_dataframe_to_jsonl: Convert DataFrame to JSONL format
    process_excel_file: Process a single Excel file
    extract_excel_to_jsonl: Main extraction function for batch processing

Example:
    Run extraction as a standalone script::

        $ python -m scripts.extract_data

    Or import and use programmatically::

        from scripts.extract_data import extract_excel_to_jsonl
        extract_excel_to_jsonl()

See Also:
    :mod:`scripts.load_dictionary`: Data dictionary processing
    :mod:`config`: Configuration and path settings

Author:
    RePORTaLiN Development Team

Version:
    0.0.1
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm
import config
import re

def clean_record_for_json(record: dict) -> dict:
    """
    Clean a pandas record by converting values to JSON-serializable types.

    This function handles the conversion of pandas/numpy-specific data types
    to standard Python types that can be serialized to JSON. It's essential
    for preventing serialization errors when writing to JSONL files.

    Type conversions performed:
        - ``pd.isna()`` values → ``None``
        - ``np.integer`` / ``np.floating`` → Python ``int`` / ``float``
        - ``pd.Timestamp`` / ``np.datetime64`` / ``datetime`` / ``date`` → ``str``
        - All other types preserved as-is

    Args:
        record (dict): A dictionary containing data from a pandas DataFrame row,
            potentially with pandas/numpy types.

    Returns:
        dict: A new dictionary with all values converted to JSON-serializable types.

    Example:
        >>> import pandas as pd
        >>> import numpy as np
        >>> record = {
        ...     'name': 'John',
        ...     'age': np.int64(30),
        ...     'score': np.float64(95.5),
        ...     'date': pd.Timestamp('2023-01-01'),
        ...     'missing': np.nan
        ... }
        >>> cleaned = clean_record_for_json(record)
        >>> cleaned
        {'name': 'John', 'age': 30, 'score': 95.5, 'date': '2023-01-01 00:00:00', 'missing': None}

    Note:
        - NaN and None values are converted to JSON ``null``
        - Datetime objects are converted to ISO format strings
        - The original record is not modified (a new dict is returned)
    """
    cleaned = {}
    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = None
        elif isinstance(value, (np.integer, np.floating)):
            cleaned[key] = value.item()
        elif isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
            cleaned[key] = str(value)
        else:
            cleaned[key] = value
    return cleaned

def find_excel_files(directory: str) -> List[Path]:
    """
    Find all Excel files (.xlsx) in the specified directory.

    This function searches for Excel files with the .xlsx extension in a given
    directory. It does not search subdirectories (non-recursive).

    Args:
        directory (str): Path to the directory to search for Excel files.

    Returns:
        List[Path]: A list of Path objects representing found Excel files.
            Returns an empty list if no files are found.

    Example:
        >>> files = find_excel_files('data/dataset/Indo-vap_csv_files')
        >>> print(f"Found {len(files)} files")
        Found 43 files
        >>> print(files[0].name)
        '10_TST.xlsx'

    Note:
        - Only searches the immediate directory (not subdirectories)
        - Only matches .xlsx files (not .xls or other Excel formats)
        - Files are returned in the order found by the file system
    """
    return list(Path(directory).glob("*.xlsx"))


def is_dataframe_empty(df: pd.DataFrame) -> bool:
    """
    Check if a DataFrame is completely empty (no rows AND no columns).

    This function distinguishes between DataFrames that have structure (columns)
    but no data rows, versus DataFrames that are completely empty. This is
    important for deciding whether to preserve column metadata.

    Args:
        df (pd.DataFrame): The DataFrame to check.

    Returns:
        bool: True if the DataFrame has no columns AND no rows, False otherwise.

    Example:
        >>> import pandas as pd
        >>> # Completely empty DataFrame
        >>> df1 = pd.DataFrame()
        >>> is_dataframe_empty(df1)
        True
        
        >>> # Has columns but no rows
        >>> df2 = pd.DataFrame(columns=['A', 'B', 'C'])
        >>> is_dataframe_empty(df2)
        False
        
        >>> # Has data
        >>> df3 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> is_dataframe_empty(df3)
        False

    Note:
        - A DataFrame with columns but no rows returns False (has structure)
        - Only returns True when both rows and columns are absent
    """
    return len(df.columns) == 0 and len(df) == 0


def convert_dataframe_to_jsonl(df: pd.DataFrame, output_file: Path, source_filename: str) -> int:
    """
    Convert a DataFrame to JSONL (JSON Lines) format.

    This function writes each row of a DataFrame as a separate JSON object on
    its own line, creating a JSONL file. It handles empty DataFrames gracefully
    by creating metadata records.

    Special Cases:
        - **Empty DataFrame with columns**: Creates a single metadata record with
          column names and null values, preserving the data structure.
        - **DataFrame with data**: Converts each row to a JSON object with the
          source filename added.

    Args:
        df (pd.DataFrame): The DataFrame to convert. Can be empty.
        output_file (Path): Path where the JSONL file will be written.
        source_filename (str): Name of the source Excel file, added to each record
            for traceability.

    Returns:
        int: The number of JSON records written to the file.

    Example:
        >>> import pandas as pd
        >>> from pathlib import Path
        >>> 
        >>> df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
        >>> output = Path('output.jsonl')
        >>> count = convert_dataframe_to_jsonl(df, output, 'data.xlsx')
        >>> print(f"Wrote {count} records")
        Wrote 2 records

    Note:
        - Each line in the output file is a valid JSON object
        - Files are written with UTF-8 encoding
        - The ``source_file`` field is automatically added to each record
        - Empty DataFrames with columns generate one metadata record
    
    See Also:
        :func:`clean_record_for_json`: Function used to clean each record
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        if len(df) == 0 and len(df.columns) > 0:
            record = {col: None for col in df.columns}
            record.update({"source_file": source_filename, "_metadata": {
                "type": "column_structure", "columns": list(df.columns),
                "note": "File contains column headers but no data rows"}})
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            return 1
        
        records = 0
        for _, row in df.iterrows():
            record = clean_record_for_json(row.to_dict())
            record["source_file"] = source_filename
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            records += 1
        return records


def process_excel_file(excel_file: Path, output_dir: str) -> Tuple[bool, int, Optional[str]]:
    """
    Process a single Excel file and convert it to JSONL format.

    This function reads an Excel file, checks if it's empty, and converts it to
    JSONL format if it contains data or structure. It creates both original and
    cleaned versions, where the cleaned version removes duplicate columns.

    Processing Steps:
        1. Determine output file paths (original and cleaned)
        2. Read Excel file into DataFrame
        3. Check if DataFrame is completely empty
        4. Save original version to JSONL
        5. Remove duplicate columns (SUBJID2, SUBJID3, etc.)
        6. Save cleaned version to JSONL with "_cleaned" suffix
        7. Report results or errors

    Args:
        excel_file (Path): Path object pointing to the Excel file to process.
        output_dir (str): Directory where both original and cleaned JSONL files will be saved.

    Returns:
        Tuple[bool, int, Optional[str]]: A tuple containing:
            - **success** (bool): True if processing succeeded, False otherwise
            - **record_count** (int): Number of records written (0 if failed/skipped)
            - **error_message** (Optional[str]): Error description if failed, None otherwise

    Example:
        >>> from pathlib import Path
        >>> excel_file = Path('data/10_TST.xlsx')
        >>> success, count, error = process_excel_file(excel_file, 'results/')
          ✓ Created 10_TST.jsonl with 150 rows (original)
            → Removing duplicate columns: SUBJID2, SUBJID3
          ✓ Created clean_10_TST.jsonl with 150 rows (cleaned)
        >>> print(f"Success: {success}, Records: {count}")
        Success: True, Records: 150

    Error Handling:
        - Empty files are skipped with a warning (not treated as errors)
        - Excel reading errors are caught and returned as error messages
        - All errors are logged to both console and log file

    Note:
        - Original output filename: ``<filename>.jsonl``
        - Cleaned output filename: ``clean_<filename>.jsonl``
        - Progress messages are written via tqdm for proper formatting
        - Empty DataFrames (no columns and no rows) are skipped entirely
        - Duplicate columns like SUBJID2, SUBJID3 are removed in cleaned version

    See Also:
        :func:`convert_dataframe_to_jsonl`: Conversion function
        :func:`is_dataframe_empty`: Empty file detection
        :func:`clean_duplicate_columns`: Duplicate column removal
    """
    try:
        output_file = Path(output_dir) / f"{excel_file.stem}.jsonl"
        output_file_cleaned = Path(output_dir) / f"clean_{excel_file.stem}.jsonl"
        
        df = pd.read_excel(excel_file)
        if is_dataframe_empty(df):
            tqdm.write(f"  ⊘ Skipping {excel_file.name} (empty)")
            return False, 0, None
        
        # Save original version
        records_count = convert_dataframe_to_jsonl(df, output_file, excel_file.name)
        tqdm.write(f"  ✓ Created {output_file.name} with {records_count} rows (original)")
        
        # Clean duplicate columns like SUBJID2, SUBJID3, etc. and save cleaned version
        df_cleaned = clean_duplicate_columns(df)
        records_count_cleaned = convert_dataframe_to_jsonl(df_cleaned, output_file_cleaned, excel_file.name)
        tqdm.write(f"  ✓ Created {output_file_cleaned.name} with {records_count_cleaned} rows (cleaned)")
        
        return True, records_count, None
    except Exception as e:
        error_msg = f"Error processing {excel_file.name}: {str(e)}"
        tqdm.write(f"  ✗ {error_msg}")
        return False, 0, error_msg


def clean_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate columns that end with numeric suffixes (e.g., SUBJID2, SUBJID3).
    
    This function identifies columns that appear to be duplicates based on naming
    patterns where a base column name is followed by a numeric suffix (e.g., 
    SUBJID, SUBJID2, SUBJID3). It keeps only the base column and removes the
    numbered variants.
    
    Detection Pattern:
        - Looks for columns ending with a number (e.g., "SUBJID2", "ID3", "NAME_1")
        - Checks if the base name (without the number) exists as a column
        - Removes the numbered column if the base exists
    
    Args:
        df (pd.DataFrame): The DataFrame with potentially duplicate columns.
    
    Returns:
        pd.DataFrame: A new DataFrame with duplicate columns removed.
    
    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'SUBJID': ['A001', 'A002'],
        ...     'SUBJID2': ['A001', 'A002'],
        ...     'SUBJID3': ['A001', 'A002'],
        ...     'NAME': ['John', 'Jane']
        ... })
        >>> cleaned_df = clean_duplicate_columns(df)
        >>> list(cleaned_df.columns)
        ['SUBJID', 'NAME']
    
    Note:
        - The original DataFrame is not modified
        - Removes columns like: SUBJID2, SUBJID3, VAR_1, VAR_2, etc.
        - Keeps the base column name without suffix
        - Case-sensitive matching
    """
    columns_to_keep = []
    columns_to_remove = []
    
    for col in df.columns:
        # Check if column ends with a number (e.g., SUBJID2, SUBJID3, VAR_1)
        match = re.match(r'^(.+?)_?(\d+)$', str(col))
        if match:
            base_name = match.group(1)
            # If the base column exists, this is a duplicate
            if base_name in df.columns:
                columns_to_remove.append(col)
                continue
        columns_to_keep.append(col)
    
    if columns_to_remove:
        tqdm.write(f"    → Removing duplicate columns: {', '.join(columns_to_remove)}")
    
    return df[columns_to_keep].copy()


def extract_excel_to_jsonl():
    """
    Extract all Excel files from the dataset directory and convert to JSONL format.

    This is the main batch processing function that orchestrates the extraction
    of multiple Excel files. It creates both original and cleaned versions of each file.
    The cleaned version has duplicate columns (like SUBJID2, SUBJID3) removed.

    Workflow:
        1. Create output directory if it doesn't exist
        2. Discover all Excel files in the dataset directory
        3. Process each file (skipping already-processed files)
        4. Save both original and cleaned versions
        5. Track statistics (records, successes, failures)
        6. Display comprehensive summary report

    Features:
        - **Dual Output**: Creates both original and cleaned versions
        - **Idempotent**: Skips files that already have output files
        - **Progress Tracking**: Visual progress bar with real-time updates
        - **Error Recovery**: Continues processing even if individual files fail
        - **Summary Statistics**: Detailed report of processing results
        - **Duplicate Removal**: Cleaned versions remove columns like SUBJID2, SUBJID3

    Configuration:
        Uses the following config variables:
            - ``config.CLEAN_DATASET_DIR``: Output directory for JSONL files
            - ``config.DATASET_DIR``: Input directory containing Excel files

    Output Format:
        Each Excel file ``filename.xlsx`` produces two JSONL files:
            - ``filename.jsonl`` - Original data with all columns
            - ``clean_filename.jsonl`` - Data with duplicate columns removed

    Example:
        Run as part of the main pipeline::

            from scripts.extract_data import extract_excel_to_jsonl
            extract_excel_to_jsonl()

        Output::

            Found 43 Excel files to process...
            Processing files: 100%|██████████| 43/43 [00:15<00:00, 2.87file/s]
            
            Extraction complete:
              - 15,234 total records processed
              - 42 JSONL files created
              - 1 file skipped (already exists)
              - Output directory: results/dataset/Indo-vap

    Returns:
        None

    Note:
        - Creates ``config.CLEAN_DATASET_DIR`` automatically if missing
        - Skips processing if output file already exists (prevents duplicates)
        - All errors are logged but don't stop the entire batch process
        - Empty files (no columns/rows) are skipped with a warning

    See Also:
        :func:`process_excel_file`: Single file processing function
        :func:`find_excel_files`: Excel file discovery
        :mod:`config`: Configuration settings
    """
    os.makedirs(config.CLEAN_DATASET_DIR, exist_ok=True)
    excel_files = find_excel_files(config.DATASET_DIR)
    
    if not excel_files:
        print(f"No Excel files found in {config.DATASET_DIR}")
        return
    
    print(f"Found {len(excel_files)} Excel files to process...")
    total_records, files_created, files_skipped, errors = 0, 0, 0, []
    
    for excel_file in tqdm(excel_files, desc="Processing files", unit="file"):
        output_file = Path(config.CLEAN_DATASET_DIR) / f"{excel_file.stem}.jsonl"
        
        # Check if file already exists before processing
        if output_file.exists():
            files_skipped += 1
            tqdm.write(f"  ⊙ Skipping {excel_file.name} (output already exists)")
            continue
            
        print(f"Processing: {excel_file.name}")
        success, records_count, error_msg = process_excel_file(excel_file, config.CLEAN_DATASET_DIR)
        if success:
            files_created += 1
            total_records += records_count
        elif error_msg:
            errors.append(error_msg)
    
    print(f"\nExtraction complete:")
    print(f"  - {total_records} total records processed")
    print(f"  - {files_created} JSONL files created")
    print(f"  - {files_skipped} files skipped (already exist)")
    print(f"  - Output directory: {config.CLEAN_DATASET_DIR}")
    if errors:
        print(f"  - {len(errors)} files had errors")


if __name__ == "__main__":
    extract_excel_to_jsonl()
