Migration System Architecture
==============================

.. currentmodule:: scripts.utils.migrate_data_structure

This guide provides a deep dive into the migration system's architecture, design decisions, 
and implementation details for developers who want to understand, maintain, or extend 
the migration functionality.

System Overview
---------------

The migration system is designed as a **safe**, **auditable**, and **intelligent** data 
transformation pipeline that converts legacy directory structures into a standardized format.

**Core Design Principles:**

1. **Safety First**: Never lose data (custom paths preserve originals, default paths require backup)
2. **Auditability**: Comprehensive logging of all operations
3. **Intelligence**: Auto-detects path type and chooses optimal file handling
4. **Idempotency**: Safe to run multiple times (auto-detects if already migrated)
5. **Testability**: Dry-run mode for testing
6. **Clarity**: Clear error messages and progress feedback

**File Handling Modes:**

- **Default Path** (data/): Files MOVED within project (internal reorganization)
  - Old structure folders deleted after migration
  - Only data/Study-Name/ remains
  - Requires external backup before migration

- **Custom Path**: Files COPIED from source to project's data/
  - Originals preserved at source location (never altered)
  - New structure created in project's data/
  - No backup needed (originals preserved automatically)

Architecture Diagram
--------------------

.. mermaid::

   graph TB
       subgraph "Entry Points"
           A[Command Line]
           B[Python API]
       end
       
       subgraph "Core Components"
           C[DataMigrationManager]
           D[extract_study_name]
       end
       
       subgraph "Operations"
           E[validate_current_structure]
           F[create_backup]
           G[create_new_structure]
           H[move_files]
           I[validate_migration]
           J[write_migration_log]
       end
       
       subgraph "External Dependencies"
           K[config.DATA_DIR]
           L[scripts.utils.logging]
           M[pathlib.Path]
       end
       
       A --> C
       B --> C
       C --> D
       C --> E
       C --> F
       C --> G
       C --> H
       C --> I
       C --> J
       C --> K
       C --> L
       E --> M
       F --> M
       G --> M
       H --> M

Component Details
-----------------

DataMigrationManager Class
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Orchestrates the entire migration workflow.

**Responsibilities**:

- Initialize migration configuration
- Coordinate all migration steps
- Track progress and state
- Handle errors gracefully
- Generate comprehensive logs

**Key Attributes**:

.. code-block:: python

   class DataMigrationManager:
       source_dir: Path           # Source data directory (custom path or project's data/)
       dest_dir: Path             # Destination directory (always project's data/)
       is_custom_path: bool       # True if using custom path, False if default
       dry_run: bool              # Simulation mode flag
       migration_log: List[str]   # Migration operation log
       study_name: str            # Detected or fallback study name
       old_to_new: Dict[str, str] # Directory mapping (source→destination)

**State Machine**:

.. code-block:: text

   [INIT] -> detect_path_type -> [PATH_DETECTED]
          -> check_if_migrated -> [MIGRATION_STATUS_KNOWN]
          -> validate -> [VALIDATED]
          -> create_structure -> [STRUCTURED]
          -> copy_or_move_files -> [MIGRATED]
          -> validate_migration -> [VERIFIED]
          -> cleanup_old_structure -> [CLEANED] (default path only)
          -> write_log -> [COMPLETE]

extract_study_name Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Intelligently detect study name from dataset folder structure.

**Algorithm**:

1. Look for ``dataset/`` subdirectory
2. Find first subdirectory within ``dataset/``
3. Extract study name from subdirectory name
4. Clean up common suffixes (``_csv_files``, ``_files``, etc.)
5. Apply fallback rules for generic names
6. Capitalize study name components

**Example Transformations**:

.. code-block:: python

   "Indo-vap_csv_files"     → "Indo-VAP"
   "Study-ABC_files"        → "Study-ABC"
   "data_files"             → "ext_data" (fallback)
   "csv_files"              → "ext_data" (fallback)
   "ReproNet-Kenya"         → "ReproNet-KENYA"

**Fallback Logic**:

.. code-block:: python

   generic_names = {
       'data', 'dataset', 'csv', 'files', 'excel', 
       'output', 'input', 'raw', 'processed'
   }
   
   if study_name in generic_names or len(study_name) < 2:
       return 'ext_data'  # Fallback to generic name

Migration Workflow Details
--------------------------

Step 0: Path Type Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Determine if using default or custom data path.

**Detection Logic**:

.. code-block:: python

   def __init__(self, data_dir: Optional[Path] = None, dry_run: bool = False):
       # Detect path type
       default_data_dir = Path(__file__).parent.parent.parent / "data"
       
       if data_dir is None:
           # Using default path
           self.source_dir = default_data_dir
           self.dest_dir = default_data_dir
           self.is_custom_path = False
       else:
           # Using custom path
           self.source_dir = Path(data_dir).resolve()
           self.dest_dir = default_data_dir
           self.is_custom_path = True

