# Makefile for RePORTaLiN Project
# Simplified for production use

# Detect Python command (python3 preferred, fallback to python)
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

.PHONY: help install clean clean-all clean-logs clean-results run run-deidentify run-deidentify-plain docs docs-open test

help:
	@echo "RePORTaLiN Project - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install all dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run                      - Run pipeline (no de-identification)"
	@echo "  make run-deidentify          - Run pipeline WITH de-identification (encrypted)"
	@echo "  make run-deidentify-plain    - Run pipeline WITH de-identification (NO encryption)"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean         - Remove Python cache files"
	@echo "  make clean-logs    - Remove log files"
	@echo "  make clean-results - Remove generated results"
	@echo "  make clean-all     - Remove all generated files (cache + logs + results)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Build Sphinx HTML documentation"
	@echo "  make docs-open    - Build docs and open in browser"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run tests (if available)"
	@echo ""
	@echo "Direct commands you can also use:"
	@echo "  $(PYTHON) main.py                              - Run pipeline (no de-identification)"
	@echo "  $(PYTHON) main.py --enable-deidentification    - Run with de-identification (encrypted)"
	@echo "  $(PYTHON) main.py --enable-deidentification --no-encryption  - Run with de-identification (plain text)"
	@echo "  cd docs/sphinx && make html                 - Build docs"
	@echo ""

# Setup commands
install:
	@echo "Installing dependencies..."
	@echo "Using Python: $(PYTHON)"
	$(PYTHON) -m pip install -r requirements.txt
	@echo "[OK] Dependencies installed"

# Running commands
run:
	@echo "Running RePORTaLiN pipeline (without de-identification)..."
	$(PYTHON) main.py

run-deidentify:
	@echo "Running RePORTaLiN pipeline WITH de-identification (encrypted)..."
	@echo "Note: Encryption is enabled by default for security"
	$(PYTHON) main.py --enable-deidentification

run-deidentify-plain:
	@echo "WARNING: Running RePORTaLiN pipeline WITH de-identification (NO ENCRYPTION)"
	@echo "WARNING: Mapping files will be stored in plain text!"
	@echo "WARNING: This is NOT recommended for production use."
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	$(PYTHON) main.py --enable-deidentification --no-encryption

# Cleaning command
clean:
	@echo "Cleaning up Python cache files..."
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "[OK] Cache files cleaned"

clean-logs:
	@echo "Cleaning log files..."
	rm -rf .logs/
	@echo "[OK] Log files cleaned"

clean-results:
	@echo "WARNING: This will delete all generated results!"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	rm -rf results/
	@echo "[OK] Results cleaned"

clean-all: clean clean-logs
	@echo "WARNING: This will delete cache, logs, and results!"
	@printf "Press Enter to continue or Ctrl+C to cancel..." && read confirm
	rm -rf results/
	@echo "[OK] All generated files cleaned"

# Testing command
test:
	@echo "Running tests..."
	@if [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Skipping tests."; \
	fi

# Documentation commands
docs:
	@echo "Building Sphinx documentation..."
	cd docs/sphinx && $(MAKE) html
	@echo "[OK] Documentation built at docs/sphinx/_build/html/index.html"

docs-open: docs
	@echo "Opening documentation in browser..."
	open docs/sphinx/_build/html/index.html || xdg-open docs/sphinx/_build/html/index.html || echo "Please manually open docs/sphinx/_build/html/index.html"
