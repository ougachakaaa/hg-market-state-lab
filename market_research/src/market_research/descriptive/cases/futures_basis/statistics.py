"""Explicit scalar adaptation, common-date association and observed discount spans."""

from dataclasses import dataclass
from datetime import date
from itertools import combinations
from typing import Literal

import market_statistics as stats

from .models import SLOTS, ContractTransition, Slot
from .observations import FuturesBasisResult, SlotDayObservation

type AnalysisMetric = Literal["basis_value", "basis_ratio", "annualized_basis_ratio"]
METRICS: tuple[AnalysisMetric, ...] = ("basis_value", "basis_ratio", "annualized_basis_ratio")
PAIRS = tuple(combinations(SLOTS, 2))


@dataclass(frozen=True, slots=True)
class DistributionRequest:
    analysis_id: str
    slot: Slot
    metric: AnalysisMetric
    start_date: date
    end_date: date
    quantile: stats.QuantileSpec
    histogram: stats.IntervalCountSpec


@dataclass(frozen=True, slots=True)
class ComparisonRequest:
    analysis_id: str
    slots: tuple[Slot, Slot]
    metric: AnalysisMetric
    start_date: date
    end_date: date
    quantile: stats.QuantileSpec
    histogram: stats.IntervalCountSpec


class AnalysisRequestError(ValueError):
    def __init__(self, request: object, reason: str) -> None:
        super().__init__(reason)
        self.request = request
        self.reason = reason


@dataclass(frozen=True, slots=True)
class MethodOutcome:
    spec: stats.StatisticalSpec
    result: stats.StatisticalResult | None
    failure_category: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DistributionResult:
    request: DistributionRequest
    source: FuturesBasisResult
    candidates: tuple[SlotDayObservation, ...]
    binding: tuple[SlotDayObservation, ...]
    methods: tuple[MethodOutcome, ...]

    def count(self, status: str) -> int:
        return sum(r.outcome(self.request.metric).status == status for r in self.candidates)


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    request: ComparisonRequest
    source: FuturesBasisResult
    candidates: tuple[tuple[SlotDayObservation, SlotDayObservation], ...]
    binding: tuple[tuple[SlotDayObservation, SlotDayObservation], ...]
    dropped: tuple[tuple[SlotDayObservation, SlotDayObservation], ...]
    left_methods: tuple[MethodOutcome, ...]
    right_methods: tuple[MethodOutcome, ...]

    @property
    def common_dates(self) -> tuple[date, ...]:
        return tuple(left.trade_date for left, _ in self.binding)


def _validate(source: FuturesBasisResult, request: DistributionRequest | ComparisonRequest) -> None:
    original = source.prepared.request
    try:
        if not isinstance(request.analysis_id, str) or not request.analysis_id.strip():
            raise ValueError("Nonempty analysis_id required")
        if request.metric not in METRICS:
            raise ValueError("Unknown metric")
        if type(request.start_date) is not date or type(request.end_date) is not date:
            raise ValueError("Date-only window required")
        if not original.start_date <= request.start_date <= request.end_date <= original.end_date:
            raise ValueError("Analysis window must be within observation window")
        if isinstance(request, DistributionRequest):
            if request.slot not in SLOTS:
                raise ValueError("Unknown Slot")
        elif request.slots not in PAIRS:
            raise ValueError("Expected canonical ordered Slot pair")
        if (
            type(request.quantile) is not stats.QuantileSpec
            or type(request.histogram) is not stats.IntervalCountSpec
        ):
            raise ValueError("Explicit QuantileSpec and IntervalCountSpec required")
        stats.validate_spec(request.quantile)
        stats.validate_spec(request.histogram)
        if request.histogram.unit != _unit(request.metric):
            raise ValueError("Histogram unit differs from metric unit")
    except (ValueError, stats.InvalidStatisticalSpec) as exc:
        raise AnalysisRequestError(request, str(exc)) from exc


def _unit(metric: AnalysisMetric) -> str:
    return "index_points" if metric == "basis_value" else "decimal_ratio"


def _rows(
    source: FuturesBasisResult, slot: Slot, start: date, end: date
) -> tuple[SlotDayObservation, ...]:
    rows = tuple(
        sorted(
            (r for r in source.slot_days if r.slot == slot and start <= r.trade_date <= end),
            key=lambda r: r.trade_date,
        )
    )
    expected = tuple(d for d in source.prepared.candidate_dates if start <= d <= end)
    if tuple(r.trade_date for r in rows) != expected:
        raise ValueError("Observation candidates are missing, duplicated or outside calendar")
    return rows


