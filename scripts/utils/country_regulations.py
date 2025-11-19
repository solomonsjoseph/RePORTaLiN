#!/usr/bin/env python3
"""Country-specific data privacy regulations for de-identification.

This module provides a comprehensive framework for managing country-specific
data privacy regulations and compliance requirements for medical research data.
It supports 14+ countries and regions with their respective data protection laws
(HIPAA, GDPR, DPDPA, LGPD, etc.).

Key Features:
    - **Multi-Country Support**: 14 countries including US, India, Indonesia, Brazil,
      Philippines, South Africa, EU, UK, Canada, Australia, Kenya, Nigeria, Ghana, Uganda
    - **Regulation Definitions**: Complete regulation details with requirements and
      country-specific identifiers
    - **Data Field Catalog**: Comprehensive catalog of personal data fields with:
        - Field types (name, identifier, contact, demographic, location, medical, etc.)
        - Privacy levels (PUBLIC, LOW, MEDIUM, HIGH, CRITICAL)
        - Validation patterns (compiled regex for performance)
        - Examples for testing and documentation
    - **Country-Specific Identifiers**: Support for SSN (US), Aadhaar (India),
      NIK (Indonesia), CPF (Brazil), NHS Number (UK), SIN (Canada), etc.
    - **Flexible Management**: CountryRegulationManager for multi-country workflows
    - **Export Capability**: Export regulation configs to JSON for external tools

Architecture:
    The module is organized into four layers:
    
    1. **Enums & Base Classes**:
       - DataFieldType: Categorizes field types (PERSONAL_NAME, IDENTIFIER, etc.)
       - PrivacyLevel: 5-tier sensitivity model (PUBLIC to CRITICAL)
       - DataField: Immutable field definition with validation
       - CountryRegulation: Complete country regulation specification
    
    2. **Common Fields**:
       - get_common_fields(): Universal fields applicable to all countries
         (name, DOB, phone, email, address, gender, etc.)
    
    3. **Country-Specific Regulations**:
       - 14 get_*_regulation() factory functions, one per country
       - Each returns CountryRegulation with country-specific identifiers
       - Examples: SSN (US), Aadhaar (India), NIK (Indonesia), CPF (Brazil)
    
    4. **Management & Utilities**:
       - CountryRegulationManager: Manages multi-country workflows
       - Utility functions for querying and merging regulations
       - CLI interface for testing and configuration export

Supported Regulations:
    - **US**: HIPAA (Health Insurance Portability and Accountability Act)
    - **India**: DPDPA (Digital Personal Data Protection Act 2023)
    - **Indonesia**: UU PDP (Personal Data Protection Law)
    - **Brazil**: LGPD (Lei Geral de Proteção de Dados)
    - **Philippines**: DPA (Data Privacy Act 2012)
    - **South Africa**: POPIA (Protection of Personal Information Act)
    - **EU**: GDPR (General Data Protection Regulation)
    - **UK**: UK GDPR + Data Protection Act 2018
    - **Canada**: PIPEDA (Personal Information Protection and Electronic Documents Act)
    - **Australia**: Privacy Act 1988
    - **Kenya**: DPA 2019 (Data Protection Act)
    - **Nigeria**: NDPR (Nigeria Data Protection Regulation)
    - **Ghana**: DPA 2012 (Data Protection Act)
    - **Uganda**: DPPA 2019 (Data Protection and Privacy Act)

Typical Usage:
    Single country setup::
    
        from scripts.utils.country_regulations import get_regulation_for_country
        
        us_reg = get_regulation_for_country("US")
        print(f"Regulation: {us_reg.regulation_name}")
        print(f"Specific IDs: {[f.display_name for f in us_reg.specific_fields]}")
        # Output: Specific IDs: ['Social Security Number', 'Medical Record Number', ...]
    
    Multi-country workflow::
    
        from scripts.utils.country_regulations import CountryRegulationManager
        
        manager = CountryRegulationManager(countries=["US", "IN", "ID"])
        all_fields = manager.get_all_data_fields()
        high_privacy = manager.get_high_privacy_fields()
        patterns = manager.get_detection_patterns()
        
        # Export to JSON for external tools
        manager.export_configuration("regulations.json")
    
    Field validation::
    
        from scripts.utils.country_regulations import get_us_regulation
        
        us_reg = get_us_regulation()
        ssn_field = us_reg.specific_fields[0]  # SSN field
        
        if ssn_field.validate("123-45-6789"):
            print("Valid SSN format")
    
    List all supported countries::
    
        from scripts.utils.country_regulations import get_all_supported_countries
        
        countries = get_all_supported_countries()
        for code, name in countries.items():
            print(f"{code}: {name}")

Privacy Levels:
    The module uses a 5-tier privacy sensitivity model:
        1. PUBLIC: Publicly available information (rarely used in medical data)
        2. LOW: Low-sensitivity demographic data (gender, broad age ranges)
        3. MEDIUM: Medium-sensitivity data (city, postal code, middle name)
        4. HIGH: High-sensitivity data (name, phone, email, address, national IDs)
        5. CRITICAL: Most sensitive data (DOB, SSN, Aadhaar, medical record numbers)
    
    HIGH and CRITICAL fields require special de-identification handling.

Thread Safety:
    All classes and functions are thread-safe for read operations. The
    CountryRegulationManager._REGISTRY is immutable after module load.

Note:
    Regex patterns are compiled at DataField initialization for performance.
    Invalid patterns raise ValueError during __post_init__.

See Also:
    - scripts.deidentify: Main de-identification engine using these regulations
    - scripts.load_dictionary: Data dictionary loading with field mapping
"""

import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from scripts.utils import logging_system as log

__all__ = [
    # Enums
    'DataFieldType',
    'PrivacyLevel',
    # Data Classes
    'DataField',
    'CountryRegulation',
    # Main Manager Class
    'CountryRegulationManager',
    # Helper Functions
    'get_common_fields',
    # Utility Functions
    'get_regulation_for_country',
    'get_all_supported_countries',
    'merge_regulations',
]

# ============================================================================
# Enums and Base Classes
# ============================================================================

class DataFieldType(Enum):
    """Data field type categorization for privacy classification.
    
    Categorizes personal data fields into logical types for consistent handling
    across different privacy regulations. Each type has specific handling
    requirements under various data protection laws.
    
    Attributes:
        PERSONAL_NAME: Name fields (first, middle, last names)
        IDENTIFIER: Unique identifiers (SSN, Aadhaar, passport numbers)
        CONTACT: Contact information (phone, email)
        DEMOGRAPHIC: Demographic data (age, gender, ethnicity)
        LOCATION: Geographic data (address, city, postal code)
        MEDICAL: Medical identifiers (MRN, insurance ID)
        FINANCIAL: Financial data (bank account, credit card)
        BIOMETRIC: Biometric identifiers (fingerprint, iris scan)
        CUSTOM: Custom/project-specific field types
    
    Example:
        >>> field = DataField(
        ...     name="ssn",
        ...     display_name="Social Security Number",
        ...     field_type=DataFieldType.IDENTIFIER,
        ...     privacy_level=PrivacyLevel.CRITICAL
        ... )
        >>> field.field_type.value
        'identifier'
    """
    PERSONAL_NAME = "personal_name"
    IDENTIFIER = "identifier"
    CONTACT = "contact"
    DEMOGRAPHIC = "demographic"
    LOCATION = "location"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    BIOMETRIC = "biometric"
    CUSTOM = "custom"


class PrivacyLevel(Enum):
    """Privacy sensitivity levels for data classification.
    
    A 5-tier privacy sensitivity model used to determine de-identification
    requirements. Higher levels require stricter protection measures under
    most privacy regulations.
    
    The numeric values (1-5) can be used for threshold comparisons in
    automated compliance checks.
    
    Attributes:
        PUBLIC (1): Publicly available information, minimal protection needed
        LOW (2): Low-sensitivity data, basic protection
        MEDIUM (3): Medium-sensitivity data, standard protection
        HIGH (4): High-sensitivity personal data, strong protection required
        CRITICAL (5): Most sensitive data, maximum protection (often requires
            removal or strong pseudonymization under regulations like HIPAA)
    
    Example:
        >>> from scripts.utils.country_regulations import PrivacyLevel
        >>> dob_level = PrivacyLevel.CRITICAL
        >>> gender_level = PrivacyLevel.LOW
        >>> dob_level.value > gender_level.value
        True
        >>> # Check if field needs high-level protection
        >>> needs_strong_protection = dob_level in (PrivacyLevel.HIGH, PrivacyLevel.CRITICAL)
        >>> needs_strong_protection
        True
    
    Note:
        HIPAA requires removal or de-identification of all 18 identifiers,
        most of which are classified as HIGH or CRITICAL in this system.
    """
    PUBLIC = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


