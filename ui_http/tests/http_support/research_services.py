"""Deterministic public DataLake service fakes; no storage or external network."""

from dataclasses import dataclass
from datetime import date, timedelta

from data_lake import CoverageResult, EnsureResult, OperationError, UnitFailure
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
from market_research.descriptive.observation import DateWindow

SESSIONS = tuple(date(2024, 1, day) for day in (8, 9, 10, 11, 12, 15, 16))
CLOSES = dict(zip(SESSIONS, (100.0, 100.0, 120.0, 80.0, 100.0, 80.0, 100.0), strict=True))


@dataclass(frozen=True)
class CalendarScope:
    exchange: str


class ResearchServices:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.missing: set[date] = set()
        self.nonpositive: set[date] = set()
        self.fail_codes: set[str] = set()
        self.calendar_incomplete = False
        self.calendar_error = False

    def create_calendar(self) -> "ResearchServices":
        self.calls.append(("create_calendar", None))
        return self

    def create_index(self) -> "ResearchServices":
        self.calls.append(("create_index", None))
        return self

    def export(self, request: TradeCalendarRange | IndexDailyRange) -> object:
        self.calls.append(("export", request))
        if isinstance(request, TradeCalendarRange):
            if self.calendar_error:
                raise OperationError(
                    "secret token=FAKE_SECRET C:\\private\\cache.sqlite3 Traceback"
                )
            days = tuple(
                request.start_date + timedelta(days=i)
                for i in range((request.end_date - request.start_date).days + 1)
            )
            rows = tuple(
                TradeCalendarRecord(request.exchange, day, int(day in SESSIONS), None)
                for day in days
            )
            if self.calendar_incomplete:
                rows = rows[:-1]
            return TradeCalendarExport(
                "tushare_trade_calendar",
                "calendar",
                1,
                CalendarScope(request.exchange),  # type: ignore[arg-type]
                DateWindow(request.start_date, request.end_date),  # type: ignore[arg-type]
                CoverageResult(
                    len(days), len(rows), len(days) - len(rows), 0, 0, len(days) == len(rows)
                ),
                rows,
            )
        code = request.index_codes[0]
        if code in self.fail_codes:
            raise OperationError("deliberate unavailable source")
        expected = tuple(day for day in SESSIONS if request.start_date <= day <= request.end_date)
        records = []
        for day in expected:
            if day in self.missing:
                continue
            close = 0.0 if day in self.nonpositive else CLOSES[day]
            records.append(
                IndexDailyRow(
                    code,
                    code[:6],
                    "Synthetic index fixture",
                    "SSE",
                    None,
                    "fixture",
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
            )
        absent = len(expected) - len(records)
        return IndexDailyExport(
            "tushare_index_daily",
            "index_daily",
            1,
            IndexDailyScope(tuple(request.index_codes)),
            DateWindow(request.start_date, request.end_date),
            CoverageResult(len(expected), len(records), absent, 0, 0, absent == 0),
            tuple(records),
        )

    def ensure(self, request: TradeCalendarRange | IndexDailyRange) -> EnsureResult:
        self.calls.append(("ensure", request))
        failures: tuple[UnitFailure, ...]
        if isinstance(request, TradeCalendarRange):
            count = (request.end_date - request.start_date).days + 1
            failures = (UnitFailure((request.exchange, request.end_date), "provider diagnostic"),)
        else:
            expected = tuple(d for d in SESSIONS if request.start_date <= d <= request.end_date)
            count = len(expected)
            failures = tuple(
                UnitFailure(
                    (request.index_codes[0], d),
                    "secret token=FAKE_SECRET C:\\private\\cache.sqlite3",
                )
                for d in expected
                if d in self.missing
            )
        failed = len(failures)
        return EnsureResult(count, count - failed, failed, 0, failed, 0, failed == 0, failures)
