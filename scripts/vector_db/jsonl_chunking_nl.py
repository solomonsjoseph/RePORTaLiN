"""Natural language text extraction and chunking for JSONL clinical research records.

Converts structured JSON records to human-readable natural language text and chunks
for semantic search and vector database ingestion. Designed for clinical research
datasets (patient records, lab results, forms) with intelligent field name humanization,
type-aware formatting, and adaptive chunking strategies (semantic, fixed-size, hybrid).

**Architecture:**
```
JSON Record → NL Conversion → Text Chunking → TextChunk Objects
     ↓             ↓                ↓              ↓
 Structured    Field name      Semantic/     Metadata
 data          humanization    Fixed/        preservation
                               Hybrid
```

**Key Features:**

- **JSON-to-NL Conversion**: Transforms structured JSON to readable sentences
- **Field Name Humanization**: Converts technical names (HC_SMOKHX → "Smoking history")
- **Type-Aware Formatting**: Handles booleans, numbers, lists, nested dicts, NaN/Inf
- **Entity Detection**: Auto-identifies patients, orders, sensors from ID fields
- **Adaptive Chunking**: Three strategies (semantic, fixed, hybrid)
- **Token-Aware**: Uses tiktoken for accurate token counting (OpenAI models)
- **Clinical Domain Support**: Extensive clinical abbreviation mappings

**Chunking Strategies:**

1. **Semantic** (sentence-boundary preservation):
   - Splits at sentence boundaries (periods)
   - Preserves complete sentences
   - Respects chunk_size limits
   - Best for: Maintaining readability and context

2. **Fixed** (RecursiveCharacterTextSplitter):
   - Fixed token-size chunks with overlap
   - Uses LangChain's recursive splitter
   - Splits on: \\n\\n, \\n, ., ,, space
   - Best for: Consistent chunk sizes, maximum coverage

3. **Hybrid** (semantic + fixed fallback):
   - Primary: Semantic chunking
   - Fallback: Fixed splitting for oversized chunks
   - Best for: Balance between readability and size control
   - **Default and recommended**

**JSON-to-NL Conversion Logic:**

Transformation rules:
1. **Entity Identification**: Detects SUBJID, patient_id, etc. → "Patient 12345"
2. **Field Humanization**: HC_SMOKHX → "Smoking history", DOB → "Date of birth"
3. **Type Handling**:
   - Booleans: True/False → "Yes"/"No"
   - Floats: Rounded to 2 decimals, NaN → "Not Available"
   - Lists: Comma-separated (max 10 items), empty values filtered
   - Nested dicts: Recursively flattened
4. **Sentence Construction**: "Field: Value. Field: Value. ..."
5. **Metadata Filtering**: Skips _id, recordid, empty values

Example conversion:
```json
{
  "SUBJID": "12345",
  "IC_AGE": 45,
  "IC_SEX": "M",
  "TB_COUGH": true,
  "LAB_RESULT": "negative"
}
```
→
```
"Patient 12345. Age: 45. Sex: M. Cough: Yes. Laboratory result: negative."
```

**Field Name Humanization:**

Built-in mappings (extensible):
- **Clinical**: HC_SMOKHX → "Smoking history", TB_FEVER → "Fever"
- **Common**: DOB → "Date of birth", SSN → "Social security number"
- **Technical**: Removes HC_, IC_, TB_, LAB_ prefixes
- **Conventions**: camelCase → Title Case, underscores → spaces

**Performance Characteristics:**

Typical processing rates (CPU):
- **NL Conversion**: ~1,000-5,000 records/second (depends on record complexity)
- **Token Counting**: ~10,000 texts/second (tiktoken)
- **Semantic Chunking**: ~500-2,000 records/second
- **Fixed Chunking**: ~1,000-3,000 records/second (LangChain overhead)
- **Hybrid Chunking**: ~500-2,000 records/second

For 10,000 records (~100 fields/record average):
- NL conversion: ~2-10 seconds
- Chunking (hybrid): ~5-20 seconds
- Total: ~7-30 seconds

**Usage Patterns:**

Basic NL conversion:
    >>> from scripts.vector_db.jsonl_chunking_nl import TextChunker
    >>> chunker = TextChunker()  # doctest: +SKIP
    >>> record = {
    ...     "SUBJID": "12345",
    ...     "IC_AGE": 45,
    ...     "TB_COUGH": True,
    ...     "LAB_RESULT": "negative"
    ... }
    >>> nl_text = chunker.json_to_natural_language(record)  # doctest: +SKIP
    >>> print(nl_text)  # doctest: +SKIP
    Patient 12345. Age: 45. Cough: Yes. Laboratory result: negative.

Chunk single record:
    >>> chunker = TextChunker(chunk_size=512, strategy='hybrid')  # doctest: +SKIP
    >>> chunks = chunker.chunk_record(record, source_file='screening.jsonl')  # doctest: +SKIP
    >>> for chunk in chunks:
    ...     print(f"{chunk.chunk_index}: {chunk.token_count} tokens")  # doctest: +SKIP

Chunk entire JSONL file:
    >>> from pathlib import Path
    >>> chunker = TextChunker(strategy='semantic')  # doctest: +SKIP
    >>> jsonl_path = Path('output/deidentified/Indo-VAP/cleaned/screening.jsonl')
    >>> all_chunks = chunker.chunk_jsonl_file(jsonl_path)  # doctest: +SKIP
    >>> print(f"Total chunks: {len(all_chunks)}")  # doctest: +SKIP

Custom chunking parameters:
    >>> chunker = TextChunker(
    ...     chunk_size=1024,
    ...     chunk_overlap=200,
    ...     strategy='hybrid',
    ...     encoding_name='cl100k_base'
    ... )  # doctest: +SKIP

Token counting:
    >>> text = "Patient demographics: age 45, sex male."
    >>> token_count = chunker.count_tokens(text)  # doctest: +SKIP
    >>> print(f"Tokens: {token_count}")  # doctest: +SKIP

**Dependencies:**
- tiktoken: Fast token counting (OpenAI tokenizer)
- langchain_text_splitters: RecursiveCharacterTextSplitter for fixed chunking
- logging_system: Centralized logging with verbose mode

**Error Handling:**
- ValueError: Invalid chunk_size (≤0), chunk_overlap (< 0 or ≥ chunk_size), strategy
- RuntimeError: tiktoken encoding loading failure
- FileNotFoundError: JSONL file doesn't exist (chunk_jsonl_file)
- JSONDecodeError: Malformed JSONL lines (logged, skipped)
- Exception: Generic record processing errors (logged, skipped)

**Configuration:**

Initialization parameters:
- chunk_size: Max tokens per chunk (default: 1024)
- chunk_overlap: Overlap between chunks (default: 150)
- strategy: 'semantic', 'fixed', or 'hybrid' (default: 'hybrid')
- encoding_name: Tokenizer encoding (default: 'cl100k_base' for OpenAI)

NL conversion options (json_to_natural_language):
- include_entity_prefix: Add "Patient 12345" prefix (default: True)
- entity_id_fields: Custom ID field priority list (default: auto-detect)

See Also:
    ingest_records.py: Batch JSONL ingestion to vector database
    vector_store.py: Vector database storage for chunks
    embeddings.py: Embedding generation for chunks

Note:
    tiktoken required for token counting—raises RuntimeError if unavailable.
    Field name humanization is clinical-domain focused but extensible via
    _humanize_field_name(). NaN/Inf handling for robust numeric field processing.
    Empty/None values auto-filtered from NL output. Large text fields (>500 chars)
    truncated with "...". Nested dicts recursively flattened.
"""

