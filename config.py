# config.py
"""Centralized configuration with dynamic study detection and fail-fast validation."""
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
    """Detect study name from data directory structure."""
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
    """Create necessary output directories if they don't exist."""
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
    """Validate configuration and raise errors if critical paths are missing."""
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
