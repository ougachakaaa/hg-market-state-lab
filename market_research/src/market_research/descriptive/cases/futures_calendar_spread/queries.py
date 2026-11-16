"""Independent synchronous business queries sharing one WP2 observation collection."""

from collections.abc import Sequence
from datetime import date
from typing import Literal, cast

from market_research.descriptive.cases.futures_basis import Slot
from market_statistics import (
    EmpiricalPercentileResult,
    EmpiricalPercentileSpec,
    IntervalCountResult,
    IntervalCountSpec,
    InvalidStatisticalSpec,
    NumericSample,
    QuantileResult,
    QuantileSpec,
    validate_spec,
)

from .construction import construct_observations
from .inputs import CalendarSpreadRequest, InputPreparationError
from .observations import (
    PAIRS,
    CalendarSpreadObservationSet,
    ObservationConstructionError,
    OutcomeAccounting,
    PairDayObservation,
)
from .preparation import CalendarService, FuturesService, prepare_inputs
from .query_models import (
    CalendarSpreadQueryError,
    CurrentAssessment,
    DailySpreadsRequest,
    DailySpreadsResult,
    DistributionStage,
    HistogramAnalysis,
    HistoricalDistribution,
    HistoricalRelativeValueRequest,
    HistoricalRelativeValueResult,
    HistoricalSamplePoint,
    Metric,
    PairRelativeValueResult,
    PercentileAnalysis,
    QuantileAnalysis,
    SampleStatus,
)
from .query_statistics import compute_associated
from .validation import PublicInputError, require, validate_request

UNITS = {
    "signed_spread": "index_points",
    "annualized_point_spread": "index_points_per_365_natural_days",
    "annualized_spread_ratio": "decimal_ratio",
}
STAGES: tuple[DistributionStage, ...] = ("0_7", "8_21", "22_plus", "all_stages")
QUANTILES = (0, 0.05, 0.25, 0.5, 0.75, 0.95, 1)
SMALL_SAMPLE_WARNING = (
    "Small descriptive sample (N < 30); no reliability or predictive inference.",
)


def _validate(product_code: str, start: date, end: date) -> None:
    try:
        validate_request(CalendarSpreadRequest(product_code, start, end))
    except PublicInputError as exc:
        raise CalendarSpreadQueryError(
            "invalid_request", "query_validation", "request", str(exc)
        ) from exc


def _collect(
    product_code: str,
    start: date,
    end: date,
    calendar_service: CalendarService | None,
    futures_service: FuturesService | None,
) -> CalendarSpreadObservationSet:
    try:
        prepared = prepare_inputs(
            product_code,
            start,
            end,
            calendar_service=calendar_service,
            futures_service=futures_service,
        )
        return construct_observations(prepared)
    except InputPreparationError as exc:
        raise CalendarSpreadQueryError(
            exc.category,
            exc.stage,
            exc.dependency,
            "Input preparation failed",
            evidence=exc.evidence,
        ) from exc
    except ObservationConstructionError as exc:
        raise CalendarSpreadQueryError(
            exc.category,
            exc.stage,
            exc.dependency,
            "Observation construction failed",
            method="compute_calendar_spread" if exc.dependency == "financial_core" else None,
            trade_date=exc.trade_date,
            near_slot=exc.near_slot,
            far_slot=exc.far_slot,
            evidence=prepared.evidence,
            prepared_inputs=prepared,
        ) from exc


def query_daily_spreads(
    product_code: str,
    trade_date: date,
    *,
    calendar_service: CalendarService | None = None,
    futures_service: FuturesService | None = None,
) -> DailySpreadsResult:
    _validate(product_code, trade_date, trade_date)
    collection = _collect(product_code, trade_date, trade_date, calendar_service, futures_service)
    return DailySpreadsResult(DailySpreadsRequest(product_code, trade_date), collection)


def _account(observations: tuple[PairDayObservation, ...]) -> OutcomeAccounting:
    return OutcomeAccounting(
        len(observations),
        sum(o.outcome == "valid" for o in observations),
        sum(o.outcome == "not_applicable" for o in observations),
        sum(o.outcome == "excluded" for o in observations),
    )


