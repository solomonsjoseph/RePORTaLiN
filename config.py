# config.py
"""Centralized configuration management for RePORTaLiN with dynamic study detection.

This module serves as the single source of truth for all configuration settings,
file paths, and directory structures used throughout the RePORTaLiN pipeline. It
implements a fail-fast validation philosophy to catch configuration errors early,
before any data processing begins.

Architecture Philosophy:
    **Convention over Configuration**: The module auto-detects the active study
    from the directory structure (e.g., `data/Indo-VAP/`) rather than requiring
    manual configuration. This reduces setup friction while maintaining flexibility
    for multi-study deployments.
    
    **Fail-Fast Validation**: The `validate_config()` function checks all critical
    paths at startup and raises descriptive errors immediately if anything is
    missing. This prevents silent failures deep in the pipeline.
    
    **Immutable Constants**: All paths are computed once at import time and should
    be treated as immutable. This ensures consistency across all modules.

Directory Structure:
    The expected project structure is::
    
        RePORTaLiN/
        ├── data/
        │   └── {STUDY_NAME}/              # Auto-detected study (e.g., Indo-VAP)
        │       ├── datasets/              # Excel/CSV source files
        │       ├── annotated_pdfs/        # PDF forms with annotations
        │       └── data_dictionary/       # Field definitions and mappings
        │           └── RePORT_DEB_to_Tables_mapping.xlsx
        ├── output/
        │   ├── data_dictionary_mappings/  # Parsed JSON dictionaries
        │   ├── {STUDY_NAME}/              # Extracted JSONL records
        │   │   ├── original/              # Raw extraction output
        │   │   └── cleaned/               # Validated/cleaned records
        │   ├── deidentified/              # De-identified datasets (optional)
        │   └── vector_db/                 # Vector database storage
        │       ├── chroma_db/             # ChromaDB (primary backend)
        │       └── qdrant_storage/        # Qdrant (fallback backend)
        ├── .logs/                         # Application logs
        └── tmp/                           # Temporary/scratch files

Study Detection Algorithm:
    1. Scan `data/` directory for subdirectories
    2. Exclude system directories (`.backup`, `.DS_Store`, etc.)
    3. Check each candidate for a `datasets/` subdirectory
    4. Return first valid study name (alphabetically sorted)
    5. Fall back to `DEFAULT_DATASET_NAME` ("Indo-VAP") if none found

Vector Database Integration:
    Supports dual-backend architecture:
    - **ChromaDB** (primary): Pure-Python, easy setup, good for development
    - **Qdrant** (fallback): Production-grade, supports cloud deployment
    
    Auto-selection tries ChromaDB first, then Qdrant if ChromaDB fails.
    Set `PREFERRED_VECTOR_BACKEND` to override auto-selection.

Configuration Categories:
    - **Base Paths**: Project root, data, output, logs, temp directories
    - **Study Configuration**: Auto-detected study name and study-specific paths
    - **Study Data Directories**: Datasets, PDFs, data dictionary locations
    - **Output Directories**: Processed data and vector database storage
    - **Vector DB Settings**: Chunking, embeddings, collection names, search params
    - **Logging**: Log levels, logger names, file paths

Module Attributes:
    BASE_DIR (str): Absolute path to project root directory
    DATA_DIR (str): Path to `data/` directory containing all study data
    OUTPUT_DIR (str): Base directory for all pipeline outputs
    STUDY_NAME (str): Auto-detected current study name (e.g., "Indo-VAP")
    DATASETS_DIR (str): Directory containing Excel/CSV dataset files
    EMBEDDING_MODEL (str): Sentence transformer model for vector embeddings
    
    See `__all__` for complete list of exported symbols.

Example:
    >>> # Import configuration (auto-detects study from directory structure)
    >>> import config
    >>> print(config.STUDY_NAME)  # doctest: +SKIP
    'Indo-VAP'
    >>> print(config.DATASETS_DIR)  # doctest: +SKIP
    '/path/to/RePORTaLiN/data/Indo-VAP/datasets'
    
    >>> # Validate configuration before processing
    >>> try:
    ...     config.validate_config()
    ...     print("Configuration valid!")
    ... except FileNotFoundError as e:  # doctest: +SKIP
    ...     print(f"Configuration error: {e}")
    
    >>> # Ensure output directories exist
    >>> config.ensure_directories()  # Creates output/, .logs/, tmp/, etc.

Notes:
    - This module has zero external dependencies except stdlib
    - All paths use `os.path.join()` for cross-platform compatibility
    - Configuration is loaded at import time (eager evaluation)
    - Use `validate_config()` in main.py before starting any pipeline steps
    - Directory creation is idempotent (safe to call multiple times)

See Also:
    main.py: Calls `validate_config()` and `ensure_directories()` at startup
    __version__.py: Version information used in configuration
    scripts.vector_db.vector_store: Uses vector DB configuration
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

# Explicitly define public API
__all__ = [
    # Base paths
    'BASE_DIR', 'DATA_DIR', 'OUTPUT_DIR', 'LOGS_DIR', 'TMP_DIR',
    # Study configuration
    'STUDY_NAME', 'STUDY_DATA_DIR',
    # Study data directories
    'DATASETS_DIR', 'ANNOTATED_PDFS_DIR', 'DATA_DICTIONARY_DIR',
    # Output directories
    'DICTIONARY_EXCEL_FILE', 'DICTIONARY_JSON_OUTPUT_DIR',
    # Vector database configuration
    'VECTOR_DB_DIR', 'QDRANT_STORAGE_PATH',
    'CHROMA_DB_PATH', 'PREFERRED_VECTOR_BACKEND',
    'CHUNK_SIZE', 'CHUNK_OVERLAP', 'CHUNK_STRATEGY',
    'EMBEDDING_MODEL', 'EMBEDDING_DIM', 'BATCH_SIZE',
    'PDF_COLLECTION', 'JSONL_COLLECTION', 'JSONL_COLLECTION_CLEANED', 
    'JSONL_COLLECTION_ORIGINAL', 'DEFAULT_SEARCH_LIMIT',
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
    """Detect and return the active study name from the data directory structure.
    
    This function implements automatic study detection by scanning the `data/`
    directory for subdirectories that contain a valid study structure. A valid
    study must have a `datasets/` subdirectory containing Excel/CSV files.
    
    The detection algorithm prioritizes alphabetically-first valid studies and
    falls back to `DEFAULT_DATASET_NAME` if no valid study is found. This
    fail-safe behavior ensures the configuration never fails at import time.
    
    Detection Algorithm:
        1. Check if `DATA_DIR` exists; return default if not
        2. List all subdirectories in `DATA_DIR`
        3. Filter out system/hidden directories (`.backup`, `.DS_Store`, etc.)
        4. Sort candidates alphabetically for deterministic selection
        5. Check each candidate for a `datasets/` subdirectory
        6. Return first valid candidate, or default if none found
    
    Excluded Directories:
        - `.backup`: Backup directories
        - `.DS_Store`: macOS metadata
        - `output`: Pipeline output (not a study)
        - Any directory starting with `.` (hidden directories)
    
    Returns:
        str: The detected study name (e.g., "Indo-VAP"), or DEFAULT_DATASET_NAME
            ("Indo-VAP") if no valid study is found. Never returns None.
    
    Example:
        >>> # Assume data/ contains: data/Indo-VAP/datasets/, data/Study-B/
        >>> import config
        >>> config.detect_study_name()  # doctest: +SKIP
        'Indo-VAP'
        
        >>> # If no valid study exists, falls back to default
        >>> # (Empty data/ directory case)
        >>> config.DEFAULT_DATASET_NAME
        'Indo-VAP'
    
    Notes:
        - This function is called once at module import time
        - Silent fallback on OSError/PermissionError (returns default)
        - No exceptions raised - always returns a valid string
        - Uses sorted() for deterministic ordering across platforms
        - Changes to data/ directory require module reload to take effect
    
    See Also:
        validate_config: Validates that the detected study actually exists
        STUDY_NAME: Module-level constant storing the detected study name
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
# VECTOR DATABASE CONFIGURATION
# ============================================================================

