"""EXEC-02: whole-plan isolation, real Single Job composition and honest accounting."""

import importlib
from collections import UserList
from copy import copy
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from typing import Any, cast

import pytest

from data_lake.datasets.tushare_index_daily import IndexDailyScope
from market_research.descriptive.association import AnalysisRequest, ResultAssociationFailure
from market_research.descriptive.cases.trailing_return import (
    DEFINITION,
    UpstreamFailure,
    validate_job,
)
from market_research.descriptive.execution import (
    BatchResult,
    InvalidPlan,
    JobResult,
    ResearchPlan,
    execute_batch,
    execute_job,
)
from market_research.descriptive.observation import (
    DateWindow,
    InvalidObservationRequest,
    ObservationJobSpec,
)
from market_statistics import (
    CalculationFailure,
    IntervalCountSpec,
    InvalidStatisticalSpec,
    QuantileSpec,
)
from observation_fixtures import DAYS, CalendarFake, IndexFake

API = importlib.import_module("market_research.descriptive.execution.api")
BATCH = importlib.import_module("market_research.descriptive.execution.batch")
PREPARATION = importlib.import_module(
    "market_research.descriptive.cases.trailing_return.preparation"
)
REQUESTS = (
    AnalysisRequest("quantiles", QuantileSpec([0.1, 0.5, 0.9])),
    AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
)
WINDOWS = (DateWindow(DAYS[2], DAYS[4]), DateWindow(DAYS[3], DAYS[5]))


def corrupt[T](value: T, **changes: Any) -> T:
    result = copy(value)
    for name, replacement in changes.items():
        object.__setattr__(result, name, replacement)
    return result


def plan(**changes: Any) -> ResearchPlan:
    fields: dict[str, Any] = dict(
        metric="trailing_cumulative_return_v1",
        metric_parameters={},
        subjects=["000001.SH", "000300.SH"],
        horizons=[1, 2],
        windows=list(WINDOWS),
        analysis_requests=list(REQUESTS),
        on_job_failure="continue",
    )
    fields.update(changes)
    return ResearchPlan(**fields)


