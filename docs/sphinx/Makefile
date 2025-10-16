# Makefile for Sphinx Documentation
# ===================================
# Enhanced for cross-platform compatibility and robustness
#
# Features:
# - Cross-platform compatibility (macOS/Linux/BSD)
# - Environment variable-based mode switching (no file modification)
# - Enhanced error handling and validation
# - Browser detection for multiple platforms
# - Colored output for better readability

# Color output for better readability
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Check if sphinx-build is available
SPHINX_CHECK := $(shell command -v $(SPHINXBUILD) 2>/dev/null)

# Detect OS for platform-specific commands
UNAME_S := $(shell uname -s)

# Detect browser command
ifeq ($(UNAME_S),Darwin)
	BROWSER := open
else ifeq ($(UNAME_S),Linux)
	BROWSER := xdg-open
else
	BROWSER := echo "Please manually open:"
endif

# Put it first so that "make" without argument is like "make help".
help:
	@echo "$(CYAN)═══════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)      Sphinx Documentation Build System       $(NC)"
	@echo "$(CYAN)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Standard Targets:$(NC)"
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "$(GREEN)Custom Build Modes:$(NC)"
	@echo "  $(YELLOW)user-mode$(NC)     - Build documentation for end users only (no dev/API docs)"
	@echo "  $(YELLOW)dev-mode$(NC)      - Build full documentation including developer and API reference"
	@echo ""
	@echo "$(GREEN)Convenience Targets:$(NC)"
	@echo "  $(YELLOW)html-open$(NC)     - Build HTML documentation and open in browser"
	@echo "  $(YELLOW)watch$(NC)         - Auto-rebuild documentation on file changes (if sphinx-autobuild installed)"
	@echo "  $(YELLOW)check$(NC)         - Check for broken links and inconsistencies"
	@echo "  $(YELLOW)clean$(NC)         - Remove all build artifacts"
	@echo "  $(YELLOW)cleanall$(NC)      - Clean build artifacts and backups"
	@echo ""
	@echo "$(BLUE)Build directory:$(NC) $(BUILDDIR)"
	@echo "$(BLUE)Sphinx builder:$(NC) $(SPHINXBUILD)"
	@echo ""

.PHONY: help user-mode dev-mode clean cleanall html-open watch check check-sphinx

# Check if Sphinx is installed
check-sphinx:
	@if [ -z "$(SPHINX_CHECK)" ]; then \
		echo "$(RED)✗ Error: sphinx-build not found!$(NC)"; \
		echo "$(YELLOW)Install Sphinx with: pip install sphinx$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ Sphinx found: $(SPHINXBUILD)$(NC)"; \
	fi

# Build user-only documentation (using environment variable instead of file modification)
user-mode: check-sphinx
	@echo "$(BLUE)Building USER MODE documentation (excluding developer/API docs)...$(NC)"
	@if [ ! -f conf.py ]; then \
		echo "$(RED)✗ Error: conf.py not found!$(NC)"; \
		exit 1; \
	fi
	@DEVELOPER_MODE=False $(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "$(GREEN)✓ User mode documentation built successfully!$(NC)"
	@echo "$(CYAN)Output: $(BUILDDIR)/html/index.html$(NC)"

# Build full developer documentation (using environment variable)
dev-mode: check-sphinx
	@echo "$(BLUE)Building DEVELOPER MODE documentation (including dev/API docs)...$(NC)"
	@if [ ! -f conf.py ]; then \
		echo "$(RED)✗ Error: conf.py not found!$(NC)"; \
		exit 1; \
	fi
	@DEVELOPER_MODE=True $(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "$(GREEN)✓ Developer mode documentation built successfully!$(NC)"
	@echo "$(CYAN)Output: $(BUILDDIR)/html/index.html$(NC)"

# Build HTML and open in browser (cross-platform)
html-open: check-sphinx
	@echo "$(BLUE)Building HTML documentation...$(NC)"
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "$(GREEN)✓ Documentation built successfully!$(NC)"
	@echo "$(BLUE)Opening in browser...$(NC)"
	@$(BROWSER) $(BUILDDIR)/html/index.html 2>/dev/null || \
		echo "$(YELLOW)Please manually open: $(BUILDDIR)/html/index.html$(NC)"

# Auto-rebuild on file changes (requires sphinx-autobuild)
watch:
	@echo "$(BLUE)Starting auto-rebuild server...$(NC)"
	@if command -v sphinx-autobuild >/dev/null 2>&1; then \
		echo "$(GREEN)✓ sphinx-autobuild found$(NC)"; \
		echo "$(CYAN)Server will start at http://127.0.0.1:8000$(NC)"; \
		echo "$(YELLOW)Press Ctrl+C to stop$(NC)"; \
		sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O); \
	else \
		echo "$(RED)✗ sphinx-autobuild not found!$(NC)"; \
		echo "$(YELLOW)Install with: pip install sphinx-autobuild$(NC)"; \
		exit 1; \
	fi

# Check documentation for issues
check: check-sphinx
	@echo "$(BLUE)Checking documentation for issues...$(NC)"
	@echo "$(CYAN)Checking for broken links...$(NC)"
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O) || true
	@echo ""
	@echo "$(CYAN)Checking for syntax issues...$(NC)"
	@$(SPHINXBUILD) -b dummy -W --keep-going "$(SOURCEDIR)" "$(BUILDDIR)/dummy" $(SPHINXOPTS) $(O) || true
	@echo ""
	@echo "$(GREEN)✓ Documentation checks completed$(NC)"
	@echo "$(YELLOW)Check $(BUILDDIR)/linkcheck/output.txt for broken links$(NC)"

# Clean build artifacts
clean:
	@echo "$(BLUE)Cleaning documentation build artifacts...$(NC)"
	@rm -rf "$(BUILDDIR)"
	@echo "$(GREEN)✓ Build artifacts cleaned$(NC)"

# Clean everything including backups
cleanall:
	@echo "$(BLUE)Cleaning all documentation artifacts and backups...$(NC)"
	@rm -rf "$(BUILDDIR)"
	@rm -f conf.py.bak
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ All artifacts cleaned$(NC)"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%:
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
