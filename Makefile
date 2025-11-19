# Makefile for RePORTaLiN Project
# =================================
# Enhanced for cross-platform compatibility and production use
#
# Features:
# - Auto-detection of Python (python3/python)
# - Virtual environment support and auto-detection
# - Cross-platform browser detection
# - Colored output for better readability
# - Comprehensive cleaning and testing commands
# - Documentation building and serving

# Color output for better readability
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
ORANGE := \033[38;5;208m
NC := \033[0m # No Color

# Detect Python command (python3 preferred, fallback to python)
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

# Virtual environment settings
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Check if virtual environment exists
VENV_EXISTS := $(shell test -d $(VENV_DIR) && echo 1 || echo 0)

# Use venv python if it exists, otherwise use system python
ifeq ($(VENV_EXISTS),1)
	PYTHON_CMD := $(VENV_PYTHON)
	PIP_CMD := $(VENV_PIP)
else
	PYTHON_CMD := $(PYTHON)
	PIP_CMD := $(PYTHON) -m pip
endif

# Detect OS for platform-specific commands
UNAME_S := $(shell uname -s)

# Detect browser command (for opening docs)
ifeq ($(UNAME_S),Darwin)
	BROWSER := open
else ifeq ($(UNAME_S),Linux)
	BROWSER := xdg-open
else
	BROWSER := echo "Please manually open:"
endif

.PHONY: help install clean clean-all clean-all-force clean-all-execute clean-logs clean-tmp clean-output clean-docs run run-verbose run-deidentify run-deidentify-verbose run-deidentify-plain ingest-pdfs ingest-pdfs-verbose ingest-records ingest-records-verbose ingest-records-cleaned ingest-records-cleaned-verbose ingest-records-original ingest-records-original-verbose ingest-all ingest-all-verbose ingest-all-datasets ingest-all-datasets-verbose clean-vector-db docs docs-open docs-watch docs-help docs-check test venv check-python version bump-patch bump-minor bump-major show-version lint format status commit

help:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)    RePORTaLiN Project - Available Commands    $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make venv                     - Create virtual environment"
	@echo "  make install                  - Install all dependencies (auto-detects venv)"
	@echo "  make check-python             - Check Python and environment status"
	@echo "  make version                  - Show project version information"
	@echo ""
	@echo "$(GREEN)Version Management:$(NC)"
	@echo "  make show-version             - Show current version only"
	@$(PYTHON_CMD) -c "from __version__ import __version__; parts = __version__.split('.'); print('  make bump-patch               - Bump patch version (e.g., {} → {}.{}.{})'.format(__version__, parts[0], parts[1], int(parts[2])+1))"
	@$(PYTHON_CMD) -c "from __version__ import __version__; parts = __version__.split('.'); print('  make bump-minor               - Bump minor version (e.g., {} → {}.{}.0)'.format(__version__, parts[0], int(parts[1])+1))"
	@$(PYTHON_CMD) -c "from __version__ import __version__; parts = __version__.split('.'); print('  make bump-major               - Bump major version (e.g., {} → {}.0.0)'.format(__version__, int(parts[0])+1))"
	@echo "  make commit MSG=\"msg\"          - Smart commit with auto version bump"
	@echo ""
	@echo "$(GREEN)Running:$(NC)"
	@echo "  make run                      - Run pipeline (no de-identification)"
	@echo "  make run-deidentify           - Run pipeline WITH de-identification (simple logging)"
	@echo "  make run-deidentify-plain     - Run pipeline WITH de-identification (NO encryption)"
	@echo ""
	@echo "$(ORANGE)Data Ingestion-RAG:$(NC)"
	@echo "  make ingest-pdfs              - Ingest PDF forms into vector database"
	@echo "  make ingest-records           - Ingest JSONL records (cleaned dataset, default)"
	@echo "  make ingest-records-cleaned   - Ingest cleaned JSONL records explicitly"
	@echo "  make ingest-records-original  - Ingest original JSONL records"
	@echo "  make ingest-all               - Ingest PDFs + cleaned JSONL records"
	@echo "  make ingest-all-datasets      - Ingest PDFs + both cleaned & original JSONL"
	@echo "  make ingest-pdfs-verbose      - Ingest PDFs with VERBOSE (DEBUG) logging"
	@echo "  make ingest-records-verbose   - Ingest cleaned JSONL with VERBOSE logging"
	@echo "  make ingest-records-cleaned-verbose    - Ingest cleaned JSONL with VERBOSE logging"
	@echo "  make ingest-records-original-verbose   - Ingest original JSONL with VERBOSE logging"
	@echo "  make ingest-all-verbose       - Ingest PDFs + cleaned JSONL with VERBOSE logging"
	@echo "  make ingest-all-datasets-verbose       - Ingest all datasets with VERBOSE logging"
	@echo "  make clean-vector-db          - Remove vector database storage"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test                     - Run tests (if available)"
	@echo "  make lint                     - Check code style (if ruff/flake8 installed)"
	@echo "  make format                   - Format code (if black installed)"
	@echo "  make status                   - Show project status summary"
	@echo ""
	@echo "$(YELLOW)Logging Modes (For Developers):$(NC)"
	@echo "  make run-verbose              - Run with VERBOSE (DEBUG) logging - detailed context in .logs/"
	@echo "  make run-deidentify-verbose   - Run de-identification + VERBOSE logging"
	@echo "  Note: Simple logging (INFO level, minimal console) is DEFAULT for all commands"
	@echo "        Use -verbose targets for detailed DEBUG output"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  make docs                     - Build Sphinx HTML documentation"
	@echo "  make docs-open                - Build docs and open in browser"
	@echo "  make docs-watch               - Auto-rebuild docs on file changes (requires sphinx-autobuild)"
	@echo "  make docs-check               - Quick style compliance check (daily use, ~10 sec)"
	@echo "  make docs-quality             - Comprehensive quality check (quarterly, ~60 sec)"
	@echo "  make docs-maintenance         - Full maintenance: check + quality + build"
	@echo "  make docs-help                - Show advanced Sphinx documentation options"
	@echo ""
	@echo "$(GREEN)Cleaning:$(NC)"
	@echo "  make clean                    - Remove Python cache files"
	@echo "  make clean-logs               - Remove log files"
	@echo "  make clean-tmp                - Remove tmp files (analysis/reports)"
	@echo "  make clean-output             - Remove generated output files"
	@echo "  make clean-docs               - Remove documentation build files"
	@echo "  make clean-all                - Remove ALL generated files (including tmp)"
	@echo ""
	@echo "$(YELLOW)Using Python:$(NC) $(PYTHON_CMD)"
	@echo ""

# Setup commands
check-python:
	@echo "$(BLUE)Checking Python environment...$(NC)"
	@echo "System Python: $(PYTHON)"
	@echo "Active Python: $(PYTHON_CMD)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "$(GREEN)✓ Virtual environment found at: $(VENV_DIR)$(NC)"; \
	else \
		echo "$(YELLOW)⚠ No virtual environment found. Run 'make venv' to create one.$(NC)"; \
	fi
	@$(PYTHON_CMD) --version
	@echo ""

venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Virtual environment already exists at $(VENV_DIR)$(NC)"; \
	else \
		echo "$(BLUE)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "$(GREEN)✓ Virtual environment created at $(VENV_DIR)$(NC)"; \
		echo "$(YELLOW)Run 'make install' to install dependencies$(NC)"; \
	fi

install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@echo "Using Python: $(PYTHON_CMD)"
	@echo "Using pip: $(PIP_CMD)"
	@$(PIP_CMD) install --upgrade pip
	@$(PIP_CMD) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

version:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)       RePORTaLiN Version Information          $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Project Version:$(NC)"
	@$(PYTHON_CMD) main.py --version
	@echo ""
	@echo "$(GREEN)Python Environment:$(NC)"
	@echo "  Python: $$($(PYTHON_CMD) --version)"
	@echo "  Path:   $(PYTHON_CMD)"
	@echo ""
	@echo "$(GREEN)Key Dependencies:$(NC)"
	@$(PYTHON_CMD) -c "import pandas; print('  pandas:     ', pandas.__version__)" 2>/dev/null || echo "  pandas:      Not installed"
	@$(PYTHON_CMD) -c "import openpyxl; print('  openpyxl:   ', openpyxl.__version__)" 2>/dev/null || echo "  openpyxl:    Not installed"
	@$(PYTHON_CMD) -c "import tqdm; print('  tqdm:       ', tqdm.__version__)" 2>/dev/null || echo "  tqdm:        Not installed"
	@$(PYTHON_CMD) -c "import cryptography; print('  cryptography:', cryptography.__version__)" 2>/dev/null || echo "  cryptography: Not installed"
	@echo ""

