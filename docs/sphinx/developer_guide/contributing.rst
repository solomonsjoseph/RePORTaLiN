Contributing
============

**For Developers: Contributing to RePORTaLiN**

We welcome contributions to RePORTaLiN! This guide will help you get started with development,
testing, and submitting your improvements.

**Current Version: |version|** (October 28, 2025)

**Project Status:**

✅ **Complete data extraction and transformation pipeline**  
✅ **De-identification with encryption and multi-country compliance**  
✅ **Comprehensive documentation** (user guides, developer guides, API reference)  
✅ **Production-ready codebase** with robust error handling and type safety  
✅ **68% code reduction** while maintaining 100% functionality

For detailed version history and feature additions, see :doc:`../changelog`.

Getting Started
---------------

1. **Fork the Repository**

   Visit the GitHub repository and click "Fork"

2. **Clone Your Fork**

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/RePORTaLiN.git
      cd RePORTaLiN

3. **Set Up Development Environment**

   .. code-block:: bash

      # Create virtual environment
      python -m venv .venv
      source .venv/bin/activate  # On Windows: .venv\Scripts\activate
      
      # Install dependencies
      pip install -r requirements.txt

4. **Create a Branch**

   .. code-block:: bash

      git checkout -b feature/your-feature-name

Version Management
------------------

.. versionadded:: 0.2.0
   Hybrid version management system with automatic semantic versioning via conventional commits.

RePORTaLiN uses a **hybrid version management system** that combines:

- **Single source of truth**: ``__version__.py`` 
- **Automatic bumping**: Post-commit hook for VS Code/GUI workflows
- **Manual control**: Makefile targets and CLI scripts when needed

How Version Bumping Works
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Automatic (Recommended for Most Users)**:

When you commit with a conventional commit message, the version is automatically bumped:

.. code-block:: bash

   # From VS Code or command line - just commit normally!
   git add .
   git commit -m "feat: add new feature"
   # → Post-commit hook detects "feat:" and bumps 0.2.0 → 0.3.0
   # → Amends commit to include __version__.py change

**Version Bump Rules**:

+-------------------------+------------------+-------------------------+
| Commit Type             | Version Bump     | Example                 |
+=========================+==================+=========================+
| ``fix:``                | Patch            | 0.2.0 → 0.2.1           |
+-------------------------+------------------+-------------------------+
| ``feat:``               | Minor            | 0.2.0 → 0.3.0           |
+-------------------------+------------------+-------------------------+
| ``feat!:`` or           | Major            | 0.2.0 → 1.0.0           |
| ``BREAKING CHANGE:``    |                  |                         |
+-------------------------+------------------+-------------------------+
| ``docs:``, ``chore:``,  | No bump          | 0.2.0 → 0.2.0           |
| ``refactor:``, etc.     |                  |                         |
+-------------------------+------------------+-------------------------+

**Manual Version Bumping**:

When you need explicit control (e.g., for releases):

.. code-block:: bash

   # Bump patch version (0.2.0 → 0.2.1)
   make bump-patch
   git commit -m "chore: bump version to 0.2.1"
   
   # Bump minor version (0.2.0 → 0.3.0)
   make bump-minor
   git commit -m "chore: bump version to 0.3.0"
   
   # Bump major version (0.2.0 → 1.0.0)
   make bump-major
   git commit -m "chore: bump version to 1.0.0"

**Smart Commit (Preview Before Committing)**:

Use ``smart-commit`` when you want to see the version change before committing:

.. code-block:: bash

   # Preview version bump
   ./scripts/utils/smart-commit "feat: add new feature"
   # Shows: Current: 0.2.0 → New: 0.3.0
   # Asks for confirmation before committing

**Check Current Version**:

.. code-block:: bash

   # Quick version check
   make show-version
   # or
   python main.py --version

Version Import Pattern
~~~~~~~~~~~~~~~~~~~~~~

All modules import version from ``__version__.py``:

.. code-block:: python

   # Correct: Import from __version__.py
   from __version__ import __version__
   
   # Then use in your module
   __version__ = __version__  # Re-export at module level

This ensures version consistency across:

- CLI output (``--version`` flag)
- Module ``__version__`` attributes  
- Sphinx documentation (``docs/sphinx/conf.py``)
- Package metadata

**Never hardcode versions** in module files - always import from ``__version__.py``.

Development Workflow
--------------------

Making Changes
~~~~~~~~~~~~~~

1. Make your changes in your feature branch
2. Follow the :ref:`coding-standards` below
3. Add or update tests as needed
4. Update documentation if needed
5. Ensure all tests pass

.. code-block:: bash

   # Run tests (if available)
   make test
   
   # Clean build artifacts
   make clean
   
   # Test the pipeline
   python main.py

Commit Guidelines
~~~~~~~~~~~~~~~~~

.. versionchanged:: 0.2.0
   RePORTaLiN now uses **Conventional Commits** with automatic semantic versioning.
   Version bumps are handled automatically via post-commit hook.

Use **Conventional Commits** for automatic semantic versioning:

