"""Transport-neutral calendar request and view values."""

from dataclasses import dataclass
from datetime import date

from data_lake.results import ExportEnvelope, InvalidRequestError


@dataclass(frozen=True)
class TradeCalendarRange:
    exchange: str
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if (
            not isinstance(self.exchange, str)
            or not self.exchange
            or any(character.isspace() for character in self.exchange)
        ):
            raise InvalidRequestError("exchange must be a non-empty canonical identifier")
        if type(self.start_date) is not date or type(self.end_date) is not date:
            raise InvalidRequestError("start_date and end_date must be datetime.date values")
        if self.start_date > self.end_date:
            raise InvalidRequestError("start_date must be <= end_date")


@dataclass(frozen=True)
class TradeCalendarRecord:
    exchange: str
    cal_date: date
    is_open: int
    pretrade_date: date | None


@dataclass(frozen=True)
class TradeCalendarScope:
    exchange: str


@dataclass(frozen=True)
class CalendarWindow:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class TradeCalendarExport(ExportEnvelope):
    scope: TradeCalendarScope
    window: CalendarWindow
    records: tuple[TradeCalendarRecord, ...]
