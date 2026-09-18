import json
from pathlib import Path
from typing import Any

import pytest

import _common
import fetch_mo_option_basic
from fake_source import FakeTushareApi, mo_option_contract, option_basic_frame

TARGET_DATE = "2026-09-17"
ACTIVE_CONTRACTS = [
    mo_option_contract(
        "MO2609-C-7000.CFE", exercise_price=7000.0, call_put="C", list_date="20260622"
    ),
    mo_option_contract(
        "MO2609-C-7200.CFE", exercise_price=7200.0, call_put="C", list_date="20260622"
    ),
    mo_option_contract(
        "MO2609-P-7000.CFE", exercise_price=7000.0, call_put="P", list_date="20260622"
    ),
    mo_option_contract(
        "MO2609-P-7200.CFE", exercise_price=7200.0, call_put="P", list_date="20260622"
    ),
]
OUT_OF_LIFECYCLE_CONTRACTS = [
    # Listed after the target trade date.
    mo_option_contract(
        "MO2610-C-7000.CFE", list_date="20260924", delist_date="20261023", call_put="C"
    ),
    # Delisted before the target trade date.
    mo_option_contract(
        "MO2608-C-7000.CFE", list_date="20260520", delist_date="20260828", call_put="C"
    ),
]
OTHER_PRODUCTS = [
    mo_option_contract("IO2609-C-4000.CFE", opt_code="OPIO2609.CFE", call_put="C"),
    mo_option_contract("510050C2609M03000.SH", opt_code="510050.SH", call_put="C"),
]
ALL_CONTRACTS = [*ACTIVE_CONTRACTS, *OUT_OF_LIFECYCLE_CONTRACTS, *OTHER_PRODUCTS]


def fake_api(contracts: list[dict[str, Any]] | None = None) -> FakeTushareApi:
    return FakeTushareApi(
        option_basic=option_basic_frame(ALL_CONTRACTS if contracts is None else contracts)
    )


def collect(api: FakeTushareApi) -> list[_common.RawRecord]:
    return fetch_mo_option_basic.collect_mo_option_basic(
        TARGET_DATE, lambda **kwargs: api.opt_basic(**kwargs)
    )


def test_requests_cffex_option_contract_facts() -> None:
    api = fake_api()

    collect(api)

    assert api.opt_basic_calls == [{"exchange": "CFFEX", "list_date": ""}]


def test_keeps_only_active_mo_contracts_of_the_target_date() -> None:
    records = collect(fake_api())

    assert [record["ts_code"] for record in records] == [
        "MO2609-C-7000.CFE",
        "MO2609-C-7200.CFE",
        "MO2609-P-7000.CFE",
        "MO2609-P-7200.CFE",
    ]


@pytest.mark.parametrize(
    ("list_date", "delist_date", "included"),
    [
        ("20260917", "20260917", True),
        ("20260622", "20260925", True),
        ("20260622", "20260916", False),
        ("20260918", "20260925", False),
    ],
)
def test_lifecycle_boundary_is_inclusive(
    list_date: str | None, delist_date: str | None, included: bool
) -> None:
    contract = mo_option_contract(
        "MO2609-C-7000.CFE", call_put="C", list_date=list_date, delist_date=delist_date
    )
    api = fake_api([contract])

    if included:
        assert [record["ts_code"] for record in collect(api)] == ["MO2609-C-7000.CFE"]
    else:
        with pytest.raises(_common.CollectionError):
            collect(api)


@pytest.mark.parametrize(
    ("list_date", "delist_date"),
    [
        (None, "20260925"),
        ("20260622", None),
        (None, None),
    ],
)
def test_mo_contract_without_lifecycle_facts_is_an_error(
    list_date: str | None, delist_date: str | None
) -> None:
    """A missing lifecycle bound is a Source gap, not an unbounded lifecycle."""
    contract = mo_option_contract(
        "MO2609-C-7000.CFE", call_put="C", list_date=list_date, delist_date=delist_date
    )

    with pytest.raises(_common.CollectionError, match="lifecycle"):
        collect(fake_api([contract]))


