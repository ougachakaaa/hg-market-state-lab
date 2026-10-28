"""G3 local HTTP acceptance; fake publication never admits new business capabilities."""

import base64
import copy
import hashlib
import json
import runpy
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
from test_historical_return_g1 import compatible_document

TASK_DIR = Path(__file__).resolve().parents[1] / "tasks" / "historical_return_observation"
G1 = runpy.run_path(str(TASK_DIR / "record_g1.py"))
G3 = runpy.run_path(str(TASK_DIR / "record_g3.py"))
CHECK = G3["CHECK"]
FIXTURE = Path(__file__).parent / "fixtures" / "capability.json"
REQUIRED = "trailing_cumulative_return_v1"


def descriptor(id=REQUIRED):
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    value["id"] = id
    return value


def response(value, status=200, media="application/json", delay=0, encoding="", trickle=False):
    return {"body": value if isinstance(value, bytes) else json.dumps(value).encode(),
            "status": status, "media": media, "delay": delay, "encoding": encoding,
            "trickle": trickle}


@contextmanager
def backend(catalog=None):
    catalog = [descriptor()] if catalog is None else catalog
    routes = {"/openapi.json": response(compatible_document()),
              "/research/capabilities": response(catalog)}
    for item in catalog:
        if isinstance(item, dict) and "id" in item:
            routes["/research/capabilities/" + item["id"]] = response(item)
    calls = []
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append((self.command, self.path))
            route = routes.get(self.path, response({"error": {"kind": "capability_not_found",
                                 "detail": "Unknown Research capability", "param": None}}, 404))
            release.wait(route["delay"])
            try:
                self.send_response(route["status"])
                self.send_header("Content-Type", route["media"])
                if route["encoding"]:
                    self.send_header("Content-Encoding", route["encoding"])
                self.end_headers()
                if route["trickle"]:
                    for byte in route["body"]:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        if release.wait(0.02):
                            break
                else:
                    self.wfile.write(route["body"])
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_POST(self):
            calls.append((self.command, self.path))
            self.send_error(405)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", routes, calls
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def ready(root, target):
    return G1["record_g1"](root, "G1 readiness; subsequent WB-03 read-only discovery", target, 2)


def inspect(root, run_id, timeout=2):
    return CHECK["check_capabilities"](RunStore(root).read(run_id), root, timeout)


@pytest.mark.parametrize("count", [0, 1, 3])
def test_count_is_observed_empty_is_complete_but_not_task_ready(tmp_path, count):
    catalog = [descriptor()] + [descriptor(f"synthetic-test-only-{i}") for i in range(count - 1)]
    if count == 0:
        catalog = []
    with backend(catalog) as (target, _, calls):
        run = ready(tmp_path, target)
        result = inspect(tmp_path, run["run_id"])
        assert calls == [("GET", "/openapi.json"), ("GET", "/research/capabilities")] + [
            ("GET", "/research/capabilities/" + d["id"]) for d in catalog]
    assert result["status"] == ("PASS" if count else "FAIL")
    assert result["capability_count"] == count
    assert result["capability_ids"] == [d["id"] for d in catalog]
    assert result["capabilities"] == catalog
    assert result["discovery_complete"] is True
    assert result["task_readiness"] is bool(count)
    assert result["missing_task_requirements"] == ([] if count else [REQUIRED])
    assert result["live_market_readiness"] == "not_probed"
    assert result["prerequisites"]["authentication"] == "not_established"


def test_unrelated_valid_capability_is_not_task_support(tmp_path):
    with backend([descriptor("synthetic-other-case")]) as (target, _, _):
        run = ready(tmp_path, target)
        result = inspect(tmp_path, run["run_id"])
    assert result["reason_code"] == "missing_task_capability"
    assert result["discovery_complete"] is True
    assert result["missing_task_requirements"] == [REQUIRED]