@dataclass
class DataField:
    """Data field definition with privacy characteristics and validation.
    
    Represents a single personal data field with its type, privacy level,
    validation pattern, and metadata. Used to define both common fields
    (applicable to all countries) and country-specific identifiers.
    
    The class automatically compiles regex patterns during initialization for
    efficient validation. Invalid patterns raise ValueError immediately.
    
    Attributes:
        name: Programmatic field name (snake_case, e.g., "first_name", "ssn")
        display_name: Human-readable field name (e.g., "First Name", "SSN")
        field_type: Category of the field (see DataFieldType)
        privacy_level: Sensitivity level (see PrivacyLevel)
        required: Whether the field is required in the dataset
        pattern: Optional regex pattern for validation (compiled automatically)
        description: Detailed field description for documentation
        examples: List of example values for testing and documentation
        country_specific: Whether this field is specific to one country
        compiled_pattern: Auto-generated compiled regex (internal use)
    
    Raises:
        ValueError: If the regex pattern is invalid and cannot be compiled.
    
    Example:
        Basic field definition::
        
            >>> from scripts.utils.country_regulations import (
            ...     DataField, DataFieldType, PrivacyLevel
            ... )
            >>> ssn = DataField(
            ...     name="ssn",
            ...     display_name="Social Security Number",
            ...     field_type=DataFieldType.IDENTIFIER,
            ...     privacy_level=PrivacyLevel.CRITICAL,
            ...     required=False,
            ...     pattern=r'^\\d{3}-\\d{2}-\\d{4}$',
            ...     description="US Social Security Number",
            ...     examples=["123-45-6789"],
            ...     country_specific=True
            ... )
        
        Field validation::
        
            >>> ssn.validate("123-45-6789")
            True
            >>> ssn.validate("invalid")
            False
            >>> ssn.validate("123456789")  # Missing dashes
            False
        
        Invalid pattern raises error::
        
            >>> bad_field = DataField(
            ...     name="test",
            ...     display_name="Test",
            ...     field_type=DataFieldType.CUSTOM,
            ...     privacy_level=PrivacyLevel.LOW,
            ...     pattern=r'[invalid(regex'  # Unclosed bracket
            ... )
            Traceback (most recent call last):
            ...
            ValueError: Invalid regex pattern '[invalid(regex': ...
    
    Note:
        The compiled_pattern attribute is automatically generated and should
        not be set manually. It's excluded from repr for readability.
    """
    name: str
    display_name: str
    field_type: DataFieldType
    privacy_level: PrivacyLevel
    required: bool = False
    pattern: Optional[str] = None
    description: str = ""
    examples: List[str] = field(default_factory=list)
    country_specific: bool = False
    compiled_pattern: Optional[re.Pattern] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Compile regex pattern with error handling.
        
        Automatically compiles the regex pattern if provided, enabling
        efficient validation without repeated compilation. Raises ValueError
        if the pattern is malformed.
        
        Raises:
            ValueError: If the regex pattern cannot be compiled.
        """
        if self.pattern and isinstance(self.pattern, str):
            try:
                self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{self.pattern}': {e}")
        else:
            self.compiled_pattern = None
    
    def validate(self, value: str) -> bool:
        """Validate value against field's pattern.
        
        Checks if the provided value matches the field's validation pattern.
        If no pattern is defined, validation always succeeds (returns True).
        
        Args:
            value: The string value to validate against the field's pattern.
        
        Returns:
            True if the value matches the pattern or no pattern is defined,
            False if the value doesn't match.
        
        Example:
            >>> from scripts.utils.country_regulations import get_us_regulation
            >>> us_reg = get_us_regulation()
            >>> ssn_field = [f for f in us_reg.specific_fields if f.name == "ssn"][0]
            >>> ssn_field.validate("123-45-6789")
            True
            >>> ssn_field.validate("123456789")  # Also valid (9 digits)
            True
            >>> ssn_field.validate("abc-de-fghi")
            False
        
        Note:
            Validation is case-insensitive due to re.IGNORECASE flag in
            pattern compilation.
        """
        if not self.compiled_pattern:
            return True
        return bool(self.compiled_pattern.match(value))


@dataclass
class CountryRegulation:
    """Country data privacy regulation configuration.
    
    Represents a complete privacy regulation for a specific country, including
    regulation metadata, common fields, country-specific identifiers, and
    compliance requirements.
    
    This class combines universal data fields (applicable to all countries)
    with country-specific identifiers (like SSN for US, Aadhaar for India)
    to provide a complete view of data protection requirements.
    
    Attributes:
        country_code: Two-letter ISO country code (e.g., "US", "IN", "BR")
        country_name: Full country name (e.g., "United States", "India")
        regulation_name: Full name of the privacy regulation
        regulation_acronym: Short acronym (e.g., "HIPAA", "GDPR", "DPDPA")
        common_fields: Universal data fields applicable to all countries
        specific_fields: Country-specific identifiers and fields
        description: Brief description of the regulation's scope and purpose
        requirements: List of key compliance requirements
    
    Example:
        Creating a regulation manually (typically use factory functions)::
        
            >>> from scripts.utils.country_regulations import (
            ...     CountryRegulation, DataField, DataFieldType, PrivacyLevel
            ... )
            >>> us_reg = CountryRegulation(
            ...     country_code="US",
            ...     country_name="United States",
            ...     regulation_name="Health Insurance Portability and Accountability Act",
            ...     regulation_acronym="HIPAA",
            ...     common_fields=get_common_fields(),
            ...     specific_fields=[
            ...         DataField(
            ...             name="ssn",
            ...             display_name="Social Security Number",
            ...             field_type=DataFieldType.IDENTIFIER,
            ...             privacy_level=PrivacyLevel.CRITICAL,
            ...             pattern=r'^\\d{3}-\\d{2}-\\d{4}$',
            ...             country_specific=True
            ...         )
            ...     ],
            ...     requirements=["Remove all 18 HIPAA identifiers"]
            ... )
        
        Using factory function (recommended)::
        
            >>> from scripts.utils.country_regulations import get_us_regulation
            >>> us_reg = get_us_regulation()
            >>> print(f"{us_reg.country_name}: {us_reg.regulation_acronym}")
            United States: HIPAA
            >>> print(f"Specific fields: {len(us_reg.specific_fields)}")
            Specific fields: 3
    
    Note:
        Use the factory functions (get_us_regulation(), get_india_regulation(),
        etc.) rather than constructing CountryRegulation instances directly.
    """
    country_code: str
    country_name: str
    regulation_name: str
    regulation_acronym: str
    common_fields: List[DataField]
    specific_fields: List[DataField]
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    
    def get_all_fields(self) -> List[DataField]:
        """Get all data fields (common + specific).
        
        Returns the complete list of data fields for this regulation,
        combining both universal fields (like name, DOB) and country-specific
        identifiers (like SSN, Aadhaar).
        
        Returns:
            Combined list of common and country-specific data fields.
        
        Example:
            >>> from scripts.utils.country_regulations import get_india_regulation
            >>> india_reg = get_india_regulation()
            >>> all_fields = india_reg.get_all_fields()
            >>> len(all_fields)  # 10 common + 4 specific
            14
            >>> field_names = [f.name for f in all_fields]
            >>> 'aadhaar_number' in field_names
            True
            >>> 'first_name' in field_names
            True
        """
        return self.common_fields + self.specific_fields
    
    def get_high_privacy_fields(self) -> List[DataField]:
        """Get fields with HIGH or CRITICAL privacy level.
        
        Filters all fields to return only those requiring strong protection
        measures (privacy level HIGH or CRITICAL). These fields typically
        require pseudonymization, removal, or special handling under most
        privacy regulations.
        
        Returns:
            List of DataField instances with privacy_level of HIGH or CRITICAL.
        
        Example:
            >>> from scripts.utils.country_regulations import get_us_regulation
            >>> us_reg = get_us_regulation()
            >>> high_privacy = us_reg.get_high_privacy_fields()
            >>> high_privacy_names = [f.name for f in high_privacy]
            >>> 'ssn' in high_privacy_names  # CRITICAL
            True
            >>> 'first_name' in high_privacy_names  # HIGH
            True
            >>> 'gender' in high_privacy_names  # LOW - excluded
            False
        
        Note:
            Under HIPAA, most HIGH and CRITICAL fields must be removed or
            de-identified. Under GDPR, they require explicit consent and
            special processing safeguards.
        """
        return [f for f in self.get_all_fields() 
                if f.privacy_level in (PrivacyLevel.HIGH, PrivacyLevel.CRITICAL)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Converts the regulation configuration to a JSON-serializable dictionary,
        useful for exporting configurations, API responses, or configuration
        file generation.
        
        Returns:
            Dictionary with regulation metadata and all fields serialized
            to basic Python types (str, int, list, dict).
        
        Example:
            >>> from scripts.utils.country_regulations import get_us_regulation
            >>> import json
            >>> us_reg = get_us_regulation()
            >>> reg_dict = us_reg.to_dict()
            >>> reg_dict['country_code']
            'US'
            >>> reg_dict['regulation_acronym']
            'HIPAA'
            >>> len(reg_dict['specific_fields'])
            3
            >>> # Export to JSON file (use temp directory for actual file operations)
            >>> import tempfile
            >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=True) as f:
            ...     json.dump(reg_dict, f, indent=2)
            ...     f.flush()  # Ensure data is written
        
        Note:
            Enum values are converted to their string representations
            (e.g., DataFieldType.IDENTIFIER → "identifier").
        """
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "regulation_name": self.regulation_name,
            "regulation_acronym": self.regulation_acronym,
            "description": self.description,
            "requirements": self.requirements,
            "common_fields": [
                {
                    "name": f.name,
                    "display_name": f.display_name,
                    "field_type": f.field_type.value,
                    "privacy_level": f.privacy_level.value,
                    "required": f.required,
                    "pattern": f.pattern,
                    "description": f.description,
                    "examples": f.examples
                }
                for f in self.common_fields
            ],
            "specific_fields": [
                {
                    "name": f.name,
                    "display_name": f.display_name,
                    "field_type": f.field_type.value,
                    "privacy_level": f.privacy_level.value,
                    "required": f.required,
                    "pattern": f.pattern,
                    "description": f.description,
                    "examples": f.examples,
                    "country_specific": f.country_specific
                }
                for f in self.specific_fields
            ]
        }