# Version management commands
show-version:
	@$(PYTHON_CMD) -c "from __version__ import __version__; print(__version__)"

bump-patch:
	@./.git/hooks/bump-version patch
	@echo ""
	@echo "$(YELLOW)New version:$(NC) $$($(PYTHON_CMD) -c 'from __version__ import __version__; print(__version__)')"
	@echo "$(YELLOW)Remember to commit:$(NC) git add __version__.py && git commit -m 'Bump version'"

bump-minor:
	@./.git/hooks/bump-version minor
	@echo ""
	@echo "$(YELLOW)New version:$(NC) $$($(PYTHON_CMD) -c 'from __version__ import __version__; print(__version__)')"
	@echo "$(YELLOW)Remember to commit:$(NC) git add __version__.py && git commit -m 'Bump version'"

bump-major:
	@./.git/hooks/bump-version major
	@echo ""
	@echo "$(YELLOW)New version:$(NC) $$($(PYTHON_CMD) -c 'from __version__ import __version__; print(__version__)')"
	@echo "$(YELLOW)Remember to commit:$(NC) git add __version__.py && git commit -m 'Bump version'"

# Smart commit with automatic version bumping
commit:
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)✗ Error: Commit message required$(NC)"; \
		echo "$(YELLOW)Usage: make commit MSG=\"your commit message\"$(NC)"; \
		exit 1; \
	fi
	@./scripts/utils/smart-commit "$(MSG)"

