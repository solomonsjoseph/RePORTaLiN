# main.py

from scripts.load_dictionary import load_study_dictionary
import sys
import os

def main():
    print("Step 1: Loading Data Dictionary and Mapping Specification...")

    # Use default paths
    # tables_info = load_study_dictionary(None)
    # print(f"Extracted {len(tables_info)} tables")

    # Or specify a custom path
    custom_path = "/custom/path/to/json_or_excel_file"
    tables_info = load_study_dictionary(file_path=None, json_output_dir=None)
    print(f"Extracted {len(tables_info)} tables")

    # # Or specify a custom path
    # custom_path = "path/to/different/excel_file.xlsx"
    # tables_info = load_study_dictionary(custom_path)

    print("\nNext: Parsing Annotated PDFs...")

if __name__ == "__main__":
    main()
