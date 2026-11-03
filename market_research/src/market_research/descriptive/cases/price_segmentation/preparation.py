"""Acquire and validate exact public inputs; no algorithm or observation execution."""

import hashlib
import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from math import isfinite, log
from typing import Any, Protocol, cast

from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError, UnitFailure
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRange, IndexDailyRow
from data_lake.datasets.tushare_index_daily import create_service as create_index_service
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from .inputs import (
    ExportEvidence,
    InputAttempt,
    InputPreparationError,
    PreparedSegmentationInputs,
    SegmentationRequest,
)


class CalendarService(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...
    def ensure(self, request: TradeCalendarRange) -> EnsureResult: ...


class IndexService(Protocol):
    def export(self, request: IndexDailyRange) -> IndexDailyExport: ...
    def ensure(self, request: IndexDailyRange) -> EnsureResult: ...


def _require(condition: bool, reason: str, category: str = "invalid_public_export") -> None:
    if not condition:
        raise InputPreparationError(category, "validation", None, reason)


def _coverage(value: CoverageResult, expected: int) -> CoverageResult:
    counts = (
        value.requested_units,
        value.successful_units,
        value.missing_units,
        value.pending_units,
        value.failed_units,
    )
    _require(all(type(n) is int and n >= 0 for n in counts), "Invalid coverage counters")
    _require(counts[0] == expected and sum(counts[1:]) == expected, "Coverage accounting mismatch")
    _require(
        type(value.complete) is bool and value.complete == (counts[1] == expected),
        "Invalid coverage complete flag",
    )
    return CoverageResult(*counts, value.complete)


def _validate_export(
    raw: object, request: TradeCalendarRange | IndexDailyRange, sessions: tuple[date, ...] = ()
) -> ExportEvidence:
    calendar = isinstance(request, TradeCalendarRange)
    try:
        view = cast(Any, raw)
        dataset = "tushare_trade_calendar" if calendar else "tushare_index_daily"
        name = "calendar" if calendar else "index_daily"
        _require(type(view.dataset) is str and view.dataset == dataset, "Wrong dataset")
        _require(type(view.view) is str and view.view == name, "Wrong view")
        _require(
            type(view.export_schema_version) is int and view.export_schema_version == 1,
            "Wrong schema version",
        )
        window = view.window
        _require(
            type(window.start_date) is date
            and type(window.end_date) is date
            and window.start_date == request.start_date
            and window.end_date == request.end_date,
            "Wrong window",
        )
        if calendar:
            scope = (view.scope.exchange,)
            expected = (request.end_date - request.start_date).days + 1
            _require(scope == ("SSE",) and type(scope[0]) is str, "Wrong Calendar scope")
        else:
            codes = view.scope.index_codes
            _require(
                isinstance(codes, Sequence) and not isinstance(codes, str | bytes | bytearray),
                "Invalid Index scope",
            )
            scope = tuple(codes)
            _require(
                scope == tuple(cast(IndexDailyRange, request).index_codes), "Wrong Index scope"
            )
            expected = len(sessions)
        coverage = _coverage(view.coverage, expected)
        _require(
            isinstance(view.records, Sequence)
            and not isinstance(view.records, str | bytes | bytearray),
            "Invalid records sequence",
        )
        _require(len(view.records) == coverage.successful_units, "Record count mismatch")
        rows: list[TradeCalendarRecord | IndexDailyRow] = []
        previous = None
        session_set = set(sessions)
        metadata = None
        for row in view.records:
            if calendar:
                _require(type(row.exchange) is str and row.exchange == "SSE", "Invalid exchange")
                day = row.cal_date
                _require(
                    type(day) is date and request.start_date <= day <= request.end_date,
                    "Invalid Calendar date",
                )
                _require(type(row.is_open) is int and row.is_open in (0, 1), "Invalid is_open")
                _require(
                    row.pretrade_date is None or type(row.pretrade_date) is date,
                    "Invalid pretrade_date",
                )
                rows.append(TradeCalendarRecord(row.exchange, day, row.is_open, row.pretrade_date))
            else:
                day = row.trade_date
                _require(
                    type(row.index_code) is str and row.index_code == scope[0],
                    "Invalid index identity",
                )
                _require(type(day) is date and day in session_set, "Unexpected trading date")
                _require(type(row.symbol) is str and row.symbol == scope[0][:6], "Invalid symbol")
                for field in ("name", "market"):
                    text = getattr(row, field)
                    _require(type(text) is str and bool(text.strip()), "Invalid " + field)
                for field in ("publisher", "category"):
                    text = getattr(row, field)
                    _require(
                        text is None or (type(text) is str and bool(text.strip())),
                        "Invalid " + field,
                    )
                current_metadata = (row.symbol, row.name, row.market, row.publisher, row.category)
                _require(
                    metadata is None or metadata == current_metadata, "Conflicting index metadata"
                )
                metadata = current_metadata
                fields = (
                    "open",
                    "high",
                    "low",
                    "close",
                    "pre_close",
                    "change",
                    "pct_change",
                    "volume",
                    "amount",
                )
                for field in fields:
                    number = getattr(row, field)
                    category = "invalid_price_fact" if field == "close" else "invalid_public_export"
                    _require(
                        type(number) is float and isfinite(number), "Invalid " + field, category
                    )
                    _require(field not in ("volume", "amount") or number >= 0, "Negative " + field)
                _require(row.close > 0, "Close must be positive", "invalid_price_fact")
                rows.append(
                    IndexDailyRow(
                        row.index_code,
                        row.symbol,
                        row.name,
                        row.market,
                        row.publisher,
                        row.category,
                        day,
                        *(getattr(row, field) for field in fields),
                    )
                )
            _require(previous is None or previous < day, "Records not strictly ordered")
            previous = day
        return ExportEvidence(
            dataset, name, 1, scope, request.start_date, request.end_date, coverage, tuple(rows)
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise InputPreparationError(
            "invalid_public_export", "validation", request, "Malformed public export"
        ) from exc


def _validate_ensure(raw: object, targets: set[tuple[str, date]]) -> EnsureResult:
    try:
        value = cast(EnsureResult, raw)
        counts = (
            value.requested_units,
            value.already_successful_units,
            value.attempted_units,
            value.succeeded_units,
            value.failed_units,
            value.records_written,
        )
        _require(all(type(n) is int and n >= 0 for n in counts), "Invalid Ensure counters")
        requested, already, attempted, succeeded, failed, written = counts
        _require(
            requested == len(targets)
            and already + attempted == requested
            and succeeded + failed == attempted
            and written == succeeded,
            "Ensure accounting mismatch",
        )
        _require(
            type(value.complete) is bool and value.complete == (already + succeeded == requested),
            "Invalid Ensure complete flag",
        )
        _require(
            isinstance(value.failures, Sequence)
            and not isinstance(value.failures, str | bytes | bytearray)
            and len(value.failures) == failed,
            "Invalid Ensure failures",
        )
        failures = []
        seen: set[tuple[str, date]] = set()
        for item in value.failures:
            identity = cast(Any, item.identity)
            _require(
                isinstance(identity, Sequence)
                and not isinstance(identity, str | bytes | bytearray)
                and len(identity) == 2,
                "Invalid failure identity",
            )
            key = (identity[0], identity[1])
            _require(
                type(key[0]) is str and type(key[1]) is date and key in targets and key not in seen,
                "Foreign or duplicate failure identity",
            )
            _require(
                type(item.reason) is str and bool(item.reason.strip()), "Invalid failure reason"
            )
            seen.add(key)
            failures.append(UnitFailure(key, item.reason))
        return EnsureResult(*counts, value.complete, tuple(failures))
    except (AttributeError, TypeError, ValueError) as exc:
        raise InputPreparationError(
            "invalid_public_export", "ensure validation", None, "Malformed Ensure result"
        ) from exc


def prepare_inputs(
    request: SegmentationRequest,
    *,
    calendar_service: CalendarService | None = None,
    index_service: IndexService | None = None,
) -> PreparedSegmentationInputs:
    """Prepare complete, verified facts for one explicit Price Segmentation request."""
    stage = "request validation"
    current: object = request
    attempts: list[InputAttempt] = []
    try:
        _require(
            isinstance(request, SegmentationRequest),
            "Expected SegmentationRequest",
            "invalid_request",
        )
        _require(
            request.research == "price_segmentation_v1"
            and request.price_field == "close"
            and request.transform == "natural_log"
            and request.time_axis == "trading_session_index"
            and request.algorithm_id == "pip_vertical_error_bounded_v1",
            "Unsupported request identity",
            "invalid_request",
        )
        _require(type(request.epsilon) in (int, float), "Invalid epsilon type", "invalid_request")
        try:
            epsilon = float(request.epsilon)
        except OverflowError as exc:
            raise InputPreparationError(
                "invalid_request", stage, request, "Invalid epsilon"
            ) from exc
        _require(
            isfinite(epsilon) and epsilon > 0,
            "Epsilon must be finite and positive",
            "invalid_request",
        )
        index_request = IndexDailyRange((request.index_code,), request.start_date, request.end_date)
        calendar_request = TradeCalendarRange("SSE", request.start_date, request.end_date)
        identity = replace(request, epsilon=epsilon)
        current = calendar_request
        stage = "create calendar service"
        calendar = calendar_service if calendar_service is not None else create_calendar_service()
        attempts.append(InputAttempt(calendar_request))
        stage = "calendar export"
        view = _validate_export(calendar.export(calendar_request), calendar_request)
        attempts[-1] = replace(attempts[-1], preliminary_export=view)
        if not view.coverage.complete:
            stage = "calendar ensure"
            targets = {
                ("SSE", date.fromordinal(n))
                for n in range(request.start_date.toordinal(), request.end_date.toordinal() + 1)
            }
            ensured = _validate_ensure(calendar.ensure(calendar_request), targets)
            attempts[-1] = replace(attempts[-1], ensure_result=ensured)
            stage = "calendar final export"
            view = _validate_export(calendar.export(calendar_request), calendar_request)
        attempts[-1] = replace(attempts[-1], final_export=view)
        _require(view.coverage.complete, "Calendar is incomplete", "incomplete_calendar")
        sessions = tuple(
            row.cal_date
            for row in view.records
            if isinstance(row, TradeCalendarRecord) and row.is_open == 1
        )
        _require(len(sessions) >= 2, "Fewer than two open sessions", "incomplete_calendar")
        current = index_request
        stage = "create index service"
        index = index_service if index_service is not None else create_index_service()
        attempts.append(InputAttempt(index_request))
        stage = "index export"
        view = _validate_export(index.export(index_request), index_request, sessions)
        attempts[-1] = replace(attempts[-1], preliminary_export=view)
        if not view.coverage.complete:
            stage = "index ensure"
            ensured = _validate_ensure(
                index.ensure(index_request), {(request.index_code, d) for d in sessions}
            )
            attempts[-1] = replace(attempts[-1], ensure_result=ensured)
            stage = "index final export"
            view = _validate_export(index.export(index_request), index_request, sessions)
        attempts[-1] = replace(attempts[-1], final_export=view)
        _require(view.coverage.complete, "Price series is incomplete", "incomplete_price_series")
        rows = cast(tuple[IndexDailyRow, ...], view.records)
        _require(
            tuple(row.trade_date for row in rows) == sessions, "Index rows do not match sessions"
        )
        closes = tuple(row.close for row in rows)
        stage = "log transformation"
        try:
            logs = tuple(log(close) for close in closes)
        except (ValueError, OverflowError) as exc:
            raise InputPreparationError(
                "numerical_transformation_failure", stage, current, "Cannot compute natural log"
            ) from exc
        _require(
            all(isfinite(x) for x in logs),
            "Non-finite logarithm",
            "numerical_transformation_failure",
        )
        payload = [
            "price_segmentation_inputs_v1",
            "tushare_index_daily",
            "index_daily",
            1,
            request.index_code,
            [[day.isoformat(), close.hex()] for day, close in zip(sessions, closes, strict=True)],
        ]
        fingerprint = hashlib.sha256(
            json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return PreparedSegmentationInputs(
            identity, sessions, closes, logs, len(sessions), fingerprint, tuple(attempts)
        )
    except InputPreparationError as exc:
        exc.stage = stage
        exc.request = current
        exc.evidence = tuple(attempts)
        raise
    except InvalidRequestError as exc:
        category = (
            "invalid_request" if stage == "request validation" else "upstream_operation_failure"
        )
        raise InputPreparationError(category, stage, current, str(exc), tuple(attempts)) from exc
    except OperationError as exc:
        raise InputPreparationError(
            "upstream_operation_failure", stage, current, str(exc), tuple(attempts)
        ) from exc
