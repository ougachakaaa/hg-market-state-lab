"""Controlled HTTP tests, invoked by collector.test.ts with existing formal fixtures."""

import base64
import json
import sys
import tempfile
import threading
import unittest
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlsplit

import collect
import httpx

FIXTURES = None


class ControlledServer(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.dispatch("get")

    def do_POST(self):
        self.dispatch("post")

    def dispatch(self, method):
        state = self.server.state
        path = unquote(urlsplit(self.path).path)
        query = parse_qs(urlsplit(self.path).query)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"null")
        state["calls"].append(
            (method, path, query, body, self.headers.get("Cookie"), self.headers.get("Origin"))
        )
        status, payload = 200, None
        if method == "post" and self.headers.get("Origin") != "http://127.0.0.1:5173":
            status = 403
        elif path == "/auth/login":
            status = state.get("login_status", 200)
            payload = {"id": "approved-user", "username": "tester", "status": "active"}
        elif self.headers.get("Cookie") != "lab_access_token=" + str(state["cookie"]):
            status = 401
        elif state.get("error_path") == path:
            status = state.get("error_status", 503)
        elif path == "/auth/me":
            payload = {"id": "approved-user", "username": "tester", "status": "active"}
        elif path == "/mo-option-chain":
            assert query == {
                key: [value] for key, value in state["presets"]["chain"]["request"].items()
            }
            payload = state["fixtures"]["chain"]
        elif path == "/mo-option-premium-plane":
            payload = state["fixtures"]["premium"]
        elif path == "/research/capabilities":
            payload = state["fixtures"]["catalog"]["list"]
        elif path.startswith("/research/capabilities/"):
            payload = state["fixtures"]["catalog"]["details"][0]
        elif path == "/research/publications":
            if "after" not in query:
                payload = {
                    **state["fixtures"]["publications"]["pages"][0],
                    "next_cursor": "opaque+/=? token",
                }
            else:
                assert query["after"] == ["opaque+/=? token"]
                payload = {
                    "data": [],
                    "next_cursor": "opaque+/=? token" if state.get("repeat_cursor") else None,
                }
        elif path.startswith("/research/publications/"):
            publication = state["fixtures"]["publications"]
            if "/analyses/" in path:
                payload = {
                    "data": next(
                        item
                        for item in publication["analyses"]
                        if item["summary"]["analysis_id"] == path.split("/")[-1]
                    )
                }
            elif "/views/" in path:
                payload = {
                    "data": next(
                        item["view"]
                        for item in publication["views"]
                        if item["view_id"] == path.split("/")[-1]
                    )
                }
            else:
                payload = {"data": publication["manifests"][0]}
        elif path.endswith("/runs") and method == "post":
            state["submits"] += 1
            if state.get("lost_submit"):
                self.close_connection = True
                return
            basis = path.startswith("/research/")
            request = {**body, "case": "futures_basis_v1" if basis else "futures_roll_long_v1"}
            if basis:
                request["analysis_profile"] = "r01a_standard_v1"
            identity = f"{state['submits']:032x}"
            state["runs"][identity] = request
            status = 202
            payload = {
                "run_id": identity,
                "status": "PENDING",
                "request": request,
                "created_at": "2026-11-15T00:00:00Z",
            }
        elif "/runs/" in path:
            identity = path.split("/runs/")[1].split("/")[0]
            request = state["runs"][identity]
            if path.endswith("/report"):
                payload = {
                    "run_id": identity,
                    "request": request,
                    "result_status": "complete",
                    "data": state["fixtures"]["basis"],
                }
            elif path.endswith("/result"):
                data = {**state["fixtures"]["backtest"], "request": request}
                payload = {"run_id": identity, "request": request, "data": data}
            else:
                run_status = state.get("run_status", "COMPLETED")
                complete = run_status == "COMPLETED"
                terminal = run_status in ("COMPLETED", "FAILED", "INTERRUPTED")
                payload = {
                    "run_id": identity,
                    "request": request,
                    "status": run_status,
                    "created_at": "2026-11-15T00:00:00Z",
                    "started_at": None if run_status == "PENDING" else "2026-11-15T00:00:01Z",
                    "finished_at": "2026-11-15T00:00:02Z" if terminal else None,
                    "result_available": complete,
                    "failure": None,
                }
                if path.startswith("/research/"):
                    payload["result_status"] = "complete" if complete else None
                    if run_status in ("FAILED", "INTERRUPTED"):
                        payload["failure"] = {
                            "stage": "input_preparation",
                            "category": "upstream_operation",
                            "dependency": "futures",
                            "reason": "Controlled unavailable source.",
                        }
        else:
            status = 404
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if status in (200, 202):
            state["cookie"] += 1
            self.send_header(
                "Set-Cookie",
                f"lab_access_token={state['cookie']}; Path=/; HttpOnly; SameSite=Strict",
            )
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())


class CollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURES is None:
            raise unittest.SkipTest(
                "Run through collector.test.ts to supply formal fixture payloads"
            )
        cls.bridge = collect.Bridge().__enter__()
        cls.config = cls.bridge.call("config")

    @classmethod
    def tearDownClass(cls):
        cls.bridge.__exit__()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ddb03-test-only-")
        self.root = Path(self.temp.name)
        self.active, self.work = self.root / "bundles", self.root / "work"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ControlledServer)
        self.server.state = {
            "fixtures": deepcopy(FIXTURES),
            "presets": self.config["presets"],
            "calls": [],
            "cookie": 0,
            "runs": {},
            "submits": 0,
        }
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = httpx.Client(
            base_url=f"http://127.0.0.1:{self.server.server_port}", trust_env=False
        )
        self.collector = collect.Collector(
            self.bridge, self.client, "http://127.0.0.1:5173", 0.001, 0.5, 5
        )
        self.collector.login("tester", "synthetic-password")

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def generate(self, only=None):
        collect.generate(self.bridge, self.collector, only, self.active, self.work)

    def test_full_single_and_recovery(self):
        self.generate()
        collect.preflight(self.active)
        original = {item.name: item.read_bytes() for item in self.active.iterdir()}
        self.assertEqual(self.server.state["submits"], 3)
        self.assertEqual(
            {request.get("strategy_profile") for request in self.server.state["runs"].values()},
            {None, "expiry_to_M1_v1", "expiry_to_Q1_v1"},
        )
        self.generate()
        self.assertEqual(original, {item.name: item.read_bytes() for item in self.active.iterdir()})
        self.generate("catalog")
        for name, data in original.items():
            if name not in ("catalog.json", "manifest.json"):
                self.assertEqual((self.active / name).read_bytes(), data)
        actual_replace = collect.os.replace
        for interrupted_file in ("chain.json", "manifest.json"):

            def interrupt(source, target, target_name=interrupted_file):
                if Path(target) == self.active / target_name:
                    raise OSError("controlled interruption")
                return actual_replace(source, target)

            with patch.object(collect.os, "replace", side_effect=interrupt):
                with self.assertRaises(OSError):
                    self.generate("chain")
            self.assertTrue((self.work / "pending.json").exists())
            with collect.dataset_lock(self.work):
                collect.finish_transaction(self.active, self.work, self.config["registry"])
                collect.finish_transaction(self.active, self.work, self.config["registry"])
            collect.preflight(self.active)
        self.server.state["error_path"] = "/mo-option-chain"
        before = {item.name: item.read_bytes() for item in self.active.iterdir()}
        with self.assertRaises(collect.CollectionError):
            self.generate()
        self.assertEqual(before, {item.name: item.read_bytes() for item in self.active.iterdir()})

    def test_failures_and_no_partial_dataset(self):
        with self.assertRaises(collect.CollectionError):
            self.generate("chain")
        self.assertFalse(self.active.exists())
        for status in (401, 403, 404, 409, 503):
            self.server.state.update(error_path="/research/capabilities", error_status=status)
            with self.assertRaisesRegex(collect.CollectionError, f"status_{status}"):
                self.generate()
            self.assertFalse(self.active.exists())
        self.server.state.pop("error_path")
        self.server.state["repeat_cursor"] = True
        with self.assertRaisesRegex(collect.CollectionError, "repeated_cursor"):
            self.generate()
        self.assertFalse(self.active.exists())

    def test_lost_submit_timeout_and_terminal(self):
        entry = self.config["registry"][0]
        preset = self.config["presets"]["basis"]["request"]
        self.server.state["lost_submit"] = True
        with self.assertRaisesRegex(collect.CollectionError, "submit_outcome_unknown"):
            self.collector.capture(entry, preset)
        self.assertEqual(self.server.state["submits"], 1)
        self.server.state["lost_submit"] = False
        self.server.state["run_status"] = "RUNNING"
        self.collector.timeout = 0.05
        with self.assertRaisesRegex(collect.CollectionError, "poll_timeout"):
            self.collector.capture(entry, preset)
        for status in ("FAILED", "INTERRUPTED"):
            self.server.state["run_status"] = status
            with self.assertRaises(collect.CollectionError):
                self.collector.capture(entry, preset)

    def test_missing_details_and_actual_preflight_rejection(self):
        for suffix in ("analyses/analysis-quantile", "views/quantile-id"):
            self.server.state.update(
                error_path="/research/publications/pub-static-one/" + suffix, error_status=404
            )
            with self.assertRaisesRegex(collect.CollectionError, "status_404"):
                self.generate()
            self.assertFalse(self.active.exists())
        self.server.state.pop("error_path")
        self.generate()
        original = {item.name: item.read_bytes() for item in self.active.iterdir()}
        self.server.state["fixtures"]["chain"]["target_trade_date"] = "2026-11-10"
        with self.assertRaises(collect.CollectionError):
            self.generate("chain")
        self.assertEqual(original, {item.name: item.read_bytes() for item in self.active.iterdir()})
        self.server.state["fixtures"]["chain"]["target_trade_date"] = "2026-11-11"
        actual_replace = collect.os.replace

        def interrupt(source, target):
            if Path(target) == self.active / "chain.json":
                raise OSError("controlled interruption")
            return actual_replace(source, target)

        with patch.object(collect.os, "replace", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.generate("chain")
        journal = json.loads((self.work / "pending.json").read_bytes())
        (self.work / journal["candidate"] / "chain.json").write_bytes(b"corrupt")
        with collect.dataset_lock(self.work):
            with self.assertRaisesRegex(collect.CollectionError, "corrupt_pending"):
                collect.finish_transaction(self.active, self.work, self.config["registry"])
        self.assertTrue((self.work / "pending.json").exists())
        self.assertEqual(original, {item.name: item.read_bytes() for item in self.active.iterdir()})

    def test_auth_lock_and_numeric(self):
        self.collector.origin = "http://wrong-origin.invalid"
        with self.assertRaisesRegex(collect.CollectionError, "status_403"):
            self.collector.login("tester", "synthetic-password")
        self.collector.origin = "http://127.0.0.1:5173"
        self.client.cookies.clear()
        with self.assertRaisesRegex(collect.CollectionError, "status_401"):
            self.collector.request("get", "/auth/me")

        def disconnect(request):
            raise httpx.ConnectError("controlled failure", request=request)

        with httpx.Client(transport=httpx.MockTransport(disconnect)) as client:
            offline = collect.Collector(self.bridge, client, self.collector.origin, 1, 1, 1)
            with self.assertRaisesRegex(collect.CollectionError, "connection_failed"):
                offline.request("get", "http://127.0.0.1:1/auth/me")
        self.server.state["login_status"] = 401
        with self.assertRaisesRegex(collect.CollectionError, "status_401"):
            self.collector.login("tester", "synthetic-password")
        with collect.dataset_lock(self.work):
            with self.assertRaisesRegex(collect.CollectionError, "busy"):
                with collect.dataset_lock(self.work):
                    pass
        for token in ("9007199254740993", "0.10000000000000001", "-0", "1e400", "1e-400"):
            with self.assertRaisesRegex(collect.CollectionError, "unsafe_number.*nested"):
                self.bridge.call(
                    "response",
                    route="/auth/me",
                    method="get",
                    status=200,
                    bytes=base64.b64encode(('{"nested":[' + token + "]}").encode()).decode(),
                )


if __name__ == "__main__":
    FIXTURES = json.loads(Path(sys.argv.pop(1)).read_text(encoding="utf-8"))
    unittest.main(verbosity=2)