def test_lifecycle_ending_before_it_starts_is_an_error() -> None:
    contract = mo_option_contract(
        "MO2609-C-7000.CFE", call_put="C", list_date="20260901", delist_date="20260801"
    )

    with pytest.raises(_common.CollectionError, match="before"):
        collect(fake_api([contract]))


def test_incomplete_other_product_contract_is_not_a_mo_error() -> None:
    """A non-MO CFFEX product is not a member, so its facts are not validated."""
    incomplete_io = {
        **mo_option_contract("IO2609-C-4000.CFE", opt_code="OPIO2609.CFE", call_put="C"),
        "list_date": None,
        "delist_date": None,
    }

    records = collect(fake_api([*ACTIVE_CONTRACTS, incomplete_io]))

    assert {record["ts_code"] for record in records} == {
        str(contract["ts_code"]) for contract in ACTIVE_CONTRACTS
    }


def test_no_business_filters_are_applied() -> None:
    contracts = [
        mo_option_contract("MO2609-C-5000.CFE", exercise_price=5000.0, call_put="C"),
        mo_option_contract("MO2609-C-7000.CFE", exercise_price=7000.0, call_put="C"),
        mo_option_contract("MO2609-C-9000.CFE", exercise_price=9000.0, call_put="C"),
    ]

    records = collect(fake_api(contracts))

    # Far from the money and far from expiry still belongs to the Dataset.
    assert {record["exercise_price"] for record in records} == {5000.0, 7000.0, 9000.0}


def test_source_field_semantics_are_kept() -> None:
    records = collect(fake_api())
    record = records[0]

    assert record["exercise_price"] == 7000.0
    assert record["maturity_date"] == "20260925"
    assert record["call_put"] == "C"
    assert record["list_date"] == "2026-06-22"
    assert record["delist_date"] == "2026-09-25"
    assert record["exchange"] == "CFFEX"
    assert record["opt_code"] == "OPMO2609.CFE"
    assert set(record) == set(option_basic_frame(ALL_CONTRACTS).columns)
    assert not {"strike", "expiry_date", "option_type"} & set(record)


def test_other_cffex_products_are_not_part_of_the_mo_universe() -> None:
    records = collect(fake_api())

    assert all(str(record["ts_code"]).startswith("MO") for record in records)


def test_source_without_mo_contracts_is_an_error() -> None:
    with pytest.raises(_common.CollectionError):
        collect(FakeTushareApi())


def test_source_without_active_mo_contract_is_an_error() -> None:
    with pytest.raises(_common.CollectionError):
        collect(fake_api(OUT_OF_LIFECYCLE_CONTRACTS))


def test_non_iso_trade_date_is_an_error_before_the_source_call() -> None:
    api = fake_api()

    with pytest.raises(_common.CollectionError):
        fetch_mo_option_basic.collect_mo_option_basic(
            "20260917", lambda **kwargs: api.opt_basic(**kwargs)
        )

    assert api.opt_basic_calls == []


def test_main_writes_raw_dataset_file(
    test_workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(_common.TOKEN_ENV_VAR, "local-token")
    api = fake_api()
    monkeypatch.setattr(_common, "create_tushare_api", lambda token: api)

    exit_code = fetch_mo_option_basic.main([TARGET_DATE])

    assert exit_code == 0
    raw_path = (
        test_workdir / "raw" / _common.CSI1000_RAW_SUBDIR / TARGET_DATE / "mo_option_basic.json"
    )
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    assert [record["ts_code"] for record in records] == [
        "MO2609-C-7000.CFE",
        "MO2609-C-7200.CFE",
        "MO2609-P-7000.CFE",
        "MO2609-P-7200.CFE",
    ]
    assert "mo_option_basic.json" in capsys.readouterr().out


def test_main_fails_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_common.TOKEN_ENV_VAR, raising=False)

    def unreachable_api(token: str) -> _common.TushareApi:
        raise AssertionError("no credential must mean no Source client")

    monkeypatch.setattr(_common, "create_tushare_api", unreachable_api)

    assert fetch_mo_option_basic.main([TARGET_DATE]) == 1
