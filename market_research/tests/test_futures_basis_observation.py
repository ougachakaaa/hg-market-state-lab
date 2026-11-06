"""WP3 independent formula, proof, accounting and reproduction acceptance."""

import ast
import hashlib
import json
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

import pytest

from futures_basis_observation_fixtures import AFTER, DAY, REQUEST, Services, proof
from market_research.descriptive.cases import futures_basis
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest,
    InputPreparationError,
    ObservationConstructionError,
    construct_observations,
    observe_futures_basis,
)
from market_research.descriptive.cases.futures_basis.validation import canonical_value


def observe(services):
    return construct_observations(services.request, services.prepare())


def test_complete_path_and_public_api() -> None:
    services = Services()
    result = observe_futures_basis(
        REQUEST, calendar_service=services, futures_service=services, index_service=services
    )
    assert services.calls == [(key, "export") for key in ("CFFEX", "SSE", "futures", "index")]
    assert len(result.contract_days) == len(result.slot_days) == 8
    assert len(result.transitions.transitions) == 4
    assert result.transitions.absence_boundaries == ()
    for slot in result.slot_days:
        assert slot.observation is next(
            c for c in result.contract_days if c.identity == (slot.contract_code, slot.trade_date)
        )
        assert slot.outcome("basis_value") is slot.observation.basis_value
        assert slot.observation.futures_source.identity == slot.observation.identity
    assert result.resolutions[0].mappings[0].evidence.source_export_ref.endswith(":futures")


@pytest.mark.parametrize(
    ("price", "state", "difference", "ratio"),
    [
        (110.0, "Premium", 10.0, 0.1),
        (100.0, "Parity", 0.0, 0.0),
        (90.0, "Discount", -10.0, -0.1),
    ],
)
def test_independent_formula_values(price, state, difference, ratio) -> None:
    s = Services(FuturesBasisRequest("IM", DAY, DAY))
    s.futures = replace(
        s.futures,
        records=tuple(
            replace(r, close=price, delist_date=date(2024, 11, 24))
            if r.delivery_month == "202411"
            else r
            for r in s.futures.records
        ),
    )
    r = next(c for c in observe(s).contract_days if c.contract.delivery_month == "202411")
    assert r.days_to_expiry == 37
    assert r.basis_state == state
    assert r.basis_value.value == difference
    assert r.basis_ratio.value == ratio
    # Independent high-precision oracle, without the binary64 implementation formula.
    from decimal import Decimal, localcontext

    with localcontext() as ctx:
        ctx.prec = 60
        expected = Decimal(365) / Decimal(37) * (Decimal(str(price)) / Decimal(100)).ln()
    assert r.annualized_basis_ratio.value == pytest.approx(float(expected), rel=2e-14, abs=1e-16)
    if price != 100:
        assert r.annualized_basis_ratio.value != pytest.approx(365 / 37 * ratio)


def test_expiry_and_accounting() -> None:
    result = observe(Services())
    expiry = result.contract_days[0]
    assert expiry.days_to_expiry == 0
    assert (
        expiry.base.status == expiry.basis_value.status == expiry.basis_ratio.status == "eligible"
    )
    assert expiry.annualized_basis_ratio.reason == "expiry_day"
    for accounting in result.accounting:
        assert accounting.candidate_count == 2
        assert sum(c.count for c in accounting.outcomes) == 2
        assert sum(c.candidate_ratio for c in accounting.outcomes) == 1
        keys = [key for c in accounting.outcomes for key in c.identities]
        assert len(set(keys)) == len(keys)
    m0 = [a for a in result.accounting if a.slot == "M0" and a.metric == "annualized_basis_ratio"][
        0
    ]
    assert m0.eligible_count == m0.not_applicable_count == 1


