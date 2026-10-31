"""Compose public input preparation and pure observation construction."""

from .construction import construct_observations
from .inputs import SegmentationRequest
from .models import SegmentationObservationSet
from .preparation import CalendarService, IndexService, prepare_inputs


def observe_price_segments(
    request: SegmentationRequest,
    *,
    calendar_service: CalendarService | None = None,
    index_service: IndexService | None = None,
) -> SegmentationObservationSet:
    prepared = prepare_inputs(
        request, calendar_service=calendar_service, index_service=index_service
    )
    return construct_observations(request, prepared)
