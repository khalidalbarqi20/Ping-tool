#!/usr/bin/env python3
# Gaming Ping Monitor v5. One ping at a time. ICMP (system ping) or TCP connect for "approx" hosts.
import json, re, socket, subprocess, threading, time, os, ipaddress
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(D + "/games.json", encoding="utf-8"))
SNAP = D + "/snapshots.json"
REG = {rg["name"]: {**rg, "game": g["name"]} for g in CFG["games"] for rg in g["regions"]}
CUSTOM = D + "/custom.json"
if os.path.exists(CUSTOM):
    for _c in json.load(open(CUSTOM, encoding="utf-8")):
        REG[_c["name"]] = {**_c, "game": "مخصص", "custom": True}
def save_custom():
    json.dump([{k: c[k] for k in ("name", "host", "tcp") if c.get(k)} for c in REG.values() if c.get("custom")],
              open(CUSTOM, "w", encoding="utf-8"), ensure_ascii=False)

def is_public_host(host):
    """Reject localhost/private/reserved targets for the public custom-probe endpoint."""
    try:
        addresses = {x[4][0] for x in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
        return bool(addresses) and all(ipaddress.ip_address(ip).is_global for ip in addresses)
    except (OSError, ValueError):
        return False
def cfg():
    cu = [{k: c[k] for k in ("name", "host", "tcp") if c.get(k)} for c in REG.values() if c.get("custom")]
    return {"games": CFG["games"] + [{"id": "custom", "name": "مخصص", "regions": cu}]}
WIN, MAXR = 60, 6
ST = {"regions": [], "data": {}, "warm": {}, "mins": {}, "scan": [], "scanning": False}
LK, SEEN, IPS = threading.Lock(), [0.0], {}

def ping(c):
    if c.get("tcp"):
        try:
            ip = IPS.get(c["host"]) or IPS.setdefault(c["host"], socket.gethostbyname(c["host"]))
            t = time.time(); s = socket.create_connection((ip, c["tcp"]), timeout=2); s.close()
            return (time.time() - t) * 1000
        except Exception:
            return None
    try:
        o = subprocess.run(["ping", "-c", "1", "-W", "2", c["host"]], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"time[=<]([\d.]+)", o)
        return float(m.group(1)) if m else None
    except Exception:
        return None

def loop():   # round-robin, never parallel
    while True:
        with LK: rs, sc = list(ST["regions"]), ST["scanning"]
        if not rs or sc or time.time() - SEEN[0] > 10:
            time.sleep(0.5); continue
        t0 = time.time()
        for r in rs:
            if ST["scanning"]: break
            t = time.time(); v = ping(REG[r])
            with LK:
                if r not in ST["regions"]: continue
                if ST["warm"].get(r, 0) > 0: ST["warm"][r] -= 1
                else:
                    L = ST["data"].setdefault(r, []); L.append((t, v)); del L[:-WIN]
                    if v is not None:                                  # per-minute average buckets
                        M = ST["mins"].setdefault(r, {}); b = M.setdefault(int(t // 60), [0.0, 0]); b[0] += v; b[1] += 1
                        for k in [k for k in M if k < int(t // 60) - 5]: del M[k]
        time.sleep(max(0, 1.5 - (time.time() - t0)))

SCANSET = [n for n, c in REG.items() if not c.get("approx") and not c.get("custom")]
def scan():
    with LK: ST["scanning"], ST["scan"] = True, []
    for n in SCANSET:
        vs = [ping(REG[n]) for _ in range(4)][1:]
        ok = [v for v in vs if v is not None]
        with LK: ST["scan"].append({"region": n, "avg": sum(ok) / len(ok) if ok else None})
    with LK: ST["scanning"], ST["warm"] = False, {r: 1 for r in ST["regions"]}

def stats(L, method):
    n = len(L)
    if n == 0: return {"state": "No Data", "method": method}
    ok = [v for _, v in L if v is not None]
    r = {"n": n, "at": L[-1][0], "method": method}
    if ok:
        r.update(min=min(ok), avg=sum(ok) / len(ok), max=max(ok), now=sum(ok[-5:]) / len(ok[-5:]))
        d = [abs(a - b) for a, b in zip(ok, ok[1:])]
        r["jitter"] = sum(d) / len(d) if d else None
    if n >= 10: r["loss"] = 100 * (n - len(ok)) / n
    if n >= 5 and all(v is None for _, v in L[-5:]): r["state"] = "Offline"
    elif n < 10: r["state"] = "No Data"
    elif r["loss"] > 2 or (r.get("jitter") or 0) > 30: r["state"] = "Unstable"
    else: r["state"] = "Online"
    return r

def score(r): return r["avg"] + 2 * (r.get("jitter") or 0) + 10 * r["loss"]

def api_stats():
    SEEN[0] = time.time()
    with LK:
        items = []
        for r in ST["regions"]:
            c = REG[r]; m = "measured_tcp" if c.get("tcp") else "measured_icmp"
            M = ST["mins"].get(r, {})
            mins = [M[k][0] / M[k][1] for k in sorted(M)][-5:]      # last 5 minute-averages, last = current minute
            items.append({"region": r, "game": c["game"], "approx": bool(c.get("approx")), "mins": mins,
                          "stats": stats(list(ST["data"].get(r, [])), m)})
        best = []
        for g in {i["game"] for i in items}:   # compare only inside the same game
            grp = [i for i in items if i["game"] == g]
            cand = [(score(i["stats"]), i["region"]) for i in grp
                    if i["stats"]["state"] in ("Online", "Unstable") and "loss" in i["stats"] and "avg" in i["stats"]]
            if len(grp) >= 2 and cand: best.append(min(cand)[1])
        sc = [x for x in ST["scan"] if x["avg"] is not None]
        return {"items": items, "best": best, "scan": sc, "scanned": len(ST["scan"]),
                "total": len(SCANSET), "scanning": ST["scanning"]}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, body, ct="application/json", status=200):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", ct + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        try:
            self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError):
            pass
    def do_GET(self):
        if self.path in ("/health", "/api/health"):
            self.send({"ok": True, "service": "ping-tool", "time": time.time()})
        elif self.path == "/api/stats": self.send(api_stats())
        elif self.path == "/api/config": self.send(cfg())
        elif self.path == "/api/snaps":
            try: self.send(json.load(open(SNAP, encoding="utf-8")) if os.path.exists(SNAP) else [])
            except (OSError, json.JSONDecodeError): self.send([])
        elif self.path == "/":
            self.send(open(D + "/index.html", "rb").read(), "text/html")
        else:
            self.send({"error": "not_found"}, status=404)
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 4096:
                self.send({"error": "request_too_large"}, status=413)
                return
            d = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(d, dict):
                raise ValueError("JSON object required")
        except (ValueError, json.JSONDecodeError):
            self.send({"error": "invalid_json"}, status=400)
            return
        r = d.get("region")
        if self.path == "/api/add" and r in REG:
            with LK:
                if r not in ST["regions"] and len(ST["regions"]) < MAXR:
                    ST["regions"].append(r); ST["data"][r] = []; ST["mins"][r] = {}; ST["warm"][r] = 1
        elif self.path == "/api/remove":
            with LK:
                if r in ST["regions"]: ST["regions"].remove(r)
                ST["data"].pop(r, None); ST["mins"].pop(r, None); ST["warm"].pop(r, None)
        elif self.path == "/api/custom":
            name, host, port = str(d.get("name", "")).strip()[:24], str(d.get("host", "")).strip(), d.get("tcp")
            if (name and name not in REG
                    and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-]{0,100}", host)
                    and is_public_host(host)):
                c = {"name": name, "host": host, "game": "مخصص", "custom": True}
                if str(port or "").isdigit() and 0 < int(port) < 65536: c["tcp"] = int(port)
                with LK: REG[name] = c; save_custom()
        elif self.path == "/api/custom_del" and REG.get(r, {}).get("custom"):
            with LK:
                if r in ST["regions"]: ST["regions"].remove(r)
                ST["data"].pop(r, None); ST["mins"].pop(r, None); ST["warm"].pop(r, None)
                del REG[r]; save_custom()
        elif self.path == "/api/scan" and not ST["scanning"]:
            threading.Thread(target=scan, daemon=True).start()
        elif self.path == "/api/snap":
            s = api_stats(); old = json.load(open(SNAP)) if os.path.exists(SNAP) else []
            old.append({"label": str(d.get("label", "?"))[:40], "time": time.strftime("%Y-%m-%d %H:%M"), "items": s["items"]})
            json.dump(old[-100:], open(SNAP, "w"), ensure_ascii=False)
        self.send({"ok": True})

if __name__ == "__main__":
    # Render and other cloud hosts provide PORT and require binding to 0.0.0.0.
    PORT = int(os.environ.get("PORT", "8765"))
    threading.Thread(target=loop, daemon=True).start()
    print(f"Gaming Server Monitor listening on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
