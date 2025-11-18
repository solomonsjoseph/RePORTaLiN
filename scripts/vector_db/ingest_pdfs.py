"""PDF ingestion pipeline for vector database with chunking and retry logic.

Orchestrates end-to-end PDF ingestion workflow: discovers annotated research forms,
extracts structured content via PDFChunker, generates embeddings, and uploads to
vector database. Designed for clinical research data forms (CRFs) with automatic
retry on failures, progress tracking, and comprehensive error reporting.

**Pipeline Architecture:**
```
PDF Files → PDFChunker → Chunks → EmbeddingModel → Vectors → VectorStore
              ↓             ↓          ↓                ↓           ↓
         Extract text   Metadata   Generate         Standardize  Qdrant/Chroma
         + structure    tracking   embeddings       dimensions   persistence
```

**Key Features:**
- **Batch Processing**: Processes all PDFs in directory with configurable batch sizes
- **Automatic Retry**: Configurable retry attempts (default: 3) for transient failures
- **Progress Tracking**: Optional tqdm progress bars with detailed metrics
- **Dry Run Mode**: Test extraction without database writes
- **Collection Management**: Create/recreate vector database collections
- **Performance Metrics**: Tracks processing time, chunks/PDF, success rates
- **Verbose Logging**: Comprehensive debug logging for troubleshooting

**Processing Workflow:**

1. **Discovery**: Scan annotated_pdfs_dir for *.pdf files
2. **Validation**: Verify directory exists, check for PDFs
3. **Initialization**: Load PDFChunker, EmbeddingModel, VectorStore
4. **Extraction**: Chunk each PDF with structure detection (retry on failure)
5. **Embedding**: Generate vectors for all chunks (batch processing)
6. **Ingestion**: Upload embeddings + metadata to vector store
7. **Reporting**: Log performance metrics and success/failure summary

**Retry Logic:**

Failed PDFs retried up to max_retries (default: 3) with:
- Per-PDF retry (not per-chunk) for efficiency
- Last error tracked and reported
- Successful PDFs counted immediately
- Failed PDFs logged with error messages

**Performance Characteristics:**

Typical performance (CPU, default settings):
- **Extraction**: ~2-5 seconds per PDF (varies by page count, complexity)
- **Embedding**: ~0.1-0.5 seconds per chunk (depends on model, batch size)
- **Upload**: ~0.05-0.2 seconds per chunk (network/disk I/O)

For 30 PDFs (~300 chunks):
- Total time: ~3-5 minutes (CPU)
- GPU acceleration: ~2-3x faster for embedding

**Usage Patterns:**

Basic ingestion (default settings):
    >>> from scripts.vector_db.ingest_pdfs import ingest_pdfs_to_vectordb
    >>> # Ingest all PDFs from default directory
    >>> count = ingest_pdfs_to_vectordb()  # doctest: +SKIP
    >>> print(f"Ingested {count} chunks")  # doctest: +SKIP

Custom configuration:
    >>> from pathlib import Path
    >>> count = ingest_pdfs_to_vectordb(
    ...     study_name='Indo-VAP',
    ...     annotated_pdfs_dir=Path('/data/pdfs'),
    ...     collection_name='my_pdf_collection',
    ...     chunk_size=512,
    ...     recreate_collection=True,
    ...     max_retries=5,
    ...     show_progress=True
    ... )  # doctest: +SKIP

Dry run testing:
    >>> # Test extraction without database writes
    >>> count = ingest_pdfs_to_vectordb(
    ...     dry_run=True,
    ...     show_progress=True
    ... )  # doctest: +SKIP
    >>> print(f"Would ingest {count} chunks")  # doctest: +SKIP

CLI usage:
    ```bash
    # Basic ingestion
    python -m scripts.vector_db.ingest_pdfs
    
    # Recreate collection and ingest
    python -m scripts.vector_db.ingest_pdfs --recreate
    
    # Dry run with verbose logging
    python -m scripts.vector_db.ingest_pdfs --dry-run --verbose
    
    # Custom directory
    python -m scripts.vector_db.ingest_pdfs --pdf-dir /path/to/pdfs
    ```

**Dependencies:**
- PDFChunker: Extracts structured chunks from PDFs (pdf_chunking.py)
- EmbeddingModel: Generates text embeddings (embeddings.py)
- VectorStore: Manages vector database operations (vector_store.py)
- config: Global configuration (paths, model names, chunk sizes)
- tqdm: Optional progress bars (gracefully degrades if missing)

**Error Handling:**
- FileNotFoundError: PDF directory doesn't exist
- PDFChunker errors: Malformed PDFs, encoding issues (retried)
- Embedding errors: Model loading failures (fatal, not retried)
- VectorStore errors: Connection issues, schema mismatches (fatal)

**Configuration:**

Uses config.py defaults (overrideable via arguments):
- ANNOTATED_PDFS_DIR: PDF source directory
- PDF_COLLECTION: Target collection name
- CHUNK_SIZE: Chunk size in tokens (default: 500)
- CHUNK_OVERLAP: Overlap between chunks (default: 50)
- BATCH_SIZE: Embedding batch size (default: 32)
- EMBEDDING_MODEL: Model identifier (default: all-MiniLM-L6-v2)
- VECTOR_DB_DIR: Vector database storage path

See Also:
    pdf_chunking.py: PDF text extraction and chunking logic
    embeddings.py: Embedding model wrapper
    vector_store.py: Vector database abstraction
    ingest_records.py: Parallel module for ingesting JSONL records

Note:
    First run downloads embedding model (~100-500MB) from Hugging Face Hub.
    Subsequent runs use local cache. Collection recreation deletes existing
    data—use with caution in production.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from time import time

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
    vlog("🔍 [IMPORT] Importing pdf_chunking module...")
    from .pdf_chunking import PDFChunker, PDFChunk
    vlog("🔍 [IMPORT] ✅ PDFChunker and PDFChunk imported successfully")
except Exception as e:
    logger.error(f"❌ [IMPORT] Failed to import pdf_chunking: {e}", exc_info=True)
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

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    vlog("tqdm not available - progress bars disabled")


def ingest_pdfs_to_vectordb(
    study_name: str = "Indo-VAP",
    annotated_pdfs_dir: Optional[Path] = None,
    collection_name: Optional[str] = None,
    chunk_size: Optional[int] = None,
    recreate_collection: bool = False,
    dry_run: bool = False,
    max_retries: int = 3,
    show_progress: bool = True
) -> int:
    """Ingest all annotated PDF forms to vector database with retry logic.
    
    Complete PDF ingestion pipeline that discovers PDFs, extracts structured chunks,
    generates embeddings, and uploads to vector store. Handles failures gracefully
    with configurable retry attempts and comprehensive error reporting.
    
    **Processing Steps:**
    1. Validate PDF directory exists
    2. Initialize PDFChunker, EmbeddingModel, VectorStore
    3. Discover all *.pdf files in directory
    4. For each PDF (with retry on failure):
       - Extract chunks with PDFChunker (form code, title, metadata)
       - Track success/failure with error messages
    5. Generate embeddings for all chunks (batch processing)
    6. Upload embeddings + metadata to vector store
    7. Report performance metrics and failures
    
    **Retry Behavior:**
    - Retries entire PDF extraction (not individual chunks)
    - Attempts: 1 initial + (max_retries - 1) retries = max_retries total
    - Logs warnings on retry, errors on final failure
    - Failed PDFs tracked separately for reporting
    
    **Dry Run Mode:**
    When dry_run=True:
    - Performs PDF extraction and chunking
    - Skips embedding generation
    - Skips vector database upload
    - Returns chunk count that would be ingested
    - Useful for testing extraction logic
    
    Args:
        study_name: Study identifier for collection naming. Used to generate
            collection name like '{study_name}_pdf_forms'. Default: 'Indo-VAP'.
        annotated_pdfs_dir: Directory containing annotated PDF forms. If None,
            uses config.ANNOTATED_PDFS_DIR. Must exist and contain *.pdf files.
        collection_name: Target vector database collection. If None, auto-generated
            from study_name. Format: '{study_name}_pdf_forms'.
        chunk_size: Maximum chunk size in tokens. If None, uses config.CHUNK_SIZE
            (default: 500). Larger chunks = fewer chunks but more context.
        recreate_collection: If True, delete existing collection before creating
            new one. WARNING: Deletes all existing data. Default: False.
        dry_run: If True, extract and count chunks but skip database upload.
            Useful for testing. Default: False.
        max_retries: Maximum retry attempts for failed PDF extractions. Total
            attempts = max_retries (1 initial + retries). Default: 3.
        show_progress: Show tqdm progress bars during processing. Requires tqdm
            installed. Degrades gracefully if unavailable. Default: True.
    
    Returns:
        Number of chunks successfully ingested (or extracted if dry_run=True).
        Returns 0 if no PDFs found or all extractions failed.
    
    Raises:
        FileNotFoundError: If annotated_pdfs_dir doesn't exist.
        RuntimeError: If embedding model loading fails, vector store connection
            fails, or critical error during ingestion.
    
    Side Effects:
        - Logs extensive INFO/DEBUG messages (controlled by logging config)
        - Creates/modifies vector database collection (unless dry_run=True)
        - Downloads embedding model on first run (~100-500MB)
        - Writes performance metrics to logger
        - Shows tqdm progress bars if show_progress=True and tqdm available
    
    Example:
        >>> from scripts.vector_db.ingest_pdfs import ingest_pdfs_to_vectordb
        >>> from pathlib import Path
        >>> # Basic ingestion with defaults
        >>> count = ingest_pdfs_to_vectordb()  # doctest: +SKIP
        >>> print(f"Ingested {count} chunks")  # doctest: +SKIP
        >>> # Custom configuration
        >>> count = ingest_pdfs_to_vectordb(
        ...     study_name='Indo-VAP',
        ...     annotated_pdfs_dir=Path('/data/indo-vap/pdfs'),
        ...     chunk_size=512,
        ...     recreate_collection=True,
        ...     max_retries=5,
        ...     show_progress=True
        ... )  # doctest: +SKIP
        >>> # Dry run for testing
        >>> count = ingest_pdfs_to_vectordb(
        ...     dry_run=True,
        ...     show_progress=False
        ... )  # doctest: +SKIP
        >>> print(f"Would ingest {count} chunks (dry run)")  # doctest: +SKIP
    
    Note:
        - Progress bars use tqdm if available; otherwise uses standard logging
        - Verbose logging via vlog() only shown if verbose mode enabled
        - Failed PDFs logged with filename and error message
        - Performance metrics include per-PDF averages
        - Collection recreation is irreversible—backup data first!
    """
    vlog("🔍 [INGEST] Entered ingest_pdfs_to_vectordb() function")
    vlog(f"🔍 [INGEST] Parameters - study_name: {study_name}, recreate: {recreate_collection}, dry_run: {dry_run}")
    
    logger.info("=" * 80)
    logger.info("STARTING PDF INGESTION TO VECTOR DATABASE")
    if dry_run:
        logger.info("*** DRY RUN MODE - NO DATA WILL BE WRITTEN ***")
    logger.info("=" * 80)
    
    # Performance tracking
    start_time = time()
    metrics: Dict[str, Any] = {
        'total_pdfs': 0,
        'successful_pdfs': 0,
        'failed_pdfs': 0,
        'total_chunks': 0,
        'pdf_processing_time': 0.0,
        'embedding_time': 0.0,
        'total_time': 0.0
    }
    
    # Use config defaults if not provided
    pdf_dir = Path(annotated_pdfs_dir) if annotated_pdfs_dir else Path(config.ANNOTATED_PDFS_DIR)
    collection_name = collection_name or config.PDF_COLLECTION
    chunk_size = chunk_size or config.CHUNK_SIZE
    
    vlog(f"🔍 [INGEST] Resolved parameters - pdf_dir: {pdf_dir}, collection: {collection_name}, chunk_size: {chunk_size}")
    
    # Validate PDF directory exists
    if not pdf_dir.exists():
        logger.error(f"❌ [INGEST] PDF directory does not exist: {pdf_dir}")
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")
    
    vlog(f"🔍 [INGEST] ✅ PDF directory exists: {pdf_dir}")
    
    logger.info(f"Study: {study_name}")
    logger.info(f"PDF Directory: {pdf_dir}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Chunk Size: {chunk_size} tokens")
    logger.info(f"Overlap: {config.CHUNK_OVERLAP} tokens")
    logger.info(f"Max Retries: {max_retries}")
    logger.info(f"Dry Run: {dry_run}")
    vlog(f"Show Progress: {show_progress}")
    vlog(f"TQDM Available: {TQDM_AVAILABLE}")
    
    try:
        # Initialize components
        logger.info("Initializing PDF chunker...")
        vlog(f"🔍 [INGEST] Creating PDFChunker with chunk_size={chunk_size}, overlap={config.CHUNK_OVERLAP}")
        pdf_chunker = PDFChunker(
            chunk_size=chunk_size,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        vlog("🔍 [INGEST] ✅ PDFChunker initialized successfully")
        
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        vlog(f"🔍 [INGEST] Creating EmbeddingModel with model_name={config.EMBEDDING_MODEL}")
        embedder = EmbeddingModel(model_name=config.EMBEDDING_MODEL)
        vlog("🔍 [INGEST] ✅ EmbeddingModel initialized successfully")
        
        if not dry_run:
            logger.info(f"Connecting to vector store: {config.VECTOR_DB_DIR}")
            vector_store = VectorStore(
                embedder,
                storage_path=Path(config.VECTOR_DB_DIR),
                use_memory=False
            )
            
            # Verify collection_name matches study-based pattern
            expected_collection = vector_store.get_collection_name(study_name, "pdf_forms")
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
            
            if not vector_store.collection_exists(collection_name):
                logger.info(f"Creating collection: {collection_name}")
                vector_store.create_collection(
                    study_name=study_name,
                    dataset_type="pdf_forms"
                )
            else:
                logger.info(f"Using existing collection: {collection_name}")
        else:
            logger.info("Skipping vector store connection (dry run mode)")
            vector_store = None
        
        # Find all PDFs
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return 0
        
        metrics['total_pdfs'] = len(pdf_files)
        logger.info(f"Found {len(pdf_files)} PDF files")
        logger.info("-" * 80)
        
        # Process each PDF with optional progress bar
        all_chunks: List[PDFChunk] = []
        failed_pdfs: List[tuple] = []  # (filename, error_message)
        
        # Setup progress bar or iterator
        use_tqdm = show_progress and TQDM_AVAILABLE
        pdf_iterator = tqdm(pdf_files, desc="Processing PDFs", unit="file") if use_tqdm else pdf_files
        
        pdf_start = time()
        
        for idx, pdf_file in enumerate(pdf_iterator, start=1):
            # Use vlog for verbose logging with tqdm, INFO level without tqdm
            if use_tqdm:
                vlog(f"[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            else:
                logger.info(f"[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            success = False
            last_error = None
            
            # Retry logic
            for attempt in range(1, max_retries + 1):
                try:
                    # Chunk PDF with dynamic structure detection
                    chunks = pdf_chunker.chunk_pdf(
                        pdf_path=pdf_file,
                        base_path=pdf_dir.parent
                    )
                    
                    if use_tqdm:
                        vlog(f"  → Extracted {len(chunks)} chunks")
                        if chunks:
                            vlog(f"  → Form Code: {chunks[0].form_code}")
                            vlog(f"  → Form Title: {chunks[0].form_title}")
                    else:
                        logger.info(f"  → Extracted {len(chunks)} chunks")
                        if chunks:
                            logger.info(f"  → Form Code: {chunks[0].form_code}")
                            logger.info(f"  → Form Title: {chunks[0].form_title}")
                    
                    all_chunks.extend(chunks)
                    success = True
                    metrics['successful_pdfs'] += 1
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries:
                        logger.warning(f"  ⚠ Attempt {attempt}/{max_retries} failed: {e}")
                        vlog(f"  → Retrying {pdf_file.name}...")
                    else:
                        logger.error(f"  ✗ Failed after {max_retries} attempts: {e}")
            
            if not success:
                failed_pdfs.append((pdf_file.name, last_error))
                metrics['failed_pdfs'] += 1
        
        pdf_end = time()
        metrics['pdf_processing_time'] = pdf_end - pdf_start
        
        if not all_chunks:
            logger.warning("No chunks extracted from any PDFs")
            return 0
        
        metrics['total_chunks'] = len(all_chunks)
        
        logger.info("-" * 80)
        logger.info(f"Total chunks extracted: {len(all_chunks)}")
        
        # Report failed PDFs if any
        if failed_pdfs:
            logger.warning(f"Failed to process {len(failed_pdfs)} PDF(s):")
            for filename, error in failed_pdfs:
                logger.warning(f"  - {filename}: {error}")
        
        if dry_run:
            logger.info("DRY RUN: Skipping embedding and ingestion")
            count = len(all_chunks)
        else:
            logger.info("Starting embedding and ingestion...")
            embedding_start = time()
            
            # Ingest to vector database
            count = vector_store.ingest_pdf_chunks(
                pdf_chunks=all_chunks,
                collection_name=collection_name,
                batch_size=config.BATCH_SIZE
            )
            
            embedding_end = time()
            metrics['embedding_time'] = embedding_end - embedding_start
        
        end_time = time()
        metrics['total_time'] = end_time - start_time
        
        # Performance metrics
        logger.info("=" * 80)
        logger.info(f"✅ PDF INGESTION {'SIMULATION ' if dry_run else ''}COMPLETED")
        logger.info(f"   - PDFs processed: {metrics['successful_pdfs']}/{metrics['total_pdfs']}")
        if metrics['failed_pdfs'] > 0:
            logger.info(f"   - PDFs failed: {metrics['failed_pdfs']}")
        logger.info(f"   - Chunks {'extracted' if dry_run else 'ingested'}: {count}")
        logger.info(f"   - Collection: {collection_name}")
        logger.info("-" * 80)
        logger.info("PERFORMANCE METRICS:")
        logger.info(f"   - PDF Processing: {metrics['pdf_processing_time']:.2f}s")
        if not dry_run:
            logger.info(f"   - Embedding & Upload: {metrics['embedding_time']:.2f}s")
        logger.info(f"   - Total Time: {metrics['total_time']:.2f}s")
        if metrics['successful_pdfs'] > 0:
            logger.info(f"   - Avg Time/PDF: {metrics['pdf_processing_time']/metrics['successful_pdfs']:.2f}s")
            logger.info(f"   - Avg Chunks/PDF: {metrics['total_chunks']/metrics['successful_pdfs']:.1f}")
        logger.info("=" * 80)
        
        return count
        
    except Exception as e:
        logger.error(f"PDF ingestion failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to ingest PDFs: {e}")


def main() -> int:
    """CLI entry point for PDF ingestion with comprehensive argument parsing.
    
    Command-line interface for PDF ingestion pipeline. Parses arguments, configures
    logging, and invokes ingest_pdfs_to_vectordb() with validated parameters.
    Supports all ingestion options via command-line flags with sensible defaults.
    
    **Command-Line Arguments:**
    
    Required (with defaults):
        --study-name: Study identifier (default: from config.STUDY_NAME)
        
    Optional:
        --pdf-dir: PDF source directory (default: config.ANNOTATED_PDFS_DIR)
        --collection-name: Target collection (default: auto-generated)
        --chunk-size: Chunk size in tokens (default: config.CHUNK_SIZE)
        --recreate: Recreate collection flag (default: False)
        --dry-run: Test mode without database writes (default: False)
        --max-retries: Retry attempts (default: 3)
        --no-progress: Disable progress bars (default: False, shows progress)
        --verbose: Enable verbose debug logging (default: False)
        --log-level: Logging level DEBUG/INFO/WARNING/ERROR (default: INFO)
    
    **Exit Codes:**
        0: Success (all PDFs ingested or dry run completed)
        1: Failure (directory not found, ingestion error, critical exception)
    
    **Logging Configuration:**
    - Resets logging system before setup (allows reconfiguration)
    - Verbose mode (-v/--verbose) enables DEBUG level + verbose logger
    - Log level can be set explicitly via --log-level
    - Verbose mode overrides --log-level to DEBUG
    
    Returns:
        Integer exit code: 0 for success, 1 for failure. Use with sys.exit().
    
    Side Effects:
        - Reconfigures logging system (resets then sets up with args)
        - Logs extensive INFO/DEBUG messages
        - Invokes ingest_pdfs_to_vectordb() with all side effects
        - Exits with appropriate status code
    
    Example:
        >>> # Run from command line (not in doctest)
        >>> # python -m scripts.vector_db.ingest_pdfs  # doctest: +SKIP
        >>> # python -m scripts.vector_db.ingest_pdfs --recreate --verbose  # doctest: +SKIP
        >>> # python -m scripts.vector_db.ingest_pdfs --dry-run --no-progress  # doctest: +SKIP
    
    CLI Examples:
        ```bash
        # Basic ingestion with defaults
        python -m scripts.vector_db.ingest_pdfs
        
        # Recreate collection and ingest with progress
        python -m scripts.vector_db.ingest_pdfs --recreate
        
        # Dry run with verbose logging (no database writes)
        python -m scripts.vector_db.ingest_pdfs --dry-run --verbose
        
        # Custom PDF directory and chunk size
        python -m scripts.vector_db.ingest_pdfs \\
            --pdf-dir /data/pdfs \\
            --chunk-size 512
        
        # Production run with custom settings
        python -m scripts.vector_db.ingest_pdfs \\
            --study-name Indo-VAP \\
            --max-retries 5 \\
            --log-level WARNING \\
            --no-progress
        ```
    
    Note:
        - Help text shown via: python -m scripts.vector_db.ingest_pdfs --help
        - Verbose mode very detailed (use for debugging only)
        - Default log level INFO balances detail and readability
        - Progress bars require tqdm (degrades gracefully if missing)
    """
    vlog("🔍 [MAIN] Entered main() function")
    vlog(f"🔍 [MAIN] sys.argv: {sys.argv}")
    vlog(f"🔍 [MAIN] Current working directory: {Path.cwd()}")
    
    parser = argparse.ArgumentParser(
        description="Ingest annotated PDF forms into vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all PDFs with default settings
  python -m scripts.vector_db.ingest_pdfs
  
  # Recreate collection and ingest
  python -m scripts.vector_db.ingest_pdfs --recreate
  
  # Dry run to test without writing to database
  python -m scripts.vector_db.ingest_pdfs --dry-run
  
  # Custom PDF directory
  python -m scripts.vector_db.ingest_pdfs --pdf-dir /path/to/pdfs
        """
    )
    
    parser.add_argument(
        "--study-name",
        default=config.STUDY_NAME,
        help=f"Study name (default: {config.STUDY_NAME})"
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        help=f"Directory containing PDFs (default: {config.ANNOTATED_PDFS_DIR})"
    )
    parser.add_argument(
        "--collection-name",
        help=f"Target collection name (default: {config.PDF_COLLECTION})"
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
        "--dry-run",
        action="store_true",
        help="Process PDFs without uploading to vector database"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for failed PDFs (default: 3)"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
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
    
    try:
        logger.info("=" * 80)
        logger.info("🚀 [MAIN] Starting PDF ingestion via CLI")
        logger.info("=" * 80)
        logger.info(f"📋 [MAIN] Study Name: {args.study_name}")
        logger.info(f"📋 [MAIN] PDF Directory: {args.pdf_dir or config.ANNOTATED_PDFS_DIR}")
        logger.info(f"📋 [MAIN] Collection Name: {args.collection_name or config.PDF_COLLECTION}")
        logger.info(f"📋 [MAIN] Chunk Size: {args.chunk_size or config.CHUNK_SIZE}")
        logger.info(f"📋 [MAIN] Recreate Collection: {args.recreate}")
        logger.info(f"📋 [MAIN] Dry Run: {args.dry_run}")
        logger.info(f"📋 [MAIN] Max Retries: {args.max_retries}")
        logger.info(f"📋 [MAIN] Show Progress: {not args.no_progress}")
        logger.info("=" * 80)
        
        vlog("🔍 [MAIN] Calling ingest_pdfs_to_vectordb()...")
        count = ingest_pdfs_to_vectordb(
            study_name=args.study_name,
            annotated_pdfs_dir=args.pdf_dir,
            collection_name=args.collection_name,
            chunk_size=args.chunk_size,
            recreate_collection=args.recreate,
            dry_run=args.dry_run,
            max_retries=args.max_retries,
            show_progress=not args.no_progress
        )
        vlog(f"🔍 [MAIN] ingest_pdfs_to_vectordb() completed, returned count: {count}")
        logger.info("=" * 80)
        logger.info(f"✅ [MAIN] Successfully {'processed' if args.dry_run else 'ingested'} {count} PDF chunks")
        logger.info("=" * 80)
        return 0
    except FileNotFoundError as e:
        logger.error("=" * 80)
        logger.error(f"❌ [MAIN] File not found error: {e}")
        logger.error("=" * 80)
        return 1
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ [MAIN] PDF ingestion failed: {e}", exc_info=True)
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

