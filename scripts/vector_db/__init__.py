"""Vector database and embedding utilities for semantic search.

This subpackage provides complete vector database functionality including
embedding generation, document chunking, vector storage abstraction, and
ingestion pipelines. It supports dual-backend architecture (ChromaDB and
Qdrant) with automatic fallback and lazy loading for performance.

Package Architecture:
    **Embedding Generation**:
        - embeddings.py: Core embedding model wrapper (SentenceTransformers)
        - adaptive_embeddings.py: Multi-model adaptive embedder with fallback
    
    **Document Chunking**:
        - pdf_chunking.py: PDF document chunking with structure awareness
        - jsonl_chunking_nl.py: JSONL record chunking with field-level control
    
    **Vector Storage**:
        - vector_store.py: Unified interface for ChromaDB/Qdrant backends
    
    **Ingestion Pipelines**:
        - ingest_pdfs.py: PDF form ingestion to vector database
        - ingest_records.py: JSONL patient record ingestion

Lazy Loading Design:
    This package uses lazy imports via `__getattr__` to avoid loading heavy
    dependencies (sentence-transformers, chromadb, qdrant-client) until they
    are actually needed. This significantly improves import time and allows
    the main pipeline to start faster.
    
    Benefits:
        - Faster startup (no heavy ML model loading at import)
        - Memory efficiency (models loaded only when used)
        - Graceful degradation (missing deps only fail when accessed)

Public API:
    **Embedding Models**:
        - EmbeddingModel: SentenceTransformer wrapper
        - AdaptiveEmbedder: Multi-model embedder with automatic fallback
        - ModelType: Enum for model selection (SMALL, MEDIUM, LARGE)
    
    **Chunking**:
        - TextChunker: JSONL/text chunking with semantic awareness
        - PDFChunker: PDF chunking preserving document structure
    
    **Storage**:
        - VectorStore: Unified vector DB interface (ChromaDB + Qdrant)
    
    **Future APIs** (not yet implemented):
        - IngestionPipeline: Unified ingestion interface
        - search_dual_db: Cross-collection search

Module Attributes:
    __all__ (list): Public API exports (includes future placeholders)

Example:
    >>> # Lazy loading - no imports until actually used
    >>> from scripts.vector_db import EmbeddingModel, TextChunker
    >>> 
    >>> # Create embedder (loads SentenceTransformers at this point)
    >>> embedder = EmbeddingModel(model_name="all-MiniLM-L6-v2")  # doctest: +SKIP
    >>> 
    >>> # Chunk text
    >>> chunker = TextChunker(chunk_size=512, chunk_overlap=50)  # doctest: +SKIP
    >>> chunks = chunker.chunk_text("Long document text...")  # doctest: +SKIP
    >>> 
    >>> # Generate embeddings
    >>> embeddings = embedder.embed(chunks)  # doctest: +SKIP

Notes:
    - All classes are lazily loaded via `__getattr__`
    - Future APIs raise NotImplementedError when accessed
    - Heavy dependencies (transformers, chromadb) loaded on first use
    - See config.py for vector DB configuration (model, dims, etc.)

See Also:
    config.py: Vector database configuration (models, paths, collection names)
    scripts.vector_db.vector_store: Core vector storage implementation
    main.py: Uses --ingest-pdfs and --ingest-records flags
"""

# Lazy imports for performance
def __getattr__(name):
    """Lazy load modules on first access."""
    if name == "EmbeddingModel":
        from .embeddings import EmbeddingModel
        return EmbeddingModel
    elif name == "AdaptiveEmbedder":
        from .adaptive_embeddings import AdaptiveEmbedder
        return AdaptiveEmbedder
    elif name == "ModelType":
        from .adaptive_embeddings import ModelType
        return ModelType
    elif name == "TextChunker":
        from .jsonl_chunking_nl import TextChunker
        return TextChunker
    elif name == "PDFChunker":
        from .pdf_chunking import PDFChunker
        return PDFChunker
    elif name == "VectorStore":
        from .vector_store import VectorStore
        return VectorStore
    elif name == "IngestionPipeline":
        # Placeholder for future implementation
        raise NotImplementedError("IngestionPipeline not yet implemented")
    elif name == "search_dual_db":
        # Placeholder for future implementation
        raise NotImplementedError("search_dual_db not yet implemented")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Expose main components for easy import
__all__ = [
    "EmbeddingModel",
    "AdaptiveEmbedder",  # New: Adaptive multi-model embedder
    "ModelType",  # New: Model type enum for adaptive selection
    "TextChunker",
    "PDFChunker",
    "VectorStore",
    "IngestionPipeline",
    "search_dual_db",
]
