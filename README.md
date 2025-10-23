# RePORTaLiN - Report India Clinical Study

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-beta-blue.svg)](https://github.com/yourusername/RePORTaLiN)
[![Documentation](https://img.shields.io/badge/docs-sphinx-blue.svg)](docs/sphinx/)
[![Privacy-Aware](https://img.shields.io/badge/Privacy-Aware-blue.svg)](https://www.hhs.gov/hipaa/index.html)
[![Multi-Regulation Support](https://img.shields.io/badge/Regulations-14%20Countries-green.svg)](https://gdpr.eu/)

A robust data processing pipeline for clinical research data with advanced de-identification and privacy compliance features.

> 📚 **For comprehensive documentation, usage guides, and API references, see [Documentation](#documentation)**

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
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

## Key Features

### 🌍 Multi-Country Privacy Compliance
- **14 countries supported**: US, IN, ID, BR, PH, ZA, EU, GB, CA, AU, KE, NG, GH, UG
- **Regulations**: HIPAA, GDPR, LGPD, DPDPA, POPIA, and more
- **21 PHI/PII identifier types** detected and pseudonymized

### 🔒 Security & Performance
- **Encryption by default** with Fernet symmetric encryption
- **Fast processing**: Optimized for high throughput (benchmarks pending)
- **Date shifting** with temporal relationship preservation
- **Audit trails** for compliance and validation

### 📊 Data Processing
- **Multi-table detection** from complex Excel layouts
- **JSONL output** for efficient streaming
- **Progress tracking** with real-time feedback
- **Duplicate detection** and intelligent column handling
- **Type conversion** with validation and error handling

### 🔧 Robust Configuration (v0.0.12)
- **Enhanced error handling** - Graceful handling of missing directories and files
- **Auto-detection** - Automatic dataset folder discovery with validation
- **Configuration validation** - Built-in validation with clear warning messages
- **Type-safe** - Comprehensive type hints throughout codebase for better IDE support
- **Cross-platform** - Works on macOS, Linux, and Windows
- **REPL compatible** - Works in interactive environments and notebooks

> 📖 **Learn more**: See [User Guide](docs/sphinx/user_guide/) for detailed feature documentation

## Quick Start

### Installation

**Prerequisites**: Python 3.13+

```bash
# 1. Clone and navigate
git clone https://github.com/solomonsjoseph/RePORTaLiN.git
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

# Enable verbose logging (DEBUG level with file:line context)
python3 main.py --verbose

# Verbose with de-identification
python3 main.py -v --enable-deidentification --countries IN US

# Using Makefile
make run                    # Without de-identification
make run-deidentify         # With de-identification
make version                # Show project version information
make help                   # View all commands

# Documentation
make docs                   # Build HTML documentation
make docs-open              # Build and open in browser
make docs-watch             # Auto-rebuild on changes (requires sphinx-autobuild)

# For Developers - Verbose/Debug Mode
make run-verbose            # Verbose logging (DEBUG level)
make run-deidentify-verbose # De-identification + verbose logging
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
│       └── logging.py              # Logging utilities (enhanced v0.0.4)
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

## Usage Examples

### Pipeline Execution

```bash
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

# Verbose mode (DEBUG level with detailed context - shows file:line in logs)
python3 main.py --verbose
python3 main.py -v --enable-deidentification --countries IN

# Get enhanced help with examples
python3 main.py --help  # Shows usage examples and all options

# Testing mode (no encryption)
python3 main.py --enable-deidentification --no-encryption
# or
make run-deidentify-plain
```

### Shell Completion (Optional)

Enable tab completion for bash/zsh/fish:

```bash
# For bash (add to ~/.bashrc)
eval "$(register-python-argcomplete main.py)"

# For zsh (add to ~/.zshrc)
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete main.py)"

# For fish (add to ~/.config/fish/config.fish)
register-python-argcomplete --shell fish main.py | source
```

### Logging & Debugging

**Enhanced Verbose Logging** (v0.0.12+):

The `--verbose` flag now provides detailed debugging context with file and line numbers:

```bash
# Standard logging (INFO level)
python3 main.py
# Log format: 2025-10-22 19:17:11 - reportalin - INFO - Processing data

# Verbose logging (DEBUG level with context)
python3 main.py --verbose
# Log format: 2025-10-22 19:17:11 - reportalin - DEBUG - [main.py:123] - Processing data
#                                                          ↑ Shows source location
```

**Benefits:**
- **Better debugging**: Trace messages to exact source code location
- **Easier troubleshooting**: Quickly identify where errors occur
- **No performance impact**: Only active when `--verbose` is used

**Log file location**: `.logs/reportalin_TIMESTAMP.log`

### Version Management

RePORTaLiN uses **`__version__.py`** as the single source of truth for version information with intelligent **Conventional Commits** support for automatic semantic versioning.

#### Current Version

```bash
# Show current version
make show-version
# Or
python3 main.py --version
```

#### Automatic Version Bumping (Conventional Commits)

The git pre-commit hook intelligently analyzes your commit messages and bumps the version according to **Conventional Commits** standards:

| Commit Message | Version Bump | Example |
|----------------|--------------|---------|
| `fix: ...` | **Patch** | 0.0.12 → 0.0.13 |
| `feat: ...` | **Minor** | 0.0.12 → 0.1.0 |
| `feat!: ...` or `BREAKING CHANGE:` | **Major** | 0.0.12 → 1.0.0 |
| Other (docs, chore, etc.) | **Patch** (default) | 0.0.12 → 0.0.13 |

**Examples:**

```bash
# Bug fix → patch bump
git commit -m "fix: resolve login issue"
# → Version: 0.0.12 → 0.0.13

# New feature → minor bump
git commit -m "feat: add user authentication"
# → Version: 0.0.12 → 0.1.0

# Breaking change → major bump
git commit -m "feat!: redesign API"
# → Version: 0.0.12 → 1.0.0

# With scope
git commit -m "fix(auth): resolve token expiration"
# → Version: 0.0.12 → 0.0.13
```

**Features:**
- **Intelligent**: Analyzes commit message automatically
- **Standard**: Follows Conventional Commits specification
- **Transparent**: Shows version change before commit
- **Bypassable**: Use `git commit --no-verify` to skip

#### Manual Version Bumping

Use Makefile targets when you need manual control:

```bash
# Bump patch version (0.0.12 → 0.0.13)
make bump-patch

# Bump minor version (0.0.12 → 0.1.0)
make bump-minor

# Bump major version (0.0.12 → 1.0.0)
make bump-major
```

**Example output:**
```
✓ Version bumped: 0.0.12 → 0.0.13
  Type: patch

New version: 0.0.13
Remember to commit: git add __version__.py && git commit -m 'Bump version'
```

#### Version Consistency

All modules import version from `__version__.py`:
- `config.py` - Configuration module
- `main.py` - Main CLI entry point
- `scripts/__init__.py` - Scripts package
- `scripts/utils/__init__.py` - Utils package
- `docs/sphinx/conf.py` - Documentation

This ensures version consistency across:
- CLI output (`--version` flag)
- Module `__version__` attributes
- Documentation builds
- All import statements

### De-identification Module

```bash
# List supported countries
python3 -m scripts.deidentify --list-countries

# Direct de-identification
python3 -m scripts.deidentify \
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
- `pandas` (>=2.0.0, <2.3.0) - Data manipulation
- `openpyxl` (>=3.1.0, <4.0.0) - Excel handling
- `numpy` (>=1.24.0, <2.3.0) - Numerical operations
- `tqdm` (>=4.66.0, <5.0.0) - Progress bars
- `cryptography` (>=41.0.0, <43.0.0) - Encryption
- `sphinx` (>=7.0.0, <8.0.0) - Documentation

See `requirements.txt` for complete list with version constraints.

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

- **Issues**: [GitHub Issues](https://github.com/solomonsjoseph/RePORTaLiN/issues)
- **Documentation**: `docs/sphinx/` directory
- **Email**: [solomon.joseph@rutgers.edu]

---

**Version**: 0.0.12 | **Status**: Beta (Active Development) | **Last Updated**: October 15, 2025

**Latest Updates (v0.0.12 - October 15, 2025)**:

- **Main Pipeline Enhancement**: Enhanced main entry point documentation (162 lines, 2,214% increase)
- **Public API**: Added explicit ``__all__`` (2 exports: ``main``, ``run_step``)
- **Usage Examples**: Four complete examples (basic, custom, de-identification, advanced)
- **Pipeline Documentation**: Complete command-line arguments and step-by-step guide
- **Output Structure**: Directory tree showing all output locations
- **Version Synchronized**: v0.0.12 across all modules
- **Error Handling**: Documented return codes and error recovery
- **Backward Compatibility**: Zero breaking changes, all existing usage preserved
- **Comprehensive Documentation**: Complete documentation for pipeline orchestration
- See [Changelog](docs/sphinx/changelog.rst) for complete version history

**Previous Updates**:
- v0.0.10: Enhanced `scripts/utils/__init__.py` with package-level API (150 lines, 4,900% increase)
- v0.0.9: Enhanced `scripts/__init__.py` with package-level API (127 lines, 2,440% increase)
- v0.0.8: Enhanced `load_dictionary.py` with explicit public API (2 exports) and 1,400% documentation increase
- v0.0.7: Enhanced `extract_data.py` with explicit public API (6 exports) and 790% documentation increase
- v0.0.6: Enhanced `deidentify.py` with explicit public API (10 exports) and comprehensive type safety
- v0.0.5: Enhanced `country_regulations.py` with explicit public API and usage examples
- v0.0.4: Enhanced `logging.py` with improved type hints and optimized performance
- v0.0.3: Enhanced `config.py` with utility functions and improved robustness

This project is part of the RePORTaLiN (Report India Clinical Study) consortium.