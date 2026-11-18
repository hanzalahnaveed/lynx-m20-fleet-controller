"""Local HTTP server for fleet status and simple destination editing."""
import json, math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

class DashboardServer:
    def __init__(self, report_provider, target_setter=None, host="127.0.0.1", port=8765, web_dir=None):
        self.report_provider, self.target_setter = report_provider, target_setter
        self.host, self.port = host, int(port)
        self.web_dir = Path(web_dir) if web_dir else Path(__file__).resolve().parent.parent / "web"
        self.httpd = self.thread = None
    @property
    def display_host(self):
        return "127.0.0.1" if self.host in ("0.0.0.0", "::") else self.host
    def start(self):
        provider, setter, web_dir = self.report_provider, self.target_setter, self.web_dir
        class Handler(BaseHTTPRequestHandler):
            def send_data(self, code, data, kind="application/json; charset=utf-8"):
                if isinstance(data, str): data=data.encode()
                self.send_response(code); self.send_header("Content-Type",kind)
                self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(data)))
                self.end_headers(); self.wfile.write(data)
            def do_GET(self):
                path=self.path.split("?",1)[0]
                if path=="/api/status":
                    try: self.send_data(200,json.dumps(provider(),allow_nan=False))
                    except Exception: self.send_error(503,"Status unavailable")
                elif path in ("/","/index.html"):
                    try: self.send_data(200,(web_dir/"index.html").read_bytes(),"text/html; charset=utf-8")
                    except OSError: self.send_error(404,"Dashboard asset not installed")
                else: self.send_error(404)
            def do_POST(self):
                if self.path.split("?",1)[0]!="/api/target" or setter is None:
                    self.send_error(404); return
                try:
                    size=int(self.headers.get("Content-Length","0"))
                    if size<2 or size>2048: raise ValueError("Invalid request size")
                    body=json.loads(self.rfile.read(size))
                    robot=body.get("robot"); x=float(body["x"]); y=float(body["y"])
                    if robot not in ("robot_a","robot_b") or not math.isfinite(x) or not math.isfinite(y):
                        raise ValueError("Choose a robot and finite X/Y coordinates")
                    setter(robot,x,y)
                    self.send_data(200,json.dumps({"ok":True,"robot":robot,"x":x,"y":y}))
                except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
                    self.send_data(400,json.dumps({"ok":False,"error":str(exc)}))
            def log_message(self,*args): pass
        self.httpd=ThreadingHTTPServer((self.host,self.port),Handler); self.httpd.daemon_threads=True
        self.thread=Thread(target=self.httpd.serve_forever,name="fleet-dashboard-http",daemon=True); self.thread.start()
    def stop(self):
        if self.httpd is not None:
            self.httpd.shutdown(); self.httpd.server_close(); self.httpd=None
        if self.thread is not None:
            self.thread.join(timeout=2); self.thread=None
