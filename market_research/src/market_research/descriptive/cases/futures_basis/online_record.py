"""Case-specific online application and bounded, private run store."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from market_statistics import IntervalCountSpec, QuantileSpec

from .evidence import PROFILE_REPORT, json_bytes
from .inputs import DEFINITION_VERSION, FuturesBasisRequest
from .report import ReportRequest, ReportResult
from .validation import validate_online_request

PROFILE = "r01a_standard_v1"
MAX_REPORT_BYTES = 32 * 1024 * 1024
ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
FAILURE_CATEGORIES = {
    "input_preparation": {"invalid_request", "upstream_operation", "invalid_public_input"},
    "observation_construction": {"invalid_prepared_inputs", "slot_resolution", "numerical_failure"},
    "report_composition": {"invalid_report_request", "composition_failure"},
    "result_publication": {"result_too_large", "serialization_failure"},
    "execution": {"interrupted", "internal_failure"},
}
DEPENDENCIES = {"request", "calendar_cffex", "calendar_sse", "futures", "index"}


class OnlineError(Exception):
    """Safe public application error; kind is mapped by the inbound adapter."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def standard_report_request(request: FuturesBasisRequest) -> ReportRequest:
    """Construct the frozen server-selected R01-A analysis profile."""
    validate_online_request(request)
    result = ReportRequest(
        request,
        QuantileSpec((0.0, 0.25, 0.5, 0.75, 1.0)),
        (
            IntervalCountSpec((-1000, -500, -100, 0, 100, 500, 1000), "index_points"),
            IntervalCountSpec((-1, -0.1, -0.01, 0, 0.01, 0.1, 1), "decimal_ratio"),
            IntervalCountSpec((-10, -1, -0.1, 0, 0.1, 1, 10), "decimal_ratio"),
        ),
    )
    result.validate()
    return result


def _request_data(request: FuturesBasisRequest) -> dict[str, str]:
    return dict(
        case=request.case,
        product_code=request.product_code,
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat(),
        analysis_profile=PROFILE,
    )


def _validate_reader(reader: Any, report: ReportResult, request: FuturesBasisRequest) -> None:
    if not isinstance(reader, dict) or reader.get("profile") != PROFILE_REPORT:
        raise ValueError("Invalid reader profile")
    if report.status not in ("complete", "partial") or reader.get("status") != report.status:
        raise ValueError("Invalid report status")
    if report.request != standard_report_request(request):
        raise ValueError("Report request differs from standard profile")
    if reader.get("request") != json.loads(json_bytes(report.request)):
        raise ValueError("Reader request mismatch")
    if report.source.prepared.request != request:
        raise ValueError("Report source mismatch")
    fingerprint = report.source.prepared.input_fingerprint
    if (
        not isinstance(fingerprint, str)
        or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
        or reader.get("fingerprint") != fingerprint
        or reader.get("definition_version") != DEFINITION_VERSION
    ):
        raise ValueError("Invalid input fingerprint or definition")


def _decode(data: bytes) -> Any:
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(_value: str) -> Any:
        raise ValueError("Nonfinite JSON number")

    return json.loads(data, object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def _state(
    status: str,
    created: str,
    started: str | None = None,
    finished: str | None = None,
    result_status: str | None = None,
    digest: str | None = None,
    failure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return dict(
        version=1,
        status=status,
        created_at=created,
        started_at=started,
        finished_at=finished,
        result_status=result_status,
        result_digest=digest,
        failure=failure,
    )


def _valid_failure(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"stage", "category", "dependency", "reason"}:
        return False
    stage = value["stage"]
    if (
        type(stage) is not str
        or stage not in FAILURE_CATEGORIES
        or type(value["category"]) is not str
        or value["category"] not in FAILURE_CATEGORIES[stage]
    ):
        return False
    if stage == "input_preparation":
        if type(value["dependency"]) is not str or value["dependency"] not in DEPENDENCIES:
            return False
    elif value["dependency"] is not None:
        return False
    return value["reason"] == _failure_reason(stage, value["category"])


def _failure_reason(stage: str, category: str) -> str:
    if category == "interrupted":
        return "The previous execution was interrupted."
    return {
        "input_preparation": "Required public market inputs could not be prepared.",
        "observation_construction": "The observation could not be constructed.",
        "report_composition": "The report could not be composed.",
        "result_publication": "The report could not be published.",
        "execution": "The execution could not finish.",
    }[stage]


def _validate_state(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {
        "version",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "result_status",
        "result_digest",
        "failure",
    }:
        raise OnlineError("corrupt")
    if type(value["version"]) is not int or value["version"] != 1:
        raise OnlineError("unsupported_version")
    status = value["status"]
    if status not in ("PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"):
        raise OnlineError("corrupt")
    if not isinstance(value["created_at"], str) or not value["created_at"]:
        raise OnlineError("corrupt")
    for key in ("started_at", "finished_at"):
        if value[key] is not None and not isinstance(value[key], str):
            raise OnlineError("corrupt")
    for key in ("created_at", "started_at", "finished_at"):
        if value[key] is not None:
            try:
                parsed = datetime.fromisoformat(value[key])
                offset = parsed.utcoffset()
                if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
                    raise ValueError
            except (ValueError, TypeError, AttributeError):
                raise OnlineError("corrupt") from None
    if status == "PENDING" and value["started_at"] is not None:
        raise OnlineError("corrupt")
    if status in ("RUNNING", "COMPLETED") and value["started_at"] is None:
        raise OnlineError("corrupt")
    if (value["finished_at"] is None) != (status in ("PENDING", "RUNNING")):
        raise OnlineError("corrupt")
    if status == "COMPLETED":
        if (
            value["result_status"] not in ("complete", "partial")
            or not isinstance(value["result_digest"], str)
            or re.fullmatch(r"[0-9a-f]{64}", value["result_digest"]) is None
            or value["failure"] is not None
        ):
            raise OnlineError("corrupt")
    elif (
        value["result_status"] is not None
        or value["result_digest"] is not None
        or (status in ("FAILED", "INTERRUPTED")) != (value["failure"] is not None)
    ):
        raise OnlineError("corrupt")
    if value["failure"] is not None and not _valid_failure(value["failure"]):
        raise OnlineError("corrupt")


class _ExecutionFailure(Exception):
    def __init__(self, stage: str, category: str, dependency: str | None = None) -> None:
        self.stage, self.category, self.dependency = stage, category, dependency


def _failure(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, _ExecutionFailure):
        stage, category, dependency = exc.stage, exc.category, exc.dependency
    else:
        stage, category, dependency = "execution", "internal_failure", None
    if (
        stage not in FAILURE_CATEGORIES
        or category not in FAILURE_CATEGORIES[stage]
        or (stage == "input_preparation" and dependency not in DEPENDENCIES)
        or (stage != "input_preparation" and dependency is not None)
    ):
        stage, category, dependency = "execution", "internal_failure", None
    reason = _failure_reason(stage, category)
    return dict(stage=stage, category=category, dependency=dependency, reason=reason)
