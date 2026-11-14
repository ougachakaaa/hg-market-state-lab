"""WP3 fake-service acceptance using the actual public semantic export types."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta
from typing import Any

import pytest

from data_lake import (
    CacheIncompatibleError,
    CredentialMissingError,
    EnsureResult,
    InvalidRequestError,
    OperationError,
    UnitFailure,
)
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyScope
from data_lake.datasets.tushare_index_daily import IndexDailyScope
from market_backtesting.cases.futures_roll_long import (
    FuturesRollApplicationError,
    PublicInputExports,
    analyze_futures_roll,
    replay_futures_roll,
    validate_futures_roll_request,
)
from market_backtesting.cases.futures_roll_long.fingerprint import canonical_input_bytes
from public_input_fixtures import (
    DAYS,
    coverage,
    fake_services,
    public_exports,
    request,
)


def change_record(view: Any, position: int = 0, /, **changes: Any) -> Any:
    rows = list(view.records)
    rows[position] = replace(rows[position], **changes)
    return replace(view, records=tuple(rows))


@pytest.mark.parametrize(
    "profile,total,new_contract",
    [
        ("expiry_to_M1_v1", 22000.0, "IM2504.CFX"),
        ("expiry_to_Q1_v1", 19000.0, "IM2506.CFX"),
    ],
)
def test_full_public_execution_and_roll_attribution(
    profile: Any, total: float, new_contract: str
) -> None:
    service, calendar, futures, index = fake_services()
    result = service.run(request(profile))
    assert result.performance.summary.total_pnl == total
    assert result.performance.summary.initial_notional == 1200000.0
    assert result.performance.summary.benchmark_return == pytest.approx(0.0125)
    assert result.replay.rolls[0].old_contract_code == "IM2503.CFX"
    assert result.replay.rolls[0].new_contract_code == new_contract
    assert result.replay.daily[2].pnl_contract_code == "IM2503.CFX"
    assert result.performance.daily[2].daily_pnl == 10000.0
    assert result.performance.daily[3].daily_pnl == (4000.0 if total == 22000.0 else 1000.0)
    assert result.replay.replay.final_portfolio.position is None
    assert result.observed_start_date == DAYS[0] and result.observed_end_date == DAYS[-1]
    assert result.request.identity == ("futures_roll_long_v1", "IM", DAYS[0], DAYS[-1], profile)
    assert (
        analyze_futures_roll(replay_futures_roll(result.inputs.replay_input)) == result.performance
    )
    assert [name for name, _ in calendar.calls] == ["export", "export"]
    assert all([name for name, _ in source.calls] == ["export"] for source in (futures, index))
    assert result.inputs.exports == public_exports()
    assert all(
        result.input_fingerprint in item.evidence.source_export_ref
        for item in result.inputs.replay_input.decision_slots
    )
    with pytest.raises(FrozenInstanceError):
        result.inputs.input_fingerprint = "changed"


def malformed(case: str) -> PublicInputExports:
    views = public_exports()
    c, f, i = views.calendar_cffex, views.futures, views.index
    if case == "calendar_missing":
        c = replace(c, records=c.records[:-1])
    elif case == "calendar_scope":
        c = replace(c, scope=replace(c.scope, exchange="SSE"))
    elif case == "calendar_schema":
        c = replace(c, export_schema_version=2)
    elif case == "calendar_bool_schema":
        c = replace(c, export_schema_version=True)
    elif case == "calendar_bool_open":
        c = change_record(c, is_open=True)
    elif case == "calendar_duplicate":
        c = replace(c, records=(c.records[0],) + c.records[:-1])
    elif case == "calendar_counter_bool":
        c = replace(c, coverage=replace(c.coverage, missing_units=False))
    elif case == "calendar_counter_sum":
        c = replace(c, coverage=replace(c.coverage, requested_units=100))
    elif case == "calendar_wrong_window":
        c = replace(c, window=replace(c.window, start_date=DAYS[0] - timedelta(days=1)))
    elif case == "futures_duplicate":
        f = replace(f, records=(f.records[0],) + f.records)
    elif case == "metadata_conflict":
        f = change_record(f, 4, multiplier=201.0)
    elif case == "delist_invalid":
        f = change_record(f, delist_date=None)
    elif case == "delist_closed":
        f = change_record(f, delist_date=DAYS[0] + timedelta(days=1))
    elif case == "futures_wrong_product":
        f = replace(f, scope=FuturesDailyScope(("IC",)))
    elif case == "futures_wrong_count":
        f = replace(f, coverage=coverage(100))
    elif case == "futures_continuous":
        f = change_record(f, contract_code="IM.CFX")
    elif case == "futures_outside_date":
        f = change_record(f, trade_date=DAYS[0] + timedelta(days=1))
    elif case == "futures_underlying_conflict":
        f = change_record(f, underlying_index_code="000905.SH")
    elif case == "entry_missing":
        f = replace(
            f,
            records=tuple(
                row
                for row in f.records
                if not (row.trade_date == DAYS[0] and row.contract_code == "IM2503.CFX")
            ),
        )
    elif case == "roll_missing":
        f = replace(
            f,
            records=tuple(
                row
                for row in f.records
                if not (row.trade_date == DAYS[2] and row.contract_code == "IM2504.CFX")
            ),
        )
    elif case == "held_missing":
        f = replace(
            f,
            records=tuple(
                row
                for row in f.records
                if not (row.trade_date == DAYS[1] and row.contract_code == "IM2503.CFX")
            ),
        )
    elif case == "invalid_slots":
        f = replace(
            f,
            records=tuple(
                row
                for row in f.records
                if not (row.trade_date == DAYS[0] and row.contract_code == "IM2509.CFX")
            ),
        )
    elif case == "close_missing":
        f = change_record(f, 1, close=None)
    elif case == "index_identity":
        i = replace(i, scope=IndexDailyScope(("000905.SH",)))
    elif case == "index_row_identity":
        i = change_record(i, index_code="000905.SH")
    elif case == "index_missing_session":
        i = replace(i, records=i.records[:-1], coverage=coverage(4))
    elif case == "index_duplicate":
        i = replace(i, records=(i.records[0],) + i.records[:-1])
    elif case == "index_invalid_date":
        i = change_record(i, trade_date=datetime(2025, 2, 17))
    elif case == "index_nan":
        i = change_record(i, close=float("nan"))
    else:
        raise AssertionError(case)
    return PublicInputExports(c, f, i)


MALFORMED_CASES = (
    "calendar_missing",
    "calendar_scope",
    "calendar_schema",
    "calendar_bool_schema",
    "calendar_bool_open",
    "calendar_duplicate",
    "calendar_counter_bool",
    "calendar_counter_sum",
    "calendar_wrong_window",
    "futures_duplicate",
    "metadata_conflict",
    "delist_invalid",
    "delist_closed",
    "futures_wrong_product",
    "futures_wrong_count",
    "futures_continuous",
    "futures_outside_date",
    "futures_underlying_conflict",
    "entry_missing",
    "roll_missing",
    "held_missing",
    "invalid_slots",
    "close_missing",
    "index_identity",
    "index_row_identity",
    "index_missing_session",
    "index_duplicate",
    "index_invalid_date",
    "index_nan",
)


@pytest.mark.parametrize("case", MALFORMED_CASES)
def test_failure_matrix_never_returns_partial_success_or_repairs_bad_facts(case: str) -> None:
    service, *sources = fake_services(malformed(case))
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert caught.value.category and caught.value.reason
    assert not hasattr(caught.value, "input_fingerprint")
    assert not hasattr(caught.value, "replay")
    assert not any(name == "ensure" for source in sources for name, _ in source.calls)


def incomplete(view: Any, dependency: str) -> Any:
    if dependency == "calendar_cffex":
        rows = view.records[:-1]
    elif dependency == "futures":
        rows = tuple(row for row in view.records if row.trade_date != DAYS[-1])
    else:
        rows = view.records[:-1]
    return replace(
        view,
        records=rows,
        coverage=coverage(view.coverage.requested_units, view.coverage.requested_units - 1),
    )


@pytest.mark.parametrize(
    "dependency,source_index", [("calendar_cffex", 0), ("futures", 1), ("index", 2)]
)
@pytest.mark.parametrize("final_complete", [False, True])
def test_exact_window_single_ensure_then_final_export(
    dependency: str, source_index: int, final_complete: bool
) -> None:
    views = public_exports()
    service, *sources = fake_services(views)
    full = getattr(views, dependency)
    partial = incomplete(full, dependency)
    sources[source_index].exports = [partial, full if final_complete else partial]
    if final_complete:
        result = service.prepare(request())
        assert result.diagnostics[0].dependency == dependency
    else:
        with pytest.raises(FuturesRollApplicationError, match="final_export_incomplete") as caught:
            service.run(request())
        assert len(caught.value.diagnostics) == 1
    calls = sources[source_index].calls
    if dependency == "calendar_cffex":
        calls = [(name, value) for name, value in calls if value.exchange == "CFFEX"]
    assert [name for name, _ in calls] == ["export", "ensure", "export"]
    assert calls[0][1] == calls[1][1] == calls[2][1]


@pytest.mark.parametrize("final_complete", [False, True])
def test_incomplete_ensure_is_diagnostic_and_final_export_is_authoritative(
    final_complete: bool,
) -> None:
    views = public_exports()
    service, _, futures, _ = fake_services(views)
    partial = incomplete(views.futures, "futures")
    futures.exports = [partial, views.futures if final_complete else partial]
    outcome = EnsureResult(
        5, 4, 1, 0, 1, 0, False, (UnitFailure(("IM", DAYS[-1]), "source incomplete"),)
    )
    futures.ensure_result = outcome
    if final_complete:
        assert service.prepare(request()).diagnostics[0].result == outcome
    else:
        with pytest.raises(FuturesRollApplicationError) as caught:
            service.run(request())
        assert caught.value.diagnostics[0].result == outcome
    assert [name for name, _ in futures.calls] == ["export", "ensure", "export"]


@pytest.mark.parametrize("source_index", range(3))
@pytest.mark.parametrize("exception", [OperationError, InvalidRequestError])
def test_public_operation_failures_are_classified_without_raw_details(
    source_index: int, exception: Any
) -> None:
    service, *sources = fake_services()
    sources[source_index].error = exception("sensitive provider/path details")
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert caught.value.stage == "export"
    assert caught.value.category == "upstream_operation"
    assert "sensitive" not in str(caught.value)
    assert caught.value.detail is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("product_code", "im"),
        ("strategy_profile", "M1"),
        ("start_date", datetime(2025, 2, 17)),
        ("end_date", "2025-03-25"),
        ("end_date", date(2999, 1, 1)),
        ("end_date", date(2025, 1, 1)),
        ("start_date", date(2020, 1, 1)),
    ],
)
def test_request_validation_precedes_all_io(field: str, value: Any) -> None:
    service, *sources = fake_services()
    invalid_request = replace(request(), **{field: value})
    for action in (service.prepare, service.run, service.preflight, validate_futures_roll_request):
        with pytest.raises(FuturesRollApplicationError):
            action(invalid_request)
    assert not any(source.calls for source in sources)


def test_extra_sse_date_is_retained_and_fingerprinted_but_not_replayed() -> None:
    views = public_exports()
    extra = replace(views.index.records[0], trade_date=DAYS[0] + timedelta(days=1))
    rows = tuple(sorted((*views.index.records, extra), key=lambda row: row.trade_date))
    augmented = replace(views, index=replace(views.index, records=rows, coverage=coverage(6)))
    service, calendar, _, _ = fake_services(augmented)
    sse = calendar.sse_exports[0]
    calendar.sse_exports = [
        replace(
            sse,
            records=tuple(
                replace(row, is_open=1) if row.cal_date == extra.trade_date else row
                for row in sse.records
            ),
        )
    ]
    result = service.run(request())
    base = fake_services(views)[0].run(request())
    assert result.performance == base.performance
    assert result.replay.sessions == DAYS
    assert result.input_fingerprint != base.input_fingerprint
    assert len(result.inputs.exports.index.records) == 6


def test_fingerprint_encoding_and_determinism() -> None:
    result = fake_services()[0].prepare(request())
    other = fake_services()[0].prepare(request("expiry_to_Q1_v1"))
    encoded = canonical_input_bytes(result.exports)
    payload = json.loads(encoded)
    assert (
        result.input_fingerprint == other.input_fingerprint == hashlib.sha256(encoded).hexdigest()
    )
    assert (
        result.input_fingerprint
        == "5edcf4bad7ff0232471cda6d83bfbf423ac27ad659bd04659863d9621377b480"
    )
    assert payload["profile"] == "futures_roll_long_inputs_v1"
    assert payload["futures"]["records"][0]["multiplier"] == ["float64", (200.0).hex()]
    assert payload["calendar_cffex"]["records"][0]["cal_date"] == DAYS[0].isoformat()
    assert b"\\u4e2d" in encoded
    assert not encoded.endswith(b"\n")
    assert {field.name for field in fields(result.exports.futures.records[0])} == set(
        payload["futures"]["records"][0]
    )
    assert {field.name for field in fields(result.exports.index.records[0])} == set(
        payload["index"]["records"][0]
    )
    assert {field.name for field in fields(result.exports.calendar_cffex.records[0])} == set(
        payload["calendar_cffex"]["records"][0]
    )


@pytest.mark.parametrize(
    "dependency,field,value",
    [
        ("calendar_cffex", "pretrade_date", date(2025, 2, 14)),
        ("futures", "close", 6100.25),
        ("futures", "volume", 1.0),
        ("futures", "close_change_from_pre_settle", -0.0),
        ("index", "close", 6001.0),
        ("index", "publisher", "updated"),
    ],
)
def test_same_request_changed_public_fact_changes_fingerprint(
    dependency: str, field: str, value: Any
) -> None:
    views = public_exports()
    view = change_record(getattr(views, dependency), **{field: value})
    if field == "publisher":
        view = replace(view, records=tuple(replace(row, publisher=value) for row in view.records))
    changed = replace(views, **{dependency: view})
    assert (
        fake_services(changed)[0].prepare(request()).input_fingerprint
        != fake_services(views)[0].prepare(request()).input_fingerprint
    )


@pytest.mark.parametrize("bad", [None, True, float("nan"), float("inf"), -1.0, 0.0])
@pytest.mark.parametrize("dependency", ["futures", "index"])
def test_close_numeric_fail_closed(dependency: str, bad: Any) -> None:
    views = public_exports()
    changed = replace(views, **{dependency: change_record(getattr(views, dependency), close=bad)})
    with pytest.raises(FuturesRollApplicationError):
        fake_services(changed)[0].run(request())


def test_no_slot_resolution_during_prepare_and_once_per_entry_roll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_backtesting.cases.futures_roll_long import policy

    original = policy.resolve_daily_slots
    calls = []

    def tracked(*args: Any, **kwargs: Any) -> Any:
        calls.append(args[1])
        return original(*args, **kwargs)

    monkeypatch.setattr(policy, "resolve_daily_slots", tracked)
    inputs = fake_services()[0].prepare(request())
    assert not calls
    replay_futures_roll(inputs.replay_input)
    assert calls == [DAYS[0], DAYS[2]]


def test_insufficient_sessions_fails_before_market_requests() -> None:
    views = public_exports()
    c = replace(
        views.calendar_cffex,
        records=tuple(replace(row, is_open=0) for row in views.calendar_cffex.records),
    )
    service, _, futures, index = fake_services(replace(views, calendar_cffex=c))
    with pytest.raises(FuturesRollApplicationError, match="insufficient_sessions"):
        service.run(request())
    assert not futures.calls and not index.calls


def test_ensure_failure_is_typed_and_does_not_attempt_another_read() -> None:
    views = public_exports()
    service, _, futures, _ = fake_services()
    futures.exports = [incomplete(views.futures, "futures")]

    def fail(_: object) -> Any:
        raise OperationError("credential unavailable")

    futures.ensure = fail  # type: ignore[method-assign, assignment]
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert caught.value.stage == "ensure"
    assert caught.value.dependency == "futures"
    assert len(futures.calls) == 1


@pytest.mark.parametrize("complete", [False, True])
def test_sse_prerequisite_has_its_own_exact_window_proof_and_single_ensure(complete: bool) -> None:
    service, calendar, _, index = fake_services()
    sse = calendar.sse_exports[0]
    partial = incomplete(sse, "calendar_cffex")
    calendar.sse_exports = [partial, sse if complete else partial]
    if complete:
        prepared = service.prepare(request())
        assert prepared.index_calendar_export == sse
        assert prepared.index_calendar_request.exchange == "SSE"
        assert prepared.diagnostics[0].dependency == "calendar_sse"
    else:
        with pytest.raises(FuturesRollApplicationError) as caught:
            service.prepare(request())
        assert caught.value.dependency == "calendar_sse"
        assert not index.calls
    sse_calls = [(name, value) for name, value in calendar.calls if value.exchange == "SSE"]
    assert [name for name, _ in sse_calls] == ["export", "ensure", "export"]
    assert all(value == sse_calls[0][1] for _, value in sse_calls)


def test_malformed_sse_prerequisite_does_not_ensure_or_query_index() -> None:
    service, calendar, _, index = fake_services()
    calendar.sse_exports = [replace(calendar.sse_exports[0], export_schema_version=2)]
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert caught.value.dependency == "calendar_sse"
    assert not any(name == "ensure" for name, _ in calendar.calls)
    assert not index.calls


@pytest.mark.parametrize(
    "dependency,field", [("futures", "volume"), ("index", "volume"), ("index", "amount")]
)
def test_illegal_negative_source_quantity_is_rejected(dependency: str, field: str) -> None:
    views = public_exports()
    view = change_record(getattr(views, dependency), **{field: -1.0})
    with pytest.raises(FuturesRollApplicationError):
        fake_services(replace(views, **{dependency: view}))[0].prepare(request())


def test_malformed_final_export_is_not_repaired_again() -> None:
    views = public_exports()
    service, _, futures, _ = fake_services()
    futures.exports = [incomplete(views.futures, "futures"), malformed("futures_duplicate").futures]
    with pytest.raises(FuturesRollApplicationError, match="unordered_or_duplicate_contract_date"):
        service.run(request())
    assert [name for name, _ in futures.calls] == ["export", "ensure", "export"]


def test_application_preserves_pure_replay_failure_classification() -> None:
    service, *_ = fake_services(malformed("held_missing"))
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert caught.value.stage == "replay"
    assert caught.value.category == "missing_market_fact"
    assert caught.value.reason == "missing_contract_row"
    assert caught.value.trade_date == DAYS[1]
    assert caught.value.contract_code == "IM2503.CFX"


def test_source_prices_do_not_change_mechanical_targets() -> None:
    views = public_exports()
    changed = replace(
        views,
        futures=replace(
            views.futures,
            records=tuple(replace(row, close=row.close + 123.0) for row in views.futures.records),
        ),
    )
    baseline = fake_services(views)[0].run(request())
    perturbed = fake_services(changed)[0].run(request())

    def identity(result: Any) -> tuple[Any, ...]:
        return tuple(
            (event.trade_date, event.contract_code, event.side, event.reason)
            for event in result.replay.executions
        )

    assert identity(baseline) == identity(perturbed)
    assert baseline.input_fingerprint != perturbed.input_fingerprint


def test_request_maximum_inclusive_span() -> None:
    start = date(2021, 1, 1)
    validate_futures_roll_request(
        replace(request(), start_date=start, end_date=start + timedelta(days=1095))
    )
    with pytest.raises(FuturesRollApplicationError, match="window_too_large"):
        validate_futures_roll_request(
            replace(request(), start_date=start, end_date=start + timedelta(days=1096))
        )


@pytest.mark.parametrize("value", [None, "wrong", True])
def test_invalid_request_object_rejected_without_io(value: Any) -> None:
    service, *sources = fake_services()
    with pytest.raises(FuturesRollApplicationError, match="invalid_request_type"):
        service.run(value)
    assert not any(source.calls for source in sources)


def test_malformed_ensure_result_is_typed_without_success_or_retry() -> None:
    views = public_exports()
    service, _, futures, _ = fake_services()
    futures.exports = [incomplete(views.futures, "futures"), views.futures]
    futures.ensure_result = EnsureResult(5, 0, 5, 4, 0, 16, False, ())
    with pytest.raises(FuturesRollApplicationError, match="invalid_ensure_result"):
        service.run(request())
    assert [name for name, _ in futures.calls] == ["export", "ensure"]


@pytest.mark.parametrize("error,reason", [
    (CacheIncompatibleError("private/path fake-secret"), "cache_incompatible"),
    (CredentialMissingError("required credential absent"), "credential_missing"),
    (OperationError("network fake-secret /private/path"), "operation_unavailable"),
    (OperationError("credential unavailable"), "operation_unavailable"),
])
def test_safe_ensure_classification(error: OperationError, reason: str) -> None:
    from dataclasses import asdict

    from market_backtesting.cases.futures_roll_long.online_models import project_failure

    service, calendar, futures, index = fake_services()
    futures.exports = [incomplete(public_exports().futures, "futures")]
    attempts = []

    def fail(value: object) -> Any:
        attempts.append(value)
        raise error

    futures.ensure = fail  # type: ignore[method-assign, assignment]
    with pytest.raises(FuturesRollApplicationError) as caught:
        service.run(request())
    assert asdict(project_failure(caught.value)) == dict(
        stage="ensure", category="upstream_operation", dependency="futures", reason=reason
    )
    assert len(attempts) == 1
    assert [name for name, _ in futures.calls] == ["export"]
    assert not index.calls
