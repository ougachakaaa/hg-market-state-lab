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

    assert [name for name, _ in api.calls] == ["index_daily", "opt_basic", "opt_daily"]
    assert api.index_calls == [{"ts_code": "000852.SH", "trade_date": "20260917"}]
    assert len(api.opt_basic_calls) == 1
    assert chain.underlying.instrument_id == "000852.SH"
    raw_dir = raw_directory(test_workdir)
    assert {path.name for path in raw_dir.iterdir()} == {
        "index_daily.json",
        "mo_option_basic.json",
        "mo_option_daily.json",
    }
    index_rows = json.loads((raw_dir / "index_daily.json").read_text(encoding="utf-8"))
    assert len(index_rows) == 1
    assert index_rows[0]["ts_code"] == "000852.SH"
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
    assert [
        point.instrument_id for group in chain.expiries for point in (*group.calls, *group.puts)
    ] == [C1, C2, P1]


def test_group_order_null_and_zero_survive_preparation() -> None:
    chain = successful_chain(fake_source(), service.PriceType.HIGH)

    assert [group.expiry_date for group in chain.expiries] == ["2026-09-25", "2026-10-23"]
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
    assert payload["expiries"][0]["calls"] == [
        {"instrument_id": C1, "strike": 7000.0, "price": 103.0},
        {"instrument_id": C2, "strike": 7000.0, "price": None},
    ]
    assert payload["expiries"][1]["puts"] == [{"instrument_id": P1, "strike": 7000.0, "price": 0.0}]
    assert raw_directory(test_workdir).exists()
