De-identification
=================

The de-identification module provides robust and secure functionality for removing Protected Health Information (PHI) and Personally Identifiable Information (PII) from text data through pseudonymization, with support for country-specific privacy regulations.

.. seealso::
   For detailed information on country-specific regulations and identifiers, see :doc:`country_regulations`.

Overview
--------

The de-identification module implements HIPAA Safe Harbor method compatible de-identification with:

* **Comprehensive PHI/PII Detection**: 18+ identifier types
* **Country-Specific Regulations**: Support for 14 countries (US, EU, GB, CA, AU, IN, ID, BR, PH, ZA, KE, NG, GH, UG)
* **Pseudonymization**: Consistent, cryptographic placeholders
* **Encrypted Storage**: Fernet encryption for mapping tables
* **Date Shifting**: Preserves temporal relationships
* **Validation**: Ensures no PHI leakage
* **Security**: Built with encryption and access control
* **Directory Structure Preservation**: Maintains original file organization

Workflow
--------

The de-identification process is integrated into the main pipeline as Step 2:

**Step 1: Data Extraction**

Excel files are converted to JSONL format with two versions:

* ``results/dataset/Indo-vap/original/`` - All columns preserved
* ``results/dataset/Indo-vap/cleaned/`` - Duplicate columns removed

**Step 2: De-identification** (Optional)

Both subdirectories are processed while maintaining structure:

* ``results/deidentified/Indo-vap/original/`` - De-identified original files
* ``results/deidentified/Indo-vap/cleaned/`` - De-identified cleaned files
* ``results/deidentified/mappings/mappings.enc`` - Encrypted mapping table
* ``results/deidentified/Indo-vap/_deidentification_audit.json`` - Audit log

**Key Features:**

1. **Consistent Pseudonyms**: Same PHI value gets the same pseudonym across all files
2. **Encrypted Mappings**: Single encrypted mapping table shared across all datasets
3. **Structure Preservation**: Output mirrors input directory structure exactly
4. **Recursive Processing**: Automatically processes all subdirectories
5. **Audit Trail**: Complete audit log without exposing original values

Quick Start
-----------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from scripts.utils.deidentify import DeidentificationEngine

    # Initialize engine
    engine = DeidentificationEngine()

    # De-identify text
    original = "Patient John Doe, MRN: 123456, DOB: 01/15/1980"
    deidentified = engine.deidentify_text(original)
    # Output: "Patient [PATIENT-A4B8], MRN: [MRN-X7Y2], DOB: [DATE-1980-01-15]"

    # Save mappings
    engine.save_mappings()

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

    from scripts.utils.deidentify import deidentify_dataset

    # Process entire dataset (maintains directory structure)
    # Input directory contains: original/ and cleaned/ subdirectories
    stats = deidentify_dataset(
        input_dir="results/dataset/Indo-vap",
        output_dir="results/deidentified/Indo-vap",
        process_subdirs=True  # Recursively process subdirectories
    )

    print(f"Processed {stats['texts_processed']} texts")
    print(f"Detected {stats['total_detections']} PHI items")
    
    # Output structure:
    # results/deidentified/Indo-vap/
    #   ├── original/          (de-identified original files)
    #   ├── cleaned/           (de-identified cleaned files)
    #   └── _deidentification_audit.json

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Basic usage - processes subdirectories recursively
    python -m scripts.utils.deidentify \
        --input-dir results/dataset/Indo-vap \
        --output-dir results/deidentified/Indo-vap

    # With validation
    python -m scripts.utils.deidentify \
        --input-dir results/dataset/Indo-vap \
        --output-dir results/deidentified/Indo-vap \
        --validate

    # Specify text fields
    python -m scripts.utils.deidentify \
        --input-dir results/dataset/Indo-vap \
        --output-dir results/deidentified/Indo-vap \
        --text-fields patient_name notes diagnosis
        
    # Disable encryption (not recommended)
    python -m scripts.utils.deidentify \
        --input-dir results/dataset/Indo-vap \
        --output-dir results/deidentified/Indo-vap \
        --no-encryption

Pipeline Integration
~~~~~~~~~~~~~~~~~~~~

The de-identification step processes both ``original/`` and ``cleaned/`` subdirectories
while maintaining the same file structure in the output directory.

.. code-block:: bash

    # Enable de-identification in main pipeline
    python main.py --enable-deidentification

    # Skip de-identification
    python main.py --enable-deidentification --skip-deidentification
    
    # Disable encryption (not recommended for production)
    python main.py --enable-deidentification --no-encryption

**Output Directory Structure:**

