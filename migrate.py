#!/usr/bin/env python3
"""Data migration wrapper script for RePORTaLiN directory structure.

This module serves as the command-line entry point for migrating existing
RePORTaLiN data from older directory structures to the standardized
layout. It acts as a thin wrapper around the actual migration logic in
`scripts.utils.migrate_data_structure`, providing proper path setup and
a user-friendly interface.

Migration Purpose:
    The current version introduced a new directory structure with explicit
    separation of original and cleaned datasets:
    
    **Old Structure:**
        output/{STUDY_NAME}/*.jsonl  # Mixed original and cleaned files
    
    **New Structure:**
        output/{STUDY_NAME}/original/*.jsonl  # Raw extraction output
        output/{STUDY_NAME}/cleaned/*.jsonl   # Validated/cleaned records
    
    This migration script automatically reorganizes files into the new
    structure without data loss, preserving all original files.

Why This Wrapper Exists:
    - **Path Setup**: Ensures the project root is in `sys.path` for imports
    - **User Experience**: Provides clear banner and progress feedback
    - **Isolation**: Separates CLI concerns from core migration logic
    - **Testability**: Core logic in migrate_data_structure.py can be tested
      independently of CLI wrapper

Usage:
    Run from project root:
        $ python migrate.py
    
    Or make executable and run directly:
        $ chmod +x migrate.py
        $ ./migrate.py
    
    The script will:
        1. Display migration banner and project root
        2. Detect existing data structure
        3. Create new directory structure (original/, cleaned/)
        4. Move files to appropriate directories
        5. Provide summary of migration results

Example:
    >>> # This script is meant to be run from command line, not imported
    >>> # Conceptual example of what happens when executed:
    >>> # $ python migrate.py
    >>> # ============================================================
    >>> # RePORTaLiN Data Structure Migration
    >>> # ============================================================
    >>> # Project Root: /path/to/RePORTaLiN
    >>> # ============================================================
    >>> # 
    >>> # Migrating output/Indo-VAP/...
    >>> # ✓ Created output/Indo-VAP/original/
    >>> # ✓ Created output/Indo-VAP/cleaned/
    >>> # ✓ Moved 50 files successfully

Notes:
    - Safe to run multiple times (idempotent operation)
    - Does not delete original files unless explicitly configured
    - See scripts.utils.migrate_data_structure for core logic
    - Only modifies output/ directory, never touches data/ directory
    - Creates backup before migration (configurable)

See Also:
    scripts.utils.migrate_data_structure: Core migration implementation
    config.py: Directory structure configuration
"""

import sys
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Add project root to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import and run the migration script
from scripts.utils.migrate_data_structure import main

if __name__ == "__main__":
    print("="*60)
    print("RePORTaLiN Data Structure Migration")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print("="*60)
    print()
    
    # Run the migration
    main()
