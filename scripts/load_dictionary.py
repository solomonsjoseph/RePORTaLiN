"""
Data Dictionary Loader Module
==============================

Processes data dictionary Excel files, intelligently splitting sheets into multiple 
tables based on structural boundaries and saving in JSONL format.

This module provides intelligent table detection and extraction from complex Excel
layouts, automatically handling multi-table sheets, "ignore below" markers, and
duplicate column naming.

Public API
----------
The module exports 2 main functions via ``__all__``:

- ``load_study_dictionary``: High-level function to process dictionary files
- ``process_excel_file``: Low-level function for custom processing workflows

Key Features
------------
- **Multi-table Detection**: Automatically splits sheets with multiple tables
- **Boundary Detection**: Uses empty rows/columns to identify table boundaries
- **"Ignore Below" Support**: Handles special markers to segregate extra tables
- **Duplicate Column Handling**: Automatically deduplicates column names
- **Progress Tracking**: Real-time progress bars
- **Verbose Logging**: Detailed tree-view logs with timing (v0.0.12+)
- **Metadata Injection**: Adds ``__sheet__`` and ``__table__`` fields

Verbose Mode
------------
When running with ``--verbose`` flag, detailed logs are generated including
sheet-by-sheet processing, table detection results (rows/columns), "ignore below"
marker detection, and timing for sheets, tables, and overall processing.

Table Detection Algorithm
-------------------------
The module uses a sophisticated algorithm to detect tables:

1. Identify horizontal strips (separated by empty rows)
2. Within each strip, identify vertical sections (separated by empty columns)
3. Extract each non-empty section as a separate table
4. Deduplicate column names by appending numeric suffixes
5. Check for "ignore below" markers and segregate subsequent tables
6. Add metadata fields and save to JSONL

See Also
--------
- :doc:`../user_guide/usage` - Usage and detailed tutorials
- :func:`load_study_dictionary` - High-level dictionary processing function
- :func:`process_excel_file` - Low-level custom processing
- :mod:`scripts.extract_data` - For dataset extraction
"""

__all__ = ['load_study_dictionary', 'process_excel_file']

import pandas as pd
import os
import sys
import time
from typing import List, Optional
from tqdm import tqdm
from scripts.utils import logging_system as log
import config

vlog = log.get_verbose_logger()

# Constants for table processing
IGNORE_BELOW_MARKER = "ignore below"
EXTRA_TABLES_DIR = "extras"
UNNAMED_COLUMN_PREFIX = "Unnamed"
METADATA_SHEET_KEY = "__sheet__"
METADATA_TABLE_KEY = "__table__"

def _deduplicate_columns(columns) -> List[str]:
    """
    Make column names unique by appending numeric suffixes to duplicates.
    
    Args:
        columns: List of column names (may contain duplicates or NaN values)
        
    Returns:
        List of unique column names with numeric suffixes where needed
    """
    new_cols, counts = [], {}
    for col in columns:
        col_str = str(col) if pd.notna(col) else UNNAMED_COLUMN_PREFIX
        if col_str in counts:
            counts[col_str] += 1
            new_cols.append(f"{col_str}_{counts[col_str]}")
        else:
            new_cols.append(col_str)
            counts[col_str] = 0
    return new_cols

