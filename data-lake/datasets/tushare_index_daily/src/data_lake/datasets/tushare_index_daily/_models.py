"""Dataset-owned transport-neutral semantic values."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from data_lake import ExportEnvelope, InvalidRequestError


@dataclass(frozen=True)
class IndexDailyRange:
    index_codes: Sequence[str]
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        values = self.index_codes
        if isinstance(values, str | bytes) or not isinstance(values, Sequence) or not values:
            raise InvalidRequestError("selection must be a nonempty sequence of canonical codes")
        if any(
            not isinstance(code, str)
            or not (re.fullmatch(r"[0-9]{6}\.(SH|SZ|CSI)", code) is not None)
            for code in values
        ):
            raise InvalidRequestError("Invalid canonical code")
        if type(self.start_date) is not date or type(self.end_date) is not date:
            raise InvalidRequestError("Window requires dates, not timestamps")
        if self.start_date > self.end_date:
            raise InvalidRequestError("Window is inverted")
        if self.end_date > datetime.now(timezone(timedelta(hours=8))).date():
            raise InvalidRequestError("Window cannot extend beyond today in Asia/Shanghai")
        object.__setattr__(self, "index_codes", tuple(sorted(set(values))))


@dataclass(frozen=True)
class IndexDailyScope:
    index_codes: tuple[str, ...]


@dataclass(frozen=True)
class DailyWindow:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class IndexDailyRow:
    index_code: str
    symbol: str
    name: str
    market: str
    publisher: str | None
    category: str | None
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_change: float
    volume: float
    amount: float


@dataclass(frozen=True)
class IndexDailyExport(ExportEnvelope):
    records: tuple[IndexDailyRow, ...]
