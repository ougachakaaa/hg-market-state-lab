"""Self-contained composed-app HTTP acceptance using public-service fakes only.

poetry run python ui_http/tests/research_http_acceptance.py
--write-examples refreshes the explicitly synthetic, tested guide examples.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from http_support.research_services import ResearchServices
from market_research.descriptive.execution import execute_batch
from ui_http.app import create_app
from ui_http.products.research.requests import PLAN_EXAMPLE


def run_acceptance(*, write_examples: bool = False) -> None:
    services = ResearchServices()
    with (
        patch(
            "market_research.descriptive.cases.trailing_return.preparation.create_calendar_service",
            services.create_calendar,
        ),
        patch(
            "market_research.descriptive.cases.trailing_return.preparation.create_index_service",
            services.create_index,
        ),
        patch("ui_http.products.research.endpoint.execute_batch", wraps=execute_batch) as delegated,
        TestClient(create_app()) as client,
    ):
        schema = client.get("/openapi.json").json()
        body = schema["components"]["schemas"]["PlanBody"]["examples"][0]
        assert body == PLAN_EXAMPLE
        (descriptor,) = client.get("/research/capabilities").json()
        assert descriptor["id"] == body["metric"]
        detail = client.get(f"/research/capabilities/{descriptor['id']}")
        assert detail.json() == descriptor
        preview = client.post("/research/preview", json=body)
        assert preview.status_code == 200, preview.text
        assert preview.json()["planned_count"] == 1
        assert preview.json()["analysis_attempt_count"] == 2
        assert services.calls == [] and delegated.call_count == 0
        response = client.post("/research/execute", json={**body, "acknowledge_acquisition": True})
        assert response.status_code == 200, response.text
        assert delegated.call_count == 1 and services.calls
        result = response.json()
        (job,) = result["job_results"]
        assert result["status"] == "success" and job["status"] == "Success"
        assert [a["status"] for a in job["analysis_outcomes"]] == ["success", "success"]
        assert job["observation_set"]["eligible_count"] == 5
        assert [
            result[name]
            for name in (
                "planned_count",
                "success_count",
                "failed_count",
                "skipped_count",
            )
        ] == [1, 1, 0, 0]
        assert job["observation_set"]["observation_coverage"] == 1.0
        coverage = job["observation_set"]["market_fact_coverage"]
        assert [
            coverage[part]["available_fact_units"]
            for part in (
                "overall",
                "warm_up",
                "sample",
            )
        ] == [7, 2, 5]
        assert [coverage[part]["ratio"] for part in ("overall", "warm_up", "sample")] == [1.0] * 3
        assert job["projection"]["numeric_sample"]["sample_count"] == 5
        assert (
            job["projection"]["source_input_fingerprint"]
            == job["observation_set"]["provenance"]["input_fingerprint"]
        )
        assert [b["count"] for b in job["analysis_outcomes"][1]["statistical_result"]["bins"]] == [
            2,
            3,
        ]
        assert job["analysis_outcomes"][0]["statistical_result"]["points_and_values"] == [
            [0.1, -0.18666666666666662],
            [0.5, 0.0],
            [0.9, 0.12],
        ]
        assert job["projection"]["source_input_fingerprint"] == (
            "b6b4cc205d576c84e6d89dc86a214e2592e14814ff08dcfaf0eba1fa17e446b8"
        )
        fixtures = Path(__file__).parent / "fixtures"
        if not write_examples:
            assert result == json.loads((fixtures / "research_success.json").read_text())
            assert preview.json() == json.loads((fixtures / "research_preview.json").read_text())
        if write_examples:
            fixtures.mkdir(exist_ok=True)
            for name, value in (
                ("research_plan", body),
                ("research_execute", {**body, "acknowledge_acquisition": True}),
                ("research_preview", preview.json()),
                ("research_success", result),
            ):
                (fixtures / f"{name}.json").write_text(
                    json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
        print(
            json.dumps(
                {
                    "gate": "deterministic HTTP only; not live HTTP acceptance",
                    "source_operations": [name for name, _ in services.calls],
                    "execute_batch_calls": delegated.call_count,
                    "status": result["status"],
                    "job_status": job["status"],
                    "eligible_count": job["observation_set"]["eligible_count"],
                    "quantile": job["analysis_outcomes"][0]["statistical_result"],
                    "interval_count": job["analysis_outcomes"][1]["statistical_result"],
                    "input_fingerprint": job["projection"]["source_input_fingerprint"],
                },
                indent=2,
                allow_nan=False,
            )
        )


if __name__ == "__main__":
    run_acceptance(write_examples="--write-examples" in sys.argv)
