"""CONV-01 deterministic scalar projection acceptance using public Observation fixtures."""

import builtins
import importlib
import socket
from copy import copy
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import date
from typing import Any

import pytest

from market_research.descriptive.cases.trailing_return import (
    TrailingReturnProvenance,
    construct_observations,
)
from market_research.descriptive.conversion import (
    InvalidObservationSet,
    NoEligibleObservations,
    SampleBinding,
    SampleProjection,
    UnmappableSample,
    convert,
)
from market_research.descriptive.observation import ObservationSet
from market_statistics import (
    IntervalCountResult,
    IntervalCountSpec,
    InvalidSample,
    QuantileResult,
    QuantileSpec,
    compute,
)
from observation_fixtures import DAYS, execute, job, pure_fixture


def complete() -> ObservationSet[TrailingReturnProvenance]:
    return construct_observations(*pure_fixture())


def corrupt[T](value: T, **changes: Any) -> T:
    """Bypass frozen dataclass construction on a separate instance, never the source."""
    result = copy(value)
    for name, replacement in changes.items():
        object.__setattr__(result, name, replacement)
    return result


def test_a_complete_exact_mapping_duplicate_zeros_and_source_identity() -> None:
    source = complete()
    projection = convert(source)
    sample, binding = projection.numeric_sample, projection.binding
    assert isinstance(projection, SampleProjection)
    assert isinstance(binding, SampleBinding)
    assert sample.values == (121 / 100 - 1, 110 / 110 - 1, 121 / 121 - 1)
    assert tuple(v.hex() for v in sample.values) == tuple(
        o.scalar_value.hex() for o in source.eligible_observations
    )
    assert binding.ordered_observation_keys == tuple(
        o.observation_key for o in source.eligible_observations
    )
    assert len(set(binding.ordered_observation_keys)) == sample.sample_count == 3
    assert sample.unit == source.observation_definition.unit == "decimal_ratio"
    assert (
        binding.candidate_count,
        binding.eligible_count,
        binding.unavailable_count,
        binding.excluded_count,
    ) == (3, 3, 0, 0)
    assert binding.unavailable_records == binding.exclusion_reasons == ()
    assert binding.source_observation_reference is source
    assert binding.source_observation_reference.fixed_job_spec is source.fixed_job_spec
    assert binding.source_observation_reference.job_identity is source.job_identity
    assert (
        binding.source_observation_reference.observation_definition is source.observation_definition
    )
    assert binding.business_provenance is source.provenance
    assert binding.business_provenance.input_fingerprint == source.provenance.input_fingerprint
    assert binding.business_provenance.input_profile == "trailing_return_inputs_v2"
    assert binding.coverage_context is source.market_fact_coverage
    assert binding.observation_coverage == 1
    assert binding.unavailable_ratio == binding.excluded_ratio == 0
    assert binding.sample_dependence_context is source.sample_dependence_context
    assert binding.sample_dependence_context.horizon == 2
    assert binding.sample_dependence_context.spans[0].lookback == DAYS[0]
    assert binding.sample_dependence_context.spans[-1].anchor == DAYS[4]
    assert binding.sample_dependence_context.interpretation


def test_b_missing_intermediate_full_coverage_and_dependency_evidence() -> None:
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
    binding = projection.binding
    assert projection.numeric_sample.values == (90 / 110 - 1, 130 / 90 - 1)
    assert tuple(key[1] for key in binding.ordered_observation_keys) == (DAYS[3], DAYS[5])
    assert (
        binding.candidate_count,
        binding.eligible_count,
        binding.unavailable_count,
        binding.excluded_count,
    ) == (4, 2, 2, 0)
    assert binding.observation_coverage == binding.unavailable_ratio == 2 / 4
    assert binding.excluded_ratio == 0
    assert binding.coverage_context.overall.ratio == 5 / 6
    assert binding.coverage_context.warm_up.ratio == 1
    assert binding.coverage_context.sample.ratio == 3 / 4
    assert binding.unavailable_records is source.unavailable_observations
    assert tuple(o.anchor for o in binding.unavailable_records) == (DAYS[2], DAYS[4])
    for retained, original in zip(
        binding.unavailable_records, source.unavailable_observations, strict=True
    ):
        assert retained is original
        assert retained.missing_dependencies is original.missing_dependencies
        dependency = retained.missing_dependencies[0]
        assert dependency.fact.trade_date == DAYS[2]
        assert dependency.reason == "daily_fact_unavailable"
        assert dependency.input_reference
        assert dependency.diagnostic_reasons
    prepared = binding.business_provenance.prepared_inputs
    assert prepared is source.provenance.prepared_inputs
    assert prepared.index_slice is not None
    assert source.provenance.prepared_inputs.index_slice is not None
    assert (
        prepared.index_slice.final_export.coverage
        is source.provenance.prepared_inputs.index_slice.final_export.coverage
    )


