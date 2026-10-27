"""Sequential policy and bounded accounting; all attempted work delegates to execute_job."""

from dataclasses import dataclass
from typing import Literal

from ..association import AnalysisRequest, ResearchAnalysisEvidence
from ..cases.trailing_return import PreparedInputs
from ..conversion import SampleProjection
from ..observation import JobIdentity, ObservationJobSpec, ObservationSet
from .api import execute_job
from .models import AnalysisOutcome, FailureRecord, JobResult
from .plan import ResearchPlan, preflight_plan

SKIP_REASON = "Not attempted: on_job_failure=stop after the first Failed Job"


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(f"Inconsistent JobResult: {reason}")


def _validate_result(
    result: JobResult,
    fixed: ObservationJobSpec,
    identity: JobIdentity,
    requests: tuple[AnalysisRequest, ...],
    trigger: JobIdentity | None,
) -> None:
    _require(type(result) is JobResult, "expected public JobResult")
    _require(
        result.fixed_job_spec == fixed and result.job_identity == identity, "Job identity/order"
    )
    _require(type(result.analysis_outcomes) is tuple, "immutable analysis outcomes")
    _require(type(result.failures) is tuple, "immutable failures")
    _require(len(result.analysis_outcomes) == len(requests), "analysis count")
    for outcome, request in zip(result.analysis_outcomes, requests, strict=True):
        _require(
            type(outcome) is AnalysisOutcome and outcome.request is request,
            "request identity/order",
        )
    if trigger is not None:
        _require(result.status == "Skipped", "stop must skip every later Job")
        _require(result.triggering_failed_job_identity == trigger, "skip trigger")
        _require(isinstance(result.skip_reason, str) and bool(result.skip_reason), "skip reason")
        _require(
            result.prepared_inputs is result.observation_set is result.projection is None
            and result.failures == (),
            "skipped execution context",
        )
        for outcome in result.analysis_outcomes:
            _require(
                outcome.status == "not_attempted"
                and outcome.not_attempted_reason == result.skip_reason
                and outcome.statistical_result
                is outcome.associated_evidence
                is outcome.failure
                is None,
                "skipped analysis context",
            )
        return
    _require(result.status in ("Success", "Failed"), "attempted status")
    _require(
        result.skip_reason is result.triggering_failed_job_identity is None, "attempted skip fields"
    )
    for failure in result.failures:
        _require(type(failure) is FailureRecord, "failure record type")
        _require(failure.job_identity == identity, "failure identity")
        _require(isinstance(failure.error, Exception) and bool(failure.reason), "original failure")
    if result.prepared_inputs is not None:
        _require(isinstance(result.prepared_inputs, PreparedInputs), "prepared inputs type")
        _require(result.prepared_inputs.job_identity == identity, "prepared inputs identity")
    if result.observation_set is not None:
        _require(isinstance(result.observation_set, ObservationSet), "ObservationSet type")
        _require(
            result.observation_set.job_identity == identity
            and result.observation_set.fixed_job_spec == fixed,
            "ObservationSet identity",
        )
    if result.projection is None:
        _require(result.status == "Failed" and len(result.failures) == 1, "early failure")
        failure = result.failures[0]
        _require(failure.request_id is None, "early failure request")
        contexts = {
            "input_preparation": result.prepared_inputs is None and result.observation_set is None,
            "observation_construction": result.prepared_inputs is not None
            and result.observation_set is None,
            "conversion": result.prepared_inputs is not None and result.observation_set is not None,
        }
        _require(contexts.get(failure.failure_stage, False), "early failure stage/context")
        for outcome in result.analysis_outcomes:
            _require(
                outcome.status == "not_attempted"
                and outcome.not_attempted_reason == failure.reason
                and outcome.statistical_result
                is outcome.associated_evidence
                is outcome.failure
                is None,
                "early not_attempted outcome",
            )
        return
    _require(isinstance(result.projection, SampleProjection), "projection type")
    _require(
        result.prepared_inputs is not None and result.observation_set is not None,
        "attempted context",
    )
    _require(
        result.projection.binding.source_observation_reference is result.observation_set,
        "projection source",
    )
    outcome_failures: list[FailureRecord] = []
    for outcome in result.analysis_outcomes:
        _require(outcome.not_attempted_reason is None, "attempted outcome reason")
        if outcome.status == "success":
            evidence = outcome.associated_evidence
            _require(
                outcome.statistical_result is not None
                and isinstance(evidence, ResearchAnalysisEvidence)
                and evidence.request is outcome.request
                and evidence.statistical_result is outcome.statistical_result
                and evidence.projection is result.projection
                and outcome.failure is None,
                "successful outcome/evidence",
            )
        else:
            analysis_failure = outcome.failure
            _require(
                outcome.status == "failed" and type(analysis_failure) is FailureRecord,
                "failed outcome",
            )
            assert analysis_failure is not None
            _require(
                analysis_failure.request_id == outcome.request_id
                and analysis_failure.job_identity == identity
                and outcome.associated_evidence is None,
                "attributable outcome failure",
            )
            _require(
                (analysis_failure.failure_stage == "analyze" and outcome.statistical_result is None)
                or (
                    analysis_failure.failure_stage == "result_association"
                    and outcome.statistical_result is not None
                ),
                "analysis failure stage/result",
            )
            outcome_failures.append(analysis_failure)
    _require(
        len(outcome_failures) == len(result.failures)
        and all(a is b for a, b in zip(outcome_failures, result.failures, strict=True)),
        "ordered failure records",
    )
    _require((result.status == "Failed") == bool(outcome_failures), "required analysis status")


