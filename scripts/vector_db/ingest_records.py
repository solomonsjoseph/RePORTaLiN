"""JSONL record ingestion pipeline for vector database with adaptive chunking.

Orchestrates end-to-end JSONL record ingestion workflow: discovers de-identified
research data files, extracts natural language text via TextChunker, generates
embeddings, and uploads to vector database. Designed for clinical research datasets
(cleaned or original) with automatic collection management, progress tracking, and
comprehensive error reporting.

**Pipeline Architecture:**
```
JSONL Files → TextChunker → Chunks → EmbeddingModel → Vectors → VectorStore
                ↓             ↓          ↓                ↓           ↓
           Parse JSON    Extract NL   Generate         Standardize  Qdrant/Chroma
           records       text fields  embeddings       dimensions   persistence
```

**Key Features:**
- **Dual Dataset Support**: Handles both 'cleaned' and 'original' de-identified data
- **Natural Language Extraction**: Intelligent text field detection and chunking
- **Batch Processing**: Configurable batch sizes for memory-efficient embedding
- **Collection Auto-Selection**: Automatic collection based on dataset type
- **Progress Tracking**: Per-file and overall progress reporting
- **Record Limiting**: Optional max_records_per_file for testing/sampling
- **Performance Metrics**: Tracks processing time, records/file, chunks/record

**Processing Workflow:**

1. **Discovery**: Scan jsonl_dir for *.jsonl files
2. **Validation**: Verify directory exists, validate dataset type
3. **Initialization**: Load TextChunker, EmbeddingModel, VectorStore
4. **Extraction**: Parse each JSONL file, extract natural language fields
5. **Chunking**: Break long text fields into chunks (respecting token limits)
6. **Embedding**: Generate vectors for all chunks (batch processing)
7. **Ingestion**: Upload embeddings + metadata to vector store
8. **Reporting**: Log performance metrics and summary statistics

**Dataset Types:**

- **cleaned**: De-identified data with PHI removed, structured fields preserved
  - Collection: config.JSONL_COLLECTION_CLEANED (e.g., 'Indo-VAP_records_cleaned')
  - Source: output/deidentified/{study_name}/cleaned/
  - Use case: Production semantic search, safer sharing

- **original**: De-identified data preserving original structure/terminology  
  - Collection: config.JSONL_COLLECTION_ORIGINAL (e.g., 'Indo-VAP_records_original')
  - Source: output/deidentified/{study_name}/original/
  - Use case: Full-fidelity research, complete record preservation

**Performance Characteristics:**

Typical performance (CPU, default settings):
- **Parsing**: ~100-500 records/second (varies by record complexity)
- **Chunking**: ~0.1-0.5 seconds per record (depends on text length)
- **Embedding**: ~0.1-0.5 seconds per chunk (batch size, model speed)
- **Upload**: ~0.05-0.2 seconds per chunk (network/disk I/O)

For 10 files (~10,000 records, ~50,000 chunks):
- Total time: ~10-20 minutes (CPU)
- GPU acceleration: ~3-5x faster for embedding

**Usage Patterns:**

Basic ingestion (cleaned data, default settings):
    >>> from scripts.vector_db.ingest_records import ingest_records_to_vectordb
    >>> # Ingest all cleaned JSONL files
    >>> count = ingest_records_to_vectordb(
    ...     study_name='Indo-VAP',
    ...     dataset_type='cleaned'
    ... )  # doctest: +SKIP
    >>> print(f"Ingested {count} chunks")  # doctest: +SKIP

Custom configuration:
    >>> from pathlib import Path
    >>> count = ingest_records_to_vectordb(
    ...     study_name='Indo-VAP',
    ...     jsonl_dir=Path('/data/deidentified/Indo-VAP/cleaned'),
    ...     collection_name='my_records_collection',
    ...     chunk_size=512,
    ...     recreate_collection=True,
    ...     max_records_per_file=100,  # Limit for testing
    ...     dataset_type='cleaned'
    ... )  # doctest: +SKIP

Original dataset ingestion:
    >>> # Ingest original (non-cleaned) de-identified data
    >>> count = ingest_records_to_vectordb(
    ...     study_name='Indo-VAP',
    ...     dataset_type='original'
    ... )  # doctest: +SKIP

CLI usage:
    ```bash
    # Basic ingestion (cleaned data)
    python -m scripts.vector_db.ingest_records
    
    # Original dataset
    python -m scripts.vector_db.ingest_records --dataset-type original
    
    # Recreate collection and ingest
    python -m scripts.vector_db.ingest_records --recreate
    
    # Test with limited records
    python -m scripts.vector_db.ingest_records --max-records 100 --verbose
    
    # Custom directory
    python -m scripts.vector_db.ingest_records --jsonl-dir /path/to/jsonl
    ```

**Dependencies:**
- TextChunker: Extracts natural language text from JSONL (jsonl_chunking_nl.py)
- EmbeddingModel: Generates text embeddings (embeddings.py)
- VectorStore: Manages vector database operations (vector_store.py)
- config: Global configuration (paths, model names, chunk sizes)

**Error Handling:**
- FileNotFoundError: JSONL directory doesn't exist
- ValueError: Invalid dataset_type (must be 'cleaned' or 'original')
- JSONDecodeError: Malformed JSONL files (logged, skipped)
- TextChunker errors: Text extraction failures (logged per-file)
- Embedding errors: Model loading failures (fatal, not retried)
- VectorStore errors: Connection issues, schema mismatches (fatal)

**Configuration:**

Uses config.py defaults (overrideable via arguments):
- OUTPUT_DIR: Base output directory for de-identified data
- JSONL_COLLECTION_CLEANED: Collection name for cleaned records
- JSONL_COLLECTION_ORIGINAL: Collection name for original records
- CHUNK_SIZE: Chunk size in tokens (default: 500)
- CHUNK_OVERLAP: Overlap between chunks (default: 50)
- BATCH_SIZE: Embedding batch size (default: 32)
- EMBEDDING_MODEL: Model identifier (default: all-MiniLM-L6-v2)
- VECTOR_DB_DIR: Vector database storage path

See Also:
    jsonl_chunking_nl.py: Natural language text extraction from JSONL
    embeddings.py: Embedding model wrapper
    vector_store.py: Vector database abstraction
    ingest_pdfs.py: Parallel module for ingesting PDF forms

Note:
    First run downloads embedding model (~100-500MB) from Hugging Face Hub.
    Subsequent runs use local cache. Collection recreation deletes existing
    data—use with caution in production. max_records_per_file useful for
    testing but doesn't stop at exact limit (processes full files).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List

# Import centralized logging
from scripts.utils import logging_system as log

# Module-level loggers
logger = log.get_logger(__name__)
vlog = log.get_verbose_logger()

vlog(f"🔍 [IMPORT] Starting import of {__name__}")
vlog(f"🔍 [IMPORT] Python version: {sys.version}")
vlog(f"🔍 [IMPORT] Module file: {__file__}")

try:
    vlog("🔍 [IMPORT] Importing config module...")
    import config
    vlog(f"🔍 [IMPORT] ✅ Config imported successfully from: {config.__file__}")
except Exception as e:
    logger.error(f"❌ [IMPORT] Failed to import config: {e}", exc_info=True)
    raise

try:
    vlog("🔍 [IMPORT] Importing jsonl_chunking_nl module...")
    from .jsonl_chunking_nl import TextChunker, TextChunk
    vlog("🔍 [IMPORT] ✅ TextChunker and TextChunk imported successfully")
except Exception as e:
    logger.error(f"❌ [IMPORT] Failed to import jsonl_chunking_nl: {e}", exc_info=True)
    raise

try:
    vlog("🔍 [IMPORT] Importing embeddings module...")
    from .embeddings import EmbeddingModel
    vlog("🔍 [IMPORT] ✅ EmbeddingModel imported successfully")
except Exception as e:
    logger.error(f"❌ [IMPORT] Failed to import embeddings: {e}", exc_info=True)
    raise

try:
    vlog("🔍 [IMPORT] Importing vector_store module...")
    from .vector_store import VectorStore
    vlog("🔍 [IMPORT] ✅ VectorStore imported successfully")
except Exception as e:
    logger.error(f"❌ [IMPORT] Failed to import vector_store: {e}", exc_info=True)
    raise

vlog(f"🔍 [IMPORT] ✅ All imports completed successfully for {__name__}")


def ingest_records_to_vectordb(
    study_name: str = "Indo-VAP",
    jsonl_dir: Optional[Path] = None,
    collection_name: Optional[str] = None,
    chunk_size: Optional[int] = None,
    recreate_collection: bool = False,
    max_records_per_file: Optional[int] = None,
    dataset_type: str = "cleaned"
) -> int:
    """Ingest de-identified JSONL records from directory to vector database.
    
    Orchestrates end-to-end JSONL record ingestion workflow:
    1. Discovers all *.jsonl files in specified directory
    2. Parses JSON records line-by-line (JSONL format)
    3. Converts structured JSON to natural language text via TextChunker
    4. Generates embeddings for all text chunks (batch processing)
    5. Uploads embeddings + metadata to vector database
    6. Returns total count of successfully ingested records
    
    Designed for clinical research datasets with support for both 'cleaned'
    and 'original' de-identified data types. Automatically selects appropriate
    collection based on dataset_type, handles progress tracking, and provides
    comprehensive error reporting for each file/record.
    
    Args:
        study_name (str, optional): Study identifier for collection naming and
            directory resolution. Used to construct default jsonl_dir if not
            provided. Default: "Indo-VAP".
        jsonl_dir (Optional[Path], optional): Directory containing *.jsonl files
            to ingest. If None, auto-resolves to:
            {OUTPUT_DIR}/deidentified/{study_name}/{dataset_type}/
            Must exist or raises FileNotFoundError. Default: None (auto-detect).
        collection_name (Optional[str], optional): Target vector database collection.
            If None, auto-selects based on dataset_type:
            - 'cleaned' → config.JSONL_COLLECTION_CLEANED
            - 'original' → config.JSONL_COLLECTION_ORIGINAL
            Default: None (auto-detect from dataset_type).
        chunk_size (Optional[int], optional): Maximum tokens per text chunk.
            Affects granularity of semantic search. Smaller chunks = more precise
            results but more storage. If None, uses config.CHUNK_SIZE (500).
            Default: None (uses config default).
        recreate_collection (bool, optional): If True, deletes existing collection
            before ingestion. WARNING: Destroys all existing data in collection.
            Use with caution in production. Default: False.
        max_records_per_file (Optional[int], optional): Limit records processed
            per JSONL file. Useful for testing/sampling. None = process all records.
            Must be positive integer if provided. Default: None (no limit).
        dataset_type (str, optional): Type of de-identified dataset to ingest.
            Must be 'cleaned' or 'original'. Determines default collection and
            directory path. 'cleaned' = PHI-removed data, 'original' = full-fidelity
            de-identified data. Default: "cleaned".
    
    Returns:
        int: Total number of records successfully ingested to vector database.
            Includes all chunks across all processed JSONL files. Returns 0 if
            no JSONL files found or all processing failed.
    
    Raises:
        ValueError: If dataset_type not in ['cleaned', 'original'], or if
            max_records_per_file <= 0.
        FileNotFoundError: If jsonl_dir does not exist. Suggests running
            de-identification first: `python main.py --deidentify`.
        RuntimeError: If TextChunker, EmbeddingModel, or VectorStore initialization
            fails, or if any fatal error occurs during ingestion pipeline.
        JSONDecodeError: If JSONL file contains malformed JSON (logged per-line,
            processing continues).
        IOError: If JSONL files cannot be read (logged per-file, processing continues).
    
    Example:
        Basic ingestion (cleaned data, defaults):
            >>> from scripts.vector_db.ingest_records import ingest_records_to_vectordb
            >>> # Ingest all cleaned JSONL files from default directory
            >>> count = ingest_records_to_vectordb(
            ...     study_name='Indo-VAP',
            ...     dataset_type='cleaned'
            ... )  # doctest: +SKIP
            >>> print(f"Ingested {count} records")  # doctest: +SKIP
            Ingested 5234 records
        
        Custom directory and collection:
            >>> from pathlib import Path
            >>> count = ingest_records_to_vectordb(
            ...     study_name='Indo-VAP',
            ...     jsonl_dir=Path('/data/custom/jsonl'),
            ...     collection_name='my_custom_collection',
            ...     chunk_size=512,
            ...     dataset_type='cleaned'
            ... )  # doctest: +SKIP
        
        Testing with record limits:
            >>> # Ingest max 100 records per file for testing
            >>> count = ingest_records_to_vectordb(
            ...     study_name='Indo-VAP',
            ...     max_records_per_file=100,
            ...     dataset_type='cleaned'
            ... )  # doctest: +SKIP
        
        Original dataset ingestion with collection recreation:
            >>> # Ingest original (non-cleaned) de-identified data
            >>> # WARNING: recreate_collection=True deletes existing data!
            >>> count = ingest_records_to_vectordb(
            ...     study_name='Indo-VAP',
            ...     dataset_type='original',
            ...     recreate_collection=True
            ... )  # doctest: +SKIP
    
    Side Effects:
        - Creates vector database collection if it doesn't exist
        - If recreate_collection=True, deletes existing collection data
        - Writes embeddings + metadata to vector database (persistent disk storage)
        - Logs progress/errors to console and log files (via logging_system)
        - Downloads embedding model on first run (~100-500MB to cache)
    
    Performance:
        Typical processing rates (CPU, default settings):
        - Parsing: ~100-500 records/second
        - NL conversion: ~0.1-0.5s per record
        - Embedding: ~0.1-0.5s per chunk (batch size dependent)
        - Upload: ~0.05-0.2s per chunk
        
        For 10 files (~10,000 records, ~50,000 chunks):
        - Total time: ~10-20 minutes (CPU)
        - GPU acceleration: ~3-5x faster
    
    Note:
        - JSON-to-NL conversion extracts only natural language fields (text, names,
          dates, etc.), excluding purely numeric/categorical data
        - Each record becomes a single TextChunk with original JSON in metadata
        - Subject IDs extracted from SUBJID/subject_id/SubjID fields for metadata
        - Malformed JSON lines are logged and skipped (non-fatal)
        - Empty NL text (all numeric fields) results in skipped records
        - Collection name must match VectorStore.get_collection_name() pattern
        - max_records_per_file doesn't stop at exact limit (processes full files)
    
    See Also:
        jsonl_chunking_nl.TextChunker: Natural language text extraction from JSON
        embeddings.EmbeddingModel: Embedding model wrapper
        vector_store.VectorStore: Vector database operations
        main(): CLI entry point for this function
    """
    vlog("🔍 [INGEST] Entered ingest_records_to_vectordb() function")
    vlog(f"🔍 [INGEST] Parameters - study_name: {study_name}, dataset_type: {dataset_type}, recreate: {recreate_collection}")
    
    logger.info("=" * 80)
    logger.info("STARTING JSONL RECORDS INGESTION TO VECTOR DATABASE")
    logger.info("=" * 80)
    
    # Validate dataset_type
    if dataset_type not in ["cleaned", "original"]:
        logger.error(f"❌ [INGEST] Invalid dataset_type: {dataset_type}")
        raise ValueError(
            f"dataset_type must be 'cleaned' or 'original', got: {dataset_type}"
        )
    
    # Use config defaults if not provided
    if jsonl_dir:
        jsonl_dir = Path(jsonl_dir)
    else:
        # Default: output/deidentified/{study_name}/{dataset_type}
        jsonl_dir = Path(config.OUTPUT_DIR) / "deidentified" / study_name / dataset_type
    
    # Auto-detect collection name based on dataset_type if not provided
    if collection_name is None:
        if dataset_type == "cleaned":
            collection_name = config.JSONL_COLLECTION_CLEANED
        elif dataset_type == "original":
            collection_name = config.JSONL_COLLECTION_ORIGINAL
        else:
            collection_name = config.JSONL_COLLECTION  # Fallback
    
    chunk_size = chunk_size or config.CHUNK_SIZE
    
    vlog(f"🔍 [INGEST] Resolved parameters - jsonl_dir: {jsonl_dir}, collection: {collection_name}, chunk_size: {chunk_size}, dataset_type: {dataset_type}")
    
    # Validate max_records_per_file parameter
    if max_records_per_file is not None and max_records_per_file <= 0:
        logger.error(f"❌ [INGEST] Invalid max_records_per_file: {max_records_per_file}")
        raise ValueError(
            f"max_records_per_file must be a positive integer, got: {max_records_per_file}"
        )
    
    # Validate JSONL directory exists
    if not jsonl_dir.exists():
        logger.error(f"❌ [INGEST] JSONL directory does not exist: {jsonl_dir}")
        raise FileNotFoundError(
            f"JSONL directory not found: {jsonl_dir}\n"
            f"Run de-identification first: python main.py --deidentify"
        )
    
    vlog(f"🔍 [INGEST] ✅ JSONL directory exists: {jsonl_dir}")
    
    logger.info(f"Study: {study_name}")
    logger.info(f"Dataset Type: {dataset_type}")
    logger.info(f"JSONL Directory: {jsonl_dir}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Chunk Size: {chunk_size} tokens")
    
    try:
        # Initialize components
        logger.info("Initializing text chunker with JSON-to-NL converter...")
        vlog(f"🔍 [INGEST] Creating TextChunker with chunk_size={chunk_size}, overlap={config.CHUNK_OVERLAP}")
        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=config.CHUNK_OVERLAP,
            strategy="hybrid"
        )
        vlog("🔍 [INGEST] ✅ TextChunker initialized successfully")
        
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        vlog(f"🔍 [INGEST] Creating EmbeddingModel with model_name={config.EMBEDDING_MODEL}")
        embedder = EmbeddingModel(model_name=config.EMBEDDING_MODEL)
        vlog("🔍 [INGEST] ✅ EmbeddingModel initialized successfully")
        
        logger.info(f"Connecting to vector store: {config.VECTOR_DB_DIR}")
        vlog(f"🔍 [INGEST] Creating VectorStore with storage_path={config.VECTOR_DB_DIR}")
        vector_store = VectorStore(
            embedder,
            storage_path=Path(config.VECTOR_DB_DIR),
            use_memory=False
        )
        vlog("🔍 [INGEST] ✅ VectorStore initialized successfully")
        
        # Verify collection_name matches study-based pattern
        expected_collection = vector_store.get_collection_name(study_name, "jsonl_records")
        if collection_name != expected_collection:
            logger.warning(
                f"Collection name mismatch: config={collection_name}, "
                f"expected={expected_collection}. Using {expected_collection}"
            )
            collection_name = expected_collection
        
        # Create or recreate collection
        if recreate_collection and vector_store.collection_exists(collection_name):
            logger.warning(f"Deleting existing collection: {collection_name}")
            vector_store.delete_collection(collection_name)
        
        # Create collection if it doesn't exist (handles both recreate and first-time creation)
        if not vector_store.collection_exists(collection_name):
            logger.info(f"Creating collection: {collection_name}")
            vector_store.create_collection(
                study_name=study_name,
                dataset_type="jsonl_records"
            )
        else:
            logger.info(f"Using existing collection: {collection_name}")
        
        # Find all JSONL files
        jsonl_files = list(jsonl_dir.glob("*.jsonl"))
        
        if not jsonl_files:
            logger.warning(f"No JSONL files found in {jsonl_dir}")
            return 0
        
        logger.info(f"Found {len(jsonl_files)} JSONL files")
        logger.info("-" * 80)
        
        # Process each JSONL file
        all_chunks: List[TextChunk] = []
        total_records = 0
        
        for idx, jsonl_file in enumerate(jsonl_files, 1):
            logger.info(f"[{idx}/{len(jsonl_files)}] Processing: {jsonl_file.name}")
            
            file_chunks: List[TextChunk] = []
            record_count = 0
            
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check record limit
                        if max_records_per_file and record_count >= max_records_per_file:
                            logger.info(f"  → Reached max records limit: {max_records_per_file}")
                            break
                        
                        try:
                            # Parse JSON record
                            record = json.loads(line)
                            
                            # CRITICAL: Convert JSON to natural language
                            nl_text = chunker.json_to_natural_language(record)
                            
                            if not nl_text:
                                logger.warning(f"  → Line {line_num}: Empty NL text, skipping")
                                continue
                            
                            # Extract subject ID for metadata
                            subject_id = (
                                record.get("SUBJID") or 
                                record.get("subject_id") or 
                                record.get("SubjID") or 
                                ""
                            )
                            
                            # Create chunk with original JSON in metadata
                            chunk = TextChunk(
                                text=nl_text,
                                metadata={
                                    "original_record": record,
                                    "subject_id": subject_id,
                                    "form_name": jsonl_file.stem,
                                    "source_file": jsonl_file.name,
                                },
                                token_count=chunker.count_tokens(nl_text),
                                chunk_index=record_count,
                                source_file=jsonl_file.name,
                                chunk_strategy="json_to_nl"
                            )
                            
                            file_chunks.append(chunk)
                            record_count += 1
                            
                        except json.JSONDecodeError as e:
                            logger.exception(f"  → Line {line_num}: JSON decode error: {e}")
                            continue
                        except Exception as e:
                            logger.exception(f"  → Line {line_num}: Error processing record: {e}")
                            continue
                
                logger.info(f"  → Converted {record_count} records to NL")
                all_chunks.extend(file_chunks)
                total_records += record_count
                
            except Exception as e:
                logger.exception(f"  ✗ Failed to process {jsonl_file.name}: {e}")
                continue
        
        if not all_chunks:
            logger.warning("No records converted from any JSONL files")
            return 0
        
        logger.info("-" * 80)
        logger.info(f"Total records converted: {total_records}")
        logger.info(f"Total chunks created: {len(all_chunks)}")
        logger.info("Starting embedding and ingestion...")
        
        # Ingest to vector database
        count = vector_store.ingest_jsonl_chunks(
            jsonl_chunks=all_chunks,
            collection_name=collection_name,
            batch_size=config.BATCH_SIZE
        )
        
        logger.info("=" * 80)
        logger.info("✅ JSONL INGESTION COMPLETED")
        logger.info(f"   - JSONL files processed: {len(jsonl_files)}")
        logger.info(f"   - Records ingested: {count}")
        logger.info(f"   - Collection: {collection_name}")
        logger.info("=" * 80)
        
        return count
        
    except Exception as e:
        logger.error(f"JSONL ingestion failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to ingest JSONL records: {e}")


def main() -> int:
    """CLI entry point for de-identified JSONL records ingestion to vector database.
    
    Provides command-line interface for ingest_records_to_vectordb() with argument
    parsing, logging configuration, and error handling. Supports all core functionality:
    study selection, dataset type (cleaned/original), custom directories/collections,
    chunk size configuration, collection recreation, record limiting for testing,
    and verbose debug logging.
    
    **Command-line Arguments:**
    
    --study-name STUDY:
        Study identifier for collection naming and directory resolution.
        Default: config.STUDY_NAME (typically 'Indo-VAP')
    
    --dataset-type {cleaned,original}:
        Type of de-identified dataset to ingest:
        - 'cleaned': PHI-removed data, structured fields preserved
        - 'original': Full-fidelity de-identified data
        Default: 'cleaned'
    
    --jsonl-dir PATH:
        Directory containing *.jsonl files to ingest. If not provided,
        auto-resolves to: {OUTPUT_DIR}/deidentified/{study_name}/{dataset_type}/
    
    --collection-name NAME:
        Target vector database collection. If not provided, auto-selects
        based on --dataset-type (JSONL_COLLECTION_CLEANED or _ORIGINAL)
    
    --chunk-size SIZE:
        Maximum tokens per text chunk. Affects semantic search granularity.
        Default: config.CHUNK_SIZE (typically 500)
    
    --recreate:
        Recreate collection (deletes existing data). WARNING: Destructive operation!
        Use with caution in production environments.
    
    --max-records N:
        Maximum records to process per JSONL file. Useful for testing/sampling.
        Must be positive integer. Default: None (process all records)
    
    --verbose:
        Enable verbose debug logging. Shows detailed trace of all operations,
        imports, and internal state. Equivalent to --log-level DEBUG.
    
    --log-level {DEBUG,INFO,WARNING,ERROR}:
        Logging verbosity level. Default: INFO
    
    Returns:
        int: Exit code for CLI:
            - 0: Success (all records ingested)
            - 1: Failure (FileNotFoundError, ValueError, or any exception)
    
    Raises:
        FileNotFoundError: If JSONL directory doesn't exist (exit code 1)
        ValueError: If invalid parameters (dataset_type, max_records) (exit code 1)
        Exception: Any fatal error during ingestion pipeline (exit code 1)
    
    Example:
        Basic ingestion (cleaned data, defaults):
            ```bash
            # Ingest all cleaned JSONL files from default directory
            python -m scripts.vector_db.ingest_records
            
            # Output:
            # ================================================================================
            # STARTING JSONL RECORDS INGESTION TO VECTOR DATABASE
            # ================================================================================
            # Study: Indo-VAP
            # Dataset Type: cleaned
            # JSONL Directory: output/deidentified/Indo-VAP/cleaned
            # Collection: Indo-VAP_records_cleaned
            # ...
            # ✅ JSONL INGESTION COMPLETED
            #    - JSONL files processed: 10
            #    - Records ingested: 5234
            # ================================================================================
            ```
        
        Original dataset with custom settings:
            ```bash
            # Ingest original data with custom chunk size
            python -m scripts.vector_db.ingest_records \
                --dataset-type original \
                --chunk-size 512 \
                --verbose
            ```
        
        Recreate collection and limit records for testing:
            ```bash
            # WARNING: --recreate deletes existing data!
            python -m scripts.vector_db.ingest_records \
                --recreate \
                --max-records 100 \
                --verbose
            ```
        
        Custom directory and collection:
            ```bash
            # Ingest from custom directory to custom collection
            python -m scripts.vector_db.ingest_records \
                --jsonl-dir /path/to/custom/jsonl \
                --collection-name my_custom_collection
            ```
        
        Handle errors gracefully:
            ```bash
            # Missing directory error (exit code 1)
            python -m scripts.vector_db.ingest_records --jsonl-dir /nonexistent
            # Output:
            # ❌ [MAIN] File not found error: JSONL directory not found: /nonexistent
            # Run de-identification first: python main.py --deidentify
            # Exit code: 1
            ```
    
    Side Effects:
        - Resets and reconfigures logging system (log.reset_logging, log.setup_logging)
        - Creates vector database collection if it doesn't exist
        - If --recreate, deletes existing collection data (destructive!)
        - Writes embeddings + metadata to vector database (persistent storage)
        - Logs all operations to console and log files
        - Downloads embedding model on first run (~100-500MB)
    
    Performance:
        Identical to ingest_records_to_vectordb(). Typical processing:
        - 10 files (~10,000 records): ~10-20 minutes (CPU)
        - GPU acceleration: ~3-5x faster
        - Use --max-records for quick testing without full ingestion
    
    Note:
        - Logging configuration: --verbose sets DEBUG level, overrides --log-level
        - log.reset_logging() called to allow reconfiguration after module imports
        - Exit code 0 = success, 1 = any error (FileNotFoundError, ValueError, Exception)
        - --max-records applies per-file, not total (doesn't stop at exact limit)
        - Collection name validation: warns if mismatch with VectorStore pattern
        - Auto-detection of collection/directory based on --dataset-type
    
    See Also:
        ingest_records_to_vectordb(): Core ingestion function (called by this CLI)
        jsonl_chunking_nl.TextChunker: Natural language extraction from JSON
        embeddings.EmbeddingModel: Embedding generation
        vector_store.VectorStore: Vector database operations
    """
    
    vlog("🔍 [MAIN] Entered main() function")
    vlog(f"🔍 [MAIN] sys.argv: {sys.argv}")
    vlog(f"🔍 [MAIN] Current working directory: {Path.cwd()}")
    
    parser = argparse.ArgumentParser(
        description="Ingest de-identified JSONL records into vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--study-name",
        default=config.STUDY_NAME,
        help=f"Study name (default: {config.STUDY_NAME})"
    )
    parser.add_argument(
        "--dataset-type",
        choices=["cleaned", "original"],
        default="cleaned",
        help="Dataset type to ingest: 'cleaned' or 'original' (default: cleaned)"
    )
    parser.add_argument(
        "--jsonl-dir",
        type=Path,
        help="Directory containing JSONL files (default: auto-detect from study name and dataset type)"
    )
    parser.add_argument(
        "--collection-name",
        help=f"Target collection name (default: {config.JSONL_COLLECTION})"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        help=f"Chunk size in tokens (default: {config.CHUNK_SIZE})"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection (deletes existing data)"
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Maximum records per file (for testing, default: all)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup centralized logging with verbose mode if requested
    # Reset first to allow reconfiguration after module imports
    log.reset_logging()
    log_level = 'DEBUG' if args.verbose else args.log_level
    log.setup_logging(
        module_name=__name__,
        log_level=log_level,
        verbose=args.verbose
    )
    
    vlog("🔍 [MAIN] Arguments parsed successfully")
    vlog(f"🔍 [MAIN] Parsed arguments: {vars(args)}")
    
    # Validate max-records
    if args.max_records is not None and args.max_records <= 0:
        logger.error("=" * 80)
        logger.error("❌ [MAIN] --max-records must be a positive integer")
        logger.error("=" * 80)
        return 1
    
    try:
        logger.info("=" * 80)
        logger.info("🚀 [MAIN] Starting JSONL records ingestion via CLI")
        logger.info("=" * 80)
        logger.info(f"📋 [MAIN] Study Name: {args.study_name}")
        logger.info(f"📋 [MAIN] Dataset Type: {args.dataset_type}")
        logger.info(f"📋 [MAIN] JSONL Directory: {args.jsonl_dir or 'auto-detect'}")
        logger.info(f"📋 [MAIN] Collection Name: {args.collection_name or 'auto-detect from dataset_type'}")
        logger.info(f"📋 [MAIN] Chunk Size: {args.chunk_size or config.CHUNK_SIZE}")
        logger.info(f"📋 [MAIN] Recreate Collection: {args.recreate}")
        logger.info(f"📋 [MAIN] Max Records Per File: {args.max_records or 'all'}")
        logger.info("=" * 80)
        
        vlog("🔍 [MAIN] Calling ingest_records_to_vectordb()...")
        count = ingest_records_to_vectordb(
            study_name=args.study_name,
            jsonl_dir=args.jsonl_dir,
            collection_name=args.collection_name,
            chunk_size=args.chunk_size,
            recreate_collection=args.recreate,
            max_records_per_file=args.max_records,
            dataset_type=args.dataset_type
        )
        vlog(f"🔍 [MAIN] ingest_records_to_vectordb() completed, returned count: {count}")
        logger.info("=" * 80)
        logger.info(f"✅ [MAIN] Successfully ingested {count} JSONL records")
        logger.info("=" * 80)
        return 0
    except FileNotFoundError as e:
        logger.error("=" * 80)
        logger.error(f"❌ [MAIN] File not found error: {e}")
        logger.error("=" * 80)
        return 1
    except ValueError as e:
        logger.error("=" * 80)
        logger.error(f"❌ [MAIN] Invalid parameter: {e}")
        logger.error("=" * 80)
        return 1
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ [MAIN] JSONL ingestion failed: {e}", exc_info=True)
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
