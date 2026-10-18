"""HTTP contract tests for the MO Premium Plane adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from data_snapshot.products.mo_option_premium import service
from ui_http import app as runtime_app
from ui_http import create_app
from ui_http.products.mo_option_premium import endpoint
from ui_http.products.mo_option_premium.app import create_app as create_contract_app

AS_OF = "2026-09-17"
EXPIRY = "2026-09-25"
ROUTE = "/mo-option-premium-plane"


def metric(points: float | None, yield_: float | None) -> service.MetricValues:
    return service.MetricValues(points=points, yield_=yield_)


def value_metrics(value: float | None) -> service.ValueMetrics:
    return service.ValueMetrics(
        total=service.TimeNormalizedMetrics(
            unannualized=metric(value, None if value is None else value / 7300.0),
            annualized=metric(None if value is None else value * 365 / 9, None),
        ),
        time_value=service.TimeNormalizedMetrics(
            unannualized=metric(value, None),
            annualized=metric(value, None),
        ),
    )


def premium_plane(*, futures: bool = True) -> service.PremiumPlane:
    premium = 52.4
    reference = service.FuturesReference("IM2609.CFE", 7290.0) if futures else None
    return service.PremiumPlane(
        observation=service.ObservationAnchor(AS_OF),
        option_product=service.OptionProduct.MO,
        price_type=service.PriceType.CLOSE,
        underlying=service.UnderlyingReference("000852.SH", 7300.0),
        calculation_basis=service.CalculationBasis(),
        points=(
            service.PremiumPoint(
                observation=service.ObservationAnchor(AS_OF),
                instrument_id="MO2609-C-7000.CFE",
                option_product=service.OptionProduct.MO,
                option_type=service.OptionType.CALL,
                expiry_date=EXPIRY,
                strike=7000.0,
                price_type=service.PriceType.CLOSE,
                premium=premium,
                underlying=service.UnderlyingReference("000852.SH", 7300.0),
                futures=reference,
                calculation_basis=service.CalculationBasis(),
                dte=9,
                metrics=service.PremiumMetrics(
                    underlying_spot=value_metrics(premium),
                    expiry_futures=value_metrics(premium),
                ),
            ),
        ),
    )


@pytest.fixture
def client() -> TestClient:
    application = create_app()
    application.dependency_overrides[endpoint.get_premium_plane_provider] = lambda: (
        lambda _query: service.PremiumPlaneResult(plane=premium_plane())
    )
    return TestClient(application)


def error(response: Any) -> dict[str, Any]:
    payload = response.json()
    assert set(payload) == {"error"}
    return payload["error"]


def test_success_projects_the_multidimensional_metric_tree(client: TestClient) -> None:
    response = client.get(ROUTE, params={"as_of": AS_OF, "option_product": "MO"})

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
    point = payload["points"][0]
    assert point["premium"] == 52.4
    assert set(point["metrics"]) == {"underlying_spot", "expiry_futures"}
    assert set(point["metrics"]["underlying_spot"]) == {"total", "time_value"}
    assert set(point["metrics"]["underlying_spot"]["total"]) == {
        "unannualized",
        "annualized",
    }
    assert set(point["metrics"]["underlying_spot"]["total"]["unannualized"]) == {
        "points",
        "yield",
    }


def test_projection_preserves_missing_futures_without_fallback() -> None:
    payload = endpoint.project_plane(premium_plane(futures=False)).model_dump(by_alias=True)

    assert payload["expiries"][0]["futures"] is None


@pytest.mark.parametrize(
    ("params", "param"),
    [
        ({"option_product": "MO"}, "as_of"),
        ({"as_of": AS_OF}, "option_product"),
        ({"as_of": AS_OF, "option_product": "IO"}, "option_product"),
        ({"as_of": AS_OF, "option_product": "MO", "price_type": "settle"}, "price_type"),
    ],
)
def test_invalid_requests_use_the_contract_envelope(
    client: TestClient, params: dict[str, str], param: str
) -> None:
    response = client.get(ROUTE, params=params)

    assert response.status_code == 400
    assert error(response)["kind"] == "invalid_request"
    assert error(response)["param"] == param


def test_unknown_query_is_invalid_without_parameter_attribution(client: TestClient) -> None:
    response = client.get(
        ROUTE,
        params={"as_of": AS_OF, "option_product": "MO", "side": "call"},
    )

    assert response.status_code == 400
    assert error(response)["kind"] == "invalid_request"
    assert error(response)["param"] is None


def test_noncanonical_as_of_is_rejected_before_the_provider(client: TestClient) -> None:
    response = client.get(ROUTE, params={"as_of": "2026-9-17", "option_product": "MO"})

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
def test_classified_failures_map_without_partial_plane(
    failure: service.PremiumPlaneError, status: int, kind: str
) -> None:
    application = create_app()
    application.dependency_overrides[endpoint.get_premium_plane_provider] = lambda: (
        lambda _query: service.PremiumPlaneResult(error=failure)
    )
    response = TestClient(application).get(
        ROUTE, params={"as_of": AS_OF, "option_product": "MO"}
    )

    assert response.status_code == status
    assert error(response)["kind"] == kind
    assert set(response.json()) == {"error"}


def test_runtime_openapi_publishes_both_products_without_422() -> None:
    document = TestClient(runtime_app).get("/openapi.json").json()

    assert set(document["paths"]) == {"/mo-option-chain", ROUTE}
    assert set(document["paths"][ROUTE]["get"]["responses"]) == {"200", "400", "404", "503"}


def test_published_openapi_matches_the_frontend_contract_snapshot() -> None:
    snapshot = (
        Path(__file__).resolve().parents[2]
        / "ui_web/src/features/mo_option_premium/api/moOptionPremium.openapi.json"
    )

    assert create_contract_app().openapi() == json.loads(snapshot.read_text(encoding="utf-8"))