def test_permitted_extra_publication_is_preserved_and_compared_without_bool_coercion(tmp_path):
    catalog = [descriptor()]
    catalog[0]["future_publication"] = {"flag": True}
    with backend(catalog) as (target, routes, _):
        run = ready(tmp_path, target)
        passed = inspect(tmp_path, run["run_id"])
        assert passed["status"] == "PASS"
        assert passed["capabilities"] == catalog
        detail = copy.deepcopy(catalog[0])
        detail["future_publication"]["flag"] = 1
        routes["/research/capabilities/" + REQUIRED] = response(detail)
        failed = inspect(tmp_path, run["run_id"])
    assert failed["status"] == "FAIL"
    assert failed["exchanges"][1]["error"] == "detail_content_mismatch"


@pytest.mark.parametrize("prerequisite", ["missing_g1", "failed_g1", "later_failed_g1",
    "fake_g1_evidence", "bad_g1_target", "missing_g2", "g2_fail", "g2_pass", "wrong_skip_reason"])
def test_unmet_prerequisites_block_all_requests(tmp_path, prerequisite):
    with backend() as (target, _, calls):
        run = ready(tmp_path, target)
        store = RunStore(tmp_path)
        run_id = run["run_id"]
        if prerequisite in ("missing_g1", "failed_g1", "missing_g2"):
            manifest = store.create({"task": store.read(run_id)["manifest"]["task"],
                "original_request": "Synthetic prerequisite test", "resolved_inputs": {}})
            run_id = manifest["run_id"]
            if prerequisite == "missing_g2":
                source = Path(run["preserved_readiness_path"])
                artifact = store.artifact(run_id, {"label": "G1 copy test", "path": str(source)})
                store.gate(run_id, {"gate_id": "G1", "status": "PASS", "reason": "test",
                                   "evidence": [artifact["payload"]["artifact_id"]]})
            if prerequisite == "failed_g1":
                store.gate(run_id, {"gate_id": "G1", "status": "FAIL", "reason": "test failed",
                                   "evidence": []})
        elif prerequisite == "later_failed_g1":
            store.gate(run_id, {"gate_id": "G1", "status": "FAIL", "reason": "later failure",
                               "evidence": []})
        elif prerequisite in ("fake_g1_evidence", "bad_g1_target"):
            source = tmp_path / "fake.json"
            value = {} if prerequisite == "fake_g1_evidence" else copy.deepcopy(run["result"])
            if prerequisite == "bad_g1_target":
                value["target"] = "http://user:secret@localhost"
            source.write_text(json.dumps(value), encoding="utf-8")
            artifact = store.artifact(run_id, {"label": "unsuitable G1", "path": str(source)})
            store.gate(run_id, {"gate_id": "G1", "status": "PASS", "reason": "unsuitable",
                               "evidence": [artifact["payload"]["artifact_id"]]})
        else:
            status = {"g2_pass": "PASS", "g2_fail": "FAIL"}.get(prerequisite, "SKIPPED")
            store.gate(run_id, {"gate_id": "G2", "status": status, "reason": "not MVP deferral",
                "evidence": [run["artifact"]["artifact_id"]] if status == "PASS" else []})
        calls.clear()
        report = G3["record_g3"](tmp_path, run_id)
        assert calls == []
    assert report["result"]["status"] == "BLOCKED"
    assert report["result"]["exchanges"] == []
    assert report["evidence_verified"] is True


