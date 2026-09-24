"""Backend, orchestration and HTTP contract tests for MO Premium Plane."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from daily_market_snapshot.products.mo_option_chain.api.app import app as runtime_app
from daily_market_snapshot.products.mo_option_chain.api.app import create_app
from daily_market_snapshot.products.mo_option_premium import framing, preparation, service
from daily_market_snapshot.products.mo_option_premium.api import endpoint
from daily_market_snapshot.products.mo_option_premium.models import (
    CalculationBasis,
    FuturesReference,
    ObservationAnchor,
    OptionMarketBasis,
    OptionObservation,
    OptionProduct,
    OptionType,
    PriceType,
    UnderlyingReference,
)
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

AS_OF = "2026-09-17"
EXPIRY = "2026-09-25"
CALL = "MO2609-C-7000.CFE"
PUT = "MO2609-P-7100.CFE"
QUERY = service.PremiumPlaneQuery(AS_OF, OptionProduct.MO, PriceType.CLOSE)


def premium_source() -> FakeTushareApi:
    call = mo_option_contract(CALL, call_put="C", exercise_price=7000.0)
    put = mo_option_contract(PUT, call_put="P", exercise_price=7100.0)
    daily = option_daily_frame("20260917", [CALL, PUT])
    daily.loc[daily["ts_code"] == PUT, "close"] = None
    return FakeTushareApi(
        index_frames={"000852.SH": index_daily_frame("000852.SH", close=7300.0)},
        option_basic=option_basic_frame([put, call]),
        option_daily=daily,
        futures_basic=futures_basic_frame(
            [im_contract("IM2609.CFE", list_date="20260801", delist_date="20260925")]
        ),
        futures_daily={
            "IM2609.CFE": futures_daily_frame("IM2609.CFE", ["20260917"], close=7290.0)
        },
    )


def market_basis(*premiums: float | None) -> OptionMarketBasis:
    values = premiums or (90.0, None)
    return OptionMarketBasis(
        observation=ObservationAnchor(AS_OF),
        option_product=OptionProduct.MO,
        price_type=PriceType.CLOSE,
        underlying=UnderlyingReference("000852.SH", 7300.0),
        options=tuple(
            OptionObservation(
                instrument_id=f"MO2609-{'C' if index == 0 else 'P'}-{7000 + index * 100}.CFE",
                option_type=OptionType.CALL if index == 0 else OptionType.PUT,
                expiry_date=EXPIRY,
                strike=float(7000 + index * 100),
                premium=premium,
                futures=FuturesReference("IM2609.CFE", 7290.0),
            )
            for index, premium in enumerate(values)
        ),
    )


def successful_plane(api: FakeTushareApi | None = None):
    result = service.read_premium_plane_with_api(api or premium_source(), QUERY)
    assert result.error is None, result.error
    assert result.plane is not None
    return result.plane


def test_point_preparation_uses_inclusive_calendar_days_and_authority_formulas() -> None:
    point = preparation.prepare_points(market_basis(90.0))[0]

    assert point.dte == 9
    assert point.annualized_premium_points == pytest.approx(90.0 * 365 / 9)
    assert point.annualized_seller_premium_yield == pytest.approx((90.0 * 365 / 9) / 7300)
    assert point.calculation_basis == CalculationBasis(
        dte_basis="inclusive_calendar_days",
        annualization_days=365,
        seller_yield_denominator="underlying_spot_notional",
        contract_multiplier=200.0,
    )


def test_zero_and_null_premium_remain_distinct_real_points() -> None:
    zero, missing = preparation.prepare_points(market_basis(0.0, None))

    assert (zero.premium, zero.annualized_premium_points, zero.annualized_seller_premium_yield) == (
        0.0,
        0.0,
        0.0,
    )
    assert (
        missing.premium,
        missing.annualized_premium_points,
        missing.annualized_seller_premium_yield,
    ) == (None, None, None)


def test_expiry_day_has_dte_one_and_post_expiry_is_rejected() -> None:
    option = market_basis(10.0).options[0]
    expiry_day = replace(market_basis(10.0), observation=ObservationAnchor(EXPIRY))
    assert preparation.prepare_points(expiry_day)[0].dte == 1

    expired = replace(option, expiry_date="2026-09-16")
    with pytest.raises(preparation.PointPreparationError, match="post-expiry"):
        preparation.prepare_points(replace(market_basis(10.0), options=(expired,)))


def test_framer_orders_sparse_points_and_rejects_incompatible_context() -> None:
    points = preparation.prepare_points(market_basis(None, 10.0))
    plane = framing.frame_plane(tuple(reversed(points)))
    assert [point.option_type for point in plane.points] == [OptionType.CALL, OptionType.PUT]
    incompatible = replace(points[1], underlying=UnderlyingReference("000852.SH", 1.0))
    with pytest.raises(framing.PlaneFramingError, match="incompatible"):
        framing.frame_plane((points[0], incompatible))


def test_real_service_runs_five_captures_and_writes_only_premium_raw(
    test_workdir: Path,
) -> None:
    api = premium_source()
    plane = successful_plane(api)

    assert [name for name, _ in api.calls] == [
        "index_daily",
        "opt_basic",
        "opt_daily",
        "fut_basic",
        "fut_daily",
    ]
    assert len(plane.points) == 2
    raw_dir = test_workdir / "raw" / "mo-option-premium" / AS_OF
    assert {path.name for path in raw_dir.iterdir()} == {
        "index_daily.json",
        "mo_option_basic.json",
        "mo_option_daily.json",
        "im_futures_basic.json",
        "im_futures_daily.json",
    }
    assert not (test_workdir / "raw" / "mo-option-chain").exists()


def test_explicit_empty_probe_is_persisted_and_classified_as_date_not_available(
    test_workdir: Path,
) -> None:
    api = premium_source()
    api.index_frames.clear()

    result = service.read_premium_plane_with_api(api, QUERY)

    assert isinstance(result.error, service.DateNotAvailableError)
    assert [name for name, _ in api.calls] == ["index_daily"]
    payload = json.loads(
        (test_workdir / "raw/mo-option-premium" / AS_OF / "index_daily.json").read_text()
    )
    assert payload == []


def test_probe_exception_is_not_misclassified_as_date_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = premium_source()

    def fail_probe(**_kwargs: Any) -> None:
        raise Exception("transport failure")

    monkeypatch.setattr(api, "index_daily", fail_probe)
    result = service.read_premium_plane_with_api(api, QUERY)

    assert isinstance(result.error, service.PremiumPlaneUnavailableError)


def test_admitted_invalid_underlying_is_product_unavailable() -> None:
    api = premium_source()
    api.index_frames["000852.SH"].loc[0, "close"] = 0.0

    result = service.read_premium_plane_with_api(api, QUERY)

    assert isinstance(result.error, service.PremiumPlaneUnavailableError)


def test_missing_active_option_daily_row_is_product_unavailable() -> None:
    api = premium_source()
    api.option_daily = option_daily_frame("20260917", [CALL])

    result = service.read_premium_plane_with_api(api, QUERY)

    assert isinstance(result.error, service.PremiumPlaneUnavailableError)


def test_no_matching_futures_is_a_successful_null_reference() -> None:
    api = premium_source()
    api.futures_basic = futures_basic_frame(
        [im_contract("IM2610.CFE", list_date="20260801", delist_date="20261023")]
    )
    api.futures_daily = {}

    plane = successful_plane(api)

    assert {point.futures for point in plane.points} == {None}


def test_matched_futures_missing_daily_row_is_product_unavailable() -> None:
    api = premium_source()
    api.futures_daily = {}

    result = service.read_premium_plane_with_api(api, QUERY)

    assert isinstance(result.error, service.PremiumPlaneUnavailableError)


def test_multiple_structural_futures_matches_are_product_unavailable() -> None:
    api = premium_source()
    api.futures_basic = futures_basic_frame(
        [
            im_contract("IM2609.CFE", list_date="20260801", delist_date="20260925"),
            im_contract("IM02609.CFE", list_date="20260801", delist_date="20260925"),
        ]
    )
    api.futures_daily = {
        code: futures_daily_frame(code, ["20260917"])
        for code in ("IM2609.CFE", "IM02609.CFE")
    }

    result = service.read_premium_plane_with_api(api, QUERY)

    assert isinstance(result.error, service.PremiumPlaneUnavailableError)


@pytest.fixture
def http_client() -> TestClient:
    application = create_app(include_premium=True)
    application.dependency_overrides[endpoint.get_premium_plane_provider] = lambda: (
        lambda query: service.read_premium_plane_with_api(premium_source(), query)
    )
    return TestClient(application)


def error(response: Any) -> dict[str, Any]:
    payload = response.json()
    assert set(payload) == {"error"}
    return payload["error"]


def test_http_request_traverses_the_real_backend_and_projects_the_sparse_plane(
    http_client: TestClient,
) -> None:
    response = http_client.get(
        "/mo-option-premium-plane",
        params={"as_of": AS_OF, "option_product": "MO"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["observation"] == {"kind": "trade_date", "value": AS_OF}
    assert payload["option_product"] == "MO"
    assert payload["price_type"] == "close"
    assert payload["underlying"] == {"instrument_id": "000852.SH", "price": 7300.0}
    assert payload["expiries"] == [
        {
            "expiry_date": EXPIRY,
            "dte": 9,
            "futures": {"instrument_id": "IM2609.CFE", "price": 7290.0},
        }
    ]
    assert [point["instrument_id"] for point in payload["points"]] == [CALL, PUT]
    assert payload["points"][1]["premium"] is None
    assert payload["points"][1]["annualized_premium_points"] is None


@pytest.mark.parametrize(
    ("params", "param"),
    [
        ({"option_product": "MO"}, "as_of"),
        ({"as_of": AS_OF}, "option_product"),
        ({"as_of": AS_OF, "option_product": "IO"}, "option_product"),
        ({"as_of": AS_OF, "option_product": "MO", "price_type": "settle"}, "price_type"),
    ],
)
def test_http_invalid_requests_use_the_contract_envelope(
    http_client: TestClient, params: dict[str, str], param: str
) -> None:
    response = http_client.get("/mo-option-premium-plane", params=params)

    assert response.status_code == 400
    assert error(response)["kind"] == "invalid_request"
    assert error(response)["param"] == param


def test_http_unknown_query_is_invalid_without_parameter_attribution(
    http_client: TestClient,
) -> None:
    response = http_client.get(
        "/mo-option-premium-plane",
        params={"as_of": AS_OF, "option_product": "MO", "side": "call"},
    )

    assert response.status_code == 400
    assert error(response)["kind"] == "invalid_request"
    assert error(response)["param"] is None


def test_http_rejects_a_noncanonical_as_of_before_calling_the_provider(
    http_client: TestClient,
) -> None:
    response = http_client.get(
        "/mo-option-premium-plane",
        params={"as_of": "2026-9-17", "option_product": "MO"},
    )

    assert response.status_code == 400
    assert error(response)["kind"] == "invalid_request"
    assert error(response)["param"] == "as_of"


@pytest.mark.parametrize(
    ("failure", "status", "kind"),
    [
        (service.DateNotAvailableError("none"), 404, "date_not_available"),
        (
            service.PremiumPlaneUnavailableError("incomplete"),
            503,
            "premium_plane_unavailable",
        ),
    ],
)
def test_http_maps_classified_product_failures_without_partial_plane(
    failure: service.PremiumPlaneError, status: int, kind: str
) -> None:
    application = create_app(include_premium=True)
    application.dependency_overrides[endpoint.get_premium_plane_provider] = lambda: (
        lambda _query: service.PremiumPlaneResult(error=failure)
    )
    response = TestClient(application).get(
        "/mo-option-premium-plane", params={"as_of": AS_OF, "option_product": "MO"}
    )

    assert response.status_code == status
    assert error(response)["kind"] == kind
    assert set(response.json()) == {"error"}


def test_runtime_openapi_publishes_both_independent_products_without_422() -> None:
    document = TestClient(runtime_app).get("/openapi.json").json()

    assert set(document["paths"]) == {"/mo-option-chain", "/mo-option-premium-plane"}
    responses = document["paths"]["/mo-option-premium-plane"]["get"]["responses"]
    assert set(responses) == {"200", "400", "404", "503"}
