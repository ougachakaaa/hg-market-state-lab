"""Task-specific G1 acceptance: local HTTP only, no market acquisition."""

import copy
import hashlib
import json
import runpy
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from support import RunStore

TASK_DIR = Path(__file__).resolve().parents[1] / "tasks" / "historical_return_observation"
CHECK_SCRIPT = TASK_DIR / "runtime" / "check_backend.py"
RECORD_SCRIPT = TASK_DIR / "runtime" / "record_g1.py"
CHECK = runpy.run_path(str(CHECK_SCRIPT))
RECORD = runpy.run_path(str(RECORD_SCRIPT))


def compatible_document():
    # Independent minimal published contract, not derived from checker constants.
    response = {"description": "Success", "content": {"application/json": {
        "schema": {"$ref": "#/components/schemas/Result"}}}}
    body = {"required": True, "content": {"application/json": {
        "schema": {"$ref": "#/components/schemas/Plan"}}}}
    return {
        "openapi": "3.1.0", "info": {"title": "HTTP fixture", "version": "1"},
        "paths": {
            "/research/capabilities": {"get": {
                "operationId": "list_research_capabilities", "responses": {"200": response}}},
            "/research/capabilities/{id}": {"get": {
                "operationId": "get_research_capability", "responses": {"200": response},
                "parameters": [{"name": "id", "in": "path", "required": True,
                                "schema": {"type": "string"}}]}},
            "/research/preview": {"post": {
                "operationId": "preview_research_plan", "responses": {"200": response},
                "requestBody": body}},
            "/research/execute": {"post": {
                "operationId": "execute_research_plan", "responses": {"200": response},
                "requestBody": body}},
        },
        "components": {"schemas": {"Result": {"type": "object"}, "Plan": {"type": "object"}}},
    }


@contextmanager
def http_fixture(body=None, *, status=200, content_type="application/json", delay=0, trickle=False):
    if body is None:
        body = json.dumps(compatible_document()).encode()
    calls = []
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append((self.command, self.path))
            if delay:
                release.wait(delay)
            try:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if trickle:
                    for byte in body:
                        if release.wait(0.02):
                            break
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                else:
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def check(target, timeout=2):
    return CHECK["check_backend"](target, timeout)


def test_actual_compatible_http_is_pass_and_deterministic(monkeypatch):
    # Environment proxy configuration must not affect explicit local readiness.
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    with http_fixture() as (target, calls):
        result = check(target + "/")
        assert result == check(target)
        assert calls == [("GET", "/openapi.json")] * 2
    assert result["status"] == "PASS"
    assert CHECK["exit_status"](result) == 0
    assert result["observations"]["http_status"] == 200
    assert result["observations"]["openapi_version"] == "3.1.0"
    assert len(result["observations"]["operations"]) == 4
    assert not result["observations"]["compatibility_issues"]
    assert len(result["observations"]["response_sha256"]) == 64


def test_stopped_backend_is_attempted_fail():
    # A bound, non-listening socket reserves an isolated stopped-service port.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        result = check(f"http://127.0.0.1:{reserved.getsockname()[1]}", 0.3)
    assert result["status"] == "FAIL"
    assert result["reason_code"] in {"connection_failed", "request_timeout"}
    assert result["reason"]


@pytest.mark.parametrize(("body", "status", "media", "reason"), [
    (b"<html>Other server</html>", 200, "text/html", "content_type"),
    (b"{}", 404, "application/json", "http_status"),
    (b"{}", 302, "application/json", "http_status"),
    (b"not JSON", 200, "application/json", "invalid_json"),
    (b'{"openapi":"3.1.0","openapi":"3.1.0"}', 200, "application/json", "invalid_json"),
    (b'{"x":NaN}', 200, "application/json", "invalid_json"),
    (b'{"x":1e999}', 200, "application/json", "invalid_json"),
    (b"[]", 200, "application/json", "incompatible_openapi"),
    (b"{}", 200, "application/json", "incompatible_openapi"),
])
def test_wrong_service_malformed_json_http_error_no_redirect(body, status, media, reason):
    with http_fixture(body, status=status, content_type=media) as (target, calls):
        result = check(target)
        assert calls == [("GET", "/openapi.json")]
    assert result["status"] == "FAIL"
    assert result["reason_code"] == reason
    assert CHECK["exit_status"](result) == 1


