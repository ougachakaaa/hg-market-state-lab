import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import _common
import fetch_im_futures_basic
import fetch_im_futures_daily
from fake_source import FakeTushareApi, futures_basic_frame, futures_daily_frame, im_contract

TARGET_DATE = "2026-09-17"
# Covers a delisted contract, two listed before the target date, and one listed
# after it.
CONTRACTS = [
    im_contract("IM2509.CFE", list_date="20250818", delist_date="20250919"),
    im_contract("IM2603.CFE", list_date="20260216", delist_date="20260320"),
    im_contract("IM2609.CFE", list_date="20260817", delist_date="20260918"),
    im_contract("IM2612.CFE", list_date="20261116", delist_date="20261218"),
]
# Contracts whose lifecycle overlaps the collection window, in query order.
WINDOW_CONTRACTS = ["IM2509.CFE", "IM2603.CFE", "IM2609.CFE"]
# One date of each contract lifecycle: the fake Source needs a daily row for
# every contract that has entered its effective trading range.
LIFECYCLE_DATES = {
    "IM2509.CFE": ["20250818", "20250919"],
    "IM2603.CFE": ["20260216", "20260217", "20260320"],
    "IM2609.CFE": ["20260817", "20260916", "20260917"],
    "IM2612.CFE": ["20261116"],
}
DAILY_DATES = {ts_code: LIFECYCLE_DATES[ts_code] for ts_code in WINDOW_CONTRACTS}
# The whole history one long-lived contract holds, enough for the downstream
# 60-trading-day window, next to the one date every other window contract needs.
FULL_WINDOW_DATES = {
    "IM2509.CFE": LIFECYCLE_DATES["IM2509.CFE"],
    "IM2603.CFE": LIFECYCLE_DATES["IM2603.CFE"],
    "IM2609.CFE": LIFECYCLE_DATES["IM2609.CFE"],
    "IM2512.CFE": ["20251117", "20260918"],
}
IM2512 = im_contract("IM2512.CFE", list_date="20251117", delist_date="20260918")


def business_days(start: str, end: str) -> list[str]:
    """Build synthetic trading days in Source form for the given ISO date range."""
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    days: list[str] = []
    current = first
    while current <= last:
        if current.weekday() < 5:
            days.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return days


def fake_api(
    *,
    contracts: list[dict[str, Any]] | None = None,
    daily_dates: dict[str, list[str]] | None = None,
) -> FakeTushareApi:
    dates = DAILY_DATES if daily_dates is None else daily_dates
    return FakeTushareApi(
        futures_basic=futures_basic_frame(CONTRACTS if contracts is None else contracts),
        futures_daily={
            ts_code: futures_daily_frame(ts_code, trade_dates)
            for ts_code, trade_dates in dates.items()
        },
    )


def collect(api: FakeTushareApi) -> list[_common.RawRecord]:
    return fetch_im_futures_daily.collect_im_futures_daily(
        TARGET_DATE,
        api.futures_basic,
        lambda **kwargs: api.fut_daily(**kwargs),
    )


def queried_contracts(api: FakeTushareApi) -> list[str]:
    return [call["ts_code"] for call in api.fut_daily_calls]


def test_collects_the_im_contract_facts_from_fut_basic() -> None:
    """The daily Collector reads its contracts from Tushare ``fut_basic``."""
    api = fake_api()

    fetch_im_futures_basic.collect_im_futures_basic(
        TARGET_DATE, lambda **kwargs: api.fut_basic(**kwargs)
    )

    assert api.fut_basic_calls == [{"exchange": "CFFEX", "fut_type": "1", "fut_code": "IM"}]


def test_queries_each_window_contract_over_its_effective_range() -> None:
    api = fake_api()

    collect(api)

    window_start = fetch_im_futures_daily.window_start_date(TARGET_DATE)
    assert window_start == "2025-08-13"
    assert (date.fromisoformat(TARGET_DATE) - date.fromisoformat(window_start)).days > 120
    # The query ends at ``min(delist_date, target_trade_date)``, so a contract
    # delisted inside the window is not asked for facts after its delisting.
    assert api.fut_daily_calls == [
        {
            "ts_code": "IM2509.CFE",
            "trade_date": "",
            "start_date": "20250818",
            "end_date": "20250919",
        },
        {
            "ts_code": "IM2603.CFE",
            "trade_date": "",
            "start_date": "20260216",
            "end_date": "20260320",
        },
        {
            "ts_code": "IM2609.CFE",
            "trade_date": "",
            "start_date": "20260817",
            "end_date": "20260917",
        },
    ]