def _distribution(
    stage: DistributionStage,
    metric: Metric,
    unit: str,
    candidates: tuple[PairDayObservation, ...],
    points: tuple[HistoricalSamplePoint, ...],
    histogram_spec: IntervalCountSpec | None,
    collection: CalendarSpreadObservationSet,
    pair: tuple[Slot, Slot],
) -> HistoricalDistribution:
    n = len(points)
    status: SampleStatus = "empty_sample" if n == 0 else "small_sample" if n < 30 else "available"
    sample, quantile, histogram = None, None, None
    if n:
        sample = NumericSample(tuple(point.metric.value for point in points), unit)
        quantile_spec = QuantileSpec(QUANTILES)
        quantile_result = compute_associated(sample, quantile_spec, collection, pair)
        quantile = QuantileAnalysis(sample, quantile_spec, cast(QuantileResult, quantile_result))
        if histogram_spec is not None:
            histogram_result = compute_associated(sample, histogram_spec, collection, pair)
            histogram = HistogramAnalysis(
                sample, histogram_spec, cast(IntervalCountResult, histogram_result)
            )
    histogram_status: Literal["not_requested", "empty_sample", "available"] = (
        "not_requested" if histogram_spec is None else "available" if n else "empty_sample"
    )
    return HistoricalDistribution(
        stage,
        metric,
        unit,
        tuple(o.trade_date for o in candidates),
        _account(candidates),
        points,
        status,
        "no_valid_historical_observations" if not n else None,
        SMALL_SAMPLE_WARNING if status == "small_sample" else (),
        sample,
        quantile,
        histogram_status,
        histogram,
    )


def _assessment(
    kind: Literal["matching_stage", "all_stages"],
    current: PairDayObservation | None,
    distribution: HistoricalDistribution | None,
    metric: Metric,
    collection: CalendarSpreadObservationSet,
    pair: tuple[Slot, Slot],
) -> CurrentAssessment:
    if current is None or current.outcome != "valid":
        return CurrentAssessment(
            kind,
            current,
            distribution,
            "not_applicable",
            "non_trading_day" if current is None else current.reason,
            (),
            None,
        )
    # A valid current Observation always has a stage and a matching distribution.
    assert distribution is not None
    if distribution.numeric_sample is None:
        return CurrentAssessment(
            kind, current, distribution, "empty_sample", distribution.reason, (), None
        )
    spec = EmpiricalPercentileSpec((getattr(current.metrics, metric).value,), distribution.unit)
    result = compute_associated(
        distribution.numeric_sample, spec, collection, pair, current.trade_date
    )
    analysis = PercentileAnalysis(
        distribution.numeric_sample, spec, cast(EmpiricalPercentileResult, result)
    )
    return CurrentAssessment(
        kind, current, distribution, distribution.status, None, distribution.warnings, analysis
    )


def query_historical_relative_value(
    product_code: str,
    history_start: date,
    evaluation_date: date,
    metric: Metric = "annualized_spread_ratio",
    histogram_edges: Sequence[int | float] | None = None,
    *,
    calendar_service: CalendarService | None = None,
    futures_service: FuturesService | None = None,
) -> HistoricalRelativeValueResult:
    _validate(product_code, history_start, evaluation_date)
    histogram_spec = None
    try:
        require(history_start < evaluation_date, "History must start before evaluation date")
        require(type(metric) is str and metric in UNITS, "Unknown metric")
        unit = UNITS[metric]
        if histogram_edges is not None:
            histogram_spec = IntervalCountSpec(histogram_edges, unit)
            validate_spec(histogram_spec)
    except (PublicInputError, InvalidStatisticalSpec) as exc:
        raise CalendarSpreadQueryError(
            "invalid_request", "query_validation", "request", "Invalid historical query parameters"
        ) from exc
    request = HistoricalRelativeValueRequest(
        product_code,
        history_start,
        evaluation_date,
        metric,
        None if histogram_spec is None else histogram_spec.edges,
    )
    collection = _collect(
        product_code, history_start, evaluation_date, calendar_service, futures_service
    )
    historical = tuple(
        o for o in collection.observations if history_start <= o.trade_date < evaluation_date
    )
    current = {(o.near_slot, o.far_slot): o for o in collection.days[-1].observations}
    pairs = []
    for pair in PAIRS:
        candidates = tuple(o for o in historical if (o.near_slot, o.far_slot) == pair)
        points = tuple(
            HistoricalSamplePoint(o, getattr(o.metrics, metric))
            for o in candidates
            if o.outcome == "valid"
        )
        distributions = tuple(
            _distribution(
                stage,
                metric,
                unit,
                tuple(o for o in candidates if stage == "all_stages" or o.expiry_stage == stage),
                tuple(
                    p
                    for p in points
                    if stage == "all_stages" or p.observation.expiry_stage == stage
                ),
                histogram_spec,
                collection,
                pair,
            )
            for stage in STAGES
        )
        today = current.get(pair)
        matching = next(
            (d for d in distributions if today is not None and today.expiry_stage == d.stage), None
        )
        pairs.append(
            PairRelativeValueResult(
                *pair,
                distributions,
                _assessment("matching_stage", today, matching, metric, collection, pair),
                _assessment("all_stages", today, distributions[-1], metric, collection, pair),
            )
        )
    return HistoricalRelativeValueResult(
        request, unit, collection, tuple(pairs), _account(historical)
    )
