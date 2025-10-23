from http.server import HTTPServer, BaseHTTPRequestHandler
import world_core, json

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/region"):
            r = world_core.get_region("spark", {})
            print("REGION:", r)
            b = json.dumps(r).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        else:
            self.send_response(404); self.end_headers()
print("Starting test daemon on 8787")
HTTPServer(("127.0.0.1",8787),H).serve_forever()
