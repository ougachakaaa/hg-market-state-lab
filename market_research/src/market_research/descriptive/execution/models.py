"""Execution-owned records retaining the original public component objects."""

from dataclasses import dataclass
from typing import Literal

from market_statistics import StatisticalResult, StatisticalSpec

from ..association import AnalysisRequest, ResearchAnalysisEvidence
from ..cases.trailing_return import (
    InputAttempt,
    InputPreparationFailure,
    PreparedInputs,
    TrailingReturnProvenance,
)
from ..conversion import SampleProjection
from ..observation import JobIdentity, ObservationJobSpec, ObservationSet

type FailureStage = Literal[
    "input_preparation", "observation_construction", "conversion", "analyze", "result_association"
]


class InvalidPlan(ValueError):
    """Illegal direct Job input, rejected before any upstream operation."""


@dataclass(frozen=True)
class FailureRecord:
    job_identity: JobIdentity
    failure_stage: FailureStage
    failure_category: str
    reason: str
    error: Exception
    request_id: str | None = None


@dataclass(frozen=True)
class AnalysisOutcome:
    request: AnalysisRequest
    status: Literal["success", "failed", "not_attempted"]
    statistical_result: StatisticalResult | None = None
    associated_evidence: ResearchAnalysisEvidence[TrailingReturnProvenance] | None = None
    failure: FailureRecord | None = None
    not_attempted_reason: str | None = None

    @property
    def request_id(self) -> str:
        return self.request.request_id

    @property
    def spec(self) -> StatisticalSpec:
        return self.request.spec


@dataclass(frozen=True)
class JobResult:
    fixed_job_spec: ObservationJobSpec
    job_identity: JobIdentity
    status: Literal["Success", "Failed", "Skipped"]
    analysis_outcomes: tuple[AnalysisOutcome, ...]
    prepared_inputs: PreparedInputs | None
    observation_set: ObservationSet[TrailingReturnProvenance] | None
    projection: SampleProjection[TrailingReturnProvenance] | None
    failures: tuple[FailureRecord, ...]
    skip_reason: str | None = None
    triggering_failed_job_identity: JobIdentity | None = None

    @property
    def input_attempts(self) -> tuple[InputAttempt, ...]:
        if self.prepared_inputs is not None:
            return self.prepared_inputs.attempts
        for failure in self.failures:
            if isinstance(failure.error, InputPreparationFailure):
                return failure.error.evidence
        return ()