import json
import math
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from scripts.utils import logging_system as log

logger = log.get_logger(__name__)
vlog = log.get_verbose_logger()


@dataclass
class TextChunk:
    """Text chunk with metadata for vector database storage.
    
    Represents a chunked piece of text with associated metadata, token count,
    and strategy information. Base class for PDFChunk (in pdf_chunking.py).
    Used throughout vector DB pipeline for consistent chunk representation.
    
    Attributes:
        text (str): Chunk text content (natural language).
        metadata (Dict[str, Any]): User-provided metadata (form_name, subject_id, etc.).
            Default: {} (empty dict).
        token_count (int): Number of tokens in text (counted via tiktoken).
            Default: 0.
        chunk_index (int): Sequential chunk index within source (0-based).
            Default: 0.
        source_file (Optional[str]): Source filename (e.g., 'screening.jsonl').
            Default: None.
        chunk_strategy (str): Chunking strategy used ('semantic', 'fixed', 'hybrid').
            Default: "unknown".
    
    Example:
        Create text chunk:
            >>> from scripts.vector_db.jsonl_chunking_nl import TextChunk
            >>> chunk = TextChunk(
            ...     text="Patient 12345. Age: 45. Sex: M.",
            ...     metadata={'form_name': 'screening', 'subject_id': '12345'},
            ...     token_count=12,
            ...     chunk_index=0,
            ...     source_file='screening.jsonl',
            ...     chunk_strategy='hybrid'
            ... )
            >>> chunk.text
            'Patient 12345. Age: 45. Sex: M.'
            >>> chunk.token_count
            12
        
        Serialize to dict:
            >>> chunk_dict = chunk.to_dict()
            >>> chunk_dict['chunk_strategy']
            'hybrid'
            >>> chunk_dict['metadata']['subject_id']
            '12345'
        
        String representation:
            >>> print(chunk)
            TextChunk(tokens=12, strategy='hybrid', index=0)
    
    Note:
        Extended by PDFChunk in pdf_chunking.py (adds page_number, folder_path,
        form_code, form_title). Metadata dict is mutable—copy before modifying
        if sharing across chunks. token_count should match encoding used in
        TextChunker (cl100k_base by default).
    """
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    chunk_index: int = 0
    source_file: Optional[str] = None
    chunk_strategy: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for JSON serialization and vector database storage.
        
        Serializes all TextChunk attributes to a flat dictionary suitable for
        JSON serialization. Used by vector database ingestion pipeline for
        metadata storage alongside embeddings.
        
        Returns:
            Dict[str, Any]: Dictionary with all chunk attributes:
                - text (str): Chunk text content
                - metadata (Dict): User metadata
                - token_count (int): Token count
                - chunk_index (int): Sequential index
                - source_file (str|None): Source filename
                - chunk_strategy (str): Chunking method
        
        Example:
            Serialize for storage:
                >>> chunk = TextChunk(
                ...     text="Sample text",
                ...     metadata={'form': 'test'},
                ...     token_count=5,
                ...     chunk_index=0,
                ...     source_file='test.jsonl',
                ...     chunk_strategy='fixed'
                ... )
                >>> d = chunk.to_dict()
                >>> d['text']
                'Sample text'
                >>> d['token_count']
                5
                >>> d['metadata']
                {'form': 'test'}
        
        Note:
            Result is JSON-serializable (all values are basic Python types).
            Metadata dict is included as-is (not copied). Used by VectorStore
            for metadata storage.
        """
        return {
            "text": self.text,
            "metadata": self.metadata,
            "token_count": self.token_count,
            "chunk_index": self.chunk_index,
            "source_file": self.source_file,
            "chunk_strategy": self.chunk_strategy
        }
    
    def __repr__(self) -> str:
        """String representation of chunk for debugging and logging.
        
        Returns concise, readable representation showing key attributes
        (token count, strategy, index). Used in log messages and REPL output.
        
        Returns:
            str: Formatted string "TextChunk(tokens=X, strategy='Y', index=Z)"
        
        Example:
            Display chunk info:
                >>> chunk = TextChunk(
                ...     text="Sample",
                ...     token_count=50,
                ...     chunk_index=3,
                ...     chunk_strategy='semantic'
                ... )
                >>> repr(chunk)
                "TextChunk(tokens=50, strategy='semantic', index=3)"
                >>> print(chunk)
                TextChunk(tokens=50, strategy='semantic', index=3)
        
        Note:
            Doesn't include text content (may be large). Shows only key metrics
            for quick inspection.
        """
        return (
            f"TextChunk(tokens={self.token_count}, "
            f"strategy='{self.chunk_strategy}', "
            f"index={self.chunk_index})"
        )


class TextChunker:
    """Natural language text extraction and adaptive chunking for JSONL records.
    
    Converts structured JSON records to human-readable natural language text and
    chunks using adaptive strategies (semantic, fixed, hybrid). Designed for clinical
    research datasets with intelligent field name humanization, type-aware formatting,
    and tiktoken-based token counting. Core component of JSONL ingestion pipeline.
    
    **Capabilities:**
    - **JSON-to-NL**: Transforms structured data to readable sentences
    - **Field Humanization**: HC_SMOKHX → "Smoking history", DOB → "Date of birth"
    - **Type Handling**: Booleans, numbers (NaN/Inf), lists, nested dicts
    - **Entity Detection**: Auto-identifies patients, orders, sensors
    - **Adaptive Chunking**: Semantic (sentence boundaries), fixed (token-limited), hybrid
    - **Token Counting**: Accurate tiktoken counting for OpenAI models
    
    **Chunking Strategies:**
    - **semantic**: Preserves sentence boundaries, best for readability
    - **fixed**: Token-limited chunks with overlap, uses LangChain RecursiveCharacterTextSplitter
    - **hybrid** (default): Semantic primary, fixed fallback for oversized chunks
    
    Attributes:
        chunk_size (int): Maximum tokens per chunk.
        chunk_overlap (int): Overlap between chunks in tokens.
        strategy (str): Default chunking strategy ('semantic', 'fixed', 'hybrid').
        encoding (tiktoken.Encoding): Tokenizer encoding for token counting.
        text_splitter (RecursiveCharacterTextSplitter): LangChain splitter for fixed chunking.
    
    Example:
        Basic usage:
            >>> from scripts.vector_db.jsonl_chunking_nl import TextChunker
            >>> chunker = TextChunker()  # doctest: +SKIP
            >>> record = {'SUBJID': '12345', 'IC_AGE': 45, 'TB_COUGH': True}
            >>> nl_text = chunker.json_to_natural_language(record)  # doctest: +SKIP
            >>> chunks = chunker.chunk_record(record)  # doctest: +SKIP
        
        Custom configuration:
            >>> chunker = TextChunker(
            ...     chunk_size=512,
            ...     chunk_overlap=100,
            ...     strategy='semantic',
            ...     encoding_name='cl100k_base'
            ... )  # doctest: +SKIP
        
        Chunk JSONL file:
            >>> from pathlib import Path
            >>> chunks = chunker.chunk_jsonl_file(
            ...     Path('data/screening.jsonl'),
            ...     max_records=100
            ... )  # doctest: +SKIP
    
    Note:
        Requires tiktoken and langchain_text_splitters installed. Field name
        humanization is clinical-domain focused but extensible. NaN/Inf handling
        for robust numeric processing. Large text fields (>500 chars) truncated.
    """
    
    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 150,
        strategy: str = "hybrid",
        encoding_name: str = "cl100k_base"
    ):
        """Initialize text chunker with chunking configuration and tokenizer.
        
        Validates parameters, loads tiktoken encoding, and initializes LangChain
        RecursiveCharacterTextSplitter for fixed/hybrid chunking. Raises errors
        for invalid configuration.
        
        Args:
            chunk_size (int, optional): Maximum tokens per chunk. Affects semantic
                search granularity. Smaller = more precise, larger = more context.
                Must be > 0. Default: 1024.
            chunk_overlap (int, optional): Overlap between consecutive chunks in
                tokens. Helps preserve context across boundaries. Must be >= 0 and
                < chunk_size. Default: 150.
            strategy (str, optional): Default chunking strategy. Options:
                - 'semantic': Sentence-boundary preservation
                - 'fixed': Token-limited with RecursiveCharacterTextSplitter
                - 'hybrid': Semantic primary, fixed fallback (recommended)
                Default: 'hybrid'.
            encoding_name (str, optional): tiktoken encoding name. Must match
                embedding model's tokenizer. Common: 'cl100k_base' (OpenAI),
                'p50k_base' (GPT-3), 'r50k_base' (GPT-2). Default: 'cl100k_base'.
        
        Raises:
            ValueError: If chunk_size <= 0, chunk_overlap < 0 or >= chunk_size,
                or strategy not in ['fixed', 'semantic', 'hybrid'].
            RuntimeError: If tiktoken encoding fails to load (encoding_name invalid
                or tiktoken not installed).
        
        Example:
            Default initialization:
                >>> from scripts.vector_db.jsonl_chunking_nl import TextChunker
                >>> chunker = TextChunker()  # doctest: +SKIP
                >>> chunker.chunk_size  # doctest: +SKIP
                1024
                >>> chunker.strategy  # doctest: +SKIP
                'hybrid'
            
            Custom configuration:
                >>> chunker = TextChunker(
                ...     chunk_size=512,
                ...     chunk_overlap=50,
                ...     strategy='semantic'
                ... )  # doctest: +SKIP
            
            Error handling:
                >>> try:
                ...     chunker = TextChunker(chunk_size=-100)  # doctest: +SKIP
                ... except ValueError as e:
                ...     print(f"Error: {e}")  # doctest: +SKIP
                Error: chunk_size must be positive, got -100
        
        Side Effects:
            - Loads tiktoken encoding (downloads ~500KB-2MB on first use)
            - Initializes LangChain RecursiveCharacterTextSplitter
            - Logs initialization message (info level)
        
        Note:
            text_splitter uses approximate token-to-char conversion (1 token ≈ 4 chars)
            for LangChain compatibility. Actual token counting via count_tokens()
            uses tiktoken directly. Encoding download cached in ~/.tiktoken/ for
            subsequent uses. Splitter separators: \\n\\n, \\n, ., ,, space, empty.
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap must be >= 0 and < chunk_size, "
                f"got overlap={chunk_overlap}, size={chunk_size}"
            )
        if strategy not in ["fixed", "semantic", "hybrid"]:
            raise ValueError(
                f"Invalid strategy '{strategy}'. "
                f"Must be 'fixed', 'semantic', or 'hybrid'"
            )
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.error(f"Failed to load tiktoken encoding '{encoding_name}': {e}")
            raise RuntimeError(f"Could not load tokenizer: {e}")
        
        # Initialize RecursiveCharacterTextSplitter for fixed/hybrid strategies
        # Convert token counts to approximate character counts (rough estimate: 1 token ≈ 4 chars)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,  # Approximate conversion
            chunk_overlap=chunk_overlap * 4,
            length_function=self.count_tokens,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
        
        logger.info(
            f"TextChunker initialized: size={chunk_size} tokens, "
            f"overlap={chunk_overlap} tokens, strategy='{strategy}'"
        )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken encoding.
        
        Fast, accurate token counting for OpenAI-compatible models. Used internally
        for chunk validation and externally for pre-ingestion token analysis.
        
        Args:
            text (str): Text to count tokens in. Can be empty.
        
        Returns:
            int: Number of tokens in text. Returns 0 for empty/None text.
        
        Example:
            Count tokens:
                >>> from scripts.vector_db.jsonl_chunking_nl import TextChunker
                >>> chunker = TextChunker()  # doctest: +SKIP
                >>> text = "Patient demographics: age 45, sex male."
                >>> count = chunker.count_tokens(text)  # doctest: +SKIP
                >>> print(f"Tokens: {count}")  # doctest: +SKIP
                Tokens: 9
            
            Empty text:
                >>> chunker.count_tokens("")  # doctest: +SKIP
                0
        
        Note:
            Uses self.encoding (tiktoken.Encoding) loaded during __init__.
            Performance: ~10,000 texts/second on typical hardware. Token count
            may differ slightly from other tokenizers (e.g., BERT, GPT-2).
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def json_to_natural_language(
        self,
        record: Dict[str, Any],
        include_entity_prefix: bool = True,
        entity_id_fields: Optional[List[str]] = None
    ) -> str:
        """Convert structured JSON record to human-readable natural language sentence.
        
        Transforms clinical research JSON records into readable text for semantic
        search and embedding. Handles entity identification, field name humanization,
        type-aware formatting, and sentence construction. Core NL extraction method.
        
        **Transformation Logic:**
        1. Entity ID Detection: Identifies subject/patient/order ID from field names
        2. Field Humanization: Converts technical names to readable labels
        3. Type Handling: Booleans → Yes/No, floats → 2 decimals, NaN → "Not Available"
        4. List/Dict Processing: Flattens nested structures, limits list length
        5. Sentence Construction: "Field: Value. Field: Value. ..."
        6. Filtering: Skips metadata fields (_id, recordid), empty/None values
        
        Args:
            record (Dict[str, Any]): JSON record to convert. Can be empty (returns "").
            include_entity_prefix (bool, optional): If True, prepends entity identifier
                (e.g., "Patient 12345") to output. If False, starts with first field.
                Default: True.
            entity_id_fields (Optional[List[str]], optional): Priority list of field
                names to check for entity ID. If None, uses built-in defaults:
                [SUBJID, subject_id, SubjID, patient_id, order_id, etc.].
                Default: None (auto-detect).
        
        Returns:
            str: Natural language text with period-separated sentences. Empty string
                if record empty or all values filtered out.
        
        Example:
            Basic conversion (clinical record):
                >>> from scripts.vector_db.jsonl_chunking_nl import TextChunker
                >>> chunker = TextChunker()  # doctest: +SKIP
                >>> record = {
                ...     "SUBJID": "12345",
                ...     "IC_AGE": 45,
                ...     "IC_SEX": "M",
                ...     "TB_COUGH": True,
                ...     "TB_FEVER": False,
                ...     "LAB_RESULT": "negative"
                ... }
                >>> text = chunker.json_to_natural_language(record)  # doctest: +SKIP
                >>> print(text)  # doctest: +SKIP
                Patient 12345. Age: 45. Sex: M. Cough: Yes. Fever: No. Laboratory result: negative.
            
            Without entity prefix:
                >>> text = chunker.json_to_natural_language(
                ...     record,
                ...     include_entity_prefix=False
                ... )  # doctest: +SKIP
                >>> print(text)  # doctest: +SKIP
                Age: 45. Sex: M. Cough: Yes. Fever: No. Laboratory result: negative.
            
            Custom entity ID fields:
                >>> record = {"custom_id": "ABC123", "status": "active"}
                >>> text = chunker.json_to_natural_language(
                ...     record,
                ...     entity_id_fields=["custom_id"]
                ... )  # doctest: +SKIP
                >>> print(text)  # doctest: +SKIP
                Record ABC123. Status: active.
            
            Type handling examples:
                >>> import math
                >>> record = {
                ...     "boolean_field": True,
                ...     "float_field": 3.14159,
                ...     "nan_field": float('nan'),
                ...     "list_field": [1, 2, 3],
                ...     "nested_dict": {"sub_field": "value"}
                ... }
                >>> text = chunker.json_to_natural_language(record, include_entity_prefix=False)  # doctest: +SKIP
                >>> # Output: Boolean Field: Yes. Float Field: 3.14. Nan Field: Not Available. ...
        
        Side Effects:
            - Calls _humanize_field_name() for all field names
            - Calls _flatten_dict_to_nl() for nested dictionaries
            - Truncates text fields > 500 chars with "..."
            - Limits lists to first 10 items with "..."
        
        Performance:
            Typical rates (CPU):
            - Simple records (~10 fields): ~5,000 records/second
            - Complex records (~100 fields, nested): ~1,000 records/second
            - Lists/nested dicts add ~10-20% overhead
        
        Note:
            Entity type inferred from ID field name: "patient"/"subj" → "Patient",
            "order" → "Order", "sensor"/"device" → "Sensor", etc. Booleans checked
            BEFORE int (bool is int subclass in Python). NaN/Inf handled via math
            module. Empty/None values filtered automatically. Nested dicts recursively
            flattened. Lists comma-separated (max 10 items). Text > 500 chars truncated.
        """
        if not record:
            return ""
        
        sentences = []
        
        # Default ID field patterns (order matters - try most specific first)
        default_id_fields = [
            "SUBJID", "subject_id", "SubjID", "patient_id", "PatientID",
            "order_id", "OrderID", "transaction_id", "TransactionID",
            "sensor_id", "SensorID", "device_id", "DeviceID",
            "user_id", "UserID", "customer_id", "CustomerID",
            "record_id", "RecordID", "ID", "id", "_id"
        ]
        
        id_fields_to_try = entity_id_fields or default_id_fields
        
        # Extract entity ID and determine entity type
        entity_id = None
        entity_type = "Record"  # Default
        id_field_used = None
        
        for field_name in id_fields_to_try:
            if field_name in record and record[field_name]:
                entity_id = record[field_name]
                id_field_used = field_name
                
                # Infer entity type from field name
                field_lower = field_name.lower()
                if "patient" in field_lower or "subj" in field_lower:
                    entity_type = "Patient"
                elif "order" in field_lower:
                    entity_type = "Order"
                elif "sensor" in field_lower or "device" in field_lower:
                    entity_type = "Sensor"
                elif "user" in field_lower or "customer" in field_lower:
                    entity_type = "User"
                elif "transaction" in field_lower:
                    entity_type = "Transaction"
                
                break
        
        # Add entity identifier prefix if requested
        if include_entity_prefix and entity_id:
            sentences.append(f"{entity_type} {entity_id}")
        
        # Process each field
        for key, value in record.items():
            # Skip ID fields (already processed)
            if id_field_used and key == id_field_used:
                continue
            
            # Skip common metadata fields that don't add semantic value
            if key.lower() in ["_id", "id", "recordid", "record_id", "index", "row_number"]:
                continue
            
            # Skip empty/null values
            if value is None or value == "":
                continue
            
            # Skip very large text fields (truncate if needed)
            if isinstance(value, str) and len(value) > 500:
                value = value[:500] + "..."
            
            # Humanize field name
            readable_key = self._humanize_field_name(key)
            
            # Handle different value types
            # IMPORTANT: Check bool BEFORE int, since bool is a subclass of int
            if isinstance(value, bool):
                # Boolean values
                sentences.append(f"{readable_key}: {'Yes' if value else 'No'}")
            
            elif isinstance(value, dict):
                # Nested dictionary - recursively flatten
                nested_text = self._flatten_dict_to_nl(value)
                if nested_text:
                    sentences.append(f"{readable_key}: {nested_text}")
            
            elif isinstance(value, list):
                # List - join elements (limit to first 10 items)
                if len(value) > 10:
                    list_values = value[:10]
                    list_text = ", ".join(str(v) for v in list_values if v) + "..."
                else:
                    list_text = ", ".join(str(v) for v in value if v)
                
                if list_text:
                    sentences.append(f"{readable_key}: {list_text}")
            
            elif isinstance(value, (int, float)):
                # Numeric values - format appropriately
                # Check for NaN and infinity using math module
                if isinstance(value, float) and math.isnan(value):
                    # Handle NaN
                    formatted_value = "Not Available"
                elif isinstance(value, float) and math.isinf(value):
                    # Handle infinity
                    formatted_value = "Infinity" if value > 0 else "-Infinity"
                elif isinstance(value, float):
                    # Round floats to 2 decimal places for readability
                    formatted_value = f"{value:.2f}" if value != int(value) else str(int(value))
                else:
                    # Integer values
                    formatted_value = str(value)
                sentences.append(f"{readable_key}: {formatted_value}")
            
            else:
                # Simple value (string, etc.)
                sentences.append(f"{readable_key}: {value}")
        
        # Join into coherent sentence
        if not sentences:
            return ""
        
        return ". ".join(sentences) + "."
    
    def _humanize_field_name(self, field_name: str) -> str:
        """Convert technical field names to human-readable labels.
        
        Transforms database/technical field names into user-friendly labels using
        built-in abbreviation mappings (clinical + common) and naming convention
        transformations (camelCase, snake_case → Title Case). Extensible via
        abbrev_map dictionaries.
        
        **Transformation Rules:**
        1. Exact match check (HC_SMOKHX → "Smoking history")
        2. Prefix match (HC_SMOKHX_DATE → "Smoking history Date")
        3. Remove technical prefixes (HC_, IC_, TB_, tbl, dim_, fact_)
        4. camelCase → Title Case (patientName → Patient Name)
        5. snake_case → Title Case (patient_name → Patient Name)
        6. Preserve acronyms (ID, URL, API, JSON, etc.)
        
        Args:
            field_name (str): Technical field name to humanize. Can be empty.
        
        Returns:
            str: Human-readable label. Empty string for empty input.
        
        Example:
            Clinical abbreviations:
                >>> chunker._humanize_field_name("HC_SMOKHX")  # doctest: +SKIP
                'Smoking history'
                >>> chunker._humanize_field_name("TB_COUGH")  # doctest: +SKIP
                'Cough'
                >>> chunker._humanize_field_name("LAB_RESULT")  # doctest: +SKIP
                'Result'
            
            Common abbreviations:
                >>> chunker._humanize_field_name("DOB")  # doctest: +SKIP
                'Date of birth'
                >>> chunker._humanize_field_name("ZIP")  # doctest: +SKIP
                'ZIP code'
            
            Naming conventions:
                >>> chunker._humanize_field_name("patientName")  # doctest: +SKIP
                'Patient Name'
                >>> chunker._humanize_field_name("patient_name")  # doctest: +SKIP
                'Patient Name'
        
        Note:
            Private method (leading underscore). Clinical abbreviation map includes
            ~15 common clinical fields. Common abbreviation map includes ~12 general
            terms. Acronyms preserved in uppercase (ID, URL, API, etc.). Prefix
            removal supports clinical (HC_, IC_, TB_) and database (tbl, dim_, fact_).
        """
        if not field_name:
            return ""
        
        # Domain-specific abbreviation mappings (extensible)
        # Clinical domain
        clinical_abbrev = {
            "HC_SMOKHX": "Smoking history",
            "HC_MARISTAT": "Marital status",
            "IC_AGE": "Age",
            "IC_SEX": "Sex",
            "IC_DOB": "Date of birth",
            "TB_SYMPTOMS": "TB symptoms",
            "TB_COUGH": "Cough",
            "TB_FEVER": "Fever",
            "TB_WEIGHT": "Weight",
            "HIV_STATUS": "HIV status",
            "LAB_RESULT": "Laboratory result",
            "SPECIMEN_TYPE": "Specimen type",
            "VISIT_DATE": "Visit date",
            "ENROL_DATE": "Enrollment date",
        }
        
        # Common abbreviations across domains
        common_abbrev = {
            "ID": "ID",
            "URL": "URL",
            "API": "API",
            "HTTP": "HTTP",
            "JSON": "JSON",
            "XML": "XML",
            "CSV": "CSV",
            "PDF": "PDF",
            "DOB": "Date of birth",
            "SSN": "Social security number",
            "ZIP": "ZIP code",
            "QTY": "Quantity",
            "AMT": "Amount",
            "NUM": "Number",
            "PCT": "Percentage",
        }
        
        # Combine all abbreviation maps
        abbrev_map = {**clinical_abbrev, **common_abbrev}
        
        # Check for exact match first
        if field_name in abbrev_map:
            return abbrev_map[field_name]
        
        # Check for prefix matches (for clinical fields like HC_SMOKHX_DATE)
        for abbrev, readable in abbrev_map.items():
            if field_name.startswith(abbrev + "_") or field_name.startswith(abbrev):
                suffix = field_name[len(abbrev):].lstrip("_")
                if suffix:
                    suffix_readable = self._humanize_field_name(suffix)
                    return f"{readable} {suffix_readable}".strip()
                return readable
        
        # Handle different naming conventions
        cleaned = field_name
        
        # Remove common technical prefixes (for clinical/domain-specific data)
        for prefix in ["HC_", "IC_", "TB_", "LAB_", "HIV_", "SUBJ_", "tbl", "dim_", "fact_"]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        # Convert camelCase or PascalCase to spaces
        # Insert space before uppercase letters that follow lowercase letters
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
        
        # Replace underscores with spaces
        cleaned = cleaned.replace("_", " ")
        
        # Replace hyphens with spaces
        cleaned = cleaned.replace("-", " ")
        
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Title case (capitalize first letter of each word)
        cleaned = cleaned.strip().title()
        
        # Preserve common acronyms in uppercase
        words = cleaned.split()
        result_words = []
        for word in words:
            word_upper = word.upper()
            if word_upper in common_abbrev.values() or word_upper in ["ID", "URL", "API", "HTTP", "JSON", "XML", "CSV", "PDF", "ZIP", "SSN"]:
                result_words.append(word_upper)
            else:
                result_words.append(word)
        
        return " ".join(result_words)
    
    def _flatten_dict_to_nl(self, d: Dict[str, Any], parent_key: str = "") -> str:
        """Recursively flatten nested dictionary to natural language (internal helper).
        
        Converts nested dictionary structures into period-separated sentences.
        Used by json_to_natural_language() for handling nested dict values.
        Recursively processes sub-dictionaries and formats lists/values.
        
        Args:
            d (Dict[str, Any]): Dictionary to flatten. Can be nested.
            parent_key (str, optional): Parent key name (for recursion).
                Default: "" (top-level).
        
        Returns:
            str: Period-separated natural language sentences. Empty if all values
                filtered out (None, empty strings).
        
        Example:
            Flatten nested dict (internal usage):
                >>> # Inside json_to_natural_language():
                >>> # nested_text = self._flatten_dict_to_nl({"address": {"city": "NYC"}})
                >>> # Result: "Address: City: NYC"  # doctest: +SKIP
        
        Note:
            Private method. Recursively calls itself for nested dicts. Handles
            lists (comma-separated), None/empty values (filtered). parent_key
            unused in current implementation (reserved for future use).
        """
        parts = []
        
        for key, value in d.items():
            readable_key = self._humanize_field_name(key)
            
            if isinstance(value, dict):
                nested = self._flatten_dict_to_nl(value, readable_key)
                if nested:
                    parts.append(nested)
            
            elif isinstance(value, list):
                list_text = ", ".join(str(v) for v in value if v)
                if list_text:
                    parts.append(f"{readable_key}: {list_text}")
            
            elif value is not None and value != "":
                parts.append(f"{readable_key}: {value}")
        
        return ". ".join(parts)
    
    def chunk_record(
        self,
        record: Dict[str, Any],
        strategy: Optional[str] = None,
        source_file: Optional[str] = None
    ) -> List[TextChunk]:
        """Chunk a single JSONL record using specified strategy.
        
        Main entry point for single-record chunking. Converts JSON to NL text,
        extracts metadata (form_name, subject_id, record_id), and applies chunking
        strategy. Returns list of TextChunk objects ready for embedding.
        
        Args:
            record (Dict[str, Any]): JSON record to chunk. Can be empty (returns []).
            strategy (Optional[str], optional): Chunking strategy override
                ('semantic', 'fixed', 'hybrid'). If None, uses self.strategy.
                Default: None (use __init__ strategy).
            source_file (Optional[str], optional): Source filename for metadata.
                If None, uses "unknown". Default: None.
        
        Returns:
            List[TextChunk]: List of text chunks with metadata. Empty list if
                json_to_natural_language() returns empty text or record empty.
        
        Example:
            Chunk single record (default strategy):
                >>> chunker = TextChunker(strategy='hybrid')  # doctest: +SKIP
                >>> record = {"SUBJID": "12345", "IC_AGE": 45, "TB_COUGH": True}
                >>> chunks = chunker.chunk_record(record, source_file='screening.jsonl')  # doctest: +SKIP
                >>> for chunk in chunks:
                ...     print(f"Chunk {chunk.chunk_index}: {chunk.token_count} tokens")  # doctest: +SKIP
            
            Override strategy:
                >>> chunks = chunker.chunk_record(record, strategy='semantic')  # doctest: +SKIP
        
        Side Effects:
            - Calls json_to_natural_language() for NL conversion
            - Calls chunking strategy method (_chunk_semantic/_chunk_fixed/_chunk_hybrid)
            - Logs warning if NL text empty (verbose mode)
            - Logs chunk count (verbose mode)
        
        Note:
            Metadata extracted: form_name, subject_id (from SUBJID/SubjID/subject_id),
            record_id (from record_id/RecordID/ID/id), source_file. Metadata copied
            to each chunk. Empty text results in empty list with warning.
        """
        strategy = strategy or self.strategy
        
        # Extract metadata
        metadata = {
            "form_name": record.get("form_name", "unknown"),
            "subject_id": record.get("subject_id", record.get("SubjID", "unknown")),
            "source_file": source_file or "unknown"
        }
        
        # Add any other ID fields
        for id_field in ["record_id", "RecordID", "ID", "id"]:
            if id_field in record:
                metadata["record_id"] = record[id_field]
                break
        
        # Convert record to text
        text = self.json_to_natural_language(record)
        
        if not text:
            logger.warning(f"Empty text after converting record: {metadata}")
            return []
        
        # Apply chunking strategy
        if strategy == "semantic":
            chunks = self._chunk_semantic(text, metadata)
        elif strategy == "fixed":
            chunks = self._chunk_fixed(text, metadata)
        else:  # hybrid
            chunks = self._chunk_hybrid(text, metadata)
        
        vlog(
            f"Chunked record from {metadata['form_name']} "
            f"into {len(chunks)} chunks using '{strategy}' strategy"
        )
        
        return chunks
    
    def _chunk_semantic(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[TextChunk]:
        """Chunk text by sentence boundaries (semantic chunking, internal).
        
        Splits text at sentence boundaries (periods) while respecting chunk_size
        limits. Preserves complete sentences for readability. Accumulates sentences
        until chunk_size reached, then starts new chunk.
        
        Args:
            text (str): NL text to chunk.
            metadata (Dict[str, Any]): Metadata to include in all chunks.
        
        Returns:
            List[TextChunk]: Sentence-boundary chunks with strategy='semantic'.
        
        Example:
            Internal usage:
                >>> # Called by chunk_record() when strategy='semantic'
                >>> # chunks = self._chunk_semantic(text, metadata)  # doctest: +SKIP
        
        Note:
            Private method. Splits on ". " (period + space). Re-adds periods to
            sentences. Creates new chunk when next sentence would exceed chunk_size.
            Metadata copied (not shared) across chunks.
        """
        # Split on sentence boundaries (periods followed by space)
        sentences = text.split(". ")
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # Add period back if not at end
            sentence = sentence.strip()
            if sentence and not sentence.endswith("."):
                sentence += "."
            
            # Check if adding this sentence would exceed chunk size
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            token_count = self.count_tokens(test_chunk)
            
            if token_count <= self.chunk_size:
                # Add to current chunk
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(TextChunk(
                        text=current_chunk.strip(),
                        metadata=metadata.copy(),
                        token_count=self.count_tokens(current_chunk),
                        chunk_index=chunk_index,
                        source_file=metadata.get("source_file"),
                        chunk_strategy="semantic"
                    ))
                    chunk_index += 1
                
                # Start new chunk with current sentence
                current_chunk = sentence
        
        # Don't forget last chunk
        if current_chunk:
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                metadata=metadata.copy(),
                token_count=self.count_tokens(current_chunk),
                chunk_index=chunk_index,
                source_file=metadata.get("source_file"),
                chunk_strategy="semantic"
            ))
        
        return chunks
    
    def _chunk_fixed(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[TextChunk]:
        """Chunk text with fixed size and overlap using RecursiveCharacterTextSplitter (internal).
        
        Uses LangChain's RecursiveCharacterTextSplitter for token-limited chunks
        with overlap. Splits recursively on separators: \\n\\n, \\n, ., ,, space.
        Ensures consistent chunk sizes for embedding.
        
        Args:
            text (str): NL text to chunk.
            metadata (Dict[str, Any]): Metadata to include in all chunks.
        
        Returns:
            List[TextChunk]: Fixed-size chunks with strategy='fixed'.
        
        Example:
            Internal usage:
                >>> # Called by chunk_record() when strategy='fixed'
                >>> # chunks = self._chunk_fixed(text, metadata)  # doctest: +SKIP
        
        Note:
            Private method. Uses self.text_splitter (initialized in __init__).
            Splitter configured with chunk_size * 4 (token→char approximation) but
            uses count_tokens() for actual length function. Metadata copied across chunks.
        """
        # Use langchain's splitter
        text_chunks = self.text_splitter.split_text(text)
        
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunks.append(TextChunk(
                text=chunk_text.strip(),
                metadata=metadata.copy(),
                token_count=self.count_tokens(chunk_text),
                chunk_index=idx,
                source_file=metadata.get("source_file"),
                chunk_strategy="fixed"
            ))
        
        return chunks
    
    def _chunk_hybrid(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[TextChunk]:
        """Hybrid chunking: semantic primary, fixed fallback for oversized chunks (internal).
        
        Combines semantic and fixed strategies: first tries semantic chunking, then
        splits any oversized chunks (> chunk_size) using fixed strategy. Best of
        both worlds: readability + size control. Default recommended strategy.
        
        Args:
            text (str): NL text to chunk.
            metadata (Dict[str, Any]): Metadata to include in all chunks.
        
        Returns:
            List[TextChunk]: Hybrid chunks with strategy='hybrid'.
        
        Example:
            Internal usage:
                >>> # Called by chunk_record() when strategy='hybrid' (default)
                >>> # chunks = self._chunk_hybrid(text, metadata)  # doctest: +SKIP
        
        Side Effects:
            - Calls _chunk_semantic() first
            - Calls _chunk_fixed() for oversized chunks
            - Logs when splitting oversized chunks (verbose mode)
        
        Note:
            Private method. Checks each semantic chunk's token_count. If > chunk_size,
            re-chunks with _chunk_fixed(). chunk_index re-assigned sequentially across
            all final chunks. Recommended for balanced readability and size control.
        """
        # First try semantic chunking
        semantic_chunks = self._chunk_semantic(text, metadata)
        
        # Check if any chunks are too large and need splitting
        final_chunks = []
        chunk_index = 0
        
        for chunk in semantic_chunks:
            if chunk.token_count <= self.chunk_size:
                # Chunk is fine, keep it
                chunk.chunk_index = chunk_index
                chunk.chunk_strategy = "hybrid"
                final_chunks.append(chunk)
                chunk_index += 1
            else:
                # Chunk is too large, split it with fixed strategy
                vlog(
                    f"Semantic chunk too large ({chunk.token_count} tokens), "
                    f"splitting with fixed strategy"
                )
                sub_chunks = self._chunk_fixed(chunk.text, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_index = chunk_index
                    sub_chunk.chunk_strategy = "hybrid"
                    final_chunks.append(sub_chunk)
                    chunk_index += 1
        
        return final_chunks
    
    def chunk_jsonl_file(
        self,
        jsonl_path: Union[str, Path],
        strategy: Optional[str] = None,
        max_records: Optional[int] = None
    ) -> List[TextChunk]:
        """Chunk all records from a JSONL file with batch processing and error handling.
        
        Batch processes JSONL file line-by-line. Calls chunk_record() for each record
        and accumulates chunks. Continues on individual record errors (logs and skips).
        Returns flat list of all chunks across all records.
        
        Args:
            jsonl_path (Union[str, Path]): Path to JSONL file. Must exist.
            strategy (Optional[str], optional): Chunking strategy override
                ('semantic', 'fixed', 'hybrid'). If None, uses self.strategy.
                Default: None (use __init__ strategy).
            max_records (Optional[int], optional): Maximum records to process.
                Useful for testing. If None, processes all records. Default: None.
        
        Returns:
            List[TextChunk]: Flat list of all chunks from all records. Empty if
                no records successfully chunked or file empty.
        
        Raises:
            FileNotFoundError: If jsonl_path doesn't exist.
            JSONDecodeError: Per-line errors (logged and skipped, not raised).
            Exception: Per-record processing errors (logged and skipped, not raised).
        
        Example:
            Chunk entire file:
                >>> from pathlib import Path
                >>> chunker = TextChunker(strategy='hybrid')  # doctest: +SKIP
                >>> jsonl_path = Path('output/deidentified/Indo-VAP/cleaned/screening.jsonl')
                >>> all_chunks = chunker.chunk_jsonl_file(jsonl_path)  # doctest: +SKIP
                >>> print(f"Total chunks: {len(all_chunks)}")  # doctest: +SKIP
                Total chunks: 1523
            
            Limit records for testing:
                >>> chunks = chunker.chunk_jsonl_file(jsonl_path, max_records=100)  # doctest: +SKIP
            
            Override strategy:
                >>> chunks = chunker.chunk_jsonl_file(jsonl_path, strategy='semantic')  # doctest: +SKIP
        
        Side Effects:
            - Reads entire JSONL file from disk (line-by-line, not all at once)
            - Calls chunk_record() for each record
            - Logs start message (info level)
            - Logs max_records limit message if reached (info level)
            - Logs per-line errors (error level, continues processing)
            - Logs summary (record count, chunk count) (info level)
        
        Performance:
            Typical rates (CPU, hybrid strategy):
            - Simple records (~10 fields): ~1,000-2,000 records/second
            - Complex records (~100 fields): ~500-1,000 records/second
            - 10,000 records: ~5-20 seconds
        
        Note:
            Errors in individual records don't stop processing—logs error and continues
            to next line. max_records stops after N successful records (doesn't count
            skipped lines). Returns flat list (not grouped by record). source_file
            metadata set to jsonl_path.name for all chunks.
        """
        jsonl_path = Path(jsonl_path)
        
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        logger.info(f"Chunking JSONL file: {jsonl_path}")
        
        all_chunks = []
        record_count = 0
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if max_records and record_count >= max_records:
                    logger.info(f"Reached max_records limit: {max_records}")
                    break
                
                try:
                    record = json.loads(line)
                    chunks = self.chunk_record(
                        record,
                        strategy=strategy,
                        source_file=jsonl_path.name
                    )
                    all_chunks.extend(chunks)
                    record_count += 1
                    
                except json.JSONDecodeError as e:
                    logger.error(
                        f"JSON decode error in {jsonl_path} line {line_num}: {e}"
                    )
                    continue
                except Exception as e:
                    logger.error(
                        f"Error chunking record in {jsonl_path} line {line_num}: {e}"
                    )
                    continue
        
        logger.info(
            f"Chunked {record_count} records from {jsonl_path.name} "
            f"into {len(all_chunks)} chunks"
        )
        
        return all_chunks
