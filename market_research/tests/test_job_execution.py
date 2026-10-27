"""EXEC-01: deterministic public execution with exact component-object retention."""

import asyncio
import importlib
from collections import UserList
from copy import copy
from dataclasses import FrozenInstanceError
from datetime import date, datetime
from typing import Any

import pytest

from data_lake import InvalidRequestError, OperationError
from market_research.descriptive.association import (
    AnalysisRequest,
    ResultAssociationFailure,
    associate,
)
from market_research.descriptive.cases.trailing_return import (
    HistoryInsufficient,
    IncompleteInput,
    InputPreparationFailure,
    InvalidPublicInput,
    PreparedInputs,
    TrailingReturnProvenance,
    UpstreamFailure,
    construct_observations,
    validate_job,
)
from market_research.descriptive.conversion import (
    InvalidObservationSet,
    NoEligibleObservations,
    SampleProjection,
    UnmappableSample,
    convert,
)
from market_research.descriptive.execution import (
    AnalysisOutcome,
    FailureRecord,
    InvalidPlan,
    JobResult,
    execute_job,
)
from market_research.descriptive.observation import (
    DateWindow,
    InvalidObservationRequest,
    ObservationConstructionFailure,
    ObservationJobSpec,
    ObservationSet,
)
from market_statistics import (
    CalculationFailure,
    IntervalCountResult,
    IntervalCountSpec,
    InvalidSample,
    InvalidStatisticalSpec,
    NumericSample,
    QuantileResult,
    QuantileSpec,
    StatisticalResult,
    StatisticalSpec,
    compute,
)
from observation_fixtures import DAYS, CalendarFake, IndexFake, job

API = importlib.import_module("market_research.descriptive.execution.api")
PREPARATION = importlib.import_module(
    "market_research.descriptive.cases.trailing_return.preparation"
)
REQUESTS = (
    AnalysisRequest("quantiles", QuantileSpec([0, 0.5, 1])),
    AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
)


def corrupt[T](value: T, **changes: Any) -> T:
    result = copy(value)
    for name, replacement in changes.items():
        object.__setattr__(result, name, replacement)
    return result


@pytest.fixture(autouse=True)
def services(monkeypatch: pytest.MonkeyPatch) -> tuple[CalendarFake, IndexFake]:
    """Every execution in this module uses public-contract fakes, never default caches."""
    calendar = CalendarFake(DAYS)
    index = IndexFake(
        DAYS, dict(zip(DAYS, (100.0, 110.0, 121.0, 110.0, 121.0, 130.0), strict=True))
    )
    monkeypatch.setattr(PREPARATION, "create_calendar_service", lambda: calendar)
    monkeypatch.setattr(PREPARATION, "create_index_service", lambda: index)
    return calendar, index


def assert_accounting(result: JobResult, requests: tuple[AnalysisRequest, ...] = REQUESTS) -> None:
    assert result.status in {"Success", "Failed"}
    assert result.skip_reason is result.triggering_failed_job_identity is None
    assert len(result.analysis_outcomes) == len(requests)
    for outcome, request in zip(result.analysis_outcomes, requests, strict=True):
        assert outcome.request is request
        assert outcome.request_id == request.request_id
        assert outcome.spec is request.spec
        if outcome.status == "success":
            assert outcome.statistical_result is not None
            assert outcome.associated_evidence is not None
            assert outcome.associated_evidence.statistical_result is outcome.statistical_result
            assert outcome.associated_evidence.request is request
            assert outcome.associated_evidence.projection is result.projection
            assert outcome.failure is outcome.not_attempted_reason is None
        elif outcome.status == "failed":
            assert outcome.failure is not None
            assert any(outcome.failure is f for f in result.failures)
            assert outcome.failure.request_id == request.request_id
            assert outcome.failure.job_identity == result.job_identity
            assert outcome.associated_evidence is outcome.not_attempted_reason is None
        else:
            assert outcome.status == "not_attempted"
            assert outcome.not_attempted_reason == result.failures[0].reason
            assert (
                outcome.statistical_result is outcome.associated_evidence is outcome.failure is None
            )
    assert (result.status == "Success") == all(
        outcome.status == "success" for outcome in result.analysis_outcomes
    )


