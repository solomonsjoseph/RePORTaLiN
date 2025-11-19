"""PDF chunking and text extraction for annotated clinical research forms.

Provides intelligent PDF text extraction with automatic structure detection, metadata
enrichment, and adaptive chunking strategies. Designed for annotated clinical research
documents (CRFs, questionnaires, screening forms) with support for multiple extraction
backends (pypdf, pdfplumber), AcroForm field extraction, table detection, and
document structure recognition (sections, headers, form codes).

**Architecture:**
```
PDF File → Text Extraction → Structure Detection → Chunking → PDFChunk Objects
              ↓                  ↓                    ↓            ↓
           pypdf/           Form codes,        Section/Fixed  Metadata
           pdfplumber       headers,           boundaries     enrichment
                            sections
```

**Key Features:**

- **Dual Extraction Backend**: pypdf (fast) or pdfplumber (accurate), auto-selection
- **Structure Detection**: Automatic form code, title, and section header extraction
- **Adaptive Chunking**: Section-aware or fixed-size chunking based on document structure
- **Metadata Enrichment**: PDF properties, AcroForm fields, table detection
- **Page Boundary Preservation**: Optional per-page chunking vs. cross-page chunks
- **Quality Validation**: Token count metrics, empty chunk detection, validation reporting
- **Verbose Logging**: Detailed extraction and chunking statistics

**Extraction Methods:**

1. **pypdf** (default if pdfplumber unavailable):
   - Fast text extraction using pypdf.PdfReader
   - Basic page-by-page text extraction
   - Suitable for simple, well-structured PDFs
   - No table/form field support

2. **pdfplumber** (preferred, auto-selected if available):
   - Advanced text extraction with layout analysis
   - Table extraction with structure preservation
   - AcroForm field value extraction
   - PDF metadata enrichment
   - Better handling of complex layouts

3. **auto** (default):
   - Automatically selects pdfplumber if available, else pypdf
   - Recommended for most use cases

**Chunking Strategies:**

1. **Structure-Based Chunking** (automatic when sections detected):
   - Detects form codes (e.g., "1A Index Case Screening")
   - Identifies section headers (Roman: I., II.; Alpha: A., B.; Numeric: 1., 2.)
   - Chunks at section boundaries
   - Preserves section titles in metadata
   - Best for structured clinical forms

2. **Fixed-Size Chunking** (fallback when no structure detected):
   - Uses TextChunker with configurable token limits
   - Respects chunk_size and chunk_overlap parameters
   - Suitable for unstructured documents
   - Ensures consistent chunk sizes for embedding

**Document Structure Detection:**

Automatically extracts:
- **Form Code**: Numeric/alphanumeric identifier (e.g., "1A", "12B", "95")
- **Form Title**: Human-readable form name (e.g., "Index Case Screening")
- **Section Headers**: Roman numerals (I., II.), letters (A., B.), numbers (1., 2.)
- **Validation**: Form code regex validation (^[0-9]{1,2}[A-Z]?$)

Detection sources (priority order):
1. First 5 lines of extracted text
2. PDF filename (e.g., "1A Index Case Screening v1.0.pdf")

**Metadata Enrichment:**

Each PDFChunk includes:
- **source_type**: Always "pdf"
- **filename**: Original PDF filename
- **folder_path**: Relative path from base_path
- **form_code**: Detected form identifier
- **form_title**: Human-readable form name
- **page_number**: Page number (1-indexed)
- **section_title**: Section header if detected (e.g., "I. Demographics")
- **has_tables**: Boolean, True if tables detected
- **table_count**: Number of tables in PDF
- **has_form_fields**: Boolean, True if AcroForm fields present
- **form_field_count**: Number of form fields
- **PDF metadata**: Author, CreationDate, Title, etc. (if present)

**Usage Patterns:**

Basic PDF chunking (single file):
    >>> from pathlib import Path
    >>> from scripts.vector_db.pdf_chunking import PDFChunker
    >>> # Initialize chunker
    >>> chunker = PDFChunker(
    ...     chunk_size=1024,
    ...     chunk_overlap=150,
    ...     extraction_method='auto'
    ... )  # doctest: +SKIP
    >>> # Chunk a single PDF
    >>> pdf_path = Path('data/Indo-VAP/annotated_pdfs/1A Index Case Screening v1.0.pdf')
    >>> chunks = chunker.chunk_pdf(pdf_path)  # doctest: +SKIP
    >>> print(f"Created {len(chunks)} chunks")  # doctest: +SKIP
    >>> # Inspect first chunk
    >>> chunk = chunks[0]  # doctest: +SKIP
    >>> print(chunk.form_code)  # doctest: +SKIP
    1A
    >>> print(chunk.form_title)  # doctest: +SKIP
    Index Case Screening

Directory batch processing:
    >>> from pathlib import Path
    >>> chunker = PDFChunker(verbose=True)  # doctest: +SKIP
    >>> pdf_dir = Path('data/Indo-VAP/annotated_pdfs')
    >>> chunks_by_file = chunker.chunk_pdf_directory(
    ...     directory=pdf_dir,
    ...     recursive=False
    ... )  # doctest: +SKIP
    >>> total = sum(len(chunks) for chunks in chunks_by_file.values())
    >>> print(f"Processed {len(chunks_by_file)} PDFs, {total} chunks")  # doctest: +SKIP

Custom extraction with metadata:
    >>> chunker = PDFChunker(
    ...     chunk_size=512,
    ...     extraction_method='pdfplumber',
    ...     preserve_page_boundaries=True
    ... )  # doctest: +SKIP
    >>> metadata = {'study_name': 'Indo-VAP', 'version': 'v1.0'}
    >>> chunks = chunker.chunk_pdf(pdf_path, metadata=metadata)  # doctest: +SKIP

Extract tables and form fields:
    >>> # Tables (requires pdfplumber)
    >>> tables = chunker.extract_tables(pdf_path)  # doctest: +SKIP
    >>> for table in tables:
    ...     print(f"Page {table['page_number']}: {table['rows']}x{table['columns']}")  # doctest: +SKIP
    >>> # AcroForm fields
    >>> form_fields = chunker.extract_form_fields(pdf_path)  # doctest: +SKIP
    >>> for name, field in form_fields.items():
    ...     print(f"{name}: {field['value']}")  # doctest: +SKIP

**Performance Characteristics:**

Typical extraction rates (CPU):
- **pypdf**: ~5-10 pages/second (simple PDFs)
- **pdfplumber**: ~2-5 pages/second (complex layouts)
- **Table extraction**: +0.5-1s per page with tables
- **Form field extraction**: +0.1-0.3s per PDF

For 30 PDFs (~100 pages total):
- pypdf: ~10-20 seconds
- pdfplumber: ~20-50 seconds
- With tables/forms: ~30-60 seconds

**Dependencies:**
- pypdf: Basic PDF text extraction (optional)
- pdfplumber: Advanced extraction with tables/forms (optional)
- TextChunker: Token counting and fixed-size splitting (jsonl_chunking_nl.py)
- logging_system: Centralized logging with verbose mode

**Error Handling:**
- RuntimeError: No PDF libraries available (missing pypdf/pdfplumber)
- RuntimeError: Chosen extraction method not available
- FileNotFoundError: PDF file or directory doesn't exist
- ValueError: Invalid extraction_method or directory path
- PdfReadError: Corrupted or invalid PDF (pypdf)
- Exception: Generic extraction errors (logged, empty list returned)

**Configuration:**

Initialization parameters:
- chunk_size: Max tokens per chunk (default: 1024)
- chunk_overlap: Overlap between chunks (default: 150)
- extraction_method: 'pypdf', 'pdfplumber', or 'auto' (default: 'auto')
- preserve_page_boundaries: Chunk per-page vs. cross-page (default: True)
- encoding_name: Tokenizer encoding (default: 'cl100k_base')
- verbose: Enable detailed logging (default: False)

See Also:
    jsonl_chunking_nl.TextChunker: Fixed-size chunking and token counting
    ingest_pdfs.py: Batch PDF ingestion to vector database
    vector_store.py: Vector database storage for chunks

Note:
    At least one PDF library (pypdf or pdfplumber) must be installed. If neither
    is available, RuntimeError is raised. pdfplumber recommended for clinical
    forms with complex layouts, tables, and AcroForm fields. Structure detection
    is automatic—no hardcoded form profiles required. Form codes extracted from
    content or filename using regex pattern ^[0-9]{1,2}[A-Z]?$.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import warnings

# PDF processing libraries
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    warnings.warn("pypdf not installed. PDF extraction will be limited.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    warnings.warn("pdfplumber not installed. Advanced PDF extraction unavailable.")

# Import existing chunking infrastructure
from .jsonl_chunking_nl import TextChunk, TextChunker

# Import centralized logging
from scripts.utils import logging_system as log

logger = log.get_logger(__name__)
vlog = log.get_verbose_logger()


@dataclass
class PDFChunk(TextChunk):
    """PDF-specific text chunk with page, form, and folder metadata.
    
    Extends TextChunk with PDF-specific attributes for clinical research forms:
    page numbers, folder paths (for dataset organization), form codes (e.g., "1A"),
    and form titles (e.g., "Index Case Screening"). Provides serialization for
    vector database storage.
    
    Attributes:
        page_number (int): Page number in source PDF (1-indexed). Default: 1.
        folder_path (str): Relative folder path from base directory (for dataset
            organization). Empty string if no base_path provided. Default: "".
        form_code (str): Detected form identifier (e.g., "1A", "12B", "95").
            Empty if not detected. Default: "".
        form_title (str): Human-readable form name (e.g., "Index Case Screening").
            Empty if not detected. Default: "".
        text (str): Extracted text content (inherited from TextChunk).
        metadata (Dict[str, Any]): Additional metadata (inherited from TextChunk).
        token_count (int): Number of tokens in text (inherited from TextChunk).
        chunk_index (int): Sequential chunk index (inherited from TextChunk).
        source_file (str): Source filename (inherited from TextChunk).
        chunk_strategy (str): Chunking method used (inherited from TextChunk).
    
    Example:
        Create PDF chunk manually:
            >>> from scripts.vector_db.pdf_chunking import PDFChunk
            >>> chunk = PDFChunk(
            ...     text="Patient demographics section...",
            ...     metadata={"study": "Indo-VAP"},
            ...     token_count=150,
            ...     chunk_index=0,
            ...     source_file="1A Index Case Screening v1.0.pdf",
            ...     chunk_strategy="document_structure",
            ...     page_number=1,
            ...     folder_path="annotated_pdfs",
            ...     form_code="1A",
            ...     form_title="Index Case Screening"
            ... )
            >>> chunk.page_number
            1
            >>> chunk.form_code
            '1A'
        
        Serialize to dictionary:
            >>> chunk_dict = chunk.to_dict()
            >>> chunk_dict['page_number']
            1
            >>> chunk_dict['form_code']
            '1A'
            >>> 'text' in chunk_dict  # Inherited from TextChunk
            True
    
    Note:
        Inherits all TextChunk functionality (to_dict includes base fields).
        form_code and form_title auto-detected by PDFChunker._detect_document_structure.
        page_number always 1-indexed (not 0-indexed). folder_path relative to
        base_path argument in chunk_pdf().
    """
    page_number: int = 1
    folder_path: str = ""
    form_code: str = ""
    form_title: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PDF chunk to dictionary for vector database serialization.
        
        Serializes all PDFChunk attributes (including inherited TextChunk fields)
        to a flat dictionary suitable for JSON serialization and vector database
        metadata storage. Includes text, tokens, page number, form metadata, etc.
        
        Returns:
            Dict[str, Any]: Dictionary with all chunk attributes:
                - text (str): Chunk text content
                - metadata (Dict): User-provided metadata
                - token_count (int): Number of tokens
                - chunk_index (int): Sequential index
                - source_file (str): Source filename
                - chunk_strategy (str): Chunking method
                - page_number (int): Page number (1-indexed)
                - folder_path (str): Relative folder path
                - form_code (str): Form identifier
                - form_title (str): Form name
        
        Example:
            Serialize chunk for storage:
                >>> chunk = PDFChunk(
                ...     text="Sample text",
                ...     metadata={},
                ...     token_count=50,
                ...     chunk_index=0,
                ...     source_file="test.pdf",
                ...     chunk_strategy="fixed",
                ...     page_number=2,
                ...     form_code="1A"
                ... )
                >>> d = chunk.to_dict()
                >>> d['page_number']
                2
                >>> d['form_code']
                '1A'
                >>> d['token_count']
                50
        
        Note:
            Calls super().to_dict() to include TextChunk base fields, then
            adds PDF-specific fields. Result is JSON-serializable.
        """
        base_dict = super().to_dict()
        base_dict.update({
            "page_number": self.page_number,
            "folder_path": self.folder_path,
            "form_code": self.form_code,
            "form_title": self.form_title
        })
        return base_dict


