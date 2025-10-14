#!/usr/bin/env python3
"""
Country-Specific Data Privacy Regulations Module
=================================================

Country-specific configurations for patient data de-identification
according to different privacy regulations (HIPAA, GDPR, DPDPA, etc.).

Supports: US, IN, ID, BR, PH, ZA, EU, GB, CA, AU, KE, NG, GH, UG
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

# ============================================================================
# Enums and Base Classes
# ============================================================================

class DataFieldType(Enum):
    """Data field type categorization."""
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
    """Privacy sensitivity levels."""
    PUBLIC = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


@dataclass
class DataField:
    """Data field definition with privacy characteristics."""
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
        """Compile regex pattern if provided."""
        if self.pattern and isinstance(self.pattern, str):
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
        else:
            self.compiled_pattern = None
    
    def validate(self, value: str) -> bool:
        """Validate value against field's pattern."""
        if not self.compiled_pattern:
            return True
        return bool(self.compiled_pattern.match(value))


@dataclass
class CountryRegulation:
    """Country data privacy regulation configuration."""
    country_code: str
    country_name: str
    regulation_name: str
    regulation_acronym: str
    common_fields: List[DataField]
    specific_fields: List[DataField]
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    
    def get_all_fields(self) -> List[DataField]:
        """Get all data fields (common + specific)."""
        return self.common_fields + self.specific_fields
    
    def get_high_privacy_fields(self) -> List[DataField]:
        """Get fields with HIGH or CRITICAL privacy level."""
        return [f for f in self.get_all_fields() 
                if f.privacy_level in (PrivacyLevel.HIGH, PrivacyLevel.CRITICAL)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
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
    """
    Get common data fields applicable to all countries.
    
    These are universal fields that apply across all privacy regulations.
    
    Returns:
        List of common DataField objects
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
    """United States - HIPAA regulation."""
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
    """India - Digital Personal Data Protection Act."""
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
    """Indonesia - Personal Data Protection Law."""
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
    """Brazil - LGPD regulation."""
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
    """Philippines - Data Privacy Act."""
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
    """South Africa - POPIA regulation."""
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
    """European Union - GDPR regulation."""
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
    """United Kingdom - UK GDPR regulation."""
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
    """Canada - PIPEDA and provincial regulations."""
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
    """Australia - Privacy Act regulation."""
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
    """Kenya - Data Protection Act."""
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
    """Nigeria - NDPA regulation."""
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
    """Ghana - Data Protection Act."""
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
    """Uganda - Data Protection and Privacy Act."""
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
    """
    Manages country-specific regulations and data fields.
    
    Supports:
    - Loading regulations for one or more countries
    - Merging fields from multiple countries
    - Generating combined detection patterns
    - Exporting configurations
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
        """
        Initialize regulation manager.
        
        Args:
            countries: List of country codes or 'ALL' for all countries.
                      If None, defaults to IN (India).
        """
        self.logger = logging.getLogger(__name__)
        
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
            self.logger.info(f"Loaded regulation for {code}: {self.regulations[code].regulation_acronym}")
    
    @classmethod
    def get_supported_countries(cls) -> List[str]:
        """Get list of all supported country codes."""
        return list(cls._REGISTRY.keys())
    
    @classmethod
    def get_country_info(cls, country_code: str) -> Dict[str, str]:
        """
        Get information about a country's regulation.
        
        Args:
            country_code: ISO country code
            
        Returns:
            Dictionary with country information
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
        """
        Get all data fields from all loaded countries.
        
        Args:
            include_common: Whether to include common fields
            
        Returns:
            Combined list of all unique data fields
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
        """
        Get country-specific fields.
        
        Args:
            country_code: Specific country code or None for all
            
        Returns:
            List of country-specific fields
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
        """Get all fields with HIGH or CRITICAL privacy level."""
        all_fields = self.get_all_data_fields()
        return [f for f in all_fields 
                if f.privacy_level in (PrivacyLevel.HIGH, PrivacyLevel.CRITICAL)]
    
    def get_detection_patterns(self) -> Dict[str, re.Pattern]:
        """
        Get all regex patterns for detecting country-specific identifiers.
        
        Returns:
            Dictionary mapping field name to compiled regex pattern
        """
        patterns = {}
        
        for field in self.get_all_data_fields():
            if field.compiled_pattern:
                patterns[field.name] = field.compiled_pattern
        
        return patterns
    
    def export_configuration(self, output_path: Union[str, Path]):
        """
        Export current configuration to JSON file.
        
        Args:
            output_path: Path to output file
        """
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
        
        self.logger.info(f"Exported configuration to {output_path}")
    
    def get_requirements_summary(self) -> Dict[str, List[str]]:
        """
        Get summary of all regulatory requirements.
        
        Returns:
            Dictionary mapping country code to list of requirements
        """
        return {
            code: reg.requirements
            for code, reg in self.regulations.items()
        }
    
    def __str__(self) -> str:
        """String representation."""
        countries = ", ".join([f"{code} ({self.regulations[code].regulation_acronym})" 
                              for code in self.country_codes])
        return f"CountryRegulationManager(countries=[{countries}])"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"CountryRegulationManager(country_codes={self.country_codes})"


# ============================================================================
# Utility Functions
# ============================================================================

def get_regulation_for_country(country_code: str) -> CountryRegulation:
    """
    Get regulation configuration for a specific country.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code
        
    Returns:
        CountryRegulation object
        
    Raises:
        ValueError: If country code is not supported
    """
    manager = CountryRegulationManager(countries=[country_code])
    return manager.regulations[country_code.upper()]


def get_all_supported_countries() -> Dict[str, str]:
    """
    Get all supported countries with their regulation names.
    
    Returns:
        Dictionary mapping country code to regulation acronym
    """
    result = {}
    for code in CountryRegulationManager.get_supported_countries():
        info = CountryRegulationManager.get_country_info(code)
        result[code] = f"{info['name']} - {info['acronym']}"
    return result


def merge_regulations(country_codes: List[str]) -> Dict[str, Any]:
    """
    Merge regulations from multiple countries.
    
    Args:
        country_codes: List of country codes to merge
        
    Returns:
        Dictionary with merged configuration
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
    """Command-line interface for testing regulations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Country-specific data privacy regulations")
    parser.add_argument("-c", "--countries", nargs="+", default=["US"],
                       help="Country codes (e.g., US IN) or ALL")
    parser.add_argument("--list", action="store_true", help="List all supported countries")
    parser.add_argument("--export", help="Export configuration to JSON file")
    parser.add_argument("--show-fields", action="store_true", help="Show all data fields")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
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
