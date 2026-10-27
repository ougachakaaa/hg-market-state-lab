"""Standalone deterministic public Batch acceptance; no network or default market caches.

poetry run python market_research/tests/batch_execution_example.py
"""

import json
from dataclasses import replace
from datetime import date
from typing import Literal, cast
from unittest.mock import patch

from data_lake.datasets.tushare_index_daily import IndexDailyScope
from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.cases.trailing_return import PreparedInputs, prepare_inputs
from market_research.descriptive.execution import (
    BatchResult,
    JobResult,
    ResearchPlan,
    execute_batch,
    execute_job,
)
from market_research.descriptive.observation import DateWindow, ObservationJobSpec
from market_statistics import (
    CalculationFailure,
    IntervalCountSpec,
    NumericSample,
    QuantileSpec,
    StatisticalResult,
    StatisticalSpec,
    compute,
)
from observation_fixtures import CalendarFake, IndexFake

SESSIONS = tuple(date(2024, 1, day) for day in range(1, 11))


def fake_preparation(fixed: ObservationJobSpec) -> PreparedInputs:
    index = IndexFake(SESSIONS, {day: 100.0 + i * 3 for i, day in enumerate(SESSIONS)})
    index.transform = lambda view: replace(
        view,
        records=tuple(
            replace(
                row,
                index_code=cast(IndexDailyScope, view.scope).index_codes[0],
                symbol=cast(IndexDailyScope, view.scope).index_codes[0].split(".")[0],
            )
            for row in view.records
        ),
    )
    return prepare_inputs(fixed, calendar_service=CalendarFake(SESSIONS), index_service=index)


def run(policy: str, *, inject_failure: bool) -> BatchResult:
    plan = ResearchPlan(
        metric="trailing_cumulative_return_v1",
        metric_parameters={},
        subjects=["000001.SH", "000300.SH"],
        horizons=[2, 5],
        windows=[DateWindow(SESSIONS[7], SESSIONS[8]), DateWindow(SESSIONS[8], SESSIONS[9])],
        analysis_requests=[
            AnalysisRequest("quantiles", QuantileSpec([0.1, 0.5, 0.9])),
            AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
        ],
        on_job_failure=cast(Literal["continue", "stop"], policy),
    )
    originals: list[JobResult] = []
    computations = 0

    def compute_with_failure(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
        nonlocal computations
        computations += 1
        if inject_failure and computations == 3:
            raise CalculationFailure("quantile", "deterministic second Job failure")
        return compute(sample, spec)

    def tracked(fixed: ObservationJobSpec, requests: object) -> JobResult:
        assert requests is plan.analysis_requests
        result = execute_job(fixed, plan.analysis_requests)
        originals.append(result)
        return result

    with (
        patch(
            "market_research.descriptive.execution.api.prepare_inputs", side_effect=fake_preparation
        ),
        patch(
            "market_research.descriptive.execution.api.compute", side_effect=compute_with_failure
        ),
        patch("market_research.descriptive.execution.batch.execute_job", side_effect=tracked),
    ):
        batch = execute_batch(plan)
    attempted = [r for r in batch.job_results if r.status != "Skipped"]
    assert len(attempted) == len(originals)
    assert all(a is b for a, b in zip(attempted, originals, strict=True))
    assert computations == len(attempted) * 2
    for result in attempted:
        assert result.prepared_inputs is not None and result.observation_set is not None
        for outcome in result.analysis_outcomes:
            if outcome.status == "success":
                evidence = outcome.associated_evidence
                assert evidence is not None and evidence.request is outcome.request
                assert evidence.statistical_result is outcome.statistical_result
                assert evidence.projection is result.projection
                assert evidence.source_observation_reference is result.observation_set
    assert batch.planned_count == 8
    assert batch.planned_count == batch.success_count + batch.failed_count + batch.skipped_count
    if inject_failure:
        assert [o.status for o in batch.job_results[1].analysis_outcomes] == ["failed", "success"]
        assert batch.failed_count == 1 and batch.status == "partial_success"
        assert (batch.success_count, batch.skipped_count) == (
            (7, 0) if policy == "continue" else (1, 6)
        )
        for skipped in batch.job_results[2:] if policy == "stop" else ():
            assert skipped.status == "Skipped" and skipped.input_attempts == ()
            assert skipped.triggering_failed_job_identity == batch.job_results[1].job_identity
            assert all(o.status == "not_attempted" for o in skipped.analysis_outcomes)
    else:
        assert batch.status == "success" and batch.success_count == 8
    return batch


def summary(batch: BatchResult) -> dict[str, object]:
    return {
        "policy": batch.plan.on_job_failure,
        "status": batch.status,
        "planned": batch.planned_count,
        "success": batch.success_count,
        "failed": batch.failed_count,
        "skipped": batch.skipped_count,
        "analyses": sum(len(r.analysis_outcomes) for r in batch.job_results),
        "job_statuses": [r.status for r in batch.job_results],
    }


def main() -> None:
    success = run("continue", inject_failure=False)
    print(
        json.dumps(
            {
                "expansion": [
                    [
                        r.fixed_job_spec.subject,
                        r.fixed_job_spec.horizon,
                        str(r.fixed_job_spec.historical_sample_window.start_date),
                        str(r.fixed_job_spec.historical_sample_window.end_date),
                    ]
                    for r in success.job_results
                ],
                "success": summary(success),
                "continue": summary(run("continue", inject_failure=True)),
                "stop": summary(run("stop", inject_failure=True)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
