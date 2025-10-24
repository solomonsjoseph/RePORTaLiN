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
- **Encryption by default** with Fernet symmetric encryption (AES-128)
- **Fast processing**: Optimized for high throughput
- **Date shifting** with temporal relationship preservation
- **Audit trails** for compliance and validation

### 📊 Data Processing
- **Multi-table detection** from complex Excel layouts
- **JSONL output** for efficient streaming
- **Progress tracking** with real-time feedback
- **Duplicate detection** and intelligent column handling
- **Type conversion** with validation and error handling

### 🔧 Robust Configuration
- **Enhanced error handling** - Gracefully handles missing directories and files
- **Auto-detection** - Automatically finds dataset folders
- **Configuration validation** - Built-in validation with clear warning messages
- **Type-safe** - Full type hints for better IDE support and code quality
- **Cross-platform** - Works on macOS, Linux, and Windows
- **Interactive-ready** - Works in Jupyter notebooks and Python REPL

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

[Full Documentation](https://solomonsjoseph.github.io/RePORTaLiN/)
[User Guide](https://solomonsjoseph.github.io/RePORTaLiN/user_guide/)
[Developer Guide](https://solomonsjoseph.github.io/RePORTaLiN/developer_guide/)

### Building Documentation Locally

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

**Enhanced Verbose Logging**:

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

#### Automatic Version Bumping (Hybrid System)

RePORTaLiN supports **two automatic methods** that work seamlessly together:

| Commit Message | Version Bump | Example |
|----------------|--------------|---------|
| `fix: ...` | **Patch** | 0.3.0 → 0.3.1 |
| `feat: ...` | **Minor** | 0.3.0 → 0.4.0 |
| `feat!: ...` or `BREAKING CHANGE:` | **Major** | 0.3.0 → 1.0.0 |
| Other (docs, chore, etc.) | **No bump** | 0.3.0 (unchanged) |

**Method 1: VS Code Source Control (Fully Automatic)**

Just commit normally from VS Code or command line—version bumps automatically via post-commit hook!

```bash
# In terminal
git commit -m "feat: add user authentication"
# → Automatically bumps to 0.1.0 and includes in commit

# Or use VS Code:
# 1. Stage your changes
# 2. Type: "feat: add user authentication" 
# 3. Click Commit
# → Version automatically bumps to 0.1.0 ✓
```

**What happens behind the scenes:**
1. Commit is created with your files
2. Post-commit hook analyzes the message
3. Version is bumped automatically
4. Hook amends the commit to include `__version__.py`
5. Final commit contains both your changes AND the version bump

**Method 2: Smart-Commit (Explicit with Preview)**

Use `smart-commit` when you want to see the version bump before committing:

```bash
# Using Makefile
make commit MSG="feat: add user authentication"
# → Shows: ✓ Version bumped: 0.3.0 → 0.4.0
# → Then commits

# Or directly
./scripts/utils/smart-commit "feat: add user authentication"
```

**Example output:**
```
→ Analyzing commit message...
✓ Version bumped: 0.3.0 → 0.4.0
  Type: minor
✓ Version bumped and staged
[main abc1234] feat: add user authentication
 2 files changed, 10 insertions(+), 2 deletions(-)
```

**Both methods work together perfectly:**
- Post-commit hook detects when smart-commit was used
- No double-bumping or conflicts
- Use whichever method you prefer!

**To disable automatic bumping:**
```bash
git commit --no-verify -m "docs: update README"
# --no-verify skips all git hooks
```

#### Manual Version Bumping

Use Makefile targets when you need manual control:

```bash
# Bump patch version (0.3.0 → 0.3.1)
make bump-patch

# Bump minor version (0.3.0 → 0.4.0)
make bump-minor

# Bump major version (0.3.0 → 1.0.0)
make bump-major
```

**Example output:**
```
✓ Version bumped: 0.3.0 → 0.3.1
  Type: patch

New version: 0.3.1
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

**Issue**: `ModuleNotFoundError` or package not found errors  
**Solution**: Install all required packages: `pip install -r requirements.txt` or `make install`

**Issue**: Date format warnings during processing  
**Solution**: The system handles date ambiguity intelligently with country-specific format priority:

**Date Interpretation Strategy:**
1. **Unambiguous formats first**: ISO 8601 (YYYY-MM-DD) always takes priority
2. **Country-specific preference**: For ambiguous dates (e.g., 08/09/2020, 12/12/2012)
   - India (IN): Interprets as DD/MM/YYYY → "08/09/2020" = September 8, 2020
   - USA (US): Interprets as MM/DD/YYYY → "08/09/2020" = August 9, 2020
3. **Smart validation**: Rejects impossible formats
   - "13/05/2020" can only be DD/MM (no 13th month)
   - "05/25/2020" can only be MM/DD (no 25th month)

**Consistency Guarantee**: All dates from the same country use the same interpretation rules.

**Supported formats**: ISO 8601, slash/hyphen/dot-separated (DD/MM or MM/DD based on country)

**Format preservation**: Original date format is preserved after shifting (e.g., if input is "DD/MM/YYYY", output is also "DD/MM/YYYY")

Falls back to [DATE-HASH] placeholders only when all format parsing attempts fail.

**Issue**: Permission denied when accessing files  
**Solution**: Check file permissions and ensure you have read/write access to input/output directories.

**Issue**: Out of memory errors with large datasets  
**Solution**: The pipeline uses efficient streaming for large files. If issues persist, process files in smaller batches or increase available RAM.

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

**Version**: See `__version__.py` | **Status**: Beta (Active Development) | **Last Updated**: October 23, 2025

**Latest Updates (October 23, 2025)**:

- **Documentation Enhancement**: Complete Sphinx documentation audit and version alignment
- **Version Management**: Hybrid version management system with conventional commits
- **Public API**: Explicit ``__all__`` exports across all modules
- **Type Safety**: Complete type annotations and validation
- **Configuration**: Enhanced validation and error handling utilities
- **De-identification**: Country-specific privacy compliance (14 countries)
- **Logging**: Thread-safe, optimized logging with verbose mode
- **Pipeline**: Complete end-to-end workflow with error recovery
- See [Changelog](docs/sphinx/changelog.rst) for complete version history

**Previous Updates**:
- v0.2.0: Hybrid version management system implementation
- Enhanced modules with explicit public APIs and comprehensive documentation
- Security enhancements and country-specific privacy compliance
- Performance optimizations and type safety improvements

This project is part of the RePORTaLiN (Report India Clinical Study) consortium.