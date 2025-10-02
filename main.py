# main.py
"""
RePORTaLiN Main Pipeline
========================

This module serves as the central entry point for the RePORTaLiN data processing pipeline.
It orchestrates the execution of multiple data processing steps, including data dictionary
loading and raw data extraction from Excel files to JSONL format.

The pipeline is designed to be robust, with comprehensive error handling, logging, and
the ability to skip individual steps for testing or partial execution.

Example:
    Run the full pipeline::

        $ python main.py

    Skip specific steps::

        $ python main.py --skip-dictionary
        $ python main.py --skip-extraction

See Also:
    :mod:`scripts.load_dictionary`: Data dictionary loading functionality
    :mod:`scripts.extract_data`: Excel to JSONL extraction functionality
    :mod:`config`: Configuration management

Author:
    RePORTaLiN Development Team

Version:
    1.0.0
"""

import argparse
import sys
from typing import Callable, Any
from scripts.load_dictionary import load_study_dictionary
from scripts.extract_data import extract_excel_to_jsonl
from scripts.utils import logging_utils as log
import config


def run_step(step_name: str, func: Callable[[], Any]) -> Any:
    """
    Execute a pipeline step with comprehensive error handling and logging.

    This function wraps any pipeline step with standardized error handling,
    logging, and success/failure reporting. It ensures consistent behavior
    across all pipeline stages.

    Args:
        step_name (str): Human-readable name of the pipeline step for logging
            purposes. Should be descriptive (e.g., "Step 0: Loading Data Dictionary").
        func (callable): A callable function that implements the pipeline step.
            The function should return a truthy value on success or raise an
            exception on failure.

    Returns:
        Any: The return value from the executed function if successful.

    Raises:
        SystemExit: If the function raises an exception, the error is logged
            and the program exits with code 1.

    Example:
        >>> def my_step():
        ...     print("Processing...")
        ...     return True
        >>> result = run_step("My Processing Step", my_step)
        --- My Processing Step ---
        Processing...
        SUCCESS: My Processing Step completed successfully.

    Note:
        All exceptions are caught, logged with full traceback information,
        and result in program termination to prevent cascading failures.
    """
    try:
        log.info(f"--- {step_name} ---")
        result = func()
        log.success(f"{step_name} completed successfully.")
        return result
    except Exception as e:
        log.error(f"Error in {step_name}: {e}", exc_info=True)
        sys.exit(1)

def main():
    """
    Main entry point for the RePORTaLiN data processing pipeline.

    This function orchestrates the complete data processing workflow, including:
    
    1. **Data Dictionary Loading** (Step 0): Processes the Excel-based data dictionary
       and converts it to JSONL format with automatic table detection and splitting.
    
    2. **Data Extraction** (Step 1): Extracts raw data from Excel files in the dataset
       directory and converts them to JSONL format with comprehensive validation.

    The pipeline features:
        - Dynamic dataset detection and configuration
        - Comprehensive logging with timestamped log files
        - Progress tracking with visual feedback
        - Graceful error handling and recovery
        - Ability to skip individual steps for testing

    Command-line Arguments:
        --skip-dictionary: Skip the data dictionary loading step (Step 0).
            Useful when the dictionary has already been processed and you only
            want to re-run data extraction.
        
        --skip-extraction: Skip the data extraction step (Step 1).
            Useful for testing dictionary processing in isolation.

    Environment Variables:
        LOG_LEVEL: Set logging verbosity (default: INFO)
        LOG_NAME: Custom logger name (default: "reportalin")

    Returns:
        None

    Raises:
        SystemExit: If any pipeline step fails, the program exits with code 1.

    Example:
        Run the complete pipeline::

            $ python main.py

        Skip data dictionary loading::

            $ python main.py --skip-dictionary

        Skip data extraction::

            $ python main.py --skip-extraction

    See Also:
        :func:`scripts.load_dictionary.load_study_dictionary`: Data dictionary processor
        :func:`scripts.extract_data.extract_excel_to_jsonl`: Data extraction function
        :mod:`config`: Configuration settings and paths

    Note:
        - All outputs are stored in the `results/` directory
        - Logs are saved to `.logs/` with timestamps
        - The pipeline automatically detects the dataset folder in `data/dataset/`
        - Processing is idempotent - files are skipped if they already exist
    """
    parser = argparse.ArgumentParser(
        description="RePORTaLiN pipeline for data processing.",
        epilog="For detailed documentation, see the Sphinx docs or README.md"
    )
    parser.add_argument('--skip-dictionary', action='store_true', 
                       help="Skip data dictionary loading (Step 0).")
    parser.add_argument('--skip-extraction', action='store_true', 
                       help="Skip data extraction (Step 1).")
    args = parser.parse_args()

    log.setup_logger(name=config.LOG_NAME, log_level=config.LOG_LEVEL)
    log.info("Starting RePORTaLiN pipeline...")

    if not args.skip_dictionary:
        run_step("Step 0: Loading Data Dictionary", 
                lambda: load_study_dictionary(config.DICTIONARY_EXCEL_FILE, config.DICTIONARY_JSON_OUTPUT_DIR))
    else:
        log.info("--- Skipping Step 0: Data Dictionary Loading ---")

    if not args.skip_extraction:
        run_step("Step 1: Extracting Raw Data to JSONL", extract_excel_to_jsonl)
    else:
        log.info("--- Skipping Step 1: Data Extraction ---")

    log.info("RePORTaLiN pipeline finished.")

if __name__ == "__main__":
    main()
