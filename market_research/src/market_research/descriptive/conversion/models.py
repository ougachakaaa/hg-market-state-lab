"""Immutable composition of the original Research source and Statistics sample."""

from dataclasses import dataclass

from market_statistics import NumericSample

from ..observation import (
    ExcludedObservation,
    MarketFactCoverage,
    ObservationKey,
    ObservationSet,
    SampleDependenceContext,
    UnavailableObservation,
)


@dataclass(frozen=True)
class SampleBinding[Provenance]:
    source_observation_reference: ObservationSet[Provenance]
    ordered_observation_keys: tuple[ObservationKey, ...]

    @property
    def candidate_count(self) -> int:
        return self.source_observation_reference.candidate_count

    @property
    def eligible_count(self) -> int:
        return self.source_observation_reference.eligible_count

    @property
    def unavailable_count(self) -> int:
        return self.source_observation_reference.unavailable_count

    @property
    def excluded_count(self) -> int:
        return self.source_observation_reference.excluded_count

    @property
    def unavailable_records(self) -> tuple[UnavailableObservation, ...]:
        return self.source_observation_reference.unavailable_observations

    @property
    def exclusion_reasons(self) -> tuple[ExcludedObservation, ...]:
        return self.source_observation_reference.excluded_observations

    @property
    def coverage_context(self) -> MarketFactCoverage:
        return self.source_observation_reference.market_fact_coverage

    @property
    def observation_coverage(self) -> float | None:
        return self.source_observation_reference.observation_coverage

    @property
    def unavailable_ratio(self) -> float | None:
        return self.source_observation_reference.unavailable_ratio

    @property
    def excluded_ratio(self) -> float | None:
        return self.source_observation_reference.excluded_ratio

    @property
    def business_provenance(self) -> Provenance:
        return self.source_observation_reference.provenance

    @property
    def sample_dependence_context(self) -> SampleDependenceContext:
        return self.source_observation_reference.sample_dependence_context


@dataclass(frozen=True)
class SampleProjection[Provenance]:
    numeric_sample: NumericSample
    binding: SampleBinding[Provenance]
