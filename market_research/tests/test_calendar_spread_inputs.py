"""WP2 read-only final-export validation and immutable retention acceptance."""

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from calendar_spread_fixtures import AFTER, DAY, Services, coverage
from data_lake import InvalidRequestError, OperationError
from market_research.descriptive.cases.futures_calendar_spread import (
    InputPreparationError,
    PreparedCalendarSpreadInputs,
    preparation,
    prepare_inputs,
    validation,
)


def mutate(raw, path: str, value: Any):
    """Corrupt a public field without relying on any upstream internal types."""
    name, *rest = path.split(".", 1)
    original = (
        {field.name: getattr(raw, field.name) for field in fields(raw)}
        if is_dataclass(raw)
        else dict(vars(raw))
    )
    original[name] = mutate(original[name], rest[0], value) if rest else value
    return SimpleNamespace(**original)


@pytest.mark.parametrize("product", ["IF", "IH", "IC", "IM"])
def test_exact_read_only_sequence_and_full_evidence(product):
    services = Services(DAY, AFTER, product)
    prepared = services.prepare()
    assert isinstance(prepared, PreparedCalendarSpreadInputs)
    assert [name for name, _ in services.calls] == ["calendar", "futures"]
    assert services.calls[0][1].exchange == "CFFEX"
    assert services.calls[1][1].product_codes == (product,)
    assert prepared.calendar_request is services.calls[0][1]
    assert prepared.futures_request is services.calls[1][1]
    assert prepared.calendar_export.records == services.calendar.records
    assert prepared.futures_export.records == services.futures.records
    assert prepared.calendar_export.coverage == services.calendar.coverage
    assert prepared.futures_export.coverage == services.futures.coverage
    assert prepared.candidate_dates == (DAY, AFTER)
    assert prepared.evidence[0].export is prepared.calendar_export
    assert prepared.evidence[1].export is prepared.futures_export
    assert prepared.evidence[1].request is prepared.futures_request
    assert prepared == services.prepare()


@pytest.mark.parametrize(
    "args",
    [
        ("im", DAY, DAY),
        (" IM", DAY, DAY),
        (None, DAY, DAY),
        (True, DAY, DAY),
        ("IM", datetime(2024, 10, 18), DAY),
        ("IM", DAY, "2024-10-18"),
        ("IM", AFTER, DAY),
        ("IM", DAY, date.max),
        ("IM", None, DAY),
    ],
)
def test_invalid_request_before_factories_or_io(args, monkeypatch):
    def forbidden():
        pytest.fail("invalid request constructed a service")

    monkeypatch.setattr(preparation, "create_calendar_service", forbidden)
    monkeypatch.setattr(preparation, "create_futures_service", forbidden)
    with pytest.raises(InputPreparationError) as error:
        prepare_inputs(*args)
    assert error.value.category == "invalid_request"
    assert error.value.dependency == "request"
    assert error.value.evidence == ()


def test_uses_shanghai_today(monkeypatch):
    class Clock:
        @classmethod
        def now(cls, zone):
            assert str(zone) == "Asia/Shanghai"
            return datetime(2024, 10, 18, 0, 1)

    monkeypatch.setattr(validation, "datetime", Clock)
    services = Services()
    services.prepare()
    with pytest.raises(InputPreparationError) as error:
        prepare_inputs(
            "IM", DAY, DAY + timedelta(days=1), calendar_service=services, futures_service=services
        )
    assert error.value.category == "invalid_request"
    assert len(services.calls) == 2


@pytest.mark.parametrize("dependency", ["calendar", "futures"])
def test_legal_incomplete_export_is_failure_and_retains_valid_evidence(dependency):
    services = Services(DAY, AFTER)
    raw = getattr(services, dependency)
    rows = (
        raw.records[1:]
        if dependency == "calendar"
        else tuple(row for row in raw.records if row.trade_date != DAY)
    )
    n = raw.coverage.requested_units
    setattr(services, dependency, replace(raw, coverage=coverage(n, 1), records=rows))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    failure = error.value
    assert failure.category == "incomplete_inputs"
    assert failure.dependency == dependency
    assert failure.stage == "input_preparation"
    assert len(failure.evidence) == (1 if dependency == "calendar" else 2)
    assert failure.evidence[-1].export.coverage.complete is False
    assert len(services.calls) == len(failure.evidence)