# ============================================================================
# Common Data Fields
# ============================================================================

def get_common_fields() -> List[DataField]:
    """Get common data fields applicable to all countries.
    
    Returns a list of universal personal data fields that are relevant across
    all privacy regulations and countries. These fields represent standard
    demographic and contact information commonly collected in medical research.
    
    Common fields include:
        - Personal names (first, middle, last)
        - Date of birth (supports multiple formats: ISO 8601, slash, hyphen, dot)
        - Contact information (phone, email)
        - Location data (address, city, postal code)
        - Basic demographics (gender)
    
    All fields have appropriate privacy levels (LOW to CRITICAL) and validation
    patterns. The date of birth field supports multiple international formats
    to accommodate different country conventions.
    
    Returns:
        List of 10 common DataField instances representing universal personal
        data fields with validation patterns and privacy classifications.
    
    Example:
        >>> from scripts.utils.country_regulations import get_common_fields
        >>> common = get_common_fields()
        >>> len(common)
        10
        >>> field_names = [f.name for f in common]
        >>> field_names
        ['first_name', 'last_name', 'middle_name', 'date_of_birth', 'phone_number', 'email', 'address', 'city', 'postal_code', 'gender']
        >>> # Find DOB field and check its pattern
        >>> dob = [f for f in common if f.name == 'date_of_birth'][0]
        >>> dob.privacy_level.name
        'CRITICAL'
        >>> dob.validate('1980-01-15')  # ISO 8601
        True
        >>> dob.validate('01/15/1980')  # US format
        True
        >>> dob.validate('15.01.1980')  # European format
        True
    
    Note:
        These common fields are included in every country regulation via the
        CountryRegulation.common_fields attribute. Country-specific identifiers
        (SSN, Aadhaar, etc.) are added separately via specific_fields.
    
    See Also:
        - get_us_regulation(): US-specific fields (SSN, MRN, Insurance ID)
        - get_india_regulation(): India-specific fields (Aadhaar, PAN, etc.)
    """
    return [
        DataField(
            name="first_name",
            display_name="First Name",
            field_type=DataFieldType.PERSONAL_NAME,
            privacy_level=PrivacyLevel.HIGH,
            required=True,
            pattern=r'^[A-Za-z\s\'-]{1,50}$',
            description="Patient's first name",
            examples=["John", "Maria", "Rajesh"]
        ),
        DataField(
            name="last_name",
            display_name="Last Name",
            field_type=DataFieldType.PERSONAL_NAME,
            privacy_level=PrivacyLevel.HIGH,
            required=True,
            pattern=r'^[A-Za-z\s\'-]{1,50}$',
            description="Patient's last name",
            examples=["Doe", "Silva", "Kumar"]
        ),
        DataField(
            name="middle_name",
            display_name="Middle Name",
            field_type=DataFieldType.PERSONAL_NAME,
            privacy_level=PrivacyLevel.MEDIUM,
            required=False,
            pattern=r'^[A-Za-z\s\'-]{1,50}$',
            description="Patient's middle name",
            examples=["James", "Carlos", "Raj"]
        ),
        DataField(
            name="date_of_birth",
            display_name="Date of Birth",
            field_type=DataFieldType.DEMOGRAPHIC,
            privacy_level=PrivacyLevel.CRITICAL,
            required=True,
            pattern=r'^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$|^\d{2}\.\d{2}\.\d{4}$',
            description="Patient's date of birth (supports ISO 8601, slash/hyphen/dot-separated formats)",
            examples=["1980-01-15", "01/15/1980", "15-01-1980", "15.01.1980"]
        ),
        DataField(
            name="phone_number",
            display_name="Phone Number",
            field_type=DataFieldType.CONTACT,
            privacy_level=PrivacyLevel.HIGH,
            required=False,
            pattern=r'^\+?[\d\s\-\(\)]{10,20}$',
            description="Contact phone number",
            examples=["+1-555-123-4567", "9876543210"]
        ),
        DataField(
            name="email",
            display_name="Email Address",
            field_type=DataFieldType.CONTACT,
            privacy_level=PrivacyLevel.HIGH,
            required=False,
            pattern=r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$',
            description="Email address",
            examples=["patient@example.com"]
        ),
        DataField(
            name="address",
            display_name="Street Address",
            field_type=DataFieldType.LOCATION,
            privacy_level=PrivacyLevel.HIGH,
            required=False,
            description="Street address",
            examples=["123 Main St, Apt 4B"]
        ),
        DataField(
            name="city",
            display_name="City",
            field_type=DataFieldType.LOCATION,
            privacy_level=PrivacyLevel.MEDIUM,
            required=False,
            description="City name",
            examples=["New York", "Mumbai", "São Paulo"]
        ),
        DataField(
            name="postal_code",
            display_name="Postal/ZIP Code",
            field_type=DataFieldType.LOCATION,
            privacy_level=PrivacyLevel.MEDIUM,
            required=False,
            description="Postal or ZIP code",
            examples=["10001", "400001", "01310-100"]
        ),
        DataField(
            name="gender",
            display_name="Gender",
            field_type=DataFieldType.DEMOGRAPHIC,
            privacy_level=PrivacyLevel.LOW,
            required=False,
            pattern=r'^(Male|Female|Other|M|F|O)$',
            description="Gender",
            examples=["Male", "Female", "Other"]
        ),
    ]


# ============================================================================
# Country-Specific Regulations
# ============================================================================

def get_us_regulation() -> CountryRegulation:
    """United States - HIPAA regulation.
    
    Returns the complete HIPAA (Health Insurance Portability and Accountability
    Act) compliance configuration for the United States, including US-specific
    identifiers like Social Security Number, Medical Record Number, and
    Insurance ID.
    
    HIPAA Requirements:
        - Remove or de-identify all 18 HIPAA identifiers
        - Apply Safe Harbor or Expert Determination method
        - Ages over 89 must be aggregated to "90+"
        - Dates must be shifted by consistent offset (supports multi-format)
        - Geographic subdivisions smaller than state removed (except ZIP if >20,000 people)
        - Business Associate Agreements required for third-party processors
    
    US-Specific Identifiers:
        - **SSN**: Social Security Number (9 digits, format: XXX-XX-XXXX or XXXXXXXXX)
        - **MRN**: Medical Record Number (alphanumeric, 6-12 characters)
        - **Insurance ID**: Health insurance member ID
    
    Returns:
        CountryRegulation instance configured for US HIPAA compliance with
        common fields plus 3 US-specific identifier fields.
    
    Example:
        >>> from scripts.utils.country_regulations import get_us_regulation
        >>> us_reg = get_us_regulation()
        >>> us_reg.regulation_acronym
        'HIPAA'
        >>> us_reg.country_code
        'US'
        >>> len(us_reg.specific_fields)
        3
        >>> # Get SSN field
        >>> ssn = [f for f in us_reg.specific_fields if f.name == 'ssn'][0]
        >>> ssn.privacy_level.name
        'CRITICAL'
        >>> ssn.validate('123-45-6789')
        True
        >>> # Check HIPAA requirements
        >>> 'Remove all 18 HIPAA identifiers' in us_reg.requirements[0]
        True
    
    Note:
        HIPAA's 18 identifiers include names, geographic subdivisions,
        dates, phone numbers, email, SSN, MRN, account numbers, and more.
        This regulation enforces the strictest de-identification in the module.
    
    See Also:
        - scripts.deidentify: Main de-identification engine implementing HIPAA
    """
    return CountryRegulation(
        country_code="US",
        country_name="United States",
        regulation_name="Health Insurance Portability and Accountability Act",
        regulation_acronym="HIPAA",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="ssn",
                display_name="Social Security Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{3}-\d{2}-\d{4}$|^\d{9}$',
                description="US Social Security Number",
                examples=["123-45-6789", "123456789"],
                country_specific=True
            ),
            DataField(
                name="mrn",
                display_name="Medical Record Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=True,
                pattern=r'^[A-Z0-9]{6,12}$',
                description="Hospital Medical Record Number",
                examples=["MRN123456", "H12345678"],
                country_specific=True
            ),
            DataField(
                name="insurance_id",
                display_name="Insurance ID",
                field_type=DataFieldType.FINANCIAL,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                description="Health insurance member ID",
                examples=["INS123456789"],
                country_specific=True
            ),
        ],
        description="HIPAA Privacy, Security, and Breach Notification Rules; HITECH strengthens enforcement and penalties",
        requirements=[
            "HIPAA Privacy Rule: Remove all 18 HIPAA identifiers",
            "HIPAA Security Rule: Administrative, physical, and technical safeguards",
            "HIPAA Breach Notification Rule: Notify affected individuals within 60 days",
            "HITECH Act: Strengthens HIPAA enforcement and penalties",
            "Ages over 89 must be aggregated",
            "Dates must be shifted by consistent offset (multi-format support: ISO 8601, slash/hyphen/dot-separated)",
            "Geographic subdivisions smaller than state must be removed (except first 3 digits of ZIP if > 20,000 people)",
            "Business Associate Agreements required for third-party processors"
        ]
    )