.. code-block:: text

    results/
    ├── dataset/
    │   └── Indo-vap/
    │       ├── original/        (extracted JSONL files)
    │       └── cleaned/         (cleaned JSONL files)
    ├── deidentified/
    │   ├── Indo-vap/
    │   │   ├── original/        (de-identified original files)
    │   │   ├── cleaned/         (de-identified cleaned files)
    │   │   └── _deidentification_audit.json
    │   └── mappings/
    │       └── mappings.enc     (encrypted mapping table)
    └── data_dictionary_mappings/

Supported PHI/PII Types
-----------------------

The module detects and de-identifies the following 18+ HIPAA identifier types:

Names
~~~~~

* First names
* Last names
* Full names

Medical Identifiers
~~~~~~~~~~~~~~~~~~~

* Medical Record Numbers (MRN)
* Account numbers
* License/certificate numbers

Government Identifiers
~~~~~~~~~~~~~~~~~~~~~~

* Social Security Numbers (SSN)

Contact Information
~~~~~~~~~~~~~~~~~~~

* Phone numbers (US and international formats)
* Email addresses
* Fax numbers

Geographic Information
~~~~~~~~~~~~~~~~~~~~~~

* Street addresses
* Cities
* States
* ZIP codes

Temporal Information
~~~~~~~~~~~~~~~~~~~~

* Dates (all formats including DOB)
* Ages over 89 (HIPAA requirement)

Technical Identifiers
~~~~~~~~~~~~~~~~~~~~~

* Device identifiers
* URLs
* IP addresses (IPv4)

Custom Identifiers
~~~~~~~~~~~~~~~~~~

* Extensible pattern support
* User-defined PHI types

Pseudonym Formats
-----------------

Different PHI types use different pseudonym formats:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - PHI Type
     - Example Original
     - Pseudonym Format
   * - Name
     - John Doe
     - ``[PATIENT-A4B8C2]``
   * - MRN
     - AB123456
     - ``[MRN-X7Y2Z9]``
   * - SSN
     - 123-45-6789
     - ``[SSN-Q3W8E5]``
   * - Phone
     - (555) 123-4567
     - ``[PHONE-E5R7T9]``
   * - Email
     - patient@example.com
     - ``[EMAIL-T9Y3U8]``
   * - Date
     - 01/15/1980
     - Shifted date or ``[DATE-1]``
   * - Address
     - 123 Main St
     - ``[STREET-Z2X5C8]``
   * - ZIP
     - 12345
     - ``[ZIP-K9L4M7]``
   * - Age >89
     - Age 92
     - ``[AGE-K4L8P6]``

Configuration
-------------

Directory Structure Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The de-identification module automatically processes subdirectories to maintain 
the same file structure between input and output directories:

.. code-block:: python

    from scripts.utils.deidentify import deidentify_dataset

    # Process with subdirectories (default)
    stats = deidentify_dataset(
        input_dir="results/dataset/Indo-vap",
        output_dir="results/deidentified/Indo-vap",
        process_subdirs=True  # Recursively process all subdirectories
    )
    
    # Process only top-level files (no subdirectories)
    stats = deidentify_dataset(
        input_dir="results/dataset/Indo-vap",
        output_dir="results/deidentified/Indo-vap",
        process_subdirs=False  # Only process files in the root directory
    )

**Features:**

* Maintains relative directory structure in output
* Processes both ``original/`` and ``cleaned/`` subdirectories
* Creates output directories automatically
* Preserves file naming conventions
* Single mapping table shared across all subdirectories

DeidentificationConfig
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from scripts.utils.deidentify import DeidentificationConfig, DeidentificationEngine

    config = DeidentificationConfig(
        # Date shifting
        enable_date_shifting=True,
        date_shift_range_days=365,
        preserve_date_intervals=True,
        
        # Security
        enable_encryption=True,
        encryption_key=None,  # Auto-generate if None
        
        # Validation
        enable_validation=True,
        strict_mode=True,
        
        # Logging
        log_detections=True,
        log_level=logging.INFO
    )

    engine = DeidentificationEngine(config=config)

Custom PHI Patterns
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from scripts.utils.deidentify import DetectionPattern, PHIType
    import re

    # Define custom pattern
    custom_pattern = DetectionPattern(
        phi_type=PHIType.CUSTOM,
        pattern=re.compile(r'\bSTUDY-\d{4}\b'),
        priority=85,
        description="Custom Study ID format"
    )

    # Use in de-identification
    deidentified = engine.deidentify_text(
        text="Study ID: STUDY-1234",
        custom_patterns=[custom_pattern]
    )

Advanced Features
-----------------

Date Shifting
~~~~~~~~~~~~~

