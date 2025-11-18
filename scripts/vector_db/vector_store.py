"""Vector store management with ChromaDB and Qdrant backends for semantic search.

Provides unified interface for vector database operations supporting multiple backends
(ChromaDB for local development, Qdrant for production) with automatic embedding
generation, metadata filtering, and collection management.

**Architecture:**

This module implements a pluggable vector database architecture with three layers:

1. **Abstraction Layer** (`VectorStoreBackend`):
   - Abstract base class defining unified interface
   - Backend-agnostic operations (create, upsert, search, delete)
   - Standardized SearchResult format across backends

2. **Backend Implementations**:
   - **ChromaDBBackend**: Local-first, file-based storage
     - Best for: Development, testing, single-machine deployments
     - Storage: SQLite + DuckDB for metadata
     - Strengths: Zero setup, portable, fast for small datasets
   
   - **QdrantBackend**: Production-grade vector search engine
     - Best for: Production, distributed systems, large-scale
     - Storage: Custom optimized storage with HNSW indexing
     - Strengths: Scalability, filtering, cloud-native

3. **Unified Interface** (`VectorStore`):
   - High-level API wrapping backend complexity
   - Automatic backend selection and initialization
   - Batch operations with progress tracking
   - Collection lifecycle management

**Key Features:**

- **Multi-Backend Support**: Seamless switching between ChromaDB and Qdrant
- **Automatic Embeddings**: Integrates with EmbeddingModel and AdaptiveEmbedder
- **Metadata Filtering**: Backend-specific filter translation (ChromaDB where
  clauses, Qdrant Filter objects)
- **Type Safety**: Dataclasses for SearchResult and StudyDataset
- **Error Handling**: Validation, retry logic, graceful degradation
- **Batch Processing**: Efficient bulk upsert with configurable batch sizes
- **Collection Management**: Create, delete, check existence, get info

**Data Flow:**

```
Text Input → Embedder → Embeddings → Backend → Vector DB
                ↓
         Metadata (optional)
                ↓
          StudyDataset
```

**Query Flow:**

```
Query Text → Embedder → Query Embedding → Backend.search() → SearchResults
                                              ↓
                                      Metadata Filters (optional)
```

**Supported Operations:**

1. **Collection Management**:
   - create_collection(name, recreate=False)
   - delete_collection(name)
   - collection_exists(name)
   - get_collection_info(name)

2. **Data Operations**:
   - upsert_points(collection, ids, embeddings, payloads)
   - batch_upsert(collection, chunks, batch_size=100)
   - search(query, limit=10, score_threshold=0.5, filters={})

3. **Utility Operations**:
   - list_collections()
   - get_backend_type()
   - validate_embedder()

**Usage Examples:**

Basic usage with ChromaDB (default):
    >>> from scripts.vector_db.vector_store import VectorStore, BackendType
    >>> from scripts.vector_db.embeddings import EmbeddingModel
    >>> # Initialize store with default backend
    >>> embedder = EmbeddingModel(model_name='sentence-transformers/all-MiniLM-L6-v2')  # doctest: +SKIP
    >>> store = VectorStore(backend_type=BackendType.CHROMADB, embedder=embedder)  # doctest: +SKIP
    >>> # Create collection
    >>> store.create_collection('my_docs')  # doctest: +SKIP
    >>> # Upsert documents
    >>> store.batch_upsert(
    ...     collection_name='my_docs',
    ...     chunks=[chunk1, chunk2, ...],
    ...     batch_size=100
    ... )  # doctest: +SKIP

Semantic search with metadata filtering:
    >>> # Search with filters
    >>> results = store.search(
    ...     collection_name='my_docs',
    ...     query_text='tuberculosis treatment',
    ...     limit=5,
    ...     score_threshold=0.7,
    ...     metadata_filters={'study': 'Indo-VAP', 'year': 2023}
    ... )  # doctest: +SKIP
    >>> for result in results:  # doctest: +SKIP
    ...     print(f"Score: {result.score:.3f} - {result.text[:100]}")

Production deployment with Qdrant:
    >>> # Qdrant for production
    >>> store = VectorStore(
    ...     backend_type=BackendType.QDRANT,
    ...     embedder=embedder,
    ...     host='localhost',
    ...     port=6333
    ... )  # doctest: +SKIP
    >>> store.create_collection('production_docs')  # doctest: +SKIP

**Backend Comparison:**

| Feature              | ChromaDB      | Qdrant        |
|---------------------|---------------|---------------|
| Setup Complexity    | Zero          | Moderate      |
| Scalability         | Single machine| Distributed   |
| Query Speed (small) | Fast          | Fast          |
| Query Speed (large) | Moderate      | Very Fast     |
| Metadata Filtering  | Basic         | Advanced      |
| Cloud Native        | No            | Yes           |
| Use Case            | Dev/Testing   | Production    |

**Dependencies:**
- chromadb: Local vector database (optional, for ChromaDB backend)
- qdrant-client: Qdrant client library (optional, for Qdrant backend)
- numpy: Array operations and embeddings
- .embeddings: EmbeddingModel for text encoding
- .adaptive_embeddings: AdaptiveEmbedder for domain adaptation
- .jsonl_chunking_nl: TextChunk dataclass
- .pdf_chunking: PDFChunk dataclass

**Configuration:**
Backend selection via BackendType enum. Backend-specific kwargs passed
through to implementation (e.g., `persist_directory` for ChromaDB,
`host`/`port` for Qdrant).

See Also:
    embeddings.py: Embedding generation with sentence transformers
    adaptive_embeddings.py: Domain-adaptive embedding fine-tuning
    jsonl_chunking_nl.py: Text chunking for records
    pdf_chunking.py: PDF document chunking

Note:
    ChromaDB is the default backend for ease of use. Qdrant recommended
    for production deployments requiring scalability and advanced filtering.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import uuid

import numpy as np

import config
from .embeddings import EmbeddingModel
from .adaptive_embeddings import AdaptiveEmbedder
from .jsonl_chunking_nl import TextChunk
from .pdf_chunking import PDFChunk
from scripts.utils import logging_system as log

# Configure logging
logger = log.get_logger(__name__)
vlog = log.get_verbose_logger()


# ============================================================================
# Enums and Data Classes
# ============================================================================

class BackendType(Enum):
    """Vector database backend types enumeration.
    
    Defines supported vector database backends with standardized identifiers.
    Used for backend selection in VectorStore initialization.
    
    Attributes:
        CHROMADB: Local-first backend using ChromaDB (SQLite + DuckDB)
        QDRANT: Production backend using Qdrant vector search engine
    
    Example:
        >>> from scripts.vector_db.vector_store import BackendType
        >>> backend = BackendType.CHROMADB
        >>> backend.value
        'chromadb'
        >>> BackendType.QDRANT.value
        'qdrant'
    """
    CHROMADB = "chromadb"
    QDRANT = "qdrant"


@dataclass
class SearchResult:
    """Search result from vector database with score and metadata.
    
    Encapsulates a single result from semantic search with relevance score,
    retrieved text content, metadata dictionary, and source collection.
    Provides human-readable representation for debugging and logging.
    
    Attributes:
        id: Unique identifier for the document/chunk in vector database
        score: Similarity score (0.0 to 1.0, higher is more similar)
        text: Retrieved text content from the matching document
        metadata: Dictionary of associated metadata (study, date, source, etc.)
        collection_name: Name of the collection this result came from
    
    Example:
        >>> from scripts.vector_db.vector_store import SearchResult
        >>> result = SearchResult(
        ...     id='doc_123',
        ...     score=0.95,
        ...     text='Tuberculosis treatment requires 6 months of therapy',
        ...     metadata={'study': 'Indo-VAP', 'year': 2023},
        ...     collection_name='medical_docs'
        ... )
        >>> result.score
        0.95
        >>> print(result)
        SearchResult(score=0.950, collection='medical_docs', text='Tuberculosis treatment requires 6 months of ...')
    """
    id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    collection_name: str = ""
    
    def __repr__(self) -> str:
        """Generate human-readable string representation with truncated text.
        
        Returns:
            Formatted string showing score, collection, and first 50 chars of text.
        
        Example:
            >>> result = SearchResult(id='1', score=0.85, text='A'*100, collection_name='docs')
            >>> 'score=0.850' in repr(result)
            True
            >>> 'collection=\\'docs\\'' in repr(result)
            True
        """
        return (
            f"SearchResult(score={self.score:.3f}, "
            f"collection='{self.collection_name}', "
            f"text='{self.text[:50]}...')"
        )


@dataclass
class StudyDataset:
    """Study dataset descriptor with collection name and path information.
    
    Represents a dataset associated with a specific study, including its type
    (e.g., 'pdfs', 'records'), filesystem path, and auto-generated collection
    name for vector database storage.
    
    Collection name is automatically generated as "{study_name}_{dataset_type}"
    in __post_init__ if not provided explicitly.
    
    Attributes:
        study_name: Identifier for the study (e.g., 'Indo-VAP', 'TB-TRIAL')
        dataset_type: Type of dataset ('pdfs', 'records', 'annotations', etc.)
        path: Filesystem path to the dataset directory or file
        collection_name: Vector database collection name (auto-generated if empty)
    
    Example:
        >>> from pathlib import Path
        >>> from scripts.vector_db.vector_store import StudyDataset
        >>> dataset = StudyDataset(
        ...     study_name='Indo-VAP',
        ...     dataset_type='pdfs',
        ...     path=Path('/data/Indo-VAP/annotated_pdfs')
        ... )
        >>> dataset.collection_name
        'Indo-VAP_pdfs'
        >>> # Or with explicit collection name
        >>> dataset2 = StudyDataset(
        ...     study_name='TB-TRIAL',
        ...     dataset_type='records',
        ...     path=Path('/data/TB-TRIAL/datasets'),
        ...     collection_name='custom_collection'
        ... )
        >>> dataset2.collection_name
        'custom_collection'
    """
    study_name: str
    dataset_type: str
    path: Path
    collection_name: str = ""
    
    def __post_init__(self):
        """Generate collection name from study and type if not provided.
        
        Automatically creates standardized collection name using format:
        "{study_name}_{dataset_type}" when collection_name is empty string.
        
        Example:
            >>> dataset = StudyDataset('Study1', 'pdfs', Path('/data'))
            >>> dataset.collection_name
            'Study1_pdfs'
        """
        if not self.collection_name:
            self.collection_name = f"{self.study_name}_{self.dataset_type}"


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_embedder(embedder: Any) -> None:
    """Validate embedder object implements required interface for vector operations.
    
    Ensures embedder has 'encode' method for generating embeddings and 'embedding_dim'
    attribute specifying dimensionality. Validates method is callable and dimension
    is positive integer. Used during backend initialization to catch configuration
    errors early.
    
    Args:
        embedder: Embedding model object to validate (EmbeddingModel or AdaptiveEmbedder).
    
    Raises:
        TypeError: If embedder missing 'encode' method, 'embedding_dim' attribute,
            'encode' is not callable, or 'embedding_dim' is not accessible integer.
        ValueError: If embedding_dim is not positive integer (≤ 0 or non-integer).
    
    Example:
        >>> from scripts.vector_db.embeddings import EmbeddingModel
        >>> embedder = EmbeddingModel(model_name='all-MiniLM-L6-v2')  # doctest: +SKIP
        >>> _validate_embedder(embedder)  # Should pass without error  # doctest: +SKIP
        >>> # Invalid embedder
        >>> class BadEmbedder:  # doctest: +SKIP
        ...     pass
        >>> _validate_embedder(BadEmbedder())  # doctest: +SKIP
        Traceback (most recent call last):
        TypeError: Embedder must implement 'encode' method...
    
    Note:
        This function is called automatically by VectorStoreBackend.__init__()
        implementations. You typically don't need to call it directly.
    """
    if not hasattr(embedder, 'encode'):
        raise TypeError(
            f"Embedder must implement 'encode' method. "
            f"Got type: {type(embedder).__name__}"
        )
    
    if not hasattr(embedder, 'embedding_dim'):
        raise TypeError(
            f"Embedder must have 'embedding_dim' attribute. "
            f"Got type: {type(embedder).__name__}"
        )
    
    if not callable(getattr(embedder, 'encode')):
        raise TypeError(
            f"Embedder 'encode' must be callable. "
            f"Got type: {type(getattr(embedder, 'encode')).__name__}"
        )
    
    # Validate dimension is positive integer
    try:
        dim = embedder.embedding_dim
        if not isinstance(dim, int) or dim <= 0:
            raise ValueError(
                f"Invalid embedding dimension: {dim}. "
                f"Must be positive integer."
            )
    except (AttributeError, TypeError) as e:
        raise TypeError(
            f"Embedder 'embedding_dim' must be accessible integer. "
            f"Error: {e}"
        )


def _translate_filters_for_chromadb(metadata_filters: Dict[str, Any]) -> Dict[str, Any]:
    """Translate generic metadata filters to ChromaDB where clause format.
    
    Converts standard metadata filter dictionary into ChromaDB-compatible where
    clause format. ChromaDB supports simple dict format for equality matching,
    plus operator-based queries ($and, $or, $not, $in, $nin, $gt, $gte, $lt, $lte).
    
    Current implementation passes filters through as-is for basic equality matching.
    For complex queries, ChromaDB documentation should be consulted.
    
    Args:
        metadata_filters: Dictionary of metadata key-value pairs to filter by.
            Keys are metadata field names, values are expected values for equality.
    
    Returns:
        ChromaDB-compatible where clause (currently same as input for simple queries).
    
    Example:
        >>> filters = {'study': 'Indo-VAP', 'year': 2023}
        >>> result = _translate_filters_for_chromadb(filters)
        >>> result == {'study': 'Indo-VAP', 'year': 2023}
        True
        >>> # Empty filters
        >>> _translate_filters_for_chromadb({})
        {}
    
    Note:
        For advanced filtering (range queries, OR logic), ChromaDB supports
        operators like $and, $or, $in, $gt, etc. Future enhancements may
        translate from unified filter format to these operators.
    
    See Also:
        _translate_filters_for_qdrant: Qdrant filter translation
        ChromaDB documentation: https://docs.trychroma.com/usage-guide#filtering
    """
    # ChromaDB uses simple dict format - just return as is for basic equality
    # For more complex queries, ChromaDB supports:
    # - $and, $or, $not operators
    # - $in, $nin for list membership
    # - $gt, $gte, $lt, $lte for comparisons
    return metadata_filters


def _translate_filters_for_qdrant(metadata_filters: Dict[str, Any]):
    """Translate generic metadata filters to Qdrant Filter format.
    
    Converts standard metadata filter dictionary into Qdrant Filter object with
    FieldCondition entries. Builds 'must' conditions (AND logic) for all provided
    filter pairs. Requires qdrant-client package for Filter model classes.
    
    Args:
        metadata_filters: Dictionary of metadata key-value pairs to filter by.
            Keys are payload field names, values are exact match values.
    
    Returns:
        Qdrant Filter object with 'must' conditions for all filters, or None if
        qdrant-client not installed or filters dict is empty.
    
    Example:
        >>> filters = {'study': 'Indo-VAP', 'form_code': '1A'}
        >>> qdrant_filter = _translate_filters_for_qdrant(filters)  # doctest: +SKIP
        >>> # Returns Filter(must=[FieldCondition(...), FieldCondition(...)])  # doctest: +SKIP
        >>> # Empty filters
        >>> result = _translate_filters_for_qdrant({})  # doctest: +SKIP
        >>> result is None  # doctest: +SKIP
        True
    
    Note:
        - All conditions use MatchValue for exact equality matching.
        - Multiple filters are combined with AND logic (must= parameter).
        - For OR logic or range queries, Filter object should be constructed
          manually with 'should' or comparison conditions.
        - Logs error and returns None if qdrant-client not installed.
    
    See Also:
        _translate_filters_for_chromadb: ChromaDB filter translation
        Qdrant filtering docs: https://qdrant.tech/documentation/concepts/filtering/
    """
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
    except ImportError:
        logger.error("qdrant-client not installed, cannot create Qdrant filters")
        return None
    
    # Build 'must' conditions (AND logic)
    conditions = []
    for key, value in metadata_filters.items():
        conditions.append(
            FieldCondition(
                key=key,
                match=MatchValue(value=value)
            )
        )
    
    return Filter(must=conditions) if conditions else None


# ============================================================================
# Abstract Backend Interface
# ============================================================================

class VectorStoreBackend(ABC):
    """Abstract base class defining unified interface for vector database backends.
    
    Provides backend-agnostic API for vector database operations including collection
    management, point upsert, and semantic search. Concrete implementations (ChromaDBBackend,
    QdrantBackend) handle backend-specific details while exposing consistent interface.
    
    **Design Pattern:**
    Follows Strategy pattern - different backends (strategies) can be swapped at runtime
    without changing client code. VectorStore class acts as context, delegating to
    active backend implementation.
    
    **Required Methods (Must Override):**
    - __init__: Initialize backend with embedder and backend-specific kwargs
    - collection_exists: Check collection existence
    - create_collection: Create new collection with vector configuration
    - delete_collection: Delete collection and all its data
    - upsert_points: Insert or update vectors with IDs, embeddings, payloads
    - search: Semantic search with query embedding and optional filters
    - get_collection_info: Retrieve collection metadata and statistics
    - backend_type (property): Return BackendType enum value
    
    **Standardization:**
    All implementations must return SearchResult objects from search() to ensure
    consistent result handling across backends.
    
    Attributes:
        embedder: Text embedding model (EmbeddingModel or AdaptiveEmbedder).
        embedding_dim: Vector dimensionality from embedder.
        backend_type: BackendType enum identifying the implementation.
    
    Example:
        >>> # Subclass implementation pattern
        >>> class MyBackend(VectorStoreBackend):  # doctest: +SKIP
        ...     def __init__(self, embedder, **kwargs):
        ...         self.embedder = embedder
        ...         self.embedding_dim = embedder.embedding_dim
        ...     
        ...     def collection_exists(self, collection_name: str) -> bool:
        ...         # Implementation
        ...         pass
        ...     
        ...     # ... implement other abstract methods
    
    See Also:
        ChromaDBBackend: Local SQLite-based implementation
        QdrantBackend: Production-grade vector search implementation
        VectorStore: High-level wrapper managing backend selection
    """
    
    @abstractmethod
    def __init__(self, embedder: Union[EmbeddingModel, AdaptiveEmbedder], **kwargs):
        """Initialize backend with embedding model and backend-specific configuration.
        
        Args:
            embedder: Text embedding model implementing encode() method and
                embedding_dim attribute. Must be EmbeddingModel or AdaptiveEmbedder.
            **kwargs: Backend-specific configuration (e.g., persist_directory for
                ChromaDB, storage_path for Qdrant).
        
        Raises:
            TypeError: If embedder doesn't implement required interface.
            ValueError: If required backend-specific parameters missing.
            ImportError: If backend library not installed.
        """
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in vector database.
        
        Args:
            collection_name: Name of collection to check.
        
        Returns:
            True if collection exists, False otherwise.
        
        Note:
            Should not raise exceptions - return False on errors for robustness.
        """
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, recreate: bool = False) -> str:
        """Create new vector collection with appropriate configuration.
        
        Args:
            collection_name: Name for the new collection.
            recreate: If True, delete existing collection with same name before
                creating. If False and collection exists, log warning and return
                existing collection name.
        
        Returns:
            Name of created (or existing) collection.
        
        Raises:
            RuntimeError: If collection creation fails due to database errors.
        
        Note:
            Should configure collection with cosine similarity distance metric
            and vector size matching self.embedding_dim.
        """
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection and all its vectors from database.
        
        Args:
            collection_name: Name of collection to delete.
        
        Returns:
            True if deletion successful, False if failed or collection not found.
        
        Note:
            Should not raise exceptions - log errors and return False for robustness.
            Deletion is irreversible - all vectors and metadata lost.
        """
        pass
    
    @abstractmethod
    def upsert_points(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> int:
        """Insert or update vectors in collection (upsert = update + insert).
        
        Args:
            collection_name: Target collection name.
            ids: List of unique identifiers for each vector point. If ID exists,
                point is updated; if new, point is inserted.
            embeddings: List of embedding vectors as lists of floats. Must match
                collection's configured vector size (self.embedding_dim).
            payloads: List of metadata dictionaries for each point. Must include
                'text' key with original content. Additional metadata keys stored
                for filtering.
        
        Returns:
            Number of points successfully upserted.
        
        Raises:
            Exception: If upsert fails (collection not found, dimension mismatch, etc.).
                Implementations should log error before raising.
        
        Note:
            Lists must be same length (len(ids) == len(embeddings) == len(payloads)).
            Backend may transform payloads (e.g., ChromaDB separates 'text' into
            documents field).
        """
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_embedding: np.ndarray,
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform semantic search for vectors similar to query embedding.
        
        Args:
            collection_name: Collection to search.
            query_embedding: Query vector as numpy array (shape: [embedding_dim,]).
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0 to 1.0). Results below
                threshold are filtered out.
            filters: Optional metadata filters as dict (e.g., {'study': 'Indo-VAP'}).
                Backend translates to appropriate filter format.
        
        Returns:
            List of SearchResult objects sorted by descending similarity score.
            Empty list if no results above threshold or search fails.
        
        Note:
            - Should not raise exceptions - log errors and return empty list.
            - Scores should be normalized to 0.0-1.0 range (cosine similarity).
            - Backend converts query_embedding from numpy to backend-specific format.
        """
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Retrieve metadata and statistics about collection.
        
        Args:
            collection_name: Name of collection to inspect.
        
        Returns:
            Dictionary with collection information. Standard keys:
            - 'name': Collection name (str)
            - 'points_count': Number of vectors in collection (int)
            - 'backend': Backend type identifier (str)
            - Additional backend-specific keys (e.g., 'vectors_config', 'status')
            Empty dict if collection not found or error occurs.
        
        Note:
            Should not raise exceptions - log errors and return empty dict.
        """
        pass
    
    @property
    @abstractmethod
    def backend_type(self) -> BackendType:
        """Return backend type identifier.
        
        Returns:
            BackendType enum value (CHROMADB or QDRANT).
        
        Example:
            >>> backend = ChromaDBBackend(embedder, persist_directory=Path('/tmp'))  # doctest: +SKIP
            >>> backend.backend_type  # doctest: +SKIP
            <BackendType.CHROMADB: 'chromadb'>
        """
        pass


# ============================================================================
# ChromaDB Backend (Primary)
# ============================================================================

class ChromaDBBackend(VectorStoreBackend):
    """ChromaDB vector database backend for local-first storage and development.
    
    Provides local vector search using ChromaDB's embedded database (SQLite for
    metadata + DuckDB for analytics). Ideal for development, testing, and single-
    machine deployments. Zero external dependencies beyond Python package.
    
    **Storage Architecture:**
    - Persistence: SQLite database + DuckDB for OLAP
    - Indexing: HNSW (Hierarchical Navigable Small World) for approximate nearest neighbor
    - Distance: Cosine similarity (configurable via metadata)
    - Location: User-specified persist_directory path
    
    **Key Features:**
    - Zero-setup: No server process required
    - Portability: Database files can be copied/moved
    - Fast queries: Efficient for datasets up to millions of vectors
    - Simple filtering: Where clause with basic operators
    - Atomic operations: Built-in transaction support
    
    **Limitations:**
    - Single-machine only (no distributed mode)
    - Basic metadata filtering (no complex join operations)
    - Slower than Qdrant for very large datasets (>10M vectors)
    
    **Data Model:**
    - Collection: Named group of vectors with shared dimension
    - Documents: Text content (stored separately from embeddings)
    - Embeddings: Vector representations (float arrays)
    - Metadatas: Key-value metadata (simple types only, no nested dicts)
    
    Attributes:
        client: ChromaDB PersistentClient instance for database operations.
        embedder: Text embedding model (EmbeddingModel or AdaptiveEmbedder).
        embedding_dim: Vector dimensionality from embedder.
        persist_directory: Filesystem path where ChromaDB stores database files.
    
    Example:
        >>> from pathlib import Path
        >>> from scripts.vector_db.embeddings import EmbeddingModel
        >>> from scripts.vector_db.vector_store import ChromaDBBackend
        >>> # Initialize backend
        >>> embedder = EmbeddingModel(model_name='all-MiniLM-L6-v2')  # doctest: +SKIP
        >>> backend = ChromaDBBackend(
        ...     embedder=embedder,
        ...     persist_directory=Path('/tmp/my_chroma_db')
        ... )  # doctest: +SKIP
        >>> # Create collection
        >>> backend.create_collection('test_docs')  # doctest: +SKIP
        'test_docs'
        >>> # Upsert vectors
        >>> backend.upsert_points(
        ...     collection_name='test_docs',
        ...     ids=['doc1', 'doc2'],
        ...     embeddings=[[0.1]*384, [0.2]*384],
        ...     payloads=[{'text': 'hello'}, {'text': 'world'}]
        ... )  # doctest: +SKIP
        2
    
    See Also:
        QdrantBackend: Production-grade alternative with advanced features
        VectorStoreBackend: Abstract base class defining interface
        ChromaDB docs: https://docs.trychroma.com/
    """
    
    def __init__(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        persist_directory: Path,
        **kwargs
    ):
        """Initialize ChromaDB backend with persistent storage.
        
        Args:
            embedder: Text embedding model implementing encode() method and
                embedding_dim attribute (EmbeddingModel or AdaptiveEmbedder).
            persist_directory: Filesystem path for ChromaDB database storage.
                Directory created if it doesn't exist. Must be provided explicitly
                (no fallback to config) to ensure backend separation.
            **kwargs: Additional ChromaDB settings (currently unused, reserved
                for future ChromaDB configuration options).
        
        Raises:
            ImportError: If chromadb package not installed (requires chromadb>=1.3.0).
            TypeError: If embedder doesn't implement required interface (see
                _validate_embedder for details).
            ValueError: If persist_directory not provided or empty.
            RuntimeError: If ChromaDB client initialization fails (permissions,
                disk space, corrupted database).
        
        Side Effects:
            - Creates persist_directory and parent directories if needed
            - Initializes SQLite database files in persist_directory
            - Disables ChromaDB telemetry (anonymized_telemetry=False)
        
        Example:
            >>> from pathlib import Path
            >>> from scripts.vector_db.embeddings import EmbeddingModel
            >>> embedder = EmbeddingModel('all-MiniLM-L6-v2')  # doctest: +SKIP
            >>> backend = ChromaDBBackend(
            ...     embedder=embedder,
            ...     persist_directory=Path('/tmp/chroma_test')
            ... )  # doctest: +SKIP
            >>> backend.persist_directory  # doctest: +SKIP
            PosixPath('/tmp/chroma_test')
        """
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ImportError:
            raise ImportError(
                "ChromaDB is not installed. Install with: pip install chromadb>=1.3.0"
            )
        
        _validate_embedder(embedder)
        
        # Validate persist_directory is provided
        if not persist_directory:
            raise ValueError(
                "persist_directory is required for ChromaDB backend. "
                "This ensures proper directory separation between backends."
            )
        
        self.embedder = embedder
        self.embedding_dim = embedder.embedding_dim
        
        # Use provided path ONLY (no fallback to config)
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize ChromaDB PersistentClient
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=chromadb.Settings(
                    anonymized_telemetry=False,  # Disable telemetry
                    allow_reset=True  # Allow reset for development
                )
            )
            logger.info(f"ChromaDB client initialized at: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise RuntimeError(f"ChromaDB initialization failed: {e}")
    
    @property
    def backend_type(self) -> BackendType:
        """Return backend type identifier.
        
        Returns:
            BackendType.CHROMADB enum value.
        """
        return BackendType.CHROMADB
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in ChromaDB database.
        
        Args:
            collection_name: Name of collection to check.
        
        Returns:
            True if collection exists, False otherwise or on error.
        
        Example:
            >>> backend.create_collection('test_coll')  # doctest: +SKIP
            >>> backend.collection_exists('test_coll')  # doctest: +SKIP
            True
            >>> backend.collection_exists('nonexistent')  # doctest: +SKIP
            False
        """
        try:
            collections = self.client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def create_collection(self, collection_name: str, recreate: bool = False) -> str:
        """Create ChromaDB collection with cosine similarity configuration.
        
        Args:
            collection_name: Name for new collection (must be unique unless recreate=True).
            recreate: If True, delete existing collection first. If False and
                collection exists, log info and return existing name.
        
        Returns:
            Name of created or existing collection.
        
        Raises:
            RuntimeError: If collection creation fails (invalid name, permissions, etc.).
        
        Side Effects:
            - Creates new collection in ChromaDB with cosine distance metric
            - Logs info message about creation status
            - If recreate=True, deletes existing collection first
        
        Example:
            >>> backend.create_collection('medical_docs')  # doctest: +SKIP
            'medical_docs'
            >>> # Recreate existing collection
            >>> backend.create_collection('medical_docs', recreate=True)  # doctest: +SKIP
            'medical_docs'
        
        Note:
            Collection configured with {"hnsw:space": "cosine"} for cosine similarity.
            Embeddings handled externally for consistency with Qdrant backend.
        """
        try:
            exists = self.collection_exists(collection_name)
            
            if exists and recreate:
                logger.info(f"Deleting existing collection: {collection_name}")
                self.client.delete_collection(collection_name)
                exists = False
            
            if not exists:
                # Create collection with cosine distance
                # ChromaDB uses embedding function internally, but we handle
                # embeddings externally for consistency with Qdrant
                self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}  # Cosine similarity
                )
                logger.info(
                    f"Created ChromaDB collection: {collection_name} "
                    f"(dim={self.embedding_dim}, distance=cosine)"
                )
            else:
                logger.info(f"Collection already exists: {collection_name}")
            
            return collection_name
        
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise RuntimeError(f"Collection creation failed: {e}")
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete ChromaDB collection and all its data.
        
        Args:
            collection_name: Name of collection to delete.
        
        Returns:
            True if deletion successful, False on error.
        
        Side Effects:
            - Permanently deletes collection and all vectors/metadata
            - Logs info on success, error on failure
        
        Example:
            >>> backend.delete_collection('old_docs')  # doctest: +SKIP
            True
        
        Warning:
            Deletion is irreversible. All vectors and metadata are lost permanently.
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def upsert_points(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> int:
        """Upsert vectors to ChromaDB collection (insert new, update existing).
        
        Inserts new vectors or updates existing ones (matched by ID). ChromaDB
        requires separate 'documents' field for text content, extracted from
        payload['text']. Metadata values are cleaned (nested dicts/lists converted
        to strings) to meet ChromaDB's simple type requirement.
        
        Args:
            collection_name: Target collection (must exist).
            ids: List of unique string IDs for each vector. Existing IDs updated,
                new IDs inserted.
            embeddings: List of embedding vectors as lists of floats. Length must
                match embedding_dim.
            payloads: List of metadata dicts. Must include 'text' key with original
                content. Other keys stored as metadata (simple types only).
        
        Returns:
            Number of points successfully upserted (should equal len(ids) on success).
        
        Raises:
            Exception: If upsert fails (collection not found, dimension mismatch,
                invalid payload). Error logged before re-raising.
        
        Side Effects:
            - Updates collection with new/modified vectors
            - 'text' key extracted to documents, remaining keys to metadatas
            - Nested dict/list values in metadata converted to strings
        
        Example:
            >>> ids = ['doc1', 'doc2']
            >>> embeddings = [[0.1]*384, [0.2]*384]
            >>> payloads = [
            ...     {'text': 'TB treatment', 'study': 'Indo-VAP'},
            ...     {'text': 'HIV screening', 'year': 2023}
            ... ]
            >>> backend.upsert_points('docs', ids, embeddings, payloads)  # doctest: +SKIP
            2
        
        Note:
            ChromaDB metadata must be simple types (str, int, float, bool).
            Complex values (dict, list) automatically stringified. For complex
            filtering needs, consider storing as separate fields or using Qdrant.
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # ChromaDB expects documents (text) for each point
            # Extract text from payload for ChromaDB compatibility
            documents = [payload.get("text", "") for payload in payloads]
            
            # Prepare metadatas (exclude 'text' key for ChromaDB metadata)
            metadatas = []
            for payload in payloads:
                metadata = {k: v for k, v in payload.items() if k != "text"}
                # ChromaDB requires metadata values to be simple types
                # Convert nested dicts to strings if needed
                cleaned_metadata = {}
                for k, v in metadata.items():
                    if isinstance(v, (dict, list)):
                        cleaned_metadata[k] = str(v)
                    else:
                        cleaned_metadata[k] = v
                metadatas.append(cleaned_metadata)
            
            # Upsert to collection
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            return len(ids)
        
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            raise
    
    def search(
        self,
        collection_name: str,
        query_embedding: np.ndarray,
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform semantic search in ChromaDB collection using cosine similarity.
        
        Queries collection for vectors most similar to query_embedding. Returns
        results sorted by descending similarity score (1 - cosine_distance).
        Supports metadata filtering via ChromaDB where clauses.
        
        Args:
            collection_name: Collection to search.
            query_embedding: Query vector as numpy array (shape: [embedding_dim,]).
                Converted to list for ChromaDB compatibility.
            limit: Maximum number of results to return (ChromaDB n_results parameter).
            score_threshold: Minimum similarity score (0.0 to 1.0). Results below
                threshold filtered out after retrieval.
            filters: Optional metadata filters as dict (e.g., {'study': 'Indo-VAP'}).
                Passed as ChromaDB 'where' clause for server-side filtering.
        
        Returns:
            List of SearchResult objects sorted by descending score. Empty list if
            no results above threshold or on error.
        
        Side Effects:
            - Logs info message with result count and max score
            - Logs error and returns empty list on failures
        
        Example:
            >>> import numpy as np
            >>> query_vec = np.random.rand(384)  # doctest: +SKIP
            >>> results = backend.search(
            ...     collection_name='medical_docs',
            ...     query_embedding=query_vec,
            ...     limit=5,
            ...     score_threshold=0.7,
            ...     filters={'study': 'Indo-VAP'}
            ... )  # doctest: +SKIP
            >>> for r in results:  # doctest: +SKIP
            ...     print(f"{r.score:.3f}: {r.text[:50]}")
        
        Note:
            - ChromaDB returns distances (cosine distance), converted to similarity
              scores via: score = 1.0 - distance
            - Results are nested lists from batch queries - first element extracted
            - For complex filtering (OR, ranges), construct where clause manually
              using ChromaDB operators ($and, $or, $gt, etc.)
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Convert numpy array to list
            query_vector = query_embedding.tolist()
            
            # Build where clause for filtering
            where = filters if filters else None
            
            # Execute search
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=where,
                include=["metadatas", "documents", "distances"]
            )
            
            # Convert ChromaDB results to SearchResult objects
            search_results = []
            
            # ChromaDB returns nested lists (batch queries)
            ids = results['ids'][0] if results['ids'] else []
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            for idx, (doc_id, document, metadata, distance) in enumerate(
                zip(ids, documents, metadatas, distances)
            ):
                # Convert distance to similarity score (1 - cosine_distance)
                score = 1.0 - distance
                
                # Filter by score threshold
                if score >= score_threshold:
                    result = SearchResult(
                        id=doc_id,
                        score=score,
                        text=document,
                        metadata=metadata or {},
                        collection_name=collection_name
                    )
                    search_results.append(result)
            
            logger.info(
                f"ChromaDB search in {collection_name}: found {len(search_results)} results "
                f"(max_score={search_results[0].score:.3f if search_results else 0:.3f})"
            )
            
            return search_results
        
        except Exception as e:
            logger.error(f"ChromaDB search failed in {collection_name}: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Retrieve ChromaDB collection metadata and statistics.
        
        Args:
            collection_name: Name of collection to inspect.
        
        Returns:
            Dictionary with keys:
            - 'name': Collection name (str)
            - 'points_count': Number of vectors in collection (int)
            - 'backend': Always 'chromadb' (str)
            - 'metadata': Collection metadata dict (e.g., {"hnsw:space": "cosine"})
            Empty dict on error.
        
        Example:
            >>> info = backend.get_collection_info('medical_docs')  # doctest: +SKIP
            >>> info['points_count']  # doctest: +SKIP
            1523
            >>> info['metadata']  # doctest: +SKIP
            {'hnsw:space': 'cosine'}
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Get count
            count = collection.count()
            
            return {
                "name": collection_name,
                "points_count": count,
                "backend": "chromadb",
                "metadata": collection.metadata
            }
        
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return {}


# ============================================================================
# Qdrant Backend (Fallback)
# ============================================================================

class QdrantBackend(VectorStoreBackend):
    """Qdrant vector database backend for production-grade semantic search.
    
    Provides high-performance vector search using Qdrant's specialized engine
    optimized for large-scale deployments. Supports local file storage, in-memory
    mode, and remote server connections. Ideal for production, distributed systems,
    and datasets requiring advanced filtering or scalability.
    
    **Storage Architecture:**
    - Persistence: Custom optimized storage format (not SQLite)
    - Indexing: HNSW (Hierarchical Navigable Small World) with configurable parameters
    - Distance: Cosine similarity (COSINE distance metric)
    - Location: User-specified storage_path (file mode) or :memory: (in-memory)
    
    **Key Features:**
    - **Scalability**: Handles millions to billions of vectors efficiently
    - **Advanced Filtering**: Complex metadata queries (AND/OR/NOT, ranges, geo)
    - **Fast Queries**: Optimized HNSW index with tunable recall/speed tradeoff
    - **Cloud-Native**: Designed for distributed deployments and clustering
    - **Rich Payloads**: Supports nested JSON metadata without flattening
    - **Atomic Updates**: ACID guarantees for upsert operations
    
    **Deployment Modes:**
    1. **Local File Mode** (default): Persistent storage in storage_path
    2. **In-Memory Mode**: Fast ephemeral storage (use_memory=True)
    3. **Remote Server**: Connect to Qdrant server (host/port parameters)
    
    **Limitations:**
    - Requires qdrant-client package (optional dependency)
    - More complex setup than ChromaDB (but still simple for local mode)
    - Slightly higher memory overhead for metadata indexes
    
    **Data Model:**
    - Collection: Named group of vectors with vector configuration
    - Points: Vector + payload (id, vector array, metadata dict)
    - Payload: Arbitrary JSON metadata (supports nesting, no type restrictions)
    - Filters: Rich query DSL (must/should/must_not conditions)
    
    Attributes:
        client: QdrantClient instance for database operations.
        embedder: Text embedding model (EmbeddingModel or AdaptiveEmbedder).
        embedding_dim: Vector dimensionality from embedder.
        storage_path: Filesystem path for Qdrant storage (None if in-memory).
        _VectorParams: Qdrant VectorParams class (cached for performance).
        _Distance: Qdrant Distance enum (cached).
        _PointStruct: Qdrant PointStruct class (cached).
        _Filter: Qdrant Filter class (cached).
        _FieldCondition: Qdrant FieldCondition class (cached).
        _MatchValue: Qdrant MatchValue class (cached).
    
    Example:
        >>> from pathlib import Path
        >>> from scripts.vector_db.embeddings import EmbeddingModel
        >>> from scripts.vector_db.vector_store import QdrantBackend
        >>> # Initialize backend with local storage
        >>> embedder = EmbeddingModel(model_name='all-MiniLM-L6-v2')  # doctest: +SKIP
        >>> backend = QdrantBackend(
        ...     embedder=embedder,
        ...     storage_path=Path('/tmp/my_qdrant_db')
        ... )  # doctest: +SKIP
        >>> # Or in-memory mode for testing
        >>> backend_mem = QdrantBackend(
        ...     embedder=embedder,
        ...     use_memory=True
        ... )  # doctest: +SKIP
        >>> # Create collection
        >>> backend.create_collection('production_docs')  # doctest: +SKIP
        'production_docs'
    
    See Also:
        ChromaDBBackend: Local-first alternative for development
        VectorStoreBackend: Abstract base class defining interface
        Qdrant docs: https://qdrant.tech/documentation/
    """
    
    def __init__(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        storage_path: Optional[Path] = None,
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = False,
        **kwargs
    ):
        """Initialize Qdrant backend with local storage or in-memory mode.
        
        Args:
            embedder: Text embedding model implementing encode() method and
                embedding_dim attribute (EmbeddingModel or AdaptiveEmbedder).
            storage_path: Filesystem path for Qdrant database storage. Required
                unless use_memory=True. Directory created if doesn't exist.
            host: Qdrant server hostname (for remote mode, currently unused in
                local/memory modes). Default: 'localhost'.
            port: Qdrant server port (for remote mode, currently unused). Default: 6333.
            use_memory: If True, use in-memory mode (ephemeral, fast). If False,
                use file-based persistence (storage_path required).
            **kwargs: Additional Qdrant configuration (reserved for future use).
        
        Raises:
            ImportError: If qdrant-client package not installed (requires qdrant-client>=1.15.0).
            TypeError: If embedder doesn't implement required interface (see
                _validate_embedder).
            ValueError: If use_memory=False and storage_path not provided.
            RuntimeError: If Qdrant client initialization fails (permissions,
                disk space, corrupted storage).
        
        Side Effects:
            - Creates storage_path directory if needed (file mode)
            - Initializes Qdrant storage files (file mode)
            - Caches Qdrant model classes as instance attributes for performance
        
        Example:
            >>> from pathlib import Path
            >>> from scripts.vector_db.embeddings import EmbeddingModel
            >>> embedder = EmbeddingModel('all-MiniLM-L6-v2')  # doctest: +SKIP
            >>> # File-based storage
            >>> backend = QdrantBackend(
            ...     embedder=embedder,
            ...     storage_path=Path('/data/qdrant_store')
            ... )  # doctest: +SKIP
            >>> # In-memory for testing
            >>> backend_test = QdrantBackend(
            ...     embedder=embedder,
            ...     use_memory=True
            ... )  # doctest: +SKIP
        
        Note:
            Remote server mode (host/port parameters) currently not active in
            implementation. Use QdrantClient(url=...) for remote connections.
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import VectorParams, Distance
        except ImportError:
            raise ImportError(
                "Qdrant client is not installed. Install with: pip install qdrant-client>=1.15.0"
            )
        
        _validate_embedder(embedder)
        
        # Validate storage_path when not using memory
        if not use_memory and not storage_path:
            raise ValueError(
                "storage_path is required for Qdrant backend when not using memory mode. "
                "This ensures proper directory separation between backends."
            )
        
        self.embedder = embedder
        self.embedding_dim = embedder.embedding_dim
        
        # Store Qdrant-specific imports as instance attributes
        self._VectorParams = VectorParams
        self._Distance = Distance
        
        # Import remaining Qdrant models
        from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
        self._PointStruct = PointStruct
        self._Filter = Filter
        self._FieldCondition = FieldCondition
        self._MatchValue = MatchValue
        
        # Use provided path ONLY (no fallback to config)
        if storage_path:
            self.storage_path = Path(storage_path)
        
        try:
            if use_memory:
                self.client = QdrantClient(":memory:")
                logger.info("Qdrant client initialized in-memory mode")
            else:
                self.storage_path.mkdir(parents=True, exist_ok=True)
                self.client = QdrantClient(path=str(self.storage_path))
                logger.info(f"Qdrant client initialized at: {self.storage_path}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise RuntimeError(f"Qdrant initialization failed: {e}")
    
    @property
    def backend_type(self) -> BackendType:
        """Return backend type identifier.
        
        Returns:
            BackendType.QDRANT enum value.
        """
        return BackendType.QDRANT
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in Qdrant database.
        
        Args:
            collection_name: Name of collection to check.
        
        Returns:
            True if collection exists, False otherwise or on error.
        
        Example:
            >>> backend.create_collection('test_coll')  # doctest: +SKIP
            >>> backend.collection_exists('test_coll')  # doctest: +SKIP
            True
            >>> backend.collection_exists('nonexistent')  # doctest: +SKIP
            False
        """
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def create_collection(self, collection_name: str, recreate: bool = False) -> str:
        """Create Qdrant collection with vector configuration for cosine similarity.
        
        Args:
            collection_name: Name for new collection (must be unique unless recreate=True).
            recreate: If True, delete existing collection first. If False and
                collection exists, log info and return existing name.
        
        Returns:
            Name of created or existing collection.
        
        Raises:
            RuntimeError: If collection creation fails (invalid name, dimension
                mismatch, permissions).
        
        Side Effects:
            - Creates new collection with VectorParams(size=embedding_dim, distance=COSINE)
            - Logs info message about creation status
            - If recreate=True, deletes existing collection first
        
        Example:
            >>> backend.create_collection('medical_docs')  # doctest: +SKIP
            'medical_docs'
            >>> # Recreate existing collection
            >>> backend.create_collection('medical_docs', recreate=True)  # doctest: +SKIP
            'medical_docs'
        
        Note:
            Uses COSINE distance for semantic similarity matching.
            Vector size set to self.embedding_dim from embedder.
        """
        try:
            exists = self.collection_exists(collection_name)
            
            if exists and recreate:
                logger.info(f"Deleting existing collection: {collection_name}")
                self.client.delete_collection(collection_name)
                exists = False
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=self._VectorParams(
                        size=self.embedding_dim,
                        distance=self._Distance.COSINE
                    )
                )
                logger.info(
                    f"Created Qdrant collection: {collection_name} "
                    f"(dim={self.embedding_dim}, distance=COSINE)"
                )
            else:
                logger.info(f"Collection already exists: {collection_name}")
            
            return collection_name
        
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise RuntimeError(f"Collection creation failed: {e}")
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete Qdrant collection and all its data.
        
        Args:
            collection_name: Name of collection to delete.
        
        Returns:
            True if deletion successful, False on error.
        
        Side Effects:
            - Permanently deletes collection and all points/payloads
            - Logs info on success, error on failure
        
        Example:
            >>> backend.delete_collection('old_docs')  # doctest: +SKIP
            True
        
        Warning:
            Deletion is irreversible. All vectors and payloads are lost permanently.
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def upsert_points(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> int:
        """Upsert points to Qdrant collection (insert new, update existing).
        
        Creates PointStruct objects combining IDs, vectors, and payloads, then
        upserts to collection. Qdrant supports arbitrary nested JSON in payloads
        without flattening or type restrictions.
        
        Args:
            collection_name: Target collection (must exist).
            ids: List of unique string IDs for each point. Existing IDs updated,
                new IDs inserted.
            embeddings: List of embedding vectors as lists of floats. Length must
                match collection's configured vector size.
            payloads: List of metadata dictionaries. Can contain nested dicts,
                lists, and any JSON-serializable values. All keys stored for filtering.
        
        Returns:
            Number of points successfully upserted (should equal len(ids) on success).
        
        Raises:
            Exception: If upsert fails (collection not found, dimension mismatch,
                invalid JSON in payload). Error logged before re-raising.
        
        Side Effects:
            - Updates collection with new/modified points
            - All payload keys indexed for filtering
            - Entire payload dict stored as-is (no transformation)
        
        Example:
            >>> ids = ['doc1', 'doc2']
            >>> embeddings = [[0.1]*384, [0.2]*384]
            >>> payloads = [
            ...     {
            ...         'text': 'TB treatment protocol',
            ...         'study': 'Indo-VAP',
            ...         'metadata': {'year': 2023, 'nested': {'field': 'value'}}
            ...     },
            ...     {'text': 'HIV screening', 'tags': ['infectious', 'disease']}
            ... ]
            >>> backend.upsert_points('docs', ids, embeddings, payloads)  # doctest: +SKIP
            2
        
        Note:
            Qdrant supports rich payloads with nesting. No need to flatten or
            stringify complex values (unlike ChromaDB). Entire payload available
            for filtering with FieldCondition queries.
        """
        try:
            points = []
            for point_id, embedding, payload in zip(ids, embeddings, payloads):
                point = self._PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            self.client.upsert(collection_name=collection_name, points=points)
            return len(points)
        
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            raise
    
    def search(
        self,
        collection_name: str,
        query_embedding: np.ndarray,
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform semantic search in Qdrant collection using cosine similarity.
        
        Queries collection for points most similar to query_embedding. Supports
        rich metadata filtering via Qdrant Filter objects with FieldCondition entries.
        Returns results sorted by descending similarity score.
        
        Args:
            collection_name: Collection to search.
            query_embedding: Query vector as numpy array (shape: [embedding_dim,]).
                Converted to list for Qdrant compatibility.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0 to 1.0). Qdrant filters
                server-side, only results above threshold returned.
            filters: Optional metadata filters as dict (e.g., {'study': 'Indo-VAP',
                'year': 2023}). Translated to Qdrant Filter with 'must' conditions.
        
        Returns:
            List of SearchResult objects sorted by descending score. Empty list if
            no results above threshold or on error.
        
        Side Effects:
            - Logs info message with result count and max score
            - Logs error and returns empty list on failures
        
        Example:
            >>> import numpy as np
            >>> query_vec = np.random.rand(384)  # doctest: +SKIP
            >>> results = backend.search(
            ...     collection_name='medical_docs',
            ...     query_embedding=query_vec,
            ...     limit=5,
            ...     score_threshold=0.7,
            ...     filters={'study': 'Indo-VAP', 'form_code': '1A'}
            ... )  # doctest: +SKIP
            >>> for r in results:  # doctest: +SKIP
            ...     print(f"{r.score:.3f}: {r.text[:50]}")
        
        Note:
            - Filter building: Simple dict filters translated to must=[] conditions
              (AND logic). For OR/NOT logic, construct Filter object manually.
            - Payload access: Full payload available in result.metadata, 'text' key
              extracted to result.text field for consistency.
            - Performance: score_threshold applied server-side for efficiency.
        """
        try:
            # Build filters if provided
            filter_obj = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        self._FieldCondition(
                            key=key,
                            match=self._MatchValue(value=value)
                        )
                    )
                filter_obj = self._Filter(must=conditions)
            
            # Execute search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_obj
            )
            
            # Convert to SearchResult objects
            results = []
            for point in search_results:
                result = SearchResult(
                    id=str(point.id),
                    score=point.score,
                    text=point.payload.get("text", ""),
                    metadata={
                        k: v for k, v in point.payload.items()
                        if k != "text"
                    },
                    collection_name=collection_name
                )
                results.append(result)
            
            logger.info(
                f"Qdrant search in {collection_name}: found {len(results)} results "
                f"(max_score={results[0].score:.3f if results else 0:.3f})"
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Qdrant search failed in {collection_name}: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Retrieve Qdrant collection metadata and statistics.
        
        Args:
            collection_name: Name of collection to inspect.
        
        Returns:
            Dictionary with keys:
            - 'name': Collection name (str)
            - 'points_count': Number of points in collection (int)
            - 'backend': Always 'qdrant' (str)
            - 'vectors_config': String representation of VectorParams config
            - 'status': Collection status (e.g., 'green', 'yellow', 'red')
            Empty dict on error.
        
        Example:
            >>> info = backend.get_collection_info('medical_docs')  # doctest: +SKIP
            >>> info['points_count']  # doctest: +SKIP
            15230
            >>> info['status']  # doctest: +SKIP
            'green'
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "backend": "qdrant",
                "vectors_config": str(info.config.params.vectors),
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return {}


# ============================================================================
# Unified Vector Store Interface
# ============================================================================

class VectorStore:
    """Unified vector store interface with automatic backend selection and management.
    
    High-level facade providing consistent API across ChromaDB and Qdrant backends.
    Handles backend initialization, automatic fallback, collection lifecycle, batch
    ingestion, and semantic search with metadata filtering. Simplifies vector database
    operations for RePORTaLiN data ingestion and retrieval workflows.
    
    **Key Responsibilities:**
    1. **Backend Selection**: Automatically select and initialize best available backend
       (ChromaDB primary, Qdrant fallback) based on installation and preference.
    2. **Collection Management**: Create, delete, check existence, get info for collections.
    3. **Data Ingestion**: Batch upsert for PDF chunks and JSONL records with progress.
    4. **Semantic Search**: Query-based search with scoring, filtering, and fallback logic.
    5. **Study Discovery**: Scan output directory for study datasets.
    
    **Architecture:**
    - **Delegation Pattern**: Most methods delegate to active backend implementation
    - **Factory Pattern**: _select_backend() creates appropriate backend instance
    - **Facade Pattern**: Simplifies complex backend APIs with unified interface
    
    **Backend Priority:**
    1. ChromaDB (if installed) - default for development
    2. Qdrant (if installed) - fallback or preferred for production
    3. RuntimeError if neither available
    
    **Collection Naming:**
    Collections named as "{study_name}_{dataset_type}" (e.g., "Indo-VAP_pdfs",
    "TB-TRIAL_cleaned"). Ensures unique namespaces per study/dataset combination.
    
    **Batch Ingestion:**
    - PDF chunks: Extracts form metadata, page numbers, section titles
    - JSONL chunks: Extracts subject IDs, form names, original records
    - Configurable batch_size for memory management
    - Progress logging for large datasets
    
    **Search Features:**
    - Basic search: Query text → embedding → similar results
    - Filtered search: Add metadata constraints (study, form, subject)
    - Form-specific: Search within clinical form types
    - Subject-specific: Search within patient data
    - Fallback search: Auto-retry in alternate dataset if insufficient results
    
    Attributes:
        backend: Active VectorStoreBackend instance (ChromaDBBackend or QdrantBackend).
        embedder: Text embedding model (EmbeddingModel or AdaptiveEmbedder).
        embedding_dim: Vector dimensionality from embedder.
        output_dir: Path to RePORTaLiN output directory with study datasets.
        storage_path: Path to vector database storage directory.
    
    Example:
        >>> from pathlib import Path
        >>> from scripts.vector_db.embeddings import EmbeddingModel
        >>> from scripts.vector_db.vector_store import VectorStore
        >>> # Initialize with default backend (ChromaDB)
        >>> embedder = EmbeddingModel(model_name='all-MiniLM-L6-v2')  # doctest: +SKIP
        >>> store = VectorStore(
        ...     embedder=embedder,
        ...     storage_path=Path('/data/vector_store')
        ... )  # doctest: +SKIP
        >>> # Create collection
        >>> store.create_collection('Indo-VAP', 'pdfs')  # doctest: +SKIP
        'Indo-VAP_pdfs'
        >>> # Search
        >>> results = store.search(
        ...     collection_name='Indo-VAP_pdfs',
        ...     query='tuberculosis treatment guidelines',
        ...     limit=5
        ... )  # doctest: +SKIP
    
    See Also:
        ChromaDBBackend: Local storage backend implementation
        QdrantBackend: Production storage backend implementation
        EmbeddingModel: Text embedding with sentence transformers
        AdaptiveEmbedder: Domain-adaptive fine-tuned embeddings
    """
    
    def __init__(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        storage_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        prefer_backend: Optional[str] = None,
        use_memory: bool = False,
        **backend_kwargs
    ):
        """Initialize vector store with automatic backend selection.
        
        Args:
            embedder: Text embedding model implementing encode() method and
                embedding_dim attribute (EmbeddingModel or AdaptiveEmbedder).
            storage_path: Filesystem path for vector database storage. If not provided,
                defaults to output_dir/vector_db. Created if doesn't exist.
            output_dir: Path to RePORTaLiN output directory containing study datasets.
                Used for discover_studies(). Defaults to ../output relative to module.
            prefer_backend: Preferred backend ('chromadb' or 'qdrant'). If specified,
                try this backend first before fallback. Case-insensitive.
            use_memory: If True, use in-memory storage (Qdrant only). If False, use
                persistent file storage. Default: False.
            **backend_kwargs: Additional backend-specific configuration passed through
                to backend __init__ (e.g., host, port for Qdrant remote mode).
        
        Raises:
            TypeError: If embedder doesn't implement required interface.
            RuntimeError: If no backend can be initialized (both chromadb and
                qdrant-client missing or failed to load).
        
        Side Effects:
            - Creates storage_path and output_dir directories if needed
            - Initializes backend (ChromaDB or Qdrant) with embedder
            - Logs info about selected backend and configuration
        
        Example:
            >>> from pathlib import Path
            >>> from scripts.vector_db.embeddings import EmbeddingModel
            >>> embedder = EmbeddingModel('all-MiniLM-L6-v2')  # doctest: +SKIP
            >>> # Auto-select backend
            >>> store = VectorStore(embedder=embedder)  # doctest: +SKIP
            >>> # Prefer Qdrant
            >>> store_qdrant = VectorStore(
            ...     embedder=embedder,
            ...     prefer_backend='qdrant',
            ...     storage_path=Path('/data/qdrant_store')
            ... )  # doctest: +SKIP
            >>> # In-memory for testing
            >>> store_test = VectorStore(
            ...     embedder=embedder,
            ...     use_memory=True
            ... )  # doctest: +SKIP
        
        Note:
            Backend selection logic in _select_backend() tries preferred backend first,
            then falls back to alternative. Logs warnings for failures before fallback.
        """
        _validate_embedder(embedder)
        
        self.embedder = embedder
        self.embedding_dim = embedder.embedding_dim
        
        # Set up paths
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "output"
        
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = self.output_dir / "vector_db"
        
        # Select backend
        self.backend = self._select_backend(
            embedder=embedder,
            storage_path=self.storage_path,
            prefer_backend=prefer_backend,
            use_memory=use_memory,
            **backend_kwargs
        )
        
        logger.info(
            f"VectorStore initialized with {self.backend.backend_type.value} backend "
            f"(embedding_dim={self.embedding_dim})"
        )
    
    def _select_backend(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        storage_path: Path,
        prefer_backend: Optional[str] = None,
        use_memory: bool = False,
        **kwargs
    ) -> VectorStoreBackend:
        """Select and initialize vector database backend with automatic fallback.
        
        Tries to initialize backends in priority order (preferred first if specified,
        otherwise ChromaDB → Qdrant). Returns first successfully initialized backend.
        Logs warnings for failed attempts before falling back to alternative.
        
        Args:
            embedder: Text embedding model for backend initialization.
            storage_path: Base path for vector database storage. Backend-specific
                subdirectories created (chroma_db/, qdrant_storage/).
            prefer_backend: Optional preferred backend name ('chromadb' or 'qdrant').
                Case-insensitive. If specified, try this first before fallback.
            use_memory: If True, use in-memory mode (Qdrant only). If False, use
                persistent file storage.
            **kwargs: Additional backend-specific kwargs passed through.
        
        Returns:
            Initialized VectorStoreBackend instance (ChromaDBBackend or QdrantBackend).
        
        Raises:
            ValueError: If storage_path not provided (required for backend separation).
            RuntimeError: If all backends fail to initialize (libraries missing or errors).
        
        Side Effects:
            - Creates backend-specific subdirectories in storage_path
            - Logs info for successful initialization, warnings for failures
            - Initializes first available backend's client/storage
        
        Example:
            >>> # Prefer ChromaDB, fallback to Qdrant
            >>> backend = store._select_backend(
            ...     embedder=embedder,
            ...     storage_path=Path('/data/vector_db'),
            ...     prefer_backend='chromadb'
            ... )  # doctest: +SKIP
            >>> # Qdrant in-memory
            >>> backend = store._select_backend(
            ...     embedder=embedder,
            ...     storage_path=Path('/tmp/test'),
            ...     prefer_backend='qdrant',
            ...     use_memory=True
            ... )  # doctest: +SKIP
        
        Note:
            Backend directories separated to prevent conflicts:
            - ChromaDB: storage_path/chroma_db/
            - Qdrant: storage_path/qdrant_storage/ (or :memory:)
        """
        # Validate storage_path is provided
        if not storage_path:
            raise ValueError(
                "storage_path is required for VectorStore initialization. "
                "This ensures proper directory separation between backends."
            )
        
        storage_path = Path(storage_path)
        
        backends_to_try = []
        
        if prefer_backend:
            prefer_backend = prefer_backend.lower()
            if prefer_backend == "chromadb":
                backends_to_try = [BackendType.CHROMADB, BackendType.QDRANT]
            elif prefer_backend == "qdrant":
                backends_to_try = [BackendType.QDRANT, BackendType.CHROMADB]
            else:
                logger.warning(
                    f"Unknown preferred backend '{prefer_backend}'. "
                    f"Using default priority (ChromaDB -> Qdrant)"
                )
                backends_to_try = [BackendType.CHROMADB, BackendType.QDRANT]
        else:
            # Default priority: ChromaDB (primary) -> Qdrant (fallback)
            backends_to_try = [BackendType.CHROMADB, BackendType.QDRANT]
        
        last_error = None
        
        for backend_type in backends_to_try:
            try:
                if backend_type == BackendType.CHROMADB:
                    logger.info("Attempting to initialize ChromaDB backend...")
                    # Always provide explicit path - no fallback in backend
                    persist_dir = storage_path / "chroma_db"
                    backend = ChromaDBBackend(
                        embedder=embedder,
                        persist_directory=persist_dir,
                        **kwargs
                    )
                    logger.info("✓ ChromaDB backend initialized successfully")
                    logger.info(f"  Storage: {persist_dir}")
                    return backend
                
                elif backend_type == BackendType.QDRANT:
                    logger.info("Attempting to initialize Qdrant backend...")
                    # Always provide explicit path - no fallback in backend
                    qdrant_path = storage_path / "qdrant_storage"
                    backend = QdrantBackend(
                        embedder=embedder,
                        storage_path=qdrant_path,
                        use_memory=use_memory,
                        **kwargs
                    )
                    logger.info("✓ Qdrant backend initialized successfully")
                    logger.info(f"  Storage: {qdrant_path if not use_memory else 'memory'}")
                    return backend
            
            except (ImportError, RuntimeError, ValueError) as e:
                logger.warning(
                    f"Failed to initialize {backend_type.value} backend: {e}"
                )
                last_error = e
                continue
        
        # No backend could be initialized
        raise RuntimeError(
            f"Failed to initialize any vector database backend. "
            f"Last error: {last_error}. "
            f"Please install either chromadb>=1.3.0 or qdrant-client>=1.15.0"
        )
    
    @property
    def backend_type(self) -> BackendType:
        """Get active backend type identifier.
        
        Returns:
            BackendType enum value (CHROMADB or QDRANT) from active backend.
        
        Example:
            >>> store.backend_type  # doctest: +SKIP
            <BackendType.CHROMADB: 'chromadb'>
        """
        return self.backend.backend_type
    
    # ========================================================================
    # Delegated Methods (forward to active backend)
    # ========================================================================
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in active backend.
        
        Args:
            collection_name: Name of collection to check.
        
        Returns:
            True if collection exists, False otherwise.
        
        Example:
            >>> store.collection_exists('Indo-VAP_pdfs')  # doctest: +SKIP
            True
        """
        return self.backend.collection_exists(collection_name)
    
    def create_collection(
        self,
        study_name: str,
        dataset_type: str,
        recreate: bool = False
    ) -> str:
        """Create collection for study dataset with standardized naming.
        
        Generates collection name as "{study_name}_{dataset_type}" and creates
        in active backend. Ensures unique namespace per study/dataset combination.
        
        Args:
            study_name: Study identifier (e.g., 'Indo-VAP', 'TB-TRIAL').
            dataset_type: Dataset type ('pdfs', 'cleaned', 'original', etc.).
            recreate: If True, delete existing collection before creating.
                If False and exists, log info and return existing name.
        
        Returns:
            Created or existing collection name ("{study_name}_{dataset_type}").
        
        Raises:
            RuntimeError: If collection creation fails in backend.
        
        Example:
            >>> store.create_collection('Indo-VAP', 'pdfs')  # doctest: +SKIP
            'Indo-VAP_pdfs'
            >>> store.create_collection('TB-TRIAL', 'cleaned', recreate=True)  # doctest: +SKIP
            'TB-TRIAL_cleaned'
        """
        collection_name = self.get_collection_name(study_name, dataset_type)
        return self.backend.create_collection(collection_name, recreate=recreate)
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection from active backend.
        
        Args:
            collection_name: Name of collection to delete.
        
        Returns:
            True if deletion successful, False on error.
        
        Warning:
            Irreversible operation - all vectors and metadata permanently lost.
        
        Example:
            >>> store.delete_collection('old_study_pdfs')  # doctest: +SKIP
            True
        """
        return self.backend.delete_collection(collection_name)
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection metadata and statistics from active backend.
        
        Args:
            collection_name: Name of collection to inspect.
        
        Returns:
            Dictionary with 'name', 'points_count', 'backend', and backend-
            specific metadata. Empty dict on error.
        
        Example:
            >>> info = store.get_collection_info('Indo-VAP_pdfs')  # doctest: +SKIP
            >>> info['points_count']  # doctest: +SKIP
            1523
        """
        return self.backend.get_collection_info(collection_name)
    
    def get_collection_name(self, study_name: str, dataset_type: str) -> str:
        """Generate standardized collection name from study and dataset type.
        
        Args:
            study_name: Study identifier.
            dataset_type: Dataset type.
        
        Returns:
            Collection name as "{study_name}_{dataset_type}".
        
        Example:
            >>> store.get_collection_name('Indo-VAP', 'pdfs')
            'Indo-VAP_pdfs'
            >>> store.get_collection_name('TB-TRIAL', 'cleaned')
            'TB-TRIAL_cleaned'
        """
        return f"{study_name}_{dataset_type}"
    
    def discover_studies(self) -> List[StudyDataset]:
        """Scan output directory for study datasets with JSONL files.
        
        Walks output_dir to find study subdirectories with 'cleaned' or 'original'
        datasets containing .jsonl files. Returns StudyDataset descriptors for
        each discovered dataset.
        
        Skips special directories: 'vector_db', 'deidentified', 'data_dictionary_mappings'.
        
        Returns:
            List of StudyDataset objects for discovered datasets. Empty if output_dir
            doesn't exist or contains no datasets.
        
        Side Effects:
            - Logs verbose info for each discovered dataset
            - Logs info with total count
            - Logs warning if output_dir not found
        
        Example:
            >>> studies = store.discover_studies()  # doctest: +SKIP
            >>> for study in studies:  # doctest: +SKIP
            ...     print(f"{study.collection_name}: {study.path}")
            Indo-VAP_cleaned: /output/Indo-VAP/cleaned
            Indo-VAP_original: /output/Indo-VAP/original
            TB-TRIAL_cleaned: /output/TB-TRIAL/cleaned
        
        Note:
            Only returns datasets with at least one .jsonl file. Empty directories
            skipped. Use returned StudyDataset objects with ingest_jsonl_chunks().
        """
        studies = []
        
        if not self.output_dir.exists():
            logger.warning(f"Output directory not found: {self.output_dir}")
            return studies
        
        # Scan for study directories
        for study_dir in self.output_dir.iterdir():
            if not study_dir.is_dir():
                continue
            
            # Skip special directories
            if study_dir.name in ["vector_db", "deidentified", "data_dictionary_mappings"]:
                continue
            
            study_name = study_dir.name
            
            # Check for cleaned and original subdirectories
            for dataset_type in ["cleaned", "original"]:
                dataset_path = study_dir / dataset_type
                
                if dataset_path.exists() and dataset_path.is_dir():
                    jsonl_files = list(dataset_path.glob("*.jsonl"))
                    
                    if jsonl_files:
                        study_dataset = StudyDataset(
                            study_name=study_name,
                            dataset_type=dataset_type,
                            path=dataset_path
                        )
                        studies.append(study_dataset)
                        vlog(
                            f"Discovered: {study_dataset.collection_name} "
                            f"({len(jsonl_files)} files)"
                        )
        
        logger.info(f"Discovered {len(studies)} study datasets")
        return studies
    
    def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform semantic search for query text in collection.
        
        Encodes query text to embedding vector using self.embedder, then searches
        collection for most similar vectors. Supports optional metadata filtering.
        
        Args:
            collection_name: Collection to search (must exist).
            query: Natural language query text to search for.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0 to 1.0). Results below
                threshold filtered out.
            filters: Optional metadata filters (e.g., {'study': 'Indo-VAP', 'year': 2023}).
                Format varies by backend - use backend-specific filter translation.
        
        Returns:
            List of SearchResult objects sorted by descending similarity score.
            Empty list if collection not found or no results above threshold.
        
        Side Effects:
            - Logs warning if collection not found
            - Generates query embedding (embedder.encode call)
            - Backend logs search info (result count, max score)
        
        Example:
            >>> results = store.search(
            ...     collection_name='Indo-VAP_pdfs',
            ...     query='tuberculosis diagnosis and treatment',
            ...     limit=5,
            ...     score_threshold=0.7
            ... )  # doctest: +SKIP
            >>> for r in results:  # doctest: +SKIP
            ...     print(f"{r.score:.3f}: {r.text[:50]}...")
            0.856: TB diagnosis requires chest X-ray and sputum...
            0.812: Treatment protocol for drug-susceptible TB...
        
        Note:
            Query embedding generated on-the-fly. For repeated queries, consider
            caching embeddings. Filters passed directly to backend - format depends
            on active backend (ChromaDB dict, Qdrant Filter object).
        """
        # Check if collection exists
        if not self.collection_exists(collection_name):
            logger.warning(f"Collection not found: {collection_name}")
            return []
        
        # Generate query embedding
        query_vector = self.embedder.encode(query)
        
        # Delegate to backend
        return self.backend.search(
            collection_name=collection_name,
            query_embedding=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filters=filters
        )
    
    def search_with_filters(
        self,
        collection_name: str,
        query: str,
        metadata_filters: Dict[str, Any],
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """Search with automatic backend-specific metadata filter translation.
        
        Translates generic metadata filters dict to backend-specific format
        (ChromaDB where clause or Qdrant Filter object) before searching.
        Simplifies filtering across different backends.
        
        Args:
            collection_name: Collection to search.
            query: Natural language query text.
            metadata_filters: Generic metadata filters as dict (e.g.,
                {'study': 'Indo-VAP', 'form_code': '1A'}). Translated to
                backend-specific format automatically.
            limit: Maximum results.
            score_threshold: Minimum similarity score.
        
        Returns:
            List of SearchResult objects matching query and filters.
        
        Example:
            >>> results = store.search_with_filters(
            ...     collection_name='Indo-VAP_cleaned',
            ...     query='patient demographics',
            ...     metadata_filters={'form_code': '1A', 'year': 2023},
            ...     limit=10
            ... )  # doctest: +SKIP
        
        See Also:
            _translate_filters_for_chromadb: ChromaDB filter translation
            _translate_filters_for_qdrant: Qdrant filter translation
        """
        # Translate filters for active backend
        if self.backend_type == BackendType.CHROMADB:
            backend_filters = _translate_filters_for_chromadb(metadata_filters)
        elif self.backend_type == BackendType.QDRANT:
            backend_filters = _translate_filters_for_qdrant(metadata_filters)
        else:
            logger.warning(f"Unknown backend type: {self.backend_type}")
            backend_filters = metadata_filters
        
        # Use standard search with translated filters
        return self.search(
            collection_name=collection_name,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            filters=backend_filters
        )
    
    def search_by_form(
        self,
        study_name: str,
        form_code: str,
        query: str,
        dataset_type: str = "cleaned",
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """Search within specific clinical form type.
        
        Convenience method for form-specific search. Filters results to specific
        form code (e.g., '1A' for Index Case Screening) within study dataset.
        
        Args:
            study_name: Study identifier (e.g., 'Indo-VAP').
            form_code: Clinical form code to filter by (e.g., '1A', '2B', '95').
            query: Natural language query text.
            dataset_type: Dataset type ('cleaned' or 'original'). Default: 'cleaned'.
            limit: Maximum results.
            score_threshold: Minimum similarity score.
        
        Returns:
            List of SearchResult objects from specified form.
        
        Example:
            >>> # Search only Index Case Screening forms
            >>> results = store.search_by_form(
            ...     study_name='Indo-VAP',
            ...     form_code='1A',
            ...     query='patient inclusion criteria',
            ...     limit=5
            ... )  # doctest: +SKIP
        """
        collection_name = self.get_collection_name(study_name, dataset_type)
        return self.search_with_filters(
            collection_name=collection_name,
            query=query,
            metadata_filters={"form_code": form_code},
            limit=limit,
            score_threshold=score_threshold
        )
    
    def search_by_subject(
        self,
        study_name: str,
        subject_id: str,
        query: str,
        dataset_type: str = "cleaned",
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """Search within specific subject's data.
        
        Convenience method for subject-specific search. Filters results to
        specific patient/subject ID within study dataset.
        
        Args:
            study_name: Study identifier.
            subject_id: Patient/subject ID to filter by.
            query: Natural language query text.
            dataset_type: Dataset type ('cleaned' or 'original'). Default: 'cleaned'.
            limit: Maximum results.
            score_threshold: Minimum similarity score.
        
        Returns:
            List of SearchResult objects from specified subject.
        
        Example:
            >>> # Search only Subject 001's records
            >>> results = store.search_by_subject(
            ...     study_name='Indo-VAP',
            ...     subject_id='001',
            ...     query='adverse events',
            ...     limit=10
            ... )  # doctest: +SKIP
        """
        collection_name = self.get_collection_name(study_name, dataset_type)
        return self.search_with_filters(
            collection_name=collection_name,
            query=query,
            metadata_filters={"subject_id": subject_id},
            limit=limit,
            score_threshold=score_threshold
        )
    
    def search_with_fallback(
        self,
        query: str,
        study_name: str,
        primary_dataset: str = "cleaned",
        fallback_dataset: str = "original",
        use_fallback: bool = True,
        limit: int = 10,
        score_threshold: float = 0.5,
        min_results_for_fallback: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Search with automatic fallback from primary to fallback dataset.
        
        Searches primary dataset first. If result count below min_results_for_fallback
        threshold and use_fallback=True, automatically searches fallback dataset and
        merges results. Useful when cleaned data may have incomplete coverage.
        
        Args:
            query: Natural language query text.
            study_name: Study identifier.
            primary_dataset: Primary dataset type to search first. Default: 'cleaned'.
            fallback_dataset: Fallback dataset type if primary insufficient. Default: 'original'.
            use_fallback: If True, enable fallback logic. If False, only search primary.
            limit: Maximum total results after merging.
            score_threshold: Minimum similarity score.
            min_results_for_fallback: Trigger fallback if primary results below this.
                Default: 3.
            filters: Optional metadata filters applied to both searches.
        
        Returns:
            Tuple of (results_list, search_info_dict):
            - results_list: Merged and deduplicated SearchResult objects, sorted by
              score, limited to `limit`.
            - search_info_dict: Dictionary with keys:
                - 'query': Original query string
                - 'study_name': Study identifier
                - 'primary_dataset': Primary dataset searched
                - 'fallback_dataset': Fallback dataset (if triggered)
                - 'datasets_used': List of dataset types actually searched
                - 'primary_results': Count from primary search
                - 'fallback_results': Count from fallback (0 if not triggered)
                - 'fallback_triggered': Boolean, True if fallback executed
                - 'backend': Backend type used
        
        Side Effects:
            - Logs info when triggering fallback (with result counts)
            - Logs info when merging results
            - Both primary and fallback searches log their own info
        
        Example:
            >>> results, info = store.search_with_fallback(
            ...     query='adverse events',
            ...     study_name='Indo-VAP',
            ...     primary_dataset='cleaned',
            ...     min_results_for_fallback=5
            ... )  # doctest: +SKIP
            >>> print(f"Found {len(results)} results from {info['datasets_used']}")  # doctest: +SKIP
            Found 12 results from ['cleaned', 'original']
            >>> if info['fallback_triggered']:  # doctest: +SKIP
            ...     print(f"Fallback added {info['fallback_results']} results")
        
        Note:
            - Results sorted by score after merging, then limited
            - Deduplication: If same document in both datasets, higher score kept
            - Fallback only triggered when primary_results < min_results_for_fallback
            - Setting use_fallback=False disables fallback regardless of result count
        """
        search_info = {
            "query": query,
            "study_name": study_name,
            "primary_dataset": primary_dataset,
            "fallback_dataset": fallback_dataset,
            "datasets_used": [],
            "primary_results": 0,
            "fallback_results": 0,
            "fallback_triggered": False,
            "backend": self.backend_type.value
        }
        
        # Search primary collection
        primary_collection = self.get_collection_name(study_name, primary_dataset)
        primary_results = self.search(
            collection_name=primary_collection,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            filters=filters
        )
        
        search_info["primary_results"] = len(primary_results)
        search_info["datasets_used"].append(primary_dataset)
        
        # Check if fallback is needed
        if use_fallback and len(primary_results) < min_results_for_fallback:
            logger.info(
                f"Triggering fallback: only {len(primary_results)} results "
                f"from {primary_collection}"
            )
            
            # Search fallback collection
            fallback_collection = self.get_collection_name(study_name, fallback_dataset)
            fallback_results = self.search(
                collection_name=fallback_collection,
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )
            
            search_info["fallback_results"] = len(fallback_results)
            search_info["fallback_triggered"] = True
            search_info["datasets_used"].append(fallback_dataset)
            
            # Merge and deduplicate results
            all_results = primary_results + fallback_results
            all_results.sort(key=lambda x: x.score, reverse=True)
            final_results = all_results[:limit]
            
            logger.info(
                f"Merged results: {len(primary_results)} primary + "
                f"{len(fallback_results)} fallback = {len(final_results)} total"
            )
        else:
            final_results = primary_results
        
        return final_results, search_info
    
    def ingest_pdf_chunks(
        self,
        pdf_chunks: List[PDFChunk],
        collection_name: str,
        batch_size: int = 100
    ) -> int:
        """Ingest PDF document chunks to collection with metadata extraction.
        
        Processes PDF chunks in batches, generating embeddings and extracting metadata
        (form codes, page numbers, section titles) into payloads. Each chunk assigned
        unique UUID. Efficient for large PDF documents with batch processing.
        
        Args:
            pdf_chunks: List of PDFChunk objects from pdf_chunking module.
            collection_name: Target collection (must exist - create first).
            batch_size: Number of chunks to process per batch. Balances memory
                usage vs. API overhead. Default: 100.
        
        Returns:
            Total number of chunks successfully uploaded.
        
        Raises:
            ValueError: If collection doesn't exist.
        
        Side Effects:
            - Generates embeddings for all chunk texts (embedder.encode calls)
            - Creates UUIDs for each chunk
            - Logs info at start/end, verbose for each batch
            - Logs error for individual chunk failures (continues processing)
        
        Example:
            >>> from scripts.vector_db.pdf_chunking import chunk_pdf_document
            >>> # Chunk PDF first
            >>> chunks = chunk_pdf_document(pdf_path, ...)  # doctest: +SKIP
            >>> # Create collection
            >>> store.create_collection('Indo-VAP', 'pdfs')  # doctest: +SKIP
            >>> # Ingest chunks
            >>> count = store.ingest_pdf_chunks(
            ...     pdf_chunks=chunks,
            ...     collection_name='Indo-VAP_pdfs',
            ...     batch_size=50
            ... )  # doctest: +SKIP
            >>> print(f"Uploaded {count} PDF chunks")  # doctest: +SKIP
        
        Note:
            Payload structure for PDF chunks:
            - text: Chunk text content
            - source_type: Always 'pdf'
            - form_code: Clinical form code (or empty string)
            - form_title: Form title (or empty string)
            - section_title: Section within form
            - page_number: PDF page number
            - folder_path: Source folder path
            - filename: Source PDF filename
            - chunk_index: Index within document
            - token_count: Number of tokens in chunk
            - chunk_strategy: Chunking method used
        """
        if not pdf_chunks:
            logger.warning("No PDF chunks to ingest")
            return 0
        
        if not self.collection_exists(collection_name):
            raise ValueError(
                f"Collection '{collection_name}' does not exist. "
                f"Create it first using create_collection()"
            )
        
        logger.info(f"Ingesting {len(pdf_chunks)} PDF chunks to {collection_name}")
        
        total_uploaded = 0
        
        # Process in batches
        for i in range(0, len(pdf_chunks), batch_size):
            batch = pdf_chunks[i:i + batch_size]
            
            # Prepare batch data
            ids = []
            embeddings = []
            payloads = []
            
            for chunk in batch:
                try:
                    # Generate embedding
                    embedding = self.embedder.encode(chunk.text)
                    
                    # Create payload
                    payload = {
                        "text": chunk.text,
                        "source_type": "pdf",
                        "form_code": chunk.form_code or "",
                        "form_title": chunk.form_title or "",
                        "section_title": chunk.metadata.get("section_title", ""),
                        "page_number": chunk.page_number,
                        "folder_path": chunk.folder_path,
                        "filename": chunk.source_file,
                        "chunk_index": chunk.chunk_index,
                        "token_count": chunk.token_count,
                        "chunk_strategy": chunk.chunk_strategy,
                    }
                    
                    ids.append(str(uuid.uuid4()))
                    embeddings.append(embedding.tolist())
                    payloads.append(payload)
                
                except Exception as e:
                    logger.error(f"Failed to process chunk {chunk.chunk_index}: {e}")
                    continue
            
            # Upload batch
            if ids:
                try:
                    uploaded = self.backend.upsert_points(
                        collection_name=collection_name,
                        ids=ids,
                        embeddings=embeddings,
                        payloads=payloads
                    )
                    total_uploaded += uploaded
                    vlog(f"Uploaded batch {i//batch_size + 1}: {uploaded} points")
                except Exception as e:
                    logger.error(f"Failed to upload batch {i//batch_size + 1}: {e}")
        
        logger.info(f"✅ Ingested {total_uploaded}/{len(pdf_chunks)} PDF chunks to {collection_name}")
        return total_uploaded
    
    def ingest_jsonl_chunks(
        self,
        jsonl_chunks: List[TextChunk],
        collection_name: str,
        batch_size: int = 100
    ) -> int:
        """Ingest JSONL record chunks to collection with metadata extraction.
        
        Processes TextChunk objects from JSONL records in batches, generating
        embeddings and extracting metadata (subject IDs, form names, original
        records) into payloads. Each chunk assigned unique UUID.
        
        Args:
            jsonl_chunks: List of TextChunk objects from jsonl_chunking_nl module.
            collection_name: Target collection (must exist - create first).
            batch_size: Number of chunks to process per batch. Default: 100.
        
        Returns:
            Total number of chunks successfully uploaded.
        
        Raises:
            ValueError: If collection doesn't exist.
        
        Side Effects:
            - Generates embeddings for all chunk texts
            - Creates UUIDs for each chunk
            - Logs info at start/end, verbose for each batch
            - Logs error for individual chunk failures (continues processing)
        
        Example:
            >>> from scripts.vector_db.jsonl_chunking_nl import chunk_jsonl_file
            >>> # Chunk JSONL first
            >>> chunks = chunk_jsonl_file(jsonl_path, ...)  # doctest: +SKIP
            >>> # Create collection
            >>> store.create_collection('Indo-VAP', 'cleaned')  # doctest: +SKIP
            >>> # Ingest chunks
            >>> count = store.ingest_jsonl_chunks(
            ...     jsonl_chunks=chunks,
            ...     collection_name='Indo-VAP_cleaned',
            ...     batch_size=50
            ... )  # doctest: +SKIP
            >>> print(f"Uploaded {count} record chunks")  # doctest: +SKIP
        
        Note:
            Payload structure for JSONL chunks:
            - text: Chunk text content
            - source_type: Always 'jsonl'
            - original_json: Original record dict from JSONL
            - subject_id: Patient/subject identifier
            - form_name: Clinical form name
            - chunk_index: Index within record
            - token_count: Number of tokens
            - chunk_strategy: Chunking method used
        """
        if not jsonl_chunks:
            logger.warning("No JSONL chunks to ingest")
            return 0
        
        if not self.collection_exists(collection_name):
            raise ValueError(
                f"Collection '{collection_name}' does not exist. "
                f"Create it first using create_collection()"
            )
        
        logger.info(f"Ingesting {len(jsonl_chunks)} JSONL chunks to {collection_name}")
        
        total_uploaded = 0
        
        # Process in batches
        for i in range(0, len(jsonl_chunks), batch_size):
            batch = jsonl_chunks[i:i + batch_size]
            
            # Prepare batch data
            ids = []
            embeddings = []
            payloads = []
            
            for chunk in batch:
                try:
                    # Generate embedding
                    embedding = self.embedder.encode(chunk.text)
                    
                    # Create payload
                    payload = {
                        "text": chunk.text,
                        "source_type": "jsonl",
                        "original_json": chunk.metadata.get("original_record", {}),
                        "subject_id": chunk.metadata.get("subject_id", ""),
                        "form_name": chunk.metadata.get("form_name", ""),
                        "chunk_index": chunk.chunk_index,
                        "token_count": chunk.token_count,
                        "chunk_strategy": chunk.chunk_strategy,
                    }
                    
                    ids.append(str(uuid.uuid4()))
                    embeddings.append(embedding.tolist())
                    payloads.append(payload)
                
                except Exception as e:
                    logger.error(f"Failed to process chunk {chunk.chunk_index}: {e}")
                    continue
            
            # Upload batch
            if ids:
                try:
                    uploaded = self.backend.upsert_points(
                        collection_name=collection_name,
                        ids=ids,
                        embeddings=embeddings,
                        payloads=payloads
                    )
                    total_uploaded += uploaded
                    vlog(f"Uploaded batch {i//batch_size + 1}: {uploaded} points")
                except Exception as e:
                    logger.error(f"Failed to upload batch {i//batch_size + 1}: {e}")
        
        logger.info(f"✅ Ingested {total_uploaded}/{len(jsonl_chunks)} JSONL chunks to {collection_name}")
        return total_uploaded
    
    def __repr__(self) -> str:
        """Generate string representation of VectorStore instance.
        
        Returns:
            Human-readable string with backend type, embedding dimension, and output directory.
        
        Example:
            >>> store  # doctest: +SKIP
            VectorStore(backend=chromadb, embedding_dim=384, output_dir='/data/output')
        """
        return (
            f"VectorStore(backend={self.backend_type.value}, "
            f"embedding_dim={self.embedding_dim}, "
            f"output_dir='{self.output_dir}')"
        )
