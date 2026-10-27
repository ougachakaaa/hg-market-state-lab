"""Bounded public-carrier and positional checks, without rerunning conversion."""

from dataclasses import replace
from datetime import date
from math import isfinite
from types import MappingProxyType

from market_statistics import NumericSample

from ..conversion import SampleBinding, SampleProjection
from ..observation import (
    EligibleObservation,
    EndpointFact,
    ExcludedObservation,
    FactCoverage,
    JobIdentity,
    MarketFactCoverage,
    MissingDependency,
    ObservationDefinition,
    ObservationJobSpec,
    ObservationSet,
    ObservationSpan,
    RequiredFact,
    SampleDependenceContext,
    UnavailableObservation,
)
from .failures import ResultAssociationFailure


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ResultAssociationFailure(reason)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _validate_fact(fact: RequiredFact) -> None:
    require(isinstance(fact, RequiredFact), "Expected typed RequiredFact identity")
    require(
        all(_text(value) for value in (fact.dataset, fact.view, fact.subject, fact.field))
        and type(fact.export_schema_version) is int
        and type(fact.trade_date) is date,
        "Malformed required fact identity",
    )


def _validate_endpoint(endpoint: EndpointFact) -> None:
    require(isinstance(endpoint, EndpointFact), "Expected typed endpoint evidence")
    _validate_fact(endpoint.fact)
    require(
        endpoint.endpoint_role in ("anchor", "lookback")
        and type(endpoint.value) is float
        and isfinite(endpoint.value),
        "Malformed endpoint role or fact value",
    )


def fixed_identity[P](fixed: ObservationJobSpec, source: ObservationSet[P]) -> JobIdentity:
    require(isinstance(fixed, ObservationJobSpec), "Expected fixed ObservationJobSpec")
    # Its constructor copies parameters: never call __post_init__ on the original.
    replace(fixed)
    require(isinstance(source, ObservationSet), "Expected public scalar ObservationSet")
    definition = source.observation_definition
    require(isinstance(definition, ObservationDefinition), "Expected ObservationDefinition")
    require(
        all(
            isinstance(value, str) and bool(value)
            for value in (
                definition.metric,
                definition.grain,
                definition.key_definition,
                definition.formula,
                definition.unit,
                definition.horizon_unit,
                definition.calendar,
                definition.anchor_meaning,
                definition.bounds,
            )
        ),
        "Malformed observation definition",
    )
    require(
        isinstance(fixed.metric_parameters, MappingProxyType)
        and all(isinstance(key, str) for key in fixed.metric_parameters),
        "Fixed Job parameters must retain immutable named parameters",
    )
    window = fixed.historical_sample_window
    return (
        fixed.metric,
        fixed.subject,
        tuple(sorted(fixed.metric_parameters.items())),
        fixed.horizon,
        definition.horizon_unit,
        window.start_date,
        window.end_date,
        definition.anchor_meaning,
        definition.bounds,
    )


