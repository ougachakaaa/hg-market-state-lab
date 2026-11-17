"""Immutable query requests, evidence-backed projections and analysis associations."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from market_research.descriptive.cases.futures_basis import Slot
from market_statistics import (
    EmpiricalPercentileResult,
    EmpiricalPercentileSpec,
    IntervalCountResult,
    IntervalCountSpec,
    NumericSample,
    QuantileResult,
    QuantileSpec,
)

from .daily_index import DailyUnderlyingIndexEvidence, DailyUnderlyingIndexReference
from .financial import CalendarSpreadMetric
from .inputs import (
    CASE,
    DEFINITION_VERSION,
    InputEvidence,
    InputPreparationAttempt,
    PreparedCalendarSpreadInputs,
)
from .observations import (
    CalendarSpreadDay,
    CalendarSpreadObservationSet,
    OutcomeAccounting,
    PairDayObservation,
)

Metric = Literal["signed_spread", "annualized_point_spread", "annualized_spread_ratio"]
DistributionStage = Literal["0_7", "8_21", "22_plus", "all_stages"]
SampleStatus = Literal["empty_sample", "small_sample", "available"]


@dataclass(frozen=True, slots=True)
class SourceContext:
    provider: str = "tushare"
    exchange: str = "CFFEX"
    price_field: str = "close"
    limitations: tuple[str, ...] = (
        "Calendar and Futures exports are independent snapshots with no common "
        "acquisition time or freshness guarantee.",
        "Retained futures metadata is not guaranteed to have been known on the "
        "historical trade date.",
        "Read-only queries require separately prepared complete caches; "
        "they never ensure or repair missing data.",
        "Close relationships are descriptive, not executable roll quotes, "
        "forecasts or investment recommendations.",
        "Fees, slippage, margin, financing, dividends, future changes and "
        "waiting value are excluded.",
    )


EXECUTION_SOURCE_CONTEXT = SourceContext(
    limitations=(
        *SourceContext().limitations[:2],
        "Explicit execution may prepare incomplete caches through DataLake public services; "
        "analysis uses validated complete final exports.",
        *SourceContext().limitations[3:],
    )
)


@dataclass(frozen=True, slots=True)
class DailySpreadsRequest:
    product_code: str
    trade_date: date
    operation: Literal["query_daily_spreads"] = "query_daily_spreads"


@dataclass(frozen=True, slots=True)
class HistoricalRelativeValueRequest:
    product_code: str
    history_start: date
    evaluation_date: date
    metric: Metric
    histogram_edges: tuple[float, ...] | None
    operation: Literal["query_historical_relative_value"] = "query_historical_relative_value"


@dataclass(frozen=True, slots=True)
class DailySpreadsResult:
    request: DailySpreadsRequest
    observation_set: CalendarSpreadObservationSet
    underlying_index: DailyUnderlyingIndexReference
    underlying_index_evidence: DailyUnderlyingIndexEvidence
    source_context: SourceContext = SourceContext()
    case: str = CASE
    definition_version: str = DEFINITION_VERSION

    @property
    def prepared_inputs(self) -> PreparedCalendarSpreadInputs:
        return self.observation_set.prepared_inputs

    @property
    def day(self) -> CalendarSpreadDay:
        return self.observation_set.days[0]

    @property
    def accounting(self) -> OutcomeAccounting:
        return self.observation_set.accounting


@dataclass(frozen=True, slots=True)
class HistoricalSamplePoint:
    observation: PairDayObservation
    metric: CalendarSpreadMetric

    @property
    def trade_date(self) -> date:
        return self.observation.trade_date


@dataclass(frozen=True, slots=True)
class QuantileAnalysis:
    sample: NumericSample
    spec: QuantileSpec
    result: QuantileResult


@dataclass(frozen=True, slots=True)
class HistogramAnalysis:
    sample: NumericSample
    spec: IntervalCountSpec
    result: IntervalCountResult


@dataclass(frozen=True, slots=True)
class PercentileAnalysis:
    sample: NumericSample
    spec: EmpiricalPercentileSpec
    result: EmpiricalPercentileResult


@dataclass(frozen=True, slots=True)
class HistoricalDistribution:
    stage: DistributionStage
    metric: Metric
    unit: str
    candidate_dates: tuple[date, ...]
    accounting: OutcomeAccounting
    samples: tuple[HistoricalSamplePoint, ...]
    status: SampleStatus
    reason: str | None
    warnings: tuple[str, ...]
    numeric_sample: NumericSample | None
    quantile: QuantileAnalysis | None
    histogram_status: Literal["not_requested", "empty_sample", "available"]
    histogram: HistogramAnalysis | None

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def sample_dates(self) -> tuple[date, ...]:
        return tuple(point.trade_date for point in self.samples)


@dataclass(frozen=True, slots=True)
class CurrentAssessment:
    kind: Literal["matching_stage", "all_stages"]
    current: PairDayObservation | None
    distribution: HistoricalDistribution | None
    status: Literal["not_applicable", "empty_sample", "small_sample", "available"]
    reason: str | None
    warnings: tuple[str, ...]
    percentile: PercentileAnalysis | None


@dataclass(frozen=True, slots=True)
class PairRelativeValueResult:
    near_slot: Slot
    far_slot: Slot
    distributions: tuple[HistoricalDistribution, ...]
    matching_stage: CurrentAssessment
    all_stages: CurrentAssessment


@dataclass(frozen=True, slots=True)
class HistoricalRelativeValueResult:
    request: HistoricalRelativeValueRequest
    unit: str
    observation_set: CalendarSpreadObservationSet
    pairs: tuple[PairRelativeValueResult, ...]
    historical_accounting: OutcomeAccounting
    source_context: SourceContext = SourceContext()
    case: str = CASE
    definition_version: str = DEFINITION_VERSION

    @property
    def metric(self) -> Metric:
        return self.request.metric

    @property
    def prepared_inputs(self) -> PreparedCalendarSpreadInputs:
        return self.observation_set.prepared_inputs

    @property
    def current_day(self) -> CalendarSpreadDay:
        return self.observation_set.days[-1]

    @property
    def historical_days(self) -> tuple[CalendarSpreadDay, ...]:
        return self.observation_set.days[:-1]


class CalendarSpreadQueryError(Exception):
    """Classified whole-query failure; no successful partial business result."""

    def __init__(
        self,
        category: str,
        stage: str,
        dependency: str,
        reason: str,
        *,
        method: str | None = None,
        trade_date: date | None = None,
        near_slot: Slot | None = None,
        far_slot: Slot | None = None,
        evidence: tuple[InputEvidence, ...] = (),
        prepared_inputs: PreparedCalendarSpreadInputs | None = None,
        observation_set: CalendarSpreadObservationSet | None = None,
        reason_code: str | None = None,
        operation: str | None = None,
        attempts: tuple[InputPreparationAttempt, ...] = (),
    ) -> None:
        super().__init__(reason)
        self.category, self.stage, self.dependency, self.reason = (
            category,
            stage,
            dependency,
            reason,
        )
        self.method, self.trade_date = method, trade_date
        self.near_slot, self.far_slot = near_slot, far_slot
        self.evidence, self.prepared_inputs = evidence, prepared_inputs
        self.observation_set = observation_set
        self.reason_code = reason_code
        self.operation = operation
        self.attempts = attempts
