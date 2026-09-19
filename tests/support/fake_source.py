"""A fake Tushare Source used by tests.

Tests must not depend on the real Tushare API, so every collector test
injects this in-memory Source instead.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

INDEX_FIELDS = (
    "ts_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_chg",
    "vol",
    "amount",
)

OPTION_BASIC_FIELDS = (
    "ts_code",
    "symbol",
    "exchange",
    "name",
    "per_unit",
    "opt_code",
    "opt_type",
    "call_put",
    "exercise_type",
    "exercise_price",
    "opt_multiplier",
    "s_month",
    "maturity_date",
    "list_price",
    "list_date",
    "delist_date",
    "last_edate",
    "last_ddate",
    "quote_unit",
    "min_price_chg",
)

OPTION_DAILY_FIELDS = (
    "ts_code",
    "trade_date",
    "exchange",
    "pre_settle",
    "pre_close",
    "open",
    "high",
    "low",
    "close",
    "settle",
    "vol",
    "amount",
    "oi",
)

FUTURES_BASIC_FIELDS = (
    "ts_code",
    "symbol",
    "exchange",
    "name",
    "fut_code",
    "multiplier",
    "trade_unit",
    "per_unit",
    "quote_unit",
    "quote_unit_desc",
    "d_mode_desc",
    "list_date",
    "delist_date",
    "d_month",
    "last_ddate",
)

FUTURES_DAILY_FIELDS = (
    "ts_code",
    "trade_date",
    "pre_close",
    "pre_settle",
    "open",
    "high",
    "low",
    "close",
    "settle",
    "change1",
    "change2",
    "vol",
    "amount",
    "oi",
    "oi_chg",
)

# Tushare option codes carry the exchange as a suffix, not as ``CFFEX``.
OPTION_EXCHANGE_SUFFIXES = {"CFE": "CFFEX", "SH": "SSE", "SZ": "SZSE"}


def source_date(value: Any) -> str:
    """Normalize a frame's date value to Source form ``YYYYMMDD``."""
    return pd.Timestamp(str(value)).strftime("%Y%m%d")


def business_days(start: str, end: str) -> list[str]:
    """Build synthetic trading days in Source form for an ISO date range.

    The fake Source has no trading calendar, so weekdays stand in for trading
    days: enough for the history-completeness checks without depending on a
    specific exchange calendar.
    """
    current = date.fromisoformat(start)
    last = date.fromisoformat(end)
    days: list[str] = []
    while current <= last:
        if current.weekday() < 5:
            days.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return days


def as_source_frame(
    rows: list[dict[str, Any]], fields: tuple[str, ...], date_fields: tuple[str, ...]
) -> pd.DataFrame:
    """Build a Source-shaped frame, keeping its date facts as Source strings.

    The ``DataFrame`` constructor parses date-like strings into datetime
    columns, while the real Tushare responses carry them as plain strings
    (``YYYYMMDD``). Building per column keeps the date facts in Source form.
    """
    columns: dict[str, pd.Series] = {}
    for field in fields:
        if field in date_fields:
            values = ["" if row.get(field) is None else str(row.get(field)) for row in rows]
            columns[field] = pd.Series(values, dtype=object)
        else:
            columns[field] = pd.Series([row.get(field) for row in rows])
    return pd.DataFrame(columns)


def index_daily_frame(
    ts_code: str, trade_date: str = "20260917", close: float = 100.0
) -> pd.DataFrame:
    """Build one Tushare ``index_daily`` row (Source date form ``YYYYMMDD``)."""
    return pd.DataFrame(
        [
            {
                "ts_code": ts_code,
                "trade_date": trade_date,
                "open": close - 1.0,
                "high": close + 2.0,
                "low": close - 3.0,
                "close": close,
                "pre_close": close - 0.5,
                "change": 0.5,
                "pct_chg": 0.5,
                "vol": 1000.0,
                "amount": 2000.0,
            }
        ]
    )


def index_history_frame(
    ts_code: str, trade_dates: list[str], close: float = 100.0
) -> pd.DataFrame:
    """Build a multi-day Tushare ``index_daily`` history for one index."""
    rows = [
        index_daily_frame(ts_code, trade_date, close=close + offset).to_dict(orient="records")[0]
        for offset, trade_date in enumerate(trade_dates)
    ]
    return as_source_frame(rows, INDEX_FIELDS, ("trade_date",))