def validate_projection[P](
    source: ObservationSet[P],
    projection: SampleProjection[P],
    identity: JobIdentity,
) -> None:
    require(isinstance(source.fixed_job_spec, ObservationJobSpec), "Malformed source fixed Job")
    replace(source.fixed_job_spec)
    require(
        isinstance(source.fixed_job_spec.metric_parameters, MappingProxyType),
        "Source Job parameters must remain immutable",
    )
    require(type(source.job_identity) is tuple, "Expected structural source Job identity")
    require(source.job_identity == identity, "Fixed Job does not match source Job identity")
    require(source.provenance is not None, "Source must retain original provenance")
    require(type(source.candidate_anchors) is tuple, "Candidate anchors must be immutable")
    for records, variant in (
        (source.eligible_observations, EligibleObservation),
        (source.unavailable_observations, UnavailableObservation),
        (source.excluded_observations, ExcludedObservation),
    ):
        require(type(records) is tuple, "Source outcomes must be immutable tuples")
        require(all(isinstance(record, variant) for record in records), "Wrong outcome variant")
    for record in source.unavailable_observations:
        require(
            type(record.missing_dependencies) is tuple
            and all(isinstance(item, MissingDependency) for item in record.missing_dependencies)
            and type(record.available_endpoints) is tuple
            and all(isinstance(item, EndpointFact) for item in record.available_endpoints),
            "Malformed retained unavailable evidence",
        )
        for missing in record.missing_dependencies:
            _validate_fact(missing.fact)
            require(
                missing.endpoint_role in ("anchor", "lookback")
                and _text(missing.reason)
                and _text(missing.input_reference)
                and type(missing.diagnostic_reasons) is tuple
                and all(isinstance(reason, str) for reason in missing.diagnostic_reasons),
                "Malformed missing dependency evidence",
            )
        for endpoint in record.available_endpoints:
            _validate_endpoint(endpoint)
    for excluded in source.excluded_observations:
        require(
            type(excluded.offending_facts) is tuple
            and all(isinstance(item, EndpointFact) for item in excluded.offending_facts)
            and isinstance(excluded.reason_code, str)
            and bool(excluded.reason_code)
            and isinstance(excluded.reason, str)
            and bool(excluded.reason),
            "Malformed retained exclusion evidence",
        )
        for endpoint in excluded.offending_facts:
            _validate_endpoint(endpoint)
    coverage = source.market_fact_coverage
    require(isinstance(coverage, MarketFactCoverage), "Expected original MarketFactCoverage")
    for part in (coverage.overall, coverage.warm_up, coverage.sample):
        require(isinstance(part, FactCoverage), "Expected typed coverage partitions")
        require(
            type(part.expected_keys) is tuple and type(part.available_keys) is tuple,
            "Coverage keys must remain immutable",
        )
        for keys in (part.expected_keys, part.available_keys):
            require(
                all(
                    type(key) is tuple
                    and len(key) == 2
                    and _text(key[0])
                    and type(key[1]) is date
                    for key in keys
                ),
                "Malformed fact coverage key",
            )
        FactCoverage.__post_init__(part)
    MarketFactCoverage.__post_init__(coverage)
    context = source.sample_dependence_context
    require(isinstance(context, SampleDependenceContext), "Expected original dependence context")
    require(
        type(context.horizon) is int
        and type(context.ordered_anchors) is tuple
        and type(context.spans) is tuple
        and isinstance(context.interpretation, str)
        and bool(context.interpretation)
        and all(
            isinstance(span, ObservationSpan)
            and type(span.anchor) is date
            and type(span.lookback) is date
            for span in context.spans
        ),
        "Malformed dependence context",
    )
    # The public Observation owner validates identity, unique/disjoint ordered keys,
    # finite scalars, conserved outcomes and dependence alignment, not market formulas.
    ObservationSet.__post_init__(source)
    require(
        source.candidate_count
        == source.eligible_count + source.unavailable_count + source.excluded_count,
        "Source population accounting does not conserve candidates",
    )
    require(type(projection) is SampleProjection, "Expected public SampleProjection")
    binding, sample = projection.binding, projection.numeric_sample
    require(type(binding) is SampleBinding, "Expected public SampleBinding")
    require(binding.source_observation_reference is source, "Binding refers to a different source")
    require(type(sample) is NumericSample, "Expected public NumericSample")
    require(
        type(sample.values) is tuple and all(type(value) is float for value in sample.values),
        "Sample must retain immutable binary64 coordinates",
    )
    NumericSample(sample.values, sample.unit)  # Public numerical legality; retain original sample.
    require(sample.unit == source.observation_definition.unit, "Sample/source unit mismatch")
    require(
        type(binding.ordered_observation_keys) is tuple
        and len(sample.values) == len(binding.ordered_observation_keys) == source.eligible_count,
        "Sample/key/Eligible count mismatch",
    )
    require(
        binding.ordered_observation_keys
        == tuple(item.observation_key for item in source.eligible_observations),
        "Bound keys do not match Eligible keys in source order",
    )
    require(
        all(
            value.hex() == item.scalar_value.hex()
            for value, item in zip(sample.values, source.eligible_observations, strict=True)
        ),
        "Sample values do not match exact ordered Eligible binary64 coordinates",
    )
