import re
import json
import subprocess
import mammoth
import os
import sys

# --- Configuration ---
FILES_DIR = "files"
OUTPUT_FILE = "chunks.json"

# Regex to capture numbered sections/headings, e.g.:
# 1. Title
# 3.2. Title
# 4.4.13. Title Text
SECTION_REGEX = r"(?m)^(\d+(?:\.\d+)*)(?:\.?)\s+(.*)" 

# --- Document Loading Functions ---

def load_doc_antiword(path: str) -> str:
    """
    Reads old .doc files using the external 'antiword' utility.
    NOTE: 'antiword' must be installed on the system (e.g., 'brew install antiword' or 'sudo apt install antiword').
    """
    try:
        # Use sys.executable to ensure the current Python environment's path is used
        output = subprocess.check_output(["antiword", path])
        # Decode output, ignoring potential errors
        text = output.decode("utf-8", errors="ignore")
        return text
    except subprocess.CalledProcessError as e:
        print(f"Error reading .doc file with antiword: {path}. Is antiword installed and accessible?")
        raise e
    except FileNotFoundError:
        print("Error: 'antiword' command not found. Please install the antiword utility.")
        sys.exit(1)


def load_docx_mammoth(path: str) -> str:
    """
    Reads .docx files using the 'mammoth' library.
    """
    try:
        with open(path, "rb") as f:
            result = mammoth.extract_raw_text(f)
            # result.value contains the plain text
            return result.value
    except Exception as e:
        print(f"Error reading .docx file with mammoth: {path}. Error: {e}")
        return ""


def load_all_documents(files_dir: str) -> dict[str, str]:
    """
    Loads all supported documents (.doc, .docx) from the specified directory.
    Returns a dictionary mapping filename to its text content.
    """
    texts = {}
    print(f"Searching for documents in: {files_dir}")
    if not os.path.isdir(files_dir):
        print(f"Directory '{files_dir}' not found. Please create it and add documents.")
        return texts

    for file in os.listdir(files_dir):
        print("the file is", file)
        full_path = os.path.join(files_dir, file)

        if os.path.isdir(full_path):
            continue

        file_lower = file.lower()

        if file_lower.endswith(".docx"):
            print(f"Loading DOCX: {file}")
            texts[file] = load_docx_mammoth(full_path)
        elif file_lower.endswith(".doc"):
            print(f"Loading DOC: {file}")
            texts[file] = load_doc_antiword(full_path)
        else:
            print(f"Skipping (unsupported): {file}")

    return texts

# --- Chunking and Saving Functions ---

def split_into_chunks(text: str, file_title: str) -> list[dict]:
    """
    Splits the document text into chunks based on the SECTION_REGEX.
    """
    matches = list(re.finditer(SECTION_REGEX, text))

    if not matches:
        # Handle the case where no sections are found (treat as one large chunk)
        print(f"Warning: No sections found in {file_title}. Treating as a single chunk.")
        return [{
            "id": "1",
            "filename": file_title,
            # Normalize whitespace in content
            "content": re.sub(r"\s+", " ", text).strip()
        }]

    chunks = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        # Extract the ID (e.g., "3.2.1") and Title (e.g., "The Title Text")
        section_id = matches[i].group(1).strip()
        section_title = matches[i].group(2).strip()

        # The section_text includes the heading itself, which is fine for RAG
        section_text = text[start:end].strip()
        
        # Replace any sequence of whitespace (newlines, tabs, multiple spaces) with a single space
        section_text_normalized = re.sub(r"\s+", " ", section_text)


        chunks.append({
            "id": i,
            # "title": section_title, # Added title back for better context
            "filename": file_title,
            "content": section_text_normalized
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


# --- Main Execution ---

def main():
    print("Načítám a zpracovávám dokumenty z adresáře 'files'...")

    # Load all supported documents
    docs = load_all_documents(FILES_DIR)
    
    if not docs:
        print("No documents loaded. Exiting.")
        return

    all_chunks = []
    
    # Process each document
    for name, content in docs.items():
        if content:
            print(f"\nProcessing document: {name} (Length: {len(content)} chars)")
            
            # 1. Split document into structured chunks
            chunks = split_into_chunks(content, name)
            
            print(f"Found {len(chunks)} chunks in {name}.")
            all_chunks.extend(chunks)
        else:
            print(f"Skipping {name} due to empty content.")

    if all_chunks:
        # 2. Save all chunks to the single output file
        save_chunks(all_chunks, OUTPUT_FILE)
        print("\nHotovo! Všechny chunky byly uloženy.")
    else:
        print("No chunks were created. Output file not saved.")


if __name__ == "__main__":
    main()