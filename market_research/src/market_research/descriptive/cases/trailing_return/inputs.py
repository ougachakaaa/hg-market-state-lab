"""Case-owned public input evidence and pure contract validation."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from math import isfinite
from typing import cast

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_index_daily import (
    IndexDailyExport,
    IndexDailyRange,
    IndexDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)

from ...observation.models import (
    DailyKey,
    DateWindow,
    InvalidObservationRequest,
    JobIdentity,
    ObservationJobSpec,
)

METRIC = "trailing_cumulative_return_v1"
PROFILE = "trailing_return_inputs_v2"
POLICY = "descriptive_missing_tolerant_v1"
FLOAT_FIELDS = (
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
type InputRequest = TradeCalendarRange | IndexDailyRange
type InputExport = TradeCalendarExport | IndexDailyExport


@dataclass(frozen=True)
class InputAttempt:
    request: InputRequest
    preliminary_export: object = None
    ensure_result: object = None
    final_export: object = None


class InputPreparationFailure(Exception):
    stage = "input_preparation"
    category = "InputPreparationFailure"

    def __init__(
        self,
        reason: str,
        *,
        request: InputRequest | None = None,
        evidence: tuple[InputAttempt, ...] = (),
    ) -> None:
        super().__init__(reason)
        self.request = request
        self.evidence = evidence


class InvalidPublicInput(InputPreparationFailure):
    category = "InvalidPublicInput"


class IncompleteInput(InputPreparationFailure):
    category = "IncompleteInput"


class HistoryInsufficient(InputPreparationFailure):
    category = "HistoryInsufficient"


class UpstreamFailure(InputPreparationFailure):
    category = "UpstreamFailure"


@dataclass(frozen=True)
class CalendarInput:
    request: TradeCalendarRange
    final_export: TradeCalendarExport


@dataclass(frozen=True)
class IndexInput:
    request: IndexDailyRange
    final_export: IndexDailyExport


@dataclass(frozen=True)
class PreparedInputs:
    job_identity: JobIdentity
    calendar_slices: tuple[CalendarInput, ...]
    index_slice: IndexInput | None
    attempts: tuple[InputAttempt, ...]


def validate_job(job: ObservationJobSpec, *, check_current_date: bool = True) -> None:
    if not isinstance(job, ObservationJobSpec):
        raise InvalidObservationRequest("Expected ObservationJobSpec")
    replace(job)  # Validate a fresh copy without mutating the caller's fixed request.
    if job.metric != METRIC:
        raise InvalidObservationRequest("Unrecognized metric identity/version")
    if re.fullmatch(r"[0-9]{6}\.(SH|SZ|CSI)", job.subject) is None:
        raise InvalidObservationRequest("This case requires a full canonical index_code")
    if job.metric_parameters:
        raise InvalidObservationRequest("Trailing Return requires empty metric_parameters")
    if (
        check_current_date
        and job.historical_sample_window.end_date
        > datetime.now(timezone(timedelta(hours=8))).date()
    ):
        raise InvalidObservationRequest("Window cannot extend beyond today in Asia/Shanghai")


def job_identity(job: ObservationJobSpec) -> JobIdentity:
    window = job.historical_sample_window
    return (
        METRIC,
        job.subject,
        (),
        job.horizon,
        "trading_sessions",
        window.start_date,
        window.end_date,
        "end_session",
        "inclusive",
    )


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise InvalidPublicInput(reason)


def _sequence(value: object) -> Sequence[object]:
    _require(
        isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray),
        "Expected a public ordered sequence",
    )
    return cast(Sequence[object], value)


def validate_coverage(coverage: CoverageResult, expected: int) -> None:
    counts = (
        coverage.requested_units,
        coverage.successful_units,
        coverage.missing_units,
        coverage.pending_units,
        coverage.failed_units,
    )
    _require(all(type(n) is int and n >= 0 for n in counts), "Illegal coverage counter types")
    _require(
        counts[0] == expected and sum(counts[1:]) == expected,
        "Coverage counters do not conserve the complete target population",
    )
    _require(
        type(coverage.complete) is bool
        and coverage.complete == (coverage.successful_units == expected),
        "Contradictory coverage complete flag",
    )


def _validate_envelope(view: InputExport, request: InputRequest, dataset: str, name: str) -> None:
    _require(type(view.dataset) is str and view.dataset == dataset, "Wrong Dataset")
    _require(type(view.view) is str and view.view == name, "Wrong public view")
    _require(
        type(view.export_schema_version) is int and view.export_schema_version == 1,
        "Wrong export schema version",
    )
    window = cast(DateWindow, view.window)
    _require(
        type(window.start_date) is date
        and type(window.end_date) is date
        and window.start_date == request.start_date
        and window.end_date == request.end_date,
        "Wrong public window",
    )


def validate_calendar(view: object, request: TradeCalendarRange) -> TradeCalendarExport:
    """Validate partial as well as complete views; never repair an illegal payload."""
    try:
        value = cast(TradeCalendarExport, view)
        _validate_envelope(value, request, "tushare_trade_calendar", "calendar")
        _require(
            type(value.scope.exchange) is str and value.scope.exchange == request.exchange,
            "Wrong Calendar scope",
        )
        expected = (request.end_date - request.start_date).days + 1
        validate_coverage(value.coverage, expected)
        _sequence(value.records)
        _require(
            len(value.records) == value.coverage.successful_units,
            "Calendar record count disagrees with coverage",
        )
        previous: date | None = None
        for row in value.records:
            _require(
                type(row.exchange) is str and row.exchange == request.exchange,
                "Wrong Calendar record exchange",
            )
            _require(
                type(row.cal_date) is date
                and request.start_date <= row.cal_date <= request.end_date,
                "Illegal Calendar record date",
            )
            _require(
                previous is None or previous < row.cal_date,
                "Calendar records must be ordered and unique",
            )
            _require(type(row.is_open) is int and row.is_open in (0, 1), "Illegal is_open")
            _require(
                row.pretrade_date is None or type(row.pretrade_date) is date,
                "Illegal pretrade_date",
            )
            previous = row.cal_date
        return value
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidPublicInput("Malformed Calendar public view") from exc


def validate_index(
    view: object, request: IndexDailyRange, sessions: tuple[date, ...]
) -> IndexDailyExport:
    try:
        value = cast(IndexDailyExport, view)
        _validate_envelope(value, request, "tushare_index_daily", "index_daily")
        codes = _sequence(cast(IndexDailyScope, value.scope).index_codes)
        _require(tuple(codes) == tuple(request.index_codes), "Wrong Index scope")
        validate_coverage(value.coverage, len(sessions))
        _sequence(value.records)
        _require(
            len(value.records) == value.coverage.successful_units,
            "Index record count disagrees with coverage",
        )
        expected = {(request.index_codes[0], day) for day in sessions}
        previous: DailyKey | None = None
        for row in value.records:
            _require(
                type(row.index_code) is str and row.index_code == request.index_codes[0],
                "Wrong Index record identity",
            )
            _require(
                type(row.trade_date) is date and (row.index_code, row.trade_date) in expected,
                "Index record is not an expected trading session",
            )
            key = row.index_code, row.trade_date
            _require(previous is None or previous < key, "Index records must be ordered and unique")
            _require(type(row.symbol) is str and row.symbol == row.index_code[:6], "Wrong symbol")
            for name in ("name", "market"):
                text = getattr(row, name)
                _require(
                    type(text) is str and bool(text.strip()), "Illegal required Index metadata"
                )
            for name in ("publisher", "category"):
                text = getattr(row, name)
                _require(
                    text is None or (type(text) is str and bool(text.strip())),
                    "Illegal optional Index metadata",
                )
            for name in FLOAT_FIELDS:
                number = getattr(row, name)
                _require(
                    type(number) is float and isfinite(number), "Illegal public float: " + name
                )
                _require(
                    name not in ("volume", "amount") or number >= 0, "Negative volume or amount"
                )
            previous = key
        return value
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidPublicInput("Malformed Index public view") from exc


def validate_ensure(result: object, request: InputRequest, targets: set[DailyKey]) -> EnsureResult:
    try:
        value = cast(EnsureResult, result)
        counts = (
            value.requested_units,
            value.already_successful_units,
            value.attempted_units,
            value.succeeded_units,
            value.failed_units,
            value.records_written,
        )
        _require(all(type(n) is int and n >= 0 for n in counts), "Illegal Ensure counters")
        _require(
            value.requested_units == len(targets)
            and value.already_successful_units + value.attempted_units == value.requested_units
            and value.succeeded_units + value.failed_units == value.attempted_units
            and value.records_written == value.succeeded_units,
            "Ensure counters do not conserve requested targets",
        )
        _require(
            type(value.complete) is bool
            and value.complete
            == (value.already_successful_units + value.succeeded_units == value.requested_units),
            "Contradictory Ensure complete flag",
        )
        failures = _sequence(value.failures)
        _require(len(failures) == value.failed_units, "Ensure failure count mismatch")
        seen: set[DailyKey] = set()
        for item in failures:
            failure = cast(UnitFailure, item)
            identity = _sequence(failure.identity)
            _require(
                len(identity) == 2 and type(identity[0]) is str and type(identity[1]) is date,
                "Invalid UnitFailure semantic identity",
            )
            key = cast(DailyKey, tuple(identity))
            _require(key in targets and key not in seen, "Foreign or duplicate UnitFailure")
            _require(
                type(failure.reason) is str and bool(failure.reason.strip()),
                "Invalid UnitFailure reason",
            )
            seen.add(key)
        return value
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidPublicInput("Malformed EnsureResult", request=request) from exc


def resolve_calendar(
    job: ObservationJobSpec, slices: tuple[CalendarInput, ...]
) -> tuple[tuple[date, ...], tuple[date, ...]]:
    """Revalidate retained views and their exact discovery topology without I/O."""
    window = job.historical_sample_window
    remaining = list(slices)
    calendar_facts: dict[date, TradeCalendarRecord] = {}

    def take(request: TradeCalendarRange) -> tuple[date, ...]:
        matches = [item for item in remaining if item.request == request]
        _require(len(matches) == 1, "Missing or duplicate required Calendar slice")
        item = matches[0]
        remaining.remove(item)
        view = validate_calendar(item.final_export, request)
        if not view.coverage.complete:
            raise IncompleteInput("Final Calendar is incomplete", request=request)
        for row in view.records:
            _require(
                row.cal_date not in calendar_facts or calendar_facts[row.cal_date] == row,
                "Contradictory overlapping Calendar facts",
            )
            calendar_facts[row.cal_date] = row
        return tuple(row.cal_date for row in view.records if row.is_open == 1)

    anchors = take(TradeCalendarRange("SSE", window.start_date, window.end_date))
    history: tuple[date, ...] = ()
    if anchors:
        upper = anchors[0].toordinal() - 1
        width = job.horizon
        while len(history) < job.horizon:
            if upper < 1:
                raise HistoryInsufficient("Calendar exhausted at date.min")
            lower = max(1, upper - width + 1)
            request = TradeCalendarRange("SSE", date.fromordinal(lower), date.fromordinal(upper))
            history = take(request) + history
            upper = lower - 1
            width *= 2
    _require(not remaining, "Unexpected Calendar slices outside exact backward discovery")
    return anchors, history[-job.horizon :] + anchors if anchors else ()
