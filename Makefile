# Makefile for RePORTaLiN Project
# Simplified for production use

# Color output for better readability
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
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

.PHONY: help install clean clean-all clean-logs clean-results clean-docs run run-deidentify run-deidentify-plain docs docs-open test venv check-python lint format status

help:
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)    RePORTaLiN Project - Available Commands    $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make venv                     - Create virtual environment"
	@echo "  make install                  - Install all dependencies (auto-detects venv)"
	@echo "  make check-python             - Check Python and environment status"
	@echo ""
	@echo "$(GREEN)Running:$(NC)"
	@echo "  make run                      - Run pipeline (no de-identification)"
	@echo "  make run-deidentify           - Run pipeline WITH de-identification (encrypted)"
	@echo "  make run-deidentify-plain     - Run pipeline WITH de-identification (NO encryption)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test                     - Run tests (if available)"
	@echo "  make lint                     - Check code style (if ruff/flake8 installed)"
	@echo "  make format                   - Format code (if black installed)"
	@echo "  make status                   - Show project status summary"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  make docs                     - Build Sphinx HTML documentation"
	@echo "  make docs-open                - Build docs and open in browser"
	@echo ""
	@echo "$(GREEN)Cleaning:$(NC)"
	@echo "  make clean                    - Remove Python cache files"
	@echo "  make clean-logs               - Remove log files"
	@echo "  make clean-results            - Remove generated results"
	@echo "  make clean-docs               - Remove documentation build files"
	@echo "  make clean-all                - Remove ALL generated files"
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

# Running commands
run:
	@echo "$(BLUE)Running RePORTaLiN pipeline (without de-identification)...$(NC)"
	@$(PYTHON_CMD) main.py
	@echo "$(GREEN)✓ Pipeline completed$(NC)"

run-deidentify:
	@echo "$(BLUE)Running RePORTaLiN pipeline WITH de-identification (encrypted)...$(NC)"
	@echo "$(YELLOW)Note: Encryption is enabled by default for security$(NC)"
	@$(PYTHON_CMD) main.py --enable-deidentification
	@echo "$(GREEN)✓ Pipeline completed$(NC)"

run-deidentify-plain:
	@echo "$(RED)═══════════════════════════════════════════════$(NC)"
	@echo "$(RED)WARNING: Running WITH de-identification (NO ENCRYPTION)$(NC)"
	@echo "$(RED)WARNING: Mapping files will be stored in plain text!$(NC)"
	@echo "$(RED)WARNING: This is NOT recommended for production use.$(NC)"
	@echo "$(RED)═══════════════════════════════════════════════$(NC)"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	@$(PYTHON_CMD) main.py --enable-deidentification --no-encryption
	@echo "$(GREEN)✓ Pipeline completed$(NC)"

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

clean-results:
	@echo "$(RED)WARNING: This will delete all generated results!$(NC)"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	@rm -rf results/
	@echo "$(GREEN)✓ Results cleaned$(NC)"

clean-docs:
	@echo "$(BLUE)Cleaning documentation build files...$(NC)"
	@rm -rf docs/sphinx/_build/
	@echo "$(GREEN)✓ Documentation build files cleaned$(NC)"

clean-all:
	@echo "$(RED)WARNING: This will delete cache, logs, results, and documentation builds!$(NC)"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	@echo "$(BLUE)Cleaning up Python cache files...$(NC)"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache files cleaned$(NC)"
	@echo "$(BLUE)Cleaning log files...$(NC)"
	@rm -rf .logs/
	@echo "$(GREEN)✓ Log files cleaned$(NC)"
	@echo "$(BLUE)Cleaning documentation build files...$(NC)"
	@rm -rf docs/sphinx/_build/
	@echo "$(GREEN)✓ Documentation build files cleaned$(NC)"
	@echo "$(BLUE)Cleaning results...$(NC)"
	@rm -rf results/
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
	@echo "  Results: $$([ -d 'results' ] && echo '$(GREEN)✓ Exists$(NC)' || echo '$(YELLOW)⚠ Not generated yet$(NC)')"
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
	@open docs/sphinx/_build/html/index.html 2>/dev/null || \
		xdg-open docs/sphinx/_build/html/index.html 2>/dev/null || \
		echo "$(YELLOW)Please manually open: docs/sphinx/_build/html/index.html$(NC)"
