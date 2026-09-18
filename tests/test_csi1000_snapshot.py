"""Tests for the CSI1000 5-day analysis Snapshot Assembly.

Everything runs on temporary local Raw JSON: no test touches the network or the
repository's real ``data/raw`` / ``output``.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Iterable
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

import _common
import build_snapshot
from build_snapshot import SnapshotError

TARGET_DATE = "2026-09-17"
TARGET = date.fromisoformat(TARGET_DATE)
UNDERLYING_CODE = "000852.SH"

# 122 synthetic trading rows (weekdays), so the latest 120 rows ending at the
# target date are the last 120 of them and the IM 60-day window is the last 60.
ALL_DATES = [
    (date(2026, 3, 31) + timedelta(days=offset)).isoformat()
    for offset in range((TARGET - date(2026, 3, 31)).days + 1)
    if (date(2026, 3, 31) + timedelta(days=offset)).weekday() < 5
]
TARGET_INDEX = ALL_DATES.index(TARGET_DATE)
# The 120-row window starts 119 rows back; the IM 60-day window 59 rows back.
HISTORY_START = ALL_DATES[TARGET_INDEX - 119]
IM_START = ALL_DATES[TARGET_INDEX - 59]

# Hand-checkable close path: a triangular wave, +1 / -1 point per trading day
# from 100. Its log returns alternate between two fixed, exactly opposite
# values, so every derived metric below is verifiable by hand.
CLOSE_START = 100.0


def close_at(index: int) -> float:
    return CLOSE_START + index - 2 * (index // 2)


HISTORY_CLOSES = [close_at(index) for index in range(len(ALL_DATES))]
TARGET_CLOSE = close_at(TARGET_INDEX)


# Guide 7.4 ordering: (expiry_date, strike, option_type). The two MO monthly
# series carry distinct contract codes, as the Raw contract does.
OPTIONS = [
    # contract, Source maturity_date, strike, call_put, close premium
    ("MO2609-C-7450.CFE", "20260925", 7450.0, "C", 760.0),
    ("MO2609-P-7200.CFE", "20260925", 7200.0, "P", 380.0),
    ("MO2609-C-7000.CFE", "20260925", 7000.0, "C", 900.0),
    ("MO2610-C-7000.CFE", "20261023", 7000.0, "C", 950.0),
]
# Guide 7.2: the Goal 2 Collector still writes maturity_date as YYYYMMDD, while
# the snapshot expresses the same fact as expiry_date in YYYY-MM-DD.
NEAR_EXPIRY_DATE = "2026-09-25"
FAR_EXPIRY_DATE = "2026-10-23"

# (contract, delist_date, futures close), covering three delist dates of the
# target-date curve.
IM_CONTRACTS = [
    ("IM2609.CFE", "2026-09-18", 6000.0),
    ("IM2610.CFE", "2026-10-16", 6150.0),
    ("IM2612.CFE", "2026-12-18", 6200.0),
]
# Guide 8.4: days_to_delist == 0 is the one defined null annualization.
ZERO_DAY_CONTRACT = "IM2609.CFE"
ZERO_DAY_TRADE_DATE = "2026-09-17"


def im_date(offset: int) -> str:
    """Trading date of the ``offset``-th observation inside the IM window."""
    return ALL_DATES[TARGET_INDEX - 59 + offset]


def underlying_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, trade_date in enumerate(ALL_DATES):
        close = close_at(index)
        rows.append(
            {
                "ts_code": UNDERLYING_CODE,
                "trade_date": trade_date,
                "open": close - 2.0,
                "high": close + 5.0,
                "low": close - 5.0,
                "close": close,
                "pre_close": close_at(index - 1) if index else close,
                "change": 1.0,
                "pct_chg": 0.5,
                "vol": 1000.0,
                "amount": 2000.0,
            }
        )
    return rows


def option_basic_rows() -> list[dict[str, Any]]:
    return [
        {
            "ts_code": ts_code,
            "exchange": "CFFEX",
            "opt_code": "OP000852.SH",
            "call_put": call_put,
            "exercise_price": strike,
            "maturity_date": maturity_date,
            "list_date": "2026-06-22",
            "delist_date": "2026-09-25",
        }
        for ts_code, maturity_date, strike, call_put, _ in OPTIONS
    ]


def option_daily_rows() -> list[dict[str, Any]]:
    return [
        {
            "ts_code": ts_code,
            "trade_date": TARGET_DATE,
            "exchange": "CFFEX",
            "pre_settle": cash,
            "pre_close": cash - 0.5,
            "open": cash + 0.5,
            "high": cash + 1.0,
            "low": cash - 1.0,
            "close": cash,
            "settle": cash + 0.1,
            "vol": 12.0,
            "amount": 1200.0,
            "oi": 340.0,
        }
        for ts_code, _, _, call_put, cash in OPTIONS
    ]


def im_basic_rows() -> list[dict[str, Any]]:
    return [
        {
            "ts_code": ts_code,
            "exchange": "CFFEX",
            "fut_code": "IM",
            "list_date": "2026-02-16",
            "delist_date": delist_date,
        }
        for ts_code, delist_date, _ in IM_CONTRACTS
    ]


def im_daily_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ts_code, _, futures_close in IM_CONTRACTS:
        for offset in range(60):
            rows.append(
                {
                    "ts_code": ts_code,
                    "trade_date": im_date(offset),
                    "pre_close": futures_close - 1.0,
                    "pre_settle": futures_close - 0.5,
                    "open": futures_close - 2.0,
                    "high": futures_close + 3.0,
                    "low": futures_close - 3.0,
                    "close": futures_close,
                    "settle": futures_close + 0.5,
                    "change1": 1.0,
                    "change2": 1.5,
                    "vol": 5000.0,
                    "amount": 300000.0,
                    "oi": 90000.0,
                    "oi_chg": -120.0,
                }
            )
    return rows


def base_raw() -> dict[str, list[dict[str, Any]]]:
    """Build the five Raw artifacts of a complete, consistent dataset."""
    return {
        "index_daily_history": underlying_rows(),
        "mo_option_basic": option_basic_rows(),
        "mo_option_daily": option_daily_rows(),
        "im_futures_basic": im_basic_rows(),
        "im_futures_daily": im_daily_rows(),
    }


def write_raw(root: Path, raw: dict[str, list[dict[str, Any]]]) -> Path:
    """Write the Raw artifacts and return the goal-scoped dataset directory."""
    dataset_dir = root / _common.CSI1000_RAW_SUBDIR / TARGET_DATE
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for dataset, records in raw.items():
        (dataset_dir / f"{dataset}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return dataset_dir


@pytest.fixture
def raw_root(tmp_path: Path) -> Path:
    """A complete, consistent Raw dataset for the target trade date."""
    root = tmp_path / "raw"
    write_raw(root, base_raw())
    return root


def run_builder(tmp_path: Path, raw_root: Path) -> dict[str, Any]:
    """Run the Builder entry point and return the written snapshot."""
    code = build_snapshot.main([TARGET_DATE])
    assert code == 0
    return json.loads(snapshot_path(tmp_path).read_text(encoding="utf-8"))


def snapshot_path(tmp_path: Path) -> Path:
    """Canonical Data Service output path of the assembled Snapshot."""
    return tmp_path / "output" / _common.CSI1000_RAW_SUBDIR / TARGET_DATE / "snapshot.json"


def patch_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, raw_root: Path) -> None:
    """Point the builder at the temporary Raw and canonical output roots."""
    monkeypatch.setattr(build_snapshot, "RAW_DIR", raw_root)
    monkeypatch.setattr(build_snapshot, "OUTPUT_DIR", tmp_path / "output")


def window_mean(size: int) -> float:
    """Mean of the last ``size`` wave closes ending at the target date."""
    window = HISTORY_CLOSES[TARGET_INDEX - size + 1 : TARGET_INDEX + 1]
    return sum(window) / size


def window_extreme(size: int, offset: float, pick: Callable[[Iterable[float]], float]) -> float:
    """Extreme high (``+5``) or low (``-5``) of the last ``size`` wave rows."""
    window = HISTORY_CLOSES[TARGET_INDEX - size + 1 : TARGET_INDEX + 1]
    return pick(close + offset for close in window)


def expected_returns() -> list[float]:
    ratios = [HISTORY_CLOSES[i] / HISTORY_CLOSES[i - 1] for i in range(1, len(HISTORY_CLOSES))]
    return [math.log(ratio) for ratio in ratios]


def expected_realized_vol(returns: list[float]) -> float:
    """Guide 6.5: sample standard deviation (ddof=1) * sqrt(252) * 100."""
    average = sum(returns) / len(returns)
    variance = sum((value - average) ** 2 for value in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252) * 100


def test_happy_path_snapshot_is_written_with_the_locked_structure(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    snapshot = run_builder(tmp_path, raw_root)

    assert list(snapshot) == [
        "target_trade_date",
        "underlying",
        "mo_options",
        "im_futures",
    ]
    assert snapshot["target_trade_date"] == TARGET_DATE


def test_output_path_is_the_canonical_data_service_artifact(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """guides/data-services.md 6 + 7: one canonical artifact, under ``output/``."""
    patch_dirs(monkeypatch, tmp_path, raw_root)

    run_builder(tmp_path, raw_root)

    assert snapshot_path(tmp_path).is_file()
    # The pre-Data-Service location must not be written as well.
    assert not (tmp_path / "snapshots").exists()


def test_underlying_history_is_the_latest_120_rows_in_ascending_order(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    underlying = run_builder(tmp_path, raw_root)["underlying"]

    assert underlying["ts_code"] == UNDERLYING_CODE
    history = underlying["history"]
    assert len(history) == 120
    assert [row["trade_date"] for row in history] == ALL_DATES[TARGET_INDEX - 119 :]
    assert history[0]["trade_date"] == HISTORY_START
    assert history[-1]["trade_date"] == TARGET_DATE
    # Guide 5.2: identity is expressed once, by ``underlying.ts_code``.
    assert "ts_code" not in history[0]
    assert set(history[0]) == {
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "pre_close",
        "change",
        "pct_chg",
        "vol",
        "amount",
    }
    assert history[-1] == {
        "trade_date": TARGET_DATE,
        "open": TARGET_CLOSE - 2.0,
        "high": TARGET_CLOSE + 5.0,
        "low": TARGET_CLOSE - 5.0,
        "close": TARGET_CLOSE,
        "pre_close": close_at(TARGET_INDEX - 1),
        "change": 1.0,
        "pct_chg": 0.5,
        "vol": 1000.0,
        "amount": 2000.0,
    }


def test_underlying_window_excludes_trade_dates_after_the_target(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A later trade date in the Raw file is not part of the 120-row window."""
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["index_daily_history"].append(
        {
            **raw["index_daily_history"][-1],
            "trade_date": "2026-09-18",
            "close": 999.0,
        }
    )
    write_raw(raw_root, raw)

    snapshot = run_builder(tmp_path, raw_root)

    assert snapshot["underlying"]["history"][-1]["trade_date"] == TARGET_DATE
    assert snapshot["underlying"]["history"][-1]["close"] == TARGET_CLOSE


