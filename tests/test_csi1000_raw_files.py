import json
from pathlib import Path
from typing import Any

import pytest

from daily_market_snapshot import artifacts
from daily_market_snapshot.capture import csi1000_index_history as index_history
from daily_market_snapshot.capture import im_futures_basic as futures_basic
from daily_market_snapshot.capture import im_futures_daily as futures_daily
from daily_market_snapshot.capture import mo_option_basic as option_basic
from daily_market_snapshot.capture import mo_option_daily as option_daily
from daily_market_snapshot.sources import tushare
from support.fake_source import (
    FakeTushareApi,
    business_days,
    futures_basic_frame,
    futures_daily_frame,
    im_contract,
    index_history_frame,
    mo_option_contract,
    option_basic_frame,
    option_daily_frame,
)

TARGET_DATE = "2026-09-17"
INDEX_CODE = "000852.SH"
# Enough distinct trade dates for the downstream 120-trading-day window, all
# inside the requested 240-calendar-day lookback window.
INDEX_SOURCE_DATES = business_days("2026-01-20", TARGET_DATE)
CONTRACTS = [
    mo_option_contract("MO2609-C-7000.CFE", exercise_price=7000.0, call_put="C"),
    mo_option_contract("MO2609-P-7000.CFE", exercise_price=7000.0, call_put="P"),
]
OPTION_CODES = [str(contract["ts_code"]) for contract in CONTRACTS]
IM_CONTRACTS = [
    im_contract("IM2603.CFE", list_date="20260216", delist_date="20260320"),
    im_contract("IM2609.CFE", list_date="20260817", delist_date="20260918"),
]
IM_DAILY_DATES = {
    "IM2603.CFE": ["20260216", "20260217"],
    "IM2609.CFE": ["20260817", "20260917"],
}


def fake_api() -> FakeTushareApi:
    """Build one fake Source that can serve every collector of the scenario."""
    return FakeTushareApi(
        index_frames={INDEX_CODE: index_history_frame(INDEX_CODE, INDEX_SOURCE_DATES)},
        option_basic=option_basic_frame(CONTRACTS),
        option_daily=option_daily_frame("20260917", OPTION_CODES),
        futures_basic=futures_basic_frame(IM_CONTRACTS),
        futures_daily={
            ts_code: futures_daily_frame(ts_code, trade_dates)
            for ts_code, trade_dates in IM_DAILY_DATES.items()
        },
    )


def test_all_five_collectors_share_the_goal_scoped_raw_directory(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_codes = [
        index_history.main([TARGET_DATE]),
        option_basic.main([TARGET_DATE]),
        option_daily.main([TARGET_DATE]),
        futures_basic.main([TARGET_DATE]),
        futures_daily.main([TARGET_DATE]),
    ]

    assert exit_codes == [0, 0, 0, 0, 0]
    dataset_dir = test_workdir / "raw" / artifacts.CSI1000_RAW_SUBDIR / TARGET_DATE
    assert sorted(path.name for path in dataset_dir.iterdir()) == [
        "im_futures_basic.json",
        "im_futures_daily.json",
        "index_daily_history.json",
        "mo_option_basic.json",
        "mo_option_daily.json",
    ]
    for name in (
        "index_daily_history.json",
        "mo_option_basic.json",
        "mo_option_daily.json",
        "im_futures_basic.json",
        "im_futures_daily.json",
    ):
        records: Any = json.loads((dataset_dir / name).read_text(encoding="utf-8"))
        assert isinstance(records, list)
        assert records
    assert capsys.readouterr().out.count(str(dataset_dir)) == 5


def test_raw_files_meet_the_documented_completeness_requirements(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every Raw artifact must be usable for the Guide window it feeds."""
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    for collector in (index_history, option_basic, option_daily, futures_basic, futures_daily):
        assert collector.main([TARGET_DATE]) == 0

    dataset_dir = test_workdir / "raw" / artifacts.CSI1000_RAW_SUBDIR / TARGET_DATE
    loaded: dict[str, list[dict[str, Any]]] = {
        name: json.loads((dataset_dir / name).read_text(encoding="utf-8"))
        for name in (
            "index_daily_history.json",
            "mo_option_basic.json",
            "mo_option_daily.json",
            "im_futures_basic.json",
            "im_futures_daily.json",
        )
    }

    history = loaded["index_daily_history.json"]
    history_dates = {str(record["trade_date"]) for record in history}
    assert len(history_dates) >= index_history.MIN_HISTORY_TRADE_DATES
    assert TARGET_DATE in history_dates
    assert {record["ts_code"] for record in history} == {INDEX_CODE}

    basic_codes = {str(record["ts_code"]) for record in loaded["mo_option_basic.json"]}
    daily_codes = {str(record["ts_code"]) for record in loaded["mo_option_daily.json"]}
    assert basic_codes == set(OPTION_CODES)
    assert daily_codes == basic_codes

    for record in loaded["im_futures_basic.json"]:
        assert record["list_date"] is not None
        assert record["delist_date"] is not None
        assert record["list_date"] <= record["delist_date"]

    im_daily = loaded["im_futures_daily.json"]
    im_daily_codes = {str(record["ts_code"]) for record in im_daily}
    assert im_daily_codes == {str(record["ts_code"]) for record in loaded["im_futures_basic.json"]}
    assert TARGET_DATE in {str(record["trade_date"]) for record in im_daily}
    assert len({str(record["trade_date"]) for record in im_daily}) > 1


def test_collectors_never_write_into_the_daily_snapshot_raw_directory(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    for collector in (index_history, option_basic, option_daily, futures_basic, futures_daily):
        assert collector.main([TARGET_DATE]) == 0

    # data/raw/<target_trade_date>/ belongs to the daily snapshot Definition.
    assert not (test_workdir / "raw" / TARGET_DATE).exists()