def test_c_two_equal_values_keep_distinct_keys_and_signed_zero() -> None:
    source = complete()
    eligible = tuple(replace(o, scalar_value=-0.0) for o in source.eligible_observations)
    source = replace(source, eligible_observations=eligible)
    projection = convert(source)
    assert tuple(v.hex() for v in projection.numeric_sample.values) == ("-0x0.0p+0",) * 3
    assert len(set(projection.binding.ordered_observation_keys)) == 3


def test_multiple_missing_dependencies_and_original_diagnostics_are_retained() -> None:
    source = execute(job(end=DAYS[5]), DAYS, {DAYS[0]: 100.0, DAYS[2]: 121.0})
    binding = convert(source).binding
    assert any(len(o.missing_dependencies) == 2 for o in binding.unavailable_records)
    for retained, original in zip(
        binding.unavailable_records, source.unavailable_observations, strict=True
    ):
        assert retained is original
        for missing in retained.missing_dependencies:
            assert missing.fact.dataset == "tushare_index_daily"
            assert missing.fact.view == "index_daily"
            assert missing.fact.export_schema_version == 1
            assert missing.fact.field == "close"
            assert missing.input_reference and missing.reason and missing.diagnostic_reasons


def test_d_mixed_population_keeps_exclusion_facts_without_second_screen() -> None:
    source = execute(
        job(), DAYS[:5], {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[2]: 121.0, DAYS[4]: -1.0}
    )
    projection = convert(source)
    binding = projection.binding
    assert projection.numeric_sample.values == (121 / 100 - 1,)
    assert (
        binding.candidate_count
        == binding.eligible_count + binding.unavailable_count + binding.excluded_count
    )
    assert (
        binding.candidate_count,
        binding.eligible_count,
        binding.unavailable_count,
        binding.excluded_count,
    ) == (3, 1, 1, 1)
    assert binding.exclusion_reasons is source.excluded_observations
    excluded = binding.exclusion_reasons[0]
    assert excluded.reason_code == "non_positive_close"
    assert excluded.reason and excluded.offending_facts[0].value == -1.0


@pytest.mark.parametrize(
    "closes", [{}, {day: -1.0 for day in DAYS}, {DAYS[0]: -1.0, DAYS[2]: -1.0}]
)
def test_e_zero_eligible_unavailable_excluded_and_mixture(closes: dict[date, float]) -> None:
    source = execute(job(), DAYS[:5], closes)
    before = repr(source)
    with pytest.raises(NoEligibleObservations) as error:
        convert(source)
    assert error.value.stage == "conversion"
    assert error.value.category == "NoEligibleObservations"
    assert str(error.value) and repr(source) == before


