"""Public boundary and completeness tests for Index Daily History."""

from __future__ import annotations

from dataclasses import fields

import pandas as pd
import pytest

import market_snapshot.products.index_daily_history as history
from market_snapshot.products.index_daily_history.preparation import (
    IndexDailyHistoryPreparationError,
    prepare_history,
)
from market_snapshot.sources import tushare
from support.fake_source import FakeTushareApi, index_history_frame

CODE = "000852.SH"


def request(
    start: str = "2026-09-21", end: str = "2026-09-22", count: int = 2
) -> history.IndexDailyHistoryRequest:
    return history.IndexDailyHistoryRequest(CODE, start, end, count)


def source(*dates: str) -> FakeTushareApi:
    return FakeTushareApi(index_frames={CODE: index_history_frame(CODE, list(dates))})


def test_public_facade_and_zero_warmup_result() -> None:
    api = source("20260918", "20260921", "20260922")
    result = history.IndexDailyHistoryService(api).run(request(count=0))

    assert isinstance(result, history.IndexDailyHistoryResult)
    assert result.ts_code == CODE
    assert result.requested_start_trade_date == "2026-09-21"
    assert result.requested_end_trade_date == "2026-09-22"
    assert result.requested_pre_start_observation_count == 0
    assert result.warmup_observations == ()
    assert [row.trade_date for row in result.sample_observations] == [
        "2026-09-21",
        "2026-09-22",
    ]
    assert [field.name for field in fields(result.sample_observations[0])] == [
        "trade_date",
        "close",
        "volume",
    ]
    assert api.index_calls == [
        {"ts_code": CODE, "start_date": "20260921", "end_date": "20260922"}
    ]


def test_exact_preceding_observations_span_weekend_and_year_boundary() -> None:
    api = source("20251229", "20251230", "20251231", "20260102", "20260105")
    result = history.IndexDailyHistoryService(api).run(request("2026-01-03", "2026-01-06", 3))

    assert [row.trade_date for row in result.warmup_observations] == [
        "2025-12-30",
        "2025-12-31",
        "2026-01-02",
    ]
    assert [row.trade_date for row in result.sample_observations] == ["2026-01-05"]
    assert api.index_calls == [
        {"ts_code": CODE, "start_date": "20260103", "end_date": "20260106"},
        {"ts_code": CODE, "start_date": "20260101", "end_date": "20260102"},
        {"ts_code": CODE, "start_date": "20250101", "end_date": "20251231"},
    ]


def test_short_calendar_lookback_keeps_expanding_until_exact_count() -> None:
    api = source("20260910", "20260915", "20260918", "20260921")
    result = history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 3))
    assert [row.trade_date for row in result.warmup_observations] == [
        "2026-09-10",
        "2026-09-15",
        "2026-09-18",
    ]


def test_insufficient_history_fails_without_partial_result() -> None:
    api = source("20260918", "20260921")
    with pytest.raises(history.IndexDailyHistoryError, match="insufficient pre-start observations"):
        history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 2))


def test_empty_sample_fails_without_historical_queries() -> None:
    api = source("20260918")
    with pytest.raises(history.IndexDailyHistoryError, match="no sample observation"):
        history.IndexDailyHistoryService(api).run(request())
    assert len(api.index_calls) == 1


@pytest.mark.parametrize(
    "bad_request",
    [
        history.IndexDailyHistoryRequest("", "2026-09-21", "2026-09-22", 0),
        history.IndexDailyHistoryRequest("000852.SH,000300.SH", "2026-09-21", "2026-09-22", 0),
        history.IndexDailyHistoryRequest(CODE, "2026-9-21", "2026-09-22", 0),
        history.IndexDailyHistoryRequest(CODE, "2026-02-30", "2026-09-22", 0),
        history.IndexDailyHistoryRequest(CODE, "2026-09-22", "2026-09-21", 0),
        history.IndexDailyHistoryRequest(CODE, "2026-09-21", "2026-09-22", -1),
        history.IndexDailyHistoryRequest(CODE, "2026-09-21", "2026-09-22", True),
    ],
)
def test_invalid_request_fails_before_source_access(
    bad_request: history.IndexDailyHistoryRequest,
) -> None:
    api = source("20260921")
    with pytest.raises(history.IndexDailyHistoryError):
        history.IndexDailyHistoryService(api).run(bad_request)
    assert api.index_calls == []


def test_unsupported_index_is_classified() -> None:
    api = source("20260921")
    unsupported = history.IndexDailyHistoryRequest("INVALID.SH", "2026-09-21", "2026-09-21", 0)
    with pytest.raises(history.IndexDailyHistoryError, match="no sample observation"):
        history.IndexDailyHistoryService(api).run(unsupported)


@pytest.mark.parametrize("bad_date", ["20260921", "20260920"])
def test_duplicate_or_wrong_index_observation_is_rejected(bad_date: str) -> None:
    api = source("20260918", "20260921")
    frame = api.index_frames[CODE]
    if bad_date == "20260921":
        api.index_frames[CODE] = pd.concat([frame, frame.iloc[[1]]])
    else:
        api.index_frames[CODE].loc[1, "ts_code"] = "000300.SH"
    with pytest.raises(history.IndexDailyHistoryError):
        history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 1))