.. code-block:: text

   # Patch bump (0.2.0 → 0.2.1) - Bug fixes
   ✅ fix: correct date conversion bug in extract_data.py
   ✅ fix(deidentify): handle missing PHI patterns gracefully

   # Minor bump (0.2.0 → 0.3.0) - New features
   ✅ feat: add CSV output format support
   ✅ feat(cli): add --verbose flag for DEBUG logging

   # Major bump (0.2.0 → 1.0.0) - Breaking changes
   ✅ feat!: redesign configuration file structure
   ✅ feat: remove deprecated --legacy-mode flag
   
   BREAKING CHANGE: Configuration now uses YAML instead of JSON

   # No version bump - Documentation, refactoring, etc.
   ✅ docs: update README with new examples
   ✅ refactor: simplify table detection algorithm
   ✅ chore: update dependencies

**Conventional Commit Format**:

.. code-block:: text

   <type>[optional scope][optional !]: <description>

   [optional body]

   [optional footer(s)]

**Commit Types**:

- ``feat:``: New feature (→ **Minor bump**)
- ``fix:``: Bug fix (→ **Patch bump**)
- ``feat!:`` or ``BREAKING CHANGE:``: Breaking change (→ **Major bump**)
- ``docs:``: Documentation only (no version bump)
- ``style:``: Code style/formatting (no version bump)
- ``refactor:``: Code refactoring (no version bump)
- ``test:``: Add/update tests (no version bump)
- ``chore:``: Maintenance tasks (no version bump)

**How It Works**:

1. Commit normally from VS Code or CLI with conventional commit message
2. Post-commit hook automatically detects commit type
3. Version bumped in ``__version__.py`` based on commit type
4. Commit is amended to include version change
5. Final commit contains both your changes AND version bump

**Examples**:

.. code-block:: bash

   # Option 1: VS Code (recommended)
   # Just commit normally - version bumps automatically!
   git add .
   git commit -m "feat: add CSV export"  # → Auto-bumps to 0.3.0
   
   # Option 2: CLI with preview (smart-commit)
   ./scripts/utils/smart-commit "feat: add CSV export"  # Shows version before commit
   
   # Option 3: Manual version bump
   make bump-minor  # Bump minor version manually
   git commit -m "chore: bump version"

**Good Examples**:

.. code-block:: text

   ✅ feat: add support for CSV output format
   ✅ fix: correct date parsing in extract_data.py
   ✅ docs: update configuration documentation
   ✅ feat(deidentify): add encryption support
   ✅ fix(cli)!: change --output flag to --output-dir
   
   BREAKING CHANGE: --output flag renamed for clarity

**Bad Examples**:

.. code-block:: text

   ❌ Update (too vague, no type)
   ❌ Fix bug (no description, no type)
   ❌ Changes (meaningless)
   ❌ Added feature (wrong tense, no type)

.. _coding-standards:

Coding Standards
----------------

Python Style
~~~~~~~~~~~~

Follow PEP 8 guidelines:

- Use 4 spaces for indentation
- Max line length: 100 characters (flexible for readability)
- Use descriptive variable names
- Add docstrings to all public functions

Example:

.. code-block:: python

   def process_data(input_file: str, output_dir: str) -> dict:
       """
       Process a single data file.
       
       Args:
           input_file: Path to input Excel file
           output_dir: Directory for output JSONL file
       
       Returns:
           Dictionary with processing results
       
       Raises:
           FileNotFoundError: If input_file doesn't exist
       """
       # Implementation here
       pass

Documentation
~~~~~~~~~~~~~

Use Google-style docstrings:

.. code-block:: python

   def my_function(param1: str, param2: int = 0) -> bool:
       """
       Brief description of function.
       
       Longer description with more details about what the function
       does and why it exists.
       
       Args:
           param1 (str): Description of param1
           param2 (int, optional): Description of param2. Defaults to 0.
       
       Returns:
           bool: Description of return value
       
       Raises:
           ValueError: When param1 is empty
           TypeError: When param2 is negative
       
       Example:
           >>> result = my_function("test", 5)
           >>> print(result)
           True
       
       Note:
           Any important notes about usage
       
       See Also:
           :func:`related_function`: Related functionality
       """
       pass

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.3.0
   Added ``make docs-watch`` for auto-rebuild on file changes.

The project uses Sphinx for documentation with autodoc enabled. Documentation is automatically
extracted from Python docstrings when you build the docs.

**Build Commands**:

.. code-block:: bash

   # Build HTML documentation (manual)
   make docs

   # Build and open in browser
   make docs-open

   # Auto-rebuild on file changes (requires sphinx-autobuild)
   make docs-watch

**Auto-Rebuild Workflow** (Recommended for documentation development):

1. Install ``sphinx-autobuild`` (already in requirements.txt):

   .. code-block:: bash

      pip install -r requirements.txt

2. Start the auto-rebuild server:

   .. code-block:: bash

      make docs-watch

3. Open http://127.0.0.1:8000 in your browser

4. Edit any ``.rst`` file or Python docstring - changes appear automatically!

**What Gets Auto-Generated**:

- All Python module documentation (via ``.. automodule::`` directives)
- Function signatures with type hints
- Class hierarchies and methods
- Cross-references between modules

