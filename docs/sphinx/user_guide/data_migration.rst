Data Migration Guide
====================

.. currentmodule:: scripts.utils.migrate_data_structure

This guide explains how to migrate your data directory structure from the legacy format 
to the new v0.3.0 standardized format using RePORTaLiN's automated migration system.

Overview
--------

The data migration system helps you transform legacy data directories into a standardized, 
multi-study structure. It's designed to be **automated**, **efficient**, and **smart**.

**What Gets Migrated:**

- 📄 Annotated PDF files (CRFs, forms)
- 📊 Dataset files (Excel, CSV)
- 📋 Data dictionaries and mapping specifications

**Key Features:**

- ✅ **Smart Detection**: Automatically skips if data is already in v0.3.0 format
- ✅ **Efficient**: Moves files (not copies) to save disk space and time
- ✅ **Validation**: Pre and post-migration integrity checks
- ✅ **Audit Trail**: Comprehensive logging of all operations
- ✅ **Preview Mode**: Dry-run capability to test before migrating

.. warning::
   **Version 2.0.0 File Handling:**
   
   - 📂 **Default path** (data/): Files MOVED within project, old structure deleted after confirmation
   - 📂 **Custom path**: Files COPIED to project's data/, originals preserved at source
   - 🧹 **Cleanup (Custom path)**: Two-step process (both optional):
     
     1. Remove old structure from project's data/ (if exists)
     2. Remove newly copied study folder from project's data/
   
   - 🧹 **Cleanup (Default path)**: Single-step (remove old structure after move)
   - ⚠️ **No automatic backups** - Custom paths preserve originals; default paths require manual backup
   
   This design provides maximum flexibility and safety for all migration scenarios.

Why Migrate?
------------

The new directory structure provides:

1. **Multi-Study Support**: Organize data from multiple studies in one place
2. **Standardization**: Consistent naming and organization across projects
3. **Clarity**: Clear separation of datasets, documents, and mappings
4. **Scalability**: Easy to add new studies without reorganizing
5. **Efficiency**: Automatic detection of already-migrated data

Understanding the Structure Change
-----------------------------------

Old Structure (Legacy)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   data/
   ├── Annotated_PDFs/
   │   └── Annotated CRFs - Indo-VAP/
   │       ├── 1A Index Case Screening v1.0.pdf
   │       ├── 2A Index- Baseline v1.0.pdf
   │       └── ... (more PDFs)
   ├── dataset/
   │   └── Indo-vap_csv_files/
   │       ├── 1A_ICScreening.xlsx
   │       ├── 2A_ICBaseline.xlsx
   │       └── ... (more datasets)
   └── data_dictionary_and_mapping_specifications/
       └── RePORT_DEB_to_Tables_mapping.xlsx

**Issues with old structure:**

- Study name buried in subdirectories
- Inconsistent naming conventions
- Hard to add multiple studies
- Difficult to locate specific file types

New Structure (Standardized)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionchanged:: 0.3.0
   Folder names changed to lowercase with underscores: ``datasets/``, ``annotated_pdfs/``, ``data_dictionary/``

.. code-block:: text

   data/
   └── Indo-VAP/                    # Study name at top level
       ├── annotated_pdfs/          # Annotated PDF files (lowercase with underscore)
       │   ├── 1A Index Case Screening v1.0.pdf
       │   ├── 2A Index- Baseline v1.0.pdf
       │   └── ... (more PDFs)
       ├── datasets/                # Dataset files (lowercase)
       │   ├── 1A_ICScreening.xlsx
       │   ├── 2A_ICBaseline.xlsx
       │   └── ... (more datasets)
       └── data_dictionary/         # Data dictionary and mappings (lowercase with underscore)
           └── RePORT_DEB_to_Tables_mapping.xlsx

**Benefits of new structure:**

- ✅ Study name is immediately visible at top level
- ✅ Consistent lowercase naming with underscores
- ✅ Easy to add more studies (e.g., ``data/Study-B/``)
- ✅ Clear file categorization
- ✅ Compatible with ``config.py`` constants (``DATASETS_DIR``, ``ANNOTATED_PDFS_DIR``, ``DATA_DICTIONARY_DIR``)

Prerequisites
-------------

Before You Begin
~~~~~~~~~~~~~~~~

1. **Understand File Handling**:
   
   .. important::
      - **Default path** (data/): Files are MOVED within project (internal reorganization)
      - **Custom path**: Files are COPIED from source to project's data/ folder (originals preserved at source)
   
2. **Create External Backup** (for default path):
   
   If using default data path, create a backup before migration:

   .. code-block:: bash

      # Create backup (REQUIRED for default path only)
      cp -r data data_backup_$(date +%Y%m%d)
      
      # Or use tar for compression
      tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
   