@pytest.mark.parametrize("price", [0.0, -1.0])
@pytest.mark.parametrize("missing", [False, True])
def test_nonpositive_precedes_missing_and_expiry(price, missing) -> None:
    s = Services()
    s.futures = replace(
        s.futures, records=tuple(replace(r, close=price) for r in s.futures.records)
    )
    if missing:
        s.missing_index()
    result = observe(s)
    row = result.contract_days[0]
    assert row.base.status == row.annualized_basis_ratio.status == "excluded"
    assert row.base.reason == "nonpositive_futures_close"
    assert len(row.issues) == (2 if missing else 1)
    assert result.resolutions[0].mappings[0].contract_code == "IM2410.CFX"


def test_nonpositive_underlying_and_signed_zero() -> None:
    s = Services()
    s.index = replace(s.index, records=tuple(replace(r, close=-0.0) for r in s.index.records))
    result = observe(s)
    assert all(c.base.reason == "nonpositive_underlying_close" for c in result.contract_days)
    assert b'["float64","-0x0.0p+0"]' in result.prepared.canonical_bytes


def test_partial_index_unavailable_transitions_and_no_fill() -> None:
    s = Services()
    s.missing_index()
    result = observe(s)
    assert s.calls[-3:] == [("index", "export"), ("index", "ensure"), ("index", "export")]
    assert len(result.transitions.transitions) == 4
    assert len(result.slot_days) == 8
    assert all(c.base.status == "unavailable" for c in result.contract_days[:4])
    assert result.contract_days[0].annualized_basis_ratio.status == "unavailable"
    assert result.prepared.attempts[-1].ensure_result.failures[0].identity == ("000852.SH", DAY)


def test_independent_calendars() -> None:
    s = Services()
    cal = s.calendars["SSE"]
    s.calendars["SSE"] = replace(
        cal, records=tuple(replace(r, is_open=0) if r.cal_date == DAY else r for r in cal.records)
    )
    s.index = replace(s.index, coverage=proof(1), records=s.index.records[1:])
    result = observe(s)
    assert len(result.slot_days) == 8
    assert result.contract_days[0].base.reason == "underlying_session_closed"
    s = Services()
    cal = s.calendars["CFFEX"]
    s.calendars["CFFEX"] = replace(
        cal, records=tuple(replace(r, is_open=0) if r.cal_date == DAY else r for r in cal.records)
    )
    s.futures = replace(s.futures, coverage=proof(1), records=s.futures.records[4:])
    result = observe(s)
    assert len(result.slot_days) == 4 and len(result.prepared.index.records) == 2


@pytest.mark.parametrize("dependency", ["CFFEX", "SSE", "futures"])
def test_incomplete_required_fail_closed(dependency) -> None:
    s = Services()
    value = s.export_value(dependency)
    if dependency == "futures":
        s.futures = replace(value, coverage=proof(2, 1), records=value.records[4:])
    else:
        s.calendars[dependency] = replace(value, coverage=proof(4, 1), records=value.records[1:])
    # Supply a legal unsuccessful ensure for the actual missing target.
    from data_lake import EnsureResult, UnitFailure

    code = "IM" if dependency == "futures" else dependency
    s.ensure_results[dependency] = EnsureResult(
        value.coverage.requested_units,
        value.coverage.requested_units - 1,
        1,
        0,
        1,
        0,
        False,
        (UnitFailure((code, DAY), "synthetic incomplete"),),
    )
    with pytest.raises(InputPreparationError) as error:
        s.prepare()
    assert error.value.stage == "input_preparation"
    assert error.value.evidence[-1].final_export is not None
    assert not hasattr(error.value, "input_fingerprint")


@pytest.mark.parametrize(
    "field,value",
    [
        ("close", float("nan")),
        ("settle", float("inf")),
        ("close", True),
        ("close", None),
        ("volume", -1.0),
        ("multiplier", 0.0),
        ("pre_close", None),
        ("underlying_index_code", "000300.SH"),
        ("symbol", "IM9999"),
        ("delivery_month", "202413"),
        ("list_date", AFTER),
    ],
)
def test_malformed_futures_never_ensure(field, value) -> None:
    s = Services()
    s.futures = replace(
        s.futures, records=(replace(s.futures.records[0], **{field: value}), *s.futures.records[1:])
    )
    with pytest.raises(InputPreparationError):
        s.prepare()
    assert not any(op == "ensure" for _, op in s.calls)


