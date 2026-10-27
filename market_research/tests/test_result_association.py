"""ASSOC-01 acceptance: observable linkage, original evidence and explicit limits."""

import asyncio
import builtins
import importlib
import io
import os
import socket
import sqlite3
from copy import copy
from dataclasses import FrozenInstanceError, dataclass, replace
from typing import Any

import pytest

from market_research.descriptive.association import (
    AnalysisRequest,
    ResearchAnalysisEvidence,
    ResultAssociationFailure,
    associate,
)
from market_research.descriptive.cases.trailing_return import (
    TrailingReturnProvenance,
    construct_observations,
)
from market_research.descriptive.conversion import SampleBinding, SampleProjection, convert
from market_research.descriptive.observation import (
    JobIdentity,
    ObservationSet,
)
from market_statistics import (
    IntervalCountResult,
    IntervalCountSpec,
    InvalidSample,
    InvalidStatisticalSpec,
    NumericSample,
    QuantileResult,
    QuantileSpec,
    compute,
)
from observation_fixtures import DAYS, execute, job, pure_fixture


def corrupt[T](value: T, /, **changes: Any) -> T:
    """Bypass frozen constructors on a copy to exercise the untrusted boundary."""
    result = copy(value)
    for name, replacement in changes.items():
        object.__setattr__(result, name, replacement)
    return result


def complete() -> ObservationSet[TrailingReturnProvenance]:
    return construct_observations(*pure_fixture())


def quantile_bundle() -> tuple[
    ObservationSet[TrailingReturnProvenance],
    SampleProjection[TrailingReturnProvenance],
    AnalysisRequest,
    QuantileResult,
]:
    source = complete()
    projection = convert(source)
    request = AnalysisRequest("return_quantiles", QuantileSpec([0, 0.5, 1]))
    result = compute(projection.numeric_sample, request.spec)
    assert isinstance(result, QuantileResult)
    return source, projection, request, result


def interval_bundle() -> tuple[
    ObservationSet[TrailingReturnProvenance],
    SampleProjection[TrailingReturnProvenance],
    AnalysisRequest,
    IntervalCountResult,
]:
    source = complete()
    projection = convert(source)
    request = AnalysisRequest(
        "return_distribution",
        IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio"),
    )
    result = compute(projection.numeric_sample, request.spec)
    assert isinstance(result, IntervalCountResult)
    return source, projection, request, result


def test_a_public_component_chain_retains_exact_objects_and_complete_context() -> None:
    fixed, prepared = pure_fixture()
    source = construct_observations(fixed, prepared)
    projection = convert(source)
    request = AnalysisRequest("return_quantiles", QuantileSpec([0, 0.5, 1]))
    result = compute(projection.numeric_sample, request.spec)
    evidence = associate(fixed, source, projection, request, result)
    assert isinstance(evidence, ResearchAnalysisEvidence)
    assert evidence.request is request
    assert evidence.request.spec is request.spec
    assert evidence.statistical_result is result
    assert evidence.projection is projection
    retained = evidence.source_observation_reference
    assert retained is source is projection.binding.source_observation_reference
    assert retained.fixed_job_spec is fixed
    assert retained.job_identity is source.job_identity
    assert retained.observation_definition is source.observation_definition
    assert fixed.subject == "000001.SH"  # Synthetic public fixture, no live CSI1000 claim.
    assert fixed.metric == "trailing_cumulative_return_v1"
    assert dict(fixed.metric_parameters) == {} and fixed.horizon == 2
    assert fixed.historical_sample_window.start_date == DAYS[2]
    assert fixed.historical_sample_window.end_date == DAYS[4]
    definition = retained.observation_definition
    assert definition.formula and definition.unit == "decimal_ratio"
    assert definition.anchor_meaning == "end_session"
    assert definition.horizon_unit == "trading_sessions"
    sample, binding = evidence.projection.numeric_sample, evidence.projection.binding
    assert sample is projection.numeric_sample and binding is projection.binding
    assert sample.values == (0.20999999999999996, 0.0, 0.0)
    assert sample.sample_count == 3 and sample.unit == "decimal_ratio"
    assert binding.ordered_observation_keys == tuple(
        item.observation_key for item in source.eligible_observations
    )
    assert tuple(key[1] for key in binding.ordered_observation_keys) == DAYS[2:5]
    assert binding.coverage_context is source.market_fact_coverage
    assert binding.observation_coverage == 1
    assert binding.unavailable_ratio == binding.excluded_ratio == 0
    assert binding.business_provenance is source.provenance
    provenance = retained.provenance
    assert provenance.prepared_inputs is prepared
    assert provenance.input_profile == "trailing_return_inputs_v2"
    assert provenance.input_fingerprint == (
        "efa5761473299174f411a1cdb35a48bf61e7a5a13a50daaf8a9ac946cdced5ae"
    )
    assert binding.sample_dependence_context is source.sample_dependence_context
    assert binding.sample_dependence_context.spans[0].lookback == DAYS[0]
    assert binding.sample_dependence_context.interpretation
    assert isinstance(result, QuantileResult)
    assert result.method == "quantile" and result.estimator == "type7_linear_v1"
    assert result.points_and_values == ((0.0, 0.0), (0.5, 0.0), (1.0, 121 / 100 - 1))
    assert result.sample_count == sample.sample_count and result.unit == sample.unit


