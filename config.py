# config.py
"""
RePORTaLiN Configuration Module
================================

Centralized configuration management with dynamic dataset detection,
automatic path resolution, and flexible logging configuration.
"""
import os
import logging
from typing import Optional

# Project paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
DATASET_BASE_DIR = os.path.join(DATA_DIR, "dataset")

def get_dataset_folder() -> Optional[str]:
    """
    Detect first dataset folder in data/dataset/, excluding hidden folders.
    
    Returns:
        Name of the first dataset folder found, or None if none exists
    """
    if not os.path.exists(DATASET_BASE_DIR):
        return None
    
    try:
        folders = [f for f in os.listdir(DATASET_BASE_DIR) 
                  if os.path.isdir(os.path.join(DATASET_BASE_DIR, f)) 
                  and not f.startswith('.') and '..' not in f]
        return sorted(folders)[0] if folders else None
    except (OSError, PermissionError):
        # Silently return None on errors during config initialization
        # Logging will be available later after logger is set up
        return None

# Dataset configuration
DATASET_FOLDER_NAME = get_dataset_folder()
DATASET_DIR = os.path.join(DATASET_BASE_DIR, DATASET_FOLDER_NAME or "RePORTaLiN_sample")
DATASET_NAME = (DATASET_FOLDER_NAME.replace('_csv_files', '').replace('_files', '') 
                if DATASET_FOLDER_NAME else "RePORTaLiN_sample")
CLEAN_DATASET_DIR = os.path.join(RESULTS_DIR, "dataset", DATASET_NAME)

# Data dictionary paths
DICTIONARY_EXCEL_FILE = os.path.join(DATA_DIR, "data_dictionary_and_mapping_specifications", 
                                     "RePORT_DEB_to_Tables_mapping.xlsx")
DICTIONARY_JSON_OUTPUT_DIR = os.path.join(RESULTS_DIR, "data_dictionary_mappings")

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_NAME = "reportalin"
