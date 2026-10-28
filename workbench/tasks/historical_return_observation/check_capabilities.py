"""Task-specific read-only G3 inspection; see CAPABILITY_DISCOVERY.md."""

from __future__ import annotations

import base64
import hashlib
import math
import re
import runpy
from pathlib import Path
from queue import Empty, Queue
from threading import Lock, Thread
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter, ValidationError

from market_research.descriptive.capabilities import CapabilityDescription

TASK_DIR = Path(__file__).resolve().parent
G1 = runpy.run_path(str(TASK_DIR / "check_backend.py"))
MAX_BYTES = 4 * 1024 * 1024
REQUIRED_ID = "trailing_cumulative_return_v1"
G2_REASON = "Authentication deferred in current MVP; loopback backend has no authentication."
DESCRIPTOR = TypeAdapter(CapabilityDescription)
CATALOG = TypeAdapter(list[CapabilityDescription])
REASONS = {
    "discovered": "All published capabilities inspected; required Task capability is supported.",
    "missing_task_capability": "Discovery completed but the required Task capability is absent.",
    "invalid_timeout": "Timeout must be finite, greater than zero and at most 30 seconds.",
    "g1_required": "Latest G1 must PASS with suitable same-Run backend readiness evidence.",
    "g2_required": "Latest G2 must carry the Task-authorized MVP SKIPPED disposition.",
    "discovery_failed": "Discovery responses failed transport, contract or consistency checks.",
}


def _finish(result: dict[str, Any], status: str, code: str) -> dict[str, Any]:
    return {**result, "status": status, "reason_code": code, "reason": REASONS[code]}


def _prerequisites(state: dict[str, Any], root: Path, result: dict[str, Any]) -> str | None:
    latest = {r["payload"]["gate_id"]: r for r in state["gate_outcomes"]}
    g1 = latest.get("G1")
    g2 = latest.get("G2")
    result["prerequisites"] = {
        "g1_sequence": g1["sequence"] if g1 else None,
        "g2_sequence": g2["sequence"] if g2 else None,
        "g1_evidence": None,
        "authentication": "not_established",
    }
    if not g1 or g1["payload"]["status"] != "PASS":
        return "g1_required"
    artifacts = {r["payload"]["artifact_id"]: r["payload"] for r in state["artifacts"]}
    for artifact_id in g1["payload"]["evidence"]:
        artifact = artifacts[artifact_id]
        body = (root.resolve() / state["manifest"]["run_id"] / artifact["stored_path"]).read_bytes()
        try:
            saved = G1["_strict_json"](body)
            observed = saved["observations"]
            target = G1["_origin"](saved["target"])
            expected = [{"method": method.upper(), "path": path,
                         "expected_operation_id": operation, "observed_operation_id": operation,
                         "present": True} for method, path, operation in G1["EXPECTED"]]
            if (saved["schema_version"] != 1 or saved["task_id"] != result["task_id"]
                    or saved["task_version"] != "1" or saved["gate_id"] != "G1"
                    or saved["status"] != "PASS" or saved["reason_code"] != "compatible_openapi"
                    or saved["openapi_url"] != target + "/openapi.json"
                    or observed["http_status"] != 200
                    or observed["content_type"].split(";", 1)[0].strip().lower()
                    != "application/json"
                    or not re.fullmatch(r"3\.[01]\.\d+", observed["openapi_version"])
                    or observed["operations"] != expected or observed["compatibility_issues"] != []
                    or not re.fullmatch(r"[0-9a-f]{64}", observed["response_sha256"])
                    or not 0 < observed["response_bytes"] <= G1["MAX_BYTES"]):
                continue
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            continue
        result["target"] = target
        result["prerequisites"]["g1_evidence"] = artifact_id
        break
    if result["target"] is None:
        return "g1_required"
    if (not g2 or g2["payload"]["status"] != "SKIPPED"
            or g2["payload"]["reason"] != G2_REASON):
        return "g2_required"
    return None


