"""Concrete wire evidence, with bounded public summaries and no exception graphs."""

from collections.abc import Mapping
from math import isfinite
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, FiniteFloat, field_validator, model_validator

from .requests import AnalysisBody, DateOnly, EmptyParameters, PlanBody, WindowBody, WireModel


class JobIdentityBody(WireModel):
    metric: str
    subject: str
    metric_parameters: EmptyParameters
    horizon: int
    horizon_unit: str
    start_date: DateOnly
    end_date: DateOnly
    anchor_meaning: str
    bounds: str

    @model_validator(mode="before")
    @classmethod
    def structural_tuple(cls, value: object) -> object:
        if isinstance(value, tuple) and len(value) == 9:
            names = tuple(cls.model_fields)
            return dict(zip(names, (value[0], value[1], dict(value[2]), *value[3:]), strict=True))
        return value


class FixedJobBody(WireModel):
    subject: str
    metric: str
    metric_parameters: EmptyParameters
    horizon: int
    historical_sample_window: WindowBody

    @field_validator("metric_parameters", mode="before")
    @classmethod
    def empty_mapping(cls, value: object) -> object:
        return dict(value) if isinstance(value, Mapping) else value


class PlannedJobBody(WireModel):
    fixed_job_spec: FixedJobBody
    job_identity: JobIdentityBody


class PreviewResponse(WireModel):
    plan: PlanBody
    jobs: tuple[PlannedJobBody, ...]
    planned_count: int
    analysis_attempt_count: int


class ObservationKeyBody(WireModel):
    job_identity: JobIdentityBody
    anchor: DateOnly

    @model_validator(mode="before")
    @classmethod
    def structural_tuple(cls, value: object) -> object:
        if isinstance(value, tuple) and len(value) == 2:
            return {"job_identity": value[0], "anchor": value[1]}
        return value


class DefinitionBody(WireModel):
    metric: str
    grain: str
    key_definition: str
    formula: str
    unit: str
    horizon_unit: str
    calendar: str
    anchor_meaning: str
    bounds: str


class RequiredFactBody(WireModel):
    dataset: str
    view: str
    export_schema_version: int
    subject: str
    trade_date: DateOnly
    field: str


UNIT_DIAGNOSTIC = "Upstream unit acquisition failed; original diagnostic is available in Python."


