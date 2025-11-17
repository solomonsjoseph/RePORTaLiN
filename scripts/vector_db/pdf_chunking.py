"""PDF chunking and processing for annotated documents."""

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
    """PDF chunk with page and form metadata."""
    page_number: int = 1
    folder_path: str = ""
    form_code: str = ""
    form_title: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PDF chunk to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "page_number": self.page_number,
            "folder_path": self.folder_path,
            "form_code": self.form_code,
            "form_title": self.form_title
        })
        return base_dict


class PDFChunker:
    """PDF chunking for annotated documents with metadata preservation."""
    
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
        """Initialize PDF chunker."""
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
        """Extract text from PDF using pypdf."""
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
        """Extract text from PDF using pdfplumber."""
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
        """Extract text from PDF using configured extraction method."""
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
        """Extract structured tables from PDF using pdfplumber."""
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
        """Extract PDF AcroForm field values from annotated documents."""
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
        """Enrich chunk metadata with PDF document properties."""
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
        """Validate chunk quality and return metrics."""
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
        """Log detailed chunking statistics in verbose mode."""
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
        """Clean up extracted PDF text."""
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
        """Detect document structure from text and filename."""
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
        """Chunk text based on detected document structure."""
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
        """Create a PDFChunk with all metadata."""
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
        """Extract and chunk a PDF file."""
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
        """Chunk all PDFs in a directory."""
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