@pytest.mark.parametrize(
    "change",
    [
        lambda v: replace(v, export_schema_version=True),
        lambda v: replace(v, dataset="wrong"),
        lambda v: replace(v, coverage=replace(v.coverage, successful_units=True)),
        lambda v: replace(v, coverage=replace(v.coverage, complete=False)),
        lambda v: replace(v, records=(v.records[0], *v.records)),
        lambda v: replace(v, records=tuple(reversed(v.records))),
    ],
)
def test_malformed_envelope_or_identity(change) -> None:
    s = Services()
    s.futures = change(s.futures)
    with pytest.raises(InputPreparationError):
        s.prepare()
    assert not any(op == "ensure" for _, op in s.calls)


def test_legal_listing_nullable_facts() -> None:
    s = Services()
    s.futures = replace(
        s.futures,
        records=tuple(
            replace(
                r,
                list_date=r.trade_date,
                pre_close=None,
                open_interest_change=None,
                delivery_settlement_price=None,
            )
            for r in s.futures.records
        ),
    )
    assert len(observe(s).contract_days) == 8


@pytest.mark.parametrize(
    "case_request",
    [
        FuturesBasisRequest("im", DAY, AFTER),
        FuturesBasisRequest("IM", AFTER, DAY),
        FuturesBasisRequest("IM", datetime(2024, 10, 18), AFTER),
        FuturesBasisRequest("IM", DAY, date(9999, 1, 1)),
        FuturesBasisRequest("IM", DAY, AFTER, "other"),
    ],
)
def test_request_rejected_without_io(case_request) -> None:
    s = Services()
    with pytest.raises(InputPreparationError):
        futures_basis.prepare_inputs(
            case_request, calendar_service=s, futures_service=s, index_service=s
        )
    assert s.calls == []


@pytest.mark.parametrize("f,s", [(1e308, 1e-308), (1e-308, 1e308)])
def test_numerical_failure_is_stage_failure(f, s) -> None:
    services = Services()
    services.futures = replace(
        services.futures, records=tuple(replace(r, close=f) for r in services.futures.records)
    )
    services.index = replace(
        services.index, records=tuple(replace(r, close=s) for r in services.index.records)
    )
    with pytest.raises(ObservationConstructionError) as error:
        observe(services)
    assert error.value.category == "numerical_failure"
    assert error.value.identity is not None


def test_empty_universe_and_absence_boundaries() -> None:
    s = Services()
    s.futures = replace(s.futures, records=s.futures.records[4:])
    r = observe(s)
    assert len(r.contract_days) == 4 and len(r.slot_days) == 8
    assert all(item.outcome().reason == "no_active_contract" for item in r.slot_days[:4])
    assert len(r.transitions.absence_boundaries) == 4
    assert all(b.kind == "appeared" for b in r.transitions.absence_boundaries)
    s.futures = replace(s.futures, records=())
    r = observe(s)
    assert not r.contract_days and len(r.slot_days) == 8


def test_zero_candidates() -> None:
    s = Services(FuturesBasisRequest("IM", date(2024, 10, 19), date(2024, 10, 20)))
    r = observe(s)
    assert not r.contract_days and not r.slot_days and not r.transitions.transitions
    assert all(
        a.candidate_count == 0 and all(c.candidate_ratio is None for c in a.outcomes)
        for a in r.accounting
    )


