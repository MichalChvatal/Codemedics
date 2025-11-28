#!/usr/bin/env python3
import pandas as pd
import json
import argparse

def excel_to_json(excel_file_path, output_json_path):
    """
    Converts an Excel file to a JSON file.

    Args:
        excel_file_path (str): The path to the Excel file.
        output_json_path (str): The path to save the JSON output.
    """
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(excel_file_path, usecols=['Útvar/oddělení', 'Proces', 'Vazba na Organizační řád IO'])

        last_utvar = None
        for idx, row in df.iterrows():
            if not isinstance(row['Útvar/oddělení'], str):
                df.loc[idx, 'Útvar/oddělení'] = last_utvar
            last_utvar = row['Útvar/oddělení']

        # Convert the DataFrame to a list of dictionaries
        data = df.to_dict(orient='records')

        # Write the data to a JSON file
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)  # indent for pretty formatting

        print(f"Successfully converted {excel_file_path} to {output_json_path}")

    except FileNotFoundError:
        print(f"Error: The file {excel_file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert XLSX to JSON.')
    parser.add_argument('excel_file', type=str, help='Path to the XLSX file')
    parser.add_argument('json_file', type=str, help='Path to the output JSON file')

    args = parser.parse_args()
    excel_to_json(args.excel_file, args.json_file)
