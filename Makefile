# Makefile for RePORTaLiN Project
# Simplified for production use

.PHONY: help install clean run run-deidentify run-deidentify-plain docs docs-open

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
	@echo "  make clean        - Remove Python cache files"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Build Sphinx HTML documentation"
	@echo "  make docs-open    - Build docs and open in browser"
	@echo ""
	@echo "Direct commands you can also use:"
	@echo "  python main.py                              - Run pipeline (no de-identification)"
	@echo "  python main.py --enable-deidentification    - Run with de-identification (encrypted)"
	@echo "  python main.py --enable-deidentification --no-encryption  - Run with de-identification (plain text)"
	@echo "  cd docs/sphinx && make html                 - Build docs"
	@echo ""

# Setup commands
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Running commands
run:
	@echo "Running RePORTaLiN pipeline (without de-identification)..."
	python main.py

run-deidentify:
	@echo "Running RePORTaLiN pipeline WITH de-identification (encrypted)..."
	@echo "Note: Encryption is enabled by default for security"
	python main.py --enable-deidentification

run-deidentify-plain:
	@echo "⚠️  Running RePORTaLiN pipeline WITH de-identification (NO ENCRYPTION)"
	@echo "⚠️  WARNING: Mapping files will be stored in plain text!"
	@echo "⚠️  This is NOT recommended for production use."
	@read -p "Press Enter to continue or Ctrl+C to cancel..." confirm
	python main.py --enable-deidentification --no-encryption

# Cleaning command
clean:
	@echo "Cleaning up Python cache files..."
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✓ Cache files cleaned"

# Documentation commands
docs:
	@echo "Building Sphinx documentation..."
	cd docs/sphinx && $(MAKE) html
	@echo "✓ Documentation built at docs/sphinx/_build/html/index.html"

docs-open: docs
	@echo "Opening documentation in browser..."
	open docs/sphinx/_build/html/index.html || xdg-open docs/sphinx/_build/html/index.html || echo "Please manually open docs/sphinx/_build/html/index.html"
