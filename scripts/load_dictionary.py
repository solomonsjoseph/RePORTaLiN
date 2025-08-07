"""
extract_tables_to_jsonl.py

Extract multiple tables from each sheet of an Excel workbook, clean NaN-only columns,
and save each table as a line-delimited JSON (JSONL) file with metadata for RAG ingestion.
"""

import pandas as pd
import os, sys
from pathlib import Path
import json

def expand_user_path(path_str):
    return Path(os.path.expanduser(str(path_str)))

def extract_tables(input_path):
    input_path = expand_user_path(input_path)
    if not input_path.exists():
        print(f"Error: File not found: '{input_path}'", file=sys.stderr)
        return {}
    
    try:
        print(f"Loading workbook from '{input_path}'")
        xls = pd.ExcelFile(input_path, engine="openpyxl")
    except Exception as e:
        print(f"Error loading workbook: {e}", file=sys.stderr)
        return {}
    
    tables_by_sheet, total_tables = {}, 0
    
    for sheet_name in xls.sheet_names:
        print(f"Processing sheet: '{sheet_name}'")
        try:
            df = xls.parse(sheet_name, dtype=object)
            blank_cols = [c for c in df.columns if df[c].isnull().all() and (pd.isna(c) or str(c).startswith("Unnamed"))]
            
            # Group columns
            cols, col_groups, temp = list(df.columns), [], []
            for col in cols:
                if col in blank_cols:
                    if temp: col_groups.append(temp); temp = []
                else: temp.append(col)
            if temp: col_groups.append(temp)
            
            # Extract tables
            tables = []
            for group_cols in col_groups:
                df_sub = df[group_cols]
                blank_rows = df_sub.isnull().all(axis=1)
                row_idx = [0] + blank_rows[blank_rows].index.tolist() + [len(df_sub)]
                
                for start, end in zip(row_idx, row_idx[1:]):
                    table = df_sub.iloc[start:end].dropna(how="all", axis=0).reset_index(drop=True)
                    if table.empty: continue
                    
                    # Clean columns
                    for col in table.columns[table.isnull().all()]:
                        if pd.isna(col) or str(col).startswith("Unnamed"): table.drop(columns=[col], inplace=True)
                        else: table[col] = ""
                    
                    tables.append(table)
                    total_tables += 1
            
            if tables:
                tables_by_sheet[sheet_name] = tables
                print(f"  Extracted {len(tables)} tables from '{sheet_name}'")
                
        except Exception as e:
            print(f"Failed to process sheet '{sheet_name}': {e}", file=sys.stderr)
    
    return tables_by_sheet

def save_tables_as_jsonl(tables_by_sheet, output_dir):
    output_path = expand_user_path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    saved_tables = []
    
    for sheet, tables in tables_by_sheet.items():
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in sheet).strip()
        sheet_dir = output_path / safe_name
        sheet_dir.mkdir(exist_ok=True)
        
        for i, table in enumerate(tables, start=1):
            table_name = f"{safe_name}_table{i}"
            out_file = sheet_dir / f"{table_name}.jsonl"
            
            # Add metadata and save
            table = table.copy()
            table["__sheet__"], table["__table__"] = sheet, table_name
            if out_file.exists(): out_file.unlink()
            
            try:
                table.to_json(out_file, orient="records", lines=True, force_ascii=False)
                saved_tables.append({
                    "sheet": sheet, "table_name": table_name, "path": str(out_file),
                    "rows": len(table), "columns": len(table.columns) - 2
                })
            except Exception as e:
                print(f"Failed to save {sheet}/{table_name}: {e}", file=sys.stderr)
    
    return saved_tables

def load_study_dictionary(file_path=None, json_output_dir=None):
    # Default paths
    input_path = file_path or "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    output_dir = json_output_dir or "data/data_dictionary_and_mapping_specifications/json_output"
    
    # Extract and save tables
    tables = extract_tables(input_path)
    return [] if not tables else save_tables_as_jsonl(tables, output_dir)

if __name__ == "__main__":
    load_study_dictionary()