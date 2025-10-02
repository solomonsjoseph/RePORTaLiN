# RePORTaLiN

**A robust data extraction pipeline for processing medical research data from Excel files to JSONL format.**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-clean-brightgreen.svg)](.)

## Overview

RePORTaLiN is a production-ready data processing pipeline designed to extract and transform medical research data from Excel files into structured JSONL format. It features intelligent table detection, comprehensive logging, progress tracking, and robust error handling.

## ✨ Features

- 🚀 **Fast & Efficient**: Process 43 Excel files in ~15-20 seconds
- 📊 **Smart Table Detection**: Automatically splits Excel sheets into multiple tables
- 📝 **Comprehensive Logging**: Timestamped logs with detailed operation tracking
- 📈 **Progress Tracking**: Real-time progress bars for all operations
- 🔧 **Configurable**: Centralized configuration management
- 📖 **Well Documented**: Comprehensive Sphinx documentation (user & developer modes)

## Project Structure

```
RePORTaLiN/
├── main.py                          # Central entry point - run this!
├── config.py                        # Configuration settings (dynamic dataset detection)
├── requirements.txt                 # Project dependencies
├── Makefile                         # Common commands
├── scripts/
│   ├── extract_data.py             # Excel to JSONL extraction logic
│   ├── load_dictionary.py          # Data dictionary processor
│   └── utils/
│       └── logging_utils.py        # Centralized logging
├── docs/                           # Documentation
│   └── sphinx/                     # Sphinx HTML documentation (user & developer modes)
├── data/                           # Raw data files
│   ├── dataset/
│   │   └── <dataset_name>/         # Excel source files (e.g., Indo-vap_csv_files)
│   └── data_dictionary_and_mapping_specifications/
├── results/                        # Generated JSONL outputs
│   ├── dataset/
│   │   └── <dataset_name>/         # Extracted data (e.g., Indo-vap)
│   └── data_dictionary_mappings/   # Dictionary tables
└── .logs/                          # Execution logs
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/solomonsjoseph/RePORTaLiN.git
cd RePORTaLiN

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Pipeline

The simplest way to run the entire pipeline:

```bash
python main.py
```

This will:
1. ✅ Load and process the data dictionary (14 sheets)
2. ✅ Extract data from 43 Excel files
3. ✅ Generate JSONL output files in `results/dataset/<dataset_name>/`
4. ✅ Create timestamped logs in `.logs/`

**Note:** The pipeline automatically detects the dataset folder in `data/dataset/` and creates corresponding output in `results/dataset/<dataset_name>/`

**Expected output:**
```
Processing sheets: 100%|██████████| 14/14 [00:00<00:00, 122.71sheet/s]
SUCCESS: Excel processing complete!
SUCCESS: Step 0: Loading Data Dictionary completed successfully.
Found 43 Excel files to process...
Processing files: 100%|██████████| 43/43 [00:15<00:00, 2.87file/s]
SUCCESS: Step 1: Extracting Raw Data to JSONL completed successfully.
RePORTaLiN pipeline finished.
```

### 3. Command-Line Options

```bash
# Skip data dictionary loading
python main.py --skip-dictionary

# Skip data extraction
python main.py --skip-extraction

