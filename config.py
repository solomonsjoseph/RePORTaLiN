# config.py
"""
RePORTaLiN Configuration Module
================================

Centralized configuration management with dynamic study detection,
standardized directory structure, and fail-fast validation.

Version 0.3.0 - Major refactoring with breaking changes.

.. module:: config
   :synopsis: Configuration management for RePORTaLiN project

.. moduleauthor:: RePORTaLiN Team

.. versionchanged:: 0.3.0
   Complete refactoring: removed legacy dataset detection, added dynamic study
   detection, introduced standardized folder structure (datasets/, annotated_pdfs/, 
   data_dictionary/). Removed backward compatibility.
"""
import os
import logging
from typing import Optional

# Safe version import with fallback
try:
    from __version__ import __version__
except ImportError:
    __version__ = "0.3.0"

# Constants
DEFAULT_DATASET_NAME = "Indo-VAP"  # Default study name

# Explicitly define public API (v0.3.0)
__all__ = [
    # Base paths
    'BASE_DIR', 'DATA_DIR', 'OUTPUT_DIR', 'LOGS_DIR', 'TMP_DIR',
    # Study configuration
    'STUDY_NAME', 'STUDY_DATA_DIR',
    # Study data directories
    'DATASETS_DIR', 'ANNOTATED_PDFS_DIR', 'DATA_DICTIONARY_DIR',
    # Output directories
    'DICTIONARY_EXCEL_FILE', 'DICTIONARY_JSON_OUTPUT_DIR',
    # Configuration constants
    'LOG_LEVEL', 'LOG_NAME', 'DEFAULT_DATASET_NAME',
    # Public functions
    'ensure_directories', 'validate_config', 'detect_study_name',
]

# ============================================================================
# BASE PATHS
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
"""Absolute path to the project root directory."""

DATA_DIR = os.path.join(BASE_DIR, "data")
"""Path to the data directory containing all study data."""

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
"""Base directory for all output files."""

LOGS_DIR = os.path.join(BASE_DIR, ".logs")
"""Directory for log files."""

TMP_DIR = os.path.join(BASE_DIR, "tmp")
"""Directory for temporary files."""


# ============================================================================
# STUDY DETECTION
# ============================================================================

def detect_study_name() -> str:
    """
    Detect study name from data directory structure.
    
    Scans the data/ directory for subdirectories containing a valid study structure
    (must have a datasets/ subdirectory). Returns the first valid study found
    alphabetically, or falls back to DEFAULT_DATASET_NAME.
    
    Returns:
        str: Name of the first valid study directory found, or DEFAULT_DATASET_NAME
        
    Note:
        - Directories starting with '.' are excluded (hidden folders)
        - System directories (.backup, .DS_Store) are excluded
        - Returns first valid study alphabetically
        - Falls back to DEFAULT_DATASET_NAME ("Indo-VAP") if no valid study found
        
    Examples:
        >>> # data/Indo-VAP/datasets/ exists
        >>> detect_study_name()
        'Indo-VAP'
        
        >>> # data/Brazil-Study/datasets/ exists (alphabetically first)
        >>> detect_study_name()
        'Brazil-Study'
        
        >>> # data/ is empty
        >>> detect_study_name()
        'Indo-VAP'
    
    .. versionadded:: 0.3.0
       Replaces get_dataset_folder() with simplified logic.
    """
    if not os.path.exists(DATA_DIR):
        return DEFAULT_DATASET_NAME
    
    try:
        # Exclude system/backup directories
        exclude_dirs = {'.backup', '.DS_Store', 'output'}
        
        # Get all potential study directories
        candidates = [
            d for d in os.listdir(DATA_DIR)
            if os.path.isdir(os.path.join(DATA_DIR, d))
            and not d.startswith('.')
            and d not in exclude_dirs
        ]
        
        # Find first directory with valid study structure
        for candidate in sorted(candidates):
            study_path = os.path.join(DATA_DIR, candidate)
            datasets_path = os.path.join(study_path, 'datasets')
            
            # Valid study must have datasets/ directory
            if os.path.isdir(datasets_path):
                return candidate
        
        # No valid study found
        return DEFAULT_DATASET_NAME
        
    except (OSError, PermissionError):
        # Silent fallback on errors during initialization
        return DEFAULT_DATASET_NAME


# ============================================================================
# STUDY CONFIGURATION
# ============================================================================

STUDY_NAME = detect_study_name()
"""Name of the current study, automatically detected from data directory."""

