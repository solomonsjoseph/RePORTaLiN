"""
Data Dictionary Loader Module
==============================

This module provides sophisticated functionality for processing data dictionary
Excel files. It intelligently splits Excel sheets into multiple tables based on
structural boundaries (empty rows/columns) and saves them in JSONL format.

The module is specifically designed to handle complex Excel layouts commonly found
in medical research data dictionaries, including:
    - Multiple tables within a single sheet
    - Tables separated by empty rows or columns
    - Special "ignore below" markers for excluding extraneous content
    - Duplicate column names requiring disambiguation

Key Features:
    - **Automatic Table Detection**: Splits sheets into logical tables
    - **Smart Column Handling**: Deduplicates column names automatically
    - **Content Filtering**: Supports "ignore below" markers
    - **Metadata Preservation**: Tracks sheet and table provenance
    - **Progress Tracking**: Visual feedback for multi-sheet processing

Architecture:
    The processing pipeline consists of:
    
    1. **Sheet Reading**: Load Excel sheets without assuming structure
    2. **Table Detection**: Identify logical tables using empty boundaries
    3. **Column Deduplication**: Make column names unique
    4. **Content Filtering**: Apply "ignore below" rules
    5. **JSONL Export**: Save tables with metadata

Functions:
    _deduplicate_columns: Make column names unique
    _split_sheet_into_tables: Split DataFrame into multiple tables
    _process_and_save_tables: Process and save table with metadata
    process_excel_file: Main Excel processing function
    load_study_dictionary: High-level API for dictionary loading

Example:
    Load a data dictionary::

        from scripts.load_dictionary import load_study_dictionary
        load_study_dictionary(
            file_path='data/dictionary.xlsx',
            json_output_dir='results/dictionary/'
        )

See Also:
    :mod:`scripts.extract_data`: Data extraction module
    :mod:`config`: Configuration management

Author:
    RePORTaLiN Development Team

Version:
    1.0.0
"""

import pandas as pd
import os, sys
from tqdm import tqdm

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from scripts.utils import logging_utils as log
import config

def _deduplicate_columns(columns):
    """
    Make column names unique by appending numeric suffixes to duplicates.

    This function ensures all column names in a DataFrame are unique by tracking
    duplicate names and adding incremental suffixes (_1, _2, etc.). This is
    essential for proper JSON serialization where keys must be unique.

    Algorithm:
        - First occurrence: Keep original name
        - Second occurrence: Append "_1"
        - Third occurrence: Append "_2"
        - And so on...

    Args:
        columns (list): A list of column names, potentially containing duplicates.
            Can include None or NaN values which are converted to "Unnamed".

    Returns:
        list: A new list with all column names made unique through suffixing.

    Example:
        >>> cols = ['ID', 'Value', 'Value', None, 'ID', 'Value']
        >>> _deduplicate_columns(cols)
        ['ID', 'Value', 'Value_1', 'Unnamed', 'ID_1', 'Value_2']

    Note:
        - None and NaN values are converted to "Unnamed"
        - Original column names are not modified
        - Suffixes start at 1 (not 0) for the first duplicate
    """
    new_cols, counts = [], {}
    for col in columns:
        col_str = str(col) if pd.notna(col) else "Unnamed"
        if col_str in counts:
            counts[col_str] += 1
            new_cols.append(f"{col_str}_{counts[col_str]}")
        else:
            new_cols.append(col_str)
            counts[col_str] = 0
    return new_cols

