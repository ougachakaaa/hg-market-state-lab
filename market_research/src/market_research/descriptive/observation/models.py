"""Immutable scalar observation contracts, independent of any instrument taxonomy."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from math import isfinite
from types import MappingProxyType
from typing import Literal


class InvalidObservationRequest(ValueError):
    """A fixed observation request is invalid, before input acquisition."""


class ObservationConstructionFailure(Exception):
    """Validated inputs could not produce a legal, accountable observation set."""

    stage = "observation_construction"
    category = "ObservationConstructionFailure"


@dataclass(frozen=True)
class DateWindow:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if type(self.start_date) is not date or type(self.end_date) is not date:
            raise InvalidObservationRequest("Window requires dates, not timestamps or strings")
        if self.start_date > self.end_date:
            raise InvalidObservationRequest("Window start_date must be <= end_date")


@dataclass(frozen=True)
class ObservationJobSpec:
    subject: str
    metric: str
    metric_parameters: Mapping[str, object]
    horizon: int
    historical_sample_window: DateWindow

    def __post_init__(self) -> None:
        if not isinstance(self.subject, str) or not self.subject:
            raise InvalidObservationRequest("subject must be an explicit stable identity")
        if not isinstance(self.metric, str) or not self.metric:
            raise InvalidObservationRequest("metric must be an explicit versioned identity")
        if not isinstance(self.metric_parameters, Mapping):
            raise InvalidObservationRequest("metric_parameters must be an explicit mapping")
        if type(self.horizon) is not int or self.horizon <= 0:
            raise InvalidObservationRequest("horizon must be a positive integer, excluding bool")
        if not isinstance(self.historical_sample_window, DateWindow):
            raise InvalidObservationRequest("historical_sample_window must be a DateWindow")
        self.historical_sample_window.__post_init__()
        object.__setattr__(
            self, "metric_parameters", MappingProxyType(dict(self.metric_parameters))
        )


type JobIdentity = tuple[str, str, tuple[tuple[str, object], ...], int, str, date, date, str, str]
type ObservationKey = tuple[JobIdentity, date]
type DailyKey = tuple[str, date]
type EndpointRole = Literal["anchor", "lookback"]


@dataclass(frozen=True)
class ObservationDefinition:
    metric: str
    grain: str
    key_definition: str
    formula: str
    unit: str
    horizon_unit: str
    calendar: str
    anchor_meaning: str
    bounds: str


@dataclass(frozen=True)
class RequiredFact:
    dataset: str
    view: str
    export_schema_version: int
    subject: str
    trade_date: date
    field: str

    @property
    def daily_key(self) -> DailyKey:
        return self.subject, self.trade_date


@dataclass(frozen=True)
class MissingDependency:
    endpoint_role: EndpointRole
    fact: RequiredFact
    reason: str
    input_reference: str
    diagnostic_reasons: tuple[str, ...]


@dataclass(frozen=True)
class EndpointFact:
    endpoint_role: EndpointRole
    fact: RequiredFact
    value: float


@dataclass(frozen=True)
class EligibleObservation:
    observation_key: ObservationKey
    anchor: date
    scalar_value: float


@dataclass(frozen=True)
class UnavailableObservation:
    observation_key: ObservationKey
    anchor: date
    missing_dependencies: tuple[MissingDependency, ...]
    available_endpoints: tuple[EndpointFact, ...]


@dataclass(frozen=True)
class ExcludedObservation:
    observation_key: ObservationKey
    anchor: date
    reason_code: str
    reason: str
    offending_facts: tuple[EndpointFact, ...]


@dataclass(frozen=True)
class FactCoverage:
    expected_keys: tuple[DailyKey, ...]
    available_keys: tuple[DailyKey, ...]

    def __post_init__(self) -> None:
        if (
            tuple(sorted(set(self.expected_keys))) != self.expected_keys
            or tuple(sorted(set(self.available_keys))) != self.available_keys
            or not set(self.available_keys) <= set(self.expected_keys)
        ):
            raise ObservationConstructionFailure("Invalid fact coverage keys")

    @property
    def expected_fact_units(self) -> int:
        return len(self.expected_keys)

    @property
    def available_fact_units(self) -> int:
        return len(self.available_keys)

    @property
    def absent_keys(self) -> tuple[DailyKey, ...]:
        available = set(self.available_keys)
        return tuple(key for key in self.expected_keys if key not in available)

    @property
    def ratio(self) -> float | None:
        return len(self.available_keys) / len(self.expected_keys) if self.expected_keys else None


@dataclass(frozen=True)
class MarketFactCoverage:
    overall: FactCoverage
    warm_up: FactCoverage
    sample: FactCoverage

    def __post_init__(self) -> None:
        if (
            self.warm_up.expected_keys + self.sample.expected_keys != self.overall.expected_keys
            or self.warm_up.available_keys + self.sample.available_keys
            != self.overall.available_keys
        ):
            raise ObservationConstructionFailure("Fact coverage partition does not conserve keys")


@dataclass(frozen=True)
class ObservationSpan:
    anchor: date
    lookback: date


@dataclass(frozen=True)
class SampleDependenceContext:
    horizon: int
    horizon_unit: str
    ordered_anchors: tuple[date, ...]
    spans: tuple[ObservationSpan, ...]
    interpretation: str


@dataclass(frozen=True)
class ObservationSet[Provenance]:
    job_identity: JobIdentity
    fixed_job_spec: ObservationJobSpec
    observation_definition: ObservationDefinition
    candidate_anchors: tuple[date, ...]
    eligible_observations: tuple[EligibleObservation, ...]
    unavailable_observations: tuple[UnavailableObservation, ...]
    excluded_observations: tuple[ExcludedObservation, ...]
    market_fact_coverage: MarketFactCoverage
    provenance: Provenance
    sample_dependence_context: SampleDependenceContext

    def __post_init__(self) -> None:
        def fail(reason: str) -> None:
            raise ObservationConstructionFailure(reason)

        job = self.fixed_job_spec
        definition = self.observation_definition
        window = job.historical_sample_window
        expected_identity = (
            job.metric,
            job.subject,
            tuple(sorted(job.metric_parameters.items())),
            job.horizon,
            definition.horizon_unit,
            window.start_date,
            window.end_date,
            definition.anchor_meaning,
            definition.bounds,
        )
        if self.job_identity != expected_identity or definition.metric != job.metric:
            fail("Observation identity and definition must agree with the fixed request")
        if any(
            type(anchor) is not date or not window.start_date <= anchor <= window.end_date
            for anchor in self.candidate_anchors
        ):
            fail("Candidate anchors must be dates within the fixed sample window")
        if tuple(sorted(set(self.candidate_anchors))) != self.candidate_anchors:
            fail("Candidate anchors must be ordered and unique")
        seen: set[date] = set()
        for outcomes in (
            self.eligible_observations,
            self.unavailable_observations,
            self.excluded_observations,
        ):
            anchors = tuple(item.anchor for item in outcomes)
            if tuple(sorted(set(anchors))) != anchors:
                fail("Outcome collection must be ordered and unique")
            for item in outcomes:
                if item.anchor in seen or item.observation_key != (self.job_identity, item.anchor):
                    fail("Outcome key is duplicated or disagrees with the fixed Job")
                seen.add(item.anchor)
        if seen != set(self.candidate_anchors):
            fail("Every candidate must have exactly one outcome")
        if any(
            type(o.scalar_value) is not float or not isfinite(o.scalar_value)
            for o in self.eligible_observations
        ):
            fail("Eligible scalar must be a finite binary64 float")
        if any(not o.missing_dependencies for o in self.unavailable_observations):
            fail("Unavailable observations must retain missing dependencies")
        if any(not o.offending_facts for o in self.excluded_observations):
            fail("Excluded observations must retain offending facts")
        context = self.sample_dependence_context
        if context.horizon != job.horizon or context.horizon_unit != definition.horizon_unit:
            fail("Dependence horizon must agree with the fixed request")
        if context.ordered_anchors != self.candidate_anchors or (
            tuple(span.anchor for span in context.spans) != self.candidate_anchors
        ):
            fail("Dependence context must cover the candidate population")

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_anchors)

    @property
    def eligible_count(self) -> int:
        return len(self.eligible_observations)

    @property
    def unavailable_count(self) -> int:
        return len(self.unavailable_observations)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded_observations)

    @property
    def observation_coverage(self) -> float | None:
        return self.eligible_count / self.candidate_count if self.candidate_count else None

    @property
    def unavailable_ratio(self) -> float | None:
        return self.unavailable_count / self.candidate_count if self.candidate_count else None

    @property
    def excluded_ratio(self) -> float | None:
        return self.excluded_count / self.candidate_count if self.candidate_count else None
