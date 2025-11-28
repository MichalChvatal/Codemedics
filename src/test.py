import re
import json

INPUT_FILE = "dokument.txt"
OUTPUT_FILE = "chunks.json"

# Regex, který zachytí nadpisy typu:
# 1.
# 3.2.
# 4.4.13.
# 2.1 Něco
# 5.3.1.2 Další text
SECTION_REGEX = r"(?m)^(\d+(?:\.\d+)*)(?:\.?)\s+(.*)"


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_into_chunks(text):
    matches = list(re.finditer(SECTION_REGEX, text))

    chunks = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        section_id = matches[i].group(1).strip()
        section_title = matches[i].group(2).strip()

        section_text = text[start:end].strip()

        chunks.append({
            "id": section_id,
            "title": section_title,
            "text": section_text
        })

    return chunks


def save_chunks(chunks, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    print("Načítám dokument...")
    text = load_text(INPUT_FILE)

    print("Rozděluji dokument na chunky...")
    chunks = split_into_chunks(text)

    print(f"Nalezeno {len(chunks)} chunků.")
    save_chunks(chunks, OUTPUT_FILE)

    print(f"Hotovo! Výstup uložen do: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
