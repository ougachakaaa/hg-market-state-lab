"""The real MO read path against a deterministic, in-memory Source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from daily_market_snapshot import artifacts
from daily_market_snapshot.api.app import create_app
from daily_market_snapshot.preparation import mo_option_chain as preparation
from daily_market_snapshot.services import mo_option_chain as service
from daily_market_snapshot.sources import tushare
from support.fake_source import (
    FakeTushareApi,
    futures_basic_frame,
    futures_daily_frame,
    im_contract,
    index_daily_frame,
    mo_option_contract,
    option_basic_frame,
    option_daily_frame,
)

TARGET = "2026-09-17"
QUERY = service.ChainQuery(TARGET, service.OptionProduct.MO, service.PriceType.CLOSE)
C1 = "MO2609-C-7000.CFE"
C2 = "MO2609-C-7001.CFE"
P1 = "MO2609-P-7000.CFE"


def fake_source() -> FakeTushareApi:
    contracts = [
        mo_option_contract(C2, call_put="C"),
        mo_option_contract(P1, call_put="P"),
        mo_option_contract(C1, call_put="C"),
    ]
    contracts[1]["maturity_date"] = "20261023"
    daily = option_daily_frame("20260917", [C1, C2, P1])
    daily.loc[1, "high"] = None
    daily.loc[2, "high"] = 0.0
    return FakeTushareApi(
        index_frames={"000852.SH": index_daily_frame("000852.SH", close=100.0)},
        option_basic=option_basic_frame(contracts),
        option_daily=daily,
        futures_basic=futures_basic_frame(
            [
                im_contract("IM2609.CFE", list_date="20260817", delist_date="20260925"),
                im_contract("IM2610.CFE", list_date="20260817", delist_date="20261023"),
            ]
        ),
        futures_daily={
            "IM2609.CFE": futures_daily_frame("IM2609.CFE", ["20260916", "20260917"], close=7486.6),
            "IM2610.CFE": futures_daily_frame("IM2610.CFE", ["20260917"], close=7520.0),
        },
    )


def successful_chain(
    api: FakeTushareApi,
    price: service.PriceType = service.PriceType.CLOSE,
    raw_root: Path | None = None,
) -> service.OptionChain:
    result = service.read_chain_with_api(
        api, service.ChainQuery(TARGET, service.OptionProduct.MO, price), raw_root
    )
    assert result.error is None, result.error
    assert result.chain is not None
    return result.chain


def raw_directory(test_workdir: Path) -> Path:
    return test_workdir / "raw" / "mo-option-chain" / TARGET


def test_real_provider_call_order_and_goal_scoped_raw(test_workdir: Path) -> None:
    api = fake_source()

    chain = successful_chain(api)

    assert [name for name, _ in api.calls] == [
        "index_daily", "opt_basic", "opt_daily", "fut_basic", "fut_daily", "fut_daily"
    ]
    assert api.index_calls == [{"ts_code": "000852.SH", "trade_date": "20260917"}]
    assert len(api.opt_basic_calls) == 1
    assert chain.underlying.instrument_id == "000852.SH"
    raw_dir = raw_directory(test_workdir)
    assert {path.name for path in raw_dir.iterdir()} == {
        "index_daily.json",
        "mo_option_basic.json",
        "mo_option_daily.json",
        "im_futures_basic.json",
        "im_futures_daily.json",
    }
    index_rows = json.loads((raw_dir / "index_daily.json").read_text(encoding="utf-8"))
    assert len(index_rows) == 1
    assert index_rows[0]["ts_code"] == "000852.SH"
    im_rows = json.loads((raw_dir / "im_futures_daily.json").read_text(encoding="utf-8"))
    assert {row["trade_date"] for row in im_rows} == {TARGET}
    assert {row["ts_code"] for row in im_rows} == {"IM2609.CFE", "IM2610.CFE"}
    assert all(call["trade_date"] == "20260917" for call in api.fut_daily_calls)
    assert all(call["start_date"] == call["end_date"] == "" for call in api.fut_daily_calls)
    assert not (test_workdir / "raw" / "csi1000-5d-analysis").exists()


@pytest.mark.parametrize(
    ("price_type", "option_price", "index_price"),
    [
        (service.PriceType.OPEN, 102.0, 99.0),
        (service.PriceType.HIGH, 103.0, 102.0),
        (service.PriceType.LOW, 99.0, 97.0),
        (service.PriceType.CLOSE, 100.5, 100.0),
    ],
)
def test_price_type_is_unified_and_universe_is_stable(
    price_type: service.PriceType, option_price: float, index_price: float
) -> None:
    chain = successful_chain(fake_source(), price_type)

    assert chain.price_type is price_type
    assert chain.underlying.price == index_price
    assert chain.expiries[0].calls[0].price == option_price
    assert chain.expiries[0].futures.price == 7487.6 + {
        service.PriceType.OPEN: 2.0,
        service.PriceType.HIGH: 3.0,
        service.PriceType.LOW: -3.0,
        service.PriceType.CLOSE: 0.0,
    }[price_type]
    assert [
        point.instrument_id for group in chain.expiries for point in (*group.calls, *group.puts)
    ] == [C1, C2, P1]


def test_group_order_null_and_zero_survive_preparation() -> None:
    chain = successful_chain(fake_source(), service.PriceType.HIGH)

    assert [group.expiry_date for group in chain.expiries] == ["2026-09-25", "2026-10-23"]
    assert [group.futures.instrument_id for group in chain.expiries] == [
        "IM2609.CFE", "IM2610.CFE"
    ]
    assert [point.instrument_id for point in chain.expiries[0].calls] == [C1, C2]
    assert [point.price for point in chain.expiries[0].calls] == [103.0, None]
    assert chain.expiries[1].puts[0].price == 0.0


def test_strike_order_precedes_instrument_id_order() -> None:
    api = fake_source()
    contracts = [
        mo_option_contract(C1, call_put="C", exercise_price=7200.0),
        mo_option_contract(C2, call_put="C", exercise_price=7000.0),
        mo_option_contract(P1, call_put="P"),
    ]
    api.option_basic = option_basic_frame(contracts)

    chain = successful_chain(api)

    assert [point.instrument_id for point in chain.expiries[0].calls] == [C2, C1]


def test_all_missing_selected_option_prices_keep_a_complete_chain() -> None:
    api = fake_source()
    api.option_daily["high"] = None

    chain = successful_chain(api, service.PriceType.HIGH)

    assert [point.price for group in chain.expiries for point in (*group.calls, *group.puts)] == [
        None,
        None,
        None,
    ]


def test_no_underlying_observation_is_date_not_available() -> None:
    api = fake_source()
    api.index_frames.clear()

    result = service.read_chain_with_api(api, QUERY)

    assert isinstance(result.error, service.DateNotAvailableError)
    assert result.chain is None
    assert [name for name, _ in api.calls] == ["index_daily"]


def test_invalid_direct_query_fails_before_source_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_client(_token: str) -> FakeTushareApi:
        raise AssertionError("invalid query must not create a Source client")

    monkeypatch.setattr(tushare, "create_tushare_api", forbidden_client)
    bad_query = service.ChainQuery("2026-9-17", service.OptionProduct.MO, service.PriceType.CLOSE)

    result = service.read_chain(bad_query)

    assert isinstance(result.error, service.InvalidQueryError)


def test_missing_daily_row_is_chain_unavailable() -> None:
    api = fake_source()
    api.option_daily = option_daily_frame("20260917", [C1, P1])

    result = service.read_chain_with_api(api, QUERY)

    assert isinstance(result.error, service.OptionChainUnavailableError)
    assert result.chain is None


def test_source_api_exception_is_chain_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    api = fake_source()

    def failed_daily(**_kwargs: Any) -> None:
        raise Exception("Source API failure")

    monkeypatch.setattr(api, "opt_daily", failed_daily)
    result = service.read_chain_with_api(api, QUERY)

    assert isinstance(result.error, service.OptionChainUnavailableError)
    assert result.chain is None


def test_source_index_exception_is_not_misclassified_as_an_unavailable_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = fake_source()

    def failed_index(**_kwargs: Any) -> None:
        raise Exception("Source API failure")

    monkeypatch.setattr(api, "index_daily", failed_index)

    result = service.read_chain_with_api(api, QUERY)

    assert isinstance(result.error, service.OptionChainUnavailableError)


def test_duplicate_contract_is_chain_unavailable() -> None:
    api = fake_source()
    contract = mo_option_contract(C1, call_put="C")
    api.option_basic = option_basic_frame([contract, contract])
    api.option_daily = option_daily_frame("20260917", [C1])

    result = service.read_chain_with_api(api, QUERY)

    assert isinstance(result.error, service.OptionChainUnavailableError)


@pytest.mark.parametrize(
    ("artifact", "field", "value"),
    [
        ("mo_option_basic", "maturity_date", None),
        ("mo_option_basic", "exercise_price", "bad"),
        ("mo_option_basic", "call_put", "X"),
        ("index_daily", "high", None),
        ("index_daily", "high", "bad"),
    ],
)
def test_preparation_rejects_malformed_required_facts(
    test_workdir: Path, artifact: str, field: str, value: Any
) -> None:
    successful_chain(fake_source(), service.PriceType.HIGH)
    raw_dir = raw_directory(test_workdir)
    rows = artifacts.read_raw_artifact(raw_dir, artifact)
    assert isinstance(rows, list)
    rows[0][field] = value
    artifacts.write_raw_artifact(rows, raw_dir, artifact)

    with pytest.raises(preparation.PreparationError):
        preparation.build_chain(TARGET, "high", raw_dir)


@pytest.mark.parametrize(
    "case",
    [
        "no_match",
        "multiple_matches",
        "outside_lifecycle",
        "missing_daily",
        "duplicate_daily",
        "null_price",
        "malformed_price",
    ],
)
def test_preparation_rejects_incomplete_matched_im_reference(
    test_workdir: Path, case: str
) -> None:
    successful_chain(fake_source())
    raw_dir = raw_directory(test_workdir)
    basic = artifacts.read_raw_artifact(raw_dir, "im_futures_basic")
    daily = artifacts.read_raw_artifact(raw_dir, "im_futures_daily")
    assert isinstance(basic, list) and isinstance(daily, list)
    if case == "no_match":
        basic[0]["delist_date"] = "2026-09-26"
    elif case == "multiple_matches":
        competing = dict(basic[0])
        competing["ts_code"] = "IM2699.CFE"
        competing["symbol"] = "IM2699"
        basic.append(competing)
    elif case == "outside_lifecycle":
        basic[0]["list_date"] = "2026-09-18"
    elif case == "missing_daily":
        daily = [row for row in daily if row["ts_code"] != "IM2609.CFE"]
    elif case == "duplicate_daily":
        daily.append(dict(daily[0]))
    elif case == "null_price":
        daily[0]["close"] = None
    elif case == "malformed_price":
        daily[0]["close"] = "bad"
    artifacts.write_raw_artifact(basic, raw_dir, "im_futures_basic")
    artifacts.write_raw_artifact(daily, raw_dir, "im_futures_daily")

    with pytest.raises(preparation.PreparationError):
        preparation.build_chain(TARGET, "close", raw_dir)


def test_unrelated_active_im_without_daily_does_not_affect_chain() -> None:
    api = fake_source()
    extra = im_contract("IM2611.CFE", list_date="20260817", delist_date="20261120")
    api.futures_basic = futures_basic_frame(
        [*api.futures_basic.to_dict(orient="records"), extra]
    )

    chain = successful_chain(api)

    assert [group.futures.instrument_id for group in chain.expiries] == [
        "IM2609.CFE", "IM2610.CFE"
    ]
    assert {call["ts_code"] for call in api.fut_daily_calls} == {
        "IM2609.CFE", "IM2610.CFE", "IM2611.CFE"
    }


def test_missing_matched_im_daily_is_service_failure() -> None:
    api = fake_source()
    api.futures_daily.pop("IM2609.CFE")

    result = service.read_chain_with_api(api, QUERY)

    assert isinstance(result.error, service.OptionChainUnavailableError)
    assert result.chain is None


def test_zero_matched_futures_price_is_a_valid_numeric_reference() -> None:
    api = fake_source()
    api.futures_daily["IM2609.CFE"].loc[1, "close"] = 0.0

    chain = successful_chain(api)

    assert chain.expiries[0].futures.price == 0.0


def test_default_http_provider_uses_real_path_with_fake_source(
    monkeypatch: pytest.MonkeyPatch, test_workdir: Path
) -> None:
    api = fake_source()
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "fake-token")
    monkeypatch.setattr(tushare, "create_tushare_api", lambda _token: api)
    client = TestClient(create_app())

    response = client.get(
        "/mo-option-chain",
        params={"target_trade_date": TARGET, "option_product": "MO", "price_type": "high"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["price_type"] == "high"
    assert payload["underlying"] == {"instrument_id": "000852.SH", "price": 102.0}
    assert payload["expiries"][0]["futures"] == {
        "instrument_id": "IM2609.CFE", "price": 7490.6
    }
    assert payload["expiries"][0]["calls"] == [
        {"instrument_id": C1, "strike": 7000.0, "price": 103.0},
        {"instrument_id": C2, "strike": 7000.0, "price": None},
    ]
    assert payload["expiries"][1]["puts"] == [{"instrument_id": P1, "strike": 7000.0, "price": 0.0}]
    assert raw_directory(test_workdir).exists()


def test_real_http_provider_maps_missing_matched_futures_to_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = fake_source()
    api.futures_daily.pop("IM2609.CFE")
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "fake-token")
    monkeypatch.setattr(tushare, "create_tushare_api", lambda _token: api)

    response = TestClient(create_app()).get(
        "/mo-option-chain",
        params={"target_trade_date": TARGET, "option_product": "MO"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["kind"] == "option_chain_unavailable"
