"""Regression tests for the new read-only Executor. Run: python -m unittest discover -s tests"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

from executor import runtime, control

class TestRuntime(unittest.TestCase):
    def test_allowed_operations_reject_shell(self):
        for name in ["shell.exec","sudo","file.delete","docker.down"]:
            with self.assertRaises(ValueError):
                runtime.perform(name,{},[])

    def test_time(self):
        result=runtime.perform("clock.read",{},[])
        self.assertTrue(result["ok"])
        self.assertIn("+00:00",result["data"]["utc"])

    def test_snapshot(self):
        result=runtime.perform("host.snapshot",{},[],["/"])
        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["hostname"])

    def test_repo_allowlist(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); allowed=root/"allowed"; forbidden=root/"forbidden"
            for p in (allowed,forbidden):
                p.mkdir()
                subprocess.run(["git","init",str(p)],check=True,capture_output=True)
            r=runtime.perform("git.status",{"repo":str(allowed)},[str(allowed)])
            self.assertTrue(r["ok"])
            with self.assertRaises(ValueError):
                runtime.perform("git.status",{"repo":str(forbidden)},[str(allowed)])

    def test_root_not_escape(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); safe=root/"safe"; sibling=root/"safe2"
            safe.mkdir();sibling.mkdir()
            subprocess.run(["git","init",str(sibling)],check=True,capture_output=True)
            with self.assertRaises(ValueError):
                runtime.perform("git.diff_stat",{"repo":str(sibling)},[str(safe)])

class TestController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        control.DB_PATH=Path(cls.tmp.name)/"state.sqlite3"
        control.CONTROL_TOKEN="test-controller-private"
        control.AGENT_TOKEN="test-agent-private"
        control.init_db()
        cls.server=control.ThreadingHTTPServer(("127.0.0.1",0),control.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def req(self,path,token=None,body=None):
        data=json.dumps(body).encode() if body is not None else None
        req=Request(self.base+path,data=data,method="POST" if body is not None else "GET",
                    headers={"Authorization":"Bearer "+token} if token else {})
        if data is not None: req.add_header("Content-Type","application/json")
        with urlopen(req,timeout=10) as response:
            return response.status,json.loads(response.read())

    def test_public_health(self):
        status,data=self.req("/health")
        self.assertEqual(status,200)
        self.assertEqual(data["status"],"ok")

    def test_auth_required(self):
        with self.assertRaises(HTTPError) as ctx:
            self.req("/api/hosts")
        self.assertEqual(ctx.exception.code,401)

    def test_agent_cannot_submit_job(self):
        with self.assertRaises(HTTPError) as ctx:
            self.req("/api/jobs",control.AGENT_TOKEN,{"host":"ubuntu","kind":"clock.read"})
        self.assertEqual(ctx.exception.code,401)

    def test_windows_queue(self):
        status,new=self.req("/api/jobs",control.CONTROL_TOKEN,
                            {"host":"acer","kind":"clock.read","args":{}})
        self.assertEqual(status,202)
        status,nxt=self.req("/api/agent/next?host=acer",control.AGENT_TOKEN)
        self.assertEqual(nxt["job"]["id"],new["id"])
        self.assertEqual(nxt["job"]["kind"],"clock.read")
        status,done=self.req("/api/agent/result",control.AGENT_TOKEN,
                             {"id":new["id"],"result":{"ok":True,"data":{"utc":"test"}}})
        self.assertEqual(status,200)
        status,jobs=self.req("/api/jobs/"+new["id"],control.CONTROL_TOKEN)
        self.assertEqual(jobs["job"]["state"],"done")

    def test_disallowed_operation(self):
        with self.assertRaises(HTTPError) as ctx:
            self.req("/api/jobs",control.CONTROL_TOKEN,
                     {"host":"ubuntu","kind":"shell.exec","args":{"command":"id"}})
        self.assertEqual(ctx.exception.code,400)

if __name__ == "__main__":
    unittest.main()
