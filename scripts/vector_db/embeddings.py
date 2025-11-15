"""
Embedding Model Management for Vector Database.

This module provides a wrapper around sentence-transformers models for generating
embeddings from clinical text. It handles model loading, caching, batching, and
error recovery.

Key Features:
    - Automatic model download and caching
    - Batch processing for efficiency
    - GPU acceleration support (if available)
    - Retry logic for transient failures
    - Progress tracking for large datasets

Default Model:
    all-MiniLM-L6-v2 (384 dimensions)
    - Fast inference
    - Good general-purpose performance
    - Widely tested and reliable
    
    Alternatives:
    - FremyCompany/BioLORD-2023-C (768 dimensions)
      * Medical domain-specific (UMLS, SNOMED-CT trained)
      * State-of-the-art for clinical text
      * Recommended for medical queries
    
    - pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb (768 dimensions)
      * Medical domain-specific
      * Good for clinical terminology
      * Slower, larger model

Author: RePORTaLiN Development Team
Date: November 2025
"""

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
    """
    Wrapper for sentence-transformers embedding models.
    
    This class manages embedding generation with support for batching,
    caching, GPU acceleration, and error handling.
    
    Attributes:
        model_name (str): Name of the sentence-transformers model
        model (SentenceTransformer): Loaded embedding model
        embedding_dim (int): Dimensionality of embeddings
        device (str): Device for inference ('cuda' or 'cpu')
        batch_size (int): Batch size for encoding
    
    Example:
        >>> import numpy as np
        >>> embedder = EmbeddingModel()
        >>> texts = ["Patient has cough and fever", "TB symptoms present"]
        >>> embeddings: np.ndarray = embedder.encode(texts)
        >>> embeddings.shape  # tuple: (2, 384)
        (2, 384)
    """
    
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
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of sentence-transformers model. Defaults to all-MiniLM-L6-v2.
            device: Device for inference ('cuda', 'cpu', or None for auto-detect).
            batch_size: Batch size for encoding. Default 32.
            cache_dir: Directory to cache models. Defaults to ~/.cache/sentence-transformers.
            show_progress: Show progress bars during encoding. Default True.
        
        Raises:
            RuntimeError: If model fails to load
            ValueError: If invalid model name provided
        """
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
        """
        Load sentence-transformers model with retry logic.
        
        Args:
            device: Device for inference ('cuda', 'cpu', or None for auto-detect)
        
        Returns:
            Loaded SentenceTransformer model
        
        Raises:
            RuntimeError: If model fails to load after retries
        """
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
        """
        Generate embeddings for text or list of texts.
        
        Args:
            texts: Single text string or list of text strings
            normalize_embeddings: Normalize embeddings to unit length (for cosine similarity)
            show_progress_bar: Override class default for progress bar display
            convert_to_numpy: Return as numpy array (True) or torch tensor (False)
        
        Returns:
            Numpy array of shape (n_texts, embedding_dim) or single embedding
        
        Example:
            >>> import numpy as np
            >>> embedder = EmbeddingModel()
            >>> embedding: np.ndarray = embedder.encode("Patient has TB symptoms")
            >>> embedding.shape  # tuple: (384,)
            (384,)
            >>> embeddings: np.ndarray = embedder.encode(["Text 1", "Text 2"])
            >>> embeddings.shape  # tuple: (2, 384)
            (2, 384)
        """
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
        """
        Generate embeddings with associated metadata.
        
        Useful for ingestion pipeline where each text chunk has metadata
        (form name, subject ID, etc.).
        
        Args:
            texts: List of text strings to encode
            metadata: List of metadata dicts (same length as texts)
            normalize_embeddings: Normalize embeddings to unit length
        
        Returns:
            List of dicts with 'text', 'embedding', and 'metadata' keys
        
        Example:
            >>> from typing import List, Dict
            >>> embedder = EmbeddingModel()
            >>> texts = ["Patient A has cough", "Patient B has fever"]
            >>> metadata = [{"subject_id": "SUBJ_001"}, {"subject_id": "SUBJ_002"}]
            >>> results: List[Dict] = embedder.encode_batch_with_metadata(texts, metadata)
            >>> list(results[0].keys())  # List[str]
            ['text', 'embedding', 'metadata']
        """
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
        """
        Calculate similarity between two texts or embeddings.
        
        For normalized embeddings, dot product is mathematically equivalent to
        cosine similarity: cos_sim(a,b) = dot(a,b) when ||a|| = ||b|| = 1.
        This follows the official SentenceTransformer recommendation for
        efficient pairwise similarity computation.
        
        Args:
            text1: Text string or embedding array
            text2: Text string or embedding array
            metric: Similarity metric ('cosine' or 'dot')
        
        Returns:
            Similarity score (0 to 1 for cosine, -1 to 1 for dot product)
        
        Example:
            >>> embedder = EmbeddingModel()
            >>> sim: float = embedder.get_similarity("TB symptoms", "cough and fever")
            >>> f"{sim:.3f}"  # str: similarity score
            '0.742'
        
        Note:
            This implementation uses NumPy's dot product for optimal performance
            in pairwise similarity computation. For batch similarity matrices,
            consider using sentence_transformers.util.cos_sim() directly.
        """
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
    """
    Factory function to get default embedding model.
    
    Args:
        use_biomedical: Use biomedical model instead of general-purpose model
        **kwargs: Additional arguments passed to EmbeddingModel
    
    Returns:
        Initialized EmbeddingModel instance
    
    Example:
        >>> embedder = get_default_embedder()
        >>> embedder.model_name  # str: model name
        'sentence-transformers/all-MiniLM-L6-v2'
        >>> bio_embedder = get_default_embedder(use_biomedical=True)
        >>> bio_embedder.model_name  # str: biomedical model
        'pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb'
    """
    model_name = (
        EmbeddingModel.BIOMEDICAL_MODEL if use_biomedical 
        else EmbeddingModel.DEFAULT_MODEL
    )
    
    logger.info(
        f"Creating default embedder: "
        f"{'Biomedical' if use_biomedical else 'General-purpose'}"
    )
    
    return EmbeddingModel(model_name=model_name, **kwargs)
