#!/usr/bin/env python3
"""
Data Migration Wrapper Script
==============================

Convenient wrapper for running the data migration utility.

Usage:
    python3 migrate.py                    # Default path: moves files
    python3 migrate.py --dry-run          # Simulate migration
    python3 migrate.py --data-dir /path   # Custom path: copies files, preserves originals
    python3 migrate.py --help             # Show all options

Migration Behavior:
    - **Skips migration if data is already in v0.3.0 format**
    - **Default path** (data/): Files are moved (internal reorganization)
    - **Custom path**: Files are copied (originals preserved at source)
    - **No backups created** for custom paths (originals preserved)
    - Auto-detects study name from dataset structure
    - Validates all operations
    - Comprehensive logging

File Handling:
    - **Default path**: Files MOVED (originals deleted)
    - **Custom path**: Files COPIED (originals preserved)

This script simply calls the migration utility in scripts/utils/
with proper path handling.

Author: RePORTaLiN Team
Date: December 2025
Version: 2.0.0 (smart migration with custom path support)
"""

import sys
import os
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