VECTOR_DB_DIR = os.path.join(OUTPUT_DIR, "vector_db")
"""Base directory for vector database storage."""

QDRANT_STORAGE_PATH = os.path.join(VECTOR_DB_DIR, "qdrant_storage")
"""Storage path for Qdrant vector database (fallback)."""

CHROMA_DB_PATH = os.path.join(VECTOR_DB_DIR, "chroma_db")
"""Storage path for ChromaDB vector database (primary)."""

PREFERRED_VECTOR_BACKEND = None
"""
Preferred vector database backend: 'chromadb', 'qdrant', or None for auto-selection.
Auto-selection tries ChromaDB first (primary), then Qdrant (fallback).
"""

# Chunking parameters (based on Pinecone best practices for document chunking)
CHUNK_SIZE = 1024
"""Target chunk size in tokens (optimal for clinical data based on analysis)."""

CHUNK_OVERLAP = 150
"""Overlap between chunks in tokens (preserves context across boundaries)."""

CHUNK_STRATEGY = "document_structure"
"""Chunking strategy: 'document_structure' for structure-based chunking."""

# Embedding model configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
"""Sentence transformer model for generating embeddings."""

EMBEDDING_DIM = 384
"""Dimension of embedding vectors (384 for all-MiniLM-L6-v2)."""

BATCH_SIZE = 32
"""Batch size for embedding generation."""

# Collection names for two-collection architecture
# Format: {STUDY_NAME}_{dataset_type} - preserves hierarchical study-based naming
PDF_COLLECTION = f"{STUDY_NAME}_pdf_forms"
"""Collection name for PDF form documents (study-based naming: {study_name}_pdf_forms)."""

# JSONL collection names support both 'cleaned' and 'original' datasets
JSONL_COLLECTION = f"{STUDY_NAME}_jsonl_records"
"""Collection name for JSONL patient records (study-based naming: {study_name}_jsonl_records)."""