def test_canonical_fixture_and_mutations() -> None:
    p = Services().prepare()
    fixture = Path(__file__).parent / "fixtures" / "futures_basis_inputs_v1.json"
    assert p.canonical_bytes == fixture.read_bytes()
    assert p.input_fingerprint == "f9990fff3ba3de740e04ae2a0c468dde881ffe70486fa68b8d2351d05e48d224"
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == p.input_fingerprint
    assert not p.canonical_bytes.endswith(b"\n")
    payload = json.loads(p.canonical_bytes)
    assert set(payload) == {"profile", "calendar_cffex", "calendar_sse", "futures", "index"}
    assert payload["futures"]["records"][0]["close"] == ["float64", "0x1.b800000000000p+6"]
    s = Services()
    s.futures = replace(
        s.futures,
        records=(replace(s.futures.records[0], close=110.00000000000001), *s.futures.records[1:]),
    )
    assert s.prepare().input_fingerprint != p.input_fingerprint
    s = Services()
    s.missing_index()
    p = s.prepare()
    s.index = replace(s.index, coverage=replace(s.index.coverage, missing_units=0, failed_units=1))
    assert s.prepare().input_fingerprint != p.input_fingerprint
    assert canonical_value(-0.0) != canonical_value(0.0)


def test_preliminary_diagnostics_excluded_from_identity() -> None:
    s = Services()
    final = s.index
    expected = s.prepare().input_fingerprint
    s.missing_index()
    s.after_ensure["index"] = final
    from data_lake import EnsureResult

    s.ensure_results["index"] = EnsureResult(2, 1, 1, 1, 0, 1, True, ())
    assert s.prepare().input_fingerprint == expected


def test_tampered_preparation_and_invalid_resolution_fail() -> None:
    p = Services().prepare()
    with pytest.raises(ObservationConstructionError, match="identity"):
        construct_observations(REQUEST, replace(p, input_fingerprint="bad"))
    s = Services()
    s.futures = replace(s.futures, records=s.futures.records[1:])
    with pytest.raises(ObservationConstructionError) as error:
        observe(s)
    assert error.value.category == "slot_resolution"


def test_case_dependencies_and_pure_construction() -> None:
    root = Path(futures_basis.__file__).parent
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
        ]
        assert not any(
            name.startswith(("market_statistics", "data_snapshot", "ui_", "tushare"))
            for name in imports
        )
        assert all(
            not name.startswith("data_lake.")
            or name
            in {
                "data_lake.datasets.tushare_trade_calendar",
                "data_lake.datasets.tushare_index_daily",
                "data_lake.datasets.tushare_equity_index_futures",
            }
            for name in imports
        )
        if path.name not in {"preparation.py", "service.py", "__init__.py"}:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    assert (
                        node.func.attr not in {"export", "ensure", "coverage", "now"}
                        or path.name == "validation.py"
                    )


@pytest.mark.parametrize(
    "product,underlying",
    [
        ("IF", "000300.SH"),
        ("IH", "000016.SH"),
        ("IC", "000905.SH"),
    ],
)
def test_other_published_products(product, underlying) -> None:
    from types import SimpleNamespace

    s = Services()
    s.request = replace(s.request, product_code=product)
    s.futures = replace(
        s.futures,
        scope=SimpleNamespace(product_codes=(product,)),
        records=tuple(
            replace(
                r,
                product_code=product,
                contract_code=product + r.contract_code[2:],
                symbol=product + r.symbol[2:],
                underlying_index_code=underlying,
            )
            for r in s.futures.records
        ),
    )
    s.index = replace(
        s.index,
        scope=SimpleNamespace(index_codes=(underlying,)),
        records=tuple(
            replace(r, index_code=underlying, symbol=underlying[:6]) for r in s.index.records
        ),
    )
    assert len(observe(s).slot_days) == 8


@pytest.mark.parametrize(
    "change",
    [
        lambda v: replace(v, records=(replace(v.records[0], close=None), *v.records[1:])),
        lambda v: replace(v, records=(replace(v.records[0], amount=-1.0), *v.records[1:])),
        lambda v: replace(
            v, records=(replace(v.records[0], trade_date=date(2024, 10, 19)), *v.records[1:])
        ),
        lambda v: replace(
            v, records=(replace(v.records[0], index_code="000300.SH"), *v.records[1:])
        ),
        lambda v: replace(v, records=(replace(v.records[0], name="conflict"), *v.records[1:])),
        lambda v: replace(v, records=v.records[1:]),
        lambda v: replace(
            v, coverage=replace(v.coverage, requested_units=3, missing_units=1, complete=False)
        ),
    ],
)
def test_illegal_index_facts_and_population_fail(change) -> None:
    s = Services()
    s.index = change(s.index)
    with pytest.raises(InputPreparationError):
        s.prepare()
    assert s.calls[-1] == ("index", "export")


