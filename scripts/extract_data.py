#!/usr/bin/env python3
"""
Data Extraction Module
======================

Extracts raw data from Excel files and converts to JSONL format with
type conversion, progress tracking, and error recovery.

This module provides robust Excel-to-JSONL conversion with duplicate column
handling, data validation, and comprehensive error recovery.

Example:
    Basic usage::

        from scripts.extract_data import extract_excel_to_jsonl
        
        # Extract all Excel files from dataset directory
        result = extract_excel_to_jsonl()
        print(f"Processed {result['files_created']} files")
        print(f"Total records: {result['total_records']}")

    Programmatic usage::

        from scripts.extract_data import process_excel_file, find_excel_files
        from pathlib import Path
        
        # Find Excel files
        excel_files = find_excel_files("data/dataset/Indo-vap")
        
        # Process individual file
        for file in excel_files:
            success, count, error = process_excel_file(file, "results/dataset")
            if success:
                print(f"{file.name}: {count} records")

Key Features:
    - Dual output: Creates both original and cleaned JSONL versions
    - Duplicate column removal: Intelligently removes SUBJID2, SUBJID3, etc.
    - Type conversion: Handles pandas/numpy types, dates, NaN values
    - Integrity checks: Validates output files before skipping
    - Error recovery: Continues processing even if individual files fail
    - Progress tracking: Real-time progress bars
"""
import os
import sys
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from tqdm import tqdm
from scripts.utils import logging as log
import config

__all__ = [
    # Main Functions
    'extract_excel_to_jsonl',
    # File Processing
    'process_excel_file',
    'find_excel_files',
    # Data Conversion
    'convert_dataframe_to_jsonl',
    'clean_record_for_json',
    'clean_duplicate_columns',
]

def clean_record_for_json(record: dict) -> dict:
    """Convert pandas record to JSON-serializable types."""
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
    """Find all Excel files (.xlsx) in the specified directory."""
    return list(Path(directory).glob("*.xlsx"))

def is_dataframe_empty(df: pd.DataFrame) -> bool:
    """Check if DataFrame is completely empty (no rows AND no columns)."""
    return len(df.columns) == 0 and len(df) == 0

def convert_dataframe_to_jsonl(df: pd.DataFrame, output_file: Path, source_filename: str) -> int:
    """Convert DataFrame to JSONL format, handling empty DataFrames with column metadata."""
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
    """Process Excel file to JSONL format, creating both original and cleaned versions."""
    try:
        # Create separate directories for original and cleaned files
        original_dir = Path(output_dir) / "original"
        cleaned_dir = Path(output_dir) / "cleaned"
        original_dir.mkdir(exist_ok=True)
        cleaned_dir.mkdir(exist_ok=True)
        
        output_file = original_dir / f"{excel_file.stem}.jsonl"
        output_file_cleaned = cleaned_dir / f"{excel_file.stem}.jsonl"
        
        # Use openpyxl engine for better performance with .xlsx files
        df = pd.read_excel(excel_file, engine='openpyxl')
        if is_dataframe_empty(df):
            tqdm.write(f"  ⊘ Skipping {excel_file.name} (empty)")
            return False, 0, None
        
        # Save original version
        records_count = convert_dataframe_to_jsonl(df, output_file, excel_file.name)
        tqdm.write(f"  ✓ Created original/{output_file.name} with {records_count} rows (original)")
        
        # Clean duplicate columns like SUBJID2, SUBJID3, etc. and save cleaned version
        df_cleaned = clean_duplicate_columns(df)
        records_count_cleaned = convert_dataframe_to_jsonl(df_cleaned, output_file_cleaned, excel_file.name)
        tqdm.write(f"  ✓ Created cleaned/{output_file_cleaned.name} with {records_count_cleaned} rows (cleaned)")
        
        return True, records_count, None
    except Exception as e:
        error_msg = f"Error processing {excel_file.name}: {str(e)}"
        tqdm.write(f"  ✗ {error_msg}")
        return False, 0, error_msg

