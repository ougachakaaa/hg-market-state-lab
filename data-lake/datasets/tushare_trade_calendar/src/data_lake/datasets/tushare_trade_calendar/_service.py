"""Calendar interpretation composed with the existing cache execution core."""

import math
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

from data_lake._application import Core, Source
from data_lake._domain import CachedUnit, ExecutionFailure, Record, Unit, UnitRecords
from data_lake._repository import Repository
from data_lake._runtime import database_path
from data_lake.results import CoverageResult, EnsureResult, InvalidRequestError

from ._models import (
    CalendarWindow,
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
    TradeCalendarScope,
)
from ._source import batches, identity, prepare_source, provider_date

DATASET = "tushare_trade_calendar"


def targets(request: TradeCalendarRange) -> tuple[Unit, ...]:
    if not isinstance(request, TradeCalendarRange):
        raise InvalidRequestError("request must be a TradeCalendarRange")
    request.__post_init__()
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


class TradeCalendarService:
    def __init__(self) -> None:
        self._core = _compose(
            Repository(
                database_path(DATASET, Path(__file__).resolve().parents[4] / "data"),
                DATASET,
                "tushare",
            ),
            prepare_source,
        )

    def coverage(self, request: TradeCalendarRange) -> CoverageResult:
        return self._core.coverage(request)

    def ensure(self, request: TradeCalendarRange) -> EnsureResult:
        return self._core.ensure(request)

    def export(self, request: TradeCalendarRange) -> TradeCalendarExport:
        return self._core.export(request)


def _compose(
    repository: Repository, source_factory: Callable[[], Source]
) -> Core[TradeCalendarRange, TradeCalendarExport]:
    return Core(
        repository,
        targets=targets,
        prepare_source=source_factory,
        normalize=normalize,
        check_complete=check_complete,
        project=project,
        batches=batches,
    )


def _create_service(
    repository: Repository, source_factory: Callable[[], Source]
) -> TradeCalendarService:
    """Internal test/composition seam, excluded from the consumer facade."""
    service = TradeCalendarService.__new__(TradeCalendarService)
    service._core = _compose(repository, source_factory)
    return service


def create_service() -> TradeCalendarService:
    return TradeCalendarService()
