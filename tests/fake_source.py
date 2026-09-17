"""A fake Tushare Source used by tests.

Tests must not depend on the real Tushare API, so every collector test
injects this in-memory Source instead.
"""

from __future__ import annotations

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


class FakeTushareApi:
    """In-memory stand-in for the Tushare pro client.

    Records the calls it receives so tests can assert the target trade date
    and requested codes, and returns empty frames when asked to.
    """

    def __init__(
        self,
        index_frames: dict[str, pd.DataFrame] | None = None,
        stock_frame: pd.DataFrame | None = None,
    ) -> None:
        self.index_frames = index_frames if index_frames is not None else {}
        self.stock_frame = stock_frame if stock_frame is not None else pd.DataFrame()
        self.index_calls: list[dict[str, str]] = []
        self.daily_calls: list[dict[str, str]] = []

    def index_daily(self, *, ts_code: str, trade_date: str) -> pd.DataFrame:
        self.index_calls.append({"ts_code": ts_code, "trade_date": trade_date})
        return self.index_frames.get(ts_code, pd.DataFrame())

    def daily(self, *, trade_date: str) -> pd.DataFrame:
        self.daily_calls.append({"trade_date": trade_date})
        return self.stock_frame


def index_frames_for_all(
    codes: tuple[str, ...], trade_date: str = "20260917"
) -> dict[str, pd.DataFrame]:
    """Build an ``index_daily`` frame for every code in the universe."""
    return {
        code: index_daily_frame(code, trade_date, close=100.0 + offset)
        for offset, code in enumerate(codes)
    }
