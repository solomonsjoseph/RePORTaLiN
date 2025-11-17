"""Text chunking strategies for JSONL records."""

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
    """Text chunk with metadata."""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    chunk_index: int = 0
    source_file: Optional[str] = None
    chunk_strategy: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "token_count": self.token_count,
            "chunk_index": self.chunk_index,
            "source_file": self.source_file,
            "chunk_strategy": self.chunk_strategy
        }
    
    def __repr__(self) -> str:
        """String representation of chunk."""
        return (
            f"TextChunk(tokens={self.token_count}, "
            f"strategy='{self.chunk_strategy}', "
            f"index={self.chunk_index})"
        )


class TextChunker:
    """Text chunking for JSONL records with multiple strategies."""
    
    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 150,
        strategy: str = "hybrid",
        encoding_name: str = "cl100k_base"
    ):
        """Initialize text chunker with specified parameters."""
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
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def json_to_natural_language(
        self,
        record: Dict[str, Any],
        include_entity_prefix: bool = True,
        entity_id_fields: Optional[List[str]] = None
    ) -> str:
        """Convert JSON record to natural language sentence."""
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
        """Convert field names to readable format."""
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
        """Recursively flatten nested dictionary to natural language."""
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
        """Chunk a single JSONL record using specified strategy."""
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
        """Chunk text by semantic boundaries preserving sentence structure."""
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
        """Chunk text with fixed size and overlap using RecursiveCharacterTextSplitter."""
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
        """Hybrid chunking combining semantic boundaries with size limits."""
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
        """Chunk all records from a JSONL file."""
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
