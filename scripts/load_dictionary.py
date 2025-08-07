"""
extract_tables_to_jsonl.py

Extract multiple tables from each sheet of an Excel workbook, clean NaN-only columns,
and save each table as a line-delimited JSON (JSONL) file with metadata for RAG ingestion.
"""

import pandas as pd
import os
import sys
from pathlib import Path
import argparse
import json


def expand_user_path(path_str):
    """Expand user paths like ~/Documents to absolute paths."""
    return Path(os.path.expanduser(str(path_str)))


def find_excel_file(filename=None, directory=None):
    """Find Excel file in specified directory or common locations."""
    search_paths = []
    common_dirs = [".", "~/Documents", "~/Downloads", "~/Desktop"]
    extensions = [".xlsx", ".xls", ".xlsm"]
    
    # Build search paths
    if filename and directory:
        search_paths.append(Path(directory) / filename)
    
    if filename:
        for common_dir in common_dirs:
            search_paths.append(expand_user_path(common_dir) / filename)
    
    if directory:
        dir_path = expand_user_path(directory)
        for ext in extensions:
            search_paths.extend(dir_path.glob(f"*{ext}"))
    
    if not (filename or directory):
        for common_dir in common_dirs:
            dir_path = expand_user_path(common_dir)
            for ext in extensions:
                search_paths.extend(dir_path.glob(f"*{ext}"))
    
    # Find existing files
    found_files = [path for path in search_paths if path.exists()]
    
    if not found_files:
        print("No Excel files found in the specified locations.")
        return None
    
    # Return single file or prompt for selection
    if len(found_files) == 1:
        return found_files[0]
    
    print("\nMultiple Excel files found. Please select one:")
    for i, file_path in enumerate(found_files, 1):
        print(f"{i}. {file_path}")
    
    try:
        choice = int(input("\nEnter the number of your choice (or 0 to cancel): "))
        return found_files[choice - 1] if 1 <= choice <= len(found_files) else None
    except (ValueError, IndexError):
        print("Invalid selection. Canceled.")
        return None


def extract_tables(input_path):
    """Extract tables from Excel workbook, handling both vertical and horizontal table separation."""
    # Setup and file validation
    input_path = expand_user_path(input_path)
    if not input_path.exists():
        print(f"Error: File not found: '{input_path}'", file=sys.stderr)
        found_path = find_excel_file(input_path.name)
        if not found_path:
            print("Could not find the Excel file.")
            return {}
        input_path = found_path
        print(f"Found Excel file at: '{input_path}'")
    
    # Load workbook
    try:
        print(f"Loading workbook from '{input_path}'")
        xls = pd.ExcelFile(input_path, engine="openpyxl")
    except Exception as e:
        print(f"Error loading workbook: {e}", file=sys.stderr)
        return {}
    
    tables_by_sheet = {}
    total_tables = 0
    
    # Process each sheet
    for sheet_name in xls.sheet_names:
        print(f"Processing sheet: '{sheet_name}'")
        try:
            df = xls.parse(sheet_name, dtype=object)
            
            # Find blank column separators (unnamed and full NaN)
            blank_cols = [col for col in df.columns
                         if df[col].isnull().all() and (pd.isna(col) or str(col).startswith("Unnamed"))]
            
            # Group columns by blank column separators
            cols, col_groups, temp_cols = list(df.columns), [], []
            for col in cols:
                if col in blank_cols:
                    if temp_cols:  # Save this column group if not empty
                        col_groups.append(temp_cols)
                        temp_cols = []
                else:
                    temp_cols.append(col)
            if temp_cols:  # Save the last column group
                col_groups.append(temp_cols)
                
            print(f"  Found {len(col_groups)} column groups separated by {len(blank_cols)} blank columns")
            
            # Extract tables from each column group
            tables = []
            for grp_idx, group_cols in enumerate(col_groups, 1):
                # Get dataframe subset with only these columns
                df_sub = df[group_cols]
                
                # Find blank row separators
                blank_rows = df_sub.isnull().all(axis=1)
                row_indices = [0] + blank_rows[blank_rows].index.tolist() + [len(df_sub)]
                
                # Extract tables between blank rows
                for start, end in zip(row_indices, row_indices[1:]):
                    table = df_sub.iloc[start:end].dropna(how="all", axis=0).reset_index(drop=True)
                    if table.empty:
                        continue
                        
                    # Process empty columns: drop unnamed, fill named
                    for col in table.columns[table.isnull().all()]:
                        if pd.isna(col) or str(col).startswith("Unnamed"):
                            table.drop(columns=[col], inplace=True)
                        else:
                            table[col] = ""
                            
                    tables.append(table)
                    total_tables += 1
            
            if tables:
                tables_by_sheet[sheet_name] = tables
                print(f"  Extracted {len(tables)} tables from '{sheet_name}'")
                
        except Exception as e:
            print(f"  Failed to process sheet '{sheet_name}': {e}", file=sys.stderr)
    
    print(f"Extracted {total_tables} tables across {len(tables_by_sheet)} sheets")
    return tables_by_sheet


