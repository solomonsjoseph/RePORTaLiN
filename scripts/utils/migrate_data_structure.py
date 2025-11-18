#!/usr/bin/env python3
"""Data structure migration utility for RePORTaLiN v0.3.0 organization.

Automates migration from legacy flat directory structure to v0.3.0's study-based
organization with intelligent study name detection and dual-mode file handling.

**Migration Overview:**

This utility performs comprehensive data structure migration with:

1. **Intelligent Study Detection**: Auto-detects study name from dataset folder
   names with fallback logic for generic names (e.g., "dataset" → "ext_data").

2. **Dual-Mode Operation**:
   - **Custom Path Mode**: Copies files FROM external source TO project data/
     (preserves originals at source)
   - **Default Path Mode**: Reorganizes files WITHIN project data/ directory
     (moves files, deletes originals)

3. **Safe Migration Workflow**:
   - Pre-migration validation (checks existing structure)
   - Dry-run mode for testing without changes
   - Post-migration validation (verifies file counts)
   - Optional cleanup with user confirmation
   - Migration log generation for audit trail

**Old Structure (Pre-v0.3.0):**
```
data/
├── dataset/
│   └── Indo-VAP_csv_files/  # Study-specific folder
│       ├── 1A_ICScreening.xlsx
│       └── ...
├── Annotated_PDFs/
│   └── annotated_pdfs/      # PDFs folder
│       ├── 1A Index Case Screening v1.0.pdf
│       └── ...
└── data_dictionary_and_mapping_specifications/
    └── RePORT_DEB_to_Tables_mapping.xlsx
```

**New Structure (v0.3.0):**
```
data/
└── Indo-VAP/                # Detected study name
    ├── datasets/            # Standardized folder names
    │   ├── 1A_ICScreening.xlsx
    │   └── ...
    ├── annotated_pdfs/
    │   ├── 1A Index Case Screening v1.0.pdf
    │   └── ...
    └── data_dictionary/
        └── RePORT_DEB_to_Tables_mapping.xlsx
```

**Study Name Detection Algorithm:**

1. Scans `data/dataset/` for first subdirectory
2. Removes common suffixes (_csv_files, _files, _data, _dataset, _excel)
3. Capitalizes parts after hyphens (Indo-vap → Indo-VAP)
4. Falls back to 'ext_data' for generic names (dataset, data, files)
5. Falls back to 'ext_data' if no subdirectory found

**Migration Modes:**

**Custom Path Mode** (--data-dir=/external/path):
- Copies files FROM external source TO project data/
- Preserves originals at source location
- Creates new study folder in project data/
- Use case: Importing data from external drive/network share

**Default Path Mode** (no --data-dir):
- Reorganizes files WITHIN project data/ directory
- Moves files (deletes originals after copy)
- Use case: Upgrading existing project data structure

**Safety Features:**

- Dry-run mode (--dry-run) for testing without changes
- Pre-migration validation checks structure exists
- Detects if already migrated (skips redundant work)
- User confirmation prompts for destructive operations
- Optional cleanup with separate confirmation
- Comprehensive migration log file
- Error tracking with continue/abort options

**Usage Examples:**

Test migration without changes:
    >>> # From command line:
    >>> # python3 migrate_data_structure.py --dry-run

Import from external source (preserves originals):
    >>> # python3 migrate_data_structure.py --data-dir=/Volumes/ExternalDrive/data

Reorganize existing data (moves files):
    >>> # python3 migrate_data_structure.py

Programmatic usage:
    >>> from pathlib import Path
    >>> from scripts.utils.migrate_data_structure import DataMigrationManager
    >>> manager = DataMigrationManager(data_dir=Path('/custom/path'), dry_run=True)
    >>> success = manager.migrate()  # doctest: +SKIP
    >>> if success:  # doctest: +SKIP
    ...     print(f"Migrated to {manager.study_name}/ structure")

**Exit Codes:**
- 0: Migration successful
- 1: Migration failed or user cancelled

**Dependencies:**
- config module for default DATA_DIR
- scripts.utils.logging_system for comprehensive logging
- Standard library: argparse, os, shutil, sys, pathlib, datetime

**Warning:**
Default path mode MOVES files (deletes originals). Ensure external backups
exist before running. Custom path mode is safer as it preserves originals.

**Note:**
Migration is idempotent - detects if already migrated and skips redundant work.
Safe to run multiple times.

See Also:
    config.py: DATA_DIR configuration and study detection
    main.py: Uses migrated data structure for pipeline execution
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Fix sys.path to avoid local logging.py shadowing standard logging
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_script_dir))

# Remove script directory from path temporarily to import standard logging
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

# Now import standard logging
# Add root directory for imports
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import config
from scripts.utils import logging_system as log

# Setup enhanced logger
log.setup_logging(
    module_name="scripts.utils.migrate_data_structure",
    log_level="INFO"
)


def extract_study_name(data_dir: Path) -> str:
    """Extract study name from dataset folder with intelligent fallback logic.
    
    Implements multi-stage study name detection algorithm:
    
    1. **Locate Dataset**: Scans data_dir/dataset/ for subdirectories
    2. **Extract Name**: Uses first subdirectory name as base
    3. **Clean Suffixes**: Removes common suffixes (_csv_files, _files, _data, etc.)
    4. **Capitalize**: Capitalizes parts after hyphens (indo-vap → Indo-VAP)
    5. **Validate**: Checks length (>=2 chars) and rejects generic names
    6. **Fallback**: Returns 'ext_data' if detection fails or name is generic
    
    This ensures consistent, meaningful study identifiers for the v0.3.0
    directory structure while handling edge cases gracefully.
    
    Args:
        data_dir: Path to data directory containing dataset/ subdirectory.
            Expected structure: data_dir/dataset/StudyName_csv_files/
    
    Returns:
        Detected study name (cleaned and capitalized) or 'ext_data' fallback.
        Examples: "Indo-VAP", "TB-TRIAL", "ext_data"
    
    Side Effects:
        - Logs warnings if dataset directory not found or empty
        - Logs info for detected folder and extracted study name
    
    Example:
        >>> from pathlib import Path
        >>> # Case 1: Well-formed study name
        >>> data_dir = Path('/path/to/data')
        >>> # Assume dataset/Indo-VAP_csv_files/ exists
        >>> name = extract_study_name(data_dir)  # doctest: +SKIP
        >>> print(name)  # doctest: +SKIP
        'Indo-VAP'
        
        >>> # Case 2: Generic name triggers fallback
        >>> # Assume dataset/dataset/ exists (generic)
        >>> name = extract_study_name(data_dir)  # doctest: +SKIP
        >>> print(name)  # doctest: +SKIP
        'ext_data'
        
        >>> # Case 3: Missing dataset directory
        >>> empty_dir = Path('/tmp/empty')
        >>> name = extract_study_name(empty_dir)  # doctest: +SKIP
        >>> print(name)  # doctest: +SKIP
        'ext_data'
    
    Note:
        Generic names that trigger fallback: 'dataset', 'data', 'files',
        'csv', 'excel', 'raw'. This prevents meaningless study identifiers.
    """
    dataset_dir = data_dir / 'dataset'
    
    # Generic names that trigger fallback
    generic_names = {'dataset', 'data', 'files', 'csv', 'excel', 'raw'}
    
    if not dataset_dir.exists():
        log.warning("Dataset directory not found, using fallback name 'ext_data'")
        return 'ext_data'
    
    # Find first subdirectory in dataset folder
    subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        log.warning("No subdirectories in dataset folder, using fallback name 'ext_data'")
        return 'ext_data'
    
    # Get the first subdirectory name
    folder_name = subdirs[0].name
    log.info(f"Detected dataset folder: {folder_name}")
    
    # Remove common suffixes
    study_name = folder_name
    suffixes_to_remove = ['_csv_files', '_files', '_data', '_dataset', '_excel']
    for suffix in suffixes_to_remove:
        if study_name.endswith(suffix):
            study_name = study_name[:-len(suffix)]
            break
    
    # Check if name is too short or generic
    if len(study_name) < 2 or study_name.lower() in generic_names:
        log.warning(f"Study name '{study_name}' is generic, using fallback 'ext_data'")
        return 'ext_data'
    
    # Capitalize parts after hyphen (Indo-vap -> Indo-VAP)
    if '-' in study_name:
        parts = study_name.split('-')
        # Keep first part as-is, capitalize rest
        study_name = parts[0] + '-' + '-'.join(p.upper() for p in parts[1:])
    
    log.info(f"Extracted study name: {study_name}")
    return study_name


class DataMigrationManager:
    """Manages migration of data structure from legacy to v0.3.0 format.
    
    Orchestrates complete migration workflow with dual-mode operation for
    custom (external) vs default (in-place) data paths. Provides safe,
    validated migration with dry-run testing, error handling, and audit logging.
    
    **Key Features:**
    
    1. **Dual-Mode Operation**:
       - **Custom Path**: Copies FROM external source TO project data/
         (preserves originals, --data-dir=/external/path)
       - **Default Path**: Reorganizes WITHIN project data/ directory
         (moves files, deletes originals after copy)
    
    2. **Intelligent Detection**:
       - Auto-detects study name from dataset folder structure
       - Builds dynamic migration mappings based on actual folders
       - Detects if already migrated (idempotent operation)
    
    3. **Safety Mechanisms**:
       - Dry-run mode for testing without file operations
       - Pre-migration structure validation
       - Post-migration file count verification
       - User confirmation for destructive operations
       - Comprehensive error tracking and logging
    
    4. **Migration Workflow**:
       - Validate current structure exists
       - Create new study-based directory hierarchy
       - Copy or move files with progress tracking
       - Validate migration success
       - Optional cleanup with confirmation
       - Generate migration log for audit trail
    
    **Attributes:**
        source_dir: Path to source data directory (custom or default)
        dest_dir: Path to destination data directory (always project data/)
        dry_run: If True, simulate operations without file changes
        migration_log: List of operation descriptions for audit log
        migration_success: Boolean flag indicating if migration completed
        is_custom_path: True if using custom (external) source path
        study_name: Auto-detected study identifier (e.g., "Indo-VAP")
        old_to_new: Dictionary mapping old paths to new paths
    
    **Migration Mappings Example:**
        Old structure → New structure:
        - dataset/Indo-VAP_csv_files/ → Indo-VAP/datasets/
        - Annotated_PDFs/annotated_pdfs/ → Indo-VAP/annotated_pdfs/
        - data_dictionary_and_mapping_specifications/ → Indo-VAP/data_dictionary/
    
    Example:
        >>> from pathlib import Path
        >>> # Dry-run test with default path
        >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
        >>> success = manager.migrate()  # doctest: +SKIP
        >>> print(f"Study: {manager.study_name}")  # doctest: +SKIP
        
        >>> # Import from external source (preserves originals)
        >>> manager = DataMigrationManager(
        ...     data_dir=Path('/Volumes/ExternalDrive/data'),
        ...     dry_run=False
        ... )  # doctest: +SKIP
        >>> success = manager.migrate()  # doctest: +SKIP
        >>> if success:  # doctest: +SKIP
        ...     print(f"Imported {manager.study_name} study")
    
    Note:
        Default path mode is DESTRUCTIVE (deletes originals after move).
        Custom path mode is SAFE (copies files, preserves originals).
        Always test with --dry-run first!
    """
    
    def __init__(self, data_dir: Path = None, dry_run: bool = False):
        """Initialize migration manager with path detection and configuration.
        
        Automatically determines operation mode (custom vs default path),
        detects study name, and builds migration mappings from actual
        directory structure.
        
        Args:
            data_dir: Optional custom source data directory path. If provided,
                files will be COPIED from this location to project data/.
                If None, uses config.DATA_DIR and files will be MOVED
                (deleted after copy).
            dry_run: If True, simulate all operations without actual file
                changes. Useful for testing migration before execution.
        
        Side Effects:
            - Logs initialization details (paths, mode, study name)
            - Calls extract_study_name() to detect study identifier
            - Builds migration mappings from actual directory structure
        
        Example:
            >>> from pathlib import Path
            >>> # Default mode (reorganize within project data/)
            >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
            >>> manager.is_custom_path  # doctest: +SKIP
            False
            
            >>> # Custom mode (import from external source)
            >>> manager = DataMigrationManager(
            ...     data_dir=Path('/external/data'),
            ...     dry_run=False
            ... )  # doctest: +SKIP
            >>> manager.is_custom_path  # doctest: +SKIP
            True
            >>> manager.source_dir  # doctest: +SKIP
            PosixPath('/external/data')
        """
        self.source_dir = Path(data_dir) if data_dir else Path(config.DATA_DIR)
        self.dry_run = dry_run
        self.migration_log = []
        self.migration_success = False
        
        # Detect if using custom data path
        default_data_dir = Path(config.DATA_DIR)
        self.is_custom_path = (self.source_dir.resolve() != default_data_dir.resolve())
        
        # Set destination directory
        # Custom path: Copy TO project data/ directory
        # Default path: Reorganize WITHIN data/ directory
        if self.is_custom_path:
            self.dest_dir = default_data_dir
            log.info(f"Source directory (custom): {self.source_dir}")
            log.info(f"Destination directory: {self.dest_dir}")
        else:
            self.dest_dir = self.source_dir
            log.info(f"Data directory (default): {self.source_dir}")
        
        log.info(f"Custom path: {self.is_custom_path}")
        
        # Auto-detect study name from source dataset folder
        self.study_name = extract_study_name(self.source_dir)
        log.info(f"Study name determined: {self.study_name}")
        
        # Define migration mappings (dynamically based on detected study name)
        self.old_to_new = self._build_migration_mappings()
        
        log.info(f"Migration Manager initialized (dry_run={dry_run}, custom_path={self.is_custom_path})")
    
    def _build_migration_mappings(self) -> Dict[str, str]:
        """Build migration path mappings based on detected study name and actual folders.
        
        Scans source directory for actual subdirectories and constructs mapping
        dictionary from old structure paths to new v0.3.0 paths. Handles variable
        folder names (e.g., "Indo-VAP_csv_files" vs "TB-Trial_excel_files").
        
        Mapping logic:
        - dataset/<study>_files/ → <study_name>/datasets/
        - Annotated_PDFs/<pdfs>/ → <study_name>/annotated_pdfs/
        - data_dictionary_and_mapping_specifications/ → <study_name>/data_dictionary/
        
        Returns:
            Dictionary mapping old relative paths to new relative paths.
            Keys are relative to source_dir, values relative to dest_dir.
            Example: {'dataset/Indo-VAP_csv_files': 'Indo-VAP/datasets'}
        
        Side Effects:
            - Logs number of mappings built
            - Logs each mapping (old → new path)
            - Differentiates logging for custom vs default path modes
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
            >>> mappings = manager._build_migration_mappings()  # doctest: +SKIP
            >>> for old, new in mappings.items():  # doctest: +SKIP
            ...     print(f"{old} → {new}")
            dataset/Indo-VAP_csv_files → Indo-VAP/datasets
            Annotated_PDFs/annotated_pdfs → Indo-VAP/annotated_pdfs
            data_dictionary_and_mapping_specifications → Indo-VAP/data_dictionary
        
        Note:
            Only creates mappings for directories that actually exist in source.
            Missing directories are skipped (allows partial migrations).
        """
        # Find actual subdirectories in dataset
        dataset_dir = self.source_dir / 'dataset'
        dataset_subdir = None
        if dataset_dir.exists():
            subdirs = [d.name for d in dataset_dir.iterdir() if d.is_dir()]
            if subdirs:
                dataset_subdir = f'dataset/{subdirs[0]}'
        
        # Find actual subdirectories in Annotated_PDFs
        annotated_dir = self.source_dir / 'Annotated_PDFs'
        annotated_subdir = None
        if annotated_dir.exists():
            subdirs = [d.name for d in annotated_dir.iterdir() if d.is_dir()]
            if subdirs:
                annotated_subdir = f'Annotated_PDFs/{subdirs[0]}'
        
        # Build mappings using standardized folder names (lowercase with underscores)
        mappings = {}
        
        if dataset_subdir:
            mappings[dataset_subdir] = f'{self.study_name}/datasets'
        
        if annotated_subdir:
            mappings[annotated_subdir] = f'{self.study_name}/annotated_pdfs'
        
        # Data dictionary mapping (usually at root level)
        if (self.source_dir / 'data_dictionary_and_mapping_specifications').exists():
            mappings['data_dictionary_and_mapping_specifications'] = f'{self.study_name}/data_dictionary'
        
        log.info(f"Built {len(mappings)} migration mappings:")
        for old, new in mappings.items():
            if self.is_custom_path:
                log.info(f"  {self.source_dir}/{old} → {self.dest_dir}/{new}")
            else:
                log.info(f"  {old} → {new}")
        
        return mappings
    
    def is_already_migrated(self) -> bool:
        """Check if data is already in v0.3.0 structure format.
        
        Detects if migration has already been performed by checking for
        new structure subdirectories (datasets/, annotated_pdfs/,
        data_dictionary/) under study name folder in destination.
        
        This makes migration idempotent - safe to run multiple times without
        duplicate operations.
        
        Returns:
            True if data already migrated to v0.3.0 format, False otherwise.
        
        Side Effects:
            - Logs success message if already migrated
            - No file system modifications
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
            >>> # Before migration
            >>> if not manager.is_already_migrated():  # doctest: +SKIP
            ...     print("Need to migrate")
            >>> # After migration
            >>> if manager.is_already_migrated():  # doctest: +SKIP
            ...     print("Already in v0.3.0 format, skipping")
        
        Note:
            Checks for ALL three subdirectories (datasets/, annotated_pdfs/,
            data_dictionary/). Partial migration is considered incomplete.
        """
        # Check if study directory exists in destination
        study_dir = self.dest_dir / self.study_name
        
        if not study_dir.exists():
            return False
        
        # Check for new structure subdirectories
        new_structure_dirs = ['datasets', 'annotated_pdfs', 'data_dictionary']
        has_new_structure = all(
            (study_dir / dirname).exists() 
            for dirname in new_structure_dirs
        )
        
        if has_new_structure:
            log.info(f"✅ Data already in v0.3.0 format: {study_dir}")
            return True
        
        return False
    
    def validate_current_structure(self) -> bool:
        """Validate that current structure exists and can be migrated.
        
        Performs comprehensive pre-migration validation:
        1. Checks source directory exists
        2. Verifies at least one old structure path found
        3. Creates destination directory if needed (custom path mode)
        4. Warns if new structure already exists
        5. Prompts user for confirmation if conflicts detected
        
        Returns:
            True if structure valid and ready for migration, False otherwise.
        
        Side Effects:
            - Logs validation progress and results
            - May create destination directory (custom path mode)
            - Prompts user for confirmation if new structure exists
            - Logs file counts for each found path
        
        Raises:
            No exceptions raised; returns False on validation failures.
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
            >>> if manager.validate_current_structure():  # doctest: +SKIP
            ...     print("Structure valid, proceeding with migration")
            ... else:
            ...     print("Validation failed, aborting")
        
        Note:
            Interactive - may prompt user for input if conflicts detected.
            Returns False if user chooses not to continue.
        """
        log.info("Validating current data structure...")
        
        if not self.source_dir.exists():
            log.error(f"Source directory not found: {self.source_dir}")
            return False
        
        # Check if old structure exists in source
        old_paths = []
        for old_path in self.old_to_new.keys():
            full_path = self.source_dir / old_path
            if full_path.exists():
                old_paths.append(full_path)
                file_count = len(list(full_path.rglob('*')))
                log.info(f"✓ Found: {old_path} ({file_count} items)")
            else:
                log.warning(f"✗ Not found: {old_path}")
        
        if not old_paths:
            log.error("No old structure found to migrate!")
            return False
        
        # Check if destination directory exists (for custom paths)
        if self.is_custom_path:
            if not self.dest_dir.exists():
                log.info(f"Destination directory will be created: {self.dest_dir}")
                try:
                    self.dest_dir.mkdir(parents=True, exist_ok=True)
                    log.info(f"✓ Created destination directory: {self.dest_dir}")
                except Exception as e:
                    log.error(f"Failed to create destination directory: {e}")
                    return False
        
        # Check if new structure already exists in destination
        new_base = self.dest_dir / self.study_name
        if new_base.exists():
            log.warning(f"New structure already exists: {new_base}")
            response = input("Do you want to continue anyway? (yes/no): ")
            if response.lower() != 'yes':
                log.info("Migration cancelled by user")
                return False
        
        log.info(f"✅ Validation complete: {len(old_paths)} paths ready for migration")
        return True
    
    def create_new_structure(self) -> bool:
        """Create new v0.3.0 directory structure based on detected study name.
        
        Creates three-tier directory hierarchy:
        - <study_name>/datasets/        # For Excel/CSV data files
        - <study_name>/annotated_pdfs/  # For annotated PDF forms
        - <study_name>/data_dictionary/ # For mapping specifications
        
        Returns:
            True if all directories created successfully, False on any failure.
        
        Side Effects:
            - Creates directories in dest_dir (unless dry_run=True)
            - Logs creation status for each directory
            - Appends operations to migration_log
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
            >>> if manager.create_new_structure():  # doctest: +SKIP
            ...     print(f"Created structure for {manager.study_name}")
        
        Note:
            Uses mkdir(parents=True, exist_ok=True) - safe to call multiple
            times. Dry-run mode logs what would be created without changes.
        """
        log.info("Creating new directory structure...")
        
        new_dirs = [
            f'{self.study_name}/datasets',
            f'{self.study_name}/annotated_pdfs',
            f'{self.study_name}/data_dictionary'
        ]
        
        for dir_path in new_dirs:
            full_path = self.dest_dir / dir_path
            
            if self.dry_run:
                log.info(f"[DRY RUN] Would create: {full_path}")
                continue
            
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                log.info(f"✓ Created: {full_path}")
                self.migration_log.append(f"Created directory: {full_path}")
            except Exception as e:
                log.error(f"Failed to create {dir_path}: {e}")
                return False
        
        log.info("✅ New structure created")
        return True
    
    def move_files(self) -> Tuple[int, int, List[str]]:
        """Copy or move files from old to new structure based on operation mode.
        
        Performs bulk file operations with mode-specific behavior:
        
        **Custom Path Mode** (is_custom_path=True):
        - COPIES files from source to destination
        - Preserves originals at source location
        - Uses shutil.copy2 (preserves metadata)
        
        **Default Path Mode** (is_custom_path=False):
        - MOVES files from old to new paths
        - DELETES originals after move (destructive!)
        - Uses shutil.move
        
        For each old→new mapping:
        1. Recursively finds all files in old path
        2. Calculates relative paths for reorganization
        3. Creates destination directories as needed
        4. Copies or moves each file with error handling
        5. Logs progress every 10 files
        6. Tracks successes, failures, and error messages
        
        Returns:
            Tuple of (files_processed, files_failed, error_messages):
                - files_processed: Count of successfully copied/moved files
                - files_failed: Count of files that failed to process
                - error_messages: List of error descriptions for failures
        
        Side Effects:
            - Creates directories in dest_dir
            - Copies or moves files (unless dry_run=True)
            - Logs progress and completion status
            - Appends operations to migration_log
            - Updates file system (potentially destructive in default mode)
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=False)  # doctest: +SKIP
            >>> success_count, fail_count, errors = manager.move_files()  # doctest: +SKIP
            >>> print(f"Processed: {success_count}, Failed: {fail_count}")  # doctest: +SKIP
            >>> if fail_count > 0:  # doctest: +SKIP
            ...     for error in errors[:5]:  # Show first 5 errors
            ...         print(f"  Error: {error}")
        
        Warning:
            Default mode is DESTRUCTIVE - deletes original files after move.
            Custom mode is SAFE - preserves originals. Test with dry_run first!
        
        Note:
            Preserves directory structure within each mapping. For example,
            if source has subdirectories, they're recreated in destination.
        """
        log.info("Starting file migration...")
        
        if self.is_custom_path:
            log.info(f"Custom path detected: Copying FROM {self.source_dir} TO {self.dest_dir}")
            log.info("Files will be COPIED (originals preserved at source)")
        else:
            log.info(f"Default path: Reorganizing within {self.source_dir}")
            log.info("Files will be MOVED (originals deleted)")
        
        files_processed = 0
        files_failed = 0
        errors = []
        
        for old_path, new_path in self.old_to_new.items():
            source = self.source_dir / old_path
            dest = self.dest_dir / new_path
            
            if not source.exists():
                log.warning(f"Source not found, skipping: {source}")
                continue
            
            operation = "Copying" if self.is_custom_path else "Moving"
            if self.is_custom_path:
                log.info(f"{operation}: {source} → {dest}")
            else:
                log.info(f"{operation}: {old_path} → {new_path}")
            
            # Get all files in source
            if source.is_file():
                files_to_process = [source]
            else:
                files_to_process = list(source.rglob('*'))
                files_to_process = [f for f in files_to_process if f.is_file()]
            
            log.info(f"Found {len(files_to_process)} files to {operation.lower()}")
            
            for file_path in files_to_process:
                # Calculate relative path
                rel_path = file_path.relative_to(source)
                dest_file = dest / rel_path
                
                if self.dry_run:
                    log.debug(f"[DRY RUN] Would {operation.lower()}: {file_path.name}")
                    files_processed += 1
                    continue
                
                try:
                    # Create destination directory
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Custom path: COPY files (preserve originals)
                    # Default path: MOVE files (delete originals)
                    if self.is_custom_path:
                        shutil.copy2(str(file_path), str(dest_file))
                        action = "Copied"
                    else:
                        shutil.move(str(file_path), str(dest_file))
                        action = "Moved"
                    
                    files_processed += 1
                    
                    if files_processed % 10 == 0:
                        log.info(f"Progress: {files_processed} files {action.lower()}...")
                    
                    self.migration_log.append(f"{action}: {old_path}/{rel_path} → {new_path}/{rel_path}")
                    
                except Exception as e:
                    files_failed += 1
                    error_msg = f"Failed to {operation.lower()} {file_path}: {e}"
                    log.error(error_msg)
                    errors.append(error_msg)
        
        operation_past = "copied" if self.is_custom_path else "moved"
        log.info(f"✅ Migration complete: {files_processed} files {operation_past}, {files_failed} failed")
        
        if self.is_custom_path:
            log.info(f"📁 Original files preserved at: {self.source_dir}")
            log.info(f"📁 New structure created at: {self.dest_dir}/{self.study_name}")
        
        return files_processed, files_failed, errors
    
    def validate_migration(self) -> bool:
        """Validate that migration was successful by checking file counts.
        
        Post-migration validation ensures data integrity:
        1. Verifies all new structure paths exist in destination
        2. Counts files in each new path
        3. Logs file counts for audit trail
        4. Warns if any paths are empty (potential issue)
        
        Returns:
            True if all new paths exist (regardless of counts), False if
            any expected path is missing.
        
        Side Effects:
            - Logs validation progress and results
            - Logs file counts for each migrated path
            - Logs warnings for empty directories
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=False)  # doctest: +SKIP
            >>> # After running move_files()
            >>> if manager.validate_migration():  # doctest: +SKIP
            ...     print("Migration validated successfully")
            ... else:
            ...     print("Validation failed - check logs")
        
        Note:
            Dry-run mode skips validation (returns True immediately).
            Empty directories trigger warnings but not failures.
        """
        log.info("Validating migration...")
        
        if self.dry_run:
            log.info("[DRY RUN] Skipping validation")
            return True
        
        validation_passed = True
        
        # Check that new structure exists in destination and has files
        for new_path in self.old_to_new.values():
            full_path = self.dest_dir / new_path
            
            if not full_path.exists():
                log.error(f"New path not found: {full_path}")
                validation_passed = False
                continue
            
            file_count = len(list(full_path.rglob('*')))
            log.info(f"✓ {full_path}: {file_count} items")
            
            if file_count == 0:
                log.warning(f"Warning: {full_path} is empty")
        
        if validation_passed:
            log.info("✅ Validation passed")
        else:
            log.error("❌ Validation failed")
        
        return validation_passed
    
    def cleanup_old_structure(self) -> bool:
        """Remove old directory structure after successful migration.
        
        Two-stage cleanup process with user confirmation at each stage:
        
        **Stage 1: Old Directory Structure Cleanup** (Both modes):
        - Prompts user to remove old structure directories
        - Checks if directories empty (should be after moves)
        - Warns if non-empty directories found
        - Removes old structure paths (dataset/, Annotated_PDFs/, etc.)
        
        **Stage 2: Copied Study Folder Cleanup** (Custom path mode only):
        - Prompts to remove newly copied study folder from project data/
        - Confirms originals preserved at source location
        - Only applies if is_custom_path=True
        - Use case: Verify migration without keeping duplicate in project
        
        Interactive prompts ensure user control over destructive operations.
        
        Returns:
            True if cleanup completed successfully or user cancelled,
            False only on errors during file removal.
        
        Side Effects:
            - Prompts user for confirmation (interactive)
            - Removes directories if confirmed (destructive!)
            - Logs cleanup operations
            - Appends operations to migration_log
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=False)  # doctest: +SKIP
            >>> # After successful migration
            >>> if manager.cleanup_old_structure():  # doctest: +SKIP
            ...     print("Cleanup completed")
            ... else:
            ...     print("Cleanup failed")
        
        Warning:
            Destructive operation - removes directories permanently.
            Dry-run mode skips cleanup (logs what would be prompted).
        
        Note:
            User can decline cleanup - old structure preserved if desired.
            Useful for manual verification before permanent cleanup.
        """
        if self.dry_run:
            log.info("[DRY RUN] Would prompt for cleanup")
            return True
        
        # STEP 1: Clean up old structure (applies to both default and custom paths)
        old_structure_exists = any((self.dest_dir / old_path).exists() 
                                   for old_path in self.old_to_new.keys())
        
        if old_structure_exists:
            log.info("Cleaning up old directory structure...")
            
            print("\n" + "="*60)
            print("⚠️  CLEANUP STEP 1: Old Directory Structure")
            print("="*60)
            if self.is_custom_path:
                print("\nFound old structure in project's data/ folder.")
                print("(This is separate from your custom source path)")
            else:
                print("\nDirectories to be removed (should be empty after file moves):")
            
            for old_path in self.old_to_new.keys():
                full_path = self.dest_dir / old_path
                if full_path.exists():
                    print(f"  - {full_path}")
            print("="*60)
            
            response = input("\nRemove old directory structure? (type 'yes' to confirm): ")
            
            if response.lower() == 'yes':
                for old_path in self.old_to_new.keys():
                    full_path = self.dest_dir / old_path
                    
                    if not full_path.exists():
                        continue
                    
                    try:
                        # Check if directory is empty (it should be after moves)
                        if full_path.is_dir():
                            remaining_items = list(full_path.rglob('*'))
                            if remaining_items:
                                log.warning(f"Directory not empty: {old_path} ({len(remaining_items)} items)")
                        
                        if full_path.is_file():
                            full_path.unlink()
                        else:
                            shutil.rmtree(full_path)
                        
                        log.info(f"✓ Removed: {old_path}")
                        self.migration_log.append(f"Removed old structure: {old_path}")
                        
                    except Exception as e:
                        log.error(f"Failed to remove {old_path}: {e}")
                        return False
                
                log.info("✅ Old structure cleanup complete")
            else:
                log.info("Old structure cleanup cancelled by user")
        
        # STEP 2: For custom paths only - ask to remove newly copied study folder
        if self.is_custom_path:
            study_dir = self.dest_dir / self.study_name
            
            if study_dir.exists():
                print("\n" + "="*60)
                print("⚠️  CLEANUP STEP 2: Newly Copied Study Folder")
                print("="*60)
                print(f"\nThe following folder was copied from your custom path:")
                print(f"  - {study_dir}")
                print(f"\nYour original data at '{self.source_dir}' is untouched.")
                print("="*60)
                
                response = input(f"\nRemove copied study folder '{self.study_name}' from project's data/? (type 'yes' to confirm): ")
                
                if response.lower() == 'yes':
                    try:
                        shutil.rmtree(study_dir)
                        log.info(f"✓ Removed copied study folder: {self.study_name}")
                        self.migration_log.append(f"Removed copied study: {self.study_name}")
                        print(f"\n✅ Removed: {study_dir}")
                        print(f"✅ Original data preserved at: {self.source_dir}")
                    except Exception as e:
                        log.error(f"Failed to remove study folder: {e}")
                        return False
                else:
                    log.info(f"Study folder '{self.study_name}' retained by user choice")
                    print(f"\n✅ Kept: {study_dir}")
        
        log.info("✅ Cleanup process complete")
        return True
    
    def save_migration_log(self) -> None:
        """Save migration operation log to file for audit trail.
        
        Creates migration_log.txt in destination directory with:
        - Timestamp
        - Study name
        - List of all operations performed (creates, copies, moves, removes)
        
        Log file serves as permanent record of migration for troubleshooting
        and compliance auditing.
        
        Side Effects:
            - Creates migration_log.txt in dest_dir (unless dry_run=True)
            - Logs save status
            - Overwrites existing log file if present
        
        Example:
            >>> from pathlib import Path
            >>> manager = DataMigrationManager(dry_run=False)  # doctest: +SKIP
            >>> # After running migration
            >>> manager.save_migration_log()  # doctest: +SKIP
            >>> # Check log file
            >>> log_path = manager.dest_dir / 'migration_log.txt'  # doctest: +SKIP
            >>> print(f"Log saved to: {log_path}")  # doctest: +SKIP
        
        Note:
            Dry-run mode skips log creation (logs what would be saved).
        """
        if self.dry_run:
            log.info("[DRY RUN] Would save migration log")
            return
        
        log_file = self.dest_dir / 'migration_log.txt'
        
        try:
            with open(log_file, 'w') as f:
                f.write(f"Data Migration Log\n")
                f.write(f"{'='*60}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Study: {self.study_name}\n\n")
                
                f.write("Migration Steps:\n")
                f.write("-" * 60 + "\n")
                for entry in self.migration_log:
                    f.write(f"{entry}\n")
            
            log.info(f"Migration log saved: {log_file}")
            
        except Exception as e:
            log.error(f"Failed to save migration log: {e}")
    
    def migrate(self) -> bool:
        """Execute complete migration workflow from validation to cleanup.
        
        Orchestrates full migration process:
        
        **Step 0**: Check if already migrated (idempotent)
        **Step 1**: Validate current structure exists
        **Step 2**: Create new directory structure
        **Step 3**: Copy or move files (mode-dependent)
        **Step 4**: Validate migration success
        **Step 5**: Optional cleanup with user confirmation
        **Step 6**: Save migration log
        
        Provides comprehensive logging at each step with clear success/failure
        indicators. Handles errors gracefully with user prompts for recovery.
        
        Returns:
            True if migration completed successfully, False on any failure
            or user cancellation.
        
        Side Effects:
            - Executes all migration operations (unless dry_run=True)
            - Logs comprehensive progress and results
            - May prompt user for decisions (cleanup, error recovery)
            - Updates migration_success flag
            - Creates/modifies file system structure
        
        Raises:
            No exceptions raised; all errors handled internally with logging.
        
        Example:
            >>> from pathlib import Path
            >>> # Test migration with dry-run
            >>> manager = DataMigrationManager(dry_run=True)  # doctest: +SKIP
            >>> if manager.migrate():  # doctest: +SKIP
            ...     print(f"Dry-run successful for {manager.study_name}")
            
            >>> # Execute actual migration
            >>> manager = DataMigrationManager(dry_run=False)  # doctest: +SKIP
            >>> success = manager.migrate()  # doctest: +SKIP
            >>> if success:  # doctest: +SKIP
            ...     print(f"Migrated {manager.study_name} successfully")
            ...     print(f"  Files processed: {manager.migration_log}")
            ... else:
            ...     print("Migration failed - check logs")
        
        Note:
            Idempotent - safe to run multiple times. Detects existing v0.3.0
            structure and skips redundant work. Dry-run mode recommended for
            testing before actual migration.
        """
        log.info("="*60)
        log.info("Starting Data Structure Migration")
        log.info("="*60)
        
        if self.dry_run:
            log.info("🔍 DRY RUN MODE - No actual changes will be made")
        
        # Log file handling mode
        if self.is_custom_path:
            log.info("📂 Custom path mode: Files will be COPIED (originals preserved)")
        else:
            log.info("📂 Default path mode: Files will be MOVED (originals deleted)")
        
        # Step 0: Check if already migrated to v0.3.0 format
        if self.is_already_migrated():
            log.info("="*60)
            log.info("✅ Data is already in v0.3.0 format!")
            log.info("="*60)
            log.info("No migration needed. Exiting.")
            return True
        
        # Step 1: Validate current structure
        if not self.validate_current_structure():
            log.error("❌ Validation failed. Migration aborted.")
            return False
        
        # Step 2: Create new structure
        if not self.create_new_structure():
            log.error("❌ Failed to create new structure. Migration aborted.")
            return False
        
        # Step 3: Copy or Move files
        files_processed, files_failed, errors = self.move_files()
        
        if files_failed > 0:
            log.error(f"❌ {files_failed} files failed to process")
            for error in errors[:10]:  # Show first 10 errors
                log.error(f"  {error}")
            
            response = input("\nContinue despite errors? (yes/no): ")
            if response.lower() != 'yes':
                log.info("Migration aborted by user")
                return False
        
        # Step 4: Validate migration
        if not self.validate_migration():
            log.error("❌ Migration validation failed")
            return False
        
        # Step 5: Cleanup (handles both custom and default paths appropriately)
        if not self.dry_run:
            self.cleanup_old_structure()
        
        # Step 6: Save migration log
        self.save_migration_log()
        
        # Mark migration as successful
        self.migration_success = True
        
        log.info("\n" + "="*60)
        log.info("✅ Migration Complete!")
        log.info("="*60)
        log.info(f"Files processed: {files_processed}")
        log.info(f"Files failed: {files_failed}")
        
        if self.is_custom_path:
            log.info("📁 Original files: PRESERVED at source location")
            log.info(f"   Source: {self.source_dir}")
        else:
            log.info("📁 Original files: DELETED (moved to new structure)")
        
        log.info("="*60)
        
        return True


def main():
    """Main entry point for data migration CLI.
    
    Provides command-line interface for data structure migration with:
    - Argument parsing (--dry-run, --data-dir)
    - Safety warnings for destructive operations
    - User confirmation prompts
    - Migration manager initialization and execution
    - Exit code reporting for shell scripting
    
    **Command-Line Arguments:**
        --dry-run: Simulate migration without making changes (recommended first)
        --data-dir: Path to custom source data directory (optional)
    
    **Safety Features:**
    - Displays WARNING about no backup creation
    - Explains file operations (move vs copy)
    - Requires explicit 'yes' confirmation for actual migration
    - Dry-run mode available for risk-free testing
    
    **Exit Codes:**
    - 0: Migration successful
    - 1: Migration failed or user cancelled
    
    Side Effects:
        - Parses sys.argv for command-line arguments
        - Prompts user for confirmation (unless dry-run)
        - Creates DataMigrationManager and runs migration
        - Prints status messages to console
        - Calls sys.exit() with appropriate code
    
    Example:
        >>> # From command line:
        >>> # Test migration first (safe, no changes)
        >>> # python3 migrate_data_structure.py --dry-run
        >>>
        >>> # Import from external source (preserves originals)
        >>> # python3 migrate_data_structure.py --data-dir=/Volumes/ExternalDrive/data
        >>>
        >>> # Reorganize existing data (destructive - moves files)
        >>> # python3 migrate_data_structure.py
        >>>
        >>> # Programmatic usage:
        >>> import sys
        >>> sys.argv = ['migrate_data_structure.py', '--dry-run']
        >>> # main()  # Would execute migration in dry-run mode
    
    Warning:
        Default mode (no --data-dir) MOVES files and DELETES originals.
        Ensure external backups exist before running. Always test with
        --dry-run first!
    
    Note:
        Interactive - prompts for user confirmation unless --dry-run used.
        Safe to run multiple times - detects if already migrated.
    """
    
    parser = argparse.ArgumentParser(
        description='Migrate RePORTaLiN data structure to v0.3.0 organization',
        epilog='Example: python3 migrate.py --dry-run  # Test migration without changes'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without making actual changes'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Path to data directory (default: from config)'
    )
    
    args = parser.parse_args()
    
    # Display warning about no backups
    if not args.dry_run:
        print("\n" + "="*60)
        print("⚠️  WARNING: MIGRATION MOVES FILES (NO BACKUP CREATED)")
        print("="*60)
        print("This script will:")
        print("  • Move files from old structure to new structure")
        print("  • Delete original files automatically (via move)")
        print("  • NOT create any backup")
        print("\nEnsure you have external backups before proceeding!")
        print("="*60)
        
        response = input("\nDo you want to continue? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            sys.exit(0)
    
    # Initialize migration manager
    manager = DataMigrationManager(
        data_dir=args.data_dir,
        dry_run=args.dry_run
    )
    
    # Execute migration
    success = manager.migrate()
    
    if success:
        print("\n✅ Migration completed successfully!")
        if args.dry_run:
            print("This was a dry run. No actual changes were made.")
            print("Run without --dry-run to perform actual migration.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
