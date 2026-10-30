"""Read-only G1 check for Historical Return Observation, using the root runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from queue import Empty, Queue
from threading import Thread
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

DEFAULT_TARGET = "http://127.0.0.1:8011"
DEFAULT_TIMEOUT = 2.0
MAX_BYTES = 4 * 1024 * 1024
EXPECTED = (
    ("get", "/research/capabilities", "list_research_capabilities"),
    ("get", "/research/capabilities/{id}", "get_research_capability"),
    ("post", "/research/preview", "preview_research_plan"),
    ("post", "/research/execute", "execute_research_plan"),
)
REASONS = {
    "compatible_openapi": "Observed the expected published Research OpenAPI structure.",
    "invalid_target": (
        "Target must be an HTTP(S) origin without credentials, path, query or fragment."
    ),
    "invalid_timeout": "Timeout must be finite, greater than zero and at most 30 seconds.",
    "connection_failed": "Could not connect to the target backend.",
    "request_timeout": "Backend readiness request exceeded the configured timeout.",
    "http_status": "OpenAPI endpoint did not return HTTP 200.",
    "content_type": "OpenAPI endpoint did not return a JSON media type.",
    "response_too_large": "OpenAPI response exceeded the 4 MiB checker limit.",
    "invalid_json": "OpenAPI response was not strict finite JSON.",
    "incompatible_openapi": "OpenAPI did not satisfy the Task's structural compatibility criteria.",
    "transport_error": "Backend readiness request failed at the HTTP transport boundary.",
}


def _finish(result: dict[str, Any], status: str, code: str) -> dict[str, Any]:
    return {**result, "status": status, "reason_code": code, "reason": REASONS[code]}


def exit_status(result: dict[str, Any]) -> int:
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["status"]]


def json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def _origin(value: str) -> str:
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError("invalid origin")
    url = urlsplit(value)
    if (url.scheme not in ("http", "https") or not url.hostname
            or url.username is not None or url.password is not None
            or url.path not in ("", "/") or url.query or url.fragment
            or "?" in value or "#" in value or "\\" in value):
        raise ValueError("invalid origin")
    port = url.port
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("invalid port")
    return urlunsplit((url.scheme, url.netloc.lower(), "", "", ""))


def _strict_json(body: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def finite(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite JSON number")
        return number

    def constant(value: str) -> Any:
        raise ValueError("non-finite JSON constant")

    return json.loads(body.decode("utf-8"), object_pairs_hook=pairs,
                      parse_float=finite, parse_constant=constant)


def _references(document: dict[str, Any], operations: list[dict[str, Any]]) -> list[str]:
    visited: set[str] = set()
    issues: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                if not isinstance(ref, str) or not ref.startswith("#/"):
                    issues.add("Research operation has a non-local or invalid reference")
                elif ref not in visited:
                    visited.add(ref)
                    target: Any = document
                    try:
                        for part in ref[2:].split("/"):
                            part = part.replace("~1", "/").replace("~0", "~")
                            target = target[int(part)] if isinstance(target, list) else target[part]
                        if not isinstance(target, dict):
                            raise ValueError("reference is not an object")
                        walk(target)
                    except (KeyError, IndexError, TypeError, ValueError):
                        issues.add("Research operation has an unresolved reference")
            for key, value in node.items():
                if key != "$ref":
                    walk(value)

    walk(operations)
    return sorted(issues)


def _compatibility(document: Any, observed: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not isinstance(document, dict):
        return ["OpenAPI root is not an object"]
    version = document.get("openapi")
    observed["openapi_version"] = version if isinstance(version, str) else None
    if not isinstance(version, str) or not re.fullmatch(r"3\.[01]\.\d+", version):
        issues.append("Expected OpenAPI 3.0.x or 3.1.x")
    info = document.get("info")
    if (not isinstance(info, dict)
            or any(not isinstance(info.get(k), str) or not info[k].strip()
                   for k in ("title", "version"))):
        issues.append("Expected nonempty info.title and info.version")
    paths = document.get("paths")
    if not isinstance(paths, dict):
        issues.append("Expected paths object")
        paths = {}
    methods = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}
    ids = [operation["operationId"] for path in paths.values() if isinstance(path, dict)
           for method, operation in path.items() if method in methods
           and isinstance(operation, dict) and isinstance(operation.get("operationId"), str)]
    if any(count > 1 for count in Counter(ids).values()):
        issues.append("OperationIds are not unique")
    operations: list[dict[str, Any]] = []

    def schema(container: Any) -> bool:
        if not isinstance(container, dict):
            return False
        content = container.get("content")
        media = content.get("application/json") if isinstance(content, dict) else None
        return isinstance(media, dict) and isinstance(media.get("schema"), dict)

    for method, path, expected_id in EXPECTED:
        item = paths.get(path)
        operation = item.get(method) if isinstance(item, dict) else None
        actual_id = operation.get("operationId") if isinstance(operation, dict) else None
        observed["operations"].append({"method": method.upper(), "path": path,
                                       "expected_operation_id": expected_id,
                                       "observed_operation_id": actual_id,
                                       "present": isinstance(operation, dict)})
        if not isinstance(operation, dict):
            issues.append(f"Missing {method.upper()} {path}")
            continue
        operations.append(operation)
        if actual_id != expected_id:
            issues.append(f"Unexpected operationId for {method.upper()} {path}")
        responses = operation.get("responses")
        if not isinstance(responses, dict) or not schema(responses.get("200")):
            issues.append(f"Missing 200 JSON schema for {method.upper()} {path}")
        if method == "post":
            body = operation.get("requestBody")
            if not isinstance(body, dict) or not schema(body) or body.get("required") is not True:
                issues.append(f"Missing required JSON request schema for POST {path}")
        if "{id}" in path:
            parameters = operation.get("parameters", [])
            path_parameters = item.get("parameters", []) if isinstance(item, dict) else []
            if (not isinstance(parameters, list) or not isinstance(path_parameters, list)
                    or not any(isinstance(p, dict) and p.get("name") == "id"
                               and p.get("in") == "path" and p.get("required") is True
                               for p in parameters + path_parameters)):
                issues.append("Missing required id path parameter")
            else:
                operations.extend(p for p in path_parameters if isinstance(p, dict))
    return issues + _references(document, operations)


def _request(result: dict[str, Any]) -> dict[str, Any]:
    observed = result["observations"]
    try:
        # Explicitly ignore proxy/environment settings and never follow redirects or retry.
        with httpx.Client(timeout=result["timeout_seconds"], trust_env=False,
                          follow_redirects=False) as client:
            with client.stream("GET", result["openapi_url"],
                               headers={"Accept": "application/json",
                                        "Accept-Encoding": "identity"}) as response:
                observed["http_status"] = response.status_code
                observed["content_type"] = response.headers.get("content-type", "")
                if response.status_code != 200:
                    return _finish(result, "FAIL", "http_status")
                media = observed["content_type"].split(";", 1)[0].strip().lower()
                if media != "application/json":
                    return _finish(result, "FAIL", "content_type")
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=16384):
                    body.extend(chunk)
                    observed["response_bytes"] = len(body)
                    if len(body) > MAX_BYTES:
                        return _finish(result, "FAIL", "response_too_large")
                observed["response_sha256"] = hashlib.sha256(body).hexdigest()
                try:
                    document = _strict_json(bytes(body))
                except (ValueError, UnicodeError, RecursionError):
                    return _finish(result, "FAIL", "invalid_json")
                try:
                    issues = _compatibility(document, observed)
                except RecursionError:
                    issues = ["OpenAPI structure exceeds checker traversal depth"]
                observed["compatibility_issues"] = issues
                if issues:
                    return _finish(result, "FAIL", "incompatible_openapi")
                return _finish(result, "PASS", "compatible_openapi")
    except httpx.TimeoutException:
        return _finish(result, "FAIL", "request_timeout")
    except httpx.ConnectError:
        return _finish(result, "FAIL", "connection_failed")
    except (httpx.HTTPError, OSError, ValueError):
        return _finish(result, "FAIL", "transport_error")


def check_backend(target: str = DEFAULT_TARGET,
                  timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    result: dict[str, Any] = {"schema_version": 1, "task_id": "historical_return_observation",
              "task_version": "1", "gate_id": "G1", "target": None, "openapi_url": None,
              "timeout_seconds": None,
              "observations": {"http_status": None, "content_type": None,
                               "response_bytes": 0, "response_sha256": None,
                               "openapi_version": None, "operations": [],
                               "compatibility_issues": []}}
    if (isinstance(timeout, bool) or not isinstance(timeout, int | float)
            or not math.isfinite(timeout) or not 0 < timeout <= 30):
        return _finish(result, "BLOCKED", "invalid_timeout")
    result["timeout_seconds"] = float(timeout)
    try:
        result["target"] = _origin(target)
    except (ValueError, TypeError):
        return _finish(result, "BLOCKED", "invalid_target")
    result["openapi_url"] = result["target"] + "/openapi.json"
    # Keep worker state separate: a deadline result cannot be mutated by a late response.
    worker_result = json.loads(json_text(result))
    completed: Queue[dict[str, Any]] = Queue(maxsize=1)
    worker = Thread(target=lambda: completed.put(_request(worker_result)), daemon=True)
    worker.start()
    try:
        return completed.get(timeout=timeout)
    except Empty:
        return _finish(result, "FAIL", "request_timeout")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=DEFAULT_TARGET)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="Seconds, 0 < t <= 30")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    args = parser.parse_args(argv)
    result = check_backend(args.base_url, args.timeout)
    print(json_text(result))
    return exit_status(result)


if __name__ == "__main__":
    raise SystemExit(main())