def _fetch(target: str, path: str, timeout: float) -> dict[str, Any]:
    # Capture a bounded immutable snapshot even when DNS or slow trickle outlasts the deadline.
    lock = Lock()
    body = bytearray()
    observed: dict[str, Any] = {"method": "GET", "path": path, "http_status": None,
        "content_type": None, "content_encoding": None, "body_complete": False, "error": None}
    done: Queue[bool] = Queue(maxsize=1)

    def request() -> None:
        error = None
        try:
            with httpx.Client(timeout=timeout, trust_env=False, follow_redirects=False) as client:
                with client.stream("GET", target + path, headers={"Accept": "application/json",
                                   "Accept-Encoding": "identity"}) as response:
                    with lock:
                        observed.update(http_status=response.status_code,
                            content_type=response.headers.get("content-type", ""),
                            content_encoding=response.headers.get("content-encoding", ""))
                    for chunk in response.iter_raw():
                        with lock:
                            remaining = MAX_BYTES - len(body)
                            body.extend(chunk[:remaining])
                        if len(chunk) > remaining:
                            error = "response_too_large"
                            break
                    else:
                        with lock:
                            observed["body_complete"] = True
        except httpx.TimeoutException:
            error = "request_timeout"
        except httpx.ConnectError:
            error = "connection_failed"
        except (httpx.HTTPError, OSError, ValueError):
            error = "transport_error"
        finally:
            with lock:
                observed["error"] = error
            done.put(True)

    Thread(target=request, daemon=True).start()
    deadline_error = None
    try:
        done.get(timeout=timeout)
    except Empty:
        deadline_error = "request_timeout"
    with lock:
        snapshot = dict(observed)
        received = bytes(body)
    snapshot.update(body_base64=base64.b64encode(received).decode("ascii"),
                    response_bytes=len(received),
                    response_sha256=hashlib.sha256(received).hexdigest())
    if deadline_error:
        snapshot.update(error=deadline_error, body_complete=False)
    if not snapshot["error"]:
        if snapshot["http_status"] != 200:
            snapshot["error"] = "http_status"
        elif snapshot["content_type"].split(";", 1)[0].strip().lower() != "application/json":
            snapshot["error"] = "content_type"
        elif snapshot["content_encoding"].strip().lower() not in ("", "identity"):
            snapshot["error"] = "content_encoding"
    return snapshot


def _validate(exchange: dict[str, Any], catalog: bool) -> Any:
    if exchange["error"]:
        return None
    body = base64.b64decode(exchange["body_base64"])
    try:
        value = G1["_strict_json"](body)
    except (ValueError, UnicodeError, RecursionError):
        exchange["error"] = "invalid_json"
        return None
    try:
        # Same public return type FastAPI publishes; never invoke the Python capability catalog.
        (CATALOG if catalog else DESCRIPTOR).validate_json(body, strict=True)
        for descriptor in value if catalog else [value]:
            # Pydantic boolean Literals also accept numeric 1/0; require JSON booleans.
            if (type(descriptor["on_job_failure_required"]) is not bool
                    or type(descriptor["subject"]["example_is_default"]) is not bool):
                raise ValueError("boolean literal type mismatch")
    except (ValidationError, ValueError, TypeError, KeyError, RecursionError):
        exchange["error"] = "invalid_descriptor"
        return None
    return value


def check_capabilities(state: dict[str, Any], root: Path, timeout: float = 2) -> dict[str, Any]:
    """Inspect a Run already verified by RunStore.read; recording is the caller's job."""
    result: dict[str, Any] = {"schema_version": 1, "task_id": "historical_return_observation",
        "task_version": "1", "gate_id": "G3", "target": None, "timeout_seconds": None,
        "prerequisites": {}, "capability_count": None, "capability_ids": [], "capabilities": [],
        "discovery_complete": False, "task_readiness": False,
        "missing_task_requirements": [REQUIRED_ID], "live_market_readiness": "not_probed",
        "exchanges": []}
    if (isinstance(timeout, bool) or not isinstance(timeout, int | float)
            or not math.isfinite(timeout) or not 0 < timeout <= 30):
        return _finish(result, "BLOCKED", "invalid_timeout")
    result["timeout_seconds"] = float(timeout)
    blocked = _prerequisites(state, root, result)
    if blocked:
        return _finish(result, "BLOCKED", blocked)
    exchange = _fetch(result["target"], "/research/capabilities", timeout)
    result["exchanges"].append(exchange)
    catalog = _validate(exchange, catalog=True)
    if catalog is None:
        return _finish(result, "FAIL", "discovery_failed")
    ids = [d["id"] for d in catalog]
    result.update(capability_count=len(catalog), capability_ids=ids)
    if (len(set(ids)) != len(ids) or any(not id.strip() or id in (".", "..")
            or "/" in id or "\\" in id or any(ord(c) < 32 for c in id) for id in ids)):
        exchange["error"] = "invalid_catalog_identity"
        return _finish(result, "FAIL", "discovery_failed")
    for listed in catalog:
        path = "/research/capabilities/" + quote(listed["id"], safe="")
        exchange = _fetch(result["target"], path, timeout)
        result["exchanges"].append(exchange)
        detail = _validate(exchange, catalog=False)
        if detail is not None:
            result["capabilities"].append(detail)
            if detail["id"] != listed["id"]:
                exchange["error"] = "detail_identity_mismatch"
            elif G1["json_text"](detail) != G1["json_text"](listed):
                exchange["error"] = "detail_content_mismatch"
    if any(e["error"] for e in result["exchanges"]):
        return _finish(result, "FAIL", "discovery_failed")
    result["discovery_complete"] = True
    result["missing_task_requirements"] = [] if REQUIRED_ID in ids else [REQUIRED_ID]
    result["task_readiness"] = not result["missing_task_requirements"]
    if not result["task_readiness"]:
        return _finish(result, "FAIL", "missing_task_capability")
    return _finish(result, "PASS", "discovered")
