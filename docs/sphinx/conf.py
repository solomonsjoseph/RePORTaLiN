"""Sphinx documentation configuration for RePORTaLiN."""
import os
import sys
from typing import Dict, List, Tuple, Any

# Add the project root to the Python path for autodoc
sys.path.insert(0, os.path.abspath('../..'))

# Import version from single source of truth
from __version__ import __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project: str = 'RePORTaLiN'
copyright: str = '2025, RePORTaLiN Development Team'
author: str = 'RePORTaLiN Development Team'

# Version imported from __version__.py (single source of truth)
version: str = __version__
release: str = __version__

# RST prolog for automatic version substitution in all .rst files
# This allows using |version| and |release| anywhere in documentation
# and they will automatically update when __version__.py changes
rst_prolog: str = f"""
.. |version| replace:: {version}
.. |release| replace:: {release}
"""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions: List[str] = [
    'sphinx.ext.autodoc',          # Auto-generate docs from docstrings
    'sphinx.ext.viewcode',         # Add links to source code
    'sphinx.ext.intersphinx',      # Link to other project docs
    'sphinx.ext.napoleon',         # Support for Google/NumPy docstrings
    'sphinx_autodoc_typehints',    # Render type hints in docs
]

# Napoleon settings for Google and NumPy style docstrings
napoleon_google_docstring: bool = True
napoleon_numpy_docstring: bool = True
napoleon_include_init_with_doc: bool = True

# Developer mode - controls inclusion of API documentation
# Can be overridden by DEVELOPER_MODE environment variable
# Set to False for user-only documentation (hides developer_guide/ and api/)
developer_mode: bool = os.environ.get('DEVELOPER_MODE', 'True').lower() in ('true', '1', 'yes')

templates_path: List[str] = ['_templates']
exclude_patterns: List[str] = ['_build', 'Thumbs.db', '.DS_Store']

# Conditionally exclude developer content when developer_mode is False
if not developer_mode:
    exclude_patterns.extend([
        'developer_guide/*',
        'api/*',
    ])

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme: str = 'sphinx_rtd_theme'
html_static_path: List[str] = ['_static']

html_theme_options: Dict[str, Any] = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
}

# Add custom context for templates
html_context: Dict[str, bool] = {
    'developer_mode': developer_mode,
}

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping: Dict[str, Tuple[str, None]] = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}
