"""
extract_tables_to_jsonl.py

Extract multiple tables from each sheet of an Excel workbook, clean NaN-only columns,
and save each table as a line-delimited JSON (JSONL) file with metadata for RAG ingestion.
"""

import pandas as pd
import os
import sys
from pathlib import Path
import json


def expand_user_path(path_str):
    """Expand user paths like ~/Documents to absolute paths."""
    return Path(os.path.expanduser(str(path_str)))


def extract_tables(input_path):
    """Extract tables from Excel workbook, handling both vertical and horizontal table separation."""
    # Setup and file validation
    input_path = expand_user_path(input_path)
    if not input_path.exists():
        print(f"Error: File not found: '{input_path}'", file=sys.stderr)
        return {}
    
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
    saved_tables = []
    
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
                saved_tables.append({
                    "sheet": sheet,
                    "table_name": table_name,
                    "path": str(out_file),
                    "rows": len(table),
                    "columns": len(table.columns) - 2  # Subtract metadata columns
                })
            except Exception as e:
                print(f"Failed to save {sheet}/{table_name}: {e}", file=sys.stderr)
    
    print(f"Successfully saved {saved_count} tables as JSONL files in '{output_path}'")
    return saved_tables


def load_study_dictionary(file_path):
    """
    Load study dictionary from Excel file and extract tables to JSONL format.
    
    Parameters:
        file_path (str): Path to the Excel file containing the study dictionary
        
    Returns:
        list: Information about the extracted tables
    """
    # Default paths
    input_path = "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    output_dir = "data/data_dictionary_and_mapping_specifications/json_output"
    
    # Override with provided path if specified
    if file_path:
        input_path = file_path
    
    print(f"Loading study dictionary from: {input_path}")
    print(f"Saving extracted tables to: {output_dir}")
    
    # Extract tables from the Excel file
    tables = extract_tables(input_path)
    
    if not tables:
        print("No tables were extracted from the study dictionary.")
        return []
    
    # Save tables as JSONL files
    saved_tables = save_tables_as_jsonl(tables, output_dir)
    
    print(f"Study dictionary processing complete: {len(saved_tables)} tables extracted and saved")
    return saved_tables


# This allows the script to be run standalone for testing
if __name__ == "__main__":
    # When run directly, use the default paths
    load_study_dictionary(None)