**File Handling Based on Path Type**:

- **is_custom_path = False**: Files MOVED within project's data/ (shutil.move)
- **is_custom_path = True**: Files COPIED from source to project's data/ (shutil.copy2)

Step 1: Migration Status Check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Detect if data is already in v0.3.0 format to avoid redundant migration.

**Detection Logic**:

.. code-block:: python

   def is_already_migrated(self) -> bool:
       """Check if data is already in v0.3.0 format."""
       check_dir = self.dest_dir if self.is_custom_path else self.source_dir
       
       # Look for standardized structure
       for item in check_dir.iterdir():
           if item.is_dir():
               has_datasets = (item / "datasets").exists()
               has_annotated_pdfs = (item / "annotated_pdfs").exists()
               has_data_dict = (item / "data_dictionary").exists()
               
               if has_datasets or has_annotated_pdfs or has_data_dict:
                   return True  # Already migrated!
       
       return False  # Needs migration

Step 2: Validation (Pre-Migration)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Step 2: Validation (Pre-Migration)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Ensure source structure is valid for migration.

**Checks Performed**:

1. Source directory exists
2. At least one mapping path exists in source
3. Directories are not empty
4. New structure doesn't already exist in destination (prevents double migration)

**Code Path**:

.. code-block:: python

   def validate_current_structure(self) -> bool:
       # Check source directory
       if not self.source_dir.exists():
           logger.error(f"Source directory not found: {self.source_dir}")
           return False
       
       # Check for old structure in source
       old_paths = []
       for old_path in self.old_to_new.keys():
           full_path = self.source_dir / old_path
           if full_path.exists():
               old_paths.append(full_path)
       
       if not old_paths:
           logger.error("No old structure found to migrate")
           return False
       
       # Check if new structure already exists in destination
       new_study_dir = self.dest_dir / self.study_name
       if new_study_dir.exists():
           logger.error(f"New structure already exists: {new_study_dir}")
           return False
       
       return True

Step 3: New Structure Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Create new standardized directory structure in destination.

**Directory Creation**:

.. code-block:: python

   def create_new_structure(self) -> bool:
       for new_path in self.old_to_new.values():
           full_path = self.dest_dir / new_path
           
           if self.dry_run:
               logger.info(f"[DRY RUN] Would create: {full_path}")
           else:
               full_path.mkdir(parents=True, exist_ok=True)
               logger.info(f"✅ Created: {full_path}")
       
       return True

**Created Directories** (v0.3.0) in destination:

- ``{dest_dir}/{study_name}/annotated_pdfs/`` (lowercase with underscore)
- ``{dest_dir}/{study_name}/datasets/`` (lowercase)
- ``{dest_dir}/{study_name}/data_dictionary/`` (lowercase with underscore)

.. versionchanged:: 0.3.0
   Folder names changed to lowercase with underscores for consistency.

.. versionchanged:: 2.0.0
   Custom paths create structure in project's data/, not in source location.

Step 4: File Migration
~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Copy or move files from source to destination based on path type.

**Migration Algorithm**:

1. Iterate through each old→new mapping
2. Find all files recursively in source location
3. Calculate relative path within old structure
4. Compute new path in destination structure
5. Create parent directories if needed in destination
6. **Copy** file (custom path) or **Move** file (default path)
7. Log operation
8. Track progress

**Code Path**:

.. code-block:: python

   def move_files(self) -> bool:
       for old_path, new_path in self.old_to_new.items():
           old_full = self.source_dir / old_path
           new_full = self.dest_dir / new_path
           
           if not old_full.exists():
               continue
           
           # Find all files recursively in source
           for file_path in old_full.rglob('*'):
               if file_path.is_file():
                   # Calculate relative path
                   rel_path = file_path.relative_to(old_full)
                   
                   # Calculate new path in destination
                   new_file_path = new_full / rel_path
                   
                   if self.dry_run:
                       action = "copy" if self.is_custom_path else "move"
                       logger.info(f"[DRY RUN] Would {action}: {file_path} → {new_file_path}")
                   else:
                       new_file_path.parent.mkdir(parents=True, exist_ok=True)
                       
                       if self.is_custom_path:
                           # COPY for custom paths (preserve originals)
                           shutil.copy2(str(file_path), str(new_file_path))
                           logger.info(f"Copied: {rel_path}")
                       else:
                           # MOVE for default path (internal reorganization)
                           shutil.move(str(file_path), str(new_file_path))
                           logger.info(f"Moved: {rel_path}")
                   
                   self.migration_log.append(f"Migrated: {old_path}/{rel_path}")
       
       return True

