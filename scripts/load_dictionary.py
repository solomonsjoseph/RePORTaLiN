import pandas as pd
import os
import sys

# --- Path Setup ---
# Add the project root to the Python path to allow importing the config file.
# This makes the script runnable from anywhere.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from scripts.utils import logging_utils as log
import config  # Import the centralized configuration

# --- Helper Functions ---

def _deduplicate_columns(columns):
    """Makes column names unique by appending a suffix to duplicates."""
    new_cols, counts = [], {}
    for col in columns:
        col_str = str(col) if pd.notna(col) else "Unnamed"
        if col_str in counts:
            counts[col_str] += 1
            new_cols.append(f"{col_str}_{counts[col_str]}")
        else:
            new_cols.append(col_str)
            counts[col_str] = 0
    return new_cols

def _split_sheet_into_tables(df):
    """Splits a DataFrame into a grid of smaller table DataFrames based on empty rows/columns."""
    # Find empty rows to identify horizontal boundaries
    empty_rows = df.index[df.isnull().all(axis=1)].tolist()
    row_boundaries = [-1] + empty_rows + [df.shape[0]]
    
    horizontal_strips = []
    for i in range(len(row_boundaries) - 1):
        start_row, end_row = row_boundaries[i] + 1, row_boundaries[i+1]
        if start_row < end_row:
            horizontal_strips.append(df.iloc[start_row:end_row])

    # Split horizontal strips by empty columns to get final tables
    all_tables = []
    for strip in horizontal_strips:
        empty_cols = strip.columns[strip.isnull().all(axis=0)].tolist()
        col_boundaries = [-1] + empty_cols + [df.shape[1]]
        for j in range(len(col_boundaries) - 1):
            start_col, end_col = col_boundaries[j] + 1, col_boundaries[j+1]
            if start_col < end_col:
                table_df = strip.iloc[:, start_col:end_col].copy()
                table_df.dropna(how='all', axis=0, inplace=True)
                table_df.dropna(how='all', axis=1, inplace=True)
                if not table_df.empty:
                    all_tables.append(table_df)
    return all_tables

def _process_and_save_tables(all_tables, sheet_name, output_dir):
    """Processes, adds metadata to, and saves a list of tables."""
    folder_name = "".join(c for c in sheet_name if c.isalnum() or c in "._- ").strip()
    sheet_dir = os.path.join(output_dir, folder_name)
    os.makedirs(sheet_dir, exist_ok=True)
    
    ignore_mode_activated = False
    
    for i, table_df in enumerate(all_tables):
        table_df.reset_index(drop=True, inplace=True)
        
        # Check for "ignore below" marker in the first row
        if not ignore_mode_activated:
            header_row = table_df.iloc[0]
            for idx, col in enumerate(header_row):
                if "ignore below" in str(col).lower().strip():
                    log.info(f"Found 'ignore below' in table {i+1}. Subsequent tables will be saved to 'extraas' folder.")
                    ignore_mode_activated = True
                    # Remove the marker column
                    table_df = table_df.drop(table_df.columns[idx], axis=1)
                    break
        
        # Set headers and clean up the table
        table_df.columns = _deduplicate_columns(table_df.iloc[0])
        table_df = table_df.iloc[1:].reset_index(drop=True)
        if table_df.empty:
            continue
        
        # Determine output path based on whether the "ignore" marker was found
        if ignore_mode_activated:
            extraas_dir = os.path.join(sheet_dir, "extraas")
            os.makedirs(extraas_dir, exist_ok=True)
            table_suffix = f"_table_{i+1}" if len(all_tables) > 1 else "_table"
            table_name = f"extraas{table_suffix}"
            output_path = os.path.join(extraas_dir, f"{table_name}.jsonl")
            metadata_name = f"{folder_name}_extraas{table_suffix}"
        else:
            table_suffix = f"_table_{i+1}" if len(all_tables) > 1 else "_table"
            table_name = f"{folder_name}{table_suffix}"
            output_path = os.path.join(sheet_dir, f"{table_name}.jsonl")
            metadata_name = table_name
        
        # Skip saving if file already exists and is not empty
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            log.warning(f"File exists and is not empty. Skipping: {output_path}")
            continue
        
        # Add metadata and save to JSONL
        table_df['__sheet__'] = sheet_name
        table_df['__table__'] = metadata_name
        table_df.to_json(output_path, orient='records', lines=True, force_ascii=False)
        log.info(f"Saved {len(table_df)} rows to '{output_path}'")

# --- Main Processing Function ---
def process_excel_file(excel_path, output_dir, preserve_na=True):
    """
    Extracts all distinct tables from an Excel file and saves them as JSONL.
    """
    if not os.path.exists(excel_path):
        log.error(f"Input file not found: {excel_path}")
        return

    log.info(f"Output will be saved in: '{output_dir}'")
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        log.error(f"Cannot create output directory {output_dir}: {e}")
        return

    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        log.error(f"Failed to read Excel workbook: {e}")
        return

    log.info(f"Processing workbook: '{excel_path}'")
    for sheet_name in xls.sheet_names:
        try:
            log.info(f"--- Processing sheet: '{sheet_name}' ---")
            
            parse_options = {'header': None}
            if preserve_na:
                parse_options.update({'keep_default_na': False, 'na_values': ['']})
            
            df = pd.read_excel(xls, sheet_name=sheet_name, **parse_options)
            
            all_tables = _split_sheet_into_tables(df)

            if not all_tables:
                log.info("No data tables found on this sheet.")
                continue

            log.info(f"Found {len(all_tables)} table(s) on this sheet.")
            _process_and_save_tables(all_tables, sheet_name, output_dir)

        except Exception as e:
            log.error(f"❌ An unexpected error occurred on sheet '{sheet_name}' ❌: {e}", exc_info=True)

    log.success("Excel file processing complete!")

def load_study_dictionary(file_path=None, json_output_dir=None, preserve_na=True):
    """Load study dictionary from Excel and save as JSONL files."""
    # Use paths from config file if not provided
    file_path = file_path or config.DICTIONARY_EXCEL_FILE
    json_output_dir = json_output_dir or config.DICTIONARY_JSON_OUTPUT_DIR
    
    process_excel_file(
        excel_path=file_path,
        output_dir=json_output_dir,
        preserve_na=preserve_na
    )
    
    return True

# --- Script Entry Point ---
if __name__ == "__main__":
    # When run directly, use settings from the config file.
    load_study_dictionary(preserve_na=True)
    
    log.success(f"Processing complete for data dictionary from {config.DICTIONARY_EXCEL_FILE}")