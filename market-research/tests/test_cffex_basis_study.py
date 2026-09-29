"""Retained four-family CFFEX Study semantics and CLI evidence tests."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from market_research.studies.cffex_basis_forward_return_association import cli, study
from market_research.ui import configuration
from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult,
    CFFEXEquityIndexBasisObservation,
)

MAPPING = {
    "IF": ("000300.SH", "2010-04-16"),
    "IH": ("000016.SH", "2015-04-16"),
    "IC": ("000905.SH", "2015-04-16"),
    "IM": ("000852.SH", "2022-07-22"),
}


def weekdays(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    result: list[str] = []
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current.isoformat())
        current += timedelta(days=1)
    return result


def snapshots(
    *, flat_basis: bool = False, flat_close: bool = False
) -> list[CFFEXEquityIndexBasisHistoryResult]:
    dates = weekdays("2025-12-01", 35)
    result = []
    for family_index, family in enumerate(study.FAMILIES):
        family_dates = dates if family == "IF" else dates[5:]
        observations = []
        for day, trade_date in enumerate(family_dates):
            close = 100.0 if flat_close else 100 + day * (family_index + 1) + day**2 * 0.01
            predictor = 1.0 if flat_basis else day * 0.1 + family_index * 0.3
            for slot_index, slot in enumerate(study.SLOTS):
                basis = predictor + slot_index
                observations.append(
                    CFFEXEquityIndexBasisObservation(
                        trade_date=trade_date,
                        futures_family=family,
                        underlying_code=MAPPING[family][0],
                        contract_code=f"{family}{slot_index}",
                        contract_slot=slot,
                        delist_date="2026-12-31",
                        days_to_delist=360,
                        annualization_days=360,
                        underlying_close=close,
                        futures_close=close + 1,
                        basis_points=1.0,
                        basis_pct=1.0,
                        annualized_basis_pct=basis,
                    )
                )
        result.append(
            CFFEXEquityIndexBasisHistoryResult(
                futures_family=family,
                start_trade_date=dates[0],
                end_trade_date=dates[-1],
                family_listing_date=MAPPING[family][1],
                first_observation_date=family_dates[0],
                last_observation_date=family_dates[-1],
                underlying_code=MAPPING[family][0],
                source_identity="tushare:index_daily+fut_basic+fut_daily",
                observations=tuple(observations),
            )
        )
    return result


def test_observations_populations_and_thresholds() -> None:
    result = study.compute(snapshots())
    obs = result["observations"]
    assert len(obs["basis_term_structure"]) == 4 * (35 + 30 * 3)
    assert len(obs["daily_basis_environment"]) == 35 + 30 * 3
    assert len(obs["underlying_forward_returns"]) == 35 + 30 * 3
    first = obs["daily_basis_environment"][0]
    assert first["daily_non_front_basis"] == pytest.approx(
        (
            first["m1_annualized_basis_pct"]
            + first["q1_annualized_basis_pct"]
            + first["q2_annualized_basis_pct"]
        )
        / 3
    )
    assert obs["underlying_forward_returns"][0]["forward_return_20d_pct"] is not None
    assert obs["underlying_forward_returns"][34]["forward_return_1d_pct"] is None
    summary = result["sample_summary"]
    assert [row["predictor_date_count"] for row in summary["families"]] == [15, 10, 10, 10]
    assert summary["common_period"]["date_count"] == 10
    full = result["basis_regime_forward_returns"]["breakpoints"]
    common = result["common_period_cross_family_comparison"]["breakpoints"]
    assert full[0]["p20"] != common[0]["p20"]
    for family in study.FAMILIES:
        count = next(
            row["predictor_date_count"] for row in summary["families"] if row["family"] == family
        )
        for horizon in study.HORIZONS:
            assert (
                sum(
                    row["sample_count"]
                    for row in result["basis_regime_forward_returns"]["table"]
                    if row["family"] == family and row["horizon"] == horizon
                )
                == count
            )
            assert (
                sum(
                    row["sample_count"]
                    for row in result["common_period_cross_family_comparison"]["table"]
                    if row["family"] == family and row["horizon"] == horizon
                )
                == 10
            )


def test_ties_empty_quintiles_and_null_statistics() -> None:
    result = study.compute(snapshots(flat_basis=True, flat_close=True))
    rows = result["basis_regime_forward_returns"]["table"]
    assert (
        next(row for row in rows if row["family"] == "IF" and row["quintile"] == "Q2")["median"]
        is None
    )
    assert (
        next(row for row in rows if row["family"] == "IF" and row["quintile"] == "Q1")[
            "positive_return_rate"
        ]
        == 0
    )
    linear = result["linear_association"]["table"][0]
    assert linear["pearson_correlation"] is None
    assert linear["ols_beta"] is None
    assert linear["null_reasons"]["pearson_correlation"] == "zero_predictor_variance"


def test_empirical_quantile_and_ols_null_rules() -> None:
    assert study._quantile([1, 2, 3, 4], 0.2) == pytest.approx(1.6)
    assert study._quantile([], 0.2) is None
    eligible = [{"daily_non_front_basis": x, "forward_return_1d_pct": 0.0} for x in (1.0, 2.0, 3.0)]
    row = study._association(eligible, "IF", 1)
    assert row["ols_alpha"] == 0
    assert row["ols_beta"] == 0
    assert row["ols_r_squared"] is None
    assert row["null_reasons"]["ols_r_squared"] == "zero_outcome_variance"

    single = study._association(
        [{"daily_non_front_basis": 1.0, "forward_return_1d_pct": 2.0}], "IF", 1
    )
    assert single["pearson_correlation"] is None
    assert single["ols_alpha"] is None
    assert single["null_reasons"]["ols_beta"] == "sample_count_below_two"


def test_short_or_nonoverlapping_population_fails() -> None:
    short = snapshots()
    short[3] = CFFEXEquityIndexBasisHistoryResult(
        **{
            **short[3].__dict__,
            "observations": short[3].observations[:80],
            "last_observation_date": short[3].observations[76].trade_date,
        }
    )
    with pytest.raises(study.CFFEXStudyError, match="IM has no complete 20D"):
        study.compute(short)


def test_common_period_uses_actual_dates_with_an_internal_gap() -> None:
    source = snapshots()
    ih = source[1]
    omitted_date = ih.observations[7 * 4].trade_date
    kept = tuple(row for row in ih.observations if row.trade_date != omitted_date)
    source[1] = CFFEXEquityIndexBasisHistoryResult(**{**ih.__dict__, "observations": kept})
    result = study.compute(source)
    assert result["sample_summary"]["common_period"]["date_count"] == 9
    for horizon in study.HORIZONS:
        assert (
            sum(
                row["sample_count"]
                for row in result["common_period_cross_family_comparison"]["table"]
                if row["family"] == "IF" and row["horizon"] == horizon
            )
            == 9
        )


def test_retained_artifacts_and_cli_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = snapshots()
    result = study.compute(source)
    first_dir = tmp_path / "direct"
    study.retain(result, first_dir)
    names = {path.name for path in first_dir.iterdir()}
    assert {
        "result.json",
        "report.md",
        "basis_term_structure.jsonl",
        "daily_basis_environment.jsonl",
        "underlying_forward_returns.jsonl",
        "historical_context.png",
        "term_structure.png",
        "quintile_heatmaps.png",
        "common_period_comparison.png",
    } <= names
    serialized = json.loads((first_dir / "result.json").read_text())
    assert (
        serialized["provenance"]["observation_artifacts"]
        == result["provenance"]["observation_artifacts"]
    )
    assert (
        study.compute(source)["provenance"]["observation_artifacts"]
        == result["provenance"]["observation_artifacts"]
    )
    assert len((first_dir / "basis_term_structure.jsonl").read_text().splitlines()) == 500
    assert "Common-period" in (first_dir / "report.md").read_text()

    config_path = tmp_path / "market-research" / "research.toml"
    config_path.parent.mkdir()
    output_root = tmp_path / "retained"
    config_path.write_text(f"[output]\nroot = '{output_root}'\n")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", config_path)
    calls = []

    def run_product(request):
        calls.append(request.futures_family)
        return next(item for item in source if item.futures_family == request.futures_family)

    monkeypatch.setattr(cli.snapshot_product, "run_cffex_equity_index_basis_history", run_product)
    start, end = source[0].start_trade_date, source[0].end_trade_date
    assert cli.main(["--start", start, "--end", end]) == 0
    assert calls == list(study.FAMILIES)
    run_dir = output_root / study.STUDY_ID / f"{start}__{end}"
    assert (run_dir / "result.json").exists()
    calls.clear()
    assert cli.main(["--start", start, "--end", end]) == 6
    assert calls == []
    assert cli.main(["--start", start, "--end", end, "--overwrite"]) == 0