def test_b_c_two_methods_retain_one_projection_with_exact_interval_geometry() -> None:
    source, projection, request, result = quantile_bundle()
    first = associate(source.fixed_job_spec, source, projection, request, result)
    second_request = AnalysisRequest(
        "return_distribution",
        IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio"),
    )
    second_result = compute(projection.numeric_sample, second_request.spec)
    second = associate(source.fixed_job_spec, source, projection, second_request, second_result)
    assert first is not second
    assert first.request.request_id != second.request.request_id
    assert first.request.spec is not second.request.spec
    assert first.statistical_result is not second.statistical_result
    assert first.projection is second.projection is projection
    assert first.source_observation_reference is second.source_observation_reference is source
    assert isinstance(second_result, IntervalCountResult)
    assert second_result.edges == (-0.2, 0.0, 0.2)
    assert tuple(
        (b.left, b.right, b.left_inclusive, b.right_inclusive) for b in second_result.bins
    ) == (
        (-0.2, 0.0, True, False),
        (0.0, 0.2, True, True),
    )
    assert tuple(b.count for b in second_result.bins) == (0, 2)
    assert tuple(b.frequency for b in second_result.bins) == (0.0, 2 / 3)
    assert second_result.underflow_count == 0 and second_result.overflow_count == 1
    assert second_result.underflow_frequency == 0 and second_result.overflow_frequency == 1 / 3
    assert second_result.sample_count == 3 and second_result.unit == "decimal_ratio"


def test_d_partial_population_retains_every_missing_dependency_and_coverage_reference() -> None:
    source = execute(
        job(end=DAYS[5]),
        DAYS,
        dict(
            zip(
                (DAYS[0], DAYS[1], DAYS[3], DAYS[4], DAYS[5]),
                (100.0, 110.0, 90.0, 120.0, 130.0),
                strict=True,
            )
        ),
    )
    projection = convert(source)
    request = AnalysisRequest("partial", QuantileSpec([0, 0.5, 1]))
    result = compute(projection.numeric_sample, request.spec)
    evidence = associate(source.fixed_job_spec, source, projection, request, result)
    binding = evidence.projection.binding
    assert (
        binding.candidate_count,
        binding.eligible_count,
        binding.unavailable_count,
        binding.excluded_count,
    ) == (4, 2, 2, 0)
    assert binding.observation_coverage == binding.unavailable_ratio == 0.5
    assert binding.excluded_ratio == 0
    assert binding.coverage_context is source.market_fact_coverage
    coverage = binding.coverage_context
    assert coverage.overall.ratio == 5 / 6
    assert coverage.warm_up.ratio == 1 and coverage.sample.ratio == 3 / 4
    assert binding.unavailable_records is source.unavailable_observations
    assert tuple(item.anchor for item in binding.unavailable_records) == (DAYS[2], DAYS[4])
    for retained, original in zip(
        binding.unavailable_records, source.unavailable_observations, strict=True
    ):
        assert retained is original
        assert retained.missing_dependencies is original.missing_dependencies
        missing = retained.missing_dependencies[0]
        assert missing.fact.trade_date == DAYS[2]
        assert missing.reason and missing.input_reference and missing.diagnostic_reasons
    provenance = binding.business_provenance
    assert provenance is source.provenance
    prepared = provenance.prepared_inputs
    assert prepared.index_slice is not None
    assert prepared.index_slice.final_export.coverage.successful_units == 5
    assert binding.sample_dependence_context is source.sample_dependence_context


def test_exclusions_and_shared_missing_facts_remain_original_evidence() -> None:
    for source in (
        execute(job(), DAYS[:5], {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[2]: 121.0, DAYS[4]: -1.0}),
        execute(job(end=DAYS[5]), DAYS, {DAYS[0]: 100.0, DAYS[2]: 121.0}),
    ):
        projection = convert(source)
        request = AnalysisRequest("mixed", QuantileSpec([0.5]))
        result = compute(projection.numeric_sample, request.spec)
        evidence = associate(source.fixed_job_spec, source, projection, request, result)
        binding = evidence.projection.binding
        assert binding.exclusion_reasons is source.excluded_observations
        assert binding.unavailable_records is source.unavailable_observations
        assert binding.candidate_count == (
            binding.eligible_count + binding.unavailable_count + binding.excluded_count
        )
        if source.excluded_count:
            assert binding.exclusion_reasons[0].reason_code == "non_positive_close"
            assert binding.exclusion_reasons[0].offending_facts[0].value == -1.0
        else:
            assert any(len(o.missing_dependencies) == 2 for o in binding.unavailable_records)


@pytest.mark.parametrize(
    "changes",
    [
        {"horizon": 3},
        {"historical_sample_window": job(end=DAYS[5]).historical_sample_window},
        {"subject": "another-subject"},
        {"metric": "another_metric_v1"},
        {"metric_parameters": {"new": 1}},
    ],
)
def test_e_changed_job_identity_is_rejected(changes: dict[str, Any]) -> None:
    source, projection, request, result = quantile_bundle()
    wrong = replace(source.fixed_job_spec, **changes)
    with pytest.raises(ResultAssociationFailure, match="Job identity") as error:
        associate(wrong, source, projection, request, result)
    assert error.value.request_id == request.request_id
    assert error.value.job_identity is not None


def test_e_equivalent_job_is_accepted_but_equal_source_objects_are_not_interchangeable() -> None:
    source, projection, request, result = quantile_bundle()
    equivalent = replace(source.fixed_job_spec)
    assert equivalent is not source.fixed_job_spec
    evidence = associate(equivalent, source, projection, request, result)
    assert evidence.source_observation_reference.fixed_job_spec is source.fixed_job_spec
    other_source = complete()
    assert other_source == source and other_source is not source
    with pytest.raises(ResultAssociationFailure, match="different source"):
        associate(equivalent, other_source, projection, request, result)
    assert evidence.source_observation_reference.provenance is source.provenance


