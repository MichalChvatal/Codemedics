import os
import re
import csv
import json
import mammoth
import subprocess
import unicodedata
from to_json import excel_to_json
from db_insertion import insert_chunks
# import pdfplumber

# ------------------------------------------
# CONFIG
# ------------------------------------------

SECTION_REGEX = r"(?m)^(\d+(?:\.\d+)*)(?:\.?)\s+(.*)"


# ------------------------------------------
# FILE LOADING HELPERS
# ------------------------------------------

def load_txt(path: str) -> str:
    """Reads .txt files."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_csv(path: str) -> str:
    """Reads CSV into a simple text representation."""
    rows = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(" | ".join(row))
    return "\n".join(rows)


# def load_pdf(path: str) -> str:
#     """Extract text from PDF using pdfplumber."""
#     all_text = []
#     try:
#         with pdfplumber.open(path) as pdf:
#             for page in pdf.pages:
#                 text = page.extract_text() or ""
#                 all_text.append(text)
#     except Exception as e:
#         print(f"PDF read error {path}: {e}")
#         return ""

#     return "\n".join(all_text)


def load_doc(path: str) -> str:
    """Reads legacy .doc files using antiword."""
    try:
        raw = subprocess.check_output(["antiword", path])
        return raw.decode("utf-8", errors="ignore")
    except FileNotFoundError:
        raise RuntimeError("antiword is not installed. Install it first.")
    except Exception as e:
        print(f"Failed to load .doc: {path}: {e}")
        return ""


def load_docx(path: str) -> str:
    """Reads .docx files using mammoth."""
    try:
        with open(path, "rb") as f:
            result = mammoth.extract_raw_text(f)
            return result.value or ""
    except Exception as e:
        print(f"Failed to load .docx: {path}: {e}")
        return ""


# ------------------------------------------
# MAIN DISPATCH FUNCTION (IMPORT THIS)
# ------------------------------------------

def load_document(path: str) -> str:
    """Loads any supported document based on extension."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".txt":
        return load_txt(path)
    if ext == ".csv":
        return load_csv(path)
    # if ext == ".pdf":
    #     return load_pdf(path)
    if ext == ".xlsx":
        return excel_to_json(path)
    if ext == ".doc":
        return load_doc(path)
    if ext == ".docx":
        return load_docx(path)

    print(f"Unsupported extension '{ext}' for {path}")
    return ""


# ------------------------------------------
# CHUNKING
# ------------------------------------------

def chunk_document(text: str, filename: str) -> list[dict]:
    """Splits text into structured chunks based on numbered headings."""

    matches = list(re.finditer(SECTION_REGEX, text))

    if not matches:
        return [{
            "id": "1",
            "filename": filename,
            "content": re.sub(r"\s+", " ", text).strip(),
        }]

    chunks = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)

        section_id = matches[i].group(1)
        section_title = matches[i].group(2)

        section_text = text[start:end]
        normalized = re.sub(r"\s+", " ", section_text).strip()

        chunks.append({
            "id": section_id,
            "filename": filename,
            "title": section_title,
            "content": normalized,
        })

    return chunks

def save_chunks(chunks: list[dict], path: str):
    """
    Saves the list of chunk dictionaries to a JSON file.
    """
    print(f"Saving {len(chunks)} total chunks to: {path}")
    with open(path, "w", encoding="utf-8") as f:
        # ensure_ascii=False supports non-ASCII characters like Czech/Slovak diacritics
        json.dump(chunks, f, ensure_ascii=False, indent=2)


# ------------------------------------------
# SAVE / LOAD HELPERS
# ------------------------------------------

def save_chunks(chunks: list[dict], output_path: str):
    """Saves chunks to JSON."""
    print("output_path for the chunks is " + output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


# ------------------------------------------
# OPTIONAL: PROCESS ENTIRE FOLDERS
# ------------------------------------------

def process_folder(folder_path: str) -> list[dict]:
    """
    Loads every supported file in a folder and returns all chunks as a list.
    """
    all_chunks = []

    for filename in os.listdir(folder_path):
        full = os.path.join(folder_path, filename)
        if not os.path.isfile(full):
            continue

        text = load_document(full)
        if not text:
            continue

        ext = os.path.splitext(full)[1].lower()

        if ext == ".xlsx":
            print("we are here")
            all_chunks.extend(text)
            return text
        chunks = chunk_document(text, filename)
        all_chunks.extend(chunks)

    insert_chunks(all_chunks)
    return all_chunks


# ------------------------------------------
# OPTIONAL MAIN (disabled unless run directly)
# ------------------------------------------

if __name__ == "__main__":
    folder = "files"
    output = "chunks.json"

    all_chunks = process_folder(folder)
    save_chunks(all_chunks, output)
    print(f"Saved {len(all_chunks)} chunks → {output}")
