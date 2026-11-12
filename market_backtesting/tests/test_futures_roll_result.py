"""Independent WP4 result/evidence oracle, failure and projection acceptance."""

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from math import inf, nan
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long import (
    FuturesRollError,
    build_backtest_result,
    build_evidence_package,
    decode_evidence_package,
    encode_evidence_package,
    reproduce_futures_roll_evidence,
    validate_backtest_result,
)
from market_backtesting.cases.futures_roll_long.evidence import _json
from market_backtesting.cases.futures_roll_long.fingerprint import (
    canonical_input_bytes,
    decode_canonical_inputs,
    input_fingerprint,
    strict_json,
)
from market_backtesting.cases.futures_roll_long.result_models import LIMITATIONS
from public_input_fixtures import DAYS, fake_services, public_exports, request


def execution(profile: str = "expiry_to_M1_v1") -> Any:
    return fake_services()[0].run(request(profile))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "profile,pnl,new",
    [
        ("expiry_to_M1_v1", (0, 10000, 10000, 4000, -2000), "IM2504.CFX"),
        ("expiry_to_Q1_v1", (0, 10000, 10000, 1000, -2000), "IM2506.CFX"),
    ],
)
def test_result_oracle(profile: str, pnl: tuple[int, ...], new: str) -> None:
    run = execution(profile)
    result = build_backtest_result(run)
    assert tuple(d.daily_pnl for d in result.daily) == pnl
    assert result.summary.total_pnl == sum(pnl)
    assert result.summary.gross_return == pytest.approx(sum(pnl) / 1200000, abs=1e-15)
    assert result.summary.benchmark_return == pytest.approx(0.0125, abs=1e-15)
    assert result.initial_notional.value == 1200000
    assert result.benchmark.index_name == "中证1000"
    assert tuple(d.trade_date for d in result.daily) == DAYS
    assert result.daily[0].previous_close is None
    assert result.daily[0].close == 5900
    assert result.daily[2].pnl_contract_code == "IM2503.CFX"
    assert result.daily[2].position_contract_code == new
    assert result.daily[2].previous_close == 5950
    assert result.daily[2].close == 6000
    assert result.daily[3].previous_close == (6010 if "M1" in profile else 6025)
    assert result.daily[-1].position_contract_code is None
    assert [t.side for t in result.trades] == ["BUY", "SELL", "BUY", "SELL"]
    assert [t.reason for t in result.trades] == [
        "entry",
        "expiry_close",
        "expiry_open",
        "study_end_close",
    ]
    assert [t.selection_slot for t in result.trades] == [
        "M1",
        None,
        "M1" if "M1" in profile else "Q1",
        None,
    ]
    assert [t.multiplier for t in result.trades] == [200] * 4
    assert result.summary.execution_count == 4 and result.summary.roll_count == 1
    assert result.rolls[0].old_slot == "M0"
    assert result.profile == "futures_roll_long_result_v1"
    assert result.case == result.request.case == "futures_roll_long_v1"
    assert (
        result.definition_version
        == run.inputs.definition_version
        == ("futures_roll_long_definition_v1")
    )
    assert result.evidence.input_profile == "futures_roll_long_inputs_v1"
    assert (
        len({result.profile, result.case, result.definition_version, result.evidence.input_profile})
        == 4
    )
    assert result.evidence.limitations == LIMITATIONS
    for view, fields in (
        (result.views.returns, ("cumulative_return", "benchmark_cumulative_return")),
        (result.views.drawdown, ("drawdown", "benchmark_drawdown")),
    ):
        assert view.version == 2
        for binding, field in zip(view.layers, fields, strict=True):
            assert tuple(m.x for m in binding.layer.data) == tuple(d.isoformat() for d in DAYS)
            assert tuple(m.y for m in binding.layer.data) == tuple(
                getattr(d, field) for d in result.daily
            )
            assert binding.layer.y.unit == "decimal_ratio"
            assert {m.segment_id for m in binding.layer.data} == {"series"}
        assert [e.label for e in view.events] == ["Entry", "Roll", "Exit"]
        assert [e.x for e in view.events] == [DAYS[i].isoformat() for i in (0, 2, 4)]
    assert result == build_backtest_result(run)
    with pytest.raises(FrozenInstanceError):
        result.views.returns.layers[0].layer.data[0].y = 42  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.summary.total_pnl = 42  # type: ignore[misc]


