"""RePORTaLiN version information."""

import re

__version__: str = "0.9.1"

# Validate semantic versioning format (MAJOR.MINOR.PATCH)
if not re.match(r'^\d+\.\d+\.\d+$', __version__):
    raise ValueError(
        f"Invalid version format: {__version__}. "
        f"Must follow semantic versioning: MAJOR.MINOR.PATCH"
    )

# Auto-derive version tuple from version string to ensure consistency
__version_info__: tuple[int, int, int] = tuple(map(int, __version__.split('.')))

__all__ = ['__version__', '__version_info__']
