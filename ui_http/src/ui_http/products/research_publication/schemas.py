"""Explicit versioned HTTP projections of public publication facts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from ui_http.products.research.requests import (
    EmptyParameters,
    WindowBody,
)
from ui_http.products.research.schemas import JobIdentityBody


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class QuantileSpec(DTO):
    method: Literal["quantile"]
    points: list[float]


class IntervalSpec(DTO):
    method: Literal["interval_count"]
    edges: list[float]
    unit: Literal["decimal_ratio"]


class AnalysisRequest(DTO):
    request_id: str
    spec: QuantileSpec | IntervalSpec


class ViewReference(DTO):
    view_id: str
    measure: Literal["quantile", "count", "frequency"]


class AnalysisSummary(DTO):
    analysis_id: str
    job_identity: JobIdentityBody
    request_id: str
    spec: QuantileSpec | IntervalSpec
    status: Literal["success", "failed", "not_attempted"]
    views: list[ViewReference]


class JobSummary(DTO):
    job_identity: JobIdentityBody
    status: Literal["Success", "Failed", "Skipped"]
    analyses: list[str]


class SourceSummary(DTO):
    sha256: str
    size: int


class Scope(DTO):
    metric: Literal["trailing_cumulative_return_v1"]
    metric_parameters: EmptyParameters
    subjects: list[str]
    horizons: list[int]
    windows: list[WindowBody]
    analysis_requests: list[AnalysisRequest]
    on_job_failure: Literal["continue", "stop"]


class Manifest(DTO):
    schema_version: Literal[1]
    publication_id: str
    context: None
    scope: Scope
    status: Literal["success", "partial_success", "failed"]
    jobs: list[JobSummary]
    analyses: list[AnalysisSummary]
    source: SourceSummary


class Navigation(DTO):
    publication_id: str
    status: Literal["success", "partial_success", "failed"]


class PublicationList(DTO):
    data: list[Navigation]
    next_cursor: str | None


class ManifestResponse(DTO):
    data: Manifest


class QuantileResult(DTO):
    method: Literal["quantile"]
    estimator: str
    points_and_values: list[tuple[float, float]]
    sample_count: int
    unit: str


class Bin(DTO):
    left: float
    right: float
    left_inclusive: bool
    right_inclusive: bool
    count: int
    frequency: float


class IntervalResult(DTO):
    method: Literal["interval_count"]
    edges: list[float]
    bins: list[Bin]
    underflow_count: int
    underflow_frequency: float
    overflow_count: int
    overflow_frequency: float
    sample_count: int
    unit: str


class FactCoverage(DTO):
    expected_fact_count: int
    available_fact_count: int
    coverage_ratio: float | None


class MarketFactCoverage(DTO):
    overall: FactCoverage
    warm_up: FactCoverage
    sample: FactCoverage


class Coverage(DTO):
    candidate_count: int
    eligible_count: int
    unavailable_count: int
    excluded_count: int
    observation_coverage: float | None
    unavailable_ratio: float | None
    excluded_ratio: float | None
    market_facts: MarketFactCoverage
    observation_unit: Literal["decimal_ratio"]
    input_profile: Literal["trailing_return_inputs_v2"]
    input_fingerprint: str


class Analysis(DTO):
    schema_version: Literal[1]
    publication_id: str
    summary: AnalysisSummary
    result: QuantileResult | IntervalResult | None
    outcome: Literal["success", "failed", "not_attempted"]
    reason: Literal["Analysis failed.", "Analysis was not attempted."] | None
    coverage: Coverage | None


class AnalysisResponse(DTO):
    data: Analysis


class Coordinate(DTO):
    kind: Literal["number", "date", "category"]
    unit: str


class Axis(DTO):
    id: str
    orientation: Literal["x", "y"]
    coordinate: Coordinate


class Mark(DTO):
    x: float | str
    y: float | str


class Layer(DTO):
    type: Literal["line", "bar"]
    version: Literal[1]
    x: Coordinate
    y: Coordinate
    data: list[Mark]


class Binding(DTO):
    id: str
    layer: Layer
    x_axis: str
    y_axis: str


class Layout(DTO):
    title: str


class Presentation(DTO):
    show_legend: bool


class ChartView(DTO):
    version: Literal[1]
    axes: list[Axis]
    layers: list[Binding]
    layout: Layout
    presentation: Presentation


class ViewResponse(DTO):
    data: ChartView


class ErrorBody(DTO):
    kind: Literal[
        "invalid_request",
        "not_found",
        "corrupt",
        "inconsistent",
        "unsupported_version",
        "response_too_large",
        "verification_budget_exceeded",
        "unavailable",
        "internal_error",
    ]
    detail: str
    param: None = None


class ErrorResponse(DTO):
    error: ErrorBody
