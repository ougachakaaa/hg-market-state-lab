"""Issue #13 public-service execution, diagnostics and read-only compatibility."""

from dataclasses import FrozenInstanceError, replace
from datetime import date
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
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from market_research.descriptive.cases.futures_calendar_spread import (
    CalendarSpreadQueryError,
    InputPreparationError,
    execute_daily_spreads,
    execute_historical_relative_value,
    preparation,
    prepare_inputs_for_execution,
    query_daily_spreads,
    query_historical_relative_value,
)


class ExecutionServices(Services):
    def __init__(self, *args, cold=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.cold = set(cold)
        self.results = {}
        self.faults = {}
        self.final_incomplete = set()
        self.final_malformed = set()
        self.ensured = set()

    def export(self, request):
        if isinstance(request, TradeCalendarRange) and request.exchange == "SSE":
            return super().export(request)
        name = "calendar" if isinstance(request, TradeCalendarRange) else "futures"
        self.calls.append((name, "export", request))
        error = self.faults.get((name, "final_export" if name in self.ensured else "export"))
        if error:
            raise error
        view = getattr(self, name)
        if name in self.final_malformed and name in self.ensured:
            return replace(view, view="wrong")
        if name in self.cold or name in self.final_incomplete:
            return replace(
                view,
                coverage=coverage(view.coverage.requested_units, view.coverage.requested_units),
                records=(),
            )
        return view

    def ensure(self, request):
        name = "calendar" if isinstance(request, TradeCalendarRange) else "futures"
        self.calls.append((name, "ensure", request))
        if error := self.faults.get((name, "ensure")):
            raise error
        self.cold.discard(name)
        self.ensured.add(name)
        view = getattr(self, name)
        n = view.coverage.requested_units
        return self.results.get(name, EnsureResult(n, 0, n, n, 0, len(view.records), True, ()))

    def execute(self):
        return prepare_inputs_for_execution(
            self.product, self.start, self.end, calendar_service=self, futures_service=self
        )


def order(fake):
    return [(dep, op) for dep, op, _ in fake.calls]


@pytest.mark.parametrize("cold", [(), ("calendar",), ("futures",), ("calendar", "futures")])
def test_bounded_exact_sequence_and_final_evidence(cold):
    fake = ExecutionServices(cold=cold)
    prepared = fake.execute()
    expected = []
    for dep in ("calendar", "futures"):
        expected.append((dep, "export"))
        if dep in cold:
            expected.extend(((dep, "ensure"), (dep, "export")))
    assert order(fake) == expected
    assert len(prepared.attempts) == 2
    for attempt, evidence in zip(prepared.attempts, prepared.evidence, strict=True):
        assert attempt.final_export is evidence.export
        assert attempt.request == evidence.request
        assert attempt.final_export.coverage.complete
        assert (attempt.ensure_result is not None) == (attempt.dependency in cold)
        if attempt.dependency not in cold:
            assert attempt.preliminary_export is attempt.final_export
    assert prepared.attempts[1].request.start_date == DAY
    assert prepared.attempts[0].request.exchange == "CFFEX"


@pytest.mark.parametrize("dep", ["calendar", "futures"])
@pytest.mark.parametrize("failures", [False, True])
def test_incomplete_ensure_is_diagnostic_final_export_is_authoritative(dep, failures):
    fake = ExecutionServices(cold=(dep,))
    identity = ("CFFEX" if dep == "calendar" else "IM", DAY)
    fake.results[dep] = EnsureResult(
        1,
        0,
        1,
        0 if failures else 1,
        int(failures),
        0 if failures else (1 if dep == "calendar" else 4),
        False,
        (UnitFailure(identity, "synthetic failure"),) if failures else (),
    )
    prepared = fake.execute()
    attempt = next(a for a in prepared.attempts if a.dependency == dep)
    assert attempt.ensure_result == fake.results[dep]
    assert attempt.final_export.coverage.complete


@pytest.mark.parametrize("dep", ["calendar", "futures"])
def test_final_incomplete_keeps_all_legal_evidence(dep):
    fake = ExecutionServices(cold=(dep,))
    fake.final_incomplete.add(dep)
    with pytest.raises(InputPreparationError) as caught:
        fake.execute()
    error = caught.value
    assert (error.category, error.reason_code, error.operation) == (
        "incomplete_inputs",
        "final_export_incomplete",
        "final_export",
    )
    assert error.attempts[-1].ensure_result is not None
    assert error.attempts[-1].final_export is error.evidence[-1].export
    assert not error.evidence[-1].export.coverage.complete
    if dep == "calendar":
        assert all(call[0] == "calendar" for call in fake.calls)


@pytest.mark.parametrize("dep", ["calendar", "futures"])
@pytest.mark.parametrize("phase", ["export", "ensure", "final_export"])
@pytest.mark.parametrize(
    "exception,code,category",
    [
        (CredentialMissingError, "credential_missing", "upstream_unavailable"),
        (CacheIncompatibleError, "cache_incompatible", "upstream_unavailable"),
        (OperationError, "operation_unavailable", "upstream_unavailable"),
        (InvalidRequestError, "upstream_request_rejected", "input_contract_error"),
    ],
)
def test_typed_errors_keep_safe_diagnostics(dep, phase, exception, code, category):
    fake = ExecutionServices(cold=(dep,) if phase != "export" else ())
    fake.faults[dep, phase] = exception("secret-token-private-path")
    with pytest.raises(CalendarSpreadQueryError) as caught:
        execute_daily_spreads("IM", DAY, calendar_service=fake, futures_service=fake)
    error = caught.value
    assert (error.category, error.reason_code, error.operation) == (category, code, phase)
    assert "secret" not in error.reason
    assert error.attempts[-1].dependency == dep
    assert error.attempts[-1].reason_code == code
    assert isinstance(error.__cause__.__cause__, exception)
    assert len(fake.calls) == (1 if dep == "calendar" else 2) + (
        0 if phase == "export" else 1 if phase == "ensure" else 2
    )


@pytest.mark.parametrize("dep", ["calendar", "futures"])
@pytest.mark.parametrize("final", [False, True])
def test_malformed_export_never_becomes_validated_evidence(dep, final):
    fake = ExecutionServices(cold=(dep,) if final else ())
    if final:
        fake.final_malformed.add(dep)
    else:
        setattr(fake, dep, replace(getattr(fake, dep), view="wrong"))
    with pytest.raises(InputPreparationError) as caught:
        fake.execute()
    error = caught.value
    assert error.reason_code == "malformed_export"
    assert error.attempts[-1].final_export is None
    assert (error.attempts[-1].preliminary_export is not None) == final
    assert all(e.dependency != dep for e in error.evidence)
    if not final:
        assert all(op != "ensure" for _, op in order(fake))


@pytest.mark.parametrize("dep", ["calendar", "futures"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_units", True),
        ("requested_units", 2),
        ("already_successful_units", -1),
        ("already_successful_units", 1),
        ("attempted_units", 2),
        ("succeeded_units", -1),
        ("failed_units", True),
        ("records_written", -1),
        ("complete", 1),
        ("failures", None),
        ("failures", (UnitFailure(("wrong", DAY), "bad"),)),
    ],
)
def test_malformed_ensure_stops_before_final_export(dep, field, value):
    fake = ExecutionServices(cold=(dep,))
    result = EnsureResult(1, 0, 1, 1, 0, 1 if dep == "calendar" else 4, True, ())
    fake.results[dep] = replace(result, **{field: value})
    with pytest.raises(InputPreparationError) as caught:
        fake.execute()
    error = caught.value
    assert (error.reason_code, error.operation) == ("malformed_ensure_result", "ensure")
    assert error.attempts[-1].ensure_result is None
    assert error.attempts[-1].final_export is None
    assert order(fake)[-1] == (dep, "ensure")


@pytest.mark.parametrize(
    "identity,reason",
    [
        (("IM", date(2024, 10, 19)), "outside"),
        (("IM", "2024-10-18"), "type"),
        (("IM", DAY, DAY), "shape"),
        (("IM", DAY), 3),
    ],
)
def test_failure_identity_and_reason_validation(identity, reason):
    fake = ExecutionServices(cold=("futures",))
    fake.results["futures"] = EnsureResult(
        1, 0, 1, 0, 1, 0, False, (UnitFailure(identity, reason),)
    )
    with pytest.raises(InputPreparationError, match="malformed_ensure_result"):
        fake.execute()


def test_duplicate_failures_and_calendar_row_accounting():
    fake = ExecutionServices(DAY, AFTER, cold=("calendar",))
    n = fake.calendar.coverage.requested_units
    fake.results["calendar"] = EnsureResult(
        n,
        0,
        n,
        n - 2,
        2,
        n - 2,
        False,
        (UnitFailure(("CFFEX", DAY), "a"), UnitFailure(("CFFEX", DAY), "b")),
    )
    with pytest.raises(InputPreparationError, match="malformed_ensure_result"):
        fake.execute()
    fake = ExecutionServices(cold=("calendar",))
    fake.results["calendar"] = EnsureResult(1, 0, 1, 1, 0, 4, True, ())
    with pytest.raises(InputPreparationError, match="malformed_ensure_result"):
        fake.execute()


@pytest.mark.parametrize("phase", ["export", "ensure", "final_export"])
def test_programming_error_propagates(phase):
    fake = ExecutionServices(cold=("calendar",))
    fake.faults["calendar", phase] = RuntimeError("programming defect")
    with pytest.raises(RuntimeError, match="programming defect"):
        fake.execute()


@pytest.mark.parametrize("entry", [execute_daily_spreads, execute_historical_relative_value])
def test_execution_and_queries_share_analysis_and_read_only_permissions(entry):
    historical = entry is execute_historical_relative_value
    fake = ExecutionServices(DAY, AFTER if historical else DAY, cold=("calendar", "futures"))
    args = ("IM", DAY, AFTER, "signed_spread", (-100, 0, 100)) if historical else ("IM", DAY)
    executed = entry(*args, calendar_service=fake, futures_service=fake)
    read = Services(DAY, AFTER if historical else DAY)
    query = query_historical_relative_value if historical else query_daily_spreads
    queried = query(*args, calendar_service=read, futures_service=read)
    # Attempts and permission disclosure are the only differences in retained results.
    expected_prepared = replace(executed.prepared_inputs, attempts=())
    assert expected_prepared == queried.prepared_inputs
    assert executed.request == queried.request
    assert executed.case == queried.case
    assert (
        replace(executed.observation_set, prepared_inputs=expected_prepared)
        == queried.observation_set
    )
    if historical:
        assert executed.pairs == queried.pairs
        assert executed.historical_accounting == queried.historical_accounting
        assert all(d.trade_date < AFTER for d in executed.historical_days)
    assert len(read.calls) == 2
    assert len(fake.calls) == 6
    assert "may prepare" in executed.source_context.limitations[2]
    assert "Read-only" in queried.source_context.limitations[2]
    assert executed.source_context.limitations[:2] == queried.source_context.limitations[:2]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"metric": "bad"},
        {"histogram_edges": [1, 0]},
        {"histogram_edges": [0, float("nan")]},
        {"histogram_edges": [1]},
    ],
)
def test_full_historical_validation_before_factories(kwargs, monkeypatch):
    def forbidden():
        pytest.fail("factory called for invalid request")

    monkeypatch.setattr(preparation, "create_calendar_service", forbidden)
    monkeypatch.setattr(preparation, "create_futures_service", forbidden)
    with pytest.raises(CalendarSpreadQueryError) as caught:
        execute_historical_relative_value("IM", DAY, AFTER, **kwargs)
    assert caught.value.category == "invalid_request"


