"""Adaptive embedding system with automatic medical/general model selection."""

import time
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Sentence-transformers for embedding generation
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    warnings.warn(
        "sentence-transformers not installed. "
        "Install with: pip install sentence-transformers"
    )

# Import model constants from embeddings module (avoid duplication)
from .embeddings import EmbeddingModel
from scripts.utils import logging_system as log

# Configure logging
logger = log.get_logger(__name__)
vlog = log.get_verbose_logger()


# ============================================================================
# CONSTANTS
# ============================================================================

# Model identifiers (imported from embeddings.py to avoid duplication)
MEDICAL_MODEL_ID = EmbeddingModel.BIOLORD_MODEL
GENERAL_MODEL_ID = EmbeddingModel.DEFAULT_MODEL

# Embedding dimensions (reference from embeddings.MODEL_DIMENSIONS)
MEDICAL_MODEL_DIM = EmbeddingModel.MODEL_DIMENSIONS[MEDICAL_MODEL_ID]  # 768
GENERAL_MODEL_DIM = EmbeddingModel.MODEL_DIMENSIONS[GENERAL_MODEL_ID]  # 384
TARGET_DIM = 768  # Standardized dimension for Qdrant (matches BioLORD)

# Batch processing defaults
DEFAULT_BATCH_SIZE = 32
MAX_SEQUENCE_LENGTH = 512

# Medical keyword detection threshold (configurable)
MEDICAL_KEYWORD_THRESHOLD = 0.15  # 15% of tokens must be medical


# ============================================================================
# ENUMS
# ============================================================================

class QueryType(Enum):
    """Query content classification types."""
    MEDICAL = "medical"
    GENERAL = "general"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ModelType(Enum):
    """Available embedding model types."""
    BIOLORD = MEDICAL_MODEL_ID
    MINILM = GENERAL_MODEL_ID


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EmbeddingResult:
    """Embedding generation result with metadata."""
    embeddings: np.ndarray
    model_used: List[str] = field(default_factory=list)
    query_types: List[QueryType] = field(default_factory=list)
    token_counts: List[int] = field(default_factory=list)
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "embeddings_shape": self.embeddings.shape,
            "model_used": self.model_used,
            "query_types": [qt.value for qt in self.query_types],
            "token_counts": self.token_counts,
            "processing_time": self.processing_time
        }


# ============================================================================
# MAIN CLASS
# ============================================================================

