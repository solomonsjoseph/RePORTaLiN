"""
JSONL Records Ingestion Module for Vector Database.

This module handles ingestion of de-identified patient records (JSONL format)
into the vector database. It converts structured JSON to natural language
for optimal semantic search. Supports both 'cleaned' and 'original' datasets
for comprehensive data coverage.

Key Features:
    - JSON-to-NL conversion (works with ANY domain, not just clinical)
    - Generic field name humanization
    - Automatic entity type detection (patient, order, sensor, etc.)
    - Preserves original JSON in metadata
    - Dual dataset support (cleaned and original)
    - Progress tracking and error handling

Collections:
    - Target: {study_name}_jsonl_records_cleaned (processed data)
    - Target: {study_name}_jsonl_records_original (complete data)
    - Purpose: Structured search of patient data with fallback support
    - Content: De-identified patient records (JSONL)

Author: RePORTaLiN Development Team
Date: November 2025
Version: 0.3.1
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
    """
    Ingest all JSONL records to vector database.
    
    Process:
    1. Find all JSONL files in deidentified/{study_name}/{dataset_type}/
    2. Convert each JSON record to natural language (generic, works with any data)
    3. Embed NL sentences
    4. Store with original JSON in metadata
    
    Args:
        study_name: Name of the study (e.g., "Indo-VAP")
        jsonl_dir: Directory containing JSONL files (defaults to auto-detect)
        collection_name: Target collection name (defaults to auto-detect from dataset_type)
        chunk_size: Chunk size in tokens (defaults to config.CHUNK_SIZE)
        recreate_collection: If True, delete and recreate collection
        max_records_per_file: Limit records per file (for testing, must be > 0)
        dataset_type: Type of dataset - 'cleaned' or 'original' (default: 'cleaned')
    
    Returns:
        Total number of records ingested
    
    Raises:
        FileNotFoundError: If JSONL directory doesn't exist
        ValueError: If max_records_per_file is invalid (≤ 0) or dataset_type is invalid
        RuntimeError: If ingestion fails
    
    Example:
        >>> from scripts.vector_db.ingest_records import ingest_records_to_vectordb
        >>> # Ingest cleaned dataset
        >>> count = ingest_records_to_vectordb(study_name="Indo-VAP", dataset_type="cleaned")
        >>> print(f"Ingested {count} records")
        Ingested 57017 records
        
        >>> # Ingest original dataset
        >>> count = ingest_records_to_vectordb(study_name="Indo-VAP", dataset_type="original")
        >>> print(f"Ingested {count} records")
        Ingested 57017 records
    
    .. versionadded:: 0.3.0
       Generic JSON-to-NL ingestion for vector database.
    
    .. versionchanged:: 0.3.1
       Added dataset_type parameter to support both 'cleaned' and 'original' datasets.
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
    """
    CLI entry point for JSONL records ingestion.
    
    Provides command-line interface for ingesting de-identified patient
    records (JSONL format) into the vector database.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    
    Example:
        >>> python -m scripts.vector_db.ingest_records --help
        >>> python -m scripts.vector_db.ingest_records --recreate
        >>> python -m scripts.vector_db.ingest_records --max-records 100
    """
    
    vlog("🔍 [MAIN] Entered main() function")
    vlog(f"🔍 [MAIN] sys.argv: {sys.argv}")
    vlog(f"🔍 [MAIN] Current working directory: {Path.cwd()}")
    
    parser = argparse.ArgumentParser(
        description="Ingest de-identified JSONL records into vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all cleaned JSONL records (default)
  python -m scripts.vector_db.ingest_records
  
  # Ingest original JSONL records
  python -m scripts.vector_db.ingest_records --dataset-type original
  
  # Recreate collection and ingest cleaned records
  python -m scripts.vector_db.ingest_records --recreate --dataset-type cleaned
  
  # Limit records per file (for testing)
  python -m scripts.vector_db.ingest_records --max-records 100
  
  # Custom JSONL directory
  python -m scripts.vector_db.ingest_records --jsonl-dir /path/to/jsonl
        """
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
