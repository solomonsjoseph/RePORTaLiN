De-identification
=================

**For Users: Protecting Privacy**

This feature helps you protect sensitive patient information by replacing real names, dates, 
and other personal details with safe placeholders. It follows medical privacy rules from 
14 different countries.

.. versionchanged:: 0.3.0
   Enhanced privacy protection with improved detection and better support for international regulations.

.. seealso::
   For information about privacy rules in specific countries, see :doc:`country_regulations`.

Overview
--------

The privacy protection feature can detect and replace 21 types of personal information including:

* **Names and Addresses**: Patient names, street addresses, cities
* **Dates**: Birth dates, admission dates, appointment dates  
* **ID Numbers**: Social security numbers, medical record numbers, account numbers
* **Contact Info**: Phone numbers, email addresses, website URLs
* **Encrypted Storage**: Fernet encryption for mapping tables with secure key management
* **Date Shifting**: Preserves temporal relationships while shifting dates by consistent offset
* **Validation**: Comprehensive validation to ensure no PHI leakage in de-identified output
* **Security**: Built-in encryption, access control, and audit trail capabilities
* **Directory Structure Preservation**: Maintains original file organization during batch processing

What's New in |version|
~~~~~~~~~~~~~~~~~~~~~~~~

**Better Privacy Protection**:
  - Improved detection of sensitive information
  - More secure replacement methods
  - Easier to use with better error messages

**Enhanced Security**:
  - Stronger encryption for mapping files
  - Better protection of patient information
  - Comprehensive audit trail for compliance

**Improved Documentation**:
  - Clear examples for common tasks
  - Step-by-step privacy protection guides
  - Easy-to-follow security best practices

How It Works
------------

Privacy protection happens automatically as part of the data processing:

**Step 1: Data Extraction**

Your Excel files are converted to a simpler format (JSONL):

* ``output/dataset/Indo-vap/original/`` - All your data preserved
* ``output/dataset/Indo-vap/cleaned/`` - Duplicate information removed

**Step 2: Privacy Protection** (Optional)

Both folders are protected while keeping the same structure:

* ``output/deidentified/Indo-vap/original/`` - Protected original files
* ``output/deidentified/Indo-vap/cleaned/`` - Protected cleaned files
* ``output/deidentified/mappings/mappings.enc`` - Encrypted lookup table
* ``output/deidentified/Indo-vap/_deidentification_audit.json`` - Record of changes

**What You Get:**

1. **Consistent Replacement**: The same name always gets the same safe placeholder
2. **Secure Storage**: Your lookup table is encrypted and protected
3. **Same Organization**: Protected files are organized exactly like your original files
4. **Complete Record**: Full audit trail of what was changed (without showing the original values)
5. **Easy Review**: You can verify the protection worked correctly

Getting Started
---------------

Basic Usage
~~~~~~~~~~~

To protect patient privacy in your data, run:

.. code-block:: bash

   # Protect data for United States privacy rules
   python main.py --enable-deidentification --countries US

   # Protect data for multiple countries
   python main.py --enable-deidentification --countries IN US GB

This will:
- Find and replace sensitive information like names, dates, and phone numbers
- Create protected versions of your files
- Save an encrypted lookup table so you can track changes
- Generate a report showing what was protected

.. _deidentification-what-gets-protected:

What Gets Protected
~~~~~~~~~~~~~~~~~~~

The privacy feature protects **21 types** of sensitive information including:

**Names and Identifiers:**
  - First names, last names, full patient names
  - Medical record numbers (MRN)
  - Social security numbers (SSN)
  - Account numbers, license numbers

**Contact Information:**
  - Phone numbers
  - Email addresses
  - Street addresses, cities, states, ZIP codes
  - Website URLs and IP addresses

**Dates and Ages:**
  - Birth dates, appointment dates, admission dates
  - Ages over 89 (HIPAA requirement)

**Device and Location:**
  - Device identifiers
  - Geographic locations
  - Organization names

For developer information about the Public API, see :doc:`../api/scripts.deidentify`.

