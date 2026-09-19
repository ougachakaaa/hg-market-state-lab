import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from daily_market_snapshot import artifacts
from daily_market_snapshot.capture import common, csi1000_index_history
from daily_market_snapshot.sources import tushare
from support.fake_source import FakeTushareApi, business_days, index_history_frame

TARGET_DATE = "2026-09-17"


def iso_dates(source_dates: list[str]) -> list[str]:
    """Convert Source-form ``YYYYMMDD`` dates to the Raw ``YYYY-MM-DD`` form."""
    return [
        datetime.strptime(source_date, tushare.TRADE_DATE_TUSHARE_FORMAT).strftime(
            tushare.TRADE_DATE_ISO_FORMAT
        )
        for source_date in source_dates
    ]


# Source date form: the frame carries Tushare facts, the Raw records are ISO.
# Synthetic trading days from the start of the requested 240-calendar-day
# lookback window to the target date: comfortably more distinct trade dates than
# the 120 the analysis window needs.
SOURCE_HISTORY_DATES = business_days("2026-01-20", TARGET_DATE)
HISTORY_DATES = iso_dates(SOURCE_HISTORY_DATES)
# Fewer distinct trade dates than the completeness requirement.
SHORT_SOURCE_HISTORY_DATES = business_days("2026-08-03", TARGET_DATE)
SHORT_HISTORY_DATES = iso_dates(SHORT_SOURCE_HISTORY_DATES)


def fake_api(trade_dates: list[str] | None = None) -> FakeTushareApi:
    return FakeTushareApi(
        index_frames={
            csi1000_index_history.INDEX_CODE: index_history_frame(
                csi1000_index_history.INDEX_CODE,
                trade_dates if trade_dates is not None else SOURCE_HISTORY_DATES,
            )
        }
    )


def collect(api: FakeTushareApi) -> list[artifacts.RawRecord]:
    return csi1000_index_history.collect_index_daily_history(
        TARGET_DATE, lambda **kwargs: api.index_daily(**kwargs)
    )


def test_requests_csi1000_over_a_history_window() -> None:
    api = fake_api()

    collect(api)

    start_date, end_date = csi1000_index_history.lookback_window(TARGET_DATE)
    assert api.index_calls == [
        {
            "ts_code": "000852.SH",
            "start_date": start_date,
            "end_date": "20260917",
        }
    ]


def test_requested_window_reaches_well_beyond_120_calendar_days() -> None:
    start_date, end_date = csi1000_index_history.lookback_window(TARGET_DATE)

    assert end_date == "20260917"
    assert start_date == "20260120"
    assert (
        datetime.strptime(TARGET_DATE, tushare.TRADE_DATE_ISO_FORMAT)
        - datetime.strptime(start_date, tushare.TRADE_DATE_TUSHARE_FORMAT)
        > timedelta(days=120)
    )


def test_history_keeps_multiple_trade_dates_in_iso_form() -> None:
    records = collect(fake_api())

    assert [record["trade_date"] for record in records] == HISTORY_DATES
    assert {record["ts_code"] for record in records} == {"000852.SH"}


def test_requests_cover_the_requested_window_only() -> None:
    """The Raw artifact keeps the Target trade date; window bounds are guarded.

    Source rows outside ``start_date..target_trade_date`` are a Source contract
    mismatch and must fail instead of being written silently.
    """
    api = fake_api()

    collect(api)

    assert api.index_calls[0]["end_date"] == "20260917"
    assert api.index_calls[0]["start_date"] == csi1000_index_history.lookback_window(
        TARGET_DATE
    )[0]


def test_history_includes_the_target_trade_date() -> None:
    records = collect(fake_api())

    assert records[-1]["trade_date"] == TARGET_DATE


