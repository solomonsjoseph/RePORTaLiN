#!/usr/bin/env python3
"""PHI/PII de-identification with country-specific compliance."""

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
    priority: int = DEFAULT_PATTERN_PRIORITY
    description: str = ""
    
    def __post_init__(self):
        """Validate and compile regex pattern if provided as string."""
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
    """Library of regex patterns for detecting PHI/PII."""
    
    @staticmethod
    def get_default_patterns() -> List[DetectionPattern]:
        """Get default detection patterns for common PHI/PII types."""
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
        """Get country-specific detection patterns."""
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
    """Generates consistent, deterministic pseudonyms for PHI/PII."""
    
    def __init__(self, salt: Optional[str] = None):
        """Initialize pseudonym generator."""
        self.salt = salt or secrets.token_hex(CRYPTO_SALT_LENGTH)
        self._counter: Dict[PHIType, int] = defaultdict(int)
        self._cache: Dict[Tuple[PHIType, str], str] = {}
    
    def generate(self, value: str, phi_type: PHIType, template: str) -> str:
        """Generate a pseudonym for a given value."""
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
        """Get statistics on pseudonym generation."""
        return {phi_type.value: count for phi_type, count in self._counter.items()}


# ============================================================================
# Date Shifting
# ============================================================================

class DateShifter:
    """Consistent date shifting with intelligent multi-format parsing."""
    
    def __init__(self, shift_range_days: int = DEFAULT_DATE_SHIFT_RANGE_DAYS, preserve_intervals: bool = True, seed: Optional[str] = None, country_code: str = DEFAULT_COUNTRY_CODE):
        """Initialize date shifter with country-specific format interpretation."""
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
        """Get consistent shift offset based on seed."""
        if self._shift_offset is None:
            # Generate deterministic offset from seed
            hash_digest = hashlib.sha256(self.seed.encode()).digest()
            offset_int = int.from_bytes(hash_digest[:HASH_ID_BYTES], byteorder='big')
            self._shift_offset = (offset_int % (2 * self.shift_range_days + 1)) - self.shift_range_days
        return self._shift_offset
    
    def shift_date(self, date_str: str, date_format: Optional[str] = None) -> str:
        """Shift a date string by consistent offset with intelligent format detection."""
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
    """Secure storage for PHI to pseudonym mappings."""
    
    def __init__(self, storage_path: Path, encryption_key: Optional[bytes] = None, enable_encryption: bool = True):
        """Initialize mapping store."""
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
        """Save mappings to storage file with atomic write operation."""
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
        """Add a mapping entry with validation."""
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
        """Retrieve pseudonym for original value with validation."""
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
        """Export mappings for audit purposes with atomic write."""
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
    """Main engine for PHI/PII detection and de-identification."""
    
    def __init__(self, config: Optional[DeidentificationConfig] = None, mapping_store: Optional[MappingStore] = None):
        """Initialize de-identification engine with comprehensive error handling."""
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
        """De-identify a single text string with comprehensive error handling."""
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
        """De-identify a dictionary record (e.g., from JSONL)."""
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
        """Get de-identification statistics."""
        return {
            **self.stats,
            "pseudonym_stats": self.pseudonym_generator.get_statistics(),
            "total_mappings": len(self.mapping_store.mappings)
        }
    
    def validate_deidentification(self, text: str, strict: bool = True) -> Tuple[bool, List[str]]:
        """Validate that no PHI remains in de-identified text."""
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
    """Batch de-identification of JSONL dataset files."""
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
    """Validate that no PHI remains in de-identified dataset."""
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
    """Command-line interface for de-identification."""
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
                    # Auto-detect dataset directory from config (v0.3.0 API)
                    clean_dataset_dir = os.path.join(project_config.OUTPUT_DIR, "cleaned_datasets")
                    input_dir = os.path.join(clean_dataset_dir, "cleaned")
                    print(f"Using auto-detected input directory: {input_dir}")
                if not output_dir:
                    # Use sensible default for output (v0.3.0 API)
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