@pytest.mark.parametrize("dependency", ["calendar", "futures"])
@pytest.mark.parametrize(
    "field, value",
    [
        ("dataset", "wrong"),
        ("view", "wrong"),
        ("export_schema_version", True),
        ("export_schema_version", 99),
        ("coverage.requested_units", 99),
        ("coverage.successful_units", True),
        ("coverage.failed_units", -1),
        ("coverage.missing_units", 1),
        ("coverage.complete", False),
        ("coverage.complete", 1),
    ],
)
def test_reject_malformed_envelopes(dependency, field, value):
    services = Services()
    setattr(services, dependency, mutate(getattr(services, dependency), field, value))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"
    assert error.value.dependency == dependency
    assert len(error.value.evidence) == (0 if dependency == "calendar" else 1)


@pytest.mark.parametrize("dependency", ["calendar", "futures"])
@pytest.mark.parametrize("bound", ["start_date", "end_date"])
@pytest.mark.parametrize("value", [date(2024, 10, 17), datetime(2024, 10, 18), "2024-10-18"])
def test_wrong_export_window(dependency, bound, value):
    services = Services()
    setattr(services, dependency, mutate(getattr(services, dependency), "window." + bound, value))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"


@pytest.mark.parametrize(
    "dependency, scope",
    [
        ("calendar", SimpleNamespace(exchange="SSE")),
        ("futures", SimpleNamespace(product_codes=("IF",))),
        ("futures", SimpleNamespace(product_codes="IM")),
        ("futures", SimpleNamespace(product_codes=("IM", "IM"))),
    ],
)
def test_wrong_scope(dependency, scope):
    services = Services()
    setattr(services, dependency, replace(getattr(services, dependency), scope=scope))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "reverse",
        "missing",
        "outside",
        "bool-open",
        "timestamp",
        "wrong-exchange",
        "bad-pretrade",
    ],
)
def test_calendar_record_integrity(change):
    services = Services(DAY, AFTER)
    rows = list(services.calendar.records)
    if change == "duplicate":
        rows[1] = rows[0]
    if change == "reverse":
        rows.reverse()
    if change == "missing":
        rows.pop()
    if change == "outside":
        rows[0] = replace(rows[0], cal_date=DAY - timedelta(days=1))
    if change == "bool-open":
        rows[0] = replace(rows[0], is_open=True)
    if change == "timestamp":
        rows[0] = replace(rows[0], cal_date=datetime(2024, 10, 18))
    if change == "wrong-exchange":
        rows[0] = replace(rows[0], exchange="SSE")
    if change == "bad-pretrade":
        rows[0] = replace(rows[0], pretrade_date="2024-10-17")
    services.calendar = replace(services.calendar, records=tuple(rows))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"


@pytest.mark.parametrize(
    "field, value",
    [
        ("contract_code", "IM2410.CFE"),
        ("product_code", "IF"),
        ("symbol", "IM0000"),
        ("exchange", "SSE"),
        ("underlying_index_code", "000300.SH"),
        ("delivery_month", "202413"),
        ("delivery_month", "000010"),
        ("list_date", AFTER),
        ("delist_date", date(2024, 10, 17)),
        ("last_delivery_date", "2024-10-19"),
        ("trade_date", date(2024, 10, 19)),
        ("close", float("nan")),
        ("close", float("inf")),
        ("close", True),
        ("close", None),
        ("pre_settle", None),
        ("pre_close", None),
        ("open_interest_change", None),
        ("volume", -1.0),
        ("amount", -1.0),
        ("open_interest", -1.0),
        ("multiplier", 0.0),
        ("per_unit", -1.0),
        ("name", " "),
        ("quote_unit", None),
    ],
)
def test_all_futures_fact_legality(field, value):
    services = Services()
    rows = list(services.futures.records)
    rows[0] = replace(rows[0], **{field: value})
    services.futures = replace(services.futures, records=tuple(rows))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"
    assert len(error.value.evidence) == 1