.. _deidentification-basic-usage:

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from scripts.deidentify import DeidentificationEngine

    # Initialize engine
    engine = DeidentificationEngine()

    # De-identify text
    original = "Patient John Doe, MRN: 123456, DOB: 01/15/1980"
    deidentified = engine.deidentify_text(original)
    # Output: "Patient [PATIENT-A4B8], MRN: [MRN-X7Y2], DOB: [DATE-1980-01-15]"

    # Save mappings
    engine.save_mappings()

.. _deidentification-batch-processing:
    # Output: "Patient [PATIENT-A4B8], MRN: [MRN-X7Y2], DOB: [DATE-1980-01-15]"

    # Save mappings
    engine.save_mappings()

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

    from scripts.deidentify import deidentify_dataset

    # Process entire dataset (maintains directory structure)
    # Input directory contains: original/ and cleaned/ subdirectories
    stats = deidentify_dataset(
        input_dir="output/dataset/Indo-vap",
        output_dir="output/deidentified/Indo-vap",
        process_subdirs=True  # Recursively process subdirectories
    )

    print(f"Processed {stats['texts_processed']} texts")
    print(f"Detected {stats['total_detections']} PHI items")
    
    # Output structure:
    # output/deidentified/Indo-vap/
    #   ├── original/          (de-identified original files)
    #   ├── cleaned/           (de-identified cleaned files)
    #   └── _deidentification_audit.json

.. _deidentification-advanced-usage:

Advanced Usage
--------------

.. _deidentification-with-config:

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

Configure de-identification behavior with ``DeidentificationConfig``:

.. code-block:: python

    from scripts.deidentify import DeidentificationEngine, DeidentificationConfig
    
    # Create custom configuration
    config = DeidentificationConfig(
        enable_date_shifting=True,
        date_shift_range_days=365,
        preserve_date_intervals=True,
        enable_encryption=True,
        enable_validation=True,
        strict_mode=True,
        countries=['US', 'IN'],
        enable_country_patterns=True
    )
    
    # Use configuration
    engine = DeidentificationEngine(config=config)
    text = "Patient John Doe, MRN: AB123456, DOB: 01/15/1980"
    deidentified = engine.deidentify_text(text)

.. _deidentification-custom-patterns:

Custom Detection Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~

Add organization-specific patterns:

.. code-block:: python

    from scripts.deidentify import (
        DeidentificationEngine,
        PHIType,
        DetectionPattern
    )
    import re
    
    # Define custom pattern for employee IDs
    custom_pattern = DetectionPattern(
        phi_type=PHIType.CUSTOM,
        pattern=re.compile(r'EMP-\d{6}'),
        priority=85,
        description="Employee ID format: EMP-XXXXXX"
    )
    
    # Use with engine
    engine = DeidentificationEngine()
    text = "Employee EMP-123456 accessed record"
    deidentified = engine.deidentify_text(text, custom_patterns=[custom_pattern])

.. _deidentification-validation:

Validation
~~~~~~~~~~

Validate de-identified datasets to ensure no PHI leakage:

.. code-block:: python

    from scripts.deidentify import validate_dataset
    
    # Validate de-identified output
    validation = validate_dataset(
        dataset_dir="output/deidentified/Indo-vap"
    )
    
    if validation['is_valid']:
        print("✓ No PHI detected in output")
    else:
        print(f"⚠ Found {len(validation['potential_phi_found'])} issues")
        for issue in validation['potential_phi_found']:
            print(f"  - {issue['file']}: {issue['text']}")

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Basic usage - processes subdirectories recursively
    python -m scripts.deidentify \
        --input-dir output/dataset/Indo-vap \
        --output-dir output/deidentified/Indo-vap

    # With validation
    python -m scripts.deidentify \
        --input-dir output/dataset/Indo-vap \
        --output-dir output/deidentified/Indo-vap \
        --validate

    # Specify text fields
    python -m scripts.deidentify \
        --input-dir output/dataset/Indo-vap \
        --output-dir output/deidentified/Indo-vap \
        --text-fields patient_name notes diagnosis
        
    # Disable encryption (not recommended)
    python -m scripts.deidentify \
        --input-dir output/dataset/Indo-vap \
        --output-dir output/deidentified/Indo-vap \
        --no-encryption

