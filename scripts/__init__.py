"""Clinical research data processing package for RePORTaLiN.

This package provides the core data processing functionality for the RePORTaLiN
(Report India) clinical study pipeline. It contains modules for loading data
dictionaries, extracting raw data from Excel files, de-identifying PHI/PII,
and ingesting data into vector databases for semantic search.

Package Architecture:
    The scripts package is organized into functional subpackages:
    
    **Core Pipeline Modules** (top-level):
        - load_dictionary: Parse and validate data dictionary Excel files
        - extract_data: Convert Excel datasets to JSONL format
        - deidentify: Remove PHI/PII using country-specific patterns
    
    **Utility Subpackages**:
        - utils/: Logging, country regulations, migration tools
        - vector_db/: Vector database ingestion and search
        - llm/: Large language model adapters (future)
        - session/: Session management (future)
        - cache/: Multi-level caching (future)

Public API:
    The package exposes two primary functions for the main pipeline:
    
    - load_study_dictionary: Parse data dictionary Excel → JSON
    - extract_excel_to_jsonl: Convert Excel datasets → JSONL records

Module Attributes:
    __version__ (str): Current package version from __version__.py
    __all__ (list): Explicitly exported symbols for `from scripts import *`

Example:
    >>> # Import core pipeline functions
    >>> from scripts import load_study_dictionary, extract_excel_to_jsonl
    >>> 
    >>> # Load data dictionary (Step 0)
    >>> load_study_dictionary(
    ...     file_path='data/Indo-VAP/data_dictionary/RePORT_DEB_to_Tables_mapping.xlsx',
    ...     json_output_dir='output/data_dictionary_mappings'
    ... )  # doctest: +SKIP
    >>> 
    >>> # Extract data to JSONL (Step 1)
    >>> extract_excel_to_jsonl()  # doctest: +SKIP

Notes:
    - This __init__.py establishes the public API for the scripts package
    - Only load_dictionary and extract_data are exposed at the top level
    - Other modules (deidentify, vector_db, etc.) must be imported explicitly
    - Version is imported from root __version__.py for consistency

See Also:
    main.py: Orchestrates the pipeline using these functions
    config.py: Provides configuration for all scripts
    scripts.deidentify: PHI/PII de-identification (not in __all__)
    scripts.vector_db: Vector database ingestion (subpackage)
"""

from .load_dictionary import load_study_dictionary
from .extract_data import extract_excel_to_jsonl
from __version__ import __version__

__all__ = ['load_study_dictionary', 'extract_excel_to_jsonl']