3. **Custom Path Users**:
   
   If migrating from a custom path, files will be copied to the project's data/ folder while your originals remain at the source.
   
   **Two-Step Cleanup (Both Optional)**:
   
   After migration, you'll be asked:
   
   - **Step 1**: Remove old structure from project's data/ (if exists)
   - **Step 2**: Remove newly copied study folder from project's data/
   
   You can decline either or both steps to keep the data in project's data/ folder.
   
   .. code-block:: bash
   
      # Custom path: Files copied to project's data/, originals stay at /custom/path
      python3 migrate.py --data-dir /custom/path
      
      # After migration, you'll be prompted for cleanup options

4. **Check Disk Space**:
   
   Disk space requirements:
   
   - **Default path**: Minimal extra space (files moved within project data/)
   - **Custom path**: Need space in project's data/ directory for copied files

   .. code-block:: bash

      # Check data directory size
      du -sh data/
      
      # Check available disk space
      df -h .

5. **Close All Files**:
   
   Make sure no Excel files or PDFs from the data directory are open.

6. **Review Current Structure**:
   
   Familiarize yourself with your current directory structure:

   .. code-block:: bash

      # View directory tree
      tree data/ -L 2

Migration Workflow
------------------

The migration follows a smart, multi-step process:

.. mermaid::

   graph TD
       A[Start] --> B{Already in v0.3.0 Format?}
       B -->|Yes| C[Skip Migration - Exit]
       B -->|No| D[Validate Old Structure]
       D --> E{Structure Valid?}
       E -->|No| F[Error: Fix Structure]
       E -->|Yes| G[Create New Directories]
       G --> H[Move Files]
       H --> I[Validate Migration]
       I --> J{All Files Moved?}
       J -->|No| K[Error: Check Logs]
       J -->|Yes| L[Remove Empty Old Dirs]
       L --> M[Generate Migration Log]
       M --> N[Success!]

Step 1: Dry-Run (Testing)
--------------------------

**Always start with a dry-run** to preview what will happen without making actual changes.

Using Python
~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Initialize in dry-run mode
   manager = DataMigrationManager(dry_run=True)
   
   # Check if already migrated
   if manager.is_already_migrated():
       print("✅ Data is already in v0.3.0 format - no migration needed!")
   else:
       # Run simulation
       manager.migrate()
       
       # Review output
       print(f"Would migrate {len(manager.migration_log)} operations")
       print(f"Study name: {manager.study_name}")

Using Command Line
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run dry-run
   python3 migrate.py --dry-run

**Expected Output (Already Migrated):**

.. code-block:: text

   ════════════════════════════════════════════════
   Starting Data Structure Migration
   ════════════════════════════════════════════════
   🔍 DRY RUN MODE - No actual changes will be made
   
   ════════════════════════════════════════════════
   ✅ Data is already in v0.3.0 format!
   ════════════════════════════════════════════════
   No migration needed. Exiting.

**Expected Output (Needs Migration):**

.. code-block:: text

   🔍 DRY RUN MODE - No actual changes will be made
   ════════════════════════════════════════════════
   
   Study name detected: Indo-VAP
   
   Migration mappings:
     dataset/Indo-vap_csv_files → Indo-VAP/datasets
     Annotated_PDFs/Annotated CRFs - Indo-VAP → Indo-VAP/annotated_pdfs
     data_dictionary_and_mapping_specifications → Indo-VAP/data_dictionary
   
   Would move 73 files:
     - 28 PDF files
     - 43 Excel/CSV files
     - 2 data dictionary files
   
   ✅ Dry-run completed successfully!

Step 2: Run Actual Migration
-----------------------------

File Handling Modes
~~~~~~~~~~~~~~~~~~~

The migration script automatically detects your data path and chooses the appropriate file handling:

+------------------+------------------+-------------------------+---------------------------+
| Data Path        | File Operation   | Original Files          | Destination               |
+==================+==================+=========================+===========================+
| Default (data/)  | **MOVE**         | ❌ Deleted              | Within project data/      |
+------------------+------------------+-------------------------+---------------------------+
| Custom path      | **COPY**         | ✅ Preserved at source  | Project's data/ folder    |
+------------------+------------------+-------------------------+---------------------------+

**For Default Path Users:**

.. danger::
   **IMPORTANT: CREATE EXTERNAL BACKUP FIRST!**
   
   Files will be MOVED within project's data/ folder (originals deleted). Create backup BEFORE running:
   
   .. code-block:: bash
   
      cp -r data data_backup_$(date +%Y%m%d)

