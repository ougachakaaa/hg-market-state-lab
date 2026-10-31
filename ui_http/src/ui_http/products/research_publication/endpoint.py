"""Bounded transport of the Research-owned public publication reader."""

from __future__ import annotations

import base64
import binascii
import os
import re
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from market_research.publication import (
    InconsistentPublication,
    InvalidPublicationInput,
    PublicationCorrupt,
    PublicationNotFound,
    PublicationStore,
    PublicationUnavailable,
    UnsupportedPublicationVersion,
    VerificationBudgetExceeded,
)

from .schemas import (
    AnalysisResponse,
    ErrorResponse,
    ManifestResponse,
    PublicationList,
    ViewResponse,
)

MAX_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
_verification_slot = BoundedSemaphore(1)
router = APIRouter(prefix="/research/publications", tags=["Research Publication"])
ERRORS: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorResponse, "description": description}
    for status, description in {
        400: "invalid_request",
        404: "not_found",
        409: "corrupt, inconsistent or unsupported_version",
        413: "response_too_large",
        503: "unavailable or verification_budget_exceeded",
        500: "internal_error",
    }.items()
}


class DeliveryError(Exception):
    def __init__(self, status: int, kind: str, detail: str):
        self.status, self.kind, self.detail = status, kind, detail


def fail(status: int, kind: str, detail: str) -> DeliveryError:
    return DeliveryError(status, kind, detail)


def store(request: Request) -> PublicationStore:
    injected = getattr(request.app.state, "publication_store", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]
    root = os.environ.get("LAB_RESEARCH_PUBLICATION_ROOT", "")
    if not root or not Path(root).is_absolute() or ".." in Path(root).parts or "\x00" in root:
        raise fail(503, "unavailable", "Publication storage is unavailable.")
    return PublicationStore(root)


def decode(value: Any) -> Any:
    """Decode only the admitted carrier forms used by the explicitly projected fields."""
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {"$tuple"}:
            return [decode(v) for v in value["$tuple"]]
        if set(value) == {"$mapping"}:
            return {k: decode(v) for k, v in value["$mapping"].items()}
        if set(value) == {"$date"}:
            return value["$date"]
        if set(value) == {"$type", "fields"}:
            return {k: decode(v) for k, v in value["fields"].items()}
        return {k: decode(v) for k, v in value.items()}
    return value


def identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value):
        raise fail(413, "response_too_large", "Publication is not deliverable under V1.")
    return value


def identity(raw: Any) -> dict[str, Any]:
    values = decode(raw)
    return dict(
        zip(
            (
                "metric",
                "subject",
                "metric_parameters",
                "horizon",
                "horizon_unit",
                "start_date",
                "end_date",
                "anchor_meaning",
                "bounds",
            ),
            [values[0], identifier(values[1]), dict(values[2]), *values[3:]],
            strict=True,
        )
    )


def summary(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis_id": raw["analysis_id"],
        "job_identity": identity(raw["job_identity"]),
        "request_id": identifier(raw["request_id"]),
        "spec": decode(raw["spec"]),
        "status": raw["status"],
        "views": [{"view_id": v["view_id"], "measure": v["measure"]} for v in raw["views"]],
    }


def manifest(raw: dict[str, Any]) -> dict[str, Any]:
    scope = decode(raw["scope"])
    scope["subjects"] = [identifier(s) for s in scope["subjects"]]
    for analysis in scope["analysis_requests"]:
        identifier(analysis["request_id"])
    return {
        "schema_version": 1,
        "publication_id": raw["publication_id"],
        "context": None,
        "scope": scope,
        "status": raw["status"],
        "jobs": [
            {
                "job_identity": identity(j["job_identity"]),
                "status": j["status"],
                "analyses": j["analyses"],
            }
            for j in raw["jobs"]
        ],
        "analyses": [summary(a) for a in raw["analyses"]],
        "source": {"sha256": raw["source"]["sha256"], "size": raw["source"]["size"]},
    }


def query(request: Request, allowed: set[str]) -> None:
    keys = list(request.query_params.multi_items())
    if any(key not in allowed for key, _ in keys) or len({k for k, _ in keys}) != len(keys):
        raise fail(400, "invalid_request", "Invalid Publication request.")


def cursor_encode(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("ascii")).decode("ascii").rstrip("=")


def cursor_decode(value: str) -> str:
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
            raise ValueError
        decoded = base64.b64decode(value + "=", altchars=b"-_", validate=True).decode("ascii")
        if cursor_encode(decoded) != value:
            raise ValueError
        return decoded
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise fail(400, "invalid_request", "Invalid Publication request.") from exc


def bounded(model: BaseModel) -> JSONResponse:
    body = model.model_dump_json().encode("utf-8")
    if len(body) > MAX_BYTES:
        raise fail(413, "response_too_large", "Publication response exceeds delivery bounds.")
    from starlette.responses import Response

    return Response(content=body, media_type="application/json")  # type: ignore[return-value]


