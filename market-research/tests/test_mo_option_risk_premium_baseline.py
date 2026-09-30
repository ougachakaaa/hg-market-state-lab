"""MO Option Risk Premium Baseline semantics and public-boundary integration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from market_research.studies.mo_option_risk_premium_baseline import cli, evidence, study
from market_research.ui import configuration
from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryError,
    IndexDailyHistoryResult,
    IndexDailyObservation,
)
from market_snapshot.products.mo_option_chain import service as chain_product

EXPIRY = "2026-09-18"
ENTRY = "2026-09-08"
ARGS = [
    "--start-expiry",
    EXPIRY,
    "--end-expiry",
    EXPIRY,
    "--dte-targets",
    "10",
    "--moneyness-targets",
    "0,0.05",
]


def request(
    *, dtes: tuple[int, ...] = (10,), money: tuple[Decimal, ...] = (Decimal("0"), Decimal("0.05"))
) -> study.MOOptionRiskPremiumRequest:
    return study.MOOptionRiskPremiumRequest(EXPIRY, EXPIRY, dtes, money)


def history(
    req: study.MOOptionRiskPremiumRequest,
    dates: tuple[str, ...] = (ENTRY, EXPIRY),
    *,
    closes: tuple[float, ...] = (100.0, 103.0),
) -> IndexDailyHistoryResult:
    query = study.index_request(req)
    return IndexDailyHistoryResult(
        "000852.SH",
        query.start_trade_date,
        query.end_trade_date,
        0,
        (),
        tuple(
            IndexDailyObservation(day, close, None)
            for day, close in zip(dates, closes, strict=True)
        ),
    )


def chain(
    day: str,
    kind: chain_product.PriceType,
    *,
    underlying: float = 100.0,
    calls: tuple[chain_product.OptionPoint, ...] | None = None,
    puts: tuple[chain_product.OptionPoint, ...] | None = None,
    expiry: str = EXPIRY,
) -> chain_product.OptionChain:
    if calls is None:
        calls = (
            chain_product.OptionPoint(
                "C100", 100.0, 5.0 if kind is chain_product.PriceType.HIGH else 3.0
            ),
            chain_product.OptionPoint(
                "C105", 105.0, 2.0 if kind is chain_product.PriceType.HIGH else 1.0
            ),
        )
    if puts is None:
        puts = (
            chain_product.OptionPoint(
                "P95", 95.0, 2.0 if kind is chain_product.PriceType.HIGH else 1.0
            ),
            chain_product.OptionPoint(
                "P100", 100.0, 4.0 if kind is chain_product.PriceType.HIGH else 2.0
            ),
        )
    return chain_product.OptionChain(
        day,
        chain_product.OptionProduct.MO,
        kind,
        chain_product.UnderlyingRef("000852.SH", underlying),
        (chain_product.ExpiryGroup(expiry, None, calls, puts),),
    )


def chains(
    days: tuple[str, ...] = (ENTRY, EXPIRY),
    *,
    underlying: float = 100.0,
    calls: tuple[chain_product.OptionPoint, ...] | None = None,
    puts: tuple[chain_product.OptionPoint, ...] | None = None,
    expiry: str = EXPIRY,
) -> dict[str, tuple[chain_product.OptionChain, chain_product.OptionChain]]:
    return {
        day: (
            chain(
                day,
                chain_product.PriceType.HIGH,
                underlying=underlying,
                calls=calls,
                puts=puts,
                expiry=expiry,
            ),
            chain(
                day,
                chain_product.PriceType.LOW,
                underlying=underlying,
                calls=calls,
                puts=puts,
                expiry=expiry,
            ),
        )
        for day in days
    }


def test_request_canonicalization_and_exact_run_identity() -> None:
    defaults = study.MOOptionRiskPremiumRequest(EXPIRY, EXPIRY)
    explicit = study.MOOptionRiskPremiumRequest(
        EXPIRY,
        EXPIRY,
        (60, 50, 40, 30, 20, 10, 10),
        (
            Decimal("0.200"),
            Decimal("0.15"),
            Decimal("0.10"),
            Decimal("0.05"),
            Decimal("-0"),
            Decimal("0"),
        ),
    )
    assert defaults == explicit
    assert study.canonical_request(defaults)["moneyness_targets"] == [
        "0",
        "0.05",
        "0.1",
        "0.15",
        "0.2",
    ]
    assert study.run_key(defaults) == study.run_key(explicit)
    assert len(study.run_key(defaults).rsplit("__", 1)[1]) == 64
    canonical = (
        '{"start_expiry_date":"2026-09-18","end_expiry_date":"2026-09-18",'
        '"dte_targets":[10,20,30,40,50,60],'
        '"moneyness_targets":["0","0.05","0.1","0.15","0.2"]}'
    )
    assert study.run_key(defaults) == (
        f"{EXPIRY}__{EXPIRY}__{hashlib.sha256(canonical.encode()).hexdigest()}"
    )
    assert study.run_key(defaults) != study.run_key(replace(defaults, dte_targets=(10,)))
    assert study.run_key(defaults) != study.run_key(replace(defaults, end_expiry_date="2026-09-19"))
    assert (
        cli._request(
            cli.build_parser().parse_args(["--start-expiry", EXPIRY, "--end-expiry", EXPIRY])
        )
        == defaults
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["--dte-targets", ""],
        ["--dte-targets", "0"],
        ["--dte-targets", "1.5"],
        ["--moneyness-targets", ""],
        ["--moneyness-targets", "-0.01"],
        ["--moneyness-targets", "NaN"],
        ["--moneyness-targets", "Infinity"],
        ["--start-expiry", "2026-09-31"],
        ["--end-expiry", "2026-09-01"],
    ],
)
def test_bad_input_fails_before_configuration(
    argv: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(configuration, "load_config", lambda: pytest.fail("configuration loaded"))
    args = ARGS.copy()
    if argv[0] in args:
        args[args.index(argv[0]) + 1] = argv[1]
    else:
        args.extend(argv)
    assert cli.main(args) == 2
    assert "Input error" in capsys.readouterr().err


def test_discovery_window_and_valid_outcomes() -> None:
    req = request()
    assert study.index_request(req).start_trade_date == "2026-09-03"
    result = study.compute(req, history(req), chains())
    assert len(result.cells) == 4
    assert all(not cell.exclusion_reasons for cell in result.cells)
    call_atm = next(
        c for c in result.cells if c.option_type == "CALL" and c.moneyness_target == "0"
    )
    put_otm = next(
        c for c in result.cells if c.option_type == "PUT" and c.moneyness_target == "0.05"
    )
    assert (call_atm.entry_trade_date, call_atm.actual_dte, call_atm.instrument_id) == (
        ENTRY,
        10,
        "C100",
    )
    assert call_atm.entry_premium_proxy == 4
    assert call_atm.expiry_payoff_proxy == 3
    assert call_atm.seller_compensation_points == 1
    assert call_atm.seller_compensation_ratio == 0.01
    assert call_atm.annualized_compensation_ratio == pytest.approx(0.365)
    assert put_otm.instrument_id == "P95"
    assert put_otm.expiry_payoff_proxy == 0
    assert result.expected_expiry_count == 1
    assert len(result.summary) == 4


def test_entry_tie_chooses_earlier_date_without_price_fallback() -> None:
    req = request(dtes=(10,), money=(Decimal("0"),))
    days = ("2026-09-07", "2026-09-09", EXPIRY)
    facts = chains(days)
    high, low = facts[days[0]]
    facts[days[0]] = (
        replace(
            high,
            expiries=(
                replace(high.expiries[0], calls=(chain_product.OptionPoint("C100", 100, None),)),
            ),
        ),
        replace(
            low,
            expiries=(
                replace(low.expiries[0], calls=(chain_product.OptionPoint("C100", 100, None),)),
            ),
        ),
    )
    result = study.compute(req, history(req, days, closes=(100, 100, 103)), facts)
    call = next(c for c in result.cells if c.option_type == "CALL")
    assert call.entry_trade_date == days[0]
    assert call.actual_dte == 11
    assert call.exclusion_reasons == ("invalid_selected_option_price",)


def test_itm_is_never_selected_even_when_closer_and_ties_are_deterministic() -> None:
    req = request(money=(Decimal("0"), Decimal("0.05")))
    call_points = (
        chain_product.OptionPoint("ITM", 99, 2),
        chain_product.OptionPoint("A-OTM", 101, 2),
        chain_product.OptionPoint("Z-OTM", 101, 2),
        chain_product.OptionPoint("FAR", 109, 2),
    )
    facts = chains(calls=call_points)
    result = study.compute(req, history(req), facts)
    call_atm = next(
        c for c in result.cells if c.option_type == "CALL" and c.moneyness_target == "0"
    )
    call_target = next(
        c for c in result.cells if c.option_type == "CALL" and c.moneyness_target == "0.05"
    )
    assert call_atm.instrument_id == "A-OTM"
    assert Decimal(call_atm.actual_moneyness or "-1") == Decimal("0.01")
    assert call_target.instrument_id == "FAR"  # equal distance .04: more OTM wins
    assert all(c.actual_moneyness is None or Decimal(c.actual_moneyness) >= 0 for c in result.cells)


def test_no_atm_or_otm_and_moneyness_tolerance_are_cell_exclusions() -> None:
    req = request(money=(Decimal("0"), Decimal("0.20")))
    facts = chains(calls=(chain_product.OptionPoint("ITM", 99, 2),))
    result = study.compute(req, history(req), facts)
    calls = [c for c in result.cells if c.option_type == "CALL"]
    assert all(c.exclusion_reasons == ("no_atm_or_otm_contract",) for c in calls)
    put_far = next(
        c for c in result.cells if c.option_type == "PUT" and c.moneyness_target == "0.2"
    )
    assert put_far.exclusion_reasons[0] == "moneyness_out_of_tolerance"
    assert put_far.instrument_id == "P95"
    empty = next(g for g in result.summary if g["option_type"] == "CALL")
    assert empty["sample_count"] == 0
    assert empty["seller_compensation_points_mean"] is None
    assert empty["positive_frequency"] is None


def test_exact_tolerance_boundaries_zero_price_and_no_second_strike() -> None:
    req = request(money=(Decimal("0.025"),))
    zero = chain_product.OptionPoint("ZERO", 100.0, 0.0)
    farther = chain_product.OptionPoint("SECOND", 105.0, 2.0)
    facts = chains(calls=(zero, farther))
    result = study.compute(req, history(req), facts)
    call = next(c for c in result.cells if c.option_type == "CALL")
    assert call.instrument_id == "SECOND"  # exact tie goes farther OTM
    assert call.moneyness_error == "0.025"
    assert call.exclusion_reasons == ()

    req_atm = request(money=(Decimal("0"),))
    facts = chains(calls=(zero, farther))
    result = study.compute(req_atm, history(req_atm), facts)
    call = next(c for c in result.cells if c.option_type == "CALL")
    assert call.instrument_id == "ZERO"
    assert call.entry_premium_proxy == 0

    null = chain_product.OptionPoint("ZERO", 100.0, None)
    missing = chains(calls=(null, farther))
    result = study.compute(req_atm, history(req_atm), missing)
    call = next(c for c in result.cells if c.option_type == "CALL")
    assert call.instrument_id == "ZERO"
    assert call.exclusion_reasons == ("invalid_selected_option_price",)


def test_invalid_underlying_and_option_order_exclude_selected_cell() -> None:
    high, low = chains()[ENTRY]
    invalid_underlying = study._selected_cell(
        EXPIRY,
        10,
        "CALL",
        Decimal("0"),
        ENTRY,
        replace(high, underlying=replace(high.underlying, price=99.0)),
        low,
        103.0,
    )
    assert invalid_underlying.exclusion_reasons == ("invalid_entry_underlying",)
    high_calls = (chain_product.OptionPoint("C100", 100, 2),)
    low_calls = (chain_product.OptionPoint("C100", 100, 3),)
    invalid_option = study._selected_cell(
        EXPIRY,
        10,
        "CALL",
        Decimal("0"),
        ENTRY,
        replace(high, expiries=(replace(high.expiries[0], calls=high_calls),)),
        replace(low, expiries=(replace(low.expiries[0], calls=low_calls),)),
        103.0,
    )
    assert invalid_option.exclusion_reasons == ("invalid_selected_option_price",)


def test_no_eligible_entry_date_is_explicit_when_expiry_only_is_observed() -> None:
    req = request(money=(Decimal("0"),))
    with pytest.raises(study.MOOptionRiskPremiumStudyError, match="zero valid"):
        study.compute(req, history(req, (EXPIRY,), closes=(103,)), chains((EXPIRY,)))
    cell = study._selected_cell(EXPIRY, 10, "CALL", Decimal("0"), None, None, None, 103)
    assert cell.exclusion_reasons == ("no_eligible_entry_date",)


def test_dte_tolerance_and_exact_expiry_close() -> None:
    req = request(dtes=(10, 20), money=(Decimal("0"),))
    result = study.compute(req, history(req), chains())
    far = [c for c in result.cells if c.target_dte == 20]
    assert all(c.exclusion_reasons == ("dte_out_of_tolerance",) for c in far)
    assert all(c.actual_dte == 10 and c.dte_error == -10 for c in far)
    high, low = chains((ENTRY,))[ENTRY]
    missing_close = study._selected_cell(EXPIRY, 10, "CALL", Decimal("0"), ENTRY, high, low, None)
    assert missing_close.exclusion_reasons == ("missing_expiry_close",)
    within = study._selected_cell(EXPIRY, 15, "CALL", Decimal("0"), ENTRY, high, low, 103)
    outside = study._selected_cell(EXPIRY, 16, "CALL", Decimal("0"), ENTRY, high, low, 103)
    assert within.exclusion_reasons == ()
    assert outside.exclusion_reasons == ("dte_out_of_tolerance",)


def test_structural_contradiction_and_zero_valid_are_whole_run_failures() -> None:
    req = request()
    facts = chains()
    high, low = facts[ENTRY]
    facts[ENTRY] = high, replace(low, expiries=(replace(low.expiries[0], calls=()),))
    with pytest.raises(study.SnapshotContractError, match="structure differs"):
        study.compute(req, history(req), facts)
    far = request(dtes=(40,), money=(Decimal("0"),))
    with pytest.raises(study.MOOptionRiskPremiumStudyError, match="zero valid"):
        study.compute(far, history(far), chains())
    absent = {
        day: (replace(pair[0], expiries=()), replace(pair[1], expiries=()))
        for day, pair in chains().items()
    }
    with pytest.raises(study.MOOptionRiskPremiumStudyError, match="no MO expiry"):
        study.compute(req, history(req), absent)


def test_statistics_and_provenance_fingerprints_are_deterministic() -> None:
    req = request()
    first = study.compute(req, history(req), chains())
    second = study.compute(req, history(req), chains())
    assert first.provenance == second.provenance
    changed = chains()
    high, low = changed[ENTRY]
    changed[ENTRY] = replace(high, underlying=replace(high.underlying, price=102)), low
    modified = study.compute(req, history(req), changed)
    assert (
        first.provenance["observation_artifact_sha256"]
        != modified.provenance["observation_artifact_sha256"]
    )
    cells = tuple(
        replace(
            cell,
            seller_compensation_points=value,
            seller_compensation_ratio=value,
            annualized_compensation_ratio=value,
        )
        for cell, value in zip(first.cells, (1.0, -2.0, 0.0, 3.0), strict=True)
    )
    groups = study._summarize(cells, req, 1)
    assert sum(g["sample_count"] for g in groups) == 4
    assert study._quantile((1.0, 2.0, 5.0, 10.0), 0.5) == 3.5
    assert study._quantile((1.0, 2.0, 5.0, 10.0), 0.05) == pytest.approx(1.15)


def test_group_statistics_equal_expiry_weight_signs_and_overlapping_reasons() -> None:
    req = request(money=(Decimal("0"),))
    base = study.compute(req, history(req), chains())
    template = next(cell for cell in base.cells if cell.option_type == "CALL")
    values = (-4.0, 0.0, 2.0, 10.0)
    valid = tuple(
        replace(
            template,
            expiry_date=f"2026-09-{18 + i:02d}",
            seller_compensation_points=value,
            seller_compensation_ratio=value,
            annualized_compensation_ratio=value,
        )
        for i, value in enumerate(values)
    )
    excluded = replace(
        template,
        expiry_date="2026-09-22",
        exclusion_reasons=("missing_expiry_close", "invalid_selected_option_price"),
    )
    call_group = study._summarize((*valid, excluded), req, 5)[0]
    assert call_group["sample_count"] == 4
    assert call_group["unique_expiry_count"] == 4
    assert call_group["expected_expiry_count"] == 5
    assert call_group["unique_expiry_coverage_ratio"] == 0.8
    assert call_group["excluded_cell_count"] == 1
    assert call_group["reason_counts"] == {
        "invalid_selected_option_price": 1,
        "missing_expiry_close": 1,
    }
    assert call_group["seller_compensation_points_mean"] == 2
    assert call_group["seller_compensation_points_median"] == 1
    assert call_group["seller_compensation_points_p50"] == 1
    assert call_group["seller_compensation_points_p05"] == pytest.approx(-3.4)
    assert call_group["positive_frequency"] == 0.5
    assert call_group["negative_frequency"] == 0.25
    assert call_group["zero_frequency"] == 0.25


def test_retention_contains_auditable_panel_summary_and_report(tmp_path: Path) -> None:
    result = study.compute(request(), history(request()), chains())
    paths = evidence.retain(result, tmp_path)
    assert {path.name for path in paths} == {
        "request.json",
        "option_outcome_panel.json",
        "compensation_summary.json",
        "risk_premium_report.md",
    }
    panel = json.loads((tmp_path / "option_outcome_panel.json").read_text())
    summary = json.loads((tmp_path / "compensation_summary.json").read_text())
    assert len(panel["cells"]) == 4
    assert len(summary["groups"]) == 4
    assert panel["semantic_identity_sha256"] == summary["observation_artifact_sha256"]
    report = (tmp_path / "risk_premium_report.md").read_text()
    for text in (
        "DTE compensation profile",
        "CALL / PUT",
        "Coverage and exclusions",
        "payoff proxy",
        "not exact CFFEX settlement",
        "not portfolio CAGR",
    ):
        assert text in report
    mixed = study.compute(
        request(),
        history(request()),
        chains(calls=(chain_product.OptionPoint("ITM", 99, 2),)),
    )
    excluded_dir = tmp_path / "mixed"
    excluded_dir.mkdir()
    evidence.retain(mixed, excluded_dir)
    mixed_panel = json.loads((excluded_dir / "option_outcome_panel.json").read_text())
    excluded = [cell for cell in mixed_panel["cells"] if cell["exclusion_reasons"]]
    assert len(excluded) == 2
    assert all(cell["exclusion_reasons"] == ["no_atm_or_otm_contract"] for cell in excluded)
    assert all(cell["entry_trade_date"] == ENTRY for cell in excluded)


def configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "market-research" / "research.toml"
    path.parent.mkdir()
    path.write_text('[output]\nroot = "retained"\n')
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", path)
    return tmp_path / "retained"


def test_cli_public_calls_collision_and_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = configure(tmp_path, monkeypatch)
    req = request()
    index_calls: list[object] = []
    chain_calls: list[chain_product.ChainQuery] = []

    def run_index(query: object) -> IndexDailyHistoryResult:
        index_calls.append(query)
        return history(req)

    def read(query: chain_product.ChainQuery) -> chain_product.ChainReadResult:
        chain_calls.append(query)
        return chain_product.ChainReadResult(
            chain=chains()[query.target_trade_date][
                0 if query.price_type is chain_product.PriceType.HIGH else 1
            ]
        )

    monkeypatch.setattr(cli.index_product, "run_index_daily_history", run_index)
    monkeypatch.setattr(cli.chain_product, "read_chain", read)
    assert cli.main(ARGS) == 0
    directory = root / cli.STUDY_ID / study.run_key(req)
    assert directory.is_dir()
    assert len(index_calls) == 1
    assert index_calls == [study.index_request(req)]
    assert len(chain_calls) == 4
    assert {q.target_trade_date for q in chain_calls} == {ENTRY, EXPIRY}
    assert {q.price_type for q in chain_calls} == {
        chain_product.PriceType.HIGH,
        chain_product.PriceType.LOW,
    }
    assert "Study completed" in capsys.readouterr().out
    assert cli.main(ARGS) == 6
    assert len(index_calls) == 1
    (directory / "stale.txt").write_text("old")
    assert cli.main([*ARGS, "--overwrite"]) == 0
    assert not (directory / "stale.txt").exists()
    assert len(index_calls) == 2


def test_cli_failure_categories_and_help(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit, match="0"):
        cli.main(["--help"])
    assert "--moneyness-targets" in capsys.readouterr().out
    configure(tmp_path, monkeypatch)
    monkeypatch.setattr(
        cli.index_product,
        "run_index_daily_history",
        lambda _: (_ for _ in ()).throw(IndexDailyHistoryError("upstream")),
    )
    assert cli.main(ARGS) == 4
    assert "Snapshot/data error" in capsys.readouterr().err


def test_cli_configuration_and_chain_failure_categories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with monkeypatch.context() as config_patch:
        config_patch.setattr(
            configuration,
            "load_config",
            lambda: (_ for _ in ()).throw(configuration.ResearchConfigError("bad config")),
        )
        assert cli.main(ARGS) == 3
        assert "Configuration error" in capsys.readouterr().err
    configure(tmp_path, monkeypatch)
    req = request()
    monkeypatch.setattr(cli.index_product, "run_index_daily_history", lambda _: history(req))
    monkeypatch.setattr(
        cli.chain_product,
        "read_chain",
        lambda _: chain_product.ChainReadResult(
            error=chain_product.OptionChainUnavailableError("no chain")
        ),
    )
    assert cli.main(ARGS) == 4
    assert "Snapshot/data error" in capsys.readouterr().err


def test_public_result_contract_failure_precedes_chain_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configure(tmp_path, monkeypatch)
    req = request()
    bad = replace(history(req), ts_code="WRONG")
    monkeypatch.setattr(cli.index_product, "run_index_daily_history", lambda _: bad)
    monkeypatch.setattr(cli.chain_product, "read_chain", lambda _: pytest.fail("chain called"))
    assert cli.main(ARGS) == 4
    assert "Snapshot/data error" in capsys.readouterr().err
