"""WP3: actual HTTP/Research/DataLake services and SQLite, controlled Source only.

Dataset-private composition seams are test facilities, never consumer APIs.
"""

from collections import Counter
from datetime import date, timedelta
from time import perf_counter

import pytest

from data_lake.adapters.outbound.sqlite import Repository
from data_lake.datasets.tushare_equity_index_futures._service import (
    _create_service as futures_create,
)
from data_lake.datasets.tushare_equity_index_futures._source import DailySource
from data_lake.datasets.tushare_trade_calendar._service import _create_service as calendar_create
from data_lake.datasets.tushare_trade_calendar._source import TradeCalSource
from http_support.auth import authenticated_client
from market_research.descriptive.cases.futures_calendar_spread import daily_index, preparation
from ui_http.app import create_app
from ui_http.products.calendar_spread_relative_value.schemas import HistoricalResponse
from ui_http.products.futures_calendar_spread.schemas import DailyResponse


class Frame:
    def __init__(self, rows):
        self.rows = rows

    def to_dict(self, **kwargs):
        return self.rows


class Source:
    """Deterministic provider rows; weekends closed, ordinary monthly contracts."""

    def call(self, endpoint, **params):
        if endpoint == "trade_cal":
            start, end = (date.fromisoformat(params[k]) for k in ("start_date", "end_date"))
            return Frame(
                [
                    dict(
                        exchange="CFFEX",
                        cal_date=day.strftime("%Y%m%d"),
                        is_open=int(day.weekday() < 5),
                        pretrade_date=None,
                    )
                    for day in (start + timedelta(days=i) for i in range((end - start).days + 1))
                ]
            )
        catalog = [
            dict(
                ts_code=f"IF24{month:02}.CFX",
                symbol=f"IF24{month:02}",
                fut_code="IF",
                name="synthetic future",
                exchange="CFFEX",
                multiplier=300,
                trade_unit="point",
                per_unit=1,
                quote_unit="point",
                list_date="20240120" if month == 9 else "20231001",
                delist_date=f"2024{month:02}19",
                d_month=f"2024{month:02}",
                last_ddate=f"2024{month:02}19",
            )
            for month in (1, 2, 3, 6, 9)
        ]
        if endpoint == "fut_basic":
            return Frame([] if params["fut_type"] == "2" or params["offset"] else catalog)
        assert endpoint == "fut_daily"
        start, end = (date.fromisoformat(params[k]) for k in ("start_date", "end_date"))
        rows = []
        for i in range((end - start).days + 1):
            day = start + timedelta(days=i)
            if day.weekday() >= 5:
                continue
            for meta in catalog:
                if not meta["list_date"] <= day.strftime("%Y%m%d") <= meta["delist_date"]:
                    continue
                close = 4000 - int(meta["d_month"][-2:]) + i
                rows.append(
                    dict(
                        ts_code=meta["ts_code"],
                        trade_date=day.strftime("%Y%m%d"),
                        pre_close=close,
                        pre_settle=close,
                        open=close,
                        high=close,
                        low=close,
                        close=close,
                        settle=close,
                        change1=0,
                        change2=0,
                        vol=1,
                        amount=1,
                        oi=1,
                        oi_chg=0,
                        delv_settle=None,
                    )
                )
        return Frame(rows[params["offset"] : params["offset"] + 4000])


class ObservedSource:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = Counter()

    def call(self, endpoint, **params):
        self.calls[endpoint] += 1
        return self.delegate.call(endpoint, **params)


class ObservedService:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = Counter()
        self.exports = []

    def export(self, request):
        self.calls["export"] += 1
        view = self.delegate.export(request)
        self.exports.append(view)
        return view

    def ensure(self, request):
        self.calls["ensure"] += 1
        return self.delegate.ensure(request)


def isolated_services(root, executor):
    source = ObservedSource(executor)
    calendar = ObservedService(
        calendar_create(
            Repository(root / "calendar.sqlite3", "tushare_trade_calendar", "tushare"),
            lambda: TradeCalSource(source),
        )
    )
    futures = ObservedService(
        futures_create(
            Repository(root / "futures.sqlite3", "tushare_equity_index_futures", "tushare"),
            calendar,
            lambda: DailySource(source),
        )
    )
    return calendar, futures, source


