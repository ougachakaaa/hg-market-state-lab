"""Pure, missing-aware index trailing return construction."""

from collections.abc import Sequence
from datetime import date
from math import isfinite
from typing import cast

from data_lake import EnsureResult
from data_lake.datasets.tushare_index_daily import IndexDailyRow

from ...observation.models import (
    EligibleObservation,
    EndpointFact,
    EndpointRole,
    ExcludedObservation,
    FactCoverage,
    MarketFactCoverage,
    MissingDependency,
    ObservationConstructionFailure,
    ObservationDefinition,
    ObservationJobSpec,
    ObservationSet,
    ObservationSpan,
    RequiredFact,
    SampleDependenceContext,
    UnavailableObservation,
)
from .identity import EndpointRequirement, TrailingReturnProvenance, input_provenance
from .inputs import (
    METRIC,
    InvalidPublicInput,
    PreparedInputs,
    job_identity,
    resolve_calendar,
    validate_index,
    validate_job,
)

DEFINITION = ObservationDefinition(
    METRIC,
    "one_scalar_per_end_session",
    "(job_identity, anchor)",
    "close(T) / close(T-H) - 1",
    "decimal_ratio",
    "trading_sessions",
    "SSE",
    "end_session",
    "inclusive",
)


def construct_observations(
    job: ObservationJobSpec, prepared: PreparedInputs
) -> ObservationSet[TrailingReturnProvenance]:
    validate_job(job, check_current_date=False)
    identity = job_identity(job)
    if prepared.job_identity != identity:
        raise ObservationConstructionFailure("Prepared inputs belong to a different fixed question")
    anchors, sessions = resolve_calendar(job, prepared.calendar_slices)
    rows: tuple[IndexDailyRow, ...] = ()
    if anchors:
        item = prepared.index_slice
        if item is None or (
            tuple(item.request.index_codes) != (job.subject,)
            or item.request.start_date != sessions[0]
            or item.request.end_date != anchors[-1]
        ):
            raise InvalidPublicInput("Index request must cover exact L..B range")
        rows = validate_index(item.final_export, item.request, sessions).records
    elif prepared.index_slice is not None:
        raise InvalidPublicInput("Zero-candidate inputs must not contain an Index request")
    by_date = {row.trade_date: row for row in rows}
    expected = tuple((job.subject, day) for day in sessions)
    available = tuple((row.index_code, row.trade_date) for row in rows)
    start = job.historical_sample_window.start_date
    coverage = MarketFactCoverage(
        FactCoverage(expected, available),
        FactCoverage(
            tuple(k for k in expected if k[1] < start), tuple(k for k in available if k[1] < start)
        ),
        FactCoverage(
            tuple(k for k in expected if k[1] >= start),
            tuple(k for k in available if k[1] >= start),
        ),
    )
    eligible: list[EligibleObservation] = []
    unavailable: list[UnavailableObservation] = []
    excluded: list[ExcludedObservation] = []
    endpoints: list[EndpointRequirement] = []
    spans: list[ObservationSpan] = []
    positions = {day: position for position, day in enumerate(sessions)}
    diagnostics = tuple(
        failure
        for attempt in prepared.attempts
        if isinstance(attempt.ensure_result, EnsureResult)
        for failure in attempt.ensure_result.failures
        if prepared.index_slice is not None and attempt.request == prepared.index_slice.request
    )
    for anchor in anchors:
        lookback = sessions[positions[anchor] - job.horizon]
        key = identity, anchor
        missing: list[MissingDependency] = []
        present: list[EndpointFact] = []
        endpoint_days: tuple[tuple[EndpointRole, date], ...] = (
            ("anchor", anchor),
            ("lookback", lookback),
        )
        for endpoint_role, day in endpoint_days:
            fact = RequiredFact("tushare_index_daily", "index_daily", 1, job.subject, day, "close")
            row = by_date.get(day)
            if row is None:
                missing.append(
                    MissingDependency(
                        endpoint_role,
                        fact,
                        "daily_fact_unavailable",
                        "index_slice.final_export",
                        tuple(
                            failure.reason
                            for failure in diagnostics
                            if tuple(cast(Sequence[object], failure.identity)) == fact.daily_key
                        ),
                    )
                )
            else:
                present.append(EndpointFact(endpoint_role, fact, row.close))
        endpoints.append(
            EndpointRequirement(
                anchor, (job.subject, anchor), (job.subject, lookback), tuple(missing)
            )
        )
        spans.append(ObservationSpan(anchor, lookback))
        if missing:
            unavailable.append(UnavailableObservation(key, anchor, tuple(missing), tuple(present)))
            continue
        offending = tuple(fact for fact in present if fact.value <= 0)
        if offending:
            excluded.append(
                ExcludedObservation(
                    key,
                    anchor,
                    "non_positive_close",
                    "Required endpoint close is non-positive",
                    offending,
                )
            )
            continue
        value = by_date[anchor].close / by_date[lookback].close - 1
        if not isfinite(value):
            raise ObservationConstructionFailure(
                f"Non-finite trailing return at {anchor.isoformat()}"
            )
        eligible.append(EligibleObservation(key, anchor, value))
    provenance = input_provenance(job, prepared, expected, available, tuple(endpoints))
    dependence = SampleDependenceContext(
        job.horizon,
        "trading_sessions",
        anchors,
        tuple(spans),
        "Lookback spans may overlap and share endpoint facts, including across Jobs; "
        "no independence, causality or predictive claim is implied.",
    )
    return ObservationSet(
        identity,
        job,
        DEFINITION,
        anchors,
        tuple(eligible),
        tuple(unavailable),
        tuple(excluded),
        coverage,
        provenance,
        dependence,
    )
