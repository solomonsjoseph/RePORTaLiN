# config.py
"""
RePORTaLiN Configuration Module
================================

This module provides centralized configuration management for the RePORTaLiN project.
All paths, settings, and parameters are defined here to ensure consistency across
all pipeline components.

The configuration system features:
    - Dynamic dataset detection from the file system
    - Automatic path resolution relative to project root
    - Organized output structure in results directory
    - Flexible logging configuration

Architecture:
    The configuration uses a hierarchical directory structure:
    
    - **data/**: Raw input data
        - **dataset/<dataset_name>/**: Excel source files
        - **data_dictionary_and_mapping_specifications/**: Data dictionary Excel files
    
    - **results/**: Processed outputs
        - **dataset/<dataset_name>/**: Extracted JSONL files
        - **data_dictionary_mappings/**: Dictionary tables in JSONL format

Configuration Variables:
    ROOT_DIR (str): Absolute path to project root directory
    DATA_DIR (str): Path to raw data directory
    RESULTS_DIR (str): Path to output results directory
    DATASET_DIR (str): Path to current dataset directory
    DATASET_NAME (str): Name of the current dataset (e.g., "Indo-vap")
    CLEAN_DATASET_DIR (str): Path to output directory for processed dataset
    DICTIONARY_EXCEL_FILE (str): Path to data dictionary Excel file
    DICTIONARY_JSON_OUTPUT_DIR (str): Output directory for dictionary JSONL files
    LOG_LEVEL (int): Logging verbosity level (default: logging.INFO)
    LOG_NAME (str): Logger instance name (default: "reportalin")

Example:
    Import and use configuration::

        import config
        
        # Use predefined paths
        print(f"Dataset: {config.DATASET_NAME}")
        print(f"Input: {config.DATASET_DIR}")
        print(f"Output: {config.CLEAN_DATASET_DIR}")

Note:
    - The configuration automatically detects the first folder in `data/dataset/`
    - If no dataset folder is found, it falls back to "Indo-vap_csv_files"
    - Output directories are created automatically by the pipeline

See Also:
    :mod:`main`: Main pipeline entry point
    :mod:`scripts.utils.logging_utils`: Logging configuration

Author:
    RePORTaLiN Development Team

Version:
    1.0.0
"""
import os
from pathlib import Path
from typing import Optional
from scripts.utils import logging_utils as log

# --- Project Root ---
# This assumes the script is run from the project's root directory.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Data and Results Directories ---
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")

# --- Step 1: Dataset and Output Paths ---
# Dynamically get the dataset folder name from data/dataset/
DATASET_BASE_DIR = os.path.join(DATA_DIR, "dataset")

# Get the first folder in the dataset directory (e.g., "Indo-vap_csv_files")
def get_dataset_folder() -> Optional[str]:
    """
    Dynamically detect the dataset folder name from the file system.

    This function scans the `data/dataset/` directory and returns the name of
    the first subdirectory found (excluding hidden folders starting with '.').
    This enables the pipeline to work with different datasets without hardcoding
    folder names.

    Returns:
        str or None: The name of the first dataset folder found, or None if
            the dataset base directory doesn't exist or contains no subdirectories.

    Example:
        >>> # Assuming data/dataset/Indo-vap_csv_files/ exists
        >>> folder = get_dataset_folder()
        >>> print(folder)
        'Indo-vap_csv_files'

    Note:
        - Only visible directories are detected (hidden folders are ignored)
        - If multiple folders exist, only the first one is returned (sorted alphabetically)
        - The function does not validate folder contents
        - Path traversal protection: validates folder name doesn't contain '..'
    """
    if not os.path.exists(DATASET_BASE_DIR):
        return None
    
    try:
        folders = [
            f for f in os.listdir(DATASET_BASE_DIR) 
            if (os.path.isdir(os.path.join(DATASET_BASE_DIR, f)) 
                and not f.startswith('.') 
                and '..' not in f)  # Security: prevent path traversal
        ]
        if folders:
            # Sort alphabetically for deterministic behavior
            return sorted(folders)[0]
    except (OSError, PermissionError) as e:
        log.error(f"Error accessing dataset directory: {e}")
    
    return None

DATASET_FOLDER_NAME = get_dataset_folder()

if DATASET_FOLDER_NAME:
    DATASET_DIR = os.path.join(DATASET_BASE_DIR, DATASET_FOLDER_NAME)
    # Extract dataset name without suffix (e.g., "Indo-vap_csv_files" -> "Indo-vap")
    DATASET_NAME = DATASET_FOLDER_NAME.replace('_csv_files', '').replace('_files', '')
    # Organize results: results/dataset/<dataset_name>/
    CLEAN_DATASET_DIR = os.path.join(RESULTS_DIR, "dataset", DATASET_NAME)
else:
    # Fallback if no dataset folder found
    DATASET_DIR = os.path.join(DATASET_BASE_DIR, "Indo-vap_csv_files")
    DATASET_NAME = "Indo-vap"
    CLEAN_DATASET_DIR = os.path.join(RESULTS_DIR, "dataset", DATASET_NAME)

# --- Step 0: Data Dictionary Paths ---
DICTIONARY_EXCEL_FILE = os.path.join(DATA_DIR, "data_dictionary_and_mapping_specifications", "RePORT_DEB_to_Tables_mapping.xlsx")
DICTIONARY_JSON_OUTPUT_DIR = os.path.join(RESULTS_DIR, "data_dictionary_mappings")

# --- Logging Configuration ---
LOG_LEVEL = log.logging.INFO
LOG_NAME = "reportalin"