@pytest.mark.parametrize(
    "entry",
    [prepare_inputs_for_execution, execute_daily_spreads, execute_historical_relative_value],
)
def test_invalid_product_before_factories(entry, monkeypatch):
    monkeypatch.setattr(preparation, "create_calendar_service", lambda: pytest.fail("factory"))
    args = ("bad", DAY) if entry is execute_daily_spreads else ("bad", DAY, AFTER)
    with pytest.raises((InputPreparationError, CalendarSpreadQueryError)) as caught:
        entry(*args)
    assert caught.value.category == "invalid_request"


def test_closed_and_empty_universe_need_no_ensure():
    for day, empty in [(date(2024, 10, 19), False), (DAY, True)]:
        fake = ExecutionServices(day, day)
        if empty:
            fake.set_rows(())
        result = execute_daily_spreads("IM", day, calendar_service=fake, futures_service=fake)
        assert order(fake) == [("calendar", "export"), ("futures", "export")]
        assert len(result.day.observations) == (6 if empty else 0)


def test_immutable_ensure_and_preliminary_final_copies():
    fake = ExecutionServices(cold=("calendar",))
    failure = SimpleNamespace(identity=["CFFEX", DAY], reason="diagnostic")
    failures = [failure]
    result = SimpleNamespace(
        requested_units=1,
        already_successful_units=0,
        attempted_units=1,
        succeeded_units=0,
        failed_units=1,
        records_written=0,
        complete=False,
        failures=failures,
    )
    fake.results["calendar"] = result
    fake.calendar = replace(fake.calendar, records=list(fake.calendar.records))
    prepared = fake.execute()
    failure.identity[0] = "changed"
    failure.reason = "changed"
    failures.clear()
    result.failed_units = 999
    fake.calendar.records.clear()
    attempt = prepared.attempts[0]
    assert attempt.ensure_result.failures == (UnitFailure(("CFFEX", DAY), "diagnostic"),)
    assert attempt.ensure_result.failed_units == 1
    assert len(attempt.final_export.records) == 1
    assert attempt.preliminary_export.records == ()
    with pytest.raises(FrozenInstanceError):
        attempt.reason_code = "changed"


