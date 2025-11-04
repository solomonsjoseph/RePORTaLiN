#!/usr/bin/env python3
"""
Data Structure Migration Script for RePORTaLiN
===============================================

Migrates existing data structure to new v0.3.0 organization with dynamic study name detection.

Old Structure (pre-v0.3.0):
    data/
    ├── dataset/[Study]_csv_files/
    ├── Annotated_PDFs/Annotated CRFs - [Study]/
    └── data_dictionary_and_mapping_specifications/

New Structure (v0.3.0):
    data/
    └── [Study-NAME]/
        ├── datasets/
        ├── annotated_pdfs/
        └── data_dictionary/

Study Name Detection:
    - Extracts from dataset folder (e.g., 'Indo-vap_csv_files' → 'Indo-VAP')
    - Removes common suffixes (_csv_files, _files, etc.)
    - Capitalizes parts after hyphen
    - Defaults to 'ext_data' if name is unclear or generic

Migration Behavior:
    - **Skips migration if data is already in v0.3.0 format**
    - **Only migrates custom/old structure data**
    - **Default path**: Moves files (internal reorganization, originals deleted)
    - **Custom path**: Copies files to project's data/ (preserves originals at source)
    - **Cleanup (Custom path)**: Two-step process:
        1. Remove old structure from project's data/ (if exists)
        2. Remove newly copied study folder (optional, user confirms)
    - **Cleanup (Default path)**: Remove old structure (user confirms)
    - **No backups created** - not needed for custom paths (originals preserved)
    - Validates all file operations
    - Comprehensive logging to logs/
    - Dry-run mode for safety

Usage:
    python3 migrate.py                    # Default path: moves files
    python3 migrate.py --dry-run          # Test without changes
    python3 migrate.py --data-dir /path   # Custom path: copies files, preserves originals

⚠️  File Handling:
   - Default path: Files are MOVED (originals deleted)
   - Custom path: Files are COPIED (originals preserved)

Author: RePORTaLiN Team
Date: December 2025
Version: 2.0.0 (smart migration with custom path support)
"""

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
import logging

# Add root directory for imports
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import config
from scripts.utils import logging as custom_log

# Setup logger
logger = custom_log.setup_logger("migrate_data_structure", log_level=logging.INFO)


def extract_study_name(data_dir: Path) -> str:
    """
    Extract study name from dataset folder with intelligent fallback.
    
    Logic:
    1. Look for dataset folder (e.g., 'dataset/Indo-vap_csv_files')
    2. Remove common suffixes (_csv_files, _files, etc.)
    3. Capitalize parts after hyphen (Indo-vap -> Indo-VAP)
    4. Fallback to 'ext_data' if name is unclear or generic
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        str: Extracted study name or 'ext_data' as fallback
        
    Examples:
        >>> extract_study_name(Path('data'))  # with dataset/Indo-vap_csv_files
        'Indo-VAP'
        >>> extract_study_name(Path('data'))  # with dataset/data
        'ext_data'
    """
    dataset_dir = data_dir / 'dataset'
    
    # Generic names that trigger fallback
    generic_names = {'dataset', 'data', 'files', 'csv', 'excel', 'raw'}
    
    if not dataset_dir.exists():
        logger.warning("Dataset directory not found, using fallback name 'ext_data'")
        return 'ext_data'
    
    # Find first subdirectory in dataset folder
    subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        logger.warning("No subdirectories in dataset folder, using fallback name 'ext_data'")
        return 'ext_data'
    
    # Get the first subdirectory name
    folder_name = subdirs[0].name
    logger.info(f"Detected dataset folder: {folder_name}")
    
    # Remove common suffixes
    study_name = folder_name
    suffixes_to_remove = ['_csv_files', '_files', '_data', '_dataset', '_excel']
    for suffix in suffixes_to_remove:
        if study_name.endswith(suffix):
            study_name = study_name[:-len(suffix)]
            break
    
    # Check if name is too short or generic
    if len(study_name) < 2 or study_name.lower() in generic_names:
        logger.warning(f"Study name '{study_name}' is generic, using fallback 'ext_data'")
        return 'ext_data'
    
    # Capitalize parts after hyphen (Indo-vap -> Indo-VAP)
    if '-' in study_name:
        parts = study_name.split('-')
        # Keep first part as-is, capitalize rest
        study_name = parts[0] + '-' + '-'.join(p.upper() for p in parts[1:])
    
    logger.info(f"Extracted study name: {study_name}")
    return study_name


