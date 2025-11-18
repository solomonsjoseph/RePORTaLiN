#!/usr/bin/env python3
"""Clinical data processing pipeline for RePORTaLiN.

This module provides the main entry point for the RePORTaLiN (Report India) 
clinical study data processing pipeline. It orchestrates a multi-step workflow
that transforms raw Excel datasets into clean, structured, and optionally 
de-identified JSONL records suitable for analysis and vector database ingestion.

The pipeline consists of the following stages:
    1. **Dictionary Loading (Step 0):** Parse and validate the data dictionary
       Excel file to understand field definitions, types, and constraints.
    2. **Data Extraction (Step 1):** Convert Excel datasets to JSONL format,
       applying validation rules and creating both original and cleaned outputs.
    3. **De-identification (Step 2):** Optional PHI/PII removal using country-
       specific regex patterns, encryption, and date-shifting techniques.
    4. **Vector DB Ingestion (Optional):** Embed PDF forms and JSONL records
       into a vector database for semantic search capabilities.

Architecture:
    The pipeline follows a fail-fast philosophy. Each step is wrapped in error
    handling via `run_step()`, which logs progress and exits immediately on 
    failure. Configuration is centralized in `config.py`, and all operations
    are logged to both console and `.logs/` directory.

Security:
    - De-identification uses Fernet encryption (AES-128) for mapping storage
    - Date shifting applies consistent random offsets per patient
    - Country-specific patterns (Aadhaar, SSN, etc.) are validated via regex
    - All encryption keys are managed securely in `config.py`

Usage:
    Run the complete pipeline:
        $ python main.py
    
    Skip dictionary loading and enable de-identification:
        $ python main.py --skip-dictionary --enable-deidentification
    
    Process multiple countries with verbose logging:
        $ python main.py -c IN US BR --verbose
    
    Ingest PDFs to vector database (dry run):
        $ python main.py --ingest-pdfs --dry-run

Example:
    >>> # Basic pipeline execution (requires data setup)
    >>> # This is a conceptual example - actual execution requires data files
    >>> import sys
    >>> sys.argv = ['main.py', '--version']
    >>> # Would display: RePORTaLiN <version>

Notes:
    - Requires Python 3.13+ for compatibility with dependencies
    - All data paths are configured in `config.py`
    - Shell completion available if `argcomplete` is installed
    - See README.md and Sphinx docs for detailed setup instructions

See Also:
    config.py: Central configuration and path management
    scripts.load_dictionary: Data dictionary parsing logic
    scripts.extract_data: Excel to JSONL conversion
    scripts.deidentify: PHI/PII de-identification engine
"""
import argparse
import logging
import sys
from typing import Callable, Any
from pathlib import Path
from scripts.load_dictionary import load_study_dictionary
from scripts.extract_data import extract_excel_to_jsonl
from scripts.deidentify import deidentify_dataset, DeidentificationConfig
from scripts.utils import logging_system as log
# Vector database ingestion modules (v0.3.0)
from scripts.vector_db.ingest_pdfs import ingest_pdfs_to_vectordb
from scripts.vector_db.ingest_records import ingest_records_to_vectordb
import config

try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

from __version__ import __version__

__all__ = ['main', 'run_step']

