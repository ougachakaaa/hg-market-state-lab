"""WP4 population, association, calendar boundaries and failure acceptance."""

from dataclasses import replace
from datetime import date
from unittest.mock import patch

import pytest

import market_statistics as stats
from futures_basis_observation_fixtures import AFTER, DAY, Services
from market_research.descriptive.cases.futures_basis import (
    AnalysisRequestError,
    ComparisonRequest,
    DistributionRequest,
    FuturesBasisRequest,
    ObservationOutcome,
    analyze_distribution,
    compare_terms,
    construct_observations,
    discount_runs,
)
from market_research.descriptive.cases.futures_basis.statistics import METRICS, PAIRS


def source(services=None):
    services = services or Services()
    return construct_observations(services.request, services.prepare())


def request(metric="basis_value", slot="M0", start=DAY, end=AFTER):
    return DistributionRequest(
        "explicit-id",
        slot,
        metric,
        start,
        end,
        stats.QuantileSpec([0, 0.5, 1]),
        stats.IntervalCountSpec(
            [-100, 0, 10, 100], "index_points" if metric == "basis_value" else "decimal_ratio"
        ),
    )


@pytest.mark.parametrize("metric", METRICS)
def test_distribution_exact_binding_and_original_result(metric):
    original = source()
    req = request(metric)
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
        wraps=stats.compute,
    ) as compute:
        result = analyze_distribution(original, req)
    expected = tuple(
        r for r in original.slot_days if r.slot == "M0" and r.outcome(metric).status == "eligible"
    )
    assert result.binding == expected
    assert result.source is original and result.request is req
    assert result.count("eligible") == (1 if metric == "annualized_basis_ratio" else 2)
    assert compute.call_args_list[0].args[0].values == tuple(
        r.outcome(metric).value for r in expected
    )
    for call, method in zip(compute.call_args_list, result.methods, strict=True):
        assert call.args[1] is method.spec
        assert method.result.sample_count == len(expected)
    hist = result.methods[2].result
    assert sum(b.count for b in hist.bins) + hist.underflow_count + hist.overflow_count == len(
        expected
    )
    assert sum(
        b.frequency for b in hist.bins
    ) + hist.underflow_frequency + hist.overflow_frequency == pytest.approx(1)
    assert result.count("not_applicable") == (1 if metric == "annualized_basis_ratio" else 0)


@pytest.mark.parametrize("pair", PAIRS)
@pytest.mark.parametrize("metric", METRICS)
def test_all_pairs_use_common_dates(pair, metric):
    original = source()
    req = request(metric)
    result = compare_terms(
        original,
        ComparisonRequest(req.analysis_id, pair, metric, DAY, AFTER, req.quantile, req.histogram),
    )
    expected = tuple(
        d
        for d in (DAY, AFTER)
        if all(
            next(r for r in original.slot_days if r.slot == slot and r.trade_date == d)
            .outcome(metric)
            .status
            == "eligible"
            for slot in pair
        )
    )
    assert result.common_dates == expected
    assert all(
        m.result.sample_count == len(expected) for m in result.left_methods + result.right_methods
    )
    assert len(result.dropped) + len(result.binding) == 2


def test_empty_distribution_and_pair_do_not_call_statistics():
    services = Services()
    services.missing_index()
    services.missing_index(AFTER)
    services.index = replace(
        services.index,
        coverage=replace(services.index.coverage, successful_units=0, missing_units=2),
    )
    original = source(services)
    req = request()
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute"
    ) as compute:
        result = analyze_distribution(original, req)
        pair = compare_terms(
            original,
            ComparisonRequest(
                "pair", ("M0", "Q1"), req.metric, DAY, AFTER, req.quantile, req.histogram
            ),
        )
    compute.assert_not_called()
    assert all(
        m.failure_category == "no_eligible_sample"
        for m in result.methods + pair.left_methods + pair.right_methods
    )
    assert len(pair.dropped) == 2


def test_failure_preserves_category_request_and_other_methods():
    original = source()
    real_compute = stats.compute

    def compute(sample, spec):
        if isinstance(spec, stats.MeanSpec):
            raise stats.CalculationFailure("mean", "injected")
        return real_compute(sample, spec)

    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
        side_effect=compute,
    ):
        result = analyze_distribution(original, request())
    assert result.request.analysis_id == "explicit-id"
    assert result.methods[0].failure_category == "CalculationFailure"
    assert result.methods[1].result is not None
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
        return_value=stats.MeanResult(0, 99, "wrong"),
    ):
        assert (
            analyze_distribution(original, request()).methods[0].failure_category
            == "association_failure"
        )


@pytest.mark.parametrize(
    "change",
    [
        dict(analysis_id=""),
        dict(metric="base"),
        dict(slot="X"),
        dict(end_date=DAY.replace(day=30)),
        dict(histogram=stats.IntervalCountSpec([0, 1], "wrong")),
    ],
)
def test_invalid_requests(change):
    req = replace(request(), **change)
    with pytest.raises(AnalysisRequestError) as exc:
        analyze_distribution(source(), req)
    assert exc.value.request is req


