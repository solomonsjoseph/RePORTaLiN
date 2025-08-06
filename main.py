# main.py

from scripts.load_dictionary import load_study_dictionary
import sys
import os

def main():
    print("Step 1: Loading Data Dictionary and Mapping Specification...")
    
    # Path to the Excel workbook
    file_path = "data/data_dictionary_and_mapping_specifications/RePORT_DEB_to_Tables_mapping.xlsx"
    
    # Process the data dictionary
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        study_data = load_study_dictionary(file_path)
        
        # Print summary information
        print(f"Loaded 'New Codelists' with {len(study_data['codelists'])} rows.")
        print(f"Loaded 'Notes' with {len(study_data['site_notes'])} rows.")
        print(f"Loaded {len(study_data['forms'])} form sheets:")
        for sheet_name, df in study_data['forms'].items():
            print(f"   - {sheet_name} ({len(df)} rows)")
        
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
        
    print("\nNext: Parsing Annotated PDFs...")

if __name__ == "__main__":
    main()