class DataMigrationManager:
    """
    Manages migration of data structure from old to v0.3.0 format.
    
    Workflow:
    1. Detect if already in new format (skip migration)
    2. Validate old structure exists
    3. Create new structure
    4. Copy/Move files based on path type:
       - Default path: Move files (internal reorganization)
       - Custom path: Copy files (preserve originals)
    5. Validate migration
    6. Cleanup empty old directories (default path only)
    
    File Handling:
    - **Default path** (data/): Files are moved, originals deleted
    - **Custom path**: Files are copied, originals preserved at source
    """
    
    def __init__(self, data_dir: Path = None, dry_run: bool = False):
        """
        Initialize migration manager.
        
        Args:
            data_dir: Path to data directory (default: config.DATA_DIR)
            dry_run: If True, only simulate migration without actual changes
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
            logger.info(f"Source directory (custom): {self.source_dir}")
            logger.info(f"Destination directory: {self.dest_dir}")
        else:
            self.dest_dir = self.source_dir
            logger.info(f"Data directory (default): {self.source_dir}")
        
        logger.info(f"Custom path: {self.is_custom_path}")
        
        # Auto-detect study name from source dataset folder
        self.study_name = extract_study_name(self.source_dir)
        logger.info(f"Study name determined: {self.study_name}")
        
        # Define migration mappings (dynamically based on detected study name)
        self.old_to_new = self._build_migration_mappings()
        
        logger.info(f"Migration Manager initialized (dry_run={dry_run}, custom_path={self.is_custom_path})")
    
    def _build_migration_mappings(self) -> Dict[str, str]:
        """
        Build migration mappings based on detected study name.
        
        For custom paths: Maps from source path to project data/ directory
        For default path: Maps within same directory
        
        Returns:
            Dict mapping old paths to new paths (relative to respective directories)
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
        
        logger.info(f"Built {len(mappings)} migration mappings:")
        for old, new in mappings.items():
            if self.is_custom_path:
                logger.info(f"  {self.source_dir}/{old} → {self.dest_dir}/{new}")
            else:
                logger.info(f"  {old} → {new}")
        
        return mappings
    
    def is_already_migrated(self) -> bool:
        """
        Check if data is already in the new v0.3.0 structure format.
        
        The new format has:
        - data/[Study-NAME]/datasets/
        - data/[Study-NAME]/annotated_pdfs/
        - data/[Study-NAME]/data_dictionary/
        
        For custom paths: Checks in project's data/ directory
        For default path: Checks in same directory
        
        Returns:
            bool: True if data is already in new format
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
            logger.info(f"✅ Data already in v0.3.0 format: {study_dir}")
            return True
        
        return False
    
    def validate_current_structure(self) -> bool:
        """
        Validate that current structure exists and can be migrated.
        
        Returns:
            bool: True if structure is valid for migration
        """
        logger.info("Validating current data structure...")
        
        if not self.source_dir.exists():
            logger.error(f"Source directory not found: {self.source_dir}")
            return False
        
        # Check if old structure exists in source
        old_paths = []
        for old_path in self.old_to_new.keys():
            full_path = self.source_dir / old_path
            if full_path.exists():
                old_paths.append(full_path)
                file_count = len(list(full_path.rglob('*')))
                logger.info(f"✓ Found: {old_path} ({file_count} items)")
            else:
                logger.warning(f"✗ Not found: {old_path}")
        
        if not old_paths:
            logger.error("No old structure found to migrate!")
            return False
        
        # Check if destination directory exists (for custom paths)
        if self.is_custom_path:
            if not self.dest_dir.exists():
                logger.info(f"Destination directory will be created: {self.dest_dir}")
                try:
                    self.dest_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"✓ Created destination directory: {self.dest_dir}")
                except Exception as e:
                    logger.error(f"Failed to create destination directory: {e}")
                    return False
        
        # Check if new structure already exists in destination
        new_base = self.dest_dir / self.study_name
        if new_base.exists():
            logger.warning(f"New structure already exists: {new_base}")
            response = input("Do you want to continue anyway? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration cancelled by user")
                return False
        
        logger.info(f"✅ Validation complete: {len(old_paths)} paths ready for migration")
        return True
    
    def create_new_structure(self) -> bool:
        """
        Create new directory structure based on detected study name.
        
        For custom paths: Creates in project data/ directory
        For default path: Creates in same directory
        
        Returns:
            bool: True if structure created successfully
        """
        logger.info("Creating new directory structure...")
        
        new_dirs = [
            f'{self.study_name}/datasets',
            f'{self.study_name}/annotated_pdfs',
            f'{self.study_name}/data_dictionary'
        ]
        
        for dir_path in new_dirs:
            full_path = self.dest_dir / dir_path
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create: {full_path}")
                continue
            
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✓ Created: {full_path}")
                self.migration_log.append(f"Created directory: {full_path}")
            except Exception as e:
                logger.error(f"Failed to create {dir_path}: {e}")
                return False
        
        logger.info("✅ New structure created")
        return True
    
    def move_files(self) -> Tuple[int, int, List[str]]:
        """
        Copy or move files from old to new structure.
        
        Behavior:
        - **Custom path**: Files are COPIED from custom path TO project data/ (originals preserved)
        - **Default path**: Files are MOVED within data/ (originals deleted, internal reorganization)
        
        Returns:
            Tuple of (files_processed, files_failed, error_list)
        """
        logger.info("Starting file migration...")
        
        if self.is_custom_path:
            logger.info(f"Custom path detected: Copying FROM {self.source_dir} TO {self.dest_dir}")
            logger.info("Files will be COPIED (originals preserved at source)")
        else:
            logger.info(f"Default path: Reorganizing within {self.source_dir}")
            logger.info("Files will be MOVED (originals deleted)")
        
        files_processed = 0
        files_failed = 0
        errors = []
        
        for old_path, new_path in self.old_to_new.items():
            source = self.source_dir / old_path
            dest = self.dest_dir / new_path
            
            if not source.exists():
                logger.warning(f"Source not found, skipping: {source}")
                continue
            
            operation = "Copying" if self.is_custom_path else "Moving"
            if self.is_custom_path:
                logger.info(f"{operation}: {source} → {dest}")
            else:
                logger.info(f"{operation}: {old_path} → {new_path}")
            
            # Get all files in source
            if source.is_file():
                files_to_process = [source]
            else:
                files_to_process = list(source.rglob('*'))
                files_to_process = [f for f in files_to_process if f.is_file()]
            
            logger.info(f"Found {len(files_to_process)} files to {operation.lower()}")
            
            for file_path in files_to_process:
                # Calculate relative path
                rel_path = file_path.relative_to(source)
                dest_file = dest / rel_path
                
                if self.dry_run:
                    logger.debug(f"[DRY RUN] Would {operation.lower()}: {file_path.name}")
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
                        logger.info(f"Progress: {files_processed} files {action.lower()}...")
                    
                    self.migration_log.append(f"{action}: {old_path}/{rel_path} → {new_path}/{rel_path}")
                    
                except Exception as e:
                    files_failed += 1
                    error_msg = f"Failed to {operation.lower()} {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        operation_past = "copied" if self.is_custom_path else "moved"
        logger.info(f"✅ Migration complete: {files_processed} files {operation_past}, {files_failed} failed")
        
        if self.is_custom_path:
            logger.info(f"📁 Original files preserved at: {self.source_dir}")
            logger.info(f"📁 New structure created at: {self.dest_dir}/{self.study_name}")
        
        return files_processed, files_failed, errors
    
    def validate_migration(self) -> bool:
        """
        Validate that migration was successful.
        
        Checks new structure in destination directory.
        
        Returns:
            bool: True if validation passed
        """
        logger.info("Validating migration...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Skipping validation")
            return True
        
        validation_passed = True
        
        # Check that new structure exists in destination and has files
        for new_path in self.old_to_new.values():
            full_path = self.dest_dir / new_path
            
            if not full_path.exists():
                logger.error(f"New path not found: {full_path}")
                validation_passed = False
                continue
            
            file_count = len(list(full_path.rglob('*')))
            logger.info(f"✓ {full_path}: {file_count} items")
            
            if file_count == 0:
                logger.warning(f"Warning: {full_path} is empty")
        
        if validation_passed:
            logger.info("✅ Validation passed")
        else:
            logger.error("❌ Validation failed")
        
        return validation_passed
    
    def cleanup_old_structure(self) -> bool:
        """
        Remove old directory structure after files have been moved/copied.
        
        For default path: Asks to remove old structure (single step)
        For custom path: Two-step cleanup process:
            1. Ask to remove old structure from project's data/ (if exists)
            2. Ask to remove newly copied study folder from project's data/
        
        Returns:
            bool: True if cleanup successful or skipped by user
        """
        if self.dry_run:
            logger.info("[DRY RUN] Would prompt for cleanup")
            return True
        
        # STEP 1: Clean up old structure (applies to both default and custom paths)
        old_structure_exists = any((self.dest_dir / old_path).exists() 
                                   for old_path in self.old_to_new.keys())
        
        if old_structure_exists:
            logger.info("Cleaning up old directory structure...")
            
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
                                logger.warning(f"Directory not empty: {old_path} ({len(remaining_items)} items)")
                        
                        if full_path.is_file():
                            full_path.unlink()
                        else:
                            shutil.rmtree(full_path)
                        
                        logger.info(f"✓ Removed: {old_path}")
                        self.migration_log.append(f"Removed old structure: {old_path}")
                        
                    except Exception as e:
                        logger.error(f"Failed to remove {old_path}: {e}")
                        return False
                
                logger.info("✅ Old structure cleanup complete")
            else:
                logger.info("Old structure cleanup cancelled by user")
        
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
                        logger.info(f"✓ Removed copied study folder: {self.study_name}")
                        self.migration_log.append(f"Removed copied study: {self.study_name}")
                        print(f"\n✅ Removed: {study_dir}")
                        print(f"✅ Original data preserved at: {self.source_dir}")
                    except Exception as e:
                        logger.error(f"Failed to remove study folder: {e}")
                        return False
                else:
                    logger.info(f"Study folder '{self.study_name}' retained by user choice")
                    print(f"\n✅ Kept: {study_dir}")
        
        logger.info("✅ Cleanup process complete")
        return True
    
    def save_migration_log(self):
        """Save migration log to file."""
        if self.dry_run:
            logger.info("[DRY RUN] Would save migration log")
            return
        
        log_file = self.dest_dir / 'migration_log.txt'
        
        try:
            with open(log_file, 'w') as f:
                f.write(f"Data Migration Log\n")
                f.write(f"{'='*60}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Study: {self.study_name}\n")
                f.write(f"Version: 2.0.0 (no backup)\n\n")
                
                f.write("Migration Steps:\n")
                f.write("-" * 60 + "\n")
                for entry in self.migration_log:
                    f.write(f"{entry}\n")
            
            logger.info(f"Migration log saved: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save migration log: {e}")
    
    def migrate(self) -> bool:
        """
        Execute complete migration workflow.
        
        Workflow:
        1. Check if already in new format → skip migration
        2. Validate old structure exists
        3. Create new structure
        4. Copy/Move files based on path type
        5. Validate migration
        6. Cleanup empty old directories (default path only)
        
        Returns:
            bool: True if migration successful or already migrated
        """
        logger.info("="*60)
        logger.info("Starting Data Structure Migration")
        logger.info("="*60)
        
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No actual changes will be made")
        
        # Log file handling mode
        if self.is_custom_path:
            logger.info("📂 Custom path mode: Files will be COPIED (originals preserved)")
        else:
            logger.info("📂 Default path mode: Files will be MOVED (originals deleted)")
        
        # Step 0: Check if already migrated to v0.3.0 format
        if self.is_already_migrated():
            logger.info("="*60)
            logger.info("✅ Data is already in v0.3.0 format!")
            logger.info("="*60)
            logger.info("No migration needed. Exiting.")
            return True
        
        # Step 1: Validate current structure
        if not self.validate_current_structure():
            logger.error("❌ Validation failed. Migration aborted.")
            return False
        
        # Step 2: Create new structure
        if not self.create_new_structure():
            logger.error("❌ Failed to create new structure. Migration aborted.")
            return False
        
        # Step 3: Copy or Move files
        files_processed, files_failed, errors = self.move_files()
        
        if files_failed > 0:
            logger.error(f"❌ {files_failed} files failed to process")
            for error in errors[:10]:  # Show first 10 errors
                logger.error(f"  {error}")
            
            response = input("\nContinue despite errors? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration aborted by user")
                return False
        
        # Step 4: Validate migration
        if not self.validate_migration():
            logger.error("❌ Migration validation failed")
            return False
        
        # Step 5: Cleanup (handles both custom and default paths appropriately)
        if not self.dry_run:
            self.cleanup_old_structure()
        
        # Step 6: Save migration log
        self.save_migration_log()
        
        # Mark migration as successful
        self.migration_success = True
        
        logger.info("\n" + "="*60)
        logger.info("✅ Migration Complete!")
        logger.info("="*60)
        logger.info(f"Files processed: {files_processed}")
        logger.info(f"Files failed: {files_failed}")
        
        if self.is_custom_path:
            logger.info("📁 Original files: PRESERVED at source location")
            logger.info(f"   Source: {self.source_dir}")
        else:
            logger.info("📁 Original files: DELETED (moved to new structure)")
        
        logger.info("="*60)
        
        return True


def main():
    """Main entry point for migration script."""
    import argparse
    
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
