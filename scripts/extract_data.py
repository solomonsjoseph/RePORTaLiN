#!/usr/bin/env python3
"""
Data Extraction Module
======================

Extracts raw data from Excel files and converts to JSONL format with
type conversion, progress tracking, and error recovery.

This module provides robust Excel-to-JSONL conversion with duplicate column
handling, data validation, and comprehensive error recovery.

Key Features:
    - Dual output: Creates both original and cleaned JSONL versions
    - Duplicate column removal: Intelligently removes SUBJID2, SUBJID3, etc.
    - Type conversion: Handles pandas/numpy types, dates, NaN values
    - Integrity checks: Validates output files before skipping
    - Error recovery: Continues processing even if individual files fail
    - Progress tracking: Real-time progress bars
    - Verbose logging: Detailed tree-view logs with timing (v0.0.12+)

Verbose Mode:
    When running with ``--verbose`` flag, detailed logs are generated including
    file-by-file processing, Excel loading details (rows/columns), duplicate column
    detection, and per-file timing information.

See Also
--------
- :doc:`../user_guide/usage` - Usage and detailed tutorials
- :func:`extract_excel_to_jsonl` - Main extraction function
- :func:`process_excel_file` - Process individual Excel files
"""
import os
import sys
import json
import time
import pandas as pd
import numpy as np
import re
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from tqdm import tqdm
from scripts.utils import logging_system as log
import config

vlog = log.get_verbose_logger()

# ============================================================================
# Module Constants
# ============================================================================

# File Configuration
EXCEL_ENGINE: str = 'openpyxl'
"""Excel file reading engine for .xlsx files."""

EXCEL_FILE_EXTENSION: str = '*.xlsx'
"""Glob pattern for Excel files to process."""

JSONL_FILE_EXTENSION: str = '.jsonl'
"""Output file extension for JSONL format."""

FILE_ENCODING: str = 'utf-8'
"""Default text encoding for file operations."""

# Directory Structure
ORIGINAL_OUTPUT_DIR: str = 'original'
"""Subdirectory name for original (unmodified) JSONL files."""

CLEANED_OUTPUT_DIR: str = 'cleaned'
"""Subdirectory name for cleaned (duplicate columns removed) JSONL files."""

# Metadata Keys
METADATA_KEY: str = '_metadata'
"""Key name for metadata objects in JSONL records."""

SOURCE_FILE_KEY: str = 'source_file'
"""Key name for source filename tracking in JSONL records."""

METADATA_TYPE_KEY: str = 'type'
"""Key name for metadata type identifier."""

METADATA_COLUMNS_KEY: str = 'columns'
"""Key name for column list in metadata."""

METADATA_NOTE_KEY: str = 'note'
"""Key name for explanatory notes in metadata."""

# Metadata Values
METADATA_TYPE_COLUMN_STRUCTURE: str = 'column_structure'
"""Metadata type value for files with column headers but no data rows."""

METADATA_NOTE_EMPTY_FILE: str = 'File contains column headers but no data rows'
"""Standard message for empty files that contain only column structure."""

# Duplicate Column Detection
DUPLICATE_COLUMN_PATTERN: str = r'^(.+?)_?(\d+)$'
"""Regex pattern to identify duplicate columns (e.g., SUBJID2, NAME_3).

Pattern matches:
    - Any base name (captured in group 1)
    - Optional underscore
    - One or more digits at end (captured in group 2)
    
Examples:
    - SUBJID2 → base: SUBJID, suffix: 2
    - NAME_3 → base: NAME, suffix: 3
    - AGE1 → base: AGE, suffix: 1
"""

# Return Dictionary Keys
RESULT_FILES_FOUND: str = 'files_found'
"""Key for total Excel files found in extraction results."""

RESULT_FILES_CREATED: str = 'files_created'
"""Key for number of JSONL files successfully created."""

RESULT_FILES_SKIPPED: str = 'files_skipped'
"""Key for number of files skipped (already exist with valid content)."""

RESULT_TOTAL_RECORDS: str = 'total_records'
"""Key for total number of records processed across all files."""

RESULT_ERRORS: str = 'errors'
"""Key for list of error messages encountered during processing."""

RESULT_PROCESSING_TIME: str = 'processing_time'
"""Key for total processing time in seconds."""

