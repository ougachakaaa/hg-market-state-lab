"""Local Workbench evidence recorder; run as a script, not an installed package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(__file__).resolve().parent / ".runs"
STATUSES = {"PASS", "FAIL", "BLOCKED", "SKIPPED"}


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return [_text(item, name) for item in value]


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value):
        raise ValueError("identity must be a generated lowercase UUID hex string")
    return value


def _json_bytes(value: Any) -> bytes:
    def check_keys(item: Any) -> None:
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("JSON object keys must be strings")
            for child in item.values():
                check_keys(child)
        elif isinstance(item, list | tuple):
            for child in item:
                check_keys(child)

    check_keys(value)
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        return encoded.encode("utf-8")
    except (TypeError, UnicodeError) as error:
        raise ValueError(f"value is not representable as UTF-8 JSON: {error}") from error


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _timestamp(value: Any) -> None:
    parsed = datetime.fromisoformat(_text(value, "timestamp"))
    if parsed.utcoffset() != UTC.utcoffset(None):
        raise ValueError("timestamp must be UTC")


def _load(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise ValueError(f"non-finite JSON value: {value}")

    return _object(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                              parse_constant=constant), str(path))


def _publish(path: Path, data: bytes) -> None:
    """Publish a whole file atomically without ever replacing a destination."""
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # Atomic create-if-absent, including on Windows.
    finally:
        Path(temporary).unlink(missing_ok=True)


def _task(value: Any) -> dict[str, Any]:
    task = _object(value, "task")
    for key in ("task_id", "version", "goal", "scope"):
        _text(task.get(key), key)
    approval = _object(task.get("approval"), "approval")
    if approval.get("kind") not in ("user_approved", "synthetic"):
        raise ValueError("approval.kind must be user_approved or synthetic")
    _text(approval.get("reference"), "approval.reference")
    for key in ("required_inputs", "allowed_capabilities", "planning_constraints",
                "expected_outputs", "acceptance_criteria"):
        _strings(task.get(key), key)
    gates = task.get("gates")
    if not isinstance(gates, list):
        raise ValueError("gates must be an array")
    graph: dict[str, list[str]] = {}
    for value in gates:
        gate = _object(value, "gate")
        gate_id = _text(gate.get("gate_id"), "gate_id")
        if gate_id in graph:
            raise ValueError("duplicate Gate definition")
        _text(gate.get("criteria"), "criteria")
        dependencies = _strings(gate.get("depends_on"), "depends_on")
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("duplicate Gate dependency")
        graph[gate_id] = dependencies
    visited: set[str] = set()
    active: set[str] = set()

    def visit(gate_id: str) -> None:
        if gate_id not in graph:
            raise ValueError("unknown Gate dependency")
        if gate_id in active:
            raise ValueError("cyclic Gate dependencies")
        if gate_id in visited:
            return
        active.add(gate_id)
        for dependency in graph[gate_id]:
            visit(dependency)
        active.remove(gate_id)
        visited.add(gate_id)

    for gate_id in graph:
        visit(gate_id)
    _json_bytes(task)
    return task


def _creation(value: Any) -> dict[str, Any]:
    request = _object(value, "creation request")
    _task(request.get("task"))
    _text(request.get("original_request"), "original_request")
    _object(request.get("resolved_inputs"), "resolved_inputs")
    _json_bytes(request)
    return request


def _gate(payload: dict[str, Any], task: dict[str, Any], artifacts: set[str]) -> None:
    gate_id = _text(payload.get("gate_id"), "gate_id")
    if gate_id not in {gate["gate_id"] for gate in task["gates"]}:
        raise ValueError("Gate is not defined in this Run's Task snapshot")
    status = payload.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("Gate status must be PASS / FAIL / BLOCKED / SKIPPED")
    reason = payload.get("reason")
    if not isinstance(reason, str) or (status != "PASS" and not reason.strip()):
        raise ValueError("non-PASS outcomes require an explicit reason")
    evidence = _strings(payload.get("evidence"), "evidence")
    if status == "PASS" and not evidence:
        raise ValueError("PASS requires actual registered evidence")
    if any(item not in artifacts for item in evidence):
        raise ValueError("evidence must reference previously registered artifacts in this Run")


def _event(payload: dict[str, Any]) -> None:
    _text(payload.get("operation"), "operation")
    _object(payload.get("details"), "details")


class RunStore:
    """Create Runs and append immutable evidence; never execute or approve Tasks."""

    def __init__(self, root: str | Path = DEFAULT_ROOT) -> None:
        self.root = Path(root).resolve()

    def _inside(self, *parts: str) -> Path:
        path = self.root.joinpath(*parts)
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("stored path escapes the Run store")
        # Do not follow aliases even if they point elsewhere inside the store.
        current = self.root
        for part in parts:
            current = current / part
            if current.is_symlink() or current.is_junction():
                raise ValueError("stored paths must not use symlinks or junctions")
        return path

    def create(self, request: dict[str, Any]) -> dict[str, Any]:
        # Detach caller objects; preserve the JSON snapshot, not a mutable reference.
        request = json.loads(_json_bytes(_creation(request)))
        run_id = uuid.uuid4().hex
        self.root.mkdir(parents=True, exist_ok=True)
        run = self._inside(run_id)
        run.mkdir()  # No collision overwrite or silent identity reuse.
        (run / "records").mkdir()
        (run / "blobs").mkdir()
        manifest = {"format_version": 1, "run_id": run_id, "created_at": _now(),
                    "task": request["task"],
                    "task_sha256": _digest(_json_bytes(request["task"])),
                    "original_request": request["original_request"],
                    "resolved_inputs": request["resolved_inputs"],
                    "workflow": request.get("workflow")}
        _publish(run / "manifest.json", _json_bytes(manifest))
        return manifest

    @contextmanager
    def _writer(self, run_id: str) -> Iterator[None]:
        lock = self._inside(_identifier(run_id), ".writer")
        lock.mkdir()  # An existing lock is an explicit busy error.
        try:
            yield
        finally:
            lock.rmdir()

    def _artifact(self, run_id: str, payload: dict[str, Any]) -> None:
        artifact_id = _identifier(payload.get("artifact_id"))
        _text(payload.get("label"), "label")
        source = _text(payload.get("source_location"), "source_location")
        if not Path(source).is_absolute():
            raise ValueError("source_location must be absolute")
        if payload.get("stored_path") != f"blobs/{artifact_id}":
            raise ValueError("invalid artifact stored_path")
        blob = self._inside(run_id, "blobs", artifact_id).read_bytes()
        size = payload.get("size_bytes")
        if type(size) is not int or size != len(blob) or payload.get("sha256") != _digest(blob):
            raise ValueError("artifact content digest or size mismatch")

    def read(self, run_id: str) -> dict[str, Any]:
        run_id = _identifier(run_id)
        manifest = _load(self._inside(run_id, "manifest.json"))
        if type(manifest.get("format_version")) is not int or manifest["format_version"] != 1:
            raise ValueError("unsupported storage format")
        if manifest.get("run_id") != run_id:
            raise ValueError("Run identity mismatch")
        _creation(manifest)
        _timestamp(manifest.get("created_at"))
        if manifest.get("task_sha256") != _digest(_json_bytes(manifest["task"])):
            raise ValueError("Task snapshot digest mismatch")
        paths = sorted(self._inside(run_id, "records").iterdir())
        records: list[dict[str, Any]] = []
        artifact_ids: set[str] = set()
        for path in paths:
            if path.name.startswith(".pending-"):
                continue
            sequence = len(records) + 1
            if path.name != f"{sequence:08d}.json":
                raise ValueError("noncontiguous or invalid record filename")
            record = _load(self._inside(run_id, "records", path.name))
            _json_bytes(record)
            if type(record.get("sequence")) is not int or record["sequence"] != sequence:
                raise ValueError("record sequence mismatch")
            _timestamp(record.get("recorded_at"))
            payload = _object(record.get("payload"), "payload")
            kind = record.get("kind")
            if kind == "artifact":
                self._artifact(run_id, payload)
                if payload["artifact_id"] in artifact_ids:
                    raise ValueError("duplicate artifact identity")
                artifact_ids.add(payload["artifact_id"])
            elif kind == "gate":
                _gate(payload, manifest["task"], artifact_ids)
            elif kind == "event":
                _event(payload)
            else:
                raise ValueError("unknown record kind")
            records.append(record)
        return {"manifest": manifest, "records": records,
                "gate_outcomes": [r for r in records if r["kind"] == "gate"],
                "events": [r for r in records if r["kind"] == "event"],
                "artifacts": [r for r in records if r["kind"] == "artifact"]}

    def _append(self, run_id: str, state: dict[str, Any], kind: str,
                payload: dict[str, Any]) -> dict[str, Any]:
        sequence = len(state["records"]) + 1
        record = {"sequence": sequence, "recorded_at": _now(), "kind": kind, "payload": payload}
        destination = self._inside(run_id, "records", f"{sequence:08d}.json")
        _publish(destination, _json_bytes(record))
        return record

    def gate(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload = json.loads(_json_bytes(_object(payload, "gate outcome")))
        with self._writer(run_id):
            state = self.read(run_id)
            _gate(payload, state["manifest"]["task"],
                  {r["payload"]["artifact_id"] for r in state["artifacts"]})
            return self._append(run_id, state, "gate", payload)

    def event(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload = json.loads(_json_bytes(_object(payload, "event")))
        _event(payload)
        with self._writer(run_id):
            return self._append(run_id, self.read(run_id), "event", payload)

    def artifact(self, run_id: str, request: dict[str, Any]) -> dict[str, Any]:
        request = _object(request, "artifact request")
        label = _text(request.get("label"), "label")
        source = Path(_text(request.get("path"), "path")).resolve(strict=True)
        data = source.read_bytes()
        with self._writer(run_id):
            state = self.read(run_id)
            artifact_id = uuid.uuid4().hex
            _publish(self._inside(run_id, "blobs", artifact_id), data)
            payload = {"artifact_id": artifact_id, "label": label,
                       "source_location": str(source), "stored_path": f"blobs/{artifact_id}",
                       "sha256": _digest(data), "size_bytes": len(data)}
            return self._append(run_id, state, "artifact", payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    for operation in ("create", "gate", "event", "artifact", "read"):
        command = commands.add_parser(operation)
        if operation != "create":
            command.add_argument("--run", required=True)
        if operation != "read":
            command.add_argument("--input", required=True, type=Path, help="UTF-8 JSON object")
    args = parser.parse_args(argv)
    store = RunStore(args.root)
    try:
        if args.command == "read":
            result = store.read(args.run)
        elif args.command == "create":
            result = store.create(_load(args.input))
        else:
            result = getattr(store, args.command)(args.run, _load(args.input))
        print(_json_bytes(result).decode("utf-8"))
    except (OSError, ValueError, TypeError) as error:
        print(f"workbench: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
