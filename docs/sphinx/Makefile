# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "Custom targets:"
	@echo "  user-mode     Build documentation for end users only (no dev/API docs)"
	@echo "  dev-mode      Build full documentation including developer and API reference"
	@echo ""

.PHONY: help Makefile user-mode dev-mode

# Build user-only documentation
user-mode:
	@echo "Building USER MODE documentation (excluding developer/API docs)..."
	@sed -i.bak 's/developer_mode = True/developer_mode = False/' conf.py
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@sed -i.bak 's/developer_mode = False/developer_mode = True/' conf.py
	@rm -f conf.py.bak
	@echo "User mode documentation built in $(BUILDDIR)/html/"

# Build full developer documentation
dev-mode:
	@echo "Building DEVELOPER MODE documentation (including dev/API docs)..."
	@sed -i.bak 's/developer_mode = False/developer_mode = True/' conf.py
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@rm -f conf.py.bak
	@echo "Developer mode documentation built in $(BUILDDIR)/html/"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
