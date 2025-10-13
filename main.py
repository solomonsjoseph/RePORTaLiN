# main.py
"""
RePORTaLiN Main Pipeline
========================

This module serves as the central entry point for the RePORTaLiN data processing pipeline.
It orchestrates the execution of multiple data processing steps, including data dictionary
loading, raw data extraction from Excel files to JSONL format, and de-identification of
Protected Health Information (PHI) and Personally Identifiable Information (PII).

The pipeline is designed to be robust, with comprehensive error handling, logging, and
the ability to skip individual steps for testing or partial execution.

Example:
    Run the full pipeline::

        $ python main.py

    Run with de-identification::

        $ python main.py --enable-deidentification

    Skip specific steps::

        $ python main.py --skip-dictionary
        $ python main.py --skip-extraction
        $ python main.py --enable-deidentification --skip-deidentification

See Also:
    :mod:`scripts.load_dictionary`: Data dictionary loading functionality
    :mod:`scripts.extract_data`: Excel to JSONL extraction functionality
    :mod:`scripts.utils.deidentify`: PHI/PII de-identification functionality
    :mod:`config`: Configuration management

Author:
    RePORTaLiN Development Team

Version:
    0.0.1
"""

import argparse
import sys
from typing import Callable, Any
from pathlib import Path
from scripts.load_dictionary import load_study_dictionary
from scripts.extract_data import extract_excel_to_jsonl
from scripts.utils.deidentify import deidentify_dataset, DeidentificationConfig
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
    
    3. **De-identification** (Step 2, optional): Removes PHI/PII from extracted data
       using pseudonymization with encrypted mapping storage. Disabled by default.

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
        
        --enable-deidentification: Enable de-identification step (Step 2).
            De-identification is disabled by default. Use this flag to enable it.
        
        --skip-deidentification: Skip de-identification even if enabled.
            Useful for testing other steps without de-identification.
        
        --no-encryption: Disable encryption for de-identification mappings.
            Encryption is ENABLED BY DEFAULT for security.
            This flag disables it - not recommended for production use.
        
        -c, --countries: Specify country codes for de-identification (e.g., IN US ID BR).
            Use 'ALL' for all supported countries. Default: IN (India).
            Supported: US, EU, GB, CA, AU, IN, ID, BR, PH, ZA, KE, NG, GH, UG.

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

        Run with de-identification::

            $ python main.py --enable-deidentification

        Skip data dictionary loading::

            $ python main.py --skip-dictionary

        De-identify without encryption (testing only)::

            $ python main.py --enable-deidentification --no-encryption

        De-identify with specific countries::

            $ python main.py --enable-deidentification --countries IN US ID

        De-identify with all supported countries::

            $ python main.py --enable-deidentification --countries ALL

    See Also:
        :func:`scripts.load_dictionary.load_study_dictionary`: Data dictionary processor
        :func:`scripts.extract_data.extract_excel_to_jsonl`: Data extraction function
        :func:`scripts.utils.deidentify.deidentify_dataset`: De-identification function
        :mod:`config`: Configuration settings and paths

    Note:
        - All outputs are stored in the `results/` directory
        - Logs are saved to `.logs/` with timestamps
        - The pipeline automatically detects the dataset folder in `data/dataset/`
        - Processing is idempotent - files are skipped if they already exist
        - De-identification mappings are encrypted and stored separately
    """
    parser = argparse.ArgumentParser(
        description="RePORTaLiN pipeline for data processing.",
        epilog="For detailed documentation, see the Sphinx docs or README.md"
    )
    parser.add_argument('--skip-dictionary', action='store_true', 
                       help="Skip data dictionary loading (Step 0).")
    parser.add_argument('--skip-extraction', action='store_true', 
                       help="Skip data extraction (Step 1).")
    parser.add_argument('--skip-deidentification', action='store_true',
                       help="Skip de-identification of extracted data (Step 2).")
    parser.add_argument('--enable-deidentification', action='store_true',
                       help="Enable de-identification (disabled by default for testing).")
    parser.add_argument('--no-encryption', action='store_true',
                       help="Disable encryption for de-identification mappings (encryption enabled by default).")
    parser.add_argument('-c', '--countries', nargs='+',
                       help="Country codes for de-identification (e.g., IN US ID BR) or ALL. Default: IN (India).")
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

    # De-identification step (opt-in for now)
    if args.enable_deidentification and not args.skip_deidentification:
        def run_deidentification():
            # Input directory contains original/ and cleaned/ subdirectories
            input_dir = Path(config.CLEAN_DATASET_DIR)
            
            # Output to dedicated deidentified directory within results
            output_dir = Path(config.RESULTS_DIR) / "deidentified" / config.DATASET_NAME
            
            log.info(f"De-identifying dataset: {input_dir} -> {output_dir}")
            log.info(f"Processing both 'original' and 'cleaned' subdirectories...")
            
            # Parse countries argument
            countries = None
            if args.countries:
                if "ALL" in [c.upper() for c in args.countries]:
                    countries = ["ALL"]
                else:
                    countries = [c.upper() for c in args.countries]
            
            # Configure de-identification
            deid_config = DeidentificationConfig(
                enable_encryption=not args.no_encryption,
                enable_date_shifting=True,
                enable_validation=True,
                log_level=config.LOG_LEVEL,
                countries=countries,
                enable_country_patterns=True
            )
            
            # Log configuration
            country_display = countries or ["IN (default)"]
            log.info(f"Countries: {', '.join(country_display)}")
            
            # Run de-identification (will process subdirectories recursively)
            stats = deidentify_dataset(
                input_dir=input_dir,
                output_dir=output_dir,
                config=deid_config,
                process_subdirs=True  # Enable recursive processing
            )
            
            log.info(f"De-identification complete:")
            log.info(f"  Texts processed: {stats.get('texts_processed', 0)}")
            log.info(f"  Total detections: {stats.get('total_detections', 0)}")
            log.info(f"  Countries: {', '.join(stats.get('countries', ['N/A']))}")
            log.info(f"  Unique mappings: {stats.get('total_mappings', 0)}")
            log.info(f"  Output structure:")
            log.info(f"    - {output_dir}/original/  (de-identified original files)")
            log.info(f"    - {output_dir}/cleaned/   (de-identified cleaned files)")
            
            return stats
        
        run_step("Step 2: De-identifying PHI/PII", run_deidentification)
    elif not args.enable_deidentification:
        log.info("--- De-identification disabled (use --enable-deidentification to enable) ---")
    else:
        log.info("--- Skipping Step 2: De-identification ---")

    log.info("RePORTaLiN pipeline finished.")

if __name__ == "__main__":
    main()
