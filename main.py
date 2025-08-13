# main.py

from scripts.load_dictionary import load_study_dictionary
import sys
import os

def main():

    print("Step 1: Loading Data Dictionary and Mapping Specification...")
    # Use defaults or pass file_path and json_output_dir; preserve_na defaults to True.
    tables_info = load_study_dictionary(file_path=None, json_output_dir=None)
    print(f"Extracted {len(tables_info)} tables")

    print("\nStep 2: Parsing Annotated PDFs...")

if __name__ == "__main__":
    main()