def _compute(
    rows: tuple[SlotDayObservation, ...], request: DistributionRequest | ComparisonRequest
) -> tuple[MethodOutcome, ...]:
    specs = (stats.MeanSpec(), request.quantile, request.histogram)
    if not rows:
        return tuple(
            MethodOutcome(spec, None, "no_eligible_sample", "No eligible candidate dates")
            for spec in specs
        )
    values = tuple(r.outcome(request.metric).value for r in rows)
    # WP3 guarantees finite eligible values; never filter or repair a malformed binding.
    if any(v is None for v in values):
        raise ValueError("Eligible binding has no value")
    sample = stats.NumericSample(tuple(v for v in values if v is not None), _unit(request.metric))
    outcomes = []
    for spec in specs:
        try:
            result = stats.compute(sample, spec)
        except stats.StatisticalFailure as exc:
            outcomes.append(MethodOutcome(spec, None, type(exc).__name__, str(exc)))
            continue
        if (
            result.sample_count != len(rows)
            or result.unit != sample.unit
            or result.method != spec.method
            or not _parameters_match(spec, result)
        ):
            outcomes.append(
                MethodOutcome(
                    spec,
                    result,
                    "association_failure",
                    "Result identity/count/unit/parameters mismatch",
                )
            )
        else:
            outcomes.append(MethodOutcome(spec, result))
    return tuple(outcomes)


def _parameters_match(spec: stats.StatisticalSpec, result: stats.StatisticalResult) -> bool:
    if isinstance(spec, stats.MeanSpec):
        return isinstance(result, stats.MeanResult) and result.estimator == "arithmetic_binary64_v1"
    if isinstance(spec, stats.QuantileSpec):
        return (
            isinstance(result, stats.QuantileResult)
            and result.estimator == "type7_linear_v1"
            and tuple(p for p, _ in result.points_and_values) == spec.points
        )
    return isinstance(result, stats.IntervalCountResult) and result.edges == spec.edges


def analyze_distribution(
    source: FuturesBasisResult, request: DistributionRequest
) -> DistributionResult:
    _validate(source, request)
    rows = _rows(source, request.slot, request.start_date, request.end_date)
    binding = tuple(r for r in rows if r.outcome(request.metric).status == "eligible")
    return DistributionResult(request, source, rows, binding, _compute(binding, request))


def compare_terms(source: FuturesBasisResult, request: ComparisonRequest) -> ComparisonResult:
    _validate(source, request)
    left, right = (
        _rows(source, slot, request.start_date, request.end_date) for slot in request.slots
    )
    candidates = tuple(zip(left, right, strict=True))
    binding = tuple(
        pair
        for pair in candidates
        if all(r.outcome(request.metric).status == "eligible" for r in pair)
    )
    dropped = tuple(pair for pair in candidates if pair not in binding)
    return ComparisonResult(
        request,
        source,
        candidates,
        binding,
        dropped,
        _compute(tuple(a for a, _ in binding), request),
        _compute(tuple(b for _, b in binding), request),
    )


type Boundary = Literal["window", "gap", "non_discount"]


@dataclass(frozen=True, slots=True)
class DiscountRun:
    slot: Slot
    references: tuple[SlotDayObservation, ...]
    transitions: tuple[ContractTransition, ...]
    left_boundary: Boundary
    right_boundary: Boundary

    @property
    def start(self) -> date:
        return self.references[0].trade_date

    @property
    def end(self) -> date:
        return self.references[-1].trade_date

    @property
    def observed_trading_sessions(self) -> int:
        return len(self.references)

    @property
    def left_censored(self) -> bool:
        return self.left_boundary != "non_discount"

    @property
    def right_censored(self) -> bool:
        return self.right_boundary != "non_discount"


@dataclass(frozen=True, slots=True)
class DiscountSummary:
    source: FuturesBasisResult
    slot: Slot
    start_date: date
    end_date: date
    complete: tuple[DiscountRun, ...]
    censored: tuple[DiscountRun, ...]


def discount_runs(
    source: FuturesBasisResult, slot: Slot, start_date: date, end_date: date
) -> DiscountSummary:
    original = source.prepared.request
    if (
        slot not in SLOTS
        or type(start_date) is not date
        or type(end_date) is not date
        or not original.start_date <= start_date <= end_date <= original.end_date
    ):
        raise AnalysisRequestError(
            (slot, start_date, end_date), "Invalid persistence subject/window"
        )
    rows = _rows(source, slot, start_date, end_date)
    runs: list[DiscountRun] = []
    active: list[SlotDayObservation] = []
    left: Boundary = "window"

    def finish(right: Boundary) -> None:
        if active:
            dates = {r.trade_date for r in active}
            transitions = tuple(
                t
                for t in source.transitions.transitions
                if t.slot == slot and t.previous_date in dates and t.trade_date in dates
            )
            runs.append(DiscountRun(slot, tuple(active), transitions, left, right))
            active.clear()

    for row in rows:
        outcome = row.outcome("basis_value")
        if outcome.status == "eligible" and outcome.value is not None and outcome.value < 0:
            active.append(row)
        else:
            boundary: Boundary = "non_discount" if outcome.status == "eligible" else "gap"
            finish(boundary)
            left = boundary
    finish("window")
    return DiscountSummary(
        source,
        slot,
        start_date,
        end_date,
        tuple(r for r in runs if not r.left_censored and not r.right_censored),
        tuple(r for r in runs if r.left_censored or r.right_censored),
    )