def test_lazy_factory_order_and_failure_retains_request(monkeypatch):
    fake = ExecutionServices(cold=("calendar",))
    events = []
    monkeypatch.setattr(
        preparation, "create_calendar_service", lambda: (events.append("calendar") or fake)
    )

    def futures_factory():
        events.append("futures")
        assert order(fake) == [
            ("calendar", "export"),
            ("calendar", "ensure"),
            ("calendar", "export"),
        ]
        raise CredentialMissingError("private")

    monkeypatch.setattr(preparation, "create_futures_service", futures_factory)
    with pytest.raises(InputPreparationError) as caught:
        prepare_inputs_for_execution("IM", DAY, DAY)
    assert events == ["calendar", "futures"]
    assert len(caught.value.evidence) == 1
    assert caught.value.attempts[-1].request.product_codes == ("IM",)
    assert caught.value.attempts[-1].preliminary_export is None


@pytest.mark.parametrize("succeed", [True, False])
def test_partial_preliminary_and_failure_diagnostics_are_owned(succeed):
    fake = ExecutionServices(DAY, AFTER, cold=("calendar",))
    original_export = fake.export
    mutable_row = SimpleNamespace(exchange="CFFEX", cal_date=DAY, is_open=1, pretrade_date=None)
    mutable_rows = [mutable_row]
    preliminary = replace(fake.calendar, coverage=coverage(4, 3), records=mutable_rows)

    def export(request):
        result = original_export(request)
        if isinstance(request, TradeCalendarRange) and "calendar" not in fake.ensured:
            return preliminary
        return result

    fake.export = export
    failure = SimpleNamespace(identity=["CFFEX", AFTER], reason="retained")
    raw = SimpleNamespace(
        requested_units=4,
        already_successful_units=1,
        attempted_units=3,
        succeeded_units=2,
        failed_units=1,
        records_written=2,
        complete=False,
        failures=[failure],
    )
    fake.results["calendar"] = raw
    if succeed:
        attempt = fake.execute().attempts[0]
    else:
        fake.final_incomplete.add("calendar")
        with pytest.raises(InputPreparationError) as caught:
            fake.execute()
        attempt = caught.value.attempts[0]
    mutable_row.is_open = 0
    mutable_rows.clear()
    failure.identity.clear()
    raw.failures.clear()
    assert len(attempt.preliminary_export.records) == 1
    assert attempt.preliminary_export.records[0].is_open == 1
    assert attempt.ensure_result.failures == (UnitFailure(("CFFEX", AFTER), "retained"),)
    assert attempt.final_export.coverage.complete is succeed