def _split_sheet_into_tables(df):
    """
    Split a DataFrame into multiple tables based on empty row/column boundaries.

    This function implements a two-phase algorithm to detect and extract multiple
    logical tables from a single Excel sheet:

    1. **Horizontal Split**: Divide sheet into horizontal strips using empty rows
    2. **Vertical Split**: Within each strip, divide into tables using empty columns

    This approach handles complex layouts where multiple tables are arranged both
    vertically and horizontally within a single sheet.

    Algorithm:
        Phase 1 - Horizontal Splitting:
            - Identify rows where all cells are empty/null
            - Split DataFrame at these boundaries into horizontal strips
            
        Phase 2 - Vertical Splitting:
            - For each horizontal strip, identify empty columns
            - Split strip at these boundaries into individual tables
            
        Phase 3 - Cleanup:
            - Remove completely empty tables
            - Remove rows that are all null

    Args:
        df (pd.DataFrame): The input DataFrame representing a complete Excel sheet.
            Should have header=None (raw data without assuming first row is header).

    Returns:
        list[pd.DataFrame]: A list of DataFrames, each representing a distinct
            table found in the original sheet. Returns empty list if no tables found.

    Example:
        >>> import pandas as pd
        >>> # Sheet with two tables separated by empty row
        >>> data = [[1, 2, None, 'A', 'B'],
        ...         [3, 4, None, 'C', 'D'],
        ...         [None, None, None, None, None],  # separator
        ...         [5, 6, None, 'E', 'F']]
        >>> df = pd.DataFrame(data)
        >>> tables = _split_sheet_into_tables(df)
        >>> len(tables)
        2

    Note:
        - Empty tables (all null values) are automatically removed
        - Each resulting table is a copy (not a view) of the original data
        - Tables preserve their relative row ordering from the original sheet
    
    See Also:
        :func:`_process_and_save_tables`: Function that processes these tables
    """
    empty_rows = df.index[df.isnull().all(axis=1)].tolist()
    row_boundaries = [-1] + empty_rows + [df.shape[0]]
    horizontal_strips = [df.iloc[row_boundaries[i]+1:row_boundaries[i+1]] 
                        for i in range(len(row_boundaries)-1) if row_boundaries[i]+1 < row_boundaries[i+1]]
    
    all_tables = []
    for strip in horizontal_strips:
        empty_col_indices = [i for i, col in enumerate(strip.columns) if strip[col].isnull().all()]
        col_boundaries = [-1] + empty_col_indices + [len(strip.columns)]
        for j in range(len(col_boundaries)-1):
            start_col, end_col = col_boundaries[j]+1, col_boundaries[j+1]
            if start_col < end_col:
                table_df = strip.iloc[:, start_col:end_col].copy()
                table_df.dropna(how='all', inplace=True)
                if not table_df.empty:
                    all_tables.append(table_df)
    return all_tables