@pytest.mark.parametrize(
    "kind",
    [
        "empty_keys",
        "wrong_keys",
        "list_keys",
        "reordered",
        "duplicated",
        "values",
        "count",
        "unit",
        "source",
        "binding",
        "sample",
        "sample_list",
        "sample_int",
        "sample_empty",
        "sample_nonfinite",
        "sample_empty_unit",
        "sample_missing_field",
        "signed_zero",
    ],
)
def test_f_malformed_projection_is_rejected_without_repair(kind: str) -> None:
    source, projection, request, result = quantile_bundle()
    binding, sample = projection.binding, projection.numeric_sample
    keys = binding.ordered_observation_keys
    if kind in {"empty_keys", "wrong_keys", "list_keys", "reordered", "duplicated"}:
        bad_keys: Any = {
            "empty_keys": (),
            "wrong_keys": ("bad",) * 3,
            "list_keys": list(keys),
            "reordered": keys[::-1],
            "duplicated": (keys[0],) * 3,
        }[kind]
        binding = corrupt(binding, ordered_observation_keys=bad_keys)
    elif kind == "source":
        binding = SampleBinding(complete(), keys)
    elif kind == "binding":
        binding = None  # type: ignore[assignment]
    elif kind == "sample":
        sample = None  # type: ignore[assignment]
    elif kind in {"values", "count", "unit", "signed_zero"}:
        values = {
            "values": (1.0, 0.0, 0.0),
            "count": (0.0,),
            "unit": sample.values,
            "signed_zero": (sample.values[0], -0.0, 0.0),
        }[kind]
        sample = NumericSample(values, "wrong" if kind == "unit" else sample.unit)
    elif kind == "sample_missing_field":
        sample = copy(sample)
        object.__delattr__(sample, "values")
    elif kind == "sample_empty_unit":
        sample = corrupt(sample, unit="")
    else:
        bad_values: Any = {
            "sample_list": list(sample.values),
            "sample_int": (0, 0, 0),
            "sample_empty": (),
            "sample_nonfinite": (float("nan"), 0.0, 0.0),
        }[kind]
        sample = corrupt(sample, values=bad_values)
    bad = SampleProjection(sample, binding)
    before = repr(bad) if kind != "sample_missing_field" else None
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, bad, request, result)
    assert error.value.stage == "result_association"
    assert error.value.category == "ResultAssociationFailure"
    assert error.value.reason
    if before is not None:
        assert repr(bad) == before
    else:
        assert not hasattr(bad.numeric_sample, "values")
    assert projection.numeric_sample.values == (121 / 100 - 1, 0.0, 0.0)
    if kind in {"sample_empty", "sample_nonfinite", "sample_empty_unit"}:
        assert isinstance(error.value.__cause__, InvalidSample)


@pytest.mark.parametrize("position", range(5))
@pytest.mark.parametrize("wrong", [None, (), {}, "wrong", object()])
def test_wrong_argument_variants_use_association_failure(position: int, wrong: Any) -> None:
    source, projection, request, result = quantile_bundle()
    arguments: list[Any] = [source.fixed_job_spec, source, projection, request, result]
    arguments[position] = wrong
    with pytest.raises(ResultAssociationFailure) as error:
        associate(*arguments)
    assert error.value.stage == "result_association"
    assert error.value.request_id == (None if position == 3 else request.request_id)
    if position in (0, 1):
        assert error.value.job_identity is None


@pytest.mark.parametrize(
    "changes",
    [
        {"job_identity": ()},
        {"provenance": None},
        {"fixed_job_spec": None},
        {"observation_definition": None},
        {"candidate_anchors": ()},
        {"eligible_observations": ()},
        {"eligible_observations": (None,)},
        {"market_fact_coverage": None},
        {"sample_dependence_context": None},
    ],
)
def test_malformed_source_cannot_produce_evidence(changes: dict[str, Any]) -> None:
    source, projection, request, result = quantile_bundle()
    bad = corrupt(source, **changes)
    with pytest.raises(ResultAssociationFailure):
        associate(
            source.fixed_job_spec,
            bad,
            SampleProjection(
                projection.numeric_sample,
                SampleBinding(bad, projection.binding.ordered_observation_keys),
            ),
            request,
            result,
        )


def test_g_crossed_spec_result_methods_both_fail() -> None:
    source, projection, quantile_request, quantile_result = quantile_bundle()
    interval_request = AnalysisRequest("interval", IntervalCountSpec([0, 1], "decimal_ratio"))
    interval_result = compute(projection.numeric_sample, interval_request.spec)
    for request, result in (
        (quantile_request, interval_result),
        (interval_request, quantile_result),
    ):
        with pytest.raises(ResultAssociationFailure, match="requires"):
            associate(source.fixed_job_spec, source, projection, request, result)


@pytest.mark.parametrize(
    "changes",
    [
        {"points_and_values": ((0.25, 0.0), (0.5, 0.0), (0.75, 0.21))},
        {"points_and_values": ((1.0, 0.21), (0.5, 0.0), (0.0, 0.0))},
        {"points_and_values": ((0.0, 0.0), (0.5, 0.0))},
        {"points_and_values": ((0.0, 0.0), (0.5, 0.0), (0.75, 0.2), (1.0, 0.21))},
        {"points_and_values": ((0.0, 0.0), (0.5, 0.0), (0.5, 0.0))},
        {"points_and_values": ()},
        {"points_and_values": []},
        {"points_and_values": ((0.0,),)},
        {"points_and_values": ((True, 0.0),)},
        {"points_and_values": ((0.0, float("inf")), (0.5, 0.0), (1.0, 0.2))},
        {"points_and_values": ((0.0, float("nan")), (0.5, 0.0), (1.0, 0.2))},
        {"points_and_values": ((0.0, 0), (0.5, 0.0), (1.0, 0.2))},
        {"points_and_values": ((-0.0, 0.0), (0.5, 0.0), (1.0, 0.2))},
        {"estimator": "wrong"},
        {"method": "interval_count"},
        {"sample_count": 2},
        {"sample_count": True},
        {"sample_count": 3.0},
        {"unit": "wrong"},
        {"unit": ""},
        {"unit": None},
    ],
)
def test_h_quantile_parameter_or_payload_mismatch_fails(changes: dict[str, Any]) -> None:
    source, projection, request, result = quantile_bundle()
    if (
        "points_and_values" in changes
        and changes["points_and_values"]
        and (changes["points_and_values"][0][0] == 0.25)
    ):
        request = AnalysisRequest("other-points", QuantileSpec([0.1, 0.5, 0.9]))
    with pytest.raises(ResultAssociationFailure):
        associate(source.fixed_job_spec, source, projection, request, replace(result, **changes))