@pytest.mark.parametrize(("bad_response", "reason"), [
    (response(b"not-json"), "invalid_json"),
    (response(b'{"x":1,"x":2}'), "invalid_json"),
    (response(b'[NaN]'), "invalid_json"),
    (response(b'[1e999]'), "invalid_json"),
    (response({}), "invalid_descriptor"),
    (response([{}]), "invalid_descriptor"),
    (response(b"<html>wrong service</html>", media="text/html"), "content_type"),
    (response({"error": "safe test"}, 500), "http_status"),
    (response({}, 302), "http_status"),
    (response(b"encoded", encoding="gzip"), "content_encoding"),
])
def test_list_failures_preserve_original_response(tmp_path, bad_response, reason):
    with backend() as (target, routes, calls):
        run = ready(tmp_path, target)
        routes["/research/capabilities"] = bad_response
        report = G3["record_g3"](tmp_path, run["run_id"])
        assert calls[-1] == ("GET", "/research/capabilities")
        assert len(calls) == 2
    assert report["result"]["status"] == "FAIL"
    exchange = report["result"]["exchanges"][0]
    assert exchange["error"] == reason
    assert base64.b64decode(exchange["body_base64"]) == bad_response["body"]
    assert exchange["response_sha256"] == hashlib.sha256(bad_response["body"]).hexdigest()
    assert report["evidence_verified"] is True


@pytest.mark.parametrize("defect", ["missing_field", "nested_type", "numeric_true", "numeric_false",
    "numeric_string", "method_literal", "tuple_size", "duplicate_id", "blank_id", "unsafe_id"])
def test_transport_shape_and_routable_unique_identity(tmp_path, defect):
    d = descriptor()
    match defect:
        case "missing_field":
            del d["limitations"]
        case "nested_type":
            d["subject"] = []
        case "numeric_true":
            d["on_job_failure_required"] = 1
        case "numeric_false":
            d["subject"]["example_is_default"] = 0
        case "numeric_string":
            d["analysis_methods"][0]["minimum_points"] = "1"
        case "method_literal":
            d["analysis_methods"][0]["method"] = "unsupported"
        case "tuple_size":
            d["analysis_methods"] = []
        case "blank_id":
            d["id"] = " "
        case "unsafe_id":
            d["id"] = ".."
    catalog = [d, d] if defect == "duplicate_id" else [d]
    with backend(catalog) as (target, _, calls):
        run = ready(tmp_path, target)
        result = inspect(tmp_path, run["run_id"])
        assert len(calls) == 2
    assert result["status"] == "FAIL"


@pytest.mark.parametrize("defect", ["404", "wrong_id", "description", "constraints", "extra_field",
    "malformed", "invalid_shape"])
def test_detail_failures_and_continue_inspecting_remaining_capabilities(tmp_path, defect):
    catalog = [descriptor(), descriptor("synthetic-second")]
    detail = copy.deepcopy(catalog[0])
    match defect:
        case "wrong_id":
            detail["id"] = "different"
        case "description":
            detail["purpose"] = "Changed purpose"
        case "constraints":
            detail["window_constraints"] = ["Changed constraint"]
        case "extra_field":
            detail["additional_publication"] = True
    with backend(catalog) as (target, routes, calls):
        run = ready(tmp_path, target)
        path = "/research/capabilities/" + REQUIRED
        if defect == "404":
            del routes[path]
        elif defect == "malformed":
            routes[path] = response(b"malformed")
        elif defect == "invalid_shape":
            routes[path] = response({})
        else:
            routes[path] = response(detail)
        result = inspect(tmp_path, run["run_id"])
        assert calls[-1] == ("GET", "/research/capabilities/synthetic-second")
        assert len(calls) == 4
    assert result["status"] == "FAIL"
    assert result["capability_count"] == 2
    assert result["discovery_complete"] is False
    assert result["task_readiness"] is False
    assert result["exchanges"][1]["error"]


@pytest.mark.parametrize("detail", [False, True])
@pytest.mark.parametrize("trickle", [False, True])
def test_request_deadline_is_bounded_with_partial_evidence(tmp_path, detail, trickle):
    with backend() as (target, routes, _):
        run = ready(tmp_path, target)
        path = "/research/capabilities" + ("/" + REQUIRED if detail else "")
        routes[path] = response(descriptor() if detail else [descriptor()],
                                delay=0 if trickle else 1, trickle=trickle)
        start = time.monotonic()
        result = inspect(tmp_path, run["run_id"], 0.15)
        assert time.monotonic() - start < 0.9
        frozen = json.dumps(result)
        time.sleep(0.04)
        assert json.dumps(result) == frozen
    assert result["status"] == "FAIL"
    assert result["exchanges"][-1]["error"] == "request_timeout"
    assert result["exchanges"][-1]["body_complete"] is False


