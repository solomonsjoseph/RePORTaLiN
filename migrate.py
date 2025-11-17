#!/usr/bin/env python3
"""Data migration wrapper script for v0.3.0 structure."""

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