def test_history_covers_at_least_120_distinct_trade_dates() -> None:
    """The Raw artifact must be enough for the downstream 120-trading-day window."""
    records = collect(fake_api())

    trade_dates = {record["trade_date"] for record in records}
    assert len(trade_dates) >= csi1000_index_history.MIN_HISTORY_TRADE_DATES
    assert len(records) > csi1000_index_history.MIN_HISTORY_TRADE_DATES


def test_history_without_enough_trade_dates_is_an_error() -> None:
    api = fake_api(SHORT_SOURCE_HISTORY_DATES)

    assert len(SHORT_HISTORY_DATES) < csi1000_index_history.MIN_HISTORY_TRADE_DATES
    with pytest.raises(common.CollectionError, match="distinct"):
        collect(api)


def test_history_without_target_trade_date_is_an_error() -> None:
    api = fake_api(SOURCE_HISTORY_DATES[:-1])

    with pytest.raises(common.CollectionError):
        collect(api)


def test_source_without_data_is_an_error() -> None:
    with pytest.raises(common.CollectionError):
        collect(FakeTushareApi())


def test_duplicate_source_row_is_an_error() -> None:
    """One trade date must appear exactly once in the Raw history."""
    records = common.to_raw_records(
        index_history_frame("000852.SH", [*SOURCE_HISTORY_DATES, SOURCE_HISTORY_DATES[-1]])
    )

    with pytest.raises(common.CollectionError, match="duplicate"):
        csi1000_index_history.require_history_window(records, "2026-01-20", TARGET_DATE)


def test_another_index_code_is_an_error() -> None:
    records = common.to_raw_records(
        index_history_frame("000300.SH", SOURCE_HISTORY_DATES)
    )

    with pytest.raises(common.CollectionError, match="ts_code"):
        csi1000_index_history.require_history_window(records, "2026-01-20", TARGET_DATE)


def test_source_row_after_target_trade_date_is_an_error() -> None:
    """A row beyond the requested end date must not reach the Raw file."""
    # The fake Source only returns rows inside the requested window, so the
    # Collector's own guard is exercised directly.
    records = common.to_raw_records(
        index_history_frame("000852.SH", [*SOURCE_HISTORY_DATES, "20260918"])
    )

    with pytest.raises(common.CollectionError):
        csi1000_index_history.require_history_window(records, "2026-01-20", TARGET_DATE)


def test_raw_layer_adds_no_derived_fields() -> None:
    records = collect(fake_api())

    source_fields = set(index_history_frame("000852.SH", SOURCE_HISTORY_DATES).columns)
    for record in records:
        assert set(record) == source_fields
    assert not any(
        field in record
        for record in records
        for field in ("ma", "ma20", "atr", "realized_volatility", "return")
    )


def test_raw_history_is_not_trimmed_to_120_rows() -> None:
    """The Collector keeps the collected window; the 120-row cut is assembly."""
    records = collect(fake_api())

    assert len(records) == len(SOURCE_HISTORY_DATES)
    assert len(records) != csi1000_index_history.MIN_HISTORY_TRADE_DATES


def test_main_writes_raw_dataset_file(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_code = csi1000_index_history.main([TARGET_DATE])

    assert exit_code == 0
    raw_path = (
        test_workdir
        / "raw"
        / artifacts.CSI1000_RAW_SUBDIR
        / TARGET_DATE
        / "index_daily_history.json"
    )
    assert raw_path.is_file()
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    assert isinstance(records, list)
    assert [record["trade_date"] for record in records] == HISTORY_DATES
    assert "index_daily_history.json" in capsys.readouterr().out


def test_main_fails_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(tushare.TOKEN_ENV_VAR, raising=False)

    def unreachable_api(token: str) -> tushare.TushareApi:
        raise AssertionError("no credential must mean no Source client")

    monkeypatch.setattr(tushare, "create_tushare_api", unreachable_api)

    assert csi1000_index_history.main([TARGET_DATE]) == 1


def test_main_rejects_non_iso_trade_date(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_code = csi1000_index_history.main(["20260917"])

    assert exit_code == 1
    assert api.index_calls == []
