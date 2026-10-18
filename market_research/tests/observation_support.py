"""Controlled public Dataset dependencies; no provider network or real cache."""

from collections.abc import Callable
from dataclasses import replace
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any, cast

from data_lake import CoverageResult, EnsureResult
from data_lake.datasets.tushare_equity_index_options import (
    OptionsDailyExport,
    OptionsDailyRange,
    OptionsDailyRow,
    OptionsDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)


def coverage(units: int, complete: bool = True) -> CoverageResult:
    return CoverageResult(units, units if complete else 0, 0 if complete else units, 0, 0, complete)


def ensured(units: int, complete: bool = True) -> EnsureResult:
    return EnsureResult(units, units, 0, 0, 0, 0, complete, ())


def row(
    expiry: date,
    trade: date,
    strike: int = 8000,
    side: str = "CALL",
    product: str = "MO",
    **changes: Any,
) -> OptionsDailyRow:
    symbol = f"{product}{expiry:%y%m}-{'C' if side == 'CALL' else 'P'}-{strike}"
    underlying = {"IO": "000300.SH", "HO": "000016.SH", "MO": "000852.SH"}[product]
    value = OptionsDailyRow(
        contract_code=symbol + ".CFX",
        product_code=product,
        symbol=symbol,
        name="option",
        exchange="CFFEX",
        source_underlying_code="OP" + underlying,
        underlying_index_code=underlying,
        option_type="index option",
        exercise_type="EUROPEAN",
        quote_unit="points",
        settlement_month=expiry.strftime("%Y%m"),
        call_put=side,
        list_date=trade,
        delist_date=max(expiry, trade),
        expiry=expiry,
        last_exercise_date=expiry,
        trade_date=trade,
        last_delivery_date=None,
        per_unit=100.0,
        opt_multiplier=101.0,
        strike=float(strike),
        pre_settle=2.0,
        pre_close=None,
        close=3.0,
        settle=3.1,
        volume=0.0,
        amount=0.0,
        open_interest=4.0,
        open=None,
        high=3.0,
        low=None,
    )
    return replace(value, **changes)


class OptionsDouble:
    def __init__(
        self,
        opens: tuple[date, ...],
        rows: tuple[OptionsDailyRow, ...] = (),
        *,
        complete: bool = True,
    ):
        self.opens = opens
        self.rows = rows
        self.complete = complete
        self.calls: list[tuple[str, OptionsDailyRange]] = []
        self.ensure_hook: Callable[[EnsureResult], EnsureResult] = lambda result: result
        self.export_hook: Callable[[OptionsDailyExport], OptionsDailyExport] = lambda result: result

    def ensure(self, request: OptionsDailyRange) -> EnsureResult:
        self.calls.append(("ensure", request))
        units = sum(request.start_date <= day <= request.end_date for day in self.opens)
        result = self.ensure_hook(ensured(units))
        self.complete = result.complete
        return result

    def export(self, request: OptionsDailyRange) -> OptionsDailyExport:
        self.calls.append(("export", request))
        units = sum(request.start_date <= day <= request.end_date for day in self.opens)
        values = tuple(
            sorted(
                (
                    value
                    for value in self.rows
                    if self.complete
                    and value.product_code in request.product_codes
                    and request.start_date <= value.trade_date <= request.end_date
                ),
                key=lambda value: (value.product_code, value.trade_date, value.contract_code),
            )
        )
        return self.export_hook(
            OptionsDailyExport(
                "tushare_equity_index_options",
                "options_daily",
                2,
                OptionsDailyScope(tuple(request.product_codes)),
                SimpleNamespace(start_date=request.start_date, end_date=request.end_date),
                coverage(units, self.complete),
                values,
            )
        )


class CalendarDouble:
    def __init__(self, opens: tuple[date, ...], *, complete: bool = True):
        self.opens = opens
        self.complete = complete
        self.calls: list[tuple[str, TradeCalendarRange]] = []
        self.ensure_hook: Callable[[EnsureResult], EnsureResult] = lambda result: result
        self.export_hook: Callable[[TradeCalendarExport], TradeCalendarExport] = (
            lambda result: result
        )

    def ensure(self, request: TradeCalendarRange) -> EnsureResult:
        self.calls.append(("ensure", request))
        result = self.ensure_hook(ensured((request.end_date - request.start_date).days + 1))
        self.complete = result.complete
        return result

    def export(self, request: TradeCalendarRange) -> TradeCalendarExport:
        self.calls.append(("export", request))
        units = (request.end_date - request.start_date).days + 1
        records = (
            tuple(
                TradeCalendarRecord(
                    request.exchange,
                    request.start_date + timedelta(days=index),
                    int(request.start_date + timedelta(days=index) in self.opens),
                    None,
                )
                for index in range(units)
            )
            if self.complete
            else ()
        )
        return self.export_hook(
            TradeCalendarExport(
                "tushare_trade_calendar",
                "calendar",
                1,
                cast(Any, SimpleNamespace(exchange=request.exchange)),
                cast(
                    Any, SimpleNamespace(start_date=request.start_date, end_date=request.end_date)
                ),
                coverage(units, self.complete),
                records,
            )
        )