# Logging Configuration
DEFAULT_LOG_LEVEL: int = 20
"""Default logging level (INFO) when LOG_LEVEL not configured."""

MODULE_LOGGER_NAME: str = 'extract_data'
"""Logger name for this module when run as standalone script."""

__all__ = [
    # Main Functions
    'extract_excel_to_jsonl',
    # File Processing
    'process_excel_file',
    'find_excel_files',
    # Utility Functions
    'check_file_integrity',
    'is_dataframe_empty',
    # Data Conversion
    'convert_dataframe_to_jsonl',
    'clean_record_for_json',
    'clean_duplicate_columns',
]

def clean_record_for_json(record: dict) -> dict:
    """
    Convert pandas record to JSON-serializable types.
    
    Handles NaN, infinity, numpy types, and datetime objects, ensuring
    all values are properly serializable to JSON format.
    
    Args:
        record: Dictionary with potentially non-JSON-serializable values
        
    Returns:
        Dictionary with all values converted to JSON-serializable types
        
    Note:
        - NaN values are converted to None
        - Infinity values (+inf, -inf) are converted to None
        - Numpy types are converted to Python native types
        - Datetime objects are converted to ISO format strings
    """
    cleaned = {}
    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = None
        elif isinstance(value, (np.integer, np.floating)):
            # Convert numpy numeric types to Python types
            num_value = value.item()
            # Handle infinity and -infinity (check before converting to Python type)
            if not np.isfinite(value):
                cleaned[key] = None  # Convert inf/-inf to None for valid JSON
            else:
                cleaned[key] = num_value
        elif isinstance(value, (float, int)):
            # Handle Python native float/int (might contain inf)
            if isinstance(value, float) and not np.isfinite(value):
                cleaned[key] = None  # Convert inf/-inf to None for valid JSON
            else:
                cleaned[key] = value
        elif isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
            cleaned[key] = str(value)
        else:
            cleaned[key] = value
    return cleaned

def find_excel_files(directory: str) -> List[Path]:
    """
    Find all Excel files (.xlsx) in the specified directory.
    
    Validates that the directory exists and is accessible before searching.
    Returns an empty list if the directory doesn't exist or isn't a directory.
    
    Args:
        directory: Path to directory to search
        
    Returns:
        List of Path objects for all .xlsx files found (empty if directory invalid)
        
    Note:
        - Uses the EXCEL_FILE_EXTENSION constant for file pattern matching
        - Logs warnings if directory doesn't exist or isn't accessible
        - Returns empty list on errors instead of raising exceptions
    """
    try:
        dir_path = Path(directory)
        
        # Validate directory exists
        if not dir_path.exists():
            log.warning(f"Directory does not exist: {directory}")
            vlog.detail(f"WARNING: Directory not found: {directory}")
            return []
        
        # Validate path is actually a directory
        if not dir_path.is_dir():
            log.error(f"Path is not a directory: {directory}")
            vlog.detail(f"ERROR: Not a directory: {directory}")
            return []
        
        # Search for Excel files
        files = list(dir_path.glob(EXCEL_FILE_EXTENSION))
        log.debug(f"Found {len(files)} Excel files in {directory}")
        vlog.detail(f"Excel files discovered: {len(files)}")
        
        return files
        
    except Exception as e:
        log.error(f"Error searching for Excel files in {directory}: {e}")
        vlog.detail(f"ERROR: File search failed: {e}")
        return []

def is_dataframe_empty(df: pd.DataFrame) -> bool:
    """Check if DataFrame is completely empty (no rows AND no columns)."""
    return len(df.columns) == 0 and len(df) == 0

