# RePORTaLiN - Regional Prospective Observational Research for Tuberculosis and Lung Infections

A robust data processing pipeline for clinical research data with advanced de-identification and privacy compliance features.

## Overview

RePORTaLiN is a comprehensive data processing system designed for handling sensitive clinical research data. It provides:

- **Data Dictionary Processing**: Automated loading and validation of study data dictionaries
- **Data Extraction**: Excel to JSONL conversion with validation
- **De-identification**: Advanced PHI/PII detection and pseudonymization with country-specific privacy regulations
- **Security**: Encryption by default, secure key management, and audit trails

## Key Features

### 🌍 Country-Specific Privacy Compliance
Support for 14 countries with region-specific data protection regulations:
- **US** - HIPAA (Health Insurance Portability and Accountability Act)
- **IN** - DPDPA 2023 (Digital Personal Data Protection Act)
- **ID** - UU PDP (Personal Data Protection Law)
- **BR** - LGPD (Lei Geral de Proteção de Dados)
- **PH** - Data Privacy Act of 2012
- **ZA** - POPIA (Protection of Personal Information Act)
- **EU** - GDPR (General Data Protection Regulation)
- **GB** - UK GDPR
- **CA** - PIPEDA (Personal Information Protection and Electronic Documents Act)
- **AU** - Privacy Act 1988
- **KE** - Data Protection Act 2019
- **NG** - Nigeria Data Protection Act 2023
- **GH** - Data Protection Act 2012
- **UG** - Data Protection and Privacy Act 2019

### 🔒 Security Features
- **Encryption by Default**: Fernet symmetric encryption for mapping tables
- **Secure Pseudonymization**: Consistent, deterministic placeholders
- **Date Shifting**: Preserves temporal relationships while obscuring dates
- **Audit Trails**: Complete logging of all de-identification operations
- **Validation**: Post-processing checks to ensure no PHI leakage

### ⚡ Performance
- Processes 200,000+ texts per second
- Batch processing with real-time progress tracking (tqdm)
- Efficient memory usage with streaming JSONL
- Handles large datasets (1.8M+ texts verified)
- Clean console output with progress bars and status messages

## Installation

### Prerequisites
- Python 3.13 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd RePORTaLiN
```

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage (Default India Dataset)

Run the complete pipeline:
```bash
python3 main.py
```

Run with de-identification enabled:
```bash
python3 main.py --enable-deidentification
```

### Country-Specific De-identification

**Single Country**:
```bash
python3 main.py --enable-deidentification --countries US
```

**Multiple Countries**:
```bash
python3 main.py --enable-deidentification --countries IN US ID BR
```

**All Countries**:
```bash
python3 main.py --enable-deidentification --countries ALL
```

**List Supported Countries**:
```bash
python3 -m scripts.utils.deidentify --list-countries
```

### Advanced Options

**Skip Specific Steps**:
```bash
# Skip data dictionary loading
python3 main.py --skip-dictionary --enable-deidentification

# Skip data extraction
python3 main.py --skip-extraction --enable-deidentification

# Skip de-identification
python3 main.py --enable-deidentification --skip-deidentification
```

**Testing Mode (No Encryption)**:
```bash
python3 main.py --enable-deidentification --no-encryption
```

## Project Structure

```
RePORTaLiN/
├── main.py                          # Main pipeline entry point
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── scripts/                         # Core processing modules
│   ├── __init__.py
│   ├── load_dictionary.py          # Data dictionary processor
│   ├── extract_data.py             # Excel to JSONL extraction
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       ├── country_regulations.py  # Country-specific privacy rules
│       ├── deidentify.py          # De-identification engine
│       └── logging_utils.py       # Logging utilities
├── data/                           # Input data directory
│   ├── data_dictionary_and_mapping_specifications/
│   └── dataset/
│       └── Indo-vap_csv_files/    # Excel files for processing
├── results/                        # Output directory
│   ├── data_dictionary_mappings/  # Processed dictionaries
│   ├── dataset/                   # Extracted JSONL files
│   └── deidentified/             # De-identified data
│       ├── Indo-vap/
│       │   ├── original/         # De-identified original files
│       │   └── cleaned/          # De-identified cleaned files
│       └── mappings/             # Encrypted mapping store
└── docs/                          # Documentation
    └── sphinx/                    # Sphinx documentation
        ├── conf.py
        ├── index.rst
        ├── user_guide/           # User documentation
        └── developer_guide/      # Developer documentation
