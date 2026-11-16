"""Historical transport projection without duplicated numerical samples or source exports."""

from typing import Literal

from pydantic import Field

from ui_http.products.futures_calendar_spread.schemas import (
    Accounting,
    Contract,
    DailyErrorResponse,
    DateOnly,
    Day,
    DaySummary,
    FinancialMetric,
    Metric,
    Product,
    Slot,
    SourceContext,
    Stage,
    Unit,
    Wire,
)

DistributionStage = Literal["0_7", "8_21", "22_plus", "all_stages"]
SampleStatus = Literal["empty_sample", "small_sample", "available"]


class HistoricalRequest(Wire):
    product_code: Product
    history_start: DateOnly
    evaluation_date: DateOnly
    metric: Metric = "annualized_spread_ratio"
    histogram_edges: list[float] = Field(default_factory=list)


class HistoricalEcho(Wire):
    product_code: Product
    history_start: DateOnly
    evaluation_date: DateOnly
    metric: Metric
    histogram_edges: tuple[float, ...] | None
    operation: Literal["query_historical_relative_value"]


class QuantileSpec(Wire):
    method: Literal["quantile"]
    points: tuple[float, ...]


class QuantileResult(Wire):
    method: Literal["quantile"]
    estimator: Literal["type7_linear_v1"]
    points_and_values: tuple[tuple[float, float], ...]
    sample_count: int
    unit: Unit


class Quantile(Wire):
    spec: QuantileSpec
    result: QuantileResult


class HistogramSpec(Wire):
    method: Literal["interval_count"]
    edges: tuple[float, ...]
    unit: Unit


class Bin(Wire):
    left: float
    right: float
    left_inclusive: bool
    right_inclusive: bool
    count: int
    frequency: float


class HistogramResult(Wire):
    method: Literal["interval_count"]
    edges: tuple[float, ...]
    bins: tuple[Bin, ...]
    underflow_count: int
    overflow_count: int
    underflow_frequency: float
    overflow_frequency: float
    sample_count: int
    unit: Unit


class Histogram(Wire):
    spec: HistogramSpec
    result: HistogramResult


class PercentileSpec(Wire):
    method: Literal["empirical_percentile"]
    queries: tuple[float, ...]
    unit: Unit


class PercentilePoint(Wire):
    query: float
    less_count: int
    equal_count: int
    greater_count: int
    percentile: float = Field(ge=0, le=1)


class PercentileResult(Wire):
    method: Literal["empirical_percentile"]
    estimator: Literal["midrank_v1"]
    query_results: tuple[PercentilePoint, ...]
    sample_count: int
    unit: Unit


class Percentile(Wire):
    spec: PercentileSpec
    result: PercentileResult


class SamplePoint(Wire):
    trade_date: DateOnly
    expiry_stage: Stage
    near: Contract
    far: Contract
    delta_days: int
    near_dte_days: int
    metric: FinancialMetric


class Distribution(Wire):
    stage: DistributionStage
    metric: Metric
    unit: Unit
    candidate_dates: tuple[DateOnly, ...]
    accounting: Accounting
    sample_dates: tuple[DateOnly, ...]
    sample_count: int
    status: SampleStatus
    reason: str | None
    warnings: tuple[str, ...]
    quantile: Quantile | None
    histogram_status: Literal["not_requested", "empty_sample", "available"]
    histogram: Histogram | None


class Assessment(Wire):
    kind: Literal["matching_stage", "all_stages"]
    distribution_stage: DistributionStage | None
    status: Literal["not_applicable", "empty_sample", "small_sample", "available"]
    reason: str | None
    warnings: tuple[str, ...]
    percentile: Percentile | None


class PairResult(Wire):
    near_slot: Slot
    far_slot: Slot
    samples: tuple[SamplePoint, ...]
    distributions: tuple[Distribution, ...] = Field(min_length=4, max_length=4)
    matching_stage: Assessment
    all_stages: Assessment


class HistoricalResponse(Wire):
    case: Literal["futures_calendar_spread_v1"]
    definition_version: Literal["futures_calendar_spread_definition_v1"]
    request: HistoricalEcho
    metric: Metric
    unit: Unit
    current_day: Day
    historical_days: tuple[DaySummary, ...]
    historical_accounting: Accounting
    pairs: tuple[PairResult, ...] = Field(min_length=6, max_length=6)
    source_context: SourceContext


class HistoricalErrorResponse(DailyErrorResponse):
    pass
