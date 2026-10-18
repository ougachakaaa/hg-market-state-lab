from typing import Any

import pandas as pd
import pytest

from data_snapshot import artifacts
from data_snapshot.capture import common, mo_option_basic, mo_option_daily
from snapshot_support.fake_source import (
    FakeTushareApi,
    mo_option_contract,
    option_basic_frame,
    option_daily_frame,
)

TARGET_DATE = "2026-09-17"
ACTIVE_CONTRACTS = [
    mo_option_contract("MO2609-C-7000.CFE", exercise_price=7000.0, call_put="C"),
    mo_option_contract("MO2609-C-7200.CFE", exercise_price=7200.0, call_put="C"),
    mo_option_contract("MO2609-P-7000.CFE", exercise_price=7000.0, call_put="P"),
    mo_option_contract("MO2609-P-7200.CFE", exercise_price=7200.0, call_put="P"),
]
DELISTED_CONTRACT = mo_option_contract(
    "MO2608-C-7000.CFE", call_put="C", list_date="20260520", delist_date="20260828"
)
OTHER_PRODUCT = mo_option_contract("IO2609-C-4000.CFE", opt_code="OP000300.SH", call_put="C")
ACTIVE_CODES = [str(contract["ts_code"]) for contract in ACTIVE_CONTRACTS]


def daily_rows(contracts: list[str], trade_date: str = "20260917") -> pd.DataFrame:
    """Build ``opt_daily`` rows for the given contracts."""
    return option_daily_frame(trade_date, contracts)


def fake_api(
    *,
    basic_contracts: list[dict[str, Any]] | None = None,
    daily_contracts: list[str] | None = None,
) -> FakeTushareApi:
    return FakeTushareApi(
        option_basic=option_basic_frame(
            basic_contracts if basic_contracts is not None else ACTIVE_CONTRACTS
        ),
        option_daily=daily_rows(
            daily_contracts if daily_contracts is not None else ACTIVE_CODES
        ),
    )


def collect(api: FakeTushareApi) -> list[artifacts.RawRecord]:
    """Run the daily Capture on the MO basic facts of the same request."""
    return mo_option_daily.collect_mo_option_daily(
        TARGET_DATE,
        mo_option_basic.capture(api, TARGET_DATE),
        lambda **kwargs: api.opt_daily(**kwargs),
    )


def test_uses_target_trade_date_in_source_form() -> None:
    api = fake_api()

    collect(api)

    assert api.opt_daily_calls == [
        {"trade_date": "20260917", "exchange": "CFFEX", "start_date": ""}
    ]


def test_keeps_daily_facts_of_the_active_mo_universe() -> None:
    api = fake_api()

    records = collect(api)

    assert [record["ts_code"] for record in records] == [
        "MO2609-C-7000.CFE",
        "MO2609-C-7200.CFE",
        "MO2609-P-7000.CFE",
        "MO2609-P-7200.CFE",
    ]
    assert {record["trade_date"] for record in records} == {TARGET_DATE}


def test_other_cffex_products_are_ignored_as_non_members() -> None:
    """``exchange=CFFEX`` returns IO/HO too; they are not in this Capture scope."""
    api = fake_api(
        basic_contracts=[*ACTIVE_CONTRACTS, DELISTED_CONTRACT, OTHER_PRODUCT],
        daily_contracts=[
            *ACTIVE_CODES,
            str(DELISTED_CONTRACT["ts_code"]),
            str(OTHER_PRODUCT["ts_code"]),
        ],
    )

    records = collect(api)

    assert [record["ts_code"] for record in records] == ACTIVE_CODES


def test_daily_row_of_an_inactive_mo_contract_is_ignored() -> None:
    """A not-yet-listed or delisted MO contract is not in the active universe."""
    not_yet_listed = mo_option_contract(
        "MO2610-C-7000.CFE", list_date="20260924", delist_date="20261023", call_put="C"
    )
    api = fake_api(daily_contracts=[*ACTIVE_CODES, str(not_yet_listed["ts_code"])])

    records = collect(api)

    assert [record["ts_code"] for record in records] == ACTIVE_CODES


def test_missing_active_mo_daily_row_is_an_error() -> None:
    api = fake_api(daily_contracts=ACTIVE_CODES[:-1])

    with pytest.raises(common.CollectionError, match="no daily row"):
        collect(api)


def test_duplicate_active_mo_daily_row_is_an_error() -> None:
    api = fake_api(daily_contracts=[*ACTIVE_CODES, ACTIVE_CODES[0]])

    with pytest.raises(common.CollectionError, match="more than one row"):
        collect(api)


def test_universe_without_active_contract_is_an_error() -> None:
    api = fake_api(basic_contracts=[DELISTED_CONTRACT])

    with pytest.raises(common.CollectionError):
        collect(api)


def test_source_without_daily_rows_is_an_error() -> None:
    api = fake_api(daily_contracts=[])

    with pytest.raises(common.CollectionError):
        collect(api)


def test_daily_rows_of_another_trade_date_are_an_error() -> None:
    api = fake_api()
    api.option_daily = daily_rows(
        [str(contract["ts_code"]) for contract in ACTIVE_CONTRACTS], trade_date="20260916"
    )

    with pytest.raises(common.CollectionError):
        collect(api)


def test_daily_rows_keep_zero_activity_contracts() -> None:
    api = fake_api()
    api.option_daily.loc[0, ["vol", "amount", "oi"]] = 0.0

    records = collect(api)

    assert records[0]["vol"] == 0.0
    assert records[0]["amount"] == 0.0
    assert records[0]["oi"] == 0.0


def test_static_contract_facts_are_not_joined_into_daily_raw() -> None:
    records = collect(fake_api())

    assert set(records[0]) == set(option_daily_frame("20260917", []).columns)
    assert not {
        "exercise_price",
        "strike",
        "maturity_date",
        "expiry_date",
        "call_put",
        "option_type",
        "moneyness",
        "iv",
        "delta",
        "gamma",
        "vega",
        "theta",
    } & set(records[0])
