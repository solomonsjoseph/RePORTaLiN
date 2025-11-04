"""
RePORTaLiN Scripts Package
===========================

Core data processing modules for clinical research data extraction, validation,
and de-identification.

This package provides high-level functions for the complete data processing pipeline:

- **Data Dictionary Processing**: Load and validate study data dictionaries
- **Data Extraction**: Convert Excel files to JSONL format with validation
- **De-identification**: Advanced PHI/PII detection and pseudonymization (via utils)

Public API
----------
The package exports 2 main high-level functions via ``__all__``:

- ``load_study_dictionary``: Process data dictionary Excel files
- ``extract_excel_to_jsonl``: Extract dataset Excel files to JSONL

For more specialized functionality, import directly from submodules:

- ``scripts.load_dictionary``: Dictionary processing (2 public functions)
- ``scripts.extract_data``: Data extraction (6 public functions)
- ``scripts.deidentify``: De-identification engine (10 public functions)
- ``scripts.utils.country_regulations``: Privacy regulations (6 public functions)
- ``scripts.utils.logging``: Enhanced logging (12 public functions)

Usage Examples
--------------

Basic Pipeline
~~~~~~~~~~~~~~

Process both data dictionary and dataset with default configuration::

    from scripts import load_study_dictionary, extract_excel_to_jsonl
    
    # Step 1: Load data dictionary
    dict_success = load_study_dictionary()
    
    # Step 2: Extract dataset (uses config.DATASETS_DIR and config.OUTPUT_DIR)
    result = extract_excel_to_jsonl()
    
    if dict_success and result['files_created'] > 0:
        print("✓ Pipeline completed successfully!")

Custom Processing
~~~~~~~~~~~~~~~~~

Use individual modules for custom workflows::

    from scripts.load_dictionary import process_excel_file
    from scripts.extract_data import find_excel_files, process_excel_file as process_data
    
    # Custom dictionary processing
    process_excel_file(
        excel_path="custom_dict.xlsx",
        output_dir="output/custom_dict"
    )
    
    # Custom data extraction with file discovery
    excel_files = find_excel_files("data/custom_dataset")
    for file_path in excel_files:
        process_data(
            excel_path=file_path,
            output_dir="output/custom_output"
        )

De-identification Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complete pipeline with de-identification::

    from scripts import extract_excel_to_jsonl
    from scripts.deidentify import deidentify_dataset, DeidentificationConfig
    import config
    import os
    
    # Step 1: Extract data (uses config.DATASETS_DIR and config.OUTPUT_DIR)
    result = extract_excel_to_jsonl()
    
    # Step 2: De-identify with custom configuration
    deidentify_config = DeidentificationConfig(
        countries=['IN', 'US'],
        enable_encryption=True
    )
    
    clean_dataset_dir = os.path.join(config.OUTPUT_DIR, "cleaned_datasets")
    deidentify_dataset(
        input_dir=f"{clean_dataset_dir}/cleaned",
        output_dir=os.path.join(config.OUTPUT_DIR, "deidentified", config.STUDY_NAME),
        config=deidentify_config
    )

Module Structure
----------------

The package is organized as follows::

    scripts/
    ├── __init__.py              # Package API (this file)
    ├── load_dictionary.py       # Data dictionary processing
    ├── extract_data.py          # Excel to JSONL extraction
    ├── deidentify.py            # De-identification engine
    └── utils/                   # Utility modules
        ├── __init__.py
        ├── country_regulations.py  # Privacy compliance
        └── logging.py           # Enhanced logging

Version History
---------------
- v0.0.9: Enhanced package-level API with comprehensive documentation
- v0.0.8: Enhanced load_dictionary module (public API, type hints, docs)
- v0.0.7: Enhanced extract_data module (public API, type hints, docs)
- v0.0.6: Enhanced deidentify module (public API, type safety, docs)
- v0.0.5: Enhanced country_regulations module (public API, docs)
- v0.0.4: Enhanced logging module (performance, type hints)
- v0.0.3: Enhanced config module (utilities, robustness)
- v0.0.1: Initial package structure

See Also
--------
- :mod:`scripts.load_dictionary` - Data dictionary processing
- :mod:`scripts.extract_data` - Data extraction
- :mod:`scripts.deidentify` - De-identification
- :mod:`scripts.utils.country_regulations` - Privacy regulations
- :mod:`scripts.utils.logging` - Logging utilities
"""

from .load_dictionary import load_study_dictionary
from .extract_data import extract_excel_to_jsonl
from __version__ import __version__

__all__ = ['load_study_dictionary', 'extract_excel_to_jsonl']