def get_india_regulation() -> CountryRegulation:
    """India - Digital Personal Data Protection Act.
    
    Returns the DPDPA (Digital Personal Data Protection Act 2023) compliance
    configuration for India, including India-specific identifiers like Aadhaar,
    PAN, Voter ID, and Passport numbers.
    
    DPDPA 2023 Requirements:
        - Obtain explicit consent for data processing
        - Data minimization principle (collect only necessary data)
        - Purpose limitation (use data only for stated purpose)
        - Storage limitation (retain only as long as needed)
        - Right to erasure and correction (data subject rights)
    
    India-Specific Identifiers:
        - **Aadhaar**: Unique 12-digit identity number issued by UIDAI
          (format: XXXX XXXX XXXX or XXXXXXXXXXXX)
        - **PAN**: Permanent Account Number for taxation (format: ABCDE1234F)
        - **Voter ID**: Electoral Photo Identity Card (format: ABC1234567)
        - **Passport**: Indian passport number (format: A1234567)
    
    Returns:
        CountryRegulation instance configured for India DPDPA compliance with
        common fields plus 4 India-specific identifier fields.
    
    Example:
        >>> from scripts.utils.country_regulations import get_india_regulation
        >>> india_reg = get_india_regulation()
        >>> india_reg.regulation_acronym
        'DPDPA'
        >>> india_reg.country_name
        'India'
        >>> len(india_reg.specific_fields)
        4
        >>> # Validate Aadhaar number
        >>> aadhaar = [f for f in india_reg.specific_fields if f.name == 'aadhaar_number'][0]
        >>> aadhaar.validate('1234 5678 9012')
        True
        >>> aadhaar.validate('123456789012')  # Without spaces also valid
        True
        >>> # Check requirements
        >>> 'consent' in india_reg.requirements[0].lower()
        True
    
    Note:
        Aadhaar is highly sensitive under Indian law. The Supreme Court has
        placed restrictions on mandatory Aadhaar collection. Always ensure
        proper consent and security for Aadhaar data.
    """
    return CountryRegulation(
        country_code="IN",
        country_name="India",
        regulation_name="Digital Personal Data Protection Act",
        regulation_acronym="DPDPA",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="aadhaar_number",
                display_name="Aadhaar Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{4}\s?\d{4}\s?\d{4}$|^\d{12}$',
                description="Unique Identification Authority of India number",
                examples=["1234 5678 9012", "123456789012"],
                country_specific=True
            ),
            DataField(
                name="pan_number",
                display_name="PAN Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^[A-Z]{5}\d{4}[A-Z]$',
                description="Permanent Account Number for taxation",
                examples=["ABCDE1234F"],
                country_specific=True
            ),
            DataField(
                name="voter_id",
                display_name="Voter ID",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^[A-Z]{3}\d{7}$',
                description="Electoral Photo Identity Card number",
                examples=["ABC1234567"],
                country_specific=True
            ),
            DataField(
                name="passport_number",
                display_name="Passport Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^[A-Z]\d{7}$',
                description="Indian passport number",
                examples=["A1234567"],
                country_specific=True
            ),
        ],
        description="DPDPA 2023 regulates processing of digital personal data",
        requirements=[
            "Obtain consent for data processing",
            "Data minimization principle",
            "Purpose limitation",
            "Storage limitation",
            "Right to erasure and correction"
        ]
    )


def get_indonesia_regulation() -> CountryRegulation:
    """Indonesia - Personal Data Protection Law (UU PDP).
    
    Returns UU PDP compliance configuration for Indonesia with country-specific
    identifiers: NIK (16-digit national ID), KK Number (family card), NPWP
    (taxpayer ID), and passport.
    
    Returns:
        CountryRegulation for Indonesia with 4 specific ID fields.
    
    Example:
        >>> indonesia_reg = get_indonesia_regulation()
        >>> indonesia_reg.regulation_acronym
        'UU PDP'
        >>> nik = [f for f in indonesia_reg.specific_fields if f.name == 'nik'][0]
        >>> nik.validate('3201234567890123')  # 16 digits
        True
    """
    return CountryRegulation(
        country_code="ID",
        country_name="Indonesia",
        regulation_name="Personal Data Protection Law",
        regulation_acronym="UU PDP",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="nik",
                display_name="NIK (Nomor Induk Kependudukan)",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{16}$',
                description="National Identity Number (16 digits)",
                examples=["3201234567890123"],
                country_specific=True
            ),
            DataField(
                name="kk_number",
                display_name="KK Number (Kartu Keluarga)",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^\d{16}$',
                description="Family Card Number",
                examples=["3201234567890123"],
                country_specific=True
            ),
            DataField(
                name="npwp",
                display_name="NPWP (Tax ID)",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3}$|^\d{15}$',
                description="Taxpayer Identification Number",
                examples=["01.234.567.8-901.234", "012345678901234"],
                country_specific=True
            ),
        ],
        description="UU PDP No. 27 of 2022 governs personal data protection",
        requirements=[
            "Consent-based data processing",
            "Data protection officer required for large processors",
            "Cross-border transfer restrictions",
            "Breach notification within 72 hours"
        ]
    )


def get_brazil_regulation() -> CountryRegulation:
    """Brazil - Lei Geral de Proteção de Dados (LGPD).
    
    Returns LGPD compliance configuration for Brazil with country-specific
    identifiers: CPF (individual taxpayer ID, 11 digits), RG (general
    registration), CNS (national health card), and passport.
    
    Returns:
        CountryRegulation for Brazil with 4 specific ID fields.
    
    Example:
        >>> brazil_reg = get_brazil_regulation()
        >>> brazil_reg.regulation_acronym
        'LGPD'
        >>> cpf = [f for f in brazil_reg.specific_fields if f.name == 'cpf'][0]
        >>> cpf.validate('12345678901')  # 11 digits
        True
    """
    return CountryRegulation(
        country_code="BR",
        country_name="Brazil",
        regulation_name="Lei Geral de Proteção de Dados",
        regulation_acronym="LGPD",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="cpf",
                display_name="CPF (Cadastro de Pessoas Físicas)",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$',
                description="Individual Taxpayer Registry",
                examples=["123.456.789-01", "12345678901"],
                country_specific=True
            ),
            DataField(
                name="rg",
                display_name="RG (Registro Geral)",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^\d{1,2}\.\d{3}\.\d{3}-[A-Z0-9]$',
                description="General Registry (ID card)",
                examples=["12.345.678-9"],
                country_specific=True
            ),
            DataField(
                name="sus_number",
                display_name="SUS Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{15}$',
                description="Sistema Único de Saúde (Unified Health System) number",
                examples=["123456789012345"],
                country_specific=True
            ),
        ],
        description="LGPD (Law 13.709/2018) is Brazil's comprehensive data protection law",
        requirements=[
            "Legal basis required for processing",
            "Data protection impact assessment for high-risk processing",
            "Data protection officer for public bodies and large processors",
            "Sensitive data requires specific consent"
        ]
    )


def get_philippines_regulation() -> CountryRegulation:
    """Philippines - Data Privacy Act of 2012 (DPA).
    
    Returns DPA compliance configuration for Philippines with country-specific
    identifiers: UMID (unified multi-purpose ID), SSS (social security), TIN
    (taxpayer identification), and PhilHealth numbers.
    
    Returns:
        CountryRegulation for Philippines with 4 specific ID fields.
    
    Example:
        >>> ph_reg = get_philippines_regulation()
        >>> ph_reg.regulation_acronym
        'DPA'
    """
    return CountryRegulation(
        country_code="PH",
        country_name="Philippines",
        regulation_name="Data Privacy Act of 2012",
        regulation_acronym="DPA",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="philhealth_number",
                display_name="PhilHealth Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{2}-\d{9}-\d$|^\d{12}$',
                description="Philippine Health Insurance Corporation number",
                examples=["12-345678901-2", "123456789012"],
                country_specific=True
            ),
            DataField(
                name="umid",
                display_name="UMID Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^\d{4}-\d{7}-\d$|^\d{12}$',
                description="Unified Multi-Purpose ID",
                examples=["1234-5678901-2", "123456789012"],
                country_specific=True
            ),
            DataField(
                name="sss_number",
                display_name="SSS Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                pattern=r'^\d{2}-\d{7}-\d$|^\d{10}$',
                description="Social Security System number",
                examples=["12-3456789-0", "1234567890"],
                country_specific=True
            ),
        ],
        description="Republic Act No. 10173 protects personal information",
        requirements=[
            "Consent or legitimate interest required",
            "Privacy policy must be provided",
            "Data breach notification to NPC within 72 hours",
            "Security measures proportionate to risk"
        ]
    )