Date shifting preserves temporal relationships while obscuring actual dates:

.. code-block:: python

    from scripts.utils.deidentify import DateShifter

    shifter = DateShifter(
        shift_range_days=365,
        preserve_intervals=True,
        seed="consistent-seed"
    )

    # All dates shift by same offset
    date1 = shifter.shift_date("01/15/1980")
    date2 = shifter.shift_date("01/20/1980")  # 5 days after date1

    # Interval preserved: date2 - date1 = 5 days

Encrypted Mapping Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~

Mapping tables are stored in a centralized location within the ``results/deidentified/mappings/``
directory:

.. code-block:: python

    from cryptography.fernet import Fernet
    from scripts.utils.deidentify import DeidentificationConfig

    # Generate and save key
    encryption_key = Fernet.generate_key()
    with open('encryption_key.bin', 'wb') as f:
        f.write(encryption_key)

    # Use encrypted storage
    config = DeidentificationConfig(
        enable_encryption=True,
        encryption_key=encryption_key
    )

    engine = DeidentificationEngine(config=config)
    
    # Mappings stored in: results/deidentified/mappings/mappings.enc
    # This single mapping file is used across all datasets and subdirectories

Record De-identification
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # De-identify structured records
    record = {
        "patient_name": "John Doe",
        "mrn": "123456",
        "notes": "Patient has diabetes. DOB: 01/15/1980",
        "lab_value": 95.5  # Numeric field preserved
    }

    # Specify which fields to de-identify
    deidentified = engine.deidentify_record(
        record,
        text_fields=["patient_name", "notes"]
    )

Validation
~~~~~~~~~~

.. code-block:: python

    # Validate de-identified text
    is_valid, issues = engine.validate_deidentification(deidentified_text)

    if not is_valid:
        print(f"Validation failed! Issues: {issues}")
    else:
        print("✓ No PHI detected")

    # Validate entire dataset (processes all subdirectories)
    from scripts.utils.deidentify import validate_dataset

    validation_results = validate_dataset(
        "results/deidentified/Indo-vap"
    )

    print(f"Valid: {validation_results['is_valid']}")
    print(f"Issues: {len(validation_results['potential_phi_found'])}")
    print(f"Files validated: {validation_results['total_files']}")
    print(f"Records validated: {validation_results['total_records']}")

Security
--------

Encryption
~~~~~~~~~~

Mapping storage uses **Fernet** (symmetric encryption):

* Algorithm: AES-128 in CBC mode
* Key management: Separate from data files
* Format: Base64-encoded encrypted JSON

Cryptographic Pseudonyms
~~~~~~~~~~~~~~~~~~~~~~~~~

Pseudonyms are generated using:

* Algorithm: SHA-256 hashing
* Salt: Random or deterministic per session
* Encoding: Base32 for readability
* Property: Irreversible without mapping table

Best Practices
~~~~~~~~~~~~~~

1. **Protect Encryption Keys**

   * Store keys separately from mapping files
   * Use key management systems in production
   * Rotate keys periodically

2. **Enable Validation**

   * Always validate after de-identification
   * Manual review of sample outputs
   * Regular pattern updates

3. **Audit Logging**

   * Enable comprehensive logging
   * Monitor for validation failures
   * Track mapping usage

4. **Access Control**

   * Restrict access to mapping files
   * Separate re-identification permissions
   * Log all mapping exports

HIPAA Compliance
~~~~~~~~~~~~~~~~

The module implements HIPAA Safe Harbor method requirements:

✓ Removes all 18 HIPAA identifiers

✓ Ages over 89 handled appropriately

✓ Geographic subdivisions (ZIP codes) de-identified

✓ Dates shifted to preserve intervals

✓ No re-identification without authorization

Performance
-----------

Benchmarks
~~~~~~~~~~

Typical performance on modern hardware:

* **Text Processing**: ~1,000 records/second
* **Pattern Matching**: ~500 KB/second
* **Mapping Lookup**: O(1) average case
* **Encryption Overhead**: ~5-10% slowdown

Optimization Tips
~~~~~~~~~~~~~~~~~

1. **Batch Processing**: Process files in parallel
2. **Pattern Priority**: Put common patterns first
3. **Caching**: Pseudonyms cached automatically
4. **Validation**: Disable in production if pre-validated

Examples
--------

See ``scripts/utils/deidentify.py`` ``--help`` for command-line usage:

.. code-block:: bash

    python -m scripts.utils.deidentify --help

Examples include:

1. Basic text de-identification
2. Consistent pseudonyms
3. Structured record de-identification
4. Custom patterns
5. Date shifting
6. Batch processing
7. Validation workflow
8. Mapping management
9. Security features