.. _deidentification-pipeline-integration:

Pipeline Integration
~~~~~~~~~~~~~~~~~~~~

The de-identification step processes both ``original/`` and ``cleaned/`` subdirectories
while maintaining the same file structure in the output directory.

.. code-block:: bash

    # Enable de-identification in main pipeline
    python main.py --enable-deidentification

    # With multi-country support
    python main.py --enable-deidentification --countries IN US GB
    
    # Disable encryption (not recommended for production)
    python main.py --enable-deidentification --no-encryption

**Output Directory Structure:**

.. code-block:: text

    output/
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

.. important::
   **Version Control Best Practices**
   
   The ``.gitignore`` file is pre-configured with security best practices:
   
   **Safe to Track in Git:**
   
   * ✅ De-identified datasets (``output/deidentified/Indo-vap/``)
   * ✅ Data dictionary mappings (``output/data_dictionary_mappings/``)
   * ✅ Source code and documentation
   
   **Never Commit to Git:**
   
   * ❌ Original datasets with PHI (``output/dataset/``)
   * ❌ Deidentification mappings (``output/deidentified/mappings/``)
   * ❌ Encryption keys (``*.key``, ``*.pem``, ``*.fernet``)
   * ❌ Audit logs (``*_deidentification_audit.json``)
   
   Always review ``git status`` before committing to ensure no PHI/PII files are staged.

Supported PHI/PII Types
-----------------------

The tool detects and de-identifies the following 21 HIPAA identifier types:

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

* Easy to extend with new detection rules
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

The de-identification tool automatically processes subfolders to maintain 
the same file structure between input and output directories:

