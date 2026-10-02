"""Shared IM basis predictor with a fake-Source vertical slice."""

from __future__ import annotations

from datetime import date, timedelta
from typing import cast

import pandas as pd
import pytest

from market_research.shared.distribution import linear_quantile
from market_research.shared.im_basis import daily_im_basis
from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryRequest,
    CSI1000IMBasisHistoryService,
)
from market_snapshot.sources import tushare

CONTRACTS = (
    ("IM2601.CFE", "20250101", "20260130", 102.0),
    ("IM2602.CFE", "20250201", "20260227", 104.0),
    ("IM2603.CFE", "20250301", "20260327", 106.0),
    ("IM2606.CFE", "20250601", "20260626", 108.0),
)


class FakeTushareApi:
    """Small Source fake containing only the three endpoints in this slice."""

    def __init__(
        self,
        index_frame: pd.DataFrame,
        basic_frame: pd.DataFrame,
        daily_frames: dict[str, pd.DataFrame],
    ) -> None:
        self.index_frame = index_frame
        self.basic_frame = basic_frame
        self.daily_frames = daily_frames

    @staticmethod
    def _range(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
        values = frame["trade_date"].astype(str)
        return frame[(values >= start) & (values <= end)].copy()

    def index_daily(
        self,
        *,
        ts_code: str,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        assert ts_code == "000852.SH"
        if trade_date is not None:
            return self._range(self.index_frame, trade_date, trade_date)
        assert start_date is not None and end_date is not None
        return self._range(self.index_frame, start_date, end_date)

    def fut_basic(
        self,
        *,
        exchange: str,
        fut_type: str | None = None,
        fut_code: str | None = None,
        fields: str | None = None,
    ) -> pd.DataFrame:
        assert exchange == "CFFEX" and fut_type == "1" and fut_code == "IM"
        return self.basic_frame.copy()

    def fut_daily(
        self,
        *,
        ts_code: str | None = None,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        assert ts_code is not None
        frame = self.daily_frames[ts_code]
        if trade_date is not None:
            return self._range(frame, trade_date, trade_date)
        assert start_date is not None and end_date is not None
        return self._range(frame, start_date, end_date)


def weekdays(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    result: list[str] = []
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return result


def full_service(count: int = 30) -> tuple[CSI1000IMBasisHistoryService, list[str]]:
    dates = weekdays("2025-12-01", count)
    index_frame = pd.DataFrame(
        {
            "ts_code": ["000852.SH"] * count,
            "trade_date": dates,
            "close": [100.0 + index for index in range(count)],
        }
    )
    basic_frame = pd.DataFrame(
        [
            {
                "ts_code": code,
                "symbol": code.split(".")[0],
                "exchange": "CFFEX",
                "fut_code": "IM",
                "list_date": listed,
                "delist_date": delisted,
            }
            for code, listed, delisted, _ in CONTRACTS
        ]
    )
    daily_frames = {
        code: pd.DataFrame(
            {
                "ts_code": [code] * count,
                "trade_date": dates,
                "close": [close + index for index in range(count)],
            }
        )
        for code, _, _, close in CONTRACTS
    }
    api = FakeTushareApi(
        index_frame=index_frame,
        basic_frame=basic_frame,
        daily_frames=daily_frames,
    )
    return CSI1000IMBasisHistoryService(cast(tushare.TushareApi, api)), dates


def request(dates: list[str]) -> CSI1000IMBasisHistoryRequest:
    return CSI1000IMBasisHistoryRequest(
        start_trade_date=date.fromisoformat(
            f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}"
        ).isoformat(),
        end_trade_date=date.fromisoformat(
            f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}"
        ).isoformat(),
    )


def test_shared_predictor_excludes_m0_and_quantile_is_linear() -> None:
    service, dates = full_service(2)
    daily = daily_im_basis(service.run(request(dates)))

    first = daily[0]
    assert first.non_front_mean_basis == pytest.approx(
        sum(first.annualized_basis_by_slot[slot] for slot in ("M1", "Q1", "Q2")) / 3
    )
    assert linear_quantile([0.0, 10.0], 0.25) == 2.5