**Key Differences**:

- **Custom Path**: Uses ``shutil.copy2()`` to preserve originals at source
- **Default Path**: Uses ``shutil.move()`` for efficient reorganization

**Progress Tracking**:

Progress is tracked via logging and can be extended with progress bars (e.g., tqdm).

Step 5: Post-Migration Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Verify migration completed successfully.

**Validation Checks**:

1. Count files in new structure (destination)
2. Compare with expected count from migration log
3. Verify new directories exist in destination
4. For custom paths: Verify original files still exist at source

**Code Path**:

.. code-block:: python

   def validate_migration(self) -> bool:
       if self.dry_run:
           return True
       
       # Count files in new structure (destination)
       new_study_dir = self.dest_dir / self.study_name
       if not new_study_dir.exists():
           logger.error("New structure not created in destination")
           return False
       
       migrated_count = len(list(new_study_dir.rglob('*.* ')))
       expected_count = len(self.migration_log)
       
       if migrated_count != expected_count:
           logger.error(f"File count mismatch: {migrated_count} vs {expected_count}")
           return False
       
       # For custom paths, verify originals still exist
       if self.is_custom_path:
           for old_path in self.old_to_new.keys():
               old_full = self.source_dir / old_path
               if old_full.exists() and any(old_full.rglob('*')):
                   logger.info(f"✅ Originals preserved at: {old_full}")
       
       logger.info(f"✅ Validated: {migrated_count} files migrated")
       return True

Step 6: Old Structure Cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2.0.0
.. versionchanged:: 2.0.0
   Custom paths now support two-step cleanup process.

**Purpose**: Remove old directory structure and optionally remove copied data.

**Cleanup Modes**:

- **Default path**: Single-step cleanup (remove old structure)
- **Custom path**: Two-step cleanup process (both optional)

**When It Runs**:

After successful migration and validation.

**Custom Path Two-Step Process**:

**Step 1: Remove Old Structure (if exists in project's data/)**

Prompts user to remove old structure folders from project's data directory:

- ``data/dataset/``
- ``data/Annotated_PDFs/``
- ``data/data_dictionary_and_mapping_specifications/``

User can decline to keep old structure alongside new structure.

**Step 2: Remove Newly Copied Study Folder**

Prompts user to remove the newly copied and organized study folder:

- ``data/Study-Name/`` (the folder just copied from custom source)

This allows users to:
- Keep the copied data in project for active use
- Remove it to keep project's data/ clean (originals preserved at source)
- Have full control over data retention strategy

**Code Path**:

.. code-block:: python

   def cleanup_old_structure(self) -> bool:
       """Remove old directory structure and optionally copied data."""
       
       # Step 1: Clean up old structure (both default and custom paths)
       old_structure_exists = any((self.dest_dir / old_path).exists() 
                                  for old_path in self.old_to_new.keys())
       
       if old_structure_exists:
           response = input("Remove old directory structure? (yes/no): ")
           if response.lower() == 'yes':
               # Remove old structure
               for old_path in self.old_to_new.keys():
                   full_path = self.dest_dir / old_path
                   if full_path.exists():
                       shutil.rmtree(full_path)
       
       # Step 2: For custom paths - ask to remove copied study folder
       if self.is_custom_path:
           study_dir = self.dest_dir / self.study_name
           if study_dir.exists():
               response = input(f"Remove copied study folder '{self.study_name}'? (yes/no): ")
               if response.lower() == 'yes':
                   shutil.rmtree(study_dir)
                   logger.info(f"Original data preserved at: {self.source_dir}")
       
       return True

**Possible Results**:

- **Default path** (confirmed cleanup): Only ``data/Study-Name/`` remains
- **Default path** (declined cleanup): Old structure and ``data/Study-Name/`` both exist
- **Custom path** (both steps confirmed): Project's data/ completely clean
- **Custom path** (step 1 only): Old structure removed, ``data/Study-Name/`` kept
- **Custom path** (step 2 only): Old structure kept, ``data/Study-Name/`` removed
- **Custom path** (both declined): Old structure and ``data/Study-Name/`` both kept
- **All scenarios**: Custom source location never touched

Step 7: Log Generation
~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Create permanent migration log file.

**Log Contents**:

- Timestamp
- Source and destination paths
- File handling mode (COPY vs MOVE)
- File counts (migrated, failed)
- List of all migrated files
- Original file disposition
- Error information (if any)

**Log Location**: 

- **Default path**: ``{project}/data/migration_log.txt``
- **Custom path**: ``{project}/data/migration_log.txt``

.. versionchanged:: 2.0.0
   Log always saved to project's data/, includes source/destination paths.
```