class MissingDependencyBody(WireModel):
    endpoint_role: Literal["anchor", "lookback"]
    fact: RequiredFactBody
    reason: Literal["daily_fact_unavailable"]
    input_reference: Literal["index_slice.final_export"]
    diagnostic_reasons: tuple[str, ...]

    @field_validator("diagnostic_reasons", mode="before")
    @classmethod
    def safe_diagnostics(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(UNIT_DIAGNOSTIC for _ in value)


class EndpointFactBody(WireModel):
    endpoint_role: Literal["anchor", "lookback"]
    fact: RequiredFactBody
    value: FiniteFloat


class EligibleBody(WireModel):
    observation_key: ObservationKeyBody
    anchor: DateOnly
    scalar_value: FiniteFloat


class UnavailableBody(WireModel):
    observation_key: ObservationKeyBody
    anchor: DateOnly
    missing_dependencies: tuple[MissingDependencyBody, ...]
    available_endpoints: tuple[EndpointFactBody, ...]


class ExcludedBody(WireModel):
    observation_key: ObservationKeyBody
    anchor: DateOnly
    reason_code: Literal["non_positive_close"]
    reason: Literal["Required endpoint close is non-positive"]
    offending_facts: tuple[EndpointFactBody, ...]


DailyKeyBody = tuple[str, DateOnly]


class FactCoverageBody(WireModel):
    expected_keys: tuple[DailyKeyBody, ...]
    available_keys: tuple[DailyKeyBody, ...]
    absent_keys: tuple[DailyKeyBody, ...]
    expected_fact_units: int
    available_fact_units: int
    ratio: FiniteFloat | None


class MarketCoverageBody(WireModel):
    overall: FactCoverageBody
    warm_up: FactCoverageBody
    sample: FactCoverageBody


class SpanBody(WireModel):
    anchor: DateOnly
    lookback: DateOnly


class DependenceBody(WireModel):
    horizon: int
    horizon_unit: str
    ordered_anchors: tuple[DateOnly, ...]
    spans: tuple[SpanBody, ...]
    interpretation: str


class EndpointRequirementBody(WireModel):
    anchor: DateOnly
    anchor_daily_key: DailyKeyBody
    lookback_daily_key: DailyKeyBody
    missing_required_facts: tuple[MissingDependencyBody, ...]


class ProvenanceBody(WireModel):
    input_profile: str
    input_fingerprint: str
    endpoint_requirements: tuple[EndpointRequirementBody, ...]


class ObservationSetBody(WireModel):
    job_identity: JobIdentityBody
    observation_definition: DefinitionBody
    candidate_anchors: tuple[DateOnly, ...]
    candidate_count: int
    eligible_count: int
    unavailable_count: int
    excluded_count: int
    observation_coverage: FiniteFloat | None
    unavailable_ratio: FiniteFloat | None
    excluded_ratio: FiniteFloat | None
    eligible_observations: tuple[EligibleBody, ...]
    unavailable_observations: tuple[UnavailableBody, ...]
    excluded_observations: tuple[ExcludedBody, ...]
    market_fact_coverage: MarketCoverageBody
    sample_dependence_context: DependenceBody
    provenance: ProvenanceBody


class NumericSampleBody(WireModel):
    values: tuple[FiniteFloat, ...]
    unit: str
    sample_count: int


class ProjectionBody(WireModel):
    numeric_sample: NumericSampleBody
    ordered_observation_keys: tuple[ObservationKeyBody, ...]
    source_job_identity: JobIdentityBody
    source_input_fingerprint: str


class NonFiniteCoordinate(WireModel):
    kind: Literal["non_finite"] = "non_finite"
    value: Literal["nan", "positive_infinity", "negative_infinity"]


def raw_coordinate(value: object) -> object:
    if type(value) is float and not isfinite(value):
        if value != value:
            return NonFiniteCoordinate(value="nan")
        return NonFiniteCoordinate(value="positive_infinity" if value > 0 else "negative_infinity")
    return value


RawCoordinate = Annotated[FiniteFloat | NonFiniteCoordinate, BeforeValidator(raw_coordinate)]


class QuantileResultBody(WireModel):
    method: Literal["quantile"]
    estimator: Literal["type7_linear_v1"]
    points_and_values: tuple[tuple[RawCoordinate, RawCoordinate], ...]
    sample_count: int
    unit: str


class BinBody(WireModel):
    left: RawCoordinate
    right: RawCoordinate
    left_inclusive: bool
    right_inclusive: bool
    count: int
    frequency: RawCoordinate


class IntervalCountResultBody(WireModel):
    method: Literal["interval_count"]
    edges: tuple[RawCoordinate, ...]
    bins: tuple[BinBody, ...]
    underflow_count: int
    overflow_count: int
    underflow_frequency: RawCoordinate
    overflow_frequency: RawCoordinate
    sample_count: int
    unit: str


ResultBody = Annotated[QuantileResultBody | IntervalCountResultBody, Field(discriminator="method")]


class FailureBody(WireModel):
    job_identity: JobIdentityBody
    failure_stage: Literal[
        "input_preparation",
        "observation_construction",
        "conversion",
        "analyze",
        "result_association",
    ]
    failure_category: str
    reason: str
    request_id: str | None


class AnalysisOutcomeBody(WireModel):
    request: AnalysisBody
    status: Literal["success", "failed", "not_attempted"]
    statistical_result: ResultBody | None
    associated: bool
    failure: FailureBody | None
    not_attempted_reason: str | None

    @model_validator(mode="after")
    def successful_numbers_are_finite(self) -> "AnalysisOutcomeBody":
        def contains_anomaly(value: object) -> bool:
            if isinstance(value, dict):
                return value.get("kind") == "non_finite" or any(
                    contains_anomaly(item) for item in value.values()
                )
            if isinstance(value, tuple | list):
                return any(contains_anomaly(item) for item in value)
            return False

        if self.status == "success" and self.statistical_result is not None:
            if contains_anomaly(self.statistical_result.model_dump()):
                raise ValueError("Successful numerical results require finite JSON numbers")
        return self


class CoverageBody(WireModel):
    requested_units: int
    successful_units: int
    missing_units: int
    pending_units: int
    failed_units: int
    complete: bool


class InvalidPublicShape(WireModel):
    state: Literal["invalid_public_shape"] = "invalid_public_shape"


class ExportSummary(WireModel):
    state: Literal["available"] = "available"
    dataset: Literal["tushare_trade_calendar", "tushare_index_daily"]
    view: Literal["calendar", "index_daily"]
    export_schema_version: int
    coverage: CoverageBody
    record_count: int


class UnitFailureBody(WireModel):
    identity: DailyKeyBody
    reason: str = UNIT_DIAGNOSTIC

    @field_validator("reason", mode="before")
    @classmethod
    def safe_reason(cls, value: object) -> str:
        return UNIT_DIAGNOSTIC


class EnsureSummary(WireModel):
    state: Literal["available"] = "available"
    requested_units: int
    already_successful_units: int
    attempted_units: int
    succeeded_units: int
    failed_units: int
    records_written: int
    complete: bool
    failures: tuple[UnitFailureBody, ...]

    @field_validator("failures", mode="before")
    @classmethod
    def safe_failures(cls, value: tuple[object, ...]) -> tuple[UnitFailureBody, ...]:
        return tuple(UnitFailureBody.model_validate(item) for item in value)


class CalendarRequestBody(WireModel):
    kind: Literal["calendar"] = "calendar"
    exchange: str
    start_date: DateOnly
    end_date: DateOnly


class IndexRequestBody(WireModel):
    kind: Literal["index_daily"] = "index_daily"
    index_codes: tuple[str, ...]
    start_date: DateOnly
    end_date: DateOnly


InputRequestBody = Annotated[CalendarRequestBody | IndexRequestBody, Field(discriminator="kind")]
ExportEvidence = Annotated[ExportSummary | InvalidPublicShape, Field(discriminator="state")]
EnsureEvidence = Annotated[EnsureSummary | InvalidPublicShape, Field(discriminator="state")]


class InputAttemptBody(WireModel):
    request: InputRequestBody
    preliminary_export: ExportEvidence | None
    ensure_result: EnsureEvidence | None
    final_export: ExportEvidence | None


class PreparedSliceBody(WireModel):
    request: InputRequestBody
    final_export: ExportSummary


class PreparedContextBody(WireModel):
    calendar_slices: tuple[PreparedSliceBody, ...]
    index_slice: PreparedSliceBody | None


class JobResultBody(PlannedJobBody):
    status: Literal["Success", "Failed", "Skipped"]
    skip_reason: str | None
    triggering_failed_job_identity: JobIdentityBody | None
    analysis_outcomes: tuple[AnalysisOutcomeBody, ...]
    failures: tuple[FailureBody, ...]
    input_attempts: tuple[InputAttemptBody, ...]
    prepared_context: PreparedContextBody | None
    observation_set: ObservationSetBody | None
    projection: ProjectionBody | None


class BatchResponse(WireModel):
    plan: PlanBody
    status: Literal["success", "partial_success", "failed"]
    planned_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    job_results: tuple[JobResultBody, ...]
    source_identity_limitation: str
