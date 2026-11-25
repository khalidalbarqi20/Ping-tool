#!/usr/bin/env python3
"""Gaming Server Monitor v13: metadata-only backend; never fabricates player ping."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

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
    return {"version": "13", "measurement": "disabled_until_valid_client_probe_exists", "games": games}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

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
        if self.path in ("/health", "/api/health"):
            self.send_bytes(200, json.dumps({"ok": True, "service": "ping-tool", "version": "13"}).encode(), "application/json; charset=utf-8")
            return
        if self.path == "/api/config":
            self.send_bytes(200, json.dumps(public_config(), ensure_ascii=False).encode(), "application/json; charset=utf-8")
            return
        if self.path == "/api/stats":
            payload = {
                "version": "13",
                "measurement": "not_available",
                "message": "لا توجد نقطة اختبار تدعم قياساً مباشراً من المتصفح لهذه الوجهة.",
                "items": [],
            }
            self.send_bytes(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            return
        if self.path == "/" or self.path == "/index.html":
            self.send_bytes(200, (BASE / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if self.path == "/favicon.ico":
            self.send_bytes(204, b"", "image/x-icon")
            return
        self.send_bytes(404, b'{"error":"not_found"}', "application/json; charset=utf-8")


if __name__ == "__main__":
    print(f"Gaming Server Monitor v13 listening on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
