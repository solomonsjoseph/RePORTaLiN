# RePORTaLiN Sphinx Documentation

This directory contains the Sphinx documentation for the RePORTaLiN project.

## Quick Start

### Building the Documentation

1. **Install Sphinx and dependencies** (if not already installed):
```bash
pip install -r ../../requirements.txt
```

2. **Build HTML documentation**:
```bash
make html
```

3. **View the documentation**:
```bash
# macOS
open _build/html/index.html

# Linux
xdg-open _build/html/index.html

# Windows
start _build/html/index.html
```

## Available Documentation

### User Guide (`user_guide/`)
Documentation for end users of the RePORTaLiN system:

- **usage.rst**: Getting started and basic usage
- **deidentification.rst**: PHI/PII de-identification guide
- **country_regulations.rst**: Country-specific privacy compliance

### Developer Guide (`developer_guide/`)
Documentation for developers and maintainers:

- **architecture.rst**: System architecture and design
- **extending.rst**: How to extend the system (add countries, features)
- **testing.rst**: Testing strategies and best practices (if available)

### API Reference (`api/`)
Auto-generated API documentation from code docstrings.

## Build Commands

### HTML Output
```bash
make html          # Build HTML documentation
make clean         # Remove build artifacts
make html-clean    # Clean and rebuild
```

### Other Formats
```bash
make latexpdf      # Build PDF (requires LaTeX)
make epub          # Build EPUB
make man           # Build man pages
make text          # Build plain text
```

### Development
```bash
make livehtml      # Auto-rebuild on changes (requires sphinx-autobuild)
```

## Documentation Structure

```
docs/sphinx/
├── README.md              # This file
├── conf.py               # Sphinx configuration
├── index.rst             # Documentation home page
├── Makefile              # Build commands (Unix/macOS/Linux)
├── make.bat              # Build commands (Windows)
├── _build/               # Generated documentation (git-ignored)
│   └── html/            # HTML output
├── _static/              # Static files (CSS, images, etc.)
├── _templates/           # Custom templates
├── user_guide/          # User documentation
│   ├── index.rst
│   ├── usage.rst
│   ├── deidentification.rst
│   └── country_regulations.rst
├── developer_guide/     # Developer documentation
│   ├── index.rst
│   ├── architecture.rst
│   └── extending.rst
└── api/                 # API reference
    └── index.rst
```

## Configuration

### conf.py Settings

Key configuration in `conf.py`:

```python
# Project information
project = 'RePORTaLiN'
copyright = '2025, RePORTaLiN Development Team'
author = 'RePORTaLiN Development Team'

# Extensions
extensions = [
    'sphinx.ext.autodoc',      # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',     # Google/NumPy style docstrings
    'sphinx.ext.viewcode',     # Add source code links
    'sphinx.ext.intersphinx',  # Link to other projects
]

# Theme
html_theme = 'sphinx_rtd_theme'  # Read the Docs theme
```

## Writing Documentation

### reStructuredText (.rst) Basics

**Headings**:
```rst
Section Title
=============

Subsection Title
----------------

Subsubsection Title
~~~~~~~~~~~~~~~~~~~
```

**Code Blocks**:
```rst
.. code-block:: python

   def example():
       return "Hello"
```

**Lists**:
```rst
- Bullet item 1
- Bullet item 2

1. Numbered item 1
2. Numbered item 2
```

**Links**:
```rst
`Link text <https://example.com>`_
:doc:`Other document <user_guide/usage>`
:ref:`Section label <section-name>`
```

**Admonitions**:
```rst
.. note::
   This is a note.

.. warning::
   This is a warning.

.. seealso::
   See also this related topic.
```

## Automatic Documentation

### From Python Docstrings

Use the `automodule` directive to generate docs from code:

```rst
.. automodule:: scripts.utils.deidentify
   :members:
   :undoc-members:
   :show-inheritance:
```

### Docstring Format

Use Google-style or NumPy-style docstrings:

```python
def function_name(param1, param2):
    """Short description.

    Longer description with more details.

    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2

    Returns:
        bool: Description of return value

    Raises:
        ValueError: When invalid input

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Live Preview

For real-time documentation preview during development:

1. **Install sphinx-autobuild**:
```bash
pip install sphinx-autobuild
```

2. **Start live server**:
```bash
sphinx-autobuild . _build/html
```

3. **Open browser**: Navigate to `http://localhost:8000`

The documentation will automatically rebuild when you save changes.

## Troubleshooting

### Common Issues

**Issue**: `make: command not found` (Windows)
**Solution**: Use `make.bat` instead of `make`

**Issue**: Theme not found
**Solution**: Install theme: `pip install sphinx_rtd_theme`

**Issue**: Extension errors
**Solution**: Check `extensions` list in `conf.py` and install missing packages

**Issue**: Build warnings
**Solution**: Fix warnings by updating .rst files or docstrings

### Clean Rebuild

If you encounter build errors:

```bash
make clean
make html
```

## Publishing

### GitHub Pages

To publish to GitHub Pages:

1. Build documentation:
```bash
make html
```

2. Copy `_build/html/` to your GitHub Pages branch

3. Push to repository

### Read the Docs

To publish on Read the Docs:

1. Connect your GitHub repository to Read the Docs
2. Configure the build in your Read the Docs dashboard
3. Documentation builds automatically on push

## Contributing

When contributing documentation:

1. Follow existing structure and style
2. Use reStructuredText formatting
3. Include code examples
4. Add cross-references where appropriate
5. Test the build before submitting

## Resources

- **Sphinx Documentation**: https://www.sphinx-doc.org/
- **reStructuredText Primer**: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
- **Read the Docs Theme**: https://sphinx-rtd-theme.readthedocs.io/

---

**Last Updated**: October 13, 2025  
**Sphinx Version**: 7.0+  
**Theme**: Read the Docs