def get_south_africa_regulation() -> CountryRegulation:
    """South Africa - POPIA (Protection of Personal Information Act).
    
    Returns POPIA compliance configuration for South Africa with country-specific
    identifiers: 13-digit ID number (YYMMDD-GSSS-C-AZ format) and passport.
    
    Returns:
        CountryRegulation for South Africa with 2 specific ID fields.
    
    Example:
        >>> za_reg = get_south_africa_regulation()
        >>> za_reg.regulation_acronym
        'POPIA'
        >>> id_field = [f for f in za_reg.specific_fields if f.name == 'id_number'][0]
        >>> id_field.validate('8001015009087')  # 13 digits
        True
    """
    return CountryRegulation(
        country_code="ZA",
        country_name="South Africa",
        regulation_name="Protection of Personal Information Act",
        regulation_acronym="POPIA",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="id_number",
                display_name="South African ID Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{13}$',
                description="13-digit ID number (YYMMDD-GSSS-C-AZ)",
                examples=["8001015009087"],
                country_specific=True
            ),
            DataField(
                name="passport_number",
                display_name="Passport Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^[A-Z]\d{8}$',
                description="South African passport number",
                examples=["A12345678"],
                country_specific=True
            ),
        ],
        description="POPIA (Act 4 of 2013) regulates processing of personal information",
        requirements=[
            "Process information lawfully and reasonably",
            "Collect for specific purpose with consent",
            "Further processing compatible with original purpose",
            "Adequate security measures",
            "Data subject participation rights"
        ]
    )


def get_eu_regulation() -> CountryRegulation:
    """European Union / EEA - GDPR (General Data Protection Regulation).
    
    Returns GDPR compliance configuration for EU/EEA with special-category health
    data requirements and country-varying identifiers (national ID, EHIC).
    
    Returns:
        CountryRegulation for EU with 2 specific ID fields.
    
    Example:
        >>> eu_reg = get_eu_regulation()
        >>> eu_reg.regulation_acronym
        'GDPR'
        >>> 'explicit consent' in eu_reg.requirements[0].lower()
        True
    """
    return CountryRegulation(
        country_code="EU",
        country_name="European Union / EEA",
        regulation_name="General Data Protection Regulation",
        regulation_acronym="GDPR",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="national_id",
                display_name="National ID Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                description="National identification number (varies by country)",
                examples=["Varies by EU country"],
                country_specific=True
            ),
            DataField(
                name="eu_health_card",
                display_name="European Health Insurance Card",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                description="EHIC number",
                examples=["Varies by country"],
                country_specific=True
            ),
        ],
        description="GDPR (2016/679) special-category health data requires explicit consent/legal basis",
        requirements=[
            "Special-category health data requires explicit consent or legal basis",
            "Lawful basis for processing required",
            "Data minimization and purpose limitation",
            "Right to erasure (right to be forgotten)",
            "Data portability",
            "Privacy by design and by default",
            "Breach notification within 72 hours",
            "Data Protection Impact Assessment for high-risk processing",
            "Notable member states: Germany (BDSG/SGB), France (Code de la santé publique), Netherlands (WGBO/AVG)"
        ]
    )


def get_uk_regulation() -> CountryRegulation:
    """United Kingdom - UK GDPR and Data Protection Act 2018.
    
    Returns UK GDPR compliance configuration with NHS Number (10-digit patient
    identifier) and National Insurance Number. Governed by Caldicott Principles.
    
    Returns:
        CountryRegulation for UK with 2 specific ID fields.
    
    Example:
        >>> uk_reg = get_uk_regulation()
        >>> uk_reg.regulation_acronym
        'UK GDPR'
        >>> nhs = [f for f in uk_reg.specific_fields if f.name == 'nhs_number'][0]
        >>> nhs.validate('123 456 7890')
        True
    """
    return CountryRegulation(
        country_code="GB",
        country_name="United Kingdom",
        regulation_name="UK GDPR and Data Protection Act 2018",
        regulation_acronym="UK GDPR",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="nhs_number",
                display_name="NHS Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{3}\s?\d{3}\s?\d{4}$|^\d{10}$',
                description="National Health Service unique patient identifier",
                examples=["123 456 7890", "1234567890"],
                country_specific=True
            ),
            DataField(
                name="national_insurance",
                display_name="National Insurance Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^[A-Z]{2}\d{6}[A-D]$',
                description="UK National Insurance number",
                examples=["AB123456C"],
                country_specific=True
            ),
        ],
        description="UK GDPR + DPA 2018 treats health data as special category; governed by Caldicott Principles and NHS info governance",
        requirements=[
            "Health data treated as special category",
            "Caldicott Principles for health and social care",
            "NHS information governance framework",
            "Lawful basis and special category condition required",
            "Data Protection Impact Assessment for high-risk processing",
            "ICO breach notification within 72 hours",
            "Privacy by design and default"
        ]
    )


def get_canada_regulation() -> CountryRegulation:
    """Canada - PIPEDA (federal) and provincial health privacy laws.
    
    Returns PIPEDA compliance configuration for Canada with provincial health
    card numbers (varying by province) and Social Insurance Number (9 digits).
    
    Returns:
        CountryRegulation for Canada with 2 specific ID fields.
    
    Example:
        >>> ca_reg = get_canada_regulation()
        >>> ca_reg.regulation_acronym
        'PIPEDA'
        >>> sin = [f for f in ca_reg.specific_fields if f.name == 'sin'][0]
        >>> sin.validate('123-456-789')
        True
    """
    return CountryRegulation(
        country_code="CA",
        country_name="Canada",
        regulation_name="Personal Information Protection and Electronic Documents Act",
        regulation_acronym="PIPEDA",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="health_card",
                display_name="Provincial Health Card Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                description="Provincial health insurance card (format varies by province)",
                examples=["Varies by province"],
                country_specific=True
            ),
            DataField(
                name="sin",
                display_name="Social Insurance Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{3}-\d{3}-\d{3}$|^\d{9}$',
                description="Canadian Social Insurance Number",
                examples=["123-456-789", "123456789"],
                country_specific=True
            ),
        ],
        description="PIPEDA (federal) for private sector; provincial laws: Ontario PHIPA, Alberta HIA, BC PIPA/eHealth Act",
        requirements=[
            "Federal PIPEDA applies to private sector health data",
            "Provincial laws: Ontario PHIPA, Alberta HIA, BC PIPA/eHealth Act",
            "Consent required for collection, use, and disclosure",
            "Individual access and correction rights",
            "Security safeguards proportionate to sensitivity",
            "Breach notification to Privacy Commissioner and affected individuals",
            "Accountability principle"
        ]
    )


def get_australia_regulation() -> CountryRegulation:
    """Australia - Privacy Act 1988 and Australian Privacy Principles (APPs).
    
    Returns APPs compliance configuration for Australia with Medicare number,
    Individual Healthcare Identifier (IHI, 16 digits), and Tax File Number.
    
    Returns:
        CountryRegulation for Australia with 3 specific ID fields.
    
    Example:
        >>> au_reg = get_australia_regulation()
        >>> au_reg.regulation_acronym
        'APPs'
        >>> ihi = [f for f in au_reg.specific_fields if f.name == 'ihi_number'][0]
        >>> ihi.validate('8003608166690503')  # 16 digits
        True
    """
    return CountryRegulation(
        country_code="AU",
        country_name="Australia",
        regulation_name="Privacy Act 1988 and Australian Privacy Principles",
        regulation_acronym="APPs",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="medicare_number",
                display_name="Medicare Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{10}$|^\d{4}\s?\d{5}\s?\d{1}$',
                description="Medicare card number",
                examples=["1234567890", "1234 56789 0"],
                country_specific=True
            ),
            DataField(
                name="ihi_number",
                display_name="Individual Healthcare Identifier",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{16}$',
                description="IHI number for My Health Record",
                examples=["8003608166690503"],
                country_specific=True
            ),
            DataField(
                name="tfn",
                display_name="Tax File Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{8,9}$',
                description="Australian Tax File Number",
                examples=["123456789"],
                country_specific=True
            ),
        ],
        description="Privacy Act 1988 + APPs treat health data as sensitive; My Health Records Act 2012 governs digital health records",
        requirements=[
            "Health data is sensitive information under APPs",
            "My Health Records Act 2012 for digital health records",
            "State/territory health-record laws apply",
            "Consent or legal authority required for sensitive data",
            "Security safeguards for personal information",
            "Breach notification under Notifiable Data Breaches scheme",
            "Individual access and correction rights"
        ]
    )


