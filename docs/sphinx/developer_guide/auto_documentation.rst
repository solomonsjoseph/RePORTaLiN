Sphinx Auto-Documentation Guide
=================================

**For Developers: Automated Documentation System**

This guide explains how Sphinx automatically generates documentation from your code
and how to enhance automation for "write code → instant docs" workflow.

**Last Updated:** October 23, 2025

Current Automation Status
--------------------------

✅ What's Already Automated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **API Documentation from Docstrings** (FULLY AUTOMATED)
   
   Sphinx `autodoc` automatically extracts:
   
   - Function signatures with type hints
   - Docstrings (Google/NumPy style)
   - Class hierarchies and inheritance
   - Module-level documentation
   - Return types and parameters
   
   **Example:**
   
   .. code-block:: python
   
      # In your code: config.py
      def normalize_dataset_name(folder_name: Optional[str]) -> str:
          """
          Normalize a dataset folder name by removing common suffixes.
          
          Args:
              folder_name: Dataset folder name to normalize
              
          Returns:
              Normalized dataset name without common suffixes
          """
          # ... implementation
   
   **Result:** Automatically appears in ``docs/sphinx/api/config.rst`` when you run ``make html``!

2. **Type Hints Rendering** (FULLY AUTOMATED)
   
   The ``sphinx-autodoc-typehints`` extension automatically renders:
   
   - Function parameters with types
   - Return type annotations
   - Variable type hints
   - Complex types (List, Dict, Optional, etc.)

3. **Version Tracking** (SEMI-AUTOMATED)
   
   Version is automatically pulled from ``__version__.py``:
   
   .. code-block:: python
   
      # docs/sphinx/conf.py
      from __version__ import __version__
      version: str = __version__
      release: str = __version__

4. **Cross-References** (AUTOMATED)
   
   Sphinx automatically creates links between:
   
   - Function references
   - Class references  
   - Module references
   - External library docs (via intersphinx)

❌ What's Still Manual
~~~~~~~~~~~~~~~~~~~~~~~

1. **User Guides** - Manual writing required
   
   - Tutorials and how-tos
   - Conceptual explanations
   - Examples and workflows

2. **Developer Guides** - Manual writing required
   
   - Architecture decisions
   - Design patterns
   - Best practices

3. **Changelog** - Manual updates required
   
   - Version history
   - Breaking changes
   - Migration guides

How It Works
------------

The Autodoc Pipeline
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. You write code with docstrings
      ↓
   2. Sphinx autodoc reads Python source
      ↓
   3. Extracts docstrings, signatures, types
      ↓
   4. Generates .rst documentation
      ↓
   5. Builds HTML automatically

**Example Flow:**

.. code-block:: python

   # Step 1: Write code (config.py)
   def ensure_directories() -> None:
       """Create all required output directories.
       
       This function creates:
       - RESULTS_DIR
       - CLEAN_DATASET_DIR  
       - DICTIONARY_JSON_OUTPUT_DIR
       
       Raises:
           OSError: If directory creation fails
       """
       os.makedirs(RESULTS_DIR, exist_ok=True)
       # ...

.. code-block:: bash

   # Step 2: Run Sphinx build
   cd docs/sphinx && make html
   
   # Step 3: Documentation is automatically generated! ✅

Current Setup
-------------

Sphinx Extensions Enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # docs/sphinx/conf.py
   extensions = [
       'sphinx.ext.autodoc',          # Auto-generate from docstrings ✅
       'sphinx.ext.viewcode',         # Link to source code ✅
       'sphinx.ext.intersphinx',      # Link to external docs ✅
       'sphinx.ext.napoleon',         # Google/NumPy docstrings ✅
       'sphinx_autodoc_typehints',    # Render type hints ✅
   ]

Auto-Documentation Files
~~~~~~~~~~~~~~~~~~~~~~~~~

These files use ``automodule`` directive to auto-generate content:

