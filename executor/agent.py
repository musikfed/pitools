"""Small Windows polling worker. No LLM, no arbitrary shell, no inbound port."""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError

from executor.runtime import perform, snapshot

URL = os.environ.get("PITOOLS_EXECUTOR_URL", "").rstrip("/")
TOKEN = os.environ.get("PITOOLS_AGENT_TOKEN", "")
ROOTS = [x for x in os.environ.get("PITOOLS_ALLOWED_ROOTS", "F:\\").split(os.pathsep) if x]
DISKS = [x for x in os.environ.get("PITOOLS_DISKS", "C:\\,F:\\").split(",") if x]
INTERVAL = max(2.0,float(os.environ.get("PITOOLS_AGENT_INTERVAL", "5")))

def request(path: str, method="GET", body: dict | None = None) -> dict:
    raw = json.dumps(body,ensure_ascii=False).encode() if body is not None else None
    r = Request(URL + path, data=raw, method=method,
                headers={"Authorization":"Bearer "+TOKEN,
                         "Content-Type":"application/json"})
    with urlopen(r,timeout=15) as f:
        return json.loads(f.read(65536))

def main():
    if not URL.startswith("https://") or not TOKEN:
        raise SystemExit("PITOOLS_EXECUTOR_URL must be HTTPS and agent token set")
    print("Windows agent started, outbound polling only",flush=True)
    while True:
        try:
            request("/api/agent/heartbeat","POST",{"host":"acer","snapshot":snapshot(DISKS)})
            job = request("/api/agent/next?host=acer").get("job")
            if job:
                try:
                    result = perform(job["kind"],job.get("args"),ROOTS,DISKS)
                except Exception as exc:
                    result = {"ok":False,"error":str(exc)[:600]}
                request("/api/agent/result","POST",{"id":job["id"],"result":result})
        except (URLError,TimeoutError,OSError,ValueError,KeyError) as exc:
            print("Agent connection error:",str(exc)[:220],file=sys.stderr,flush=True)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