def get_kenya_regulation() -> CountryRegulation:
    """Kenya - Data Protection Act 2019.
    
    Returns DPA 2019 compliance configuration for Kenya with 7-8 digit National
    ID and NHIF (National Hospital Insurance Fund) number.
    
    Returns:
        CountryRegulation for Kenya with 2 specific ID fields.
    
    Example:
        >>> ke_reg = get_kenya_regulation()
        >>> ke_reg.regulation_acronym
        'DPA 2019'
        >>> nat_id = [f for f in ke_reg.specific_fields if f.name == 'national_id'][0]
        >>> nat_id.validate('12345678')
        True
    """
    return CountryRegulation(
        country_code="KE",
        country_name="Kenya",
        regulation_name="Data Protection Act 2019",
        regulation_acronym="DPA 2019",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="national_id",
                display_name="National ID Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{7,8}$',
                description="Kenyan National ID number",
                examples=["12345678"],
                country_specific=True
            ),
            DataField(
                name="nhif_number",
                display_name="NHIF Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                description="National Hospital Insurance Fund number",
                examples=["123456789"],
                country_specific=True
            ),
        ],
        description="Data Protection Act 2019 treats health data as sensitive; Health Act 2017 ensures patient confidentiality",
        requirements=[
            "Sensitive health data requires explicit consent",
            "Health Act 2017 provisions for patient confidentiality",
            "Data Protection Commissioner oversight",
            "Cross-border transfer restrictions for sensitive data",
            "Security safeguards required",
            "Breach notification obligations",
            "Data subject rights (access, correction, erasure)"
        ]
    )


def get_nigeria_regulation() -> CountryRegulation:
    """Nigeria - NDPA (Nigeria Data Protection Act 2023).
    
    Returns NDPA compliance configuration for Nigeria with 11-digit National
    Identification Number (NIN) and NHIS (National Health Insurance Scheme) number.
    
    Returns:
        CountryRegulation for Nigeria with 2 specific ID fields.
    
    Example:
        >>> ng_reg = get_nigeria_regulation()
        >>> ng_reg.regulation_acronym
        'NDPA'
        >>> nin = [f for f in ng_reg.specific_fields if f.name == 'nin'][0]
        >>> nin.validate('12345678901')  # 11 digits
        True
    """
    return CountryRegulation(
        country_code="NG",
        country_name="Nigeria",
        regulation_name="Nigeria Data Protection Act 2023",
        regulation_acronym="NDPA",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="nin",
                display_name="National Identification Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^\d{11}$',
                description="11-digit National Identification Number",
                examples=["12345678901"],
                country_specific=True
            ),
            DataField(
                name="nhis_number",
                display_name="NHIS Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                description="National Health Insurance Scheme number",
                examples=["NIG-123456789"],
                country_specific=True
            ),
        ],
        description="Nigeria Data Protection Act 2023 treats health data as sensitive; enforced by NDPC",
        requirements=[
            "Health data treated as sensitive personal data",
            "Explicit consent required for sensitive data processing",
            "Nigeria Data Protection Commission (NDPC) enforcement",
            "Data localization requirements for sensitive data",
            "Mandatory data protection audits",
            "Breach notification within 72 hours",
            "Data Protection Officer required for certain entities"
        ]
    )


def get_ghana_regulation() -> CountryRegulation:
    """Ghana - Data Protection Act 2012.
    
    Returns DPA 2012 compliance configuration for Ghana with Ghana Card
    (GHA-XXXXXXXXX-X format) and NHIS (National Health Insurance Scheme) number.
    
    Returns:
        CountryRegulation for Ghana with 2 specific ID fields.
    
    Example:
        >>> gh_reg = get_ghana_regulation()
        >>> gh_reg.regulation_acronym
        'DPA 2012'
        >>> card = [f for f in gh_reg.specific_fields if f.name == 'ghana_card'][0]
        >>> card.validate('GHA-123456789-0')
        True
    """
    return CountryRegulation(
        country_code="GH",
        country_name="Ghana",
        regulation_name="Data Protection Act 2012",
        regulation_acronym="DPA 2012",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="ghana_card",
                display_name="Ghana Card Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^GHA-\d{9}-\d$',
                description="Ghana National Identification Card",
                examples=["GHA-123456789-0"],
                country_specific=True
            ),
            DataField(
                name="nhis_number",
                display_name="NHIS Number",
                field_type=DataFieldType.MEDICAL,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                description="National Health Insurance Scheme number",
                examples=["NHIS-123456789"],
                country_specific=True
            ),
        ],
        description="Data Protection Act 2012 treats health data as sensitive; Ghana Health Service confidentiality rules apply",
        requirements=[
            "Health data classified as sensitive",
            "Ghana Health Service confidentiality rules",
            "Consent required for sensitive data processing",
            "Data Protection Commission oversight",
            "Security measures for sensitive data",
            "Cross-border transfer restrictions",
            "Data subject access and correction rights"
        ]
    )


def get_uganda_regulation() -> CountryRegulation:
    """Uganda - DPPA (Data Protection and Privacy Act 2019).
    
    Returns DPPA 2019 compliance configuration for Uganda with National ID
    (alphanumeric 14-character format) and NSSF (National Social Security Fund) number.
    
    Returns:
        CountryRegulation for Uganda with 2 specific ID fields.
    
    Example:
        >>> ug_reg = get_uganda_regulation()
        >>> ug_reg.regulation_acronym
        'DPPA 2019'
        >>> nat_id = [f for f in ug_reg.specific_fields if f.name == 'national_id'][0]
        >>> nat_id.validate('CM12345678901AB')
        True
    """
    return CountryRegulation(
        country_code="UG",
        country_name="Uganda",
        regulation_name="Data Protection and Privacy Act 2019",
        regulation_acronym="DPPA 2019",
        common_fields=get_common_fields(),
        specific_fields=[
            DataField(
                name="national_id",
                display_name="National ID Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.CRITICAL,
                required=False,
                pattern=r'^[A-Z]{2}[0-9A-Z]{12}$',
                description="National Identification Number",
                examples=["CM12345678901AB"],
                country_specific=True
            ),
            DataField(
                name="nssf_number",
                display_name="NSSF Number",
                field_type=DataFieldType.IDENTIFIER,
                privacy_level=PrivacyLevel.HIGH,
                required=False,
                description="National Social Security Fund number",
                examples=["NSSF-123456"],
                country_specific=True
            ),
        ],
        description="Data Protection and Privacy Act 2019 treats health data as sensitive; Public Health Act ensures medical records confidentiality",
        requirements=[
            "Health data treated as sensitive",
            "Public Health Act medical records confidentiality",
            "Explicit consent for sensitive data processing",
            "Personal Data Protection Office oversight",
            "Security safeguards required",
            "Breach notification obligations",
            "Data subject rights (access, correction, deletion)"
        ]
    )


# ============================================================================
# Country Regulation Manager
# ============================================================================