def stock_daily_frame(trade_date: str = "20260917") -> pd.DataFrame:
    """Build Tushare ``daily`` rows for the given Source date."""
    rows = [
        {
            "ts_code": "000001.SZ",
            "trade_date": trade_date,
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "pre_close": 10.0,
            "change": 0.5,
            "pct_chg": 5.0,
            "vol": 100.0,
            "amount": 50.0,
        },
        {
            "ts_code": "600000.SH",
            "trade_date": trade_date,
            "open": 8.0,
            "high": 8.1,
            "low": 7.5,
            "close": 7.6,
            "pre_close": 8.2,
            "change": -0.6,
            "pct_chg": -7.3171,
            "vol": 200.0,
            "amount": 60.0,
        },
        {
            "ts_code": "000002.SZ",
            "trade_date": trade_date,
            "open": 5.0,
            "high": 5.0,
            "low": 5.0,
            "close": 5.0,
            "pre_close": 5.0,
            "change": 0.0,
            "pct_chg": 0.0,
            "vol": 10.0,
            "amount": 5.0,
        },
    ]
    return pd.DataFrame(rows)


def option_basic_frame(contracts: list[dict[str, Any]]) -> pd.DataFrame:
    """Build Tushare ``opt_basic`` rows from partial contract facts."""
    rows = [
        {field: contract.get(field) for field in OPTION_BASIC_FIELDS} for contract in contracts
    ]
    return as_source_frame(
        rows, OPTION_BASIC_FIELDS, ("maturity_date", "list_date", "delist_date", "last_edate")
    )


def mo_option_contract(
    ts_code: str,
    *,
    call_put: str,
    exercise_price: float = 7000.0,
    opt_code: str = "OP000852.SH",
    list_date: str | None = "20260622",
    delist_date: str | None = "20260925",
) -> dict[str, Any]:
    """Build one MO option contract fact in Source date form.

    ``opt_code`` follows the real Tushare convention: the underlying index of the
    option in ``OP`` + index-code form, ``OP000852.SH`` for the CSI1000 MO options.
    """
    return {
        "ts_code": ts_code,
        "symbol": ts_code.split(".")[0],
        "exchange": "CFFEX",
        "name": ts_code.split(".")[0],
        "per_unit": 100.0,
        "opt_code": opt_code,
        "opt_type": "1",
        "call_put": call_put,
        "exercise_type": "E",
        "exercise_price": exercise_price,
        "opt_multiplier": 100.0,
        "s_month": "2609",
        "maturity_date": "20260925",
        "list_price": 100.0,
        "list_date": list_date,
        "delist_date": delist_date,
        "last_edate": "20260925",
        "last_ddate": "20260930",
        "quote_unit": "元",
        "min_price_chg": 0.2,
    }


def option_daily_frame(
    trade_date: str = "20260917", contracts: list[str] | None = None
) -> pd.DataFrame:
    """Build Tushare ``opt_daily`` rows for the given contracts and Source date."""
    rows = [
        {
            "ts_code": ts_code,
            "trade_date": trade_date,
            "exchange": OPTION_EXCHANGE_SUFFIXES.get(ts_code.rsplit(".", 1)[-1], ""),
            "pre_settle": 100.0,
            "pre_close": 101.0,
            "open": 102.0,
            "high": 103.0,
            "low": 99.0,
            "close": 100.5,
            "settle": 100.6,
            "vol": 12.0,
            "amount": 1200.0,
            "oi": 340.0,
        }
        for ts_code in (contracts if contracts is not None else [])
    ]
    return as_source_frame(rows, OPTION_DAILY_FIELDS, ("trade_date",))


def futures_basic_frame(contracts: list[dict[str, Any]]) -> pd.DataFrame:
    """Build Tushare ``fut_basic`` rows from partial contract facts."""
    rows = [
        {field: contract.get(field) for field in FUTURES_BASIC_FIELDS} for contract in contracts
    ]
    return as_source_frame(rows, FUTURES_BASIC_FIELDS, ("list_date", "delist_date", "last_ddate"))