@pytest.mark.parametrize("defect", [
    "version", "info", "missing_path", "method", "operation_id", "duplicate_id",
    "response_schema", "request_schema", "required_body", "path_parameter", "dangling_ref",
    "external_ref", "nested_ref",
])
def test_incompatible_openapi_structure(defect):
    document = copy.deepcopy(compatible_document())
    preview = document["paths"]["/research/preview"]["post"]
    match defect:
        case "version":
            document["openapi"] = "2.0"
        case "info":
            document["info"]["title"] = ""
        case "missing_path":
            del document["paths"]["/research/execute"]
        case "method":
            document["paths"]["/research/preview"] = {"get": preview}
        case "operation_id":
            preview["operationId"] = "other_preview"
        case "duplicate_id":
            document["paths"]["/other"] = {"get": copy.deepcopy(preview)}
        case "response_schema":
            preview["responses"] = {"200": {"description": "No body"}}
        case "request_schema":
            preview["requestBody"] = {}
        case "required_body":
            preview["requestBody"]["required"] = False
        case "path_parameter":
            document["paths"]["/research/capabilities/{id}"]["get"]["parameters"] = []
        case "dangling_ref":
            del document["components"]["schemas"]["Result"]
        case "external_ref":
            document["components"]["schemas"]["Result"] = {"$ref": "http://example.invalid/schema"}
        case "nested_ref":
            document["components"]["schemas"]["Result"] = {
                "properties": {"nested": {"$ref": "#/components/schemas/Absent"}}}
    with http_fixture(json.dumps(document).encode()) as (target, _):
        result = check(target)
    assert result["status"] == "FAIL"
    assert result["reason_code"] == "incompatible_openapi"
    assert result["observations"]["compatibility_issues"]


def test_oversized_response_fails():
    with http_fixture(b" " * (CHECK["MAX_BYTES"] + 1)) as (target, _):
        assert check(target)["reason_code"] == "response_too_large"


@pytest.mark.parametrize("trickle", [False, True])
def test_actual_timeout_is_bounded_including_slow_trickle(trickle):
    with http_fixture(delay=1 if not trickle else 0, trickle=trickle) as (target, _):
        start = time.monotonic()
        result = check(target, 0.1)
        assert time.monotonic() - start < 0.7
    assert result["status"] == "FAIL"
    assert result["reason_code"] == "request_timeout"
    frozen = CHECK["json_text"](result)
    time.sleep(0.02)
    assert CHECK["json_text"](result) == frozen


def test_connection_timeout_is_explicit():
    # Deterministic connect-timeout injection; real sockets cover response timeouts above.
    error = httpx.ConnectTimeout("private diagnostic")
    with patch.object(httpx.Client, "stream", side_effect=error):
        result = check("http://127.0.0.1:8011")
    assert result["reason_code"] == "request_timeout"
    assert "private diagnostic" not in CHECK["json_text"](result)


@pytest.mark.parametrize("target", [
    "ftp://127.0.0.1", "http://user:secret@localhost", "http://localhost/path",
    "http://localhost?token=secret", "http://localhost#fragment", "http://localhost:0",
    "http://localhost:99999", "http://localhost\n", "http://localhost\\other",
])
def test_invalid_target_blocks_without_network_or_leaking_input(target):
    with patch.object(httpx.Client, "stream", side_effect=AssertionError("No request allowed")):
        result = check(target)
    assert result["status"] == "BLOCKED"
    assert result["reason_code"] == "invalid_target"
    assert "secret" not in CHECK["json_text"](result)


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf"), 31])
def test_invalid_timeout_blocks(timeout):
    assert check("http://127.0.0.1:8011", timeout)["reason_code"] == "invalid_timeout"