def test_underlying_derived_matches_the_locked_formulas(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    derived = run_builder(tmp_path, raw_root)["underlying"]["derived"]

    assert list(derived) == [
        "return_1d_pct",
        "return_5d_pct",
        "return_20d_pct",
        "sma_5",
        "sma_20",
        "sma_60",
        "rolling_high_20",
        "rolling_low_20",
        "atr_14",
        "realized_vol_5d_annualized_pct",
        "realized_vol_20d_annualized_pct",
    ]
    # Guide 6.1: the triangular wave loses one point over one and five trading
    # days; twenty trading days back it is at the same level again.
    assert derived["return_1d_pct"] == pytest.approx((TARGET_CLOSE / (TARGET_CLOSE + 1) - 1) * 100)
    assert derived["return_5d_pct"] == pytest.approx(-100 / (TARGET_CLOSE + 1))
    assert derived["return_20d_pct"] == pytest.approx(0.0)
    # The wave has a four-session period, so the mean depends only on where the
    # window starts; all three windows start and end on the same leg here.
    assert derived["sma_5"] == pytest.approx(window_mean(5))
    assert derived["sma_20"] == pytest.approx(window_mean(20))
    assert derived["sma_60"] == pytest.approx(window_mean(60))
    # Guide 6.3: the 20-day extremes include the target date.
    assert derived["rolling_high_20"] == window_extreme(20, 5.0, max)
    assert derived["rolling_low_20"] == window_extreme(20, 5.0, min) - 10.0
    # Guide 6.4: every row has high - low = 10, abs(high - pre_close) <= 6.
    assert derived["atr_14"] == pytest.approx(10.0)
    # Guide 6.5: five returns need six closes, twenty returns need 21 closes.
    returns = expected_returns()
    assert derived["realized_vol_5d_annualized_pct"] == pytest.approx(
        expected_realized_vol(returns[-5:])
    )
    assert derived["realized_vol_20d_annualized_pct"] == pytest.approx(
        expected_realized_vol(returns[-20:])
    )
    # Both figures are in percentage points of annualized volatility: with the
    # alternating +-1 point wave, the 5-day figure is hand-checkable.
    assert derived["realized_vol_5d_annualized_pct"] == pytest.approx(17.303279177098972)
    assert derived["realized_vol_20d_annualized_pct"] == pytest.approx(
        expected_realized_vol(returns[-20:])
    )
    assert derived["realized_vol_5d_annualized_pct"] > derived["realized_vol_20d_annualized_pct"]


def test_mo_chain_is_joined_renamed_sorted_and_derived(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    snapshot = run_builder(tmp_path, raw_root)
    mo_options = snapshot["mo_options"]

    # Guide 5.3: the option section reads the history's target-date close.
    assert mo_options["underlying_close"] == TARGET_CLOSE
    assert mo_options["underlying_close"] == snapshot["underlying"]["history"][-1]["close"]

    chain = mo_options["chain"]
    assert [row["ts_code"] for row in chain] == [
        "MO2609-C-7000.CFE",
        "MO2609-P-7200.CFE",
        "MO2609-C-7450.CFE",
        "MO2610-C-7000.CFE",
    ]
    assert [(row["expiry_date"], row["strike"], row["option_type"]) for row in chain] == [
        ("2026-09-25", 7000.0, "C"),
        ("2026-09-25", 7200.0, "P"),
        ("2026-09-25", 7450.0, "C"),
        ("2026-10-23", 7000.0, "C"),
    ]
    first = chain[0]
    assert list(first) == [
        "ts_code",
        "option_type",
        "strike",
        "expiry_date",
        "days_to_expiry",
        "open",
        "high",
        "low",
        "close",
        "settle",
        "vol",
        "amount",
        "oi",
        "strike_minus_spot_points",
        "moneyness_pct",
        "close_premium_pct_of_spot",
    ]
    assert first["option_type"] == "C"
    assert first["strike"] == 7000.0
    assert first["expiry_date"] == NEAR_EXPIRY_DATE
    assert first["days_to_expiry"] == 8
    assert first["close"] == 900.0
    assert first["strike_minus_spot_points"] == pytest.approx(7000.0 - TARGET_CLOSE)
    assert first["moneyness_pct"] == pytest.approx((7000.0 / TARGET_CLOSE - 1) * 100)
    assert first["close_premium_pct_of_spot"] == pytest.approx(900.0 / TARGET_CLOSE * 100)
    # Guide 7.3: moneyness does not flip sign for puts.
    put = chain[1]
    assert put["option_type"] == "P"
    assert put["moneyness_pct"] == pytest.approx((7200.0 / TARGET_CLOSE - 1) * 100)
    assert chain[3]["expiry_date"] == FAR_EXPIRY_DATE
    assert chain[3]["days_to_expiry"] == 36


def test_mo_expiry_date_is_normalized_from_source_date_form(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guide 7.2 / 16: maturity_date may still arrive as YYYYMMDD."""
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    assert {record["maturity_date"] for record in raw["mo_option_basic"]} == {
        "20260925",
        "20261023",
    }
    write_raw(raw_root, raw)

    chain = run_builder(tmp_path, raw_root)["mo_options"]["chain"]

    assert [row["expiry_date"] for row in chain] == [
        NEAR_EXPIRY_DATE,
        NEAR_EXPIRY_DATE,
        NEAR_EXPIRY_DATE,
        FAR_EXPIRY_DATE,
    ]
    assert all("maturity_date" not in row for row in chain)

def test_mo_malformed_maturity_date_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_basic"][0]["maturity_date"] = "2026092"
    write_raw(raw_root, raw)
    with pytest.raises(SnapshotError, match="maturity_date"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_im_history_uses_the_last_60_underlying_trade_dates(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    im_futures = run_builder(tmp_path, raw_root)["im_futures"]
    history = im_futures["history"]

    # Three contracts over 60 trade dates, sorted by trade_date then ts_code.
    assert len(history) == 180
    assert sorted({row["trade_date"] for row in history}) == ALL_DATES[TARGET_INDEX - 59 :]
    assert history[0]["trade_date"] == IM_START
    assert history[0]["ts_code"] == "IM2609.CFE"
    assert history[-1]["trade_date"] == TARGET_DATE
    assert history[-1]["ts_code"] == "IM2612.CFE"
    assert [(row["trade_date"], row["ts_code"]) for row in history] == sorted(
        (row["trade_date"], row["ts_code"]) for row in history
    )


def test_im_basis_fields_match_the_locked_formulas(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    im_futures = run_builder(tmp_path, raw_root)["im_futures"]
    curve = im_futures["target_date_curve"]

    # Guide 9: the curve is the target-date projection, by delist_date.
    assert [row["ts_code"] for row in curve] == [
        "IM2609.CFE",
        "IM2610.CFE",
        "IM2612.CFE",
    ]
    assert [row["delist_date"] for row in curve] == [
        "2026-09-18",
        "2026-10-16",
        "2026-12-18",
    ]
    assert all(row["trade_date"] == TARGET_DATE for row in curve)

    by_code = {row["ts_code"]: row for row in curve}
    first = by_code["IM2609.CFE"]
    assert list(first) == [
        "ts_code",
        "trade_date",
        "delist_date",
        "days_to_delist",
        "open",
        "high",
        "low",
        "close",
        "settle",
        "vol",
        "amount",
        "oi",
        "oi_chg",
        "underlying_close",
        "basis_points",
        "basis_pct",
        "annualized_basis_pct",
    ]
    assert first["days_to_delist"] == 1
    assert first["underlying_close"] == TARGET_CLOSE
    assert first["close"] == 6000.0
    assert first["basis_points"] == pytest.approx(6000.0 - TARGET_CLOSE)
    assert first["basis_pct"] == pytest.approx((6000.0 / TARGET_CLOSE - 1) * 100)
    assert first["annualized_basis_pct"] == pytest.approx(first["basis_pct"] * 365 / 1)
    assert first["oi_chg"] == -120.0

    far = by_code["IM2612.CFE"]
    assert far["days_to_delist"] == (date(2026, 12, 18) - TARGET).days
    assert far["annualized_basis_pct"] == pytest.approx(
        far["basis_pct"] * 365 / far["days_to_delist"]
    )


def test_im_contract_delisting_on_the_target_date_has_a_null_annualization(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    for record in raw["im_futures_basic"]:
        if record["ts_code"] == ZERO_DAY_CONTRACT:
            record["delist_date"] = ZERO_DAY_TRADE_DATE
    write_raw(raw_root, raw)

    curve = run_builder(tmp_path, raw_root)["im_futures"]["target_date_curve"]
    zero_day = next(row for row in curve if row["ts_code"] == ZERO_DAY_CONTRACT)

    assert zero_day["days_to_delist"] == 0
    assert zero_day["annualized_basis_pct"] is None
    assert zero_day["basis_pct"] is not None


def test_im_window_drops_observations_before_it(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    outside = ALL_DATES[TARGET_INDEX - 60]  # one trade date before the window
    raw["im_futures_daily"] = [
        row for row in raw["im_futures_daily"] if row["trade_date"] != outside
    ] + [
        {**raw["im_futures_daily"][0], "trade_date": outside, "close": 1.0},
    ]
    write_raw(raw_root, raw)

    history = run_builder(tmp_path, raw_root)["im_futures"]["history"]

    assert outside not in {row["trade_date"] for row in history}
    assert {row["trade_date"] for row in history} == set(ALL_DATES[TARGET_INDEX - 59 :])


def test_repeated_runs_on_the_same_raw_produce_the_same_file(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    first = build_snapshot.build_snapshot(TARGET_DATE)
    path = build_snapshot.write_snapshot(first, TARGET_DATE, tmp_path / "output")
    second = build_snapshot.build_snapshot(TARGET_DATE)

    assert path.read_text(encoding="utf-8") == (
        snapshot_path(tmp_path).read_text(encoding="utf-8")
    )
    assert first == second


def test_builder_reads_no_other_directory_and_never_calls_the_source(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    # A neighbouring date directory with garbage must not be read or fall back.
    decoy = raw_root / _common.CSI1000_RAW_SUBDIR / "2026-09-16"
    decoy.mkdir(parents=True)
    (decoy / "index_daily_history.json").write_text("{ not json", encoding="utf-8")
    (decoy / "mo_option_basic.json").write_text("[]", encoding="utf-8")

    def unreachable(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("the Snapshot Builder must stay offline")

    monkeypatch.setattr(_common, "get_tushare_token", unreachable)
    monkeypatch.setattr(_common, "create_tushare_api", unreachable)

    snapshot = build_snapshot.build_snapshot(TARGET_DATE)

    assert snapshot["target_trade_date"] == TARGET_DATE
    assert len(snapshot["underlying"]["history"]) == 120


def test_main_reports_missing_raw_files(
    tmp_path: Path,
    raw_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    (raw_root / _common.CSI1000_RAW_SUBDIR / TARGET_DATE / "mo_option_daily.json").unlink()

    assert build_snapshot.main([TARGET_DATE]) == 1
    assert "mo_option_daily.json" in capsys.readouterr().err
    assert not snapshot_path(tmp_path).exists()


@pytest.mark.parametrize(
    ("dataset", "payload"),
    [
        ("index_daily_history", "{ not json"),
        ("im_futures_basic", '{"ts_code": "IM2609.CFE"}'),
        ("mo_option_basic", "[[1, 2]]"),
    ],
)
def test_invalid_json_shape_fails(
    tmp_path: Path,
    raw_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset: str,
    payload: str,
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    dataset_dir = raw_root / _common.CSI1000_RAW_SUBDIR / TARGET_DATE
    (dataset_dir / f"{dataset}.json").write_text(payload, encoding="utf-8")

    with pytest.raises(SnapshotError, match=dataset):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_non_iso_target_trade_date_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)

    with pytest.raises(SnapshotError, match="target_trade_date"):
        build_snapshot.build_snapshot("20260917")

    assert build_snapshot.main(["20260917"]) == 1


def test_underlying_with_fewer_than_120_trading_days_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    dropped = set(ALL_DATES[10:14])
    raw["index_daily_history"] = [
        row for row in raw["index_daily_history"] if row["trade_date"] not in dropped
    ]
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="119 distinct trade dates"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_underlying_without_the_target_trade_date_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["index_daily_history"] = [
        row for row in raw["index_daily_history"] if row["trade_date"] != TARGET_DATE
    ]
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="no row"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_duplicate_underlying_trade_date_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["index_daily_history"].append(dict(raw["index_daily_history"][-1]))
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="duplicate"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_underlying_row_of_another_index_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["index_daily_history"][0]["ts_code"] = "000300.SH"
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="000852.SH"):
        build_snapshot.build_snapshot(TARGET_DATE)


@pytest.mark.parametrize("field", ["close", "high", "pre_close"])
def test_missing_or_malformed_underlying_number_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["index_daily_history"][-1][field] = None
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match=field):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_non_positive_underlying_close_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["index_daily_history"][-1]["close"] = 0.0
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="greater than 0"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_option_quote_field_the_source_omits_stays_null(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A key the Source did not return at all is a missing fact, not an error.

    The assembly only rejects a value that is present but malformed; the Snapshot
    never invents a quote the Source did not return.
    """
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    del raw["mo_option_daily"][0]["settle"]
    write_raw(raw_root, raw)

    chain = run_builder(tmp_path, raw_root)["mo_options"]["chain"]

    missing = next(row for row in chain if row["ts_code"] == raw["mo_option_daily"][0]["ts_code"])
    assert missing["settle"] is None
    assert missing["close"] is not None


def test_unquoted_option_contract_keeps_null_quotes(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A contract with no trade on the target date has no open / high / low.

    The Source omits those facts, so the Snapshot keeps them missing; the
    contract and its hand-checkable close-based derived fields stay in the chain.
    """
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    ts_code, _, _, _, premium = OPTIONS[0]
    row_index = next(
        index
        for index, record in enumerate(raw["mo_option_daily"])
        if record["ts_code"] == ts_code
    )
    raw["mo_option_daily"][row_index].update(
        {"open": None, "high": None, "low": None, "vol": 0.0}
    )
    write_raw(raw_root, raw)

    chain = run_builder(tmp_path, raw_root)["mo_options"]["chain"]

    row = next(entry for entry in chain if entry["ts_code"] == ts_code)
    assert row["open"] is None
    assert row["high"] is None
    assert row["low"] is None
    assert row["vol"] == 0.0
    assert row["close"] == premium
    assert row["settle"] == premium + 0.1
    assert row["close_premium_pct_of_spot"] == pytest.approx(premium / TARGET_CLOSE * 100)
    # Every contract of the active universe stays in the chain.
    assert len(chain) == len(OPTIONS)


def test_first_trading_day_observation_keeps_a_null_optional_quote(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fact the Source does not return stays missing in the Snapshot.

    ``oi_chg`` is a per-observation change the Source leaves empty on a
    contract's first trading day; the basis fields never read it.
    """
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    first_day = raw["im_futures_daily"][0]
    assert first_day["trade_date"] == IM_START
    first_day["oi_chg"] = None
    write_raw(raw_root, raw)

    history = run_builder(tmp_path, raw_root)["im_futures"]["history"]

    observation = next(
        row
        for row in history
        if row["ts_code"] == first_day["ts_code"] and row["trade_date"] == first_day["trade_date"]
    )
    assert observation["oi_chg"] is None
    # The basis fields never read it, so they are still computed from the
    # underlying close of that observation's own trade date.
    underlying_close = observation["underlying_close"]
    assert observation["basis_points"] == pytest.approx(observation["close"] - underlying_close)
    assert observation["basis_pct"] == pytest.approx(
        (observation["close"] / underlying_close - 1) * 100
    )


@pytest.mark.parametrize("field", ["open", "high", "low", "vol"])
def test_present_but_malformed_option_quote_field_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    """Only a missing fact is tolerated; a malformed one is still an error."""
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_daily"][0][field] = "n/a"
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match=field):
        build_snapshot.build_snapshot(TARGET_DATE)


@pytest.mark.parametrize("value", ["7000.0", None])
def test_malformed_option_strike_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch, value: Any
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_basic"][0]["exercise_price"] = value
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="exercise_price"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_duplicate_mo_basic_contract_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_basic"].append(dict(raw["mo_option_basic"][0]))
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="more than one row"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_duplicate_mo_daily_contract_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_daily"].append(dict(raw["mo_option_daily"][0]))
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="more than one row"):
        build_snapshot.build_snapshot(TARGET_DATE)


@pytest.mark.parametrize("side", ["basic", "daily"])
def test_mo_basic_and_daily_set_mismatch_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch, side: str
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    dataset = "mo_option_basic" if side == "basic" else "mo_option_daily"
    raw[dataset] = raw[dataset][:-1]
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="one-to-one"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_mo_daily_of_another_trade_date_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_daily"][0]["trade_date"] = "2026-09-16"
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="trade_date"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_empty_mo_chain_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["mo_option_basic"] = []
    raw["mo_option_daily"] = []
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="holds no contract"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_unknown_im_daily_contract_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    del raw["im_futures_basic"][0]
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="maps to no known contract"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_all_im_window_trade_dates_have_an_underlying_close(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guide 8.2 + 8.3: every window observation aligns to a CSI1000 close.

    The 60-day window is taken from the underlying history, so this is an
    invariant of the assembly rather than a reachable failure state: every
    ``underlying_close`` of the assembled IM history is a close of that history.
    """
    patch_dirs(monkeypatch, tmp_path, raw_root)

    snapshot = run_builder(tmp_path, raw_root)
    closes_by_date = {
        row["trade_date"]: row["close"] for row in snapshot["underlying"]["history"]
    }

    assert snapshot["im_futures"]["history"]
    for observation in snapshot["im_futures"]["history"]:
        assert observation["underlying_close"] == closes_by_date[observation["trade_date"]]


def test_empty_im_history_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["im_futures_daily"] = []
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="no observation inside"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_empty_target_date_curve_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["im_futures_daily"] = [
        row for row in raw["im_futures_daily"] if row["trade_date"] != TARGET_DATE
    ]
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="target-date futures curve"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_missing_im_number_fails(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_dirs(monkeypatch, tmp_path, raw_root)
    raw = base_raw()
    raw["im_futures_daily"][0]["oi_chg"] = "n/a"
    write_raw(raw_root, raw)

    with pytest.raises(SnapshotError, match="oi_chg"):
        build_snapshot.build_snapshot(TARGET_DATE)


def test_no_analysis_fields_leak_into_the_snapshot(
    tmp_path: Path, raw_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guide 2.2 / 7.5 / 13: no analyzer conclusion may appear."""
    patch_dirs(monkeypatch, tmp_path, raw_root)

    snapshot = run_builder(tmp_path, raw_root)

    # Exact field names come from the serialized form, so the check does not
    # fire on an allowed name, such as ``derived``, that merely contains one.
    serialized = json.dumps(snapshot)
    field_names = set(re.findall(r'"([^"]+)":', serialized))
    assert field_names == {
        "target_trade_date",
        "underlying",
        "ts_code",
        "history",
        "derived",
        "return_1d_pct",
        "return_5d_pct",
        "return_20d_pct",
        "sma_5",
        "sma_20",
        "sma_60",
        "rolling_high_20",
        "rolling_low_20",
        "atr_14",
        "realized_vol_5d_annualized_pct",
        "realized_vol_20d_annualized_pct",
        "mo_options",
        "underlying_close",
        "chain",
        "option_type",
        "strike",
        "expiry_date",
        "days_to_expiry",
        "open",
        "high",
        "low",
        "close",
        "settle",
        "vol",
        "amount",
        "oi",
        "strike_minus_spot_points",
        "moneyness_pct",
        "close_premium_pct_of_spot",
        "im_futures",
        "trade_date",
        "pre_close",
        "change",
        "pct_chg",
        "delist_date",
        "days_to_delist",
        "oi_chg",
        "basis_points",
        "basis_pct",
        "annualized_basis_pct",
        "target_date_curve",
    }
    # The forbidden list of Guide 2.2 / 7.5 / 8.4 / 13, by exact field name.
    forbidden = {
        "center",
        "noise_zone",
        "upper_reversal_zone",
        "lower_reversal_zone",
        "market_regime",
        "trend_strength",
        "overbought",
        "oversold",
        "sell_call",
        "sell_put",
        "cheap",
        "expensive",
        "recommended_strike",
        "probability_up",
        "probability_down",
        "confidence",
        "recommendation",
        "bullish",
        "bearish",
        "iv",
        "delta",
        "gamma",
        "theta",
        "vega",
        "skew",
        "atm",
        "otm",
        "itm",
    }
    assert not forbidden & field_names