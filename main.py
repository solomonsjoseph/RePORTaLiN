# main.py
import argparse
import sys
from scripts.load_dictionary import load_study_dictionary
from scripts.utils import logging_utils as log
from extract_data import extract_excel_to_jsonl
import config

def run_dictionary_step():
    """Runs the data dictionary loading step."""
    try:
        log.info("--- Step 0: Loading Data Dictionary and Mapping Specification ---")
        success = load_study_dictionary(
            file_path=config.DICTIONARY_EXCEL_FILE,
            json_output_dir=config.DICTIONARY_JSON_OUTPUT_DIR
        )
        if success:
            log.success("Data dictionary processing completed successfully.")
        else:
            log.error("Data dictionary processing encountered issues.")
    except Exception as e:
        log.error(f"An error occurred during data dictionary loading: {e}", exc_info=True)
        sys.exit(1)

def run_extraction_step():
    """Runs the data extraction step."""
    try:
        log.info("--- Step 1: Extracting Raw Data to JSONL ---")
        extract_excel_to_jsonl()
        log.success("Data extraction completed successfully.")
    except Exception as e:
        log.error(f"An error occurred during data extraction: {e}", exc_info=True)
        sys.exit(1)

def main():
    # --- Argument Parser Setup ---
    parser = argparse.ArgumentParser(description="RePORTaLiN pipeline for data processing.")
    parser.add_argument(
        '--skip-dictionary', 
        action='store_true', 
        help="Skip the data dictionary loading step."
    )
    parser.add_argument(
        '--skip-extraction', 
        action='store_true', 
        help="Skip the data extraction step."
    )
    args = parser.parse_args()

    # --- Logger Initialization ---
    log.setup_logger(name=config.LOG_NAME, log_level=config.LOG_LEVEL)
    log.info("Starting RePORTaLiN pipeline...")

    # --- Step 0: Load Data Dictionary ---
    if not args.skip_dictionary:
        run_dictionary_step()
    else:
        log.info("--- Skipping Step 0: Data Dictionary Loading ---")

    # --- Step 1: Extract Raw Data ---
    if not args.skip_extraction:
        run_extraction_step()
    else:
        log.info("--- Skipping Step 1: Data Extraction ---")

    log.info("RePORTaLiN pipeline finished.")

if __name__ == "__main__":
    main()
