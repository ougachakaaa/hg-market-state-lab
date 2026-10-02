"""Observation producer acceptance through owned SQLite and public dependency doubles."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from pathlib import Path
from threading import Barrier
from typing import Any, cast

import pytest

from data_lake import EnsureResult, OperationError, UnitFailure
from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_trade_calendar as calendar
from market_research.observations import (
    ObservationError,
    ObservationInvalidRequestError,
    ObservationOperationError,
)
from market_research.observations import cffex_option_expiry_dte_chain as chain
from market_research.observations import cffex_option_expiry_universe as universe
from observation_support import CalendarDouble, OptionsDouble, coverage, row

EXPIRY = date(2025, 10, 23)
IDEAL = date(2025, 10, 9)
START = date(2025, 10, 1)
END = date(2025, 10, 31)


def unavailable() -> Any:
    pytest.fail("retained hit must not construct / call upstream")


def make_universe(path: Path, dependency: OptionsDouble) -> universe.ExpiryUniverseService:
    return universe.ExpiryUniverseService(
        _path=path,
        _options_factory=lambda: cast(options.OptionsDailyService, dependency),
    )


def make_chain(
    path: Path, facts: OptionsDouble, dates: CalendarDouble
) -> chain.ExpiryDteChainService:
    return chain.ExpiryDteChainService(
        _path=path,
        _options_factory=lambda: cast(options.OptionsDailyService, facts),
        _calendar_factory=lambda: cast(calendar.TradeCalendarService, dates),
    )


@pytest.mark.parametrize("stage", ["universe", "calendar", "options"])
@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("unit_failure", "Upstream ensure did not complete"),
        ("incomplete", "Upstream ensure did not complete"),
        ("invalid_counters", "Invalid ensure counters"),
        ("inconsistent_counters", "Inconsistent ensure counters"),
        ("invalid_complete", "Invalid ensure complete flag"),
        ("invalid_failures", "Invalid ensure failures"),
        ("invalid_failure", "Invalid ensure failure"),
        ("invalid_identity", "Invalid ensure failure identity"),
        ("short_identity", "Invalid ensure failure identity"),
        ("invalid_selector", "Invalid ensure failure identity"),
        ("invalid_date", "Invalid ensure failure identity"),
        ("invalid_reason", "Invalid ensure failure reason"),
        ("empty_reason", "Invalid ensure failure reason"),
    ],
)
def test_ensure_diagnostics_preserve_context_without_publishing_or_fallback(
    tmp_path: Path, stage: str, scenario: str, expected: str
) -> None:
    class Unprintable:
        def __repr__(self) -> str:
            raise AssertionError("diagnostics formatted an arbitrary object")

    marker = Unprintable()
    selector = "CFFEX" if stage == "calendar" else "MO"
    dataset = "tushare_trade_calendar" if stage == "calendar" else "tushare_equity_index_options"
    reason = "opt_daily: timeout"

    def fail(result: EnsureResult) -> EnsureResult:
        failure = UnitFailure((selector, IDEAL), reason)
        failed = replace(
            result,
            already_successful_units=result.requested_units - 1,
            attempted_units=1,
            succeeded_units=0,
            failed_units=1,
            complete=False,
            failures=(failure,),
        )
        if scenario == "incomplete":
            return replace(result, complete=False)
        if scenario == "invalid_counters":
            return replace(failed, failed_units=True)
        if scenario == "inconsistent_counters":
            return replace(failed, requested_units=result.requested_units + 1)
        if scenario == "invalid_complete":
            return replace(failed, complete=cast(Any, 0))
        if scenario == "invalid_failures":
            return replace(failed, failures=cast(Any, [failure]))
        if scenario == "invalid_failure":
            return replace(failed, failures=(cast(Any, marker),))
        if scenario == "invalid_identity":
            failure = replace(failure, identity=marker)
        elif scenario == "short_identity":
            failure = replace(failure, identity=(selector,))
        elif scenario == "invalid_selector":
            failure = replace(failure, identity=(marker, IDEAL))
        elif scenario == "invalid_date":
            failure = replace(failure, identity=(selector, datetime(2025, 10, 9)))
        elif scenario == "invalid_reason":
            failure = replace(failure, reason=cast(Any, marker))
        elif scenario == "empty_reason":
            failure = replace(failure, reason="")
        return replace(failed, failures=(failure,))

    facts = OptionsDouble((IDEAL,), (row(EXPIRY, IDEAL),), complete=stage != "options")
    dates = CalendarDouble((IDEAL,), complete=stage != "calendar")
    if stage == "calendar":
        dates.ensure_hook = fail
    else:
        facts.ensure_hook = fail
    path = tmp_path / "artifact.sqlite3"
    with pytest.raises(ObservationOperationError) as raised:
        if stage == "universe":
            make_universe(path, facts).ensure(universe.ExpiryUniverseRequest("MO", START, END))
        else:
            make_chain(path, facts, dates).ensure(chain.ExpiryDteChainRequest("MO", EXPIRY, 15))
    message = str(raised.value)
    assert dataset in message and expected in message
    assert f"{'exchange' if stage == 'calendar' else 'product_code'}={selector}" in message
    if stage == "universe":
        assert f"start_date={START} end_date={END}" in message
        assert dates.calls == []
        assert [operation for operation, _ in facts.calls] == ["ensure"]
    elif stage == "calendar":
        request = dates.calls[0][1]
        assert f"start_date={request.start_date} end_date={request.end_date}" in message
        assert facts.calls == []
        assert [operation for operation, _ in dates.calls] == ["export", "ensure"]
    else:
        assert f"start_date={IDEAL} end_date={IDEAL}" in message
        assert [operation for operation, _ in facts.calls] == ["export", "ensure"]
        assert all(request.start_date == IDEAL for _, request in facts.calls)
    if scenario in ("unit_failure", "incomplete"):
        assert "requested_units=" in message and "attempted_units=" in message
        assert "succeeded_units=" in message and "failed_units=" in message
    if scenario == "unit_failure":
        assert f"unit=({selector}, {IDEAL}): {reason}" in message
    elif scenario == "incomplete":
        assert "failures=none" in message
    else:
        assert "Upstream ensure did not complete" not in message
    assert not path.exists()


@pytest.mark.parametrize("stage", ["universe", "calendar"])
def test_ensure_diagnostics_keep_all_failures_in_upstream_order(tmp_path: Path, stage: str) -> None:
    previous = date(2025, 10, 8)
    selector = "CFFEX" if stage == "calendar" else "MO"
    failures = tuple(
        UnitFailure((selector, day), reason)
        for day, reason in ((IDEAL, "first timeout"), (previous, "second permission"))
    )

    def fail(result: EnsureResult) -> EnsureResult:
        return replace(
            result,
            already_successful_units=result.requested_units - 2,
            attempted_units=2,
            succeeded_units=0,
            failed_units=2,
            complete=False,
            failures=failures,
        )

    facts = OptionsDouble((previous, IDEAL))
    dates = CalendarDouble((previous, IDEAL), complete=False)
    path = tmp_path / "artifact.sqlite3"
    with pytest.raises(ObservationOperationError) as raised:
        if stage == "universe":
            facts.ensure_hook = fail
            make_universe(path, facts).ensure(universe.ExpiryUniverseRequest("MO", START, END))
        else:
            dates.ensure_hook = fail
            make_chain(path, facts, dates).ensure(chain.ExpiryDteChainRequest("MO", EXPIRY, 15))
    message = str(raised.value)
    first = f"unit=({selector}, {IDEAL}): first timeout"
    second = f"unit=({selector}, {previous}): second permission"
    assert message.index(first) < message.index(second)
    assert "attempted_units=2 succeeded_units=0 failed_units=2" in message
    assert not path.exists()


def test_public_facades_and_factory_without_upstream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(options, "create_service", unavailable)
    monkeypatch.setattr(calendar, "create_service", unavailable)
    assert isinstance(universe.create_service(), universe.ExpiryUniverseService)
    assert isinstance(chain.create_service(), chain.ExpiryDteChainService)
    assert issubclass(ObservationInvalidRequestError, ObservationError)
    assert issubclass(ObservationOperationError, ObservationError)
    assert not hasattr(universe, "__all__") and not hasattr(chain, "__all__")


@pytest.mark.parametrize(
    "values",
    [
        ("mo", START, END),
        (" MO", START, END),
        ("UNKNOWN", START, END),
        (None, START, END),
        ("MO", str(START), END),
        ("MO", datetime(2026, 10, 1), END),
        ("MO", END, START),
    ],
)
def test_universe_rejects_invalid_requests(values: tuple[Any, ...]) -> None:
    with pytest.raises(ObservationInvalidRequestError):
        universe.ExpiryUniverseRequest(*values)


@pytest.mark.parametrize(
    "values",
    [
        ("mo", EXPIRY, 15),
        ("MO", str(EXPIRY), 15),
        ("MO", datetime(2026, 10, 23), 15),
        ("MO", EXPIRY, True),
        ("MO", EXPIRY, 0),
        ("MO", EXPIRY, -1),
        ("MO", EXPIRY, 1.5),
        ("MO", EXPIRY, "15"),
        ("MO", None, 15),
    ],
)
def test_chain_rejects_invalid_requests(values: tuple[Any, ...]) -> None:
    with pytest.raises(ObservationInvalidRequestError):
        chain.ExpiryDteChainRequest(*values)


def test_invalid_ensure_precedes_lookup_and_dependencies(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.sqlite3"
    path.write_text("corrupt", encoding="utf-8")
    for service in (
        universe.ExpiryUniverseService(_path=path, _options_factory=unavailable),
        chain.ExpiryDteChainService(
            _path=path, _options_factory=unavailable, _calendar_factory=unavailable
        ),
    ):
        with pytest.raises(ObservationInvalidRequestError):
            service.ensure(cast(Any, object()))


def test_universe_semantics_durable_reuse_multiple_requests(tmp_path: Path) -> None:
    before, after = START.replace(month=9), END.replace(month=11, day=30)
    values = (
        row(END, IDEAL, strike=8500),
        row(START, START),
        row(EXPIRY, IDEAL),
        row(EXPIRY, IDEAL, side="PUT"),
        row(before, START),
        row(after, IDEAL),
    )
    dependency = OptionsDouble((START, IDEAL), values)
    path = tmp_path / "universe.sqlite3"
    request = universe.ExpiryUniverseRequest("MO", START, END)
    first_service = make_universe(path, dependency)
    first = first_service.ensure(request)
    assert first.expiries == (START, EXPIRY, END)
    assert [operation for operation, _ in dependency.calls] == ["ensure", "export"]
    assert (
        dependency.calls[0][1]
        == dependency.calls[1][1]
        == options.OptionsDailyRange(
            ("MO",),
            START,
            END,
        )
    )
    assert first.provenance.coverage.requested_units == 2
    assert first.provenance.window.start_date == START
    with pytest.raises(FrozenInstanceError):
        first.product_code = "IO"  # type: ignore[misc]
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 1
    del first_service
    recreated = universe.ExpiryUniverseService(_path=path, _options_factory=unavailable)
    assert recreated.ensure(request) == first
    assert len(dependency.calls) == 2
    other = universe.ExpiryUniverseRequest("MO", IDEAL, IDEAL)
    make_universe(path, dependency).ensure(other)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 2


@pytest.mark.parametrize("opens", [(), (IDEAL,)])
def test_universe_complete_empty(tmp_path: Path, opens: tuple[date, ...]) -> None:
    result = make_universe(tmp_path / "u.sqlite3", OptionsDouble(opens)).ensure(
        universe.ExpiryUniverseRequest("MO", START, END),
    )
    assert result.complete is True and result.expiries == ()


@pytest.mark.parametrize(
    "kind",
    [
        "incomplete",
        "unit_failure",
        "export_incomplete",
        "bad_schema",
        "bad_scope",
        "bad_window",
        "bad_counters",
        "bad_row",
        "operation",
    ],
)
def test_universe_failure_never_publishes(tmp_path: Path, kind: str) -> None:
    dependency = OptionsDouble((IDEAL,), (row(EXPIRY, IDEAL),))
    if kind == "incomplete":
        dependency.ensure_hook = lambda result: replace(result, complete=False)
    elif kind == "unit_failure":
        dependency.ensure_hook = lambda result: replace(
            result, failures=(UnitFailure("unit", "bad"),)
        )
    elif kind == "export_incomplete":
        dependency.export_hook = lambda view: replace(view, coverage=coverage(1, False), records=())
    elif kind == "bad_schema":
        dependency.export_hook = lambda view: replace(view, export_schema_version=1)
    elif kind == "bad_scope":
        dependency.export_hook = lambda view: replace(
            view, scope=options.OptionsDailyScope(("IO",))
        )
    elif kind == "bad_window":
        dependency.export_hook = lambda view: replace(view, window=object())
    elif kind == "bad_counters":
        dependency.export_hook = lambda view: replace(
            view, coverage=replace(view.coverage, failed_units=1)
        )
    elif kind == "bad_row":
        dependency.export_hook = lambda view: replace(
            view, records=(replace(view.records[0], close=float("nan")),)
        )
    else:

        def fail(result: Any) -> Any:
            raise OperationError("calendar prerequisite unavailable")

        dependency.ensure_hook = fail
    path = tmp_path / "u.sqlite3"
    with pytest.raises(ObservationOperationError):
        make_universe(path, dependency).ensure(universe.ExpiryUniverseRequest("MO", START, END))
    assert not path.exists()


def test_chain_exact_dte_population_owned_values_and_restart(tmp_path: Path) -> None:
    values = (
        row(EXPIRY, IDEAL),
        row(EXPIRY, IDEAL, side="PUT"),
        row(EXPIRY, IDEAL, strike=8500),
        row(date(2025, 11, 20), IDEAL),
    )
    facts, dates = OptionsDouble((IDEAL,), values), CalendarDouble((IDEAL,))
    request = chain.ExpiryDteChainRequest("MO", EXPIRY, 15)
    path = tmp_path / "c.sqlite3"
    service = make_chain(path, facts, dates)
    artifact = service.ensure(request)
    assert artifact.ideal_calendar_date == artifact.observation_date == IDEAL
    assert artifact.actual_dte == artifact.target_dte == 15
    assert len(artifact.rows) == 3
    assert all(isinstance(value, chain.ExpiryDteChainRow) for value in artifact.rows)
    assert artifact.rows[0].per_unit == 100.0 and artifact.rows[0].opt_multiplier == 101.0
    assert artifact.rows[0].pre_close is None and artifact.rows[0].open is None
    assert artifact.rows[0].last_delivery_date is None and artifact.rows[0].amount == 0.0
    assert [operation for operation, _ in facts.calls] == ["export"]
    assert [operation for operation, _ in dates.calls] == ["export"]
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 1
    del service
    recreated = chain.ExpiryDteChainService(
        _path=path,
        _options_factory=unavailable,
        _calendar_factory=unavailable,
    )
    assert recreated.ensure(request) == artifact
    second = chain.ExpiryDteChainRequest("MO", EXPIRY, 16)
    earlier = IDEAL.replace(day=8)
    make_chain(
        path, OptionsDouble((earlier,), (row(EXPIRY, earlier),)), CalendarDouble((earlier,))
    ).ensure(second)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 2


@pytest.mark.parametrize(
    "scenario",
    [
        "holiday",
        "weekend",
        "absence",
        "empty_day",
        "missing",
        "failed_cache",
        "chunks",
        "target_one",
    ],
)
def test_chain_resolution_and_read_first(tmp_path: Path, scenario: str) -> None:
    ideal = EXPIRY if scenario == "target_one" else IDEAL
    target = 1 if scenario == "target_one" else 15
    if scenario == "weekend":
        ideal, target = date(2025, 10, 11), 13
    previous = ideal - (date(2025, 10, 10) - IDEAL)
    if scenario == "chunks":
        previous = date(2025, 8, 1)
    opens = (
        (previous,)
        if scenario in ("holiday", "weekend", "chunks", "target_one")
        else (previous, ideal)
    )
    selected = ideal if scenario in ("missing", "failed_cache") else previous
    values: tuple[options.OptionsDailyRow, ...] = (row(EXPIRY, selected),)
    if scenario == "absence":
        values += (row(date(2025, 11, 20), ideal),)
    facts = OptionsDouble(opens, values, complete=scenario not in ("missing", "failed_cache"))
    if scenario == "failed_cache":

        def failed_initial(view: Any) -> Any:
            return (
                replace(view, coverage=replace(view.coverage, missing_units=0, failed_units=1))
                if not view.coverage.complete
                else view
            )

        facts.export_hook = failed_initial
    dates = CalendarDouble(opens, complete=scenario != "missing")
    artifact = make_chain(tmp_path / "c.sqlite3", facts, dates).ensure(
        chain.ExpiryDteChainRequest("MO", EXPIRY, target),
    )
    assert artifact.observation_date == selected
    assert artifact.actual_dte == (EXPIRY - selected).days + 1
    assert artifact.actual_dte >= target
    option_dates = [
        request.start_date for operation, request in facts.calls if operation == "export"
    ]
    assert option_dates == (
        [ideal, ideal]
        if scenario in ("missing", "failed_cache")
        else [ideal, previous]
        if scenario in ("absence", "empty_day")
        else [previous]
    )
    if scenario == "missing":
        assert [operation for operation, _ in dates.calls] == ["export", "ensure", "export"]
        assert dates.calls[0][1] == dates.calls[1][1] == dates.calls[2][1]
    if scenario in ("missing", "failed_cache"):
        assert [operation for operation, _ in facts.calls] == ["export", "ensure", "export"]
        assert facts.calls[0][1] == facts.calls[1][1] == facts.calls[2][1]
    if scenario == "chunks":
        assert len(artifact.calendar_provenance) == 3


def test_authority_dte_example_is_exact() -> None:
    from market_research.observations.cffex_option_expiry_dte_chain._date_resolution import (
        ideal_date,
    )

    assert ideal_date(date(2026, 10, 23), 15) == date(2026, 10, 9)


@pytest.mark.parametrize(
    "kind",
    [
        "calendar_ensure",
        "calendar_after_ensure",
        "calendar_invalid",
        "options_ensure",
        "options_after_ensure",
        "options_invalid",
        "prerequisite",
        "duplicate_rows",
        "illegal_nullable",
    ],
)
def test_chain_failure_stops_no_date_fallback(tmp_path: Path, kind: str) -> None:
    previous = date(2025, 10, 8)
    opens = (previous, IDEAL)
    facts = OptionsDouble(opens, (row(EXPIRY, IDEAL), row(EXPIRY, previous)))
    dates = CalendarDouble(opens)
    if kind == "calendar_ensure":
        dates.complete = False
        dates.ensure_hook = lambda result: replace(result, complete=False)
    elif kind == "calendar_after_ensure":
        dates.complete = False
        dates.export_hook = lambda view: replace(
            view, coverage=coverage(view.coverage.requested_units, False), records=()
        )
    elif kind == "calendar_invalid":
        dates.export_hook = lambda view: replace(view, records=view.records[:-1])
    elif kind == "options_ensure":
        facts.complete = False
        facts.ensure_hook = lambda result: replace(result, complete=False)
    elif kind == "options_after_ensure":
        facts.complete = False
        facts.export_hook = lambda view: replace(view, coverage=coverage(1, False), records=())
    elif kind == "options_invalid":
        facts.export_hook = lambda view: replace(view, export_schema_version=1)
    elif kind == "duplicate_rows":
        facts.export_hook = lambda view: replace(view, records=view.records * 2)
    elif kind == "illegal_nullable":
        facts.export_hook = lambda view: replace(
            view, records=(replace(view.records[0], volume=1.0),)
        )
    else:

        def fail(view: Any) -> Any:
            raise OperationError("Calendar prerequisite unavailable")

        facts.export_hook = fail
    path = tmp_path / "c.sqlite3"
    with pytest.raises(ObservationOperationError):
        make_chain(path, facts, dates).ensure(chain.ExpiryDteChainRequest("MO", EXPIRY, 15))
    assert all(request.start_date == IDEAL for _, request in facts.calls)
    assert not path.exists()


@pytest.mark.parametrize("expiry,target", [(date.min, 2), (EXPIRY, 10**20), (date.min, 1)])
def test_chain_unrepresentable_date_or_exhausted_history(
    tmp_path: Path, expiry: date, target: int
) -> None:
    dates = CalendarDouble(())
    facts = OptionsDouble(())
    with pytest.raises(ObservationOperationError):
        make_chain(tmp_path / "c.sqlite3", facts, dates).ensure(
            chain.ExpiryDteChainRequest("MO", expiry, target),
        )
    assert not facts.calls


@pytest.mark.parametrize("producer", ["universe", "chain"])
@pytest.mark.parametrize("damage", ["corrupt", "version", "payload", "partial", "publication"])
def test_persistence_failure_is_not_a_hit_or_silent_miss(
    tmp_path: Path, producer: str, damage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "owned.sqlite3"
    facts, dates = OptionsDouble((IDEAL,), (row(EXPIRY, IDEAL),)), CalendarDouble((IDEAL,))
    if producer == "universe":
        service: Any = make_universe(path, facts)
        request: Any = universe.ExpiryUniverseRequest("MO", START, END)
        from market_research.observations.cffex_option_expiry_universe import (
            _persistence as universe_storage,
        )

        storage: Any = universe_storage
    else:
        service = make_chain(path, facts, dates)
        request = chain.ExpiryDteChainRequest("MO", EXPIRY, 15)
        from market_research.observations.cffex_option_expiry_dte_chain import (
            _persistence as chain_storage,
        )

        storage = chain_storage
    if damage == "publication":

        def fail(*args: Any) -> Any:
            raise sqlite3.OperationalError("publication failed")

        monkeypatch.setattr(storage, "publish_payload", fail)
        with pytest.raises(ObservationOperationError):
            service.ensure(request)
        assert not path.exists()
        return
    service.ensure(request)
    facts.calls.clear()
    dates.calls.clear()
    if damage == "corrupt":
        path.write_text("not sqlite", encoding="utf-8")
    else:
        with sqlite3.connect(path) as db:
            if damage == "version":
                db.execute("PRAGMA user_version=99")
            elif damage == "payload":
                db.execute("UPDATE artifacts SET payload='{}'")
            else:
                payload = json.loads(db.execute("SELECT payload FROM artifacts").fetchone()[0])
                payload["complete"] = False
                db.execute("UPDATE artifacts SET payload=?", (json.dumps(payload),))
    with pytest.raises(ObservationOperationError):
        service.ensure(request)
    assert not facts.calls and not dates.calls


@pytest.mark.parametrize("producer", ["universe", "chain"])
def test_concurrent_misses_publish_one_logical_artifact(tmp_path: Path, producer: str) -> None:
    path = tmp_path / "owned.sqlite3"
    barrier = Barrier(2)

    def run(index: int) -> Any:
        facts = OptionsDouble((IDEAL,), (row(EXPIRY, IDEAL, strike=8000 + index),))

        def synchronize(view: Any) -> Any:
            barrier.wait(timeout=10)
            return view

        facts.export_hook = synchronize
        if producer == "universe":
            return make_universe(path, facts).ensure(
                universe.ExpiryUniverseRequest("MO", START, END)
            )
        return make_chain(path, facts, CalendarDouble((IDEAL,))).ensure(
            chain.ExpiryDteChainRequest("MO", EXPIRY, 15),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = tuple(pool.map(run, (0, 1)))
    assert values[0] == values[1]
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 1


@pytest.mark.parametrize("producer", ["universe", "chain"])
def test_sqlite_insert_abort_is_atomic_and_failed_request_can_be_ensured_later(
    tmp_path: Path,
    producer: str,
) -> None:
    path = tmp_path / "owned.sqlite3"
    facts = OptionsDouble((IDEAL,), (row(EXPIRY, IDEAL),))
    if producer == "universe":
        service: Any = make_universe(path, facts)
        first: Any = universe.ExpiryUniverseRequest("MO", START, END)
        second: Any = universe.ExpiryUniverseRequest("MO", IDEAL, END)
    else:
        service = make_chain(path, facts, CalendarDouble((IDEAL,)))
        first = chain.ExpiryDteChainRequest("MO", EXPIRY, 15)
        second = chain.ExpiryDteChainRequest("MO", EXPIRY, 14)
    retained = service.ensure(first)
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TRIGGER reject_publication BEFORE INSERT ON artifacts
                      BEGIN SELECT RAISE(ABORT, 'controlled publication failure'); END""")
    with pytest.raises(ObservationOperationError, match="publication failure"):
        service.ensure(second)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 1
        db.execute("DROP TRIGGER reject_publication")
    assert service.ensure(first) == retained
    assert service.ensure(second).complete is True
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 2