**For Custom Path Users:**

.. tip::
   Your original files are automatically preserved at the source location.
   Files will be copied to the project's data/ folder.
   No backup needed!

Using Python
~~~~~~~~~~~~

.. code-block:: python

   from scripts.utils.migrate_data_structure import DataMigrationManager
   
   # Default path: Files will be MOVED within project's data/
   manager = DataMigrationManager()
   
   # Custom path: Files will be COPIED to project's data/ (originals preserved at source)
   # manager = DataMigrationManager(data_dir="/path/to/custom/data")
   
   # Check if already migrated
   if manager.is_already_migrated():
       print("✅ Already in v0.3.0 format - no migration needed!")
   else:
       # Run migration
       success = manager.migrate()
       
       if success:
           print("✅ Migration completed successfully!")
           if manager.is_custom_path:
               print(f"Original files preserved at: {manager.source_dir}")
               print(f"Migrated files copied to: {manager.dest_dir}")
       else:
           print("❌ Migration failed. Check logs for details.")

Using Command Line
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Default path: Files will be MOVED within project's data/
   python3 migrate.py
   
   # Custom path: Files will be COPIED from source to project's data/
   python3 migrate.py --data-dir /path/to/custom/data

**Expected Output (Default Path):**

.. code-block:: text

   ════════════════════════════════════════════════
   Starting Data Structure Migration
   ════════════════════════════════════════════════
   📂 Default path mode: Files will be MOVED within project's data/
   
   [1/6] Checking if already migrated...
   Old structure detected. Proceeding with migration.
   
   [2/6] Validating old structure...
   ✅ Found 73 files to migrate
   
   [3/6] Creating new directory structure...
   ✅ Created: data/Indo-VAP/annotated_pdfs
   ✅ Created: data/Indo-VAP/datasets
   ✅ Created: data/Indo-VAP/data_dictionary
   
   [4/6] Moving files...
   Progress: [████████████████████] 73/73 (100%)
   
   [5/6] Validating migration...
   ✅ All 73 files moved successfully
   
   Remove old directory structure? (yes/no): yes
   
   Cleaning up old directories...
   ✓ Removed: data/dataset/Indo-vap_csv_files
   ✓ Removed: data/Annotated_PDFs/Annotated CRFs - Indo-VAP
   ✓ Removed: data/data_dictionary_and_mapping_specifications
   
   [6/6] Generating migration log...
   ✅ Log saved: data/migration_log.txt
   
   ════════════════════════════════════════════════
   ✅ Migration Complete!
   ════════════════════════════════════════════════
   Files processed: 73
   Files failed: 0
   📁 Old structure: DELETED (cleaned up)
   📁 New structure: data/Indo-VAP/ (only this remains)
   ════════════════════════════════════════════════
   Migration log: data/migration_log.txt
   System log: logs/migrate_data_structure_20251203_134948.log

**Expected Output (Custom Path):**

.. code-block:: text

   ════════════════════════════════════════════════
   Starting Data Structure Migration
   ════════════════════════════════════════════════
   📂 Custom path mode: Files will be COPIED to project's data/ folder
   📂 Source: /custom/path (preserved, never altered)
   📂 Destination: /project/data/
   
   [1/6] Checking if already migrated...
   Old structure detected. Proceeding with migration.
   
   [2/6] Validating old structure...
   ✅ Found 73 files to migrate from /custom/path
   
   [3/6] Creating new directory structure...
   ✅ Created: /project/data/Indo-VAP/annotated_pdfs
   ✅ Created: /project/data/Indo-VAP/datasets
   ✅ Created: /project/data/Indo-VAP/data_dictionary
   
   [4/6] Copying files from /custom/path to /project/data/...
   Progress: [████████████████████] 73/73 (100%)
   
   [5/6] Validating migration...
   ✅ All 73 files copied successfully to project's data/
   
   ✅ Custom path: Original files NEVER altered
      Source remains unchanged: /custom/path
   
   [6/6] Generating migration log...
   ✅ Log saved: /project/data/migration_log.txt
   
   ════════════════════════════════════════════════
   ✅ Migration Complete!
   ════════════════════════════════════════════════
   Files processed: 73
   Files failed: 0
   📁 Original files: PRESERVED at /custom/path (never touched)
   📁 New structure: Created in /project/data/Indo-VAP/
   ════════════════════════════════════════════════
   
   ════════════════════════════════════════════════
   🧹 CLEANUP STEP 1: Old Directory Structure
   ════════════════════════════════════════════════
   Found old structure in project's data/ folder.
   (This is separate from your custom source path)
     - /project/data/dataset/Indo-vap_csv_files
     - /project/data/Annotated_PDFs/...
     - /project/data/data_dictionary_and_mapping_specifications
   ════════════════════════════════════════════════
   Remove old directory structure? (type 'yes' to confirm): yes
   
   ✅ Old structure cleanup complete
   
   ════════════════════════════════════════════════
   🧹 CLEANUP STEP 2: Newly Copied Study Folder
   ════════════════════════════════════════════════
   The following folder was copied from your custom path:
     - /project/data/Indo-VAP
   
   Your original data at '/custom/path' is untouched.
   ════════════════════════════════════════════════
   Remove copied study folder 'Indo-VAP' from project's data/? (type 'yes' to confirm): no
   
   ✅ Kept: /project/data/Indo-VAP

