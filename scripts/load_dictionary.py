import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

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
    input_path = expand_path(input_path)
    if not input_path.exists():
        logging.error(f"File not found: {input_path}")
        return {}

    try:
        xls = pd.ExcelFile(input_path, engine="openpyxl")
    except Exception as e:
        logging.error(f"Error loading workbook: {e}")
        return {}

    tables_by_sheet = {}
    total_tables = 0
    
    for sheet in xls.sheet_names:
        try:
            # Parse sheet with NA preservation if requested
            if preserve_na:
                df = xls.parse(sheet, dtype=object, keep_default_na=False, na_values=[])
            else:
                df = xls.parse(sheet, dtype=object)
                
            # Identify blank columns (original logic from working code)
            blank_cols = [c for c in df.columns if df[c].isnull().all() and (pd.isna(c) or str(c).startswith("Unnamed"))]
            
            # Group columns - using original algorithm
            cols, col_groups, temp = list(df.columns), [], []
            for col in cols:
                if col in blank_cols:
                    if temp: 
                        col_groups.append(temp)
                        temp = []
                else: 
                    temp.append(col)
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
                    
                    # Clean columns (original logic from working code)
                    for col in table.columns[table.isnull().all()]:
                        if pd.isna(col) or str(col).startswith("Unnamed"):
                            table.drop(columns=[col], inplace=True)
                        else:
                            table[col] = ""
                    
                    tables.append(table)
                    total_tables += 1
            
            if tables:
                tables_by_sheet[sheet] = tables
                logging.info(f"Extracted {len(tables)} tables from '{sheet}'")
                
        except Exception as e:
            logging.error(f"Failed to process sheet '{sheet}': {e}")
    
    logging.info(f"Total tables extracted: {total_tables}")
    return tables_by_sheet

def save_tables(tables_by_sheet, output_dir, merge=False):
    output_path = expand_path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    summary = []

    # Debug: Log all sheet names at the start
    logging.info(f"Processing sheets: {list(tables_by_sheet.keys())}")
    
    for sheet, tables in tables_by_sheet.items():
        # Clean the sheet name to avoid invisible characters
        clean_sheet = sheet.strip()
        folder_name = clean_sheet.replace(" ", "_")
        
        # Debug: Log the exact conversion
        logging.info(f"Sheet name: '{sheet}' → Folder name: '{folder_name}'")
        
        sheet_dir = output_path / folder_name
        sheet_dir.mkdir(exist_ok=True)
        
        if merge:
            # Merge logic remains unchanged
            merged = pd.concat(tables, ignore_index=True)
            table_name = f"{sheet}_merged_table"
            merged["__sheet__"], merged["__table__"] = sheet, table_name
            out_file = sheet_dir / f"{table_name}.jsonl"
            
            # CHANGE HERE: Check if file exists, don't overwrite
            if out_file.exists():
                logging.info(f"File already exists, not overwriting: {out_file}")
            else:
                merged.to_json(out_file, orient="records", lines=True, force_ascii=False)
            
            summary.append({
                "sheet": sheet, 
                "table_name": table_name,
                "path": str(out_file),
                "rows": len(merged),
                "columns": len(merged.columns) - 2,  # Subtract __sheet__ and __table__
                "exists": out_file.exists()
            })
        else:
            # Only add numbers if multiple tables exist
            for i, table in enumerate(tables, 1):
                if len(tables) == 1:
                    table_name = f"{sheet}_table"
                else:
                    table_name = f"{sheet}_table{i}"
                
                table = table.copy()
                table["__sheet__"], table["__table__"] = sheet, table_name
                out_file = sheet_dir / f"{table_name}.jsonl"
                
                # CHANGE HERE: Check if file exists, don't overwrite
                if out_file.exists():
                    logging.info(f"File already exists, not overwriting: {out_file}")
                else:
                    table.to_json(out_file, orient="records", lines=True, force_ascii=False)
                
                summary.append({
                    "sheet": sheet, 
                    "table_name": table_name,
                    "path": str(out_file),
                    "rows": len(table),
                    "columns": len(table.columns) - 2,  # Subtract __sheet__ and __table__
                    "exists": out_file.exists()
                })
    
    pd.DataFrame(summary).to_json(output_path / "summary.json", orient="records", lines=True)
    return summary

def load_study_dictionary(file_path=None, json_output_dir=None, merge=False, preserve_na=True):
    file_path = file_path or "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    json_output_dir = json_output_dir or "data/data_dictionary_and_mapping_specifications/json_output"
    tables = extract_tables(file_path, preserve_na=preserve_na)
    return save_tables(tables, json_output_dir, merge=merge) if tables else []

if __name__ == "__main__":
    load_study_dictionary()