def test_ordinary_projection_never_replays_or_analyzes(monkeypatch: Any) -> None:
    run = execution()

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("unexpected numerical execution")

    monkeypatch.setattr(
        "market_backtesting.cases.futures_roll_long.replay.replay_futures_roll", forbidden
    )
    monkeypatch.setattr(
        "market_backtesting.cases.futures_roll_long.performance.analyze_futures_roll", forbidden
    )
    assert build_backtest_result(run).summary.total_pnl == 22000


def test_requested_and_observed_dates_are_distinct() -> None:
    views = public_exports()
    start, end = DAYS[0] - timedelta(days=1), DAYS[-1] + timedelta(days=1)
    from data_lake.datasets.tushare_trade_calendar import TradeCalendarRecord

    window = replace(views.calendar_cffex.window, start_date=start, end_date=end)
    cal = replace(
        views.calendar_cffex,
        window=window,
        coverage=replace(
            views.calendar_cffex.coverage,
            requested_units=len(views.calendar_cffex.records) + 2,
            successful_units=len(views.calendar_cffex.records) + 2,
        ),
        records=(
            TradeCalendarRecord("CFFEX", start, 0, None),
            *views.calendar_cffex.records,
            TradeCalendarRecord("CFFEX", end, 0, None),
        ),
    )
    views = replace(
        views,
        calendar_cffex=cal,
        futures=replace(views.futures, window=window),
        index=replace(views.index, window=window),
    )
    run = fake_services(views)[0].run(replace(request(), start_date=start, end_date=end))
    result = build_backtest_result(run)
    assert (result.request.start_date, result.request.end_date) == (start, end)
    assert (result.window.first_session, result.window.last_session) == (DAYS[0], DAYS[-1])


@pytest.mark.parametrize(
    "field",
    [
        "profile",
        "case",
        "definition_version",
        "status",
        "daily",
        "summary",
        "trades",
        "rolls",
        "evidence",
        "views",
        "request",
        "window",
        "benchmark",
        "initial_notional",
    ],
)
def test_result_cross_field_corruption(field: str) -> None:
    run = execution()
    result = build_backtest_result(run)
    changes: dict[str, Any] = {
        "profile": "wrong",
        "case": "wrong",
        "definition_version": "wrong",
        "status": "partial",
        "daily": result.daily[::-1],
        "summary": replace(result.summary, total_pnl=1),
        "trades": result.trades[:-1],
        "rolls": (),
        "evidence": replace(result.evidence, input_fingerprint="0" * 64),
        "views": replace(result.views, returns=result.views.drawdown),
        "request": replace(result.request, strategy_profile="expiry_to_Q1_v1"),
        "window": replace(result.window, cffex_session_count=99),
        "benchmark": replace(result.benchmark, first_close=1),
        "initial_notional": replace(result.initial_notional, value=1),
    }
    with pytest.raises(FuturesRollError):
        validate_backtest_result(replace(result, **{field: changes[field]}), run)


@pytest.mark.parametrize(
    "field",
    [
        "daily_pnl",
        "equity",
        "benchmark_equity",
        "previous_close",
        "close",
        "drawdown",
        "benchmark_daily_return",
    ],
)
@pytest.mark.parametrize("value", [nan, inf, -inf, True, 10**400])
def test_invalid_result_numeric(field: str, value: Any) -> None:
    run = execution()
    result = build_backtest_result(run)
    with pytest.raises(FuturesRollError):
        validate_backtest_result(
            replace(result, daily=(replace(result.daily[0], **{field: value}), *result.daily[1:])),
            run,
        )