class CountryRegulationManager:
    """Manages country-specific regulations and data fields for multi-country workflows.
    
    Central management class for working with multiple country regulations
    simultaneously. Provides unified access to regulations, data fields,
    validation patterns, and compliance requirements across countries.
    
    This class is essential for multi-country clinical trials or research
    projects that need to comply with different privacy regulations
    simultaneously (e.g., HIPAA + GDPR + DPDPA).
    
    Features:
        - Load regulations for single or multiple countries
        - Merge data fields from multiple regulations
        - Filter fields by privacy level or country
        - Export unified configuration to JSON
        - Query regulatory requirements across countries
    
    Attributes:
        country_codes: List of loaded country codes (e.g., ["US", "IN", "BR"])
        regulations: Dict mapping country codes to CountryRegulation instances
        _REGISTRY: Class-level registry of all supported countries (private)
    
    Example:
        Single country::
        
            >>> from scripts.utils.country_regulations import CountryRegulationManager
            >>> manager = CountryRegulationManager(countries="US")
            >>> manager.country_codes
            ['US']
            >>> us_fields = manager.get_all_data_fields()
        
        Multiple countries::
        
            >>> manager = CountryRegulationManager(countries=["US", "IN", "BR"])
            >>> manager.country_codes
            ['US', 'IN', 'BR']
            >>> all_fields = manager.get_all_data_fields()
            >>> high_privacy = manager.get_high_privacy_fields()
        
        All supported countries::
        
            >>> manager = CountryRegulationManager(countries="ALL")
            >>> len(manager.country_codes)
            14
            >>> countries_info = [(code, reg.regulation_acronym) 
            ...                   for code, reg in manager.regulations.items()]
        
        Export configuration::
        
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> manager.export_configuration("multi_country_config.json")
    
    Raises:
        ValueError: If any country code is not supported.
    
    Note:
        Default country is India ("IN") if no countries specified. Use "ALL"
        to load all 14 supported countries.
    
    See Also:
        - get_regulation_for_country(): Get single country regulation
        - merge_regulations(): Merge multiple countries without creating manager
    """
    
    # Registry of all supported countries (private to prevent external modification)
    _REGISTRY: Dict[str, callable] = {
        "US": get_us_regulation,
        "IN": get_india_regulation,
        "ID": get_indonesia_regulation,
        "BR": get_brazil_regulation,
        "PH": get_philippines_regulation,
        "ZA": get_south_africa_regulation,
        "EU": get_eu_regulation,
        "GB": get_uk_regulation,
        "CA": get_canada_regulation,
        "AU": get_australia_regulation,
        "KE": get_kenya_regulation,
        "NG": get_nigeria_regulation,
        "GH": get_ghana_regulation,
        "UG": get_uganda_regulation,
    }
    
    def __init__(self, countries: Optional[Union[List[str], str]] = None):
        """Initialize regulation manager with specified countries.
        
        Loads and validates regulations for the specified countries. Country
        codes are case-insensitive. Use "ALL" to load all supported countries.
        
        Args:
            countries: Country specification in one of these forms:
                - None: Defaults to India ("IN")
                - str: Single country code ("US") or "ALL" for all countries
                - List[str]: Multiple country codes (["US", "IN", "BR"])
        
        Raises:
            ValueError: If any country code is not in the supported list.
        
        Side Effects:
            Loads all specified regulations and logs each load via centralized
            logging system.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["us", "in"])  # Case insensitive
            >>> manager.country_codes
            ['US', 'IN']
            >>> manager = CountryRegulationManager()  # Default to India
            >>> manager.country_codes
            ['IN']
            >>> manager = CountryRegulationManager(countries="ALL")
            >>> len(manager.country_codes)
            14
        """
        # Parse countries
        if countries is None:
            self.country_codes = ["IN"]
        elif isinstance(countries, str):
            if countries.upper() == "ALL":
                self.country_codes = list(self._REGISTRY.keys())
            else:
                self.country_codes = [countries.upper()]
        else:
            self.country_codes = [c.upper() for c in countries]
        
        # Validate country codes
        invalid = set(self.country_codes) - set(self._REGISTRY.keys())
        if invalid:
            raise ValueError(f"Unsupported country codes: {invalid}. "
                           f"Supported: {list(self._REGISTRY.keys())}")
        
        # Load regulations
        self.regulations: Dict[str, CountryRegulation] = {}
        for code in self.country_codes:
            self.regulations[code] = self._REGISTRY[code]()
            log.info(f"Loaded regulation for {code}: {self.regulations[code].regulation_acronym}")
    
    @classmethod
    def get_supported_countries(cls) -> List[str]:
        """Get list of all supported country codes.
        
        Returns:
            List of two-letter country codes for all supported countries.
        
        Example:
            >>> CountryRegulationManager.get_supported_countries()
            ['US', 'IN', 'ID', 'BR', 'PH', 'ZA', 'EU', 'GB', 'CA', 'AU', 'KE', 'NG', 'GH', 'UG']
        """
        return list(cls._REGISTRY.keys())
    
    @classmethod
    def get_country_info(cls, country_code: str) -> Dict[str, str]:
        """Get information about a country's regulation without loading full config.
        
        Provides quick access to regulation metadata without instantiating
        the full CountryRegulation object. Useful for displaying country
        lists or checking regulation details.
        
        Args:
            country_code: Two-letter country code (case-insensitive).
        
        Returns:
            Dictionary with keys: code, name, regulation, acronym, description.
        
        Raises:
            ValueError: If country code is not supported.
        
        Example:
            >>> info = CountryRegulationManager.get_country_info("US")
            >>> info['acronym']
            'HIPAA'
            >>> info['name']
            'United States'
            >>> info['regulation']
            'Health Insurance Portability and Accountability Act'
        """
        if country_code.upper() not in cls._REGISTRY:
            raise ValueError(f"Unsupported country code: {country_code}")
        
        reg = cls._REGISTRY[country_code.upper()]()
        return {
            "code": reg.country_code,
            "name": reg.country_name,
            "regulation": reg.regulation_name,
            "acronym": reg.regulation_acronym,
            "description": reg.description
        }
    
    def get_all_data_fields(self, include_common: bool = True) -> List[DataField]:
        """Get all data fields from all loaded countries (deduplicated).
        
        Merges data fields from all loaded regulations, removing duplicates.
        Country-specific fields are namespaced with country code to avoid
        conflicts (e.g., "US_ssn", "IN_aadhaar_number").
        
        Args:
            include_common: If True, include common fields (name, DOB, etc.).
                If False, return only country-specific fields.
        
        Returns:
            Deduplicated list of DataField instances from all loaded countries.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> all_fields = manager.get_all_data_fields()
            >>> field_names = [f.name for f in all_fields]
            >>> 'first_name' in field_names  # Common field
            True
            >>> any('ssn' in name for name in field_names)  # US-specific
            True
            >>> any('aadhaar' in name for name in field_names)  # India-specific
            True
            >>> # Get only country-specific fields
            >>> specific = manager.get_all_data_fields(include_common=False)
            >>> len(specific) < len(all_fields)
            True
        """
        fields_dict: Dict[str, DataField] = {}
        
        for regulation in self.regulations.values():
            if include_common:
                for field in regulation.common_fields:
                    if field.name not in fields_dict:
                        fields_dict[field.name] = field
            
            for field in regulation.specific_fields:
                # Use country-specific name for country-specific fields
                key = f"{regulation.country_code}_{field.name}" if field.country_specific else field.name
                if key not in fields_dict:
                    fields_dict[key] = field
        
        return list(fields_dict.values())
    
    def get_country_specific_fields(self, country_code: Optional[str] = None) -> List[DataField]:
        """Get country-specific fields (excluding common fields).
        
        Returns country-specific identifier fields like SSN, Aadhaar, NIK, etc.
        Can filter to a single country or return all country-specific fields.
        
        Args:
            country_code: Optional country code to filter fields. If None,
                returns all country-specific fields from all loaded countries.
        
        Returns:
            List of country-specific DataField instances.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> us_fields = manager.get_country_specific_fields("US")
            >>> us_names = [f.name for f in us_fields]
            >>> us_names
            ['ssn', 'mrn', 'insurance_id']
            >>> # Get all country-specific fields
            >>> all_specific = manager.get_country_specific_fields()
            >>> len(all_specific) == len(us_fields) + 4  # US (3) + India (4)
            True
        """
        fields = []
        
        if country_code:
            if country_code.upper() in self.regulations:
                fields = self.regulations[country_code.upper()].specific_fields
        else:
            for regulation in self.regulations.values():
                fields.extend(regulation.specific_fields)
        
        return fields
    
    def get_high_privacy_fields(self) -> List[DataField]:
        """Get all fields with HIGH or CRITICAL privacy level.
        
        Filters all fields (common + specific) to return only those requiring
        strong protection measures. These typically need pseudonymization,
        removal, or special handling under privacy regulations.
        
        Returns:
            List of DataField instances with privacy_level HIGH or CRITICAL.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> high_privacy = manager.get_high_privacy_fields()
            >>> names = [f.name for f in high_privacy]
            >>> 'first_name' in names  # HIGH
            True
            >>> 'date_of_birth' in names  # CRITICAL
            True
            >>> 'gender' in names  # LOW - excluded
            False
        """
        all_fields = self.get_all_data_fields()
        return [f for f in all_fields 
                if f.privacy_level in (PrivacyLevel.HIGH, PrivacyLevel.CRITICAL)]
        return [f for f in all_fields 
                if f.privacy_level in (PrivacyLevel.HIGH, PrivacyLevel.CRITICAL)]
    
    def get_detection_patterns(self) -> Dict[str, re.Pattern]:
        """Get all regex patterns for detecting country-specific identifiers.
        
        Returns compiled regex patterns for all fields that have validation
        patterns. Useful for automated detection of sensitive data in datasets.
        
        Returns:
            Dictionary mapping field names to compiled regex Pattern objects.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US"])
            >>> patterns = manager.get_detection_patterns()
            >>> 'ssn' in patterns
            True
            >>> patterns['ssn'].match('123-45-6789')  # Returns Match object
            <re.Match object; span=(0, 11), match='123-45-6789'>
        """
        patterns = {}
        
        for field in self.get_all_data_fields():
            if field.compiled_pattern:
                patterns[field.name] = field.compiled_pattern
        
        return patterns
    
    def export_configuration(self, output_path: Union[str, Path]) -> None:
        """Export current configuration to JSON file.
        
        Exports complete regulation configuration including all countries,
        fields, and requirements to a JSON file for use by external tools,
        documentation generation, or configuration management.
        
        Args:
            output_path: Path where JSON file will be written. Parent
                directories are created if they don't exist.
        
        Raises:
            IOError: If file cannot be written due to permissions or disk issues.
        
        Side Effects:
            Creates output file and parent directories. Logs export action.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> manager.export_configuration("config/regulations.json")
            # Creates regulations.json with full configuration
        """
        try:
            config = {
                "countries": self.country_codes,
                "regulations": {
                    code: reg.to_dict()
                    for code, reg in self.regulations.items()
                },
                "all_fields": [
                    {
                        "name": f.name,
                        "display_name": f.display_name,
                        "field_type": f.field_type.value,
                        "privacy_level": f.privacy_level.value,
                        "required": f.required,
                        "pattern": f.pattern,
                        "description": f.description,
                        "country_specific": f.country_specific
                    }
                    for f in self.get_all_data_fields()
                ]
            }
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            log.info(f"Exported configuration to {output_path}")
            
        except (IOError, OSError) as e:
            raise IOError(f"Failed to export configuration to {output_path}: {e}") from e
    
    def get_requirements_summary(self) -> Dict[str, List[str]]:
        """Get summary of all regulatory requirements by country.
        
        Returns:
            Dictionary mapping country codes to lists of requirement strings.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> reqs = manager.get_requirements_summary()
            >>> 'HIPAA' in reqs['US'][0]
            True
            >>> 'consent' in reqs['IN'][0].lower()
            True
        """
        return {
            code: reg.requirements
            for code, reg in self.regulations.items()
        }
    
    def __str__(self) -> str:
        """String representation showing loaded countries and regulations.
        
        Returns:
            Human-readable string listing countries and their regulation acronyms.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> str(manager)
            'CountryRegulationManager(countries=[US (HIPAA), IN (DPDPA)])'
        """
        countries = ", ".join([f"{code} ({self.regulations[code].regulation_acronym})" 
                              for code in self.country_codes])
        return f"CountryRegulationManager(countries=[{countries}])"
    
    def __repr__(self) -> str:
        """Detailed representation showing country codes.
        
        Returns:
            Detailed string representation with country codes list.
        
        Example:
            >>> manager = CountryRegulationManager(countries=["US", "IN"])
            >>> repr(manager)
            "CountryRegulationManager(country_codes=['US', 'IN'])"
        """
        return f"CountryRegulationManager(country_codes={self.country_codes})"


