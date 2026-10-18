import json
from pathlib import Path

import pytest

from data_snapshot.products.daily_market_snapshot import stock_daily
from data_snapshot.sources import tushare
from snapshot_support.fake_source import FakeTushareApi, stock_daily_frame


def test_uses_requested_trade_date_in_source_form() -> None:
    api = FakeTushareApi(stock_frame=stock_daily_frame())

    stock_daily.collect_stock_daily("2026-09-17", lambda **kwargs: api.daily(**kwargs))

    assert api.daily_calls == [{"trade_date": "20260917"}]


def test_source_records_become_raw_records() -> None:
    api = FakeTushareApi(stock_frame=stock_daily_frame())

    records = stock_daily.collect_stock_daily(
        "2026-09-17", lambda **kwargs: api.daily(**kwargs)
    )

    assert records[0] == {
        "ts_code": "000001.SZ",
        "trade_date": "2026-09-17",
        "open": 10.0,
        "high": 11.0,
        "low": 9.5,
        "close": 10.5,
        "pre_close": 10.0,
        "change": 0.5,
        "pct_chg": 5.0,
        "vol": 100.0,
        "amount": 50.0,
    }
    assert len(records) == 3


def test_records_keep_source_pct_chg_without_recalculation() -> None:
    api = FakeTushareApi(stock_frame=stock_daily_frame())

    records = stock_daily.collect_stock_daily(
        "2026-09-17", lambda **kwargs: api.daily(**kwargs)
    )

    assert [record["pct_chg"] for record in records] == [5.0, -7.3171, 0.0]


def test_raw_layer_adds_no_snapshot_fields() -> None:
    api = FakeTushareApi(stock_frame=stock_daily_frame())

    records = stock_daily.collect_stock_daily(
        "2026-09-17", lambda **kwargs: api.daily(**kwargs)
    )

    source_fields = set(stock_daily_frame().columns)
    for record in records:
        assert set(record) == source_fields
    assert not any(
        field in record
        for record in records
        for field in ("breadth", "advancers", "decliners", "traded_stocks", "total_amount")
    )


def test_source_without_data_is_an_error() -> None:
    api = FakeTushareApi()

    with pytest.raises(tushare.TushareSourceError):
        stock_daily.collect_stock_daily("2026-09-17", lambda **kwargs: api.daily(**kwargs))


def test_date_mismatch_from_source_is_an_error() -> None:
    api = FakeTushareApi(stock_frame=stock_daily_frame(trade_date="20260916"))

    with pytest.raises(tushare.TushareSourceError):
        stock_daily.collect_stock_daily("2026-09-17", lambda **kwargs: api.daily(**kwargs))


def test_main_writes_raw_dataset_file(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = FakeTushareApi(stock_frame=stock_daily_frame())
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_code = stock_daily.main(["2026-09-17"])

    assert exit_code == 0
    raw_path = test_workdir / "raw" / "2026-09-17" / "stock_daily.json"
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    assert isinstance(records, list)
    assert len(records) == 3
    assert {record["trade_date"] for record in records} == {"2026-09-17"}
    assert "stock_daily.json" in capsys.readouterr().out


def test_main_fails_without_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(tushare.TOKEN_ENV_VAR, raising=False)
    called = False

    def unreachable_api(token: str) -> tushare.TushareApi:
        nonlocal called
        called = True
        raise AssertionError("no credential must mean no Source client")

    monkeypatch.setattr(tushare, "create_tushare_api", unreachable_api)

    exit_code = stock_daily.main(["2026-09-17"])

    assert exit_code == 1
    assert called is False
    assert tushare.TOKEN_ENV_VAR in capsys.readouterr().err


def test_main_rejects_non_iso_trade_date(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = FakeTushareApi(stock_frame=stock_daily_frame())
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_code = stock_daily.main(["20260917"])

    assert exit_code == 1
    assert api.daily_calls == []
