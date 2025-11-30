from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import base64
import os
import unicodedata
import mimetypes

from file_chunkers import load_document, chunk_document, save_chunks


from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from model.main import RAGChatbot
from dotenv import load_dotenv

rag_chatbot = RAGChatbot()

UPLOAD_DIR = os.getenv("FILES_PATH")
BASE_URL = "http://localhost:8000/files"
def debug_unicode(label, s):
    print(f"{label}: {s!r}")
    print("Codepoints:", [hex(ord(c)) for c in s])

class SimpleHandler(BaseHTTPRequestHandler):

    # Utility: add CORS headers
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # ---- Static file serving ----
    def handle_file_serve(self):
        upload_dir = UPLOAD_DIR

        raw_filename = self.path.replace("/files/", "")

        # NEW: decode %CC%81 etc.
        from urllib.parse import unquote
        decoded_filename = unquote(raw_filename)

        # Normalize Unicode (macOS compatibility)
        safe_filename = unicodedata.normalize("NFC", decoded_filename)


        file_path = os.path.join(upload_dir, safe_filename)

        if not os.path.isfile(file_path):
            self.send_response(404)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"File not found")
            return

        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    # ---- OPTIONS (CORS) ----
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    # ---- List uploaded files ----
    def handle_uploads_get(self):
        # Ensure upload folder exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        files = []
        for filename in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(path):
                files.append({
                    "name": filename,
                    "link": f"{BASE_URL}/{filename}"
                })

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"files": files}).encode())

    # ---- GET Router ----
    def do_GET(self):
        if self.path.startswith("/files/"):
            return self.handle_file_serve()

        if self.path == "/uploaded-files":
            return self.handle_uploads_get()

        # Fallback
        resp = b"<h1>Hello from Python HTTP Server!</h1>"
        content_type = "text/html"

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(resp)

    # ---- POST Router ----
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except:
            self.send_response(400)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"error":"invalid JSON"}')
            return

        print("POST data:", data)
        content_type = self.headers.get("Content-Type", "")

        if self.path == "/upload-document":
            print("Uploading a document...")

            filename = data.get("filename")
            dateOfCreation = data.get("dateOfCreation")
            content_base64 = data.get("content")

            # Normalize filename for macOS
            raw_filename = self.path.replace("/files/", "")

            # 1. URL-decode
            decoded = raw_filename

            # 2. Normalize to NFC (match macOS-friendly form)
            safe_filename = unicodedata.normalize("NFC", decoded)

            print(f"Saving '{safe_filename}' created at {dateOfCreation}")

            # Decode data
            file_bytes = base64.b64decode(content_base64)

            # Ensure upload directory exists
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            # Save file
            safe_filename = unicodedata.normalize("NFC", filename)

            # Always use the ABSOLUTE UPLOAD DIRECTORY
            file_path = os.path.join(UPLOAD_DIR, safe_filename)

            with open(file_path, "wb") as f:
                f.write(file_bytes)

            document_data = load_document(file_path)

            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".xlsx":
                print("document_data ")
                print(document_data)
                chunks = document_data
            else:
                chunks = chunk_document(document_data, safe_filename)
            os.makedirs("./chunks", exist_ok=True)

            save_chunks(chunks, "./chunks/" +safe_filename + "-chunks.json")
            rag_chatbot.insert_chunks_into_table(chunks)

            print(f"File saved to {file_path}")

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"OK"}')
            return

        # ---- Default POST behavior ----
        message = data.get("message", "")
        llm_response = rag_chatbot.return_response(message)
        response = {"message": llm_response}

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


def main():
    print("Starting server at http://localhost:8000")
    server = HTTPServer(("0.0.0.0", 8000), SimpleHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