@pytest.mark.parametrize("producer", ["universe", "chain"])
def test_interrupted_upstream_never_publishes(tmp_path: Path, producer: str) -> None:
    path = tmp_path / "owned.sqlite3"
    facts = OptionsDouble((IDEAL,), (row(EXPIRY, IDEAL),))

    def interrupt(value: Any) -> Any:
        raise KeyboardInterrupt

    facts.export_hook = interrupt
    with pytest.raises(KeyboardInterrupt):
        if producer == "universe":
            make_universe(path, facts).ensure(universe.ExpiryUniverseRequest("MO", START, END))
        else:
            make_chain(path, facts, CalendarDouble((IDEAL,))).ensure(
                chain.ExpiryDteChainRequest("MO", EXPIRY, 15),
            )
    assert not path.exists()


@pytest.mark.parametrize("producer", ["universe", "chain"])
def test_factory_construction_error_is_public_operation_failure(
    producer: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    name = (
        "cffex_option_expiry_universe"
        if producer == "universe"
        else "cffex_option_expiry_dte_chain"
    )
    module = importlib.import_module(f"market_research.observations.{name}._service")

    def fail(*args: Any) -> Any:
        raise OSError("owned path unavailable")

    monkeypatch.setattr(module, "owned_path", fail)
    with pytest.raises(ObservationOperationError, match="construction failed"):
        module.create_service()
