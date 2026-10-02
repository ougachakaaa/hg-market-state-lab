"""Dataset-owned transport-neutral semantic values."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from data_lake import ExportEnvelope, InvalidRequestError


@dataclass(frozen=True)
class FuturesDailyRange:
    product_codes: Sequence[str]
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        values = self.product_codes
        if isinstance(values, str | bytes) or not isinstance(values, Sequence) or not values:
            raise InvalidRequestError("selection must be a nonempty sequence of canonical codes")
        if any(
            not isinstance(code, str) or code not in ("IF", "IH", "IC", "IM") for code in values
        ):
            raise InvalidRequestError("Invalid canonical code")
        if type(self.start_date) is not date or type(self.end_date) is not date:
            raise InvalidRequestError("Window requires dates, not timestamps")
        if self.start_date > self.end_date:
            raise InvalidRequestError("Window is inverted")
        object.__setattr__(self, "product_codes", tuple(sorted(set(values))))


@dataclass(frozen=True)
class FuturesDailyScope:
    product_codes: tuple[str, ...]


@dataclass(frozen=True)
class DailyWindow:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class FuturesDailyRow:
    contract_code: str
    product_code: str
    symbol: str
    name: str
    exchange: str
    underlying_index_code: str
    trade_unit: str
    quote_unit: str
    delivery_month: str
    list_date: date
    delist_date: date
    last_delivery_date: date
    trade_date: date
    multiplier: float
    per_unit: float
    pre_close: float
    pre_settle: float
    open: float
    high: float
    low: float
    close: float
    settle: float
    close_change_from_pre_settle: float
    settle_change_from_pre_settle: float
    volume: float
    amount: float
    open_interest: float
    open_interest_change: float
    delivery_settlement_price: float | None


@dataclass(frozen=True)
class FuturesDailyExport(ExportEnvelope):
    records: tuple[FuturesDailyRow, ...]
