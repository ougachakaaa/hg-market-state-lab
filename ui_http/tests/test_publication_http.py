"""Publication delivery through the actual app and public synthetic publisher."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from http_support.auth import authenticated_client
from market_research.publication import PublicationStore, publish, retain_source
from market_research.publication.visualization import validate_view
from ui_http.app import create_app

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "market_research" / "tests"))
from batch_execution_example import run  # noqa: E402


@pytest.fixture
def published(tmp_path: Path):
    batch = run("stop", inject_failure=True)
    source = retain_source(batch, "synthetic", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "synthetic context", store)
    app = create_app()
    app.state.publication_store = store
    return authenticated_client(app), store, pid


def test_end_to_end(published):
    client, store, pid = published
    path = f"/research/publications/{pid}"
    listing = client.get("/research/publications")
    assert listing.status_code == 200, listing.text
    assert listing.json()["data"][0]["publication_id"] == pid
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert str(store.root) not in response.text and "source.json" not in response.text
    manifest = response.json()["data"]
    for item in manifest["analyses"]:
        analysis = client.get(f"{path}/analyses/{item['analysis_id']}")
        assert analysis.status_code == 200, analysis.text
        assert analysis.json()["data"]["outcome"] == item["status"]
        original = store.get_analysis(pid, item["analysis_id"])
        if item["status"] == "success":
            from ui_http.products.research_publication.endpoint import decode

            assert analysis.json()["data"]["result"] == decode(original["result"])
        for view in item["views"]:
            response = client.get(f"{path}/views/{view['view_id']}")
            assert response.status_code == 200, response.text
            result = response.json()["data"]
            assert result == store.get_chart_view(pid, view["view_id"])
            validate_view(result)
    assert client.get(path + "?unknown=1").status_code == 400
    assert client.get("/research/publications?limit=101").status_code == 400
    assert client.get("/research/publications/bad").status_code == 400
    assert client.get(path + "/analyses/" + "0" * 64).status_code == 404
    assert client.get(path + "/views/" + "0" * 64).status_code == 404
    assert "no-store" in listing.headers["cache-control"]


def test_access_and_openapi(published):
    client, store, pid = published
    anonymous = TestClient(client.app, base_url="https://testserver")
    assert anonymous.get(f"/research/publications/{pid}").status_code == 401
    schema = client.app.openapi()
    paths = [p for p in schema["paths"] if p.startswith("/research/publications")]
    assert len(paths) == 4
    parameters = schema["paths"]["/research/publications"]["get"]["parameters"]
    assert {item["name"] for item in parameters} == {"limit", "after"}
    routes = [
        route
        for entry in client.app.routes
        for route in getattr(getattr(entry, "original_router", None), "routes", [])
    ]
    for path in paths:
        assert sum(getattr(route, "path", None) == path for route in routes) == 1
    assert all(schema["paths"][path]["get"]["security"] for path in paths)
    assert all("422" not in schema["paths"][path]["get"]["responses"] for path in paths)
    analysis_schema = schema["components"]["schemas"]["Analysis"]
    assert "coverage" in analysis_schema["required"]
    assert (
        "verification_budget_exceeded"
        in schema["components"]["schemas"]["ErrorBody"]["properties"]["kind"]["enum"]
    )


def test_access_never_invokes_reader(published, monkeypatch):
    from ui_http.auth import create_service

    client, store, pid = published
    paths = [
        "/research/publications",
        f"/research/publications/{pid}",
        f"/research/publications/{pid}/analyses/" + "0" * 64,
        f"/research/publications/{pid}/views/" + "0" * 64,
    ]

    def forbidden(*args, **kwargs):
        raise AssertionError("reader called before authentication")

    for method in (
        "list_publications",
        "get_publication_manifest",
        "get_analysis",
        "get_chart_view",
    ):
        monkeypatch.setattr(store, method, forbidden)
    anonymous = TestClient(client.app, base_url="https://testserver")
    for path in paths:
        assert anonymous.get(path).status_code == 401
        assert (
            anonymous.get(path, headers={"Cookie": "lab_access_token=invalid"}).status_code == 401
        )
    user_id = client.get("/auth/me").json()["id"]
    create_service().disable(user_id)
    for path in paths:
        assert client.get(path).status_code == 401


def test_failures_and_bounds(published, tmp_path, monkeypatch):
    from market_research.publication import (
        InconsistentPublication,
        PublicationCorrupt,
        PublicationUnavailable,
        UnsupportedPublicationVersion,
    )
    from ui_http.products.research_publication import endpoint

    client, store, pid = published
    path = f"/research/publications/{pid}"
    for exc, status, kind in [
        (PublicationCorrupt, 409, "corrupt"),
        (InconsistentPublication, 409, "inconsistent"),
        (UnsupportedPublicationVersion, 409, "unsupported_version"),
        (PublicationUnavailable, 503, "unavailable"),
        (RuntimeError, 500, "internal_error"),
    ]:

        def fail(*args, _exc=exc, **kwargs):
            raise _exc("secret /private/path")

        with monkeypatch.context() as patch:
            patch.setattr(store, "get_publication_manifest", fail)
            response = client.get(path)
            assert response.status_code == status
            assert response.json()["error"]["kind"] == kind
            assert "secret" not in response.text and "/private/path" not in response.text
    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "MAX_BYTES", 1)
        assert client.get(path).status_code == 413
    client.app.state.publication_store = PublicationStore(tmp_path / "empty")
    assert client.get("/research/publications").json() == {"data": [], "next_cursor": None}
    del client.app.state.publication_store
    monkeypatch.delenv("LAB_RESEARCH_PUBLICATION_ROOT", raising=False)
    assert client.get("/research/publications").status_code == 503


def test_corrupt_manifest_and_layer(published):
    import json

    client, store, pid = published
    commit = store.root / "publications" / f"{pid}.json"
    envelope = json.loads(commit.read_text())
    source_manifest = store.get_publication_manifest(pid)
    view = next(v for analysis in source_manifest["analyses"] for v in analysis["views"])
    layer = store.root / "bundles" / envelope["bundle"] / "layers" / f"{view['layer_id']}.json"
    layer.write_text("{}")
    response = client.get(f"/research/publications/{pid}/views/{view['view_id']}")
    assert response.status_code == 409 and response.json()["error"]["kind"] == "corrupt"
    commit.write_text("{}")
    response = client.get(f"/research/publications/{pid}")
    assert response.status_code == 409 and response.json()["error"]["kind"] == "corrupt"


def test_expired_cookie_rejected_before_read(published, monkeypatch):
    import jwt

    from ui_http.auth import _session
    from ui_http.auth._session import AUDIENCE, AuthConfig

    client, store, pid = published
    token = client.cookies["lab_access_token"]
    claims = jwt.decode(
        token,
        AuthConfig.from_environment().key,
        algorithms=["HS256"],
        audience=AUDIENCE,
        options={"verify_iat": False, "verify_exp": False},
    )
    monkeypatch.setattr(_session.time, "time", lambda: claims["exp"])

    def forbidden(*args, **kwargs):
        raise AssertionError("reader called for expired session")

    monkeypatch.setattr(store, "get_publication_manifest", forbidden)
    response = client.get(
        f"/research/publications/{pid}", headers={"Cookie": f"lab_access_token={token}"}
    )
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_cursor_and_strict_queries(published):
    client, store, pid = published
    response = client.get("/research/publications?limit=1")
    assert response.status_code == 200
    cursor = response.json()["next_cursor"]
    assert cursor and pid not in cursor
    assert client.get("/research/publications", params={"after": cursor}).json()["data"] == []
    for query in ("limit=1&limit=2", "after=bad", "limit=0", "other=value"):
        assert client.get(f"/research/publications?{query}").status_code == 400
    assert client.get("/research/publications/00000000000040008000000000000000").status_code == 404


def test_get_does_not_modify_store_or_invoke_execution(published, monkeypatch):
    import market_research.descriptive.execution as execution
    import market_research.publication as publication
    import market_statistics

    client, store, pid = published
    manifest = store.get_publication_manifest(pid)
    sample = next(a for a in manifest["analyses"] if a["views"])
    before = {
        p.relative_to(store.root): p.read_bytes() for p in store.root.rglob("*") if p.is_file()
    }

    def forbidden(*args, **kwargs):
        raise AssertionError("GET invoked a mutation or computation")

    monkeypatch.setattr(publication, "publish", forbidden)
    monkeypatch.setattr(publication, "retain_source", forbidden)
    monkeypatch.setattr(execution, "execute_batch", forbidden)
    monkeypatch.setattr(market_statistics, "compute", forbidden)
    path = f"/research/publications/{pid}"
    for url in (
        "/research/publications",
        path,
        f"{path}/analyses/{sample['analysis_id']}",
        f"{path}/views/{sample['views'][0]['view_id']}",
    ):
        assert client.get(url).status_code == 200
    after = {
        p.relative_to(store.root): p.read_bytes() for p in store.root.rglob("*") if p.is_file()
    }
    assert before == after


def test_coverage_is_job_scoped_and_absence_is_honest(published):
    client, store, pid = published
    manifest = store.get_publication_manifest(pid)
    job = manifest["jobs"][0]
    results = [
        client.get(f"/research/publications/{pid}/analyses/{aid}").json()["data"]
        for aid in job["analyses"]
    ]
    coverage = results[0]["coverage"]
    assert coverage == results[1]["coverage"]
    assert (
        coverage["candidate_count"],
        coverage["eligible_count"],
        coverage["unavailable_count"],
        coverage["excluded_count"],
    ) == (2, 2, 0, 0)
    assert coverage["observation_coverage"] == 1
    assert coverage["market_facts"]["overall"]["coverage_ratio"] == 1
    skipped = next(j for j in manifest["jobs"] if j["status"] == "Skipped")
    response = client.get(f"/research/publications/{pid}/analyses/{skipped['analyses'][0]}")
    assert response.json()["data"]["outcome"] == "not_attempted"
    assert response.json()["data"]["coverage"] is None


def test_verification_slot_and_corrupt_source(published):
    from ui_http.products.research_publication import endpoint

    client, store, pid = published
    manifest = store.get_publication_manifest(pid)
    analysis = next(a for a in manifest["analyses"] if a["views"])
    path = f"/research/publications/{pid}/views/{analysis['views'][0]['view_id']}"
    assert endpoint._verification_slot.acquire(blocking=False)
    try:
        response = client.get(path)
        assert response.status_code == 503
        assert response.json()["error"]["kind"] == "verification_budget_exceeded"
    finally:
        endpoint._verification_slot.release()
    import json

    envelope = json.loads((store.root / "publications" / f"{pid}.json").read_text())
    (store.root / "bundles" / envelope["bundle"] / "source.json").write_text("{}")
    response = client.get(path)
    assert response.status_code == 409
    assert response.json()["error"]["kind"] == "corrupt"


def test_large_verified_source_and_capacity(tmp_path, monkeypatch):
    from dataclasses import replace
    from unittest.mock import patch

    from batch_execution_example import fake_preparation
    from market_research.descriptive.execution import execute_batch
    from ui_http.products.research_publication import endpoint

    template = run("continue", inject_failure=False).plan
    plan = replace(
        template,
        subjects=[f"{i:06d}.SH" for i in range(6)],
        horizons=template.horizons,
        windows=template.windows,
    )
    with patch(
        "market_research.descriptive.execution.api.prepare_inputs", side_effect=fake_preparation
    ):
        batch = execute_batch(plan)
    source = retain_source(batch, "large_synthetic", tmp_path / "source.json")
    assert 2 * 1024 * 1024 < source.size < endpoint.MAX_SOURCE_BYTES
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "synthetic", store)
    app = create_app()
    app.state.publication_store = store
    client = authenticated_client(app)
    manifest = store.get_publication_manifest(pid)
    analysis = manifest["analyses"][0]
    view_id = analysis["views"][0]["view_id"]
    path = f"/research/publications/{pid}/views/{view_id}"
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert len(response.content) < endpoint.MAX_BYTES
    assert response.json()["data"] == store.get_chart_view(pid, view_id)
    monkeypatch.setattr(endpoint, "MAX_SOURCE_BYTES", source.size - 1)
    response = client.get(path)
    assert response.status_code == 503
    assert response.json()["error"]["kind"] == "verification_budget_exceeded"
    assert str(tmp_path) not in response.text and str(source.size) not in response.text


def test_partial_coverage_from_real_job(tmp_path):
    from dataclasses import replace
    from unittest.mock import patch

    from batch_execution_example import run
    from market_research.descriptive.cases.trailing_return import prepare_inputs
    from market_research.descriptive.execution import execute_batch
    from market_research.descriptive.observation import DateWindow
    from observation_fixtures import DAYS, CalendarFake, IndexFake

    template = run("continue", inject_failure=False).plan
    plan = replace(
        template, subjects=["000001.SH"], horizons=[2], windows=[DateWindow(DAYS[2], DAYS[5])]
    )
    closes = {DAYS[0]: 100.0, DAYS[1]: -1.0, DAYS[3]: 90.0, DAYS[4]: 120.0, DAYS[5]: 130.0}

    def prepare(fixed):
        return prepare_inputs(
            fixed, calendar_service=CalendarFake(DAYS), index_service=IndexFake(DAYS, closes)
        )

    with patch("market_research.descriptive.execution.api.prepare_inputs", side_effect=prepare):
        batch = execute_batch(plan)
    obs = batch.job_results[0].observation_set
    assert obs is not None and obs.unavailable_count and obs.excluded_count
    source = retain_source(batch, "partial", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "partial", store)
    app = create_app()
    app.state.publication_store = store
    client = authenticated_client(app)
    aid = store.get_publication_manifest(pid)["analyses"][0]["analysis_id"]
    response = client.get(f"/research/publications/{pid}/analyses/{aid}")
    assert response.status_code == 200, response.text
    coverage = response.json()["data"]["coverage"]
    assert [
        coverage[k]
        for k in ("candidate_count", "eligible_count", "unavailable_count", "excluded_count")
    ] == [obs.candidate_count, obs.eligible_count, obs.unavailable_count, obs.excluded_count]
    assert coverage["observation_coverage"] == obs.observation_coverage
    assert coverage["unavailable_ratio"] == obs.unavailable_ratio
    assert coverage["excluded_ratio"] == obs.excluded_ratio
    for name in ("overall", "warm_up", "sample"):
        actual = getattr(obs.market_fact_coverage, name)
        assert coverage["market_facts"][name] == {
            "expected_fact_count": actual.expected_fact_units,
            "available_fact_count": actual.available_fact_units,
            "coverage_ratio": actual.ratio,
        }


def test_failed_job_without_observation_set(tmp_path):
    from dataclasses import replace
    from unittest.mock import patch

    from market_research.descriptive.cases.trailing_return import InputPreparationFailure
    from market_research.descriptive.execution import execute_batch

    template = run("continue", inject_failure=False).plan
    plan = replace(
        template,
        subjects=template.subjects[:1],
        horizons=template.horizons[:1],
        windows=template.windows[:1],
    )
    with patch(
        "market_research.descriptive.execution.api.prepare_inputs",
        side_effect=InputPreparationFailure("private failure"),
    ):
        batch = execute_batch(plan)
    assert batch.job_results[0].observation_set is None
    source = retain_source(batch, "failed", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "failed", store)
    app = create_app()
    app.state.publication_store = store
    client = authenticated_client(app)
    aid = store.get_publication_manifest(pid)["analyses"][0]["analysis_id"]
    response = client.get(f"/research/publications/{pid}/analyses/{aid}")
    assert response.status_code == 200, response.text
    assert response.json()["data"]["outcome"] == "not_attempted"
    assert response.json()["data"]["coverage"] is None
    assert "private failure" not in response.text


def test_default_verification_budget_rejects_large_valid_publication(tmp_path):
    from dataclasses import replace
    from unittest.mock import patch

    from batch_execution_example import fake_preparation
    from market_research.descriptive.execution import execute_batch
    from ui_http.products.research_publication import endpoint

    template = run("continue", inject_failure=False).plan
    plan = replace(template, subjects=[f"{i:06d}.SH" for i in range(12)])
    with patch(
        "market_research.descriptive.execution.api.prepare_inputs", side_effect=fake_preparation
    ):
        batch = execute_batch(plan)
    source = retain_source(batch, "over_capacity", tmp_path / "source.json")
    assert source.size > endpoint.MAX_SOURCE_BYTES
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "synthetic", store)
    app = create_app()
    app.state.publication_store = store
    client = authenticated_client(app)
    analysis = store.get_publication_manifest(pid)["analyses"][0]
    path = f"/research/publications/{pid}/views/{analysis['views'][0]['view_id']}"
    response = client.get(path)
    assert response.status_code == 503
    assert response.json()["error"]["kind"] == "verification_budget_exceeded"
    assert str(tmp_path) not in response.text and str(source.size) not in response.text


def test_empty_population_preserves_not_applicable_ratios(tmp_path):
    from dataclasses import replace
    from unittest.mock import patch

    from market_research.descriptive.cases.trailing_return import prepare_inputs
    from market_research.descriptive.execution import execute_batch
    from market_research.descriptive.observation import DateWindow
    from observation_fixtures import DAYS, CalendarFake, IndexFake

    template = run("continue", inject_failure=False).plan
    plan = replace(
        template, subjects=["000001.SH"], horizons=[2], windows=[DateWindow(DAYS[2], DAYS[4])]
    )

    def prepare(fixed):
        return prepare_inputs(
            fixed, calendar_service=CalendarFake(()), index_service=IndexFake((), {})
        )

    with patch("market_research.descriptive.execution.api.prepare_inputs", side_effect=prepare):
        batch = execute_batch(plan)
    obs = batch.job_results[0].observation_set
    assert obs is not None and obs.candidate_count == 0
    source = retain_source(batch, "empty", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "empty", store)
    app = create_app()
    app.state.publication_store = store
    client = authenticated_client(app)
    aid = store.get_publication_manifest(pid)["analyses"][0]["analysis_id"]
    response = client.get(f"/research/publications/{pid}/analyses/{aid}")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["outcome"] == "not_attempted"
    coverage = data["coverage"]
    assert coverage["candidate_count"] == 0
    assert coverage["observation_coverage"] is None
    assert coverage["unavailable_ratio"] is None
    assert coverage["excluded_ratio"] is None
    assert all(v["coverage_ratio"] is None for v in coverage["market_facts"].values())