def generate_table_name(table, sheet_name, index):
    """Generate a meaningful name for the table based on its content."""
    name_candidates = ["name", "title", "description", "id", "type"]
    
    if not table.empty and len(table.columns) > 0:
        # Try column headers first
        for candidate in name_candidates:
            matching_cols = [col for col in table.columns 
                            if isinstance(col, str) and candidate in col.lower()]
            if matching_cols and len(table) > 0:
                first_val = table[matching_cols[0]].iloc[0]
                if pd.notna(first_val) and str(first_val).strip():
                    return f"{sheet_name}_{str(first_val).strip().replace(' ', '_')[:30]}"
        
        # Try first cell in first column
        if len(table) > 0:
            first_val = table.iloc[0, 0]
            if pd.notna(first_val) and str(first_val).strip():
                return f"{sheet_name}_{str(first_val).strip().replace(' ', '_')[:30]}"
    
    # Default name
    return f"{sheet_name}_table_{index}"


def save_tables_as_jsonl(tables_by_sheet, output_dir):
    """Save tables as JSONL files with overwrite behavior."""
    output_path = expand_user_path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    saved_count = 0
    
    for sheet, tables in tables_by_sheet.items():
        # Create directory for sheet
        safe_sheet_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in sheet).strip()
        sheet_dir = output_path / safe_sheet_name
        sheet_dir.mkdir(exist_ok=True)
        
        # Save each table
        for i, table in enumerate(tables, start=1):
            table_name = f"{safe_sheet_name}_table{i}"
            out_file = sheet_dir / f"{table_name}.jsonl"
            
            # Add metadata
            table = table.copy()
            table["__sheet__"] = sheet
            table["__table__"] = table_name
            
            # Always overwrite - solves the appending issue
            if out_file.exists():
                out_file.unlink()
                
            try:
                table.to_json(out_file, orient="records", lines=True, force_ascii=False)
                print(f"  Saved {len(table)} records to {out_file.name}")
                saved_count += 1
            except Exception as e:
                print(f"Failed to save {sheet}/{table_name}: {e}", file=sys.stderr)
    
    print(f"Successfully saved {saved_count} tables as JSONL files in '{output_path}'")
    return saved_count


def extract_and_save_tables(input_path=None, output_dir=None):
    """Extract tables from Excel file and save as JSONL files."""
    # Find input file if not specified
    if not input_path:
        print("No input file specified. Searching for Excel files...")
        input_path = find_excel_file() or ""
        if not input_path:
            print("No Excel files found. Please specify a file path.")
            return 0
    
    # Set default output directory
    if not output_dir:
        output_dir = expand_user_path(input_path).parent / "extracted_tables"
    
    print(f"Starting extraction from '{input_path}' to '{output_dir}'")
    tables = extract_tables(input_path)
    if not tables:
        print("No tables were extracted.")
        return 0
        
    saved = save_tables_as_jsonl(tables, output_dir)
    print(f"Process complete: {saved} tables extracted and saved")
    return saved


def main():
    """Parse command-line arguments and run the extraction process."""
    parser = argparse.ArgumentParser(
        description="Extract tables from Excel files and save as JSONL."
    )
    parser.add_argument("-i", "--input", help="Input Excel file path")
    parser.add_argument("-o", "--output", help="Output directory for JSONL files")
    parser.add_argument("--search-dir", help="Directory to search for Excel files")
    
    args = parser.parse_args()
    
    # If search directory provided but no input file, search that directory
    if args.search_dir and not args.input:
        args.input = find_excel_file(directory=args.search_dir)
    
    extract_and_save_tables(args.input, args.output)


if __name__ == "__main__":
    main()