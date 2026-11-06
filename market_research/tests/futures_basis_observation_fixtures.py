"""Small public-service fakes; no provider, repositories or real market facts."""

from dataclasses import fields, replace
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any, cast

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRow
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord
from market_research.descriptive.cases.futures_basis import FuturesBasisRequest, prepare_inputs

DAY = date(2024, 10, 18)
AFTER = date(2024, 10, 21)
REQUEST = FuturesBasisRequest("IM", DAY, AFTER)


def proof(n: int, missing: int = 0) -> CoverageResult:
    return CoverageResult(n, n - missing, missing, 0, 0, missing == 0)


def future(day: date, month: str, close: float = 110.0) -> FuturesDailyRow:
    values: dict[str, Any] = {field.name: 1.0 for field in fields(FuturesDailyRow)}
    values.update(
        contract_code="IM" + month[2:] + ".CFX",
        product_code="IM",
        symbol="IM" + month[2:],
        name="synthetic",
        exchange="CFFEX",
        underlying_index_code="000852.SH",
        trade_unit="lot",
        quote_unit="points",
        delivery_month=month,
        list_date=date(2024, 1, 1),
        delist_date=DAY if month == "202410" else date(2025, 12, 31),
        last_delivery_date=date(2026, 1, 1),
        trade_date=day,
        close=close,
    )
    return FuturesDailyRow(**values)


class Services:
    def __init__(self, request: FuturesBasisRequest = REQUEST) -> None:
        self.request = request
        self.calls: list[tuple[str, str]] = []
        days = tuple(
            request.start_date + timedelta(days=i)
            for i in range((request.end_date - request.start_date).days + 1)
        )
        self.calendars = {
            exchange: TradeCalendarExport(
                "tushare_trade_calendar",
                "calendar",
                1,
                cast(Any, SimpleNamespace(exchange=exchange)),
                cast(
                    Any, SimpleNamespace(start_date=request.start_date, end_date=request.end_date)
                ),
                proof(len(days)),
                tuple(TradeCalendarRecord(exchange, d, int(d.weekday() < 5), None) for d in days),
            )
            for exchange in ("CFFEX", "SSE")
        }
        sessions = tuple(d for d in days if d.weekday() < 5)
        rows = tuple(
            future(d, month)
            for d in sessions
            for month in (
                ("202410", "202411", "202412", "202503")
                if d <= DAY
                else ("202411", "202412", "202503", "202506")
            )
        )
        window = SimpleNamespace(start_date=request.start_date, end_date=request.end_date)
        self.futures = FuturesDailyExport(
            "tushare_equity_index_futures",
            "futures_daily",
            2,
            SimpleNamespace(product_codes=("IM",)),
            window,
            proof(len(sessions)),
            rows,
        )
        self.index = IndexDailyExport(
            "tushare_index_daily",
            "index_daily",
            1,
            SimpleNamespace(index_codes=("000852.SH",)),
            window,
            proof(len(sessions)),
            tuple(
                IndexDailyRow(
                    "000852.SH",
                    "000852",
                    "synthetic",
                    "SSE",
                    None,
                    None,
                    d,
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                )
                for d in sessions
            ),
        )
        self.ensure_results: dict[str, EnsureResult] = {}
        self.after_ensure: dict[str, Any] = {}

    def export(self, request):
        name = getattr(
            request, "exchange", "futures" if hasattr(request, "product_codes") else "index"
        )
        self.calls.append((name, "export"))
        return self.calendars[name] if name in self.calendars else getattr(self, name)

    def ensure(self, request):
        name = getattr(
            request, "exchange", "futures" if hasattr(request, "product_codes") else "index"
        )
        self.calls.append((name, "ensure"))
        value = self.export_value(name)
        n, success = value.coverage.requested_units, value.coverage.successful_units
        if name in self.after_ensure:
            if name in self.calendars:
                self.calendars[name] = self.after_ensure[name]
            else:
                setattr(self, name, self.after_ensure[name])
        if name in self.ensure_results:
            return self.ensure_results[name]
        code = name if name in self.calendars else "IM" if name == "futures" else "000852.SH"
        dates = tuple(
            row.cal_date
            for row in self.calendars["CFFEX" if name == "futures" else "SSE"].records
            if row.is_open
        )
        missing = [
            day
            for day in dates
            if day not in {getattr(r, "trade_date", None) for r in value.records}
        ]
        failures = tuple(UnitFailure((code, day), "synthetic unavailable") for day in missing)
        return EnsureResult(n, success, n - success, 0, n - success, 0, False, failures)

    def export_value(self, name):
        return self.calendars[name] if name in self.calendars else getattr(self, name)

    def prepare(self):
        return prepare_inputs(
            self.request, calendar_service=self, futures_service=self, index_service=self
        )

    def missing_index(self, day=DAY):
        self.index = replace(
            self.index,
            coverage=proof(self.index.coverage.requested_units, 1),
            records=tuple(row for row in self.index.records if row.trade_date != day),
        )