.. code-block:: text

   docs/sphinx/api/
   ├── modules.rst                 # Auto-generated module index
   ├── config.rst                  # Auto-docs for config.py
   ├── main.rst                    # Auto-docs for main.py
   ├── scripts.rst                 # Auto-docs for scripts package
   ├── scripts.deidentify.rst      # Auto-docs for deidentify.py
   ├── scripts.extract_data.rst    # Auto-docs for extract_data.py
   ├── scripts.load_dictionary.rst # Auto-docs for load_dictionary.py
   └── scripts.utils.*.rst         # Auto-docs for utils modules

Each uses:

.. code-block:: rst

   .. automodule:: config
      :members:
      :undoc-members:
      :show-inheritance:

Enhancing Automation
---------------------

🚀 Level 1: Watch Mode (AVAILABLE NOW)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Auto-rebuild documentation when files change:

.. code-block:: bash

   # Install sphinx-autobuild
   pip install sphinx-autobuild
   
   # Run in watch mode
   cd docs/sphinx
   sphinx-autobuild . _build/html
   
   # Opens browser, auto-refreshes on code changes! ✨

**Makefile target (add this):**

.. code-block:: makefile

   .PHONY: docs-watch
   docs-watch:
       @cd docs/sphinx && sphinx-autobuild . _build/html --open-browser

Then just:

.. code-block:: bash

   make docs-watch

Now whenever you save a Python file with docstrings, the docs rebuild automatically!