def run_step(step_name: str, func: Callable[[], Any]) -> Any:
    """Execute a pipeline step with comprehensive error handling and logging.
    
    This function wraps individual pipeline steps to provide consistent error
    handling, logging, and exit behavior. It acts as the pipeline's safety net,
    ensuring that any failure in a step is caught, logged, and results in a
    clean exit with a non-zero status code.
    
    The function supports multiple failure modes:
    - Boolean `False` return values indicate step failure
    - Dict results with an 'errors' key indicate partial failure
    - Uncaught exceptions are logged with full stack traces
    
    All steps are logged with clear start/success/failure messages to both
    console and log files (see `config.LOG_NAME` for log file location).
    
    Args:
        step_name (str): Human-readable name of the pipeline step (e.g., 
            "Step 1: Extracting Raw Data to JSONL"). Used in log messages
            and error reporting.
        func (Callable[[], Any]): Zero-argument callable that executes the
            actual step logic. This should be a lambda or function reference
            that performs the work and returns a result or raises an exception.
    
    Returns:
        Any: The return value from `func()` if successful. Return type depends
            on the specific step being executed (e.g., dict with statistics,
            bool for success/failure, or None).
    
    Raises:
        SystemExit: Always raised on failure (exit code 1). This terminates
            the entire pipeline to prevent cascading errors from invalid data.
            Reasons for exit:
            - `func()` returns `False`
            - `func()` returns a dict with non-empty 'errors' list
            - `func()` raises any exception
    
    Example:
        >>> import logging
        >>> from scripts.utils import logging_system as log
        >>> log.setup_logger(name='test', log_level=logging.INFO, simple_mode=True)
        >>> # Successful step
        >>> def successful_task():
        ...     return {'processed': 100, 'errors': []}
        >>> result = run_step("Test Task", successful_task)
        >>> result['processed']
        100
        >>> # Failing step (returns False)
        >>> def failing_task():
        ...     return False
        >>> try:
        ...     run_step("Failing Task", failing_task)
        ... except SystemExit as e:
        ...     print(f"Exit code: {e.code}")
        Exit code: 1
    
    Notes:
        - This function uses `sys.exit(1)` rather than raising exceptions to
          ensure clean termination visible to shell scripts and CI/CD systems.
        - Stack traces are logged via `exc_info=True` for debugging.
        - Success messages use `log.success()` for visual distinction in logs.
    
    See Also:
        main: Orchestrates all pipeline steps using this wrapper
        config.LOG_NAME: Configures the log file name
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

def main() -> None:
    """Orchestrate the complete clinical data processing pipeline.
    
    This is the main entry point for the RePORTaLiN pipeline. It parses command-
    line arguments, configures logging, validates the environment, and executes
    the multi-step workflow to process clinical study data from raw Excel files
    to clean, structured, and optionally de-identified JSONL records.
    
    The function implements a sequential pipeline with optional step skipping:
    
    **Step 0 - Dictionary Loading:**
        Parses the data dictionary Excel file to extract field definitions,
        data types, validation rules, and metadata. Outputs structured JSON
        for downstream validation. (Skip with `--skip-dictionary`)
    
    **Step 1 - Data Extraction:**
        Converts Excel datasets to JSONL format, applying validation rules
        and creating both 'original/' (raw) and 'cleaned/' (validated) outputs.
        (Skip with `--skip-extraction`)
    
    **Step 2 - De-identification (Optional):**
        Removes PHI/PII using country-specific regex patterns, applies date
        shifting, and encrypts mapping files. Enabled with 
        `--enable-deidentification` flag. (Skip with `--skip-deidentification`)
    
    **Vector DB Ingestion (Optional):**
        Embeds PDF forms and/or JSONL records into a vector database for
        semantic search. Enabled with `--ingest-pdfs` or `--ingest-records`.
    
    Configuration and Validation:
        - All paths, study names, and settings are loaded from `config.py`
        - Configuration validation runs before any processing starts
        - Required directories are created automatically if missing
        - Logging is configured based on `--verbose` flag (default: simple mode)
    
    Command-Line Interface:
        The function accepts numerous CLI arguments for fine-grained control:
        
        **Workflow Control:**
            --skip-dictionary           Skip Step 0
            --skip-extraction           Skip Step 1
            --skip-deidentification     Skip Step 2
            --enable-deidentification   Enable PHI/PII removal
        
        **De-identification Options:**
            -c, --countries CODE [CODE ...]  Process specific countries (IN US BR)
                                             or ALL for all patterns
            --no-encryption             Disable mapping encryption (testing only)
        
        **Vector Database:**
            --ingest-pdfs               Embed PDF forms to vector DB
            --ingest-records            Embed JSONL records to vector DB
            --dry-run                   Test ingestion without writing
        
        **Logging:**
            -v, --verbose               Enable DEBUG logging with full output
            --version                   Show version and exit
    
    Returns:
        None: This function orchestrates the pipeline but does not return a
            value. It exits with code 0 on success or code 1 on failure.
    
    Raises:
        SystemExit: Always raised on failure (exit code 1). Reasons include:
            - Configuration validation failure (missing directories)
            - Any step failure (logged via `run_step()`)
            - Uncaught exceptions in argument parsing or setup
        FileNotFoundError: Caught and converted to SystemExit if required
            directories are missing (data/<study>/datasets/, etc.)
    
    Example:
        >>> # Simulate command-line execution (conceptual - requires data setup)
        >>> import sys
        >>> # Show version
        >>> sys.argv = ['main.py', '--version']
        >>> # Would display version and exit
        >>> 
        >>> # Run with verbose logging (requires actual data files)
        >>> # sys.argv = ['main.py', '--verbose']
        >>> # main()  # Would execute full pipeline with DEBUG logging
    
    Notes:
        - Default logging: Simple mode (INFO level, minimal console output)
        - Verbose mode (`-v`): DEBUG level with full context and stack traces
        - All operations are logged to `.logs/<LOG_NAME>.log`
        - Shell completion available if `argcomplete` package is installed
        - De-identification is opt-in and disabled by default for safety
    
    See Also:
        run_step: Wrapper for individual pipeline steps with error handling
        config.validate_config: Validates directory structure and settings
        scripts.load_dictionary.load_study_dictionary: Step 0 implementation
        scripts.extract_data.extract_excel_to_jsonl: Step 1 implementation
        scripts.deidentify.deidentify_dataset: Step 2 implementation
    """
    parser = argparse.ArgumentParser(
        prog='RePORTaLiN',
        description='Clinical data processing pipeline with de-identification support.',
        epilog="""
Usage:
  %(prog)s                              # Run complete pipeline
  %(prog)s --skip-dictionary            # Skip dictionary, run extraction
  %(prog)s --enable-deidentification    # Run pipeline with de-identification
  %(prog)s -c IN US --verbose           # Multi-country with debug logging

