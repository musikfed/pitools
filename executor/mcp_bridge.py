"""MCP adapter for ChatGPT-compatible clients (no additional LLM).

The actual MCP transport is standard stdio. Remote ChatGPT requires supported
connector/tunnel registration; opening a LAN port alone does not connect it.
"""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit("Install optional MCP SDK: uv pip install mcp") from exc

SERVER = os.environ.get("PITOOLS_EXECUTOR_URL", "").rstrip("/")
TOKEN = os.environ.get("PITOOLS_CONTROL_TOKEN", "")
if not SERVER.startswith("https://") or not TOKEN:
    raise SystemExit("Set HTTPS PITOOLS_EXECUTOR_URL and PITOOLS_CONTROL_TOKEN")

mcp = FastMCP("PEGINELAB Executor")

def call(path, method="GET", payload=None):
    body=json.dumps(payload).encode() if payload is not None else None
    req=Request(SERVER+path,method=method,data=body,
                headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})
    with urlopen(req,timeout=20) as response:
        return json.loads(response.read(65536))

@mcp.tool()
def host_metrics() -> dict:
    """Read live CPU, RAM, GPU, VRAM, disks and timestamps of Ubuntu and Acer."""
    return call("/api/hosts")

@mcp.tool()
def list_jobs() -> dict:
    """List the latest 50 bounded read-only operations and their results."""
    return call("/api/jobs")

@mcp.tool()
def job_status(job_id: str) -> dict:
    """Read the current state and compact result for one job by UUID."""
    if len(job_id)!=36 or not all(c in "0123456789abcdef-" for c in job_id.lower()):
        raise ValueError("Expected UUID")
    return call("/api/jobs/"+job_id)

@mcp.tool()
def submit_diagnostic(host: str, operation: str, repository: str = "") -> dict:
    """Request a READ-ONLY operation. host: acer|ubuntu;
    operation: host.snapshot|clock.read|git.status|git.diff_stat.
    Git operations require a path inside the server's allowlisted repo roots.
    No shell, file mutation, deployments or root privileges.
    """
    if host not in ("acer","ubuntu"):
        raise ValueError("Unknown host")
    if operation not in ("host.snapshot","clock.read","git.status","git.diff_stat"):
        raise ValueError("Operation denied")
    args={"repo":repository} if operation.startswith("git.") else {}
    return call("/api/jobs","POST",{"host":host,"kind":operation,"args":args})

if __name__ == "__main__":
    mcp.run(transport="stdio")
