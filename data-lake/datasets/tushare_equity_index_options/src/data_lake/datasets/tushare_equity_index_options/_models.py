"""Dataset-owned transport-neutral semantic values."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from data_lake import ExportEnvelope, InvalidRequestError


@dataclass(frozen=True)
class OptionsDailyRange:
    product_codes: Sequence[str]
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        values = self.product_codes
        if isinstance(values, str | bytes) or not isinstance(values, Sequence) or not values:
            raise InvalidRequestError("selection must be a nonempty sequence of canonical codes")
        if any(not isinstance(code, str) or code not in ("IO", "HO", "MO") for code in values):
            raise InvalidRequestError("Invalid canonical code")
        if type(self.start_date) is not date or type(self.end_date) is not date:
            raise InvalidRequestError("Window requires dates, not timestamps")
        if self.start_date > self.end_date:
            raise InvalidRequestError("Window is inverted")
        object.__setattr__(self, "product_codes", tuple(sorted(set(values))))


@dataclass(frozen=True)
class OptionsDailyScope:
    product_codes: tuple[str, ...]


@dataclass(frozen=True)
class DailyWindow:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class OptionsDailyRow:
    contract_code: str
    product_code: str
    symbol: str
    name: str
    exchange: str
    source_underlying_code: str
    underlying_index_code: str
    option_type: str
    exercise_type: str
    quote_unit: str
    settlement_month: str
    call_put: str
    list_date: date
    delist_date: date
    expiry: date
    last_exercise_date: date
    trade_date: date
    last_delivery_date: date | None
    per_unit: float
    opt_multiplier: float
    strike: float
    pre_settle: float
    pre_close: float | None
    close: float
    settle: float
    volume: float
    amount: float
    open_interest: float
    open: float | None
    high: float | None
    low: float | None


@dataclass(frozen=True)
class OptionsDailyExport(ExportEnvelope):
    records: tuple[OptionsDailyRow, ...]
