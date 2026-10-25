"""Behavioral acceptance for calendar-based populations and three-way outcomes."""

from dataclasses import replace
from datetime import date
from sys import float_info

import pytest

from market_research.descriptive.cases.trailing_return import (
    HistoryInsufficient,
    InvalidPublicInput,
    construct_observations,
    prepare_inputs,
)
from market_research.descriptive.observation import (
    EligibleObservation,
    ObservationConstructionFailure,
)
from observation_fixtures import CODE, DAYS, CalendarFake, IndexFake, execute, job, pure_fixture


def test_a_complete_binary64_returns_and_distinct_equal_value_keys() -> None:
    spec, prepared = pure_fixture()
    result = construct_observations(spec, prepared)
    assert result.fixed_job_spec is spec
    assert result.provenance.prepared_inputs is prepared
    assert result.candidate_anchors == DAYS[2:5]
    assert [o.scalar_value for o in result.eligible_observations] == [121 / 100 - 1, 0.0, 0.0]
    assert len({o.observation_key for o in result.eligible_observations}) == 3
    assert (
        result.candidate_count,
        result.eligible_count,
        result.unavailable_count,
        result.excluded_count,
    ) == (3, 3, 0, 0)
    assert result.observation_coverage == 1
    assert result.unavailable_ratio == result.excluded_ratio == 0
    assert result.observation_definition.unit == "decimal_ratio"
    assert result.market_fact_coverage.overall.ratio == 1
    assert result.sample_dependence_context.horizon == 2
    assert [(span.anchor, span.lookback) for span in result.sample_dependence_context.spans] == [
        (DAYS[2], DAYS[0]),
        (DAYS[3], DAYS[1]),
        (DAYS[4], DAYS[2]),
    ]


def test_b_missing_intermediate_price_never_compresses_horizon() -> None:
    closes = {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[3]: 90.0, DAYS[4]: 120.0, DAYS[5]: 130.0}
    result = execute(job(end=DAYS[5]), DAYS, closes)
    assert [(o.anchor, o.scalar_value) for o in result.eligible_observations] == [
        (DAYS[3], 90 / 110 - 1),
        (DAYS[5], 130 / 90 - 1),
    ]
    assert [
        (
            o.anchor,
            o.missing_dependencies[0].endpoint_role,
            o.missing_dependencies[0].fact.trade_date,
        )
        for o in result.unavailable_observations
    ] == [(DAYS[2], "anchor", DAYS[2]), (DAYS[4], "lookback", DAYS[2])]
    assert result.candidate_count == 4
    assert result.eligible_count == result.unavailable_count == 2
    assert result.excluded_count == 0
    assert result.observation_coverage == result.unavailable_ratio == 0.5
    fact = result.market_fact_coverage
    assert fact.overall.ratio == 5 / 6
    assert fact.warm_up.ratio == 1
    assert fact.sample.ratio == 3 / 4
    assert fact.overall.absent_keys == ((CODE, DAYS[2]),)
    for observation in result.unavailable_observations:
        dep = observation.missing_dependencies[0]
        assert dep.reason == "daily_fact_unavailable"
        assert dep.input_reference == "index_slice.final_export"
        assert dep.diagnostic_reasons == ("not currently published",)


def test_c_weekends_and_holidays_are_not_candidates_or_missing_facts() -> None:
    opens = (date(2024, 2, 7), date(2024, 2, 8), date(2024, 2, 19), date(2024, 2, 20))
    result = execute(
        job(opens[2], opens[3]), opens, dict(zip(opens, (100.0, 110.0, 120.0, 130.0), strict=True))
    )
    assert result.candidate_anchors == opens[2:]
    assert [(s.anchor, s.lookback) for s in result.sample_dependence_context.spans] == [
        (opens[2], opens[0]),
        (opens[3], opens[1]),
    ]
    assert result.market_fact_coverage.overall.expected_fact_units == 4
    assert result.market_fact_coverage.overall.ratio == 1
    assert result.eligible_count == 2


