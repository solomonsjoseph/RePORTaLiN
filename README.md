# RePORTaLiN Project

This repository contains a data processing pipeline for the RePORTaLiN project. The scripts are designed to be modular, configurable, and run from a central entry point.

## Project Structure

The project is organized into the following key files and directories:

-   `main.py`: The central entry point for running the entire data processing pipeline. It uses command-line arguments to control which steps are executed.
-   `config.py`: A centralized configuration file where all paths, settings, and parameters are defined. This allows for easy management of project settings without modifying the core logic.
-   `scripts/`: A directory containing the individual processing scripts.
    -   `load_dictionary.py`: A script dedicated to extracting and processing tables from the data dictionary Excel file.
-   `data/`: Contains the raw data files used in the pipeline.
-   `results/`: The default directory where output files are saved.
-   `requirements.txt`: A file listing the Python packages required to run this project.

## Installation

To set up the project, first clone the repository and then install the required dependencies from `requirements.txt`:

```bash
git clone https://github.com/solomonsjoseph/RePORTaLiN.git
cd RePORTaLiN
pip install -r requirements.txt
```

## Configuration

All project configurations, including file paths and logging settings, are managed in `config.py`. Before running the pipeline, you can modify this file to match your environment and data locations.

## Usage

The pipeline should be run from the project's root directory using `main.py`. You can control the execution flow with command-line arguments.

**To run the default pipeline (loads the data dictionary):**

```bash
python main.py
```

**To skip the data dictionary loading step:**

```bash
python main.py --skip-dictionary
```

## Scripts

### `scripts/load_dictionary.py`

This script is responsible for extracting tables from the data dictionary Excel file and saving them as JSONL files. It is designed to be called from the main pipeline but can also be run directly for debugging purposes.

#### Features

- **Dynamic Grid-Splitting Logic:** Intelligently detects and splits a single Excel sheet into multiple tables based on empty rows and columns.
- **"Ignore Below" Marker Handling:** When this marker is found in a table header, all subsequent tables on that sheet are saved to a separate `extraas` sub-directory.
- **Duplicate Column Name Resolution:** Automatically resolves duplicate column names by appending a numerical suffix to ensure data integrity.
- **Modular and Reusable Code:** The core logic is broken down into smaller, well-defined functions for clarity and maintainability.
- **Enhanced Error Handling and Logging:** Provides detailed feedback and gracefully handles file I/O errors or issues during sheet processing.
