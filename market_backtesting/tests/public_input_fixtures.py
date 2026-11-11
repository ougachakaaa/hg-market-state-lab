"""Published public types/shapes, with an explicitly artificial five-session calendar."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any, cast

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_equity_index_futures import (
    FuturesDailyExport,
    FuturesDailyRow,
    FuturesDailyScope,
)
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRow, IndexDailyScope
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord
from market_backtesting.cases.futures_roll_long import (
    FuturesRollRequest,
    PublicInputExports,
    StrategyProfile,
    create_futures_roll_service,
)

DAYS = (
    date(2025, 2, 17),
    date(2025, 3, 20),
    date(2025, 3, 21),
    date(2025, 3, 24),
    date(2025, 3, 25),
)
MONTHS = (
    ("202502", "202503", "202506", "202509"),
    ("202503", "202504", "202506", "202509"),
    ("202503", "202504", "202506", "202509"),
    ("202504", "202505", "202506", "202509"),
    ("202504", "202505", "202506", "202509"),
)
LISTED = {"202504": date(2025, 2, 18), "202505": date(2025, 3, 22)}
DELISTED = {
    "202502": DAYS[0],
    "202503": DAYS[2],
    "202504": date(2025, 4, 18),
    "202505": date(2025, 5, 16),
    "202506": date(2025, 6, 20),
    "202509": date(2025, 9, 19),
}


# Calendar scope/window constructors are not facade exports. These frozen fixtures
# implement exactly the documented public semantic shapes, without private imports.
@dataclass(frozen=True)
class CalendarScopeShape:
    exchange: str


@dataclass(frozen=True)
class WindowShape:
    start_date: date
    end_date: date


def request(profile: StrategyProfile = "expiry_to_M1_v1") -> FuturesRollRequest:
    return FuturesRollRequest("IM", DAYS[0], DAYS[-1], profile)


def coverage(requested: int, successful: int | None = None) -> CoverageResult:
    count = requested if successful is None else successful
    return CoverageResult(requested, count, requested - count, 0, 0, requested == count)


def public_exports() -> PublicInputExports:
    window = WindowShape(DAYS[0], DAYS[-1])
    count = (DAYS[-1] - DAYS[0]).days + 1
    calendar = TradeCalendarExport(
        "tushare_trade_calendar",
        "calendar",
        1,
        cast(Any, CalendarScopeShape("CFFEX")),
        cast(Any, window),
        coverage(count),
        tuple(
            TradeCalendarRecord("CFFEX", day, int(day in DAYS), None)
            for day in (DAYS[0] + timedelta(days=i) for i in range(count))
        ),
    )
    prices = (
        {"202503": 5900.0},
        {"202503": 5950.0},
        {"202503": 6000.0, "202504": 6010.0, "202506": 6025.0},
        {"202504": 6030.0, "202506": 6030.0},
        {"202504": 6020.0, "202506": 6020.0},
    )
    rows = []
    for day, months, closes in zip(DAYS, MONTHS, prices, strict=True):
        for month in months:
            close = closes.get(month, 6000.0)
            symbol = "IM" + month[2:]
            rows.append(
                FuturesDailyRow(
                    contract_code=symbol + ".CFX",
                    product_code="IM",
                    symbol=symbol,
                    name=symbol,
                    exchange="CFFEX",
                    underlying_index_code="000852.SH",
                    trade_unit="lot",
                    quote_unit="point",
                    delivery_month=month,
                    list_date=LISTED.get(month, date(2025, 1, 1)),
                    delist_date=DELISTED[month],
                    last_delivery_date=DELISTED[month],
                    trade_date=day,
                    multiplier=200.0,
                    per_unit=1.0,
                    pre_close=close,
                    pre_settle=close,
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    settle=close,
                    close_change_from_pre_settle=0.0,
                    settle_change_from_pre_settle=0.0,
                    volume=0.0,
                    amount=0.0,
                    open_interest=0.0,
                    open_interest_change=0.0,
                    delivery_settlement_price=None,
                )
            )
    futures = FuturesDailyExport(
        "tushare_equity_index_futures",
        "futures_daily",
        2,
        FuturesDailyScope(("IM",)),
        window,
        coverage(len(DAYS)),
        tuple(rows),
    )
    index = IndexDailyExport(
        "tushare_index_daily",
        "index_daily",
        1,
        IndexDailyScope(("000852.SH",)),
        window,
        coverage(len(DAYS)),
        tuple(
            IndexDailyRow(
                "000852.SH",
                "000852",
                "中证1000",
                "SSE",
                None,
                None,
                day,
                close,
                close,
                close,
                close,
                close,
                0.0,
                0.0,
                0.0,
                0.0,
            )
            for day, close in zip(DAYS, (6000.0, 6060.0, 6030.0, 6090.0, 6075.0), strict=True)
        ),
    )
    return PublicInputExports(calendar, futures, index)


class FakeService:
    def __init__(self, *exports: Any, ensure_result: EnsureResult | None = None) -> None:
        self.exports = list(exports)
        self.calls: list[tuple[str, Any]] = []
        self.ensure_result = ensure_result
        self.error: Exception | None = None
        self.last_export: Any = None

    def export(self, request: Any) -> Any:
        self.calls.append(("export", request))
        if self.error is not None:
            raise self.error
        self.last_export = self.exports.pop(0) if len(self.exports) > 1 else self.exports[0]
        return self.last_export

    def ensure(self, request: Any) -> EnsureResult:
        self.calls.append(("ensure", request))
        if self.error is not None:
            raise self.error
        if self.ensure_result is not None:
            return self.ensure_result
        final = (
            self.sse_exports[0]  # type: ignore[attr-defined]
            if getattr(request, "exchange", None) == "SSE"
            else self.exports[0]
        )
        before = self.last_export
        units = before.coverage.requested_units
        already = before.coverage.successful_units
        attempted = units - already
        succeeded = final.coverage.successful_units - already
        failed = attempted - succeeded
        identity = (
            request.exchange
            if hasattr(request, "exchange")
            else request.product_codes[0]
            if hasattr(request, "product_codes")
            else request.index_codes[0]
        )
        return EnsureResult(
            units,
            already,
            attempted,
            succeeded,
            failed,
            len(final.records) - len(before.records),
            final.coverage.complete,
            tuple(
                UnitFailure(
                    (identity, request.end_date - timedelta(days=i)), "synthetic source incomplete"
                )
                for i in range(failed)
            ),
        )

    def coverage(self, request: Any) -> Any:
        raise AssertionError("Export already supplies coverage")


class FakeCalendar(FakeService):
    def __init__(self, view: Any) -> None:
        super().__init__(view)
        self.sse_exports = [
            replace(
                view,
                scope=replace(view.scope, exchange="SSE"),
                records=tuple(replace(row, exchange="SSE") for row in view.records),
            )
        ]

    def export(self, request: Any) -> Any:
        if request.exchange != "SSE":
            return super().export(request)
        self.calls.append(("export", request))
        self.last_export = (
            self.sse_exports.pop(0) if len(self.sse_exports) > 1 else self.sse_exports[0]
        )
        return self.last_export


def fake_services(
    exports: PublicInputExports | None = None,
) -> tuple[Any, FakeCalendar, FakeService, FakeService]:
    views = public_exports() if exports is None else exports
    calendar = FakeCalendar(views.calendar_cffex)
    futures = FakeService(views.futures)
    index = FakeService(views.index)
    return (
        create_futures_roll_service(calendar=calendar, futures=futures, index=index),
        calendar,
        futures,
        index,
    )
