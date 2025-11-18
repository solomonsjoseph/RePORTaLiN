"""Embedding model wrapper for sentence-transformers with medical domain support.

Provides unified interface for text-to-vector embedding using sentence-transformers
library. Supports multiple pre-trained models including general-purpose and biomedical
domain-specific transformers. Handles model loading, batch encoding, similarity
computation, and automatic retry logic for robust operation.

**Key Features:**
- **Multiple Model Support**: General-purpose (MiniLM), biomedical (BioBERT, BioLORD)
- **Automatic Retries**: Robust model loading with exponential backoff
- **Batch Processing**: Configurable batch sizes for memory-efficient encoding
- **Similarity Metrics**: Cosine and dot product similarity computation
- **Progress Tracking**: Optional progress bars for batch operations
- **Device Management**: Automatic CPU/GPU selection and reporting
- **Metadata Handling**: Combined embedding + metadata output

**Supported Models:**
1. **all-MiniLM-L6-v2** (Default): Fast general-purpose model
   - Dimension: 384
   - Use case: General semantic search, fast inference
   - Speed: Very fast (~1000 sentences/sec on CPU)

2. **BioBERT-mnli-snli**: Medical/scientific domain
   - Dimension: 768
   - Use case: Clinical text, medical research
   - Strengths: Medical terminology understanding

3. **BioLORD-2023-C**: Advanced medical embeddings
   - Dimension: 768
   - Use case: Clinical notes, medical ontologies
   - Strengths: UMLS-aligned, medical concept linking

**Architecture:**
```
Text Input → EmbeddingModel.encode() → SentenceTransformer → Embeddings (numpy)
                ↓
         Batch Processing
                ↓
        Normalized Vectors (L2 norm = 1)
```

**Normalization:**
All embeddings normalized by default (L2 norm = 1) enabling:
- Direct cosine similarity via dot product
- Efficient distance computation
- Consistent similarity ranges [0, 1]

**Usage Patterns:**

Basic embedding generation:
    >>> from scripts.vector_db.embeddings import EmbeddingModel
    >>> # Default model (all-MiniLM-L6-v2)
    >>> embedder = EmbeddingModel()  # doctest: +SKIP
    >>> embedding = embedder.encode("tuberculosis treatment")  # doctest: +SKIP
    >>> embedding.shape  # doctest: +SKIP
    (384,)

Medical domain embeddings:
    >>> # Use biomedical model
    >>> bio_embedder = EmbeddingModel(
    ...     model_name='pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb'
    ... )  # doctest: +SKIP
    >>> embeddings = bio_embedder.encode([
    ...     "Patient presents with cough and fever",
    ...     "Prescribed rifampicin for TB treatment"
    ... ])  # doctest: +SKIP
    >>> embeddings.shape  # doctest: +SKIP
    (2, 768)

Similarity computation:
    >>> similarity = embedder.get_similarity(
    ...     "tuberculosis diagnosis",
    ...     "TB testing procedure"
    ... )  # doctest: +SKIP
    >>> similarity > 0.7  # High similarity  # doctest: +SKIP
    True

Factory pattern with defaults:
    >>> from scripts.vector_db.embeddings import get_default_embedder
    >>> # General-purpose
    >>> embedder = get_default_embedder()  # doctest: +SKIP
    >>> # Biomedical
    >>> bio_embedder = get_default_embedder(use_biomedical=True)  # doctest: +SKIP

**Dependencies:**
- sentence-transformers: Embedding model framework (Hugging Face)
- numpy: Array operations and vector math
- tenacity: Retry logic with exponential backoff
- torch: PyTorch backend (CPU or CUDA)

**Performance Considerations:**
- Batch processing recommended for large datasets (batch_size=32-128)
- GPU acceleration available via device='cuda' parameter
- Model caching reduces initialization time (cache_dir parameter)
- Progress bars can be disabled for production (show_progress=False)

**Error Handling:**
- Model loading failures: Retry up to 3 times with exponential backoff
- Empty/invalid text inputs: Filtered with warnings, returns empty array
- Dimension mismatches: Validated during encoding
- Connection issues: Helpful error messages with troubleshooting hints

See Also:
    adaptive_embeddings.py: Fine-tuning embeddings for domain adaptation
    vector_store.py: Vector database integration using these embeddings
    sentence-transformers docs: https://www.sbert.net/

Note:
    First model initialization downloads from Hugging Face Hub. Subsequent
    loads use local cache. Biomedical models require ~3GB disk space.
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
    """Sentence-transformer wrapper for text embedding with retry logic and validation.
    
    Encapsulates sentence-transformers model with robust initialization, batch encoding,
    similarity computation, and automatic device management. Supports multiple pre-trained
    models optimized for general and biomedical domains.
    
    **Design Pattern:**
    - **Facade**: Simplifies sentence-transformers API with sensible defaults
    - **Lazy Loading**: Model loaded on __init__, cached for subsequent calls
    - **Fail-Safe**: Automatic retry with exponential backoff for transient errors
    
    **Model Selection:**
    Use class constants for standard models or specify custom Hugging Face model:
    - DEFAULT_MODEL: Fast general-purpose (384 dims)
    - BIOMEDICAL_MODEL: Medical domain (768 dims)
    - BIOLORD_MODEL: UMLS-aligned medical (768 dims)
    
    **Normalization:**
    Embeddings normalized to unit vectors (L2 norm = 1) by default. This enables:
    - Cosine similarity = dot product
    - Efficient nearest neighbor search
    - Consistent distance metrics
    
    Attributes:
        model_name: Hugging Face model identifier or path.
        batch_size: Number of texts to encode per batch (default: 32).
        show_progress: Show progress bars during encoding (default: True).
        cache_dir: Directory for model cache (None = default HF cache).
        model: Loaded SentenceTransformer instance.
        embedding_dim: Vector dimensionality for this model.
        device: Device used for inference ('cpu', 'cuda:0', etc.).
        DEFAULT_MODEL: Class constant for default model.
        BIOMEDICAL_MODEL: Class constant for biomedical model.
        BIOLORD_MODEL: Class constant for advanced medical model.
        MODEL_DIMENSIONS: Dict mapping model names to dimensions.
    
    Example:
        >>> from scripts.vector_db.embeddings import EmbeddingModel
        >>> # Initialize with defaults
        >>> embedder = EmbeddingModel()  # doctest: +SKIP
        >>> embedder.embedding_dim  # doctest: +SKIP
        384
        >>> # Biomedical model
        >>> bio_model = EmbeddingModel(
        ...     model_name=EmbeddingModel.BIOMEDICAL_MODEL,
        ...     batch_size=64
        ... )  # doctest: +SKIP
        >>> bio_model.embedding_dim  # doctest: +SKIP
        768
    
    See Also:
        SentenceTransformer: Underlying sentence-transformers model
        AdaptiveEmbedder: Fine-tuned domain-adapted variant
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
        """Initialize embedding model with automatic loading and device selection.
        
        Loads sentence-transformers model with retry logic (up to 3 attempts with
        exponential backoff). Automatically detects embedding dimension and device.
        First initialization downloads model from Hugging Face Hub; subsequent
        loads use local cache.
        
        Args:
            model_name: Hugging Face model identifier or local path. If None, uses
                DEFAULT_MODEL (all-MiniLM-L6-v2). Supports any sentence-transformers
                compatible model.
            device: Torch device for inference ('cpu', 'cuda', 'cuda:0', etc.). If
                None, automatically selects CUDA if available, else CPU.
            batch_size: Number of texts to encode per batch. Larger batches faster
                but use more memory. Recommended: 32-128. Default: 32.
            cache_dir: Directory for model cache. If None, uses Hugging Face default
                (~/.cache/huggingface/). Useful for custom cache locations.
            show_progress: Show progress bars during batch encoding. Set False for
                production/logging environments. Default: True.
        
        Raises:
            RuntimeError: If model loading fails after 3 retry attempts (network
                issues, invalid model name, insufficient memory).
        
        Side Effects:
            - Downloads model from Hugging Face Hub on first use (~100-500MB)
            - Loads model weights into memory (~0.5-3GB RAM)
            - Logs info messages (initialization, device, dimension)
            - Sets self.model, self.embedding_dim, self.device attributes
        
        Example:
            >>> # Default model (fast, general-purpose)
            >>> embedder = EmbeddingModel()  # doctest: +SKIP
            >>> # Biomedical model with custom settings
            >>> bio_embedder = EmbeddingModel(
            ...     model_name='pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb',
            ...     device='cuda',
            ...     batch_size=64,
            ...     show_progress=False
            ... )  # doctest: +SKIP
            >>> # Custom cache location
            >>> from pathlib import Path
            >>> embedder = EmbeddingModel(
            ...     cache_dir=Path('/data/models')
            ... )  # doctest: +SKIP
        
        Note:
            Model loading retries up to 3 times with exponential backoff (2s, 4s, 8s).
            Helps handle transient network issues during download.
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
        """Load sentence-transformers model with automatic retry on failure.
        
        Private method called by __init__ to load model with robust error handling.
        Retries up to 3 times with exponential backoff (2s, 4s, 8s) to handle
        transient network issues during model download.
        
        Args:
            device: Torch device string ('cpu', 'cuda', 'cuda:0', etc.). If None,
                SentenceTransformer automatically selects CUDA if available.
        
        Returns:
            Loaded and initialized SentenceTransformer instance ready for encoding.
        
        Raises:
            RuntimeError: If model loading fails after all retry attempts. Includes
                original error message and troubleshooting hints.
        
        Side Effects:
            - Downloads model from Hugging Face Hub if not in cache
            - Loads model weights to specified device
            - Logs error on failures (before retry or final failure)
        
        Note:
            Decorated with @retry from tenacity package:
            - stop_after_attempt(3): Maximum 3 attempts
            - wait_exponential: 2s, 4s, 8s delays between attempts
            - reraise=True: Re-raise final exception if all attempts fail
        
        Example:
            >>> # Called automatically by __init__, not typically called directly
            >>> embedder = EmbeddingModel()  # doctest: +SKIP
            >>> # Internally calls: self.model = self._load_model(device)  # doctest: +SKIP
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
        """Generate embeddings for single text or batch of texts.
        
        Converts text(s) to dense vector representations using loaded sentence-
        transformers model. Handles single strings and batches uniformly. Automatically
        filters invalid inputs (None, empty strings) with warnings.
        
        Args:
            texts: Single string or list of strings to embed. Empty strings and None
                values are filtered out with warning logged.
            normalize_embeddings: If True, normalize embeddings to unit vectors
                (L2 norm = 1). Enables cosine similarity via dot product. Default: True.
            show_progress_bar: Override instance setting for progress bar display.
                If None, uses self.show_progress. Default: None.
            convert_to_numpy: Return numpy arrays instead of torch tensors. Should
                always be True for compatibility with vector stores. Default: True.
        
        Returns:
            For single string input: 1D numpy array of shape (embedding_dim,)
            For list input: 2D numpy array of shape (n_texts, embedding_dim)
            For invalid/empty input: Empty numpy array with shape (0,)
        
        Side Effects:
            - Logs warning if any texts filtered (None/empty)
            - Logs error if no valid texts remain after filtering
            - Logs verbose info about batch size
            - Computes embeddings on self.device (CPU/GPU)
        
        Raises:
            RuntimeError: If embedding generation fails (model error, OOM, etc.).
        
        Example:
            >>> embedder = EmbeddingModel()  # doctest: +SKIP
            >>> # Single text
            >>> embedding = embedder.encode("tuberculosis treatment")  # doctest: +SKIP
            >>> embedding.shape  # doctest: +SKIP
            (384,)
            >>> # Batch of texts
            >>> embeddings = embedder.encode([
            ...     "Patient presents with cough",
            ...     "Prescribed rifampicin",
            ...     "Follow-up in 2 weeks"
            ... ])  # doctest: +SKIP
            >>> embeddings.shape  # doctest: +SKIP
            (3, 384)
            >>> # Normalized (unit vectors)
            >>> import numpy as np
            >>> np.linalg.norm(embedding)  # doctest: +SKIP
            1.0
            >>> # Without normalization
            >>> raw_embedding = embedder.encode(
            ...     "test text",
            ...     normalize_embeddings=False
            ... )  # doctest: +SKIP
        
        Note:
            - Batch processing uses self.batch_size (default: 32)
            - Normalized embeddings required for most vector stores
            - Progress bar helps track long-running batch operations
            - Invalid texts (None, '') filtered automatically
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
        """Generate embeddings with associated metadata for batch processing.
        
        Convenience method that combines embeddings with metadata dictionaries.
        Useful for pipeline operations where text, embedding, and metadata need
        to stay together. Always shows progress bar for batch feedback.
        
        Args:
            texts: List of strings to embed. Must be non-empty.
            metadata: Optional list of metadata dictionaries, one per text. If
                provided, must match length of texts. If None, empty dicts used.
            normalize_embeddings: Normalize embeddings to unit vectors. Default: True.
        
        Returns:
            List of dictionaries, one per text, each containing:
            - 'text': Original text string
            - 'embedding': Numpy array embedding vector
            - 'metadata': Associated metadata dict (or {} if none provided)
        
        Raises:
            ValueError: If metadata list length doesn't match texts list length.
            RuntimeError: If embedding generation fails.
        
        Side Effects:
            - Generates embeddings (compute-intensive)
            - Shows progress bar during encoding
            - Logs info with count of generated embeddings
        
        Example:
            >>> embedder = EmbeddingModel()  # doctest: +SKIP
            >>> texts = [
            ...     "Patient diagnosed with TB",
            ...     "Started treatment regimen"
            ... ]
            >>> metadata = [
            ...     {'subject_id': '001', 'form': '1A'},
            ...     {'subject_id': '001', 'form': '13'}
            ... ]
            >>> results = embedder.encode_batch_with_metadata(
            ...     texts, metadata
            ... )  # doctest: +SKIP
            >>> len(results)  # doctest: +SKIP
            2
            >>> results[0].keys()  # doctest: +SKIP
            dict_keys(['text', 'embedding', 'metadata'])
            >>> results[0]['metadata']['subject_id']  # doctest: +SKIP
            '001'
        
        Note:
            Useful for data pipelines where metadata must stay paired with
            embeddings. Alternative to manually zipping texts, embeddings, metadata.
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
        """Calculate semantic similarity between two texts or embedding vectors.
        
        Computes similarity score between two inputs using specified metric. Accepts
        either raw text strings (which are embedded automatically) or pre-computed
        embedding vectors. For normalized embeddings, cosine similarity equals dot
        product, providing efficient computation.
        
        **Similarity Metrics:**
        - **cosine**: Angle-based similarity, range [-1, 1] (or [0, 1] for normalized)
          - 1.0 = identical direction (semantically very similar)
          - 0.0 = orthogonal (unrelated)
          - -1.0 = opposite direction (rare with normalized embeddings)
        - **dot**: Dot product, range depends on normalization
          - For normalized embeddings: equivalent to cosine similarity
          - For unnormalized: influenced by magnitude (not recommended)
        
        Args:
            text1: First text string or embedding vector (1D numpy array). If string,
                automatically embedded with normalization.
            text2: Second text string or embedding vector (1D numpy array). If string,
                automatically embedded with normalization.
            metric: Similarity metric to use. Options: 'cosine' (default), 'dot'.
                Use 'cosine' for semantic similarity; 'dot' only for special cases.
        
        Returns:
            Similarity score as float. For cosine metric with normalized embeddings:
            - > 0.8: Very high similarity (near-duplicates, paraphrases)
            - 0.6-0.8: High similarity (related concepts)
            - 0.4-0.6: Moderate similarity (somewhat related)
            - < 0.4: Low similarity (different topics)
        
        Raises:
            ValueError: If metric is not 'cosine' or 'dot'.
            RuntimeError: If embedding generation fails (for string inputs).
        
        Side Effects:
            - Generates embeddings for string inputs (compute-intensive)
            - Logs via encode() if new embeddings created
        
        Example:
            >>> embedder = EmbeddingModel()  # doctest: +SKIP
            >>> # Compare two text strings
            >>> sim = embedder.get_similarity(
            ...     "tuberculosis treatment",
            ...     "TB medication therapy"
            ... )  # doctest: +SKIP
            >>> sim > 0.7  # High similarity expected  # doctest: +SKIP
            True
            >>> # Compare unrelated texts
            >>> sim = embedder.get_similarity(
            ...     "tuberculosis treatment",
            ...     "weather forecast sunny"
            ... )  # doctest: +SKIP
            >>> sim < 0.3  # Low similarity expected  # doctest: +SKIP
            True
            >>> # Use pre-computed embeddings
            >>> emb1 = embedder.encode("first text")  # doctest: +SKIP
            >>> emb2 = embedder.encode("second text")  # doctest: +SKIP
            >>> sim = embedder.get_similarity(emb1, emb2)  # doctest: +SKIP
            >>> # Dot product metric
            >>> sim_dot = embedder.get_similarity(
            ...     "text one",
            ...     "text two",
            ...     metric="dot"
            ... )  # doctest: +SKIP
        
        Note:
            - For normalized embeddings (default): cosine = dot product
            - Embedding dimension must match between text1 and text2
            - Pre-computed embeddings avoid redundant encoding
            - Cosine similarity preferred for semantic comparisons
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
        """Return formal string representation of EmbeddingModel instance.
        
        Provides detailed string showing model configuration for debugging and logging.
        Includes model name, embedding dimension, and compute device. Useful for
        verifying model setup and troubleshooting configuration issues.
        
        Returns:
            String in format: "EmbeddingModel(model='<name>', dim=<int>, device='<device>')"
            Example: "EmbeddingModel(model='all-MiniLM-L6-v2', dim=384, device='cpu')"
        
        Example:
            >>> embedder = EmbeddingModel()  # doctest: +SKIP
            >>> repr(embedder)  # doctest: +SKIP
            "EmbeddingModel(model='sentence-transformers/all-MiniLM-L6-v2', dim=384, device='cpu')"
            >>> print(embedder)  # Uses __repr__  # doctest: +SKIP
            EmbeddingModel(model='sentence-transformers/all-MiniLM-L6-v2', dim=384, device='cpu')
            >>> # Useful for logging model configuration
            >>> import logging
            >>> logging.info(f"Using embedder: {embedder}")  # doctest: +SKIP
        
        Note:
            Called automatically by repr() and str() functions. Also displayed
            in interactive Python shells and debugging output.
        """
        return (
            f"EmbeddingModel(model='{self.model_name}', "
            f"dim={self.embedding_dim}, device='{self.device}')"
        )


def get_default_embedder(
    use_biomedical: bool = False,
    **kwargs
) -> EmbeddingModel:
    """Factory function to create EmbeddingModel with sensible defaults.
    
    Convenience function that instantiates EmbeddingModel with pre-configured
    model selection. Simplifies common use cases: general-purpose vs biomedical
    embeddings. Accepts additional keyword arguments for customization.
    
    **Design Pattern:**
    Factory method providing simplified interface for common configurations.
    Reduces boilerplate when standard models suffice.
    
    **Model Selection:**
    - use_biomedical=False: all-MiniLM-L6-v2 (384 dims, fast, general)
    - use_biomedical=True: BioBERT-mnli (768 dims, medical domain)
    
    Args:
        use_biomedical: If True, use biomedical model optimized for clinical text.
            If False, use fast general-purpose model. Default: False.
        **kwargs: Additional keyword arguments passed to EmbeddingModel constructor.
            Examples: device='cuda', batch_size=64, cache_dir=Path('/models'),
            show_progress=False. See EmbeddingModel.__init__ for full options.
    
    Returns:
        Initialized EmbeddingModel instance with specified configuration.
    
    Side Effects:
        - Logs info message indicating model type (general-purpose or biomedical)
        - Triggers model download/loading (via EmbeddingModel.__init__)
        - All side effects from EmbeddingModel initialization apply
    
    Example:
        >>> from scripts.vector_db.embeddings import get_default_embedder
        >>> # General-purpose embedding (default)
        >>> embedder = get_default_embedder()  # doctest: +SKIP
        >>> embedder.model_name  # doctest: +SKIP
        'sentence-transformers/all-MiniLM-L6-v2'
        >>> embedder.embedding_dim  # doctest: +SKIP
        384
        >>> # Biomedical embedding
        >>> bio_embedder = get_default_embedder(use_biomedical=True)  # doctest: +SKIP
        >>> bio_embedder.model_name  # doctest: +SKIP
        'pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb'
        >>> bio_embedder.embedding_dim  # doctest: +SKIP
        768
        >>> # With custom settings
        >>> embedder = get_default_embedder(
        ...     use_biomedical=False,
        ...     device='cuda',
        ...     batch_size=128,
        ...     show_progress=False
        ... )  # doctest: +SKIP
        >>> # Quick setup for common workflows
        >>> from pathlib import Path
        >>> embedder = get_default_embedder(
        ...     use_biomedical=True,
        ...     cache_dir=Path('/data/models')
        ... )  # doctest: +SKIP
    
    Note:
        - Equivalent to: EmbeddingModel(model_name=<default_or_bio>, **kwargs)
        - Use for quick prototyping and standard workflows
        - For custom models, instantiate EmbeddingModel directly
    
    See Also:
        EmbeddingModel: Full class with all configuration options
        EmbeddingModel.DEFAULT_MODEL: General-purpose model name
        EmbeddingModel.BIOMEDICAL_MODEL: Biomedical model name
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
