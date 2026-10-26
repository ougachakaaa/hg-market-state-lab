"""Minimal immutable request and evidence compositions, retaining original objects."""

from dataclasses import dataclass

from market_statistics import StatisticalResult, StatisticalSpec, validate_spec

from ..conversion import SampleProjection
from ..observation import ObservationSet


@dataclass(frozen=True)
class AnalysisRequest:
    request_id: str
    spec: StatisticalSpec

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id:
            raise ValueError("request_id must be an explicit non-empty string")
        validate_spec(self.spec)


@dataclass(frozen=True)
class ResearchAnalysisEvidence[Provenance]:
    """Use associate to establish validity; direct construction is only a carrier."""

    request: AnalysisRequest
    statistical_result: StatisticalResult
    projection: SampleProjection[Provenance]

    @property
    def source_observation_reference(self) -> ObservationSet[Provenance]:
        return self.projection.binding.source_observation_reference
