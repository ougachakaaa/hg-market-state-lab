"""Public-contract fakes; no upstream private composition or storage."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date
from typing import Any, cast

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_index_daily import (
    IndexDailyExport,
    IndexDailyRange,
    IndexDailyRow,
    IndexDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)
from market_research.descriptive.cases.trailing_return import (
    CalendarInput,
    IndexInput,
    PreparedInputs,
    construct_observations,
    prepare_inputs,
)
from market_research.descriptive.cases.trailing_return.identity import TrailingReturnProvenance
from market_research.descriptive.cases.trailing_return.inputs import job_identity
from market_research.descriptive.observation import DateWindow, ObservationJobSpec, ObservationSet

CODE = "000001.SH"  # Explicit fixture identity, never a CSI1000 name-to-code default.
DAYS = tuple(date(2024, 1, n) for n in range(8, 14))


def altered[T](value: T, **changes: Any) -> T:
    """Deliberately corrupt public dataclasses at the untrusted runtime boundary."""
    return cast(T, replace(cast(Any, value), **changes))


@dataclass(frozen=True)
class CalendarScope:
    exchange: str


def dates(start: date, end: date) -> tuple[date, ...]:
    return tuple(date.fromordinal(n) for n in range(start.toordinal(), end.toordinal() + 1))


def job(start: date = DAYS[2], end: date = DAYS[4], horizon: int = 2) -> ObservationJobSpec:
    return ObservationJobSpec(
        CODE, "trailing_cumulative_return_v1", {}, horizon, DateWindow(start, end)
    )


def calendar_view(request: TradeCalendarRange, opens: tuple[date, ...]) -> TradeCalendarExport:
    rows = tuple(
        TradeCalendarRecord(request.exchange, day, int(day in opens), None)
        for day in dates(request.start_date, request.end_date)
    )
    # Scope/window are structural public values, not imports of private type definitions.
    return TradeCalendarExport(
        "tushare_trade_calendar",
        "calendar",
        1,
        CalendarScope(request.exchange),  # type: ignore[arg-type]
        DateWindow(request.start_date, request.end_date),  # type: ignore[arg-type]
        CoverageResult(len(rows), len(rows), 0, 0, 0, True),
        rows,
    )


def daily_row(day: date, close: float) -> IndexDailyRow:
    return IndexDailyRow(
        CODE,
        "000001",
        "示例指数",
        "SSE",
        None,
        "综合指数",
        day,
        close,
        close,
        close,
        close,
        100.0,
        0.0,
        0.0,
        10.0,
        20.0,
    )


def index_view(
    request: IndexDailyRange, sessions: tuple[date, ...], closes: dict[date, float]
) -> IndexDailyExport:
    expected = tuple(day for day in sessions if request.start_date <= day <= request.end_date)
    rows = tuple(daily_row(day, closes[day]) for day in expected if day in closes)
    missing = len(expected) - len(rows)
    return IndexDailyExport(
        "tushare_index_daily",
        "index_daily",
        1,
        IndexDailyScope(tuple(request.index_codes)),
        DateWindow(request.start_date, request.end_date),
        CoverageResult(len(expected), len(rows), missing, 0, 0, missing == 0),
        rows,
    )


class CalendarFake:
    def __init__(self, opens: tuple[date, ...]) -> None:
        self.opens = opens
        self.calls: list[tuple[str, TradeCalendarRange]] = []
        self.transform: Callable[[TradeCalendarExport], TradeCalendarExport] = lambda view: view
        self.ensure_value: EnsureResult | Exception = AssertionError("Unexpected Calendar ensure")
        self.after_ensure: Callable[[TradeCalendarExport], TradeCalendarExport] | None = None
        self.ensured = False

    def export(self, request: TradeCalendarRange) -> TradeCalendarExport:
        self.calls.append(("export", request))
        view = calendar_view(request, self.opens)
        transform = self.after_ensure if self.ensured and self.after_ensure else self.transform
        return transform(view)

    def ensure(self, request: TradeCalendarRange) -> EnsureResult:
        self.calls.append(("ensure", request))
        self.ensured = True
        if isinstance(self.ensure_value, Exception):
            raise self.ensure_value
        return self.ensure_value


class IndexFake:
    def __init__(self, sessions: tuple[date, ...], closes: dict[date, float]) -> None:
        self.sessions = sessions
        self.closes = closes
        self.calls: list[tuple[str, IndexDailyRange]] = []
        self.transform: Callable[[IndexDailyExport], IndexDailyExport] = lambda view: view
        self.after_ensure: Callable[[IndexDailyExport], IndexDailyExport] | None = None
        self.ensure_value: EnsureResult | Exception | None = None
        self.ensured = False

    def export(self, request: IndexDailyRange) -> IndexDailyExport:
        self.calls.append(("export", request))
        view = index_view(request, self.sessions, self.closes)
        transform = self.after_ensure if self.ensured and self.after_ensure else self.transform
        return transform(view)

    def ensure(self, request: IndexDailyRange) -> EnsureResult:
        self.calls.append(("ensure", request))
        self.ensured = True
        if isinstance(self.ensure_value, Exception):
            raise self.ensure_value
        if self.ensure_value is not None:
            return self.ensure_value
        view = index_view(request, self.sessions, self.closes)
        failures = tuple(
            UnitFailure((CODE, day), "not currently published")
            for day in self.sessions
            if request.start_date <= day <= request.end_date and day not in self.closes
        )
        return EnsureResult(
            view.coverage.requested_units,
            len(view.records),
            len(failures),
            0,
            len(failures),
            0,
            not failures,
            failures,
        )


def execute(
    spec: ObservationJobSpec, sessions: tuple[date, ...], closes: dict[date, float]
) -> ObservationSet[TrailingReturnProvenance]:
    inputs = prepare_inputs(
        spec, calendar_service=CalendarFake(sessions), index_service=IndexFake(sessions, closes)
    )
    return construct_observations(spec, inputs)


def pure_fixture() -> tuple[ObservationJobSpec, PreparedInputs]:
    spec = job()
    closes = dict(zip(DAYS[:5], (100.0, 110.0, 121.0, 110.0, 121.0), strict=True))
    sample = TradeCalendarRange("SSE", DAYS[2], DAYS[4])
    warm = TradeCalendarRange("SSE", DAYS[0], DAYS[1])
    request = IndexDailyRange((CODE,), DAYS[0], DAYS[4])
    inputs = PreparedInputs(
        job_identity(spec),
        (
            CalendarInput(sample, calendar_view(sample, DAYS)),
            CalendarInput(warm, calendar_view(warm, DAYS)),
        ),
        IndexInput(request, index_view(request, DAYS[:5], closes)),
        (),
    )
    return spec, inputs