@pytest.mark.parametrize(
    "field", ["points_and_values", "sample_count", "unit", "method", "estimator"]
)
def test_missing_quantile_public_fields_are_translated_with_cause(field: str) -> None:
    source, projection, request, result = quantile_bundle()
    bad = copy(result)
    object.__delattr__(bad, field)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, request, bad)
    assert isinstance(error.value.__cause__, AttributeError)
    assert field in error.value.reason


@pytest.mark.parametrize(
    "changes",
    [
        {"edges": (-0.2, 0.0, 0.3)},
        {"edges": (0.2, 0.0, -0.2)},
        {"edges": (-0.2, -0.0, 0.2)},
        {"edges": [-0.2, 0.0, 0.2]},
        {"edges": (-0.2, float("nan"), 0.2)},
        {"bins": ()},
        {"bins": (None, None)},
        {"method": "quantile"},
        {"sample_count": 2},
        {"sample_count": False},
        {"sample_count": 3.0},
        {"unit": "wrong"},
        {"underflow_count": -1},
        {"overflow_count": True},
        {"overflow_count": 1.0},
        {"overflow_count": 4},
        {"underflow_frequency": float("inf")},
        {"overflow_frequency": float("nan")},
        {"underflow_frequency": -0.1},
        {"overflow_frequency": 1.1},
        {"overflow_frequency": 0.5},
        {"underflow_frequency": False},
        {"overflow_frequency": None},
        {"underflow_count": 1, "underflow_frequency": 1 / 3},
    ],
)
def test_i_interval_parameters_and_accounting_mismatch_fail(changes: dict[str, Any]) -> None:
    source, projection, request, result = interval_bundle()
    with pytest.raises(ResultAssociationFailure):
        associate(source.fixed_job_spec, source, projection, request, replace(result, **changes))


@pytest.mark.parametrize(
    "index,changes",
    [
        (0, {"left": -0.3}),
        (0, {"right": 0.1}),
        (0, {"right_inclusive": True}),
        (0, {"left_inclusive": False}),
        (0, {"left_inclusive": 1}),
        (1, {"right_inclusive": False}),
        (1, {"right_inclusive": 1}),
        (1, {"left": -0.0}),
        (1, {"count": -1}),
        (1, {"count": True}),
        (1, {"count": 2.0}),
        (1, {"count": 4}),
        (1, {"frequency": 0.5}),
        (1, {"frequency": float("nan")}),
        (1, {"frequency": 0}),
    ],
)
def test_i_bad_interval_geometry_and_bin_fields_fail(index: int, changes: dict[str, Any]) -> None:
    source, projection, request, result = interval_bundle()
    bins = list(result.bins)
    bins[index] = replace(bins[index], **changes)
    with pytest.raises(ResultAssociationFailure):
        associate(
            source.fixed_job_spec, source, projection, request, replace(result, bins=tuple(bins))
        )


@pytest.mark.parametrize(
    "field",
    [
        "edges",
        "bins",
        "underflow_count",
        "overflow_count",
        "underflow_frequency",
        "overflow_frequency",
        "sample_count",
        "unit",
        "method",
    ],
)
def test_missing_interval_public_fields_fail(field: str) -> None:
    source, projection, request, result = interval_bundle()
    bad = copy(result)
    object.__delattr__(bad, field)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, request, bad)
    assert isinstance(error.value.__cause__, AttributeError)


def test_single_final_closed_bin_and_spec_unit_compatibility() -> None:
    source, projection, _, _ = interval_bundle()
    request = AnalysisRequest("single", IntervalCountSpec([0, 1], "decimal_ratio"))
    result = compute(projection.numeric_sample, request.spec)
    evidence = associate(source.fixed_job_spec, source, projection, request, result)
    assert isinstance(evidence.statistical_result, IntervalCountResult)
    assert evidence.statistical_result.bins[0].right_inclusive is True
    incompatible = AnalysisRequest("wrong-unit", IntervalCountSpec([0, 1], "Decimal_Ratio"))
    with pytest.raises(ResultAssociationFailure, match="spec/sample unit"):
        associate(source.fixed_job_spec, source, projection, incompatible, result)


@pytest.mark.parametrize("identity", ["", None, 1, False, (), {}])
def test_j_request_construction_rejects_invalid_identity(identity: Any) -> None:
    with pytest.raises(ValueError, match="request_id"):
        AnalysisRequest(identity, QuantileSpec([0.5]))


