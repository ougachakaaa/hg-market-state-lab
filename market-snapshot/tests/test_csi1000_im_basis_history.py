"""Authority-invariant tests for the CSI1000 IM Basis History product."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryError,
    CSI1000IMBasisHistoryRequest,
    CSI1000IMBasisHistoryService,
    run_csi1000_im_basis_history,
)
from market_snapshot.products.csi1000_im_basis_history.basis_semantics import (
    IMBasisError,
    assign_contract_slots,
)
from market_snapshot.sources import tushare
from support.fake_source import (
    FakeTushareApi,
    futures_basic_frame,
    futures_daily_frame,
    im_contract,
    index_history_frame,
)

CONTRACTS = (
    ("IM2601.CFE", "2025-01-01", "2026-01-30", 102.0),
    ("IM2602.CFE", "2025-02-01", "2026-02-27", 103.0),
    ("IM2603.CFE", "2025-03-01", "2026-03-27", 104.0),
    ("IM2606.CFE", "2025-06-01", "2026-06-26", 105.0),
)


def weekdays(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    result: list[str] = []
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return result


def api_for_dates(trade_dates: list[str]) -> FakeTushareApi:
    basics = [
        im_contract(code, list_date=listed.replace("-", ""), delist_date=delisted.replace("-", ""))
        for code, listed, delisted, _ in CONTRACTS
    ]
    return FakeTushareApi(
        index_frames={"000852.SH": index_history_frame("000852.SH", trade_dates, close=100.0)},
        futures_basic=futures_basic_frame(basics),
        futures_daily={
            code: futures_daily_frame(code, trade_dates, close=close)
            for code, _, _, close in CONTRACTS
        },
    )


def request_for(trade_dates: list[str]) -> CSI1000IMBasisHistoryRequest:
    return CSI1000IMBasisHistoryRequest(
        start_trade_date=pd.Timestamp(trade_dates[0]).strftime("%Y-%m-%d"),
        end_trade_date=pd.Timestamp(trade_dates[-1]).strftime("%Y-%m-%d"),
    )


def test_public_service_builds_complete_canonically_ordered_panel() -> None:
    dates = weekdays("2025-12-01", 3)
    api = api_for_dates(dates)

    result = CSI1000IMBasisHistoryService(api).run(request_for(dates))

    assert result.underlying_ts_code == "000852.SH"
    assert len(result.observations) == 12
    assert [row.contract_slot for row in result.observations[:4]] == [
        "M0",
        "M1",
        "Q1",
        "Q2",
    ]
    first = result.observations[0]
    assert first.future_close == 102.0
    assert first.basis_points == 2.0
    assert first.basis_pct == pytest.approx(2.0)
    assert first.annualized_basis_pct == pytest.approx(
        first.basis_pct * 365 / first.annualization_days
    )
    assert api.index_calls == [
        {"ts_code": "000852.SH", "start_date": dates[0], "end_date": dates[-1]}
    ]
    assert len(api.fut_basic_calls) == 1
    assert len(api.fut_daily_calls) == 4


def test_delivery_day_keeps_zero_calendar_days_and_uses_one_for_annualization() -> None:
    dates = ["20260130"]
    result = CSI1000IMBasisHistoryService(api_for_dates(dates)).run(request_for(dates))

    front = result.observations[0]
    assert front.contract_slot == "M0"
    assert front.days_to_delist == 0
    assert front.annualization_days == 1
    assert front.annualized_basis_pct == pytest.approx(front.basis_pct * 365)


def test_missing_active_daily_fact_fails_without_partial_result() -> None:
    dates = weekdays("2025-12-01", 2)
    api = api_for_dates(dates)
    api.futures_daily["IM2603.CFE"] = api.futures_daily["IM2603.CFE"].iloc[:1]

    with pytest.raises(CSI1000IMBasisHistoryError, match="missing IM daily row"):
        CSI1000IMBasisHistoryService(api).run(request_for(dates))


def test_duplicate_source_fact_fails_without_partial_result() -> None:
    dates = weekdays("2025-12-01", 2)
    api = api_for_dates(dates)
    frame = api.futures_daily["IM2603.CFE"]
    api.futures_daily["IM2603.CFE"] = pd.concat([frame, frame.iloc[[0]]])

    with pytest.raises(CSI1000IMBasisHistoryError, match="duplicate IM daily row"):
        CSI1000IMBasisHistoryService(api).run(request_for(dates))


@pytest.mark.parametrize(
    "history_request",
    [
        CSI1000IMBasisHistoryRequest("2025-12-02", "2025-12-01"),
        CSI1000IMBasisHistoryRequest("2025-12-1", "2025-12-02"),
    ],
)
def test_invalid_explicit_range_fails_before_source_calls(
    history_request: CSI1000IMBasisHistoryRequest,
) -> None:
    api = api_for_dates(weekdays("2025-12-01", 2))
    with pytest.raises(CSI1000IMBasisHistoryError):
        CSI1000IMBasisHistoryService(api).run(history_request)
    assert api.calls == []


def test_slot_mapping_rejects_duplicate_or_malformed_month_structure() -> None:
    contracts = [
        {
            "ts_code": code,
            "list_date": listed,
            "delist_date": delisted,
        }
        for code, listed, delisted, _ in CONTRACTS
    ]
    contracts[-1] = {
        "ts_code": "IM2609.CFE",
        "list_date": "2025-06-01",
        "delist_date": "2026-09-25",
    }
    with pytest.raises(IMBasisError, match="quarter IM months"):
        assign_contract_slots("2025-12-01", contracts)


def test_production_entry_owns_credential_and_client_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dates = weekdays("2025-12-01", 2)
    api = api_for_dates(dates)
    seen: list[str] = []
    monkeypatch.setattr(tushare, "get_tushare_token", lambda: "configured-token")

    def create_api(token: str) -> FakeTushareApi:
        seen.append(token)
        return api

    monkeypatch.setattr(tushare, "create_tushare_api", create_api)

    result = run_csi1000_im_basis_history(request_for(dates))

    assert seen == ["configured-token"]
    assert len(result.observations) == 8


def test_production_entry_validates_before_loading_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unreachable() -> str:
        raise AssertionError("invalid input must fail before credential loading")

    monkeypatch.setattr(tushare, "get_tushare_token", unreachable)
    with pytest.raises(CSI1000IMBasisHistoryError, match="YYYY-MM-DD"):
        run_csi1000_im_basis_history(
            CSI1000IMBasisHistoryRequest("2025-12-1", "2025-12-02")
        )


@pytest.mark.parametrize("stage", ["credential", "client"])
def test_production_entry_classifies_composition_failures(
    monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    dates = weekdays("2025-12-01", 2)
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

    with pytest.raises(CSI1000IMBasisHistoryError):
        run_csi1000_im_basis_history(request_for(dates))