def _process_and_save_tables(all_tables, sheet_name, output_dir):
    """
    Process detected tables and save them to JSONL files with metadata.

    This function handles the post-processing of tables extracted from an Excel
    sheet, including column naming, filtering, metadata addition, and file saving.

    Processing Steps:
        1. Create output directory based on sanitized sheet name
        2. For each table:
            - Set first row as column headers
            - Deduplicate column names
            - Check for "ignore below" markers
            - Add metadata fields (__sheet__, __table__)
            - Save to JSONL format

    Special Features:
        - **"Ignore Below" Support**: When a cell contains "ignore below" (case-insensitive),
          that column is removed and all subsequent tables are saved to an "extraas"
          subdirectory as excluded content.
        - **Smart Naming**: Table filenames include sheet name and table index
        - **Duplicate Prevention**: Skips saving if output file already exists

    Args:
        all_tables (list[pd.DataFrame]): List of tables extracted from a sheet.
        sheet_name (str): Name of the Excel sheet these tables came from.
        output_dir (str): Base output directory for saving JSONL files.

    Returns:
        None

    Output Structure:
        Normal tables::
        
            output_dir/
                SheetName/
                    SheetName_table_1.jsonl
                    SheetName_table_2.jsonl

        Ignored tables (after "ignore below" marker)::
        
            output_dir/
                SheetName/
                    extraas/
                        extraas_table_3.jsonl

    Example:
        >>> tables = [df1, df2, df3]
        >>> _process_and_save_tables(tables, "tblENROL", "results/dictionary/")
        INFO: Saved 25 rows → 'results/dictionary/tblENROL/tblENROL_table_1.jsonl'
        INFO: Saved 10 rows → 'results/dictionary/tblENROL/tblENROL_table_2.jsonl'

    Note:
        - Empty tables (after header row removal) are skipped
        - Each record includes ``__sheet__`` and ``__table__`` metadata fields
        - Files are saved in JSONL format (one JSON object per line)
        - "ignore below" mode persists for all subsequent tables

    See Also:
        :func:`_deduplicate_columns`: Column name deduplication
        :func:`_split_sheet_into_tables`: Table detection function
    """
    folder_name = "".join(c for c in sheet_name if c.isalnum() or c in "._- ").strip()
    sheet_dir = os.path.join(output_dir, folder_name)
    os.makedirs(sheet_dir, exist_ok=True)
    ignore_mode = False
    
    for i, table_df in enumerate(all_tables):
        table_df.reset_index(drop=True, inplace=True)
        
        if not ignore_mode:
            for idx, col in enumerate(table_df.iloc[0]):
                if "ignore below" in str(col).lower().strip():
                    log.info(f"'ignore below' found in table {i+1}. Subsequent → 'extraas'.")
                    ignore_mode = True
                    table_df = table_df.drop(table_df.columns[idx], axis=1)
                    break
        
        table_df.columns = _deduplicate_columns(table_df.iloc[0])
        table_df = table_df.iloc[1:].reset_index(drop=True)
        if table_df.empty:
            continue
        
        table_suffix = f"_table_{i+1}" if len(all_tables) > 1 else "_table"
        if ignore_mode:
            extraas_dir = os.path.join(sheet_dir, "extraas")
            os.makedirs(extraas_dir, exist_ok=True)
            table_name, metadata_name = f"extraas{table_suffix}", f"{folder_name}_extraas{table_suffix}"
            output_path = os.path.join(extraas_dir, f"{table_name}.jsonl")
        else:
            table_name = metadata_name = f"{folder_name}{table_suffix}"
            output_path = os.path.join(sheet_dir, f"{table_name}.jsonl")
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            log.warning(f"File exists. Skipping: {output_path}")
            continue
        
        table_df['__sheet__'], table_df['__table__'] = sheet_name, metadata_name
        table_df.to_json(output_path, orient='records', lines=True, force_ascii=False)
        log.info(f"Saved {len(table_df)} rows → '{output_path}'")

def process_excel_file(excel_path, output_dir, preserve_na=True):
    """
    Extract all tables from an Excel file and save them as JSONL files.

    This is the main processing function that coordinates the entire data dictionary
    extraction workflow. It handles multi-sheet Excel files and processes each sheet
    independently with comprehensive error handling.

    Workflow:
        1. Validate input file exists
        2. Create output directory structure
        3. Open Excel file
        4. For each sheet:
            - Read sheet data (without assuming header structure)
            - Split into logical tables
            - Process and save each table
        5. Report completion status

    Args:
        excel_path (str): Path to the input Excel file to process.
        output_dir (str): Directory where JSONL files will be saved. Created if
            it doesn't exist.
        preserve_na (bool, optional): If True, uses special pandas settings to
            better preserve NA/null values. Default is True.

    Returns:
        None: Logs success/failure but returns nothing.

    Raises:
        Logs errors but does not raise exceptions. Processing continues even if
        individual sheets fail.

    Example:
        >>> process_excel_file(
        ...     excel_path='data/dictionary.xlsx',
        ...     output_dir='results/dictionary/',
        ...     preserve_na=True
        ... )
        INFO: Processing: 'data/dictionary.xlsx'
        Processing sheets: 100%|██████████| 14/14 [00:02<00:00,  5.23sheet/s]
        SUCCESS: Excel processing complete!

    Output Structure:
        For an Excel file with sheets "Sheet1" and "Sheet2"::
        
            output_dir/
                Sheet1/
                    Sheet1_table.jsonl
                Sheet2/
                    Sheet2_table_1.jsonl
                    Sheet2_table_2.jsonl

    Note:
        - Handles multiple sheets automatically
        - Each sheet can contain multiple tables
        - Progress bar shows real-time sheet processing
        - Individual sheet failures don't stop processing of other sheets
        - All operations are logged to both file and console

    See Also:
        :func:`_split_sheet_into_tables`: Table detection
        :func:`_process_and_save_tables`: Table processing and saving
        :func:`load_study_dictionary`: High-level wrapper function
    """
    if not os.path.exists(excel_path):
        return log.error(f"Input file not found: {excel_path}")
    
    log.info(f"Output → '{output_dir}'")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        return log.error(f"Failed to read Excel: {e}")
    
    log.info(f"Processing: '{excel_path}'")
    for sheet_name in tqdm(xls.sheet_names, desc="Processing sheets", unit="sheet"):
        try:
            log.info(f"--- Sheet: '{sheet_name}' ---")
            parse_opts = {'header': None, 'keep_default_na': False, 'na_values': ['']} if preserve_na else {'header': None}
            all_tables = _split_sheet_into_tables(pd.read_excel(xls, sheet_name=sheet_name, **parse_opts))
            if not all_tables:
                log.info("No tables found.")
            else:
                log.info(f"Found {len(all_tables)} table(s).")
                _process_and_save_tables(all_tables, sheet_name, output_dir)
        except Exception as e:
            log.error(f"Error on sheet '{sheet_name}': {e}", exc_info=True)
    log.success("Excel processing complete!")