@pytest.fixture(autouse=True)
def services(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Only public-contract service fakes may be created; log every creation."""
    creations: list[str] = []

    def calendar() -> CalendarFake:
        creations.append("calendar")
        return CalendarFake(DAYS)

    def index() -> IndexFake:
        creations.append("index")
        fake = IndexFake(
            DAYS, dict(zip(DAYS, (100.0, 110.0, 121.0, 110.0, 121.0, 130.0), strict=True))
        )
        fake.transform = lambda view: replace(
            view,
            records=tuple(
                replace(
                    row,
                    index_code=cast(IndexDailyScope, view.scope).index_codes[0],
                    symbol=cast(IndexDailyScope, view.scope).index_codes[0].split(".")[0],
                )
                for row in view.records
            ),
        )
        return fake

    monkeypatch.setattr(PREPARATION, "create_calendar_service", calendar)
    monkeypatch.setattr(PREPARATION, "create_index_service", index)
    return creations


def assert_totals(result: BatchResult, expected: tuple[int, int, int, int, str]) -> None:
    assert (
        result.planned_count,
        result.success_count,
        result.failed_count,
        result.skipped_count,
        result.status,
    ) == expected
    assert result.planned_count == len(result.job_results)
    assert result.planned_count == result.success_count + result.failed_count + result.skipped_count


def test_eight_jobs_sixteen_analyses_exact_order_and_original_objects(
    monkeypatch: pytest.MonkeyPatch,
    services: list[str],
) -> None:
    accepted = plan()
    actual: list[JobResult] = []

    def execute(fixed: ObservationJobSpec, requests: Any) -> JobResult:
        assert requests is accepted.analysis_requests
        result = execute_job(fixed, requests)
        actual.append(result)
        return result

    monkeypatch.setattr(BATCH, "execute_job", execute)
    result = execute_batch(accepted)
    assert_totals(result, (8, 8, 0, 0, "success"))
    assert result.plan is accepted
    assert [r.fixed_job_spec for r in result.job_results] == [
        ObservationJobSpec(s, accepted.metric, {}, h, w)
        for s in accepted.subjects
        for h in accepted.horizons
        for w in accepted.windows
    ]
    assert all(a is b for a, b in zip(actual, result.job_results, strict=True))
    assert services == ["calendar", "index"] * 8
    assert sum(len(r.analysis_outcomes) for r in result.job_results) == 16
    for job in result.job_results:
        assert job.job_identity == validate_job(job.fixed_job_spec)
        assert job.prepared_inputs is not None and job.observation_set is not None
        assert job.projection is not None
        assert job.observation_set.observation_definition is DEFINITION
        for outcome, request in zip(job.analysis_outcomes, REQUESTS, strict=True):
            evidence = outcome.associated_evidence
            assert evidence is not None and outcome.request is request
            assert (
                evidence.request is request
                and evidence.statistical_result is outcome.statistical_result
            )
            assert evidence.projection is job.projection
            assert evidence.source_observation_reference is job.observation_set
    assert len({id(r.projection) for r in result.job_results}) == 8


@pytest.mark.parametrize("field", ["subjects", "horizons", "windows", "analysis_requests"])
@pytest.mark.parametrize(
    "bad", [[], "abc", b"abc", bytearray(b"abc"), {1}, {"a": 1}, iter([1]), None]
)
def test_reject_bad_containers_at_construction_and_execution(
    field: str,
    bad: Any,
    services: list[str],
) -> None:
    accepted = plan()
    with pytest.raises(InvalidPlan):
        plan(**{field: bad})
    with pytest.raises(InvalidPlan):
        execute_batch(corrupt(accepted, **{field: bad}))
    assert services == []


@pytest.mark.parametrize(
    "changes",
    [
        {"subjects": ("000001.SH", "000300")},
        {"horizons": (1, True)},
        {"horizons": (1, 0)},
        {"horizons": (1, -1)},
        {"horizons": (1, 2.0)},
        {"windows": (WINDOWS[0], "2024-01-11")},
        {"windows": (WINDOWS[0], corrupt(WINDOWS[1], end_date=datetime(2024, 1, 13)))},
        {"windows": (WINDOWS[0], corrupt(WINDOWS[1], start_date=date(2025, 1, 1)))},
        {"windows": (WINDOWS[0], DateWindow(date(9999, 1, 1), date(9999, 1, 2)))},
        {"subjects": ("000001.SH", "000001.SH")},
        {"horizons": (2, 2)},
        {"windows": (WINDOWS[0], WINDOWS[0])},
        {"analysis_requests": (REQUESTS[0], REQUESTS[0])},
        {"analysis_requests": (corrupt(REQUESTS[0], request_id=""),)},
        {"analysis_requests": (corrupt(REQUESTS[0], request_id=1),)},
        {"analysis_requests": ("quantiles",)},
        {
            "analysis_requests": (
                corrupt(REQUESTS[0], spec=corrupt(QuantileSpec([0.5]), points=(2.0,))),
            )
        },
        {"analysis_requests": (AnalysisRequest("unit", IntervalCountSpec([-1, 1], "percent")),)},
        {"metric": "trailing_cumulative_return_v2"},
        {"metric": None},
        {"metric_parameters": {"unused": []}},
        {"metric_parameters": None},
        {"on_job_failure": "STOP"},
        {"on_job_failure": None},
        {"on_job_failure": True},
    ],
)
def test_all_fields_revalidated_before_io(changes: dict[str, Any], services: list[str]) -> None:
    accepted = plan()
    with pytest.raises(InvalidPlan):
        plan(**changes)
    with pytest.raises(InvalidPlan):
        execute_batch(corrupt(accepted, **changes))
    assert services == []


def test_eighth_case_specific_job_invalid_executes_none(
    monkeypatch: pytest.MonkeyPatch,
    services: list[str],
) -> None:
    accepted = plan()
    validated: list[ObservationJobSpec] = []

    def validate(fixed: ObservationJobSpec) -> Any:
        validated.append(fixed)
        if len(validated) == 8:
            raise InvalidObservationRequest("eighth expanded combination is illegal")
        return validate_job(fixed)

    monkeypatch.setattr(API, "validate_job", validate)
    monkeypatch.setattr(
        BATCH, "execute_job", lambda *args: pytest.fail("executed before full preflight")
    )
    with pytest.raises(InvalidPlan, match="eighth expanded") as caught:
        execute_batch(accepted)
    assert isinstance(caught.value.__cause__, InvalidObservationRequest)
    assert len(validated) == 8 and services == []


def test_spec_exception_chain_and_wrong_plan_type(services: list[str]) -> None:
    accepted = plan()
    invalid = corrupt(REQUESTS[0], spec=object())
    with pytest.raises(InvalidPlan) as caught:
        execute_batch(corrupt(accepted, analysis_requests=(invalid,)))
    assert isinstance(caught.value.__cause__, InvalidStatisticalSpec)
    with pytest.raises(InvalidPlan):
        execute_batch(None)  # type: ignore[arg-type]
    assert services == []


def test_reordered_overlapping_windows_and_identical_specs() -> None:
    first = execute_batch(plan())
    second = execute_batch(
        plan(subjects=["000300.SH", "000001.SH"], horizons=[2, 1], windows=list(reversed(WINDOWS)))
    )
    assert [r.job_identity for r in second.job_results] == [
        r.job_identity for r in reversed(first.job_results)
    ]
    requests = (REQUESTS[0], AnalysisRequest("another ID", REQUESTS[0].spec))
    same = execute_batch(plan(subjects=["000001.SH"], horizons=[2], analysis_requests=requests))
    assert_totals(same, (2, 2, 0, 0, "success"))
    for result in same.job_results:
        assert [o.request_id for o in result.analysis_outcomes] == ["quantiles", "another ID"]
        assert (
            result.analysis_outcomes[0].statistical_result
            is not result.analysis_outcomes[1].statistical_result
        )


def three_jobs(policy: str) -> ResearchPlan:
    return plan(
        subjects=["000001.SH"],
        horizons=[2],
        windows=[DateWindow(day, day) for day in DAYS[2:5]],
        on_job_failure=policy,
    )


@pytest.mark.parametrize(
    "policy,failed_job,expected,statuses,attempted",
    [
        ("continue", 2, (3, 2, 1, 0, "partial_success"), ["Success", "Failed", "Success"], 3),
        ("stop", 2, (3, 1, 1, 1, "partial_success"), ["Success", "Failed", "Skipped"], 2),
        ("stop", 1, (3, 0, 1, 2, "failed"), ["Failed", "Skipped", "Skipped"], 1),
        ("continue", 0, (3, 0, 3, 0, "failed"), ["Failed"] * 3, 3),
    ],
)
def test_continue_stop_and_all_failed_retain_full_attempts(
    monkeypatch: pytest.MonkeyPatch,
    services: list[str],
    policy: str,
    failed_job: int,
    expected: tuple[int, int, int, int, str],
    statuses: list[str],
    attempted: int,
) -> None:
    compute = API.compute
    calls: list[str] = []

    def fail(sample: Any, spec: Any) -> Any:
        calls.append(spec.method)
        if len(calls) % 2 == 1 and (failed_job == 0 or (len(calls) + 1) // 2 == failed_job):
            raise CalculationFailure("quantile", "deterministic batch failure")
        return compute(sample, spec)

    monkeypatch.setattr(API, "compute", fail)
    result = execute_batch(three_jobs(policy))
    assert_totals(result, expected)
    assert [r.status for r in result.job_results] == statuses
    assert services == ["calendar", "index"] * attempted and len(calls) == attempted * 2
    trigger = next(r.job_identity for r in result.job_results if r.status == "Failed")
    for job in result.job_results:
        if job.status == "Skipped":
            assert job.triggering_failed_job_identity == trigger and job.skip_reason
            assert job.prepared_inputs is job.observation_set is job.projection is None
            assert job.failures == () and job.input_attempts == ()
            for outcome in job.analysis_outcomes:
                assert (
                    outcome.status == "not_attempted"
                    and outcome.not_attempted_reason == job.skip_reason
                )
                assert (
                    outcome.statistical_result
                    is outcome.associated_evidence
                    is outcome.failure
                    is None
                )
        elif job.status == "Failed":
            assert [o.status for o in job.analysis_outcomes] == ["failed", "success"]
            assert job.analysis_outcomes[1].associated_evidence is not None
            assert job.observation_set is not None and job.projection is not None
            assert (
                job.projection.binding.source_observation_reference.provenance
                is job.observation_set.provenance
            )
            assert job.observation_set.market_fact_coverage.overall.available_fact_units > 0


def test_association_failure_keeps_raw_result_and_other_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    associate = API.associate

    def fail(*args: Any) -> Any:
        if args[3].request_id == "quantiles":
            raise ResultAssociationFailure("injected association failure")
        return associate(*args)

    monkeypatch.setattr(API, "associate", fail)
    result = execute_batch(three_jobs("stop"))
    assert_totals(result, (3, 0, 1, 2, "failed"))
    job = result.job_results[0]
    assert job.analysis_outcomes[0].statistical_result is not None
    assert job.analysis_outcomes[0].associated_evidence is None
    assert job.analysis_outcomes[1].associated_evidence is not None


def test_plan_snapshots_frozen_results_and_independent_runs() -> None:
    subjects = UserList(["000001.SH"])
    horizons, windows, requests = [2], list(WINDOWS), list(REQUESTS)
    params: dict[str, object] = {}
    accepted = plan(
        subjects=subjects,
        horizons=horizons,
        windows=windows,
        analysis_requests=requests,
        metric_parameters=params,
    )
    subjects.clear()
    horizons.clear()
    windows.clear()
    requests.clear()
    params["new"] = []
    assert accepted.subjects == ("000001.SH",) and accepted.horizons == (2,)
    assert accepted.windows == WINDOWS and accepted.analysis_requests == REQUESTS
    assert dict(accepted.metric_parameters) == {}
    with pytest.raises(TypeError):
        accepted.metric_parameters["new"] = 1  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        accepted.on_job_failure = "stop"  # type: ignore[misc]
    first, second = execute_batch(accepted), execute_batch(accepted)
    with pytest.raises(FrozenInstanceError):
        first.job_results = ()  # type: ignore[misc]
    assert first.job_results[0].job_identity == second.job_results[0].job_identity
    for a, b in zip(first.job_results, second.job_results, strict=True):
        assert (
            a is not b
            and a.projection is not b.projection
            and a.observation_set is not b.observation_set
        )


@pytest.mark.parametrize(
    "change",
    [
        {"status": "Success", "analysis_outcomes": ()},
        {"status": "other"},
        {"job_identity": ()},
        {"fixed_job_spec": None},
        {"skip_reason": "unexpected"},
        {"prepared_inputs": None},
        {"projection": None},
        {"analysis_outcomes": tuple(reversed(REQUESTS))},
    ],
)
def test_reject_executor_contract_violation_without_later_io(
    monkeypatch: pytest.MonkeyPatch,
    services: list[str],
    change: dict[str, Any],
) -> None:
    fixed = ObservationJobSpec("000001.SH", "trailing_cumulative_return_v1", {}, 2, WINDOWS[0])
    actual = execute_job(fixed, REQUESTS)
    services.clear()
    monkeypatch.setattr(BATCH, "execute_job", lambda *args: corrupt(actual, **change))
    with pytest.raises(ValueError):
        execute_batch(plan(subjects=["000001.SH"], horizons=[2]))
    assert services == []


def test_batch_result_rejects_count_order_failed_success_and_bad_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accepted = three_jobs("stop")
    original = API.compute
    calls = 0

    def fail(sample: Any, spec: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise CalculationFailure("quantile", "stop fixture")
        return original(sample, spec)

    monkeypatch.setattr(API, "compute", fail)
    batch = execute_batch(accepted)
    success, failed, skipped = batch.job_results
    bad_skips = [
        corrupt(skipped, prepared_inputs=success.prepared_inputs),
        corrupt(skipped, failures=failed.failures),
        corrupt(skipped, skip_reason=None),
        corrupt(skipped, triggering_failed_job_identity=success.job_identity),
        corrupt(
            skipped, analysis_outcomes=(success.analysis_outcomes[0], skipped.analysis_outcomes[1])
        ),
    ]
    for bad in bad_skips:
        with pytest.raises(ValueError):
            BatchResult(accepted, (success, failed, bad))
    for results in [
        (),
        (success,),
        (failed, success, skipped),
        (success, corrupt(failed, status="Success"), skipped),
        (success, corrupt(failed, failures=()), skipped),
    ]:
        with pytest.raises(ValueError):
            BatchResult(accepted, results)


def test_unexpected_executor_exception_and_cancellation_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for error in (RuntimeError("unexpected executor failure"), KeyboardInterrupt(), SystemExit()):

        def fail(*args: Any, error: BaseException = error) -> Any:
            raise error

        monkeypatch.setattr(BATCH, "execute_job", fail)
        with pytest.raises(type(error)):
            execute_batch(plan())


def test_case_definition_is_public_frozen_and_shared_preflight_uses_it(
    monkeypatch: pytest.MonkeyPatch,
    services: list[str],
) -> None:
    with pytest.raises(FrozenInstanceError):
        DEFINITION.unit = "percent"  # type: ignore[misc]
    monkeypatch.setattr(API, "DEFINITION", replace(DEFINITION, unit="fixture_unit"))
    with pytest.raises(InvalidPlan, match="fixture_unit"):
        plan()
    with pytest.raises(InvalidPlan, match="fixture_unit"):
        execute_job(ObservationJobSpec("000001.SH", DEFINITION.metric, {}, 2, WINDOWS[0]), REQUESTS)
    assert services == []


def test_partial_failed_job_preserves_raw_evidence_coverage_provenance_and_missing_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = IndexFake(
        DAYS, {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[3]: 90.0, DAYS[4]: 120.0, DAYS[5]: 130.0}
    )
    monkeypatch.setattr(PREPARATION, "create_index_service", lambda: index)
    associate = API.associate

    def fail(*args: Any) -> Any:
        if args[3].request_id == "quantiles":
            raise ResultAssociationFailure("injected partial-population association failure")
        return associate(*args)

    monkeypatch.setattr(API, "associate", fail)
    result = execute_batch(
        plan(subjects=["000001.SH"], horizons=[2], windows=[DateWindow(DAYS[2], DAYS[5])])
    )
    assert_totals(result, (1, 0, 1, 0, "failed"))
    job = result.job_results[0]
    source, projection = job.observation_set, job.projection
    assert source is not None and projection is not None and job.prepared_inputs is not None
    assert (source.candidate_count, source.eligible_count, source.unavailable_count) == (4, 2, 2)
    assert source.observation_coverage == 0.5 and source.market_fact_coverage.overall.ratio == 5 / 6
    assert source.provenance.prepared_inputs is job.prepared_inputs
    assert projection.binding.business_provenance is source.provenance
    assert projection.binding.coverage_context is source.market_fact_coverage
    assert projection.binding.unavailable_records is source.unavailable_observations
    assert len(source.provenance.input_fingerprint) == 64
    assert job.analysis_outcomes[0].statistical_result is not None
    evidence = job.analysis_outcomes[1].associated_evidence
    assert evidence is not None and evidence.projection is projection
    assert any(
        dep.diagnostic_reasons
        for row in source.unavailable_observations
        for dep in row.missing_dependencies
    )


@pytest.mark.parametrize("stage", ["input_preparation", "conversion"])
def test_early_failed_job_stops_without_fabricated_analyses(
    monkeypatch: pytest.MonkeyPatch,
    services: list[str],
    stage: str,
) -> None:
    error = UpstreamFailure("deterministic unavailable input service")
    if stage == "input_preparation":

        def prepare(*args: Any) -> Any:
            raise error

        monkeypatch.setattr(API, "prepare_inputs", prepare)
    else:
        monkeypatch.setattr(PREPARATION, "create_index_service", lambda: IndexFake(DAYS, {}))
    result = execute_batch(three_jobs("stop"))
    assert_totals(result, (3, 0, 1, 2, "failed"))
    attempted = result.job_results[0]
    assert attempted.failures[0].failure_stage == stage
    assert all(o.status == "not_attempted" for o in attempted.analysis_outcomes)
    if stage == "input_preparation":
        assert attempted.failures[0].error is error and services == []
    else:
        assert attempted.observation_set is not None
        assert attempted.observation_set.eligible_count == 0
        assert services == ["calendar"]


def test_direct_batch_result_rejects_malformed_success_outcomes_and_request_order() -> None:
    accepted = plan(subjects=["000001.SH"], horizons=[2], windows=[WINDOWS[0]])
    batch = execute_batch(accepted)
    job = batch.job_results[0]
    outcome = job.analysis_outcomes[0]
    bad_outcomes = [
        corrupt(outcome, statistical_result=None),
        corrupt(outcome, associated_evidence=None),
        corrupt(outcome, status="failed"),
        corrupt(outcome, not_attempted_reason="not attempted"),
        corrupt(outcome, request=AnalysisRequest("other", outcome.spec)),
        corrupt(
            outcome, associated_evidence=corrupt(outcome.associated_evidence, request=REQUESTS[1])
        ),
    ]
    for bad in bad_outcomes:
        with pytest.raises(ValueError):
            BatchResult(
                accepted, (corrupt(job, analysis_outcomes=(bad, job.analysis_outcomes[1])),)
            )
    with pytest.raises(ValueError):
        BatchResult(
            accepted, (corrupt(job, analysis_outcomes=tuple(reversed(job.analysis_outcomes))),)
        )
    with pytest.raises(ValueError):
        BatchResult(accepted, [job])  # type: ignore[arg-type]


def test_public_facade_and_required_policy() -> None:
    facade = importlib.import_module("market_research.descriptive.execution")
    for name, expected in (
        ("ResearchPlan", ResearchPlan),
        ("BatchResult", BatchResult),
        ("execute_batch", execute_batch),
        ("execute_job", execute_job),
    ):
        assert getattr(facade, name) is expected
    assert not hasattr(facade, "__all__")
    with pytest.raises(TypeError):
        ResearchPlan(DEFINITION.metric, {}, ["000001.SH"], [2], [WINDOWS[0]], REQUESTS)  # type: ignore[call-arg]