def test_public_api_complete_success_and_exact_ordered_component_handoffs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed = job()
    original_parameters = fixed.metric_parameters
    requests = list(REQUESTS)
    trace: list[str] = []
    retained: dict[str, Any] = {}
    preparation_operation = API.prepare_inputs

    def prepare(given: ObservationJobSpec) -> PreparedInputs:
        assert given is fixed
        trace.append("prepare")
        retained["prepared"] = preparation_operation(given)
        return retained["prepared"]  # type: ignore[no-any-return]

    def construct(
        given: ObservationJobSpec, prepared: PreparedInputs
    ) -> ObservationSet[TrailingReturnProvenance]:
        assert given is fixed and prepared is retained["prepared"]
        trace.append("construct")
        retained["source"] = construct_observations(given, prepared)
        return retained["source"]  # type: ignore[no-any-return]

    def conversion(source: ObservationSet[TrailingReturnProvenance]) -> Any:
        assert source is retained["source"]
        trace.append("convert")
        retained["projection"] = convert(source)
        return retained["projection"]

    def numerical(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
        position = len(retained.setdefault("raw", []))
        assert sample is retained["projection"].numeric_sample
        assert spec is REQUESTS[position].spec
        trace.append("compute:" + REQUESTS[position].request_id)
        raw = compute(sample, spec)
        retained["raw"].append(raw)
        return raw

    def association(
        given: ObservationJobSpec,
        source: ObservationSet[TrailingReturnProvenance],
        projection: SampleProjection[TrailingReturnProvenance],
        request: AnalysisRequest,
        raw: StatisticalResult,
    ) -> Any:
        assert given is fixed and source is retained["source"]
        assert projection is retained["projection"]
        assert raw is retained["raw"][-1]
        trace.append("associate:" + request.request_id)
        return associate(given, source, projection, request, raw)

    monkeypatch.setattr(API, "prepare_inputs", prepare)
    monkeypatch.setattr(API, "construct_observations", construct)
    monkeypatch.setattr(API, "convert", conversion)
    monkeypatch.setattr(API, "compute", numerical)
    monkeypatch.setattr(API, "associate", association)
    result = execute_job(fixed, requests)
    assert result.status == "Success" and result.failures == ()
    assert_accounting(result)
    assert trace == [
        "prepare",
        "construct",
        "convert",
        "compute:quantiles",
        "associate:quantiles",
        "compute:distribution",
        "associate:distribution",
    ]
    assert result.fixed_job_spec is fixed
    assert result.job_identity == validate_job(fixed)
    assert result.prepared_inputs is retained["prepared"]
    assert result.prepared_inputs is not None
    assert result.input_attempts is result.prepared_inputs.attempts
    assert result.observation_set is retained["source"]
    assert result.projection is retained["projection"]
    assert fixed.metric_parameters is original_parameters
    assert requests == list(REQUESTS)
    assert result.projection is not None
    assert result.projection.numeric_sample.values == (121 / 100 - 1, 0.0, 0.0)
    quantile, distribution = result.analysis_outcomes
    assert isinstance(quantile.statistical_result, QuantileResult)
    assert quantile.statistical_result.points_and_values == (
        (0.0, 0.0),
        (0.5, 0.0),
        (1.0, 121 / 100 - 1),
    )
    assert isinstance(distribution.statistical_result, IntervalCountResult)
    assert tuple(b.count for b in distribution.statistical_result.bins) == (0, 2)
    assert distribution.statistical_result.overflow_count == 1
    for outcome, raw in zip(result.analysis_outcomes, retained["raw"], strict=True):
        assert outcome.statistical_result is raw
        assert outcome.associated_evidence is not None
        assert outcome.associated_evidence.source_observation_reference is result.observation_set


def test_legal_partial_market_facts_can_succeed_with_original_diagnostics_and_coverage(
    services: tuple[CalendarFake, IndexFake],
) -> None:
    _, index = services
    del index.closes[DAYS[2]]
    result = execute_job(job(end=DAYS[5]), REQUESTS)
    assert result.status == "Success" and result.failures == ()
    assert_accounting(result)
    source = result.observation_set
    assert source is not None and result.projection is not None
    assert (source.candidate_count, source.eligible_count, source.unavailable_count) == (4, 2, 2)
    assert source.observation_coverage == source.unavailable_ratio == 0.5
    assert source.market_fact_coverage.overall.ratio == 5 / 6
    binding = result.projection.binding
    assert binding.source_observation_reference is source
    assert binding.unavailable_records is source.unavailable_observations
    assert binding.coverage_context is source.market_fact_coverage
    assert binding.business_provenance is source.provenance
    assert source.provenance.prepared_inputs is result.prepared_inputs
    assert result.prepared_inputs is not None and result.prepared_inputs.index_slice is not None
    assert len(source.provenance.input_fingerprint) == 64
    assert result.input_attempts[-1].final_export is result.prepared_inputs.index_slice.final_export
    assert result.input_attempts[-1].ensure_result is not None
    assert any(
        "not currently published" in dep.diagnostic_reasons
        for row in binding.unavailable_records
        for dep in row.missing_dependencies
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"subject": "000001"},
        {"subject": "000001.sh"},
        {"subject": "000001.SH "},
        {"subject": 1},
        {"subject": ""},
        {"metric": "trailing_cumulative_return_v2"},
        {"metric": ""},
        {"metric_parameters": {"x": 1}},
        {"metric_parameters": None},
        {"horizon": True},
        {"horizon": 0},
        {"horizon": -2},
        {"horizon": 2.0},
        {"historical_sample_window": (DAYS[2], DAYS[4])},
        {"historical_sample_window": DateWindow(date.max, date.max)},
        {"historical_sample_window": corrupt(DateWindow(DAYS[2], DAYS[4]), start_date="2024")},
        {
            "historical_sample_window": corrupt(
                DateWindow(DAYS[2], DAYS[4]), end_date=datetime(2024, 1, 12)
            )
        },
        {"historical_sample_window": corrupt(DateWindow(DAYS[2], DAYS[4]), end_date=DAYS[0])},
    ],
)
def test_preflight_revalidates_corrupted_fixed_jobs_before_upstream_calls(
    changes: dict[str, Any], services: tuple[CalendarFake, IndexFake]
) -> None:
    with pytest.raises(InvalidPlan) as caught:
        execute_job(corrupt(job(), **changes), REQUESTS)
    assert isinstance(caught.value.__cause__, InvalidObservationRequest)
    assert not any(service.calls for service in services)


