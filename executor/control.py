"""PEGINELAB Executor controller (Ubuntu, port 10999).

Minimal stdlib control plane. No arbitrary commands, unsafe file writes or LLM.
Bind to loopback by default; use TLS and firewall restrictions for VPN exposure.
"""
from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
import ssl
import threading
import time
import uuid
from urllib.parse import urlparse, parse_qs

from executor.runtime import perform, snapshot, utcnow

DB_PATH = Path(os.environ.get("PITOOLS_EXECUTOR_DB", "/1tbdisk/pitools-executor/state.sqlite3"))
BIND = os.environ.get("PITOOLS_EXECUTOR_BIND", "127.0.0.1")
PORT = int(os.environ.get("PITOOLS_EXECUTOR_PORT", "10999"))
CONTROL_TOKEN = os.environ.get("PITOOLS_CONTROL_TOKEN", "")
AGENT_TOKEN = os.environ.get("PITOOLS_AGENT_TOKEN", "")
ROOTS = [v for v in os.environ.get("PITOOLS_ALLOWED_ROOTS", "/1tbdisk").split(os.pathsep) if v]
DISKS = [v for v in os.environ.get("PITOOLS_DISKS", "/,/1tbdisk").split(",") if v]
LOCK = threading.RLock()
OPERATIONS = {"host.snapshot", "clock.read", "git.status", "git.diff_stat"}