def _skipped(
    fixed: ObservationJobSpec,
    identity: JobIdentity,
    requests: tuple[AnalysisRequest, ...],
    trigger: JobIdentity,
) -> JobResult:
    return JobResult(
        fixed,
        identity,
        "Skipped",
        tuple(
            AnalysisOutcome(r, "not_attempted", not_attempted_reason=SKIP_REASON) for r in requests
        ),
        None,
        None,
        None,
        (),
        SKIP_REASON,
        trigger,
    )


@dataclass(frozen=True)
class BatchResult:
    plan: ResearchPlan
    job_results: tuple[JobResult, ...]

    def __post_init__(self) -> None:
        jobs = preflight_plan(self.plan)
        _require(type(self.job_results) is tuple, "immutable Job results")
        _require(len(self.job_results) == len(jobs), "planned Job count")
        trigger: JobIdentity | None = None
        for result, (fixed, identity) in zip(self.job_results, jobs, strict=True):
            _validate_result(result, fixed, identity, tuple(self.plan.analysis_requests), trigger)
            if self.plan.on_job_failure == "stop" and result.status == "Failed":
                trigger = identity

    @property
    def planned_count(self) -> int:
        return len(self.job_results)

    @property
    def success_count(self) -> int:
        return sum(r.status == "Success" for r in self.job_results)

    @property
    def failed_count(self) -> int:
        return sum(r.status == "Failed" for r in self.job_results)

    @property
    def skipped_count(self) -> int:
        return sum(r.status == "Skipped" for r in self.job_results)

    @property
    def status(self) -> Literal["success", "partial_success", "failed"]:
        if not self.failed_count:
            return "success"
        return "partial_success" if self.success_count else "failed"


def execute_batch(plan: ResearchPlan) -> BatchResult:
    """Preflight the entire Plan, then execute independent Jobs in declaration order."""
    jobs = preflight_plan(plan)
    requests = tuple(plan.analysis_requests)
    results: list[JobResult] = []
    trigger: JobIdentity | None = None
    for fixed, identity in jobs:
        result = (
            _skipped(fixed, identity, requests, trigger)
            if trigger is not None
            else execute_job(fixed, plan.analysis_requests)
        )
        _validate_result(result, fixed, identity, requests, trigger)
        results.append(result)
        if plan.on_job_failure == "stop" and result.status == "Failed":
            trigger = identity
    return BatchResult(plan, tuple(results))
