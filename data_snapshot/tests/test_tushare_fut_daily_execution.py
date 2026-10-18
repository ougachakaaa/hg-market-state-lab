"""Provider-call pacing and error normalization for CFFEX futures Capture."""

from __future__ import annotations

import pandas as pd
import pytest

from data_snapshot.capture import im_futures_basic, im_futures_daily, index_daily
from data_snapshot.sources import tushare
from snapshot_support.fake_source import FakeTushareApi

_REAL_PACE = tushare._pace_fut_daily
RATE_LIMIT = "抱歉，您访问接口(fut_daily)频率超限(300次/分钟)"


class RecordingApi(FakeTushareApi):
    def __init__(self, clock: list[float]) -> None:
        super().__init__()
        self.clock = clock
        self.starts: list[float] = []

    def fut_daily(
        self,
        *,
        ts_code: str | None = None,
        exchange: str | None = None,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        self.starts.append(self.clock[0])
        return super().fut_daily(
            ts_code=ts_code,
            exchange=exchange, trade_date=trade_date, start_date=start_date, end_date=end_date
        )


def test_fut_daily_pacing_spans_query_shapes_and_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [10.0]
    waits: list[float] = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(tushare, "_pace_fut_daily", _REAL_PACE)
    monkeypatch.setattr(tushare, "_monotonic", lambda: clock[0])
    monkeypatch.setattr(tushare, "_sleep", sleep)
    monkeypatch.setattr(tushare, "_last_fut_daily_start", None)
    first = RecordingApi(clock)
    second = RecordingApi(clock)

    im_futures_daily.query_fut_daily(first, "IF2601.CFX", "20260101", "20260131")
    im_futures_daily.query_target_date_fut_daily(second, "IM2601.CFX", "20260105")
    im_futures_daily.query_fut_daily(first, "IH2601.CFX", "20260101", "20260131")

    assert first.starts == [10.0, 10.5]
    assert second.starts == [10.25]
    assert waits == [0.25, 0.25]
    assert len(first.fut_daily_calls) == 2
    assert len(second.fut_daily_calls) == 1


def test_rate_limit_retries_once_after_conservative_wait(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    waits: list[float] = []
    paced: list[None] = []
    monkeypatch.setattr(tushare, "_pace_fut_daily", lambda: paced.append(None))
    monkeypatch.setattr(tushare, "_sleep", waits.append)
    calls = 0

    def provider() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise Exception(RATE_LIMIT)
        return pd.DataFrame([{"ts_code": "IF2601.CFX"}])

    result = tushare.call_fut_daily(provider)

    assert result.iloc[0]["ts_code"] == "IF2601.CFX"
    assert calls == 2
    assert len(paced) == 2
    assert waits == [tushare.FUT_DAILY_RATE_LIMIT_RETRY_SECONDS]


def test_rate_limit_exhaustion_is_source_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[float] = []
    monkeypatch.setattr(tushare, "_sleep", waits.append)
    calls = 0

    def provider() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        raise Exception(RATE_LIMIT)

    with pytest.raises(tushare.TushareSourceError, match="频率超限") as caught:
        tushare.call_fut_daily(provider)
    assert isinstance(caught.value.__cause__, Exception)
    assert calls == 2
    assert waits == [tushare.FUT_DAILY_RATE_LIMIT_RETRY_SECONDS]


@pytest.mark.parametrize(
    "message", ["network unavailable", "permission denied", "invalid endpoint"]
)
def test_other_provider_failures_are_normalized_without_retry(
    monkeypatch: pytest.MonkeyPatch, message: str
) -> None:
    waits: list[float] = []
    monkeypatch.setattr(tushare, "_sleep", waits.append)
    calls = 0

    def provider() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        raise RuntimeError(message)

    with pytest.raises(tushare.TushareSourceError, match=message) as caught:
        tushare.call_fut_daily(provider)
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert calls == 1
    assert waits == []


@pytest.mark.parametrize(
    "query",
    [
        lambda api: index_daily.query_index_daily_range(api, "000300.SH", "20260101", "20260131"),
        lambda api: im_futures_basic.query_fut_basic(api, "CFFEX", "1", "IF"),
    ],
)
def test_other_required_endpoints_normalize_provider_failure(query) -> None:
    class BrokenApi(FakeTushareApi):
        def index_daily(self, **_kwargs):
            raise RuntimeError("provider unavailable")

        def fut_basic(self, **_kwargs):
            raise RuntimeError("provider unavailable")

    with pytest.raises(tushare.TushareSourceError, match="provider unavailable") as caught:
        query(BrokenApi())
    assert isinstance(caught.value.__cause__, RuntimeError)