def test_connection_error_never_leaks_private_exception_text(tmp_path):
    with backend() as (target, _, _):
        run = ready(tmp_path, target)
        with patch.object(httpx.Client, "stream", side_effect=httpx.ConnectError("secret-token")):
            result = inspect(tmp_path, run["run_id"])
    assert result["status"] == "FAIL"
    assert result["exchanges"][0]["error"] == "connection_failed"
    assert "secret-token" not in json.dumps(result)


def test_oversize_preserves_bounded_prefix(tmp_path):
    with backend() as (target, routes, _):
        run = ready(tmp_path, target)
        routes["/research/capabilities"] = response(b" " * (CHECK["MAX_BYTES"] + 100))
        result = inspect(tmp_path, run["run_id"])
    exchange = result["exchanges"][0]
    assert exchange["error"] == "response_too_large"
    assert exchange["response_bytes"] == CHECK["MAX_BYTES"]
    assert exchange["body_complete"] is False


@pytest.mark.parametrize("timeout", [0, -1, True, 31, float("nan"), float("inf")])
def test_invalid_timeout_blocks_without_http(tmp_path, timeout):
    with backend() as (target, _, calls):
        run = ready(tmp_path, target)
        calls.clear()
        result = inspect(tmp_path, run["run_id"], timeout)
        assert calls == []
    assert result["status"] == "BLOCKED"
    assert result["reason_code"] == "invalid_timeout"


def test_same_run_round_trip_rechecks_preserve_manifest_workflow_and_previous_records(tmp_path):
    with backend() as (target, _, calls):
        run = ready(tmp_path, target)
        before = RunStore(tmp_path).read(run["run_id"])
        report = G3["record_g3"](tmp_path, run["run_id"])
        repeat = G3["record_g3"](tmp_path, run["run_id"])
        assert report["result"] == repeat["result"]
        assert len(calls) == 5
    after = RunStore(tmp_path).read(run["run_id"])
    assert after["manifest"] == before["manifest"]
    assert after["records"][:4] == before["records"]
    assert len(after["records"]) == 8
    assert report["result"]["prerequisites"]["g1_evidence"] == run["artifact"]["artifact_id"]
    assert report["unexecuted_gates"] == ["G4", "G5"]
    saved = Path(report["preserved_discovery_path"])
    assert json.loads(saved.read_bytes()) == report["result"]
    assert not Path(report["artifact"]["source_location"]).exists()
    other = ready(tmp_path, "http://127.0.0.1:1")
    with pytest.raises(ValueError):
        RunStore(tmp_path).gate(other["run_id"], {"gate_id": "G3", "status": "PASS", "reason": "",
                                                "evidence": [report["artifact"]["artifact_id"]]})


def test_rejects_unsupported_task_and_corrupt_evidence(tmp_path):
    with backend() as (target, _, _):
        run = ready(tmp_path, target)
    request = {"task": RunStore(tmp_path).read(run["run_id"])["manifest"]["task"],
               "original_request": "synthetic different version", "resolved_inputs": {}}
    request["task"]["version"] = "2"
    other = RunStore(tmp_path).create(request)
    with pytest.raises(ValueError, match="Unsupported Task"):
        G3["record_g3"](tmp_path, other["run_id"])
    Path(run["preserved_readiness_path"]).write_text("corrupt", encoding="utf-8")
    with pytest.raises(ValueError):
        G3["record_g3"](tmp_path, run["run_id"])