@pytest.mark.parametrize("spec", [None, {}, (), "quantile", object()])
def test_j_only_statistics_public_spec_is_accepted(spec: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        AnalysisRequest("request", spec)


def test_j_exact_ids_and_same_spec_can_represent_two_explicit_occurrences() -> None:
    source, projection, _, result = quantile_bundle()
    spec = QuantileSpec([0, 0.5, 1])
    for identity in (" exact ID ", " ", "another-ID"):
        request = AnalysisRequest(identity, spec)
        evidence = associate(source.fixed_job_spec, source, projection, request, result)
        assert evidence.request is request and request.request_id == identity
        assert evidence.request.spec is spec


@pytest.mark.parametrize(
    "changes",
    [
        {"request_id": ""},
        {"request_id": None},
        {"request_id": 2},
        {"spec": None},
        {"spec": {}},
        {"spec": corrupt(QuantileSpec([0.5]), points=(0.9, 0.1))},
        {"spec": corrupt(QuantileSpec([0.5]), method="other")},
    ],
)
def test_j_malformed_request_is_revalidated_at_association(changes: dict[str, Any]) -> None:
    source, projection, request, result = quantile_bundle()
    bad = corrupt(request, **changes)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, bad, result)
    assert error.value.reason
    assert error.value.request_id == (request.request_id if "request_id" not in changes else None)
    if "spec" in changes:
        assert isinstance(error.value.__cause__, InvalidStatisticalSpec)
    else:
        assert isinstance(error.value.__cause__, ValueError)
        assert not isinstance(error.value.__cause__, ResultAssociationFailure)


def test_k_immutability_and_negative_purity_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    source, projection, request, result = quantile_bundle()
    originals = (source, projection, projection.numeric_sample, projection.binding, request, result)
    before = tuple(repr(value) for value in originals)
    parameters = source.fixed_job_spec.metric_parameters

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Association invoked I/O, conversion, construction or computation")

    for name in (
        "market_statistics",
        "market_statistics.api",
        "market_research.descriptive.conversion",
        "market_research.descriptive.conversion.api",
        "market_research.descriptive.cases.trailing_return",
    ):
        module = importlib.import_module(name)
        for operation in ("compute", "convert", "construct_observations", "prepare_inputs"):
            if hasattr(module, operation):
                monkeypatch.setattr(module, operation, forbidden)
    for name in (
        "data_lake.datasets.tushare_index_daily",
        "data_lake.datasets.tushare_trade_calendar",
    ):
        module = importlib.import_module(name)
        monkeypatch.setattr(module, "create_service", forbidden)
        service = getattr(module, "TradeCalendarService", None) or module.IndexDailyService
        for operation in ("coverage", "export", "ensure"):
            monkeypatch.setattr(service, operation, forbidden)
    with monkeypatch.context() as guards:
        for module, operation in (
            (builtins, "open"),
            (io, "open"),
            (os, "open"),
            (socket, "socket"),
            (sqlite3, "connect"),
        ):
            guards.setattr(module, operation, forbidden)
        first = associate(source.fixed_job_spec, source, projection, request, result)
        second = associate(source.fixed_job_spec, source, projection, request, result)
        with pytest.raises(ResultAssociationFailure):
            associate(
                source.fixed_job_spec,
                source,
                projection,
                AnalysisRequest("bad-points", QuantileSpec([0.25])),
                result,
            )
    assert first == second and first is not second
    assert tuple(repr(value) for value in originals) == before
    assert source.fixed_job_spec.metric_parameters is parameters
    with pytest.raises(FrozenInstanceError):
        first.request = request  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        request.request_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.projection = projection  # type: ignore[misc]


def test_l_failure_retains_raw_result_attributable_context_and_readable_reason() -> None:
    source, projection, request, raw_result = quantile_bundle()
    before = repr(raw_result)
    inconsistent = AnalysisRequest("wrong-points", QuantileSpec([0.1, 0.5, 0.9]))
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, inconsistent, raw_result)
    failure = error.value
    assert failure.stage == "result_association" and failure.category == "ResultAssociationFailure"
    assert failure.request_id == "wrong-points" and failure.job_identity == source.job_identity
    assert "points" in failure.reason and failure.reason == str(failure)
    assert failure.__cause__ is None  # Native association failure is not wrapped.
    assert repr(raw_result) == before and raw_result is not None
    evidence = associate(source.fixed_job_spec, source, projection, request, raw_result)
    assert evidence.statistical_result is raw_result


@dataclass(frozen=True)
class OtherProvenance:
    public_fact_reference: str


def test_m_other_scalar_case_and_parameter_name_order_need_no_specialized_association() -> None:
    original = complete()
    fixed = replace(
        original.fixed_job_spec,
        subject="another-series",
        metric="other_scalar_v1",
        metric_parameters={"b": 2, "a": 1},
    )
    definition = replace(
        original.observation_definition,
        metric=fixed.metric,
        formula="other published scalar definition",
        unit=" Opaque Unit ",
    )
    identity: JobIdentity = (
        fixed.metric,
        fixed.subject,
        (("a", 1), ("b", 2)),
        fixed.horizon,
        definition.horizon_unit,
        DAYS[2],
        DAYS[4],
        definition.anchor_meaning,
        definition.bounds,
    )
    source = ObservationSet(
        identity,
        fixed,
        definition,
        original.candidate_anchors,
        tuple(
            replace(item, observation_key=(identity, item.anchor))
            for item in original.eligible_observations
        ),
        (),
        (),
        original.market_fact_coverage,
        OtherProvenance("original typed fact evidence"),
        original.sample_dependence_context,
    )
    projection = convert(source)
    equivalent = replace(fixed, metric_parameters={"a": 1, "b": 2})
    assert equivalent is not fixed
    for spec in (QuantileSpec([0, 1]), IntervalCountSpec([0, 1], " Opaque Unit ")):
        request = AnalysisRequest("other-case", spec)
        result = compute(projection.numeric_sample, spec)
        evidence = associate(equivalent, source, projection, request, result)
        assert type(evidence) is ResearchAnalysisEvidence
        assert evidence.source_observation_reference is source
        assert evidence.source_observation_reference.provenance is source.provenance
        assert evidence.projection.binding.business_provenance is source.provenance
        assert not hasattr(source.provenance, "input_fingerprint")
        assert evidence.projection.numeric_sample.unit == " Opaque Unit "


