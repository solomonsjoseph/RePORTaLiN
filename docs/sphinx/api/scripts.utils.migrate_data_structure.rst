scripts.utils.migrate\_data\_structure module
=============================================

.. currentmodule:: scripts.utils.migrate_data_structure

The **migrate_data_structure** module provides a robust, production-ready system for 
safely migrating data directory structures with automatic backup, validation, and 
comprehensive logging.

**Key Features:**

- ✅ **Dynamic Study Name Detection**: Automatically detects study names from dataset folders
- ✅ **Intelligent Directory Mapping**: Maps old structure to standardized new structure
- ✅ **Automatic Backup**: Creates timestamped backups before migration
- ✅ **Dry-Run Mode**: Test migrations without making actual changes
- ✅ **Comprehensive Validation**: Pre and post-migration validation
- ✅ **Centralized Logging**: Detailed logs for audit trails
- ✅ **Progress Tracking**: Real-time migration progress reporting

Overview
--------

This module is designed to transform legacy data directory structures into a standardized 
format that supports multi-study organization. It follows a safe, multi-step workflow:

1. **Validate** current structure
2. **Create backup** with timestamp
3. **Create** new directory structure
4. **Move files** with integrity tracking
5. **Validate** migration results
6. **Generate** migration log

Workflow Analogy
~~~~~~~~~~~~~~~~

Think of this migration system like moving to a new house:

- **Backup** = Take photos and inventory of your old house
- **Dry-run** = Plan the move without actually packing
- **Migration** = Carefully move each item to the new house
- **Validation** = Check that everything arrived safely
- **Logs** = Keep a detailed moving record for insurance

Module Contents
---------------

Functions
~~~~~~~~~

.. autofunction:: extract_study_name

Classes
~~~~~~~

.. autoclass:: DataMigrationManager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Main Function
~~~~~~~~~~~~~

.. autofunction:: main

Usage Examples
--------------

Basic Migration (Interactive)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the migration script interactively with automatic study name detection:

.. code-block:: python

   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Initialize migration manager
   manager = DataMigrationManager(dry_run=False)
   
   # Run migration
   success = manager.run_migration()
   
   if success:
       print("✅ Migration completed successfully!")
   else:
       print("❌ Migration failed. Check logs for details.")

Dry-Run Mode (Testing)
~~~~~~~~~~~~~~~~~~~~~~~

Test the migration without making actual changes:

.. code-block:: python

   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Initialize in dry-run mode
   manager = DataMigrationManager(dry_run=True)
   
   # Simulate migration
   manager.run_migration()
   
   # Review what would happen without actual changes
   print(f"Would migrate {len(manager.migration_log)} files")

Custom Data Directory
~~~~~~~~~~~~~~~~~~~~~

Specify a custom data directory path:

.. code-block:: python

   from pathlib import Path
   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Custom data directory
   custom_dir = Path("/path/to/custom/data")
   
   # Initialize with custom path
   manager = DataMigrationManager(data_dir=custom_dir, dry_run=False)
   
   # Run migration
   manager.run_migration()

Study Name Extraction
~~~~~~~~~~~~~~~~~~~~~

Extract study name from dataset folder structure:

.. code-block:: python

   from pathlib import Path
   from scripts.utils.migrate_data_structure import extract_study_name
   
   data_dir = Path("data")
   study_name = extract_study_name(data_dir)
   
   print(f"Detected study: {study_name}")
   # Output: "Detected study: Indo-VAP"

Command-Line Usage
~~~~~~~~~~~~~~~~~~

Run migration from the command line:

.. code-block:: bash

   # Dry-run (test mode)
   python -m scripts.utils.migrate_data_structure --dry-run
   
   # Actual migration
   python -m scripts.utils.migrate_data_structure

Directory Structure Mapping
----------------------------

The migration maps old directory structures to a standardized format:

**Before Migration:**

.. code-block:: text

   data/
   ├── Annotated_PDFs/
   │   └── Annotated CRFs - Indo-VAP/
   │       └── *.pdf
   ├── dataset/
   │   └── Indo-vap_csv_files/
   │       └── *.xlsx
   └── data_dictionary_and_mapping_specifications/
       └── *.xlsx

**After Migration:**

.. code-block:: text

   data/
   └── Indo-VAP/
       ├── Annotated_PDFs/
       │   └── *.pdf
       ├── dataset/
       │   └── *.xlsx
       └── mapping/
           └── *.xlsx

Migration Log Format
--------------------

The migration creates two types of logs:

**1. System Log** (`.logs/migrate_data_structure_*.log`):

.. code-block:: text

   2025-11-03 13:49:48,501 - migrate_data_structure - INFO - Migration Manager initialized
   2025-11-03 13:49:48,501 - migrate_data_structure - INFO - Study name determined: Indo-VAP
   2025-11-03 13:49:48,501 - migrate_data_structure - INFO - Built 3 migration mappings
   2025-11-03 13:49:48,720 - migrate_data_structure - INFO - ✅ Migration complete: 73 files moved

**2. Migration Log** (`data/migration_log.txt`):

.. code-block:: text

   Migration completed at: 2025-11-03 13:49:48
   Total files moved: 73
   Files failed: 0
   
   Moved: Annotated_PDFs/Annotated CRFs - Indo-VAP/1A Index Case Screening v1.0.pdf
   Moved: dataset/Indo-vap_csv_files/1A_ICScreening.xlsx
   Moved: data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx

Error Handling
--------------

The migration system includes comprehensive error handling:

**Pre-Migration Validation Errors:**

- Missing data directory
- No old structure found
- Empty directories

**Migration Errors:**

- File permission issues
- Disk space problems
- Path conflicts

**Post-Migration Validation Errors:**

- File count mismatch
- Missing files
- Incomplete migration

All errors are logged to both system logs and displayed to the user with actionable guidance.

Configuration
-------------

The migration system uses configuration from :mod:`config`:

- **DATA_DIR**: Base data directory path (default: ``./data``)
- **LOG_LEVEL**: Logging level (default: ``INFO``)

See Also
--------

- :mod:`scripts.utils.logging` - Centralized logging system
- :mod:`config` - Project configuration
- :doc:`/user_guide/data_migration` - User guide for data migration
- :doc:`/developer_guide/migration_system` - Developer guide for migration architecture

Notes
-----

.. note::
   Always run with ``--dry-run`` first to preview changes before actual migration.

.. warning::
   Ensure sufficient disk space for backup creation (approximately 2x data size).

.. tip::
   The migration creates automatic backups, so your original data is always safe.

Version History
---------------

- **v1.0.0** (November 2025): Initial release with production-ready migration system

API Reference
-------------

.. automodule:: scripts.utils.migrate_data_structure
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
