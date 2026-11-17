"""Synthetic fixtures for the two exact public services; never use real caches."""

from dataclasses import fields, replace
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from data_lake import CoverageResult
from data_lake.datasets.tushare_equity_index_futures import (
    FuturesDailyExport,
    FuturesDailyRange,
    FuturesDailyRow,
    FuturesDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)
from market_research.descriptive.cases.futures_calendar_spread import prepare_inputs

DAY = date(2024, 10, 18)
AFTER = date(2024, 10, 21)
BEFORE_MONTHS = ("202410", "202411", "202412", "202503")
AFTER_MONTHS = ("202411", "202412", "202503", "202506")
UNDERLYING = {"IF": "000300.SH", "IH": "000016.SH", "IC": "000905.SH", "IM": "000852.SH"}


def coverage(n: int, missing: int = 0) -> CoverageResult:
    return CoverageResult(n, n - missing, missing, 0, 0, missing == 0)


def future(day: date, month: str, close: float = 110.0, product: str = "IM") -> FuturesDailyRow:
    values = {field.name: 1.0 for field in fields(FuturesDailyRow)}
    expiry = date(int(month[:4]), int(month[4:]), 18)
    values.update(
        contract_code=product + month[2:] + ".CFX",
        product_code=product,
        symbol=product + month[2:],
        name="synthetic",
        exchange="CFFEX",
        underlying_index_code=UNDERLYING[product],
        trade_unit="lot",
        quote_unit="points",
        delivery_month=month,
        list_date=date(2023, 1, 1),
        delist_date=expiry,
        last_delivery_date=expiry + timedelta(days=1),
        trade_date=day,
        close=close,
        delivery_settlement_price=None,
    )
    return FuturesDailyRow(**values)


class Services:
    """Each call returns its final public export; unexpected operations fail the test."""

    def __init__(self, start: date = DAY, end: date = DAY, product: str = "IM") -> None:
        self.start, self.end, self.product = start, end, product
        self.calls: list[Any] = []
        self.reference_calls: list[Any] = []
        self.errors: dict[str, Exception] = {}
        dates = tuple(start + timedelta(days=i) for i in range((end - start).days + 1))
        window = SimpleNamespace(start_date=start, end_date=end)
        self.calendar = TradeCalendarExport(
            "tushare_trade_calendar",
            "calendar",
            1,
            SimpleNamespace(exchange="CFFEX"),
            window,
            coverage(len(dates)),
            tuple(TradeCalendarRecord("CFFEX", day, int(day.weekday() < 5), None) for day in dates),
        )
        self.futures = FuturesDailyExport(
            "tushare_equity_index_futures",
            "futures_daily",
            2,
            FuturesDailyScope((product,)),
            window,
            coverage(sum(r.is_open for r in self.calendar.records)),
            tuple(
                sorted(
                    (
                        future(day, month, close, product)
                        for day in dates
                        if day.weekday() < 5
                        for month, close in zip(
                            BEFORE_MONTHS if day <= DAY else AFTER_MONTHS,
                            (110.0, 100.0, 120.0, 110.0),
                            strict=True,
                        )
                    ),
                    key=lambda r: (r.product_code, r.trade_date, r.contract_code),
                )
            ),
        )

    def export(self, request: TradeCalendarRange | FuturesDailyRange):
        if isinstance(request, TradeCalendarRange) and request.exchange == "SSE":
            self.reference_calls.append(("sse_calendar", request))
            # Existing core fixtures explicitly prove independent SSE closure.
            return replace(
                self.calendar, scope=SimpleNamespace(exchange="SSE"),
                window=SimpleNamespace(start_date=request.start_date, end_date=request.end_date),
                coverage=coverage(1),
                records=(TradeCalendarRecord("SSE", request.start_date, 0, None),),
            )
        name = "calendar" if isinstance(request, TradeCalendarRange) else "futures"
        self.calls.append((name, request))
        if name in self.errors:
            raise self.errors[name]
        return getattr(self, name)

    def ensure(self, request):
        raise AssertionError("Ensure is forbidden")

    def coverage(self, request):
        raise AssertionError("Separate coverage is forbidden")

    def prepare(self):
        return prepare_inputs(
            self.product, self.start, self.end, calendar_service=self, futures_service=self
        )

    def set_rows(self, rows):
        self.futures = replace(
            self.futures,
            records=tuple(
                sorted(rows, key=lambda r: (r.product_code, r.trade_date, r.contract_code))
            ),
        )