def test_d_missing_warm_up_preserves_other_eligible_candidates() -> None:
    result = execute(job(), DAYS[:5], {day: 100.0 for day in DAYS[1:5]})
    assert [o.anchor for o in result.unavailable_observations] == [DAYS[2]]
    assert [o.anchor for o in result.eligible_observations] == list(DAYS[3:5])
    assert result.market_fact_coverage.warm_up.ratio == 0.5
    assert result.market_fact_coverage.sample.ratio == 1


def test_f_all_unavailable_is_a_valid_zero_eligible_set() -> None:
    result = execute(job(), DAYS[:5], {})
    assert (result.candidate_count, result.eligible_count, result.unavailable_count) == (3, 0, 3)
    assert result.observation_coverage == 0
    assert result.unavailable_ratio == 1
    assert result.excluded_ratio == 0
    assert result.market_fact_coverage.overall.ratio == 0
    assert result.provenance.prepared_inputs.index_slice is not None
    assert len(result.provenance.absent_daily_keys) == 5


def test_h_missing_precedes_non_positive_with_available_endpoint_retained() -> None:
    result = execute(job(DAYS[2], DAYS[2]), DAYS[:3], {DAYS[0]: -2.0})
    (outcome,) = result.unavailable_observations
    assert outcome.missing_dependencies[0].endpoint_role == "anchor"
    assert outcome.available_endpoints[0].endpoint_role == "lookback"
    assert outcome.available_endpoints[0].value == -2.0
    assert result.excluded_count == 0
    assert result.market_fact_coverage.overall.available_fact_units == 1


def test_i_two_missing_endpoints_one_outcome_in_endpoint_order() -> None:
    result = execute(job(DAYS[2], DAYS[2]), DAYS[:3], {})
    (outcome,) = result.unavailable_observations
    assert [dep.endpoint_role for dep in outcome.missing_dependencies] == ["anchor", "lookback"]
    assert [dep.fact.daily_key for dep in outcome.missing_dependencies] == [
        (CODE, DAYS[2]),
        (CODE, DAYS[0]),
    ]
    assert result.candidate_count == result.unavailable_count == 1


def test_j_zero_candidates_retains_calendar_no_index_request() -> None:
    calendar, index = CalendarFake(()), IndexFake((), {})
    spec = job()
    prepared = prepare_inputs(spec, calendar_service=calendar, index_service=index)
    result = construct_observations(spec, prepared)
    assert index.calls == []
    assert len(calendar.calls) == 1
    assert result.candidate_count == result.eligible_count == 0
    assert result.observation_coverage is result.unavailable_ratio is result.excluded_ratio is None
    assert result.market_fact_coverage.overall.ratio is None
    assert result.market_fact_coverage.warm_up.ratio is None
    assert result.provenance.prepared_inputs.index_slice is None
    assert len(result.provenance.prepared_inputs.calendar_slices) == 1


@pytest.mark.parametrize("closes", [(0.0, -1.0), (-0.0, 10.0), (10.0, -3.0)])
def test_available_non_positive_endpoints_are_excluded_and_still_available(
    closes: tuple[float, float],
) -> None:
    result = execute(
        job(DAYS[2], DAYS[2]), DAYS[:3], {DAYS[0]: closes[0], DAYS[1]: 100.0, DAYS[2]: closes[1]}
    )
    (outcome,) = result.excluded_observations
    assert outcome.reason_code == "non_positive_close"
    assert [(f.endpoint_role, f.value) for f in outcome.offending_facts] == [
        (role, value)
        for role, value in (("anchor", closes[1]), ("lookback", closes[0]))
        if value <= 0
    ]
    assert result.observation_coverage == 0
    assert result.excluded_ratio == 1
    assert result.market_fact_coverage.overall.ratio == 1


def test_intermediate_missing_fact_affects_coverage_not_endpoint_computability() -> None:
    result = execute(job(DAYS[2], DAYS[2]), DAYS[:3], {DAYS[0]: 10.0, DAYS[2]: 11.0})
    assert result.eligible_count == 1
    assert result.market_fact_coverage.overall.ratio == 2 / 3
    assert result.observation_coverage == 1