def test_contracts_listed_after_the_target_date_are_not_queried() -> None:
    api = fake_api()

    collect(api)

    assert "IM2612.CFE" not in queried_contracts(api)


def test_contracts_without_lifecycle_overlap_are_not_queried() -> None:
    """A contract delisted before the collection window carries no window facts."""
    long_gone = im_contract("IM2506.CFE", list_date="20250519", delist_date="20250620")
    api = fake_api(contracts=[*CONTRACTS, long_gone])

    records = collect(api)

    assert queried_contracts(api) == WINDOW_CONTRACTS
    assert "IM2506.CFE" not in queried_contracts(api)
    assert {record["ts_code"] for record in records} == set(WINDOW_CONTRACTS)


def test_records_cover_several_trade_dates_and_only_im_contracts() -> None:
    records = collect(fake_api())

    assert {record["trade_date"] for record in records} == {
        "2025-08-18",
        "2025-09-19",
        "2026-02-16",
        "2026-02-17",
        "2026-03-20",
        "2026-08-17",
        "2026-09-16",
        "2026-09-17",
    }
    assert {record["ts_code"] for record in records} == set(WINDOW_CONTRACTS)


def test_records_cover_enough_history_for_a_60_trading_day_window() -> None:
    """The Raw artifact keeps the whole collected history, not a 60-day selection."""
    # One contract carries daily facts over its whole effective range, spanning
    # more than the 60 trading days assembly needs.
    full_window = business_days("2025-08-14", "2026-09-17")
    api = fake_api(
        contracts=[*CONTRACTS, IM2512],
        daily_dates={**FULL_WINDOW_DATES, "IM2512.CFE": full_window},
    )

    records = collect(api)

    im2512_dates = {
        str(record["trade_date"]) for record in records if record["ts_code"] == "IM2512.CFE"
    }
    assert len(im2512_dates) > 60
    assert min(im2512_dates) == "2025-11-17"
    assert max(im2512_dates) == "2026-09-17"
    all_trade_dates = {str(record["trade_date"]) for record in records}
    assert TARGET_DATE in all_trade_dates
    assert len(all_trade_dates) > 60
    assert len(records) > len(all_trade_dates)


def test_rows_keep_source_fields_and_no_derived_values() -> None:
    records = collect(fake_api())
    record = records[0]

    assert set(record) == set(futures_daily_frame("IM2603.CFE", []).columns)
    assert record["change1"] == 1.0
    assert record["change2"] == 1.5
    assert record["oi_chg"] == -120.0
    assert not {
        "basis",
        "basis_pct",
        "annualized_basis",
        "calendar_spread",
        "term_structure",
        "roll_yield",
    } & set(record)


def test_rows_outside_the_contract_lifecycle_are_an_error() -> None:
    """A Source row before the contract listing must not reach the Raw file."""
    # IM2609.CFE lists on 2026-08-17, so a 2026-08-01 row is a Source mismatch.
    before_listing = futures_daily_frame("IM2609.CFE", ["20260801"])
    api = fake_api()

    with pytest.raises(_common.CollectionError, match="outside"):
        fetch_im_futures_daily.collect_im_futures_daily(
            TARGET_DATE,
            api.futures_basic,
            lambda **kwargs: (
                before_listing if kwargs["ts_code"] == "IM2609.CFE" else api.fut_daily(**kwargs)
            ),
        )


def test_rows_after_the_delist_date_are_an_error() -> None:
    """The lifecycle upper bound is ``min(delist_date, target_trade_date)``."""
    # IM2603.CFE delists on 2026-03-20, so a 2026-03-25 row is a Source mismatch.
    after_delisting = futures_daily_frame("IM2603.CFE", ["20260325"])
    api = fake_api()

    with pytest.raises(_common.CollectionError, match="outside"):
        fetch_im_futures_daily.collect_im_futures_daily(
            TARGET_DATE,
            api.futures_basic,
            lambda **kwargs: (
                after_delisting if kwargs["ts_code"] == "IM2603.CFE" else api.fut_daily(**kwargs)
            ),
        )


