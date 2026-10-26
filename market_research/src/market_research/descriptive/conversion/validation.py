"""Revalidate public structure, without reconstructing case inputs or provenance."""

from dataclasses import replace
from datetime import date
from math import isfinite
from types import MappingProxyType

from ..observation import (
    EligibleObservation,
    EndpointFact,
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
from .failures import InvalidObservationSet


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise InvalidObservationSet(reason)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _fact(fact: RequiredFact) -> None:
    _require(isinstance(fact, RequiredFact), "Required evidence must contain a RequiredFact")
    _require(
        all(_text(value) for value in (fact.dataset, fact.view, fact.subject, fact.field))
        and type(fact.export_schema_version) is int
        and type(fact.trade_date) is date,
        "Malformed required fact identity",
    )


def _endpoint(endpoint: EndpointFact) -> None:
    _require(isinstance(endpoint, EndpointFact), "Expected typed endpoint evidence")
    _fact(endpoint.fact)
    _require(
        endpoint.endpoint_role in ("anchor", "lookback")
        and type(endpoint.value) is float
        and isfinite(endpoint.value),
        "Malformed endpoint role or fact value",
    )


def _coverage(coverage: FactCoverage) -> None:
    _require(isinstance(coverage, FactCoverage), "Expected typed FactCoverage")
    for keys in (coverage.expected_keys, coverage.available_keys):
        _require(type(keys) is tuple, "Fact coverage keys must be immutable tuples")
        for key in keys:
            _require(
                type(key) is tuple and len(key) == 2 and _text(key[0]) and type(key[1]) is date,
                "Malformed fact coverage key",
            )
    coverage.__post_init__()


def validate_source[Provenance](source: ObservationSet[Provenance]) -> None:
    """Translate structural failures; reuse Observation's own invariant validation.

    Provenance has no common cross-case schema. Retaining the exact source preserves
    its concrete type and association without interpreting a case's private payload.
    """
    try:
        _validate(source)
    except InvalidObservationSet:
        raise
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        ObservationConstructionFailure,
    ) as exc:
        raise InvalidObservationSet(f"Malformed ObservationSet: {exc}") from exc


def _validate[Provenance](source: ObservationSet[Provenance]) -> None:
    _require(isinstance(source, ObservationSet), "Expected the public scalar ObservationSet")
    job = source.fixed_job_spec
    _require(isinstance(job, ObservationJobSpec), "Expected a fixed ObservationJobSpec")
    _require(
        isinstance(job.metric_parameters, MappingProxyType), "Job parameters must be immutable"
    )
    # The request constructor copies parameters. Revalidate a new request, never mutate
    # the original via its __post_init__ (which replaces its mapping).
    replace(job)
    definition = source.observation_definition
    _require(isinstance(definition, ObservationDefinition), "Expected typed ObservationDefinition")
    # A missing field is malformed structure; representability of a present unit
    # belongs to the Statistics constructor after source/zero-eligible validation.
    _ = definition.unit
    _require(
        all(
            _text(value)
            for value in (
                definition.metric,
                definition.grain,
                definition.key_definition,
                definition.formula,
                definition.horizon_unit,
                definition.calendar,
                definition.anchor_meaning,
                definition.bounds,
            )
        ),
        "Malformed observation definition",
    )
    _require(type(source.job_identity) is tuple, "Job identity must be a structural tuple")
    _require(source.provenance is not None, "Source must retain its provenance evidence")
    _require(type(source.candidate_anchors) is tuple, "Candidates must be an immutable tuple")
    for outcomes, variant in (
        (source.eligible_observations, EligibleObservation),
        (source.unavailable_observations, UnavailableObservation),
        (source.excluded_observations, ExcludedObservation),
    ):
        _require(type(outcomes) is tuple, "Outcomes must be immutable tuples")
        for outcome in outcomes:
            _require(isinstance(outcome, variant), "Wrong public outcome variant")
            _require(
                type(outcome.anchor) is date and type(outcome.observation_key) is tuple,
                "Malformed outcome anchor or key",
            )
    for unavailable in source.unavailable_observations:
        _require(
            type(unavailable.missing_dependencies) is tuple
            and type(unavailable.available_endpoints) is tuple,
            "Unavailable evidence must be immutable tuples",
        )
        for missing in unavailable.missing_dependencies:
            _require(isinstance(missing, MissingDependency), "Expected typed missing dependency")
            _fact(missing.fact)
            _require(
                missing.endpoint_role in ("anchor", "lookback")
                and _text(missing.reason)
                and _text(missing.input_reference)
                and type(missing.diagnostic_reasons) is tuple
                and all(isinstance(reason, str) for reason in missing.diagnostic_reasons),
                "Malformed missing dependency evidence",
            )
        for endpoint in unavailable.available_endpoints:
            _endpoint(endpoint)
    for excluded in source.excluded_observations:
        _require(
            _text(excluded.reason_code)
            and _text(excluded.reason)
            and type(excluded.offending_facts) is tuple,
            "Malformed exclusion evidence",
        )
        for endpoint in excluded.offending_facts:
            _endpoint(endpoint)
    coverage = source.market_fact_coverage
    _require(isinstance(coverage, MarketFactCoverage), "Expected typed MarketFactCoverage")
    for partition in (coverage.overall, coverage.warm_up, coverage.sample):
        _coverage(partition)
    coverage.__post_init__()
    context = source.sample_dependence_context
    _require(isinstance(context, SampleDependenceContext), "Expected typed dependence context")
    _require(
        type(context.horizon) is int
        and type(context.ordered_anchors) is tuple
        and type(context.spans) is tuple
        and _text(context.interpretation),
        "Malformed dependence context",
    )
    for span in context.spans:
        _require(
            isinstance(span, ObservationSpan)
            and type(span.anchor) is date
            and type(span.lookback) is date,
            "Expected typed dependence spans with date coordinates",
        )
    ObservationSet.__post_init__(source)
