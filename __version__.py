"""RePORTaLiN version information and semantic versioning management.

This module defines the canonical version string for the RePORTaLiN project and
provides automated validation to ensure strict adherence to semantic versioning
(SemVer) standards. The version is used throughout the project for:

- CLI `--version` output (see main.py)
- Package distribution metadata
- Documentation generation (Sphinx)
- API compatibility checks
- Release management and tagging

Semantic Versioning Philosophy:
    RePORTaLiN follows SemVer 2.0.0 (https://semver.org/):
    
    **MAJOR.MINOR.PATCH** format where:
    - MAJOR: Incompatible API changes (e.g., breaking configuration changes)
    - MINOR: Backward-compatible new features (e.g., new de-identification patterns)
    - PATCH: Backward-compatible bug fixes (e.g., regex pattern corrections)
    
    Examples:
        0.9.1 → 0.9.2  (bug fix)
        0.9.2 → 0.10.0 (new feature, backward-compatible)
        0.10.0 → 1.0.0 (breaking changes, production-ready API)

Auto-Derivation Mechanism:
    The module automatically derives `__version_info__` tuple from the 
    `__version__` string to prevent inconsistencies. This ensures there's
    a single source of truth for version information.

Validation:
    The module validates the version format at import time using a regex
    pattern. Invalid formats raise a ValueError immediately, preventing
    silent failures in downstream tools (pip, setuptools, sphinx).

Module Attributes:
    __version__ (str): The canonical version string in MAJOR.MINOR.PATCH format.
        This is the single source of truth for all version information.
    
    __version_info__ (tuple[int, int, int]): Auto-derived version tuple for
        programmatic comparison (e.g., `if __version_info__ >= (1, 0, 0)`).

Example:
    >>> # Access version string (for display)
    >>> from __version__ import __version__
    >>> print(__version__)
    0.9.1
    
    >>> # Access version tuple (for comparisons)
    >>> from __version__ import __version_info__
    >>> __version_info__
    (0, 9, 1)
    >>> __version_info__ >= (0, 9, 0)
    True
    >>> __version_info__ < (1, 0, 0)
    True
    
    >>> # Validation happens automatically at import
    >>> # Invalid version would raise ValueError:
    >>> # __version__ = "1.0"  # Missing PATCH - would fail validation

Raises:
    ValueError: Raised at import time if `__version__` does not match the
        required semantic versioning format (MAJOR.MINOR.PATCH). This ensures
        all version strings are valid before any code execution.

Notes:
    - This module has zero external dependencies (only stdlib `re`)
    - Version changes should be committed with corresponding Git tags
    - Use `git tag -a v0.9.1 -m "Release 0.9.1"` for releases
    - Sphinx multiversion builds rely on Git tags matching this format

See Also:
    main.py: Uses `__version__` for CLI `--version` output
    config.py: May reference version for compatibility checks
    https://semver.org/: Semantic Versioning specification
"""

import re

__version__: str = "0.9.1"
"""Canonical version string following semantic versioning (MAJOR.MINOR.PATCH).

This is the single source of truth for RePORTaLiN's version. Update this when
releasing new versions, then create a corresponding Git tag.
"""

# Validate semantic versioning format (MAJOR.MINOR.PATCH) at import time
# This regex ensures exactly three numeric components separated by periods
if not re.match(r'^\d+\.\d+\.\d+$', __version__):
    raise ValueError(
        f"Invalid version format: {__version__}. "
        f"Must follow semantic versioning: MAJOR.MINOR.PATCH"
    )

# Auto-derive version tuple from version string to ensure consistency
# This prevents manual tuple updates and guarantees single source of truth
__version_info__: tuple[int, int, int] = tuple(map(int, __version__.split('.')))
"""Auto-derived version tuple for programmatic comparisons.

Automatically parsed from `__version__` string to prevent inconsistencies.
Use this for version comparisons in code (e.g., feature flags based on version).

Example:
    >>> __version_info__ >= (0, 9, 0)
    True
"""

__all__ = ['__version__', '__version_info__']
