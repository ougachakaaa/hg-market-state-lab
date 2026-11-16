"""Explicit one-way projection from the public Research facade."""

from market_research.descriptive.cases.futures_calendar_spread import (
    CurrentAssessment,
    HistoricalRelativeValueResult,
    PairRelativeValueResult,
)

from .schemas import (
    Assessment,
    Distribution,
    HistoricalResponse,
    PairResult,
    SamplePoint,
)


def assessment(value: CurrentAssessment) -> Assessment:
    return Assessment.model_validate(
        {
            "kind": value.kind,
            "distribution_stage": None if value.distribution is None else value.distribution.stage,
            "status": value.status,
            "reason": value.reason,
            "warnings": value.warnings,
            "percentile": value.percentile,
        }
    )


def pair(value: PairRelativeValueResult) -> PairResult:
    # Business owns the all-stages population and ordering. Do not sort, select a
    # financial value or rebuild stage membership here.
    all_stages = next(d for d in value.distributions if d.stage == "all_stages")
    samples = tuple(
        SamplePoint.model_validate(
            {
                "trade_date": point.trade_date,
                "expiry_stage": point.observation.expiry_stage,
                "near": point.observation.near,
                "far": point.observation.far,
                "delta_days": point.observation.delta_days,
                "near_dte_days": point.observation.near_dte_days,
                "metric": point.metric,
            }
        )
        for point in all_stages.samples
    )
    return PairResult.model_validate(
        {
            "near_slot": value.near_slot,
            "far_slot": value.far_slot,
            "samples": samples,
            "distributions": tuple(Distribution.model_validate(d) for d in value.distributions),
            "matching_stage": assessment(value.matching_stage),
            "all_stages": assessment(value.all_stages),
        }
    )


def historical_response(value: HistoricalRelativeValueResult) -> HistoricalResponse:
    return HistoricalResponse.model_validate(
        {
            "case": value.case,
            "definition_version": value.definition_version,
            "request": value.request,
            "metric": value.metric,
            "unit": value.unit,
            "current_day": value.current_day,
            "historical_days": value.historical_days,
            "historical_accounting": value.historical_accounting,
            "pairs": tuple(pair(p) for p in value.pairs),
            "source_context": value.source_context,
        }
    )
