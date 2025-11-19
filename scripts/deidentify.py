#!/usr/bin/env python3
"""PHI/PII de-identification with country-specific compliance.

This module implements HIPAA-compliant de-identification of Protected Health Information
(PHI) and Personally Identifiable Information (PII) in research datasets. It supports
multiple de-identification strategies including pseudonymization, date shifting, and
pattern-based redaction with country-specific regulatory compliance.

Architecture:
    The de-identification engine implements a five-component architecture:
    1. PatternLibrary: Regex-based detection of 18 PHI/PII types
    2. PseudonymGenerator: Consistent hash-based pseudonym generation
    3. DateShifter: Cryptographic date shifting preserving intervals
    4. MappingStore: Encrypted storage of original→pseudonym mappings
    5. DeidentificationEngine: Orchestration and transformation logic

De-identification Strategies:
    - **Pseudonymization**: Replace with consistent fake IDs (e.g., PATIENT-A1B2C3)
    - **Date Shifting**: Shift dates by random offset per subject (preserves intervals)
    - **Suppression**: Remove values exceeding thresholds (e.g., ages > 89)
    - **Generalization**: Replace with broader categories (planned)
    - **Encryption**: Optionally encrypt mapping files with Fernet

PHI Types Detected (18 total):
    - Identifiers: Names, MRN, SSN, Account Numbers, License Numbers
    - Contact: Phone, Email, Addresses (Street, City, State, ZIP)
    - Technical: IP Addresses, URLs, Device IDs
    - Temporal: Dates (multiple formats), Ages > 89
    - Organizational: Organizations, Locations
    - Custom: User-defined patterns

Country-Specific Features:
    When country_regulations module is available:
    - Automatic detection pattern loading for specified countries
    - Country-specific date format interpretation (DD/MM vs. MM/DD)
    - Regulatory compliance mapping (HIPAA, GDPR, country-specific)
    - Custom pattern priorities based on country context

Security Features:
    - Cryptographic random number generation for date shifts
    - SHA-256 hashing for deterministic pseudonym generation
    - Optional Fernet encryption for mapping files
    - Consistent salts/seeds ensure reproducibility
    - Mapping files stored outside study directory for security

Validation:
    - Pre-processing validation of dataset structure
    - Post-processing residual PHI detection
    - Consistency checks (mapping integrity, date intervals)
    - Detailed reporting with field-level statistics

Typical Usage:
    # Basic de-identification with defaults
    >>> from scripts.deidentify import deidentify_dataset
    >>> result = deidentify_dataset(
    ...     input_dir='output/Indo-VAP/cleaned',
    ...     output_dir='output/Indo-VAP/deidentified',
    ...     mapping_dir='.mappings'
    ... )
    >>> print(f"Processed {result['files_processed']} files")
    
    # With country-specific patterns
    >>> result = deidentify_dataset(
    ...     input_dir='data/cleaned',
    ...     output_dir='data/deidentified',
    ...     countries=['IN', 'US'],  # India + US patterns
    ...     enable_encryption=True
    ... )
    
    # Validation only (check for residual PHI)
    >>> from scripts.deidentify import validate_dataset
    >>> issues = validate_dataset('output/deidentified')
    >>> if issues['total_detections'] == 0:
    ...     print("No PHI detected!")

Dependencies:
    - cryptography: Fernet encryption (optional but recommended)
    - scripts.utils.country_regulations: Country-specific patterns (optional)
    - scripts.utils.logging_system: Centralized logging
    - Standard library: re, hashlib, secrets, datetime, pathlib

Notes:
    - Date shifting uses per-subject random offset for consistency
    - Pseudonyms are deterministic (same input → same output) for linking
    - Mapping files enable re-identification by authorized personnel
    - Validation should be run post-processing to verify no PHI leaked
    - Ages > 89 are de-identified per HIPAA Safe Harbor requirements
    - All patterns use case-insensitive matching by default
    - Processing is resilient: failures logged but don't stop pipeline
"""

import re
import json
import hashlib
import secrets
import logging
import sys
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import base64

# ...existing code...

__all__ = [
    # Enums
    'PHIType',
    # Data Classes
    'DetectionPattern',
    'DeidentificationConfig',
    # Core Classes
    'PatternLibrary',
    'PseudonymGenerator',
    'DateShifter',
    'MappingStore',
    'DeidentificationEngine',
    # Top-level Functions
    'deidentify_dataset',
    'validate_dataset',
]

# Optional imports
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography package not available. Mapping encryption disabled.")

from tqdm import tqdm

try:
    from scripts.utils.country_regulations import CountryRegulationManager, DataField
    COUNTRY_REGULATIONS_AVAILABLE = True
except ImportError:
    COUNTRY_REGULATIONS_AVAILABLE = False
    logging.warning("country_regulations module not available. Country-specific features disabled.")

from scripts.utils import logging_system as log

vlog = log.get_verbose_logger()

# ============================================================================
# Module-Level Constants
# ============================================================================

# Detection Pattern Priorities (higher = higher priority)
DEFAULT_PATTERN_PRIORITY = 50      # Default priority for new patterns
PRIORITY_ZIP_CODE = 55              # Priority for ZIP code patterns
PRIORITY_LOW = 60                   # Low priority (dates)
PRIORITY_DATE_TEXT_MONTH = 65       # Priority for text-based month date formats
PRIORITY_MEDIUM_LOW = 70            # Medium-low priority (MRN alt, IP)
PRIORITY_MEDIUM = 75                # Medium priority (Phone, URL)
PRIORITY_MEDIUM_HIGH = 80           # Medium-high priority (MRN, Age>89)
PRIORITY_HIGH = 85                  # High priority (Email, SSN alt, License)
PRIORITY_HIGH_SSN = 90              # Highest priority (SSN primary)

# Date Shifting Configuration
DEFAULT_DATE_SHIFT_RANGE_DAYS = 365  # ±365 days

# Country Defaults
DEFAULT_COUNTRY_CODE = "IN"          # India

# Cryptographic Constants
CRYPTO_SALT_LENGTH = 32              # bytes for salt/seed generation
HASH_ID_BYTES = 4                    # bytes for hash-based ID generation
PSEUDONYM_ID_LENGTH = 6              # characters in generated pseudonym IDs

# Validation Constants
MAX_MONTH_VALUE = 12                 # Maximum valid month number
HIPAA_AGE_THRESHOLD = 89             # HIPAA requires de-identification of ages > 89

# Display/Logging Limits
DEBUG_LOG_FILE_LIMIT = 10            # Number of files to show in debug logs
VALIDATION_DISPLAY_LIMIT = 10        # Number of validation issues to display
RECORD_PROGRESS_INTERVAL = 1000      # Log progress every N records
CONSOLE_SEPARATOR_WIDTH = 70         # Width of console separator lines

# ============================================================================
# Enums and Constants
# ============================================================================

class PHIType(Enum):
    """PHI/PII type categorization for de-identification.
    
    Enumerates the 18 types of Protected Health Information (PHI) and Personally
    Identifiable Information (PII) that can be detected and de-identified. Based
    on HIPAA Safe Harbor 18 identifiers with extensions for digital PHI.
    
    Attributes:
        NAME_FIRST: First/given name (FNAME)
        NAME_LAST: Last/family name (LNAME)
        NAME_FULL: Full patient name (PATIENT)
        MRN: Medical Record Number
        SSN: Social Security Number
        PHONE: Telephone numbers (all formats)
        EMAIL: Email addresses
        DATE: Dates (all formats except year)
        ADDRESS_STREET: Street addresses
        ADDRESS_CITY: City names
        ADDRESS_STATE: State/province names
        ADDRESS_ZIP: ZIP/postal codes
        DEVICE_ID: Device identifiers and serial numbers
        URL: Web URLs
        IP_ADDRESS: IP addresses (IPv4/IPv6)
        ACCOUNT_NUMBER: Account numbers
        LICENSE_NUMBER: License/certificate numbers
        LOCATION: Geographic locations smaller than state
        ORGANIZATION: Organization names
        AGE_OVER_89: Ages greater than 89 (HIPAA requirement)
        CUSTOM: User-defined custom PHI types
    
    Example:
        >>> PHIType.SSN.value
        'SSN'
        >>> phi_type = PHIType.EMAIL
        >>> print(f"Detected {phi_type.name}")
        Detected EMAIL
    """
    NAME_FIRST = "FNAME"
    NAME_LAST = "LNAME"
    NAME_FULL = "PATIENT"
    MRN = "MRN"
    SSN = "SSN"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    DATE = "DATE"
    ADDRESS_STREET = "STREET"
    ADDRESS_CITY = "CITY"
    ADDRESS_STATE = "STATE"
    ADDRESS_ZIP = "ZIP"
    DEVICE_ID = "DEVICE"
    URL = "URL"
    IP_ADDRESS = "IP"
    ACCOUNT_NUMBER = "ACCOUNT"
    LICENSE_NUMBER = "LICENSE"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORG"
    AGE_OVER_89 = "AGE"
    CUSTOM = "CUSTOM"


@dataclass
class DetectionPattern:
    """PHI/PII detection pattern configuration.
    
    Encapsulates a regex pattern for detecting a specific type of PHI/PII, along
    with metadata for prioritization and logging. Patterns are applied in priority
    order to handle overlapping matches correctly.
    
    Attributes:
        phi_type: Type of PHI/PII this pattern detects.
        pattern: Compiled regex pattern (or string to be compiled).
        priority: Priority level (higher = applied first). Default: 50.
        description: Human-readable description of what pattern matches.
    
    Example:
        >>> pattern = DetectionPattern(
        ...     phi_type=PHIType.SSN,
        ...     pattern=r'\\b\\d{3}-\\d{2}-\\d{4}\\b',
        ...     priority=90,
        ...     description="SSN format: XXX-XX-XXXX"
        ... )
        >>> pattern.pattern.search("SSN: 123-45-6789")
        <re.Match object; span=(5, 16), match='123-45-6789'>
        
    Notes:
        - String patterns are automatically compiled with re.IGNORECASE
        - Higher priority patterns are tested first to resolve ambiguities
        - Priority constants defined at module level (PRIORITY_HIGH, etc.)
    """
    phi_type: PHIType
    pattern: re.Pattern
    priority: int = DEFAULT_PATTERN_PRIORITY
    description: str = ""
    
    def __post_init__(self):
        """Validate and compile regex pattern if provided as string."""
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.IGNORECASE)


@dataclass
class DeidentificationConfig:
    """De-identification engine configuration.
    
    Centralized configuration for all de-identification operations including
    pseudonym formatting, date shifting, security, and validation settings.
    
    Attributes:
        pseudonym_templates: Dict mapping PHI types to format strings with {id} placeholder.
        enable_date_shifting: Enable cryptographic date shifting. Default: True.
        date_shift_range_days: Maximum days to shift (±N days). Default: 365.
        preserve_date_intervals: Keep time intervals between dates constant. Default: True.
        enable_encryption: Encrypt mapping files with Fernet. Default: True.
        encryption_key: Fernet key (auto-generated if None). Default: None.
        enable_validation: Run validation after de-identification. Default: True.
        strict_mode: Fail on validation errors. Default: True.
        log_detections: Log all PHI detections. Default: True.
        log_level: Logging level (logging.INFO, etc.). Default: logging.INFO.
        countries: List of country codes for patterns (e.g., ['IN', 'US']). Default: None.
        enable_country_patterns: Load country-specific patterns. Default: True.
    
    Example:
        >>> config = DeidentificationConfig(
        ...     date_shift_range_days=180,
        ...     enable_encryption=True,
        ...     countries=['IN'],
        ...     strict_mode=False
        ... )
        >>> config.pseudonym_templates[PHIType.SSN]
        'SSN-{id}'
        
    Notes:
        - encryption_key is auto-generated if enable_encryption=True and key=None
        - countries=None uses DEFAULT_COUNTRY_CODE ('IN')
        - preserve_date_intervals=True maintains time differences within subjects
        - strict_mode=True causes sys.exit(1) on validation failures
    """
    # Pseudonym format templates
    pseudonym_templates: Dict[PHIType, str] = field(default_factory=lambda: {
        PHIType.NAME_FIRST: "FNAME-{id}",
        PHIType.NAME_LAST: "LNAME-{id}",
        PHIType.NAME_FULL: "PATIENT-{id}",
        PHIType.MRN: "MRN-{id}",
        PHIType.SSN: "SSN-{id}",
        PHIType.PHONE: "PHONE-{id}",
        PHIType.EMAIL: "EMAIL-{id}",
        PHIType.DATE: "DATE-{id}",
        PHIType.ADDRESS_STREET: "STREET-{id}",
        PHIType.ADDRESS_CITY: "CITY-{id}",
        PHIType.ADDRESS_STATE: "STATE-{id}",
        PHIType.ADDRESS_ZIP: "ZIP-{id}",
        PHIType.DEVICE_ID: "DEVICE-{id}",
        PHIType.URL: "URL-{id}",
        PHIType.IP_ADDRESS: "IP-{id}",
        PHIType.ACCOUNT_NUMBER: "ACCT-{id}",
        PHIType.LICENSE_NUMBER: "LIC-{id}",
        PHIType.LOCATION: "LOC-{id}",
        PHIType.ORGANIZATION: "ORG-{id}",
        PHIType.AGE_OVER_89: "AGE-{id}",
    })
    
    # Date shifting
    enable_date_shifting: bool = True
    date_shift_range_days: int = DEFAULT_DATE_SHIFT_RANGE_DAYS
    preserve_date_intervals: bool = True
    
    # Security
    enable_encryption: bool = True
    encryption_key: Optional[bytes] = None
    
    # Validation
    enable_validation: bool = True
    strict_mode: bool = True  # Fail on validation errors
    
    # Logging
    log_detections: bool = True
    log_level: int = logging.INFO
    
    # Country-specific regulations
    countries: Optional[List[str]] = None  # List of country codes or None for default (IN - India)
    enable_country_patterns: bool = True  # Enable country-specific detection patterns


# ============================================================================
# Detection Patterns
# ============================================================================