@pytest.mark.parametrize(
    "change",
    [
        lambda r: replace(r, is_open=True),
        lambda r: replace(r, pretrade_date="2024-10-17"),
        lambda r: replace(r, exchange="OTHER"),
        lambda r: replace(r, cal_date=date(2024, 10, 10)),
    ],
)
def test_illegal_calendar_facts_fail_without_repair(change) -> None:
    s = Services()
    value = s.calendars["CFFEX"]
    s.calendars["CFFEX"] = replace(value, records=(change(value.records[0]), *value.records[1:]))
    with pytest.raises(InputPreparationError):
        s.prepare()
    assert s.calls == [("CFFEX", "export")]


@pytest.mark.parametrize(
    "change",
    [
        lambda e: replace(e, records_written=1),
        lambda e: replace(e, attempted_units=True),
        lambda e: replace(e, complete=True),
        lambda e: replace(e, failures=()),
        lambda e: replace(e, requested_units=3),
    ],
)
def test_illegal_ensure_preserves_attempt(change) -> None:
    from data_lake import EnsureResult, UnitFailure

    s = Services()
    s.missing_index()
    s.ensure_results["index"] = change(
        EnsureResult(2, 1, 1, 0, 1, 0, False, (UnitFailure(("000852.SH", DAY), "unavailable"),))
    )
    with pytest.raises(InputPreparationError) as error:
        s.prepare()
    assert error.value.evidence[-1].ensure_result is not None
    assert s.calls[-1] == ("index", "ensure")


def test_operation_error_retains_prior_exports() -> None:
    from data_lake import OperationError

    s = Services()

    def fail(query):
        raise OperationError("synthetic operation failure")

    with pytest.raises(InputPreparationError) as error:
        futures_basis.prepare_inputs(
            REQUEST,
            calendar_service=s,
            futures_service=s,
            index_service=type("BrokenIndex", (), {"export": staticmethod(fail)})(),
        )
    assert error.value.category == "upstream_operation"
    assert len(error.value.evidence) == 4
    assert all(a.final_export is not None for a in error.value.evidence[:3])


def test_live_oracle_rejects_corrupt_metrics_and_harness_isolation(tmp_path) -> None:
    from futures_basis_live_acceptance import isolated_storage, verify

    result = observe(Services())
    assert len(verify(result)) == 3
    first = result.contract_days[0]
    corrupt = replace(first, basis_value=replace(first.basis_value, value=999.0))
    with pytest.raises(AssertionError):
        verify(replace(result, contract_days=(corrupt, *result.contract_days[1:])))
    with isolated_storage(tmp_path / "cache") as audit:
        import sqlite3

        with pytest.raises(AssertionError, match="escaped"):
            sqlite3.connect(tmp_path / "outside.sqlite3")
    assert audit["default_caches_unchanged"] is True


def test_construction_is_deterministic_without_services_or_clock(monkeypatch) -> None:
    from market_research.descriptive.cases.futures_basis import preparation, validation

    prepared = Services().prepare()

    def forbidden(*args, **kwargs):
        raise AssertionError("Pure construction attempted external I/O or clock access")

    class Clock:
        now = staticmethod(forbidden)

    monkeypatch.setattr(validation, "datetime", Clock)
    for name in ("create_calendar_service", "create_futures_service", "create_index_service"):
        monkeypatch.setattr(preparation, name, forbidden)
    first = construct_observations(REQUEST, prepared)
    assert first == construct_observations(REQUEST, prepared)
    assert first.prepared is prepared