@pytest.mark.parametrize("profile", ["expiry_to_M1_v1", "expiry_to_Q1_v1"])
def test_portable_offline_reproduction(profile: str, monkeypatch: Any) -> None:
    run = execution(profile)
    result = build_backtest_result(run)
    package = build_evidence_package(run, result)
    payload = encode_evidence_package(package)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("upstream I/O forbidden")

    monkeypatch.setattr("public_input_fixtures.FakeService.export", forbidden)
    monkeypatch.setattr("public_input_fixtures.FakeService.ensure", forbidden)
    monkeypatch.setattr(
        "market_backtesting.cases.futures_roll_long.application.create_calendar_service", forbidden
    )
    assert encode_evidence_package(decode_evidence_package(payload)) == payload
    verification = reproduce_futures_roll_evidence(payload, result)
    assert verification.status == "verified"
    assert verification.result == result
    assert verification.daily_record_count == 5
    assert verification.state_event_count == 8  # open / mark / mark-close-open / mark / mark-close
    assert package == build_evidence_package(run, result)
    raw = strict_json(payload)
    assert raw["auxiliary_sse_calendar"]["scope"]["exchange"] == "SSE"
    assert set(raw["canonical_inputs"]) == {"profile", "calendar_cffex", "futures", "index"}
    assert [e["kind"] for e in raw["replay"]["replay"]["daily"][1]["transition"]["events"]] == [
        "mark"
    ]
    for forbidden_text in ("/tmp/", "sqlite3", "token", "Traceback", "diagnostics"):
        assert forbidden_text not in payload.decode()


@pytest.mark.parametrize(
    "fault",
    [
        "fact",
        "fingerprint",
        "event",
        "daily_missing",
        "daily_order",
        "portfolio",
        "accounting",
        "performance",
        "result",
        "extra",
        "request",
        "auxiliary",
        "association",
        "nonfinite",
        "bool",
    ],
)
def test_evidence_tampering_rejected(fault: str) -> None:
    run = execution()
    raw = strict_json(
        encode_evidence_package(build_evidence_package(run, build_backtest_result(run)))
    )
    records = raw["replay"]["replay"]["daily"]
    if fault == "fact":
        raw["canonical_inputs"]["futures"]["records"][0]["close"] = ["float64", (123.0).hex()]
    elif fault == "fingerprint":
        raw["input_fingerprint"] = "0" * 64
    elif fault == "event":
        records[1]["transition"]["events"] = []
    elif fault == "daily_missing":
        records.pop()
    elif fault == "daily_order":
        records.reverse()
    elif fault == "portfolio":
        records[1]["transition"]["next_portfolio"]["position"]["reference_price"] = 123
    elif fault == "accounting":
        records[1]["accounting"]["daily_return"] = 123
    elif fault == "performance":
        raw["performance"]["daily"][1]["drawdown"] = -0.5
    elif fault == "result":
        raw["result"]["summary"]["total_pnl"] = 123
    elif fault == "extra":
        raw["replay"]["extra"] = "unknown"
    elif fault == "request":
        raw["request"]["strategy_profile"] = "expiry_to_Q1_v1"
    elif fault == "auxiliary":
        raw["auxiliary_sse_calendar"]["records"].pop()
    elif fault == "association":
        raw["associations"]["definition_version"] = "wrong"
    elif fault == "bool":
        raw["canonical_inputs"]["calendar_cffex"]["records"][0]["is_open"] = True
    else:
        with pytest.raises(FuturesRollError):
            reproduce_futures_roll_evidence(b'{"value": NaN}')
        return
    with pytest.raises(FuturesRollError):
        reproduce_futures_roll_evidence(_json(raw))


def test_duplicate_keys_and_wrong_expected_result_rejected() -> None:
    with pytest.raises(FuturesRollError):
        decode_evidence_package(b'{"profile":1,"profile":2}')
    run = execution()
    result = build_backtest_result(run)
    payload = encode_evidence_package(build_evidence_package(run, result))
    with pytest.raises(FuturesRollError):
        reproduce_futures_roll_evidence(payload, replace(result, status="wrong"))  # type: ignore[arg-type]