def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, host TEXT NOT NULL, kind TEXT NOT NULL,
            args TEXT NOT NULL, state TEXT NOT NULL,
            result TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS heartbeats (
            host TEXT PRIMARY KEY, seen_at TEXT NOT NULL, snapshot TEXT NOT NULL
        );
        """)

def authenticate(header: str, token: str) -> bool:
    if not token:
        return False
    return hmac.compare_digest(header, "Bearer " + token)

def job_row(row):
    return {k: row[k] for k in ("id","host","kind","state","created_at","updated_at")} | {
        "args": json.loads(row["args"]),
        "result": json.loads(row["result"]) if row["result"] else None}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Avoid recording Authorization header or payloads.
        print("%s %s" % (self.address_string(), format % args), flush=True)

    def respond(self, status: int, data: dict):
        payload = json.dumps(data, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def read_body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size < 1 or size > 16384:
            raise ValueError("Invalid request size (1..16384 bytes)")
        result = json.loads(self.rfile.read(size))
        if not isinstance(result, dict):
            raise ValueError("Expected JSON object")
        return result

    def authorized(self, agent=False) -> bool:
        ok = authenticate(self.headers.get("Authorization",""), AGENT_TOKEN if agent else CONTROL_TOKEN)
        if not ok:
            self.respond(401, {"error": "Unauthorized"})
        return ok

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            content = (Path(__file__).parent / "ui.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Security-Policy",
                "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if parsed.path == "/health":
            self.respond(200, {"status":"ok","service":"PEGINELAB Executor","version":"7.0.0-pre",
                               "utc":utcnow()})
            return
        if parsed.path == "/api/agent/next":
            if not self.authorized(agent=True): return
            host = parse_qs(parsed.query).get("host", [""])[0]
            if host != "acer":
                self.respond(400,{"error":"Unrecognized agent host"}); return
            with LOCK, connect() as db:
                row = db.execute("SELECT * FROM jobs WHERE host=? AND state='queued' ORDER BY created_at LIMIT 1", (host,)).fetchone()
                if row:
                    db.execute("UPDATE jobs SET state='running', updated_at=? WHERE id=?", (utcnow(), row["id"]))
            self.respond(200, {"job": job_row(row) if row else None})
            return
        if not self.authorized(): return
        if parsed.path == "/api/hosts":
            with connect() as db:
                rows = db.execute("SELECT * FROM heartbeats").fetchall()
            hosts = [{"host":"ubuntu", "snapshot":snapshot(DISKS),"source":"controller"}]
            for row in rows:
                hosts.append({"host":row["host"],"snapshot":json.loads(row["snapshot"]),
                              "last_seen":row["seen_at"],"source":"agent"})
            self.respond(200, {"hosts":hosts}); return
        if parsed.path == "/api/jobs":
            with connect() as db:
                rows = db.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50").fetchall()
            self.respond(200, {"jobs":[job_row(row) for row in rows]});return
        if parsed.path.startswith("/api/jobs/"):
            jid = parsed.path.split("/")[-1]
            with connect() as db:
                row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
            self.respond(200 if row else 404, {"job":job_row(row) if row else None});return
        self.respond(404,{"error":"Not found"})

    def do_POST(self):
        try:
            body = self.read_body()
            if self.path == "/api/agent/heartbeat":
                if not self.authorized(agent=True): return
                if body.get("host") != "acer" or not isinstance(body.get("snapshot"),dict):
                    raise ValueError("Invalid heartbeat")
                with LOCK, connect() as db:
                    db.execute("INSERT INTO heartbeats(host,seen_at,snapshot) VALUES (?,?,?) "
                               "ON CONFLICT(host) DO UPDATE SET seen_at=excluded.seen_at,snapshot=excluded.snapshot",
                               ("acer",utcnow(),json.dumps(body["snapshot"])[:12000]))
                self.respond(200,{"ok":True});return
            if self.path == "/api/agent/result":
                if not self.authorized(agent=True): return
                jid = str(body.get("id",""))
                if not isinstance(body.get("result"),dict):
                    raise ValueError("Missing result object")
                with LOCK, connect() as db:
                    job = db.execute("SELECT host,state FROM jobs WHERE id=?", (jid,)).fetchone()
                    if not job or job["host"] != "acer" or job["state"] != "running":
                        self.respond(409,{"error":"Job state mismatch"});return
                    result = json.dumps(body["result"],ensure_ascii=False)[:14000]
                    db.execute("UPDATE jobs SET state='done',result=?,updated_at=? WHERE id=?",
                               (result,utcnow(),jid))
                self.respond(200,{"ok":True});return
            if not self.authorized(): return
            if self.path == "/api/jobs":
                host = body.get("host")
                kind = body.get("kind")
                args = body.get("args", {})
                if host not in ("ubuntu","acer") or kind not in OPERATIONS or not isinstance(args,dict):
                    raise ValueError("Host, operation or args not allowed")
                jid = str(uuid.uuid4()); now = utcnow()
                with LOCK, connect() as db:
                    db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                               (jid,host,kind,json.dumps(args),"queued",None,now,now))
                if host == "ubuntu":
                    try:
                        result = perform(kind,args,ROOTS,DISKS)
                    except Exception as exc:
                        result = {"ok":False,"error":str(exc)[:600]}
                    with LOCK, connect() as db:
                        db.execute("UPDATE jobs SET state='done',result=?,updated_at=? WHERE id=?",
                                   (json.dumps(result,ensure_ascii=False)[:14000],utcnow(),jid))
                self.respond(202,{"id":jid,"state":"done" if host=="ubuntu" else "queued"});return
            self.respond(404,{"error":"Not found"})
        except (ValueError,json.JSONDecodeError) as exc:
            self.respond(400,{"error":str(exc)[:300]})

def main():
    if not CONTROL_TOKEN or not AGENT_TOKEN or CONTROL_TOKEN == AGENT_TOKEN:
        raise SystemExit("Set distinct PITOOLS_CONTROL_TOKEN and PITOOLS_AGENT_TOKEN")
    init_db()
    httpd = ThreadingHTTPServer((BIND,PORT),Handler)
    cert,key=os.environ.get("PITOOLS_TLS_CERT"),os.environ.get("PITOOLS_TLS_KEY")
    if cert and key:
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert,key)
        httpd.socket=ctx.wrap_socket(httpd.socket,server_side=True)
    elif BIND not in ("127.0.0.1","::1","localhost"):
        raise SystemExit("Non-loopback listener requires PITOOLS_TLS_CERT and PITOOLS_TLS_KEY")
    print(f"PEGINELAB Executor on {BIND}:{PORT} ({'TLS' if cert else 'loopback-only HTTP'})",flush=True)
    try: httpd.serve_forever(poll_interval=0.5)
    finally: httpd.server_close()

if __name__ == "__main__":
    main()
