"""Application-level invariants of the FastAPI delivery adapter.

Authority: ``products/mo_option_chain/http-contract.md`` (the only endpoint and the
documented statuses) over ``ui_web/ARCHITECTURE.md`` (the web UI depends on a
stable, machine-readable contract).

These tests keep the application itself honest, not just the MO Option Chain
payload:

* the framework's own routes are registered exactly once, so no application
  composition step re-runs FastAPI setup and duplicates them;
* only the contract endpoint is published, with only the statuses the adapter can
  actually return.
"""

from __future__ import annotations

import collections
import importlib
from types import ModuleType
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import ui_http
import ui_http.products.mo_option_chain as chain_api
import ui_http.products.mo_option_premium as premium_api
from ui_http.products.mo_option_chain import ROUTE_PATH
from ui_http.products.mo_option_premium import (
    ROUTE_PATH as PREMIUM_ROUTE_PATH,
)

app_module: ModuleType = importlib.import_module(
    "ui_http.products.mo_option_chain.app"
)
premium_app_module: ModuleType = importlib.import_module(
    "ui_http.products.mo_option_premium.app"
)
premium_endpoint_module: ModuleType = importlib.import_module(
    "ui_http.products.mo_option_premium.endpoint"
)
runtime_module: ModuleType = importlib.import_module("ui_http.app")

# The routes FastAPI registers for itself (all ``include_in_schema=False``).
FRAMEWORK_ROUTES = ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")


def test_package_facades_publish_the_runtime_and_product_attributes() -> None:
    assert ui_http.app is runtime_module.app
    assert ui_http.create_app is runtime_module.create_app
    assert chain_api.app is app_module.app
    assert chain_api.create_app is app_module.create_app
    assert chain_api.ROUTE_PATH == ROUTE_PATH
    assert premium_api.app is premium_app_module.app
    assert premium_api.create_app is premium_app_module.create_app
    assert premium_api.ROUTE_PATH == PREMIUM_ROUTE_PATH
    assert premium_api.router is premium_endpoint_module.router


@pytest.fixture
def application() -> FastAPI:
    """The one application instance these invariants are about."""
    return app_module.create_app()


@pytest.fixture
def client(application: FastAPI) -> TestClient:
    return TestClient(application)


def route_paths(application: FastAPI) -> list[str]:
    """Every route path the application registers, included routers unwrapped.

    FastAPI keeps an ``include_router`` result as a nested router object, so the
    paths are collected recursively instead of depending on one framework
    version's internal listing.
    """
    paths: list[str] = []

    def collect(routes: Any) -> None:
        for route in routes:
            path = getattr(route, "path", None)
            if isinstance(path, str) and path:
                paths.append(path)
            nested = getattr(route, "original_router", None) or getattr(route, "router", None)
            if nested is not None:
                collect(nested.routes)

    collect(application.routes)
    return paths


def test_the_contract_endpoint_is_registered_once(application: FastAPI) -> None:
    assert route_paths(application).count(ROUTE_PATH) == 1


@pytest.mark.parametrize("path", FRAMEWORK_ROUTES)
def test_a_framework_route_is_registered_once(application: FastAPI, path: str) -> None:
    """Building the application must not run FastAPI setup a second time."""
    assert route_paths(application).count(path) == 1


def test_no_route_path_is_registered_twice(application: FastAPI) -> None:
    duplicates = [
        path
        for path, count in collections.Counter(route_paths(application)).items()
        if count > 1
    ]

    assert duplicates == []


def test_the_framework_routes_are_registered_exactly_once(application: FastAPI) -> None:
    paths = route_paths(application)

    assert [path for path in FRAMEWORK_ROUTES if paths.count(path) != 1] == []


def test_the_framework_routes_are_not_published(client: TestClient) -> None:
    document = client.get("/openapi.json").json()

    assert list(document["paths"]) == [ROUTE_PATH]


def test_the_application_still_serves_its_framework_routes(client: TestClient) -> None:
    """Removing the duplicate setup must not remove the framework routes."""
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_the_published_contract_is_stable_across_builds(application: FastAPI) -> None:
    """Building the app twice publishes the same contract."""
    first = TestClient(application).get("/openapi.json").json()
    second = TestClient(app_module.create_app()).get("/openapi.json").json()

    assert first == second


def test_neutral_runtime_composes_each_product_route_once() -> None:
    runtime = runtime_module.create_app()

    assert route_paths(runtime).count(ROUTE_PATH) == 1
    assert route_paths(runtime).count(PREMIUM_ROUTE_PATH) == 1
    assert all(route_paths(runtime).count(path) == 1 for path in FRAMEWORK_ROUTES)


@pytest.mark.parametrize(
    ("path", "params", "missing_param"),
    [
        (ROUTE_PATH, {"option_product": "MO"}, "target_trade_date"),
        (PREMIUM_ROUTE_PATH, {"option_product": "MO"}, "as_of"),
    ],
)
def test_neutral_runtime_preserves_each_product_validation_envelope(
    path: str, params: dict[str, str], missing_param: str
) -> None:
    response = TestClient(runtime_module.create_app()).get(path, params=params)

    assert response.status_code == 400
    assert response.json()["error"]["kind"] == "invalid_request"
    assert response.json()["error"]["param"] == missing_param