def test_input_identity_preserved_and_auxiliary_independent() -> None:
    m1, q1 = execution(), execution("expiry_to_Q1_v1")
    assert m1.input_fingerprint == q1.input_fingerprint
    assert (
        m1.input_fingerprint == "5edcf4bad7ff0232471cda6d83bfbf423ac27ad659bd04659863d9621377b480"
    )
    assert canonical_input_bytes(
        decode_canonical_inputs(canonical_input_bytes(m1.inputs.exports))
    ) == (canonical_input_bytes(m1.inputs.exports))
    auxiliary = m1.inputs.index_calendar_export
    auxiliary = replace(
        auxiliary,
        records=(
            replace(auxiliary.records[0], pretrade_date=DAYS[0] - timedelta(days=3)),
            *auxiliary.records[1:],
        ),
    )
    changed = replace(m1, inputs=replace(m1.inputs, index_calendar_export=auxiliary))
    result = build_backtest_result(changed)
    assert result.evidence.input_fingerprint == input_fingerprint(m1.inputs.exports)
    payload = encode_evidence_package(build_evidence_package(changed, result))
    assert reproduce_futures_roll_evidence(payload).result == result


def test_final_session_expiry_closes_without_roll() -> None:
    exports = public_exports()
    end = DAYS[2]
    window = replace(exports.calendar_cffex.window, end_date=end)
    calendar = exports.calendar_cffex
    records = tuple(r for r in calendar.records if r.cal_date <= end)
    calendar = replace(
        calendar,
        window=window,
        records=records,
        coverage=replace(
            calendar.coverage, requested_units=len(records), successful_units=len(records)
        ),
    )
    futures = replace(
        exports.futures,
        window=window,
        records=tuple(r for r in exports.futures.records if r.trade_date <= end),
        coverage=replace(exports.futures.coverage, requested_units=3, successful_units=3),
    )
    index = replace(
        exports.index,
        window=window,
        records=tuple(r for r in exports.index.records if r.trade_date <= end),
        coverage=replace(exports.index.coverage, requested_units=3, successful_units=3),
    )
    run = fake_services(replace(exports, calendar_cffex=calendar, futures=futures, index=index))[
        0
    ].run(replace(request(), end_date=end))
    result = build_backtest_result(run)
    assert result.rolls == ()
    assert [t.reason for t in result.trades] == ["entry", "study_end_close"]
    assert [e.kind for e in run.replay.replay.daily[-1].transition.events] == ["mark", "close"]
    assert result.daily[-1].position_contract_code is None
    assert result.daily[-1].pnl_contract_code == "IM2503.CFX"
    assert (
        reproduce_futures_roll_evidence(
            encode_evidence_package(build_evidence_package(run, result))
        ).result
        == result
    )


@pytest.mark.parametrize(
    "fault",
    [
        "mark",
        "order",
        "missing",
        "state",
        "pricing",
        "multiplier",
        "accounting",
        "summary",
        "nonfinite",
        "zero_equity",
    ],
)
def test_execution_corruption_is_rejected_before_projection(fault: str) -> None:
    run = execution()
    records = list(run.replay.replay.daily)
    row = records[2]
    transition = row.transition
    if fault == "mark":
        transition = replace(transition, events=transition.events[1:])
    elif fault == "state":
        transition = replace(transition, next_portfolio=transition.previous_portfolio)
    elif fault == "pricing":
        transition = replace(transition, pricing=replace(transition.pricing, current_close=1))
    elif fault == "multiplier":
        event = transition.events[-1]
        after = replace(event.after, instrument=replace(event.after.instrument, multiplier=300))
        transition = replace(
            transition, events=(*transition.events[:-1], replace(event, after=after))
        )
    elif fault == "accounting":
        row = replace(row, accounting=replace(row.accounting, cumulative_pnl=123))
    elif fault == "nonfinite":
        row = replace(row, accounting=replace(row.accounting, daily_return=nan))
    elif fault == "zero_equity":
        row = replace(row, accounting=replace(row.accounting, equity=0))
    elif fault == "summary":
        run = replace(
            run,
            performance=replace(
                run.performance, summary=replace(run.performance.summary, total_pnl=123)
            ),
        )
    records[2] = replace(row, transition=transition)
    if fault == "order":
        records.reverse()
    elif fault == "missing":
        records.pop()
    run = replace(
        run, replay=replace(run.replay, replay=replace(run.replay.replay, daily=tuple(records)))
    )
    with pytest.raises(FuturesRollError):
        build_backtest_result(run)


