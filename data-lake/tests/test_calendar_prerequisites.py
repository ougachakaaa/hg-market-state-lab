"""Calendar producer/consumer contract and permission checks across all consumers."""

from copy import deepcopy
from dataclasses import fields, is_dataclass
from datetime import date, datetime, timedelta
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from data_lake import InvalidRequestError, OperationError
from data_lake.adapters.outbound.sqlite import Repository
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import _domain as calendar_domain
from data_lake.datasets.tushare_trade_calendar._service import _create_service as calendar_create
from data_lake.domain import Unit

FIRST = date(2024, 1, 2)
LAST = FIRST + timedelta(days=2)


class CalendarSource:
    def __init__(self) -> None:
        self.calls: list[tuple[Unit, ...]] = []

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        self.calls.append(units)
        result: dict[str, object] = {}
        for unit in units:
            exchange, day = calendar_domain.identity(unit)
            result[unit.key] = {
                "exchange": exchange,
                "cal_date": day.strftime("%Y%m%d"),
                "is_open": int(day != FIRST + timedelta(days=1)),
                "pretrade_date": None,
            }
        return result


@pytest.fixture(params=["index_daily", "equity_index_futures", "equity_index_options"])
def consumer(request: Any, tmp_path: Path) -> Any:
    dataset = "tushare_" + request.param
    package = import_module("data_lake.datasets." + dataset)
    service_module = import_module(package.__name__ + "._service")
    domain = import_module(package.__name__ + "._domain")
    kind, codes, exchange = {
        "index_daily": ("Index", ["000905.SH", "000300.SH"], "SSE"),
        "equity_index_futures": ("Futures", ["IM", "IF"], "CFFEX"),
        "equity_index_options": ("Options", ["MO", "IO"], "CFFEX"),
    }[request.param]
    target = getattr(package, kind + "DailyRange")(codes, FIRST, LAST)
    source = CalendarSource()
    calendar_repo = Repository(tmp_path / "calendar.sqlite3", "tushare_trade_calendar", "fake")
    calendar = calendar_create(calendar_repo, lambda: source)
    repo = Repository(tmp_path / "consumer.sqlite3", dataset, "fake")

    def no_source() -> Any:
        pytest.fail("Consumer Source must not be prepared")

    service = service_module._create_service(repo, calendar, no_source)
    return SimpleNamespace(
        service=service,
        resolver=service_module.trading_days,
        domain=domain,
        request=target,
        calendar=calendar,
        calendar_repo=calendar_repo,
        source=source,
        repo=repo,
        dependency=TradeCalendarRange(exchange, FIRST, LAST),
        codes=tuple(sorted(codes)),
    )


def mutable(value: Any) -> Any:
    if is_dataclass(value):
        return SimpleNamespace(
            **{field.name: mutable(getattr(value, field.name)) for field in fields(value)}
        )
    if isinstance(value, tuple):
        return [mutable(item) for item in value]
    return value