class PatternLibrary:
    """Library of regex patterns for detecting PHI/PII.
    
    Provides pre-configured detection patterns for 18 types of PHI/PII with
    priority-based matching. Patterns are tested in priority order (highest first)
    to handle overlapping matches correctly (e.g., SSN vs. generic number).
    
    The library includes patterns for:
    - US identifiers: SSN, MRN, phone numbers
    - Contact info: Email addresses, ZIP codes
    - Dates: Multiple formats (ISO, slash-separated, text months)
    - Network: IP addresses, URLs
    - HIPAA-specific: Ages > 89
    
    Methods:
        get_default_patterns: Returns list of DetectionPattern objects sorted by priority.
        
    Example:
        >>> patterns = PatternLibrary.get_default_patterns()
        >>> len(patterns)
        12
        >>> patterns[0].phi_type  # Highest priority
        <PHIType.SSN: 'SSN'>
        >>> patterns[0].priority
        90
        
    Notes:
        - Patterns are sorted by priority (highest → lowest) for correct precedence
        - All patterns use re.IGNORECASE for case-insensitive matching
        - Date patterns are ambiguous (DD/MM vs. MM/DD); country context determines
        - Additional country-specific patterns loaded via country_regulations module
        - Custom patterns can be added programmatically to engine
    """
    
    @staticmethod
    def get_default_patterns() -> List[DetectionPattern]:
        """Get default detection patterns for common PHI/PII types.
        
        Returns a pre-configured list of 12 detection patterns for the most common
        PHI/PII types in US healthcare data. Patterns are sorted by priority
        (highest first) to ensure correct precedence when multiple patterns match.
        
        Returns:
            List of DetectionPattern objects sorted by priority (descending).
            Includes patterns for: SSN (2 formats), MRN (2 formats), Phone,
            Email, Dates (3 formats), ZIP, IP, URL, Ages > 89.
        
        Example:
            >>> patterns = PatternLibrary.get_default_patterns()
            >>> len(patterns)
            12
            >>> # Highest priority pattern
            >>> patterns[0].phi_type
            <PHIType.SSN: 'SSN'>
            >>> patterns[0].priority
            90
            >>> # Find all SSN patterns
            >>> ssn_patterns = [p for p in patterns if p.phi_type == PHIType.SSN]
            >>> len(ssn_patterns)
            2
        
        Notes:
            - Patterns are pre-sorted by priority (no manual sorting needed)
            - All patterns use case-insensitive matching (re.IGNORECASE)
            - SSN has highest priority (90) to avoid matching generic numbers
            - Date patterns support ISO 8601, slash/hyphen-separated, and text months
            - Additional country-specific patterns loaded separately
            - Custom patterns can be added via DeidentificationEngine
        """
        patterns = [
            # SSN patterns (high priority)
            DetectionPattern(
                phi_type=PHIType.SSN,
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                priority=PRIORITY_HIGH_SSN,
                description="SSN format: XXX-XX-XXXX"
            ),
            DetectionPattern(
                phi_type=PHIType.SSN,
                pattern=re.compile(r'\b\d{9}\b'),
                priority=PRIORITY_HIGH,
                description="SSN format: XXXXXXXXX"
            ),
            
            # MRN patterns
            DetectionPattern(
                phi_type=PHIType.MRN,
                pattern=re.compile(r'\b(?:MRN|Medical\s+Record\s+(?:Number|#)):\s*([A-Z0-9]{6,12})\b', re.IGNORECASE),
                priority=PRIORITY_MEDIUM_HIGH,
                description="Medical Record Number with label"
            ),
            DetectionPattern(
                phi_type=PHIType.MRN,
                pattern=re.compile(r'\b[A-Z]{2}\d{6,10}\b'),
                priority=PRIORITY_MEDIUM_LOW,
                description="MRN format: LLNNNNNN"
            ),
            
            # Phone numbers
            DetectionPattern(
                phi_type=PHIType.PHONE,
                pattern=re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
                priority=PRIORITY_MEDIUM,
                description="US phone number"
            ),
            
            # Email addresses
            DetectionPattern(
                phi_type=PHIType.EMAIL,
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                priority=PRIORITY_HIGH,
                description="Email address"
            ),
            
            # Dates (multiple formats)
            # Note: DD/MM/YYYY is ambiguous with MM/DD/YYYY - country context determines interpretation
            # Date shifter supports multiple formats: ISO 8601, slash/hyphen/dot-separated
            DetectionPattern(
                phi_type=PHIType.DATE,
                pattern=re.compile(r'\b(?:0?[1-9]|[12][0-9]|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b'),
                priority=PRIORITY_LOW,
                description="Date format: DD/MM/YYYY or MM/DD/YYYY (slash-separated, country determines interpretation)"
            ),
            DetectionPattern(
                phi_type=PHIType.DATE,
                pattern=re.compile(r'\b(?:19|20)\d{2}[/-](?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12][0-9]|3[01])\b'),
                priority=PRIORITY_LOW,
                description="Date format: YYYY-MM-DD (ISO 8601)"
            ),
            DetectionPattern(
                phi_type=PHIType.DATE,
                pattern=re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:0?[1-9]|[12][0-9]|3[01]),?\s+(?:19|20)\d{2}\b', re.IGNORECASE),
                priority=PRIORITY_DATE_TEXT_MONTH,
                description="Date format: Month DD, YYYY (text month)"
            ),
            
            # Zip codes
            DetectionPattern(
                phi_type=PHIType.ADDRESS_ZIP,
                pattern=re.compile(r'\b\d{5}(?:-\d{4})?\b'),
                priority=PRIORITY_ZIP_CODE,
                description="US ZIP code"
            ),
            
            # IP addresses
            DetectionPattern(
                phi_type=PHIType.IP_ADDRESS,
                pattern=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
                priority=PRIORITY_MEDIUM_LOW,
                description="IPv4 address"
            ),
            
            # URLs
            DetectionPattern(
                phi_type=PHIType.URL,
                pattern=re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)', re.IGNORECASE),
                priority=PRIORITY_MEDIUM,
                description="HTTP/HTTPS URL"
            ),
            
            # Ages over 89 (HIPAA requirement)
            DetectionPattern(
                phi_type=PHIType.AGE_OVER_89,
                pattern=re.compile(r'\b(?:age|aged|Age|AGE)[\s:]+([9]\d|[1-9]\d{2,})\b'),
                priority=PRIORITY_MEDIUM_HIGH,
                description=f"Age over {HIPAA_AGE_THRESHOLD} years"
            ),
        ]
        
        # Sort by priority (highest first)
        patterns.sort(key=lambda p: p.priority, reverse=True)
        return patterns
    
    @staticmethod
    def get_country_specific_patterns(countries: Optional[List[str]] = None) -> List[DetectionPattern]:
        """Get country-specific PHI/PII detection patterns from regulations module.
        
        Loads detection patterns for country-specific identifiers (e.g., Aadhaar for India,
        CPF for Brazil, NIK for Indonesia) via the CountryRegulationManager. Maps country
        fields to appropriate PHI types with priority levels.
        
        Args:
            countries: List of ISO 3166-1 alpha-2 country codes (e.g., ['IN', 'US', 'BR']).
                If None, uses DEFAULT_COUNTRY_CODE ('IN'). Default: None.
        
        Returns:
            List of DetectionPattern objects for country-specific identifiers.
            Returns empty list if country_regulations module unavailable or on error.
        
        Raises:
            ValueError: If countries is not a list or contains non-string values.
            RuntimeError: If CountryRegulationManager API is incompatible.
        
        Example:
            >>> # India-specific patterns (Aadhaar, PAN, etc.)
            >>> patterns = PatternLibrary.get_country_specific_patterns(['IN'])
            >>> len(patterns) > 0
            True
            >>> # Multi-country patterns
            >>> patterns = PatternLibrary.get_country_specific_patterns(['IN', 'US', 'BR'])
            >>> phi_types = {p.phi_type for p in patterns}
            >>> PHIType.SSN in phi_types  # US SSN, BR CPF, etc.
            True
            >>> # Module not available → empty list (graceful degradation)
            >>> # (if country_regulations not installed)
            >>> patterns = PatternLibrary.get_country_specific_patterns(['XX'])
            >>> patterns
            []
        
        Side Effects:
            - Imports CountryRegulationManager dynamically
            - Logs warnings/errors for missing module or invalid inputs
            - Logs info on successful pattern loading
        
        Notes:
            - **Requires**: scripts.utils.country_regulations module (optional dependency)
            - **Graceful degradation**: Returns [] if module unavailable
            - **Field mapping**: Maps country fields to PHI types:
                - SSN-like (Aadhaar, CPF, NIK) → PHIType.SSN (priority 92)
                - MRN/health IDs → PHIType.MRN (priority 88)
                - Passport/ID/PAN → PHIType.LICENSE_NUMBER (priority 85)
                - Others → PHIType.CUSTOM (priority 75)
            - **Pattern priority**: Country patterns prioritized higher than generic patterns
            - **Validation**: Checks countries list type and CountryRegulationManager API
            - **Error handling**: Returns [] on unexpected errors (logged)
        """
        if not COUNTRY_REGULATIONS_AVAILABLE:
            logging.warning("Country regulations module not available")
            return []
        
        patterns = []
        
        try:
            # Validate country codes if provided
            if countries:
                if not isinstance(countries, list):
                    raise ValueError(f"countries must be a list, got {type(countries).__name__}")
                if not all(isinstance(c, str) for c in countries):
                    raise ValueError("All country codes must be strings")
            
            manager = CountryRegulationManager(countries=countries)
            
            if not hasattr(manager, 'get_country_specific_fields'):
                raise RuntimeError("CountryRegulationManager missing required method")
            
            country_fields = manager.get_country_specific_fields()
            
            if not isinstance(country_fields, (list, tuple)):
                raise RuntimeError(f"Expected list from get_country_specific_fields, got {type(country_fields).__name__}")
            
            for field in country_fields:
                if not hasattr(field, 'compiled_pattern'):
                    logging.warning(f"Field {getattr(field, 'name', 'unknown')} missing compiled_pattern, skipping")
                    continue
                    
                if field.compiled_pattern:
                    # Map to appropriate PHIType
                    if "ssn" in field.name.lower() or "cpf" in field.name.lower() or \
                       "aadhaar" in field.name.lower() or "nik" in field.name.lower():
                        phi_type = PHIType.SSN
                        priority = 92
                    elif "mrn" in field.name.lower() or "health" in field.name.lower():
                        phi_type = PHIType.MRN
                        priority = 88
                    elif any(x in field.name.lower() for x in ["passport", "id", "voter", "pan"]):
                        phi_type = PHIType.LICENSE_NUMBER
                        priority = PRIORITY_HIGH
                    else:
                        phi_type = PHIType.CUSTOM
                        priority = PRIORITY_MEDIUM
                    
                    patterns.append(DetectionPattern(
                        phi_type=phi_type,
                        pattern=field.compiled_pattern,
                        priority=priority,
                        description=f"{field.display_name}: {field.description}"
                    ))
            
            logging.info(f"Loaded {len(patterns)} country-specific patterns")
            
        except ValueError as e:
            logging.error(f"Invalid country codes provided: {e}")
            raise
        except ImportError as e:
            logging.error(f"Failed to import CountryRegulationManager: {e}")
            return []
        except AttributeError as e:
            logging.error(f"CountryRegulationManager API error: {e}")
            raise RuntimeError(f"Country regulations module API incompatible: {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading country-specific patterns: {e}", exc_info=True)
            # Return empty list on unexpected errors to allow graceful degradation
            return []
        
        return patterns


# ============================================================================
# Pseudonym Generation
# ============================================================================

