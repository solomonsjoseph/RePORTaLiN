Architecture
============

This document describes the technical architecture of the RePORTaLiN data pipeline.

System Overview
---------------

RePORTaLiN is built as a modular pipeline with clear separation of concerns:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                     RePORTaLiN System                       │
   ├─────────────────────────────────────────────────────────────┤
   │                                                             │
   │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │
   │  │   Config    │  │   Logging   │  │   Utilities  │       │
   │  │   System    │  │   System    │  │   (Utils)    │       │
   │  └─────────────┘  └─────────────┘  └──────────────┘       │
   │                                                             │
   │  ┌──────────────────────────────────────────────────────┐  │
   │  │              Core Pipeline Modules                   │  │
   │  ├──────────────────────────────────────────────────────┤  │
   │  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │  │
   │  │  │   Dictionary │→ │    Extract   │→ │  Deidentify│ │  │
   │  │  │    Loader    │  │     Data     │  │            │  │  │
   │  │  └──────────────┘  └──────────────┘  └───────────┘  │  │
   │  └──────────────────────────────────────────────────────┘  │
   │                                                             │
   │  ┌──────────────────────────────────────────────────────┐  │
   │  │             Supporting Services                      │  │
   │  ├──────────────────────────────────────────────────────┤  │
   │  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │  │
   │  │  │  Vector DB   │  │     LLM      │  │   Cache   │  │  │
   │  │  │   Service    │  │   Adapters   │  │  Service  │  │  │
   │  │  └──────────────┘  └──────────────┘  └───────────┘  │  │
   │  └──────────────────────────────────────────────────────┘  │
   │                                                             │
   └─────────────────────────────────────────────────────────────┘

Core Components
---------------