# Running commands
run:
	@echo "$(BLUE)Running RePORTaLiN pipeline (without de-identification)...$(NC)"
	@$(PYTHON_CMD) main.py
	@echo "$(GREEN)✓ Pipeline completed$(NC)"

run-verbose:
	@echo "$(BLUE)Running RePORTaLiN pipeline with VERBOSE logging...$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(PYTHON_CMD) main.py --verbose
	@echo "$(GREEN)✓ Pipeline completed$(NC)"
	@echo "$(YELLOW)Check log file in .logs/ for detailed output$(NC)"

run-deidentify:
	@echo "$(BLUE)Running RePORTaLiN pipeline WITH de-identification (encrypted)...$(NC)"
	@echo "$(YELLOW)Note: Encryption is enabled by default for security$(NC)"
	@echo "$(YELLOW)      Simple logging mode (INFO level, minimal console output)$(NC)"
	@$(PYTHON_CMD) main.py --enable-deidentification
	@echo "$(GREEN)✓ Pipeline completed$(NC)"

run-deidentify-verbose:
	@echo "$(BLUE)Running RePORTaLiN pipeline WITH de-identification + VERBOSE logging...$(NC)"
	@echo "$(YELLOW)Note: Encryption enabled + Detailed DEBUG output to log file$(NC)"
	@$(PYTHON_CMD) main.py --enable-deidentification --verbose
	@echo "$(GREEN)✓ Pipeline completed$(NC)"
	@echo "$(YELLOW)Check log file in .logs/ for detailed output$(NC)"

