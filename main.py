# main.py

from scripts.load_dictionary import load_study_dictionary
from scripts.utils import logging_utils as log
import sys
import os

def main():
    # Initialize the logger at the start of the program
    logger = log.setup_logger(name="reportalin", log_level=log.logging.INFO)
    log.info("Starting RePORTaLiN pipeline")
    
    try:
        log.info("Step 0: Loading Data Dictionary and Mapping Specification...")
        # Use defaults or pass file_path and json_output_dir; preserve_na defaults to True.
        success = load_study_dictionary(file_path=None, json_output_dir=None)
        if success:
            log.success("Data dictionary processing completed successfully and saved as JSONL files.")
        else:
            log.error("Data dictionary processing encountered issues")

        log.info("Step 1: Parsing Annotated PDFs...")
        # Future implementation...
        
    except Exception as e:
        log.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