@pytest.mark.parametrize(("body", "status"), [(None, "PASS"), (b"{}", "FAIL")])
def test_actual_check_run_evidence_round_trip_and_same_run_ownership(tmp_path, body, status):
    root = tmp_path / "runs"
    with http_fixture(body) as (target, calls):
        report = RECORD["record_g1"](root, "WB-02 G1 acceptance only", target, 2)
        assert calls == [("GET", "/openapi.json")]
    assert report["result"]["status"] == status
    assert report["evidence_verified"] is True
    store = RunStore(root)
    state = store.read(report["run_id"])
    task = json.loads((TASK_DIR / "task.json").read_text(encoding="utf-8"))
    assert state["manifest"]["task"] == task
    assert [g["name"] for g in task["gates"]] == [
        "Backend Ready", "Authentication", "Capability Discovery",
        "Workflow Planning and Persistence", "Execution", "Visualization"]
    assert state["manifest"]["resolved_inputs"]["research_inputs"].startswith("unresolved")
    outcomes = [r["payload"] for r in state["gate_outcomes"]]
    assert [(g["gate_id"], g["status"]) for g in outcomes] == [
        ("G1", status), ("G2", "SKIPPED"), ("G6", "SKIPPED")]
    assert all(g["reason"] for g in outcomes)
    assert report["unexecuted_gates"] == ["G3", "G4", "G5"]
    artifact = state["artifacts"][0]["payload"]
    data = Path(report["preserved_readiness_path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == artifact["sha256"]
    assert json.loads(data) == report["result"]
    assert outcomes[0]["evidence"] == [artifact["artifact_id"]]
    assert not Path(artifact["source_location"]).exists()
    other = store.create({"task": task, "original_request": "Independent G1 Run",
                          "resolved_inputs": {}})["run_id"]
    with pytest.raises(ValueError, match="this Run"):
        store.gate(other, outcomes[0])


def test_blocked_check_preserved_in_run(tmp_path):
    report = RECORD["record_g1"](tmp_path, "Readiness only", "invalid", 2)
    assert report["result"]["status"] == "BLOCKED"
    assert report["evidence_verified"]


def test_cli_result_and_exit_status(tmp_path):
    with http_fixture() as (target, _):
        command = [sys.executable, str(CHECK_SCRIPT), "--base-url", target]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
        assert completed.returncode == 0
        assert json.loads(completed.stdout)["status"] == "PASS"
    blocked = subprocess.run([sys.executable, str(CHECK_SCRIPT), "--timeout", "nan"],
                             capture_output=True, text=True, timeout=10)
    assert blocked.returncode == 2
    assert json.loads(blocked.stdout)["status"] == "BLOCKED"
    with http_fixture(b"{}") as (target, _):
        failed = subprocess.run([sys.executable, str(RECORD_SCRIPT), "--base-url", target,
                                 "--root", str(tmp_path), "--original-request", "G1 only"],
                                capture_output=True, text=True, timeout=10)
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["evidence_verified"] is True


def test_real_composed_openapi_without_market_or_cache_side_effects(tmp_path, monkeypatch):
    # Actual published schemas must pass, without invoking any published Research operation.
    from market_research.descriptive import capabilities, execution
    from market_research.descriptive.cases import trailing_return
    from ui_http import app

    def forbidden(*args, **kwargs):
        raise AssertionError("G1 must not perform capability discovery or business execution")

    monkeypatch.setattr(capabilities, "list_capabilities", forbidden)
    monkeypatch.setattr(execution, "execute_batch", forbidden)
    monkeypatch.setattr(trailing_return, "prepare_inputs", forbidden)
    document = app.openapi()
    monkeypatch.chdir(tmp_path)
    with http_fixture(json.dumps(document).encode()) as (target, calls):
        with patch.object(Path, "open", side_effect=AssertionError("No file I/O in checker")):
            result = check(target)
        assert calls == [("GET", "/openapi.json")]
    assert result["status"] == "PASS", result
    assert list(tmp_path.iterdir()) == []