def test_n_metadata_cannot_attest_hidden_computation_origin_or_numerical_correctness() -> None:
    source, projection, request, _ = quantile_bundle()
    # Unrelated values and same count/unit can even yield an identical numerical payload.
    first = compute(NumericSample([0.0, 0.0, 121 / 100 - 1], "decimal_ratio"), request.spec)
    second = compute(NumericSample([121 / 100 - 1, 0.0, 0.0], "decimal_ratio"), request.spec)
    assert first == second and first is not second
    for result in (first, second):
        assert (
            associate(source.fixed_job_spec, source, projection, request, result).statistical_result
            is result
        )
    # Bounded finite payload checks cannot certify Type 7 interpolation.
    fabricated = QuantileResult(((0.0, 10.0), (0.5, 20.0), (1.0, 30.0)), 3, "decimal_ratio")
    assert (
        associate(source.fixed_job_spec, source, projection, request, fabricated).statistical_result
        is fabricated
    )
    interval = AnalysisRequest("interval", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio"))
    unrelated = compute(NumericSample([-0.1, -0.1, -0.1], "decimal_ratio"), interval.spec)
    # Legal geometry/accounting does not prove that bins contain this source's values.
    assert (
        associate(source.fixed_job_spec, source, projection, interval, unrelated).statistical_result
        is unrelated
    )


def test_public_facade_attributes_use_one_request_model_without_all() -> None:
    facade = importlib.import_module("market_research.descriptive.association")
    for name, value in (
        ("AnalysisRequest", AnalysisRequest),
        ("ResearchAnalysisEvidence", ResearchAnalysisEvidence),
        ("ResultAssociationFailure", ResultAssociationFailure),
        ("associate", associate),
    ):
        assert getattr(facade, name) is value
    assert not hasattr(facade, "__all__")


def test_signed_zero_is_preserved_in_valid_mapping_and_exact_request_parameters() -> None:
    original = complete()
    source = replace(
        original,
        eligible_observations=tuple(
            replace(item, scalar_value=-0.0) for item in original.eligible_observations
        ),
    )
    projection = convert(source)
    for spec in (QuantileSpec([-0.0, 1]), IntervalCountSpec([-0.0, 1], "decimal_ratio")):
        request = AnalysisRequest("signed-zero", spec)
        result = compute(projection.numeric_sample, spec)
        evidence = associate(source.fixed_job_spec, source, projection, request, result)
        assert (
            tuple(value.hex() for value in evidence.projection.numeric_sample.values)
            == ("-0x0.0p+0",) * 3
        )
        assert evidence.statistical_result is result


@pytest.mark.parametrize("changes", [{"horizon": True}, {"horizon": 0}, {"subject": ""}])
def test_invalid_fixed_job_has_no_invented_failure_identity(changes: dict[str, Any]) -> None:
    source, projection, request, result = quantile_bundle()
    fixed = corrupt(source.fixed_job_spec, **changes)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(fixed, source, projection, request, result)
    assert error.value.job_identity is None
    assert error.value.request_id == request.request_id
    assert error.value.__cause__ is not None


@pytest.mark.parametrize("field", ["request_id", "spec"])
def test_missing_request_fields_fail_with_only_legally_identifiable_context(field: str) -> None:
    source, projection, request, result = quantile_bundle()
    bad = copy(request)
    object.__delattr__(bad, field)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, bad, result)
    assert error.value.request_id == (request.request_id if field == "spec" else None)
    assert error.value.job_identity == source.job_identity
    assert isinstance(error.value.__cause__, AttributeError)


@pytest.mark.parametrize("kind", ["list", "missing_bin", "extra_bin", "reordered", "missing_left"])
def test_interval_bin_container_and_required_geometry_fields(kind: str) -> None:
    source, projection, request, result = interval_bundle()
    bins: Any = result.bins
    if kind == "list":
        bins = list(bins)
    elif kind == "missing_bin":
        bins = bins[:-1]
    elif kind == "extra_bin":
        bins = (*bins, bins[-1])
    elif kind == "reordered":
        bins = bins[::-1]
    else:
        first = copy(bins[0])
        object.__delattr__(first, "left")
        bins = (first, bins[1])
    with pytest.raises(ResultAssociationFailure):
        associate(source.fixed_job_spec, source, projection, request, replace(result, bins=bins))


def test_public_statistics_spec_validation_is_used_at_both_request_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, projection, _, result = quantile_bundle()
    statistics = importlib.import_module("market_statistics")
    models = importlib.import_module("market_research.descriptive.association.models")
    seen = []

    def validate(spec: Any) -> None:
        seen.append(spec)
        statistics.validate_spec(spec)

    monkeypatch.setattr(models, "validate_spec", validate)
    spec = QuantileSpec([0, 0.5, 1])
    request = AnalysisRequest("delegated", spec)
    assert len(seen) == 1 and seen[0] is spec
    associate(source.fixed_job_spec, source, projection, request, result)
    assert len(seen) == 2 and seen[1] is spec


@pytest.fixture
def mixed_source() -> ObservationSet[TrailingReturnProvenance]:
    return execute(
        job(), DAYS[:5], {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[2]: 121.0, DAYS[4]: -1.0}
    )


