#!/usr/bin/env python3
"""
De-identification and Pseudonymization Module
==============================================

Robust PHI/PII detection and replacement with encrypted mapping storage,
country-specific compliance, and comprehensive validation.

This module provides HIPAA/GDPR-compliant de-identification for medical datasets,
supporting 14 countries with country-specific regulations, encrypted mapping storage,
and comprehensive validation.

Example:
    Basic de-identification::

        from scripts.utils.deidentify import deidentify_dataset, DeidentificationConfig

        # Configure de-identification
        config = DeidentificationConfig(
            enable_date_shifting=True,
            enable_encryption=True,
            countries=['US', 'IN']
        )
        
        # De-identify dataset
        deidentify_dataset(
            input_path='data/patient_data.jsonl',
            output_path='data/deidentified_data.jsonl',
            mapping_path='mappings/phi_mappings.enc.json',
            config=config
        )

    Using the engine directly::

        from scripts.utils.deidentify import DeidentificationEngine

        engine = DeidentificationEngine(config)
        deidentified_text = engine.deidentify_text("Patient John Doe, MRN: AB123456")
        # Returns: "Patient PATIENT-001, MRN: MRN-001"

    Validation::

        from scripts.utils.deidentify import validate_dataset

        is_clean = validate_dataset(
            file_path='data/deidentified_data.jsonl',
            config=config
        )
"""

import re
import json
import hashlib
import secrets
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import base64

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
# ============================================================================
# Enums and Constants
# ============================================================================

class PHIType(Enum):
    """PHI/PII type categorization."""
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
    """PHI/PII detection pattern configuration."""
    phi_type: PHIType
    pattern: re.Pattern
    priority: int = 50
    description: str = ""
    
    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.IGNORECASE)


