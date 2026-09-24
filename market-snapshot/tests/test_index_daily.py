import json
from pathlib import Path

import pytest

from daily_market_snapshot.products.daily_market_snapshot import index_daily
from daily_market_snapshot.sources import tushare
from support.fake_source import FakeTushareApi, index_daily_frame, index_frames_for_all


def test_uses_requested_trade_date_in_source_form() -> None:
    api = FakeTushareApi(index_frames=index_frames_for_all(index_daily.INDEX_CODES))

    index_daily.collect_index_daily(
        "2026-09-17", lambda **kwargs: api.index_daily(**kwargs)
    )

    assert api.index_calls == [
        {"ts_code": ts_code, "trade_date": "20260917"}
        for ts_code in index_daily.INDEX_CODES
    ]


def test_requests_all_six_universe_indices() -> None:
    api = FakeTushareApi(index_frames=index_frames_for_all(index_daily.INDEX_CODES))

    index_daily.collect_index_daily(
        "2026-09-17", lambda **kwargs: api.index_daily(**kwargs)
    )

    assert [call["ts_code"] for call in api.index_calls] == list(index_daily.INDEX_CODES)
    assert len(index_daily.INDEX_CODES) == 6


def test_records_keep_source_fields_and_normalize_trade_date() -> None:
    api = FakeTushareApi(index_frames=index_frames_for_all(index_daily.INDEX_CODES))

    records = index_daily.collect_index_daily(
        "2026-09-17", lambda **kwargs: api.index_daily(**kwargs)
    )

    assert len(records) == len(index_daily.INDEX_CODES)
    assert [record["ts_code"] for record in records] == list(index_daily.INDEX_CODES)
    assert records[0] == {
        "ts_code": "000016.SH",
        "trade_date": "2026-09-17",
        "open": 99.0,
        "high": 102.0,
        "low": 97.0,
        "close": 100.0,
        "pre_close": 99.5,
        "change": 0.5,
        "pct_chg": 0.5,
        "vol": 1000.0,
        "amount": 2000.0,
    }


def test_partial_universe_is_kept_as_source_fact() -> None:
    """The Raw layer keeps what the Source returned.

    Detecting that one of the six universe indices is missing is Analysis
    Preparation's job (first-version Guide 6.1); the Raw layer must not invent or
    drop rows.
    """
    frames = index_frames_for_all(index_daily.INDEX_CODES)
    del frames["000688.SH"]
    api = FakeTushareApi(index_frames=frames)

    records = index_daily.collect_index_daily(
        "2026-09-17", lambda **kwargs: api.index_daily(**kwargs)
    )

    assert [record["ts_code"] for record in records] == [
        "000016.SH",
        "000300.SH",
        "000905.SH",
        "000852.SH",
        "399006.SZ",
    ]


def test_source_without_data_is_an_error() -> None:
    api = FakeTushareApi()

    with pytest.raises(tushare.TushareSourceError):
        index_daily.collect_index_daily(
            "2026-09-17", lambda **kwargs: api.index_daily(**kwargs)
        )


def test_date_mismatch_from_source_is_an_error() -> None:
    api = FakeTushareApi(
        index_frames={
            ts_code: index_daily_frame(ts_code, trade_date="20260916")
            for ts_code in index_daily.INDEX_CODES
        }
    )

    with pytest.raises(tushare.TushareSourceError):
        index_daily.collect_index_daily(
            "2026-09-17", lambda **kwargs: api.index_daily(**kwargs)
        )


def test_main_writes_raw_dataset_file(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = FakeTushareApi(index_frames=index_frames_for_all(index_daily.INDEX_CODES))
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_code = index_daily.main(["2026-09-17"])

    assert exit_code == 0
    raw_path = test_workdir / "raw" / "2026-09-17" / "index_daily.json"
    assert raw_path.is_file()
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    assert isinstance(records, list)
    assert len(records) == 6
    assert {record["trade_date"] for record in records} == {"2026-09-17"}
    assert {record["ts_code"] for record in records} == set(index_daily.INDEX_CODES)
    assert "index_daily.json" in capsys.readouterr().out


def test_main_fails_without_token(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(tushare.TOKEN_ENV_VAR, raising=False)
    called = False

    def unreachable_api(token: str) -> tushare.TushareApi:
        nonlocal called
        called = True
        raise AssertionError("no credential must mean no Source client")

    monkeypatch.setattr(tushare, "create_tushare_api", unreachable_api)

    exit_code = index_daily.main(["2026-09-17"])

    assert exit_code == 1
    assert called is False
    assert tushare.TOKEN_ENV_VAR in capsys.readouterr().err
    assert not (test_workdir / "raw").exists()