def error(exc: Exception) -> JSONResponse:
    mapping = {
        InvalidPublicationInput: (400, "invalid_request", "Invalid Publication request."),
        PublicationNotFound: (404, "not_found", "Publication resource not found."),
        PublicationCorrupt: (409, "corrupt", "Publication artifact is corrupt."),
        InconsistentPublication: (409, "inconsistent", "Publication association is inconsistent."),
        UnsupportedPublicationVersion: (
            409,
            "unsupported_version",
            "Publication version is unsupported.",
        ),
        PublicationUnavailable: (503, "unavailable", "Publication storage is unavailable."),
        VerificationBudgetExceeded: (
            503,
            "verification_budget_exceeded",
            "Publication verification capacity exceeded.",
        ),
    }
    if isinstance(exc, DeliveryError):
        status, kind, detail = exc.status, exc.kind, exc.detail
    else:
        status, kind, detail = next(
            (entry for typ, entry in mapping.items() if isinstance(exc, typ)),
            (500, "internal_error", "Publication delivery failed."),
        )
    return JSONResponse(
        status_code=status, content={"error": {"kind": kind, "detail": detail, "param": None}}
    )


def verify_read(method: Any, *args: str) -> Any:
    if not _verification_slot.acquire(blocking=False):
        raise fail(
            503, "verification_budget_exceeded", "Publication verification capacity exceeded."
        )
    try:
        return method(*args, source_limit=MAX_SOURCE_BYTES)
    finally:
        _verification_slot.release()


@router.get(
    "",
    operation_id="list_research_publications",
    response_model=PublicationList,
    responses=ERRORS,
    openapi_extra={
        "parameters": [
            {
                "name": "limit",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
            },
            {
                "name": "after",
                "in": "query",
                "required": False,
                "description": "Opaque cursor returned by a prior list response.",
                "schema": {"type": "string"},
            },
        ]
    },
)
def list_publications(request: Request) -> JSONResponse:
    try:
        query(request, {"limit", "after"})
        raw_limit = request.query_params.get("limit", "50")
        if not re.fullmatch(r"[1-9][0-9]{0,2}", raw_limit) or int(raw_limit) > 100:
            raise fail(400, "invalid_request", "Invalid Publication request.")
        limit = int(raw_limit)
        after = request.query_params.get("after")
        items = store(request).list_publications(
            limit=limit, after=cursor_decode(after) if after is not None else None
        )
        data = [{"publication_id": m["publication_id"], "status": m["status"]} for m in items]
        return bounded(
            PublicationList.model_validate(
                {
                    "data": data,
                    "next_cursor": cursor_encode(items[-1]["publication_id"])
                    if len(items) == limit
                    else None,
                }
            )
        )
    except Exception as exc:
        return error(exc)


@router.get(
    "/{publication_id}",
    operation_id="get_research_publication",
    response_model=ManifestResponse,
    responses=ERRORS,
)
def get_manifest(request: Request, publication_id: str) -> JSONResponse:
    try:
        query(request, set())
        return bounded(
            ManifestResponse.model_validate(
                {"data": manifest(store(request).get_publication_manifest(publication_id))}
            )
        )
    except Exception as exc:
        return error(exc)


@router.get(
    "/{publication_id}/analyses/{analysis_id}",
    operation_id="get_research_publication_analysis",
    response_model=AnalysisResponse,
    responses=ERRORS,
)
def get_analysis(request: Request, publication_id: str, analysis_id: str) -> JSONResponse:
    try:
        query(request, set())
        reader = store(request)
        data = verify_read(reader.get_analysis, publication_id, analysis_id)
        status = data["summary"]["status"]
        result = decode(data["result"]) if status == "success" else None
        if result and result.get("method") == "quantile":
            result["points_and_values"] = [tuple(p) for p in result["points_and_values"]]
        return bounded(
            AnalysisResponse.model_validate(
                {
                    "data": {
                        "schema_version": 1,
                        "publication_id": publication_id,
                        "summary": summary(data["summary"]),
                        "outcome": status,
                        "reason": {
                            "success": None,
                            "failed": "Analysis failed.",
                            "not_attempted": "Analysis was not attempted.",
                        }[status],
                        "result": result,
                        "coverage": data["coverage"],
                    }
                }
            )
        )
    except Exception as exc:
        return error(exc)


@router.get(
    "/{publication_id}/views/{view_id}",
    operation_id="get_research_publication_view",
    response_model=ViewResponse,
    responses=ERRORS,
)
def get_view(request: Request, publication_id: str, view_id: str) -> JSONResponse:
    try:
        query(request, set())
        reader = store(request)
        return bounded(
            ViewResponse.model_validate(
                {"data": verify_read(reader.get_chart_view, publication_id, view_id)}
            )
        )
    except Exception as exc:
        return error(exc)