@pytest.mark.parametrize("dep", ["calendar", "futures"])
def test_read_only_incomplete_retains_old_category_and_new_reason(dep):
    from market_research.descriptive.cases.futures_calendar_spread import prepare_inputs

    fake = ExecutionServices(cold=(dep,))
    with pytest.raises(InputPreparationError) as caught:
        prepare_inputs("IM", DAY, DAY, calendar_service=fake, futures_service=fake)
    assert caught.value.category == "incomplete_inputs"
    assert caught.value.reason_code == "cache_incomplete"
    assert caught.value.attempts == ()
    assert order(fake)[-1] == (dep, "export")
    assert len(fake.calls) == (1 if dep == "calendar" else 2)


def test_successful_empty_futures_unit_writes_zero_records():
    fake = ExecutionServices(cold=("futures",))
    fake.set_rows(())
    prepared = fake.execute()
    result = prepared.attempts[1].ensure_result
    assert result.succeeded_units == 1
    assert result.records_written == 0
    assert prepared.futures_export.coverage.complete
    assert prepared.futures_export.records == ()


def test_missing_ensure_fields_are_not_validated_evidence():
    fake = ExecutionServices(cold=("calendar",))
    fake.results["calendar"] = SimpleNamespace(complete=True)
    with pytest.raises(InputPreparationError) as caught:
        fake.execute()
    assert caught.value.reason_code == "malformed_ensure_result"
    assert caught.value.attempts[-1].ensure_result is None
    assert order(fake) == [("calendar", "export"), ("calendar", "ensure")]