Configuration System (config.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Centralized configuration management using dataclasses and environment variables.

**Responsibilities:**

* Load configuration from `config.py` and `.env`
* Provide type-safe access to settings
* Validate configuration on startup
* Support environment-specific overrides

**Key Classes:**

* ``Config``: Main configuration dataclass

Logging System
~~~~~~~~~~~~~~

Comprehensive logging with file rotation and structured output.

**Location:** ``scripts/utils/logging_system.py``

**Features:**

* Automatic log rotation
* Configurable log levels
* Structured logging with timestamps
* Error tracking and reporting

**Key Functions:**

* ``get_logger(name)``: Get a configured logger
* ``setup_logging()``: Initialize logging system

Pipeline Modules
----------------

Dictionary Loader
~~~~~~~~~~~~~~~~~

**Location:** ``scripts/load_dictionary.py``

**Purpose:** Parse and validate data dictionary files

**Key Functions:**

* ``load_data_dictionary(dict_path)``: Load from Excel
* ``parse_field_definitions(df)``: Extract field metadata
* ``validate_dictionary(dict_obj)``: Validate completeness

**Data Flow:**

1. Read Excel file
2. Parse sheets (fields, validation, mappings)
3. Build structured dictionary object
4. Validate completeness and consistency
5. Save for downstream use

Data Extraction
~~~~~~~~~~~~~~~

**Location:** ``scripts/extract_data.py``

**Purpose:** Extract structured data from PDFs and Excel files

**Key Components:**

* **PDF Parser**: Extract text from PDFs
* **LLM Extractor**: Use LLM to identify and extract fields
* **Excel Reader**: Direct column mapping for Excel data
* **Validator**: Validate against data dictionary

**Data Flow:**

1. Read source files (PDF/Excel)
2. Chunk content for processing
3. Extract fields using LLM or direct mapping
4. Validate against dictionary
5. Merge data from multiple sources
6. Generate extraction report

**Extraction Strategies:**

* **Template-based**: For structured forms
* **LLM-based**: For variable layouts
* **Hybrid**: Combine both approaches

De-identification
~~~~~~~~~~~~~~~~~

**Location:** ``scripts/deidentify.py``

**Purpose:** Remove or pseudonymize PII

**Key Components:**

* **PII Detector**: Identify PII fields and patterns
* **Transformers**: Apply de-identification methods
* **Validator**: Verify PII removal
* **Auditor**: Generate audit trail

**De-identification Methods:**

* Date shifting with random offsets
* Name removal/pseudonymization
* Location generalization
* Identifier hashing with secure salt
* Free-text redaction using NER

**Data Flow:**

1. Identify PII fields from dictionary
2. Apply transformations by field type
3. Scan free text for PII patterns
4. Generate de-identification map (secure storage)
5. Validate no PII remains
6. Generate audit report

Supporting Services
-------------------

Vector Database Service
~~~~~~~~~~~~~~~~~~~~~~~~

**Location:** ``scripts/vector_db/``

**Purpose:** Semantic search and document retrieval

**Key Modules:**

* ``vector_store.py``: ChromaDB interface
* ``embeddings.py``: Text embedding generation
* ``adaptive_embeddings.py``: Context-aware embeddings
* ``ingest_pdfs.py``: PDF document ingestion
* ``ingest_records.py``: Record ingestion
* ``pdf_chunking.py``: PDF text chunking
* ``jsonl_chunking_nl.py``: JSONL chunking

**Architecture:**

.. code-block:: text

   ┌─────────────┐
   │  Documents  │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │   Chunker   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Embeddings │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  ChromaDB   │
   │ Vector Store│
   └─────────────┘

LLM Adapters
~~~~~~~~~~~~

**Location:** ``scripts/llm/``

**Purpose:** Abstract LLM provider interactions

**Key Modules:**

* ``base_adapter.py``: Base adapter interface
* Provider-specific adapters (future)

**Design Pattern:** Strategy pattern for swappable LLM providers

**Key Features:**

* Unified interface for multiple providers
* Streaming support
* JSON mode for structured output
* Error handling and retries
* Token counting and cost tracking

Cache Service
~~~~~~~~~~~~~

**Location:** ``scripts/cache/``

**Purpose:** Cache expensive operations

**Use Cases:**

* LLM responses (avoid re-extraction)
* Parsed PDF content
* Validation results
* Embedding vectors

Utilities
---------

Country Regulations
~~~~~~~~~~~~~~~~~~~

**Location:** ``scripts/utils/country_regulations.py``

**Purpose:** Manage regulatory requirements by region

**Key Functions:**

* ``get_pii_fields(region)``: Get PII fields for region
* ``get_date_shift_rules(region)``: Get date shifting rules
* ``validate_compliance(data, region)``: Check compliance

Document Maintenance Toolkit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Location:** ``scripts/utils/doc_maintenance_toolkit.py``

**Purpose:** Maintain documentation quality

**Key Functions:**

* ``check_docstrings(filepath)``: Verify docstring presence
* ``generate_docstring_template(func)``: Generate templates
* ``validate_examples(docstring)``: Test docstring examples

Data Structure Migration
~~~~~~~~~~~~~~~~~~~~~~~~~

**Location:** ``scripts/utils/migrate_data_structure.py``

**Purpose:** Migrate data between schema versions

**Key Functions:**

* ``migrate_to_version(data, target_version)``: Version migration
* ``validate_schema(data, schema)``: Schema validation

Data Flow
---------

End-to-End Data Flow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Input Files                 Processing Stages              Output
   ───────────                 ─────────────────              ──────
   
   Data Dict ──┐
               ├──→ Dictionary Loader ──→ Dict Object ──┐
   Config ─────┘                                         │
                                                         │
   PDFs ───────┐                                         │
               ├──→ Data Extraction ──→ Raw Data ───────┤
   Excel ──────┘         ▲                               │
                         │                               │
                         │                               │
                    Vector DB                            │
                    (Context)                            │
                                                         │
                                                         ▼
   De-ID Rules ─────→ De-identification ──→ Clean Data ──→ Output Files

Error Handling Strategy
~~~~~~~~~~~~~~~~~~~~~~~~

**Levels:**

1. **Validation**: Catch errors early during validation
2. **Graceful Degradation**: Continue processing on non-critical errors
3. **Recovery**: Save partial results before exit
4. **Logging**: Comprehensive error logging for debugging

**Example:**

.. code-block:: python

   try:
       data = extract_from_pdf(pdf_path)
   except ExtractionError as e:
       logger.error(f"Failed to extract from {pdf_path}: {e}")
       # Save partial results
       save_partial_results(partial_data)
       # Continue with next file
       continue

Design Principles
-----------------

Modularity
~~~~~~~~~~

Each component has a single, well-defined responsibility. Components communicate through clear interfaces.

Extensibility
~~~~~~~~~~~~~

New features can be added without modifying existing code:

* Plugin architecture for LLM providers
* Configurable de-identification rules
* Custom validators

Testability
~~~~~~~~~~~

All components are unit-testable:

* Dependency injection for external services
* Mock-friendly interfaces
* Isolated test fixtures

Performance
~~~~~~~~~~~

Optimized for large-scale processing:

* Batch processing
* Parallel execution
* Result caching
* Efficient data structures

Technology Stack
----------------

Core Libraries
~~~~~~~~~~~~~~

* **Python 3.8+**: Programming language
* **pandas**: Data manipulation
* **openpyxl**: Excel file handling
* **PyPDF2/pypdf**: PDF processing

LLM Integration
~~~~~~~~~~~~~~~

* **OpenAI API**: GPT models
* **Anthropic API**: Claude models (future)
* **Langchain**: LLM orchestration (future)

Vector Database
~~~~~~~~~~~~~~~

* **ChromaDB**: Vector storage and retrieval
* **sentence-transformers**: Text embeddings
* **HuggingFace**: Embedding models

Development Tools
~~~~~~~~~~~~~~~~~

* **pytest**: Testing framework
* **black**: Code formatting
* **flake8**: Linting
* **mypy**: Type checking
* **sphinx**: Documentation generation

Deployment Considerations
--------------------------

Environment Setup
~~~~~~~~~~~~~~~~~

1. Python virtual environment
2. Environment variables in `.env`
3. Configuration in `config.py`
4. Data directories structure

Resource Requirements
~~~~~~~~~~~~~~~~~~~~~

* **CPU**: Multi-core for parallel processing
* **RAM**: 8GB minimum, 16GB recommended
* **Disk**: 2GB for app, varies for data
* **Network**: For LLM API calls

Scalability
~~~~~~~~~~~

* Horizontal: Run multiple instances for different studies
* Vertical: Increase batch size and worker count
* Caching: Reduce redundant LLM calls

Security
~~~~~~~~

* API keys in environment variables (not in code)
* Secure storage of de-identification mappings
* Encrypted data at rest (when required)
* Audit logging for compliance

Future Enhancements
-------------------

Planned Features
~~~~~~~~~~~~~~~~

* Web interface for pipeline management
* Real-time processing dashboard
* Advanced validation rules engine
* Multi-language support
* Distributed processing for large-scale studies

See :doc:`contributing` for information on contributing to these features.
