"""Shared IM daily Capture behavior used by active Products."""

from __future__ import annotations

import pytest

from market_snapshot.capture import common, im_futures_basic, im_futures_daily
from support.fake_source import (
    FakeTushareApi,
    futures_basic_frame,
    futures_daily_frame,
    im_contract,
)

TARGET_DATE = "2026-09-17"
CONTRACTS = [
    im_contract("IM2603.CFX", list_date="20260216", delist_date="20260320"),
    im_contract("IM2609.CFX", list_date="20260817", delist_date="20260918"),
    im_contract("IM2612.CFX", list_date="20261116", delist_date="20261218"),
]


def fake_api() -> FakeTushareApi:
    return FakeTushareApi(
        futures_basic=futures_basic_frame(CONTRACTS),
        futures_daily={
            "IM2603.CFX": futures_daily_frame("IM2603.CFX", ["20260319"]),
            "IM2609.CFX": futures_daily_frame(
                "IM2609.CFX", ["20260916", "20260917"]
            ),
        },
    )


def test_target_date_capture_queries_active_contracts_only() -> None:
    api = fake_api()
    basic = im_futures_basic.capture(api, TARGET_DATE)

    records = im_futures_daily.capture_target_date(api, TARGET_DATE, basic)

    assert [(row["ts_code"], row["trade_date"]) for row in records] == [
        ("IM2609.CFX", TARGET_DATE)
    ]
    assert [call["ts_code"] for call in api.fut_daily_calls] == ["IM2609.CFX"]
    assert api.fut_daily_calls[0]["trade_date"] == "20260917"


def test_target_date_capture_keeps_missing_daily_as_raw_absence() -> None:
    api = FakeTushareApi(futures_basic=futures_basic_frame(CONTRACTS))
    basic = im_futures_basic.capture(api, TARGET_DATE)

    assert im_futures_daily.capture_target_date(api, TARGET_DATE, basic) == []


def test_target_date_capture_rejects_another_contract_or_date() -> None:
    api = fake_api()
    basic = im_futures_basic.capture(api, TARGET_DATE)

    with pytest.raises(common.CollectionError, match="ts_code"):
        im_futures_daily.collect_target_date_im_futures_daily(
            TARGET_DATE,
            basic,
            lambda **_kwargs: futures_daily_frame("IM2610.CFX", ["20260917"]),
        )
    with pytest.raises(common.CollectionError, match="trade_date"):
        im_futures_daily.collect_target_date_im_futures_daily(
            TARGET_DATE,
            basic,
            lambda **kwargs: futures_daily_frame(kwargs["ts_code"], ["20260916"]),
        )


def test_explicit_range_capture_respects_contract_lifecycle() -> None:
    api = fake_api()
    basic = im_futures_basic.capture(api, TARGET_DATE)

    records = im_futures_daily.capture_range(
        api, "2026-03-01", TARGET_DATE, basic
    )

    assert {(row["ts_code"], row["trade_date"]) for row in records} == {
        ("IM2603.CFX", "2026-03-19"),
        ("IM2609.CFX", "2026-09-16"),
        ("IM2609.CFX", TARGET_DATE),
    }
    assert [call["ts_code"] for call in api.fut_daily_calls] == [
        "IM2603.CFX",
        "IM2609.CFX",
    ]
    assert api.fut_daily_calls[0]["end_date"] == "20260320"
    assert api.fut_daily_calls[1]["start_date"] == "20260817"
