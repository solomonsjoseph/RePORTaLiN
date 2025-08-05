# main.py

from scripts.load_dictionary import load_study_dictionary

def main():
    print("Step 1: Loading Data Dictionary and Mapping Specification...")

    # Path to the Excel workbook
    file_path = "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"

    # Load and extract structured data
    study_data = load_study_dictionary(file_path)

    # Summary output
    print(f"Loaded 'New Codelists' with {len(study_data['codelists'])} rows.")
    print(f"Loaded 'Notes' with {len(study_data['site_notes'])} rows.")
    print(f"Loaded {len(study_data['forms'])} form sheets:")
    for sheet_name in study_data['forms']:
        print(f"   - {sheet_name} ({len(study_data['forms'][sheet_name])} rows)")

    # Placeholder for next steps
    print("\nNext: Parsing Annotated PDFs...")

if __name__ == "__main__":
    main()
