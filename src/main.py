from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class SimpleHandler(BaseHTTPRequestHandler):

    # Utility: add CORS headers
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # Handle preflight OPTIONS request
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Hello from Python HTTP Server!</h1>")

    def do_POST(self):
        # 1. Read content length
        content_length = int(self.headers.get("Content-Length", 0))
        
        # 2. Read body
        body = self.rfile.read(content_length)
        print("Received body:", body)

        # 3. Parse JSON
        try:
            data = json.loads(body)
            message = data.get("message", "")
        except Exception as e:
            print("JSON parse error:", e)
            self.send_response(400)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"invalid JSON"}')
            return

        # 4. Process the message
        upper_message = message.upper()
        response = {"message": "server response: " + upper_message}

        # 5. Send response
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


def main():
    print("Starting server at http://localhost:8000")
    server = HTTPServer(("localhost", 8000), SimpleHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
