"""Research discovery → pure preview → actual Batch execution through the composed app."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from datetime import date
from pathlib import Path
from threading import Event
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from http_support.auth import authenticated_client
from http_support.research_services import ResearchServices
from market_research.descriptive.execution import BatchResult, ResearchPlan, execute_batch
from market_research.descriptive.observation import ObservationConstructionFailure
from market_statistics import (
    CalculationFailure,
    NumericSample,
    QuantileResult,
    StatisticalSpec,
    compute,
)
from ui_http.app import create_app
from ui_http.products.research import endpoint
from ui_http.products.research.requests import PLAN_EXAMPLE

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def services(monkeypatch: pytest.MonkeyPatch) -> ResearchServices:
    services = ResearchServices()
    monkeypatch.setattr(
        "market_research.descriptive.cases.trailing_return.preparation.create_calendar_service",
        services.create_calendar,
    )
    monkeypatch.setattr(
        "market_research.descriptive.cases.trailing_return.preparation.create_index_service",
        services.create_index,
    )
    return services


@pytest.fixture
def batches(monkeypatch: pytest.MonkeyPatch) -> list[BatchResult]:
    batches: list[BatchResult] = []

    def tracked(plan: ResearchPlan) -> BatchResult:
        result = execute_batch(plan)
        batches.append(result)
        return result

    monkeypatch.setattr(endpoint, "execute_batch", tracked)
    return batches


@pytest.fixture
def client(services: ResearchServices, batches: list[BatchResult]) -> TestClient:
    return authenticated_client(create_app())


def execute_body() -> dict[str, Any]:
    return {**deepcopy(PLAN_EXAMPLE), "acknowledge_acquisition": True}


def assert_error(response: Any, status: int, kind: str) -> None:
    assert response.status_code == status, response.text
    assert set(response.json()) == {"error"}
    error = response.json()["error"]
    assert set(error) == {"kind", "detail", "param"}
    assert error["kind"] == kind
    assert "FAKE_SECRET" not in response.text and "Traceback" not in response.text


def test_agent_schema_driven_acceptance(
    client: TestClient,
    services: ResearchServices,
    batches: list[BatchResult],
) -> None:
    document = client.get("/openapi.json").json()
    discovered = client.get("/research/capabilities")
    assert discovered.status_code == 200
    (descriptor,) = discovered.json()
    id = descriptor["id"]
    assert id == "trailing_cumulative_return_v1"
    assert descriptor["metric_parameters"] == {}
    assert descriptor["subject"]["verified_example"] == "000852.SH"
    assert descriptor["subject"]["example_is_default"] is False
    assert descriptor["live_readiness"] == "not_probed"
    assert client.get(f"/research/capabilities/{id}").json() == descriptor
    schema = document["components"]["schemas"]["PlanBody"]
    body = schema["examples"][0]
    assert set(schema["required"]) == set(body)
    assert body == json.loads((FIXTURES / "research_plan.json").read_text())
    preview = client.post("/research/preview", json=body)
    assert preview.status_code == 200, preview.text
    assert preview.json()["planned_count"] == 1
    assert preview.json()["analysis_attempt_count"] == 2
    assert preview.json()["plan"] == body
    assert services.calls == [] and batches == []
    response = client.post("/research/execute", json={**body, "acknowledge_acquisition": True})
    assert response.status_code == 200, response.text
    actual = response.json()
    assert actual == json.loads((FIXTURES / "research_success.json").read_text())
    assert len(batches) == 1 and services.calls
    assert not any(op == "ensure" for op, _ in services.calls)
    assert actual["status"] == "success"
    assert [
        actual[n] for n in ("planned_count", "success_count", "failed_count", "skipped_count")
    ] == [1, 1, 0, 0]
    (job,) = actual["job_results"]
    original = batches[0].job_results[0]
    assert job["job_identity"] == preview.json()["jobs"][0]["job_identity"]
    assert job["status"] == "Success"
    obs = job["observation_set"]
    assert [
        obs[n] for n in ("candidate_count", "eligible_count", "unavailable_count", "excluded_count")
    ] == [5, 5, 0, 0]
    assert obs["observation_coverage"] == 1.0
    assert obs["candidate_anchors"] == [f"2024-01-{d}" for d in (10, 11, 12, 15, 16)]
    projection = job["projection"]
    assert projection["numeric_sample"]["values"] == pytest.approx([0.2, -0.2, -1 / 6, 0, 0])
    assert projection["ordered_observation_keys"] == [
        o["observation_key"] for o in obs["eligible_observations"]
    ]
    assert original.observation_set is not None
    assert (
        projection["source_input_fingerprint"]
        == obs["provenance"]["input_fingerprint"]
        == original.observation_set.provenance.input_fingerprint
    )
    assert obs["provenance"]["input_profile"] == "trailing_return_inputs_v2"
    quantile, interval = job["analysis_outcomes"]
    assert [o["request"]["request_id"] for o in job["analysis_outcomes"]] == [
        "p10_p50_p90",
        "distribution",
    ]
    raw_quantile = original.analysis_outcomes[0].statistical_result
    assert isinstance(raw_quantile, QuantileResult)
    assert quantile["statistical_result"]["points_and_values"] == [
        list(p) for p in raw_quantile.points_and_values
    ]
    assert [b["count"] for b in interval["statistical_result"]["bins"]] == [2, 3]
    assert interval["statistical_result"]["sample_count"] == 5
    assert all(o["associated"] and o["status"] == "success" for o in (quantile, interval))
    assert len(job["input_attempts"]) == 3
    assert (
        job["prepared_context"]["index_slice"]["final_export"]["coverage"]["requested_units"] == 7
    )
    encoded = json.dumps(actual, allow_nan=False)
    for private in ("sqlite", "Traceback", "FAKE_SECRET", "canonical_input_bytes", "Repository"):
        assert private not in encoded


def test_unknown_capability_is_typed_and_read_only(
    client: TestClient, services: ResearchServices
) -> None:
    assert_error(client.get("/research/capabilities/stock_return"), 404, "capability_not_found")
    assert services.calls == []


INVALID_FIELDS = [
    ("subjects", []),
    ("subjects", ["000852.SH", "bad"]),
    ("subjects", ["000852.SH", "000852.SH"]),
    ("subjects", "000852.SH"),
    ("subjects", [123]),
    ("horizons", [True]),
    ("horizons", [2.0]),
    ("horizons", ["2"]),
    ("horizons", [0]),
    ("horizons", [-1]),
    ("horizons", [2, 2]),
    ("horizons", []),
    ("windows", []),
    ("windows", [{"start_date": "2024-01-16", "end_date": "2024-01-10"}]),
    ("windows", [{"start_date": "20240110", "end_date": "2024-01-16"}]),
    ("windows", [{"start_date": "2024-01-10T00:00:00", "end_date": "2024-01-16"}]),
    ("windows", [{"start_date": 1704844800, "end_date": "2024-01-16"}]),
    ("windows", [{"start_date": "2024-02-30", "end_date": "2024-03-01"}]),
    ("windows", [{"start_date": "9999-01-01", "end_date": "9999-01-02"}]),
    ("windows", [{"start_date": "2024-01-10", "end_date": "2024-01-16"}] * 2),
    ("metric", "other"),
    ("metric_parameters", {"H": 2}),
    ("metric_parameters", []),
    ("on_job_failure", "retry"),
    ("analysis_requests", []),
]


@pytest.mark.parametrize("field,value", INVALID_FIELDS)
@pytest.mark.parametrize("route", ["preview", "execute"])
def test_invalid_plan_rejected_before_any_io(
    field: str,
    value: object,
    route: str,
    client: TestClient,
    services: ResearchServices,
    batches: list[BatchResult],
) -> None:
    body: dict[str, Any] = execute_body() if route == "execute" else deepcopy(PLAN_EXAMPLE)
    body[field] = value
    assert_error(client.post(f"/research/{route}", json=body), 400, "invalid_request")
    assert services.calls == [] and batches == []


@pytest.mark.parametrize(
    "spec",
    [
        {"method": "mean"},
        {"method": "quantile"},
        {"method": "quantile", "points": []},
        {"method": "quantile", "points": [True]},
        {"method": "quantile", "points": ["0.5"]},
        {"method": "quantile", "points": [0.9, 0.1]},
        {"method": "quantile", "points": [0.5, 0.5]},
        {"method": "quantile", "points": [1.1]},
        {"method": "quantile", "points": [0.5], "estimator": "other"},
        {"method": "interval_count", "edges": [0, 1]},
        {"method": "interval_count", "edges": [0, 1], "unit": "percent"},
        {"method": "interval_count", "edges": [0], "unit": "decimal_ratio"},
        {"method": "interval_count", "edges": [1, 0], "unit": "decimal_ratio"},
        {"method": "interval_count", "edges": [0, False], "unit": "decimal_ratio"},
    ],
)
def test_spec_legality_uses_public_preflight(
    spec: object,
    client: TestClient,
    services: ResearchServices,
) -> None:
    body = execute_body()
    body["analysis_requests"] = [{"request_id": "a", "spec": spec}]
    assert_error(client.post("/research/execute", json=body), 400, "invalid_request")
    assert services.calls == []


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_id",
        "empty_id",
        "missing_policy",
        "extra",
        "nested_extra",
        "missing_ack",
        "false_ack",
        "numeric_ack",
    ],
)
def test_exact_fields_and_acknowledgment(
    mutation: str,
    client: TestClient,
    services: ResearchServices,
) -> None:
    body = execute_body()
    if mutation == "duplicate_id":
        body["analysis_requests"][1]["request_id"] = body["analysis_requests"][0]["request_id"]
    elif mutation == "empty_id":
        body["analysis_requests"][0]["request_id"] = ""
    elif mutation == "missing_policy":
        del body["on_job_failure"]
    elif mutation == "extra":
        body["private_secret"] = "FAKE_SECRET"
    elif mutation == "nested_extra":
        body["windows"][0]["extra"] = 1
    elif mutation == "missing_ack":
        del body["acknowledge_acquisition"]
    else:
        body["acknowledge_acquisition"] = False if mutation == "false_ack" else 1
    assert_error(client.post("/research/execute", json=body), 400, "invalid_request")
    assert services.calls == []


@pytest.mark.parametrize(
    "raw", ["{", "null", "[]", '{"horizons":[NaN]}', '{"horizons":[Infinity]}']
)
@pytest.mark.parametrize("route", ["preview", "execute"])
def test_malformed_json_is_research_error(
    raw: str,
    route: str,
    client: TestClient,
    services: ResearchServices,
) -> None:
    assert_error(
        client.post(
            f"/research/{route}", content=raw, headers={"Content-Type": "application/json"}
        ),
        400,
        "invalid_request",
    )
    assert services.calls == []


def test_invalid_utf8_body_is_400_not_an_internal_or_sibling_error(
    client: TestClient,
    services: ResearchServices,
) -> None:
    response = client.post(
        "/research/execute", content=b"\xff", headers={"Content-Type": "application/json"}
    )
    assert_error(response, 400, "invalid_request")
    assert services.calls == []


@pytest.mark.parametrize("coordinate", ["NaN", "Infinity", "-Infinity", "true", '"0.1"'])
def test_wire_coordinates_never_coerce_nonfinite_bool_or_text(
    coordinate: str,
    client: TestClient,
    services: ResearchServices,
) -> None:
    raw = json.dumps(execute_body()).replace("[0.1, 0.5, 0.9]", f"[{coordinate}, 0.5, 0.9]")
    assert_error(
        client.post("/research/execute", content=raw, headers={"Content-Type": "application/json"}),
        400,
        "invalid_request",
    )
    assert services.calls == []


@pytest.mark.parametrize(
    "bound", ["jobs", "analyses", "days", "horizon", "coordinates", "id", "body"]
)
@pytest.mark.parametrize("route", ["preview", "execute"])
def test_transport_caps_reject_without_delegation(
    bound: str,
    route: str,
    client: TestClient,
    services: ResearchServices,
    batches: list[BatchResult],
) -> None:
    body: dict[str, Any] = execute_body() if route == "execute" else deepcopy(PLAN_EXAMPLE)
    if bound == "jobs":
        body["subjects"] = [f"{i:06}.SH" for i in range(9)]
    elif bound == "analyses":
        body["analysis_requests"] = [
            {"request_id": str(i), "spec": {"method": "quantile", "points": [0.5]}}
            for i in range(5)
        ]
    elif bound == "days":
        body["windows"] = [{"start_date": "2024-01-01", "end_date": "2024-04-03"}]
    elif bound == "horizon":
        body["horizons"] = [21]
    elif bound == "coordinates":
        body["analysis_requests"][0]["spec"]["points"] = [i / 128 for i in range(129)]
    elif bound == "id":
        body["analysis_requests"][0]["request_id"] = "x" * 129
    else:
        response = client.post(f"/research/{route}", content=b" " * 65537)
        assert_error(response, 400, "request_too_large")
        assert services.calls == [] and batches == []
        return
    assert_error(client.post(f"/research/{route}", json=body), 400, "request_too_large")
    assert services.calls == [] and batches == []


@pytest.mark.parametrize(
    "policy,expected",
    [
        ("continue", ["Success", "Failed", "Success"]),
        ("stop", ["Success", "Failed", "Skipped"]),
    ],
)
def test_partial_batch_and_stop_keep_all_ordered_records(
    policy: str,
    expected: list[str],
    client: TestClient,
    services: ResearchServices,
    batches: list[BatchResult],
) -> None:
    services.fail_codes = {"000300.SH"}
    body = execute_body()
    body.update(subjects=["000852.SH", "000300.SH", "000001.SH"], on_job_failure=policy)
    response = client.post("/research/execute", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert "Max-Age=3600" in response.headers["set-cookie"]
    assert result["status"] == "partial_success"
    assert [j["status"] for j in result["job_results"]] == expected
    assert len(batches) == 1
    failed = result["job_results"][1]
    assert failed["failures"][0]["failure_stage"] == "input_preparation"
    assert failed["failures"][0]["failure_category"] == "UpstreamFailure"
    assert all(o["status"] == "not_attempted" for o in failed["analysis_outcomes"])
    assert failed["input_attempts"] and failed["prepared_context"] is None
    if policy == "stop":
        skipped = result["job_results"][2]
        assert skipped["triggering_failed_job_identity"] == failed["job_identity"]
        assert skipped["observation_set"] is skipped["projection"] is None
        assert skipped["input_attempts"] == [] and skipped["failures"] == []


@pytest.mark.parametrize(
    "mode", ["compute", "association", "calendar", "incomplete", "conversion", "construction"]
)
def test_failed_batch_is_200_and_retains_obtained_context(
    mode: str,
    client: TestClient,
    services: ResearchServices,
    batches: list[BatchResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_compute(sample: NumericSample, spec: StatisticalSpec) -> object:
        if spec.method == "quantile":
            if mode == "compute":
                raise CalculationFailure("quantile", "FAKE_SECRET C:\\private Traceback")
            return replace(compute(sample, spec), unit="wrong")
        return compute(sample, spec)

    def fail_construction(*args: object) -> None:
        raise ObservationConstructionFailure("FAKE_SECRET private cache")

    if mode in ("compute", "association"):
        monkeypatch.setattr("market_research.descriptive.execution.api.compute", failing_compute)
    elif mode == "calendar":
        services.calendar_error = True
    elif mode == "incomplete":
        services.calendar_incomplete = True
    elif mode == "conversion":
        services.missing = set(date(2024, 1, d) for d in (8, 9, 10, 11, 12, 15, 16))
    else:
        monkeypatch.setattr(
            "market_research.descriptive.execution.api.construct_observations", fail_construction
        )
    body = execute_body()
    body.update(subjects=["000852.SH", "000300.SH"], on_job_failure="stop")
    response = client.post("/research/execute", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert "Max-Age=3600" in response.headers["set-cookie"]
    assert result["status"] == "failed"
    job, skipped = result["job_results"]
    assert [job["status"], skipped["status"]] == ["Failed", "Skipped"]
    assert len(batches) == 1 and result["success_count"] == 0
    first, second = job["analysis_outcomes"]
    if mode in ("compute", "association"):
        assert [first["status"], second["status"]] == ["failed", "success"]
        assert second["associated"]
        assert (first["statistical_result"] is None) == (mode == "compute")
        assert job["projection"] is not None
        if mode == "association":
            assert first["statistical_result"]["unit"] == "wrong"
            assert first["failure"]["failure_stage"] == "result_association"
    elif mode == "conversion":
        assert job["observation_set"]["eligible_count"] == 0
        assert job["observation_set"]["unavailable_count"] == 5
        assert job["observation_set"]["observation_coverage"] == 0.0
        assert job["failures"][0]["failure_category"] == "NoEligibleObservations"
    elif mode == "construction":
        assert job["prepared_context"] is not None and job["observation_set"] is None
    else:
        assert job["prepared_context"] is None and job["input_attempts"]
    for sensitive in ("FAKE_SECRET", "C:\\private", "sqlite3", "Traceback"):
        assert sensitive not in response.text
    json.dumps(result, allow_nan=False)


def test_missing_excluded_coverage_and_exact_ids(
    client: TestClient,
    services: ResearchServices,
) -> None:
    services.missing = {date(2024, 1, 10)}
    services.nonpositive = {date(2024, 1, 11)}
    body = execute_body()
    body["analysis_requests"][0]["request_id"] = " ID unchanged \u4e2d "
    result = client.post("/research/execute", json=body).json()
    assert result["status"] == "success"
    (job,) = result["job_results"]
    obs = job["observation_set"]
    assert [
        obs[n] for n in ("candidate_count", "eligible_count", "unavailable_count", "excluded_count")
    ] == [5, 1, 2, 2]
    assert obs["observation_coverage"] == 0.2
    assert obs["market_fact_coverage"]["overall"]["ratio"] == 6 / 7
    assert obs["market_fact_coverage"]["overall"]["absent_keys"] == [["000852.SH", "2024-01-10"]]
    assert obs["unavailable_observations"][0]["missing_dependencies"][0]["diagnostic_reasons"]
    assert job["analysis_outcomes"][0]["request"]["request_id"] == " ID unchanged \u4e2d "
    ensure = job["input_attempts"][-1]["ensure_result"]
    assert ensure["failed_units"] == 1
    assert ensure["failures"][0]["identity"] == ["000852.SH", "2024-01-10"]
    assert "FAKE_SECRET" not in json.dumps(result)


def test_zero_candidates_preserve_null_ratios(client: TestClient) -> None:
    body = execute_body()
    body["windows"] = [{"start_date": "2024-01-13", "end_date": "2024-01-14"}]
    response = client.post("/research/execute", json=body)
    assert response.status_code == 200, response.text
    obs = response.json()["job_results"][0]["observation_set"]
    assert obs["candidate_count"] == 0 and obs["observation_coverage"] is None
    assert obs["market_fact_coverage"]["overall"]["ratio"] is None


@pytest.mark.parametrize(
    "value,tag",
    [
        (float("nan"), "nan"),
        (float("inf"), "positive_infinity"),
        (float("-inf"), "negative_infinity"),
    ],
)
def test_rejected_raw_nonfinite_results_remain_inspectable_as_valid_json(
    value: float,
    tag: str,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def malformed_result(sample: NumericSample, spec: StatisticalSpec) -> object:
        result = compute(sample, spec)
        if isinstance(result, QuantileResult):
            return replace(result, points_and_values=((0.1, value), (0.5, 0.0), (0.9, 0.12)))
        return result

    monkeypatch.setattr("market_research.descriptive.execution.api.compute", malformed_result)
    response = client.post("/research/execute", json=execute_body())
    assert response.status_code == 200, response.text
    result = response.json()
    assert "Max-Age=3600" in response.headers["set-cookie"]
    assert result["status"] == "failed"
    first, second = result["job_results"][0]["analysis_outcomes"]
    assert first["status"] == "failed" and not first["associated"]
    assert first["failure"]["failure_stage"] == "result_association"
    assert first["statistical_result"]["points_and_values"][0][1] == {
        "kind": "non_finite",
        "value": tag,
    }
    assert second["status"] == "success"
    json.dumps(result, allow_nan=False)


def test_malformed_obtained_public_evidence_is_tagged_not_dumped(
    client: TestClient,
    services: ResearchServices,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "export", lambda request: {"secret": "FAKE_SECRET"})
    response = client.post("/research/execute", json=execute_body())
    assert response.status_code == 200, response.text
    (job,) = response.json()["job_results"]
    assert job["status"] == "Failed"
    assert job["failures"][0]["failure_category"] == "InvalidPublicInput"
    assert job["input_attempts"][0]["preliminary_export"] == {"state": "invalid_public_shape"}
    assert "FAKE_SECRET" not in response.text


def test_eighth_job_invalidates_entire_http_plan_before_io(
    client: TestClient,
    services: ResearchServices,
    batches: list[BatchResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_research.descriptive.cases.trailing_return import validate_job
    from market_research.descriptive.observation import InvalidObservationRequest

    calls = 0

    def reject_eighth(fixed: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 8:
            raise InvalidObservationRequest("late fixed Job rejected by public case validation")
        return validate_job(fixed)

    monkeypatch.setattr("market_research.descriptive.execution.api.validate_job", reject_eighth)
    body = execute_body()
    body["subjects"] = ["000852.SH", "000300.SH"]
    body["horizons"] = [2, 5]
    body["windows"].append({"start_date": "2024-01-11", "end_date": "2024-01-16"})
    assert_error(client.post("/research/execute", json=body), 400, "invalid_request")
    assert calls == 8 and services.calls == [] and batches == []


def test_published_http_limits_accept_the_boundary_without_io(
    client: TestClient,
    services: ResearchServices,
) -> None:
    body: dict[str, Any] = deepcopy(PLAN_EXAMPLE)
    body.update(
        subjects=["000852.SH", "000300.SH"],
        horizons=[19, 20],
        windows=[
            {"start_date": "2024-01-01", "end_date": "2024-04-02"},
            {"start_date": "2024-01-02", "end_date": "2024-04-03"},
        ],
        analysis_requests=[
            {
                "request_id": str(i) + "x" * 127,
                "spec": {"method": "quantile", "points": [p / 127 for p in range(128)]},
            }
            for i in range(4)
        ],
    )
    response = client.post("/research/preview", json=body)
    assert response.status_code == 200, response.text
    assert response.json()["planned_count"] == 8
    assert response.json()["analysis_attempt_count"] == 32
    assert services.calls == []


def test_guard_is_process_wide_and_discovery_responsive(
    client: TestClient,
    batches: list[BatchResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered, release = Event(), Event()
    original = endpoint.execute_batch
    calls = 0

    def blocked(plan: ResearchPlan) -> BatchResult:
        nonlocal calls
        calls += 1
        entered.set()
        assert release.wait(10)
        return original(plan)

    monkeypatch.setattr(endpoint, "execute_batch", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(client.post, "/research/execute", json=execute_body())
        try:
            assert entered.wait(10)
            second_client = authenticated_client(create_app())
            assert_error(
                second_client.post("/research/execute", json=execute_body()), 409, "execution_busy"
            )
            assert second_client.get("/research/capabilities").status_code == 200
            assert second_client.post("/research/preview", json=PLAN_EXAMPLE).status_code == 200
            assert calls == 1
        finally:
            release.set()
        assert first.result(timeout=10).status_code == 200
    assert len(batches) == 1
    assert client.post("/research/execute", json=execute_body()).status_code == 200


def test_internal_error_is_safe_and_releases_guard(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = endpoint.execute_batch

    def broken(plan: ResearchPlan) -> BatchResult:
        raise RuntimeError("FAKE_SECRET C:\\private\\cache.sqlite3 Traceback")

    monkeypatch.setattr(endpoint, "execute_batch", broken)
    assert_error(client.post("/research/execute", json=execute_body()), 500, "internal_error")
    monkeypatch.setattr(endpoint, "execute_batch", original)
    assert client.post("/research/execute", json=execute_body()).status_code == 200


def test_synchronous_execution_does_not_block_the_same_asgi_event_loop(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered, release = Event(), Event()
    original = endpoint.execute_batch

    def blocked(plan: ResearchPlan) -> BatchResult:
        entered.set()
        assert release.wait(10)
        return original(plan)

    monkeypatch.setattr(endpoint, "execute_batch", blocked)

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(
            transport=transport,
            base_url="https://testserver",
            cookies=client.cookies,
            headers={"Origin": "https://testserver"},
        ) as session:
            first = asyncio.create_task(session.post("/research/execute", json=execute_body()))
            try:
                assert await asyncio.to_thread(entered.wait, 10)
                discovered = await asyncio.wait_for(session.get("/research/capabilities"), 2)
                assert discovered.status_code == 200
                busy = await asyncio.wait_for(
                    session.post("/research/execute", json=execute_body()), 2
                )
                assert_error(busy, 409, "execution_busy")
            finally:
                release.set()
            assert (await asyncio.wait_for(first, 10)).status_code == 200

    asyncio.run(exercise())


def test_openapi_exposes_concrete_unique_operations_and_real_statuses(client: TestClient) -> None:
    doc = client.get("/openapi.json").json()
    expected = {
        "/research/capabilities": ("get", "list_research_capabilities", {"200", "500"}),
        "/research/capabilities/{id}": ("get", "get_research_capability", {"200", "404", "500"}),
        "/research/preview": ("post", "preview_research_plan", {"200", "400", "500"}),
        "/research/execute": ("post", "execute_research_plan", {"200", "400", "409", "500"}),
    }
    ids = [op["operationId"] for path in doc["paths"].values() for op in path.values()]
    assert len(ids) == len(set(ids))
    for path, (method, id, statuses) in expected.items():
        operation = doc["paths"][path][method]
        assert operation["operationId"] == id
        assert set(operation["responses"]) == statuses | {"401", "403"}
    schemas = doc["components"]["schemas"]
    assert schemas["PlanBody"]["additionalProperties"] is False
    assert (
        schemas["AnalysisBody"]["properties"]["spec"]["discriminator"]["propertyName"] == "method"
    )
    assert (
        schemas["AnalysisOutcomeBody"]["properties"]["statistical_result"]["anyOf"][0][
            "discriminator"
        ]["propertyName"]
        == "method"
    )
    assert schemas["ExecuteBody"]["properties"]["acknowledge_acquisition"]["const"] is True
    assert schemas["PlanBody"]["properties"]["on_job_failure"]["enum"] == ["continue", "stop"]
    assert schemas["IntervalCountBody"]["properties"]["unit"]["const"] == "decimal_ratio"