class AdaptiveEmbedder:
    """Adaptive embedding system with automatic model selection."""
    
    def __init__(
        self,
        medical_model: str = MEDICAL_MODEL_ID,
        general_model: str = GENERAL_MODEL_ID,
        medical_keywords: Optional[List[str]] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        device: Optional[str] = None,
        show_progress: bool = False
    ):
        """Initialize adaptive embedder with medical and general models."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            )
        
        self.batch_size = batch_size
        self.target_dim = TARGET_DIM
        self.show_progress = show_progress
        
        # Set cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None
        
        # Initialize medical keywords
        self.medical_keywords = self._get_default_medical_keywords()
        if medical_keywords:
            self.medical_keywords.update(kw.lower() for kw in medical_keywords)
        
        # Load models using EmbeddingModel wrapper (eliminates code duplication)
        logger.info("Initializing adaptive embedder...")
        try:
            # Medical model (BioLORD-2023-C, 768 dims)
            logger.info(f"Loading medical embedder: {medical_model}...")
            self.medical_embedder = EmbeddingModel(
                model_name=medical_model,
                device=device,
                batch_size=batch_size,
                cache_dir=self.cache_dir,
                show_progress=False  # AdaptiveEmbedder controls progress display
            )
            
            # General model (all-MiniLM-L6-v2, 384 dims)
            logger.info(f"Loading general embedder: {general_model}...")
            self.general_embedder = EmbeddingModel(
                model_name=general_model,
                device=device,
                batch_size=batch_size,
                cache_dir=self.cache_dir,
                show_progress=False  # AdaptiveEmbedder controls progress display
            )
            
            # Extract underlying SentenceTransformer models for backward compatibility
            self.medical_model = self.medical_embedder.model
            self.general_model = self.general_embedder.model
            
            # Verify dimensions match expected values
            if self.medical_embedder.embedding_dim != MEDICAL_MODEL_DIM:
                logger.warning(
                    f"Medical model dimension mismatch: "
                    f"expected {MEDICAL_MODEL_DIM}, got {self.medical_embedder.embedding_dim}"
                )
            
            if self.general_embedder.embedding_dim != GENERAL_MODEL_DIM:
                logger.warning(
                    f"General model dimension mismatch: "
                    f"expected {GENERAL_MODEL_DIM}, got {self.general_embedder.embedding_dim}"
                )
            
            # Store device info (from medical embedder)
            self.device = self.medical_embedder.device
            
            logger.info(
                f"Adaptive embedder initialized successfully:\n"
                f"  Medical: {medical_model} ({self.medical_embedder.embedding_dim} dims)\n"
                f"  General: {general_model} ({self.general_embedder.embedding_dim} dims → 768 padded)\n"
                f"  Cache: {self.cache_dir or 'default'}\n"
                f"  Device: {self.device}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize adaptive embedder: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e
    
    
    def _get_default_medical_keywords(self) -> set:
        """Get default medical keywords for content detection."""
        return {
            # Diseases and conditions
            "tuberculosis", "tb", "hiv", "aids", "pneumonia", "malaria",
            "hepatitis", "diabetes", "hypertension", "anemia", "sepsis",
            "infection", "disease", "syndrome", "disorder",
            
            # Symptoms
            "symptom", "cough", "fever", "fatigue", "pain", "dyspnea",
            "hemoptysis", "weight loss", "night sweats", "lymphadenopathy",
            "nausea", "vomiting", "diarrhea", "headache",
            
            # Clinical terms
            "patient", "subject", "clinical", "medical", "diagnosis",
            "treatment", "therapy", "medication", "drug", "prophylaxis",
            "adverse event", "complication", "prognosis", "mortality",
            
            # Procedures and tests
            "chest x-ray", "ct scan", "mri", "biopsy", "culture",
            "smear", "screening", "test", "assay", "specimen",
            "tst", "igra", "cbc", "cd4", "viral load",
            
            # Anatomical terms
            "lung", "pulmonary", "respiratory", "cardiac", "hepatic",
            "renal", "lymph node", "tissue", "organ",
            
            # Medical actions
            "administer", "prescribe", "diagnose", "treat", "monitor",
            "follow-up", "hospitalization", "discharge", "referral",
            
            # Study-specific
            "hhc", "index case", "household contact", "transmission",
            "baseline", "enrollment", "consent", "eligibility"
        }
    
    def detect_query_type(self, text: str) -> Tuple[QueryType, float]:
        """Detect if text is medical, general, or mixed content."""
        if not text or not text.strip():
            return QueryType.UNKNOWN, 0.0
        
        # Tokenize (simple whitespace split)
        tokens = text.lower().split()
        if not tokens:
            return QueryType.UNKNOWN, 0.0
        
        # Count medical keywords
        medical_count = sum(
            1 for token in tokens
            if any(keyword in token for keyword in self.medical_keywords)
        )
        
        # Calculate ratio
        medical_ratio = medical_count / len(tokens)
        
        # Classify
        if medical_ratio >= MEDICAL_KEYWORD_THRESHOLD:
            if medical_ratio > 0.6:
                return QueryType.MEDICAL, medical_ratio
            else:
                return QueryType.MIXED, medical_ratio
        else:
            return QueryType.GENERAL, medical_ratio
    
    def _pad_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Pad embedding to target dimension with zeros."""
        current_dim = len(embedding)
        
        if current_dim == self.target_dim:
            return embedding
        elif current_dim > self.target_dim:
            logger.warning(
                f"Embedding dimension ({current_dim}) exceeds target "
                f"({self.target_dim}). Truncating."
            )
            return embedding[:self.target_dim]
        else:
            # Pad with zeros
            padding_size = self.target_dim - current_dim
            padding = np.zeros(padding_size, dtype=embedding.dtype)
            return np.concatenate([embedding, padding])
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: Optional[int] = None,
        show_progress: Optional[bool] = None,
        normalize_embeddings: bool = True
    ) -> EmbeddingResult:
        """Generate embeddings with adaptive model selection."""
        start_time = time.time()
        
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            logger.warning("Empty input to encode()")
            return EmbeddingResult(
                embeddings=np.array([]),
                processing_time=0.0
            )
        
        # Use provided parameters or defaults
        batch_size = batch_size or self.batch_size
        show_progress = show_progress if show_progress is not None else self.show_progress
        
        # Classify each text and group by model
        medical_texts = []
        general_texts = []
        medical_indices = []
        general_indices = []
        query_types = []
        medical_ratios = []
        
        vlog(f"Classifying {len(texts)} texts...")
        for i, text in enumerate(texts):
            query_type, ratio = self.detect_query_type(text)
            query_types.append(query_type)
            medical_ratios.append(ratio)
            
            # Route to appropriate model
            if query_type in (QueryType.MEDICAL, QueryType.MIXED):
                medical_texts.append(text)
                medical_indices.append(i)
            else:
                general_texts.append(text)
                general_indices.append(i)
        
        logger.info(
            f"Content classification:\n"
            f"  Medical: {len(medical_texts)} texts\n"
            f"  General: {len(general_texts)} texts"
        )
        
        # Generate embeddings
        embeddings = np.zeros((len(texts), self.target_dim), dtype=np.float32)
        model_used = [""] * len(texts)
        
        # Encode medical texts with BioLORD
        if medical_texts:
            vlog(f"Encoding {len(medical_texts)} medical texts with BioLORD...")
            medical_embeddings = self.medical_model.encode(
                medical_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True
            )
            
            # Already 768 dims, no padding needed
            for idx, emb in zip(medical_indices, medical_embeddings):
                embeddings[idx] = emb
                model_used[idx] = "BioLORD-2023-C"
        
        # Encode general texts with MiniLM and pad
        if general_texts:
            vlog(f"Encoding {len(general_texts)} general texts with MiniLM...")
            general_embeddings = self.general_model.encode(
                general_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True
            )
            
            # Pad from 384 to 768 dims
            for idx, emb in zip(general_indices, general_embeddings):
                embeddings[idx] = self._pad_embedding(emb)
                model_used[idx] = "all-MiniLM-L6-v2"
        
        # Calculate token counts (simple whitespace split)
        token_counts = [len(text.split()) for text in texts]
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Encoding complete:\n"
            f"  Total texts: {len(texts)}\n"
            f"  BioLORD: {len(medical_texts)}\n"
            f"  MiniLM: {len(general_texts)}\n"
            f"  Time: {processing_time:.2f}s"
        )
        
        return EmbeddingResult(
            embeddings=embeddings,
            model_used=model_used,
            query_types=query_types,
            token_counts=token_counts,
            processing_time=processing_time
        )
    
    def get_embedding_dimension(self) -> int:
        """Get the standardized embedding dimension."""
        return self.target_dim
    
    def add_medical_keywords(self, keywords: List[str]) -> None:
        """Add custom medical keywords for detection."""
        self.medical_keywords.update(kw.lower() for kw in keywords)
        logger.info(f"Added {len(keywords)} medical keywords")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "medical_model": {
                "id": MEDICAL_MODEL_ID,
                "dimension": MEDICAL_MODEL_DIM,
                "device": str(self.device)
            },
            "general_model": {
                "id": GENERAL_MODEL_ID,
                "dimension": GENERAL_MODEL_DIM,
                "device": str(self.device)
            },
            "target_dimension": self.target_dim,
            "medical_keywords_count": len(self.medical_keywords),
            "batch_size": self.batch_size,
            "cache_dir": str(self.cache_dir) if self.cache_dir else None
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_adaptive_embedder(
    cache_dir: Optional[str] = None,
    **kwargs
) -> AdaptiveEmbedder:
    """Factory function to create an AdaptiveEmbedder instance."""
    return AdaptiveEmbedder(cache_dir=cache_dir, **kwargs)


# ============================================================================
# MODULE-LEVEL EXPORTS
# ============================================================================

__all__ = [
    "AdaptiveEmbedder",
    "EmbeddingResult",
    "QueryType",
    "ModelType",
    "create_adaptive_embedder",
    "MEDICAL_MODEL_ID",
    "GENERAL_MODEL_ID",
    "TARGET_DIM",
]