.. code-block:: python

    from scripts.deidentify import deidentify_dataset

    # Process with subdirectories (default)
    stats = deidentify_dataset(
        input_dir="output/dataset/Indo-vap",
        output_dir="output/deidentified/Indo-vap",
        process_subdirs=True  # Recursively process all subdirectories
    )
    
    # Process only top-level files (no subdirectories)
    stats = deidentify_dataset(
        input_dir="output/dataset/Indo-vap",
        output_dir="output/deidentified/Indo-vap",
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

    from scripts.deidentify import DeidentificationConfig, DeidentificationEngine

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

    from scripts.deidentify import DetectionPattern, PHIType
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

Date shifting preserves temporal relationships while obscuring actual dates.
The date shifter automatically uses intelligent multi-format parsing with country-specific defaults:

.. code-block:: python

    from scripts.deidentify import DateShifter

    # For India (DD/MM/YYYY format priority)
    shifter_india = DateShifter(
        shift_range_days=365,
        preserve_intervals=True,
        country_code="IN"
    )

    # All dates shift by same offset, format preserved
    date1 = shifter_india.shift_date("04/09/2014")  # September 4, 2014 (DD/MM/YYYY)
    date2 = shifter_india.shift_date("09/09/2014")  # September 9, 2014
    # Output: 14/12/2013, 19/12/2013 (5 days interval preserved)
    
    # ISO 8601 format also supported
    date3 = shifter_india.shift_date("2014-09-04")  # September 4, 2014
    # Output: 2013-12-14 (format preserved)

    # For United States (MM/DD/YYYY format priority)
    shifter_us = DateShifter(
        shift_range_days=365,
        preserve_intervals=True,
        country_code="US"
    )

    date4 = shifter_us.shift_date("04/09/2014")  # April 9, 2014 (MM/DD/YYYY)
    # Output: Different interpretation due to country format

**Supported Date Formats** (auto-detected):

* **ISO 8601**: ``YYYY-MM-DD`` (e.g., 2014-09-04) - International standard, all countries
* **Slash-separated**: ``DD/MM/YYYY`` or ``MM/DD/YYYY`` (e.g., 04/09/2014)
* **Hyphen-separated**: ``DD-MM-YYYY`` or ``MM-DD-YYYY`` (e.g., 04-09-2014)
* **Dot-separated**: ``DD.MM.YYYY`` (e.g., 04.09.2014) - European format

**Primary Format by Country:**

* **DD/MM/YYYY** (Day first): India (IN), UK (GB), Australia (AU), Indonesia (ID), 
  Brazil (BR), South Africa (ZA), EU countries, Kenya (KE), Nigeria (NG), 
  Ghana (GH), Uganda (UG)
* **MM/DD/YYYY** (Month first): United States (US), Philippines (PH), Canada (CA)

**Key Features:**

* Intelligent multi-format detection (tries multiple formats automatically)
* Original format preservation (shifted dates maintain the input format)
* Consistent offset across all dates in a dataset
* Temporal relationships preserved (intervals between dates maintained)
* Country-specific format priority
* Fallback to [DATE-HASH] placeholder only if all formats fail

Understanding Date Format Handling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.6.0
   Improved date parsing with country-specific format priority and smart validation.

The date shifter uses an intelligent algorithm to handle ambiguous dates correctly:

**The Ambiguity Problem**

Dates like ``08/09/2020`` or ``12/12/2012`` can be interpreted in multiple ways:

.. list-table::
   :header-rows: 1
   :widths: 20 25 25 30

   * - Date String
     - US Format (MM/DD)
     - India Format (DD/MM)
     - Ambiguity
   * - ``08/09/2020``
     - August 9, 2020
     - September 8, 2020
     - ⚠️ Both valid
   * - ``12/12/2012``
     - December 12, 2012
     - December 12, 2012
     - ⚠️ Symmetric date
   * - ``13/05/2020``
     - ❌ Invalid (no 13th month)
     - May 13, 2020
     - ✅ Unambiguous
   * - ``05/25/2020``
     - May 25, 2020
     - ❌ Invalid (no 25th month)
     - ✅ Unambiguous

**The Solution: Country-Based Priority with Smart Validation**

The date shifter uses a three-step algorithm:

1. **Try ISO 8601 First** (``YYYY-MM-DD``): Always unambiguous, works for all countries
2. **Try Country-Specific Format**: Use the country's preferred interpretation
3. **Smart Validation**: Reject formats that are logically impossible

**Algorithm Details:**

.. code-block:: python

    # Example: Processing "13/05/2020" for India (DD/MM preference)
    
    Step 1: Try ISO 8601 (YYYY-MM-DD)
      Result: ❌ Doesn't match pattern
    
    Step 2: Try DD/MM/YYYY (India preference)
      Parse: ✅ Day=13, Month=05 (May 13, 2020)
      Validate: first_num=13 > 12 ✅ Valid (day can be >12)
      Result: ✅ Success! → May 13, 2020
    
    # Example: Processing "13/05/2020" for USA (MM/DD preference)
    
    Step 1: Try ISO 8601 (YYYY-MM-DD)
      Result: ❌ Doesn't match pattern
    
    Step 2: Try MM/DD/YYYY (USA preference)
      Parse: ❌ Month=13 is invalid (only 12 months)
      Result: Parsing fails, try next format
    
    Step 3: Try DD/MM/YYYY (fallback)
      Parse: ✅ Day=13, Month=05
      Result: ✅ Success! → May 13, 2020

**Smart Validation Rules:**

* If first number > 12 → **Must be day** (can't be month)
* If second number > 12 → **Must be day** (can't be month)  
* If both numbers ≤ 12 → **Trust country preference** (ambiguous case)

**Examples by Country:**

.. code-block:: python

    from scripts.deidentify import DateShifter
    
    # India: DD/MM/YYYY preference
    shifter_india = DateShifter(country_code="IN")
    
    shifter_india.shift_date("2020-01-15")   # ISO → Always Jan 15, 2020
    shifter_india.shift_date("13/05/2020")   # Unambiguous → May 13, 2020
    shifter_india.shift_date("08/09/2020")   # Ambiguous → Sep 8, 2020 (DD/MM)
    shifter_india.shift_date("12/12/2012")   # Symmetric → Dec 12, 2012 (DD/MM)
    
    # United States: MM/DD/YYYY preference
    shifter_us = DateShifter(country_code="US")
    
    shifter_us.shift_date("2020-01-15")      # ISO → Always Jan 15, 2020
    shifter_us.shift_date("13/05/2020")      # Unambiguous → May 13, 2020
    shifter_us.shift_date("08/09/2020")      # Ambiguous → Aug 9, 2020 (MM/DD)
    shifter_us.shift_date("12/12/2012")      # Symmetric → Dec 12, 2012 (MM/DD)

**Best Practices:**

1. **Use ISO 8601 when possible** (``YYYY-MM-DD``): Eliminates all ambiguity
2. **Set country code correctly**: Ensures consistent interpretation within your dataset
3. **Validate output**: Review shifted dates to ensure they make sense
4. **Document format**: Record which format your source data uses

.. tip::
   For symmetric dates like ``12/12/2012`` or ``01/01/2020``, the interpretation 
   doesn't affect the result since both formats yield the same date. However, 
   consistency is still maintained for audit purposes.

.. warning::
   Mixing date formats within a single dataset (e.g., some files using DD/MM and 
   others using MM/DD) can lead to inconsistent interpretations. Always use a 
   consistent format across your dataset, preferably ISO 8601.

Encrypted Mapping Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~

Mapping tables are stored in a centralized location within the ``output/deidentified/mappings/``
directory:

.. code-block:: python

    from cryptography.fernet import Fernet
    from scripts.deidentify import DeidentificationConfig

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
    
    # Mappings stored in: output/deidentified/mappings/mappings.enc
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
    from scripts.deidentify import validate_dataset

    validation_results = validate_dataset(
        "output/deidentified/Indo-vap"
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

* Encryption method: AES-128 in CBC mode
* Key management: Separate from data files
* Format: Base64-encoded encrypted JSON

Cryptographic Pseudonyms
~~~~~~~~~~~~~~~~~~~~~~~~~

Pseudonyms are generated using:

* Hash method: SHA-256 hashing
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
   * Regular updates to detection rules

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

The tool follows HIPAA Safe Harbor requirements:

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
* **Detection Speed**: ~500 KB/second
* **Mapping Lookup**: O(1) average case
* **Encryption Overhead**: ~5-10% slowdown

Optimization Tips
~~~~~~~~~~~~~~~~~

1. **Batch Processing**: Process files in parallel
2. **Detection Order**: Put common items first
3. **Caching**: Pseudonyms cached automatically
4. **Validation**: Disable in production if pre-validated

Examples
--------

See ``scripts/deidentify.py`` ``--help`` for command-line usage:

.. code-block:: bash

    python -m scripts.deidentify --help

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

The de-identification tool can be tested using the main process:

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
    INFO:reportalin:    - output/deidentified/Indo-vap/original/  (de-identified original files)
    INFO:reportalin:    - output/deidentified/Indo-vap/cleaned/   (de-identified cleaned files)

**What happens:**

* Processes both ``original/`` and ``cleaned/`` subdirectories (43 files each = 86 total)
* Detects and replaces PHI/PII in all string fields
* Creates 5,398 unique pseudonym mappings
* Generates encrypted mapping table at ``output/deidentified/mappings/mappings.enc``
* Exports audit log at ``output/deidentified/Indo-vap/_deidentification_audit.json``

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

✓ Detection for all PHI types

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

    # Solution: Check detection order and exclusions
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
        pattern=your_detection_rule,
        priority=90  # Higher priority
    )

**Output directory structure different from input**

.. code-block:: python

    # Solution: Ensure process_subdirs is enabled
    stats = deidentify_dataset(
        input_dir="output/dataset/Indo-vap",
        output_dir="output/deidentified/Indo-vap",
        process_subdirs=True  # Must be True to preserve structure
    )

**"Could not parse date" warnings**

.. code-block:: text

    # The tool uses smart multi-format date recognition
    # Supported formats (auto-detected, original format preserved):
    #   - YYYY-MM-DD: ISO 8601 standard (e.g., 2014-09-04)
    #   - DD/MM/YYYY or MM/DD/YYYY: Slash-separated (e.g., 04/09/2014)
    #   - DD-MM-YYYY or MM-DD-YYYY: Hyphen-separated (e.g., 04-09-2014)
    #   - DD.MM.YYYY: Dot-separated European format (e.g., 04.09.2014)
    # 
    # Format priority based on country:
    #   - DD/MM/YYYY priority: India, UK, Australia, Indonesia, Brazil, South Africa, EU, Kenya, Nigeria, Ghana, Uganda
    #   - MM/DD/YYYY priority: United States, Philippines, Canada
    # 
    # Only truly unsupported formats are replaced with [DATE-HASH] placeholders

**Date format interpretation and preservation**

The date shifter automatically tries multiple formats and preserves the original format:

.. code-block:: text

    For India (IN) with DD/MM/YYYY priority:
    - Input: 04/09/2014 → Interpreted as September 4, 2014 (DD/MM/YYYY)
    - Output: 14/12/2013 (format preserved: DD/MM/YYYY)
    
    - Input: 2014-09-04 → Interpreted as September 4, 2014 (ISO 8601)
    - Output: 2013-12-14 (format preserved: YYYY-MM-DD)
    
    For United States (US) with MM/DD/YYYY priority:
    - Input: 04/09/2014 → Interpreted as April 9, 2014 (MM/DD/YYYY)
    - Output: 10/23/2013 (format preserved: MM/DD/YYYY)
    
    - Input: 2014-04-09 → Interpreted as April 9, 2014 (ISO 8601)
    - Output: 2013-10-23 (format preserved: YYYY-MM-DD)
    
    For all countries:
    - 2014-09-04 is interpreted as September 4, 2014 (YYYY-MM-DD)
    - Replaced with: [DATE-HASH] pseudonym

Technical Reference
-------------------

For complete technical details, see the :doc:`../api/scripts.deidentify` documentation.

Key Classes
~~~~~~~~~~~

* :class:`scripts.deidentify.DeidentificationEngine` - Main processing engine
* :class:`scripts.deidentify.PseudonymGenerator` - Pseudonym generation
* :class:`scripts.deidentify.DateShifter` - Date shifting
* :class:`scripts.deidentify.MappingStore` - Encrypted storage
* :class:`scripts.deidentify.PatternLibrary` - PHI patterns

Key Functions
~~~~~~~~~~~~~

* :func:`scripts.deidentify.deidentify_dataset` - Batch processing
* :func:`scripts.deidentify.validate_dataset` - Dataset validation

Migration Guide
---------------

**Breaking Changes**: None - The de-identification tool is fully backward compatible

**New Features** (Available in current version):

1. **Use Explicit Imports** (Recommended):

   .. code-block:: python
   
      # Recommended import style
      from scripts.deidentify import DeidentificationEngine
      engine = DeidentificationEngine()

2. **Type Checking Benefits**:
   
   If you use type checkers (mypy, pyright), you'll get better type inference:
   
   .. code-block:: python
   
      # Type checkers now understand return types
      result: None = engine.save_mappings()  # Correctly inferred as None

3. **API Discovery**:
   
   You can now see exactly what's public:
   
   .. code-block:: python
   
      from scripts import deidentify
      print(deidentify.__all__)
      # ['PHIType', 'DetectionPattern', 'DeidentificationConfig', ...]

**No Changes Required**: All existing code continues to work without modification.

See Also
--------

**Related User Guides**:

* :doc:`quickstart` - Getting started with RePORTaLiN
* :doc:`usage` - General usage guide and examples
* :doc:`configuration` - De-identification configuration options
* :doc:`country_regulations` - Country-specific privacy compliance
* :doc:`troubleshooting` - Common issues and solutions

**API & Technical References**:

* :doc:`../api/scripts.deidentify` - Complete technical documentation
* :doc:`../developer_guide/contributing` - Best practices for error handling and design
* :doc:`../developer_guide/extending` - Extending de-identification features
* :doc:`../changelog` - Version 0.0.6 changelog

**External Resources**:

* `HIPAA Safe Harbor Method <https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html>`_ - Official HIPAA de-identification guidance
* `GDPR Article 4(5) <https://gdpr.eu/article-4-definitions/>`_ - GDPR pseudonymization definition
* `DPDPA 2023 (India) <https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf>`_ - Indian data protection regulations