def im_contract(
    ts_code: str,
    *,
    list_date: str | None,
    delist_date: str | None,
    name: str | None = None,
    fut_code: str = "IM",
    exchange: str = "CFFEX",
) -> dict[str, Any]:
    """Build one IM futures contract fact in Source date form."""
    return {
        "ts_code": ts_code,
        "symbol": ts_code.split(".")[0],
        "exchange": exchange,
        "name": name if name is not None else f"中证1000股指期货{ts_code.split('.')[0]}",
        "fut_code": fut_code,
        "multiplier": 200.0,
        "trade_unit": "元/点",
        "per_unit": 200.0,
        "quote_unit": "点",
        "quote_unit_desc": "0.2点",
        "d_mode_desc": "现金交割",
        "list_date": list_date,
        "delist_date": delist_date,
        "d_month": ts_code[2:6],
        "last_ddate": delist_date,
    }


def futures_daily_frame(
    ts_code: str, trade_dates: list[str], close: float = 6000.0
) -> pd.DataFrame:
    """Build Tushare ``fut_daily`` rows for one contract over several days."""
    rows = [
        {
            "ts_code": ts_code,
            "trade_date": trade_date,
            "pre_close": close + offset,
            "pre_settle": close + offset + 1.0,
            "open": close + offset + 2.0,
            "high": close + offset + 3.0,
            "low": close + offset - 3.0,
            "close": close + offset,
            "settle": close + offset + 0.5,
            "change1": 1.0,
            "change2": 1.5,
            "vol": 5000.0,
            "amount": 300000.0,
            "oi": 90000.0,
            "oi_chg": -120.0,
        }
        for offset, trade_date in enumerate(trade_dates)
    ]
    return as_source_frame(rows, FUTURES_DAILY_FIELDS, ("trade_date",))