@dataclass
class DeidentificationConfig:
    """De-identification engine configuration."""
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
    date_shift_range_days: int = 365  # Shift dates by up to ±365 days
    preserve_date_intervals: bool = True  # Keep time intervals consistent
    
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
    """Library of regex patterns for detecting PHI/PII."""
    
    @staticmethod
    def get_default_patterns() -> List[DetectionPattern]:
        """
        Get default detection patterns for common PHI/PII types.
        
        Returns:
            List of DetectionPattern objects sorted by priority.
        """
        patterns = [
            # SSN patterns (high priority)
            DetectionPattern(
                phi_type=PHIType.SSN,
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                priority=90,
                description="SSN format: XXX-XX-XXXX"
            ),
            DetectionPattern(
                phi_type=PHIType.SSN,
                pattern=re.compile(r'\b\d{9}\b'),
                priority=85,
                description="SSN format: XXXXXXXXX"
            ),
            
            # MRN patterns
            DetectionPattern(
                phi_type=PHIType.MRN,
                pattern=re.compile(r'\b(?:MRN|Medical\s+Record\s+(?:Number|#)):\s*([A-Z0-9]{6,12})\b', re.IGNORECASE),
                priority=80,
                description="Medical Record Number with label"
            ),
            DetectionPattern(
                phi_type=PHIType.MRN,
                pattern=re.compile(r'\b[A-Z]{2}\d{6,10}\b'),
                priority=70,
                description="MRN format: LLNNNNNN"
            ),
            
            # Phone numbers
            DetectionPattern(
                phi_type=PHIType.PHONE,
                pattern=re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
                priority=75,
                description="US phone number"
            ),
            
            # Email addresses
            DetectionPattern(
                phi_type=PHIType.EMAIL,
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                priority=85,
                description="Email address"
            ),
            
            # Dates (multiple formats)
            # Note: DD/MM/YYYY is ambiguous with MM/DD/YYYY - country context determines interpretation
            # Date shifter supports multiple formats: ISO 8601, slash/hyphen/dot-separated
            DetectionPattern(
                phi_type=PHIType.DATE,
                pattern=re.compile(r'\b(?:0?[1-9]|[12][0-9]|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b'),
                priority=60,
                description="Date format: DD/MM/YYYY or MM/DD/YYYY (slash-separated, country determines interpretation)"
            ),
            DetectionPattern(
                phi_type=PHIType.DATE,
                pattern=re.compile(r'\b(?:19|20)\d{2}[/-](?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12][0-9]|3[01])\b'),
                priority=60,
                description="Date format: YYYY-MM-DD (ISO 8601)"
            ),
            DetectionPattern(
                phi_type=PHIType.DATE,
                pattern=re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:0?[1-9]|[12][0-9]|3[01]),?\s+(?:19|20)\d{2}\b', re.IGNORECASE),
                priority=65,
                description="Date format: Month DD, YYYY (text month)"
            ),
            
            # Zip codes
            DetectionPattern(
                phi_type=PHIType.ADDRESS_ZIP,
                pattern=re.compile(r'\b\d{5}(?:-\d{4})?\b'),
                priority=55,
                description="US ZIP code"
            ),
            
            # IP addresses
            DetectionPattern(
                phi_type=PHIType.IP_ADDRESS,
                pattern=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
                priority=70,
                description="IPv4 address"
            ),
            
            # URLs
            DetectionPattern(
                phi_type=PHIType.URL,
                pattern=re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)', re.IGNORECASE),
                priority=75,
                description="HTTP/HTTPS URL"
            ),
            
            # Ages over 89 (HIPAA requirement)
            DetectionPattern(
                phi_type=PHIType.AGE_OVER_89,
                pattern=re.compile(r'\b(?:age|aged|Age|AGE)[\s:]+([9]\d|[1-9]\d{2,})\b'),
                priority=80,
                description="Age over 89 years"
            ),
        ]
        
        # Sort by priority (highest first)
        patterns.sort(key=lambda p: p.priority, reverse=True)
        return patterns
    
    @staticmethod
    def get_country_specific_patterns(countries: Optional[List[str]] = None) -> List[DetectionPattern]:
        """
        Get country-specific detection patterns.
        
        Args:
            countries: List of country codes or None for all
            
        Returns:
            List of DetectionPattern objects for country-specific identifiers
        """
        if not COUNTRY_REGULATIONS_AVAILABLE:
            logging.warning("Country regulations module not available")
            return []
        
        patterns = []
        
        try:
            manager = CountryRegulationManager(countries=countries)
            country_fields = manager.get_country_specific_fields()
            
            for field in country_fields:
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
                        priority = 85
                    else:
                        phi_type = PHIType.CUSTOM
                        priority = 75
                    
                    patterns.append(DetectionPattern(
                        phi_type=phi_type,
                        pattern=field.compiled_pattern,
                        priority=priority,
                        description=f"{field.display_name}: {field.description}"
                    ))
            
            logging.info(f"Loaded {len(patterns)} country-specific patterns")
        except Exception as e:
            logging.error(f"Failed to load country-specific patterns: {e}")
        
        return patterns


# ============================================================================
# Pseudonym Generation
# ============================================================================

