"""DD-02 independent reference acquisition through deterministic public services."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta
from types import SimpleNamespace

import pytest

from calendar_spread_fixtures import AFTER, DAY, Services, coverage
from data_lake import (
    CacheIncompatibleError,
    CredentialMissingError,
    EnsureResult,
    InvalidRequestError,
    OperationError,
    UnitFailure,
)
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRange, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, TradeCalendarRecord
from market_research.descriptive.cases import futures_calendar_spread as case
from market_research.descriptive.cases.futures_calendar_spread import daily_index


class ReferenceServices(Services):
    def __init__(self, product="IM", *, cold=(), closed=False):
        super().__init__(product=product)
        self.events = []
        self.cold = set(cold)
        self.ensured = set()
        self.still_missing = set()
        self.faults = {}
        self.ensure_results = {}
        self.sse = replace(
            self.calendar,
            scope=SimpleNamespace(exchange="SSE"),
            records=(TradeCalendarRecord("SSE", DAY, int(not closed), None),),
        )
        code = self.futures.records[0].underlying_index_code
        values = {f.name: 1.0 for f in fields(IndexDailyRow)}
        values.update(
            index_code=code,
            symbol=code[:6],
            name="synthetic",
            market="SSE",
            publisher=None,
            category=None,
            trade_date=DAY,
            close=3500.123456789,
        )
        self.index = IndexDailyExport(
            "tushare_index_daily",
            "index_daily",
            1,
            SimpleNamespace(index_codes=(code,)),
            self.calendar.window,
            coverage(1),
            (IndexDailyRow(**values),),
        )

    def export(self, request):
        if isinstance(request, TradeCalendarRange) and request.exchange == "CFFEX":
            self.events.append(("core_calendar", "export"))
            return super().export(request)
        if not isinstance(request, TradeCalendarRange | IndexDailyRange):
            self.events.append(("core_futures", "export"))
            return super().export(request)
        dep = "sse" if isinstance(request, TradeCalendarRange) else "index"
        phase = "final_export" if dep in self.ensured else "export"
        self.events.append((dep, phase))
        value = self.faults.get((dep, phase))
        if isinstance(value, Exception):
            raise value
        if value is not None:
            return value
        view = getattr(self, dep)
        if dep in self.cold or dep in self.still_missing:
            return replace(view, coverage=coverage(1, 1), records=())
        return view

    def ensure(self, request):
        dep = "sse" if isinstance(request, TradeCalendarRange) else "index"
        self.events.append((dep, "ensure"))
        value = self.faults.get((dep, "ensure"))
        if isinstance(value, Exception):
            raise value
        self.cold.discard(dep)
        self.ensured.add(dep)
        return self.ensure_results.get(dep, EnsureResult(1, 0, 1, 1, 0, 1, True, ()))

    def run(self, execution=False):
        entry = case.execute_daily_spreads if execution else case.query_daily_spreads
        return entry(
            self.product, DAY, calendar_service=self, futures_service=self, index_service=self
        )


def state(result):
    ref = result.underlying_index
    return ref.availability, ref.reason_code, ref.failure_category


@pytest.mark.parametrize("product", ["IF", "IH", "IC", "IM"])
@pytest.mark.parametrize("close", [0.0, -5.0, 3500.123456789])
def test_selection_finite_prices_and_hot_order(product, close):
    fake = ReferenceServices(product)
    fake.index = replace(fake.index, records=(replace(fake.index.records[0], close=close),))
    result = fake.run()
    ref = result.underlying_index
    assert state(result) == ("available", None, None)
    assert ref.close == close and ref.trade_date == DAY
    assert ref.index_code == fake.futures.records[0].underlying_index_code
    assert fake.events == [
        ("core_calendar", "export"),
        ("core_futures", "export"),
        ("sse", "export"),
        ("index", "export"),
    ]
    for attempt in result.underlying_index_evidence.attempts:
        assert attempt.preliminary_export is attempt.final_export
        assert attempt.ensure_result is None
        assert attempt.request.start_date == attempt.request.end_date == DAY
        assert type(attempt.final_export.records) is tuple
    with pytest.raises(FrozenInstanceError):
        ref.close = 10


def test_independent_closures_and_empty_core():
    fake = ReferenceServices(closed=True)
    result = fake.run(True)
    assert state(result) == ("not_applicable", "non_trading_day", None)
    assert len(result.day.observations) == 6
    assert fake.events[-1] == ("sse", "export")
    fake = ReferenceServices()
    fake.calendar = replace(fake.calendar, records=(TradeCalendarRecord("CFFEX", DAY, 0, None),))
    fake.futures = replace(fake.futures, coverage=coverage(0), records=())
    result = fake.run()
    assert result.day.status == "closed" and not result.day.observations
    assert state(result) == ("available", None, None)
    fake = ReferenceServices()
    fake.set_rows(())
    result = fake.run()
    assert result.accounting.not_applicable_count == 6
    assert state(result) == ("available", None, None)


@pytest.mark.parametrize("dep", ["sse", "index"])
def test_read_only_incomplete_and_execution_final_incomplete(dep):
    fake = ReferenceServices(cold=(dep,))
    result = fake.run()
    assert state(result) == ("unavailable", "cache_incomplete", None)
    assert result.underlying_index.close is None
    assert not any(op == "ensure" for _, op in fake.events)
    assert len(result.day.observations) == 6
    fake.still_missing.add(dep)
    result = fake.run(True)
    assert state(result) == ("error", "final_export_incomplete", "incomplete_inputs")
    evidence = result.underlying_index_evidence
    assert evidence.operation == "final_export"
    assert evidence.attempts[-1].ensure_result.complete
    assert not evidence.attempts[-1].final_export.coverage.complete


@pytest.mark.parametrize("cold", [("sse",), ("index",), ("sse", "index")])
@pytest.mark.parametrize("failures", [False, True])
def test_bounded_ensure_and_final_export_authority(cold, failures):
    fake = ReferenceServices(cold=cold)
    for dep in cold:
        code = "SSE" if dep == "sse" else fake.index.records[0].index_code
        fake.ensure_results[dep] = EnsureResult(
            1,
            0,
            1,
            int(not failures),
            int(failures),
            int(not failures),
            False,
            (UnitFailure((code, DAY), "private provider diagnostic"),) if failures else (),
        )
    result = fake.run(True)
    assert state(result) == ("available", None, None)
    expected = [("core_calendar", "export"), ("core_futures", "export")]
    for dep in ("sse", "index"):
        expected.append((dep, "export"))
        if dep in cold:
            expected.extend(((dep, "ensure"), (dep, "final_export")))
    assert fake.events == expected
    assert all(a.final_export.coverage.complete for a in result.underlying_index_evidence.attempts)


@pytest.mark.parametrize("dep", ["sse", "index"])
@pytest.mark.parametrize("phase", ["export", "ensure", "final_export"])
@pytest.mark.parametrize(
    "error,reason,category",
    [
        (CredentialMissingError, "credential_missing", "upstream_unavailable"),
        (CacheIncompatibleError, "cache_incompatible", "upstream_unavailable"),
        (OperationError, "operation_unavailable", "upstream_unavailable"),
        (InvalidRequestError, "upstream_request_rejected", "input_contract_error"),
    ],
)
def test_public_failures_are_isolated_and_retain_original(dep, phase, error, reason, category):
    fake = ReferenceServices(cold=(dep,) if phase != "export" else ())
    baseline = ReferenceServices().run(True).observation_set
    exception = error("secret provider details")
    fake.faults[dep, phase] = exception
    result = fake.run(True)
    assert result.observation_set == baseline
    assert state(result) == ("error", reason, category)
    evidence = result.underlying_index_evidence
    assert evidence.exception is exception and evidence.operation == phase
    assert evidence.attempts[-1].final_export is None
    assert fake.events[-1] == (dep, phase)


@pytest.mark.parametrize("dep", ["sse", "index"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_units", 2),
        ("already_successful_units", True),
        ("attempted_units", -1),
        ("succeeded_units", 0),
        ("records_written", 2),
        ("complete", 1),
        ("failures", (UnitFailure(("wrong", DAY), "bad"),)),
        ("failures", None),
    ],
)
def test_malformed_ensure_stops_before_final_export(dep, field, value):
    fake = ReferenceServices(cold=(dep,))
    fake.ensure_results[dep] = replace(EnsureResult(1, 0, 1, 1, 0, 1, True, ()), **{field: value})
    result = fake.run(True)
    assert state(result) == ("error", "malformed_ensure_result", "input_contract_error")
    attempt = result.underlying_index_evidence.attempts[-1]
    assert attempt.preliminary_export is not None
    assert attempt.ensure_result is None and attempt.final_export is None
    assert fake.events[-1] == (dep, "ensure")


@pytest.mark.parametrize(
    "dep,field,value",
    [
        ("sse", "dataset", "wrong"),
        ("index", "dataset", "wrong"),
        ("index", "view", "wrong"),
        ("index", "export_schema_version", True),
        ("index", "scope", SimpleNamespace(index_codes=("000300.SH",))),
        ("sse", "scope", SimpleNamespace(exchange="CFFEX")),
        ("sse", "window", SimpleNamespace(start_date=AFTER, end_date=AFTER)),
        ("index", "window", SimpleNamespace(start_date=AFTER, end_date=AFTER)),
        ("index", "coverage", coverage(0)),
        ("sse", "coverage", coverage(2)),
        ("index", "records", ()),
        ("sse", "records", ()),
        ("index", "coverage", replace(coverage(1), complete=False)),
    ],
)
def test_malformed_export_never_ensured(dep, field, value):
    fake = ReferenceServices()
    setattr(fake, dep, replace(getattr(fake, dep), **{field: value}))
    result = fake.run(True)
    assert state(result) == ("error", "malformed_export", "input_contract_error")
    assert not any(op == "ensure" for _, op in fake.events)
    assert result.underlying_index_evidence.attempts[-1].preliminary_export is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("index_code", "000300.SH"),
        ("symbol", "000300"),
        ("trade_date", DAY - timedelta(days=1)),
        ("trade_date", DAY.isoformat()),
        ("close", float("nan")),
        ("close", float("inf")),
        ("close", True),
        ("close", None),
        ("volume", -1.0),
        ("amount", -1.0),
        ("publisher", 1),
        ("name", ""),
    ],
)
def test_all_index_row_fields_and_exact_association(field, value):
    fake = ReferenceServices()
    fake.index = replace(fake.index, records=(replace(fake.index.records[0], **{field: value}),))
    assert state(fake.run()) == ("error", "malformed_export", "input_contract_error")


@pytest.mark.parametrize("dep", ["sse", "index"])
@pytest.mark.parametrize("phase", ["export", "ensure", "final_export"])
def test_unknown_operation_defects_propagate(dep, phase):
    fake = ReferenceServices(cold=(dep,) if phase != "export" else ())
    fake.faults[dep, phase] = RuntimeError("defect")
    with pytest.raises(RuntimeError, match="defect"):
        fake.run(True)


@pytest.mark.parametrize("entry", [case.query_daily_spreads, case.execute_daily_spreads])
def test_core_failure_and_invalid_request_never_start_reference(entry, monkeypatch):
    monkeypatch.setattr(daily_index, "create_index_service", lambda: pytest.fail("index factory"))
    monkeypatch.setattr(daily_index, "create_calendar_service", lambda: pytest.fail("SSE factory"))
    with pytest.raises(case.CalendarSpreadQueryError):
        entry("bad", DAY)
    fake = ReferenceServices()
    fake.errors["futures"] = OperationError("core failed")
    with pytest.raises(case.CalendarSpreadQueryError):
        entry("IM", DAY, calendar_service=fake, futures_service=fake, index_service=fake)
    assert fake.events == [("core_calendar", "export"), ("core_futures", "export")]


def test_historical_never_reaches_reference_factories(monkeypatch):
    monkeypatch.setattr(daily_index, "create_index_service", lambda: pytest.fail("index factory"))
    monkeypatch.setattr(daily_index, "create_calendar_service", lambda: pytest.fail("SSE factory"))
    for entry in (case.query_historical_relative_value, case.execute_historical_relative_value):
        fake = Services(DAY, AFTER)
        result = entry("IM", DAY, AFTER, calendar_service=fake, futures_service=fake)
        assert not fake.reference_calls and len(fake.calls) == 2
        assert not hasattr(result, "underlying_index")
        assert len(result.pairs) == 6 and len(result.current_day.observations) == 6


def test_validated_evidence_owns_mutable_sequences():
    fake = ReferenceServices(cold=("index",))
    row = SimpleNamespace(
        **{f.name: getattr(fake.index.records[0], f.name) for f in fields(IndexDailyRow)}
    )
    rows = [row]
    fake.index = replace(fake.index, records=rows)
    result = fake.run(True)
    row.close = 999
    rows.clear()
    assert result.underlying_index.close == 3500.123456789
    assert len(result.underlying_index_evidence.attempts[-1].final_export.records) == 1


@pytest.mark.parametrize("dep", ["sse", "index"])
@pytest.mark.parametrize("phase", ["export", "final_export"])
def test_malformed_partial_and_final_exports_retain_only_valid_proof(dep, phase):
    fake = ReferenceServices(cold=(dep,) if phase == "final_export" else ())
    # Incomplete coverage cannot excuse rows outside the successful target set.
    fake.faults[dep, phase] = replace(getattr(fake, dep), coverage=coverage(1, 1))
    result = fake.run(True)
    assert state(result) == ("error", "malformed_export", "input_contract_error")
    attempt = result.underlying_index_evidence.attempts[-1]
    assert attempt.final_export is None
    assert (attempt.preliminary_export is not None) == (phase == "final_export")
    assert (attempt.ensure_result is not None) == (phase == "final_export")
    assert fake.events[-1] == (dep, phase)


@pytest.mark.parametrize("dep", ["sse", "index"])
def test_duplicate_rows_rejected(dep):
    fake = ReferenceServices()
    view = getattr(fake, dep)
    setattr(fake, dep, replace(view, records=(*view.records, *view.records)))
    assert state(fake.run()) == ("error", "malformed_export", "input_contract_error")


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange", "CFFEX"),
        ("cal_date", AFTER),
        ("is_open", True),
        ("pretrade_date", "bad"),
    ],
)
def test_sse_row_validation(field, value):
    fake = ReferenceServices()
    fake.sse = replace(fake.sse, records=(replace(fake.sse.records[0], **{field: value}),))
    assert state(fake.run(True)) == ("error", "malformed_export", "input_contract_error")
    assert fake.events[-1] == ("sse", "export")


@pytest.mark.parametrize("dep", ["sse", "index"])
@pytest.mark.parametrize("identity", [("SSE", AFTER), ("SSE", "2024-10-18"), ("SSE", DAY, DAY)])
def test_ensure_failure_target_validation(dep, identity):
    fake = ReferenceServices(cold=(dep,))
    fake.ensure_results[dep] = EnsureResult(
        1, 0, 1, 0, 1, 0, False, (UnitFailure(identity, "private"),)
    )
    assert state(fake.run(True)) == ("error", "malformed_ensure_result", "input_contract_error")
    assert fake.events[-1] == (dep, "ensure")


@pytest.mark.parametrize("factory", ["create_calendar_service", "create_index_service"])
def test_lazy_factory_failures_keep_reached_request(factory, monkeypatch):
    fake = ReferenceServices()
    failure = CredentialMissingError("secret")

    def unavailable():
        raise failure

    baseline = fake.run()
    monkeypatch.setattr(case.queries, "_collect", lambda *args, **kwargs: baseline.observation_set)
    monkeypatch.setattr(daily_index, "create_calendar_service", lambda: fake)
    monkeypatch.setattr(daily_index, "create_index_service", lambda: fake)
    monkeypatch.setattr(daily_index, factory, unavailable)
    result = case.query_daily_spreads("IM", DAY)
    assert state(result) == ("error", "credential_missing", "upstream_unavailable")
    evidence = result.underlying_index_evidence
    assert evidence.exception is failure and evidence.operation == "export"
    assert evidence.attempts[-1].preliminary_export is None
    assert evidence.attempts[-1].request.start_date == DAY


def test_core_construction_failure_never_reaches_reference():
    fake = ReferenceServices()
    fake.set_rows(fake.futures.records[:3])  # illegal active Slot universe
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        fake.run()
    assert caught.value.category == "slot_resolution_error"
    assert fake.events == [("core_calendar", "export"), ("core_futures", "export")]


def test_all_reference_states_preserve_identical_core_observations():
    baseline = ReferenceServices().run(True)
    scenarios = [ReferenceServices(closed=True), ReferenceServices(cold=("index",))]
    incomplete = ReferenceServices(cold=("sse",))
    incomplete.still_missing.add("sse")
    scenarios.append(incomplete)
    for error in (
        CredentialMissingError,
        CacheIncompatibleError,
        OperationError,
        InvalidRequestError,
    ):
        fake = ReferenceServices()
        fake.faults["index", "export"] = error("private")
        scenarios.append(fake)
    malformed = ReferenceServices()
    malformed.index = replace(malformed.index, records=())
    scenarios.append(malformed)
    bad_ensure = ReferenceServices(cold=("index",))
    bad_ensure.ensure_results["index"] = replace(
        EnsureResult(1, 0, 1, 1, 0, 1, True, ()), complete=1
    )
    scenarios.append(bad_ensure)
    for fake in scenarios:
        result = fake.run(True)
        assert result.day == baseline.day and result.accounting == baseline.accounting
        assert result.observation_set == baseline.observation_set
    read = ReferenceServices(cold=("index",)).run()
    assert read.day == baseline.day and read.accounting == baseline.accounting