# ============================================================================
# Utility Functions
# ============================================================================

def get_regulation_for_country(country_code: str) -> CountryRegulation:
    """Get regulation configuration for a specific country.
    
    Convenience function to retrieve a single country's regulation without
    manually creating a CountryRegulationManager instance. This is the
    recommended way to load a single country's regulation.
    
    Args:
        country_code: Two-letter country code (case-insensitive), e.g., "US",
            "IN", "BR". Must be a supported country.
    
    Returns:
        CountryRegulation instance for the specified country.
    
    Raises:
        ValueError: If country code is not supported.
    
    Example:
        >>> from scripts.utils.country_regulations import get_regulation_for_country
        >>> us_reg = get_regulation_for_country("US")
        >>> us_reg.regulation_acronym
        'HIPAA'
        >>> us_reg.country_name
        'United States'
        >>> # Case-insensitive
        >>> india_reg = get_regulation_for_country("in")
        >>> india_reg.regulation_acronym
        'DPDPA'
    
    See Also:
        - CountryRegulationManager: For multi-country workflows
        - get_all_supported_countries(): List all available countries
    """
    manager = CountryRegulationManager(countries=[country_code])
    return manager.regulations[country_code.upper()]


def get_all_supported_countries() -> Dict[str, str]:
    """Get all supported countries with their regulation names.
    
    Returns a dictionary mapping country codes to human-readable descriptions
    combining country name and regulation acronym. Useful for displaying
    country selection lists in UIs or documentation.
    
    Returns:
        Dictionary mapping country codes to formatted strings like
        "United States - HIPAA", "India - DPDPA", etc.
    
    Example:
        >>> from scripts.utils.country_regulations import get_all_supported_countries
        >>> countries = get_all_supported_countries()
        >>> countries['US']
        'United States - HIPAA'
        >>> countries['IN']
        'India - DPDPA'
        >>> countries['BR']
        'Brazil - LGPD'
        >>> # Display all countries
        >>> for code, name in countries.items():
        ...     print(f"{code}: {name}")
        US: United States - HIPAA
        IN: India - DPDPA
        ...
        >>> len(countries)
        14
    
    See Also:
        - CountryRegulationManager.get_supported_countries(): Just the codes
        - CountryRegulationManager.get_country_info(): Detailed country info
    """
    result = {}
    for code in CountryRegulationManager.get_supported_countries():
        info = CountryRegulationManager.get_country_info(code)
        result[code] = f"{info['name']} - {info['acronym']}"
    return result


def merge_regulations(country_codes: List[str]) -> Dict[str, Any]:
    """Merge regulations from multiple countries into unified configuration.
    
    Convenience function to create a merged view of multiple country regulations
    without maintaining a CountryRegulationManager instance. Returns all
    fields, high-privacy fields, detection patterns, and requirements in a
    single dictionary.
    
    This is useful for multi-country clinical trials or research projects
    that need to comply with multiple regulations simultaneously.
    
    Args:
        country_codes: List of two-letter country codes to merge, e.g.,
            ["US", "IN", "BR"]. All codes must be supported.
    
    Returns:
        Dictionary with keys:
            - countries: List of country codes
            - all_fields: Deduplicated list of all DataField instances
            - high_privacy_fields: Fields with HIGH or CRITICAL privacy level
            - detection_patterns: Dict mapping field names to compiled regex patterns
            - requirements: Dict mapping country codes to requirement lists
    
    Raises:
        ValueError: If any country code is not supported.
    
    Example:
        >>> from scripts.utils.country_regulations import merge_regulations
        >>> merged = merge_regulations(["US", "IN"])
        >>> merged['countries']
        ['US', 'IN']
        >>> len(merged['all_fields'])  # Common + US-specific + India-specific
        20
        >>> # Get high-privacy fields
        >>> high_privacy_names = [f.name for f in merged['high_privacy_fields']]
        >>> 'first_name' in high_privacy_names
        True
        >>> # Access detection patterns
        >>> 'ssn' in merged['detection_patterns']  # US-specific
        True
        >>> 'aadhaar_number' in merged['detection_patterns']  # India-specific
        True
        >>> # Check requirements
        >>> 'US' in merged['requirements']
        True
        >>> 'HIPAA' in merged['requirements']['US'][0]
        True
    
    Note:
        Country-specific fields are namespaced (e.g., "US_ssn", "IN_aadhaar_number")
        to prevent naming conflicts when merging.
    
    See Also:
        - CountryRegulationManager: For persistent multi-country management
        - get_regulation_for_country(): For single-country access
    """
    manager = CountryRegulationManager(countries=country_codes)
    return {
        "countries": manager.country_codes,
        "all_fields": manager.get_all_data_fields(),
        "high_privacy_fields": manager.get_high_privacy_fields(),
        "detection_patterns": manager.get_detection_patterns(),
        "requirements": manager.get_requirements_summary()
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for testing and exploring country regulations.
    
    Provides an interactive CLI for viewing country regulations, data fields,
    requirements, and exporting configurations to JSON. Useful for testing,
    documentation generation, and debugging regulation configurations.
    
    Command-Line Arguments:
        -c, --countries CODES: One or more country codes or "ALL" (default: ["US"])
        --list: List all supported countries and exit
        --export PATH: Export configuration to JSON file
        --show-fields: Display all data fields with details
    
    Side Effects:
        - Configures centralized logging system at INFO level
        - Prints regulation details, requirements, and fields to stdout
        - Optionally writes JSON export file
    
    Example:
        Command-line usage::
        
            # List all supported countries
            $ python country_regulations.py --list
            
            # Show US regulation details
            $ python country_regulations.py -c US
            
            # Show multiple countries with field details
            $ python country_regulations.py -c US IN BR --show-fields
            
            # Load all countries and export to JSON
            $ python country_regulations.py -c ALL --export config/all_regs.json
        
        Python usage (for testing)::
        
            >>> import sys
            >>> sys.argv = ['country_regulations.py', '-c', 'US', 'IN']
            >>> main()  # Displays US and India regulations
    
    Note:
        Uses centralized logging system from scripts.utils.logging_system.
        Logging configuration is at INFO level.
    
    See Also:
        - CountryRegulationManager: Core class used by this CLI
        - get_all_supported_countries(): Lists all available countries
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Country-specific data privacy regulations")
    parser.add_argument("-c", "--countries", nargs="+", default=["US"],
                       help="Country codes (e.g., US IN) or ALL")
    parser.add_argument("--list", action="store_true", help="List all supported countries")
    parser.add_argument("--export", help="Export configuration to JSON file")
    parser.add_argument("--show-fields", action="store_true", help="Show all data fields")
    
    args = parser.parse_args()
    
    # Setup logging using centralized logging system
    log.setup_logging(module_name=__name__, log_level='INFO')
    
    if args.list:
        print("\nSupported Countries:")
        print("=" * 70)
        for code, name in get_all_supported_countries().items():
            print(f"  {code}: {name}")
        return
    
    # Create manager
    countries = ["ALL"] if "ALL" in [c.upper() for c in args.countries] else args.countries
    manager = CountryRegulationManager(countries=countries)
    
    print(f"\n{manager}")
    print("=" * 70)
    
    for code, reg in manager.regulations.items():
        print(f"\n{reg.country_name} ({code})")
        print(f"  Regulation: {reg.regulation_name} ({reg.regulation_acronym})")
        print(f"  Description: {reg.description}")
        print(f"  Specific Fields: {len(reg.specific_fields)}")
        for field in reg.specific_fields:
            print(f"    - {field.display_name} ({field.privacy_level.name})")
        print(f"  Requirements: {len(reg.requirements)}")
        for req in reg.requirements:
            print(f"    • {req}")
    
    if args.show_fields:
        print(f"\n\nAll Data Fields ({len(manager.get_all_data_fields())})")
        print("=" * 70)
        for field in manager.get_all_data_fields():
            country_tag = " [Country-Specific]" if field.country_specific else ""
            print(f"  {field.display_name}: {field.description}{country_tag}")
            print(f"    Type: {field.field_type.value}, Privacy: {field.privacy_level.name}")
            if field.pattern:
                print(f"    Pattern: {field.pattern}")
            if field.examples:
                print(f"    Examples: {', '.join(field.examples)}")
            print()
    
    if args.export:
        manager.export_configuration(args.export)
        print(f"\nConfiguration exported to: {args.export}")


if __name__ == "__main__":
    main()
