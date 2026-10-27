"""Standalone deterministic public API acceptance; run from the repository root.

poetry run python market_research/tests/job_execution_example.py
Uses public-service fakes and narrow operation patches, with no market/cache access.
"""

import json
from unittest.mock import patch

from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.cases.trailing_return import PreparedInputs, prepare_inputs
from market_research.descriptive.execution import JobResult, execute_job
from market_research.descriptive.observation import ObservationJobSpec
from market_statistics import (
    CalculationFailure,
    IntervalCountSpec,
    NumericSample,
    QuantileSpec,
    StatisticalResult,
    StatisticalSpec,
    compute,
)
from observation_fixtures import DAYS, CalendarFake, IndexFake, job


def fake_preparation(fixed: ObservationJobSpec) -> PreparedInputs:
    return prepare_inputs(
        fixed,
        calendar_service=CalendarFake(DAYS),
        index_service=IndexFake(
            DAYS, dict(zip(DAYS, (100.0, 110.0, 121.0, 110.0, 121.0, 130.0), strict=True))
        ),
    )


def fail_quantile(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
    if isinstance(spec, QuantileSpec):
        raise CalculationFailure("quantile", "deterministic injected failure")
    return compute(sample, spec)


def summary(result: JobResult) -> dict[str, object]:
    return {
        "status": result.status,
        "observation_set_retained": result.observation_set is not None,
        "projection_retained": result.projection is not None,
        "analysis_outcomes": [
            {
                "request_id": outcome.request_id,
                "status": outcome.status,
                "raw_result_retained": outcome.statistical_result is not None,
                "evidence_retained": outcome.associated_evidence is not None,
            }
            for outcome in result.analysis_outcomes
        ],
        "failures": [
            {"stage": f.failure_stage, "category": f.failure_category, "request_id": f.request_id}
            for f in result.failures
        ],
    }


def main() -> None:
    fixed_job = job()
    requests = [
        AnalysisRequest("quantiles", QuantileSpec([0, 0.5, 1])),
        AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
    ]
    with patch(
        "market_research.descriptive.execution.api.prepare_inputs", side_effect=fake_preparation
    ):
        success = execute_job(fixed_job, requests)
        with patch("market_research.descriptive.execution.api.compute", side_effect=fail_quantile):
            partial_failure = execute_job(fixed_job, requests)
    assert success.status == "Success" and success.failures == ()
    assert [o.status for o in success.analysis_outcomes] == ["success", "success"]
    for outcome in success.analysis_outcomes:
        assert outcome.associated_evidence is not None
        assert outcome.associated_evidence.projection is success.projection
        assert outcome.associated_evidence.statistical_result is outcome.statistical_result
    assert partial_failure.status == "Failed"
    assert [o.status for o in partial_failure.analysis_outcomes] == ["failed", "success"]
    assert partial_failure.analysis_outcomes[1].associated_evidence is not None
    print(
        json.dumps(
            {"success": summary(success), "partial_failure": summary(partial_failure)}, indent=2
        )
    )


if __name__ == "__main__":
    main()
