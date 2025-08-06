import pandas as pd
import os

def load_study_dictionary(file_path):
    # Validate input
    if not isinstance(file_path, str) or not os.path.exists(file_path):
        raise FileNotFoundError(f"Invalid or non-existent file: {file_path}")
    
    try:
        # Load workbook and initialize containers
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        codelists_df, site_notes_df = pd.DataFrame(), pd.DataFrame()
        form_sheets = {}

        # Process each sheet
        for sheet in xls.sheet_names:
            try:
                df = xls.parse(sheet)
                df.columns = [str(col).strip() for col in df.columns]
                
                if sheet == "New Codelists": codelists_df = df
                elif sheet == "Notes": site_notes_df = df
                elif sheet.startswith("tbl"): form_sheets[sheet] = df
            except Exception as e:
                print(f"Warning: Error processing sheet '{sheet}': {str(e)}")

        return {
            "codelists": codelists_df,
            "site_notes": site_notes_df,
            "forms": form_sheets
        }
    except Exception as e:
        raise ValueError(f"Failed to process Excel file: {str(e)}")

# # Example usage
# if __name__ == "__main__":
#     file_path = "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
#     data = load_study_dictionary(file_path)
#     print(f"Loaded 'New Codelists' with {len(data['codelists'])} rows.")
#     print(f"Loaded 'Notes' with {len(data['site_notes'])} rows.")
#     print(f"Loaded {len(data['forms'])} form sheets:")
#     for sheet_name, df in data['forms'].items():
#         print(f"   - {sheet_name} ({len(df)} rows)")
