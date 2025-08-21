# config.py
"""
Central configuration file for the RePORTaLiN project.
All paths, settings, and parameters should be defined here.
"""
import os
from scripts.utils import logging_utils as log

# --- Project Root ---
# This assumes the script is run from the project's root directory.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Data and Results Directories ---
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")

# --- Step 0: Data Dictionary Paths ---
DICTIONARY_EXCEL_FILE = os.path.join(DATA_DIR, "data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx")
DICTIONARY_JSON_OUTPUT_DIR = os.path.join(DATA_DIR, "data_dictionary_and_mapping_specifications/json_output")

# --- Logging Configuration ---
LOG_LEVEL = log.logging.INFO
LOG_NAME = "reportalin"