def load_study_dictionary(file_path=None, json_output_dir=None, preserve_na=True):
    """
    Load and process a study data dictionary from Excel to JSONL format.

    This is the high-level API function for data dictionary processing. It provides
    a simple interface with sensible defaults from the configuration module.

    This function is the recommended entry point for dictionary processing as it:
        - Uses configuration defaults when arguments are not provided
        - Provides a clean, simple API
        - Returns a boolean success indicator
        - Integrates seamlessly with the main pipeline

    Args:
        file_path (str, optional): Path to the data dictionary Excel file.
            If None, uses ``config.DICTIONARY_EXCEL_FILE``. Default is None.
        json_output_dir (str, optional): Output directory for JSONL files.
            If None, uses ``config.DICTIONARY_JSON_OUTPUT_DIR``. Default is None.
        preserve_na (bool, optional): Whether to preserve NA values with special
            pandas settings. Default is True.

    Returns:
        bool: Always returns True on completion (errors are logged, not raised).

    Example:
        Use with defaults from config::

            from scripts.load_dictionary import load_study_dictionary
            load_study_dictionary()

        Use with custom paths::

            load_study_dictionary(
                file_path='custom/dictionary.xlsx',
                json_output_dir='custom/output/',
                preserve_na=True
            )

        Use in main pipeline::

            from scripts.load_dictionary import load_study_dictionary
            import config
            
            success = load_study_dictionary(
                config.DICTIONARY_EXCEL_FILE,
                config.DICTIONARY_JSON_OUTPUT_DIR
            )

    Configuration:
        When arguments are None, uses these config variables:
            - ``config.DICTIONARY_EXCEL_FILE``: Default input Excel file
            - ``config.DICTIONARY_JSON_OUTPUT_DIR``: Default output directory

    Note:
        - This function wraps :func:`process_excel_file` with config defaults
        - Always returns True (check logs for actual success/failure)
        - Creates output directory if it doesn't exist
        - Suitable for use as a pipeline step

    See Also:
        :func:`process_excel_file`: Lower-level processing function
        :mod:`config`: Configuration settings
        :mod:`main`: Main pipeline orchestration
    """
    process_excel_file(
        excel_path=file_path or config.DICTIONARY_EXCEL_FILE,
        output_dir=json_output_dir or config.DICTIONARY_JSON_OUTPUT_DIR,
        preserve_na=preserve_na
    )
    return True

if __name__ == "__main__":
    load_study_dictionary(preserve_na=True)
    log.success(f"Processing complete for data dictionary from {config.DICTIONARY_EXCEL_FILE}")
