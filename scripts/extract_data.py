#!/usr/bin/env python3
"""Excel to JSONL data extraction with type conversion and validation.

This module extracts research data from Excel files (.xlsx) and converts them to
JSONL (JSON Lines) format for efficient downstream processing. It produces two
versions of each dataset: 'original' (unmodified) and 'cleaned' (duplicate columns
removed), ensuring data integrity while optimizing for analysis.

Architecture:
    The extraction pipeline implements a three-stage process:
    1. Discovery: Recursively find all Excel files in datasets directory
    2. Conversion: Read Excel → DataFrame → JSONL with type safety
    3. Cleaning: Detect and remove duplicate columns in cleaned version

Key Features:
    - **Dual Output**: Creates both original and cleaned JSONL files
    - **Type Safety**: Converts pandas/numpy types to JSON-serializable Python types
    - **Duplicate Detection**: Identifies duplicate columns (e.g., SUBJID2, NAME_3)
    - **File Integrity**: Validates existing files before skipping
    - **Empty Handling**: Preserves column metadata even for empty DataFrames
    - **Error Resilience**: Continues processing on row-level errors

Type Conversion Logic:
    The module handles these type conversions:
    - pandas.NA, numpy.nan → None (JSON null)
    - numpy.int64, numpy.float64 → Python int, float
    - numpy.inf, -numpy.inf → None (JSON can't represent infinity)
    - pandas.Timestamp, datetime → ISO 8601 string
    - All other types preserved as-is

Duplicate Column Detection:
    Columns are flagged as duplicates if:
    - Name matches pattern: base_name + optional '_' + digits (e.g., SUBJID2, AGE_1)
    - Base column exists (e.g., SUBJID for SUBJID2)
    - Content is 100% identical OR entirely null
    
    Columns are KEPT if they have any differing values from the base column.

Output Structure:
    {OUTPUT_DIR}/{STUDY_NAME}/
        ├── original/          # Unmodified data with all columns
        │   ├── file1.jsonl
        │   └── file2.jsonl
        └── cleaned/           # Duplicate columns removed
            ├── file1.jsonl
            └── file2.jsonl

Typical Usage:
    # Using defaults from config
    >>> from scripts.extract_data import extract_excel_to_jsonl
    >>> result = extract_excel_to_jsonl()
    >>> print(f"Processed {result['total_records']} records")
    
    # Standalone script execution
    $ python scripts/extract_data.py
    Found 50 Excel files to process...
    Processing files: 100%|██████| 50/50 [00:30<00:00]
    ✓ 10,000 total records processed

Dependencies:
    - pandas: Excel reading and DataFrame operations
    - numpy: Type checking and NaN handling
    - tqdm: Progress visualization
    - scripts.utils.logging_system: Centralized logging
    - config: Study-specific paths and settings

Notes:
    - Uses openpyxl engine for .xlsx files (xlrd deprecated for .xlsx)
    - Empty DataFrames with columns → metadata-only record with column structure
    - File integrity checks prevent partial/corrupted overwrites
    - All infinity values converted to None for valid JSON
    - Progress tracked with tqdm and verbose logging for observability
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
    """Convert pandas record to JSON-serializable types.
    
    This function transforms a DataFrame row (as dict) into a JSON-safe format by
    converting pandas/numpy types to Python native types. It handles edge cases
    like infinity, NaN, and datetime objects that aren't natively JSON-serializable.
    
    Args:
        record: Dictionary from DataFrame row (typically from row.to_dict()).
            May contain pandas/numpy types like np.int64, pd.Timestamp, etc.
    
    Returns:
        Dictionary with all values converted to JSON-serializable Python types:
            - pd.NA, np.nan → None
            - np.integer, np.floating → int, float
            - np.inf, -np.inf → None (JSON can't represent infinity)
            - pd.Timestamp, datetime → str (ISO 8601 format)
            - Other types preserved as-is
    
    Example:
        >>> import pandas as pd
        >>> import numpy as np
        >>> record = {'age': np.int64(25), 'score': np.inf, 'date': pd.Timestamp('2023-01-01')}
        >>> clean_record_for_json(record)
        {'age': 25, 'score': None, 'date': '2023-01-01 00:00:00'}
        
    Notes:
        - Infinity values are converted to None (JSON spec doesn't support ±Infinity)
        - All NaN values (pandas.NA, numpy.nan) become JSON null (None)
        - Dates are converted to strings (ISO 8601 format by default)
        - Used before every json.dumps() call to ensure no TypeErrors
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
    """Find all Excel files (.xlsx) in the specified directory.
    
    Recursively searches for Excel files matching the .xlsx extension pattern.
    Validates directory existence and accessibility before searching.
    
    Args:
        directory: Path to directory to search (can be relative or absolute).
    
    Returns:
        List of Path objects for found Excel files. Empty list if no files found,
        directory doesn't exist, or errors occur during search.
        
    Example:
        >>> files = find_excel_files('data/Indo-VAP/datasets')
        >>> len(files)
        50
        >>> files[0].name
        '1A_ICScreening.xlsx'
        
    Notes:
        - Returns empty list (not error) if directory doesn't exist
        - Validates path is actually a directory before searching
        - Uses glob pattern from EXCEL_FILE_EXTENSION constant (*.xlsx)
        - All errors caught and logged; function never raises exceptions
        - Results include recursive subdirectories if they exist
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
    """Check if DataFrame is completely empty (no rows AND no columns).
    
    This differs from pandas' df.empty which returns True for DataFrames with
    columns but no rows. This function only returns True if BOTH rows and
    columns are absent.
    
    Args:
        df: DataFrame to check for emptiness.
    
    Returns:
        True if DataFrame has zero rows AND zero columns, False otherwise.
        
    Example:
        >>> df_no_data = pd.DataFrame()
        >>> is_dataframe_empty(df_no_data)
        True
        
        >>> df_with_cols = pd.DataFrame(columns=['A', 'B'])
        >>> is_dataframe_empty(df_with_cols)
        False
        
    Notes:
        - DataFrames with columns but no rows are NOT considered empty
        - Such DataFrames are saved as metadata records with column structure
        - This allows preserving schema information from empty Excel files
    """
    return len(df.columns) == 0 and len(df) == 0

def convert_dataframe_to_jsonl(df: pd.DataFrame, output_file: Path, source_filename: str) -> int:
    """Convert DataFrame to JSONL format, handling empty DataFrames with column metadata.
    
    Writes one JSON object per line (JSONL format) to the output file. Each record
    includes a source_file field for provenance tracking. Empty DataFrames (with
    columns but no data) are saved as a single metadata record preserving schema.
    
    Args:
        df: DataFrame to convert (may be empty but have columns).
        output_file: Path where JSONL file will be written.
        source_filename: Original Excel filename (for provenance tracking).
    
    Returns:
        Number of records written to file. Returns 1 for metadata-only records.
        
    Raises:
        IOError: If file cannot be opened or written.
        OSError: If filesystem errors occur during write.
        TypeError: If a record cannot be JSON-serialized (propagated after logging).
        ValueError: If JSON serialization fails for other reasons.
        
    Example:
        >>> import tempfile
        >>> df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        ...     temp_path = Path(f.name)
        >>> count = convert_dataframe_to_jsonl(df, temp_path, 'test.xlsx')  # doctest: +SKIP
        >>> count  # doctest: +SKIP
        2
        
        >>> # Empty DataFrame with columns → metadata record
        >>> empty_df = pd.DataFrame(columns=['ID', 'Name'])
        >>> count = convert_dataframe_to_jsonl(empty_df, temp_path, 'empty.xlsx')  # doctest: +SKIP
        >>> count  # doctest: +SKIP
        1
        
    Side Effects:
        - Creates/overwrites output_file
        - Logs warnings for rows that fail JSON serialization (but continues)
        - Updates verbose logger with metrics and warnings
        
    Notes:
        - Empty DataFrames (rows=0, cols>0) → single metadata record with schema
        - Metadata records have _metadata field with type, columns, and note
        - Rows with serialization errors are skipped (logged as warnings)
        - All records include source_file field for data lineage
        - Uses UTF-8 encoding and ensure_ascii=False for international characters
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
    """Process a single Excel file to JSONL format, creating both original and cleaned versions.
    
    This function orchestrates the complete processing pipeline for one Excel file:
    1. Create output directory structure (original/ and cleaned/ subdirs)
    2. Load Excel file into DataFrame with openpyxl engine
    3. Save original version (all columns preserved)
    4. Clean duplicate columns using pattern matching + content comparison
    5. Save cleaned version (duplicates removed)
    
    Args:
        excel_file: Path to the Excel file to process (.xlsx).
        output_dir: Base output directory (subdirs created automatically).
    
    Returns:
        Tuple of (success, record_count, error_message):
            - success: True if processing completed, False on any error
            - record_count: Number of records in original version (0 on error)
            - error_message: Error description if failed, None if successful
            
    Example:
        >>> from pathlib import Path
        >>> success, count, error = process_excel_file(
        ...     Path('data/1A_ICScreening.xlsx'),
        ...     'output/Indo-VAP'
        ... )
        >>> if success:
        ...     print(f"Processed {count} records")
        Processed 150 records
        
    Side Effects:
        - Creates output_dir/original/ and output_dir/cleaned/ directories
        - Writes two JSONL files: {filename}.jsonl in each directory
        - Logs progress, metrics, and timing via logging_system
        - Prints status to stdout via tqdm.write()
        
    Notes:
        - Empty DataFrames (no rows or columns) are skipped
        - Empty with columns → metadata-only record is created
        - Uses openpyxl engine for .xlsx (xlrd deprecated)
        - Duplicate detection: columns ending with _N or N compared to base
        - All errors caught; never raises exceptions to caller
        - Processing time logged via verbose logger
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
    """Remove duplicate columns ending with numeric suffixes (e.g., SUBJID2, SUBJID3).
    
    This function implements intelligent duplicate detection:
    1. Identify columns matching pattern: base_name + optional '_' + digits
    2. Check if base column exists (e.g., SUBJID for SUBJID2)
    3. Compare content: remove if 100% identical OR entirely null
    4. Keep columns that have ANY differing values (even 1 row difference)
    
    This preserves intentional duplicate columns that contain different data.
    
    Args:
        df: DataFrame potentially containing duplicate columns.
    
    Returns:
        New DataFrame with duplicate columns removed. Original DataFrame unchanged.
        
    Example:
        >>> df = pd.DataFrame({
        ...     'SUBJID': [1, 2, 3],
        ...     'SUBJID2': [1, 2, 3],  # Identical → removed
        ...     'AGE': [25, 30, 35],
        ...     'AGE_1': [25, 30, 36]  # Different → kept
        ... })
        >>> cleaned = clean_duplicate_columns(df)
        >>> list(cleaned.columns)
        ['SUBJID', 'AGE', 'AGE_1']
        
    Notes:
        - Pattern matched: r'^(.+?)_?(\\d+)$' (e.g., SUBJID2, NAME_3, AGE1)
        - Columns removed if: entirely null OR 100% identical to base column
        - NaN-to-NaN comparisons handled correctly (both NaN → considered equal)
        - Comparison failures → column kept for safety
        - Removal reasons logged for each column (null vs. identical)
        - Returns copy; original DataFrame unmodified
        - If base column doesn't exist, numbered column is kept
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
    """Check if JSONL file is valid and readable.
    
    Performs three validation checks:
    1. File exists and is not empty (size > 0)
    2. First line is valid JSON
    3. First line parses to a non-empty dictionary
    
    Args:
        file_path: Path to JSONL file to validate.
    
    Returns:
        True if file is valid and readable, False otherwise.
        
    Example:
        >>> from pathlib import Path
        >>> valid = check_file_integrity(Path('output/file.jsonl'))  # doctest: +SKIP
        >>> if valid:  # doctest: +SKIP
        ...     print("File is valid, skipping reprocessing")  # doctest: +SKIP
        
    Notes:
        - Only validates first line (not entire file) for performance
        - Returns False for: missing files, empty files, corrupt JSON
        - Used to skip reprocessing existing valid files
        - Catches all I/O and JSON errors; never raises exceptions
        - Empty files (size=0) are considered invalid
    """
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
    """Extract all Excel files from dataset directory, creating original and cleaned JSONL versions.
    
    This is the main orchestration function that processes all Excel files in the
    configured datasets directory. It creates two versions of each dataset:
    - original/: Unmodified data with all columns
    - cleaned/: Duplicate columns removed
    
    The function validates configuration, discovers files, processes each file,
    tracks progress, and returns comprehensive results.
    
    Returns:
        Dictionary with extraction results:
            - 'files_found': Total Excel files discovered (int)
            - 'files_created': Number of JSONL files successfully created (int)
            - 'files_skipped': Files skipped (valid output already exists) (int)
            - 'total_records': Total data records processed (int)
            - 'errors': List of error messages (List[str])
            - 'processing_time': Total elapsed time in seconds (float)
    
    Example:
        >>> from scripts.extract_data import extract_excel_to_jsonl
        >>> result = extract_excel_to_jsonl()
        Found 50 Excel files to process...
        Processing files: 100%|██████| 50/50 [00:30<00:00]
        ✓ 10,000 total records processed
        
        >>> print(f"Created {result['files_created']} files")
        Created 50 files
        >>> print(f"Processed {result['total_records']} records")
        Processed 10,000 records
        
    Side Effects:
        - Creates {OUTPUT_DIR}/{STUDY_NAME}/original/ directory
        - Creates {OUTPUT_DIR}/{STUDY_NAME}/cleaned/ directory
        - Writes JSONL files for each Excel file (2 versions per file)
        - Prints progress to stdout via tqdm and print statements
        - Logs extensively via logging_system (INFO, DEBUG, ERROR levels)
        - Updates verbose logger with metrics and timing
        
    Notes:
        - Requires config.DATASETS_DIR, config.OUTPUT_DIR, config.STUDY_NAME
        - Returns error dict with 0 counts if configuration invalid
        - Validates file integrity before skipping (prevents using corrupt files)
        - Corrupted existing files trigger reprocessing with warning
        - Continues processing on individual file errors (resilient)
        - Empty directories return success with 0 files found
        - Progress tracked with tqdm progress bar
        - Total processing time included in results
        - Suitable for batch processing hundreds of files
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