def convert_dataframe_to_jsonl(df: pd.DataFrame, output_file: Path, source_filename: str) -> int:
    """
    Convert DataFrame to JSONL format, handling empty DataFrames with column metadata.
    
    Handles file I/O errors and JSON serialization errors gracefully. If individual
    rows fail serialization, they are skipped with a warning, allowing the rest of
    the file to process successfully.
    
    Args:
        df: DataFrame to convert
        output_file: Path to output JSONL file
        source_filename: Name of source Excel file for tracking
        
    Returns:
        Number of records written (may be less than total rows if some failed)
        
    Raises:
        IOError: If file cannot be opened or written due to permissions or disk issues
        OSError: If file path is invalid or filesystem errors occur
        
    Note:
        - Uses constants for encoding, metadata keys, and source file tracking
        - Skips rows with JSON serialization errors (logged as warnings)
        - Empty DataFrames with column headers create metadata-only records
    """
    try:
        with open(output_file, 'w', encoding=FILE_ENCODING) as f:
            # Handle empty DataFrames with column structure
            if len(df) == 0 and len(df.columns) > 0:
                record = {col: None for col in df.columns}
                record.update({
                    SOURCE_FILE_KEY: source_filename, 
                    METADATA_KEY: {
                        METADATA_TYPE_KEY: METADATA_TYPE_COLUMN_STRUCTURE, 
                        METADATA_COLUMNS_KEY: list(df.columns),
                        METADATA_NOTE_KEY: METADATA_NOTE_EMPTY_FILE
                    }
                })
                try:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    log.debug(f"Created metadata-only record for {source_filename}")
                    vlog.detail(f"Metadata record created (empty file with {len(df.columns)} columns)")
                except (TypeError, ValueError) as e:
                    error_msg = f"JSON serialization error for metadata in {source_filename}: {e}"
                    log.error(error_msg)
                    vlog.detail(f"ERROR: {error_msg}")
                    raise
                return 1
            
            # Process regular data rows
            records = 0
            skipped_rows = 0
            for row_idx, row in df.iterrows():
                try:
                    record = clean_record_for_json(row.to_dict())
                    record[SOURCE_FILE_KEY] = source_filename
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    records += 1
                except (TypeError, ValueError) as e:
                    # Skip this row but continue processing
                    skipped_rows += 1
                    log.warning(f"Skipping row {row_idx} in {source_filename} due to JSON error: {e}")
                    vlog.detail(f"WARNING: Row {row_idx} skipped (JSON serialization failed: {e})")
                    continue
            
            # Log summary if rows were skipped
            if skipped_rows > 0:
                log.warning(f"Skipped {skipped_rows} rows in {source_filename} due to serialization errors")
                vlog.detail(f"Total skipped rows: {skipped_rows} out of {len(df)}")
            
            return records
            
    except IOError as e:
        error_msg = f"File I/O error writing to {output_file}: {e}"
        log.error(error_msg)
        vlog.detail(f"ERROR: {error_msg}")
        raise
    except OSError as e:
        error_msg = f"Filesystem error writing to {output_file}: {e}"
        log.error(error_msg)
        vlog.detail(f"ERROR: {error_msg}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error in convert_dataframe_to_jsonl for {source_filename}: {e}"
        log.error(error_msg)
        vlog.detail(f"ERROR: {error_msg}")
        raise


def process_excel_file(excel_file: Path, output_dir: str) -> Tuple[bool, int, Optional[str]]:
    """
    Process a single Excel file to JSONL format, creating both original and cleaned versions.
    
    Creates two JSONL outputs:
        1. Original: Complete data with all columns intact
        2. Cleaned: Duplicate columns removed (e.g., SUBJID2, SUBJID3)
    
    Args:
        excel_file: Path to Excel (.xlsx) file to process
        output_dir: Base output directory (subdirectories created automatically)
        
    Returns:
        Tuple containing:
            - success (bool): True if file processed successfully
            - record_count (int): Number of records written (0 if failed)
            - error_message (Optional[str]): Error description if failed, None otherwise
            
    Note:
        - Uses EXCEL_ENGINE constant for pandas Excel reading
        - Creates subdirectories using ORIGINAL_OUTPUT_DIR and CLEANED_OUTPUT_DIR
        - Logs detailed processing steps when verbose mode is enabled
        - Timing information is recorded for performance monitoring
        
    Examples:
        >>> from pathlib import Path
        >>> success, count, error = process_excel_file(Path("data.xlsx"), "./output")
        >>> if success:
        ...     print(f"Processed {count} records")  # int: number of records
        ... else:
        ...     print(f"Error: {error}")
        Processed 1250 records
    """
    start_time = time.time()
    try:
        # Create separate directories for original and cleaned files
        original_dir = Path(output_dir) / ORIGINAL_OUTPUT_DIR
        cleaned_dir = Path(output_dir) / CLEANED_OUTPUT_DIR
        
        try:
            original_dir.mkdir(exist_ok=True, parents=True)
            cleaned_dir.mkdir(exist_ok=True, parents=True)
            vlog.detail(f"Created/verified output directories: {ORIGINAL_OUTPUT_DIR}, {CLEANED_OUTPUT_DIR}")
        except OSError as e:
            error_msg = f"Failed to create output directories for {excel_file.name}: {e}"
            log.error(error_msg)
            vlog.detail(f"ERROR: {error_msg}")
            return False, 0, error_msg
        
        output_file = original_dir / f"{excel_file.stem}{JSONL_FILE_EXTENSION}"
        output_file_cleaned = cleaned_dir / f"{excel_file.stem}{JSONL_FILE_EXTENSION}"
        
        # Use openpyxl engine for better performance with .xlsx files
        with vlog.step("Loading Excel file"):
            df = pd.read_excel(excel_file, engine=EXCEL_ENGINE)
            vlog.metric("Rows", len(df))
            vlog.metric("Columns", len(df.columns))
        
        if is_dataframe_empty(df):
            tqdm.write(f"  ⊘ Skipping {excel_file.name} (empty)")
            return False, 0, None
        
        # Save original version
        with vlog.step("Saving original version"):
            records_count = convert_dataframe_to_jsonl(df, output_file, excel_file.name)
            vlog.detail(f"Created: {output_file.name} ({records_count} records)")
            tqdm.write(f"  ✓ Created original/{output_file.name} with {records_count} rows (original)")
        
        # Clean duplicate columns and save cleaned version
        with vlog.step("Cleaning duplicate columns"):
            df_cleaned = clean_duplicate_columns(df)
            vlog.detail(f"Removed {len(df.columns) - len(df_cleaned.columns)} duplicate columns")
        
        with vlog.step("Saving cleaned version"):
            records_count_cleaned = convert_dataframe_to_jsonl(df_cleaned, output_file_cleaned, excel_file.name)
            vlog.detail(f"Created: {output_file_cleaned.name} ({records_count_cleaned} records)")
            tqdm.write(f"  ✓ Created cleaned/{output_file_cleaned.name} with {records_count_cleaned} rows (cleaned)")
        
        # Log timing
        elapsed_time = time.time() - start_time
        vlog.timing("Total processing time", elapsed_time)
        
        return True, records_count, None
    except Exception as e:
        error_msg = f"Error processing {excel_file.name}: {str(e)}"
        tqdm.write(f"  ✗ {error_msg}")
        log.error(error_msg)
        vlog.detail(f"ERROR: {error_msg}")
        elapsed_time = time.time() - start_time
        vlog.timing("Processing time before error", elapsed_time)
        return False, 0, error_msg

def clean_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate columns ending with numeric suffixes (e.g., SUBJID2, SUBJID3).
    
    Uses 100% safe duplicate detection - only removes columns if:
    1. Column name ends with optional underscore and digits (e.g., SUBJID2, NAME_3)
    2. Base column name exists (e.g., SUBJID, NAME)
    3. Content is EXACTLY identical to base column (100% match) OR column is entirely null
    
    This conservative approach ensures zero risk of data loss by only removing columns
    that are provably redundant. Any column with even a single different value is preserved.
    
    Args:
        df: DataFrame to clean
        
    Returns:
        DataFrame with duplicate columns removed
        
    Note:
        - Uses element-wise comparison with proper NaN handling
        - Logs all removal decisions with detailed explanations
        - Preserves column order of remaining columns
        - **Edge case**: If base column is all-NaN but duplicate has values,
          the duplicate is preserved (not 100% identical)
    """
    columns_to_keep = []
    columns_to_remove = []
    removal_reasons = {}  # Track why each column was removed
    
    for col in df.columns:
        # Match columns ending with optional underscore and digits
        match = re.match(DUPLICATE_COLUMN_PATTERN, str(col))
        
        if match:
            base_name = match.group(1)
            # Only remove if base column exists AND content is duplicate/empty
            if base_name in df.columns:
                try:
                    # Check if column is entirely null
                    if df[col].isna().all():
                        columns_to_remove.append(col)
                        removal_reasons[col] = "entirely null"
                        log.debug(f"Marking '{col}' for removal (entirely null)")
                        vlog.detail(f"Marking '{col}' for removal (entirely null)")
                    else:
                        # Check for exact equality using element-wise comparison
                        # This handles NaN values correctly (NaN == NaN is False, so we use fillna)
                        base_col = df[base_name]
                        dup_col = df[col]
                        
                        # Compare with proper NaN handling: both NaN counts as equal
                        both_na = base_col.isna() & dup_col.isna()
                        both_equal = (base_col == dup_col)
                        all_match = (both_na | both_equal).all()
                        
                        if all_match:
                            columns_to_remove.append(col)
                            removal_reasons[col] = f"100% identical to '{base_name}'"
                            log.debug(f"Marking '{col}' for removal (100% identical to '{base_name}')")
                            vlog.detail(f"Marking '{col}' for removal (100% identical to '{base_name}')")
                        else:
                            # Column has at least one different value - keep it
                            columns_to_keep.append(col)
                            # Calculate match percentage for logging
                            match_count = (both_na | both_equal).sum()
                            match_pct = (match_count / len(df) * 100) if len(df) > 0 else 0
                            log.debug(f"Keeping '{col}' ({match_pct:.1f}% similar to '{base_name}', not 100%)")
                            vlog.detail(f"Keeping '{col}' ({match_pct:.1f}% similar to '{base_name}')")
                except Exception as e:
                    # If comparison fails, keep the column to be safe
                    columns_to_keep.append(col)
                    log.warning(f"Could not compare '{col}' with '{base_name}': {e}. Keeping column for safety.")
                    vlog.detail(f"Keeping '{col}' (comparison failed: {e})")
            else:
                # Base column doesn't exist, keep this column
                columns_to_keep.append(col)
                log.debug(f"Keeping '{col}' (base column '{base_name}' not found)")
        else:
            # Column name doesn't match pattern, keep it
            columns_to_keep.append(col)
    
    # Log summary of removals
    if columns_to_remove:
        removal_summary = [f"{col} ({removal_reasons[col]})" for col in columns_to_remove]
        tqdm.write(f"    → Removing {len(columns_to_remove)} duplicate column(s): {', '.join(columns_to_remove)}")
        log.info(f"Removed {len(columns_to_remove)} duplicate columns: {', '.join(removal_summary)}")
        vlog.detail(f"Duplicate columns removed: {', '.join(removal_summary)}")
    else:
        log.debug("No duplicate columns found to remove")
        vlog.detail("No duplicate columns found")
    
    return df[columns_to_keep].copy()

def check_file_integrity(file_path: Path) -> bool:
    """Check if JSONL file is valid and readable."""
    try:
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False
        
        with open(file_path, 'r', encoding=FILE_ENCODING) as f:
            first_line = f.readline().strip()
            if not first_line:
                return False
            data = json.loads(first_line)
            return isinstance(data, dict) and len(data) > 0
    except (json.JSONDecodeError, IOError, OSError):
        return False


def extract_excel_to_jsonl() -> Dict[str, Any]:
    """
    Extract all Excel files from dataset directory, creating original and cleaned JSONL versions.
    
    Processes all .xlsx files in the configured DATASETS_DIR, converting each to JSONL format.
    Creates two versions of each file:
        1. Original: Unmodified data with all columns
        2. Cleaned: Duplicate columns removed for data quality
    
    Features:
        - Automatic duplicate detection and skipping of already-processed files
        - Integrity validation of existing output files
        - Comprehensive error handling and recovery
        - Progress tracking with real-time status updates
        - Detailed logging in verbose mode
        
    Returns:
        Dictionary with extraction statistics containing:
            - files_found (int): Total Excel files discovered
            - files_created (int): Successfully created JSONL files
            - files_skipped (int): Files skipped (valid output exists)
            - total_records (int): Total data records processed
            - errors (List[str]): Error messages for failed files
            - processing_time (float): Total execution time in seconds
            
    Note:
        - Uses config.DATASETS_DIR for input location
        - Uses config.OUTPUT_DIR/config.STUDY_NAME for output location
        - Return keys are defined by RESULT_* constants
        - Requires verbose logger (vlog) for detailed operation tracking
        
    Examples:
        >>> from typing import Dict, Any
        >>> result: Dict[str, Any] = extract_excel_to_jsonl()
        >>> print(f"Created {result['files_created']} files")
        Created 15 files
        >>> print(f"Total: {result['total_records']} records")
        Total: 18750 records
        
    See Also:
        - :func:`process_excel_file` - Individual file processing
        - :func:`clean_duplicate_columns` - Duplicate column removal logic
    """
    overall_start = time.time()
    
    # Validate required configuration
    if not hasattr(config, 'DATASETS_DIR') or not config.DATASETS_DIR:
        error_msg = "Configuration error: DATASETS_DIR not set"
        log.error(error_msg)
        print(f"ERROR: {error_msg}")
        return {
            RESULT_FILES_FOUND: 0,
            RESULT_FILES_CREATED: 0,
            RESULT_FILES_SKIPPED: 0,
            RESULT_TOTAL_RECORDS: 0,
            RESULT_ERRORS: [error_msg],
            RESULT_PROCESSING_TIME: 0
        }
    
    if not hasattr(config, 'OUTPUT_DIR') or not config.OUTPUT_DIR:
        error_msg = "Configuration error: OUTPUT_DIR not set"
        log.error(error_msg)
        print(f"ERROR: {error_msg}")
        return {
            RESULT_FILES_FOUND: 0,
            RESULT_FILES_CREATED: 0,
            RESULT_FILES_SKIPPED: 0,
            RESULT_TOTAL_RECORDS: 0,
            RESULT_ERRORS: [error_msg],
            RESULT_PROCESSING_TIME: 0
        }
    
    if not hasattr(config, 'STUDY_NAME') or not config.STUDY_NAME:
        error_msg = "Configuration error: STUDY_NAME not set"
        log.error(error_msg)
        print(f"ERROR: {error_msg}")
        return {
            RESULT_FILES_FOUND: 0,
            RESULT_FILES_CREATED: 0,
            RESULT_FILES_SKIPPED: 0,
            RESULT_TOTAL_RECORDS: 0,
            RESULT_ERRORS: [error_msg],
            RESULT_PROCESSING_TIME: 0
        }
    
    # Use new v0.3.0 config API: DATASETS_DIR and OUTPUT_DIR
    clean_dataset_dir = os.path.join(config.OUTPUT_DIR, config.STUDY_NAME)
    log.info(f"Output directory: {clean_dataset_dir}")
    vlog.detail(f"Configuration: DATASETS_DIR={config.DATASETS_DIR}, OUTPUT_DIR={config.OUTPUT_DIR}, STUDY_NAME={config.STUDY_NAME}")
    
    # Create output directory with error handling
    try:
        os.makedirs(clean_dataset_dir, exist_ok=True)
        log.debug(f"Created/verified output directory: {clean_dataset_dir}")
        vlog.detail(f"Output directory ready: {clean_dataset_dir}")
    except OSError as e:
        error_msg = f"Failed to create output directory {clean_dataset_dir}: {e}"
        log.error(error_msg)
        print(f"ERROR: {error_msg}")
        return {
            RESULT_FILES_FOUND: 0,
            RESULT_FILES_CREATED: 0,
            RESULT_FILES_SKIPPED: 0,
            RESULT_TOTAL_RECORDS: 0,
            RESULT_ERRORS: [error_msg],
            RESULT_PROCESSING_TIME: 0
        }
    
    excel_files = find_excel_files(config.DATASETS_DIR)
    
    if not excel_files:
        log.warning(f"No Excel files found in {config.DATASETS_DIR}")
        print(f"No Excel files found in {config.DATASETS_DIR}")
        return {
            RESULT_FILES_FOUND: 0,
            RESULT_FILES_CREATED: 0,
            RESULT_FILES_SKIPPED: 0,
            RESULT_TOTAL_RECORDS: 0,
            RESULT_ERRORS: []
        }
    
    log.info(f"Found {len(excel_files)} Excel files to process")
    log.debug(f"Excel files: {[f.name for f in excel_files[:10]]}{'...' if len(excel_files) > 10 else ''}")
    print(f"Found {len(excel_files)} Excel files to process...")
    total_records, files_created, files_skipped, errors = 0, 0, 0, []
    
    # Start verbose logging context
    with vlog.file_processing("Data extraction", total_records=len(excel_files)):
        vlog.metric("Total files to process", len(excel_files))
        
        # Progress bar for processing files
        for file_index, excel_file in enumerate(tqdm(excel_files, desc="Processing files", unit="file",
                                   file=sys.stdout, dynamic_ncols=True, leave=True,
                                   bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'), 1):
            # Check if files already exist in both original and cleaned directories
            original_file = Path(clean_dataset_dir) / ORIGINAL_OUTPUT_DIR / f"{excel_file.stem}{JSONL_FILE_EXTENSION}"
            cleaned_file = Path(clean_dataset_dir) / CLEANED_OUTPUT_DIR / f"{excel_file.stem}{JSONL_FILE_EXTENSION}"
            
            # Check if files exist AND have valid content (integrity check)
            if (original_file.exists() and cleaned_file.exists() and
                check_file_integrity(original_file) and check_file_integrity(cleaned_file)):
                files_skipped += 1
                tqdm.write(f"  ⊙ Skipping {excel_file.name} (valid output already exists)")
                log.debug(f"Skipping {excel_file.name} - valid output exists")
                vlog.detail(f"File {file_index}: Skipped (valid output exists)")
                continue
            
            # If files exist but are corrupted, warn and reprocess
            if original_file.exists() or cleaned_file.exists():
                tqdm.write(f"  ⚠ Re-processing {excel_file.name} (existing files are corrupted or incomplete)")
                log.warning(f"Re-processing {excel_file.name} - existing files corrupted")
                vlog.detail(f"File {file_index}: Re-processing (corrupted files)")
                
            tqdm.write(f"Processing: {excel_file.name}")
            log.debug(f"Processing {excel_file.name}")
            
            # Process file with verbose logging context
            with vlog.step(f"File {file_index}/{len(excel_files)}: {excel_file.name}"):
                success, records_count, error_msg = process_excel_file(excel_file, clean_dataset_dir)
                if success:
                    files_created += 1
                    total_records += records_count
                    log.debug(f"Successfully processed {excel_file.name}: {records_count} records")
                    vlog.detail(f"✓ Successfully processed ({records_count} records)")
                elif error_msg:
                    errors.append(error_msg)
                    log.error(f"Failed to process {excel_file.name}: {error_msg}")
                    vlog.detail(f"✗ Error: {error_msg}")
    
    # Calculate overall timing
    overall_elapsed = time.time() - overall_start
    vlog.timing("Overall extraction time", overall_elapsed)
    
    # Summary
    print(f"\nExtraction complete:")
    print(f"  ✓ {total_records} total records processed")
    print(f"  ✓ {files_created} JSONL files created")
    print(f"  ⊙ {files_skipped} files skipped (already exist)")
    print(f"  → Output directory: {clean_dataset_dir}")
    if errors:
        print(f"  ✗ {len(errors)} files had errors")
        log.error(f"{len(errors)} files had errors during extraction")
    
    log.info(f"Extraction complete: {total_records} records, {files_created} files created, {files_skipped} skipped")
    
    return {
        RESULT_FILES_FOUND: len(excel_files),
        RESULT_FILES_CREATED: files_created,
        RESULT_FILES_SKIPPED: files_skipped,
        RESULT_TOTAL_RECORDS: total_records,
        RESULT_ERRORS: errors,
        RESULT_PROCESSING_TIME: overall_elapsed
    }


if __name__ == "__main__":
    try:
        # Initialize logger when running as standalone script
        log.setup_logging(
            module_name=MODULE_LOGGER_NAME,
            log_level=config.LOG_LEVEL if hasattr(config, 'LOG_LEVEL') else 'INFO'
        )
        
        result = extract_excel_to_jsonl()
        
        # Exit with appropriate code based on results
        if result[RESULT_ERRORS]:
            log.error(f"Extraction completed with {len(result[RESULT_ERRORS])} errors")
            sys.exit(1)
        elif result[RESULT_FILES_CREATED] == 0 and result[RESULT_FILES_FOUND] > 0:
            log.warning("No files were processed (all were skipped)")
            sys.exit(0)
        else:
            log.success(f"Extraction successful: {result[RESULT_FILES_CREATED]} files created, {result[RESULT_TOTAL_RECORDS]} records processed")
            sys.exit(0)
            
    except KeyboardInterrupt:
        log.warning("Extraction cancelled by user")
        print("\n⚠ Extraction cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
        
    except Exception as e:
        log.error(f"Fatal error in main execution: {e}")
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