.. versionchanged:: 2.0.0
   Added smart file handling: MOVE for default path, COPY for custom paths.
   Custom paths preserve original files and offer two-step optional cleanup.

Command-Line Options
~~~~~~~~~~~~~~~~~~~~

The migration script supports the following command-line options:

.. code-block:: bash

   python3 migrate.py [OPTIONS]

**Options:**

.. option:: --dry-run

   Simulate migration without making actual changes. Useful for testing and 
   previewing what will happen.
   
   **Example:**
   
   .. code-block:: bash
   
      python3 migrate.py --dry-run

.. option:: --data-dir PATH

   Specify a custom data directory path. Useful when your data is not in the 
   default ``data/`` location.
   
   **Example:**
   
   .. code-block:: bash
   
      python3 migrate.py --data-dir /path/to/custom/data

**Combining Options:**

.. code-block:: bash

   # Test with custom data directory
   python3 migrate.py --dry-run --data-dir /custom/path
   
   # Migrate custom directory
   python3 migrate.py --data-dir /custom/path
   
   # Migrate default location (with confirmation)
   python3 migrate.py

.. versionremoved:: 2.0.0
   Removed ``--keep-backup`` option as backups are no longer created.

Best Practices
--------------

1. **Create External Backup** (default path only): Create backup before migrating default data path
2. **Always Dry-Run First**: Test with ``--dry-run`` before actual migration
3. **Understand Your Path Type**: Know whether you're using default or custom path
4. **Custom Path Benefits**: Use custom path to automatically preserve originals
5. **Review Logs**: Check migration logs after completion
6. **Verify Structure**: Check that all files are in new structure
7. **Document Changes**: Note migration dates and study names

Next Steps
----------

After successful migration:

1. ✅ Verify all files are in new structure
2. ✅ **Default path**: Verify backup before deleting it
3. ✅ **Custom path**: Original files remain at source (safe to use or archive)
4. ✅ Update any scripts that reference the old directory structure
5. ✅ Update documentation to reflect new structure
6. ✅ Inform team members about the new organization

See Also
--------

- :mod:`scripts.utils.migrate_data_structure` - API Reference
- :doc:`/developer_guide/migration_system` - Developer guide
- :doc:`/user_guide/troubleshooting` - General troubleshooting

FAQs
----

**Q: Does the migration create backups?**

A: No. However, custom paths automatically preserve original files at the source location.
   For default path, you must create external backups manually.

**Q: What's the difference between default and custom paths?**

A: 
   - **Default path** (data/): Files are MOVED (originals deleted, internal reorganization)
   - **Custom path**: Files are COPIED (originals preserved at source location)

**Q: How do I preserve my original files?**

A: Use a custom data path (``--data-dir /path``). Files will be copied and originals 
   preserved automatically.

**Q: Can I reverse the migration?**

A: 
   - **Default path**: Yes, if you created an external backup beforehand
   - **Custom path**: Yes! Original files are still at the source location

**Q: How long does migration take?**

A: 
   - **Default path**: Very fast (files moved, not copied) - seconds for most datasets
   - **Custom path**: Depends on file size (files copied) - may take longer

**Q: Can I migrate multiple studies at once?**

A: Currently, the migration runs per study. Run separately for each study's data directory.

**Q: Will migration affect my original files?**

A: 
   - **Default path**: Yes! Files are MOVED (originals deleted). Create backup first!
   - **Custom path**: No! Files are COPIED (originals preserved at source).

**Q: What if the script says "already in v0.3.0 format"?**

A: Your data is already migrated! No action needed. The script automatically detects and 
   skips migration if data is already in the new format.

**Q: What if I find issues after migration?**

A: 
   - **Default path**: Restore from your external backup
   - **Custom path**: Use the original files at the source location
   - Report issues to the development team before trying again.

**Q: Which approach should I use?**

A: 
   - **Default path**: For permanent migration of project data (internal reorganization)
   - **Custom path**: For migrating external data while keeping originals intact