def test_concurrent_run_change_prevents_g3_publication(tmp_path):
    with backend() as (target, _, _):
        run = ready(tmp_path, target)
        real_check = CHECK["check_capabilities"]

        def concurrent(state, root, timeout):
            result = real_check(state, root, timeout)
            RunStore(root).event(run["run_id"], {"operation": "concurrent test", "details": {}})
            return result

        with patch.dict(CHECK, {"check_capabilities": concurrent}):
            with pytest.raises(ValueError, match="Run changed"):
                G3["record_g3"](tmp_path, run["run_id"])
    assert all(r["payload"]["gate_id"] != "G3"
               for r in RunStore(tmp_path).read(run["run_id"])["gate_outcomes"])


def test_cli_statuses_and_fresh_read(tmp_path):
    with backend() as (target, routes, _):
        run = ready(tmp_path, target)
        command = [sys.executable, str(TASK_DIR / "record_g3.py"), "--root", str(tmp_path),
                   "--run", run["run_id"]]
        for status, code in (("PASS", 0), ("FAIL", 1), ("BLOCKED", 2)):
            if status == "FAIL":
                routes["/research/capabilities"] = response(b"not JSON")
            completed = subprocess.run(command + (["--timeout", "nan"] if code == 2 else []),
                                       capture_output=True, text=True, timeout=15)
            assert completed.returncode == code, completed.stderr
            report = json.loads(completed.stdout)
            assert report["result"]["status"] == status
            assert report["evidence_verified"] is True
    read = subprocess.run([sys.executable, str(TASK_DIR.parents[1] / "run_store.py"), "--root",
                           str(tmp_path), "read", "--run", run["run_id"]],
                          capture_output=True, text=True, timeout=10)
    assert read.returncode == 0
    assert len(json.loads(read.stdout)["records"]) == 10
    missing = subprocess.run(command[:-1] + ["0" * 32], capture_output=True, text=True, timeout=15)
    assert missing.returncode == 1
    assert missing.stdout == ""
    assert "Traceback" not in missing.stderr


def test_actual_composed_contract_and_zero_market_side_effects(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from market_research.descriptive import capabilities
    from market_research.descriptive.cases import trailing_return
    from ui_http import app
    from ui_http.products.research import endpoint

    def forbidden(*args, **kwargs):
        raise AssertionError("G3 must not preview, execute or acquire data")

    monkeypatch.setattr(endpoint, "preview_plan", forbidden)
    monkeypatch.setattr(endpoint, "execute_batch", forbidden)
    monkeypatch.setattr(trailing_return, "prepare_inputs", forbidden)
    document = app.openapi()
    # Bind client validation to exactly the schema FastAPI publishes, including nested types.
    schema = CHECK["CATALOG"].json_schema(ref_template="#/components/schemas/{model}")
    for name, definition in schema.pop("$defs").items():
        assert definition == document["components"]["schemas"][name]
    published_list = document["paths"]["/research/capabilities"]["get"]["responses"]["200"][
        "content"]["application/json"]["schema"].copy()
    published_list.pop("title")
    assert schema == published_list
    assert document["paths"]["/research/capabilities/{id}"]["get"]["responses"]["200"][
        "content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/CapabilityDescription"}
    client = TestClient(app)
    with backend() as (target, routes, calls):
        routes["/openapi.json"] = response(document)
        for path in ("/research/capabilities", "/research/capabilities/" + REQUIRED):
            actual = client.get(path)
            assert actual.status_code == 200
            routes[path] = response(actual.content)
        monkeypatch.setattr(capabilities, "list_capabilities", forbidden)
        monkeypatch.setattr(capabilities, "get_capability", forbidden)
        monkeypatch.setattr(endpoint, "list_capabilities", forbidden)
        monkeypatch.setattr(endpoint, "get_capability", forbidden)
        run = ready(tmp_path / "runs", target)
        monkeypatch.chdir(tmp_path)
        report = G3["record_g3"](tmp_path / "runs", run["run_id"])
        assert calls == [("GET", "/openapi.json"), ("GET", "/research/capabilities"),
                         ("GET", "/research/capabilities/" + REQUIRED)]
    assert report["result"]["status"] == "PASS"
    assert report["result"]["capabilities"] == [descriptor()]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["runs"]
