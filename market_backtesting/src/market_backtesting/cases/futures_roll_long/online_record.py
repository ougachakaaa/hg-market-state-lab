"""Pure W2 record identity, timestamp and lifecycle validation."""

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from .online_codec import json_bytes
from .online_models import (
    CATEGORIES,
    DEPENDENCIES,
    SAFE_REASONS,
    STAGES,
    TERMINAL,
    FuturesRollOnlineError,
)

ID_PATTERN = re.compile(r"[0-9a-f]{32}")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")


def now() -> str:
    return datetime.now(UTC).isoformat()


def valid_id(run_id: str) -> None:
    if type(run_id) is not str or ID_PATTERN.fullmatch(run_id) is None:
        raise FuturesRollOnlineError("run_not_found")


def _timestamp(value: Any) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.tzinfo == UTC and parsed.isoformat() == value
    except ValueError:
        return False


def validate_state(state: Any, run_id: str, metadata: dict[str, Any]) -> None:
    if type(state) is not dict or set(state) != {
        "version",
        "run_id",
        "request_digest",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "failure",
        "result_digest",
    }:
        raise ValueError("state_fields")
    status = state["status"]
    if (
        type(state["version"]) is not int
        or state["version"] != 1
        or state["run_id"] != run_id
        or state["request_digest"] != hashlib.sha256(json_bytes(metadata)).hexdigest()
        or type(status) is not str
        or status not in {"PENDING", "RUNNING", *TERMINAL}
        or state["created_at"] != metadata["created_at"]
        or not _timestamp(state["created_at"])
    ):
        raise ValueError("state_identity")
    started, finished = state["started_at"], state["finished_at"]
    if (
        (started is not None and (not _timestamp(started) or started < state["created_at"]))
        or (
            finished is not None
            and (not _timestamp(finished) or finished < (started or state["created_at"]))
        )
        or (status == "PENDING" and started is not None)
        or (status in {"RUNNING", "COMPLETED"} and started is None)
        or (status in TERMINAL) != (finished is not None)
    ):
        raise ValueError("state_timestamps")
    digest = state["result_digest"]
    if status == "COMPLETED":
        if type(digest) is not str or DIGEST_PATTERN.fullmatch(digest) is None:
            raise ValueError("state_digest")
    elif digest is not None:
        raise ValueError("unexpected_digest")
    failure = state["failure"]
    if (status in {"FAILED", "INTERRUPTED"}) != (failure is not None):
        raise ValueError("state_failure")
    if failure is not None:
        if type(failure) is not dict or set(failure) != {
            "stage",
            "category",
            "dependency",
            "reason",
        }:
            raise ValueError("failure_fields")
        stage, category, dependency, reason = (
            failure[k] for k in ("stage", "category", "dependency", "reason")
        )
        if (
            type(stage) is not str
            or stage not in STAGES
            or type(category) is not str
            or type(reason) is not str
            or (
                dependency is not None
                and (type(dependency) is not str or dependency not in DEPENDENCIES)
            )
        ):
            raise ValueError("failure_type")
        if category in {"internal_failure", "interrupted"}:
            if stage != "execution" or reason != category or dependency is not None:
                raise ValueError("execution_failure")
        elif category in {"result_too_large", "serialization_failure", "storage_failure"}:
            if stage != "result_publication" or reason != category or dependency is not None:
                raise ValueError("publication_failure")
        elif category not in CATEGORIES or reason not in SAFE_REASONS:
            raise ValueError("case_failure")
        if status == "INTERRUPTED" and category != "interrupted":
            raise ValueError("interruption_failure")
