import json
from pathlib import Path
from typing import Any

import pytest

from market_snapshot import artifacts
from market_snapshot.capture import common, im_futures_basic
from market_snapshot.sources import tushare
from support.fake_source import FakeTushareApi, futures_basic_frame, im_contract

TARGET_DATE = "2026-09-17"
IM_CONTRACTS = [
    im_contract("IM2601.CFE", list_date="20260119", delist_date="20260220"),
    im_contract("IM2609.CFE", list_date="20260817", delist_date="20260918"),
    im_contract("IM2612.CFE", list_date="20261116", delist_date="20261218"),
]
NOISE_CONTRACTS = [
    # Main / continuous contract: same fut_code, no delivery month in the symbol.
    im_contract(
        "IM.CFE",
        name="中证1000股指期货主力合约",
        list_date="20260817",
        delist_date="20260918",
    ),
    # Another CFFEX product.
    im_contract(
        "IF2609.CFE",
        fut_code="IF",
        name="沪深300股指期货2609",
        list_date="20260817",
        delist_date="20260918",
    ),
    # Another exchange.
    im_contract("IM2609.DCE", exchange="DCE", list_date="20260817", delist_date="20260918"),
]
ALL_CONTRACTS = [*IM_CONTRACTS, *NOISE_CONTRACTS]


def fake_api(contracts: list[dict[str, Any]] | None = None) -> FakeTushareApi:
    return FakeTushareApi(
        futures_basic=futures_basic_frame(ALL_CONTRACTS if contracts is None else contracts)
    )


def collect(api: FakeTushareApi) -> list[artifacts.RawRecord]:
    return im_futures_basic.collect_im_futures_basic(
        TARGET_DATE, lambda **kwargs: api.fut_basic(**kwargs)
    )


def test_requests_only_cffex_ordinary_monthly_im_contracts() -> None:
    api = fake_api()

    collect(api)

    assert api.fut_basic_calls == [
        {"exchange": "CFFEX", "fut_type": "1", "fut_code": "IM"},
    ]


def test_keeps_ordinary_im_contract_facts() -> None:
    records = collect(fake_api())

    assert [record["ts_code"] for record in records] == [
        "IM2601.CFE",
        "IM2609.CFE",
        "IM2612.CFE",
    ]


def test_contract_facts_keep_source_fields_and_units() -> None:
    records = collect(fake_api())
    record = records[0]

    assert record["exchange"] == "CFFEX"
    assert record["fut_code"] == "IM"
    assert record["multiplier"] == 200.0
    assert record["trade_unit"] == "元/点"
    assert record["list_date"] == "2026-01-19"
    assert record["delist_date"] == "2026-02-20"
    assert set(record) == set(futures_basic_frame(ALL_CONTRACTS).columns)
    assert not {"basis", "annualized_basis", "main_contract", "roll_yield"} & set(record)


def test_contract_without_lifecycle_facts_is_an_error() -> None:
    """A member contract with incomplete lifecycle facts fails, not disappears."""
    pending = im_contract("IM2703.CFE", list_date="20270315", delist_date=None)

    with pytest.raises(common.CollectionError, match="lifecycle"):
        collect(fake_api([*IM_CONTRACTS, pending]))


def test_contract_without_any_lifecycle_facts_is_an_error() -> None:
    broken = im_contract("IM2706.CFE", list_date=None, delist_date=None)

    with pytest.raises(common.CollectionError, match="lifecycle"):
        collect(fake_api([*IM_CONTRACTS, broken]))


def test_lifecycle_ending_before_it_starts_is_an_error() -> None:
    broken = im_contract("IM2706.CFE", list_date="20270615", delist_date="20270610")

    with pytest.raises(common.CollectionError, match="before"):
        collect(fake_api([*IM_CONTRACTS, broken]))


def test_non_im_or_non_cffex_contracts_are_not_part_of_the_universe() -> None:
    records = collect(fake_api())

    assert {record["fut_code"] for record in records} == {"IM"}
    assert {record["exchange"] for record in records} == {"CFFEX"}


def test_incomplete_non_member_contract_is_not_an_im_error() -> None:
    """A contract outside the Capture scope is not validated."""
    other_product = im_contract(
        "IF2612.CFE",
        fut_code="IF",
        name="沪深300股指期货2612",
        list_date=None,
        delist_date=None,
    )

    records = collect(fake_api([*IM_CONTRACTS, other_product]))

    assert [record["ts_code"] for record in records] == [
        "IM2601.CFE",
        "IM2609.CFE",
        "IM2612.CFE",
    ]


def test_source_without_contract_facts_is_an_error() -> None:
    with pytest.raises(common.CollectionError):
        collect(FakeTushareApi())


def test_non_iso_trade_date_is_an_error_before_the_source_call() -> None:
    api = fake_api()

    with pytest.raises(tushare.TushareDateError):
        im_futures_basic.collect_im_futures_basic(
            "20260917", lambda **kwargs: api.fut_basic(**kwargs)
        )

    assert api.fut_basic_calls == []


def test_main_writes_raw_dataset_file(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)

    exit_code = im_futures_basic.main([TARGET_DATE])

    assert exit_code == 0
    raw_path = (
        test_workdir / "raw" / artifacts.CSI1000_RAW_SUBDIR / TARGET_DATE / "im_futures_basic.json"
    )
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    assert [record["ts_code"] for record in records] == [
        "IM2601.CFE",
        "IM2609.CFE",
        "IM2612.CFE",
    ]
    assert "im_futures_basic.json" in capsys.readouterr().out


def test_main_fails_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(tushare.TOKEN_ENV_VAR, raising=False)

    def unreachable_api(token: str) -> tushare.TushareApi:
        raise AssertionError("no credential must mean no Source client")

    monkeypatch.setattr(tushare, "create_tushare_api", unreachable_api)

    assert im_futures_basic.main([TARGET_DATE]) == 1
