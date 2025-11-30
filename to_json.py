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


def excel_to_json(excel_files):
    """
    Converts an Excel file to a JSON file.

    Args:
        excel_file_path (str): The path to the Excel file.
        output_json_path (str): The path to save the JSON output.
    """
    chunk_id = 0
    data = []
    try:
        for excel_file in excel_files:
            all_sheets = pd.read_excel(excel_file, sheet_name=None)
            df = pd.concat(all_sheets.values(), ignore_index=True)
            last_utvar = None
            df.columns = {col: col.lower() for col in df.columns}
            processes_col = None
            department_col = None
            try:
                for col in df.columns:
                    if col.find("proces") != -1:
                        processes_col = col
                print(df.columns, file=sys.stderr)
                for col in df.columns:
                    if col.find("oddělení") != -1:
                        department_col = col
                        print(col, file=sys.stderr)
                for idx, row in df.iterrows():
                    # Skip row if essential columns missing
                    if (processes_col is None or department_col is None):
                        continue
                    if not isinstance(row[processes_col], str):
                        continue
                    # Take care of "assumed" dept names
                    if not isinstance(row[department_col], str) and isinstance(row[processes_col], str):
                        df.loc[idx, department_col] = last_utvar
                        last_utvar = row[department_col]
                filename = os.path.basename(excel_file)

                for index, row in df.iterrows():
                    chunk_list = []
                    row_dict = {}
                    processes_col = None
                    for col in df.columns:
                        value = row[col]
                        if isinstance(value, str):
                            s = value.strip(' ·\t\xA0')  # Strip whitespace
                            chunk_list.append(f"{col}: {s}")
                    match = re.search(r"Zhodnocení procesů (.*?)(\.[^.]*)?$", filename)
                    department_name = "Unknown"
                    if match:
                        department_name = match.group(1).strip()
                        utvar_s = row[department_col]
                        row_dict['id'] = chunk_id
                        chunk_id += 1
                        row_dict['filename'] = filename
                        row_dict['content'] = ";".join(chunk_list)
                        data.append(row_dict)
            except FileNotFoundError:
                print(f"Error: The file {excel_file} was not found.", file=sys.stderr)
                return
            except Exception as e:
                print(f"An error occurred while reading {excel_file}: {e}", file=sys.stderr)
                return

        json.dump(data, sys.stdout, indent=4, ensure_ascii=False)
    except FileNotFoundError:
        print(f"Error: File not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert XLSX to JSON.')
    parser.add_argument('excel_files', nargs='+', type=str, help='Paths to the XLSX files')

    args = parser.parse_args()
    excel_to_json(args.excel_files)