def test_result_uses_recorded_core_accumulation_not_compensated_sum() -> None:
    # Independent binary64 order oracle. Inject recorded values to exercise result
    # projection, not to claim these sentinels came from the retained market prices.
    from market_backtesting.cases.futures_roll_long import analyze_futures_roll

    run = execution()
    records = tuple(
        replace(
            record,
            transition=replace(record.transition, daily_pnl=pnl),
            accounting=replace(
                record.accounting,
                cumulative_pnl=cumulative,
                equity=1200000.0 + cumulative,
                daily_return=pnl / 1200000.0,
                cumulative_return=cumulative / 1200000.0,
            ),
        )
        for record, pnl, cumulative in zip(
            run.replay.replay.daily,
            (0.0, 1.0, 1e-16, 1e-16, -1.0),
            (0.0, 1.0, 1.0, 1.0, 0.0),
            strict=True,
        )
    )
    replay = replace(run.replay, replay=replace(run.replay.replay, daily=records))
    run = replace(run, replay=replay, performance=analyze_futures_roll(replay))
    result = build_backtest_result(run)
    assert result.summary.total_pnl == 0.0
    assert sum(d.daily_pnl for d in result.daily) == 2e-16  # Python 3.13 compensated sum


def test_raw_acquisition_diagnostics_never_enter_public_evidence() -> None:
    from data_lake import EnsureResult, UnitFailure
    from market_backtesting.cases.futures_roll_long import EnsureDiagnostic

    run = execution()
    diagnostics = (
        EnsureDiagnostic(
            "futures",
            EnsureResult(
                1,
                0,
                1,
                0,
                1,
                0,
                False,
                (UnitFailure(("IM", DAYS[0]), "secret-token /private/cache.sqlite raw exception"),),
            ),
        ),
    )
    run = replace(run, inputs=replace(run.inputs, diagnostics=diagnostics))
    result = build_backtest_result(run)
    payload = encode_evidence_package(build_evidence_package(run, result))
    assert b"secret-token" not in payload and b"/private/" not in payload
    assert reproduce_futures_roll_evidence(payload).result == result


@pytest.mark.parametrize(
    "fault",
    [
        "profile",
        "field",
        "missing_field",
        "date",
        "hex",
        "nonfinite_hex",
        "float_type",
        "counter_type",
        "schema_type",
    ],
)
def test_strict_portable_input_decoder(fault: str) -> None:
    raw = strict_json(canonical_input_bytes(public_exports()))
    if fault == "profile":
        raw["profile"] = "unknown"
    elif fault == "field":
        raw["futures"]["records"][0]["extra"] = "bad"
    elif fault == "missing_field":
        del raw["index"]["records"][0]["name"]
    elif fault == "date":
        raw["calendar_cffex"]["records"][0]["cal_date"] += "T00:00:00"
    elif fault == "hex":
        raw["futures"]["records"][0]["close"] = ["float64", "0x1p0"]
    elif fault == "nonfinite_hex":
        raw["futures"]["records"][0]["close"] = ["float64", "inf"]
    elif fault == "float_type":
        raw["futures"]["records"][0]["close"] = "6000"
    elif fault == "counter_type":
        raw["index"]["coverage"]["requested_units"] = True
    else:
        raw["index"]["export_schema_version"] = True
    with pytest.raises(FuturesRollError):
        decode_canonical_inputs(_json(raw))