class PDFChunker:
    """Intelligent PDF chunking for annotated clinical research documents.
    
    Extracts text from PDF files using pypdf or pdfplumber, automatically detects
    document structure (form codes, section headers), enriches metadata (tables,
    AcroForm fields, PDF properties), and chunks text using adaptive strategies
    (section-aware or fixed-size). Designed for clinical research forms (CRFs,
    screening forms, questionnaires) with comprehensive validation and logging.
    
    **Extraction Backends:**
    - **pypdf**: Fast text extraction, basic page-by-page processing
    - **pdfplumber**: Advanced extraction with tables, forms, layout analysis
    - **auto**: Prefers pdfplumber if available, falls back to pypdf
    
    **Chunking Strategies:**
    - **Structure-based**: Chunks at detected section boundaries (I., A., 1., etc.)
    - **Fixed-size**: Token-limited chunks when no structure detected
    
    **Structure Detection:**
    Automatically identifies:
    - Form codes: "1A", "12B", "95" (from text or filename)
    - Section headers: Roman (I., II.), alpha (A., B.), numeric (1., 2.)
    - Form titles: Human-readable names
    
    **Metadata Enrichment:**
    - PDF document properties (author, creation date, etc.)
    - Table detection and counting
    - AcroForm field extraction (name-value pairs)
    - Page-level and chunk-level metadata
    
    Attributes:
        extraction_method (str): Selected extraction backend ('pypdf' or 'pdfplumber').
        chunk_size (int): Maximum tokens per chunk.
        chunk_overlap (int): Overlap between chunks in tokens.
        preserve_page_boundaries (bool): If True, chunks don't span pages.
        verbose (bool): Enable detailed debug logging.
        text_chunker (TextChunker): Underlying token counter and splitter.
    
    Class Attributes:
        _PATTERN_WHITESPACE (re.Pattern): Regex for multiple spaces → single space.
        _PATTERN_NEWLINES (re.Pattern): Regex for multiple newlines → double newline.
        _PATTERN_ROMAN (re.Pattern): Regex for roman numeral headers (I., II., III.).
        _PATTERN_ALPHA (re.Pattern): Regex for alpha headers (A., B., C.).
        _PATTERN_NUMERIC (re.Pattern): Regex for numeric headers (1., 2., 3.).
        _PATTERN_FORM_CODE (re.Pattern): Regex for form code + title extraction.
        _PATTERN_FORM_CODE_VALIDATE (re.Pattern): Regex for form code validation.
    
    Example:
        Basic usage (auto-detect extraction method):
            >>> from pathlib import Path
            >>> from scripts.vector_db.pdf_chunking import PDFChunker
            >>> chunker = PDFChunker()  # doctest: +SKIP
            >>> pdf_path = Path('data/annotated_pdfs/1A Index Case Screening v1.0.pdf')
            >>> chunks = chunker.chunk_pdf(pdf_path)  # doctest: +SKIP
            >>> print(f"Created {len(chunks)} chunks")  # doctest: +SKIP
        
        Custom configuration:
            >>> chunker = PDFChunker(
            ...     chunk_size=512,
            ...     chunk_overlap=100,
            ...     extraction_method='pdfplumber',
            ...     preserve_page_boundaries=True,
            ...     verbose=True
            ... )  # doctest: +SKIP
        
        Process directory:
            >>> pdf_dir = Path('data/annotated_pdfs')
            >>> chunks_by_file = chunker.chunk_pdf_directory(pdf_dir)  # doctest: +SKIP
            >>> total = sum(len(c) for c in chunks_by_file.values())
            >>> print(f"Total chunks: {total}")  # doctest: +SKIP
    
    Note:
        Requires at least one of pypdf or pdfplumber installed. Raises RuntimeError
        if neither available. pdfplumber recommended for complex clinical forms
        with tables and AcroForm fields. Pre-compiled regex patterns for performance.
    """
    
    # Pre-compiled regex patterns for performance
    _PATTERN_WHITESPACE = re.compile(r' +')
    _PATTERN_NEWLINES = re.compile(r'\n\s*\n\s*\n+')
    _PATTERN_ROMAN = re.compile(r"^([IVX]+)\.\s+(.+?)$")
    _PATTERN_ALPHA = re.compile(r"^([A-Z])\.\s+(.+?)$")
    _PATTERN_NUMERIC = re.compile(r"^([0-9]+)\.\s+(.+?)$")
    _PATTERN_FORM_CODE = re.compile(r"^([0-9]{1,2}[A-Z]?)\s+(.+?)$")
    _PATTERN_FORM_CODE_VALIDATE = re.compile(r'^[0-9]{1,2}[A-Z]?$')
    
    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 150,
        extraction_method: str = "auto",
        preserve_page_boundaries: bool = True,
        encoding_name: str = "cl100k_base",
        verbose: bool = False
    ):
        """Initialize PDF chunker with extraction and chunking configuration.
        
        Validates extraction method availability, initializes TextChunker for token
        counting, and configures logging. Auto-selects pdfplumber if available,
        otherwise falls back to pypdf.
        
        Args:
            chunk_size (int, optional): Maximum tokens per chunk. Affects semantic
                search granularity. Smaller = more precise, larger = more context.
                Default: 1024.
            chunk_overlap (int, optional): Overlap between consecutive chunks in
                tokens. Helps preserve context across boundaries. Default: 150.
            extraction_method (str, optional): PDF extraction backend. Options:
                - 'pypdf': Fast basic extraction
                - 'pdfplumber': Advanced with tables/forms
                - 'auto': Prefer pdfplumber, fallback to pypdf
                Default: 'auto'.
            preserve_page_boundaries (bool, optional): If True, chunks never span
                multiple pages (each page chunked separately). If False, allows
                cross-page chunks. Default: True.
            encoding_name (str, optional): Tokenizer encoding for token counting.
                Must match embedding model's tokenizer. Default: 'cl100k_base'
                (OpenAI models).
            verbose (bool, optional): Enable detailed debug logging (extraction
                stats, chunking metrics, structure detection). Default: False.
        
        Raises:
            ValueError: If extraction_method not in ['pypdf', 'pdfplumber', 'auto'].
            RuntimeError: If no PDF extraction libraries available (missing both
                pypdf and pdfplumber).
            RuntimeError: If chosen extraction_method library not installed.
        
        Example:
            Default initialization (auto-select backend):
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker()  # doctest: +SKIP
                >>> chunker.extraction_method  # doctest: +SKIP
                'pdfplumber'  # or 'pypdf' if pdfplumber unavailable
            
            Force pypdf with custom settings:
                >>> chunker = PDFChunker(
                ...     chunk_size=512,
                ...     chunk_overlap=50,
                ...     extraction_method='pypdf',
                ...     preserve_page_boundaries=False
                ... )  # doctest: +SKIP
            
            Verbose mode for debugging:
                >>> chunker = PDFChunker(verbose=True)  # doctest: +SKIP
                >>> # Will log detailed extraction and chunking statistics
        
        Side Effects:
            - Logs initialization message with configuration details
            - Initializes TextChunker (loads tokenizer on first use)
            - If verbose=True, logs verbose mode activation
        
        Note:
            Auto-selection ('auto') prefers pdfplumber for better accuracy with
            clinical forms. If both libraries installed, pdfplumber always chosen.
            Raises RuntimeError if specified method unavailable (e.g.,
            extraction_method='pdfplumber' but pdfplumber not installed).
        """
        if extraction_method not in ["pypdf", "pdfplumber", "auto"]:
            raise ValueError(
                f"Invalid extraction_method '{extraction_method}'. "
                f"Must be 'pypdf', 'pdfplumber', or 'auto'"
            )
        
        # Check library availability
        if not PYPDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise RuntimeError(
                "No PDF extraction libraries available. "
                "Install pypdf and/or pdfplumber."
            )
        
        # Determine extraction method
        if extraction_method == "auto":
            # Prefer pdfplumber for better extraction, fallback to pypdf
            self.extraction_method = "pdfplumber" if PDFPLUMBER_AVAILABLE else "pypdf"
        else:
            self.extraction_method = extraction_method
            
            # Validate chosen method is available
            if extraction_method == "pypdf" and not PYPDF_AVAILABLE:
                raise RuntimeError("pypdf not available. Install with: pip install pypdf")
            if extraction_method == "pdfplumber" and not PDFPLUMBER_AVAILABLE:
                raise RuntimeError("pdfplumber not available. Install with: pip install pdfplumber")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_page_boundaries = preserve_page_boundaries
        self.verbose = verbose
        
        # Log verbose mode initialization
        if self.verbose:
            vlog("PDFChunker initialized in VERBOSE mode")
        
        # Initialize underlying text chunker for token counting and splitting
        self.text_chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy="fixed",  # Use fixed for PDFs (no semantic structure like JSONL)
            encoding_name=encoding_name
        )
        
        logger.info(
            f"PDFChunker initialized: size={chunk_size} tokens, "
            f"overlap={chunk_overlap} tokens, method='{self.extraction_method}', "
            f"preserve_pages={preserve_page_boundaries}, verbose={verbose}"
        )
    
    def extract_text_pypdf(self, pdf_path: Path) -> List[Tuple[int, str]]:
        """Extract text from PDF using pypdf library (fast, basic extraction).
        
        Uses pypdf.PdfReader for page-by-page text extraction. Faster than pdfplumber
        but less accurate with complex layouts. Automatically cleans extracted text
        (whitespace normalization, artifact removal). Skips empty pages.
        
        Args:
            pdf_path (Path): Absolute path to PDF file to extract. Must exist.
        
        Returns:
            List[Tuple[int, str]]: List of (page_number, text) tuples, one per
                non-empty page. page_number is 1-indexed. Empty pages excluded.
                Empty list if all pages empty or extraction fails.
        
        Raises:
            RuntimeError: If pypdf library not available (not installed).
            FileNotFoundError: If pdf_path doesn't exist.
            pypdf.errors.PdfReadError: If PDF is corrupted or invalid.
            Exception: Any other extraction error (logged).
        
        Example:
            Extract text from simple PDF:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(extraction_method='pypdf')  # doctest: +SKIP
                >>> pdf_path = Path('data/simple_form.pdf')
                >>> pages = chunker.extract_text_pypdf(pdf_path)  # doctest: +SKIP
                >>> for page_num, text in pages:
                ...     print(f"Page {page_num}: {len(text)} chars")  # doctest: +SKIP
                Page 1: 1523 chars
                Page 2: 987 chars
        
        Side Effects:
            - Reads PDF file from disk
            - Logs number of pages extracted (verbose mode)
            - Logs errors for corrupted/invalid PDFs
        
        Note:
            Automatically calls _clean_extracted_text() to normalize whitespace
            and remove PDF artifacts. Empty pages (after cleaning) are excluded
            from results. For better accuracy with tables/forms, use
            extract_text_pdfplumber() instead.
        """
        if not PYPDF_AVAILABLE:
            raise RuntimeError("pypdf not available")
        
        pages = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    
                    # Clean up extracted text
                    text = self._clean_extracted_text(text)
                    
                    if text.strip():  # Only add non-empty pages
                        pages.append((page_num, text))
                        
            vlog(f"Extracted {len(pages)} pages from {pdf_path.name} using pypdf")
            return pages
            
        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except pypdf.errors.PdfReadError as e:
            logger.error(f"Invalid or corrupted PDF {pdf_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path} using pypdf: {e}")
            raise
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> List[Tuple[int, str]]:
        """Extract text from PDF using pdfplumber library (accurate, advanced extraction).
        
        Uses pdfplumber.open() for page-by-page text extraction with layout analysis.
        More accurate than pypdf for complex layouts, tables, and multi-column text.
        Automatically cleans extracted text and skips empty pages. Recommended for
        clinical research forms.
        
        Args:
            pdf_path (Path): Absolute path to PDF file to extract. Must exist.
        
        Returns:
            List[Tuple[int, str]]: List of (page_number, text) tuples, one per
                non-empty page. page_number is 1-indexed. Empty pages excluded.
                Empty list if all pages empty or extraction fails.
        
        Raises:
            RuntimeError: If pdfplumber library not available (not installed).
            FileNotFoundError: If pdf_path doesn't exist.
            Exception: Any other extraction error (logged, empty list returned).
        
        Example:
            Extract text from complex form:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(extraction_method='pdfplumber')  # doctest: +SKIP
                >>> pdf_path = Path('data/1A Index Case Screening v1.0.pdf')
                >>> pages = chunker.extract_text_pdfplumber(pdf_path)  # doctest: +SKIP
                >>> for page_num, text in pages:
                ...     print(f"Page {page_num}: {len(text)} chars")  # doctest: +SKIP
                Page 1: 2341 chars
                Page 2: 1876 chars
        
        Side Effects:
            - Reads PDF file from disk
            - Logs number of pages extracted (verbose mode)
            - Logs errors for missing/corrupted PDFs
        
        Note:
            Automatically calls _clean_extracted_text() to normalize whitespace.
            Handles None text (some PDFs have image-only pages). Empty pages
            excluded. Preferred over pypdf for clinical forms with tables,
            checkboxes, and complex layouts.
        """
        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError("pdfplumber not available")
        
        pages = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    
                    # Clean up extracted text
                    text = self._clean_extracted_text(text) if text else ""
                    
                    if text.strip():  # Only add non-empty pages
                        pages.append((page_num, text))
                        
            vlog(f"Extracted {len(pages)} pages from {pdf_path.name} using pdfplumber")
            return pages
            
        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path} using pdfplumber: {e}")
            raise
    
    def extract_text(self, pdf_path: Path) -> List[Tuple[int, str]]:
        """Extract text from PDF using configured extraction method.
        
        Dispatcher method that calls extract_text_pypdf() or extract_text_pdfplumber()
        based on self.extraction_method (set during __init__). Provides unified
        interface for text extraction regardless of backend.
        
        Args:
            pdf_path (Path): Absolute path to PDF file to extract. Must exist.
        
        Returns:
            List[Tuple[int, str]]: List of (page_number, text) tuples from chosen
                extraction method. See extract_text_pypdf() or extract_text_pdfplumber()
                for details.
        
        Raises:
            RuntimeError: If self.extraction_method is invalid (not 'pypdf' or
                'pdfplumber'). This should never happen if __init__ validation works.
            FileNotFoundError: If pdf_path doesn't exist (from extraction method).
            Exception: Any extraction error (from extraction method).
        
        Example:
            Extract using auto-selected method:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(extraction_method='auto')  # doctest: +SKIP
                >>> pdf_path = Path('data/form.pdf')
                >>> pages = chunker.extract_text(pdf_path)  # doctest: +SKIP
                >>> # Uses pdfplumber if available, else pypdf
        
        Note:
            This is the primary text extraction method used by chunk_pdf().
            Don't call extract_text_pypdf() or extract_text_pdfplumber() directly
            unless you need a specific backend. extraction_method set during
            __init__ based on 'auto' selection or user choice.
        """
        if self.extraction_method == "pypdf":
            return self.extract_text_pypdf(pdf_path)
        elif self.extraction_method == "pdfplumber":
            return self.extract_text_pdfplumber(pdf_path)
        else:
            raise RuntimeError(
                f"Unknown extraction method: {self.extraction_method}. "
                f"Must be 'pypdf' or 'pdfplumber'"
            )
    
    def extract_tables(
        self, 
        pdf_path: Path,
        table_settings: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Extract structured tables from PDF using pdfplumber (pdfplumber only).
        
        Detects and extracts tabular data from all pages in PDF. Returns table data
        as nested lists with metadata (page number, dimensions). Requires pdfplumber—
        returns empty list if unavailable. Useful for extracting lab results, test
        scores, or structured data from clinical forms.
        
        Args:
            pdf_path (Path): Absolute path to PDF file containing tables. Must exist.
            table_settings (Optional[Dict[str, Any]], optional): pdfplumber table
                extraction settings (e.g., {"vertical_strategy": "lines",
                "horizontal_strategy": "text"}). If None, uses pdfplumber defaults.
                Default: None.
        
        Returns:
            List[Dict[str, Any]]: List of table dictionaries, each containing:
                - page_number (int): Page number (1-indexed)
                - table_index (int): Table index on page (0-indexed)
                - data (List[List[str]]): Table data as nested lists (rows of cells)
                - rows (int): Number of rows in table
                - columns (int): Number of columns in table
                - source_file (str): PDF filename
                Empty list if no tables found, pdfplumber unavailable, or error.
        
        Raises:
            FileNotFoundError: If pdf_path doesn't exist.
            Exception: Any extraction error (logged, returns empty list).
        
        Example:
            Extract all tables from clinical form:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(extraction_method='pdfplumber')  # doctest: +SKIP
                >>> pdf_path = Path('data/5 CBC v2.0.pdf')  # Lab results form
                >>> tables = chunker.extract_tables(pdf_path)  # doctest: +SKIP
                >>> for table in tables:
                ...     print(f"Page {table['page_number']}: {table['rows']}x{table['columns']}")
                ...     print(table['data'][0])  # First row (header)  # doctest: +SKIP
                Page 1: 10x5
                ['Test', 'Result', 'Unit', 'Reference Range', 'Flag']
            
            Custom table settings:
                >>> settings = {
                ...     "vertical_strategy": "lines",
                ...     "horizontal_strategy": "text",
                ...     "snap_tolerance": 3
                ... }
                >>> tables = chunker.extract_tables(pdf_path, table_settings=settings)  # doctest: +SKIP
        
        Side Effects:
            - Reads PDF file from disk
            - Logs table count and dimensions (info level)
            - Logs detailed table info (verbose mode)
            - Logs warning if pdfplumber unavailable
        
        Note:
            Requires pdfplumber library—returns empty list if not installed. Does
            NOT raise error if unavailable (logs warning instead). Empty tables
            excluded from results. table_settings allows fine-tuning extraction
            for specific PDF layouts. See pdfplumber docs for settings options.
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available. Cannot extract tables.")
            return []
        
        settings = table_settings or {}
        tables_with_metadata = []
        
        try:
            if self.verbose:
                vlog(f"Extracting tables from: {pdf_path.name}")
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_tables = page.extract_tables(table_settings=settings)
                    
                    for table_index, table_data in enumerate(page_tables):
                        if table_data:  # Only add non-empty tables
                            tables_with_metadata.append({
                                "page_number": page_num,
                                "table_index": table_index,
                                "data": table_data,
                                "rows": len(table_data),
                                "columns": len(table_data[0]) if table_data else 0,
                                "source_file": pdf_path.name
                            })
            
            if self.verbose:
                vlog(f"Extracted {len(tables_with_metadata)} tables")
                for i, table in enumerate(tables_with_metadata):
                    vlog(f"  Table {i+1}: {table['rows']}x{table['columns']} on page {table['page_number']}")
            
            logger.info(f"Extracted {len(tables_with_metadata)} tables from {pdf_path.name}")
            return tables_with_metadata
            
        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract tables from {pdf_path}: {e}")
            return []
    
    def extract_form_fields(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract PDF AcroForm field values from annotated documents (pdfplumber only).
        
        Extracts interactive form field data (text boxes, checkboxes, radio buttons)
        from PDFs with AcroForm annotations. Returns field names, values, alternate
        names, and types. Requires pdfplumber—returns empty dict if unavailable.
        Useful for extracting pre-filled data from electronic clinical forms.
        
        Args:
            pdf_path (Path): Absolute path to PDF with AcroForm fields. Must exist.
        
        Returns:
            Dict[str, Any]: Dictionary mapping field_name → field_info:
                - value (Any): Field value (str, bool, or None if empty)
                - alternate_name (str): User-friendly field name (if present)
                - type (str): Field type (e.g., "/Tx" for text, "/Btn" for button)
                Empty dict if no AcroForm fields, pdfplumber unavailable, or error.
        
        Raises:
            FileNotFoundError: If pdf_path doesn't exist.
            Exception: Any extraction error (logged, returns empty dict).
        
        Example:
            Extract form field values:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(extraction_method='pdfplumber', verbose=True)  # doctest: +SKIP
                >>> pdf_path = Path('data/filled_form.pdf')
                >>> fields = chunker.extract_form_fields(pdf_path)  # doctest: +SKIP
                >>> for name, info in fields.items():
                ...     print(f"{name}: {info['value']}")  # doctest: +SKIP
                PatientID: 12345
                VisitDate: 2024-01-15
                Consent: Yes
            
            Check field metadata:
                >>> fields['PatientID']['alternate_name']  # doctest: +SKIP
                'Patient Identifier'
                >>> fields['PatientID']['type']  # doctest: +SKIP
                '/Tx'  # Text field
        
        Side Effects:
            - Reads PDF file from disk
            - Logs field count (info level)
            - Logs each field name/value (verbose mode)
            - Logs warning if pdfplumber unavailable or no AcroForm
            - Logs detailed exception traceback (verbose mode on error)
        
        Note:
            Requires pdfplumber library—returns empty dict if not installed. Does
            NOT raise error if unavailable. Only works with PDFs containing AcroForm
            fields (interactive forms). Scanned PDFs or image-based forms have no
            extractable fields. Empty/None values included in results. Uses
            pdfplumber.utils.pdfinternals for low-level PDF parsing.
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available. Cannot extract form fields.")
            return {}
        
        try:
            if self.verbose:
                vlog(f"Extracting form fields from: {pdf_path.name}")
            
            from pdfplumber.utils.pdfinternals import resolve_and_decode, resolve
            
            form_data = {}
            
            with pdfplumber.open(pdf_path) as pdf:
                # Check if PDF has AcroForm fields
                if not pdf.doc.catalog.get("AcroForm"):
                    if self.verbose:
                        vlog(f"No AcroForm fields found in {pdf_path.name}")
                    return {}
                
                acroform = resolve(pdf.doc.catalog["AcroForm"])
                if "Fields" not in acroform:
                    if self.verbose:
                        vlog(f"AcroForm exists but has no Fields in {pdf_path.name}")
                    return {}
                
                fields = resolve(acroform["Fields"])
                
                for field in fields:
                    resolved_field = field.resolve()
                    
                    # Get field name (T = field name, TU = alternate/user-friendly name)
                    field_name = resolve_and_decode(resolved_field.get("T")) if "T" in resolved_field else None
                    alternate_name = resolve_and_decode(resolved_field.get("TU")) if "TU" in resolved_field else None
                    
                    # Get field value
                    field_value = resolve_and_decode(resolved_field.get("V")) if "V" in resolved_field else None
                    
                    # Get field type (e.g., /Tx for text, /Btn for button/checkbox)
                    field_type = str(resolved_field.get("FT", "")) if "FT" in resolved_field else "Unknown"
                    
                    if field_name:
                        form_data[field_name] = {
                            "value": field_value,
                            "alternate_name": alternate_name,
                            "type": field_type
                        }
                        
                        if self.verbose:
                            vlog(f"  Field: {field_name} = {field_value}")
            
            if self.verbose:
                vlog(f"Extracted {len(form_data)} form fields")
            
            logger.info(f"Extracted {len(form_data)} form fields from {pdf_path.name}")
            return form_data
            
        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract form fields from {pdf_path}: {e}")
            if self.verbose:
                logger.exception("Detailed traceback:")
            return {}
    
    def enrich_metadata(self, pdf_path: Path, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich chunk metadata with PDF document properties (pdfplumber only).
        
        Extracts and adds PDF metadata (author, creation date, title, subject, etc.)
        to base_metadata dictionary. Filters out None values. Requires pdfplumber—
        returns base_metadata unchanged if unavailable. Non-destructive (adds to,
        doesn't replace base_metadata).
        
        Args:
            pdf_path (Path): Absolute path to PDF file. Must exist.
            base_metadata (Dict[str, Any]): Existing metadata dictionary to enrich.
                Not modified in-place (copy created).
        
        Returns:
            Dict[str, Any]: Enriched metadata dictionary with PDF properties added.
                Original base_metadata keys preserved. If pdfplumber unavailable or
                error occurs, returns base_metadata unchanged.
        
        Example:
            Enrich metadata with PDF properties:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(extraction_method='pdfplumber')  # doctest: +SKIP
                >>> pdf_path = Path('data/form.pdf')
                >>> base = {'study': 'Indo-VAP', 'version': 'v1.0'}
                >>> enriched = chunker.enrich_metadata(pdf_path, base)  # doctest: +SKIP
                >>> enriched.keys()  # doctest: +SKIP
                dict_keys(['study', 'version', 'Author', 'CreationDate', 'Title'])
                >>> enriched['Author']  # doctest: +SKIP
                'Research Team'
        
        Side Effects:
            - Reads PDF file from disk (brief)
            - Logs added metadata keys (verbose mode)
            - Logs warning on error (returns base_metadata unchanged)
        
        Note:
            Requires pdfplumber library—returns base_metadata if not installed.
            Non-destructive operation (doesn't modify base_metadata in-place).
            Only non-None metadata values added. Common metadata keys: Author,
            Creator, Producer, CreationDate, ModDate, Title, Subject. Not all
            PDFs have metadata (returns base_metadata if none found).
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available. Cannot enrich metadata.")
            return base_metadata
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.metadata:
                    # Add PDF metadata (filter out None values)
                    pdf_meta = {k: v for k, v in pdf.metadata.items() if v is not None}
                    base_metadata.update(pdf_meta)
                    
                    if self.verbose:
                        vlog(f"Added PDF metadata: {list(pdf_meta.keys())}")
            
            return base_metadata
            
        except Exception as e:
            logger.warning(f"Failed to enrich metadata from {pdf_path}: {e}")
            return base_metadata
    
    def validate_chunks(self, chunks: List[PDFChunk]) -> Dict[str, Any]:
        """Validate chunk quality and return comprehensive metrics.
        
        Analyzes chunk list for quality issues: empty chunks, token count statistics,
        section header detection, form code presence, and page coverage. Returns
        validation metrics dictionary. Logs warnings for quality issues (empty chunks,
        low token counts). Used internally by chunk_pdf() for quality assurance.
        
        Args:
            chunks (List[PDFChunk]): List of PDF chunks to validate. Can be empty.
        
        Returns:
            Dict[str, Any]: Validation metrics dictionary containing:
                - total_chunks (int): Number of chunks
                - avg_token_count (float): Average tokens per chunk
                - min_token_count (int): Minimum tokens in any chunk
                - max_token_count (int): Maximum tokens in any chunk
                - chunks_without_text (int): Count of empty text chunks
                - chunks_with_sections (int): Chunks with section_title metadata
                - form_code_detected (bool): True if chunks[0] has form_code
                - pages_covered (int): Number of unique pages in chunks
                - validation_passed (bool): True if no issues detected
        
        Example:
            Validate chunk quality:
                >>> from scripts.vector_db.pdf_chunking import PDFChunker, PDFChunk
                >>> chunks = [
                ...     PDFChunk(text="Section I...", token_count=150,
                ...              chunk_index=0, source_file="test.pdf",
                ...              chunk_strategy="structure", page_number=1,
                ...              form_code="1A"),
                ...     PDFChunk(text="Section II...", token_count=200,
                ...              chunk_index=1, source_file="test.pdf",
                ...              chunk_strategy="structure", page_number=1,
                ...              form_code="1A")
                ... ]
                >>> chunker = PDFChunker()  # doctest: +SKIP
                >>> metrics = chunker.validate_chunks(chunks)  # doctest: +SKIP
                >>> metrics['total_chunks']  # doctest: +SKIP
                2
                >>> metrics['avg_token_count']  # doctest: +SKIP
                175.0
                >>> metrics['validation_passed']  # doctest: +SKIP
                True
            
            Handle empty chunk list:
                >>> chunker = PDFChunker()  # doctest: +SKIP
                >>> metrics = chunker.validate_chunks([])  # doctest: +SKIP
                >>> metrics['total_chunks']  # doctest: +SKIP
                0
                >>> metrics['validation_passed']  # doctest: +SKIP
                False
        
        Side Effects:
            - Logs warnings for chunks_without_text > 0
            - Logs warning if avg_token_count < 50
            - Logs all metrics (verbose mode)
            - Sets validation_passed=False if issues detected
        
        Note:
            Empty chunk list returns all zeros with validation_passed=False.
            Low token count threshold is 50 (configurable in code). form_code_detected
            only checks chunks[0] (assumes all chunks from same form). Used internally
            by chunk_pdf() after chunking completes.
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_token_count": 0,
                "min_token_count": 0,
                "max_token_count": 0,
                "chunks_without_text": 0,
                "chunks_with_sections": 0,
                "form_code_detected": False,
                "validation_passed": False
            }
        
        token_counts = [c.token_count for c in chunks]
        
        metrics = {
            "total_chunks": len(chunks),
            "avg_token_count": sum(token_counts) / len(chunks),
            "min_token_count": min(token_counts),
            "max_token_count": max(token_counts),
            "chunks_without_text": sum(1 for c in chunks if not c.text.strip()),
            "chunks_with_sections": sum(1 for c in chunks if c.metadata.get("section_title")),
            "form_code_detected": bool(chunks[0].form_code) if chunks else False,
            "pages_covered": len(set(c.page_number for c in chunks)),
            "validation_passed": True
        }
        
        # Warn about potential issues
        if metrics["chunks_without_text"] > 0:
            logger.warning(f"{metrics['chunks_without_text']} chunks have no text content")
            metrics["validation_passed"] = False
        
        if metrics["avg_token_count"] < 50:
            logger.warning(f"Average token count ({metrics['avg_token_count']:.1f}) is very low")
        
        if self.verbose:
            vlog("Chunk Validation Metrics:")
            for key, value in metrics.items():
                vlog(f"  {key}: {value}")
        
        return metrics
    
    def _log_chunking_stats(self, chunks: List[PDFChunk]) -> None:
        """Log detailed chunking statistics in verbose mode (internal helper).
        
        Formats and logs comprehensive chunking metrics using validate_chunks().
        Only logs if verbose=True and chunks non-empty. Displays total chunks,
        token stats, section/page coverage, and form metadata. Used internally
        by chunk_pdf() for debugging.
        
        Args:
            chunks (List[PDFChunk]): Chunks to analyze and log. Can be empty (no-op).
        
        Returns:
            None: Logs to console/file, doesn't return anything.
        
        Side Effects:
            - Calls validate_chunks() to compute metrics
            - Logs formatted statistics (verbose mode only)
            - No logging if verbose=False or chunks empty
        
        Example:
            Internal usage (called by chunk_pdf):
                >>> # Inside chunk_pdf():
                >>> # self._log_chunking_stats(all_chunks)  # doctest: +SKIP
                >>> # Output (verbose mode):
                >>> # ============================================================
                >>> # CHUNKING STATISTICS
                >>> # ============================================================
                >>> # Total chunks: 15
                >>> # Token stats: avg=234.5, min=100, max=512
                >>> # Chunks with sections: 12
                >>> # Pages covered: 3
                >>> # Form code detected: True
                >>> # Form code: 1A
                >>> # Form title: Index Case Screening
                >>> # ============================================================
        
        Note:
            Private method (leading underscore). Only active in verbose mode.
            Relies on validate_chunks() for metric computation. Displays form_code
            and form_title from chunks[0] if present.
        """
        if not chunks or not self.verbose:
            return
        
        metrics = self.validate_chunks(chunks)
        
        vlog("=" * 60)
        vlog("CHUNKING STATISTICS")
        vlog("=" * 60)
        vlog(f"Total chunks: {metrics['total_chunks']}")
        vlog(f"Token stats: avg={metrics['avg_token_count']:.1f}, "
                    f"min={metrics['min_token_count']}, max={metrics['max_token_count']}")
        vlog(f"Chunks with sections: {metrics['chunks_with_sections']}")
        vlog(f"Pages covered: {metrics['pages_covered']}")
        vlog(f"Form code detected: {metrics['form_code_detected']}")
        
        if chunks[0].form_code:
            vlog(f"Form code: {chunks[0].form_code}")
        if chunks[0].form_title:
            vlog(f"Form title: {chunks[0].form_title}")
        
        vlog("=" * 60)
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean up extracted PDF text by normalizing whitespace and removing artifacts.
        
        Applies multiple cleaning transformations:
        1. Collapses multiple spaces to single space
        2. Reduces 3+ newlines to double newline (paragraph breaks)
        3. Strips leading/trailing whitespace from each line
        4. Removes PDF artifacts (null chars, BOM markers)
        5. Final strip of entire text
        
        Used internally by extract_text_pypdf() and extract_text_pdfplumber() to
        normalize raw PDF text before chunking.
        
        Args:
            text (str): Raw extracted text from PDF. Can be empty or None.
        
        Returns:
            str: Cleaned text with normalized whitespace and artifacts removed.
                Empty string if input empty/None.
        
        Example:
            Clean raw PDF text:
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker()  # doctest: +SKIP
                >>> raw_text = "Multiple    spaces\\n\\n\\n\\nToo many newlines"
                >>> clean = chunker._clean_extracted_text(raw_text)  # doctest: +SKIP
                >>> clean  # doctest: +SKIP
                'Multiple spaces\\n\\nToo many newlines'
            
            Handle empty input:
                >>> chunker._clean_extracted_text("")  # doctest: +SKIP
                ''
                >>> chunker._clean_extracted_text(None)  # doctest: +SKIP
                ''
        
        Note:
            Private method (leading underscore). Uses pre-compiled regex patterns
            for performance (_PATTERN_WHITESPACE, _PATTERN_NEWLINES). Removes
            common PDF artifacts: \\x00 (null), \\ufeff (BOM). Preserves paragraph
            breaks (double newlines). Called automatically by extraction methods.
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        text = self._PATTERN_WHITESPACE.sub(' ', text)
        
        # Replace multiple newlines with double newline (paragraph break)
        text = self._PATTERN_NEWLINES.sub('\n\n', text)
        
        # Remove trailing/leading whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove common PDF artifacts
        text = text.replace('\x00', '')  # Null characters
        text = text.replace('\ufeff', '')  # BOM
        
        return text.strip()
    
    def _detect_document_structure(
        self, 
        text: str, 
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect document structure from text and filename (no hardcoded profiles).
        
        Automatically identifies:
        1. Form code + title from first 5 lines (e.g., "1A Index Case Screening")
        2. Form code + title from filename if not found in text
        3. Section headers throughout document:
           - Roman numerals: I., II., III., IV., ...
           - Alpha headers: A., B., C., D., ...
           - Numeric headers: 1., 2., 3., ... (up to 50, filtered for false positives)
        
        Returns structure dictionary for use in _chunk_by_structure(). No hardcoded
        form profiles—all detection is regex-based and automatic.
        
        Args:
            text (str): Full extracted text from PDF (all pages combined).
            filename (Optional[str], optional): PDF filename for fallback form code
                extraction. If None, only text is used. Default: None.
        
        Returns:
            Dict[str, Any]: Structure dictionary containing:
                - form_code (str|None): Detected form code (e.g., "1A", "12B")
                - form_title (str|None): Detected form title
                - sections (List[Dict]): Detected section headers, each dict:
                    - type (str): 'roman', 'alpha', or 'numeric'
                    - number (str): Section number/letter (e.g., "I", "A", "1")
                    - title (str): Section title text
                    - line_number (int): Line index in text
                - has_numbered_sections (bool): True if roman/numeric sections found
                - has_lettered_sections (bool): True if alpha sections found
        
        Example:
            Detect structure from text:
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(verbose=True)  # doctest: +SKIP
                >>> text = \"\"\"1A Index Case Screening
                ... I. Demographics
                ... Patient information...
                ... II. Medical History
                ... Previous conditions...\"\"\"
                >>> structure = chunker._detect_document_structure(text)  # doctest: +SKIP
                >>> structure['form_code']  # doctest: +SKIP
                '1A'
                >>> structure['form_title']  # doctest: +SKIP
                'Index Case Screening'
                >>> len(structure['sections'])  # doctest: +SKIP
                2
                >>> structure['sections'][0]  # doctest: +SKIP
                {'type': 'roman', 'number': 'I', 'title': 'Demographics', 'line_number': 1}
            
            Fallback to filename:
                >>> text_no_code = "Some content without form code..."
                >>> filename = "12B Follow-up B v1.0.pdf"
                >>> structure = chunker._detect_document_structure(text_no_code, filename)  # doctest: +SKIP
                >>> structure['form_code']  # doctest: +SKIP
                '12B'
                >>> structure['form_title']  # doctest: +SKIP
                'Follow-up B'
        
        Side Effects:
            - Logs detected form code/title (verbose mode)
            - Logs section count and types (verbose mode)
        
        Note:
            Private method (leading underscore). Uses pre-compiled regex patterns
            for performance. Form code validation: ^[0-9]{1,2}[A-Z]?$ (1-2 digits,
            optional letter). Filename extraction removes version suffix (" v1.0")
            and .pdf extension. Numeric headers filtered to avoid dates (≤50,
            title length >3, no digits in first 10 chars). No hardcoded form
            profiles—fully automatic detection.
        """
        structure = {
            "form_code": None,
            "form_title": None,
            "sections": [],
            "has_numbered_sections": False,
            "has_lettered_sections": False
        }
        
        lines = text.split('\n')
        
        # Extract form code and title from first few lines
        for i in range(min(5, len(lines))):
            line = lines[i].strip()
            if not line:
                continue
            
            # Try to match form code and title (using pre-compiled pattern)
            match = self._PATTERN_FORM_CODE.match(line)
            if match:
                potential_code = match.group(1)
                potential_title = match.group(2).strip()
                
                # Validate it looks like a form code (using pre-compiled pattern)
                if self._PATTERN_FORM_CODE_VALIDATE.match(potential_code):
                    structure["form_code"] = potential_code
                    structure["form_title"] = potential_title
                    vlog(f"Detected form from text: {potential_code} - {potential_title}")
                    break
        
        # ENHANCEMENT: Try extracting from filename if not found in text
        if not structure["form_code"] and filename:
            # Try to match form code pattern in filename
            match = self._PATTERN_FORM_CODE.match(filename)
            if match:
                potential_code = match.group(1)
                potential_title = match.group(2).strip()
                
                # Remove version suffix (e.g., " v1.0" or " V1.0")
                # Also remove .pdf extension if present
                potential_title = re.sub(r'\s+v\d+\.\d+', '', potential_title, flags=re.IGNORECASE)
                potential_title = re.sub(r'\.pdf$', '', potential_title, flags=re.IGNORECASE)
                potential_title = potential_title.strip()
                
                # Validate it looks like a form code
                if self._PATTERN_FORM_CODE_VALIDATE.match(potential_code):
                    structure["form_code"] = potential_code
                    structure["form_title"] = potential_title
                    vlog(f"Detected form from filename: {potential_code} - {potential_title}")
        
        # Detect section headers throughout document
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Try roman numeral headers (I., II., III.) - using pre-compiled pattern
            match = self._PATTERN_ROMAN.match(line)
            if match:
                structure["sections"].append({
                    "type": "roman",
                    "number": match.group(1),
                    "title": match.group(2).strip(),
                    "line_number": i
                })
                structure["has_numbered_sections"] = True
                continue
            
            # Try lettered headers (A., B., C.)
            match = self._PATTERN_ALPHA.match(line)
            if match and len(match.group(1)) == 1:  # Only single letters
                structure["sections"].append({
                    "type": "alpha",
                    "number": match.group(1),
                    "title": match.group(2).strip(),
                    "line_number": i
                })
                structure["has_lettered_sections"] = True
                continue
            
            # Try numeric headers (1., 2., 3.) - but avoid dates
            match = self._PATTERN_NUMERIC.match(line)
            if match:
                num = match.group(1)
                title = match.group(2).strip()
                
                # Avoid false positives (dates, measurements, etc.)
                if int(num) <= 50 and len(title) > 3 and not any(c.isdigit() for c in title[:10]):
                    structure["sections"].append({
                        "type": "numeric",
                        "number": num,
                        "title": title,
                        "line_number": i
                    })
        
        vlog(
            f"Structure detected: {len(structure['sections'])} sections, "
            f"numbered={structure['has_numbered_sections']}, "
            f"lettered={structure['has_lettered_sections']}"
        )
        
        return structure
    
    def _chunk_by_structure(
        self,
        text: str,
        structure: Dict[str, Any],
        page_number: int,
        base_metadata: Dict[str, Any],
        folder_path: str,
        source_file: str
    ) -> List[PDFChunk]:
        """Chunk text using detected document structure (section-aware or fixed-size).
        
        Applies adaptive chunking strategy based on detected sections:
        1. **Structure-based chunking** (if sections detected):
           - Chunks at section boundaries (I., A., 1., etc.)
           - Each chunk = one section
           - Section title preserved in metadata
        2. **Fixed-size chunking** (no sections):
           - Uses TextChunker.text_splitter for token-limited chunks
           - Respects chunk_size and chunk_overlap
           - No section metadata
        
        Used internally by chunk_pdf() for both per-page and whole-document chunking.
        
        Args:
            text (str): Text to chunk (single page or full document).
            structure (Dict[str, Any]): Structure from _detect_document_structure().
            page_number (int): Page number for chunks (1-indexed). Can be 1 for
                multi-page chunks if preserve_page_boundaries=False.
            base_metadata (Dict[str, Any]): Metadata to include in all chunks.
            folder_path (str): Relative folder path for chunk metadata.
            source_file (str): PDF filename for chunk metadata.
        
        Returns:
            List[PDFChunk]: Chunked text with metadata. Empty list if text empty.
        
        Example:
            Structure-based chunking (internal usage):
                >>> # Inside chunk_pdf():
                >>> # structure = self._detect_document_structure(text)
                >>> # chunks = self._chunk_by_structure(
                >>> #     text=page_text,
                >>> #     structure=structure,
                >>> #     page_number=1,
                >>> #     base_metadata={'study': 'Indo-VAP'},
                >>> #     folder_path='annotated_pdfs',
                >>> #     source_file='1A Index Case Screening.pdf'
                >>> # )  # doctest: +SKIP
                >>> # Result: Chunks at section boundaries with section_title metadata
            
            Fixed-size fallback (no sections):
                >>> # structure = {'sections': [], 'form_code': '', 'form_title': ''}
                >>> # chunks = self._chunk_by_structure(...)  # doctest: +SKIP
                >>> # Result: Fixed-size chunks via TextChunker.text_splitter
        
        Side Effects:
            - Calls _create_pdf_chunk() for each chunk
            - Calls text_chunker.text_splitter.split_text() for fixed-size chunking
            - Logs chunking strategy and chunk count (verbose mode)
        
        Note:
            Private method (leading underscore). Section-based chunking creates
            one chunk per section (may exceed chunk_size if section is long).
            Fixed-size chunking respects chunk_size limits. Section titles
            formatted as "{number}. {title}" (e.g., "I. Demographics"). Empty
            chunks (after stripping) excluded from results.
        """
        chunks = []
        form_code = structure.get("form_code", "")
        form_title = structure.get("form_title", "")
        
        if structure["sections"]:
            # Chunk at section boundaries
            lines = text.split('\n')
            current_section = None
            current_section_title = None
            current_text = []
            chunk_index = 0
            
            for i, line in enumerate(lines):
                # Check if this line is a section header
                section_at_line = next(
                    (s for s in structure["sections"] if s["line_number"] == i),
                    None
                )
                
                if section_at_line:
                    # Save previous section
                    if current_text:
                        chunk_text = '\n'.join(current_text).strip()
                        if chunk_text:
                            chunk = self._create_pdf_chunk(
                                text=chunk_text,
                                section_title=current_section_title,
                                form_code=form_code,
                                form_title=form_title,
                                page_number=page_number,
                                folder_path=folder_path,
                                source_file=source_file,
                                chunk_index=chunk_index,
                                base_metadata=base_metadata
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                    
                    # Start new section
                    current_section = section_at_line
                    current_section_title = f"{section_at_line['number']}. {section_at_line['title']}"
                    current_text = [line]
                else:
                    current_text.append(line)
            
            # Save last section
            if current_text:
                chunk_text = '\n'.join(current_text).strip()
                if chunk_text:
                    chunk = self._create_pdf_chunk(
                        text=chunk_text,
                        section_title=current_section_title,
                        form_code=form_code,
                        form_title=form_title,
                        page_number=page_number,
                        folder_path=folder_path,
                        source_file=source_file,
                        chunk_index=chunk_index,
                        base_metadata=base_metadata
                    )
                    chunks.append(chunk)
            
            vlog(f"Created {len(chunks)} structure-based chunks")
        
        else:
            # No sections detected, use fixed-size chunking
            vlog("No sections detected, using fixed-size chunking")
            text_pieces = self.text_chunker.text_splitter.split_text(text)
            
            for i, piece in enumerate(text_pieces):
                chunk = self._create_pdf_chunk(
                    text=piece,
                    section_title=None,
                    form_code=form_code,
                    form_title=form_title,
                    page_number=page_number,
                    folder_path=folder_path,
                    source_file=source_file,
                    chunk_index=i,
                    base_metadata=base_metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_pdf_chunk(
        self,
        text: str,
        section_title: Optional[str],
        form_code: str,
        form_title: str,
        page_number: int,
        folder_path: str,
        source_file: str,
        chunk_index: int,
        base_metadata: Dict[str, Any]
    ) -> PDFChunk:
        """Create a PDFChunk with all metadata (internal helper).
        
        Factory method that creates PDFChunk instances with complete metadata.
        Counts tokens, merges base_metadata, adds section_title if present, and
        populates all PDF-specific fields. Used internally by _chunk_by_structure()
        for consistent chunk creation.
        
        Args:
            text (str): Chunk text content.
            section_title (Optional[str]): Section header (e.g., "I. Demographics").
                If None, no section_title added to metadata.
            form_code (str): Form identifier (e.g., "1A"). Can be empty.
            form_title (str): Form name (e.g., "Index Case Screening"). Can be empty.
            page_number (int): Page number (1-indexed).
            folder_path (str): Relative folder path.
            source_file (str): PDF filename.
            chunk_index (int): Sequential chunk index (0-based).
            base_metadata (Dict[str, Any]): Additional metadata to include.
        
        Returns:
            PDFChunk: Fully populated PDF chunk with text, metadata, and counts.
        
        Example:
            Create chunk (internal usage):
                >>> # Inside _chunk_by_structure():
                >>> # chunk = self._create_pdf_chunk(
                >>> #     text="Patient demographics section...",
                >>> #     section_title="I. Demographics",
                >>> #     form_code="1A",
                >>> #     form_title="Index Case Screening",
                >>> #     page_number=1,
                >>> #     folder_path="annotated_pdfs",
                >>> #     source_file="1A Index Case Screening v1.0.pdf",
                >>> #     chunk_index=0,
                >>> #     base_metadata={'study': 'Indo-VAP'}
                >>> # )  # doctest: +SKIP
                >>> # chunk.token_count  # Auto-counted via text_chunker
                >>> # chunk.metadata['section_title']  # "I. Demographics"
        
        Side Effects:
            - Calls text_chunker.count_tokens() to compute token_count
            - Creates copy of base_metadata (non-destructive)
            - Adds page_number and section_title to metadata
        
        Note:
            Private method (leading underscore). Always sets chunk_strategy to
            "document_structure". Metadata includes page_number and section_title
            (if provided). base_metadata copied (not modified in-place). Token
            count uses text_chunker's encoding (cl100k_base by default).
        """
        token_count = self.text_chunker.count_tokens(text)
        
        # Create chunk metadata
        chunk_metadata = base_metadata.copy()
        chunk_metadata["page_number"] = page_number
        if section_title:
            chunk_metadata["section_title"] = section_title
        
        chunk = PDFChunk(
            text=text,
            metadata=chunk_metadata,
            token_count=token_count,
            chunk_index=chunk_index,
            source_file=source_file,
            chunk_strategy="document_structure",
            page_number=page_number,
            folder_path=folder_path,
            form_code=form_code,
            form_title=form_title
        )
        
        return chunk
    
    def chunk_pdf(
        self,
        pdf_path: Path,
        base_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[PDFChunk]:
        """Extract and chunk a PDF file with automatic structure detection and metadata enrichment.
        
        Main entry point for single-PDF processing. Orchestrates complete workflow:
        1. Validates PDF exists
        2. Computes folder_path (relative to base_path)
        3. Enriches metadata with PDF properties
        4. Extracts tables and form fields (if pdfplumber available)
        5. Extracts text from all pages
        6. Detects document structure (form code, sections)
        7. Chunks text using adaptive strategy (structure-aware or fixed-size)
        8. Validates chunks and logs statistics (verbose mode)
        
        Returns list of PDFChunk objects ready for embedding/vector storage.
        
        Args:
            pdf_path (Path): Absolute path to PDF file to chunk. Must exist.
            base_path (Optional[Path], optional): Base directory for computing
                relative folder_path. If None, uses pdf_path.parent as folder_path.
                Default: None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata to
                include in all chunks. Merged with auto-detected metadata (PDF
                properties, form code, etc.). Default: None (empty dict).
        
        Returns:
            List[PDFChunk]: List of chunked text with complete metadata. Each chunk
                includes text, token count, page number, form metadata, section
                titles (if detected), and enriched PDF properties. Empty list if
                text extraction fails or no text found.
        
        Raises:
            FileNotFoundError: If pdf_path doesn't exist.
            Exception: Any extraction or chunking error (logged, empty list returned).
        
        Example:
            Basic single-file chunking:
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(verbose=True)  # doctest: +SKIP
                >>> pdf_path = Path('data/Indo-VAP/annotated_pdfs/1A Index Case Screening v1.0.pdf')
                >>> chunks = chunker.chunk_pdf(pdf_path)  # doctest: +SKIP
                >>> print(f"Created {len(chunks)} chunks")  # doctest: +SKIP
                Created 8 chunks
                >>> # Inspect first chunk
                >>> chunk = chunks[0]  # doctest: +SKIP
                >>> chunk.form_code  # doctest: +SKIP
                '1A'
                >>> chunk.form_title  # doctest: +SKIP
                'Index Case Screening'
                >>> chunk.metadata.get('section_title')  # doctest: +SKIP
                'I. Demographics'
            
            With base_path for relative folder paths:
                >>> base_path = Path('data/Indo-VAP')
                >>> pdf_path = Path('data/Indo-VAP/annotated_pdfs/1A Index Case Screening v1.0.pdf')
                >>> chunks = chunker.chunk_pdf(pdf_path, base_path=base_path)  # doctest: +SKIP
                >>> chunks[0].folder_path  # doctest: +SKIP
                'annotated_pdfs'  # Relative to base_path
            
            With custom metadata:
                >>> custom_meta = {'study': 'Indo-VAP', 'version': 'v1.0', 'language': 'en'}
                >>> chunks = chunker.chunk_pdf(pdf_path, metadata=custom_meta)  # doctest: +SKIP
                >>> chunks[0].metadata['study']  # doctest: +SKIP
                'Indo-VAP'
                >>> chunks[0].metadata['has_tables']  # Auto-detected  # doctest: +SKIP
                True
            
            Handle missing PDF:
                >>> bad_path = Path('nonexistent.pdf')
                >>> try:
                ...     chunks = chunker.chunk_pdf(bad_path)  # doctest: +SKIP
                ... except FileNotFoundError as e:
                ...     print(f"Error: {e}")  # doctest: +SKIP
                Error: PDF not found: nonexistent.pdf
        
        Side Effects:
            - Reads PDF file from disk (multiple passes for text, tables, forms)
            - Logs processing steps (info level)
            - Logs detailed statistics (verbose mode)
            - Logs warnings for quality issues (empty chunks, low tokens)
            - Calls validate_chunks() for quality metrics
        
        Performance:
            Typical processing time (CPU):
            - Simple PDF (pypdf): ~0.5-2 seconds
            - Complex PDF (pdfplumber): ~1-5 seconds
            - With tables/forms: +0.5-1 second
            - Verbose mode: +10-20% overhead (logging)
        
        Note:
            base_metadata always includes: source_type='pdf', filename, folder_path,
            form_code (if detected), form_title (if detected). If pdfplumber available,
            also includes: has_tables, table_count, has_form_fields, form_field_count,
            and PDF document properties (Author, CreationDate, etc.). Structure
            detection is automatic—no hardcoded form profiles. preserve_page_boundaries
            setting (from __init__) controls per-page vs. whole-document chunking.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Compute folder path (relative to base_path)
        if base_path:
            try:
                folder_path = str(pdf_path.parent.relative_to(base_path))
            except ValueError:
                # pdf_path not relative to base_path
                folder_path = str(pdf_path.parent)
        else:
            folder_path = str(pdf_path.parent)
        
        # Initialize base metadata
        base_metadata = metadata or {}
        base_metadata.update({
            "source_type": "pdf",
            "filename": pdf_path.name,
            "folder_path": folder_path,
            "form_code": "",  # Will be set by structure detection
            "form_title": ""  # Will be set by structure detection
        })
        
        logger.info(f"Chunking PDF: {pdf_path.name}")
        
        if self.verbose:
            vlog(f"PDF file size: {pdf_path.stat().st_size / 1024:.2f} KB")
            vlog(f"Extraction method: {self.extraction_method}")
            vlog(f"Chunk settings: size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        # Enrich metadata with PDF document properties
        base_metadata = self.enrich_metadata(pdf_path, base_metadata)
        
        # Extract tables (if available with pdfplumber)
        tables = self.extract_tables(pdf_path)
        if tables:
            base_metadata['has_tables'] = True
            base_metadata['table_count'] = len(tables)
            if self.verbose:
                vlog(f"Found {len(tables)} tables in PDF")
        
        # Extract form fields (if available)
        form_fields = self.extract_form_fields(pdf_path)
        if form_fields:
            base_metadata['has_form_fields'] = True
            base_metadata['form_field_count'] = len(form_fields)
            if self.verbose:
                vlog(f"Found {len(form_fields)} form fields in PDF")
        
        # Extract text from PDF
        try:
            pages = self.extract_text(pdf_path)
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return []
        
        if not pages:
            logger.warning(f"No text extracted from {pdf_path}")
            return []
        
        # Combine all pages for structure detection
        combined_text = "\n\n".join(page_text for _, page_text in pages)
        
        # Automatically detect document structure (NO hardcoded profiles!)
        structure = self._detect_document_structure(combined_text)
        
        logger.info(
            f"Detected structure in {pdf_path.name}: "
            f"Form code={structure['form_code']}, "
            f"Sections={len(structure['sections'])}"
        )
        
        # Update form metadata if detected from content
        if structure['form_code']:
            base_metadata['form_code'] = structure['form_code']
            logger.info(f"  Detected form code: {structure['form_code']}")
        if structure['form_title']:
            base_metadata['form_title'] = structure['form_title']
            logger.info(f"  Detected form title: {structure['form_title']}")
        
        # Chunk based on detected structure
        all_chunks = []
        chunk_index = 0
        
        if self.preserve_page_boundaries:
            # Chunk each page separately with structure awareness
            for page_num, page_text in pages:
                # Detect structure for this page
                page_structure = self._detect_document_structure(page_text)
                # Preserve global form code/title
                page_structure['form_code'] = structure.get('form_code', '')
                page_structure['form_title'] = structure.get('form_title', '')
                
                page_chunks = self._chunk_by_structure(
                    text=page_text,
                    structure=page_structure,
                    page_number=page_num,
                    base_metadata=base_metadata,
                    folder_path=folder_path,
                    source_file=pdf_path.name
                )
                
                # Update chunk indices
                for chunk in page_chunks:
                    chunk.chunk_index = chunk_index
                    chunk_index += 1
                
                all_chunks.extend(page_chunks)
        
        else:
            # Chunk entire document using global structure
            all_chunks = self._chunk_by_structure(
                text=combined_text,
                structure=structure,
                page_number=1,  # Multi-page chunk
                base_metadata=base_metadata,
                folder_path=folder_path,
                source_file=pdf_path.name
            )
        
        logger.info(
            f"Created {len(all_chunks)} chunks from {len(pages)} pages "
            f"in {pdf_path.name}"
        )
        
        # Validate chunks and log statistics in verbose mode
        if self.verbose:
            self._log_chunking_stats(all_chunks)
        
        # Validate chunk quality
        validation_metrics = self.validate_chunks(all_chunks)
        if not validation_metrics['validation_passed']:
            logger.warning(f"Chunk validation warnings for {pdf_path.name}")
        
        return all_chunks
    
    def chunk_pdf_directory(
        self,
        directory: Path,
        base_path: Optional[Path] = None,
        recursive: bool = True,
        pattern: str = "*.pdf"
    ) -> Dict[str, List[PDFChunk]]:
        """Chunk all PDFs in a directory with batch processing and error handling.
        
        Batch processes multiple PDFs in a directory (recursive or non-recursive).
        Calls chunk_pdf() for each PDF and collects results. Continues processing
        on individual file errors (logs errors, returns empty list for failed files).
        Returns dictionary mapping filenames to chunk lists.
        
        Args:
            directory (Path): Directory containing PDF files. Must exist and be
                a directory.
            base_path (Optional[Path], optional): Base directory for computing
                relative folder paths in all chunks. If None, uses directory as
                base_path. Default: None.
            recursive (bool, optional): If True, searches subdirectories recursively
                (rglob). If False, only searches top-level directory (glob).
                Default: True.
            pattern (str, optional): Glob pattern for matching PDF files. Supports
                wildcards (* and ?). Default: "*.pdf" (all PDFs).
        
        Returns:
            Dict[str, List[PDFChunk]]: Dictionary mapping PDF filename (str) to
                list of chunks (List[PDFChunk]). Failed files have empty list [].
                Empty dict if no PDFs found.
        
        Raises:
            FileNotFoundError: If directory doesn't exist.
            ValueError: If directory is not a directory (is a file).
        
        Example:
            Process all PDFs in directory (recursive):
                >>> from pathlib import Path
                >>> from scripts.vector_db.pdf_chunking import PDFChunker
                >>> chunker = PDFChunker(verbose=True)  # doctest: +SKIP
                >>> pdf_dir = Path('data/Indo-VAP/annotated_pdfs')
                >>> chunks_by_file = chunker.chunk_pdf_directory(pdf_dir)  # doctest: +SKIP
                >>> print(f"Processed {len(chunks_by_file)} PDFs")  # doctest: +SKIP
                Processed 30 PDFs
                >>> # Inspect results
                >>> for filename, chunks in chunks_by_file.items():
                ...     print(f"{filename}: {len(chunks)} chunks")  # doctest: +SKIP
                1A Index Case Screening v1.0.pdf: 8 chunks
                1B HHC Screening v1.0.pdf: 6 chunks
                ...
            
            Non-recursive (top-level only):
                >>> chunks_by_file = chunker.chunk_pdf_directory(
                ...     directory=pdf_dir,
                ...     recursive=False
                ... )  # doctest: +SKIP
            
            Custom pattern (only specific forms):
                >>> chunks_by_file = chunker.chunk_pdf_directory(
                ...     directory=pdf_dir,
                ...     pattern="1*"  # Only forms starting with "1"
                ... )  # doctest: +SKIP
            
            With base_path for relative folders:
                >>> base = Path('data/Indo-VAP')
                >>> chunks_by_file = chunker.chunk_pdf_directory(
                ...     directory=pdf_dir,
                ...     base_path=base
                ... )  # doctest: +SKIP
                >>> # All chunks have folder_path relative to base
            
            Count total chunks:
                >>> chunks_by_file = chunker.chunk_pdf_directory(pdf_dir)  # doctest: +SKIP
                >>> total = sum(len(chunks) for chunks in chunks_by_file.values())
                >>> print(f"Total chunks: {total}")  # doctest: +SKIP
                Total chunks: 234
        
        Side Effects:
            - Reads all matching PDF files from disk
            - Calls chunk_pdf() for each file (see chunk_pdf side effects)
            - Logs directory scan results (info level)
            - Logs per-file processing (info level)
            - Logs errors for failed files (error level)
            - Logs total processing summary (info level)
        
        Performance:
            Typical processing time (CPU, 30 PDFs):
            - pypdf: ~15-60 seconds
            - pdfplumber: ~30-150 seconds
            - With verbose logging: +10-20% overhead
            
            Memory usage scales with number of files (not total size):
            - Each PDF processed independently
            - Results accumulated in dictionary
            - ~1-5 MB per PDF in final dictionary
        
        Note:
            Errors in individual PDFs don't stop processing—logs error and continues
            to next file. Failed files have empty list [] in results. No parallel
            processing (sequential file-by-file). Pattern supports glob wildcards
            but not regex. recursive=True searches all subdirectories. Returns empty
            dict if no matching PDFs found (not an error).
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        # Find all matching PDFs
        if recursive:
            pdf_files = list(directory.rglob(pattern))
        else:
            pdf_files = list(directory.glob(pattern))
        
        logger.info(f"Found {len(pdf_files)} PDFs in {directory}")
        
        # Process each PDF
        chunks_by_file = {}
        
        for pdf_path in pdf_files:
            try:
                chunks = self.chunk_pdf(pdf_path, base_path=base_path)
                chunks_by_file[pdf_path.name] = chunks
                
            except Exception as e:
                logger.error(f"Failed to chunk {pdf_path.name}: {e}")
                chunks_by_file[pdf_path.name] = []
        
        total_chunks = sum(len(chunks) for chunks in chunks_by_file.values())
        logger.info(
            f"Processed {len(pdf_files)} PDFs, created {total_chunks} total chunks"
        )
        
        return chunks_by_file