run-deidentify-plain:
	@echo "$(RED)═══════════════════════════════════════════════$(NC)"
	@echo "$(RED)WARNING: Running WITH de-identification (NO ENCRYPTION)$(NC)"
	@echo "$(RED)WARNING: Mapping files will be stored in plain text!$(NC)"
	@echo "$(RED)WARNING: This is NOT recommended for production use.$(NC)"
	@echo "$(RED)═══════════════════════════════════════════════$(NC)"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	@$(PYTHON_CMD) main.py --enable-deidentification --no-encryption
	@echo "$(GREEN)✓ Pipeline completed$(NC)"

# Vector database ingestion commands
ingest-pdfs:
	@echo "$(BLUE)Ingesting PDF forms into vector database...$(NC)"
	@echo "$(YELLOW)Collection: clinical_forms_pdf$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_pdfs
	@echo "$(GREEN)✓ PDF ingestion completed$(NC)"

ingest-pdfs-verbose:
	@echo "$(BLUE)Ingesting PDF forms with VERBOSE logging...$(NC)"
	@echo "$(YELLOW)Collection: clinical_forms_pdf$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_pdfs --verbose
	@echo "$(GREEN)✓ PDF ingestion completed$(NC)"
	@echo "$(YELLOW)Check log file in .logs/ for detailed output$(NC)"

ingest-records:
	@echo "$(BLUE)Ingesting JSONL patient records (cleaned dataset)...$(NC)"
	@echo "$(YELLOW)Dataset Type: cleaned$(NC)"
	@echo "$(YELLOW)Collection: Indo-VAP_jsonl_records_cleaned$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_records --dataset-type cleaned
	@echo "$(GREEN)✓ JSONL (cleaned) ingestion completed$(NC)"

ingest-records-verbose:
	@echo "$(BLUE)Ingesting JSONL patient records (cleaned) with VERBOSE logging...$(NC)"
	@echo "$(YELLOW)Dataset Type: cleaned$(NC)"
	@echo "$(YELLOW)Collection: Indo-VAP_jsonl_records_cleaned$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_records --dataset-type cleaned --verbose
	@echo "$(GREEN)✓ JSONL (cleaned) ingestion completed$(NC)"
	@echo "$(YELLOW)Check log file in .logs/ for detailed output$(NC)"

ingest-records-cleaned:
	@echo "$(BLUE)Ingesting JSONL patient records (cleaned dataset)...$(NC)"
	@echo "$(YELLOW)Dataset Type: cleaned$(NC)"
	@echo "$(YELLOW)Collection: Indo-VAP_jsonl_records_cleaned$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_records --dataset-type cleaned
	@echo "$(GREEN)✓ JSONL (cleaned) ingestion completed$(NC)"

ingest-records-cleaned-verbose:
	@echo "$(BLUE)Ingesting JSONL patient records (cleaned) with VERBOSE logging...$(NC)"
	@echo "$(YELLOW)Dataset Type: cleaned$(NC)"
	@echo "$(YELLOW)Collection: Indo-VAP_jsonl_records_cleaned$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_records --dataset-type cleaned --verbose
	@echo "$(GREEN)✓ JSONL (cleaned) ingestion completed$(NC)"
	@echo "$(YELLOW)Check log file in .logs/ for detailed output$(NC)"

ingest-records-original:
	@echo "$(BLUE)Ingesting JSONL patient records (original dataset)...$(NC)"
	@echo "$(YELLOW)Dataset Type: original$(NC)"
	@echo "$(YELLOW)Collection: Indo-VAP_jsonl_records_original$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_records --dataset-type original
	@echo "$(GREEN)✓ JSONL (original) ingestion completed$(NC)"

