"""Small loopback HTTP server for the read-only fleet dashboard."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


class DashboardServer:
    def __init__(self, report_provider, host="127.0.0.1", port=8765, web_dir=None):
        self.report_provider = report_provider
        self.host = host
        self.port = int(port)
        self.web_dir = Path(web_dir) if web_dir else Path(__file__).resolve().parent.parent / "web"
        self.httpd = None
        self.thread = None

    @property
    def display_host(self):
        return "127.0.0.1" if self.host in ("0.0.0.0", "::") else self.host

    def start(self):
        provider = self.report_provider
        web_dir = self.web_dir

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.split("?", 1)[0] == "/api/status":
                    try:
                        payload = json.dumps(provider(), allow_nan=False).encode("utf-8")
                    except Exception as exc:
                        self.send_error(503, f"Status unavailable: {exc}")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                if self.path.split("?", 1)[0] in ("/", "/index.html"):
                    path = web_dir / "index.html"
                    try:
                        payload = path.read_bytes()
                    except OSError:
                        self.send_error(404, "Dashboard asset not installed")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                self.send_error(404)

            def log_message(self, fmt, *args):
                return

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.httpd.daemon_threads = True
        self.thread = Thread(target=self.httpd.serve_forever, name="fleet-dashboard-http", daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread is not None:
            self.thread.join(timeout=2.0)
            self.thread = None