@pytest.mark.parametrize(
    "start,end",
    [
        (None, "2024-01-02"),
        ("2024-01-02", "2024-01-05"),
        ("2024-01-02", "2024-02-16"),
    ],
)
def test_formal_submission_cold_hot_and_read_only(tmp_path, monkeypatch, start, end):
    root = tmp_path / "lake"
    calendar, futures, source = isolated_services(root, Source())
    monkeypatch.setattr(preparation, "create_calendar_service", lambda: calendar)
    monkeypatch.setattr(preparation, "create_futures_service", lambda: futures)
    # This existing core acceptance explicitly isolates reference acquisition.
    # Daily's default reference factory receives deterministic SSE closure proof.
    from types import SimpleNamespace

    from data_lake import CoverageResult
    from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord

    class ClosedSSE:
        def export(self, request):
            return TradeCalendarExport(
                "tushare_trade_calendar", "calendar", 1,
                SimpleNamespace(exchange="SSE"), request,
                CoverageResult(1, 1, 0, 0, 0, True),
                (TradeCalendarRecord("SSE", request.start_date, 0, None),),
            )

    monkeypatch.setattr(daily_index, "create_calendar_service", ClosedSSE)
    client = authenticated_client(create_app())
    body = dict(product_code="IF")
    if start:
        body.update(history_start=start, evaluation_date=end, histogram_edges=[-1, 0, 1])
        path = "/research/calendar-spread-relative-value/query"
    else:
        body.update(trade_date=end)
        path = "/data/futures-calendar-spread/query"
        # Empty-cache GET must fail without starting acquisition or creating a DB.
        read = client.get("/data/futures-calendar-spread", params=body)
        assert read.status_code == 409
        assert read.json()["error"]["reason_code"] == "cache_incomplete"
        assert not root.exists() and not source.calls

    measurements = []
    for temperature in ("cold", "hot"):
        before = [calendar.calls["ensure"], futures.calls["ensure"], sum(source.calls.values())]
        tick = perf_counter()
        response = client.post(path, json=body)
        elapsed = perf_counter() - tick
        assert response.status_code == 200, response.text
        payload = response.json()
        (HistoricalResponse if start else DailyResponse).model_validate_json(response.content)
        delta = [
            a - b
            for a, b in zip(
                [calendar.calls["ensure"], futures.calls["ensure"], sum(source.calls.values())],
                before,
                strict=True,
            )
        ]
        assert delta[:2] == ([1, 1] if temperature == "cold" else [0, 0])
        if temperature == "cold":
            assert delta[2] > 0
        else:
            assert delta[2] == 0
        assert calendar.exports[-1].coverage.complete
        assert futures.exports[-1].coverage.complete
        expected_dates = (date.fromisoformat(end) - date.fromisoformat(start or end)).days + 1
        assert calendar.exports[-1].coverage.requested_units == expected_dates
        assert futures.exports[-1].coverage.requested_units == sum(
            row.is_open for row in calendar.exports[-1].records
        )
        day = payload["current_day" if start else "day"]
        assert len(day["observations"]) == 6
        assert all(o["outcome"] == "valid" for o in day["observations"])
        if start:
            assert len(payload["pairs"]) == 6
            assert all(d["trade_date"] < end for d in payload["historical_days"])
            assert all(s["trade_date"] < end for p in payload["pairs"] for s in p["samples"])
        assert all(s not in response.text for s in (str(root), "TUSHARE_TOKEN", "ensure_result"))
        if temperature == "cold":
            cold = payload
        else:
            assert payload == cold
        measurements.append(dict(temperature=temperature, seconds=elapsed, counts=delta))
    if not start:
        before = (calendar.calls["ensure"], futures.calls["ensure"], source.calls.copy())
        read = client.get("/data/futures-calendar-spread", params=body)
        assert read.status_code == 200
        assert read.json()["day"] == cold["day"]
        assert read.json()["accounting"] == cold["accounting"]
        assert (calendar.calls["ensure"], futures.calls["ensure"], source.calls) == before
    assert {p.name for p in root.iterdir()} == {"calendar.sqlite3", "futures.sqlite3"}
    assert {p.name for p in tmp_path.iterdir()} == {"lake", "http-auth.sqlite3"}
    print(dict(request=body, measurements=measurements))