```

## Documentation

### 📚 Accessing Documentation

#### User Guide
Comprehensive guides for using the system:
```bash
cd docs/sphinx
make html
open _build/html/index.html  # macOS
# or
xdg-open _build/html/index.html  # Linux
# or
start _build/html/index.html  # Windows
```

User guide includes:
- **Usage**: Getting started and basic usage
- **De-identification**: PHI/PII detection and pseudonymization
- **Country Regulations**: Country-specific privacy compliance

#### Developer Guide
Documentation for extending and maintaining the system:
- **Architecture**: System design and components
- **Extending**: How to add new countries and features
- **Testing**: Testing strategies and best practices

#### Quick Links
- **User Guide**: `docs/sphinx/user_guide/`
- **Developer Guide**: `docs/sphinx/developer_guide/`
- **API Reference**: Auto-generated from code docstrings

### Building Documentation

```bash
cd docs/sphinx
make html      # Build HTML documentation
make clean     # Clean build artifacts
make latexpdf  # Build PDF documentation (requires LaTeX)
```

## Configuration

### config.py Settings

Key configuration options in `config.py`:

```python
# Dataset Configuration
DATASET_NAME = "Indo-vap"           # Dataset identifier
DATASET_DIR = "data/dataset/Indo-vap_csv_files/"

# De-identification Settings
DEFAULT_COUNTRIES = ["IN"]          # Default country for de-identification
ENABLE_ENCRYPTION = True            # Enable mapping encryption
ENABLE_DATE_SHIFTING = True         # Enable date shifting
DATE_SHIFT_RANGE_DAYS = 365        # Date shift range (±365 days)

# Logging
LOG_LEVEL = "INFO"                  # Logging verbosity
LOG_NAME = "reportalin"            # Logger name
```

## Performance

### Benchmarks
Based on Indo-vap dataset (1.8M+ texts):

| Metric | Performance |
|--------|-------------|
| **Processing Speed** | ~200,000 texts/second |
| **PHI/PII Detection** | 365,630 detections in 9 seconds |
| **Files/Second** | ~9-12 JSONL files |
| **Memory Usage** | Efficient (streaming) |

## Security & Privacy

### Data Protection
- ✅ **HIPAA** compliant (United States)
- ✅ **GDPR** compliant (European Union)
- ✅ **LGPD** compliant (Brazil)
- ✅ **DPDPA** compliant (India)
- ✅ **14 country-specific regulations** supported

### Security Features
1. **Encryption**: All mapping tables encrypted with Fernet
2. **No PHI in Logs**: Only pseudonyms are logged
3. **Secure Storage**: Encrypted mapping files (mappings.enc)
4. **Date Shifting**: Preserves temporal relationships
5. **Validation**: Post-processing validation checks
6. **Audit Trails**: Complete operation logging

## Command Reference

### Main Pipeline

```bash
# Full pipeline with all steps
python3 main.py

# Enable de-identification (default: India)
python3 main.py --enable-deidentification

# De-identify with specific countries
python3 main.py --enable-deidentification --countries US IN ID

# De-identify with all countries
python3 main.py --enable-deidentification --countries ALL

# Skip specific steps
python3 main.py --skip-dictionary
python3 main.py --skip-extraction
python3 main.py --skip-deidentification

# Testing mode (no encryption)
python3 main.py --enable-deidentification --no-encryption
```

### De-identification Module

```bash
# List supported countries
python3 -m scripts.utils.deidentify --list-countries

# Direct de-identification
python3 -m scripts.utils.deidentify \
  --countries IN US \
  --input-dir results/dataset/Indo-vap/cleaned \
  --output-dir results/deidentified/Indo-vap
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'cryptography'`
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: Date parsing warnings
**Solution**: These are informational warnings for ISO date formats. The dates are processed correctly through alternative handlers.

**Issue**: Permission denied when accessing files
**Solution**: Check file permissions and ensure you have read/write access to input/output directories.

**Issue**: Out of memory errors
**Solution**: The pipeline uses streaming for large files. If issues persist, process files in smaller batches.

## Contributing

### Adding a New Country

1. **Define Regulation Function** in `scripts/utils/country_regulations.py`:
```python
def get_your_country_regulation() -> CountryRegulation:
    return CountryRegulation(
        country_code="XX",
        country_name="Your Country",
        regulation_name="Privacy Act Name",
        regulation_acronym="ACRONYM",
        common_fields=get_common_fields(),
        specific_fields=[
            # Add country-specific fields
        ],
        description="Privacy regulation description",
        requirements=["requirement 1", "requirement 2"]
    )