ingest-records-original-verbose:
	@echo "$(BLUE)Ingesting JSONL patient records (original) with VERBOSE logging...$(NC)"
	@echo "$(YELLOW)Dataset Type: original$(NC)"
	@echo "$(YELLOW)Collection: Indo-VAP_jsonl_records_original$(NC)"
	@echo "$(YELLOW)Output: output/vector_db/$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(PYTHON_CMD) -m scripts.vector_db.ingest_records --dataset-type original --verbose
	@echo "$(GREEN)✓ JSONL (original) ingestion completed$(NC)"
	@echo "$(YELLOW)Check log file in .logs/ for detailed output$(NC)"

ingest-all:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)   Ingesting PDFs + Cleaned JSONL Records     $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@$(MAKE) ingest-pdfs
	@echo ""
	@$(MAKE) ingest-records-cleaned
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ All document ingestion completed!$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"

ingest-all-verbose:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)   Ingesting PDFs + Cleaned JSONL with VERBOSE$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(MAKE) ingest-pdfs-verbose
	@echo ""
	@$(MAKE) ingest-records-cleaned-verbose
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ All document ingestion completed!$(NC)"
	@echo "$(GREEN)Check log file in .logs/ for detailed output$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"

ingest-all-datasets:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)   Ingesting All Datasets (PDFs + Both JSONL) $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@$(MAKE) ingest-pdfs
	@echo ""
	@$(MAKE) ingest-records-cleaned
	@echo ""
	@$(MAKE) ingest-records-original
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ All datasets ingestion completed!$(NC)"
	@echo "$(GREEN)  - PDFs ingested$(NC)"
	@echo "$(GREEN)  - Cleaned JSONL records ingested$(NC)"
	@echo "$(GREEN)  - Original JSONL records ingested$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"

ingest-all-datasets-verbose:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)   Ingesting All Datasets with VERBOSE Logging$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)Note: Detailed DEBUG output will be saved to log file$(NC)"
	@$(MAKE) ingest-pdfs-verbose
	@echo ""
	@$(MAKE) ingest-records-cleaned-verbose
	@echo ""
	@$(MAKE) ingest-records-original-verbose
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ All datasets ingestion completed!$(NC)"
	@echo "$(GREEN)  - PDFs ingested$(NC)"
	@echo "$(GREEN)  - Cleaned JSONL records ingested$(NC)"
	@echo "$(GREEN)  - Original JSONL records ingested$(NC)"
	@echo "$(GREEN)Check log file in .logs/ for detailed output$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"

clean-vector-db:
	@echo "$(RED)WARNING: This will delete the entire vector database!$(NC)"
	@printf "Continue? [y/N]: "; \
	read -r response; \
	response=$$(echo "$$response" | tr '[:upper:]' '[:lower:]'); \
	if [ "$$response" = "y" ] || [ "$$response" = "yes" ]; then \
		echo "$(BLUE)Removing vector database storage...$(NC)"; \
		rm -rf output/vector_db/; \
		echo "$(GREEN)✓ Vector database cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Clean cancelled.$(NC)"; \
	fi

# Cleaning commands
clean:
	@echo "$(BLUE)Cleaning up Python cache files...$(NC)"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache files cleaned$(NC)"

clean-logs:
	@echo "$(BLUE)Cleaning log files...$(NC)"
	@rm -rf .logs/
	@echo "$(GREEN)✓ Log files cleaned$(NC)"

