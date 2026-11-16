"""Case-local public Statistics invocation and result association, without algorithms."""

from datetime import date
from math import isfinite

from market_research.descriptive.cases.futures_basis import Slot
from market_statistics import (
    EmpiricalPercentileQueryResult,
    EmpiricalPercentileResult,
    EmpiricalPercentileSpec,
    IntervalBin,
    IntervalCountResult,
    IntervalCountSpec,
    NumericSample,
    QuantileResult,
    QuantileSpec,
    StatisticalFailure,
    StatisticalResult,
)
from market_statistics import compute as compute

from .observations import CalendarSpreadObservationSet
from .query_models import CalendarSpreadQueryError

type QuerySpec = QuantileSpec | IntervalCountSpec | EmpiricalPercentileSpec


class AssociationError(ValueError):
    """Only failures of explicit result-association checks."""


def _require(condition: bool) -> None:
    if not condition:
        raise AssociationError("Statistics result does not match its sample/spec")


def _finite(value: object) -> bool:
    return type(value) is float and isfinite(value)


def _count(value: object) -> bool:
    return type(value) is int and value >= 0


def _validate_association(
    sample: NumericSample, spec: QuerySpec, result: StatisticalResult
) -> None:
    expected = (
        QuantileResult
        if type(spec) is QuantileSpec
        else IntervalCountResult
        if type(spec) is IntervalCountSpec
        else EmpiricalPercentileResult
    )
    _require(type(result) is expected)
    _require(type(result.method) is str and result.method == spec.method)
    _require(type(result.unit) is str and result.unit == sample.unit)
    _require(type(result.sample_count) is int and result.sample_count == sample.sample_count)
    if isinstance(spec, QuantileSpec) and isinstance(result, QuantileResult):
        _require(type(result.estimator) is str and result.estimator == "type7_linear_v1")
        rows = result.points_and_values
        _require(type(rows) is tuple and len(rows) == len(spec.points))
        for point, row in zip(spec.points, rows, strict=True):
            _require(type(row) is tuple and len(row) == 2)
            _require(_finite(row[0]) and row[0] == point and _finite(row[1]))
    elif isinstance(spec, IntervalCountSpec) and isinstance(result, IntervalCountResult):
        _require(type(result.edges) is tuple and result.edges == spec.edges)
        _require(all(_finite(edge) for edge in result.edges))
        _require(type(result.bins) is tuple and len(result.bins) == len(spec.edges) - 1)
        counts = [result.underflow_count, result.overflow_count]
        frequencies = [result.underflow_frequency, result.overflow_frequency]
        for i, bin_ in enumerate(result.bins):
            _require(type(bin_) is IntervalBin)
            _require(_finite(bin_.left) and bin_.left == spec.edges[i])
            _require(_finite(bin_.right) and bin_.right == spec.edges[i + 1])
            _require(bin_.left_inclusive is True)
            _require(bin_.right_inclusive is (i == len(result.bins) - 1))
            counts.append(bin_.count)
            frequencies.append(bin_.frequency)
        _require(all(_count(c) for c in counts) and sum(counts) == sample.sample_count)
        _require(all(_finite(f) and 0 <= f <= 1 for f in frequencies))
    elif isinstance(spec, EmpiricalPercentileSpec) and isinstance(
        result, EmpiricalPercentileResult
    ):
        _require(type(result.estimator) is str and result.estimator == "midrank_v1")
        _require(
            type(result.query_results) is tuple and len(result.query_results) == len(spec.queries)
        )
        for query, ranked in zip(spec.queries, result.query_results, strict=True):
            _require(type(ranked) is EmpiricalPercentileQueryResult)
            _require(_finite(ranked.query) and ranked.query == query)
            counts = [ranked.less_count, ranked.equal_count, ranked.greater_count]
            _require(all(_count(c) for c in counts) and sum(counts) == sample.sample_count)
            _require(_finite(ranked.percentile) and 0 <= ranked.percentile <= 1)


def compute_associated(
    sample: NumericSample,
    spec: QuerySpec,
    collection: CalendarSpreadObservationSet,
    pair: tuple[Slot, Slot],
    trade_date: date | None = None,
) -> StatisticalResult:
    stage = "statistics"
    try:
        result = compute(sample, spec)
        stage = "result_association"
        try:
            _validate_association(sample, spec, result)
        except (AttributeError, TypeError) as exc:
            raise AssociationError("Malformed typed Statistics result") from exc
        return result
    except (StatisticalFailure, AssociationError) as exc:
        raise CalendarSpreadQueryError(
            "statistical_failure",
            stage,
            "market_statistics",
            "Statistics calculation failed"
            if stage == "statistics"
            else "Statistics association failed",
            method=spec.method,
            trade_date=trade_date,
            near_slot=pair[0],
            far_slot=pair[1],
            evidence=collection.prepared_inputs.evidence,
            prepared_inputs=collection.prepared_inputs,
            observation_set=collection,
        ) from exc