STUDY_DATA_DIR = os.path.join(DATA_DIR, STUDY_NAME)
"""Base directory for the current study's data (e.g., data/Indo-VAP/)."""


# ============================================================================
# STUDY DATA DIRECTORIES
# ============================================================================

DATASETS_DIR = os.path.join(STUDY_DATA_DIR, "datasets")
"""Directory containing study dataset files (Excel/CSV files)."""

ANNOTATED_PDFS_DIR = os.path.join(STUDY_DATA_DIR, "annotated_pdfs")
"""Directory containing annotated PDF files for the study."""

DATA_DICTIONARY_DIR = os.path.join(STUDY_DATA_DIR, "data_dictionary")
"""Directory containing data dictionary and mapping specification files."""


# ============================================================================
# FILE PATHS
# ============================================================================

DICTIONARY_EXCEL_FILE = os.path.join(
    DATA_DICTIONARY_DIR,
    "RePORT_DEB_to_Tables_mapping.xlsx"
)
"""Path to the data dictionary Excel file."""


# ============================================================================
# OUTPUT DIRECTORIES
# ============================================================================

DICTIONARY_JSON_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "data_dictionary_mappings")
"""Output directory for processed data dictionary files."""


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = logging.INFO
"""Logging verbosity level (default: INFO)."""

LOG_NAME = "reportalin"
"""Logger instance name used throughout the application."""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_directories() -> None:
    """
    Create necessary output directories if they don't exist.
    
    Creates:
        - OUTPUT_DIR
        - LOGS_DIR
        - TMP_DIR
        - DICTIONARY_JSON_OUTPUT_DIR
    
    Note:
        This function creates output directories only. Input data directories
        (DATASETS_DIR, ANNOTATED_PDFS_DIR, DATA_DICTIONARY_DIR) must already
        exist and are validated by validate_config().
    
    Examples:
        >>> ensure_directories()
        >>> # All output directories now exist
    
    .. versionchanged:: 0.3.0
       Now creates OUTPUT_DIR, LOGS_DIR, and TMP_DIR instead of legacy paths.
    """
    directories = [
        OUTPUT_DIR,
        LOGS_DIR,
        TMP_DIR,
        DICTIONARY_JSON_OUTPUT_DIR,
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def validate_config() -> None:
    """
    Validate configuration and raise errors if critical paths are missing.
    
    Raises:
        FileNotFoundError: If any required directory or file doesn't exist
    
    Validates:
        - DATA_DIR exists
        - STUDY_DATA_DIR exists
        - DATASETS_DIR exists
        - ANNOTATED_PDFS_DIR exists
        - DATA_DICTIONARY_DIR exists
        - DICTIONARY_EXCEL_FILE exists
    
    Examples:
        >>> try:
        ...     validate_config()
        ...     print("Configuration is valid!")
        ... except FileNotFoundError as e:
        ...     print(f"Configuration error: {e}")
    
    .. versionchanged:: 0.3.0
       Now raises exceptions instead of returning warnings. Validates new
       directory structure.
    """
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")
    
    if not os.path.exists(STUDY_DATA_DIR):
        raise FileNotFoundError(
            f"Study directory not found: {STUDY_DATA_DIR}\n"
            f"Expected structure: data/{STUDY_NAME}/"
        )
    
    if not os.path.exists(DATASETS_DIR):
        raise FileNotFoundError(
            f"Datasets directory not found: {DATASETS_DIR}\n"
            f"Expected structure: data/{STUDY_NAME}/datasets/"
        )
    
    if not os.path.exists(ANNOTATED_PDFS_DIR):
        raise FileNotFoundError(
            f"Annotated PDFs directory not found: {ANNOTATED_PDFS_DIR}\n"
            f"Expected structure: data/{STUDY_NAME}/annotated_pdfs/"
        )
    
    if not os.path.exists(DATA_DICTIONARY_DIR):
        raise FileNotFoundError(
            f"Data dictionary directory not found: {DATA_DICTIONARY_DIR}\n"
            f"Expected structure: data/{STUDY_NAME}/data_dictionary/"
        )
    
    if not os.path.exists(DICTIONARY_EXCEL_FILE):
        raise FileNotFoundError(
            f"Data dictionary file not found: {DICTIONARY_EXCEL_FILE}\n"
            f"Expected file: data/{STUDY_NAME}/data_dictionary/RePORT_DEB_to_Tables_mapping.xlsx"
        )