clean-tmp:
	@echo "$(BLUE)Cleaning temp files (analysis and reports)...$(NC)"
	# TODO : Remove even hidden files in tmp/ like .*
	@rm -rf tmp/* tmp/.* 2>/dev/null || true
	@echo "$(GREEN)✓ Temp files cleaned$(NC)"

clean-output:
	@echo "$(RED)WARNING: This will delete all generated output files!$(NC)"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	@rm -rf output/
	@echo "$(GREEN)✓ Output files cleaned$(NC)"

clean-docs:
	@echo "$(BLUE)Cleaning documentation build files...$(NC)"
	@rm -rf docs/sphinx/_build/
	@echo "$(GREEN)✓ Documentation build files cleaned$(NC)"

# Interactive clean-all with user confirmation
clean-all:
	@echo "$(RED)WARNING: This will delete cache, logs, output, tmp files, and documentation builds!$(NC)"
	@printf "Continue? [Y/n]: "; \
	read -r response; \
	response=$$(echo "$$response" | tr '[:upper:]' '[:lower:]'); \
	if [ -z "$$response" ] || [ "$$response" = "y" ] || [ "$$response" = "yes" ]; then \
		$(MAKE) clean-all-execute; \
	else \
		echo "$(YELLOW)Clean cancelled.$(NC)"; \
	fi

# Non-interactive clean-all for automation (CI/CD, scripts)
clean-all-force:
	@$(MAKE) clean-all-execute

# Internal target: actual cleanup logic
clean-all-execute:
	@echo "$(BLUE)Cleaning up Python cache files...$(NC)"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache files cleaned$(NC)"
	@echo "$(BLUE)Cleaning log files...$(NC)"
	@rm -rf .logs/
	@echo "$(GREEN)✓ Log files cleaned$(NC)"
	@echo "$(BLUE)Cleaning temp files...$(NC)"
	@rm -rf tmp/* tmp/.* 2>/dev/null || true
	@echo "$(GREEN)✓ Temp files cleaned$(NC)"
	@echo "$(BLUE)Cleaning documentation build files...$(NC)"
	@rm -rf docs/sphinx/_build/
	@echo "$(GREEN)✓ Documentation build files cleaned$(NC)"
	@echo "$(BLUE)Cleaning output...$(NC)"
	@rm -rf output/
	@echo "$(GREEN)✓ All generated files cleaned$(NC)"

# Testing commands
test:
	@echo "$(BLUE)Running tests...$(NC)"
	@if [ -d "tests" ]; then \
		$(PYTHON_CMD) -m pytest tests/ -v; \
		echo "$(GREEN)✓ Tests completed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ No tests directory found. Skipping tests.$(NC)"; \
	fi

# Development commands
lint:
	@echo "$(BLUE)Checking code style...$(NC)"
	@if $(PYTHON_CMD) -c "import ruff" 2>/dev/null; then \
		$(PYTHON_CMD) -m ruff check . ; \
	elif $(PYTHON_CMD) -c "import flake8" 2>/dev/null; then \
		$(PYTHON_CMD) -m flake8 scripts/ main.py config.py; \
	else \
		echo "$(YELLOW)⚠ No linter found. Install ruff or flake8 for code style checking.$(NC)"; \
	fi

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	@if $(PYTHON_CMD) -c "import black" 2>/dev/null; then \
		$(PYTHON_CMD) -m black scripts/ main.py config.py; \
		echo "$(GREEN)✓ Code formatted$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Black not found. Install black for code formatting: pip install black$(NC)"; \
	fi

status:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)       RePORTaLiN Project Status Summary       $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Environment:$(NC)"
	@echo "  Python: $(PYTHON_CMD)"
	@$(PYTHON_CMD) --version
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "  Virtual Env: $(GREEN)✓ Active at $(VENV_DIR)$(NC)"; \
	else \
		echo "  Virtual Env: $(YELLOW)⚠ Not found$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)Project Structure:$(NC)"
	@echo "  Data Dictionary: $$([ -f 'data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx' ] && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)')"
	@echo "  Dataset Files: $$([ -d 'data/dataset' ] && find data/dataset -name '*.xlsx' 2>/dev/null | wc -l | xargs) files"
	@echo "  Output: $$([ -d 'output' ] && echo '$(GREEN)✓ Exists$(NC)' || echo '$(YELLOW)⚠ Not generated yet$(NC)')"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  Sphinx Docs: $$([ -f 'docs/sphinx/_build/html/index.html' ] && echo '$(GREEN)✓ Built$(NC)' || echo '$(YELLOW)⚠ Not built (run: make docs)$(NC)')"
	@echo ""

# Documentation commands
docs:
	@echo "$(BLUE)Building Sphinx documentation...$(NC)"
	@cd docs/sphinx && $(MAKE) html
	@echo "$(GREEN)✓ Documentation built at docs/sphinx/_build/html/index.html$(NC)"

docs-open: docs
	@echo "$(BLUE)Opening documentation in browser...$(NC)"
	@$(BROWSER) docs/sphinx/_build/html/index.html 2>/dev/null || \
		echo "$(YELLOW)Please manually open: docs/sphinx/_build/html/index.html$(NC)"

docs-watch:
	@echo "$(BLUE)Starting Sphinx auto-rebuild server...$(NC)"
	@echo "$(YELLOW)Documentation will auto-rebuild on file changes$(NC)"
	@echo "$(YELLOW)Server will be available at http://127.0.0.1:8000$(NC)"
	@echo ""
	@if $(PYTHON_CMD) -c "import sphinx_autobuild" 2>/dev/null; then \
		cd docs/sphinx && ../../$(PYTHON_CMD) -m sphinx_autobuild -b html . _build/html --host 127.0.0.1 --port 8000; \
	else \
		echo "$(RED)✗ sphinx-autobuild not installed$(NC)"; \
		echo "$(YELLOW)Install with: pip install sphinx-autobuild$(NC)"; \
		echo "$(YELLOW)Or run: make install (if already in requirements.txt)$(NC)"; \
		exit 1; \
	fi

# Check documentation style compliance (quick, for daily use)
docs-check:
	@echo "$(BLUE)Checking documentation style compliance...$(NC)"
	@if [ -f "scripts/utils/doc_maintenance_toolkit.py" ]; then \
		$(PYTHON_CMD) scripts/utils/doc_maintenance_toolkit.py --mode style; \
		echo "$(GREEN)✓ Documentation compliance check complete$(NC)"; \
	else \
		echo "$(RED)✗ Documentation maintenance toolkit not found$(NC)"; \
		echo "$(YELLOW)Expected at: scripts/utils/doc_maintenance_toolkit.py$(NC)"; \
		exit 1; \
	fi

# Comprehensive documentation quality check (for quarterly reviews)
docs-quality:
	@echo "$(BLUE)Running comprehensive documentation quality check...$(NC)"
	@echo "$(YELLOW)This performs deep analysis and may take 30-60 seconds$(NC)"
	@if [ -f "scripts/utils/doc_maintenance_toolkit.py" ]; then \
		$(PYTHON_CMD) scripts/utils/doc_maintenance_toolkit.py --mode quality; \
		echo "$(GREEN)✓ Documentation quality check complete$(NC)"; \
	else \
		echo "$(RED)✗ Documentation maintenance toolkit not found$(NC)"; \
		echo "$(YELLOW)Expected at: scripts/utils/doc_maintenance_toolkit.py$(NC)"; \
		exit 1; \
	fi

# Full documentation maintenance (all checks + build)
docs-maintenance:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)     Full Documentation Maintenance Check      $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(CYAN)Step 1/4: Checking current version...$(NC)"
	@cat __version__.py
	@echo ""
	@echo "$(CYAN)Step 2/4: Running style compliance check...$(NC)"
	@$(MAKE) docs-check
	@echo ""
	@echo "$(CYAN)Step 3/4: Running comprehensive quality check...$(NC)"
	@$(MAKE) docs-quality
	@echo ""
	@echo "$(CYAN)Step 4/4: Building documentation...$(NC)"
	@$(MAKE) docs
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ Full documentation maintenance complete!$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════$(NC)"

# Show advanced Sphinx documentation options (delegates to Sphinx Makefile)
docs-help:
	@cd docs/sphinx && $(MAKE) help
