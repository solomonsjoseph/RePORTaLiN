# main.py
"""
RePORTaLiN Main Pipeline
========================

Central entry point for the data processing pipeline, orchestrating data dictionary loading,
Excel to JSONL extraction, and PHI/PII de-identification with comprehensive error handling.
"""
import argparse
import sys
from typing import Callable, Any
from pathlib import Path
from scripts.load_dictionary import load_study_dictionary
from scripts.extract_data import extract_excel_to_jsonl
from scripts.utils.deidentify import deidentify_dataset, DeidentificationConfig
from scripts.utils import logging as log
import config

__version__ = "0.0.1"

def run_step(step_name: str, func: Callable[[], Any]) -> Any:
    """
    Execute pipeline step with error handling and logging.
    
    Args:
        step_name: Name of the pipeline step
        func: Callable function to execute
        
    Returns:
        Result from the function, or exits with code 1 on error
    """
    try:
        log.info(f"--- {step_name} ---")
        result = func()
        
        # Check if result indicates failure
        if isinstance(result, bool) and not result:
            log.error(f"{step_name} failed.")
            sys.exit(1)
        elif isinstance(result, dict) and result.get('errors'):
            log.error(f"{step_name} completed with {len(result['errors'])} errors.")
            sys.exit(1)
        
        log.success(f"{step_name} completed successfully.")
        return result
    except Exception as e:
        log.error(f"Error in {step_name}: {e}", exc_info=True)
        sys.exit(1)

def main():
    """
    Main pipeline orchestrating dictionary loading, data extraction, and de-identification.
    
    Command-line Arguments:
        --skip-dictionary: Skip data dictionary loading
        --skip-extraction: Skip data extraction
        --enable-deidentification: Enable de-identification (disabled by default)
        --skip-deidentification: Skip de-identification even if enabled
        --no-encryption: Disable encryption for de-identification mappings
        -c, --countries: Country codes (e.g., IN US ID BR) or ALL
    """
    parser = argparse.ArgumentParser(
        prog='RePORTaLiN',
        description="RePORTaLiN pipeline for data processing.",
        epilog="For detailed documentation, see the Sphinx docs or README.md"
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                       help="Show program version and exit.")
    parser.add_argument('--skip-dictionary', action='store_true', 
                       help="Skip data dictionary loading (Step 0).")
    parser.add_argument('--skip-extraction', action='store_true', 
                       help="Skip data extraction (Step 1).")
    parser.add_argument('--skip-deidentification', action='store_true',
                       help="Skip de-identification of extracted data (Step 2).")
    parser.add_argument('--enable-deidentification', action='store_true',
                       help="Enable PHI/PII de-identification with encryption (disabled by default).")
    parser.add_argument('--no-encryption', action='store_true',
                       help="Disable encryption for de-identification mappings (testing only, not recommended).")
    parser.add_argument('-c', '--countries', nargs='+',
                       help="Country codes for de-identification (e.g., IN US ID BR) or ALL. Default: IN (India).")
    args = parser.parse_args()

    log.setup_logger(name=config.LOG_NAME, log_level=config.LOG_LEVEL)
    log.info("Starting RePORTaLiN pipeline...")

    if not args.skip_dictionary:
        run_step("Step 0: Loading Data Dictionary", 
                lambda: load_study_dictionary(
                    file_path=config.DICTIONARY_EXCEL_FILE, 
                    json_output_dir=config.DICTIONARY_JSON_OUTPUT_DIR
                ))
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
    elif args.skip_deidentification:
        log.info("--- Skipping Step 2: De-identification ---")
    else:
        log.info("--- De-identification disabled (use --enable-deidentification to enable) ---")

    log.info("RePORTaLiN pipeline finished.")

if __name__ == "__main__":
    main()
