import pandas as pd
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

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
                
                # Special case: Codelists sheet has 3 distinct tables
                if sheet == "Codelists":
                    logging.info(f"Note: '{sheet}' sheet contains 3 distinct tables instead of 1")
                
                # Identify blank columns (separators)
                blank_cols = [c for c in df.columns if df[c].isnull().all() and 
                              (pd.isna(c) or str(c).startswith("Unnamed"))]
                
                # Group columns by blank separators
                col_groups = []
                current_group = []
                
                for col in df.columns:
                    if col in blank_cols:
                        if current_group:  # Only add non-empty groups
                            col_groups.append(current_group)
                            current_group = []
                    else:
                        current_group.append(col)
                
                if current_group:  # Add the last group if not empty
                    col_groups.append(current_group)
                
                # Process each column group to find tables
                tables = []
                for cols in col_groups:
                    # Get data for these columns
                    subset = df[cols]
                    
                    # Find blank rows (separators)
                    blank_rows = subset.isnull().all(axis=1)
                    blank_indices = [0] + blank_rows[blank_rows].index.tolist() + [len(subset)]
                    
                    # Extract tables between blank rows
                    for i in range(len(blank_indices)-1):
                        start, end = blank_indices[i], blank_indices[i+1]
                        if start == end:  # Skip empty sections
                            continue
                            
                        table = subset.iloc[start:end].dropna(how="all", axis=0).reset_index(drop=True)
                        if not table.empty:
                            # Remove empty columns
                            table = table.drop(columns=[c for c in table.columns 
                                                      if table[c].isnull().all() and 
                                                         (pd.isna(c) or str(c).startswith("Unnamed"))])
                            
                            # Set empty values for named empty columns
                            for col in table.columns:
                                if not pd.isna(col) and not str(col).startswith("Unnamed") and table[col].isnull().all():
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
        # Create folder for sheet
        folder_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in sheet).strip()
        sheet_dir = output_path / folder_name
        sheet_dir.mkdir(exist_ok=True)
        
        # Save each table
        for i, table in enumerate(tables, 1):
            # Generate filename (add number only if multiple tables)
            table_name = f"{folder_name}_table{i if len(tables) > 1 else ''}"
            out_file = sheet_dir / f"{table_name}.jsonl"
            
            # Skip existing files
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
    # Use default paths if not provided
    file_path = file_path or "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    json_output_dir = json_output_dir or "data/data_dictionary_and_mapping_specifications/json_output"
    
    tables = extract_tables(file_path, preserve_na=preserve_na)
    if tables:
        save_tables(tables, json_output_dir)
        return tables
    return {}

if __name__ == "__main__":
    tables = load_study_dictionary()
    logging.info(f"Processed {len(tables)} sheets")