@pytest.mark.parametrize("kind", ["duplicate", "reverse", "missing-field"])
def test_futures_record_shape_and_order(kind):
    services = Services()
    rows = list(services.futures.records)
    if kind == "duplicate":
        rows[1] = rows[0]
    if kind == "reverse":
        rows.reverse()
    if kind == "missing-field":
        rows[0] = SimpleNamespace(close=100.0)
    services.futures = replace(services.futures, records=tuple(rows))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"


def test_listing_day_nullable_fields_and_zero_volume_preserved():
    services = Services()
    rows = tuple(
        replace(
            row,
            list_date=DAY,
            pre_close=None,
            open_interest_change=None,
            volume=0.0,
            amount=0.0,
            open_interest=0.0,
        )
        for row in services.futures.records
    )
    services.set_rows(rows)
    prepared = services.prepare()
    assert prepared.futures_export.records == rows


@pytest.mark.parametrize("dependency", ["calendar", "futures"])
@pytest.mark.parametrize(
    "exception, category",
    [
        (OperationError("synthetic unavailable"), "upstream_unavailable"),
        (InvalidRequestError("synthetic rejection"), "input_contract_error"),
    ],
)
def test_public_service_failures(dependency, exception, category):
    services = Services()
    services.errors[dependency] = exception
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == category
    assert error.value.dependency == dependency
    assert error.value.__cause__ is exception
    assert len(error.value.evidence) == (0 if dependency == "calendar" else 1)


@pytest.mark.parametrize(
    "exception", [RuntimeError("bug"), ValueError("bug"), AttributeError("bug"), TypeError("bug")]
)
def test_programming_errors_not_hidden(exception):
    services = Services()
    services.errors["futures"] = exception
    with pytest.raises(type(exception)) as error:
        services.prepare()
    assert error.value is exception


def test_lazy_default_factory_order_and_failure_evidence(monkeypatch):
    services = Services()
    events = []

    def calendar_factory():
        events.append("calendar")
        return services

    def futures_factory():
        assert len(services.calls) == 1
        events.append("futures")
        raise OperationError("unavailable")

    monkeypatch.setattr(preparation, "create_calendar_service", calendar_factory)
    monkeypatch.setattr(preparation, "create_futures_service", futures_factory)
    with pytest.raises(InputPreparationError) as error:
        prepare_inputs("IM", DAY, DAY)
    assert events == ["calendar", "futures"]
    assert error.value.dependency == "futures"
    assert len(error.value.evidence) == 1


def test_copies_mutable_export_sequences_and_context():
    services = Services()
    raw_rows = list(services.futures.records)
    codes = ["IM"]
    window = SimpleNamespace(start_date=DAY, end_date=DAY)
    services.futures = replace(
        services.futures,
        records=raw_rows,
        scope=SimpleNamespace(product_codes=codes),
        window=window,
    )
    prepared = services.prepare()
    raw_rows.clear()
    codes.append("IF")
    window.start_date = AFTER
    assert len(prepared.futures_export.records) == 4
    assert prepared.futures_export.scope.product_codes == ("IM",)
    assert prepared.futures_export.window.start_date == DAY
    with pytest.raises(FrozenInstanceError):
        prepared.candidate_dates = ()
    with pytest.raises(FrozenInstanceError):
        prepared.futures_export.records[0].close = 1.0
    with pytest.raises(FrozenInstanceError):
        prepared.futures_export.window.start_date = AFTER


@pytest.mark.parametrize("dependency", ["calendar", "futures"])
def test_missing_coverage_proof_cannot_establish_empty_universe(dependency):
    services = Services()
    raw = getattr(services, dependency)
    setattr(services, dependency, replace(raw, coverage=None, records=()))
    with pytest.raises(InputPreparationError) as error:
        services.prepare()
    assert error.value.category == "input_contract_error"
    assert error.value.dependency == dependency
    assert len(error.value.evidence) == (0 if dependency == "calendar" else 1)