def test_transition_weekend_and_window_censoring():
    services = Services()
    services.futures = replace(
        services.futures, records=tuple(replace(r, close=90.0) for r in services.futures.records)
    )
    original = source(services)
    summary = discount_runs(original, "M0", DAY, AFTER)
    assert not summary.complete
    (run,) = summary.censored
    assert run.observed_trading_sessions == 2
    assert run.start == DAY and run.end == AFTER
    assert run.left_censored and run.right_censored
    assert len(run.transitions) == 1
    assert not discount_runs(source(), "M0", DAY, AFTER).censored


def altered_source(values):
    req = FuturesBasisRequest("IM", date(2024, 10, 14), AFTER)
    original = source(Services(req))
    rows = []
    for row in original.slot_days:
        if row.slot == "M0":
            value = values[original.prepared.candidate_dates.index(row.trade_date)]
            outcome = (
                ObservationOutcome("unavailable", reason="missing")
                if value is None
                else ObservationOutcome("eligible", value, "index_points")
            )
            row = replace(row, observation=replace(row.observation, basis_value=outcome))
        rows.append(row)
    return replace(original, slot_days=tuple(reversed(rows)))


def test_complete_censored_and_gap_not_bridged():
    original = altered_source([0, -1, -1, 2, None, -1])
    summary = discount_runs(original, "M0", original.prepared.request.start_date, AFTER)
    (run,) = summary.complete
    assert run.observed_trading_sessions == 2
    assert not run.left_censored and not run.right_censored
    (fragment,) = summary.censored
    assert fragment.left_boundary == "gap" and fragment.right_boundary == "window"
    result = analyze_distribution(original, request(start=original.prepared.request.start_date))
    assert tuple(r.trade_date for r in result.binding) == tuple(
        sorted(r.trade_date for r in result.binding)
    )
    assert [r.outcome("basis_value").value for r in result.binding] == [0, -1, -1, 2, -1]


@pytest.mark.parametrize("status", ["excluded", "not_applicable", "unavailable"])
def test_each_ineligible_status_interrupts(status):
    original = altered_source([-1, -1, None, -1, -1, 0])
    rows = tuple(
        replace(
            r,
            observation=replace(
                r.observation, basis_value=ObservationOutcome(status, reason="gap")
            ),
        )
        if r.slot == "M0" and r.trade_date == date(2024, 10, 16)
        else r
        for r in original.slot_days
    )
    summary = discount_runs(
        replace(original, slot_days=rows), "M0", original.prepared.request.start_date, AFTER
    )
    assert [r.observed_trading_sessions for r in summary.censored] == [2, 2]
    assert not summary.complete


def test_disjoint_nonempty_sides_have_no_common_sample():
    original = source()
    rows = tuple(
        replace(
            r,
            observation=replace(
                r.observation, basis_value=ObservationOutcome("unavailable", reason="synthetic")
            ),
        )
        if (r.slot, r.trade_date) in (("M0", DAY), ("M1", AFTER))
        else r
        for r in original.slot_days
    )
    original = replace(original, slot_days=rows)
    req = request()
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute"
    ) as compute:
        result = compare_terms(
            original,
            ComparisonRequest(
                "disjoint", ("M0", "M1"), req.metric, DAY, AFTER, req.quantile, req.histogram
            ),
        )
    compute.assert_not_called()
    assert not result.binding and len(result.dropped) == 2
    assert {r.outcome("basis_value").status for a in result.dropped for r in a} == {
        "eligible",
        "unavailable",
    }


def test_original_statistical_objects_and_inputs_are_unchanged():
    original = source()
    req = request()
    snapshot = repr((original, req))
    returned = []
    real_compute = stats.compute

    def compute(sample, spec):
        value = real_compute(sample, spec)
        returned.append(value)
        return value

    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
        side_effect=compute,
    ):
        result = analyze_distribution(original, req)
    assert all(m.result is r for m, r in zip(result.methods, returned, strict=True))
    assert repr((original, req)) == snapshot
    assert all(
        r is next(x for x in original.slot_days if x.identity == r.identity) for r in result.binding
    )
    assert all(
        r.observation.input_fingerprint == original.prepared.input_fingerprint
        for r in result.binding
    )


def test_empty_calendar_and_narrow_window_do_not_bridge():
    original = altered_source([-1, -1, -1, -1, -1, -1])
    summary = discount_runs(original, "M0", DAY, DAY)
    (run,) = summary.censored
    assert run.observed_trading_sessions == 1
    assert run.left_censored and run.right_censored
    req = request(start=date(2024, 10, 19), end=date(2024, 10, 20))
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute"
    ) as compute:
        result = analyze_distribution(original, req)
    compute.assert_not_called()
    assert not result.candidates
