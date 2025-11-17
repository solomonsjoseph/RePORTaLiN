"""Vector store management with ChromaDB and Qdrant backends."""

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
    """Vector database backend types."""
    CHROMADB = "chromadb"
    QDRANT = "qdrant"


@dataclass
class SearchResult:
    """Search result from vector database with score and metadata."""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    collection_name: str = ""
    
    def __repr__(self) -> str:
        """String representation of search result."""
        return (
            f"SearchResult(score={self.score:.3f}, "
            f"collection='{self.collection_name}', "
            f"text='{self.text[:50]}...')"
        )


@dataclass
class StudyDataset:
    """Study dataset with collection name and path."""
    study_name: str
    dataset_type: str
    path: Path
    collection_name: str = ""
    
    def __post_init__(self):
        """Generate collection name after initialization."""
        if not self.collection_name:
            self.collection_name = f"{self.study_name}_{self.dataset_type}"


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_embedder(embedder: Any) -> None:
    """Validate that embedder implements required interface."""
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
    """Translate generic metadata filters to ChromaDB where clause format."""
    # ChromaDB uses simple dict format - just return as is for basic equality
    # For more complex queries, ChromaDB supports:
    # - $and, $or, $not operators
    # - $in, $nin for list membership
    # - $gt, $gte, $lt, $lte for comparisons
    return metadata_filters


def _translate_filters_for_qdrant(metadata_filters: Dict[str, Any]):
    """Translate generic metadata filters to Qdrant Filter format."""
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
    """Abstract base class for vector database backends."""
    
    @abstractmethod
    def __init__(self, embedder: Union[EmbeddingModel, AdaptiveEmbedder], **kwargs):
        """Initialize backend with embedder."""
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, recreate: bool = False) -> str:
        """Create a collection."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        pass
    
    @abstractmethod
    def upsert_points(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> int:
        """Upsert points to collection."""
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
        """Search collection."""
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information."""
        pass
    
    @property
    @abstractmethod
    def backend_type(self) -> BackendType:
        """Return backend type."""
        pass


# ============================================================================
# ChromaDB Backend (Primary)
# ============================================================================

class ChromaDBBackend(VectorStoreBackend):
    """ChromaDB vector database backend for local storage."""
    
    def __init__(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        persist_directory: Path,
        **kwargs
    ):
        """Initialize ChromaDB backend."""
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
        """Return backend type."""
        return BackendType.CHROMADB
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def create_collection(self, collection_name: str, recreate: bool = False) -> str:
        """Create a ChromaDB collection."""
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
        """Delete a collection."""
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
        """Upsert points to ChromaDB collection."""
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
        """Search ChromaDB collection."""
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
        """Get ChromaDB collection information."""
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
    """Qdrant vector database backend for production workloads."""
    
    def __init__(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        storage_path: Optional[Path] = None,
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = False,
        **kwargs
    ):
        """Initialize Qdrant backend."""
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
        """Return backend type."""
        return BackendType.QDRANT
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def create_collection(self, collection_name: str, recreate: bool = False) -> str:
        """Create a Qdrant collection."""
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
        """Delete a collection."""
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
        """Upsert points to Qdrant collection."""
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
        """Search Qdrant collection."""
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
        """Get Qdrant collection information."""
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
    """Unified vector store interface with automatic backend selection."""
    
    def __init__(
        self,
        embedder: Union[EmbeddingModel, AdaptiveEmbedder],
        storage_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        prefer_backend: Optional[str] = None,
        use_memory: bool = False,
        **backend_kwargs
    ):
        """Initialize vector store with automatic backend selection."""
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
        """Select vector database backend based on availability and preference."""
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
        """Get active backend type."""
        return self.backend.backend_type
    
    # ========================================================================
    # Delegated Methods (forward to active backend)
    # ========================================================================
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        return self.backend.collection_exists(collection_name)
    
    def create_collection(
        self,
        study_name: str,
        dataset_type: str,
        recreate: bool = False
    ) -> str:
        """Create a collection for a study dataset."""
        collection_name = self.get_collection_name(study_name, dataset_type)
        return self.backend.create_collection(collection_name, recreate=recreate)
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        return self.backend.delete_collection(collection_name)
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information."""
        return self.backend.get_collection_info(collection_name)
    
    def get_collection_name(self, study_name: str, dataset_type: str) -> str:
        """Generate collection name from study and dataset type."""
        return f"{study_name}_{dataset_type}"
    
    def discover_studies(self) -> List[StudyDataset]:
        """Discover all studies and datasets from output directory."""
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
        """Search collection for similar vectors."""
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
        """Search with metadata filtering."""
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
        """Search within a specific clinical form."""
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
        """Search within a specific subject's data."""
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
        """Search with automatic fallback from primary to fallback dataset."""
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
        """Ingest PDF chunks to collection."""
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
        """Ingest JSONL chunks to collection."""
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
        """String representation of vector store."""
        return (
            f"VectorStore(backend={self.backend_type.value}, "
            f"embedding_dim={self.embedding_dim}, "
            f"output_dir='{self.output_dir}')"
        )