def test_mixed_population_conserves_all_three_disjoint_outcomes() -> None:
    result = execute(
        job(end=DAYS[5]),
        DAYS,
        {
            DAYS[0]: 100.0,
            DAYS[1]: 0.0,
            DAYS[3]: 90.0,
            DAYS[4]: 120.0,
            DAYS[5]: 130.0,
        },
    )
    assert (
        result.candidate_count,
        result.eligible_count,
        result.unavailable_count,
        result.excluded_count,
    ) == (4, 1, 2, 1)
    assert (result.observation_coverage, result.unavailable_ratio, result.excluded_ratio) == (
        0.25,
        0.5,
        0.25,
    )
    assert result.eligible_observations[0].anchor == DAYS[5]
    assert result.excluded_observations[0].anchor == DAYS[3]
    assert result.market_fact_coverage.overall.ratio == 5 / 6


def test_binary64_overflow_is_construction_failure() -> None:
    with pytest.raises(ObservationConstructionFailure, match="Non-finite"):
        execute(
            job(DAYS[2], DAYS[2]),
            DAYS[:3],
            {
                DAYS[0]: float.fromhex("0x0.0000000000001p-1022"),
                DAYS[1]: 100.0,
                DAYS[2]: float_info.max,
            },
        )


@pytest.mark.parametrize(
    "anchor,horizon,opens",
    [
        (date.min, 1, (date.min,)),
        (date(1, 1, 3), 3, (date(1, 1, 1), date(1, 1, 2), date(1, 1, 3))),
    ],
)
def test_date_min_history_exhaustion(anchor: date, horizon: int, opens: tuple[date, ...]) -> None:
    calendar, index = CalendarFake(opens), IndexFake(opens, {})
    with pytest.raises(HistoryInsufficient) as caught:
        prepare_inputs(job(anchor, anchor, horizon), calendar_service=calendar, index_service=index)
    assert caught.value.stage == "input_preparation"
    assert caught.value.evidence
    assert index.calls == []
    assert len(calendar.calls) == (1 if anchor == date.min else 2)


def test_backward_discovery_is_adjacent_and_doubles_natural_day_blocks() -> None:
    anchor = date(2024, 1, 15)
    opens = (date(2024, 1, 11), date(2024, 1, 12), anchor)
    calendar = CalendarFake(opens)
    prepare_inputs(
        job(anchor, anchor),
        calendar_service=calendar,
        index_service=IndexFake(opens, {day: 100.0 for day in opens}),
    )
    assert [(r.start_date, r.end_date) for op, r in calendar.calls] == [
        (anchor, anchor),
        (date(2024, 1, 13), date(2024, 1, 14)),
        (date(2024, 1, 9), date(2024, 1, 12)),
    ]


def test_prepared_question_and_final_index_range_cannot_be_rebound() -> None:
    spec, inputs = pure_fixture()
    with pytest.raises(ObservationConstructionFailure, match="different fixed question"):
        construct_observations(replace(spec, horizon=1), inputs)
    assert inputs.index_slice is not None
    changed = replace(inputs.index_slice.request, end_date=DAYS[3])
    with pytest.raises(InvalidPublicInput, match="L..B"):
        construct_observations(
            spec, replace(inputs, index_slice=replace(inputs.index_slice, request=changed))
        )


def test_observation_set_rejects_extra_duplicate_unaccounted_and_nonfinite_outcomes() -> None:
    spec, inputs = pure_fixture()
    result = construct_observations(spec, inputs)
    with pytest.raises(ObservationConstructionFailure, match="fixed request"):
        replace(result, fixed_job_spec=replace(spec, horizon=1))
    with pytest.raises(ObservationConstructionFailure):
        replace(result, eligible_observations=result.eligible_observations[:-1])
    with pytest.raises(ObservationConstructionFailure):
        replace(result, eligible_observations=result.eligible_observations * 2)
    with pytest.raises(ObservationConstructionFailure):
        replace(
            result,
            eligible_observations=(
                EligibleObservation((result.job_identity, DAYS[2]), DAYS[2], float("inf")),
                *result.eligible_observations[1:],
            ),
        )
