#!/usr/bin/env python3
"""
extract_data.py

Step 1: Extract Raw Data to JSONL

This script reads all Excel files from the dataset directory, converts each row
into a JSON object, and saves them to separate JSONL files with the same name
as the Excel file. Skips completely empty files.

Author: Generated for RePORTaLiN project
Date: September 29, 2025
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple, Optional
import config


def convert_nan_to_none(obj):
    """
    Convert pandas NaN values to None for proper JSON serialization.
    
    Args:
        obj: Object that may contain NaN values
        
    Returns:
        Object with NaN values converted to None
    """
    if pd.isna(obj):
        return None
    return obj


def clean_record_for_json(record: dict) -> dict:
    """
    Clean a record dictionary by converting NaN values to None and handling datetime objects.
    
    Args:
        record: Dictionary that may contain NaN values and datetime objects
        
    Returns:
        Dictionary with NaN values converted to None and datetime objects to strings
    """
    cleaned_record = {}
    for key, value in record.items():
        if pd.isna(value):
            cleaned_record[key] = None
        elif isinstance(value, (np.integer, np.floating)):
            # Convert numpy types to Python types
            if pd.isna(value):
                cleaned_record[key] = None
            else:
                cleaned_record[key] = value.item()
        elif isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
            # Convert datetime-like objects to strings
            cleaned_record[key] = str(value)
        elif hasattr(value, 'isoformat'):
            # Handle other datetime-like objects with isoformat method
            cleaned_record[key] = value.isoformat()
        elif hasattr(value, '__str__') and 'datetime' in str(type(value)).lower():
            # Fallback for any datetime-like objects
            cleaned_record[key] = str(value)
        else:
            cleaned_record[key] = value
    return cleaned_record


def find_excel_files(directory: str) -> List[Path]:
    """
    Find all Excel files in the specified directory.
    
    Args:
        directory: Path to the directory to search
        
    Returns:
        List of Path objects for Excel files found
    """
    dataset_path = Path(directory)
    return list(dataset_path.glob("*.xlsx"))


def is_dataframe_empty(df: pd.DataFrame) -> bool:
    """
    Check if a dataframe is completely empty (no rows AND no columns).
    
    Files with column headers but no data rows are still valuable as they 
    contain metadata about the expected structure, so we only skip files
    that are truly empty (no structure at all).
    
    Args:
        df: DataFrame to check
        
    Returns:
        True only if dataframe has no rows AND no columns
    """
    return len(df.columns) == 0 and len(df) == 0


def create_output_path(input_file: Path, output_dir: str) -> Path:
    """
    Create the output file path for a given input Excel file.
    
    Args:
        input_file: Path to the input Excel file
        output_dir: Directory where output file should be created
        
    Returns:
        Path object for the output JSONL file
    """
    output_filename = input_file.stem + ".jsonl"
    return Path(output_dir) / output_filename


def convert_dataframe_to_jsonl(df: pd.DataFrame, output_file: Path, source_filename: str) -> int:
    """
    Convert a DataFrame to JSONL format and write to file.
    
    For files with no data rows but column headers, creates a metadata record
    to preserve the column structure information. Converts all NaN values to null.
    
    Args:
        df: DataFrame to convert
        output_file: Path where JSONL file should be written
        source_filename: Name of the source Excel file
        
    Returns:
        Number of records written
    """
    records_written = 0
    
    with open(output_file, 'w', encoding='utf-8') as jsonl_file:
        if len(df) == 0 and len(df.columns) > 0:
            # File has column headers but no data - create a metadata record
            metadata_record = {col: None for col in df.columns}
            metadata_record["source_file"] = source_filename
            metadata_record["_metadata"] = {
                "type": "column_structure", 
                "columns": list(df.columns),
                "note": "File contains column headers but no data rows"
            }
            
            json_line = json.dumps(metadata_record, ensure_ascii=False)
            jsonl_file.write(json_line + '\n')
            records_written += 1
        else:
            # Normal processing for files with data
            for _, row in df.iterrows():
                # Convert row to dictionary and clean NaN values
                record = row.to_dict()
                record["source_file"] = source_filename
                
                # Clean NaN values
                cleaned_record = clean_record_for_json(record)
                
                # Write as JSON line
                json_line = json.dumps(cleaned_record, ensure_ascii=False)
                jsonl_file.write(json_line + '\n')
                records_written += 1
    
    return records_written


def process_excel_file(excel_file: Path, output_dir: str) -> Tuple[bool, int, Optional[str]]:
    """
    Process a single Excel file and convert it to JSONL.
    
    Args:
        excel_file: Path to the Excel file to process
        output_dir: Directory where output file should be created
        
    Returns:
        Tuple of (success, records_count, error_message)
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Check if file is empty
        if is_dataframe_empty(df):
            print(f"  - Skipping {excel_file.name} (empty)")
            return False, 0, None
        
        # Create output file path
        output_file = create_output_path(excel_file, output_dir)
        
        # Convert and write to JSONL
        records_count = convert_dataframe_to_jsonl(df, output_file, excel_file.name)
        
        print(f"  - Created {output_file.name} with {records_count} rows")
        return True, records_count, None
        
    except Exception as e:
        error_msg = f"Error processing {excel_file.name}: {str(e)}"
        print(f"  - {error_msg}")
        return False, 0, error_msg


def extract_excel_to_jsonl():
    """
    Extract all Excel files from the dataset directory and convert to separate JSONL files.
    
    This function orchestrates the entire extraction process:
    1. Finds all Excel files in the dataset directory
    2. Processes each file individually
    3. Reports the results
    """
    # Ensure the output directory exists
    os.makedirs(config.CLEAN_CORPUS_DIR, exist_ok=True)
    
    # Find all Excel files
    excel_files = find_excel_files(config.DATASET_DIR)
    
    if not excel_files:
        print(f"No Excel files found in {config.DATASET_DIR}")
        return
    
    print(f"Found {len(excel_files)} Excel files to process...")
    
    # Process each file and collect results
    total_records = 0
    files_created = 0
    errors = []
    
    for excel_file in excel_files:
        print(f"Processing: {excel_file.name}")
        
        success, records_count, error_msg = process_excel_file(excel_file, config.CLEAN_CORPUS_DIR)
        
        if success:
            files_created += 1
            total_records += records_count
        elif error_msg:
            errors.append(error_msg)
    
    # Report final results
    print(f"\nExtraction complete:")
    print(f"  - {total_records} total records processed")
    print(f"  - {files_created} JSONL files created in: {config.CLEAN_CORPUS_DIR}")
    
    if errors:
        print(f"  - {len(errors)} files had errors")


if __name__ == "__main__":
    extract_excel_to_jsonl()
