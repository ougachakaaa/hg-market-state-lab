"""Contract tests of the MO Option Chain HTTP delivery adapter.

Authority: ``guides/mo-option-chain-http-contract.md`` over
``guides/mo-option-chain-read-contract.md`` (semantic shape) and
``guides/mo-option-chain.md`` (query identity, invariants).

These tests lock the transport contract the web UI may depend on:

* the endpoint, its method and its query parameters (including the resolved
  ``price_type`` default) rather than a request the caller has to guess;
* the success payload as the read contract's semantic response, unchanged:
  ordering preserved, ``null`` price kept, ``0`` price kept, nothing dropped;
* the error envelope, the closed error-kind set and the status mapping;
* the OpenAPI document the front end reads the contract from;
* the fact that the adapter reimplements no market semantics.

Most transport tests run the real application against a fake application
boundary (``support/fake_chain_service.py``); the real-provider path is covered
separately with a Fake Source.
"""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from daily_market_snapshot.api import endpoint
from daily_market_snapshot.api import errors as api_errors
from daily_market_snapshot.api import schemas as api_schemas
from daily_market_snapshot.services import mo_option_chain as service
from support.fake_chain_service import (
    CALL_WITH_NULL_PRICE,
    CALL_WITH_PRICE,
    CALL_WITH_ZERO_PRICE,
    EXPIRY_DATE,
    FUTURES_ID,
    FUTURES_PRICE,
    PUT_WITH_PRICE,
    TARGET_DATE,
    UNDERLYING_ID,
    UNDERLYING_PRICE,
    FakeChainReadProvider,
    error_result,
)

# ``daily_market_snapshot.api`` exports the FastAPI instance as ``app``, so the
# application module is imported by name to keep the module itself available.
app_module: ModuleType = importlib.import_module("daily_market_snapshot.api.app")

# Modules the delivery layer must never import: it reads the chain through the
# Data Service application boundary, not from Raw Artifacts or the Source.
FORBIDDEN_IMPORT_PREFIXES = (
    "daily_market_snapshot.artifacts",
    "daily_market_snapshot.capture",
    "daily_market_snapshot.preparation",
    "daily_market_snapshot.sources",
)

ENDPOINT = "/mo-option-chain"
QUERY = f"{ENDPOINT}?target_trade_date={TARGET_DATE}&option_product=MO"

# Every error kind the contract defines, and its HTTP status (contract 5).
ERROR_STATUS = {
    "invalid_request": 400,
    "unsupported_query": 400,
    "date_not_available": 404,
    "option_chain_unavailable": 503,
    "service_not_wired": 503,
}


@pytest.fixture
def provider() -> FakeChainReadProvider:
    return FakeChainReadProvider()


@pytest.fixture
def client(provider: FakeChainReadProvider) -> TestClient:
    """The real application reading the chain from the fake boundary."""
    application = app_module.create_app()
    application.dependency_overrides[endpoint.get_chain_read_provider] = lambda: provider
    return TestClient(application)


@pytest.fixture
def default_client() -> TestClient:
    """The real application exactly as it starts, with no provider override."""
    return TestClient(app_module.create_app())


def body(response: Any) -> dict[str, Any]:
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def error_body(response: Any) -> dict[str, Any]:
    envelope = body(response)
    assert set(envelope) == {"error"}
    return envelope["error"]


def module_source(module: ModuleType) -> str:
    return Path(str(module.__file__)).read_text(encoding="utf-8")


def imported_modules(module: ModuleType) -> set[str]:
    """Every module name ``module`` imports, relative imports resolved."""
    tree = ast.parse(module_source(module))
    package = str(module.__package__ or "")
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1])
                names.add(f"{base}.{node.module}" if node.module else base)
            elif node.module:
                names.add(node.module)
    return names


