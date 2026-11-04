"""Execute one equity_index_futures_basis_monitor Task request and preserve its Run.

The Agent owns natural-language interpretation and passes the original request plus
canonical families/dates (or one documented relative expression). This script owns
deterministic validation, one public CFFEX basis product call per family, the public
CFFEX Calendar check, the three delivery files and same-Run Workbench evidence.

Usage from the repository root:

    poetry run python workbench/tasks/equity_index_futures_basis_monitor/runtime/run_monitor.py \
        --input request.json --authorization-reference "user authorization text"

No market capability is called without a non-empty authorization reference.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import runpy
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryError,
    CFFEXEquityIndexBasisHistoryRequest,
    CFFEXEquityIndexBasisHistoryResult,
    CFFEXEquityIndexBasisObservation,
    run_cffex_equity_index_basis_history,
)

SHANGHAI: Any
try:
    from zoneinfo import ZoneInfo

    SHANGHAI = ZoneInfo("Asia/Shanghai")
except Exception:  # pragma: no cover - tzdata is a project dependency
    SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")

TASK_DIR = Path(__file__).resolve().parents[1]
TASK_PATH = TASK_DIR / "task.json"
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_STORE_ROOT = Path(__file__).resolve().parents[3] / ".runs"
PRODUCT_ID = "data_snapshot.products.cffex_equity_index_basis_history"
CALENDAR_ID = "data_lake.datasets.tushare_trade_calendar"
TASK_ID = "equity_index_futures_basis_monitor"
TASK_VERSION = "1"

CANONICAL_FAMILIES = ("IF", "IH", "IC", "IM")
FAMILY_ORDER = {family: index for index, family in enumerate(CANONICAL_FAMILIES)}
FAMILY_UNDERLYING = {
    "IF": "000300.SH",
    "IH": "000016.SH",
    "IC": "000905.SH",
    "IM": "000852.SH",
}
FAMILY_ALIASES = {
    "沪深300": "IF",
    "沪深300指数": "IF",
    "上证50": "IH",
    "上证50指数": "IH",
    "中证500": "IC",
    "中证500指数": "IC",
    "中证1000": "IM",
    "中证1000指数": "IM",
}
ALL_FAMILY_ALIASES = {"所有股指期货", "全部股指期货"}
SLOTS = ("M0", "M1", "Q1", "Q2")
SLOT_ORDER = {slot: index for index, slot in enumerate(SLOTS)}
CSV_COLUMNS = (
    "trade_date",
    "futures_family",
    "underlying_code",
    "contract_code",
    "contract_slot",
    "delist_date",
    "days_to_delist",
    "underlying_close",
    "futures_close",
    "basis_pct",
    "annualized_basis_pct",
)
STATIC_LIMITATIONS = [
    "annualized_basis_pct is a simple linear calendar-day annualization of the market "
    "price difference; it is not an executable arbitrage yield, financing-adjusted "
    "return or rolling-hold return.",
    "Annualized values near delivery are highly sensitive to days_to_delist; they are "
    "not smoothed or capped.",
    "Market price difference only; no fair value, prediction, trading advice, "
    "transaction-cost, dividend, financing or roll-strategy meaning.",
    "All active CFFEX ordinary-monthly contracts in the public result are retained; "
    "no volume, open-interest, main-contract or liquidity filter is applied.",
    "A successful public result proves a complete M0/M1/Q1/Q2 panel only on its actual "
    "observation dates; expected-session coverage is checked separately.",
    "V1 has no chart, statistical distribution, prediction, trading recommendation or "
    "backtest.",
]
REPORT_HEADINGS = (
    "## Query and actual range",
    "## Latest session by family",
    "## Coverage and failures",
    "## Source, formula and units",
    "## Near-expiry sensitivity",
    "## Limitations",
)

RunStore: Any = runpy.run_path(str(REPO_ROOT / "workbench" / "run_store.py"))["RunStore"]


class InputError(Exception):
    """Semantic input problem with the Gate status it produces."""

    def __init__(self, status: str, reason: str) -> None:
        self.status = status
        self.reason = reason
        super().__init__(reason)


@dataclass
class CalendarAttempt:
    status: str
    reason: str | None
    start_date: date | None
    end_date: date | None
    query_ranges: list[dict[str, str]]
    records: tuple[Any, ...]
    coverage: Any | None
    ensure: Any | None
    export_payload: dict[str, Any] | None
    export_bytes: bytes | None
    export_sha256: str | None


@dataclass
class Resolution:
    gate_status: str
    reason: str
    original_request: str
    families: list[str]
    start_date: date | None
    end_date: date | None
    date_expression: str | None
    kind: str
    anchor_date: date | None
    anchor_rule: str
    execution_date: date
    execution_instant_utc: str
    execution_instant_shanghai: str
    calendar: CalendarAttempt
    resolved_inputs: dict[str, Any]


@dataclass
class FamilyAcquisition:
    family: str
    request: CFFEXEquityIndexBasisHistoryRequest | None
    result: CFFEXEquityIndexBasisHistoryResult | None
    status: str
    error_reason: str | None
    error_message: str | None
    observations: tuple[CFFEXEquityIndexBasisObservation, ...]


@dataclass
class FamilyCoverage:
    family: str
    status: str
    reason: str | None
    expected: list[date]
    missing: list[date]
    unexpected: list[date]
    latest_expected: date | None
    latest_observed: bool | None


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError("FAIL", f"{name} must be a nonempty string")
    return value.strip()


def _parse_day(value: Any, name: str) -> date:
    if not isinstance(value, str):
        raise InputError("FAIL", f"{name} must be a YYYY-MM-DD string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise InputError("FAIL", f"{name} must be a real YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise InputError("FAIL", f"{name} must use YYYY-MM-DD")
    return parsed


def _optional_day(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return _parse_day(value, "anchor_date")
    except InputError:
        raise


def _decimal(value: Any) -> str:
    return repr(float(value))


def _coverage_payload(coverage: Any | None) -> dict[str, Any] | None:
    if coverage is None:
        return None
    return {
        "requested_units": coverage.requested_units,
        "successful_units": coverage.successful_units,
        "missing_units": coverage.missing_units,
        "pending_units": coverage.pending_units,
        "failed_units": coverage.failed_units,
        "complete": coverage.complete,
    }


def _ensure_payload(ensure: Any | None) -> dict[str, Any] | None:
    if ensure is None:
        return None
    return {
        "requested_units": ensure.requested_units,
        "already_successful_units": ensure.already_successful_units,
        "attempted_units": ensure.attempted_units,
        "succeeded_units": ensure.succeeded_units,
        "failed_units": ensure.failed_units,
        "records_written": ensure.records_written,
        "complete": ensure.complete,
    }


def _calendar_export_payload(export: Any) -> dict[str, Any]:
    scope = export.scope
    window = export.window
    return {
        "dataset": export.dataset,
        "view": export.view,
        "export_schema_version": export.export_schema_version,
        "scope": {"exchange": scope.exchange},
        "window": {
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
        },
        "coverage": _coverage_payload(export.coverage),
        "records": [
            {
                "exchange": record.exchange,
                "cal_date": record.cal_date.isoformat(),
                "is_open": record.is_open,
                "pretrade_date": (
                    record.pretrade_date.isoformat()
                    if record.pretrade_date is not None
                    else None
                ),
            }
            for record in export.records
        ],
    }


def _calendar_failure(exc: Exception) -> str:
    return f"{type(exc).__name__}: CFFEX calendar access failed"


def _product_failure(exc: Exception) -> str:
    if isinstance(exc, CFFEXEquityIndexBasisHistoryError):
        message = str(exc).strip()
        return message[:500] if message else exc.reason
    return f"{type(exc).__name__}: public product invocation failed"


def _execution_instant(
    execution_date: date | None, now: datetime | None
) -> tuple[date, datetime]:
    instant = now if now is not None else datetime.now(SHANGHAI)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=SHANGHAI)
    instant = instant.astimezone(SHANGHAI)
    if execution_date is None:
        return instant.date(), instant
    if type(execution_date) is not date:
        raise ValueError("execution_date must be a datetime.date")
    return execution_date, instant


def _parse_families(params: Mapping[str, Any]) -> list[str]:
    raw = params.get("futures_families")
    if raw is None:
        raise InputError("BLOCKED", "futures_families is required")
    if not isinstance(raw, list):
        raise InputError("FAIL", "futures_families must be an array")
    if not raw:
        raise InputError("BLOCKED", "futures_families must not be empty")
    seen: set[str] = set()
    selected: set[str] = set()
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise InputError("FAIL", "every futures family must be a nonempty string")
        token = item.strip()
        key = token.upper()
        if key in seen:
            raise InputError("FAIL", f"duplicate futures family: {token}")
        seen.add(key)
        if token in ALL_FAMILY_ALIASES:
            selected.update(CANONICAL_FAMILIES)
        elif key in FAMILY_ORDER:
            selected.add(key)
        elif token in FAMILY_ALIASES:
            selected.add(FAMILY_ALIASES[token])
        else:
            raise InputError("FAIL", f"unsupported or ambiguous futures family: {token}")
    if not selected:
        raise InputError("BLOCKED", "no supported futures family was resolved")
    return [family for family in CANONICAL_FAMILIES if family in selected]


def _chinese_integer(value: str) -> int:
    digits = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    if value in digits:
        return digits[value]
    if value.count("十") != 1:
        raise ValueError(value)
    left, right = value.split("十")
    tens = digits[left] if left else 1
    ones = digits[right] if right else 0
    if left and left not in digits:
        raise ValueError(value)
    if right and right not in digits:
        raise ValueError(value)
    return tens * 10 + ones


def _parse_relative(expression: str) -> tuple[str, int | None]:
    compact = re.sub(r"\s+", "", expression)
    if compact == "最近两周":
        return "two_weeks", None
    matched = re.fullmatch(r"最近([0-9]+|[零一二两三四五六七八九十]+)个交易日", compact)
    if matched is None:
        raise InputError("FAIL", f"unsupported date expression: {expression}")
    text = matched.group(1)
    try:
        count = int(text) if text.isdigit() else _chinese_integer(text)
    except ValueError as exc:
        raise InputError("FAIL", f"unsupported date expression: {expression}") from exc
    if count <= 0:
        raise InputError("FAIL", "the trading-session count must be positive")
    return "n_sessions", count


def _parse_params(params: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(params, Mapping):
        raise InputError("FAIL", "input must be a JSON object")
    original_request = _text(params.get("original_request"), "original_request")
    families = _parse_families(params)
    start_supplied = params.get("start_date") is not None
    end_supplied = params.get("end_date") is not None
    expression_supplied = params.get("date_expression") is not None
    if expression_supplied and (start_supplied or end_supplied):
        raise InputError(
            "FAIL", "supply either start_date/end_date or date_expression, not both"
        )
    anchor = _optional_day(params.get("anchor_date"))
    if expression_supplied:
        expression = _text(params.get("date_expression"), "date_expression")
        relative_kind, count = _parse_relative(expression)
        return {
            "original_request": original_request,
            "families": families,
            "kind": "relative",
            "start": None,
            "end": None,
            "expression": expression,
            "relative_kind": relative_kind,
            "count": count,
            "anchor": anchor,
        }
    if anchor is not None:
        raise InputError("FAIL", "anchor_date is only valid with date_expression")
    if start_supplied != end_supplied:
        raise InputError("FAIL", "start_date and end_date must be supplied together")
    if not start_supplied and not end_supplied:
        raise InputError("BLOCKED", "start_date/end_date or date_expression is required")
    start = _parse_day(params.get("start_date"), "start_date")
    end = _parse_day(params.get("end_date"), "end_date")
    if start > end:
        raise InputError("FAIL", "start_date must not be later than end_date")
    return {
        "original_request": original_request,
        "families": families,
        "kind": "explicit",
        "start": start,
        "end": end,
        "expression": None,
        "relative_kind": None,
        "count": None,
        "anchor": None,
    }


def _attempt_calendar(
    service: Any,
    start: date,
    end: date,
    query_ranges: list[dict[str, str]],
    purpose: str,
) -> CalendarAttempt:
    query_ranges.append(
        {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "purpose": purpose,
        }
    )
    request = TradeCalendarRange(exchange="CFFEX", start_date=start, end_date=end)
    try:
        coverage = service.coverage(request)
        ensure = None
        if not bool(getattr(coverage, "complete", False)):
            ensure = service.ensure(request)
        export = service.export(request)
    except Exception as exc:
        return CalendarAttempt(
            "unavailable",
            _calendar_failure(exc),
            start,
            end,
            query_ranges,
            (),
            None,
            None,
            None,
            None,
            None,
        )
    try:
        payload = _calendar_export_payload(export)
        data = _json_bytes(payload)
    except Exception as exc:
        return CalendarAttempt(
            "unverified",
            f"Calendar export is not usable: {type(exc).__name__}",
            start,
            end,
            query_ranges,
            (),
            getattr(export, "coverage", None),
            ensure,
            None,
            None,
            None,
        )
    digest = _sha256(data)
    scope = getattr(export, "scope", None)
    window = getattr(export, "window", None)
    export_coverage = getattr(export, "coverage", None)
    if (
        getattr(export, "dataset", None) != "tushare_trade_calendar"
        or getattr(export, "view", None) != "calendar"
        or getattr(export, "export_schema_version", None) != 1
        or getattr(scope, "exchange", None) != "CFFEX"
    ):
        return CalendarAttempt(
            "unverified",
            "Calendar export identity, view, exchange or schema version is unexpected",
            start,
            end,
            query_ranges,
            tuple(getattr(export, "records", ())),
            export_coverage,
            ensure,
            payload,
            data,
            digest,
        )
    window_start = getattr(window, "start_date", None)
    window_end = getattr(window, "end_date", None)
    if window_start is None or window_end is None:
        return CalendarAttempt(
            "unverified",
            "Calendar export has no usable window",
            start,
            end,
            query_ranges,
            tuple(getattr(export, "records", ())),
            export_coverage,
            ensure,
            payload,
            data,
            digest,
        )
    if window_start > start or window_end < end:
        return CalendarAttempt(
            "unverified",
            "Calendar export window does not cover the exact query range",
            start,
            end,
            query_ranges,
            tuple(getattr(export, "records", ())),
            export_coverage,
            ensure,
            payload,
            data,
            digest,
        )
    if not bool(getattr(export_coverage, "complete", False)):
        return CalendarAttempt(
            "unverified",
            "Calendar coverage is incomplete for the exact query range",
            start,
            end,
            query_ranges,
            tuple(getattr(export, "records", ())),
            export_coverage,
            ensure,
            payload,
            data,
            digest,
        )
    return CalendarAttempt(
        "verified",
        None,
        start,
        end,
        query_ranges,
        tuple(export.records),
        export_coverage,
        ensure,
        payload,
        data,
        digest,
    )


def _expand_range(start: date, end: date) -> date:
    span = (end - start).days + 1
    return end - timedelta(days=min(span * 2, 3660) - 1)


def _resolve_relative_window(
    relative_kind: str,
    count: int | None,
    anchor_override: date | None,
    execution_date: date,
    service: Any,
) -> tuple[str, str, date | None, date | None, date | None, str, CalendarAttempt]:
    search_end = (
        anchor_override
        if anchor_override is not None
        else execution_date - timedelta(days=1)
    )
    if search_end < date.min + timedelta(days=1):
        attempt = CalendarAttempt(
            "unavailable",
            "No natural day is available before the execution date for an anchor",
            None,
            None,
            [],
            (),
            None,
            None,
            None,
            None,
            None,
        )
        return "BLOCKED", attempt.reason or "anchor is unavailable", None, None, None, "", attempt
    initial_span = 30 if relative_kind == "two_weeks" else max(30, (count or 1) * 3)
    search_start = search_end - timedelta(days=initial_span - 1)
    query_ranges: list[dict[str, str]] = []
    while True:
        attempt = _attempt_calendar(
            service, search_start, search_end, query_ranges, "relative_resolution"
        )
        if attempt.status != "verified":
            reason = f"CFFEX calendar cannot prove the relative anchor: {attempt.reason}"
            return "BLOCKED", reason, None, None, None, "", attempt
        open_dates = sorted(
            record.cal_date for record in attempt.records if record.is_open == 1
        )
        if anchor_override is not None:
            if anchor_override > execution_date:
                reason = "anchor_date must not be later than the execution date"
                return "FAIL", reason, None, None, None, "", attempt
            if anchor_override not in open_dates:
                reason = "anchor_date is not a CFFEX open date"
                return "FAIL", reason, None, None, None, "", attempt
            anchor = anchor_override
        elif open_dates:
            anchor = open_dates[-1]
        else:
            if (search_end - search_start).days + 1 >= 3660:
                reason = "Could not establish a CFFEX anchor within ten years"
                return "BLOCKED", reason, None, None, None, "", attempt
            search_start = _expand_range(search_start, search_end)
            continue
        if relative_kind == "two_weeks":
            start = anchor - timedelta(days=13)
            end = anchor
        else:
            eligible = [value for value in open_dates if value <= anchor]
            if len(eligible) < (count or 0):
                if (search_end - search_start).days + 1 >= 3660:
                    reason = "Could not establish the requested CFFEX sessions within ten years"
                    return "BLOCKED", reason, None, None, None, "", attempt
                search_start = _expand_range(search_start, search_end)
                continue
            start = eligible[-(count or 0)]
            end = anchor
        if start < search_start:
            if (search_end - search_start).days + 1 >= 3660:
                reason = "Could not cover the resolved window with the CFFEX calendar"
                return "BLOCKED", reason, None, None, None, "", attempt
            search_start = _expand_range(search_start, search_end)
            continue
        rule = (
            "user_supplied_anchor"
            if anchor_override is not None
            else "latest_cffex_open_date_strictly_before_execution_date"
        )
        return "PASS", "", start, end, anchor, rule, attempt


def _build_resolved_inputs(
    *,
    families: list[str],
    start: date,
    end: date,
    date_expression: str | None,
    kind: str,
    anchor: date | None,
    anchor_rule: str,
    execution_date: date,
    execution_instant_utc: str,
    execution_instant_shanghai: str,
    calendar: CalendarAttempt,
    authorization_reference: str | None,
) -> dict[str, Any]:
    open_dates = [
        record.cal_date
        for record in calendar.records
        if record.is_open == 1 and start <= record.cal_date <= end
    ]
    return {
        "futures_families": families,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "resolution": {
            "kind": kind,
            "original_date_expression": date_expression,
            "anchor_date": _iso(anchor),
            "anchor_rule": anchor_rule,
            "execution_date": execution_date.isoformat(),
            "execution_instant_utc": execution_instant_utc,
            "execution_instant_asia_shanghai": execution_instant_shanghai,
            "calendar_used_for_resolution": kind == "relative",
            "calendar": {
                "source": CALENDAR_ID,
                "exchange": "CFFEX",
                "status": calendar.status,
                "reason": calendar.reason,
                "query_ranges": calendar.query_ranges,
                "coverage": _coverage_payload(calendar.coverage),
                "ensure": _ensure_payload(calendar.ensure),
                "export_sha256": calendar.export_sha256,
                "export_record_count": len(calendar.records),
                "requested_window_open_trade_date_count": len(open_dates),
            },
            "authorization_reference": authorization_reference,
            "execution_intent": (
                "Acquire the public CFFEX annualized basis history for the resolved "
                "families and inclusive date window, then deliver and verify the three "
                "Run-scoped output files."
            ),
        },
    }


def _attempted_inputs(
    params: Any,
    *,
    status: str,
    reason: str,
    execution_date: date,
    execution_instant_utc: str,
    execution_instant_shanghai: str,
    authorization_reference: str | None,
) -> dict[str, Any]:
    safe_params = json.loads(_json_bytes(params))
    return {
        "attempted_inputs": safe_params,
        "resolution": {
            "status": status,
            "reason": reason,
            "execution_date": execution_date.isoformat(),
            "execution_instant_utc": execution_instant_utc,
            "execution_instant_asia_shanghai": execution_instant_shanghai,
            "authorization_reference": authorization_reference,
        },
    }


def _resolve(
    params: Any,
    *,
    authorization_reference: str | None,
    calendar_service: Any,
    execution_date: date,
    instant: datetime,
) -> Resolution:
    if not isinstance(params, Mapping):
        raise ValueError("input must be a JSON object")
    original_request = params.get("original_request")
    if not isinstance(original_request, str) or not original_request.strip():
        raise ValueError("original_request must be a nonempty string")
    utc_text = instant.astimezone(UTC).isoformat()
    shanghai_text = instant.astimezone(SHANGHAI).isoformat()
    not_accessed = CalendarAttempt(
        "not_accessed",
        "No execution authorization; the CFFEX calendar was not accessed.",
        None,
        None,
        [],
        (),
        None,
        None,
        None,
        None,
        None,
    )
    try:
        parsed = _parse_params(params)
    except InputError as exc:
        return Resolution(
            gate_status=exc.status,
            reason=exc.reason,
            original_request=original_request,
            families=[],
            start_date=None,
            end_date=None,
            date_expression=None,
            kind="unresolved",
            anchor_date=None,
            anchor_rule="not_applicable",
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            calendar=not_accessed,
            resolved_inputs=_attempted_inputs(
                params,
                status=exc.status,
                reason=exc.reason,
                execution_date=execution_date,
                execution_instant_utc=utc_text,
                execution_instant_shanghai=shanghai_text,
                authorization_reference=authorization_reference,
            ),
        )

    families = parsed["families"]
    if (
        parsed["kind"] == "relative"
        and parsed["anchor"] is not None
        and parsed["anchor"] > execution_date
    ):
        reason = "anchor_date must not be later than the execution date"
        return Resolution(
            gate_status="FAIL",
            reason=reason,
            original_request=original_request,
            families=families,
            start_date=None,
            end_date=None,
            date_expression=parsed["expression"],
            kind="relative",
            anchor_date=parsed["anchor"],
            anchor_rule="user_supplied_anchor",
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            calendar=not_accessed,
            resolved_inputs=_attempted_inputs(
                params,
                status="FAIL",
                reason=reason,
                execution_date=execution_date,
                execution_instant_utc=utc_text,
                execution_instant_shanghai=shanghai_text,
                authorization_reference=authorization_reference,
            ),
        )
    if parsed["kind"] == "explicit":
        start = parsed["start"]
        end = parsed["end"]
        if end > execution_date:
            reason = "end_date must not be later than the execution date in Asia/Shanghai"
            return Resolution(
                gate_status="FAIL",
                reason=reason,
                original_request=original_request,
                families=families,
                start_date=start,
                end_date=end,
                date_expression=None,
                kind="explicit",
                anchor_date=None,
                anchor_rule="not_applicable",
                execution_date=execution_date,
                execution_instant_utc=utc_text,
                execution_instant_shanghai=shanghai_text,
                calendar=not_accessed,
                resolved_inputs=_attempted_inputs(
                    params,
                    status="FAIL",
                    reason=reason,
                    execution_date=execution_date,
                    execution_instant_utc=utc_text,
                    execution_instant_shanghai=shanghai_text,
                    authorization_reference=authorization_reference,
                ),
            )
        calendar = not_accessed
        if authorization_reference is not None:
            service = (
                calendar_service
                if calendar_service is not None
                else _default_calendar_service()
            )
            calendar = _attempt_calendar(
                service, start, end, [], "expected_sessions"
            )
        resolved_inputs = _build_resolved_inputs(
            families=families,
            start=start,
            end=end,
            date_expression=None,
            kind="explicit",
            anchor=None,
            anchor_rule="not_applicable",
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            calendar=calendar,
            authorization_reference=authorization_reference,
        )
        return Resolution(
            gate_status="PASS",
            reason="Explicit inputs were validated and frozen before acquisition.",
            original_request=original_request,
            families=families,
            start_date=start,
            end_date=end,
            date_expression=None,
            kind="explicit",
            anchor_date=None,
            anchor_rule="not_applicable",
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            calendar=calendar,
            resolved_inputs=resolved_inputs,
        )

    if authorization_reference is None:
        reason = (
            "Relative-date resolution requires separate execution authorization for "
            "CFFEX calendar access; no anchor can be established without it."
        )
        return Resolution(
            gate_status="BLOCKED",
            reason=reason,
            original_request=original_request,
            families=families,
            start_date=None,
            end_date=None,
            date_expression=parsed["expression"],
            kind="relative",
            anchor_date=None,
            anchor_rule="not_established",
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            calendar=not_accessed,
            resolved_inputs=_attempted_inputs(
                params,
                status="BLOCKED",
                reason=reason,
                execution_date=execution_date,
                execution_instant_utc=utc_text,
                execution_instant_shanghai=shanghai_text,
                authorization_reference=authorization_reference,
            ),
        )
    service = calendar_service if calendar_service is not None else _default_calendar_service()
    status, reason, start, end, anchor, anchor_rule, calendar = _resolve_relative_window(
        parsed["relative_kind"],
        parsed["count"],
        parsed["anchor"],
        execution_date,
        service,
    )
    if status != "PASS":
        attempted = _attempted_inputs(
            params,
            status=status,
            reason=reason,
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            authorization_reference=authorization_reference,
        )
        attempted["resolution"]["calendar"] = {
            "status": calendar.status,
            "reason": calendar.reason,
            "query_ranges": calendar.query_ranges,
            "coverage": _coverage_payload(calendar.coverage),
            "export_sha256": calendar.export_sha256,
        }
        return Resolution(
            gate_status=status,
            reason=reason,
            original_request=original_request,
            families=families,
            start_date=start,
            end_date=end,
            date_expression=parsed["expression"],
            kind="relative",
            anchor_date=anchor,
            anchor_rule=anchor_rule,
            execution_date=execution_date,
            execution_instant_utc=utc_text,
            execution_instant_shanghai=shanghai_text,
            calendar=calendar,
            resolved_inputs=attempted,
        )
    assert start is not None and end is not None
    resolved_inputs = _build_resolved_inputs(
        families=families,
        start=start,
        end=end,
        date_expression=parsed["expression"],
        kind="relative",
        anchor=anchor,
        anchor_rule=anchor_rule,
        execution_date=execution_date,
        execution_instant_utc=utc_text,
        execution_instant_shanghai=shanghai_text,
        calendar=calendar,
        authorization_reference=authorization_reference,
    )
    return Resolution(
        gate_status="PASS",
        reason="Relative expression was resolved against the published CFFEX calendar.",
        original_request=original_request,
        families=families,
        start_date=start,
        end_date=end,
        date_expression=parsed["expression"],
        kind="relative",
        anchor_date=anchor,
        anchor_rule=anchor_rule,
        execution_date=execution_date,
        execution_instant_utc=utc_text,
        execution_instant_shanghai=shanghai_text,
        calendar=calendar,
        resolved_inputs=resolved_inputs,
    )


def _default_calendar_service() -> Any:
    from data_lake.datasets.tushare_trade_calendar import create_service

    return create_service()


def _default_product_runner(
    request: CFFEXEquityIndexBasisHistoryRequest,
) -> CFFEXEquityIndexBasisHistoryResult:
    return run_cffex_equity_index_basis_history(request)


def _request_payload(request: CFFEXEquityIndexBasisHistoryRequest) -> dict[str, str]:
    return {
        "futures_family": request.futures_family,
        "start_trade_date": request.start_trade_date,
        "end_trade_date": request.end_trade_date,
    }


def _observation_payload(observation: CFFEXEquityIndexBasisObservation) -> dict[str, Any]:
    return {
        "trade_date": observation.trade_date,
        "futures_family": observation.futures_family,
        "underlying_code": observation.underlying_code,
        "contract_code": observation.contract_code,
        "contract_slot": observation.contract_slot,
        "delist_date": observation.delist_date,
        "days_to_delist": observation.days_to_delist,
        "annualization_days": observation.annualization_days,
        "underlying_close": float(observation.underlying_close),
        "futures_close": float(observation.futures_close),
        "basis_points": float(observation.basis_points),
        "basis_pct": float(observation.basis_pct),
        "annualized_basis_pct": float(observation.annualized_basis_pct),
    }


def _result_payload(result: CFFEXEquityIndexBasisHistoryResult) -> dict[str, Any]:
    return {
        "futures_family": result.futures_family,
        "start_trade_date": result.start_trade_date,
        "end_trade_date": result.end_trade_date,
        "family_listing_date": result.family_listing_date,
        "first_observation_date": result.first_observation_date,
        "last_observation_date": result.last_observation_date,
        "underlying_code": result.underlying_code,
        "source_identity": result.source_identity,
        "observations": [_observation_payload(item) for item in result.observations],
    }


def _valid_day(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def _valid_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _validate_result(
    family: str,
    request: CFFEXEquityIndexBasisHistoryRequest,
    result: Any,
) -> tuple[bool, str | None, str | None]:
    if getattr(result, "futures_family", None) != family:
        return False, "incomplete_panel", "public result family does not match the request"
    if getattr(result, "start_trade_date", None) != request.start_trade_date:
        return False, "incomplete_panel", "public result start date does not match the request"
    if getattr(result, "end_trade_date", None) != request.end_trade_date:
        return False, "incomplete_panel", "public result end date does not match the request"
    underlying = getattr(result, "underlying_code", None)
    if not isinstance(underlying, str) or not underlying:
        return False, "incomplete_panel", "public result has no underlying identity"
    listing = _valid_day(getattr(result, "family_listing_date", None))
    if listing is None:
        return False, "incomplete_panel", "public result has no valid family listing date"
    source = getattr(result, "source_identity", None)
    if not isinstance(source, str) or not source:
        return False, "incomplete_panel", "public result has no source identity"
    observations = getattr(result, "observations", None)
    if not isinstance(observations, Sequence) or isinstance(observations, str | bytes):
        return False, "incomplete_panel", "public result observations are not a sequence"
    if not observations:
        return False, "incomplete_panel", "public result has no observations"
    dates: list[date] = []
    for observation in observations:
        if getattr(observation, "futures_family", None) != family:
            return False, "incomplete_panel", "an observation has the wrong family"
        if getattr(observation, "underlying_code", None) != underlying:
            return False, "incomplete_panel", "an observation has the wrong underlying"
        trade_day = _valid_day(getattr(observation, "trade_date", None))
        if trade_day is None:
            return False, "incomplete_panel", "an observation has an invalid trade_date"
        if _valid_day(getattr(observation, "delist_date", None)) is None:
            return False, "incomplete_panel", "an observation has an invalid delist_date"
        contract_code = getattr(observation, "contract_code", None)
        slot = getattr(observation, "contract_slot", None)
        if not isinstance(contract_code, str) or not contract_code:
            return False, "incomplete_panel", "an observation has no contract_code"
        if not isinstance(slot, str) or not slot:
            return False, "incomplete_panel", "an observation has no contract_slot"
        days = getattr(observation, "days_to_delist", None)
        if type(days) is not int or days < 0:
            return False, "incomplete_panel", "an observation has an invalid days_to_delist"
        annualization = getattr(observation, "annualization_days", None)
        if type(annualization) is not int or annualization < 1:
            return False, "incomplete_panel", "an observation has invalid annualization_days"
        for field in ("underlying_close", "futures_close", "basis_points", "basis_pct",
                      "annualized_basis_pct"):
            if _valid_number(getattr(observation, field, None)) is None:
                return False, "incomplete_panel", f"an observation has an invalid {field}"
        if _valid_number(getattr(observation, "underlying_close", None)) == 0:
            return False, "incomplete_panel", "an observation has a zero underlying_close"
        dates.append(trade_day)
    if getattr(result, "first_observation_date", None) != min(dates).isoformat():
        return False, "incomplete_panel", "first_observation_date is not the first observation"
    if getattr(result, "last_observation_date", None) != max(dates).isoformat():
        return False, "incomplete_panel", "last_observation_date is not the last observation"
    return True, None, None


def _acquire_family(
    family: str,
    request: CFFEXEquityIndexBasisHistoryRequest,
    runner: Callable[[CFFEXEquityIndexBasisHistoryRequest], CFFEXEquityIndexBasisHistoryResult],
) -> FamilyAcquisition:
    try:
        result = runner(request)
    except CFFEXEquityIndexBasisHistoryError as exc:
        return FamilyAcquisition(
            family, request, None, "failed", exc.reason, _product_failure(exc), ()
        )
    except Exception as exc:
        return FamilyAcquisition(
            family, request, None, "failed", "source_failure", _product_failure(exc), ()
        )
    valid, reason, message = _validate_result(family, request, result)
    if not valid:
        return FamilyAcquisition(
            family, request, result, "failed", reason, message, ()
        )
    return FamilyAcquisition(
        family,
        request,
        result,
        "success",
        None,
        None,
        tuple(result.observations),
    )


def _coverage_for(
    acquisition: FamilyAcquisition,
    calendar: CalendarAttempt,
    start: date,
    end: date,
) -> FamilyCoverage:
    if acquisition.status != "success" or acquisition.result is None:
        return FamilyCoverage(
            acquisition.family,
            "not_applicable",
            "Family acquisition failed; no coverage claim is made.",
            [],
            [],
            [],
            None,
            None,
        )
    listing = _valid_day(acquisition.result.family_listing_date)
    assert listing is not None
    effective_start = max(start, listing)
    if effective_start > end:
        return FamilyCoverage(
            acquisition.family,
            "not_applicable",
            "The effective window is empty after the family listing date.",
            [],
            [],
            [],
            None,
            None,
        )
    observed = sorted(
        {
            day
            for item in acquisition.observations
            if (day := _valid_day(item.trade_date)) is not None
        }
    )
    if calendar.status != "verified":
        return FamilyCoverage(
            acquisition.family,
            "unverified",
            calendar.reason or "Expected-session coverage is unverified.",
            [],
            [],
            [],
            None,
            None,
        )
    expected = sorted(
        {
            record.cal_date
            for record in calendar.records
            if record.is_open == 1 and effective_start <= record.cal_date <= end
        }
    )
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    latest_expected = expected[-1] if expected else None
    latest_observed = (
        latest_expected in set(observed) if latest_expected is not None else None
    )
    if not missing and not unexpected:
        return FamilyCoverage(
            acquisition.family,
            "verified_complete",
            None,
            expected,
            [],
            [],
            latest_expected,
            latest_observed,
        )
    pieces = []
    if missing:
        pieces.append(f"{len(missing)} expected CFFEX session(s) are missing")
    if unexpected:
        pieces.append(f"{len(unexpected)} unexpected observed date(s) exist")
    if latest_observed is False:
        pieces.append("the latest expected session was not observed")
    return FamilyCoverage(
        acquisition.family,
        "verified_partial",
        "; ".join(pieces) + ".",
        expected,
        missing,
        unexpected,
        latest_expected,
        latest_observed,
    )


def _overall_coverage(acquisitions: list[FamilyAcquisition],
                      coverages: list[FamilyCoverage]) -> str:
    if not any(item.status == "success" for item in acquisitions):
        return "not_applicable"
    if any(item.status == "failed" for item in acquisitions):
        return "mixed"
    statuses = [item.status for item in coverages]
    if all(status == "verified_complete" for status in statuses):
        return "verified_complete"
    if (
        all(status in {"verified_complete", "verified_partial"} for status in statuses)
        and any(status == "verified_partial" for status in statuses)
    ):
        return "verified_partial"
    if all(status == "unverified" for status in statuses):
        return "unverified"
    return "mixed"


def _overall_status(acquisitions: list[FamilyAcquisition],
                    coverages: list[FamilyCoverage]) -> str:
    if not any(item.status == "success" for item in acquisitions):
        return "failed"
    if all(item.status == "success" for item in acquisitions) and all(
        item.status == "verified_complete" for item in coverages
    ):
        return "complete"
    return "partial"


def _acquisition_payload(
    *,
    task: dict[str, Any],
    manifest: dict[str, Any],
    acquisitions: list[FamilyAcquisition],
    coverages: list[FamilyCoverage],
) -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    for acquisition, coverage in zip(acquisitions, coverages, strict=True):
        families.append(
            {
                "futures_family": acquisition.family,
                "invocations": 1,
                "status": acquisition.status,
                "request": (
                    _request_payload(acquisition.request)
                    if acquisition.request is not None
                    else None
                ),
                "result": (
                    _result_payload(acquisition.result)
                    if acquisition.status == "success" and acquisition.result is not None
                    else None
                ),
                "error": (
                    {
                        "reason": acquisition.error_reason,
                        "message": acquisition.error_message,
                    }
                    if acquisition.status == "failed"
                    else None
                ),
                "coverage": {
                    "status": coverage.status,
                    "reason": coverage.reason,
                    "expected_trade_date_count": len(coverage.expected),
                    "missing_expected_trade_dates": [
                        value.isoformat() for value in coverage.missing
                    ],
                    "unexpected_observed_trade_dates": [
                        value.isoformat() for value in coverage.unexpected
                    ],
                    "latest_expected_trade_date": _iso(coverage.latest_expected),
                    "latest_expected_session_observed": coverage.latest_observed,
                },
            }
        )
    return {
        "schema_version": 1,
        "task_id": task["task_id"],
        "task_version": task["version"],
        "task_sha256": manifest["task_sha256"],
        "run_id": manifest["run_id"],
        "product": PRODUCT_ID,
        "product_function": "run_cffex_equity_index_basis_history",
        "calendar_source": CALENDAR_ID,
        "families": families,
    }


def _family_payload(
    acquisition: FamilyAcquisition,
    coverage: FamilyCoverage,
    start: date,
    end: date,
) -> dict[str, Any]:
    result = acquisition.result
    return {
        "futures_family": acquisition.family,
        "underlying_code": (
            result.underlying_code if result is not None else FAMILY_UNDERLYING[acquisition.family]
        ),
        "status": acquisition.status,
        "product_request": (
            _request_payload(acquisition.request)
            if acquisition.request is not None
            else {
                "futures_family": acquisition.family,
                "start_trade_date": start.isoformat(),
                "end_trade_date": end.isoformat(),
            }
        ),
        "product_error_reason": acquisition.error_reason,
        "product_error_message": acquisition.error_message,
        "source_identity": result.source_identity if result is not None else None,
        "family_listing_date": result.family_listing_date if result is not None else None,
        "first_observation_date": (
            result.first_observation_date if result is not None else None
        ),
        "last_observation_date": (
            result.last_observation_date if result is not None else None
        ),
        "observation_count": len(acquisition.observations),
        "observed_trade_date_count": len(
            {item.trade_date for item in acquisition.observations}
        ),
        "expected_trade_date_count": (
            len(coverage.expected)
            if coverage.status in {"verified_complete", "verified_partial"}
            else 0
        ),
        "missing_expected_trade_dates": [
            value.isoformat() for value in coverage.missing
        ],
        "unexpected_observed_trade_dates": [
            value.isoformat() for value in coverage.unexpected
        ],
        "latest_expected_trade_date": _iso(coverage.latest_expected),
        "latest_expected_session_observed": coverage.latest_observed,
        "coverage_status": coverage.status,
        "coverage_reason": coverage.reason,
    }


def _failures(acquisitions: list[FamilyAcquisition],
              start: date, end: date) -> list[dict[str, str]]:
    failures = []
    for acquisition in acquisitions:
        if acquisition.status == "failed":
            failures.append(
                {
                    "stage": "acquisition",
                    "futures_family": acquisition.family,
                    "reason": acquisition.error_reason or "incomplete_panel",
                    "message": acquisition.error_message or "family acquisition failed",
                    "scope": (
                        f"family {acquisition.family} requested window "
                        f"{start.isoformat()}..{end.isoformat()}"
                    ),
                }
            )
    return failures


def _unfinished_scope(
    acquisitions: list[FamilyAcquisition],
    coverages: list[FamilyCoverage],
    overall: str,
) -> list[str]:
    scope: list[str] = []
    for acquisition in acquisitions:
        if acquisition.status == "failed":
            scope.append(
                f"{acquisition.family}: acquisition failed "
                f"({acquisition.error_reason}); no market values were delivered for it."
            )
    for coverage in coverages:
        if coverage.status == "verified_partial":
            scope.append(
                f"{coverage.family}: at least one expected CFFEX session is missing; "
                "the full date list is in result.json."
            )
            if coverage.missing:
                scope.append(
                    f"{coverage.family}: missing expected sessions "
                    f"{len(coverage.missing)}; first {coverage.missing[0].isoformat()}, "
                    f"last {coverage.missing[-1].isoformat()}."
                )
            if coverage.unexpected:
                scope.append(
                    f"{coverage.family}: unexpected observed dates "
                    f"{len(coverage.unexpected)}; first "
                    f"{coverage.unexpected[0].isoformat()}, last "
                    f"{coverage.unexpected[-1].isoformat()}; this is a contract "
                    "inconsistency."
                )
            if coverage.latest_observed is False and coverage.latest_expected is not None:
                scope.append(
                    f"{coverage.family}: recent gap; latest expected CFFEX session "
                    f"{coverage.latest_expected.isoformat()} was not observed."
                )
        elif coverage.status == "unverified":
            scope.append(
                f"{coverage.family}: expected-session coverage is unverified; "
                f"{coverage.reason}"
            )
        elif coverage.status == "not_applicable":
            scope.append(
                f"{coverage.family}: no applicable coverage window; "
                f"{coverage.reason}"
            )
    if overall != "complete" and not scope:
        scope.append("The run is not complete; see coverage status and failures.")
    return scope


def _limitations(
    acquisitions: list[FamilyAcquisition],
    coverages: list[FamilyCoverage],
    overall: str,
) -> list[str]:
    limitations = list(STATIC_LIMITATIONS)
    if any(item.status == "failed" for item in acquisitions):
        limitations.append(
            "One or more requested families failed; successful family data is preserved "
            "but the Run is not a complete result."
        )
    if any(item.status == "unverified" for item in coverages):
        limitations.append(
            "Expected-session coverage is unverified for at least one family; no "
            "completeness claim is made for this Run."
        )
    if any(item.status == "verified_partial" for item in coverages):
        limitations.append(
            "At least one family is verified_partial; the delivered panel is incomplete."
        )
    if overall != "complete":
        limitations.append("The run is partial or failed and must not be read as complete.")
    return limitations


def _expected_sessions(
    calendar: CalendarAttempt, start: date, end: date
) -> dict[str, Any]:
    if calendar.status == "verified":
        open_dates = sorted(
            {
                record.cal_date
                for record in calendar.records
                if record.is_open == 1 and start <= record.cal_date <= end
            }
        )
        return {
            "status": "verified",
            "source": CALENDAR_ID,
            "trade_date_count": len(open_dates),
            "first_trade_date": open_dates[0].isoformat() if open_dates else None,
            "last_trade_date": open_dates[-1].isoformat() if open_dates else None,
            "unverified_reason": None,
        }
    return {
        "status": "unverified",
        "source": CALENDAR_ID,
        "trade_date_count": 0,
        "first_trade_date": None,
        "last_trade_date": None,
        "unverified_reason": calendar.reason or "CFFEX calendar coverage is unavailable.",
    }


def _csv_row(observation: CFFEXEquityIndexBasisObservation) -> tuple[str, ...]:
    return (
        observation.trade_date,
        observation.futures_family,
        observation.underlying_code,
        observation.contract_code,
        observation.contract_slot,
        observation.delist_date,
        str(observation.days_to_delist),
        _decimal(observation.underlying_close),
        _decimal(observation.futures_close),
        _decimal(observation.basis_pct),
        _decimal(observation.annualized_basis_pct),
    )


def _csv_sort_key(row: tuple[str, ...]) -> tuple[str, int, int, str]:
    return (
        row[0],
        FAMILY_ORDER.get(row[1], 99),
        SLOT_ORDER.get(row[4], 99),
        row[5],
    )


def _csv_bytes(rows: list[tuple[str, ...]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _report(
    *,
    result: dict[str, Any],
    acquisitions: list[FamilyAcquisition],
    coverages: list[FamilyCoverage],
) -> str:
    lines: list[str] = ["# Equity Index Futures Basis Monitor", ""]
    original = str(result["original_request"]).replace("\n", " ")
    lines.extend([f"> {original}", ""])
    lines.append("## Query and actual range")
    lines.append("")
    lines.append(f"- Resolved families: {', '.join(result['resolved_inputs']['futures_families'])}")
    lines.append(
        f"- Requested window: {result['requested_window']['start_date']} .. "
        f"{result['requested_window']['end_date']} (inclusive)"
    )
    resolution = result["resolved_inputs"]["resolution"]
    lines.append(
        f"- Resolution kind: {resolution['kind']}; original expression: "
        f"{resolution['original_date_expression'] or 'not applicable'}"
    )
    if resolution["anchor_date"] is not None:
        lines.append(
            f"- Anchor: {resolution['anchor_date']} ({resolution['anchor_rule']})"
        )
    lines.append(
        f"- Execution date (Asia/Shanghai): {resolution['execution_date']}; "
        f"authorization: {resolution['authorization_reference'] or 'none'}"
    )
    calendar = resolution["calendar"]
    query_ranges = "; ".join(
        f"{item['start_date']}..{item['end_date']}"
        for item in calendar["query_ranges"]
    )
    lines.append(
        f"- CFFEX calendar: {calendar['status']}; query ranges: "
        f"{query_ranges or 'none'}"
    )
    lines.append("")
    lines.append("| Family | Status | First observation | Last observation |")
    lines.append("| --- | --- | --- | --- |")
    for family in result["families"]:
        lines.append(
            f"| {family['futures_family']} | {family['status']} | "
            f"{family['first_observation_date'] or 'not available'} | "
            f"{family['last_observation_date'] or 'not available'} |"
        )
    lines.append("")

    lines.append("## Latest session by family")
    lines.append("")
    latest_dates: dict[str, str] = {}
    for acquisition in acquisitions:
        family = acquisition.family
        if acquisition.status != "success" or acquisition.result is None:
            lines.append(f"### {family}")
            lines.append("")
            lines.append(
                f"Acquisition failed ({acquisition.error_reason}); no values are reported."
            )
            lines.append("")
            continue
        by_date: dict[str, list[CFFEXEquityIndexBasisObservation]] = {}
        for observation in acquisition.observations:
            by_date.setdefault(observation.trade_date, []).append(observation)
        latest = max(by_date)
        latest_dates[family] = latest
        lines.append(f"### {family} - latest observation {latest}")
        lines.append("")
        lines.append("| Slot | Contract | days_to_delist | annualized_basis_pct |")
        lines.append("| --- | --- | --- | --- |")
        slots: dict[str, list[CFFEXEquityIndexBasisObservation]] = {}
        for observation in by_date[latest]:
            slots.setdefault(observation.contract_slot, []).append(observation)
        for slot in SLOTS:
            rows = slots.get(slot, [])
            if len(rows) == 1:
                observation = rows[0]
                lines.append(
                    f"| {slot} | {observation.contract_code} | "
                    f"{observation.days_to_delist} | "
                    f"{_decimal(observation.annualized_basis_pct)} |"
                )
            else:
                lines.append(f"| {slot} | inconsistent ({len(rows)} rows) | - | - |")
        lines.append("")
    if len(set(latest_dates.values())) > 1:
        lines.append(
            "Latest observation dates differ across families: "
            + ", ".join(f"{family}={day}" for family, day in latest_dates.items())
            + ". These are different sessions and must not be read as one trading day."
        )
        lines.append("")
    elif latest_dates:
        lines.append(
            "All successful families share the latest observation date "
            f"{next(iter(latest_dates.values()))}."
        )
        lines.append("")

    lines.append("## Coverage and failures")
    lines.append("")
    expected = result["expected_sessions"]
    lines.append(f"- Expected-session source: {expected['source']}")
    lines.append(f"- Expected-session status: {expected['status']}")
    lines.append(
        f"- Requested-window expected sessions: {expected['trade_date_count']} "
        f"({expected['first_trade_date'] or 'none'} .. {expected['last_trade_date'] or 'none'})"
    )
    if expected["unverified_reason"]:
        lines.append(f"- Unverified reason: {expected['unverified_reason']}")
    observed_counts = {
        item["futures_family"]: item["observed_trade_date_count"]
        for item in result["families"]
    }
    for coverage in coverages:
        lines.append(
            f"- {coverage.family} coverage is {coverage.status}; expected "
            f"{len(coverage.expected)}, observed {observed_counts.get(coverage.family, 0)}, "
            f"missing {len(coverage.missing)}, unexpected {len(coverage.unexpected)}; "
            f"latest expected {coverage.latest_expected or 'none'}, observed: "
            f"{coverage.latest_observed if coverage.latest_observed is not None else 'unknown'}."
        )
        if coverage.missing:
            lines.append(
                f"  - Missing first/last: {coverage.missing[0]} .. {coverage.missing[-1]}; "
                "the full list is in result.json."
            )
        if coverage.unexpected:
            lines.append(
                f"  - Unexpected first/last: {coverage.unexpected[0]} .. "
                f"{coverage.unexpected[-1]}; the full list is in result.json."
            )
    if any(item.latest_observed is False for item in coverages):
        lines.append("- Recent gap: yes; the latest expected session was not observed.")
    elif coverages and all(item.latest_observed is True for item in coverages):
        lines.append("- Recent gap: no.")
    else:
        lines.append("- Recent gap: unknown; coverage is unverified or not applicable.")
    if result["failures"]:
        for failure in result["failures"]:
            lines.append(
                f"- {failure['futures_family']} failed: {failure['reason']} - "
                f"{failure['message']}"
            )
    else:
        lines.append("- Failed families: none.")
    lines.append("")
    lines.append(f"Overall status: {result['overall_status']}")
    lines.append(f"Coverage status: {result['coverage_status']}")
    lines.append("")

    lines.append("## Source, formula and units")
    lines.append("")
    identities = sorted(
        {
            acquisition.result.source_identity
            for acquisition in acquisitions
            if acquisition.result is not None
        }
    )
    lines.append(
        "Source identity: " + (", ".join(f"`{item}`" for item in identities) or "not available")
    )
    lines.append("")
    lines.append("Inherited from the shared CFFEX basis authority:")
    lines.append("")
    lines.append("```text")
    lines.append("basis_pct = (futures_close / underlying_close - 1) * 100")
    lines.append("annualized_basis_pct = basis_pct * 365 / max(days_to_delist, 1)")
    lines.append("```")
    lines.append("")
    lines.append(
        "Units are percentage points. Sign convention: negative = discount (贴水), "
        "positive = premium (升水). This is not an executable arbitrage yield or a "
        "rolling-hold return."
    )
    lines.append("")

    lines.append("## Near-expiry sensitivity")
    lines.append("")
    lines.append(
        "`days_to_delist` is calendar days and `annualization_days = "
        "max(days_to_delist, 1)`. Annualized values near delivery are highly sensitive "
        "to that denominator and are not smoothed or capped."
    )
    lines.append("")

    lines.append("## Limitations")
    lines.append("")
    for limitation in result["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _artifact_reference(registration: dict[str, Any]) -> dict[str, Any]:
    payload = registration["payload"]
    return {
        "artifact_id": payload["artifact_id"],
        "label": payload["label"],
        "sha256": payload["sha256"],
        "stored_path": payload["stored_path"],
        "size_bytes": payload["size_bytes"],
    }


def _save_bytes(
    store: Any,
    run_id: str,
    directory: Path,
    name: str,
    data: bytes,
    label: str,
) -> dict[str, Any]:
    path = directory / name
    path.write_bytes(data)
    return store.artifact(run_id, {"label": label, "path": str(path)})


def _register_calendar(
    store: Any,
    run_id: str,
    directory: Path,
    calendar: CalendarAttempt,
) -> dict[str, Any] | None:
    if calendar.export_bytes is None:
        return None
    return _save_bytes(
        store,
        run_id,
        directory,
        "calendar_export.json",
        calendar.export_bytes,
        "CFFEX calendar export",
    )


def _resolution_payload(
    *,
    task: dict[str, Any],
    manifest: dict[str, Any],
    resolution: Resolution,
    calendar_registration: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": task["task_id"],
        "task_version": task["version"],
        "task_sha256": manifest["task_sha256"],
        "run_id": manifest["run_id"],
        "original_request": resolution.original_request,
        "resolved_inputs": resolution.resolved_inputs,
        "gate": {
            "gate_id": "input_resolution",
            "status": resolution.gate_status,
            "reason": resolution.reason,
        },
        "calendar_evidence": (
            _artifact_reference(calendar_registration)
            if calendar_registration is not None
            else None
        ),
    }


def _read_artifact(store: Any, run_id: str, registration: dict[str, Any]) -> bytes:
    payload = registration["payload"]
    path = store.root / run_id / payload["stored_path"]
    data = path.read_bytes()
    if len(data) != payload["size_bytes"] or _sha256(data) != payload["sha256"]:
        raise ValueError("registered artifact digest mismatch")
    return data


def _verification(
    *,
    store: Any,
    run_id: str,
    manifest: dict[str, Any],
    task: dict[str, Any],
    resolution: Resolution,
    resolution_registration: dict[str, Any],
    acquisitions: list[FamilyAcquisition],
    coverages: list[FamilyCoverage],
    result: dict[str, Any],
    result_registration: dict[str, Any],
    csv_registration: dict[str, Any],
    report_registration: dict[str, Any],
    acquisition_registration: dict[str, Any],
    calendar_registration: dict[str, Any] | None,
    acquisition_gate_status: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, details: Any | None = None) -> None:
        checks.append(
            {"check": name, "status": "pass" if passed else "fail", "details": details}
        )

    state = store.read(run_id)
    add("run_readable", True, {"record_count": len(state["records"])})
    artifact_payloads = {
        item["payload"]["artifact_id"]: item["payload"] for item in state["artifacts"]
    }
    for label, registration in (
        ("resolution", resolution_registration),
        ("calendar", calendar_registration),
        ("acquisition", acquisition_registration),
        ("basis_daily.csv", csv_registration),
        ("result.json", result_registration),
        ("REPORT.md", report_registration),
    ):
        if registration is None:
            continue
        payload = registration["payload"]
        stored = store.root / run_id / payload["stored_path"]
        data = stored.read_bytes()
        add(
            f"artifact_digest:{label}",
            (
                payload["artifact_id"] in artifact_payloads
                and len(data) == payload["size_bytes"]
                and _sha256(data) == payload["sha256"]
            ),
            {"artifact_id": payload["artifact_id"], "sha256": payload["sha256"]},
        )

    csv_data = _read_artifact(store, run_id, csv_registration)
    rows = list(csv.reader(io.StringIO(csv_data.decode("utf-8"))))
    header = rows[0] if rows else []
    data_rows = [tuple(row) for row in rows[1:]]
    add("csv_header", header == list(CSV_COLUMNS), {"header": header})

    expected_rows: list[tuple[str, ...]] = []
    for acquisition in acquisitions:
        if acquisition.status == "success":
            expected_rows.extend(_csv_row(item) for item in acquisition.observations)
    expected_rows.sort(key=_csv_sort_key)
    add(
        "csv_row_count",
        len(data_rows) == len(expected_rows),
        {"csv": len(data_rows), "acquisition": len(expected_rows)},
    )
    add(
        "csv_rows_match_acquisition",
        Counter(data_rows) == Counter(expected_rows),
        {"csv": len(data_rows), "acquisition": len(expected_rows)},
    )
    add("csv_deterministic_order", data_rows == expected_rows, {})

    slot_issues: list[str] = []
    for acquisition in acquisitions:
        if acquisition.status != "success":
            continue
        by_date: dict[str, list[CFFEXEquityIndexBasisObservation]] = {}
        for observation in acquisition.observations:
            by_date.setdefault(observation.trade_date, []).append(observation)
        for trade_date, observations in by_date.items():
            counts = Counter(item.contract_slot for item in observations)
            if any(counts.get(slot, 0) != 1 for slot in SLOTS) or set(counts) != set(SLOTS):
                slot_issues.append(
                    f"{acquisition.family} {trade_date}: "
                    + ", ".join(f"{slot}={counts.get(slot, 0)}" for slot in SLOTS)
                )
    add("panel_slot_completeness", not slot_issues, {"issues": slot_issues[:20]})

    formula_issues: list[str] = []
    for acquisition in acquisitions:
        for observation in acquisition.observations:
            if observation.annualization_days != max(observation.days_to_delist, 1):
                formula_issues.append(
                    f"{acquisition.family} {observation.trade_date} "
                    f"{observation.contract_code}: annualization_days"
                )
            if observation.delist_date < observation.trade_date:
                formula_issues.append(
                    f"{acquisition.family} {observation.trade_date} "
                    f"{observation.contract_code}: delist_date before trade_date"
                )
    add("observation_internal_consistency", not formula_issues, {"issues": formula_issues[:20]})

    family_by_name = {item["futures_family"]: item for item in result["families"]}
    family_issues: list[str] = []
    for acquisition, coverage in zip(acquisitions, coverages, strict=True):
        item = family_by_name.get(acquisition.family)
        if item is None:
            family_issues.append(f"{acquisition.family}: absent from result.json")
            continue
        if item["status"] != acquisition.status:
            family_issues.append(f"{acquisition.family}: status mismatch")
        if item["product_request"] != (
            _request_payload(acquisition.request) if acquisition.request is not None else None
        ):
            family_issues.append(f"{acquisition.family}: product_request mismatch")
        if acquisition.status == "success":
            assert acquisition.result is not None
            if item["source_identity"] != acquisition.result.source_identity:
                family_issues.append(f"{acquisition.family}: source_identity mismatch")
            if item["first_observation_date"] != acquisition.result.first_observation_date:
                family_issues.append(f"{acquisition.family}: first date mismatch")
            if item["last_observation_date"] != acquisition.result.last_observation_date:
                family_issues.append(f"{acquisition.family}: last date mismatch")
            if item["observation_count"] != len(acquisition.observations):
                family_issues.append(f"{acquisition.family}: observation_count mismatch")
            if item["observed_trade_date_count"] != len(
                {obs.trade_date for obs in acquisition.observations}
            ):
                family_issues.append(f"{acquisition.family}: observed date count mismatch")
            if item["missing_expected_trade_dates"] != [
                value.isoformat() for value in coverage.missing
            ]:
                family_issues.append(f"{acquisition.family}: missing dates mismatch")
            if item["unexpected_observed_trade_dates"] != [
                value.isoformat() for value in coverage.unexpected
            ]:
                family_issues.append(f"{acquisition.family}: unexpected dates mismatch")
            if item["coverage_status"] != coverage.status:
                family_issues.append(f"{acquisition.family}: coverage status mismatch")
            expected_count = (
                len(coverage.expected)
                if coverage.status in {"verified_complete", "verified_partial"}
                else 0
            )
            if item["expected_trade_date_count"] != expected_count:
                family_issues.append(f"{acquisition.family}: expected count mismatch")
            if item["latest_expected_trade_date"] != _iso(coverage.latest_expected):
                family_issues.append(f"{acquisition.family}: latest expected mismatch")
            if item["latest_expected_session_observed"] != coverage.latest_observed:
                family_issues.append(f"{acquisition.family}: latest observed mismatch")
    add("result_family_consistency", not family_issues, {"issues": family_issues[:20]})

    manifest_issues = []
    if result["schema_version"] != 1:
        manifest_issues.append("schema_version")
    if result["original_request"] != manifest["original_request"]:
        manifest_issues.append("original_request")
    if result["resolved_inputs"] != manifest["resolved_inputs"]:
        manifest_issues.append("resolved_inputs")
    if result["task_id"] != task["task_id"] or result["task_version"] != task["version"]:
        manifest_issues.append("task identity")
    if result["task_sha256"] != manifest["task_sha256"]:
        manifest_issues.append("task_sha256")
    if result["run_id"] != run_id:
        manifest_issues.append("run_id")
    add("result_manifest_consistency", not manifest_issues, {"issues": manifest_issues})

    expected_overall = _overall_status(acquisitions, coverages)
    expected_coverage = _overall_coverage(acquisitions, coverages)
    add(
        "status_rule",
        result["overall_status"] == expected_overall
        and result["coverage_status"] == expected_coverage,
        {
            "overall": result["overall_status"],
            "coverage": result["coverage_status"],
            "expected_overall": expected_overall,
            "expected_coverage": expected_coverage,
        },
    )

    expected_window = result["requested_window"]
    add(
        "requested_window_consistency",
        expected_window
        == {
            "start_date": manifest["resolved_inputs"]["start_date"],
            "end_date": manifest["resolved_inputs"]["end_date"],
        },
        {},
    )
    add(
        "detail_file_identity",
        result["detail_file"]["name"] == "basis_daily.csv"
        and result["detail_file"]["artifact_id"] == csv_registration["payload"]["artifact_id"]
        and result["detail_file"]["sha256"] == csv_registration["payload"]["sha256"]
        and result["detail_file"]["row_count"] == len(data_rows),
        {},
    )
    assert resolution.start_date is not None and resolution.end_date is not None
    add(
        "result_failures_consistency",
        result["failures"] == _failures(
            acquisitions, resolution.start_date, resolution.end_date
        ),
        {},
    )
    expected_sessions = result["expected_sessions"]
    if resolution.calendar.status == "verified":
        expected_count = sum(
            1
            for record in resolution.calendar.records
            if record.is_open == 1
            and resolution.start_date is not None
            and resolution.end_date is not None
            and resolution.start_date <= record.cal_date <= resolution.end_date
        )
        expected_ok = (
            expected_sessions["status"] == "verified"
            and expected_sessions["source"] == CALENDAR_ID
            and expected_sessions["trade_date_count"] == expected_count
        )
    else:
        expected_ok = (
            expected_sessions["status"] == "unverified"
            and expected_sessions["source"] == CALENDAR_ID
            and expected_sessions["trade_date_count"] == 0
            and expected_sessions["first_trade_date"] is None
            and expected_sessions["last_trade_date"] is None
            and bool(expected_sessions["unverified_reason"])
        )
    add("expected_sessions_consistency", expected_ok, {})

    acquisition_payload = json.loads(
        _read_artifact(store, run_id, acquisition_registration).decode("utf-8")
    )
    acquisition_issues = []
    if len(acquisition_payload.get("families", [])) != len(acquisitions):
        acquisition_issues.append("family count")
    for item in acquisition_payload.get("families", []):
        if item.get("invocations") != 1:
            acquisition_issues.append(f"{item.get('futures_family')}: invocations")
        if item.get("request") is None:
            acquisition_issues.append(f"{item.get('futures_family')}: request")
    add("acquisition_evidence", not acquisition_issues, {"issues": acquisition_issues})

    resolution_document = json.loads(
        _read_artifact(store, run_id, resolution_registration).decode("utf-8")
    )
    resolution_issues = []
    if resolution_document["resolved_inputs"] != manifest["resolved_inputs"]:
        resolution_issues.append("resolved_inputs")
    if resolution_document["task_sha256"] != manifest["task_sha256"]:
        resolution_issues.append("task_sha256")
    if resolution_document["run_id"] != run_id:
        resolution_issues.append("run_id")
    if calendar_registration is not None:
        calendar_ref = resolution_document.get("calendar_evidence")
        if (
            calendar_ref is None
            or calendar_ref["artifact_id"] != calendar_registration["payload"]["artifact_id"]
            or calendar_ref["sha256"] != calendar_registration["payload"]["sha256"]
        ):
            resolution_issues.append("calendar_evidence")
    add("resolution_evidence", not resolution_issues, {"issues": resolution_issues})

    report_data = _read_artifact(store, run_id, report_registration).decode("utf-8")
    report_issues = [heading for heading in REPORT_HEADINGS if heading not in report_data]
    add("report_sections", not report_issues, {"missing": report_issues})
    add(
        "report_status_lines",
        f"Overall status: {result['overall_status']}" in report_data
        and f"Coverage status: {result['coverage_status']}" in report_data,
        {},
    )
    add(
        "report_formula_and_units",
        "basis_pct = (futures_close / underlying_close - 1) * 100" in report_data
        and "annualized_basis_pct = basis_pct * 365 / max(days_to_delist, 1)"
        in report_data
        and "Units are percentage points." in report_data
        and "negative = discount" in report_data
        and "positive = premium" in report_data,
        {},
    )
    add(
        "report_near_expiry",
        "annualization_days = max(days_to_delist, 1)" in report_data
        and "highly sensitive" in report_data,
        {},
    )
    add(
        "report_limitations",
        "not an executable arbitrage yield" in report_data
        and "no chart" in report_data,
        {},
    )
    report_value_issues = []
    for acquisition in acquisitions:
        if acquisition.status != "success" or not acquisition.observations:
            continue
        latest = max(item.trade_date for item in acquisition.observations)
        if latest not in report_data:
            report_value_issues.append(f"{acquisition.family}: latest date missing")
        latest_rows = [
            item for item in acquisition.observations if item.trade_date == latest
        ]
        for slot in SLOTS:
            slot_rows = [item for item in latest_rows if item.contract_slot == slot]
            if len(slot_rows) != 1:
                continue
            if _decimal(slot_rows[0].annualized_basis_pct) not in report_data:
                report_value_issues.append(f"{acquisition.family} {slot}: value missing")
            if slot_rows[0].contract_code not in report_data:
                report_value_issues.append(f"{acquisition.family} {slot}: contract missing")
    add("report_latest_values", not report_value_issues, {"issues": report_value_issues[:20]})
    latest_dates = {
        acquisition.family: max(
            item.trade_date for item in acquisition.observations
        )
        for acquisition in acquisitions
        if acquisition.status == "success" and acquisition.observations
    }
    if len(set(latest_dates.values())) > 1:
        add(
            "report_different_sessions",
            "different sessions" in report_data,
            {"latest_dates": latest_dates},
        )
    else:
        add("report_different_sessions", True, {"latest_dates": latest_dates})

    failed_checks = [item["check"] for item in checks if item["status"] != "pass"]
    passed = not failed_checks
    if acquisition_gate_status != "PASS":
        gate_status = "BLOCKED"
        gate_reason = "basis_acquisition is not PASS; delivery cannot be accepted."
    elif not passed:
        gate_status = "FAIL"
        gate_reason = "Delivery verification failed: " + ", ".join(failed_checks[:8])
    elif any(item.status == "verified_partial" for item in coverages):
        gate_status = "FAIL"
        gate_reason = "Coverage is verified_partial; the delivered panel is incomplete."
    elif all(item.status == "verified_complete" for item in coverages):
        gate_status = "PASS"
        gate_reason = (
            "All three outputs are consistent with the lossless acquisition evidence and "
            "every family coverage is verified_complete."
        )
    else:
        gate_status = "BLOCKED"
        gate_reason = (
            "Expected-session coverage is not verified_complete; delivery cannot claim "
            "completeness."
        )
    return {
        "schema_version": 1,
        "run_id": run_id,
        "task_id": task["task_id"],
        "task_version": task["version"],
        "checks": checks,
        "passed": passed,
        "gate_decision": {
            "gate_id": "result_delivery",
            "status": gate_status,
            "reason": gate_reason,
        },
        "artifacts": {
            "resolution.json": _artifact_reference(resolution_registration),
            "calendar": (
                _artifact_reference(calendar_registration)
                if calendar_registration is not None
                else None
            ),
            "acquisition": _artifact_reference(acquisition_registration),
            "basis_daily.csv": _artifact_reference(csv_registration),
            "result.json": _artifact_reference(result_registration),
            "REPORT.md": _artifact_reference(report_registration),
        },
    }


def _load_task() -> dict[str, Any]:
    task = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    if task.get("task_id") != TASK_ID or str(task.get("version")) != TASK_VERSION:
        raise ValueError("unexpected Task identity or version")
    expected_gates = ["input_resolution", "basis_acquisition", "result_delivery"]
    if [item.get("gate_id") for item in task.get("gates", [])] != expected_gates:
        raise ValueError("Task Gate definitions do not match this runtime")
    return task


def _gate_status(gates: list[dict[str, Any]]) -> str:
    statuses = [item["status"] for item in gates]
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    return "PASS"


def run_monitor(
    params: Any,
    *,
    authorization_reference: str | None = None,
    store_root: str | Path = DEFAULT_STORE_ROOT,
    product_runner: Callable[
        [CFFEXEquityIndexBasisHistoryRequest], CFFEXEquityIndexBasisHistoryResult
    ]
    | None = None,
    calendar_service: Any | None = None,
    execution_date: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run one monitor request; fake product/calendar services are test-only seams."""
    auth = authorization_reference.strip() if isinstance(authorization_reference, str) else None
    if not auth:
        auth = None
    execution_day, instant = _execution_instant(execution_date, now)
    task = _load_task()
    resolution = _resolve(
        params,
        authorization_reference=auth,
        calendar_service=calendar_service,
        execution_date=execution_day,
        instant=instant,
    )
    store = RunStore(store_root)
    manifest = store.create(
        {
            "task": task,
            "original_request": resolution.original_request,
            "resolved_inputs": resolution.resolved_inputs,
        }
    )
    run_id = manifest["run_id"]
    gate_records: list[dict[str, Any]] = []
    result_registration: dict[str, Any] | None = None
    csv_registration: dict[str, Any] | None = None
    report_registration: dict[str, Any] | None = None
    acquisition_registration: dict[str, Any] | None = None
    verification_registration: dict[str, Any] | None = None
    result_document: dict[str, Any] | None = None

    with tempfile.TemporaryDirectory(prefix="equity-basis-monitor-") as directory_name:
        directory = Path(directory_name)
        calendar_registration = _register_calendar(
            store, run_id, directory, resolution.calendar
        )
        resolution_payload = _resolution_payload(
            task=task,
            manifest=manifest,
            resolution=resolution,
            calendar_registration=calendar_registration,
        )
        resolution_registration = _save_bytes(
            store,
            run_id,
            directory,
            "resolution.json",
            _json_bytes(resolution_payload),
            "resolution.json",
        )
        resolution_evidence = [resolution_registration["payload"]["artifact_id"]]
        if calendar_registration is not None:
            resolution_evidence.append(calendar_registration["payload"]["artifact_id"])
        input_gate = store.gate(
            run_id,
            {
                "gate_id": "input_resolution",
                "status": resolution.gate_status,
                "reason": resolution.reason,
                "evidence": resolution_evidence,
            },
        )
        gate_records.append(input_gate)

        if resolution.gate_status != "PASS" or resolution.start_date is None:
            acquisition_gate = store.gate(
                run_id,
                {
                    "gate_id": "basis_acquisition",
                    "status": "BLOCKED",
                    "reason": "input_resolution is not PASS; no product was invoked.",
                    "evidence": resolution_evidence,
                },
            )
            gate_records.append(acquisition_gate)
            delivery_gate = store.gate(
                run_id,
                {
                    "gate_id": "result_delivery",
                    "status": "BLOCKED",
                    "reason": "basis_acquisition is not PASS; no delivery was attempted.",
                    "evidence": resolution_evidence,
                },
            )
            gate_records.append(delivery_gate)
        elif auth is None:
            acquisition_gate = store.gate(
                run_id,
                {
                    "gate_id": "basis_acquisition",
                    "status": "BLOCKED",
                    "reason": (
                        "Separate execution authorization is absent; no public product or "
                        "CFFEX Calendar market request was made."
                    ),
                    "evidence": resolution_evidence,
                },
            )
            gate_records.append(acquisition_gate)
            delivery_gate = store.gate(
                run_id,
                {
                    "gate_id": "result_delivery",
                    "status": "BLOCKED",
                    "reason": "basis_acquisition is not PASS; no delivery was attempted.",
                    "evidence": resolution_evidence,
                },
            )
            gate_records.append(delivery_gate)
        else:
            start = resolution.start_date
            end = resolution.end_date
            assert end is not None
            store.event(
                run_id,
                {
                    "operation": "acquisition_intent",
                    "details": {
                        "task_id": task["task_id"],
                        "task_version": task["version"],
                        "families": resolution.families,
                        "start_date": start.isoformat(),
                        "end_date": end.isoformat(),
                        "authorization_reference": auth,
                        "product": PRODUCT_ID,
                        "calendar_source": CALENDAR_ID,
                    },
                },
            )
            runner = product_runner or _default_product_runner
            acquisitions: list[FamilyAcquisition] = []
            coverages: list[FamilyCoverage] = []
            for family in resolution.families:
                request = CFFEXEquityIndexBasisHistoryRequest(
                    futures_family=family,
                    start_trade_date=start.isoformat(),
                    end_trade_date=end.isoformat(),
                )
                acquisition = _acquire_family(family, request, runner)
                acquisitions.append(acquisition)
                coverages.append(
                    _coverage_for(acquisition, resolution.calendar, start, end)
                )
            rows: list[tuple[str, ...]] = []
            for acquisition in acquisitions:
                if acquisition.status == "success":
                    rows.extend(_csv_row(item) for item in acquisition.observations)
            rows.sort(key=_csv_sort_key)
            csv_registration = _save_bytes(
                store,
                run_id,
                directory,
                "basis_daily.csv",
                _csv_bytes(rows),
                "basis_daily.csv",
            )

            acquisition_payload = _acquisition_payload(
                task=task,
                manifest=manifest,
                acquisitions=acquisitions,
                coverages=coverages,
            )
            acquisition_registration = _save_bytes(
                store,
                run_id,
                directory,
                "acquisition.json",
                _json_bytes(acquisition_payload),
                "acquisition evidence",
            )
            failed_families = [
                item for item in acquisitions if item.status == "failed"
            ]
            if failed_families:
                acquisition_gate = store.gate(
                    run_id,
                    {
                        "gate_id": "basis_acquisition",
                        "status": "FAIL",
                        "reason": (
                            f"{len(failed_families)} of {len(acquisitions)} family "
                            "acquisition(s) failed; successful families remain preserved."
                        ),
                        "evidence": [acquisition_registration["payload"]["artifact_id"]],
                    },
                )
            else:
                acquisition_gate = store.gate(
                    run_id,
                    {
                        "gate_id": "basis_acquisition",
                        "status": "PASS",
                        "reason": (
                            f"All {len(acquisitions)} requested families returned a "
                            "successful public result with exactly one invocation each."
                        ),
                        "evidence": [acquisition_registration["payload"]["artifact_id"]],
                    },
                )
            gate_records.append(acquisition_gate)

            overall_status = _overall_status(acquisitions, coverages)
            coverage_status = _overall_coverage(acquisitions, coverages)
            result_document = {
                "schema_version": 1,
                "task_id": task["task_id"],
                "task_version": task["version"],
                "task_sha256": manifest["task_sha256"],
                "run_id": run_id,
                "original_request": manifest["original_request"],
                "resolved_inputs": manifest["resolved_inputs"],
                "requested_window": {
                    "start_date": manifest["resolved_inputs"]["start_date"],
                    "end_date": manifest["resolved_inputs"]["end_date"],
                },
                "expected_sessions": _expected_sessions(
                    resolution.calendar, start, end
                ),
                "overall_status": overall_status,
                "coverage_status": coverage_status,
                "families": [
                    _family_payload(acquisition, coverage, start, end)
                    for acquisition, coverage in zip(
                        acquisitions, coverages, strict=True
                    )
                ],
                "failures": _failures(acquisitions, start, end),
                "unfinished_scope": _unfinished_scope(
                    acquisitions, coverages, overall_status
                ),
                "limitations": _limitations(acquisitions, coverages, overall_status),
                "detail_file": {
                    "name": "basis_daily.csv",
                    "artifact_id": csv_registration["payload"]["artifact_id"],
                    "sha256": csv_registration["payload"]["sha256"],
                    "stored_path": csv_registration["payload"]["stored_path"],
                    "row_count": len(rows),
                },
            }
            result_registration = _save_bytes(
                store,
                run_id,
                directory,
                "result.json",
                _json_bytes(result_document),
                "result.json",
            )
            report_data = _report(
                result=result_document,
                acquisitions=acquisitions,
                coverages=coverages,
            )
            report_registration = _save_bytes(
                store,
                run_id,
                directory,
                "REPORT.md",
                report_data.encode("utf-8"),
                "REPORT.md",
            )
            verification = _verification(
                store=store,
                run_id=run_id,
                manifest=manifest,
                task=task,
                resolution=resolution,
                resolution_registration=resolution_registration,
                acquisitions=acquisitions,
                coverages=coverages,
                result=result_document,
                result_registration=result_registration,
                csv_registration=csv_registration,
                report_registration=report_registration,
                acquisition_registration=acquisition_registration,
                calendar_registration=calendar_registration,
                acquisition_gate_status=acquisition_gate["payload"]["status"],
            )
            verification_registration = _save_bytes(
                store,
                run_id,
                directory,
                "verification.json",
                _json_bytes(verification),
                "verification.json",
            )
            decision = verification["gate_decision"]
            delivery_gate = store.gate(
                run_id,
                {
                    "gate_id": "result_delivery",
                    "status": decision["status"],
                    "reason": decision["reason"],
                    "evidence": [verification_registration["payload"]["artifact_id"]],
                },
            )
            gate_records.append(delivery_gate)

    gates = [
        {
            "gate_id": item["payload"]["gate_id"],
            "status": item["payload"]["status"],
            "reason": item["payload"]["reason"],
        }
        for item in gate_records
    ]
    result_path = (
        str(store.root / run_id / result_registration["payload"]["stored_path"])
        if result_registration is not None
        else None
    )
    report_path = (
        str(store.root / run_id / report_registration["payload"]["stored_path"])
        if report_registration is not None
        else None
    )
    csv_path = (
        str(store.root / run_id / csv_registration["payload"]["stored_path"])
        if csv_registration is not None
        else None
    )
    return {
        "task_id": task["task_id"],
        "task_version": task["version"],
        "run_id": run_id,
        "task_sha256": manifest["task_sha256"],
        "status": _gate_status(gates),
        "overall_status": (
            result_document["overall_status"] if result_document is not None else None
        ),
        "coverage_status": (
            result_document["coverage_status"] if result_document is not None else None
        ),
        "gates": gates,
        "result": (
            _artifact_reference(result_registration)
            if result_registration is not None
            else None
        ),
        "report": (
            _artifact_reference(report_registration)
            if report_registration is not None
            else None
        ),
        "csv": (
            _artifact_reference(csv_registration)
            if csv_registration is not None
            else None
        ),
        "verification": (
            _artifact_reference(verification_registration)
            if verification_registration is not None
            else None
        ),
        "result_path": result_path,
        "report_path": report_path,
        "csv_path": csv_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON request")
    parser.add_argument(
        "--authorization-reference",
        default=None,
        help="Verbatim separate user authorization; omit to perform no market access",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_STORE_ROOT)
    args = parser.parse_args(argv)
    try:
        params = json.loads(args.input.read_text(encoding="utf-8"))
        outcome = run_monitor(
            params,
            authorization_reference=args.authorization_reference,
            store_root=args.root,
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"equity-basis: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[outcome["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
