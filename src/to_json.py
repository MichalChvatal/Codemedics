#!/usr/bin/env python3
import pandas as pd
import json
import argparse
import sys
import os
import re

department_full_names = {
    "CP":		"Centrální podatelna",
    "ČR":		"Česká republika",
    "EO":		"Ekonomický odbor",
    "EP":		"Evropský parlament",
    "EU":		"Evropská unie",
    "IŘD":		"interní řídicí dokumentace",
    "IT":		"informační technologie",
    "KŘ":		"Kancelář ředitele",
    "LN":		"Lotus Notes",
    "LPP":		"léčebná a preventivní péče",
    "NLZP":		"nelékařský zdravotnický pracovník",
    "NP":		"nadzemní podlaží",
    "NS":		"nákladové středisko",
    "OP":		"Oddělení pověřence",
    "OSS":		"Oddělení spisové služby",
    "PO":		"požární ochrana",
    "ŘDF":		"řízená dokumentace firmy",
    "SŘK":		"systém řízení kvality",
    "SÚJB":		"Státní ústav pro jadernou bezpečnost",
    "SÚKL":		"Státní ústav pro kontrolu léčiv",
    "ÚOOÚ":		"Úřad pro ochranu osobních údajů",
    "ÚSV":		"úplné středoškolské vzdělání",
    "VŠV":		"vysokoškolské vzdělání",

    "CI":		"Centrum Informatiky",
    "IO":		"Investiční Odbor",
    "OIAK": "Oddělení interního auditu a kontroly",
    "OHTS": "???",
    "OPV": "Odbor právních věcí",
    "OPZ": "???",
    "ÚVV": "??? Vědy a Výzkumu"
}


def excel_to_json(excel_file):
    """
    Convert a single Excel file to JSON (stdout).
    Works with ANY Excel file structure. No required columns.
    """

    # Validate input path
    if not isinstance(excel_file, str):
        print("Error: excel_file must be a string.", file=sys.stderr)
        return None

    if not os.path.exists(excel_file):
        print(f"Error: File does not exist: {excel_file}", file=sys.stderr)
        return None

    if not os.path.isfile(excel_file):
        print(f"Error: Not a file: {excel_file}", file=sys.stderr)
        return None

    print(f"Processing Excel: {excel_file}", file=sys.stderr)

    data = []
    chunk_id = 0

    try:
        # Load all sheets into a single dataframe
        all_sheets = pd.read_excel(excel_file, sheet_name=None)
        df = pd.concat(all_sheets.values(), ignore_index=True)

        # Normalize column names
        df.columns = [str(col).strip().lower() for col in df.columns]

        filename = os.path.basename(excel_file)

        # Convert rows into chunks
        for _, row in df.iterrows():
            chunk_list = []

            for col, value in row.items():
                if isinstance(value, str):
                    value_clean = value.strip(" ·\t\xA0")
                    if value_clean:
                        chunk_list.append(f"{col}: {value_clean}")
                elif pd.notna(value):
                    # Include numeric, datetime, or other clean values
                    chunk_list.append(f"{col}: {value}")

            if not chunk_list:
                continue

            data.append({
                "id": chunk_id,
                "filename": filename,
                "content": "; ".join(chunk_list)
            })

            chunk_id += 1

        # Output to stdout
        json.dump(data, sys.stdout, indent=4, ensure_ascii=False)
        return data

    except Exception as e:
        print(f"Error: Failed to parse Excel file: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert XLSX to JSON.')
    parser.add_argument('excel_files', nargs='+', type=str, help='Paths to the XLSX files')

    args = parser.parse_args()
    excel_to_json(args.excel_files)