def schema_of(document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve one ``$ref`` of an OpenAPI document to its schema."""
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema
    target: Any = document
    for part in ref.lstrip("#/").split("/"):
        target = target[part]
    assert isinstance(target, dict)
    return target


def query_parameters(client: TestClient) -> dict[str, Any]:
    document = client.get("/openapi.json").json()
    return {
        parameter["name"]: parameter
        for parameter in document["paths"][ENDPOINT]["get"]["parameters"]
    }


# ---------------------------------------------------------------------------
# Endpoint and query parameters
# ---------------------------------------------------------------------------


def test_only_the_contract_endpoint_exists(client: TestClient) -> None:
    """``GET /mo-option-chain`` is the only documented route of the adapter."""
    document = client.get("/openapi.json").json()

    assert list(document["paths"]) == [ENDPOINT]
    assert list(document["paths"][ENDPOINT]) == ["get"]


def test_a_valid_query_returns_the_chain(client: TestClient) -> None:
    response = client.get(QUERY)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_the_response_is_the_read_contract_semantic_shape(client: TestClient) -> None:
    """The payload is the read contract's example shape, field for field."""
    assert body(client.get(QUERY)) == {
        "target_trade_date": TARGET_DATE,
        "option_product": "MO",
        "price_type": "close",
        "underlying": {"instrument_id": UNDERLYING_ID, "price": UNDERLYING_PRICE},
        "expiries": [
            {
                "expiry_date": EXPIRY_DATE,
                "futures": {"instrument_id": FUTURES_ID, "price": FUTURES_PRICE},
                "calls": [
                    {"instrument_id": CALL_WITH_PRICE, "strike": 7000.0, "price": 356.4},
                    {"instrument_id": CALL_WITH_NULL_PRICE, "strike": 7200.0, "price": None},
                    {"instrument_id": CALL_WITH_ZERO_PRICE, "strike": 7400.0, "price": 0.0},
                ],
                "puts": [
                    {"instrument_id": PUT_WITH_PRICE, "strike": 7000.0, "price": 41.8},
                ],
            }
        ],
    }


def test_an_omitted_price_type_resolves_to_close(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    """A caller may omit ``price_type``; the resolved value is always ``close``."""
    response = client.get(QUERY)

    assert provider.last_query.price_type is service.PriceType.CLOSE
    assert body(response)["price_type"] == "close"


@pytest.mark.parametrize("price_type", ["open", "high", "low", "close"])
def test_an_explicit_price_type_is_resolved_and_echoed(
    client: TestClient, provider: FakeChainReadProvider, price_type: str
) -> None:
    response = client.get(f"{QUERY}&price_type={price_type}")

    assert response.status_code == 200
    assert provider.last_query.price_type is service.PriceType(price_type)
    assert body(response)["price_type"] == price_type


def test_the_resolved_query_identity_carries_all_three_dimensions(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    """The boundary receives the resolved identity, never a caller omission."""
    client.get(QUERY)

    assert provider.last_query == service.ChainQuery(
        target_trade_date=TARGET_DATE,
        option_product=service.OptionProduct.MO,
        price_type=service.PriceType.CLOSE,
    )


def test_the_transport_layer_makes_no_universe_or_completeness_decision(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    """The adapter forwards the chain as read: it can neither drop nor add a fact."""
    payload = body(client.get(QUERY))

    names = [point["instrument_id"] for group in payload["expiries"] for key in ("calls", "puts")
             for point in group[key]]
    assert names == [CALL_WITH_PRICE, CALL_WITH_NULL_PRICE, CALL_WITH_ZERO_PRICE, PUT_WITH_PRICE]
    assert len(provider.queries) == 1


# ---------------------------------------------------------------------------
# Price semantics over the wire
# ---------------------------------------------------------------------------


def points(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [point for group in payload["expiries"] for key in ("calls", "puts")
            for point in group[key]]


def test_a_null_selected_price_is_serialized_as_null_and_kept(client: TestClient) -> None:
    """A missing selected price keeps the contract and is never dropped or filled."""
    response = client.get(QUERY)
    payload = body(response)
    point = next(p for p in points(payload) if p["instrument_id"] == CALL_WITH_NULL_PRICE)
    # The wire payload itself must carry the key with a JSON null, not omit it.
    wire_calls = json.loads(response.text)["expiries"][0]["calls"]
    wire_point = next(p for p in wire_calls if p["instrument_id"] == CALL_WITH_NULL_PRICE)

    assert point["price"] is None
    assert "price" in wire_point
    assert wire_point["price"] is None
    assert len(wire_calls) == 3


def test_a_numeric_zero_price_stays_zero(client: TestClient) -> None:
    """``0`` is a legal fact; it must not become ``null`` or be dropped."""
    point = next(
        p for p in points(body(client.get(QUERY))) if p["instrument_id"] == CALL_WITH_ZERO_PRICE
    )

    assert point["price"] == 0.0
    assert point["price"] is not None


def test_the_response_is_self_describing(client: TestClient) -> None:
    payload = body(client.get(QUERY))

    assert payload["target_trade_date"] == TARGET_DATE
    assert payload["option_product"] == "MO"
    assert payload["price_type"] == "close"
    assert payload["underlying"]["instrument_id"] == UNDERLYING_ID
    assert payload["underlying"]["price"] is not None
    assert payload["expiries"][0]["expiry_date"] == EXPIRY_DATE


def test_the_option_point_carries_only_the_contract_fields(client: TestClient) -> None:
    """Expiry and option type come from the parent grouping, not from the point."""
    for point in points(body(client.get(QUERY))):
        assert set(point) == {"instrument_id", "strike", "price"}


def test_the_deterministic_order_of_the_read_model_is_preserved(client: TestClient) -> None:
    payload = body(client.get(QUERY))

    assert [group["expiry_date"] for group in payload["expiries"]] == [EXPIRY_DATE]
    assert [point["strike"] for point in payload["expiries"][0]["calls"]] == [
        7000.0,
        7200.0,
        7400.0,
    ]


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


def test_a_missing_required_parameter_is_an_invalid_request(client: TestClient) -> None:
    response = client.get(f"{ENDPOINT}?option_product=MO")

    assert response.status_code == 400
    assert error_body(response)["kind"] == "invalid_request"
    assert error_body(response)["param"] == "target_trade_date"


def test_a_missing_option_product_is_an_invalid_request(client: TestClient) -> None:
    response = client.get(f"{ENDPOINT}?target_trade_date={TARGET_DATE}")

    assert response.status_code == 400
    assert error_body(response)["kind"] == "invalid_request"
    assert error_body(response)["param"] == "option_product"


def test_an_unsupported_option_product_is_not_silently_served(client: TestClient) -> None:
    response = client.get(f"{ENDPOINT}?target_trade_date={TARGET_DATE}&option_product=IO")

    assert response.status_code == 400
    assert error_body(response)["kind"] == "invalid_request"
    assert error_body(response)["param"] == "option_product"


def test_an_unsupported_price_type_is_rejected(client: TestClient) -> None:
    """V1 does not support settle / pre_close / pre_settle / volume."""
    response = client.get(f"{QUERY}&price_type=settle")

    assert response.status_code == 400
    assert error_body(response)["kind"] == "invalid_request"
    assert error_body(response)["param"] == "price_type"


def test_a_canonical_date_reaches_the_boundary_unchanged(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    """A valid ``YYYY-MM-DD`` query reaches the boundary as canonical text."""
    response = client.get(QUERY)

    assert response.status_code == 200
    assert [query.target_trade_date for query in provider.queries] == [TARGET_DATE]


@pytest.mark.parametrize(
    "malformed",
    [
        "2026-9-7",
        "2026-9-17",
        "2026/09/17",
        "20260917",
        "2026-13-40",
        "2026-02-30",
        "2026-09-17T00:00:00",
        "20260917T000000",
        "foo",
        "",
    ],
)
def test_a_malformed_date_is_rejected_before_the_provider(
    client: TestClient, provider: FakeChainReadProvider, malformed: str
) -> None:
    """The query identity requires exactly ``YYYY-MM-DD``; nothing else is proxied.

    A non-padded date, another separator, a compact date, an impossible date and
    a timestamp are all invalid requests, and the provider is never asked for a
    chain under a query the authority does not define.
    """
    response = client.get(
        ENDPOINT, params={"target_trade_date": malformed, "option_product": "MO"}
    )

    assert response.status_code == 400
    assert error_body(response)["kind"] == "invalid_request"
    assert error_body(response)["param"] == "target_trade_date"
    assert provider.queries == []


def test_an_unknown_query_parameter_is_reported_as_invalid(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    """The contract accepts no extra parameter; a rejection must be explicit."""
    response = client.get(f"{QUERY}&underlying=000852.SH")

    assert response.status_code == 400
    assert error_body(response)["kind"] == "invalid_request"
    assert provider.queries == []


# ---------------------------------------------------------------------------
# Error envelope and status mapping
# ---------------------------------------------------------------------------


def test_the_error_kind_set_is_closed_and_matches_the_authority() -> None:
    assert {kind.value for kind in api_errors.ChainErrorKind} == set(ERROR_STATUS)
    assert {
        kind.value: status for kind, status in api_errors.ERROR_STATUS.items()
    } == ERROR_STATUS


def test_every_read_failure_category_maps_to_a_wire_kind() -> None:
    read_errors = (
        service.InvalidQueryError,
        service.UnsupportedQueryError,
        service.DateNotAvailableError,
        service.OptionChainUnavailableError,
        service.ServiceNotWiredError,
    )
    assert set(endpoint.CHAIN_ERROR_KINDS) == set(read_errors)


def test_the_error_envelope_has_exactly_the_contract_fields(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    provider.result = error_result(
        service.DateNotAvailableError(f"no MO option-chain facts for {TARGET_DATE}")
    )

    response = client.get(QUERY)
    error = error_body(response)

    assert response.status_code == 404
    assert set(error) == {"kind", "detail", "param"}
    assert error["kind"] == "date_not_available"
    assert error["param"] == "target_trade_date"
    assert error["detail"]


@pytest.mark.parametrize(
    ("error", "kind", "status"),
    [
        (service.InvalidQueryError("bad date format"), "invalid_request", 400),
        (service.UnsupportedQueryError("unsupported price_type"), "unsupported_query", 400),
        (service.DateNotAvailableError("not a trading date"), "date_not_available", 404),
        (
            service.OptionChainUnavailableError("active contract has no daily row"),
            "option_chain_unavailable",
            503,
        ),
        (service.ServiceNotWiredError("not wired yet"), "service_not_wired", 503),
    ],
)
def test_read_failures_map_to_the_documented_kind_and_status(
    client: TestClient,
    provider: FakeChainReadProvider,
    error: service.ChainReadError,
    kind: str,
    status: int,
) -> None:
    provider.result = error_result(error)

    response = client.get(QUERY)

    assert response.status_code == status
    assert error_body(response)["kind"] == kind


def test_an_error_response_carries_no_market_fact(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    """No silent recovery: a failure never ships a partial chain or a substitute."""
    provider.result = error_result(
        service.OptionChainUnavailableError("active contract has no daily row")
    )

    response = client.get(QUERY)

    assert response.status_code == 503
    assert set(body(response)) == {"error"}
    assert "expiries" not in response.text
    assert UNDERLYING_ID not in response.text


def test_an_unmapped_read_failure_is_not_reported_as_success(
    client: TestClient, provider: FakeChainReadProvider
) -> None:
    class UnknownFailure(service.ChainReadError):
        kind = "unknown_failure"

    provider.result = error_result(UnknownFailure("unmapped read failure"))

    response = client.get(QUERY)

    assert response.status_code == 503
    assert error_body(response)["kind"] == "option_chain_unavailable"


def test_default_application_uses_real_provider(
    default_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without credentials, the real provider fails as unavailable, not unwired."""
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    response = default_client.get(QUERY)

    assert response.status_code == 503
    assert error_body(response)["kind"] == "option_chain_unavailable"


def test_an_unknown_path_is_not_a_chain_response(client: TestClient) -> None:
    assert client.get("/mo-option-chains").status_code == 404
    assert client.get("/").status_code == 404


def test_the_supported_methods_are_the_contract_methods(client: TestClient) -> None:
    assert client.post(QUERY).status_code == 405
    assert client.delete(QUERY).status_code == 405


# ---------------------------------------------------------------------------
# OpenAPI
# ---------------------------------------------------------------------------


def test_openapi_exposes_the_endpoint_and_its_parameters(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    operation = document["paths"][ENDPOINT]["get"]

    assert operation["operationId"] == "readMoOptionChain"
    parameters = query_parameters(client)
    assert set(parameters) == {"target_trade_date", "option_product", "price_type"}
    assert [parameters[name]["required"] for name in ("target_trade_date", "option_product")] == [
        True,
        True,
    ]
    assert parameters["price_type"]["required"] is False
    price_schema = schema_of(document, parameters["price_type"]["schema"])
    assert parameters["price_type"]["schema"]["default"] == "close"
    assert price_schema["enum"] == ["open", "high", "low", "close"]
    assert {parameter["in"] for parameter in operation["parameters"]} == {"query"}


def test_the_declared_parameters_are_exactly_the_accepted_ones(client: TestClient) -> None:
    """A request may carry exactly the documented parameters, no more and no less."""
    assert set(query_parameters(client)) == set(api_errors.CONTRACT_QUERY_PARAMS)


def test_openapi_locks_the_response_price_type_enum(client: TestClient) -> None:
    """The response must not widen ``price_type`` into an arbitrary string."""
    document = client.get("/openapi.json").json()
    schemas = document["components"]["schemas"]
    price_type = schema_of(document, schemas["OptionChainDTO"]["properties"]["price_type"])

    assert price_type["enum"] == ["open", "high", "low", "close"]
    assert schemas["OptionChainDTO"]["properties"]["price_type"]["$ref"].endswith("/PriceType")


def test_openapi_locks_the_option_product_enum(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    schemas = document["components"]["schemas"]
    product = schema_of(document, schemas["OptionChainDTO"]["properties"]["option_product"])
    declared = schema_of(document, query_parameters(client)["option_product"]["schema"])

    assert product["enum"] == ["MO"]
    assert declared["enum"] == ["MO"]


def test_the_published_enums_match_the_application_boundary(client: TestClient) -> None:
    """One authoritative value set per dimension, not two that could drift."""
    document = client.get("/openapi.json").json()
    schemas = document["components"]["schemas"]

    assert schemas["PriceType"]["enum"] == [price.value for price in service.PriceType]
    assert schemas["OptionProduct"]["enum"] == [
        product.value for product in service.OptionProduct
    ]


def test_the_published_date_parameter_is_a_canonical_date(client: TestClient) -> None:
    """The published parameter is a date, and only canonical text is accepted."""
    schema = query_parameters(client)["target_trade_date"]["schema"]

    assert schema["format"] == "date"
    assert schema.get("type", "string") == "string"


def test_openapi_declares_the_success_schema_as_the_read_contract(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    schemas = document["components"]["schemas"]

    assert schemas["OptionChainDTO"]["required"] == [
        "target_trade_date",
        "option_product",
        "price_type",
        "underlying",
        "expiries",
    ]
    assert set(schemas["OptionPointDTO"]["properties"]) == {"instrument_id", "strike", "price"}
    assert schemas["ExpiryGroupDTO"]["required"] == [
        "expiry_date", "futures", "calls", "puts"
    ]
    assert schemas["FuturesRefDTO"]["required"] == ["instrument_id", "price"]
    futures_schema = schemas["ExpiryGroupDTO"]["properties"]["futures"]
    assert {"type": "null"} in futures_schema["anyOf"]
    assert {"$ref": "#/components/schemas/FuturesRefDTO"} in futures_schema["anyOf"]
    # ``price`` must stay nullable: null is a legal selected-price state.
    price_schema = schemas["OptionPointDTO"]["properties"]["price"]
    assert {"type": "null"} in price_schema["anyOf"]
    assert {"type": "number"} in price_schema["anyOf"]


def test_openapi_declares_every_error_kind_and_status(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    operation = document["paths"][ENDPOINT]["get"]
    schemas = document["components"]["schemas"]

    assert set(operation["responses"]) == {"200", "400", "404", "503"}
    assert set(schemas["ChainErrorKind"]["enum"]) == set(ERROR_STATUS)
    assert schemas["ChainErrorResponse"]["required"] == ["error"]
    assert schemas["ChainErrorBody"]["required"] == ["kind", "detail"]


def test_openapi_does_not_publish_a_validation_error_shape(client: TestClient) -> None:
    """A rejected request is the 400 error envelope, not FastAPI's own 422."""
    document = client.get("/openapi.json").json()

    assert "422" not in document["paths"][ENDPOINT]["get"]["responses"]
    assert "HTTPValidationError" not in document["components"]["schemas"]


def test_published_openapi_matches_the_frontend_contract_snapshot(client: TestClient) -> None:
    """A backend wire change fails pytest until the frontend contract is regenerated."""
    snapshot = (
        Path(__file__).resolve().parents[2] / "web-ui/src/api/moOptionChain.openapi.json"
    )

    assert client.get("/openapi.json").json() == json.loads(snapshot.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Layer boundaries
# ---------------------------------------------------------------------------


def test_the_adapter_owns_no_market_semantics() -> None:
    """No product mapping, no Source, no universe: only the transport contract."""
    source = module_source(endpoint) + module_source(api_schemas)

    for forbidden in ("000852", "opt_basic", "opt_daily", "ts_code", "Tushare", "tushare"):
        assert forbidden not in source


def test_the_delivery_layer_does_not_read_raw_artifacts_or_the_source() -> None:
    for module in (app_module, endpoint, api_errors, api_schemas):
        imports = imported_modules(module)
        for name in imports:
            for forbidden in FORBIDDEN_IMPORT_PREFIXES:
                assert not name.startswith(forbidden), f"{module.__name__} imports {name}"


def test_the_delivery_layer_depends_only_on_the_application_boundary() -> None:
    """The adapter reads the chain from the Data Service, not from a data layer."""
    imports = imported_modules(endpoint)

    assert any(name.startswith("daily_market_snapshot.services") for name in imports)
    assert not any(
        name.startswith(FORBIDDEN_IMPORT_PREFIXES) for name in imports
    )


def test_the_option_chain_service_module_imports_no_web_framework() -> None:
    """The application boundary is delivery-agnostic."""
    imports = imported_modules(service)

    assert not any(name.startswith("fastapi") for name in imports)
    assert not any(name.startswith("pydantic") for name in imports)
    assert not any(name.startswith("starlette") for name in imports)