def test_e_zero_candidates_preserves_not_applicable_and_does_not_build_sample(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = execute(job(), (), {})
    assert source.observation_coverage is source.unavailable_ratio is source.excluded_ratio is None
    api = importlib.import_module("market_research.descriptive.conversion.api")
    monkeypatch.setattr(api, "NumericSample", lambda *args: pytest.fail("Built empty sample"))
    with pytest.raises(NoEligibleObservations):
        convert(source)


@pytest.mark.parametrize("value", [None, (), {}, 1, "ObservationSet", object()])
def test_f_wrong_public_variants(value: Any) -> None:
    with pytest.raises(InvalidObservationSet) as error:
        convert(value)
    assert error.value.stage == "conversion"
    assert error.value.category == "InvalidObservationSet"


@pytest.mark.parametrize(
    "field,value",
    [
        ("job_identity", ()),
        ("provenance", None),
        ("fixed_job_spec", None),
        ("observation_definition", None),
        ("candidate_anchors", (DAYS[4], DAYS[3], DAYS[2])),
        ("candidate_anchors", DAYS[2:4]),
        ("candidate_anchors", [DAYS[2], DAYS[3], DAYS[4]]),
        ("eligible_observations", ()),
        ("eligible_observations", (None,)),
        ("market_fact_coverage", None),
        ("sample_dependence_context", None),
    ],
)
def test_f_corrupted_top_level_structure(field: str, value: Any) -> None:
    with pytest.raises(InvalidObservationSet):
        convert(corrupt(complete(), **{field: value}))


@pytest.mark.parametrize("value", [True, 1, "0", None, float("nan"), float("inf"), -float("inf")])
def test_f_illegal_observation_coordinates_are_not_unmappable(value: Any) -> None:
    source = complete()
    outcomes = (
        corrupt(source.eligible_observations[0], scalar_value=value),
        *source.eligible_observations[1:],
    )
    with pytest.raises(InvalidObservationSet):
        convert(corrupt(source, eligible_observations=outcomes))


def test_f_nested_corruption_identity_coverage_dependence_and_keys() -> None:
    source = complete()
    bad_sources = [
        corrupt(source, fixed_job_spec=corrupt(source.fixed_job_spec, horizon=True)),
        corrupt(
            source, observation_definition=corrupt(source.observation_definition, metric="other")
        ),
        corrupt(source, eligible_observations=source.eligible_observations[::-1]),
        corrupt(source, eligible_observations=(source.eligible_observations[0],) * 3),
        corrupt(
            source,
            eligible_observations=(
                corrupt(source.eligible_observations[0], observation_key=()),
                *source.eligible_observations[1:],
            ),
        ),
        corrupt(
            source,
            market_fact_coverage=corrupt(
                source.market_fact_coverage, sample=source.market_fact_coverage.overall
            ),
        ),
        corrupt(
            source,
            market_fact_coverage=corrupt(
                source.market_fact_coverage,
                overall=corrupt(source.market_fact_coverage.overall, available_keys=()),
            ),
        ),
        corrupt(
            source, sample_dependence_context=corrupt(source.sample_dependence_context, horizon=1)
        ),
        corrupt(
            source, sample_dependence_context=corrupt(source.sample_dependence_context, spans=())
        ),
    ]
    for bad in bad_sources:
        with pytest.raises(InvalidObservationSet):
            convert(bad)


def test_f_corrupt_missing_and_excluded_evidence_precedes_no_eligible() -> None:
    unavailable = execute(job(), DAYS[:5], {})
    for changes in (
        {"missing_dependencies": ()},
        {"missing_dependencies": (None,)},
        {
            "missing_dependencies": (
                corrupt(unavailable.unavailable_observations[0].missing_dependencies[0], fact=None),
            )
        },
    ):
        outcomes = (
            corrupt(unavailable.unavailable_observations[0], **changes),
            *unavailable.unavailable_observations[1:],
        )
        with pytest.raises(InvalidObservationSet):
            convert(corrupt(unavailable, unavailable_observations=outcomes))
    excluded = execute(job(), DAYS[:5], {day: -1.0 for day in DAYS})
    outcomes_x = (
        corrupt(excluded.excluded_observations[0], reason_code=""),
        *excluded.excluded_observations[1:],
    )
    with pytest.raises(InvalidObservationSet):
        convert(corrupt(excluded, excluded_observations=outcomes_x))


@pytest.mark.parametrize("unit", ["", None, 1])
def test_g_statistics_rejection_is_unmappable_with_cause(unit: Any) -> None:
    source = complete()
    source = replace(
        source, observation_definition=replace(source.observation_definition, unit=unit)
    )
    with pytest.raises(UnmappableSample) as error:
        convert(source)
    assert error.value.stage == "conversion" and error.value.category == "UnmappableSample"
    assert isinstance(error.value.__cause__, InvalidSample)
    assert str(error.value)


def test_g_no_eligible_precedes_statistics_unit_mapping() -> None:
    source = execute(job(), (), {})
    source = replace(source, observation_definition=replace(source.observation_definition, unit=""))
    with pytest.raises(NoEligibleObservations):
        convert(source)


def test_missing_unit_field_is_structural_failure_with_original_cause() -> None:
    source = complete()
    definition = copy(source.observation_definition)
    object.__delattr__(definition, "unit")
    with pytest.raises(InvalidObservationSet) as error:
        convert(corrupt(source, observation_definition=definition))
    assert isinstance(error.value.__cause__, AttributeError)


@dataclass(frozen=True)
class OtherProvenance:
    evidence_reference: str


def test_h_case_agnostic_conversion_preserves_other_typed_provenance_and_opaque_unit() -> None:
    source = complete()
    fixed = replace(source.fixed_job_spec, subject="other-series", metric="another_scalar_v1")
    definition = replace(
        source.observation_definition,
        metric=fixed.metric,
        formula="published other formula",
        unit=" Opaque Unit ",
    )
    identity = (
        fixed.metric,
        fixed.subject,
        (),
        fixed.horizon,
        definition.horizon_unit,
        fixed.historical_sample_window.start_date,
        fixed.historical_sample_window.end_date,
        definition.anchor_meaning,
        definition.bounds,
    )
    other = ObservationSet(
        fixed_job_spec=fixed,
        job_identity=identity,
        observation_definition=definition,
        eligible_observations=tuple(
            replace(o, observation_key=(identity, o.anchor)) for o in source.eligible_observations
        ),
        candidate_anchors=source.candidate_anchors,
        unavailable_observations=(),
        excluded_observations=(),
        market_fact_coverage=source.market_fact_coverage,
        sample_dependence_context=source.sample_dependence_context,
        provenance=OtherProvenance("retained public source"),
    )
    projection = convert(other)
    assert type(projection.binding) is SampleBinding
    assert projection.binding.business_provenance is other.provenance
    assert projection.numeric_sample.unit == " Opaque Unit "


def test_i_purity_determinism_and_immutable_carriers(monkeypatch: pytest.MonkeyPatch) -> None:
    source = complete()
    before = repr(source)
    parameters = source.fixed_job_spec.metric_parameters
    for module_name in (
        "data_lake.datasets.tushare_trade_calendar",
        "data_lake.datasets.tushare_index_daily",
    ):
        module = importlib.import_module(module_name)
        monkeypatch.setattr(
            module, "create_service", lambda: pytest.fail("Converter acquired facts")
        )
        service = getattr(module, "TradeCalendarService", None) or module.IndexDailyService
        for method in ("coverage", "export", "ensure"):
            monkeypatch.setattr(
                service, method, lambda *args: pytest.fail("Converter called service")
            )
    monkeypatch.setattr(socket, "socket", lambda *args: pytest.fail("Converter opened network"))
    monkeypatch.setattr(
        importlib.import_module("market_statistics"),
        "compute",
        lambda *args: pytest.fail("Converter computed statistics"),
    )
    with monkeypatch.context() as io_guard:
        io_guard.setattr(
            builtins, "open", lambda *args, **kwargs: pytest.fail("Converter opened file")
        )
        first, second = convert(source), convert(source)
    assert first == second and repr(source) == before
    assert source.fixed_job_spec.metric_parameters is parameters
    assert (
        first.binding.source_observation_reference
        is second.binding.source_observation_reference
        is source
    )
    with pytest.raises(FrozenInstanceError):
        first.binding = second.binding  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.binding.ordered_observation_keys = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.numeric_sample.unit = "changed"  # type: ignore[misc]


def test_j_one_projection_reused_by_both_public_statistics_methods() -> None:
    source = complete()
    projection = convert(source)
    binding, sample = projection.binding, projection.numeric_sample
    quantiles = compute(sample, QuantileSpec(points=[0, 0.5, 1]))
    intervals = compute(sample, IntervalCountSpec(edges=[-0.2, 0, 0.2], unit=sample.unit))
    assert isinstance(quantiles, QuantileResult)
    assert isinstance(intervals, IntervalCountResult)
    assert quantiles.points_and_values == ((0.0, 0.0), (0.5, 0.0), (1.0, 121 / 100 - 1))
    assert tuple(bin.count for bin in intervals.bins) == (0, 2)
    assert intervals.underflow_count == 0 and intervals.overflow_count == 1
    assert intervals.overflow_frequency == 1 / 3
    assert quantiles.sample_count == intervals.sample_count == sample.sample_count == 3
    assert quantiles.unit == intervals.unit == sample.unit == "decimal_ratio"
    assert projection.binding is binding and projection.numeric_sample is sample
    assert binding.source_observation_reference is source


def test_public_facade_attributes_without_all() -> None:
    facade = importlib.import_module("market_research.descriptive.conversion")
    for name, value in (
        ("convert", convert),
        ("SampleBinding", SampleBinding),
        ("SampleProjection", SampleProjection),
        ("InvalidObservationSet", InvalidObservationSet),
        ("NoEligibleObservations", NoEligibleObservations),
        ("UnmappableSample", UnmappableSample),
    ):
        assert getattr(facade, name) is value
    assert not hasattr(facade, "__all__")
