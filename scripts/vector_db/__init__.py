"""Vector database and embedding utilities."""

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