class FakeTushareApi:
    """In-memory stand-in for the Tushare pro client.

    Records the calls it receives so tests can assert the requested dates and
    codes, and returns empty frames when asked for something it does not hold.
    """

    def __init__(
        self,
        index_frames: dict[str, pd.DataFrame] | None = None,
        stock_frame: pd.DataFrame | None = None,
        option_basic: pd.DataFrame | None = None,
        option_daily: pd.DataFrame | None = None,
        futures_basic: pd.DataFrame | None = None,
        futures_daily: dict[str, pd.DataFrame] | None = None,
    ) -> None:
        self.index_frames = index_frames if index_frames is not None else {}
        self.stock_frame = stock_frame if stock_frame is not None else pd.DataFrame()
        self.option_basic = option_basic if option_basic is not None else pd.DataFrame()
        self.option_daily = option_daily if option_daily is not None else pd.DataFrame()
        self.futures_basic = futures_basic if futures_basic is not None else pd.DataFrame()
        self.futures_daily = futures_daily if futures_daily is not None else {}
        self.index_calls: list[dict[str, str]] = []
        self.daily_calls: list[dict[str, str]] = []
        self.opt_basic_calls: list[dict[str, str]] = []
        self.opt_daily_calls: list[dict[str, str]] = []
        self.fut_basic_calls: list[dict[str, str]] = []
        self.fut_daily_calls: list[dict[str, str]] = []

    def index_daily(
        self,
        *,
        ts_code: str,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        call: dict[str, str] = {"ts_code": ts_code}
        if trade_date is not None:
            call["trade_date"] = trade_date
        if start_date is not None:
            call["start_date"] = start_date
        if end_date is not None:
            call["end_date"] = end_date
        self.index_calls.append(call)
        frame = self.index_frames.get(ts_code, pd.DataFrame())
        return self._slice(frame, "trade_date", trade_date, start_date, end_date)

    def daily(self, *, trade_date: str) -> pd.DataFrame:
        self.daily_calls.append({"trade_date": trade_date})
        return self.stock_frame

    def opt_basic(
        self, *, exchange: str, list_date: str | None = None, fields: str | None = None
    ) -> pd.DataFrame:
        self.opt_basic_calls.append({"exchange": exchange, "list_date": list_date or ""})
        return self.option_basic

    def opt_daily(
        self,
        *,
        trade_date: str | None = None,
        exchange: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        self.opt_daily_calls.append(
            {
                "trade_date": trade_date or "",
                "exchange": exchange or "",
                "start_date": start_date or "",
            }
        )
        frame = self.option_daily
        if exchange is not None and not frame.empty:
            frame = frame[frame["exchange"] == exchange]
        return self._slice(frame, "trade_date", trade_date, start_date, end_date)

    def fut_basic(
        self,
        *,
        exchange: str,
        fut_type: str | None = None,
        fut_code: str | None = None,
        fields: str | None = None,
    ) -> pd.DataFrame:
        self.fut_basic_calls.append(
            {"exchange": exchange, "fut_type": fut_type or "", "fut_code": fut_code or ""}
        )
        return self.futures_basic

    def fut_daily(
        self,
        *,
        ts_code: str | None = None,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        self.fut_daily_calls.append(
            {
                "ts_code": ts_code or "",
                "trade_date": trade_date or "",
                "start_date": start_date or "",
                "end_date": end_date or "",
            }
        )
        frame = self.futures_daily.get(ts_code or "", pd.DataFrame())
        return self._slice(frame, "trade_date", trade_date, start_date, end_date)

    @staticmethod
    def _slice(
        frame: pd.DataFrame,
        date_field: str,
        trade_date: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> pd.DataFrame:
        """Return the Source rows of the requested trade date or date range."""
        if frame.empty:
            return frame
        source_dates = frame[date_field].map(source_date)
        if trade_date is not None:
            return frame[source_dates == trade_date]
        if start_date is not None and end_date is not None:
            return frame[(source_dates >= start_date) & (source_dates <= end_date)]
        return frame


def index_frames_for_all(
    codes: tuple[str, ...], trade_date: str = "20260917"
) -> dict[str, pd.DataFrame]:
    """Build an ``index_daily`` frame for every code in the universe."""
    return {
        code: index_daily_frame(code, trade_date, close=100.0 + offset)
        for offset, code in enumerate(codes)
    }


# --------------------------------------------------------------------------
# One complete CSI1000 5-day analysis scenario.
#
# The Data Service CLI tests and the Raw-file tests both need a fake Source that
# can serve every stage of ``csi1000-5d-analysis``, so the scenario lives here.
# The window bounds cover the downstream 120-trading-day underlying window with
# room to spare, and every IM daily fact fills its contract's whole effective
# range.
# --------------------------------------------------------------------------

CSI1000_TARGET_DATE = "2026-09-17"
CSI1000_INDEX_CODE = "000852.SH"
CSI1000_INDEX_SOURCE_DATES = business_days("2026-01-20", CSI1000_TARGET_DATE)
CSI1000_MO_CONTRACTS = [
    mo_option_contract("MO2609-C-7000.CFE", exercise_price=7000.0, call_put="C"),
    mo_option_contract("MO2609-P-7000.CFE", exercise_price=7000.0, call_put="P"),
]
CSI1000_MO_CODES = [str(contract["ts_code"]) for contract in CSI1000_MO_CONTRACTS]
CSI1000_IM_CONTRACTS = [
    im_contract("IM2609.CFE", list_date="20260817", delist_date="20260918"),
]
CSI1000_IM_DAILY_DATES = {
    "IM2609.CFE": business_days("2026-08-17", CSI1000_TARGET_DATE),
}


def csi1000_5d_analysis_api() -> FakeTushareApi:
    """Build one fake Source that can serve every stage of the scenario."""
    return FakeTushareApi(
        index_frames={
            CSI1000_INDEX_CODE: index_history_frame(
                CSI1000_INDEX_CODE, CSI1000_INDEX_SOURCE_DATES
            )
        },
        option_basic=option_basic_frame(CSI1000_MO_CONTRACTS),
        option_daily=option_daily_frame("20260917", CSI1000_MO_CODES),
        futures_basic=futures_basic_frame(CSI1000_IM_CONTRACTS),
        futures_daily={
            ts_code: futures_daily_frame(ts_code, trade_dates)
            for ts_code, trade_dates in CSI1000_IM_DAILY_DATES.items()
        },
    )
