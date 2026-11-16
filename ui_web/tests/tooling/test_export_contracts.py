"""Auth export is a narrow offline projection, with no runtime configuration."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_auth_export_is_offline_and_complete(monkeypatch, tmp_path):
    for name in ("LAB_AUTH_JWT_SECRET", "LAB_AUTH_MODE", "LAB_AUTH_ORIGIN"):
        monkeypatch.delenv(name, raising=False)
    database = tmp_path / "must-not-exist.sqlite3"
    monkeypatch.setenv("LAB_AUTH_DB_PATH", str(database))
    exporter = runpy.run_path(str(ROOT / "ui_web/scripts/export_contracts.py"))
    document = exporter["create_auth_app"]().openapi()
    assert not database.exists()
    assert set(document["paths"]) == {
        "/auth/register", "/auth/login", "/auth/me", "/auth/logout",
    }
    assert set(document["components"]["schemas"]) == {
        "Accepted", "ActiveIdentity", "AuthErrorBody", "AuthErrorResponse", "Credentials",
    }
    assert document["components"]["securitySchemes"]["CookieSession"] == {
        "type": "apiKey", "in": "cookie", "name": "lab_access_token",
    }
    assert document["paths"]["/auth/me"]["get"]["security"] == [{"CookieSession": []}]
    for path in ("/auth/register", "/auth/login", "/auth/logout"):
        assert document["paths"][path]["post"]["security"] == []
    assert "429" in document["paths"]["/auth/login"]["post"]["responses"]


def test_research_export_has_only_protected_publication_operations():
    exporter = runpy.run_path(str(ROOT / 'ui_web/scripts/export_contracts.py'))
    document = exporter['create_research_app']().openapi()
    assert set(document['paths']) == {
        '/research/publications', '/research/publications/{publication_id}',
        '/research/publications/{publication_id}/analyses/{analysis_id}',
        '/research/publications/{publication_id}/views/{view_id}',
    }
    for path in document['paths'].values():
        assert path['get']['security'] == [{'CookieSession': []}]
    assert document['components']['securitySchemes']['CookieSession']['in'] == 'cookie'
    assert 'Manifest' in document['components']['schemas']
    assert 'ChartView' in document['components']['schemas']


def test_catalog_export_has_only_protected_capability_reads():
    exporter = runpy.run_path(str(ROOT / 'ui_web/scripts/export_contracts.py'))
    document = exporter['create_research_catalog_app']().openapi()
    assert set(document['paths']) == {
        '/research/capabilities', '/research/capabilities/{id}',
    }
    for path in document['paths'].values():
        assert set(path) == {'get'}
        assert path['get']['security'] == [{'CookieSession': []}]
    assert 'CapabilityDescription' in document['components']['schemas']
    assert 'PlanBody' not in document['components']['schemas']


def test_futures_basis_export_is_protected_complete_and_storage_free(monkeypatch):
    from ui_http.products.futures_basis_research import runtime

    def forbidden():
        raise AssertionError("Offline export initialized runtime storage")

    monkeypatch.setattr(runtime._runtime, "get", forbidden)
    exporter = runpy.run_path(str(ROOT / "ui_web/scripts/export_contracts.py"))
    document = exporter["create_futures_basis_app"]().openapi()
    base = "/research/futures-basis/runs"
    assert set(document["paths"]) == {
        base, base + "/{run_id}", base + "/{run_id}/report",
        "/research/futures-basis/preflight",
    }
    for operations in document["paths"].values():
        for operation in operations.values():
            assert operation["security"] == [{"CookieSession": []}]
            assert "422" not in operation["responses"]
    schema = document["components"]["schemas"]["FuturesBasisRunRequest"]
    product = schema["properties"]["product_code"]
    assert product["enum"] == ["IM", "IC", "IF", "IH"]


def test_backtesting_export_is_independent_protected_and_concrete(monkeypatch, tmp_path):
    root = tmp_path / "must-not-exist"
    monkeypatch.setenv("LAB_BACKTESTING_RUN_ROOT", str(root))
    exporter = runpy.run_path(str(ROOT / "ui_web/scripts/export_contracts.py"))
    document = exporter["create_backtesting_app"]().openapi()
    assert not root.exists()
    assert set(document["paths"]) == {
        "/backtesting/futures-roll/preflight", "/backtesting/futures-roll/runs",
        "/backtesting/futures-roll/runs/{run_id}",
        "/backtesting/futures-roll/runs/{run_id}/result",
    }
    for operations in document["paths"].values():
        for operation in operations.values():
            assert operation["security"] == [{"CookieSession": []}]
            assert "422" not in operation["responses"]
    assert "FuturesRollResult" in document["components"]["schemas"]
    assert "FuturesRollView" in document["components"]["schemas"]
    assert all(
        name.startswith(("FuturesRoll", "Auth"))
        for name in document["components"]["schemas"]
    )


def test_calendar_spread_exports_preserve_operations_security_and_local_schema_closure():
    exporter = runpy.run_path(str(ROOT / "ui_web/scripts/export_contracts.py"))
    for builder, path, method, operation_id in [
        (
            "create_calendar_spread_daily_app",
            "/data/futures-calendar-spread",
            "get",
            "query_futures_calendar_spread",
        ),
        (
            "create_calendar_spread_relative_value_app",
            "/research/calendar-spread-relative-value/query",
            "post",
            "query_calendar_spread_relative_value",
        ),
    ]:
        doc = exporter[builder]().openapi()
        expected = {path}
        if builder == "create_calendar_spread_daily_app":
            expected.add("/data/futures-calendar-spread/query")
            assert doc["paths"]["/data/futures-calendar-spread/query"]["post"]["operationId"] == (
                "execute_futures_calendar_spread"
            )
        assert set(doc["paths"]) == expected
        operation = doc["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["security"] == [{"CookieSession": []}]
        assert doc["components"]["securitySchemes"]["CookieSession"]["in"] == "cookie"
        assert {"200", "400", "401", "403", "409", "413", "422", "500", "502", "503"} <= set(
            operation["responses"]
        )
        assert "HTTPValidationError" not in doc["components"]["schemas"]
        needed = set()

        def collect(value, needed=needed, doc=doc):
            if isinstance(value, dict):
                ref = value.get("$ref", "")
                if ref.startswith("#/components/schemas/"):
                    name = ref.rsplit("/", 1)[1]
                    if name not in needed:
                        needed.add(name)
                        collect(doc["components"]["schemas"][name])
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(doc["paths"])
        assert needed == set(doc["components"]["schemas"])


def test_publication_projection_keeps_its_pre_calendar_spread_names():
    exporter = runpy.run_path(str(ROOT / "ui_web/scripts/export_contracts.py"))
    schemas = exporter["create_research_app"]().openapi()["components"]["schemas"]
    assert "ErrorBody" in schemas and "QuantileResult" in schemas
    assert (
        schemas["ErrorResponse"]["properties"]["error"]["$ref"] == "#/components/schemas/ErrorBody"
    )
