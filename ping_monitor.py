#!/usr/bin/env python3
"""Gaming Server Monitor v14.2: metadata-only backend; never fabricates player ping."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "games.json").read_text(encoding="utf-8"))
PORT = int(os.environ.get("PORT", "8765"))


def public_config():
    games = []
    for game in CONFIG.get("games", []):
        regions = []
        for region in game.get("regions", []):
            regions.append({
                "name": region.get("name", "Unknown"),
                "host": region.get("host"),
                "source": region.get("source"),
                "measurement": "unsupported_from_browser",
                "note": region.get("note") or game.get("note"),
            })
        games.append({
            "id": game.get("id"),
            "name": game.get("name"),
            "regions": regions,
            "status": game.get("status"),
            "note": game.get("note"),
        })
    return {"version": "14.2", "measurement": "general_edge_probe_only", "games": games}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Keep request paths visible in Render logs for diagnosis.
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        # Render's proxy may forward a query string or absolute-form request target.
        # Route using the URL path only, not the raw request target.
        request_path = urlsplit(self.path).path or "/"
        if request_path in ("/health", "/api/health"):
            self.send_bytes(200, json.dumps({"ok": True, "service": "ping-tool", "version": "14.2"}).encode(), "application/json; charset=utf-8")
            return
        if request_path == "/api/config":
            self.send_bytes(200, json.dumps(public_config(), ensure_ascii=False).encode(), "application/json; charset=utf-8")
            return
        if request_path == "/api/stats":
            payload = {
                "version": "14.2",
                "measurement": "not_available",
                "message": "لا توجد نقطة اختبار تدعم قياساً مباشراً من المتصفح لهذه الوجهة.",
                "items": [],
            }
            self.send_bytes(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            return
        if request_path in ("/", "/index.html"):
            self.send_bytes(200, (BASE / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if request_path == "/favicon.ico":
            self.send_bytes(204, b"", "image/x-icon")
            return
        self.send_bytes(404, json.dumps({
            "error": "not_found",
            "path": request_path,
            "version": "14.2"
        }).encode(), "application/json; charset=utf-8")


if __name__ == "__main__":
    print(f"Gaming Server Monitor v14.2 listening on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
