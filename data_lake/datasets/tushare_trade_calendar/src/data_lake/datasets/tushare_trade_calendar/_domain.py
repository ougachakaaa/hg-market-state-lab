"""Calendar targets, fact normalization, completeness and business projection."""

import math
from datetime import date, timedelta

from data_lake.domain import CachedUnit, ExecutionFailure, Record, Unit, UnitRecords
from data_lake.results import CoverageResult, OperationError

from ._models import (
    CalendarWindow,
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
    TradeCalendarScope,
)


def provider_date(value: object) -> date:
    if not isinstance(value, str) or len(value) != 8 or not value.isascii() or not value.isdigit():
        raise ExecutionFailure("Source date must be a valid YYYYMMDD value", "invalid_date")
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError as exc:
        raise ExecutionFailure("Source date is invalid", "invalid_date") from exc


def identity(unit: Unit) -> tuple[str, date]:
    value = unit.identity
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or not isinstance(value[0], str)
        or type(value[1]) is not date
    ):
        raise OperationError("Invalid internal calendar identity")
    return value[0], value[1]


DATASET = "tushare_trade_calendar"


def targets(request: TradeCalendarRange) -> tuple[Unit, ...]:
    return tuple(
        Unit((request.exchange, request.start_date + timedelta(days=offset)))
        for offset in range((request.end_date - request.start_date).days + 1)
    )


def normalize(unit: Unit, raw: object) -> UnitRecords:
    if isinstance(raw, ExecutionFailure):
        raise raw
    if not isinstance(raw, dict):
        raise ExecutionFailure("Invalid Source record", "invalid_record")
    exchange, day = identity(unit)
    if raw.get("exchange") != exchange or provider_date(raw.get("cal_date")) != day:
        raise ExecutionFailure("Source record identity mismatch", "identity")
    opened = raw.get("is_open")
    if type(opened) is str and opened in ("0", "1"):
        opened = int(opened)
    if type(opened) is not int or opened not in (0, 1):
        raise ExecutionFailure("Invalid required is_open fact", "invalid_fact")
    if "pretrade_date" not in raw:
        raise ExecutionFailure("Missing pretrade_date field", "invalid_fact")
    previous = raw["pretrade_date"]
    absent = (
        previous is None
        or (isinstance(previous, str) and previous == "")
        or (type(previous) is float and math.isnan(previous))
    )
    prior = None if absent else provider_date(previous)
    return UnitRecords(
        (
            Record(
                {
                    "exchange": exchange,
                    "cal_date": day.isoformat(),
                    "is_open": opened,
                    "pretrade_date": prior.isoformat() if prior is not None else None,
                }
            ),
        )
    )


def read_record(unit: Unit, record: Record) -> TradeCalendarRecord:
    exchange, day = identity(unit)
    fields = record.fields
    if set(fields) != {"exchange", "cal_date", "is_open", "pretrade_date"}:
        raise ExecutionFailure("Invalid canonical calendar fields", "completeness")
    if record.instrument_key is not None:
        raise ExecutionFailure("Calendar records cannot reference instruments", "completeness")
    opened = fields["is_open"]
    if fields["exchange"] != exchange or fields["cal_date"] != day.isoformat():
        raise ExecutionFailure("Canonical record identity mismatch", "completeness")
    if type(opened) is not int or opened not in (0, 1):
        raise ExecutionFailure("Invalid canonical is_open fact", "completeness")
    prior = fields["pretrade_date"]
    if prior is not None:
        try:
            if not isinstance(prior, str):
                raise ValueError
            parsed = date.fromisoformat(prior)
            if parsed.isoformat() != prior:
                raise ValueError
        except ValueError as exc:
            raise ExecutionFailure("Invalid canonical pretrade_date", "completeness") from exc
    else:
        parsed = None
    return TradeCalendarRecord(exchange, day, opened, parsed)


def check_complete(unit: Unit, facts: UnitRecords) -> None:
    if len(facts.records) != 1 or facts.instruments:
        raise ExecutionFailure("Calendar unit must own exactly one record", "completeness")
    read_record(unit, facts.records[0])


def project(
    request: TradeCalendarRange, coverage: CoverageResult, cached: tuple[CachedUnit, ...]
) -> TradeCalendarExport:
    records = tuple(
        sorted(
            (read_record(item.unit, item.records[0]) for item in cached),
            key=lambda record: record.cal_date,
        )
    )
    return TradeCalendarExport(
        DATASET,
        "calendar",
        1,
        TradeCalendarScope(request.exchange),
        CalendarWindow(request.start_date, request.end_date),
        coverage,
        records,
    )
