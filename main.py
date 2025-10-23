#!/usr/bin/env python3
"""
RePORTaLiN Main Pipeline
========================

Central entry point for the clinical data processing pipeline, orchestrating:
- Data dictionary loading and validation
- Excel to JSONL extraction with type conversion
- PHI/PII de-identification with country-specific compliance

This module provides a complete end-to-end pipeline with comprehensive error handling,
progress tracking, and flexible configuration via command-line arguments.

Public API
----------
Exports 2 main functions via ``__all__``:

- ``main``: Main pipeline orchestrator
- ``run_step``: Pipeline step executor with error handling

Key Features
------------
- **Multi-Step Pipeline**: Dictionary → Extraction → De-identification
- **Flexible Execution**: Skip individual steps or run complete pipeline
- **Country Compliance**: Support for 14 countries (US, IN, ID, BR, etc.)
- **Error Recovery**: Comprehensive error handling with detailed logging
- **Version Tracking**: Built-in version management

Pipeline Steps
--------------

**Step 0: Data Dictionary Loading (Optional)**
- Processes Excel data dictionary files
- Splits multi-table sheets automatically
- Outputs JSONL format with metadata

**Step 1: Data Extraction (Default)**
- Converts Excel files to JSONL format
- Dual output: original and cleaned versions
- Type conversion and validation
- Progress tracking with real-time feedback

**Step 2: De-identification (Opt-in)**
- PHI/PII detection and pseudonymization
- Country-specific regulations (HIPAA, GDPR, DPDPA, etc.)
- Encrypted mapping storage
- Date shifting with interval preservation

Usage Examples
--------------

Basic Usage (Complete Pipeline)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run all steps with default configuration::

    python3 main.py

This executes:
1. Data dictionary loading
2. Data extraction
3. De-identification disabled (opt-in)

Custom Pipeline Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~

Skip specific steps::

    # Skip dictionary, run extraction only
    python3 main.py --skip-dictionary
    
    # Skip both dictionary and extraction
    python3 main.py --skip-dictionary --skip-extraction
    
    # Run extraction with de-identification
    python3 main.py --enable-deidentification

De-identification Workflows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable de-identification with specific countries::

    # India only (default)
    python3 main.py --enable-deidentification
    
    # Multiple countries
    python3 main.py --enable-deidentification --countries IN US
    
    # All supported countries
    python3 main.py --enable-deidentification --countries ALL
    
    # Without encryption (testing only)
    python3 main.py --enable-deidentification --no-encryption

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

Combine multiple options::

    # Complete pipeline with de-identification
    python3 main.py --enable-deidentification --countries IN US ID
    
    # Extraction + de-identification only (skip dictionary)
    python3 main.py --skip-dictionary --enable-deidentification --countries ALL

Output Structure
----------------

The pipeline creates this directory structure::

    results/
    ├── data_dictionary_mappings/
    │   └── [sheet_name]/
    │       └── [sheet_name]_table.jsonl
    ├── dataset/
    │   └── [dataset_name]/
    │       ├── original/
    │       │   └── [file]_original.jsonl
    │       └── cleaned/
    │           └── [file]_cleaned.jsonl
    └── deidentified/
        └── [dataset_name]/
            ├── original/
            │   └── [file]_original.jsonl (de-identified)
            └── cleaned/
                └── [file]_cleaned.jsonl (de-identified)

Command-Line Arguments
----------------------

**Pipeline Control:**
- ``--skip-dictionary``: Skip data dictionary loading (Step 0)
- ``--skip-extraction``: Skip data extraction (Step 1)
- ``--enable-deidentification``: Enable de-identification (Step 2, opt-in)
- ``--skip-deidentification``: Skip de-identification even if enabled

**De-identification Options:**
- ``-c, --countries CODES``: Country codes (e.g., IN US ID BR) or ALL
- ``--no-encryption``: Disable encrypted mappings (testing only)

**Logging Options:**
- ``-v, --verbose``: Enable verbose (DEBUG level) logging with detailed context
  
  .. note::
     Verbose mode (v0.0.12+) includes file and line numbers in log output
     for easier debugging: ``[filename.py:123]``

**Information:**
- ``--version``: Show program version and exit
- ``--help``: Show help message with all options

Error Handling
--------------

The pipeline uses comprehensive error handling:

1. **Step-level Errors**: Each step is wrapped in try/except
2. **Validation Errors**: Invalid results cause immediate exit
3. **Logging**: All errors logged with full stack traces
4. **Exit Codes**: Non-zero exit on any failure

Return Codes:
- 0: Success
- 1: Pipeline failure (any step)

See Also
--------
- :mod:`scripts.load_dictionary` - Data dictionary processing
- :mod:`scripts.extract_data` - Data extraction
- :mod:`scripts.deidentify` - De-identification
- :mod:`config` - Configuration settings
"""
import argparse
import logging
import sys
from typing import Callable, Any
from pathlib import Path
from scripts.load_dictionary import load_study_dictionary
from scripts.extract_data import extract_excel_to_jsonl
from scripts.deidentify import deidentify_dataset, DeidentificationConfig
from scripts.utils import logging as log
import config

try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

from __version__ import __version__

__all__ = ['main', 'run_step']

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

def main() -> None:
    """
    Main pipeline orchestrating dictionary loading, data extraction, and de-identification.
    
    Command-line Arguments:
        --skip-dictionary: Skip data dictionary loading
        --skip-extraction: Skip data extraction
        --enable-deidentification: Enable de-identification (disabled by default)
        --skip-deidentification: Skip de-identification even if enabled
        --no-encryption: Disable encryption for de-identification mappings
        -c, --countries: Country codes (e.g., IN US ID BR) or ALL
        -v, --verbose: Enable verbose (DEBUG level) logging
    """
    parser = argparse.ArgumentParser(
        prog='RePORTaLiN',
        description='Clinical data processing pipeline with de-identification support.',
        epilog="""
Examples:
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
                       help="Enable verbose (DEBUG) logging with detailed context")
    
    # Enable shell completion if available
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)
    
    args = parser.parse_args()

    # Set log level based on verbose flag (DEBUG shows filename:lineno context)
    log_level = logging.DEBUG if args.verbose else config.LOG_LEVEL
    log.setup_logger(name=config.LOG_NAME, log_level=log_level)
    log.info("Starting RePORTaLiN pipeline...")
    
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