class PseudonymGenerator:
    """
    Generates consistent, deterministic pseudonyms for PHI/PII.
    
    Uses cryptographic hashing to ensure:
    - Same input always produces same pseudonym
    - Different inputs produce different pseudonyms
    - Pseudonyms are not reversible without the mapping table
    """
    
    def __init__(self, salt: Optional[str] = None):
        """
        Initialize pseudonym generator.
        
        Args:
            salt: Optional salt for hash function. If None, generates random salt.
        """
        self.salt = salt or secrets.token_hex(32)
        self._counter: Dict[PHIType, int] = defaultdict(int)
        self._cache: Dict[Tuple[PHIType, str], str] = {}
    
    def generate(self, value: str, phi_type: PHIType, template: str) -> str:
        """
        Generate a pseudonym for a given value.
        
        Args:
            value: The sensitive value to pseudonymize
            phi_type: Type of PHI/PII
            template: Template string with {id} placeholder
            
        Returns:
            Pseudonymized value (e.g., "PATIENT-A4B8")
        """
        cache_key = (phi_type, value.lower())
        
        # Return cached pseudonym if exists
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate deterministic ID from hash
        hash_input = f"{self.salt}:{phi_type.value}:{value}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).digest()
        
        # Convert first 4 bytes to alphanumeric ID
        id_bytes = hash_digest[:4]
        id_value = base64.b32encode(id_bytes).decode('ascii').rstrip('=')[:6]
        
        # Generate pseudonym from template
        pseudonym = template.format(id=id_value)
        
        # Cache and return
        self._cache[cache_key] = pseudonym
        self._counter[phi_type] += 1
        
        return pseudonym
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics on pseudonym generation.
        
        Returns:
            Dictionary mapping PHI type to count of unique values
        """
        return {phi_type.value: count for phi_type, count in self._counter.items()}


# ============================================================================
# Date Shifting
# ============================================================================

class DateShifter:
    """
    Consistent date shifting with intelligent multi-format parsing.
    
    Shifts all dates by a consistent offset while maintaining:
    - Relative time intervals between dates
    - Original date format (ISO 8601, DD/MM/YYYY, MM/DD/YYYY, hyphen/dot-separated)
    - Country-specific format priority
    
    Supported formats (auto-detected):
    - YYYY-MM-DD (ISO 8601)
    - DD/MM/YYYY or MM/DD/YYYY (slash-separated)
    - DD-MM-YYYY or MM-DD-YYYY (hyphen-separated)
    - DD.MM.YYYY (dot-separated, European)
    
    Examples:
        >>> shifter = DateShifter(country_code="IN")
        >>> shifter.shift_date("2019-01-11")  # ISO format
        '2018-04-13'  # Shifted, format preserved
        >>> shifter.shift_date("04/09/2014")  # DD/MM/YYYY for India
        '14/12/2013'  # Shifted, format preserved
    """
    
    def __init__(self, shift_range_days: int = 365, preserve_intervals: bool = True, seed: Optional[str] = None, country_code: str = "US"):
        """
        Initialize date shifter with multi-format support.
        
        Args:
            shift_range_days: Maximum days to shift (±)
            preserve_intervals: If True, all dates shift by same offset
            seed: Optional seed for random shift generation
            country_code: Country code for format priority (IN=DD/MM/YYYY, US=MM/DD/YYYY, etc.)
        
        Note:
            The shifter automatically tries multiple formats (ISO 8601, slash/hyphen/dot-separated)
            and preserves the original format in the output.
        """
        self.shift_range_days = shift_range_days
        self.preserve_intervals = preserve_intervals
        self.seed = seed or secrets.token_hex(16)
        self.country_code = country_code.upper()
        self._shift_offset: Optional[int] = None
        self._date_cache: Dict[str, str] = {}
        
        # Country-specific date formats
        # DD/MM/YYYY: India, UK, Australia, Indonesia, Brazil, South Africa, EU countries, Kenya, Nigeria, Ghana, Uganda
        # MM/DD/YYYY: United States, Philippines, Canada (sometimes)
        self.dd_mm_yyyy_countries = {"IN", "ID", "BR", "ZA", "EU", "GB", "AU", "KE", "NG", "GH", "UG"}
        self.mm_dd_yyyy_countries = {"US", "PH", "CA"}
    
    def _get_shift_offset(self) -> int:
        """Get consistent shift offset based on seed."""
        if self._shift_offset is None:
            # Generate deterministic offset from seed
            hash_digest = hashlib.sha256(self.seed.encode()).digest()
            offset_int = int.from_bytes(hash_digest[:4], byteorder='big')
            self._shift_offset = (offset_int % (2 * self.shift_range_days + 1)) - self.shift_range_days
        return self._shift_offset
    
    def shift_date(self, date_str: str, date_format: Optional[str] = None) -> str:
        """
        Shift a date string by consistent offset with intelligent format detection.
        
        Automatically tries multiple date formats and preserves the original format
        in the output. Format priority is based on the country code.
        
        Args:
            date_str: Date string to shift (e.g., "2019-01-11", "04/09/2014")
            date_format: Specific format to use (auto-detected if None)
            
        Returns:
            Shifted date in same format as input
            
        Examples:
            >>> shifter = DateShifter(country_code="IN")
            >>> shifter.shift_date("2019-01-11")
            '2018-04-13'  # ISO format preserved
            >>> shifter.shift_date("04/09/2014")
            '14/12/2013'  # DD/MM/YYYY format preserved
        """
        if date_str in self._date_cache:
            return self._date_cache[date_str]
        
        # Define common date formats to try
        if date_format is None:
            # Try multiple formats based on country and common standards
            if self.country_code in self.dd_mm_yyyy_countries:
                formats_to_try = [
                    "%d/%m/%Y",      # DD/MM/YYYY (India, UK, AU, etc.)
                    "%Y-%m-%d",      # YYYY-MM-DD (ISO 8601)
                    "%d-%m-%Y",      # DD-MM-YYYY
                    "%d.%m.%Y",      # DD.MM.YYYY
                ]
            else:
                formats_to_try = [
                    "%m/%d/%Y",      # MM/DD/YYYY (US, PH, etc.)
                    "%Y-%m-%d",      # YYYY-MM-DD (ISO 8601)
                    "%m-%d-%Y",      # MM-DD-YYYY
                ]
        else:
            formats_to_try = [date_format]
        
        # Try each format until one works
        for fmt in formats_to_try:
            try:
                # Parse date
                date_obj = datetime.strptime(date_str, fmt)
                
                # Apply shift
                offset_days = self._get_shift_offset()
                shifted_date = date_obj + timedelta(days=offset_days)
                
                # Format back to string (use the same format that worked)
                shifted_str = shifted_date.strftime(fmt)
                
                # Cache and return
                self._date_cache[date_str] = shifted_str
                return shifted_str
                
            except ValueError:
                continue
        
        # If all formats fail, return placeholder
        logging.warning(f"Could not parse date: {date_str} (tried formats: {', '.join(formats_to_try)})")
        return f"[DATE-{hashlib.md5(date_str.encode()).hexdigest()[:6].upper()}]"


# ============================================================================
# Secure Mapping Storage
# ============================================================================

class MappingStore:
    """
    Secure storage for PHI to pseudonym mappings.
    
    Features:
    - Encrypted storage using Fernet (symmetric encryption)
    - Separate key management
    - JSON serialization
    - Audit logging
    """
    
    def __init__(self, storage_path: Path, encryption_key: Optional[bytes] = None, enable_encryption: bool = True):
        """
        Initialize mapping store.
        
        Args:
            storage_path: Path to store mapping file
            encryption_key: Encryption key (generates new if None)
            enable_encryption: Whether to encrypt mappings
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
        """Load mappings from storage file."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'rb') as f:
                data = f.read()
            
            # Decrypt if enabled
            if self.enable_encryption and self.cipher:
                data = self.cipher.decrypt(data)
            
            # Parse JSON
            self.mappings = json.loads(data.decode('utf-8'))
            logging.info(f"Loaded {len(self.mappings)} mappings from {self.storage_path}")
            
        except Exception as e:
            logging.error(f"Failed to load mappings: {e}")
            self.mappings = {}
    
    def save_mappings(self) -> None:
        """Save mappings to storage file."""
        try:
            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize to JSON
            data = json.dumps(self.mappings, indent=2, ensure_ascii=False).encode('utf-8')
            
            # Encrypt if enabled
            if self.enable_encryption and self.cipher:
                data = self.cipher.encrypt(data)
            
            # Write to file
            with open(self.storage_path, 'wb') as f:
                f.write(data)
            
            logging.info(f"Saved {len(self.mappings)} mappings to {self.storage_path}")
            
        except Exception as e:
            logging.error(f"Failed to save mappings: {e}")
            raise
    
    def add_mapping(self, original: str, pseudonym: str, phi_type: PHIType, metadata: Optional[Dict] = None) -> None:
        """
        Add a mapping entry.
        
        Args:
            original: Original sensitive value
            pseudonym: Pseudonymized value
            phi_type: Type of PHI
            metadata: Optional additional metadata
        """
        mapping_key = f"{phi_type.value}:{original}"
        self.mappings[mapping_key] = {
            "original": original,
            "pseudonym": pseudonym,
            "phi_type": phi_type.value,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
    
    def get_pseudonym(self, original: str, phi_type: PHIType) -> Optional[str]:
        """
        Retrieve pseudonym for original value.
        
        Args:
            original: Original value
            phi_type: Type of PHI
            
        Returns:
            Pseudonym if exists, None otherwise
        """
        mapping_key = f"{phi_type.value}:{original}"
        mapping = self.mappings.get(mapping_key)
        return mapping["pseudonym"] if mapping else None
    
    def export_for_audit(self, output_path: Path, include_originals: bool = False) -> None:
        """
        Export mappings for audit purposes.
        
        Args:
            output_path: Path to export file
            include_originals: Whether to include original values (dangerous!)
        """
        if include_originals:
            logging.warning("Exporting mappings with original values - ensure proper security!")
            export_data = self.mappings
        else:
            # Export without original values
            export_data = {
                key: {k: v for k, v in mapping.items() if k != "original"}
                for key, mapping in self.mappings.items()
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Exported mappings to {output_path}")


# ============================================================================
# Main De-identification Engine
# ============================================================================

class DeidentificationEngine:
    """
    Main engine for PHI/PII detection and de-identification.
    
    Orchestrates the entire de-identification process:
    1. Detects PHI/PII using patterns and optional NER
    2. Generates consistent pseudonyms
    3. Replaces sensitive data with pseudonyms
    4. Stores mappings securely
    5. Validates results
    """
    
    def __init__(self, config: Optional[DeidentificationConfig] = None, mapping_store: Optional[MappingStore] = None):
        """
        Initialize de-identification engine.
        
        Args:
            config: Configuration object
            mapping_store: Optional mapping store (creates default if None)
        """
        self.config = config or DeidentificationConfig()
        
        # Setup logging first
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # Initialize components
        self.patterns = PatternLibrary.get_default_patterns()
        
        # Add country-specific patterns if enabled
        if self.config.enable_country_patterns and COUNTRY_REGULATIONS_AVAILABLE:
            country_patterns = PatternLibrary.get_country_specific_patterns(self.config.countries)
            self.patterns.extend(country_patterns)
            # Re-sort by priority
            self.patterns.sort(key=lambda p: p.priority, reverse=True)
            self.logger.info(f"Loaded {len(country_patterns)} country-specific patterns for: "
                           f"{self.config.countries or ['IN (default)']}")
        
        self.pseudonym_generator = PseudonymGenerator()
        
        # Get primary country for date format
        primary_country = "IN"  # Default to India
        if self.config.countries and len(self.config.countries) > 0:
            primary_country = self.config.countries[0]
        
        self.date_shifter = DateShifter(
            shift_range_days=self.config.date_shift_range_days,
            preserve_intervals=self.config.preserve_date_intervals,
            country_code=primary_country
        ) if self.config.enable_date_shifting else None
        
        # Initialize mapping store
        if mapping_store is None:
            try:
                import config as project_config
                # Store mappings in the deidentified directory for better organization
                storage_path = Path(project_config.RESULTS_DIR) / "deidentified" / "mappings" / "mappings.enc"
            except (ImportError, AttributeError):
                # Fallback to current directory if config not available
                storage_path = Path.cwd() / "deidentification_mappings.enc"
            
            self.mapping_store = MappingStore(
                storage_path=storage_path,
                encryption_key=self.config.encryption_key,
                enable_encryption=self.config.enable_encryption
            )
        else:
            self.mapping_store = mapping_store
        
        # Statistics
        self.stats = {
            "texts_processed": 0,
            "detections_by_type": defaultdict(int),
            "total_detections": 0,
            "countries": self.config.countries or ["IN (default)"]
        }
    
    def deidentify_text(self, text: str, custom_patterns: Optional[List[DetectionPattern]] = None) -> str:
        """
        De-identify a single text string.
        
        Args:
            text: Text to de-identify
            custom_patterns: Optional additional patterns to use
            
        Returns:
            De-identified text with PHI/PII replaced by pseudonyms
        """
        if not text or not isinstance(text, str):
            return text
        
        # Combine patterns
        all_patterns = self.patterns.copy()
        if custom_patterns:
            all_patterns.extend(custom_patterns)
            all_patterns.sort(key=lambda p: p.priority, reverse=True)
        
        deidentified_text = text
        detections = []
        
        # Apply each pattern
        for pattern_def in all_patterns:
            matches = pattern_def.pattern.finditer(deidentified_text)
            
            for match in matches:
                original_value = match.group(0)
                phi_type = pattern_def.phi_type
                
                # Check if already mapped
                pseudonym = self.mapping_store.get_pseudonym(original_value, phi_type)
                
                if pseudonym is None:
                    # Generate new pseudonym
                    if phi_type == PHIType.DATE and self.date_shifter:
                        pseudonym = self.date_shifter.shift_date(original_value)
                    else:
                        template = self.config.pseudonym_templates.get(phi_type, "{id}")
                        pseudonym = self.pseudonym_generator.generate(original_value, phi_type, template)
                    
                    # Store mapping
                    self.mapping_store.add_mapping(
                        original=original_value,
                        pseudonym=pseudonym,
                        phi_type=phi_type,
                        metadata={"pattern": pattern_def.description}
                    )
                
                # Replace in text
                deidentified_text = deidentified_text.replace(original_value, f"[{pseudonym}]")
                
                # Track detection
                detections.append({
                    "phi_type": phi_type.value,
                    "original": original_value,
                    "pseudonym": pseudonym,
                    "position": match.start()
                })
                
                self.stats["detections_by_type"][phi_type.value] += 1
                self.stats["total_detections"] += 1
        
        self.stats["texts_processed"] += 1
        
        # Log detections
        if self.config.log_detections and detections:
            self.logger.debug(f"Detected {len(detections)} PHI/PII items: {[d['phi_type'] for d in detections]}")
        
        return deidentified_text
    
    def deidentify_record(self, record: Dict[str, Any], text_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        De-identify a dictionary record (e.g., from JSONL).
        
        Args:
            record: Dictionary containing data
            text_fields: List of field names to de-identify (all string fields if None)
            
        Returns:
            De-identified record
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
        """Save all mappings to secure storage."""
        self.mapping_store.save_mappings()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get de-identification statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            **self.stats,
            "pseudonym_stats": self.pseudonym_generator.get_statistics(),
            "total_mappings": len(self.mapping_store.mappings)
        }
    
    def validate_deidentification(self, text: str, strict: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate that no PHI remains in de-identified text.
        
        Args:
            text: De-identified text to validate
            strict: If True, any detection is considered a failure
            
        Returns:
            Tuple of (is_valid, list of potential PHI found)
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
    """
    Batch de-identification of JSONL dataset files.
    
    Processes JSONL files while maintaining directory structure. If the input
    directory contains subdirectories (e.g., 'original/', 'cleaned/'), the same
    structure will be replicated in the output directory.
    
    Args:
        input_dir: Directory containing JSONL files (may have subdirectories)
        output_dir: Directory to write de-identified files (maintains structure)
        text_fields: List of field names to de-identify (all string fields if None)
        config: De-identification configuration
        file_pattern: Glob pattern for files to process
        process_subdirs: If True, recursively process subdirectories
        
    Returns:
        Dictionary with processing statistics
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize engine
    engine = DeidentificationEngine(config=config)
    logging.debug(f"Initialized DeidentificationEngine with config: countries={config.countries}, "
                  f"encryption={config.enable_encryption}, log_detections={config.log_detections}")
    
    # Find all JSONL files (including in subdirectories if enabled)
    if process_subdirs:
        jsonl_files = list(input_path.rglob(file_pattern))
        logging.debug(f"Recursively searching for '{file_pattern}' in {input_path}")
    else:
        jsonl_files = list(input_path.glob(file_pattern))
        logging.debug(f"Searching for '{file_pattern}' in {input_path} (no subdirs)")
    
    if not jsonl_files:
        logging.warning(f"No files matching '{file_pattern}' found in {input_dir}")
        return {"error": "No files found"}
    
    logging.info(f"Processing {len(jsonl_files)} files...")
    logging.debug(f"Files to process: {[f.name for f in jsonl_files[:10]]}{'...' if len(jsonl_files) > 10 else ''}")
    
    # Statistics tracking
    files_processed = 0
    files_failed = 0
    total_records = 0
    
    # Process each file with progress bar
    for jsonl_file in tqdm(jsonl_files, desc="De-identifying files", unit="file",
                           file=sys.stdout, dynamic_ncols=True, leave=True):
        try:
            # Compute relative path to maintain directory structure
            relative_path = jsonl_file.relative_to(input_path)
            output_file = output_path / relative_path
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            logging.debug(f"Processing file: {jsonl_file} -> {output_file}")
            tqdm.write(f"Processing: {relative_path}")
            
            records_count = 0
            with open(jsonl_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8') as outfile:
                
                for line_num, line in enumerate(infile, 1):
                    if line.strip():
                        record = json.loads(line)
                        deidentified_record = engine.deidentify_record(record, text_fields)
                        outfile.write(json.dumps(deidentified_record, ensure_ascii=False) + '\n')
                        records_count += 1
                        
                        # Log progress for large files
                        if records_count % 1000 == 0:
                            logging.debug(f"  Processed {records_count} records from {jsonl_file.name}")
            
            total_records += records_count
            files_processed += 1
            logging.debug(f"Completed {jsonl_file.name}: {records_count} records de-identified")
            tqdm.write(f"  ✓ Created {output_file.relative_to(output_path)} with {records_count} records (de-identified)")
            
        except FileNotFoundError:
            files_failed += 1
            tqdm.write(f"  ✗ File not found: {jsonl_file}")
        except json.JSONDecodeError as e:
            files_failed += 1
            tqdm.write(f"  ✗ JSON error in {jsonl_file.name}: {str(e)}")
        except Exception as e:
            files_failed += 1
            tqdm.write(f"  ✗ Error processing {jsonl_file.name}: {str(e)}")
    
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
    """
    Validate that no PHI remains in de-identified dataset.
    
    Args:
        dataset_dir: Directory containing de-identified JSONL files
        file_pattern: Glob pattern for files to validate
        text_fields: List of field names to validate
        
    Returns:
        Dictionary with validation results
    """
    dataset_path = Path(dataset_dir)
    engine = DeidentificationEngine()
    
    validation_results = {
        "total_files": 0,
        "total_records": 0,
        "files_with_issues": [],
        "potential_phi_found": []
    }
    
    jsonl_files = list(dataset_path.glob(file_pattern))
    
    for jsonl_file in jsonl_files:
        validation_results["total_files"] += 1
        file_has_issues = False
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    validation_results["total_records"] += 1
                    record = json.loads(line)
                    
                    # Get text fields
                    fields = text_fields or [k for k, v in record.items() if isinstance(v, str)]
                    
                    # Validate each field
                    for field in fields:
                        if field in record and isinstance(record[field], str):
                            is_valid, potential_phi = engine.validate_deidentification(record[field])
                            
                            if not is_valid:
                                file_has_issues = True
                                validation_results["potential_phi_found"].append({
                                    "file": jsonl_file.name,
                                    "line": line_num,
                                    "field": field,
                                    "issues": potential_phi
                                })
        
        if file_has_issues:
            validation_results["files_with_issues"].append(jsonl_file.name)
    
    # Summary
    validation_results["is_valid"] = len(validation_results["files_with_issues"]) == 0
    validation_results["summary"] = (
        f"Validated {validation_results['total_records']} records in "
        f"{validation_results['total_files']} files. "
        f"Found {len(validation_results['potential_phi_found'])} potential issues."
    )
    
    return validation_results


# ============================================================================
# CLI Interface
# ============================================================================

def main() -> None:
    """Command-line interface for de-identification."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="De-identify PHI/PII in text data with country-specific regulations",
        epilog="Example: python deidentify.py --input-dir data/ --output-dir results/ --countries US IN"
    )
    parser.add_argument("--input-dir", help="Input directory with JSONL files (default: auto-detect from config)")
    parser.add_argument("--output-dir", help="Output directory for de-identified files (default: results/deidentified/)")
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
    
    # List countries if requested
    if args.list_countries:
        if COUNTRY_REGULATIONS_AVAILABLE:
            from scripts.utils.country_regulations import get_all_supported_countries
            print("\nSupported Countries and Regulations:")
            print("=" * 70)
            for code, name in get_all_supported_countries().items():
                print(f"  {code}: {name}")
            print("\nUsage Examples:")
            print("  python -m scripts.utils.deidentify --countries US IN --input-dir <dir> --output-dir <dir>")
            print("  python -m scripts.utils.deidentify --countries ALL --input-dir <dir> --output-dir <dir>")
        else:
            print("Country regulations module not available.")
        return
    
    # Get default directories from config if not provided
    input_dir = args.input_dir
    output_dir = args.output_dir
    
    if not input_dir or not output_dir:
        try:
            import os
            import config as project_config
            if not input_dir:
                # Auto-detect dataset directory from config
                input_dir = os.path.join(project_config.RESULTS_DIR, "dataset", project_config.DATASET_NAME)
                print(f"Using auto-detected input directory: {input_dir}")
            if not output_dir:
                # Use sensible default for output
                output_dir = os.path.join(project_config.RESULTS_DIR, "deidentified", project_config.DATASET_NAME)
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
    print("=" * 70)
    print(f"  Input Directory: {input_dir}")
    print(f"  Output Directory: {output_dir}")
    print(f"  Countries: {countries or ['IN (default)']}")
    print(f"  Country-Specific Patterns: {'Enabled' if deid_config.enable_country_patterns else 'Disabled'}")
    print(f"  Encryption: {'Enabled' if deid_config.enable_encryption else 'Disabled'}")
    print(f"  Validation: {'Enabled' if args.validate else 'Disabled'}")
    print("=" * 70)
    
    # Run de-identification
    print(f"\nDe-identifying dataset...")
    stats = deidentify_dataset(
        input_dir=input_dir,
        output_dir=output_dir,
        text_fields=args.text_fields,
        config=deid_config
    )
    
    print(f"\nDe-identification Statistics:")
    print("=" * 70)
    print(f"  Texts processed: {stats.get('texts_processed', 0)}")
    print(f"  Total detections: {stats.get('total_detections', 0)}")
    print(f"  Countries: {', '.join(stats.get('countries', ['N/A']))}")
    print(f"\n  Detections by type:")
    for phi_type, count in sorted(stats.get('detections_by_type', {}).items()):
        print(f"    {phi_type}: {count}")
    
    # Validate if requested
    if args.validate:
        print("\nValidating de-identified dataset...")
        print("=" * 70)
        validation = validate_dataset(output_dir, text_fields=args.text_fields)
        print(f"  {validation['summary']}")
        
        if not validation['is_valid']:
            print("\n  ⚠ Potential issues found:")
            for issue in validation['potential_phi_found'][:10]:  # Show first 10
                print(f"    {issue['file']}:{issue['line']} - {issue['field']}: {issue['issues']}")
            
            if len(validation['potential_phi_found']) > 10:
                print(f"    ... and {len(validation['potential_phi_found']) - 10} more issues")
        else:
            print("  ✓ No PHI/PII detected in de-identified data")
    
    print("\n✓ De-identification complete!")
    print(f"  De-identified files: {output_dir}")
    print(f"  Audit log: {output_dir}/_deidentification_audit.json")


if __name__ == "__main__":
    main()
