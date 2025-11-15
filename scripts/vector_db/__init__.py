"""
Vector Database Module for RePORTaLiN.

This module provides functionality for:
- Embedding generation from clinical text (single-model and adaptive multi-model)
- Smart chunking strategies for clinical forms and PDFs
- Vector database management (Qdrant)
- Dual-DB architecture (cleaned + original datasets)
- Semantic search with fallback logic
- PDF processing and chunking for annotated clinical forms

Modules:
    embeddings: Embedding model wrapper and management (single-model)
    adaptive_embeddings: Adaptive multi-model embedder with auto-selection
    jsonl_chunking_nl: Text chunking strategies and JSON-to-NL converter for JSONL data
    pdf_chunking: PDF extraction and chunking with metadata preservation
    vector_store: Qdrant vector database interface
    ingestion_pipeline: Full pipeline from JSONL/PDF to vector DB
    search: Search interface with dual-DB fallback

Example:
    >>> from scripts.vector_db import VectorStore, EmbeddingModel, AdaptiveEmbedder, PDFChunker
    >>> 
    >>> # Single-model approach
    >>> embedder = EmbeddingModel()
    >>> vector_store = VectorStore(embedder)
    >>> 
    >>> # Adaptive multi-model approach (automatic medical/general detection)
    >>> adaptive_embedder = AdaptiveEmbedder()
    >>> result = adaptive_embedder.encode(["Patient has TB symptoms"])  # Uses BioLORD
    >>> 
    >>> # PDF chunking
    >>> pdf_chunker = PDFChunker(chunk_size=512)
    >>> 
    >>> # Search with fallback
    >>> results = vector_store.search("TB symptoms in index cases", use_fallback=True)
"""

__version__ = "1.0.0"
__author__ = "RePORTaLiN Development Team"

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