class OutOfRangeSource(FakeTushareApi):
    def index_daily(
        self,
        *,
        ts_code: str,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        return self.index_frames[ts_code]


def test_out_of_range_fact_is_rejected_without_dropping() -> None:
    api = OutOfRangeSource(index_frames={CODE: index_history_frame(CODE, ["20260920", "20260921"])})
    with pytest.raises(history.IndexDailyHistoryError, match="outside"):
        history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 0))


@pytest.mark.parametrize("value", [None, "bad", 0, -1, float("inf")])
def test_unusable_close_is_rejected(value: object) -> None:
    api = source("20260921")
    api.index_frames[CODE]["close"] = value
    with pytest.raises(history.IndexDailyHistoryError, match="close"):
        history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 0))


def test_nullable_and_zero_volume_are_preserved() -> None:
    api = source("20260921", "20260922")
    api.index_frames[CODE]["vol"] = pd.Series([None, 0.0], dtype=object)
    result = history.IndexDailyHistoryService(api).run(request(count=0))
    assert [row.volume for row in result.sample_observations] == [None, 0.0]


def test_missing_source_volume_remains_null() -> None:
    api = source("20260921")
    api.index_frames[CODE] = api.index_frames[CODE].drop(columns=["vol"])
    result = history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 0))
    assert result.sample_observations[0].volume is None


@pytest.mark.parametrize("value", ["bad", -1.0, float("inf"), True])
def test_invalid_present_volume_is_rejected(value: object) -> None:
    api = source("20260921")
    api.index_frames[CODE]["vol"] = value
    with pytest.raises(history.IndexDailyHistoryError, match="vol"):
        history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 0))


def test_preparation_rejects_nonfinite_present_raw_volume() -> None:
    fact = {"ts_code": CODE, "trade_date": "2026-09-21", "close": 100.0, "vol": float("nan")}
    with pytest.raises(IndexDailyHistoryPreparationError, match="vol"):
        prepare_history(request("2026-09-21", "2026-09-21", 0), [fact], [])


def test_source_failure_is_classified() -> None:
    class FailingSource(FakeTushareApi):
        def index_daily(
            self,
            *,
            ts_code: str,
            trade_date: str | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
        ) -> pd.DataFrame:
            raise RuntimeError("Source unavailable")

    with pytest.raises(history.IndexDailyHistoryError, match="Source unavailable"):
        history.IndexDailyHistoryService(FailingSource()).run(request())


def test_pre_start_source_failure_is_not_partial_success() -> None:
    class FailingHistorySource(FakeTushareApi):
        def index_daily(
            self,
            *,
            ts_code: str,
            trade_date: str | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
        ) -> pd.DataFrame:
            if end_date is not None and end_date < "20260921":
                raise RuntimeError("history unavailable")
            return super().index_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            )

    api = FailingHistorySource(index_frames={CODE: index_history_frame(CODE, ["20260921"])})
    with pytest.raises(history.IndexDailyHistoryError, match="history unavailable"):
        history.IndexDailyHistoryService(api).run(request("2026-09-21", "2026-09-21", 1))


def test_public_execution_entry_composes_fake_source(monkeypatch: pytest.MonkeyPatch) -> None:
    api = source("20260918", "20260921")
    tokens: list[str] = []
    monkeypatch.setattr(tushare, "get_tushare_token", lambda: "configured-token")

    def create_api(token: str) -> FakeTushareApi:
        tokens.append(token)
        return api

    monkeypatch.setattr(tushare, "create_tushare_api", create_api)
    result = history.run_index_daily_history(request("2026-09-21", "2026-09-21", 1))
    assert tokens == ["configured-token"]
    assert isinstance(result, history.IndexDailyHistoryResult)
    assert [row.trade_date for row in result.warmup_observations] == ["2026-09-18"]


@pytest.mark.parametrize("stage", ["credential", "client"])
def test_public_entry_classifies_composition_failure(
    monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    if stage == "credential":
        monkeypatch.setattr(
            tushare,
            "get_tushare_token",
            lambda: (_ for _ in ()).throw(tushare.TushareCredentialError("missing token")),
        )
    else:
        monkeypatch.setattr(tushare, "get_tushare_token", lambda: "configured-token")
        monkeypatch.setattr(
            tushare,
            "create_tushare_api",
            lambda _token: (_ for _ in ()).throw(RuntimeError("client unavailable")),
        )
    with pytest.raises(history.IndexDailyHistoryError):
        history.run_index_daily_history(request())


def test_public_entry_validates_before_credential_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected() -> str:
        raise AssertionError("credential loading must not be reached")

    monkeypatch.setattr(tushare, "get_tushare_token", unexpected)
    with pytest.raises(history.IndexDailyHistoryError, match="YYYY-MM-DD"):
        history.run_index_daily_history(request("2026-9-21"))