**Best Practices**:

- Always update docstrings when changing function signatures
- Run ``make docs`` before committing to catch documentation errors
- Use auto-rebuild during development for instant feedback
- Check that autodoc picks up your changes correctly

**Note**: Documentation does NOT rebuild automatically on every code change by default.
You must explicitly run ``make docs`` or use ``make docs-watch`` for auto-rebuild.

Code Organization
~~~~~~~~~~~~~~~~~

- One class/major function per file (for large implementations)
- Related utility functions can be grouped
- Keep functions focused (single responsibility)
- Limit function length (prefer < 50 lines)

Example structure:

.. code-block:: python

   # module.py
   """
   Module docstring explaining purpose.
   """
   
   import standard_library
   import third_party
   import local_modules
   
   # Constants
   MAX_RETRIES = 3
   DEFAULT_TIMEOUT = 30
   
   # Main functions
   def public_function():
       """Public API function."""
       pass
   
   def _private_helper():
       """Private helper function."""
       pass

Error Handling
~~~~~~~~~~~~~~

.. versionchanged:: 0.3.0
   Logging module now uses specific exceptions (``ValueError``) instead of generic ``Exception``.

.. versionchanged:: 0.3.0
   De-identification module demonstrates robust error handling with 9 try/except blocks for 
   cryptography imports, country regulations, pattern loading, mapping I/O, and file processing.

Use appropriate exception handling:

.. code-block:: python

   # Good: Specific exception handling
   try:
       data = read_file(path)
   except FileNotFoundError:
       log.error(f"File not found: {path}")
       raise
   except PermissionError:
       log.error(f"Permission denied: {path}")
       raise

**Best Practices for Error Handling**:

1. **Optional Dependency Handling**:

   .. code-block:: python
   
      # From deidentify.py - handling optional cryptography
      try:
          from cryptography.fernet import Fernet
          CRYPTO_AVAILABLE = True
      except ImportError:
          CRYPTO_AVAILABLE = False
          logging.warning("cryptography package not available. Encryption disabled.")
   
   This pattern allows graceful degradation when optional dependencies are missing.

2. **File I/O Error Handling**:

   .. code-block:: python
   
      # From deidentify.py - mapping storage
      try:
          with open(self.storage_path, 'rb') as f:
              data = f.read()
          # Process data...
      except FileNotFoundError:
          # Expected on first run
          return
      except Exception as e:
          logging.error(f"Failed to load mappings: {e}")
          self.mappings = {}

3. **Batch Processing with Granular Error Handling**:

   .. code-block:: python
   
      # From deidentify.py - dataset processing
      for jsonl_file in files:
          try:
              # Process file...
              files_processed += 1
          except FileNotFoundError:
              files_failed += 1
              tqdm.write(f"✗ File not found: {jsonl_file}")
          except json.JSONDecodeError as e:
              files_failed += 1
              tqdm.write(f"✗ JSON error: {str(e)}")
          except Exception as e:
              files_failed += 1
              tqdm.write(f"✗ Error: {str(e)}")
   
   This ensures one file's error doesn't stop the entire batch.

4. **Re-raising After Logging**:

   .. code-block:: python
   
      # Critical errors should be re-raised after logging
      try:
          self.storage_path.parent.mkdir(parents=True, exist_ok=True)
          # Save data...
      except Exception as e:
          logging.error(f"Failed to save mappings: {e}")
          raise  # Re-raise to signal failure to caller

Public API Definition
~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.3.0
   All utility modules now define explicit public APIs using ``__all__``.

Define ``__all__`` to explicitly declare your module's public API:

.. code-block:: python

   # At the top of your module (after imports)
   __all__ = [
       # Enums
       'MyEnum',
       # Data Classes
       'MyDataClass',
       # Classes
       'MyMainClass',
       'MyHelperClass',
       # Functions
       'my_public_function',
       'validate_data',
   ]

**Benefits:**

- Prevents accidental exposure of internal implementation
- Improves IDE autocomplete and import suggestions
- Makes API surface explicit and maintainable
- Helps with API versioning and deprecation

**Example from De-identification Module**:

.. code-block:: python

   __all__ = [
       # Enums
       'PHIType',
       # Data Classes
       'DetectionPattern',
       'DeidentificationConfig',
       # Core Classes
       'PatternLibrary',
       'PseudonymGenerator',
       'DateShifter',
       'MappingStore',
       'DeidentificationEngine',
       # Top-level Functions
       'deidentify_dataset',
       'validate_dataset',
   ]

Return Type Annotations
~~~~~~~~~~~~~~~~~~~~~~~

.. versionchanged:: 0.3.0
   All functions now include explicit return type annotations, including ``-> None`` for 
   functions that don't return values.

Always include return type annotations:

.. code-block:: python

   # Good: Explicit return types
   def process_data(data: Dict[str, Any]) -> List[str]:
       """Process data and return results."""
       return []
   
   def save_results(path: Path, data: Dict) -> None:
       """Save results to file. Returns nothing."""
       with open(path, 'w') as f:
           json.dump(data, f)
   
   # Avoid: Missing return type
   def unclear_function(x):  # What does this return?
       pass
