"""Application-level invariants of the FastAPI delivery adapter.

Authority: ``market-snapshot/guides/mo-option-chain/http-contract.md`` (the only endpoint and the
documented statuses) over ``web-ui/ARCHITECTURE.md`` (the web UI depends on a
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

from daily_market_snapshot.api import ROUTE_PATH

app_module: ModuleType = importlib.import_module("daily_market_snapshot.api.app")

# The routes FastAPI registers for itself (all ``include_in_schema=False``).
FRAMEWORK_ROUTES = ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")


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