For detailed documentation, see the Sphinx docs or README.md
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                       help="Show program version and exit")
    parser.add_argument('--skip-dictionary', action='store_true', 
                       help="Skip data dictionary loading (Step 0)")
    parser.add_argument('--skip-extraction', action='store_true', 
                       help="Skip data extraction (Step 1)")
    parser.add_argument('--skip-deidentification', action='store_true',
                       help="Skip de-identification of extracted data (Step 2)")
    parser.add_argument('--enable-deidentification', action='store_true',
                       help="Enable PHI/PII de-identification with encryption")
    parser.add_argument('--no-encryption', action='store_true',
                       help="Disable encryption for mappings (testing only)")
    parser.add_argument('-c', '--countries', nargs='+', metavar='CODE',
                       help="Country codes (IN US ID BR etc.) or ALL. Default: IN")
    parser.add_argument('-v', '--verbose', action='store_true',
                       help="Enable verbose (DEBUG) logging with detailed context. "
                            "Default: Simple mode (INFO level, minimal console output)")
    
    # Vector database arguments (v0.3.0)
    parser.add_argument('--ingest-pdfs', action='store_true',
                       help="Ingest all PDF forms to vector database")
    parser.add_argument('--ingest-records', action='store_true',
                       help="Ingest all JSONL records to vector database")
    parser.add_argument('--dry-run', action='store_true',
                       help="Test ingestion without writing to database (use with --ingest-pdfs)")
    
    # Enable shell completion if available
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)
    
    args = parser.parse_args()

    # Set log level and mode: Default = simple mode (INFO, minimal console)
    # Only --verbose flag enables DEBUG mode with full console output
    if args.verbose:
        log_level = logging.DEBUG
        simple_mode = False  # Full verbose output to console
    else:
        # DEFAULT: Simple mode (INFO level, minimal console output)
        log_level = logging.INFO
        simple_mode = True
    
    log.setup_logger(name=config.LOG_NAME, log_level=log_level, simple_mode=simple_mode)
    log.info("Starting RePORTaLiN pipeline...")
    
    # Validate configuration (v0.3.0: raises exceptions on errors)
    try:
        config.validate_config()
        log.info("Configuration validated successfully")
    except FileNotFoundError as e:
        log.error(f"Configuration validation failed: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure your data directory structure is correct:")
        print(f"  data/{config.STUDY_NAME}/datasets/")
        print(f"  data/{config.STUDY_NAME}/annotated_pdfs/")
        print(f"  data/{config.STUDY_NAME}/data_dictionary/")
        sys.exit(1)
    
    # Ensure required directories exist
    config.ensure_directories()
    
    # Display startup banner
    print("\n" + "=" * 70)
    print("RePORTaLiN - Report India Clinical Study Data Pipeline")
    print("=" * 70 + "\n")

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
            # Input directory contains original/ and cleaned/ subdirectories (v0.3.0)
            clean_dataset_dir = Path(config.OUTPUT_DIR) / config.STUDY_NAME
            # Process the parent directory to include both original/ and cleaned/
            input_dir = clean_dataset_dir
            
            # Output to dedicated deidentified directory within output (v0.3.0)
            output_dir = Path(config.OUTPUT_DIR) / "deidentified" / config.STUDY_NAME
            
            log.info(f"De-identifying dataset: {input_dir} -> {output_dir}")
            log.info(f"Processing both 'original/' and 'cleaned/' subdirectories...")
            
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
            
            # Build consolidated completion message
            completion_msg = (
                f"De-identification complete:\n"
                f"  Texts processed: {stats.get('texts_processed', 0)}\n"
                f"  Total detections: {stats.get('total_detections', 0)}\n"
                f"  Countries: {', '.join(stats.get('countries', ['N/A']))}\n"
                f"  Unique mappings: {stats.get('total_mappings', 0)}\n"
                f"  Output structure:\n"
                f"    - {output_dir}/original/  (de-identified original files)\n"
                f"    - {output_dir}/cleaned/   (de-identified cleaned files)"
            )
            log.info(completion_msg)
            
            return stats
        
        run_step("Step 2: De-identifying PHI/PII", run_deidentification)
    elif args.skip_deidentification:
        log.info("--- Skipping Step 2: De-identification ---")
    else:
        log.info("--- De-identification disabled (use --enable-deidentification to enable) ---")

    # Vector database ingestion (v0.3.0)
    if args.ingest_pdfs:
        run_step("Vector DB: Ingesting PDF Forms", 
                lambda: ingest_pdfs_to_vectordb(
                    study_name=config.STUDY_NAME,
                    dry_run=args.dry_run
                ))
    
    if args.ingest_records:
        run_step("Vector DB: Ingesting JSONL Records", lambda: ingest_records_to_vectordb(study_name=config.STUDY_NAME))

    log.info("RePORTaLiN pipeline finished.")

if __name__ == "__main__":
    main()