@pytest.mark.parametrize("fixed", [None, {}, "job", object()])
def test_wrong_job_variant_is_invalid_plan(fixed: Any, services: Any) -> None:
    with pytest.raises(InvalidPlan):
        execute_job(fixed, REQUESTS)
    assert not any(service.calls for service in services)


@pytest.mark.parametrize(
    "requests",
    [
        [],
        (),
        "quantiles",
        b"quantiles",
        bytearray(b"quantiles"),
        {"q": REQUESTS[0]},
        {"q"},
        frozenset({"q"}),
        None,
        1,
        iter(REQUESTS),
        [object()],
        [REQUESTS[0], None],
        [REQUESTS[0], AnalysisRequest("quantiles", REQUESTS[1].spec)],
        [REQUESTS[0], REQUESTS[0]],
        [corrupt(REQUESTS[0], request_id="")],
        [corrupt(REQUESTS[0], request_id=1)],
        [corrupt(REQUESTS[0], spec=object())],
        [corrupt(REQUESTS[0], spec=corrupt(QuantileSpec([0, 1]), points=(1.0, 0.0)))],
        [AnalysisRequest("unit", IntervalCountSpec([-1, 1], "percent"))],
        [AnalysisRequest("unit", IntervalCountSpec([-1, 1], "decimal_ratio "))],
    ],
)
def test_bad_request_sequences_ids_specs_and_units_never_reach_preparation(
    requests: Any, services: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(API, "prepare_inputs", lambda *_: pytest.fail("preflight reached prepare"))
    with pytest.raises(InvalidPlan) as caught:
        execute_job(job(), requests)
    assert caught.value.__cause__ is not None
    assert not any(service.calls for service in services)


def test_invalid_spec_retains_statistics_context() -> None:
    with pytest.raises(InvalidPlan) as caught:
        execute_job(job(), [corrupt(REQUESTS[0], spec=object())])
    assert isinstance(caught.value.__cause__, InvalidStatisticalSpec)


def test_same_specs_with_different_exact_ids_are_not_deduplicated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = (AnalysisRequest(" q ", REQUESTS[0].spec), AnalysisRequest("q", REQUESTS[0].spec))
    calls: list[StatisticalSpec] = []

    def numerical(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
        calls.append(spec)
        return compute(sample, spec)

    monkeypatch.setattr(API, "compute", numerical)
    result = execute_job(job(), UserList(requests))
    assert_accounting(result, requests)
    assert result.status == "Success" and calls == [requests[0].spec, requests[1].spec]
    assert (
        result.analysis_outcomes[0].statistical_result
        is not result.analysis_outcomes[1].statistical_result
    )


@pytest.mark.parametrize("error_type", [InvalidRequestError, OperationError])
def test_preparation_failure_retains_actual_attempts_requests_and_upstream_cause(
    services: tuple[CalendarFake, IndexFake], error_type: type[Exception]
) -> None:
    _, index = services
    cause = error_type("public service rejected legal request")

    def reject(_: Any) -> Any:
        raise cause

    index.transform = reject
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert all(o.status == "not_attempted" for o in result.analysis_outcomes)
    (failure,) = result.failures
    assert failure.failure_stage == "input_preparation"
    assert failure.failure_category == "UpstreamFailure"
    assert isinstance(failure.error, UpstreamFailure) and failure.error.__cause__ is cause
    assert result.input_attempts is failure.error.evidence
    assert len(result.input_attempts) == 3
    assert result.input_attempts[0].final_export is not None
    assert result.input_attempts[-1].request is failure.error.request
    assert result.prepared_inputs is result.observation_set is result.projection is None
    assert failure.request_id is None and failure.job_identity == validate_job(job())
    assert str(cause) in failure.reason


@pytest.mark.parametrize(
    "error",
    [
        InputPreparationFailure("preparation"),
        IncompleteInput("calendar incomplete"),
        InvalidPublicInput("bad export"),
        HistoryInsufficient("short history"),
    ],
)
def test_defined_preparation_categories_are_preserved(
    error: InputPreparationFailure, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_: Any) -> Any:
        raise error

    monkeypatch.setattr(API, "prepare_inputs", fail)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.failures[0].failure_category == error.category
    assert result.failures[0].error is error


@pytest.mark.parametrize(
    "error",
    [ObservationConstructionFailure("formula/accounting"), InvalidPublicInput("bad inputs")],
)
def test_construction_failure_retains_prepared_inputs_and_attempts(
    error: Exception, monkeypatch: pytest.MonkeyPatch
) -> None:
    retained: list[PreparedInputs] = []

    def fail(_: ObservationJobSpec, prepared: PreparedInputs) -> Any:
        retained.append(prepared)
        raise error

    monkeypatch.setattr(API, "construct_observations", fail)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.prepared_inputs is retained[0]
    assert result.input_attempts is retained[0].attempts
    assert len(result.input_attempts) == 3
    assert result.observation_set is result.projection is None
    assert result.failures[0].failure_stage == "observation_construction"
    assert result.failures[0].failure_category == type(error).__name__
    assert result.failures[0].error is error


@pytest.mark.parametrize("population", ["unavailable", "excluded", "no_candidates", "mixed"])
def test_zero_eligible_retains_whole_source_and_never_computes(
    population: str, services: tuple[CalendarFake, IndexFake], monkeypatch: pytest.MonkeyPatch
) -> None:
    calendar, index = services
    if population == "unavailable":
        index.closes.clear()
    elif population == "excluded":
        index.closes = dict.fromkeys(DAYS, 0.0)
    elif population == "mixed":
        index.closes = {DAYS[0]: 0.0, DAYS[2]: 100.0}
    else:
        calendar.opens = ()
    monkeypatch.setattr(API, "compute", lambda *_: pytest.fail("empty sample computed"))
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.status == "Failed" and result.projection is None
    source = result.observation_set
    assert source is not None and source.eligible_count == 0
    assert source.candidate_count == source.unavailable_count + source.excluded_count
    assert source.provenance.prepared_inputs is result.prepared_inputs
    assert result.failures[0].failure_stage == "conversion"
    assert isinstance(result.failures[0].error, NoEligibleObservations)
    assert all(o.status == "not_attempted" for o in result.analysis_outcomes)


@pytest.mark.parametrize("error", [InvalidObservationSet("shape"), UnmappableSample("mapping")])
def test_conversion_failures_keep_exact_source(
    error: Exception, monkeypatch: pytest.MonkeyPatch
) -> None:
    retained: list[ObservationSet[TrailingReturnProvenance]] = []

    def fail(source: ObservationSet[TrailingReturnProvenance]) -> Any:
        retained.append(source)
        raise error

    monkeypatch.setattr(API, "convert", fail)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.observation_set is retained[0]
    assert result.failures[0].error is error
    assert result.failures[0].failure_category == type(error).__name__


@pytest.mark.parametrize(
    "error",
    [
        InvalidSample("sample"),
        InvalidStatisticalSpec("spec"),
        CalculationFailure("quantile", "numerical overflow"),
    ],
)
def test_first_statistics_failure_still_attempts_second_and_keeps_original_category(
    error: Exception, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[NumericSample, StatisticalSpec]] = []

    def numerical(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
        calls.append((sample, spec))
        if len(calls) == 1:
            raise error
        return compute(sample, spec)

    monkeypatch.setattr(API, "compute", numerical)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.status == "Failed"
    assert [o.status for o in result.analysis_outcomes] == ["failed", "success"]
    assert len(calls) == 2 and calls[0][0] is calls[1][0]
    assert result.analysis_outcomes[0].statistical_result is None
    (failure,) = result.failures
    assert failure.error is error and failure.failure_category == type(error).__name__
    assert failure.failure_stage == "analyze" and failure.request_id == "quantiles"


def test_first_association_failure_retains_actual_raw_result_and_later_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_results: list[StatisticalResult] = []
    error = ResultAssociationFailure("forced mismatch")

    def association(*args: Any) -> Any:
        raw_results.append(args[-1])
        if len(raw_results) == 1:
            raise error
        return associate(*args)

    monkeypatch.setattr(API, "associate", association)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.status == "Failed"
    assert [o.status for o in result.analysis_outcomes] == ["failed", "success"]
    assert result.analysis_outcomes[0].statistical_result is raw_results[0]
    assert result.analysis_outcomes[1].statistical_result is raw_results[1]
    (failure,) = result.failures
    assert failure.error is error and failure.failure_category == "ResultAssociationFailure"
    assert failure.failure_stage == "result_association" and failure.request_id == "quantiles"


def test_real_association_rejects_wrong_result_without_losing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong = QuantileResult(((0.0, 1.0),), 3, "decimal_ratio")
    monkeypatch.setattr(API, "compute", lambda *_: wrong)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert len(result.failures) == 2
    assert all(o.statistical_result is wrong for o in result.analysis_outcomes)
    assert all(f.failure_category == "ResultAssociationFailure" for f in result.failures)


def test_multiple_failure_records_keep_occurrence_order_and_request_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = (*REQUESTS, AnalysisRequest("third", REQUESTS[0].spec))
    call = 0

    def numerical(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
        nonlocal call
        call += 1
        if call == 1:
            raise CalculationFailure("quantile", "first")
        return compute(sample, spec)

    def association(*args: Any) -> Any:
        raise ResultAssociationFailure("association")

    monkeypatch.setattr(API, "compute", numerical)
    monkeypatch.setattr(API, "associate", association)
    result = execute_job(job(), requests)
    assert_accounting(result, requests)
    assert call == 3 and len(result.failures) == 3
    assert [(f.request_id, f.failure_stage) for f in result.failures] == [
        ("quantiles", "analyze"),
        ("distribution", "result_association"),
        ("third", "result_association"),
    ]
    assert all(o.status == "failed" for o in result.analysis_outcomes)


@pytest.mark.parametrize(
    "operation,stage",
    [
        ("prepare_inputs", "input_preparation"),
        ("construct_observations", "observation_construction"),
        ("convert", "conversion"),
        ("compute", "analyze"),
        ("associate", "result_association"),
    ],
)
def test_unexpected_exceptions_keep_actual_stage_and_cause(
    operation: str, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = getattr(API, operation)
    error = RuntimeError("unexpected component fault")
    count = 0

    def once(*args: Any) -> Any:
        nonlocal count
        count += 1
        if count == 1:
            raise error
        return original(*args)

    monkeypatch.setattr(API, operation, once)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    (failure,) = result.failures
    assert failure.error is error and failure.failure_category == "ExecutionFailure"
    assert failure.failure_stage == stage and "RuntimeError" in failure.reason
    assert "unexpected component fault" in failure.reason
    if operation in {"compute", "associate"}:
        assert count == 2 and result.analysis_outcomes[1].status == "success"
        assert failure.request_id == "quantiles"
        if operation == "associate":
            assert result.analysis_outcomes[0].statistical_result is not None
    else:
        assert count == 1 and failure.request_id is None
        assert all(o.status == "not_attempted" for o in result.analysis_outcomes)
    if operation != "prepare_inputs":
        assert result.prepared_inputs is not None and result.input_attempts
    if operation not in {"prepare_inputs", "construct_observations"}:
        assert result.observation_set is not None


@pytest.mark.parametrize(
    "operation",
    ["validate_job", "prepare_inputs", "construct_observations", "convert", "compute", "associate"],
)
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, asyncio.CancelledError])
def test_cancellation_and_process_exit_are_never_swallowed(
    operation: str, error_type: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    error = error_type("stop")

    def fail(*_: Any) -> Any:
        raise error

    monkeypatch.setattr(API, operation, fail)
    with pytest.raises(error_type) as caught:
        execute_job(job(), REQUESTS)
    assert caught.value is error


def test_execution_records_and_input_evidence_are_immutable_and_each_run_is_independent() -> None:
    fixed = job()
    first, second = execute_job(fixed, REQUESTS), execute_job(fixed, REQUESTS)
    assert first.job_identity == second.job_identity
    assert first is not second and first.observation_set is not second.observation_set
    assert first.projection is not second.projection
    assert first.projection is not None
    assert isinstance(first.analysis_outcomes, tuple) and isinstance(first.failures, tuple)
    with pytest.raises(FrozenInstanceError):
        first.status = "Skipped"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.analysis_outcomes[0].status = "failed"  # type: ignore[misc]
    failure = FailureRecord(first.job_identity, "analyze", "InvalidSample", "bad", InvalidSample())
    with pytest.raises(FrozenInstanceError):
        failure.reason = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.projection.numeric_sample.unit = "percent"  # type: ignore[misc]
    with pytest.raises(TypeError):
        fixed.metric_parameters["x"] = 1  # type: ignore[index]


def test_legal_exclusions_do_not_fail_a_job_with_eligible_samples(
    services: tuple[CalendarFake, IndexFake],
) -> None:
    _, index = services
    index.closes[DAYS[0]] = 0.0
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.status == "Success" and result.projection is not None
    source = result.observation_set
    assert source is not None
    assert (source.candidate_count, source.eligible_count, source.excluded_count) == (3, 2, 1)
    assert source.market_fact_coverage.overall.ratio == 1.0
    assert result.projection.binding.exclusion_reasons is source.excluded_observations


@pytest.mark.parametrize("operation", ["compute", "associate"])
def test_last_required_analysis_failure_cannot_be_hidden_by_earlier_success(
    operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = getattr(API, operation)
    count = 0

    def fail_last(*args: Any) -> Any:
        nonlocal count
        count += 1
        if count == 2:
            if operation == "compute":
                raise CalculationFailure("interval_count", "last failed")
            raise ResultAssociationFailure("last failed")
        return original(*args)

    monkeypatch.setattr(API, operation, fail_last)
    result = execute_job(job(), REQUESTS)
    assert_accounting(result)
    assert result.status == "Failed"
    assert [o.status for o in result.analysis_outcomes] == ["success", "failed"]
    assert result.failures[0].request_id == "distribution"


def test_preflight_validates_every_exact_spec_before_preparation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace: list[object] = []
    original_validate = API.validate_spec
    original_prepare = API.prepare_inputs

    def validate(spec: StatisticalSpec) -> None:
        trace.append(spec)
        original_validate(spec)

    def prepare(fixed: ObservationJobSpec) -> PreparedInputs:
        trace.append("prepare")
        return original_prepare(fixed)  # type: ignore[no-any-return]

    monkeypatch.setattr(API, "validate_spec", validate)
    monkeypatch.setattr(API, "prepare_inputs", prepare)
    result = execute_job(job(), REQUESTS)
    assert result.status == "Success"
    assert len(trace) == 3
    assert trace[0] is REQUESTS[0].spec and trace[1] is REQUESTS[1].spec
    assert trace[2] == "prepare"


def test_public_case_validator_returns_existing_identity_without_services(
    services: tuple[CalendarFake, IndexFake],
) -> None:
    fixed = job()
    parameters = fixed.metric_parameters
    identity = validate_job(fixed)
    assert identity == (
        fixed.metric,
        fixed.subject,
        (),
        2,
        "trading_sessions",
        DAYS[2],
        DAYS[4],
        "end_session",
        "inclusive",
    )
    assert fixed.metric_parameters is parameters
    assert not any(service.calls for service in services)
    with pytest.raises(InvalidObservationRequest):
        validate_job(corrupt(fixed, subject="000001"))


def test_public_facade_exports_original_attributes_without_all() -> None:
    facade = importlib.import_module("market_research.descriptive.execution")
    assert facade.execute_job is execute_job
    assert facade.InvalidPlan is InvalidPlan
    assert facade.FailureRecord is FailureRecord
    assert facade.AnalysisOutcome is AnalysisOutcome
    assert facade.JobResult is JobResult
    assert not hasattr(facade, "__all__")
    assert not hasattr(facade, "AnalysisRequest")
