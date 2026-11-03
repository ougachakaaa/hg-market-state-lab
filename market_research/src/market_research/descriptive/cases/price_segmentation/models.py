from dataclasses import dataclass
from datetime import date
from typing import Literal

from .inputs import PreparedSegmentationInputs, SegmentationRequest


@dataclass(frozen=True, slots=True)
class ImportantPoint:
    index: int
    date: date
    close: float


@dataclass(frozen=True, slots=True)
class PriceSegment:
    segment_identity: tuple[SegmentationRequest, int, int]
    start_index: int
    end_index: int
    start_date: date
    end_date: date
    start_close: float
    end_close: float
    duration_sessions: int
    amplitude_ratio: float
    direction: Literal["up", "down", "flat"]
    touches_start_boundary: bool
    touches_end_boundary: bool


@dataclass(frozen=True, slots=True)
class SegmentationDiagnostics:
    input_point_count: int
    important_point_count: int
    segment_count: int
    algorithm_id: str
    epsilon: float
    max_reconstruction_error: float


@dataclass(frozen=True, slots=True)
class SegmentationObservationSet:
    request_identity: SegmentationRequest
    important_points: tuple[ImportantPoint, ...]
    segments: tuple[PriceSegment, ...]
    diagnostics: SegmentationDiagnostics
    provenance: PreparedSegmentationInputs


class ObservationConstructionError(Exception):
    """Stable construction failure with the available input evidence."""

    def __init__(
        self, category: str, stage: str, reason: str, request: object, prepared_inputs: object
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.stage = stage
        self.reason = reason
        self.request = request
        self.prepared_inputs = prepared_inputs