def test_rows_of_another_contract_are_an_error() -> None:
    """A response that does not belong to the requested contract is a mismatch."""
    api = fake_api()

    with pytest.raises(_common.CollectionError, match="ts_code"):
        fetch_im_futures_daily.collect_im_futures_daily(
            TARGET_DATE,
            api.futures_basic,
            lambda **kwargs: (
                futures_daily_frame("IM2699.CFE", ["20260916"])
                if kwargs["ts_code"] == "IM2609.CFE"
                else api.fut_daily(**kwargs)
            ),
        )


def test_window_contract_without_daily_rows_is_an_error() -> None:
    """A contract inside its effective range must have daily facts."""
    api = fake_api(daily_dates={"IM2603.CFE": LIFECYCLE_DATES["IM2603.CFE"]})

    with pytest.raises(_common.CollectionError, match="no daily row"):
        collect(api)


def test_source_without_daily_rows_is_an_error() -> None:
    api = fake_api(daily_dates={})

    with pytest.raises(_common.CollectionError):
        collect(api)


def test_source_without_contract_facts_is_an_error() -> None:
    with pytest.raises(_common.CollectionError):
        collect(FakeTushareApi())


def test_contract_without_lifecycle_facts_is_an_error() -> None:
    """A member contract with incomplete lifecycle facts fails the collection."""
    pending = im_contract("IM2703.CFE", list_date="20270315", delist_date=None)

    with pytest.raises(_common.CollectionError, match="lifecycle"):
        fetch_im_futures_daily.collect_im_futures_daily(
            TARGET_DATE,
            futures_basic_frame([*CONTRACTS, pending]),
            lambda **kwargs: pd.DataFrame(),
        )


def test_window_contract_without_usable_lifecycle_facts_is_an_error() -> None:
    broken = {"ts_code": "IM2703.CFE", "list_date": None, "delist_date": None}

    with pytest.raises(_common.CollectionError, match="lifecycle"):
        fetch_im_futures_daily.in_collection_window(broken, "2025-08-13", TARGET_DATE)


def test_lifecycle_ending_before_it_starts_is_an_error() -> None:
    # The window overlap holds, so the inverted lifecycle is what must fail.
    broken = {"ts_code": "IM2703.CFE", "list_date": "2026-09-15", "delist_date": "2026-09-10"}

    with pytest.raises(_common.CollectionError, match="before"):
        fetch_im_futures_daily.in_collection_window(broken, "2025-08-13", TARGET_DATE)


def test_effective_range_caps_the_lifecycle_at_the_target_trade_date() -> None:
    in_window = im_contract("IM2609.CFE", list_date="20260817", delist_date="20260918")
    delisted_inside = im_contract("IM2603.CFE", list_date="20260216", delist_date="20260320")
    listed_after_the_window = im_contract(
        "IM2703.CFE", list_date="20270315", delist_date="20270319"
    )
    delisted_before_the_window = im_contract(
        "IM2506.CFE", list_date="20250519", delist_date="20250620"
    )

    assert fetch_im_futures_daily.effective_range(in_window, TARGET_DATE) == (
        "2026-08-17",
        TARGET_DATE,
    )
    assert fetch_im_futures_daily.effective_range(delisted_inside, TARGET_DATE) == (
        "2026-02-16",
        "2026-03-20",
    )
    assert fetch_im_futures_daily.effective_range(listed_after_the_window, TARGET_DATE) is None
    assert fetch_im_futures_daily.effective_range(delisted_before_the_window, TARGET_DATE) is None


def test_main_writes_raw_dataset_file(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(_common.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(_common, "create_tushare_api", lambda token: api)

    exit_code = fetch_im_futures_daily.main([TARGET_DATE])

    assert exit_code == 0
    raw_path = (
        test_workdir / "raw" / _common.CSI1000_RAW_SUBDIR / TARGET_DATE / "im_futures_daily.json"
    )
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    assert isinstance(records, list)
    assert {record["ts_code"] for record in records} == set(WINDOW_CONTRACTS)
    assert "im_futures_daily.json" in capsys.readouterr().out


def test_main_fails_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_common.TOKEN_ENV_VAR, raising=False)

    def unreachable_api(token: str) -> _common.TushareApi:
        raise AssertionError("no credential must mean no Source client")

    monkeypatch.setattr(_common, "create_tushare_api", unreachable_api)

    assert fetch_im_futures_daily.main([TARGET_DATE]) == 1


def test_main_rejects_non_iso_trade_date(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_common.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(_common, "create_tushare_api", lambda token: api)

    exit_code = fetch_im_futures_daily.main(["20260917"])

    assert exit_code == 1
    assert api.fut_daily_calls == []
