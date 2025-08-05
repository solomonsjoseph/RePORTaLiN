import pandas as pd

def load_study_dictionary(file_path):
    # Load the workbook
    xls = pd.ExcelFile(file_path, engine='openpyxl') # openpyxl is more robust for .xlsx files

    # Extract all sheet names
    sheet_names = xls.sheet_names

    # Initialize containers
    codelists_df = None
    site_notes_df = None
    form_sheets = {}

    # Define expected columns for validation
    expected_codelist_columns = ['Codelist', 'Descriptors', 'Codes']
    expected_notes_columns = ['Site', 'Country', 'N']
    expected_form_columns = ['Data Bank ID', 'Module', 'Form', 'Question', 'Type', 'Code List or format']

    # Iterate through sheets
    for sheet in sheet_names:
        df = xls.parse(sheet)
        df.columns = [str(col).strip() for col in df.columns]  # Normalize column names

        if sheet == "New Codelists":
            missing = [col for col in expected_codelist_columns if col not in df.columns]
            if missing:
                print(f"Warning: Missing columns in 'New Codelists': {missing}")
            codelists_df = df

        elif sheet == "Notes":
            missing = [col for col in expected_notes_columns if col not in df.columns]
            if missing:
                print(f"Warning: Missing columns in 'Notes': {missing}")
            site_notes_df = df

        elif sheet.startswith("tbl"):
            missing = [col for col in expected_form_columns if col not in df.columns]
            if missing:
                print(f"Warning: Missing columns in '{sheet}': {missing}")
            form_sheets[sheet] = df

    # Return structured data
    return {
        "codelists": codelists_df,
        "site_notes": site_notes_df,
        "forms": form_sheets
    }

# # Example usage
# if __name__ == "__main__":
#     file_path = "data/Data Dictionary and Mapping Specification/RePORT DEB to Tables mapping  2.xlsx"
#     data = load_study_dictionary(file_path)

#     print(f"Loaded 'New Codelists' with {len(data['codelists'])} rows.")
#     print(f"Loaded 'Notes' with {len(data['site_notes'])} rows.")
#     print(f"Loaded {len(data['forms'])} form sheets: {list(data['forms'].keys())}")