def clean_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate columns ending with numeric suffixes (e.g., SUBJID2, SUBJID3).
    
    Only removes columns if:
    1. Column name ends with optional underscore and digits (e.g., SUBJID2, NAME_3)
    2. Base column name exists (e.g., SUBJID, NAME)
    3. Content is identical to base column OR column is entirely null
    
    This prevents accidental removal of legitimate columns that happen to end with numbers.
    """
    columns_to_keep = []
    columns_to_remove = []
    
    for col in df.columns:
        # Match columns ending with optional underscore and digits
        match = re.match(r'^(.+?)_?(\d+)$', str(col))
        
        if match:
            base_name = match.group(1)
            # Only remove if base column exists AND content is duplicate/empty
            if base_name in df.columns:
                try:
                    # Check if column is entirely null or identical to base column
                    if df[col].isna().all() or df[col].equals(df[base_name]):
                        columns_to_remove.append(col)
                        log.debug(f"Marking {col} for removal (duplicate of {base_name})")
                    else:
                        # Column has different data, keep it
                        columns_to_keep.append(col)
                        log.debug(f"Keeping {col} (different from {base_name})")
                except Exception as e:
                    # If comparison fails, keep the column to be safe
                    columns_to_keep.append(col)
                    log.warning(f"Could not compare {col} with {base_name}: {e}")
            else:
                # Base column doesn't exist, keep this column
                columns_to_keep.append(col)
        else:
            # Column name doesn't match pattern, keep it
            columns_to_keep.append(col)
    
    if columns_to_remove:
        tqdm.write(f"    → Removing duplicate columns: {', '.join(columns_to_remove)}")
        log.info(f"Removed {len(columns_to_remove)} duplicate columns: {', '.join(columns_to_remove)}")
    
    return df[columns_to_keep].copy()

def check_file_integrity(file_path: Path) -> bool:
    """Check if JSONL file is valid and readable."""
    try:
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
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
    
    Returns:
        Dictionary with extraction statistics
    """
    os.makedirs(config.CLEAN_DATASET_DIR, exist_ok=True)
    excel_files = find_excel_files(config.DATASET_DIR)
    
    if not excel_files:
        log.warning(f"No Excel files found in {config.DATASET_DIR}")
        print(f"No Excel files found in {config.DATASET_DIR}")
        return {"files_found": 0, "files_created": 0, "files_skipped": 0, 
                "total_records": 0, "errors": []}
    
    log.info(f"Found {len(excel_files)} Excel files to process")
    log.debug(f"Excel files: {[f.name for f in excel_files[:10]]}{'...' if len(excel_files) > 10 else ''}")
    print(f"Found {len(excel_files)} Excel files to process...")
    total_records, files_created, files_skipped, errors = 0, 0, 0, []
    
    # Progress bar for processing files
    for excel_file in tqdm(excel_files, desc="Processing files", unit="file",
                           file=sys.stdout, dynamic_ncols=True, leave=True,
                           bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'):
        # Check if files already exist in both original and cleaned directories
        original_file = Path(config.CLEAN_DATASET_DIR) / "original" / f"{excel_file.stem}.jsonl"
        cleaned_file = Path(config.CLEAN_DATASET_DIR) / "cleaned" / f"{excel_file.stem}.jsonl"
        
        # Check if files exist AND have valid content (integrity check)
        if (original_file.exists() and cleaned_file.exists() and
            check_file_integrity(original_file) and check_file_integrity(cleaned_file)):
            files_skipped += 1
            tqdm.write(f"  ⊙ Skipping {excel_file.name} (valid output already exists)")
            log.debug(f"Skipping {excel_file.name} - valid output exists")
            continue
        
        # If files exist but are corrupted, warn and reprocess
        if original_file.exists() or cleaned_file.exists():
            tqdm.write(f"  ⚠ Re-processing {excel_file.name} (existing files are corrupted or incomplete)")
            log.warning(f"Re-processing {excel_file.name} - existing files corrupted")
            
        tqdm.write(f"Processing: {excel_file.name}")
        log.debug(f"Processing {excel_file.name}")
        success, records_count, error_msg = process_excel_file(excel_file, config.CLEAN_DATASET_DIR)
        if success:
            files_created += 1
            total_records += records_count
            log.debug(f"Successfully processed {excel_file.name}: {records_count} records")
        elif error_msg:
            errors.append(error_msg)
            log.error(f"Failed to process {excel_file.name}: {error_msg}")
    
    # Summary
    print(f"\nExtraction complete:")
    print(f"  ✓ {total_records} total records processed")
    print(f"  ✓ {files_created} JSONL files created")
    print(f"  ⊙ {files_skipped} files skipped (already exist)")
    print(f"  → Output directory: {config.CLEAN_DATASET_DIR}")
    if errors:
        print(f"  ✗ {len(errors)} files had errors")
        log.error(f"{len(errors)} files had errors during extraction")
    
    log.info(f"Extraction complete: {total_records} records, {files_created} files created, {files_skipped} skipped")
    
    return {
        "files_found": len(excel_files),
        "files_created": files_created,
        "files_skipped": files_skipped,
        "total_records": total_records,
        "errors": errors
    }


if __name__ == "__main__":
    # Initialize logger when running as standalone script
    log.setup_logger(name="extract_data", log_level=config.LOG_LEVEL if hasattr(config, 'LOG_LEVEL') else 20)
    
    result = extract_excel_to_jsonl()
    
    # Exit with appropriate code based on results
    if result["errors"]:
        log.error(f"Extraction completed with {len(result['errors'])} errors")
        sys.exit(1)
    elif result["files_created"] == 0 and result["files_found"] > 0:
        log.warning("No files were processed (all were skipped)")
        sys.exit(0)
    else:
        log.success(f"Extraction successful: {result['files_created']} files created, {result['total_records']} records processed")
        sys.exit(0)