def assert_corrupt_source_fails(
    original: ObservationSet[TrailingReturnProvenance],
    bad: ObservationSet[TrailingReturnProvenance],
) -> ResultAssociationFailure:
    # Convert/compute the valid source first, then bind to the corrupted copy so a
    # different-source guard cannot hide a missing nested-evidence check.
    projection = convert(original)
    request = AnalysisRequest("nested-evidence", QuantileSpec([0.5]))
    result = compute(projection.numeric_sample, request.spec)
    before = repr(original), repr(result)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(
            bad.fixed_job_spec,
            bad,
            SampleProjection(
                projection.numeric_sample,
                SampleBinding(bad, projection.binding.ordered_observation_keys),
            ),
            request,
            result,
        )
    failure = error.value
    assert failure.request_id == request.request_id
    assert failure.job_identity == original.job_identity
    assert failure.stage == "result_association"
    assert failure.category == "ResultAssociationFailure"
    assert not isinstance(failure.__cause__, ResultAssociationFailure)
    assert (repr(original), repr(result)) == before
    return failure


@pytest.mark.parametrize(
    "changes",
    [
        {"endpoint_role": "other"},
        {"endpoint_role": None},
        {"reason": ""},
        {"reason": None},
        {"input_reference": ""},
        {"input_reference": 1},
        {"diagnostic_reasons": ["diagnostic"]},
        {"diagnostic_reasons": (None,)},
        {"diagnostic_reasons": "diagnostic"},
        {"fact": None},
    ],
)
def test_nested_missing_dependency_fields(
    mixed_source: ObservationSet[TrailingReturnProvenance], changes: dict[str, Any]
) -> None:
    record = mixed_source.unavailable_observations[0]
    missing = corrupt(record.missing_dependencies[0], **changes)
    bad_record = corrupt(record, missing_dependencies=(missing,))
    assert_corrupt_source_fails(
        mixed_source, corrupt(mixed_source, unavailable_observations=(bad_record,))
    )


@pytest.mark.parametrize("location", ["missing", "available", "offending"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("dataset", ""),
        ("view", None),
        ("subject", 1),
        ("field", ""),
        ("export_schema_version", True),
        ("export_schema_version", 1.0),
        ("trade_date", "2024-01-08"),
    ],
)
@pytest.mark.parametrize("delete", [False, True])
def test_nested_required_fact_identity_fields(
    mixed_source: ObservationSet[TrailingReturnProvenance],
    location: str,
    field: str,
    value: Any,
    delete: bool,
) -> None:
    record: Any
    if location == "offending":
        record = mixed_source.excluded_observations[0]
        collection, outcomes = "offending_facts", "excluded_observations"
    else:
        record = mixed_source.unavailable_observations[0]
        collection = "missing_dependencies" if location == "missing" else "available_endpoints"
        outcomes = "unavailable_observations"
    endpoint = getattr(record, collection)[0]
    fact = corrupt(endpoint.fact, **{field: value})
    if delete:
        object.__delattr__(fact, field)
    bad_endpoint = corrupt(endpoint, fact=fact)
    bad_record = corrupt(record, **{collection: (bad_endpoint,)})
    failure = assert_corrupt_source_fails(
        mixed_source, corrupt(mixed_source, **{outcomes: (bad_record,)})
    )
    if delete:
        assert isinstance(failure.__cause__, AttributeError)


@pytest.mark.parametrize("location", ["available", "offending"])
@pytest.mark.parametrize(
    "changes",
    [
        {"endpoint_role": "other"},
        {"endpoint_role": None},
        {"fact": None},
        {"value": True},
        {"value": 1},
        {"value": float("nan")},
        {"value": float("inf")},
        {"value": -float("inf")},
    ],
)
def test_nested_endpoint_role_fact_and_binary64_value(
    mixed_source: ObservationSet[TrailingReturnProvenance], location: str, changes: dict[str, Any]
) -> None:
    record: Any
    if location == "available":
        record = mixed_source.unavailable_observations[0]
        collection, outcomes = "available_endpoints", "unavailable_observations"
    else:
        record = mixed_source.excluded_observations[0]
        collection, outcomes = "offending_facts", "excluded_observations"
    endpoint = corrupt(getattr(record, collection)[0], **changes)
    bad_record = corrupt(record, **{collection: (endpoint,)})
    assert_corrupt_source_fails(mixed_source, corrupt(mixed_source, **{outcomes: (bad_record,)}))


@pytest.mark.parametrize(
    "changes",
    [
        {"reason_code": ""},
        {"reason_code": None},
        {"reason": ""},
        {"reason": 1},
        {"offending_facts": []},
        {"offending_facts": ()},
        {"offending_facts": (None,)},
    ],
)
def test_nested_exclusion_reason_and_offending_facts(
    mixed_source: ObservationSet[TrailingReturnProvenance], changes: dict[str, Any]
) -> None:
    record = corrupt(mixed_source.excluded_observations[0], **changes)
    assert_corrupt_source_fails(
        mixed_source, corrupt(mixed_source, excluded_observations=(record,))
    )


@pytest.mark.parametrize("partition", ["overall", "warm_up", "sample"])
@pytest.mark.parametrize("field", ["expected_keys", "available_keys"])
@pytest.mark.parametrize(
    "keys",
    [
        [],
        (("subject",),),
        (("subject", DAYS[0], "extra"),),
        (("", DAYS[0]),),
        ((1, DAYS[0]),),
        (("subject", "2024-01-08"),),
        (["subject", DAYS[0]],),
    ],
)
def test_nested_coverage_key_structure(
    mixed_source: ObservationSet[TrailingReturnProvenance],
    partition: str,
    field: str,
    keys: Any,
) -> None:
    coverage = mixed_source.market_fact_coverage
    part = corrupt(getattr(coverage, partition), **{field: keys})
    bad_coverage = corrupt(coverage, **{partition: part})
    assert_corrupt_source_fails(
        mixed_source, corrupt(mixed_source, market_fact_coverage=bad_coverage)
    )


