# RePORTaLiN - Report India Clinical Study

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20quality-production--ready-brightgreen.svg)](https://github.com/yourusername/RePORTaLiN)
[![Documentation](https://img.shields.io/badge/docs-sphinx-blue.svg)](docs/sphinx/)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-compliant-success.svg)](https://www.hhs.gov/hipaa/index.html)
[![GDPR Compliant](https://img.shields.io/badge/GDPR-compliant-success.svg)](https://gdpr.eu/)

A robust data processing pipeline for clinical research data with advanced de-identification and privacy compliance features.

> 📚 **For comprehensive documentation, usage guides, and API references, see [Documentation](#documentation)**

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Overview

RePORTaLiN is a comprehensive data processing system designed for handling sensitive clinical research data. It provides:

- **Data Dictionary Processing**: Automated loading and validation of study data dictionaries
- **Data Extraction**: Excel to JSONL conversion with validation
- **De-identification**: Advanced PHI/PII detection and pseudonymization with country-specific privacy regulations
- **Security**: Encryption by default, secure key management, and audit trails
- **Colored Output**: Enhanced visual feedback with colored logs and progress bars

## Key Features

### 🌍 Multi-Country Privacy Compliance
- **14 countries supported**: US, IN, ID, BR, PH, ZA, EU, GB, CA, AU, KE, NG, GH, UG
- **Regulations**: HIPAA, GDPR, LGPD, DPDPA, POPIA, and more
- **18+ PHI/PII identifier types** detected and pseudonymized

### 🔒 Security & Performance
- **Encryption by default** with Fernet symmetric encryption
- **Fast processing**: 200,000+ texts per second
- **Date shifting** with temporal relationship preservation
- **Audit trails** for compliance and validation

### 📊 Data Processing
- **Multi-table detection** from complex Excel layouts
- **JSONL output** for efficient streaming
- **Colored output** for improved readability and user experience
- **Progress tracking** with real-time feedback
- **Duplicate detection** and intelligent column handling

> 📖 **Learn more**: See [User Guide](docs/sphinx/user_guide/) for detailed feature documentation

## Quick Start

### Installation

**Prerequisites**: Python 3.13+

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/RePORTaLiN.git
cd RePORTaLiN

# 2. Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run complete pipeline
python3 main.py

# Run with de-identification
python3 main.py --enable-deidentification

# Specify countries for de-identification
python3 main.py --enable-deidentification --countries IN US

# Disable colored output (if needed)
python3 main.py --no-color

# Using Makefile
make run                    # Without de-identification
make run-deidentify         # With de-identification
make help                   # View all commands
```

### Example Output

```
Processing Indo-vap dataset...
✓ Loaded 43 Excel files
✓ Extracted 1,854,110 text fields
✓ Detected 365,620 PHI/PII instances
✓ Created 5,398 unique pseudonyms
✓ Time: ~8 seconds
```

> 📖 **For detailed usage, configuration, and troubleshooting**: See [User Guide](docs/sphinx/user_guide/)

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
│       └── logging.py              # Logging utilities
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

### 📚 Complete Documentation

Comprehensive guides and references are available in the Sphinx documentation:

**User Guides:**
- [Quick Start Guide](docs/sphinx/user_guide/quickstart.rst) - Get started in minutes
- [Usage Guide](docs/sphinx/user_guide/usage.rst) - Detailed usage instructions
- [De-identification Guide](docs/sphinx/user_guide/deidentification.rst) - PHI/PII removal and privacy
- [Country Regulations](docs/sphinx/user_guide/country_regulations.rst) - Country-specific privacy rules
- [Configuration](docs/sphinx/user_guide/configuration.rst) - Configuration options
- [Troubleshooting](docs/sphinx/user_guide/troubleshooting.rst) - Common issues and solutions

**Developer Guides:**
- [Architecture](docs/sphinx/developer_guide/architecture.rst) - System design and algorithms
- [Contributing](docs/sphinx/developer_guide/contributing.rst) - How to contribute
- [Extending](docs/sphinx/developer_guide/extending.rst) - Adding features and countries
- [Production Readiness](docs/sphinx/developer_guide/production_readiness.rst) - Security and best practices

**API Reference:**
- [API Documentation](docs/sphinx/api/) - Auto-generated API references

### Building Documentation

```bash
cd docs/sphinx
make html
open _build/html/index.html  # macOS/Linux: xdg-open, Windows: start
```

# Full pipeline with all steps
python3 main.py
# or
make run

# Enable de-identification (default: India)
python3 main.py --enable-deidentification
# or
make run-deidentify

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
# or
make run-deidentify-plain
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
**Solution**: Install dependencies: `pip install -r requirements.txt` or `make install`

**Issue**: Date parsing warnings  
**Solution**: The system automatically handles multiple date formats with intelligent parsing:
- Tries ISO 8601 (YYYY-MM-DD), slash-separated (DD/MM/YYYY, MM/DD/YYYY), hyphen-separated, and dot-separated formats
- Preserves original format when shifting dates
- Country-specific format priority (DD/MM/YYYY for India, MM/DD/YYYY for US)
- Falls back to [DATE-HASH] placeholders only if all formats fail

**Issue**: Permission denied when accessing files  
**Solution**: Check file permissions and ensure you have read/write access to input/output directories.

**Issue**: Out of memory errors  
**Solution**: The pipeline uses streaming for large files. If issues persist, process files in smaller batches.

## Requirements

### System Requirements
- **Python**: 3.13+
- **OS**: macOS, Linux, or Windows
- **Memory**: 4GB RAM minimum (8GB+ recommended)
- **Disk**: 1GB+ free space

### Key Python Dependencies
- `pandas` (>=2.0.0) - Data manipulation
- `openpyxl` (>=3.1.0) - Excel handling
- `tqdm` (>=4.65.0) - Progress bars
- `cryptography` (>=41.0.0) - Encryption
- `faker` (>=19.0.0) - Pseudonym generation
- `sphinx` (>=7.0.0) - Documentation

See `requirements.txt` for complete list.

> 📖 **Installation and setup details**: See [Installation Guide](docs/sphinx/user_guide/installation.rst)

## Contributing

We welcome contributions! To contribute:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly  
5. **Update** documentation
6. **Submit** a pull request

> 📖 **Detailed contributing guidelines**: See [Contributing Guide](docs/sphinx/developer_guide/contributing.rst)

### Quick: Adding a New Country

Edit `scripts/utils/country_regulations.py` to add country-specific regulations. See the [Extending Guide](docs/sphinx/developer_guide/extending.rst) for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/RePORTaLiN/issues)
- **Documentation**: `docs/sphinx/` directory
- **Email**: [your-contact-email@example.com]

---

**Version**: 0.0.1 | **Status**: Production-Ready | **Last Updated**: October 14, 2025

This project is part of the RePORTaLiN (Report India Clinical Study) consortium.