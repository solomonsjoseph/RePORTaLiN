"""Embedding model wrapper for sentence-transformers."""

from pathlib import Path
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential

from scripts.utils import logging_system as log

# Configure logging
logger = log.get_logger(__name__)
vlog = log.get_verbose_logger()


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding models."""
    
    # Default models (ordered by recommendation)
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    BIOMEDICAL_MODEL = "pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb"
    BIOLORD_MODEL = "FremyCompany/BioLORD-2023-C"  # Medical-optimized (768 dims)
    
    # Model dimensions (for validation and reference)
    MODEL_DIMENSIONS = {
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb": 768,
        "FremyCompany/BioLORD-2023-C": 768,  # Medical domain-specific
    }
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = 32,
        cache_dir: Optional[Path] = None,
        show_progress: bool = True
    ):
        """Initialize the embedding model."""
        self.model_name = model_name or self.DEFAULT_MODEL
        self.batch_size = batch_size
        self.show_progress = show_progress
        self.cache_dir = cache_dir
        
        logger.info(f"Initializing embedding model: {self.model_name}")
        
        # Load model with retry logic
        self.model = self._load_model(device)
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.device = str(self.model.device)
        
        logger.info(
            f"Embedding model loaded successfully. "
            f"Device: {self.device}, Embedding dim: {self.embedding_dim}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _load_model(self, device: Optional[str] = None) -> SentenceTransformer:
        """Load sentence-transformers model with retry logic."""
        try:
            model = SentenceTransformer(
                self.model_name,
                device=device,
                cache_folder=str(self.cache_dir) if self.cache_dir else None
            )
            return model
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise RuntimeError(
                f"Could not load embedding model '{self.model_name}'. "
                f"Please check model name and internet connection. Error: {e}"
            )
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize_embeddings: bool = True,
        show_progress_bar: Optional[bool] = None,
        convert_to_numpy: bool = True
    ) -> np.ndarray:
        """Generate embeddings for text or list of texts."""
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        # Validate inputs
        if not texts:
            logger.warning("Empty text list provided to encode()")
            return np.array([])
        
        # Filter out None or empty strings
        valid_texts = [t for t in texts if t and isinstance(t, str)]
        if len(valid_texts) != len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} invalid texts "
                f"(None or empty strings)"
            )
        
        if not valid_texts:
            logger.error("No valid texts to encode after filtering")
            return np.array([])
        
        # Determine progress bar setting
        show_progress = (
            show_progress_bar if show_progress_bar is not None 
            else self.show_progress
        )
        
        vlog(
            f"Encoding {len(valid_texts)} texts with batch_size={self.batch_size}"
        )
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=convert_to_numpy
            )
            
            # Return single embedding if single input
            if single_input:
                return embeddings[0]
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")
    
    def encode_batch_with_metadata(
        self,
        texts: List[str],
        metadata: Optional[List[dict]] = None,
        normalize_embeddings: bool = True
    ) -> List[dict]:
        """Generate embeddings with associated metadata."""
        # Validate inputs
        if metadata is not None and len(metadata) != len(texts):
            raise ValueError(
                f"Length mismatch: {len(texts)} texts but {len(metadata)} metadata dicts"
            )
        
        # Generate embeddings
        embeddings = self.encode(
            texts,
            normalize_embeddings=normalize_embeddings,
            show_progress_bar=True
        )
        
        # Combine with metadata
        results = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            result = {
                "text": text,
                "embedding": embedding,
                "metadata": metadata[i] if metadata else {}
            }
            results.append(result)
        
        logger.info(f"Generated {len(results)} embeddings with metadata")
        return results
    
    def get_similarity(
        self,
        text1: Union[str, np.ndarray],
        text2: Union[str, np.ndarray],
        metric: str = "cosine"
    ) -> float:
        """Calculate similarity between two texts or embeddings."""
        # Generate embeddings if inputs are strings
        if isinstance(text1, str):
            text1 = self.encode(text1, normalize_embeddings=True)
        if isinstance(text2, str):
            text2 = self.encode(text2, normalize_embeddings=True)
        
        # Calculate similarity
        if metric == "cosine":
            # Cosine similarity via dot product (valid for normalized embeddings)
            # For unit vectors: cos_sim(a,b) = dot(a,b) since ||a|| = ||b|| = 1
            similarity = np.dot(text1, text2)
        elif metric == "dot":
            # Dot product similarity
            similarity = np.dot(text1, text2)
        else:
            raise ValueError(f"Unknown metric: {metric}. Use 'cosine' or 'dot'")
        
        return float(similarity)
    
    def __repr__(self) -> str:
        """String representation of embedding model."""
        return (
            f"EmbeddingModel(model='{self.model_name}', "
            f"dim={self.embedding_dim}, device='{self.device}')"
        )


def get_default_embedder(
    use_biomedical: bool = False,
    **kwargs
) -> EmbeddingModel:
    """Factory function to get default embedding model."""
    model_name = (
        EmbeddingModel.BIOMEDICAL_MODEL if use_biomedical 
        else EmbeddingModel.DEFAULT_MODEL
    )
    
    logger.info(
        f"Creating default embedder: "
        f"{'Biomedical' if use_biomedical else 'General-purpose'}"
    )
    
    return EmbeddingModel(model_name=model_name, **kwargs)