JSONL_COLLECTION_CLEANED = f"{STUDY_NAME}_jsonl_records_cleaned"
"""Collection name for cleaned JSONL records (study-based naming: {study_name}_jsonl_records_cleaned)."""

JSONL_COLLECTION_ORIGINAL = f"{STUDY_NAME}_jsonl_records_original"
"""Collection name for original JSONL records (study-based naming: {study_name}_jsonl_records_original)."""

# Query parameters
DEFAULT_SEARCH_LIMIT = 10
"""Default number of results to return from vector search."""


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
    """Create all necessary output directories if they don't already exist.
    
    This function ensures the required directory structure exists before any
    pipeline operations begin. It creates directories idempotently (safe to
    call multiple times) and never raises errors if directories already exist.
    
    The function creates the following directories:
        - `output/`: Base directory for all pipeline outputs
        - `.logs/`: Application log files
        - `tmp/`: Temporary/scratch files
        - `output/data_dictionary_mappings/`: Parsed JSON dictionaries
        - `output/vector_db/`: Vector database storage base
        - `output/vector_db/qdrant_storage/`: Qdrant backend storage
    
    All directories are created with `exist_ok=True`, making this function
    safe to call at any point in the pipeline without side effects.
    
    Returns:
        None: This function has no return value. It performs directory creation
            as a side effect and never raises exceptions.
    
    Example:
        >>> import config
        >>> # Safe to call multiple times - idempotent operation
        >>> config.ensure_directories()
        >>> config.ensure_directories()  # No error, no duplicate creation
        
        >>> # Verify directories were created
        >>> import os
        >>> os.path.exists(config.OUTPUT_DIR)  # doctest: +SKIP
        True
        >>> os.path.exists(config.LOGS_DIR)  # doctest: +SKIP
        True
    
    Notes:
        - Uses `os.makedirs(exist_ok=True)` for idempotent creation
        - Never raises OSError even if directories already exist
        - Creates parent directories automatically (recursive creation)
        - Should be called early in main.py after configuration validation
        - Does NOT create study data directories (those must exist beforehand)
    
    See Also:
        validate_config: Validates that input directories exist
        main.py: Calls this function after validate_config() at startup
    """
    directories = [
        OUTPUT_DIR,
        LOGS_DIR,
        TMP_DIR,
        DICTIONARY_JSON_OUTPUT_DIR,
        VECTOR_DB_DIR,
        QDRANT_STORAGE_PATH,
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def validate_config() -> None:
    """Validate that all required directories and files exist before processing.
    
    This function implements fail-fast validation by checking that the expected
    directory structure and critical files are in place before any pipeline
    operations begin. It raises descriptive FileNotFoundError exceptions with
    helpful messages indicating exactly what's missing and where it should be.
    
    Validation Rules:
        The function checks the following in order:
        
        1. **DATA_DIR** (`data/`): Base directory for all study data
        2. **STUDY_DATA_DIR** (`data/{STUDY_NAME}/`): Detected study directory
        3. **DATASETS_DIR** (`data/{STUDY_NAME}/datasets/`): Excel/CSV files
        4. **ANNOTATED_PDFS_DIR** (`data/{STUDY_NAME}/annotated_pdfs/`): PDF forms
        5. **DATA_DICTIONARY_DIR** (`data/{STUDY_NAME}/data_dictionary/`): Mappings
        6. **DICTIONARY_EXCEL_FILE**: The data dictionary Excel file itself
    
    Each check provides a detailed error message showing:
        - What is missing (path and purpose)
        - Where it should be located (expected structure)
        - How to fix it (create the directory or file)
    
    Returns:
        None: Returns nothing if validation passes. All checks are performed
            via side effects (raising exceptions on failure).
    
    Raises:
        FileNotFoundError: Raised immediately when any required directory or
            file is missing. The error message includes:
            - The missing path (absolute)
            - The expected directory structure
            - Guidance on how to resolve the issue
    
    Example:
        >>> import config
        >>> # Successful validation (requires actual data setup)
        >>> try:
        ...     config.validate_config()
        ...     print("Configuration is valid!")
        ... except FileNotFoundError as e:  # doctest: +SKIP
        ...     print(f"Missing: {e}")
        
        >>> # Example error message when data/ is missing:
        >>> # FileNotFoundError: Data directory not found: /path/to/data
        
        >>> # Example error message when datasets/ is missing:
        >>> # FileNotFoundError: Datasets directory not found: /path/to/data/Indo-VAP/datasets
        >>> # Expected structure: data/Indo-VAP/datasets/
    
    Notes:
        - Call this BEFORE `ensure_directories()` to validate inputs first
        - Does NOT create any directories (read-only validation)
        - Checks are ordered from general to specific (data/ → study/ → subdirs)
        - Used in main.py to prevent silent failures during processing
        - Error messages are designed for end-user troubleshooting
    
    See Also:
        ensure_directories: Creates output directories (call after validation)
        main.py: Calls this at startup and handles FileNotFoundError
        detect_study_name: Auto-detects study name used in validation
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
