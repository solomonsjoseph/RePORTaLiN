import pandas as pd
import logging
from pathlib import Path
import os

# Configure logging without INFO:root prefix
logging.basicConfig(format='%(message)s', level=logging.INFO)

def expand_path(path_str):
    return Path(path_str).expanduser()

def group_columns(df):
    blank_cols = [c for c in df.columns if df[c].isnull().all() and (pd.isna(c) or str(c).startswith("Unnamed"))]
    col_groups, temp = [], []
    for col in df.columns:
        if col in blank_cols:
            if temp: col_groups.append(temp); temp = []
        else:
            temp.append(col)
    if temp: col_groups.append(temp)
    return col_groups

def group_rows(df_sub):
    blank_rows = df_sub.isnull().all(axis=1)
    row_idx = [0] + blank_rows[blank_rows].index.tolist() + [len(df_sub)]
    return [(row_idx[i], row_idx[i+1]) for i in range(len(row_idx)-1)]

def extract_tables(input_path, preserve_na=True):
    """Extract tables from Excel file by identifying column/row groups."""
    input_path = Path(os.path.expanduser(str(input_path)))
    if not input_path.exists():
        logging.error(f"File not found: {input_path}")
        return {}
    
    try:
        xls = pd.ExcelFile(input_path, engine="openpyxl")
        tables_by_sheet = {}
        
        for sheet in xls.sheet_names:
            try:
                # Parse with NA preservation if requested
                parse_options = {"dtype": object}
                if preserve_na:
                    parse_options.update({"keep_default_na": False, "na_values": []})
                df = xls.parse(sheet, **parse_options)
                
                # Identify blank columns and group by them
                blank_cols = [c for c in df.columns if df[c].isnull().all() and 
                             (pd.isna(c) or str(c).startswith("Unnamed"))]
                
                # Group columns
                col_groups, temp = [], []
                for col in df.columns:
                    if col in blank_cols:
                        if temp: col_groups.append(temp); temp = []
                    else: temp.append(col)
                if temp: col_groups.append(temp)
                
                # Extract tables
                tables = []
                for group_cols in col_groups:
                    df_sub = df[group_cols]
                    blank_rows = df_sub.isnull().all(axis=1)
                    row_indices = [0] + blank_rows[blank_rows].index.tolist() + [len(df_sub)]
                    
                    # Create tables based on row groups
                    for i in range(len(row_indices)-1):
                        start, end = row_indices[i], row_indices[i+1]
                        table = df_sub.iloc[start:end].dropna(how="all", axis=0).reset_index(drop=True)
                        if not table.empty:
                            # Clean all-null columns
                            for col in table.columns[table.isnull().all()]:
                                if pd.isna(col) or str(col).startswith("Unnamed"):
                                    table.drop(columns=[col], inplace=True)
                                else:
                                    table[col] = ""
                            tables.append(table)
                
                if tables:
                    tables_by_sheet[sheet] = tables
                    logging.info(f"Extracted {len(tables)} tables from '{sheet}'")
                    
            except Exception as e:
                logging.error(f"Failed to process sheet '{sheet}': {e}")
        
        return tables_by_sheet
        
    except Exception as e:
        logging.error(f"Error loading workbook: {e}")
        return {}

def save_tables(tables_by_sheet, output_dir):
    """Save extracted tables as JSONL files with metadata."""
    output_path = Path(os.path.expanduser(str(output_dir)))
    output_path.mkdir(parents=True, exist_ok=True)
    
    for sheet, tables in tables_by_sheet.items():
        sheet_dir = output_path / sheet.replace(" ", "_")
        sheet_dir.mkdir(exist_ok=True)
        
        for i, table in enumerate(tables, 1):
            # Only add number if multiple tables
            if len(tables) == 1:
                table_name = f"{sheet}_table"
            else:
                table_name = f"{sheet}_table{i}"
            
            out_file = sheet_dir / f"{table_name}.jsonl"
            
            # Don't overwrite existing files
            if out_file.exists():
                logging.info(f"File already exists, not overwriting: {out_file}")
                continue
                
            # Add metadata and save
            table = table.copy()
            table["__sheet__"] = sheet
            table["__table__"] = table_name
            
            try:
                table.to_json(out_file, orient="records", lines=True, force_ascii=False)
                logging.info(f"Saved {len(table)} rows to {out_file}")
            except Exception as e:
                logging.error(f"Failed to save {table_name}: {e}")
    
    return True

def load_study_dictionary(file_path=None, json_output_dir=None, preserve_na=True):
    """Load study dictionary from Excel and save as JSONL files."""
    file_path = file_path or "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    json_output_dir = json_output_dir or "data/data_dictionary_and_mapping_specifications/json_output"
    
    tables = extract_tables(file_path, preserve_na=preserve_na)
    if tables:
        save_tables(tables, json_output_dir)
        return tables  # Return the tables dictionary instead of just the count
    return {}

if __name__ == "__main__":
    num_tables = load_study_dictionary()
    logging.info(f"Processed {num_tables} sheets")