def _split_sheet_into_tables(df: pd.DataFrame) -> List[pd.DataFrame]:
    """
    Split DataFrame into multiple tables based on empty row/column boundaries.
    
    This function uses empty rows and columns as natural boundaries to detect and
    extract separate tables from a complex Excel sheet layout.
    
    Args:
        df: DataFrame to split into separate tables
        
    Returns:
        List of DataFrames, each representing a detected table. Returns empty list
        if the input DataFrame is empty or if structural errors occur during processing.
    
    Note:
        - Handles KeyError and IndexError gracefully by returning empty list
        - Logs detailed debug information for troubleshooting
        - Empty DataFrames are filtered out from results
    """
    try:
        if df.empty:
            log.debug("Received empty DataFrame, returning empty table list")
            return []
        
        log.debug(f"Analyzing DataFrame with shape {df.shape} for table boundaries")
        
        empty_rows = df.index[df.isnull().all(axis=1)].tolist()
        row_boundaries = [-1] + empty_rows + [df.shape[0]]
        horizontal_strips = [df.iloc[row_boundaries[i]+1:row_boundaries[i+1]] 
                            for i in range(len(row_boundaries)-1) if row_boundaries[i]+1 < row_boundaries[i+1]]
        
        log.debug(f"Found {len(horizontal_strips)} horizontal strip(s)")
        
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
        
        log.debug(f"Detected {len(all_tables)} table(s) from DataFrame")
        return all_tables
        
    except (KeyError, IndexError) as e:
        log.error(f"DataFrame structure error during table splitting: {e}")
        log.debug("DataFrame info:", exc_info=True)
        return []  # Return empty list instead of crashing
    except Exception as e:
        log.error(f"Unexpected error splitting DataFrame into tables: {type(e).__name__}: {e}")
        log.debug("Full error details:", exc_info=True)
        return []

def _process_and_save_tables(all_tables: List[pd.DataFrame], sheet_name: str, output_dir: str) -> None:
    """
    Process detected tables, apply filters, add metadata, and save to JSONL files.
    
    This function handles the complete workflow of processing tables including:
    - Creating output directories (with error handling)
    - Detecting "ignore below" markers and segregating extra tables to 'extras' subdirectory
    - Deduplicating column names
    - Adding metadata fields (__sheet__ and __table__)
    - Writing JSONL files with comprehensive error handling
    
    Args:
        all_tables: List of DataFrames representing detected tables
        sheet_name: Name of the Excel sheet being processed
        output_dir: Directory where JSONL files will be saved
    
    Note:
        - Gracefully handles directory creation failures (OSError, PermissionError)
        - Continues processing remaining tables if individual table errors occur
        - Validates table row counts before processing to prevent IndexError
        - Handles file write errors (IOError, OSError, PermissionError) without stopping
        - Skips empty tables and existing files automatically
        - Uses verbose logging when enabled for detailed progress tracking
    """
    folder_name = "".join(c for c in sheet_name if c.isalnum() or c in "._- ").strip()
    sheet_dir = os.path.join(output_dir, folder_name)
    
    try:
        os.makedirs(sheet_dir, exist_ok=True)
        log.debug(f"Created/verified sheet directory: '{sheet_dir}'")
    except (OSError, PermissionError) as e:
        log.error(f"Cannot create directory '{sheet_dir}': {e}")
        return  # Cannot proceed without directory
    except Exception as e:
        log.error(f"Unexpected error creating directory '{sheet_dir}': {e}")
        return
    
    log.debug(f"Processing {len(all_tables)} tables from sheet '{sheet_name}'")
    ignore_mode = False
    
    for i, table_df in enumerate(all_tables):
        table_start = time.time()
        
        table_df.reset_index(drop=True, inplace=True)
        
        # Validate table has rows before accessing
        if len(table_df) == 0:
            log.warning(f"Table {i+1} from sheet '{sheet_name}' is empty after reset. Skipping.")
            continue
        
        if not ignore_mode:
            for idx, col in enumerate(table_df.iloc[0]):
                if IGNORE_BELOW_MARKER in str(col).lower().strip():
                    log.info(f"'{IGNORE_BELOW_MARKER}' found in table {i+1}. Subsequent → '{EXTRA_TABLES_DIR}'.")
                    vlog.detail(f"'{IGNORE_BELOW_MARKER}' found in table {i+1}. Subsequent → '{EXTRA_TABLES_DIR}'.")
                    ignore_mode = True
                    table_df = table_df.drop(table_df.columns[idx], axis=1)
                    break
        
        try:
            table_df.columns = _deduplicate_columns(table_df.iloc[0])
            table_df = table_df.iloc[1:].reset_index(drop=True)
        except IndexError as e:
            log.error(f"Cannot process table {i+1} from sheet '{sheet_name}': Index error - {e}")
            continue
        
        if table_df.empty:
            log.debug(f"Table {i+1} from sheet '{sheet_name}' is empty after removing header row. Skipping.")
            continue
        
        table_suffix = f"_table_{i+1}" if len(all_tables) > 1 else "_table"
        if ignore_mode:
            extras_dir = os.path.join(sheet_dir, EXTRA_TABLES_DIR)
            try:
                os.makedirs(extras_dir, exist_ok=True)
                log.debug(f"Created/verified extras directory: '{extras_dir}'")
            except (OSError, PermissionError) as e:
                log.error(f"Cannot create extras directory '{extras_dir}': {e}")
                continue  # Skip this table, try next one
            except Exception as e:
                log.error(f"Unexpected error creating extras directory '{extras_dir}': {e}")
                continue
            
            table_name, metadata_name = f"{EXTRA_TABLES_DIR}{table_suffix}", f"{folder_name}_{EXTRA_TABLES_DIR}{table_suffix}"
            output_path = os.path.join(extras_dir, f"{table_name}.jsonl")
        else:
            table_name = metadata_name = f"{folder_name}{table_suffix}"
            output_path = os.path.join(sheet_dir, f"{table_name}.jsonl")
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            log.warning(f"File exists. Skipping: {output_path}")
            vlog.detail(f"File exists. Skipping: {output_path}")
            continue
        
        # Verbose logging for each table
        with vlog.step(f"Table {i+1} ({table_name})"):
            vlog.metric("Rows", len(table_df))
            vlog.metric("Columns", len(table_df.columns))
            
            try:
                table_df[METADATA_SHEET_KEY], table_df[METADATA_TABLE_KEY] = sheet_name, metadata_name
                table_df.to_json(output_path, orient='records', lines=True, force_ascii=False)
                log.info(f"Saved {len(table_df)} rows → '{output_path}'")
                vlog.detail(f"Saved to: {output_path}")
            except (IOError, OSError, PermissionError) as e:
                log.error(f"Failed to write table to '{output_path}': {e}")
                vlog.detail(f"ERROR: Write failed - {e}")
                continue  # Skip this table, continue with next
            except Exception as e:
                log.error(f"Unexpected error saving table '{table_name}': {type(e).__name__}: {e}")
                vlog.detail(f"ERROR: {type(e).__name__}: {e}")
                continue  # Skip this table, continue with next
            
            table_elapsed = time.time() - table_start
            vlog.timing("Table processing time", table_elapsed)