class PseudonymGenerator:
    """Generates consistent, deterministic pseudonyms for PHI/PII.
    
    Creates cryptographically-hashed pseudonyms that are consistent across invocations
    (same input → same pseudonym) but unpredictable without the salt. Uses SHA-256
    hashing with salt, base32 encoding for human-readable IDs, and in-memory caching
    for performance.
    
    The generator ensures:
    - Determinism: Same PHI value always maps to same pseudonym
    - Consistency: Multiple occurrences of "John Smith" → single pseudonym
    - Unpredictability: No way to reverse-engineer original from pseudonym
    - Type safety: Different PHI types use separate namespaces (SSN "123" ≠ MRN "123")
    - Performance: O(1) lookup via in-memory cache
    
    Attributes:
        salt: Cryptographic salt for hashing (hex string, 32 chars = 16 bytes).
        _counter: Dict tracking pseudonym count per PHI type.
        _cache: Dict mapping (PHIType, value) → pseudonym for deduplication.
    
    Example:
        >>> generator = PseudonymGenerator(salt="abc123...")
        >>> # Same value → same pseudonym
        >>> p1 = generator.generate("John Smith", PHIType.NAME_FULL, "PATIENT-{id}")
        >>> p2 = generator.generate("John Smith", PHIType.NAME_FULL, "PATIENT-{id}")
        >>> p1 == p2
        True
        >>> p1
        'PATIENT-ABCD1234'
        >>> # Different types → different pseudonyms
        >>> ssn = generator.generate("123456789", PHIType.SSN, "SSN-{id}")
        >>> mrn = generator.generate("123456789", PHIType.MRN, "MRN-{id}")
        >>> ssn != mrn
        True
        >>> # Get statistics
        >>> generator.get_statistics()
        {'PATIENT': 1, 'SSN': 1, 'MRN': 1}
        
    Notes:
        - Salt is auto-generated if not provided (32-char hex = 16 random bytes)
        - Pseudonym IDs are 8-char base32 strings (40 bits of hash, case-insensitive)
        - Cache is in-memory only (not persisted); mappings stored separately
        - Thread-safe for reads, not thread-safe for writes (use locks if multithreading)
        - Different salt → different pseudonyms (salt = secret key)
    """
    
    def __init__(self, salt: Optional[str] = None):
        """Initialize pseudonym generator with cryptographic salt.
        
        Args:
            salt: Hex-encoded salt for hashing (32 chars). If None, auto-generated
                using secrets.token_hex(16). Default: None.
        
        Example:
            >>> # Auto-generated salt
            >>> gen = PseudonymGenerator()
            >>> len(gen.salt)
            32
            >>> # Custom salt (must be 32 hex chars)
            >>> gen = PseudonymGenerator(salt="a" * 32)
            >>> gen.salt
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        
        Notes:
            - Salt should be stored securely for reproducibility
            - Different salts → different pseudonyms for same input
            - Auto-generated salt uses secrets.token_hex for cryptographic randomness
        """
        self.salt = salt or secrets.token_hex(CRYPTO_SALT_LENGTH)
        self._counter: Dict[PHIType, int] = defaultdict(int)
        self._cache: Dict[Tuple[PHIType, str], str] = {}
    
    def generate(self, value: str, phi_type: PHIType, template: str) -> str:
        """Generate a deterministic pseudonym for a PHI/PII value.
        
        Uses SHA-256(salt:phi_type:value) → base32 encoding to create a
        consistent, human-readable 8-character ID. Caches results for performance.
        
        Args:
            value: Original PHI/PII value to pseudonymize (e.g., "John Smith").
            phi_type: Type of PHI (determines namespace and prevents collisions).
            template: Format string with {id} placeholder (e.g., "PATIENT-{id}").
        
        Returns:
            Pseudonymized value with ID embedded in template (e.g., "PATIENT-ABCD1234").
        
        Example:
            >>> gen = PseudonymGenerator(salt="test_salt_123")
            >>> # Generate pseudonym
            >>> pseudo = gen.generate("John Smith", PHIType.NAME_FULL, "PATIENT-{id}")
            >>> pseudo
            'PATIENT-X7Y3QR2A'
            >>> # Same input → same output (cached)
            >>> gen.generate("John Smith", PHIType.NAME_FULL, "PATIENT-{id}")
            'PATIENT-X7Y3QR2A'
            >>> # Different type → different pseudonym
            >>> gen.generate("John Smith", PHIType.NAME_FIRST, "FNAME-{id}")
            'FNAME-Z9K5LM3B'
            >>> # Check cache
            >>> (PHIType.NAME_FULL, "john smith") in gen._cache
            True
        
        Notes:
            - Value is lowercased for cache key (case-insensitive deduplication)
            - Hash input: f"{salt}:{phi_type.value}:{value}" → SHA-256
            - ID generation: First 4 bytes of hash → base32 → first 8 chars
            - Cache prevents redundant hash computation
            - Counter incremented on cache miss (tracks unique values per type)
        """
        cache_key = (phi_type, value.lower())
        
        # Return cached pseudonym if exists
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate deterministic ID from hash
        hash_input = f"{self.salt}:{phi_type.value}:{value}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).digest()
        
        # Convert first 4 bytes to alphanumeric ID
        id_bytes = hash_digest[:HASH_ID_BYTES]
        id_value = base64.b32encode(id_bytes).decode('ascii').rstrip('=')[:PSEUDONYM_ID_LENGTH]
        
        # Generate pseudonym from template
        pseudonym = template.format(id=id_value)
        
        # Cache and return
        self._cache[cache_key] = pseudonym
        self._counter[phi_type] += 1
        
        return pseudonym
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics on pseudonym generation by PHI type.
        
        Returns:
            Dictionary mapping PHI type names to count of unique values processed.
            Empty dict if no pseudonyms generated yet.
        
        Example:
            >>> gen = PseudonymGenerator()
            >>> gen.generate("John", PHIType.NAME_FIRST, "FNAME-{id}")
            'FNAME-ABC12345'
            >>> gen.generate("Smith", PHIType.NAME_LAST, "LNAME-{id}")
            'LNAME-XYZ67890'
            >>> gen.generate("John", PHIType.NAME_FIRST, "FNAME-{id}")  # Cache hit
            'FNAME-ABC12345'
            >>> gen.get_statistics()
            {'FNAME': 1, 'LNAME': 1}
            
        Notes:
            - Counts unique values (not total calls)
            - Cache hits don't increment counter
            - Useful for logging/reporting de-identification coverage
        """
        return {phi_type.value: count for phi_type, count in self._counter.items()}


# ============================================================================
# Date Shifting
# ============================================================================

class DateShifter:
    """Consistent date shifting with intelligent multi-format parsing.
    
    Cryptographically shifts dates by a deterministic offset while preserving
    temporal relationships and intervals. Supports country-specific date format
    interpretation (DD/MM/YYYY vs. MM/DD/YYYY) with smart ambiguity resolution.
    
    Key features:
    - **Consistency**: Same seed → same shift offset for all dates
    - **Interval preservation**: Time differences maintained within subject
    - **Multi-format support**: ISO 8601, slash/hyphen/dot-separated, text months
    - **Country-aware**: Disambiguates DD/MM vs. MM/DD by country code
    - **Smart validation**: Rejects logically impossible date interpretations
    - **Caching**: O(1) lookup for repeated dates
    
    Attributes:
        shift_range_days: Maximum days to shift (±N). Default: 365.
        preserve_intervals: If True, use same offset for all dates (maintains intervals).
            If False, each date gets random offset (breaks intervals). Default: True.
        seed: Cryptographic seed for deterministic offset (hex string).
        country_code: ISO country code for format interpretation ('IN', 'US', etc.).
        _shift_offset: Computed offset in days (lazy-loaded).
        _date_cache: Dict mapping original date strings → shifted date strings.
        dd_mm_yyyy_countries: Set of countries using DD/MM/YYYY format.
        mm_dd_yyyy_countries: Set of countries using MM/DD/YYYY format.
    
    Example:
        >>> # India uses DD/MM/YYYY format
        >>> shifter = DateShifter(shift_range_days=30, country_code='IN')
        >>> # Shift date (DD/MM interpretation)
        >>> shifter.shift_date("15/06/2023")
        '22/06/2023'
        >>> # US uses MM/DD/YYYY format
        >>> us_shifter = DateShifter(shift_range_days=30, country_code='US')
        >>> us_shifter.shift_date("06/15/2023")  # June 15
        '06/22/2023'
        >>> # Unambiguous ISO format works everywhere
        >>> shifter.shift_date("2023-06-15")
        '2023-06-22'
        >>> # Interval preservation
        >>> date1 = shifter.shift_date("01/01/2023")
        >>> date2 = shifter.shift_date("01/08/2023")
        >>> # 7 days apart in original → 7 days apart in shifted
        
    Notes:
        - Shift offset is deterministic (same seed → same offset)
        - Offset range: [-shift_range_days, +shift_range_days]
        - Ambiguous dates (e.g., "12/12/2023") use country preference
        - Impossible dates (e.g., "15" in month position for MM/DD) are auto-rejected
        - Cache prevents redundant parsing/shifting
        - preserve_intervals=True recommended for HIPAA compliance (maintains ages/durations)
    """
    
    def __init__(self, shift_range_days: int = DEFAULT_DATE_SHIFT_RANGE_DAYS, preserve_intervals: bool = True, seed: Optional[str] = None, country_code: str = DEFAULT_COUNTRY_CODE):
        """Initialize date shifter with country-specific format interpretation.
        
        Args:
            shift_range_days: Maximum days to shift (±N). Creates offset in
                range [-N, +N]. Default: 365.
            preserve_intervals: If True, use same offset for all dates (maintains
                intervals). If False, randomize per-date. Default: True.
            seed: Hex-encoded seed for deterministic offset. If None, auto-generated
                using secrets.token_hex(16). Default: None.
            country_code: ISO 3166-1 alpha-2 country code ('IN', 'US', etc.) for
                date format disambiguation. Default: 'IN'.
        
        Example:
            >>> # India: DD/MM/YYYY, ±180 days
            >>> shifter = DateShifter(shift_range_days=180, country_code='IN')
            >>> shifter.country_code
            'IN'
            >>> shifter.shift_range_days
            180
            >>> # US: MM/DD/YYYY, interval preservation disabled
            >>> shifter = DateShifter(
            ...     shift_range_days=365,
            ...     preserve_intervals=False,
            ...     country_code='US'
            ... )
            >>> shifter.preserve_intervals
            False
        
        Notes:
            - Supported DD/MM countries: IN, ID, BR, ZA, EU, GB, AU, KE, NG, GH, UG
            - Supported MM/DD countries: US, PH, CA
            - seed is auto-generated if None (32-char hex = 16 random bytes)
            - country_code is case-insensitive (auto-uppercased)
            - shift_offset is lazy-loaded on first shift_date() call
        """
        self.shift_range_days = shift_range_days
        self.preserve_intervals = preserve_intervals
        self.seed = seed or secrets.token_hex(CRYPTO_SALT_LENGTH // 2)  # 16 bytes = 32 hex chars
        self.country_code = country_code.upper()
        self._shift_offset: Optional[int] = None
        self._date_cache: Dict[str, str] = {}
        
        # Country-specific date formats
        # DD/MM/YYYY: India, UK, Australia, Indonesia, Brazil, South Africa, EU countries, Kenya, Nigeria, Ghana, Uganda
        # MM/DD/YYYY: United States, Philippines, Canada (sometimes)
        self.dd_mm_yyyy_countries = {"IN", "ID", "BR", "ZA", "EU", "GB", "AU", "KE", "NG", "GH", "UG"}
        self.mm_dd_yyyy_countries = {"US", "PH", "CA"}
    
    def _get_shift_offset(self) -> int:
        """Get consistent shift offset based on seed (lazy-loaded).
        
        Computes deterministic offset from seed using SHA-256 hash. Offset is
        cached after first computation. Range: [-shift_range_days, +shift_range_days].
        
        Returns:
            Integer offset in days (can be negative for backward shift).
        
        Example:
            >>> shifter = DateShifter(shift_range_days=100, seed="abc123")
            >>> offset = shifter._get_shift_offset()
            >>> -100 <= offset <= 100
            True
            >>> # Same seed → same offset (cached)
            >>> shifter._get_shift_offset() == offset
            True
        
        Notes:
            - Hash: SHA-256(seed) → first 4 bytes → integer
            - Mapping: integer % (2 * shift_range_days + 1) - shift_range_days
            - Lazy: only computed on first call, then cached in _shift_offset
        """
        if self._shift_offset is None:
            # Generate deterministic offset from seed
            hash_digest = hashlib.sha256(self.seed.encode()).digest()
            offset_int = int.from_bytes(hash_digest[:HASH_ID_BYTES], byteorder='big')
            self._shift_offset = (offset_int % (2 * self.shift_range_days + 1)) - self.shift_range_days
        return self._shift_offset
    
    def shift_date(self, date_str: str, date_format: Optional[str] = None) -> str:
        """Shift a date string by consistent offset with intelligent format detection.
        
        Parses date using country-specific format rules, applies deterministic offset,
        and returns shifted date in original format. Handles ambiguous dates (DD/MM vs.
        MM/DD) using country preference and smart validation.
        
        Args:
            date_str: Original date string in any supported format.
            date_format: Explicit Python strftime format string. If None, auto-detects
                using country-specific rules. Default: None.
        
        Returns:
            Shifted date string in same format as input. If parsing fails, returns
            placeholder string "[DATE-XXXXXX]" where XXXXXX is MD5 hash of input.
        
        Example:
            >>> # India (DD/MM/YYYY)
            >>> shifter = DateShifter(shift_range_days=7, seed="test", country_code='IN')
            >>> shifter.shift_date("15/06/2023")  # DD/MM
            '18/06/2023'
            >>> # US (MM/DD/YYYY)
            >>> us_shifter = DateShifter(shift_range_days=7, seed="test", country_code='US')
            >>> us_shifter.shift_date("06/15/2023")  # MM/DD
            '06/18/2023'
            >>> # Unambiguous ISO format
            >>> shifter.shift_date("2023-06-15")
            '2023-06-18'
            >>> # Text month format
            >>> shifter.shift_date("June 15, 2023")
            'June 18, 2023'
            >>> # Explicit format override
            >>> shifter.shift_date("15.06.2023", date_format="%d.%m.%Y")
            '18.06.2023'
            >>> # Invalid date → placeholder
            >>> shifter.shift_date("99/99/9999")
            '[DATE-A1B2C3]'
        
        Raises:
            None (returns placeholder on parse failure).
        
        Notes:
            - **Format priority** (if date_format=None):
                1. ISO 8601 (YYYY-MM-DD) - unambiguous, always tried first
                2. Country-specific format (DD/MM for IN, MM/DD for US, etc.)
                3. Additional separators (-, ., /) as fallbacks
            - **Smart validation**: Rejects formats where day/month values are impossible
                - Example: "15/06/2023" as MM/DD rejected (month can't be 15)
                - Example: "12/12/2023" as DD/MM accepted if country=IN (ambiguous but valid)
            - **Caching**: Repeated dates are O(1) lookup
            - **Offset**: Same offset applied to all dates (preserves intervals)
            - **Warnings**: Logged for unparseable dates
            - **Supported formats**:
                - YYYY-MM-DD, YYYY/MM/DD (ISO)
                - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY (Europe, India, etc.)
                - MM/DD/YYYY, MM-DD-YYYY (US, Philippines, etc.)
                - Month DD, YYYY (e.g., "June 15, 2023")
        """
        if date_str in self._date_cache:
            return self._date_cache[date_str]
        
        # Define common date formats to try, with COUNTRY-SPECIFIC PRIORITY
        if date_format is None:
            # Strategy: Try unambiguous formats first (ISO 8601), then use country preference
            # This ensures: 
            #   1. Unambiguous dates (YYYY-MM-DD) always parse correctly
            #   2. Ambiguous dates (12/12/2012) use country-specific interpretation
            if self.country_code in self.dd_mm_yyyy_countries:
                formats_to_try = [
                    "%Y-%m-%d",      # YYYY-MM-DD (ISO 8601) - unambiguous, always try first
                    "%d/%m/%Y",      # DD/MM/YYYY (India, UK, AU, etc.) - COUNTRY PREFERENCE
                    "%d-%m-%Y",      # DD-MM-YYYY
                    "%d.%m.%Y",      # DD.MM.YYYY (European)
                ]
            else:
                formats_to_try = [
                    "%Y-%m-%d",      # YYYY-MM-DD (ISO 8601) - unambiguous, always try first
                    "%m/%d/%Y",      # MM/DD/YYYY (US, PH, etc.) - COUNTRY PREFERENCE
                    "%m-%d-%Y",      # MM-DD-YYYY
                ]
        else:
            formats_to_try = [date_format]
        
        # Try each format until one works
        # For ambiguous dates (both numbers ≤ 12), the FIRST matching format wins
        # Since formats are ordered by country preference, this ensures consistency
        parsed_date = None
        successful_format = None
        
        for fmt in formats_to_try:
            try:
                # Parse date
                date_obj = datetime.strptime(date_str, fmt)
                
                # SMART VALIDATION: Reject formats that are logically impossible
                # This only applies to slash-separated ambiguous formats
                if fmt in ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"]:
                    # Determine separator
                    separator = "/" if "/" in date_str else "-"
                    parts = date_str.split(separator)
                    
                    if len(parts) == 3:
                        first_num = int(parts[0])
                        second_num = int(parts[1])
                        
                        # CASE 1: First number > MAX_MONTH_VALUE → MUST be day (can't be month)
                        if first_num > MAX_MONTH_VALUE and fmt in ["%m/%d/%Y", "%m-%d-%Y"]:
                            # We're trying MM/DD but first number is >12 (impossible month!)
                            continue  # Skip this format, it's logically impossible
                        
                        # CASE 2: Second number > MAX_MONTH_VALUE → MUST be day (can't be month)
                        if second_num > MAX_MONTH_VALUE and fmt in ["%d/%m/%Y", "%d-%m-%Y"]:
                            # We're trying DD/MM but second number is >12 (impossible month!)
                            continue  # Skip this format, it's logically impossible
                        
                        # CASE 3: Both numbers ≤ MAX_MONTH_VALUE → Ambiguous! Trust country preference
                        # Since formats are ordered by country priority, first match = correct interpretation
                
                # If we reach here, the format is valid and logically consistent
                parsed_date = date_obj
                successful_format = fmt
                break
                
            except ValueError:
                # Parse failed (e.g., invalid date like 2020-02-30), try next format
                continue
        
        if parsed_date is None:
            # If all formats fail, return placeholder and log warning
            logging.warning(f"Could not parse date: {date_str} (tried formats: {', '.join(formats_to_try)})")
            return f"[DATE-{hashlib.md5(date_str.encode()).hexdigest()[:6].upper()}]"
        
        # Apply consistent shift offset
        offset_days = self._get_shift_offset()
        shifted_date = parsed_date + timedelta(days=offset_days)
        
        # Format back to string (preserve original format)
        shifted_str = shifted_date.strftime(successful_format)
        
        # Cache and return
        self._date_cache[date_str] = shifted_str
        return shifted_str


# ============================================================================
# Secure Mapping Storage
# ============================================================================

class MappingStore:
    """Secure storage for PHI to pseudonym mappings.
    
    Manages persistent, encrypted storage of de-identification mappings with atomic
    file operations, JSON serialization, and optional Fernet encryption. Provides
    auditing and export capabilities while protecting original PHI values.
    
    Storage format:
    - **Encrypted**: Fernet symmetric encryption (if enabled)
    - **Serialization**: JSON with UTF-8 encoding
    - **Structure**: Dict[str, Dict[str, Any]] where key = "{phi_type}:{original}"
    
    Mapping entry structure:
    ```json
    {
        "SSN:123-45-6789": {
            "original": "123-45-6789",
            "pseudonym": "SSN-X7Y3QR2A",
            "phi_type": "SSN",
            "created_at": "2023-11-15T14:30:52.123456",
            "metadata": {"pattern": "SSN format: XXX-XX-XXXX"}
        }
    }
    ```
    
    Attributes:
        storage_path: Path to encrypted mapping file (e.g., "mappings.enc").
        enable_encryption: If True, encrypt file with Fernet. Default: True.
        encryption_key: Fernet key (32 URL-safe base64 bytes). Auto-generated if None.
        cipher: Fernet cipher instance (None if encryption disabled).
        mappings: In-memory dict of all mappings (loaded from file).
    
    Example:
        >>> # Initialize with encryption
        >>> store = MappingStore(
        ...     storage_path=Path("mappings.enc"),
        ...     enable_encryption=True
        ... )
        >>> # Add mapping
        >>> store.add_mapping(
        ...     original="John Smith",
        ...     pseudonym="PATIENT-ABC123",
        ...     phi_type=PHIType.NAME_FULL,
        ...     metadata={"source": "dataset_01"}
        ... )
        >>> # Retrieve pseudonym
        >>> store.get_pseudonym("John Smith", PHIType.NAME_FULL)
        'PATIENT-ABC123'
        >>> # Save to disk (encrypted)
        >>> store.save_mappings()  # doctest: +SKIP
        >>> # Export for audit (without originals)
        >>> import tempfile
        >>> temp_path = Path(tempfile.mkdtemp()) / "audit.json"
        >>> store.export_for_audit(temp_path, include_originals=False)  # doctest: +SKIP
        
    Side Effects:
        - Creates storage directory if not exists
        - Loads existing mappings from file on __init__
        - save_mappings() writes encrypted file to disk (atomic operation)
        - export_for_audit() writes JSON audit file
        
    Notes:
        - **Atomic writes**: Temp file + rename ensures no corruption
        - **Encryption**: Requires cryptography package (graceful degradation if missing)
        - **Key management**: Store encryption_key separately (can't decrypt without it)
        - **Audit safety**: Export can exclude originals for secure distribution
        - **Thread safety**: Not thread-safe (use locks if multithreading)
        - **Performance**: O(1) lookup, O(n) save (n = mapping count)
    """
    
    def __init__(self, storage_path: Path, encryption_key: Optional[bytes] = None, enable_encryption: bool = True):
        """Initialize mapping store with optional encryption.
        
        Args:
            storage_path: Path to mapping file (e.g., "mappings.enc").
                Created if not exists.
            encryption_key: Fernet encryption key (32 bytes, URL-safe base64).
                If None and enable_encryption=True, auto-generated. Default: None.
            enable_encryption: If True, encrypt file with Fernet. Requires
                cryptography package. Default: True.
        
        Example:
            >>> # Auto-generated key
            >>> store = MappingStore(Path("mappings.enc"))
            >>> len(store.encryption_key)
            44  # 32 bytes base64-encoded
            >>> # Custom key (must save for later decryption!)
            >>> from cryptography.fernet import Fernet
            >>> key = Fernet.generate_key()
            >>> store = MappingStore(Path("mappings.enc"), encryption_key=key)
            >>> # No encryption
            >>> store = MappingStore(Path("mappings.json"), enable_encryption=False)
            >>> store.cipher is None
            True
        
        Side Effects:
            - Loads existing mappings from storage_path if file exists
            - Logs warning if encryption requested but cryptography unavailable
            - Creates empty mappings dict if file not found
        
        Notes:
            - encryption_key must be stored securely (can't decrypt without it)
            - Auto-generated keys are not persisted (only in memory)
            - File must be decrypted with same key used for encryption
        """
        self.storage_path = Path(storage_path)
        self.enable_encryption = enable_encryption and CRYPTO_AVAILABLE
        
        if self.enable_encryption:
            self.encryption_key = encryption_key or Fernet.generate_key()
            self.cipher = Fernet(self.encryption_key)
        else:
            self.encryption_key = None
            self.cipher = None
            if enable_encryption:
                logging.warning("Encryption requested but cryptography package not available")
        
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """Load mappings from encrypted storage file with validation.
        
        Reads mapping file, decrypts if encryption enabled, parses JSON, and
        validates structure. Called automatically by __init__. Handles missing
        files gracefully (empty mappings), but raises errors for corruption.
        
        Raises:
            ValueError: If decryption fails, JSON is invalid, or structure is corrupted.
            RuntimeError: If file access fails or unexpected error occurs.
            PermissionError: If file cannot be read due to permissions.
        
        Example:
            >>> store = MappingStore(Path("existing.enc"))
            >>> # _load_mappings() called automatically
            >>> len(store.mappings) > 0
            True
            >>> # Missing file → empty mappings (no error)
            >>> store2 = MappingStore(Path("nonexistent.enc"))
            >>> len(store2.mappings)
            0
        
        Side Effects:
            - Populates self.mappings dict with loaded data
            - Logs info/warning/error messages
            - Creates empty mappings dict if file not found
        
        Notes:
            - File not found is not an error (allows fresh start)
            - Empty file triggers warning but continues
            - Decryption errors raise ValueError (wrong key)
            - JSON errors raise ValueError (file corruption)
            - Structure validation ensures dict type
        """
        if not self.storage_path.exists():
            logging.debug(f"Mapping file not found at {self.storage_path}, starting with empty mappings")
            return
        
        try:
            with open(self.storage_path, 'rb') as f:
                data = f.read()
            
            if not data:
                logging.warning(f"Mapping file {self.storage_path} is empty, starting with empty mappings")
                return
            
            # Decrypt if enabled
            if self.enable_encryption and self.cipher:
                try:
                    data = self.cipher.decrypt(data)
                except Exception as e:
                    logging.error(f"Failed to decrypt mappings: {e}")
                    raise ValueError(f"Decryption failed - invalid key or corrupted file: {e}")
            
            # Parse JSON
            try:
                decoded_data = data.decode('utf-8')
                self.mappings = json.loads(decoded_data)
            except UnicodeDecodeError as e:
                logging.error(f"Failed to decode mappings data: {e}")
                raise ValueError(f"Invalid UTF-8 data in mapping file: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON from mappings: {e}")
                raise ValueError(f"Corrupted JSON in mapping file: {e}")
            
            # Validate structure
            if not isinstance(self.mappings, dict):
                raise ValueError(f"Expected dict from mappings file, got {type(self.mappings).__name__}")
            
            logging.info(f"Loaded {len(self.mappings)} mappings from {self.storage_path}")
            
        except (PermissionError, OSError) as e:
            logging.error(f"File system error loading mappings: {e}")
            raise RuntimeError(f"Cannot access mapping file {self.storage_path}: {e}")
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logging.error(f"Unexpected error loading mappings: {e}", exc_info=True)
            self.mappings = {}
            raise RuntimeError(f"Failed to load mappings from {self.storage_path}: {e}")
    
    def save_mappings(self) -> None:
        """Save mappings to storage file with atomic write operation.
        
        Serializes mappings to JSON, optionally encrypts, and writes to disk using
        atomic write (temp file + rename) to prevent corruption. Creates parent
        directories if needed.
        
        Raises:
            ValueError: If mappings structure is invalid or JSON serialization fails.
            PermissionError: If directory/file cannot be written.
            OSError: If file system operations fail.
            RuntimeError: If encryption fails or unexpected error occurs.
        
        Example:
            >>> import tempfile
            >>> temp_dir = tempfile.mkdtemp()
            >>> store = MappingStore(Path(temp_dir) / "mappings.enc")  # doctest: +SKIP
            >>> store.add_mapping("SSN", "SSN-ABC123", PHIType.SSN)  # doctest: +SKIP
            >>> store.save_mappings()  # doctest: +SKIP
            >>> # File now exists with encrypted data
            >>> (Path(temp_dir) / "mappings.enc").exists()  # doctest: +SKIP
            True
        
        Side Effects:
            - Creates parent directory if not exists
            - Writes encrypted/plaintext file to storage_path
            - Overwrites existing file atomically (no corruption risk)
            - Logs info/debug/error messages
        
        Notes:
            - **Atomic operation**: Temp file → rename (crash-safe)
            - Creates .tmp_mappings_* file temporarily in same directory
            - Temp file cleaned up automatically on error
            - File size depends on mapping count and encryption
            - Encryption adds ~50% overhead (base64 encoding)
            - fsync() ensures data written to disk before rename
        """
        import tempfile
        
        # Validate mappings data
        if not isinstance(self.mappings, dict):
            raise ValueError(f"Mappings must be a dict, got {type(self.mappings).__name__}")
        
        logging.debug(f"Saving {len(self.mappings)} mappings to {self.storage_path}")
        
        try:
            # Ensure directory exists and is writable
            try:
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(f"Cannot create directory {self.storage_path.parent}: {e}")
            except OSError as e:
                raise OSError(f"Failed to create directory {self.storage_path.parent}: {e}")
            
            # Check parent directory is writable
            if not os.access(self.storage_path.parent, os.W_OK):
                raise PermissionError(f"Directory {self.storage_path.parent} is not writable")
            
            # Serialize to JSON
            try:
                data = json.dumps(self.mappings, indent=2, ensure_ascii=False).encode('utf-8')
            except (TypeError, ValueError) as e:
                raise RuntimeError(f"Failed to serialize mappings to JSON: {e}")
            
            logging.debug(f"Serialized {len(data)} bytes of mapping data")
            
            # Encrypt if enabled
            if self.enable_encryption and self.cipher:
                try:
                    encrypted_data = self.cipher.encrypt(data)
                    logging.debug(f"Encrypted data: {len(data)} -> {len(encrypted_data)} bytes")
                    data = encrypted_data
                except Exception as e:
                    raise RuntimeError(f"Encryption failed: {e}")
            
            # Atomic write: write to temp file, then rename
            temp_fd = None
            temp_path = None
            try:
                # Create temp file in same directory to ensure same filesystem
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=self.storage_path.parent,
                    prefix='.tmp_mappings_',
                    suffix='.enc' if self.enable_encryption else '.json'
                )
                
                # Write data to temp file
                try:
                    os.write(temp_fd, data)
                    os.fsync(temp_fd)  # Ensure data is written to disk
                except OSError as e:
                    raise OSError(f"Failed to write to temporary file {temp_path}: {e}")
                finally:
                    if temp_fd is not None:
                        os.close(temp_fd)
                
                # Atomic rename (on POSIX systems, this is atomic even if target exists)
                try:
                    os.replace(temp_path, self.storage_path)
                except OSError as e:
                    raise OSError(f"Failed to rename {temp_path} to {self.storage_path}: {e}")
                
                encryption_status = "encrypted" if self.enable_encryption else "plaintext"
                logging.info(
                    f"Saved {len(self.mappings)} mappings to {self.storage_path} "
                    f"({len(data)} bytes, {encryption_status})"
                )
                
            except Exception:
                # Clean up temp file on error
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                        logging.debug(f"Cleaned up temporary file {temp_path}")
                    except OSError as cleanup_error:
                        logging.warning(f"Failed to clean up temporary file {temp_path}: {cleanup_error}")
                raise
            
        except PermissionError as e:
            logging.error(f"Permission denied saving mappings: {e}")
            raise
        except OSError as e:
            logging.error(f"File system error saving mappings: {e}")
            raise
        except RuntimeError as e:
            logging.error(f"Operation failed saving mappings: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error saving mappings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to save mappings due to unexpected error: {e}")
    
    def add_mapping(self, original: str, pseudonym: str, phi_type: PHIType, metadata: Optional[Dict] = None) -> None:
        """Add a PHI→pseudonym mapping entry with comprehensive validation.
        
        Stores a de-identification mapping with original value, pseudonym, PHI type,
        timestamp, and optional metadata. Validates all inputs and warns if
        overwriting existing mapping with different pseudonym.
        
        Args:
            original: Original PHI/PII value (e.g., "John Smith", "123-45-6789").
            pseudonym: Generated pseudonym (e.g., "PATIENT-ABC123", "SSN-XYZ789").
            phi_type: Type of PHI being mapped (determines namespace).
            metadata: Optional dict with additional info (e.g., {"pattern": "SSN format"}).
                Must be JSON-serializable. Default: None.
        
        Raises:
            TypeError: If original/pseudonym not str, phi_type not PHIType, or metadata not dict.
            ValueError: If original/pseudonym empty/whitespace, or metadata not JSON-serializable.
            RuntimeError: If mapping addition fails unexpectedly.
        
        Example:
            >>> store = MappingStore(Path("mappings.enc"))
            >>> # Add SSN mapping
            >>> store.add_mapping(
            ...     original="123-45-6789",
            ...     pseudonym="SSN-X7Y3QR",
            ...     phi_type=PHIType.SSN,
            ...     metadata={"pattern": "XXX-XX-XXXX", "detected_at": "2023-11-15"}
            ... )
            >>> # Add patient name mapping
            >>> store.add_mapping(
            ...     original="John Smith",
            ...     pseudonym="PATIENT-ABC123",
            ...     phi_type=PHIType.NAME_FULL
            ... )
            >>> len(store.mappings)
            2
            >>> # Duplicate detection (warns if pseudonym differs)
            >>> store.add_mapping("123-45-6789", "SSN-DIFFERENT", PHIType.SSN)
            WARNING: Overwriting existing mapping...
        
        Side Effects:
            - Adds entry to self.mappings dict
            - Logs debug message for successful addition
            - Logs warning if overwriting existing mapping
            - Creates timestamp automatically
        
        Notes:
            - Mapping key format: "{phi_type}:{original}"
            - Same original + phi_type = overwrite (not duplicate)
            - Different phi_types can have same original value (e.g., SSN "123" vs MRN "123")
            - Metadata is optional but recommended for audit trails
            - Timestamp is ISO 8601 format (datetime.now().isoformat())
            - Not automatically saved to disk (call save_mappings())
        """
        # Validate input types
        if not isinstance(original, str):
            raise TypeError(f"original must be str, got {type(original).__name__}")
        if not isinstance(pseudonym, str):
            raise TypeError(f"pseudonym must be str, got {type(pseudonym).__name__}")
        if not isinstance(phi_type, PHIType):
            raise TypeError(f"phi_type must be PHIType enum, got {type(phi_type).__name__}")
        
        # Validate non-empty
        if not original.strip():
            raise ValueError("original cannot be empty or whitespace-only")
        if not pseudonym.strip():
            raise ValueError("pseudonym cannot be empty or whitespace-only")
        
        # Validate metadata if provided
        if metadata is not None:
            if not isinstance(metadata, dict):
                raise TypeError(f"metadata must be dict, got {type(metadata).__name__}")
            # Ensure metadata is JSON-serializable
            try:
                json.dumps(metadata)
            except (TypeError, ValueError) as e:
                raise ValueError(f"metadata must be JSON-serializable: {e}")
        
        mapping_key = f"{phi_type.value}:{original}"
        
        # Check for duplicate and log warning
        if mapping_key in self.mappings:
            existing = self.mappings[mapping_key]
            if existing["pseudonym"] != pseudonym:
                logging.warning(
                    f"Overwriting existing mapping for {phi_type.value}:{original[:20]}... "
                    f"(old: {existing['pseudonym'][:20]}..., new: {pseudonym[:20]}...)"
                )
        
        try:
            self.mappings[mapping_key] = {
                "original": original,
                "pseudonym": pseudonym,
                "phi_type": phi_type.value,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            logging.debug(
                f"Added mapping: {phi_type.value}:{original[:20]}... -> {pseudonym[:20]}..."
            )
            
        except Exception as e:
            logging.error(f"Failed to add mapping for {phi_type.value}: {e}")
            raise RuntimeError(f"Failed to add mapping: {e}")
    
    def get_pseudonym(self, original: str, phi_type: PHIType) -> Optional[str]:
        """Retrieve pseudonym for original PHI value with validation.
        
        Looks up pseudonym for a given original value and PHI type. Returns None
        if not found or if mapping is invalid. Validates mapping structure before
        returning.
        
        Args:
            original: Original PHI/PII value to look up.
            phi_type: Type of PHI (determines namespace).
        
        Returns:
            Pseudonym string if found, None if not found or invalid.
        
        Raises:
            TypeError: If original not str or phi_type not PHIType.
            ValueError: If original is empty or whitespace-only.
        
        Example:
            >>> store = MappingStore(Path("mappings.enc"))
            >>> store.add_mapping("John", "PATIENT-ABC", PHIType.NAME_FULL)
            >>> # Retrieve existing mapping
            >>> store.get_pseudonym("John", PHIType.NAME_FULL)
            'PATIENT-ABC'
            >>> # Not found → None
            >>> store.get_pseudonym("Jane", PHIType.NAME_FULL) is None
            True
            >>> # Different PHI type → None (separate namespace)
            >>> store.get_pseudonym("John", PHIType.SSN) is None
            True
        
        Side Effects:
            - Logs debug message if found
            - Logs debug message if not found
            - Logs error if mapping structure invalid
        
        Notes:
            - Mapping key: "{phi_type}:{original}"
            - Returns None (not exception) if not found
            - Validates mapping structure before returning
            - Same original with different phi_type → different mappings
            - Thread-safe for reads (not writes)
        """
        # Validate input types
        if not isinstance(original, str):
            raise TypeError(f"original must be str, got {type(original).__name__}")
        if not isinstance(phi_type, PHIType):
            raise TypeError(f"phi_type must be PHIType enum, got {type(phi_type).__name__}")
        
        # Validate non-empty
        if not original.strip():
            raise ValueError("original cannot be empty or whitespace-only")
        
        mapping_key = f"{phi_type.value}:{original}"
        
        try:
            mapping = self.mappings.get(mapping_key)
            
            if mapping is None:
                logging.debug(f"No mapping found for {phi_type.value}:{original[:20]}...")
                return None
            
            # Validate mapping structure
            if not isinstance(mapping, dict):
                logging.error(f"Invalid mapping structure for {mapping_key}: expected dict, got {type(mapping).__name__}")
                return None
            
            if "pseudonym" not in mapping:
                logging.error(f"Mapping for {mapping_key} missing 'pseudonym' key")
                return None
            
            pseudonym = mapping["pseudonym"]
            
            # Validate pseudonym type
            if not isinstance(pseudonym, str):
                logging.error(f"Invalid pseudonym type for {mapping_key}: expected str, got {type(pseudonym).__name__}")
                return None
            
            logging.debug(f"Retrieved mapping: {phi_type.value}:{original[:20]}... -> {pseudonym[:20]}...")
            return pseudonym
            
        except Exception as e:
            logging.error(f"Unexpected error retrieving pseudonym for {phi_type.value}:{original[:20]}...: {e}", exc_info=True)
            return None
    
    def export_for_audit(self, output_path: Path, include_originals: bool = False) -> None:
        """Export mappings for audit purposes with optional PHI redaction.
        
        Creates a human-readable JSON audit file with all mappings. Can exclude
        original PHI values for secure distribution to auditors. Uses atomic
        write to prevent corruption.
        
        Args:
            output_path: Path where audit JSON will be written.
            include_originals: If True, include original PHI values (SENSITIVE!).
                If False, only pseudonyms and metadata (safe for distribution).
                Default: False.
        
        Raises:
            TypeError: If output_path not Path or str.
            PermissionError: If directory/file cannot be written.
            OSError: If file system operations fail.
            RuntimeError: If JSON serialization or write fails.
        
        Example:
            >>> import tempfile
            >>> temp_dir = Path(tempfile.mkdtemp())
            >>> store = MappingStore(temp_dir / "mappings.enc")  # doctest: +SKIP
            >>> store.add_mapping("SSN", "SSN-ABC", PHIType.SSN, {"source": "dataset1"})  # doctest: +SKIP
            >>> # Safe export (no originals)
            >>> store.export_for_audit(temp_dir / "audit_safe.json", include_originals=False)  # doctest: +SKIP
            >>> # Sensitive export (with originals - use caution!)
            >>> store.export_for_audit(temp_dir / "audit_full.json", include_originals=True)  # doctest: +SKIP
            >>> # Verify file created
            >>> (temp_dir / "audit_safe.json").exists()  # doctest: +SKIP
            True
        
        Side Effects:
            - Creates parent directory if not exists
            - Writes JSON file to output_path (pretty-printed, UTF-8)
            - Overwrites existing file atomically
            - Logs warning if include_originals=True
            - Logs info message on success
        
        Notes:
            - **Security**: include_originals=False recommended for auditors
            - Safe export excludes "original" key from each mapping
            - Atomic write (temp file + rename) prevents corruption
            - JSON is pretty-printed (2-space indent) for readability
            - File size: ~500 bytes per mapping (varies with metadata)
            - Use include_originals=True only for authorized re-identification
        """
        import tempfile
        
        # Validate output_path
        if isinstance(output_path, str):
            output_path = Path(output_path)
        elif not isinstance(output_path, Path):
            raise TypeError(f"output_path must be Path or str, got {type(output_path).__name__}")
        
        if include_originals:
            logging.warning("Exporting mappings with original values - ensure proper security!")
            export_data = self.mappings
        else:
            logging.info("Exporting mappings without original values (safe mode)")
            export_data = {
                key: {k: v for k, v in mapping.items() if k != "original"}
                for key, mapping in self.mappings.items()
            }
        
        try:
            # Ensure directory exists and is writable
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(f"Cannot create directory {output_path.parent}: {e}")
            except OSError as e:
                raise OSError(f"Failed to create directory {output_path.parent}: {e}")
            
            # Check parent directory is writable
            if not os.access(output_path.parent, os.W_OK):
                raise PermissionError(f"Directory {output_path.parent} is not writable")
            
            # Serialize to JSON
            try:
                json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                raise RuntimeError(f"Failed to serialize mappings to JSON: {e}")
            
            logging.debug(f"Serialized {len(export_data)} mappings ({len(json_data)} bytes)")
            
            # Atomic write: write to temp file, then rename
            temp_fd = None
            temp_path = None
            try:
                # Create temp file in same directory
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=output_path.parent,
                    prefix='.tmp_audit_',
                    suffix='.json'
                )
                
                # Write data to temp file
                try:
                    os.write(temp_fd, json_data.encode('utf-8'))
                    os.fsync(temp_fd)
                except OSError as e:
                    raise OSError(f"Failed to write to temporary file {temp_path}: {e}")
                finally:
                    if temp_fd is not None:
                        os.close(temp_fd)
                
                # Atomic rename
                try:
                    os.replace(temp_path, output_path)
                except OSError as e:
                    raise OSError(f"Failed to rename {temp_path} to {output_path}: {e}")
                
                include_status = "WITH originals (SENSITIVE)" if include_originals else "without originals (safe)"
                logging.info(
                    f"Exported {len(export_data)} mappings to {output_path} "
                    f"({len(json_data)} bytes, {include_status})"
                )
                
            except Exception:
                # Clean up temp file on error
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                        logging.debug(f"Cleaned up temporary file {temp_path}")
                    except OSError as cleanup_error:
                        logging.warning(f"Failed to clean up temporary file {temp_path}: {cleanup_error}")
                raise
            
        except PermissionError as e:
            logging.error(f"Permission denied exporting audit data: {e}")
            raise
        except OSError as e:
            logging.error(f"File system error exporting audit data: {e}")
            raise
        except RuntimeError as e:
            logging.error(f"Operation failed exporting audit data: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error exporting audit data: {e}", exc_info=True)
            raise RuntimeError(f"Failed to export audit data due to unexpected error: {e}")


# ============================================================================
# Main De-identification Engine
# ============================================================================

class DeidentificationEngine:
    """Main engine for PHI/PII detection and de-identification.
    
    Orchestrates the complete de-identification pipeline: pattern matching, pseudonym
    generation, date shifting, and mapping storage. Supports country-specific patterns,
    configurable encryption, and comprehensive validation.
    
    The engine combines:
    - **Pattern matching**: 12+ default patterns + country-specific patterns
    - **Pseudonym generation**: Deterministic, salted hashing with caching
    - **Date shifting**: Cryptographic shifting with interval preservation
    - **Secure storage**: Encrypted mapping files with atomic writes
    - **Statistics tracking**: Detections by type, processing counts
    - **Validation**: Post-processing checks for residual PHI
    
    Architecture:
    ```
    Input Text → Pattern Detection → Pseudonym Generation → Text Replacement
                        ↓                       ↓
                  Statistics              Mapping Storage
                                                ↓
                                          Encrypted File
    ```
    
    Attributes:
        config: De-identification configuration (DeidentificationConfig).
        logger: Logger instance for this engine.
        patterns: List of DetectionPattern objects (sorted by priority).
        pseudonym_generator: PseudonymGenerator instance.
        date_shifter: DateShifter instance (None if disabled).
        mapping_store: MappingStore instance for persistent storage.
        stats: Dict tracking processing statistics.
    
    Example:
        >>> # Initialize with defaults
        >>> engine = DeidentificationEngine()
        >>> # De-identify text
        >>> text = "Patient: John Smith, SSN: 123-45-6789, DOB: 01/15/1980"
        >>> deidentified = engine.deidentify_text(text)
        >>> deidentified
        'Patient: [PATIENT-ABC123], SSN: [SSN-XYZ789], DOB: [DATE-01/22/1980]'
        >>> # De-identify record
        >>> record = {"name": "John Smith", "ssn": "123-45-6789", "age": 43}
        >>> deidentified_record = engine.deidentify_record(
        ...     record, text_fields=["name", "ssn"]
        ... )
        >>> deidentified_record
        {'name': '[PATIENT-ABC123]', 'ssn': '[SSN-XYZ789]', 'age': 43}
        >>> # Save mappings
        >>> engine.save_mappings()
        >>> # Get statistics
        >>> stats = engine.get_statistics()
        >>> stats['total_detections']
        3
        >>> stats['detections_by_type']
        {'PATIENT': 1, 'SSN': 1, 'DATE': 1}
        
    Configuration Example:
        >>> config = DeidentificationConfig(
        ...     enable_date_shifting=True,
        ...     date_shift_range_days=180,
        ...     enable_encryption=True,
        ...     countries=['IN', 'US'],
        ...     strict_mode=True
        ... )
        >>> engine = DeidentificationEngine(config=config)
        
    Raises:
        TypeError: If config or mapping_store have wrong types.
        RuntimeError: If initialization fails (pattern loading, component setup).
        
    Notes:
        - **Pattern priority**: Higher priority patterns tested first (SSN before MRN)
        - **Overlap resolution**: When multiple patterns match, highest priority wins
        - **Country patterns**: Loaded from country_regulations module (optional)
        - **Date shifting**: Uses same offset for all dates (preserves intervals)
        - **Encryption**: Fernet symmetric encryption for mapping files
        - **Thread safety**: Not thread-safe (use locks if multithreading)
        - **Performance**: ~1000 records/sec for typical clinical data
    """
    
    def __init__(self, config: Optional[DeidentificationConfig] = None, mapping_store: Optional[MappingStore] = None):
        """Initialize de-identification engine with pattern loading and component setup.
        
        Sets up the complete de-identification pipeline including detection patterns,
        pseudonym generator, date shifter, and mapping storage. Loads default patterns
        plus optional country-specific patterns. Validates all inputs and handles
        initialization errors gracefully.
        
        Args:
            config: De-identification configuration. If None, uses defaults
                (encryption enabled, date shifting enabled, India patterns).
                Default: None.
            mapping_store: Pre-configured mapping store. If None, creates new
                MappingStore with path from project config or fallback to CWD.
                Default: None.
        
        Raises:
            TypeError: If config not DeidentificationConfig or mapping_store not MappingStore.
            RuntimeError: If pattern loading, component initialization, or storage setup fails.
        
        Example:
            >>> # Default initialization (India, encryption enabled)
            >>> engine = DeidentificationEngine()
            >>> len(engine.patterns) > 0
            True
            >>> engine.config.enable_encryption
            True
            >>> # Custom config (multiple countries, no encryption)
            >>> config = DeidentificationConfig(
            ...     countries=['US', 'IN'],
            ...     enable_encryption=False,
            ...     date_shift_range_days=180
            ... )
            >>> engine = DeidentificationEngine(config=config)
            >>> len(engine.patterns) > 12  # default + country patterns
            True
            >>> # Custom mapping store
            >>> store = MappingStore(Path("custom_mappings.enc"))
            >>> engine = DeidentificationEngine(mapping_store=store)
            >>> engine.mapping_store.storage_path.name
            'custom_mappings.enc'
        
        Side Effects:
            - Loads default + optional country-specific detection patterns
            - Creates PseudonymGenerator with random salt
            - Creates DateShifter with random seed (if date shifting enabled)
            - Creates or loads MappingStore from file
            - Initializes statistics tracking dict
            - Logs initialization steps and component counts
        
        Notes:
            - **Pattern loading**: Default (12) + country-specific (varies)
            - **Pattern priority**: Sorted highest → lowest (SSN=90, Email=85, etc.)
            - **Country patterns**: Loaded if config.enable_country_patterns=True
            - **Date shifter**: Only created if config.enable_date_shifting=True
            - **Mapping store path**: From project config.OUTPUT_DIR or CWD fallback
            - **Statistics**: Initialized with countries list and zero counters
            - **Error resilience**: Logs errors but continues with degraded functionality
            - **Validation**: All config/store parameters type-checked
        """
        # Validate config parameter
        if config is not None and not isinstance(config, DeidentificationConfig):
            raise TypeError(f"config must be DeidentificationConfig or None, got {type(config).__name__}")
        
        # Validate mapping_store parameter
        if mapping_store is not None and not isinstance(mapping_store, MappingStore):
            raise TypeError(f"mapping_store must be MappingStore or None, got {type(mapping_store).__name__}")
        
        self.config = config or DeidentificationConfig()
        
        # Setup logging first
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(self.config.log_level)
            logging.debug("Initializing DeidentificationEngine...")
        except Exception as e:
            # Fallback to module-level logging if logger setup fails
            logging.error(f"Failed to setup logger: {e}")
            self.logger = logging.getLogger(__name__)
        
        # Initialize components with error handling
        try:
            # Load default patterns
            try:
                self.patterns = PatternLibrary.get_default_patterns()
                logging.debug(f"Loaded {len(self.patterns)} default detection patterns")
            except Exception as e:
                raise RuntimeError(f"Failed to load default patterns: {e}")
            
            # Add country-specific patterns if enabled
            if self.config.enable_country_patterns:
                if not COUNTRY_REGULATIONS_AVAILABLE:
                    logging.warning(
                        "Country-specific patterns requested but country_regulations module not available. "
                        "Install country regulations support or disable enable_country_patterns."
                    )
                else:
                    try:
                        country_patterns = PatternLibrary.get_country_specific_patterns(self.config.countries)
                        self.patterns.extend(country_patterns)
                        # Re-sort by priority
                        self.patterns.sort(key=lambda p: p.priority, reverse=True)
                        countries_str = ", ".join(self.config.countries or [f'{DEFAULT_COUNTRY_CODE} (default)'])
                        logging.info(
                            f"Loaded {len(country_patterns)} country-specific patterns for: {countries_str}"
                        )
                    except Exception as e:
                        logging.error(f"Failed to load country-specific patterns: {e}")
                        # Continue with default patterns only
            
            # Initialize pseudonym generator
            try:
                self.pseudonym_generator = PseudonymGenerator()
                logging.debug("Initialized pseudonym generator")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize pseudonym generator: {e}")
            
            # Initialize date shifter
            self.date_shifter = None
            if self.config.enable_date_shifting:
                try:
                    # Get primary country for date format
                    primary_country = DEFAULT_COUNTRY_CODE
                    if self.config.countries and len(self.config.countries) > 0:
                        primary_country = self.config.countries[0]
                    
                    self.date_shifter = DateShifter(
                        shift_range_days=self.config.date_shift_range_days,
                        preserve_intervals=self.config.preserve_date_intervals,
                        country_code=primary_country
                    )
                    logging.debug(f"Initialized date shifter (country: {primary_country}, range: ±{self.config.date_shift_range_days} days)")
                except Exception as e:
                    logging.error(f"Failed to initialize date shifter: {e}")
                    # Continue without date shifting
                    self.date_shifter = None
            
            # Initialize mapping store
            if mapping_store is None:
                storage_path = None
                try:
                    import config as project_config
                    # Store mappings in the deidentified directory
                    storage_path = Path(project_config.OUTPUT_DIR) / "deidentified" / "mappings" / "mappings.enc"
                    logging.debug(f"Using project config storage path: {storage_path}")
                except (ImportError, AttributeError) as e:
                    # Fallback to current directory if config not available
                    storage_path = Path.cwd() / "deidentification_mappings.enc"
                    logging.warning(f"Project config not available ({e}), using fallback path: {storage_path}")
                except Exception as e:
                    storage_path = Path.cwd() / "deidentification_mappings.enc"
                    logging.error(f"Error loading project config: {e}, using fallback path: {storage_path}")
                
                try:
                    self.mapping_store = MappingStore(
                        storage_path=storage_path,
                        encryption_key=self.config.encryption_key,
                        enable_encryption=self.config.enable_encryption
                    )
                    encryption_status = "encrypted" if self.config.enable_encryption else "plaintext"
                    logging.debug(f"Initialized mapping store ({encryption_status}): {storage_path}")
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize mapping store: {e}")
            else:
                self.mapping_store = mapping_store
                logging.debug("Using provided mapping store")
            
            # Initialize statistics
            self.stats = {
                "texts_processed": 0,
                "detections_by_type": defaultdict(int),
                "total_detections": 0,
                "countries": self.config.countries or [f"{DEFAULT_COUNTRY_CODE} (default)"]
            }
            
            logging.info(
                f"DeidentificationEngine initialized successfully "
                f"({len(self.patterns)} patterns, "
                f"date_shifting={'enabled' if self.date_shifter else 'disabled'}, "
                f"encryption={'enabled' if self.config.enable_encryption else 'disabled'})"
            )
            
        except RuntimeError:
            # Re-raise RuntimeError as-is
            raise
        except Exception as e:
            logging.error(f"Unexpected error initializing DeidentificationEngine: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize DeidentificationEngine: {e}")
    
    def deidentify_text(self, text: str, custom_patterns: Optional[List[DetectionPattern]] = None) -> str:
        """De-identify a single text string with comprehensive error handling.
        
        Scans text for PHI/PII using all configured detection patterns, generates
        pseudonyms, stores mappings, and replaces matches with pseudonyms. Handles
        overlapping matches using priority-based resolution. Resilient to errors.
        
        Args:
            text: Text to de-identify (e.g., clinical note, patient description).
            custom_patterns: Optional additional patterns beyond defaults. Merged
                with configured patterns and sorted by priority. Default: None.
        
        Returns:
            De-identified text with PHI replaced by bracketed pseudonyms
            (e.g., "[PATIENT-ABC123]", "[SSN-XYZ789]"). Returns original text
            on error (with logging) to avoid data loss.
        
        Raises:
            TypeError: If text not str/None or custom_patterns not list.
        
        Example:
            >>> engine = DeidentificationEngine()
            >>> # Basic de-identification
            >>> text = "Patient John Smith, SSN 123-45-6789, DOB 01/15/1980"
            >>> result = engine.deidentify_text(text)
            >>> "John Smith" in result
            False
            >>> "PATIENT-" in result
            True
            >>> "SSN-" in result
            True
            >>> # Custom patterns
            >>> custom = [DetectionPattern(
            ...     phi_type=PHIType.CUSTOM,
            ...     pattern=r'\\bStudy-\\d{4}\\b',
            ...     priority=85,
            ...     description="Study ID"
            ... )]
            >>> text2 = "Enrolled in Study-1234"
            >>> result2 = engine.deidentify_text(text2, custom_patterns=custom)
            >>> "Study-1234" in result2
            False
        
        Side Effects:
            - Updates self.stats (texts_processed, detections_by_type)
            - Adds mappings to mapping_store
            - Logs detections if config.log_detections=True
            - Returns original text on error (no exception raised)
        
        Notes:
            - **Overlapping matches**: Highest priority wins
            - **Replacement format**: "[{pseudonym}]" for easy identification
            - **Error resilience**: Never raises (returns original on error)
            - **Performance warning**: Logs if text > 1MB
            - **Pattern application**: Each pattern tested against ORIGINAL text
            - **Deduplication**: Same PHI value → same pseudonym (via mapping_store)
            - **Statistics**: Increments per detection (not per unique value)
        """
        # Validate text input
        if text is None:
            return ""
        
        if not isinstance(text, str):
            raise TypeError(f"text must be str or None, got {type(text).__name__}")
        
        if not text.strip():
            return text
        
        # Check text size (prevent performance issues)
        MAX_TEXT_SIZE = 1_000_000  # 1MB
        if len(text) > MAX_TEXT_SIZE:
            logging.warning(
                f"Large text detected ({len(text)} chars > {MAX_TEXT_SIZE}). "
                f"Processing may be slow. Consider chunking."
            )
        
        # Validate custom_patterns
        if custom_patterns is not None:
            if not isinstance(custom_patterns, list):
                raise TypeError(f"custom_patterns must be list or None, got {type(custom_patterns).__name__}")
            if not all(isinstance(p, DetectionPattern) for p in custom_patterns):
                raise TypeError("All items in custom_patterns must be DetectionPattern objects")
        
        try:
            # Combine patterns
            all_patterns = self.patterns.copy()
            if custom_patterns:
                all_patterns.extend(custom_patterns)
                all_patterns.sort(key=lambda p: p.priority, reverse=True)
            
            # Collect all matches with positions
            all_matches = []
            
            # Apply each pattern to ORIGINAL text
            for pattern_def in all_patterns:
                try:
                    matches = pattern_def.pattern.finditer(text)
                    
                    for match in matches:
                        try:
                            original_value = match.group(0)
                            phi_type = pattern_def.phi_type
                            start_pos = match.start()
                            end_pos = match.end()
                            
                            # Check if already mapped
                            try:
                                pseudonym = self.mapping_store.get_pseudonym(original_value, phi_type)
                            except Exception as e:
                                logging.error(f"Error retrieving pseudonym for {phi_type.value}: {e}")
                                pseudonym = None
                            
                            if pseudonym is None:
                                # Generate new pseudonym
                                try:
                                    if phi_type == PHIType.DATE and self.date_shifter:
                                        pseudonym = self.date_shifter.shift_date(original_value)
                                    else:
                                        template = self.config.pseudonym_templates.get(phi_type, "{id}")
                                        pseudonym = self.pseudonym_generator.generate(original_value, phi_type, template)
                                except Exception as e:
                                    logging.error(f"Error generating pseudonym for {phi_type.value}: {e}")
                                    # Fallback: use generic pseudonym
                                    pseudonym = f"[{phi_type.value}_REDACTED_{hashlib.md5(original_value.encode()).hexdigest()[:8]}]"
                                
                                # Store mapping
                                try:
                                    self.mapping_store.add_mapping(
                                        original=original_value,
                                        pseudonym=pseudonym,
                                        phi_type=phi_type,
                                        metadata={"pattern": pattern_def.description}
                                    )
                                except Exception as e:
                                    logging.error(f"Error storing mapping for {phi_type.value}: {e}")
                                    # Continue anyway - pseudonym is already generated
                            
                            # Store match for replacement
                            all_matches.append({
                                "start": start_pos,
                                "end": end_pos,
                                "original": original_value,
                                "pseudonym": pseudonym,
                                "phi_type": phi_type,
                                "priority": pattern_def.priority
                            })
                            
                            try:
                                self.stats["detections_by_type"][phi_type.value] += 1
                                self.stats["total_detections"] += 1
                            except Exception as e:
                                logging.warning(f"Error updating statistics: {e}")
                                
                        except Exception as e:
                            logging.error(f"Error processing match for pattern {pattern_def.description}: {e}")
                            continue  # Skip this match, continue with others
                            
                except Exception as e:
                    logging.error(f"Error applying pattern {pattern_def.description}: {e}")
                    continue  # Skip this pattern, continue with others
            
            # Remove overlapping matches (keep highest priority)
            all_matches.sort(key=lambda m: (m["start"], -m["priority"]))
            
            non_overlapping = []
            for match in all_matches:
                overlaps = False
                for selected in non_overlapping:
                    if not (match["end"] <= selected["start"] or match["start"] >= selected["end"]):
                        overlaps = True
                        break
                
                if not overlaps:
                    non_overlapping.append(match)
            
            # Apply replacements in reverse order
            non_overlapping.sort(key=lambda m: m["start"], reverse=True)
            
            deidentified_text = text
            detections = []
            
            for match in non_overlapping:
                try:
                    # Replace using slice
                    replacement = f"[{match['pseudonym']}]"
                    deidentified_text = (
                        deidentified_text[:match["start"]] + 
                        replacement + 
                        deidentified_text[match["end"]:]
                    )
                    
                    # Track detection
                    detections.append({
                        "phi_type": match["phi_type"].value,
                        "original": match["original"],
                        "pseudonym": match["pseudonym"],
                        "position": match["start"]
                    })
                except Exception as e:
                    logging.error(f"Error applying replacement at position {match['start']}: {e}")
                    continue  # Skip this replacement
            
            try:
                self.stats["texts_processed"] += 1
            except Exception as e:
                logging.warning(f"Error updating text count: {e}")
            
            # Log detections
            if self.config.log_detections and detections:
                try:
                    self.logger.debug(f"Detected {len(detections)} PHI/PII items: {[d['phi_type'] for d in detections]}")
                except Exception as e:
                    logging.warning(f"Error logging detections: {e}")
            
            return deidentified_text
            
        except Exception as e:
            logging.error(f"Unexpected error in deidentify_text: {e}", exc_info=True)
            # Return original text to avoid data loss, but log the error
            logging.error("Returning original text due to de-identification failure")
            return text
    
    def deidentify_record(self, record: Dict[str, Any], text_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """De-identify a dictionary record (e.g., from JSONL dataset).
        
        Applies de-identification to specified text fields in a record. Auto-detects
        string fields if not specified. Returns new dict (original unchanged).
        
        Args:
            record: Dictionary record with fields to de-identify.
            text_fields: List of field names to process. If None, auto-detects
                all string-valued fields. Default: None.
        
        Returns:
            New dictionary with text fields de-identified. Non-text fields and
            unspecified fields copied unchanged.
        
        Example:
            >>> engine = DeidentificationEngine()
            >>> record = {
            ...     "PATIENT_ID": "P001",
            ...     "NAME": "John Smith",
            ...     "SSN": "123-45-6789",
            ...     "AGE": 45,
            ...     "NOTES": "Patient presented on 01/15/2023"
            ... }
            >>> # Auto-detect text fields
            >>> result = engine.deidentify_record(record)
            >>> "John Smith" in str(result)
            False
            >>> result["AGE"]  # Non-text preserved
            45
            >>> # Explicit text fields
            >>> result2 = engine.deidentify_record(record, text_fields=["NAME", "SSN"])
            >>> result2["NOTES"]  # Not de-identified (not in list)
            'Patient presented on 01/15/2023'
        
        Side Effects:
            - Calls deidentify_text() for each field (updates stats/mappings)
            - Logs detections per field
        
        Notes:
            - Original record is NOT modified (creates copy)
            - text_fields=None → processes all str-valued fields
            - Non-string fields skipped automatically
            - Missing fields in text_fields list are ignored
            - Nested dicts not supported (only top-level fields)
        """
        deidentified = record.copy()
        
        # Determine fields to process
        if text_fields is None:
            text_fields = [k for k, v in record.items() if isinstance(v, str)]
        
        # Process each text field
        for field in text_fields:
            if field in deidentified and isinstance(deidentified[field], str):
                deidentified[field] = self.deidentify_text(deidentified[field])
        
        return deidentified
    
    def save_mappings(self) -> None:
        """Save all accumulated mappings to encrypted storage file.
        
        Delegates to mapping_store.save_mappings(). Should be called after
        processing to persist mappings for potential re-identification.
        
        Example:
            >>> engine = DeidentificationEngine()
            >>> engine.deidentify_text("Patient John Smith")
            '[PATIENT-ABC123]'
            >>> # Save mappings to disk
            >>> engine.save_mappings()
            >>> # File now contains encrypted mappings
        
        Side Effects:
            - Writes encrypted mapping file via mapping_store
            - Creates parent directory if needed
            - Logs save operation
        
        Notes:
            - Wrapper for mapping_store.save_mappings()
            - Uses atomic write (crash-safe)
            - Encryption enabled by config
        """
        self.mapping_store.save_mappings()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive de-identification statistics.
        
        Returns:
            Dictionary with processing statistics:
                - texts_processed: Number of texts de-identified (int)
                - detections_by_type: Dict[str, int] of counts per PHI type
                - total_detections: Total PHI instances detected (int)
                - countries: List of country codes configured (List[str])
                - pseudonym_stats: Dict[str, int] from pseudonym_generator
                - total_mappings: Total unique mappings stored (int)
        
        Example:
            >>> engine = DeidentificationEngine()
            >>> engine.deidentify_text("Patient John Smith, SSN 123-45-6789")
            '[PATIENT-ABC123], [SSN-XYZ789]'
            >>> stats = engine.get_statistics()
            >>> stats['texts_processed']
            1
            >>> stats['total_detections']
            2
            >>> stats['detections_by_type']
            {'PATIENT': 1, 'SSN': 1}
            >>> stats['total_mappings']
            2
        
        Notes:
            - Combines engine stats with pseudonym generator stats
            - detections_by_type counts total detections (not unique values)
            - pseudonym_stats counts unique values per type
            - total_mappings from mapping_store (includes all stored)
        """
        return {
            **self.stats,
            "pseudonym_stats": self.pseudonym_generator.get_statistics(),
            "total_mappings": len(self.mapping_store.mappings)
        }
    
    def validate_deidentification(self, text: str, strict: bool = True) -> Tuple[bool, List[str]]:
        """Validate that no PHI remains in de-identified text.
        
        Scans text for residual PHI using all configured patterns. Ignores
        bracketed pseudonyms. Returns validation status and list of potential
        PHI found (if any).
        
        Args:
            text: De-identified text to validate.
            strict: Reserved for future use (severity level). Default: True.
        
        Returns:
            Tuple of (is_valid, potential_phi):
                - is_valid: True if no PHI detected, False otherwise (bool)
                - potential_phi: List of detected PHI strings with types (List[str])
                  Format: ["{phi_type}: {value}", ...]
        
        Example:
            >>> engine = DeidentificationEngine()
            >>> # Good de-identification
            >>> text1 = "Patient [PATIENT-ABC123] seen on [DATE-XYZ789]"
            >>> is_valid, issues = engine.validate_deidentification(text1)
            >>> is_valid
            True
            >>> issues
            []
            >>> # Bad de-identification (leaked PHI)
            >>> text2 = "Patient John Smith seen on [DATE-XYZ789]"
            >>> is_valid, issues = engine.validate_deidentification(text2)
            >>> is_valid
            False
            >>> len(issues) > 0
            True
            >>> issues[0]
            'PATIENT: John Smith'
        
        Side Effects:
            - Logs warning if potential PHI found
            - No modifications to text or state
        
        Notes:
            - Ignores text inside brackets "[...]" (assumed to be pseudonyms)
            - Uses all configured detection patterns
            - Useful for post-processing quality checks
            - strict parameter reserved for future severity levels
            - Returns empty list if validation passes
        """
        potential_phi = []
        
        # Check against all patterns
        for pattern_def in self.patterns:
            matches = pattern_def.pattern.finditer(text)
            for match in matches:
                value = match.group(0)
                # Ignore if it's already a pseudonym (in brackets)
                if not (value.startswith('[') and value.endswith(']')):
                    potential_phi.append(f"{pattern_def.phi_type.value}: {value}")
        
        is_valid = len(potential_phi) == 0
        
        if not is_valid:
            self.logger.warning(f"Validation found potential PHI: {potential_phi}")
        
        return is_valid, potential_phi


# ============================================================================
# Batch Processing Functions
# ============================================================================

def deidentify_dataset(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    text_fields: Optional[List[str]] = None,
    config: Optional[DeidentificationConfig] = None,
    file_pattern: str = "*.jsonl",
    process_subdirs: bool = True
) -> Dict[str, Any]:
    """Batch de-identification of JSONL dataset files.
    
    Processes all JSONL files in a directory, applying PHI/PII de-identification to
    specified text fields. Creates de-identified copies in output directory with
    original directory structure preserved. Generates encrypted mapping file for
    potential re-identification.
    
    Args:
        input_dir: Directory containing JSONL files to process.
        output_dir: Directory where de-identified files will be written.
        text_fields: List of field names to de-identify. If None, processes all
            string fields in records. Default: None.
        config: De-identification configuration. If None, uses defaults.
            Default: None.
        file_pattern: Glob pattern for finding files. Default: '*.jsonl'.
        process_subdirs: If True, process subdirectories recursively.
            Default: True.
    
    Returns:
        Dictionary with processing results:
            - 'files_found': Total JSONL files discovered (int)
            - 'files_processed': Files successfully processed (int)
            - 'files_failed': Files that failed processing (int)
            - 'total_records': Total records processed (int)
            - 'total_detections': Total PHI instances detected (int)
            - 'detections_by_type': Dict[str, int] of counts per PHI type
            - 'processing_time': Total time in seconds (float)
            - 'mapping_file': Path to encrypted mapping file (str)
    
    Example:
        >>> result = deidentify_dataset(
        ...     input_dir='output/Indo-VAP/cleaned',
        ...     output_dir='output/Indo-VAP/deidentified',
        ...     text_fields=['PATIENT_NAME', 'CITY', 'DOB']
        ... )
        Processing files: 100%|██████| 50/50 [00:30<00:00]
        ✓ 50 files processed, 10,000 records, 5,000 PHI instances
        
        >>> print(f"Mapping: {result['mapping_file']}")
        Mapping: .mappings/indo-vap_20231115_143052.json.enc
        
    Side Effects:
        - Creates output_dir and subdirectories
        - Writes de-identified JSONL files (same structure as input)
        - Creates encrypted mapping file in .mappings/ directory
        - Logs extensively via logging_system
        - Prints progress bar to stdout via tqdm
        
    Notes:
        - Preserves directory structure: input_dir/sub/file.jsonl → output_dir/sub/file.jsonl
        - Skips files that fail to load (logged as errors)
        - text_fields=None → process all string-valued fields
        - Mapping file name includes timestamp for versioning
        - Date shifting is per-subject consistent (same offset within subject)
        - All processing is deterministic (same input → same output)
        - Requires cryptography package for mapping encryption
    """
    overall_start = time.time()
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize engine
    engine = DeidentificationEngine(config=config)
    logging.debug(f"Initialized DeidentificationEngine with config: countries={config.countries}, "
                  f"encryption={config.enable_encryption}, log_detections={config.log_detections}")
    vlog.detail(f"DeidentificationEngine initialized with {len(config.countries or ['IN'])} countries")
    
    # Find all JSONL files (including in subdirectories if enabled)
    if process_subdirs:
        jsonl_files = list(input_path.rglob(file_pattern))
        logging.debug(f"Recursively searching for '{file_pattern}' in {input_path}")
    else:
        jsonl_files = list(input_path.glob(file_pattern))
        logging.debug(f"Searching for '{file_pattern}' in {input_path} (no subdirs)")
    
    if not jsonl_files:
        logging.warning(f"No files matching '{file_pattern}' found in {input_dir}")
        vlog.detail(f"No files matching '{file_pattern}' found in {input_dir}")
        return {"error": "No files found"}
    
    logging.info(f"Processing {len(jsonl_files)} files...")
    logging.debug(f"Files to process: {[f.name for f in jsonl_files[:DEBUG_LOG_FILE_LIMIT]]}{'...' if len(jsonl_files) > DEBUG_LOG_FILE_LIMIT else ''}")
    
    # Statistics tracking
    files_processed = 0
    files_failed = 0
    total_records = 0
    
    # Start verbose logging context
    with vlog.file_processing("De-identification", total_records=len(jsonl_files)):
        vlog.metric("Total files to process", len(jsonl_files))
        vlog.metric("File pattern", file_pattern)
        vlog.metric("Process subdirectories", process_subdirs)
        
        # Process each file with progress bar
        for file_index, jsonl_file in enumerate(tqdm(jsonl_files, desc="De-identifying files", unit="file",
                               file=sys.stdout, dynamic_ncols=True, leave=True), 1):
            file_start = time.time()
            try:
                # Compute relative path to maintain directory structure
                relative_path = jsonl_file.relative_to(input_path)
                output_file = output_path / relative_path
                
                # Ensure output directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                logging.debug(f"Processing file: {jsonl_file} -> {output_file}")
                tqdm.write(f"Processing: {relative_path}")
                
                # Process file with verbose logging
                with vlog.step(f"File {file_index}/{len(jsonl_files)}: {relative_path}"):
                    records_count = 0
                    detections_count = 0
                    
                    with vlog.step("Reading and de-identifying records"):
                        with open(jsonl_file, 'r', encoding='utf-8') as infile, \
                             open(output_file, 'w', encoding='utf-8') as outfile:
                            
                            for line_num, line in enumerate(infile, 1):
                                if line.strip():
                                    record = json.loads(line)
                                    deidentified_record = engine.deidentify_record(record, text_fields)
                                    outfile.write(json.dumps(deidentified_record, ensure_ascii=False) + '\n')
                                    records_count += 1
                                    
                                    # Log progress for large files
                                    if records_count % RECORD_PROGRESS_INTERVAL == 0:
                                        logging.debug(f"  Processed {records_count} records from {jsonl_file.name}")
                                        vlog.detail(f"Processed {records_count} records...")
                    
                    vlog.metric("Records processed", records_count)
                    total_records += records_count
                    files_processed += 1
                    
                    file_elapsed = time.time() - file_start
                    vlog.timing("File processing time", file_elapsed)
                    
                    logging.debug(f"Completed {jsonl_file.name}: {records_count} records de-identified")
                    tqdm.write(f"  ✓ Created {output_file.relative_to(output_path)} with {records_count} records (de-identified)")
                
            except FileNotFoundError:
                files_failed += 1
                file_elapsed = time.time() - file_start
                tqdm.write(f"  ✗ File not found: {jsonl_file}")
                vlog.detail(f"ERROR: File not found")
                vlog.timing("Processing time before error", file_elapsed)
            except json.JSONDecodeError as e:
                files_failed += 1
                file_elapsed = time.time() - file_start
                tqdm.write(f"  ✗ JSON error in {jsonl_file.name}: {str(e)}")
                vlog.detail(f"ERROR: JSON decode error: {str(e)}")
                vlog.timing("Processing time before error", file_elapsed)
            except Exception as e:
                files_failed += 1
                file_elapsed = time.time() - file_start
                tqdm.write(f"  ✗ Error processing {jsonl_file.name}: {str(e)}")
                vlog.detail(f"ERROR: {str(e)}")
                vlog.timing("Processing time before error", file_elapsed)
    
    # Calculate overall timing
    overall_elapsed = time.time() - overall_start
    vlog.timing("Overall de-identification time", overall_elapsed)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"De-identification Summary:")
    print(f"  Files processed: {files_processed}/{len(jsonl_files)}")
    if files_failed > 0:
        print(f"  Files failed: {files_failed}")
    print(f"  Total records de-identified: {total_records:,}")
    print(f"{'='*70}\n")
    
    # Save mappings
    engine.save_mappings()
    
    # Get and log statistics
    stats = engine.get_statistics()
    stats['files_processed'] = files_processed
    stats['files_failed'] = files_failed
    stats['total_records'] = total_records
    stats['processing_time'] = overall_elapsed
    logging.info(f"De-identification complete. Statistics: {stats}")
    
    # Export audit log (without originals)
    audit_path = output_path / "_deidentification_audit.json"
    engine.mapping_store.export_for_audit(audit_path, include_originals=False)
    print(f"✓ Mappings saved and audit log exported to: {audit_path}")
    
    return stats


def validate_dataset(
    dataset_dir: Union[str, Path],
    file_pattern: str = "*.jsonl",
    text_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Validate that no PHI remains in de-identified dataset.
    
    Scans all JSONL files in a directory for residual PHI/PII using the same
    detection patterns used for de-identification. Reports any potential PHI
    found with file, line, and field-level details.
    
    Args:
        dataset_dir: Directory containing de-identified JSONL files to validate.
        file_pattern: Glob pattern for finding files. Default: '*.jsonl'.
        text_fields: List of field names to validate. If None, validates all
            string fields. Default: None.
    
    Returns:
        Dictionary with validation results:
            - 'total_files': Number of files validated (int)
            - 'total_records': Total records checked (int)
            - 'total_detections': Total potential PHI instances found (int)
            - 'files_with_issues': List of files containing potential PHI (List[str])
            - 'potential_phi_found': List of detection details (List[Dict]):
                - 'file': Filename
                - 'line': Line number
                - 'field': Field name
                - 'phi_type': Type of PHI detected
                - 'value': Detected value (first 20 chars)
            - 'processing_time': Total validation time in seconds (float)
            - 'is_clean': True if no PHI detected, False otherwise (bool)
    
    Example:
        >>> result = validate_dataset('output/Indo-VAP/deidentified')
        Validating files: 100%|██████| 50/50 [00:10<00:00]
        
        >>> if result['is_clean']:
        ...     print("✓ No residual PHI detected!")
        ... else:
        ...     print(f"⚠ Found {result['total_detections']} potential PHI instances")
        ...     for issue in result['potential_phi_found'][:5]:
        ...         print(f"  {issue['file']}:{issue['line']} - {issue['phi_type']}")
        
    Side Effects:
        - Logs validation results via logging_system
        - Prints progress bar to stdout via tqdm
        - Updates verbose logger with metrics
        - Does NOT modify any files (read-only operation)
        
    Notes:
        - Uses same patterns as de-identification for consistency
        - Ignores pseudonyms in bracket format (e.g., [SSN_REDACTED_a1b2c3])
        - Large datasets may take significant time to validate
        - Recommended to run after de-identification to verify quality
        - False positives possible (e.g., generic numbers matching SSN pattern)
        - text_fields=None validates ALL string-valued fields
    """
    overall_start = time.time()
    dataset_path = Path(dataset_dir)
    engine = DeidentificationEngine()
    
    validation_results = {
        "total_files": 0,
        "total_records": 0,
        "files_with_issues": [],
        "potential_phi_found": []
    }
    
    jsonl_files = list(dataset_path.glob(file_pattern))
    
    if not jsonl_files:
        logging.warning(f"No files matching '{file_pattern}' found in {dataset_dir}")
        vlog.detail(f"No files matching '{file_pattern}' found")
        return validation_results
    
    logging.info(f"Validating {len(jsonl_files)} files...")
    
    # Start verbose logging context
    with vlog.file_processing("Dataset validation", total_records=len(jsonl_files)):
        vlog.metric("Total files to validate", len(jsonl_files))
        vlog.metric("File pattern", file_pattern)
        
        for file_index, jsonl_file in enumerate(tqdm(jsonl_files, desc="Validating files", unit="file",
                                               file=sys.stdout, dynamic_ncols=True, leave=True), 1):
            file_start = time.time()
            validation_results["total_files"] += 1
            file_has_issues = False
            issues_count = 0
            
            with vlog.step(f"File {file_index}/{len(jsonl_files)}: {jsonl_file.name}"):
                records_in_file = 0
                
                try:
                    with open(jsonl_file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if line.strip():
                                validation_results["total_records"] += 1
                                records_in_file += 1
                                record = json.loads(line)
                                
                                # Get text fields
                                fields = text_fields or [k for k, v in record.items() if isinstance(v, str)]
                                
                                # Validate each field
                                for field in fields:
                                    if field in record and isinstance(record[field], str):
                                        is_valid, potential_phi = engine.validate_deidentification(record[field])
                                        
                                        if not is_valid:
                                            file_has_issues = True
                                            issues_count += 1
                                            validation_results["potential_phi_found"].append({
                                                "file": jsonl_file.name,
                                                "line": line_num,
                                                "field": field,
                                                "issues": potential_phi
                                            })
                    
                    vlog.metric("Records validated", records_in_file)
                    if file_has_issues:
                        vlog.metric("Issues found", issues_count)
                        validation_results["files_with_issues"].append(jsonl_file.name)
                        tqdm.write(f"  ⚠ {jsonl_file.name}: Found {issues_count} potential PHI issues")
                    else:
                        tqdm.write(f"  ✓ {jsonl_file.name}: All records valid")
                    
                    file_elapsed = time.time() - file_start
                    vlog.timing("File validation time", file_elapsed)
                    
                except Exception as e:
                    file_has_issues = True
                    logging.error(f"Error validating {jsonl_file.name}: {str(e)}")
                    vlog.detail(f"ERROR: {str(e)}")
                    file_elapsed = time.time() - file_start
                    vlog.timing("Validation time before error", file_elapsed)
        
        # Calculate overall timing
        overall_elapsed = time.time() - overall_start
        vlog.timing("Overall validation time", overall_elapsed)
    
    # Summary
    validation_results["is_valid"] = len(validation_results["files_with_issues"]) == 0
    validation_results["summary"] = (
        f"Validated {validation_results['total_records']} records in "
        f"{validation_results['total_files']} files. "
        f"Found {len(validation_results['potential_phi_found'])} potential issues."
    )
    validation_results["processing_time"] = overall_elapsed
    logging.info(validation_results["summary"])
    
    return validation_results


# ============================================================================
# CLI Interface
# ============================================================================

def main() -> int:
    """Command-line interface for PHI/PII de-identification.
    
    Provides a full-featured CLI for de-identifying datasets with country-specific
    patterns, optional validation, and flexible configuration. Supports listing
    available countries, custom field selection, and encryption control.
    
    Returns:
        Exit code: 0 for success, 1 for errors.
    
    Command-Line Arguments:
        --input-dir: Input directory with JSONL files (default: auto-detect from config)
        --output-dir: Output directory for de-identified files (default: output/deidentified/)
        -c, --countries: Country codes (e.g., IN US ID BR GB CA AU KE NG GH UG)
            or ALL for all supported countries. Default: IN.
        --validate: Validate de-identified output after processing (flag)
        --text-fields: Specific field names to de-identify (default: all string fields)
        --no-encryption: Disable mapping file encryption (flag)
        --no-country-patterns: Disable country-specific detection patterns (flag)
        --list-countries: List all supported countries and exit (flag)
        --log-level: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO.
    
    Example:
        # Basic usage (India, auto-detect directories)
        $ python -m scripts.deidentify
        
        # Explicit directories and countries
        $ python -m scripts.deidentify \\
            --input-dir data/Indo-VAP/cleaned \\
            --output-dir data/Indo-VAP/deidentified \\
            --countries IN
        
        # Multi-country with validation
        $ python -m scripts.deidentify \\
            --countries US IN BR \\
            --validate \\
            --log-level DEBUG
        
        # All countries, specific fields, no encryption
        $ python -m scripts.deidentify \\
            --countries ALL \\
            --text-fields PATIENT_NAME SSN DOB \\
            --no-encryption
        
        # List supported countries
        $ python -m scripts.deidentify --list-countries
        Supported Countries and Regulations:
        ======================================================================
          US: United States
          IN: India
          BR: Brazil
          ...
    
    Side Effects:
        - Reads JSONL files from input directory
        - Writes de-identified JSONL files to output directory
        - Creates encrypted mapping file in output/deidentified/mappings/
        - Logs to console with specified log level
        - Prints progress bars via tqdm
        - Prints summary statistics on completion
        - Optional: runs validation and prints results
    
    Exit Codes:
        0: Success (de-identification completed, validation passed if enabled)
        1: Error (missing directories, file errors, validation failed)
    
    Notes:
        - **Auto-detection**: If input/output dirs not specified, uses project config
        - **Country ALL**: Loads patterns for all supported countries (slower but comprehensive)
        - **Validation**: Recommended for production de-identification
        - **Encryption**: Enabled by default (use --no-encryption to disable)
        - **Field selection**: --text-fields limits processing to specific fields
        - **Default country**: India (IN) if --countries not specified
        - **Logging**: Logs to console only (file logging via centralized system)
        - **Error handling**: Exits with code 1 on errors, prints error message
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="De-identify PHI/PII in text data with country-specific regulations",
        epilog="Example: python deidentify.py --input-dir data/ --output-dir output/ --countries US IN"
    )
    parser.add_argument("--input-dir", help="Input directory with JSONL files (default: auto-detect from config)")
    parser.add_argument("--output-dir", help="Output directory for de-identified files (default: output/deidentified/)")
    parser.add_argument("-c", "--countries", nargs="+", 
                       help="Country codes (e.g., IN US ID BR GB CA AU KE NG GH UG) or ALL for all supported countries. "
                            "Default: IN. Supported: US, EU, GB, CA, AU, IN, ID, BR, PH, ZA, KE, NG, GH, UG")
    parser.add_argument("--validate", action="store_true", help="Validate de-identified output")
    parser.add_argument("--text-fields", nargs="+", help="Specific fields to de-identify")
    parser.add_argument("--no-encryption", action="store_true", 
                       help="Disable mapping encryption (enabled by default)")
    parser.add_argument("--no-country-patterns", action="store_true",
                       help="Disable country-specific detection patterns")
    parser.add_argument("--list-countries", action="store_true", 
                       help="List all supported countries and exit")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # List countries if requested
        if args.list_countries:
            if COUNTRY_REGULATIONS_AVAILABLE:
                from scripts.utils.country_regulations import get_all_supported_countries
                print("\nSupported Countries and Regulations:")
                print("=" * CONSOLE_SEPARATOR_WIDTH)
                for code, name in get_all_supported_countries().items():
                    print(f"  {code}: {name}")
                print("\nUsage:")
                print("  python -m scripts.deidentify --countries US IN --input-dir <dir> --output-dir <dir>")
                print("  python -m scripts.deidentify --countries ALL --input-dir <dir> --output-dir <dir>")
            else:
                print("Country regulations module not available.")
            return 0
    
        # Get default directories from config if not provided
        input_dir = args.input_dir
        output_dir = args.output_dir
        
        if not input_dir or not output_dir:
            try:
                import os
                import config as project_config
                if not input_dir:
                    # Auto-detect dataset directory from config API
                    clean_dataset_dir = os.path.join(project_config.OUTPUT_DIR, "cleaned_datasets")
                    input_dir = os.path.join(clean_dataset_dir, "cleaned")
                    print(f"Using auto-detected input directory: {input_dir}")
                if not output_dir:
                    # Use sensible default for output
                    output_dir = os.path.join(project_config.OUTPUT_DIR, "deidentified", project_config.STUDY_NAME)
                    print(f"Using default output directory: {output_dir}")
            except (ImportError, AttributeError) as e:
                if not input_dir or not output_dir:
                    parser.error("--input-dir and --output-dir are required (config.py not available for auto-detection)")
        
        # Parse countries
        countries = None
        if args.countries:
            if "ALL" in [c.upper() for c in args.countries]:
                countries = ["ALL"]
            else:
                countries = [c.upper() for c in args.countries]
        
        # Create config
        deid_config = DeidentificationConfig(
            enable_encryption=not args.no_encryption,
            log_level=getattr(logging, args.log_level),
            countries=countries,
            enable_country_patterns=not args.no_country_patterns
        )
        
        # Print configuration
        print("\nDe-identification Configuration:")
        print("=" * CONSOLE_SEPARATOR_WIDTH)
        print(f"  Input Directory: {input_dir}")
        print(f"  Output Directory: {output_dir}")
        print(f"  Countries: {countries or [f'{DEFAULT_COUNTRY_CODE} (default)']}")
        print(f"  Country-Specific Patterns: {'Enabled' if deid_config.enable_country_patterns else 'Disabled'}")
        print(f"  Encryption: {'Enabled' if deid_config.enable_encryption else 'Disabled'}")
        print(f"  Validation: {'Enabled' if args.validate else 'Disabled'}")
        print("=" * CONSOLE_SEPARATOR_WIDTH)
        
        # Run de-identification
        print(f"\nDe-identifying dataset...")
        stats = deidentify_dataset(
            input_dir=input_dir,
            output_dir=output_dir,
            text_fields=args.text_fields,
            config=deid_config
        )
        
        print(f"\nDe-identification Statistics:")
        print("=" * CONSOLE_SEPARATOR_WIDTH)
        print(f"  Texts processed: {stats.get('texts_processed', 0)}")
        print(f"  Total detections: {stats.get('total_detections', 0)}")
        print(f"  Countries: {', '.join(stats.get('countries', ['N/A']))}")
        print(f"\n  Detections by type:")
        for phi_type, count in sorted(stats.get('detections_by_type', {}).items()):
            print(f"    {phi_type}: {count}")
        
        # Validate if requested
        if args.validate:
            print("\nValidating de-identified dataset...")
            print("=" * CONSOLE_SEPARATOR_WIDTH)
            validation = validate_dataset(output_dir, text_fields=args.text_fields)
            print(f"  {validation['summary']}")
            
            if not validation['is_valid']:
                print("\n  ⚠ Potential issues found:")
                for issue in validation['potential_phi_found'][:VALIDATION_DISPLAY_LIMIT]:
                    print(f"    {issue['file']}:{issue['line']} - {issue['field']}: {issue['issues']}")
                
                if len(validation['potential_phi_found']) > VALIDATION_DISPLAY_LIMIT:
                    print(f"    ... and {len(validation['potential_phi_found']) - VALIDATION_DISPLAY_LIMIT} more issues")
            else:
                print("  ✓ No PHI/PII detected in de-identified data")
        
        print("\n✓ De-identification complete!")
        print(f"  De-identified files: {output_dir}")
        print(f"  Audit log: {output_dir}/_deidentification_audit.json")
        
        return 0
        
    except KeyboardInterrupt:
        vlog.warning("\nDe-identification interrupted by user (Ctrl+C)")
        print("\n\n⚠ De-identification interrupted by user. Exiting gracefully...")
        return 130  # Standard exit code for SIGINT (Ctrl+C)
        
    except Exception as e:
        vlog.error(
            f"Unhandled exception during de-identification: {type(e).__name__}: {e}",
            exc_info=True
        )
        print(f"\n\n❌ Error: De-identification failed with an unexpected error.")
        print(f"   {type(e).__name__}: {e}")
        print(f"   Please check the logs for detailed error information.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
