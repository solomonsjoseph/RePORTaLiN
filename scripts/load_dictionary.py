import pandas as pd
import os
from scripts.utils import logging_utils as log

# --- Helper function to deduplicate column names ---
def deduplicate_columns(columns):
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

# --- Step 2: Main Function to Extract and Save Tables ---
def process_excel_file(excel_path, output_dir, preserve_na=True):
    """
    Extracts all distinct tables from an Excel file and saves them as JSONL.

    Args:
        excel_path (str): Path to the source Excel file.
        output_dir (str): The main directory where output folders will be created.
        preserve_na (bool): If True, reads blank cells as empty strings instead of NaN.
    """
    # --- Setup Paths ---
    if not os.path.exists(excel_path):
        log.error(f"Input file not found: {excel_path}")
        return

    log.info(f"Output will be saved in: '{output_dir}'")
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        log.error(f"Cannot create output directory {output_dir}: {e}")
        return

    # --- Read Excel File ---
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        log.error(f"Failed to read Excel workbook: {e}")
        return

    log.info(f"Processing workbook: '{excel_path}'")
    for sheet_name in xls.sheet_names:
        try:
            log.info(f"--- Processing sheet: '{sheet_name}' ---")

            # Define parsing options based on preserve_na flag
            parse_options = {'header': None}
            if preserve_na:
                parse_options.update({'keep_default_na': False, 'na_values': ['']})
                log.info("Reading sheet with 'preserve_na' mode enabled.")
            
            df = pd.read_excel(xls, sheet_name=sheet_name, **parse_options)
            
            # --- Grid-Splitting Logic ---
            empty_rows = df.index[df.isnull().all(axis=1)].tolist()
            row_boundaries = [-1] + empty_rows + [df.shape[0]]
            horizontal_strips = []
            for i in range(len(row_boundaries) - 1):
                start_row, end_row = row_boundaries[i] + 1, row_boundaries[i+1]
                if start_row < end_row:
                    horizontal_strips.append(df.iloc[start_row:end_row])

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

            if not all_tables:
                log.info("No data tables found on this sheet.")
                continue

            log.info(f"Found {len(all_tables)} table(s) on this sheet.")

            # --- Clean, Add Metadata, and Save Tables ---
            folder_name = "".join(c for c in sheet_name if c.isalnum() or c in "._- ").strip()
            sheet_dir = os.path.join(output_dir, folder_name)
            os.makedirs(sheet_dir, exist_ok=True)
            
            # Flag for "ignore below" detection
            ignore_mode_activated = False
            
            # Process all tables
            for i, table_df in enumerate(all_tables):
                table_df.reset_index(drop=True, inplace=True)
                
                # Check for "ignore below" in headers (case-insensitive)
                if not ignore_mode_activated:
                    header_row = table_df.iloc[0]
                    for idx, col in enumerate(header_row):
                        if "ignore below" in str(col).lower().strip():
                            log.info(f"Found 'ignore below' in table {i+1}. Tables will be saved to extraas folder.")
                            ignore_mode_activated = True
                            # Remove the "ignore below" column
                            table_df = table_df.drop(table_df.columns[idx], axis=1)
                            break
                
                # Set headers and prepare data
                table_df.columns = deduplicate_columns(table_df.iloc[0])
                table_df = table_df.iloc[1:].reset_index(drop=True)
                if table_df.empty:
                    continue
                
                # Set output location based on ignore_mode
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
                
                # Skip existing files
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    log.warning(f"File exists and is not empty. Skipping: {output_path}")
                    continue
                
                # Add metadata and save
                table_df['__sheet__'] = sheet_name
                table_df['__table__'] = metadata_name
                table_df.to_json(output_path, orient='records', lines=True, force_ascii=False)
                log.info(f"Saved {len(table_df)} rows to '{output_path}'")

        except Exception as e:
            log.error(f"❌ An unexpected error occurred on sheet '{sheet_name}' ❌: {e}", exc_info=True)
    
    log.success("Processing complete! Tables after 'ignore below' markers saved to 'extraas' subfolder.")

def load_study_dictionary(file_path=None, json_output_dir=None, preserve_na=True):
    """Load study dictionary from Excel and save as JSONL files."""
    # Use default paths if not provided
    file_path = file_path or "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    json_output_dir = json_output_dir or "data/data_dictionary_and_mapping_specifications/json_output"
    
    # Use the new process_excel_file function to replace the old extract_tables + save_tables flow
    process_excel_file(
        excel_path=file_path,
        output_dir=json_output_dir,
        preserve_na=preserve_na
    )
    
    return True

# --- Step 3: DEFINE PATHS AND RUN THE SCRIPT ---
if __name__ == "__main__":
    # Default values
    source_excel_file = "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    save_location_path = "data/data_dictionary_and_mapping_specifications/json_output"
    PRESERVE_BLANK_CELLS = True
    
    # Run the load_study_dictionary function which calls process_excel_file
    load_study_dictionary(
        file_path=source_excel_file,
        json_output_dir=save_location_path,
        preserve_na=PRESERVE_BLANK_CELLS
    )
    
    log.success(f"Processing complete for data dictionary and mapping from {source_excel_file} at {save_location_path}")