def process_excel_file(excel_path: str, output_dir: str, preserve_na: bool = True) -> bool:
    """
    Extract all tables from an Excel file and save as JSONL files.
    
    This function orchestrates the complete Excel processing workflow with robust
    error handling and progress tracking. Uses a context manager for safe Excel
    file handling with automatic resource cleanup.
    
    Args:
        excel_path: Path to the Excel file to process
        output_dir: Directory where output JSONL files will be saved
        preserve_na: If True, preserve empty cells as None; if False, use pandas defaults
        
    Returns:
        True if all sheets processed successfully without errors, False if any errors
        occurred during processing (file read failures, sheet processing errors, etc.)
    
    Note:
        - Uses context manager (with statement) for safe Excel file resource handling
        - Continues processing remaining sheets even if individual sheets fail
        - Provides progress bars (tqdm) and verbose logging when enabled
        - Creates output directory automatically if it doesn't exist
        - Does not raise exceptions; returns False on errors instead
        - Tracks overall success state and logs final status
    """
    overall_start = time.time()
    
    log.info(f"Processing: '{excel_path}'")
    log.info(f"Output → '{output_dir}'")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        log.error(f"Cannot create output directory '{output_dir}': {e}")
        return False
    
    try:
        with pd.ExcelFile(excel_path) as xls:
            log.debug(f"Excel file loaded successfully. Found {len(xls.sheet_names)} sheets: {xls.sheet_names}")
            success = True
            
            # Start verbose logging context
            with vlog.file_processing(os.path.basename(excel_path), total_records=len(xls.sheet_names)):
                vlog.metric("Total sheets", len(xls.sheet_names))
                
                # Progress bar for processing sheets
                for sheet_index, sheet_name in enumerate(tqdm(xls.sheet_names, desc="Processing sheets", unit="sheet", 
                                       file=sys.stdout, dynamic_ncols=True, leave=True,
                                       bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')):
                    sheet_start = time.time()
                    try:
                        with vlog.step(f"Sheet {sheet_index + 1}/{len(xls.sheet_names)}: '{sheet_name}'"):
                            tqdm.write(f"--- Sheet: '{sheet_name}' ---")
                            parse_opts = {'header': None, 'keep_default_na': False, 'na_values': ['']} if preserve_na else {'header': None}
                            all_tables = _split_sheet_into_tables(pd.read_excel(xls, sheet_name=sheet_name, **parse_opts))
                            
                            if not all_tables:
                                tqdm.write(f"INFO: No tables found in '{sheet_name}'")
                                vlog.detail("No tables found in this sheet")
                            else:
                                tqdm.write(f"INFO: Found {len(all_tables)} table(s) in '{sheet_name}'")
                                vlog.metric("Tables detected", len(all_tables))
                                _process_and_save_tables(all_tables, sheet_name, output_dir)
                            
                            sheet_elapsed = time.time() - sheet_start
                            vlog.timing("Sheet processing time", sheet_elapsed)
                    except Exception as e:
                        tqdm.write(f"ERROR: Error on sheet '{sheet_name}': {e}")
                        log.error(f"Error processing sheet '{sheet_name}': {e}")
                        vlog.detail(f"ERROR: {str(e)}")
                        sheet_elapsed = time.time() - sheet_start
                        vlog.timing("Sheet processing time before error", sheet_elapsed)
                        success = False
    except Exception as e:
        log.error(f"Error reading Excel file '{excel_path}': {e}")
        log.debug("Full error details:", exc_info=True)
        return False
    
    overall_elapsed = time.time() - overall_start
    vlog.timing("Overall processing time", overall_elapsed)
    
    if success:
        log.success("Excel processing complete!")
    else:
        log.warning("Excel processing completed with some errors")
    
    return success

def load_study_dictionary(file_path: Optional[str] = None, 
                         json_output_dir: Optional[str] = None, 
                         preserve_na: bool = True) -> bool:
    """
    Load and process study data dictionary from Excel to JSONL format.
    
    This is the primary high-level interface for dictionary processing. It wraps
    :func:`process_excel_file` with default configuration values from the config module.
    
    Args:
        file_path: Path to Excel file (defaults to config.DICTIONARY_EXCEL_FILE)
        json_output_dir: Output directory (defaults to config.DICTIONARY_JSON_OUTPUT_DIR)
        preserve_na: If True, preserve empty cells as None; if False, use pandas defaults
        
    Returns:
        True if all sheets processed successfully, False if any errors occurred
    
    See Also:
        :func:`process_excel_file` - Lower-level processing function for custom workflows
    """
    success = process_excel_file(
        excel_path=file_path or config.DICTIONARY_EXCEL_FILE,
        output_dir=json_output_dir or config.DICTIONARY_JSON_OUTPUT_DIR,
        preserve_na=preserve_na
    )
    return success

if __name__ == "__main__":
    # Initialize logger when running as standalone script
    log.setup_logger(name="load_dictionary", log_level=config.LOG_LEVEL if hasattr(config, 'LOG_LEVEL') else 20)
    
    success = load_study_dictionary(preserve_na=True)
    if success:
        log.success(f"Processing complete for data dictionary from {config.DICTIONARY_EXCEL_FILE}")
    else:
        log.error(f"Processing failed for data dictionary from {config.DICTIONARY_EXCEL_FILE}")
        sys.exit(1)