@pytest.mark.parametrize("kind", ["duplicate", "order", "subset", "partition"])
def test_nested_coverage_existing_conservation_rules(
    mixed_source: ObservationSet[TrailingReturnProvenance], kind: str
) -> None:
    coverage = mixed_source.market_fact_coverage
    part = coverage.overall
    if kind == "duplicate":
        part = corrupt(part, expected_keys=(part.expected_keys[0],) * 2)
    elif kind == "order":
        part = corrupt(part, expected_keys=part.expected_keys[::-1])
    elif kind == "subset":
        part = corrupt(part, available_keys=(("outside", DAYS[0]),))
    else:
        part = corrupt(part, available_keys=())
    assert_corrupt_source_fails(
        mixed_source, corrupt(mixed_source, market_fact_coverage=corrupt(coverage, overall=part))
    )


@pytest.mark.parametrize("operation", ["fixed_identity", "validate_projection", "validate_result"])
@pytest.mark.parametrize("attributed", [False, True])
def test_existing_failure_keeps_identity_cause_and_safe_attribution(
    monkeypatch: pytest.MonkeyPatch, operation: str, attributed: bool
) -> None:
    source, projection, request, result = quantile_bundle()
    cause = ValueError("original validation cause")
    existing = ResultAssociationFailure(
        "already classified",
        request_id="original-request" if attributed else None,
        job_identity=source.job_identity if attributed else None,
    )

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise existing from cause

    api = importlib.import_module("market_research.descriptive.association.api")
    monkeypatch.setattr(api, operation, fail)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, request, result)
    assert error.value is existing
    assert existing.__cause__ is cause
    assert cause.__cause__ is None
    assert existing.reason == "already classified"
    assert existing.stage == "result_association"
    assert existing.category == "ResultAssociationFailure"
    assert existing.request_id == ("original-request" if attributed else request.request_id)
    expected_identity = source.job_identity if attributed or operation != "fixed_identity" else None
    assert existing.job_identity == expected_identity


@pytest.mark.parametrize("kind", ["request", "job"])
def test_existing_failure_does_not_invent_unsafe_attribution(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    source, projection, request, result = quantile_bundle()
    fixed = source.fixed_job_spec
    existing = ResultAssociationFailure("early failure")
    if kind == "request":
        request = corrupt(request, request_id="")
    else:
        fixed = corrupt(fixed, horizon=True)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise existing

    api = importlib.import_module("market_research.descriptive.association.api")
    monkeypatch.setattr(api, "fixed_identity", fail)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(fixed, source, projection, request, result)
    assert error.value is existing and existing.__cause__ is None
    assert existing.request_id == (None if kind == "request" else request.request_id)
    assert existing.job_identity is None


@pytest.mark.parametrize("exception", [AttributeError, TypeError, ValueError, ArithmeticError])
def test_translated_validation_failure_keeps_original_cause(
    monkeypatch: pytest.MonkeyPatch, exception: type[Exception]
) -> None:
    source, projection, request, result = quantile_bundle()
    cause = exception("original malformed field")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise cause

    api = importlib.import_module("market_research.descriptive.association.api")
    monkeypatch.setattr(api, "validate_result", fail)
    with pytest.raises(ResultAssociationFailure) as error:
        associate(source.fixed_job_spec, source, projection, request, result)
    assert error.value.__cause__ is cause
    assert error.value.request_id == request.request_id
    assert error.value.job_identity == source.job_identity
    assert error.value.reason == str(cause)


@pytest.mark.parametrize(
    "exception",
    [RuntimeError, AssertionError, asyncio.CancelledError, KeyboardInterrupt, SystemExit],
)
def test_unexpected_errors_and_cancellation_propagate(
    monkeypatch: pytest.MonkeyPatch, exception: type[BaseException]
) -> None:
    source, projection, request, result = quantile_bundle()
    unexpected = exception("propagate unchanged")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise unexpected

    api = importlib.import_module("market_research.descriptive.association.api")
    monkeypatch.setattr(api, "validate_result", fail)
    with pytest.raises(exception) as error:
        associate(source.fixed_job_spec, source, projection, request, result)
    assert error.value is unexpected and unexpected.__cause__ is None


@pytest.mark.parametrize(
    "field", ["endpoint_role", "fact", "reason", "input_reference", "diagnostic_reasons"]
)
def test_nested_missing_dependency_absent_fields(
    mixed_source: ObservationSet[TrailingReturnProvenance], field: str
) -> None:
    record = mixed_source.unavailable_observations[0]
    missing = copy(record.missing_dependencies[0])
    object.__delattr__(missing, field)
    bad_record = corrupt(record, missing_dependencies=(missing,))
    failure = assert_corrupt_source_fails(
        mixed_source, corrupt(mixed_source, unavailable_observations=(bad_record,))
    )
    assert isinstance(failure.__cause__, AttributeError)


def test_nested_legal_evidence_is_retained_without_case_revalidation(
    mixed_source: ObservationSet[TrailingReturnProvenance],
) -> None:
    record = mixed_source.unavailable_observations[0]
    # Empty diagnostics are legal; finite endpoints need no positivity policy here.
    missing = corrupt(record.missing_dependencies[0], diagnostic_reasons=())
    endpoint = corrupt(record.available_endpoints[0], value=-0.0)
    source = corrupt(
        mixed_source,
        unavailable_observations=(
            corrupt(record, missing_dependencies=(missing,), available_endpoints=(endpoint,)),
        ),
    )
    projection = convert(source)
    request = AnalysisRequest("legal-nested", QuantileSpec([0.5]))
    result = compute(projection.numeric_sample, request.spec)
    evidence = associate(source.fixed_job_spec, source, projection, request, result)
    retained = evidence.source_observation_reference.unavailable_observations[0]
    assert retained.missing_dependencies[0] is missing
    assert retained.available_endpoints[0] is endpoint
    assert endpoint.value.hex() == "-0x0.0p+0"