🚀 Level 2: Git Hook Integration (RECOMMENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Automatically rebuild docs when you commit code changes:

**Create `.git/hooks/post-commit`:**

.. code-block:: bash

   #!/bin/bash
   # Auto-rebuild documentation after code commits
   
   echo "🔧 Rebuilding documentation..."
   cd docs/sphinx
   make html
   echo "✅ Documentation updated!"

.. code-block:: bash

   chmod +x .git/hooks/post-commit

Now docs rebuild every time you commit! ✨

🚀 Level 3: CI/CD Auto-Deploy (PRODUCTION)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Automatically build and deploy docs on every push:

**GitHub Actions Example (.github/workflows/docs.yml):**

.. code-block:: yaml

   name: Build and Deploy Docs
   
   on:
     push:
       branches: [main]
   
   jobs:
     build-docs:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.13'
         
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install sphinx sphinx_rtd_theme
         
         - name: Build documentation
           run: |
             cd docs/sphinx
             make html
         
         - name: Deploy to GitHub Pages
           uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: docs/sphinx/_build/html

**Result:** Push code → Docs auto-build → Deploy to web! 🌐

🚀 Level 4: Docstring Quality Checks (AUTOMATION)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure docstrings exist and are properly formatted:

**pydocstyle check:**

.. code-block:: bash

   # Install pydocstyle
   pip install pydocstyle
   
   # Check docstring quality
   pydocstyle scripts/

**Add to pre-commit hook:**

.. code-block:: bash

   #!/bin/bash
   # .git/hooks/pre-commit
   
   echo "Checking docstrings..."
   pydocstyle scripts/ || {
       echo "❌ Docstring issues found!"
       exit 1
   }
   echo "✅ Docstrings OK"

🚀 Level 5: Auto-Generate Changelog (ADVANCED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Auto-generate changelog from commit messages:

**Install conventional-changelog:**

.. code-block:: bash

   npm install -g conventional-changelog-cli
   
   # Generate changelog
   conventional-changelog -p angular -i CHANGELOG.md -s

**Or use Python:**

.. code-block:: bash

   pip install gitchangelog
   gitchangelog > docs/sphinx/changelog.rst

Best Practices for Auto-Documentation
--------------------------------------

Write Good Docstrings
~~~~~~~~~~~~~~~~~~~~~~

**Use Google or NumPy style consistently:**

.. code-block:: python

   def process_data(input_file: str, options: Dict[str, Any]) -> pd.DataFrame:
       """Process input data file with specified options.
       
       This function reads an Excel file and applies various transformations
       based on the provided options dictionary.
       
       Args:
           input_file: Path to input Excel file
           options: Dictionary of processing options with keys:
               - 'validate': bool - Enable validation
               - 'clean': bool - Remove empty rows
               
       Returns:
           Processed DataFrame with cleaned data
           
       Raises:
           FileNotFoundError: If input file doesn't exist
           ValueError: If options are invalid
           
       Example:
           >>> df = process_data('data.xlsx', {'validate': True})
           >>> len(df)
           100
           
       Note:
           This function modifies data in-place. Make a copy if needed.
           
       See Also:
           validate_data: Validation function used internally
       """
       # ... implementation

Use Type Hints Everywhere
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import Optional, List, Dict, Any
   
   def get_dataset_folder() -> Optional[str]:
       """Get the first dataset folder."""
       # Type hint automatically appears in docs!

Add Module-Level Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   """
   Data Extraction Module
   ======================
   
   This module provides functions for extracting data from Excel files
   and converting to JSONL format.
   
   Key Functions:
       - extract_excel_to_jsonl: Main extraction function
       - process_excel_file: Single file processor
       - clean_record_for_json: Data cleaning
   
   Example:
       >>> from scripts.extract_data import extract_excel_to_jsonl
       >>> extract_excel_to_jsonl(input_dir, output_dir)
   """

Use Explicit __all__ Exports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   __all__ = [
       'extract_excel_to_jsonl',
       'process_excel_file',
       'clean_record_for_json',
   ]

Only these appear in ``from module import *`` and are prioritized in docs.

Current Workflow
----------------

Immediate Auto-Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Right now, you can already do this:

.. code-block:: bash

   # 1. Write code with docstrings
   vim config.py
   
   # 2. Build docs (reads your code automatically)
   cd docs/sphinx && make html
   
   # 3. View updated docs
   open _build/html/api/config.html

**Your docstrings → Instant API docs!** ✅

Recommended Workflow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Terminal 1: Watch mode
   make docs-watch
   
   # Terminal 2: Write code
   vim scripts/deidentify.py
   # Add/update docstrings
   # Save file
   
   # → Browser automatically refreshes with new docs! ✨

Implementation Checklist
------------------------

Quick Wins (Do Now)
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ☐ Install sphinx-autobuild
   ☐ Add docs-watch target to Makefile
   ☐ Create post-commit git hook
   ☐ Document the workflow for team

Medium Term
~~~~~~~~~~~

.. code-block:: text

   ☐ Set up GitHub Actions for auto-deploy
   ☐ Add pydocstyle to pre-commit hooks
   ☐ Create docstring templates/snippets
   ☐ Add coverage reports for documentation

Long Term
~~~~~~~~~

.. code-block:: text

   ☐ Auto-generate changelog from commits
   ☐ Set up Read the Docs hosting
   ☐ Add API diff detection for breaking changes
   ☐ Implement version-specific documentation

Summary
-------

**You Already Have:**

✅ Auto-documentation from docstrings (``autodoc``)  
✅ Type hints rendering (``sphinx-autodoc-typehints``)  
✅ Cross-references and linking  
✅ Multiple output formats (HTML, PDF)

**You Can Add:**

🚀 Watch mode for instant rebuilds  
🚀 Git hooks for automatic updates  
🚀 CI/CD for automatic deployment  
🚀 Quality checks for docstrings  
🚀 Automated changelog generation

**The Goal:**

.. code-block:: text

   Write code → Save file → Docs update automatically ✨

With `sphinx-autobuild` in watch mode, **you're already 90% there!**

Related Documentation
---------------------

- :doc:`documentation_style_guide` - Documentation standards
- :doc:`contributing` - Contribution guidelines
- :doc:`script_reorganization` - Project organization

External Resources
------------------

- `Sphinx Documentation <https://www.sphinx-doc.org/>`_
- `sphinx-autobuild <https://github.com/executablebooks/sphinx-autobuild>`_
- `Google Style Guide <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_
- `Read the Docs <https://readthedocs.org/>`_

---

**TL;DR:** Yes! Sphinx already auto-generates API docs from your code. Install ``sphinx-autobuild`` for instant updates while you code! 🚀