def change(view: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    for part in parts[:-1]:
        view = view[int(part)] if part.isdigit() else getattr(view, part)
    setattr(view, parts[-1], value)


DEFECTS = [
    ("dataset", "other"),
    ("view", "other"),
    ("export_schema_version", 2),
    ("export_schema_version", True),
    ("export_schema_version", 1.0),
    ("export_schema_version", "1"),
    ("scope.exchange", "other"),
    ("scope", None),
    ("window", None),
    ("window.start_date", FIRST - timedelta(days=1)),
    ("window.end_date", LAST + timedelta(days=1)),
    ("window.start_date", datetime(2024, 1, 2)),
    ("window.end_date", "2024-01-04"),
    ("coverage", None),
    ("coverage.requested_units", 2),
    ("coverage.requested_units", 3.0),
    ("coverage.successful_units", True),
    ("coverage.successful_units", 0),
    ("coverage.missing_units", False),
    ("coverage.pending_units", 0.0),
    ("coverage.failed_units", -1),
    ("coverage.failed_units", "0"),
    ("coverage.complete", 1),
    ("records", None),
    ("records", {}),
    ("records.0.exchange", "other"),
    ("records.0.cal_date", FIRST - timedelta(days=1)),
    ("records.0.cal_date", LAST + timedelta(days=1)),
    ("records.0.cal_date", datetime(2024, 1, 2)),
    ("records.0.cal_date", "2024-01-02"),
    ("records.0.is_open", True),
    ("records.0.is_open", 1.0),
    ("records.0.is_open", 2),
    ("records.0.pretrade_date", "20240101"),
    ("records.0.pretrade_date", datetime(2024, 1, 1)),
    ("records.1.cal_date", FIRST),
]


@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize(("path", "value"), DEFECTS)
def test_invalid_view_fails_before_prerequisite_write(
    consumer: Any, monkeypatch: pytest.MonkeyPatch, partial: bool, path: str, value: Any
) -> None:
    c = consumer
    end = LAST - timedelta(days=1) if partial else LAST
    c.calendar.ensure(TradeCalendarRange(c.dependency.exchange, FIRST, end))
    view = mutable(c.calendar.export(c.dependency))
    change(view, path, value)
    before = c.calendar_repo.path.read_bytes()
    calls = list(c.source.calls)
    monkeypatch.setattr(c.calendar, "export", lambda _: view)

    def forbidden(_: Any) -> Any:
        pytest.fail("Invalid view must never authorize prerequisite ensure")

    monkeypatch.setattr(c.calendar, "ensure", forbidden)
    for operation in ("coverage", "export", "ensure"):
        with pytest.raises(OperationError, match="Calendar"):
            getattr(c.service, operation)(c.request)
    assert c.source.calls == calls
    assert c.calendar_repo.path.read_bytes() == before
    assert not c.repo.path.exists()


@pytest.mark.parametrize("operation", ["coverage", "export"])
@pytest.mark.parametrize("populated", [False, True])
def test_read_only_never_fills_legal_partial_calendar(
    consumer: Any, operation: str, populated: bool
) -> None:
    c = consumer
    if populated:
        c.calendar.ensure(TradeCalendarRange(c.dependency.exchange, FIRST, FIRST))
    before = c.calendar_repo.path.read_bytes() if populated else None
    calls = list(c.source.calls)
    with pytest.raises(OperationError, match="Calendar"):
        getattr(c.service, operation)(c.request)
    assert c.source.calls == calls
    assert not c.repo.path.exists()
    assert (c.calendar_repo.path.read_bytes() if populated else None) == before
    assert c.calendar_repo.path.exists() == populated


def test_legal_partial_can_be_completed_and_context_is_operation_local(
    consumer: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = consumer
    c.calendar.ensure(TradeCalendarRange(c.dependency.exchange, FIRST, FIRST))
    original = c.calendar.ensure
    requests: list[TradeCalendarRange] = []

    def ensure(request: Any) -> Any:
        requests.append(request)
        return original(request)

    monkeypatch.setattr(c.calendar, "ensure", ensure)
    days = c.resolver(c.calendar, c.request, True)
    assert days == (FIRST, LAST)
    assert requests == [c.dependency]
    expected = tuple((code, day) for code in c.codes for day in days)
    assert tuple(unit.identity for unit in c.domain.targets(c.request, days)) == expected
    assert tuple(unit.identity for unit in c.domain.targets(c.request, days)) == expected
    before = c.calendar_repo.path.read_bytes()
    calls = list(c.source.calls)
    assert c.service.coverage(c.request).requested_units == len(expected)
    assert c.service.export(c.request).coverage.missing_units == len(expected)
    assert c.resolver(c.calendar, c.request, True) == days
    assert requests == [c.dependency]  # Complete prerequisites are never ensured again.
    assert c.calendar_repo.path.read_bytes() == before
    assert c.source.calls == calls
    assert not c.repo.path.exists()
    # A later operation must validate its own export rather than trust old context.
    view = mutable(c.calendar.export(c.dependency))
    view.records[0].is_open = False
    monkeypatch.setattr(c.calendar, "export", lambda _: view)
    with pytest.raises(OperationError, match="Calendar"):
        c.service.coverage(c.request)


@pytest.mark.parametrize("defect", ["incomplete", "invalid", "failed_ensure"])
def test_prerequisite_after_ensure_must_be_complete_and_valid(
    consumer: Any, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    c = consumer
    initial = c.calendar.export(c.dependency)
    c.calendar.ensure(c.dependency)
    final = mutable(c.calendar.export(c.dependency))
    if defect == "invalid":
        final.export_schema_version = True
    exports = iter([initial, initial if defect == "incomplete" else final])
    monkeypatch.setattr(c.calendar, "export", lambda _: next(exports))
    monkeypatch.setattr(
        c.calendar, "ensure", lambda _: SimpleNamespace(complete=defect != "failed_ensure")
    )
    with pytest.raises(OperationError, match="Calendar"):
        c.service.ensure(c.request)
    assert not c.repo.path.exists()


def test_empty_payload_and_complete_formula_are_validated(
    consumer: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = consumer
    initial = mutable(c.calendar.export(c.dependency))
    invalid_records: tuple[object, ...] = ("", b"", {}, None)
    for records in invalid_records:
        view = deepcopy(initial)
        view.records = records
        monkeypatch.setattr(c.calendar, "export", lambda _, view=view: view)
        with pytest.raises(OperationError, match="Calendar"):
            c.resolver(c.calendar, c.request, True)
    initial.coverage.complete = True
    monkeypatch.setattr(c.calendar, "export", lambda _: initial)
    with pytest.raises(OperationError, match="Calendar"):
        c.resolver(c.calendar, c.request, True)
    assert not c.calendar_repo.path.exists()
    assert not c.repo.path.exists()


def test_calendar_planner_includes_closed_days_and_is_stable() -> None:
    request = TradeCalendarRange("SSE", FIRST, LAST)
    expected = tuple(("SSE", FIRST + timedelta(days=i)) for i in range(3))
    for _ in range(2):
        assert tuple(unit.identity for unit in calendar_domain.targets(request)) == expected


def test_invalid_request_precedes_resolver(consumer: Any) -> None:
    for operation in ("coverage", "ensure", "export"):
        with pytest.raises(InvalidRequestError):
            getattr(consumer.service, operation)(None)
    assert consumer.source.calls == []
    assert not consumer.calendar_repo.path.exists()
    assert not consumer.repo.path.exists()