Testing
-------

The de-identification module can be tested using the main pipeline:

.. code-block:: bash

    # Test on a small dataset
    python main.py --enable-deidentification

Expected Output
~~~~~~~~~~~~~~~

When processing the Indo-vap dataset:

.. code-block:: text

    De-identifying files: 100%|██████████| 86/86 [00:08<00:00, 10.34it/s]
    INFO:reportalin:De-identification complete:
    INFO:reportalin:  Texts processed: 1854110
    INFO:reportalin:  Total detections: 365620
    INFO:reportalin:  Unique mappings: 5398
    INFO:reportalin:  Output structure:
    INFO:reportalin:    - results/deidentified/Indo-vap/original/  (de-identified original files)
    INFO:reportalin:    - results/deidentified/Indo-vap/cleaned/   (de-identified cleaned files)

**What happens:**

* Processes both ``original/`` and ``cleaned/`` subdirectories (43 files each = 86 total)
* Detects and replaces PHI/PII in all string fields
* Creates 5,398 unique pseudonym mappings
* Generates encrypted mapping table at ``results/deidentified/mappings/mappings.enc``
* Exports audit log at ``results/deidentified/Indo-vap/_deidentification_audit.json``

**Sample De-identification:**

Before:

.. code-block:: json

    {
        "HHC1": "10200009B",
        "TST_DAT1": "2014-06-11 00:00:00",
        "TST_ENDAT1": "2014-06-14 00:00:00"
    }

After:

.. code-block:: json

    {
        "HHC1": "[MRN-XTHM4A]",
        "TST_DAT1": "[DATE-A4A986]",
        "TST_ENDAT1": "[DATE-B3C874]"
    }

Verification
~~~~~~~~~~~~~

✓ Pattern detection for all PHI types

✓ Pseudonym consistency

✓ Date shifting and intervals

✓ Mapping storage and encryption

✓ Batch processing

✓ Validation

✓ Edge cases and error handling

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**"No files matching '*.jsonl' found"**

.. code-block:: python

    # Solution: Ensure extraction step completed first
    python main.py --skip-deidentification  # Run extraction
    python main.py --enable-deidentification --skip-extraction  # Then deidentify

**Encryption error - "cryptography package not available"**

.. code-block:: bash

    # Solution: Install cryptography
    pip install cryptography>=41.0.0

**Validation fails on de-identified text**

.. code-block:: python

    # Solution: Check pattern priorities and exclusions
    engine.validate_deidentification(text)

**Dates not shifting consistently**

.. code-block:: python

    # Solution: Enable interval preservation
    config = DeidentificationConfig(
        enable_date_shifting=True,
        preserve_date_intervals=True
    )

**Custom patterns not detected**

.. code-block:: python

    # Solution: Increase priority
    custom_pattern = DetectionPattern(
        phi_type=PHIType.CUSTOM,
        pattern=your_pattern,
        priority=90  # Higher priority
    )

**Output directory structure different from input**

.. code-block:: python

    # Solution: Ensure process_subdirs is enabled
    stats = deidentify_dataset(
        input_dir="results/dataset/Indo-vap",
        output_dir="results/deidentified/Indo-vap",
        process_subdirs=True  # Must be True to preserve structure
    )

**"Could not parse date" warnings**

.. code-block:: text

    # These are normal - dates in YYYY-MM-DD format use fallback placeholders
    # The module supports MM/DD/YYYY, Month DD YYYY, and other formats
    # Unsupported formats are replaced with [DATE-HASH] placeholders

API Reference
-------------

For complete API documentation, see the :doc:`../api/scripts.utils.deidentify` module reference.

Key Classes
~~~~~~~~~~~

* :class:`scripts.utils.deidentify.DeidentificationEngine` - Main processing engine
* :class:`scripts.utils.deidentify.PseudonymGenerator` - Pseudonym generation
* :class:`scripts.utils.deidentify.DateShifter` - Date shifting
* :class:`scripts.utils.deidentify.MappingStore` - Encrypted storage
* :class:`scripts.utils.deidentify.PatternLibrary` - PHI patterns

Key Functions
~~~~~~~~~~~~~

* :func:`scripts.utils.deidentify.deidentify_dataset` - Batch processing
* :func:`scripts.utils.deidentify.validate_dataset` - Dataset validation

See Also
--------

* :doc:`quickstart` - Getting started with RePORTaLiN
* :doc:`usage` - General usage guide
* :doc:`configuration` - Configuration options
* :doc:`../api/scripts.utils.deidentify` - API reference