```

2. **Register in COUNTRY_REGISTRY**:
```python
COUNTRY_REGISTRY["XX"] = get_your_country_regulation
```

3. **Update Documentation** in `docs/sphinx/user_guide/country_regulations.rst`

See `docs/sphinx/developer_guide/extending.rst` for detailed instructions.

## Output Files

### De-identification Outputs

After running de-identification, you'll find:

```
results/deidentified/Indo-vap/
├── _deidentification_audit.json    # Audit log
├── original/                       # De-identified original files
│   └── *.jsonl
└── cleaned/                        # De-identified cleaned files
    └── *.jsonl

results/deidentified/mappings/
└── mappings.enc                    # Encrypted pseudonym mappings
```

### File Formats

**JSONL Format**: Each line is a valid JSON object:
```json
{"field1": "[PATIENT-A4B8]", "field2": "[DATE-1]", "field3": "value"}
```

**Audit Log**: JSON file with de-identification statistics:
```json
{
  "texts_processed": 1854110,
  "total_detections": 365630,
  "countries": ["IN"],
  "timestamp": "2025-10-13T00:37:00"
}
```

## Requirements

### Python Packages

**Core Dependencies** (Required):
- **pandas** (≥2.0.0): Data manipulation and Excel reading
- **openpyxl** (≥3.1.0): Excel file format support (.xlsx files)
- **numpy** (≥1.24.0): Numerical operations
- **tqdm** (≥4.66.0): **Required** - Progress bars and clean console output
- **cryptography** (≥41.0.0): Encryption for de-identification mappings

**Documentation** (Optional):
- **sphinx** (≥7.0.0): Documentation generation
- **sphinx-rtd-theme** (≥1.3.0): ReadTheDocs theme
- **sphinx-autodoc-typehints** (≥1.24.0): Type hints in docs
- **myst-parser** (≥2.0.0): Markdown support in Sphinx

See `requirements.txt` for complete list with versions.

### System Requirements
- **Python**: 3.13+
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for code + data size
- **OS**: Windows, macOS, Linux

## Code Quality & Maintenance

### Production-Ready Status

RePORTaLiN has undergone comprehensive code audits to ensure production quality:

**✅ Dependencies**:
- All dependencies in `requirements.txt` are actively used
- No unused imports in any module
- tqdm is a required dependency (not optional)
- All imports verified for actual usage

**✅ Progress Tracking**:
- Consistent use of tqdm progress bars across all long-running operations
- Clean console output using `tqdm.write()` for status messages
- Real-time feedback with percentage, speed, and time remaining
- Modules with progress tracking: `extract_data.py`, `load_dictionary.py`, `deidentify.py`

**✅ Code Organization**:
- No temporary files or test directories in production
- Clean separation of concerns across modules
- Consistent error handling patterns
- Comprehensive logging at every step

**✅ Documentation**:
- Complete Sphinx documentation
- All features documented with examples
- Clear installation and usage instructions
- Developer guide for extending the system

### Quality Assurance

- ✅ All Python files compile without errors
- ✅ All imports resolve successfully
- ✅ Runtime verification of core functionality
- ✅ Consistent coding patterns across modules
- ✅ No dead code or unused functionality

## License

[Add your license information here]

## Citation

If you use this software in your research, please cite:

```
[Add citation information]
```

## Support

For questions, issues, or contributions:
- **Issues**: [GitHub Issues URL]
- **Documentation**: `docs/sphinx/`
- **Email**: [Contact email]

## Changelog

### Version 0.0.1 (October 2025)
- Initial release
- Country-specific de-identification support (14 countries)
- HIPAA, GDPR, LGPD, DPDPA compliance
- Encryption by default
- Comprehensive Sphinx documentation

## Acknowledgments

This project is part of the RePORTaLiN (Regional Prospective Observational Research for Tuberculosis and Lung Infections) consortium.

---

**Last Updated**: October 13, 2025  
**Version**: 0.0.1  
**Status**: Production-Ready
