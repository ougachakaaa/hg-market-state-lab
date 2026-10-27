"""Sequential orchestration through public component boundaries only."""

from collections.abc import Mapping, Sequence, Set

from market_statistics import (
    CalculationFailure,
    IntervalCountSpec,
    InvalidSample,
    InvalidStatisticalSpec,
    compute,
    validate_spec,
)

from ..association import AnalysisRequest, ResultAssociationFailure, associate
from ..cases.trailing_return import (
    InputPreparationFailure,
    PreparedInputs,
    TrailingReturnProvenance,
    construct_observations,
    prepare_inputs,
    validate_job,
)
from ..conversion import (
    InvalidObservationSet,
    NoEligibleObservations,
    UnmappableSample,
    convert,
)
from ..observation import (
    JobIdentity,
    ObservationConstructionFailure,
    ObservationJobSpec,
    ObservationSet,
)
from .models import AnalysisOutcome, FailureRecord, FailureStage, InvalidPlan, JobResult


def _preflight(
    fixed_job: ObservationJobSpec, analysis_requests: Sequence[AnalysisRequest]
) -> tuple[JobIdentity, tuple[AnalysisRequest, ...]]:
    try:
        identity = validate_job(fixed_job)
        if not isinstance(analysis_requests, Sequence) or isinstance(
            analysis_requests, str | bytes | bytearray | Mapping | Set
        ):
            raise ValueError("analysis_requests must be an ordered non-empty sequence")
        requests = tuple(analysis_requests)
        if not requests:
            raise ValueError("analysis_requests must not be empty")
        seen: set[str] = set()
        for request in requests:
            if type(request) is not AnalysisRequest:
                raise ValueError("Expected public AnalysisRequest")
            if not isinstance(request.request_id, str) or not request.request_id:
                raise ValueError("request_id must be an explicit non-empty string")
            validate_spec(request.spec)
            if request.request_id in seen:
                raise ValueError(f"Duplicate request_id: {request.request_id!r}")
            seen.add(request.request_id)
            if isinstance(request.spec, IntervalCountSpec) and request.spec.unit != "decimal_ratio":
                raise ValueError("Index Trailing Return requires IntervalCount unit decimal_ratio")
    except Exception as exc:
        raise InvalidPlan(f"{type(exc).__name__}: {exc}") from exc
    return identity, requests


def _failure(
    identity: JobIdentity, stage: FailureStage, error: Exception, request_id: str | None = None
) -> FailureRecord:
    category = "ExecutionFailure"
    if stage == "input_preparation" and isinstance(error, InputPreparationFailure):
        category = error.category
    elif stage == "observation_construction" and isinstance(
        error, InputPreparationFailure | ObservationConstructionFailure
    ):
        category = error.category
    elif stage == "conversion" and isinstance(
        error, InvalidObservationSet | NoEligibleObservations | UnmappableSample
    ):
        category = error.category
    elif stage == "analyze" and isinstance(
        error, InvalidSample | InvalidStatisticalSpec | CalculationFailure
    ):
        category = type(error).__name__
    elif stage == "result_association" and isinstance(error, ResultAssociationFailure):
        category = error.category
    return FailureRecord(
        identity, stage, category, f"{type(error).__name__}: {error}", error, request_id
    )


def execute_job(
    fixed_job: ObservationJobSpec, analysis_requests: Sequence[AnalysisRequest]
) -> JobResult:
    """Execute one fixed Index Trailing Return Job, retaining all partial evidence."""
    identity, requests = _preflight(fixed_job, analysis_requests)
    prepared: PreparedInputs | None = None
    observations: ObservationSet[TrailingReturnProvenance] | None = None
    stage: FailureStage = "input_preparation"
    try:
        prepared = prepare_inputs(fixed_job)
        stage = "observation_construction"
        observations = construct_observations(fixed_job, prepared)
        stage = "conversion"
        projection = convert(observations)
    except Exception as exc:
        failure = _failure(identity, stage, exc)
        return JobResult(
            fixed_job,
            identity,
            "Failed",
            tuple(
                AnalysisOutcome(request, "not_attempted", not_attempted_reason=failure.reason)
                for request in requests
            ),
            prepared,
            observations,
            None,
            (failure,),
        )

    outcomes: list[AnalysisOutcome] = []
    failures: list[FailureRecord] = []
    for request in requests:
        try:
            result = compute(projection.numeric_sample, request.spec)
        except Exception as exc:
            failure = _failure(identity, "analyze", exc, request.request_id)
            failures.append(failure)
            outcomes.append(AnalysisOutcome(request, "failed", failure=failure))
            continue
        try:
            evidence = associate(fixed_job, observations, projection, request, result)
        except Exception as exc:
            failure = _failure(identity, "result_association", exc, request.request_id)
            failures.append(failure)
            outcomes.append(AnalysisOutcome(request, "failed", result, failure=failure))
            continue
        outcomes.append(AnalysisOutcome(request, "success", result, evidence))
    return JobResult(
        fixed_job,
        identity,
        "Failed" if failures else "Success",
        tuple(outcomes),
        prepared,
        observations,
        projection,
        tuple(failures),
    )