# Skip both (useful for testing)
python main.py --skip-dictionary --skip-extraction
```

### 4. Using Make Commands

```bash
make test      # Run all unit tests
make run       # Run the pipeline
make clean     # Remove cache files
```

## Core Components

### `main.py` - Central Entry Point
The main execution script that orchestrates the entire pipeline. It:
- Sets up logging
- Loads the data dictionary
- Extracts data from Excel files
- Handles errors gracefully
- Provides progress feedback

### `scripts/extract_data.py` - Data Extraction
Converts Excel files to JSONL format with:
- Automatic data type handling (dates, numbers, NaN values)
- Source file tracking
- Empty dataframe handling
- Progress bars for file processing

### `scripts/load_dictionary.py` - Dictionary Processor
Processes the data dictionary Excel file with:
- **Smart table detection**: Splits sheets into multiple tables based on empty rows/columns
- **Duplicate column handling**: Automatically resolves duplicate column names
- **"Ignore below" marker**: Handles special markers for table segmentation
- **Metadata tracking**: Preserves table structure information

### `config.py` - Configuration
Centralized configuration for:
- File paths (data, results, logs)
- Logging settings
- Directory structure

### `scripts/utils/logging_utils.py` - Logging System
Custom logging system with:
- Timestamped log files
- Console and file output
- SUCCESS level for important milestones
- Detailed error tracking

## Output

The pipeline generates two types of outputs:

### 1. Extracted Data (`results/Indo-vap/`)
JSONL files containing the extracted data:
```
results/Indo-vap/
├── 10_TST.jsonl          (631 records)
├── 11_IGRA.jsonl         (262 records)
├── 12A_FUA.jsonl         (2,831 records)
├── 12B_FUB.jsonl         (1,862 records)
├── ...                   (43 files total)
```

### 2. Data Dictionary Mappings (`results/data_dictionary_mappings/`)
Processed tables from the data dictionary:
```
results/data_dictionary_mappings/
├── RePORT_Variables/
│   └── RePORT_Variables_table.jsonl
├── Codelists/
│   ├── Codelists_table_1.jsonl
│   └── Codelists_table_2.jsonl
├── tblENROL/
│   └── tblENROL_table.jsonl
└── ...                   (14 sheets)
```

### 3. Logs (`.logs/`)
Timestamped execution logs:
```
.logs/
└── reportalin_20251001_132124.log
```

## Configuration

Edit `config.py` to customize:

```python
# Directory paths
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"

# Logging settings
LOG_LEVEL = logging.INFO
LOG_NAME = "reportalin"

# Data locations
DATASET_DIR = DATA_DIR / "dataset" / "Indo-vap_csv_files"
DICTIONARY_EXCEL_FILE = DATA_DIR / "data_dictionary_and_mapping_specifications" / "RePORT_DEB_to_Tables_mapping.xlsx"
```

## Documentation

RePORTaLiN includes comprehensive Sphinx documentation with **two viewing modes**:

### 👥 User Mode (Simplified)
For end users - includes installation, quick start, usage, and troubleshooting:
```bash
cd docs/sphinx && make user-mode
open _build/html/index.html
```

### 🔧 Developer Mode (Complete)
For developers - includes everything plus architecture, API reference, and contributing guides:
```bash
cd docs/sphinx && make dev-mode
open _build/html/index.html
```

See **[docs/sphinx/README.md](docs/sphinx/README.md)** for detailed build instructions.

## Development

### Setting Up Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Clean cache files
make clean
```

### Project Statistics

- **Total Lines of Code:** 674 (core)
- **Documentation:** Comprehensive Sphinx documentation (user & developer modes)
- **Execution Time:** ~15-20 seconds for full pipeline

## Requirements

- **Python:** 3.13+ (tested on 3.13.5)
- **Dependencies:**
  - pandas >= 2.0.0
  - openpyxl >= 3.1.0
  - numpy >= 1.24.0
  - tqdm >= 4.66.0

## Troubleshooting

### Common Issues

**1. Import errors:**
```bash
# Ensure you're in the project root
cd /path/to/RePORTaLiN
python main.py
```

**2. No module named 'tqdm':**
```bash
pip install -r requirements.txt
```

**3. Permission denied on logs:**
```bash
# Ensure .logs directory is writable
chmod 755 .logs/
```

**4. File not found errors:**
- Check paths in `config.py`
- Ensure data files exist in `data/` directory

For more troubleshooting, see the Sphinx documentation:
```bash
cd docs/sphinx && make dev-mode
open _build/html/user_guide/troubleshooting.html
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure the code runs without errors
5. Submit a pull request

## License

This project is part of the RePORTaLiN research initiative.

## Contact

For questions or issues, please open an issue on GitHub.

---

**Status:** ✅ Production Ready | **Version:** 1.0.0
