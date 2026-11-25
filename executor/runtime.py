"""Read-only, bounded host diagnostics shared by the Ubuntu controller and Windows agent.

No model, arbitrary shell, root access or dynamic code execution is used here.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

try:
    import psutil
except ImportError:
    psutil = None

MAX_OUTPUT = 4096

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def _run(argv: list[str], *, timeout: int = 8) -> dict:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, shell=False)
        return {"exit_code": p.returncode, "stdout": p.stdout[:MAX_OUTPUT],
                "stderr": p.stderr[:1024], "truncated": len(p.stdout) > MAX_OUTPUT}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"exit_code": -1, "stdout": "", "stderr": str(exc)[:512], "truncated": False}

def _gpu() -> dict:
    if shutil.which("nvidia-smi"):
        r = _run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                  "--format=csv,noheader,nounits"], timeout=4)
        if r["exit_code"] == 0 and r["stdout"].strip():
            rows = [x.strip() for x in r["stdout"].splitlines() if x.strip()]
            return {"provider": "nvidia", "gpus": [
                {"name": x[0], "vram_total_mib": int(x[1]),
                 "vram_used_mib": int(x[2]), "gpu_percent": int(x[3])}
                for line in rows if len(x := [p.strip() for p in line.split(",")]) == 4
                and all(v.isdigit() for v in x[1:])
            ]}
    if platform.system() == "Windows":
        r = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"], timeout=5)
        if r["exit_code"] == 0:
            return {"provider": "windows-cim", "names": r["stdout"].splitlines(),
                    "vram_total_mib": None, "note": "Dedicated VRAM not reliably available via CIM"}
    return {"provider": "unavailable", "gpus": []}

def snapshot(disk_paths: list[str] | None = None) -> dict:
    """psutil is optional; absent metrics explicitly remain null (never invented)."""
    disks = []
    paths = disk_paths or (["C:\\", "F:\\"] if os.name == "nt" else ["/", "/1tbdisk"])
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            disks.append({"mount": raw, "available": False})
            continue
        try:
            usage = shutil.disk_usage(p)
            disks.append({"mount": raw, "available": True, "total": usage.total,
                          "used": usage.used, "free": usage.free})
        except OSError as exc:
            disks.append({"mount": raw, "available": False, "error": str(exc)[:160]})
    mem = psutil.virtual_memory() if psutil else None
    return {"observed_at": utcnow(), "hostname": platform.node(),
            "os": platform.platform(), "python": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(interval=0.1) if psutil else None,
            "cpu_threads": os.cpu_count(),
            "ram_total": mem.total if mem else None, "ram_used": mem.used if mem else None,
            "ram_percent": mem.percent if mem else None,
            "gpu": _gpu(), "disks": disks,
            "metrics_note": None if psutil else "Install psutil for CPU and RAM utilization"}

def allowed_repo(value: str, roots: list[str]) -> Path:
    if not value or not roots:
        raise ValueError("No repository or allowed roots configured")
    p = Path(value).expanduser().resolve(strict=True)
    if not p.is_dir() or not (p / ".git").exists():
        raise ValueError("Not a Git working directory")
    safe_roots = [Path(root).expanduser().resolve(strict=True) for root in roots]
    if not any(p == root or root in p.parents for root in safe_roots):
        raise ValueError("Repository is outside allowed roots")
    return p

def perform(kind: str, args: dict | None, roots: list[str],
            disk_paths: list[str] | None = None) -> dict:
    args = args or {}
    if kind == "host.snapshot":
        return {"ok": True, "data": snapshot(disk_paths)}
    if kind == "clock.read":
        return {"ok": True, "data": {"utc": utcnow(),
               "unix_time": time.time(), "timezone": str(dt.datetime.now().astimezone().tzinfo)}}
    if kind == "git.status":
        repo = allowed_repo(str(args.get("repo", "")), roots)
        r = _run(["git", "-C", str(repo), "status", "--short", "--branch", "--untracked-files=no"])
        return {"ok": r["exit_code"] == 0, "data": r}
    if kind == "git.diff_stat":
        repo = allowed_repo(str(args.get("repo", "")), roots)
        r = _run(["git", "-C", str(repo), "diff", "--stat"])
        return {"ok": r["exit_code"] == 0, "data": r}
    raise ValueError("Operation not allowed: " + kind[:100])
