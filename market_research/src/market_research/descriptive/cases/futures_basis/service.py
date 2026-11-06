"""Case-level composition; financial formulas remain in pure construction."""

from .construction import construct_observations
from .inputs import FuturesBasisRequest
from .observations import FuturesBasisResult
from .preparation import CalendarService, FuturesService, IndexService, prepare_inputs


def observe_futures_basis(
    request: FuturesBasisRequest,
    *,
    calendar_service: CalendarService | None = None,
    futures_service: FuturesService | None = None,
    index_service: IndexService | None = None,
) -> FuturesBasisResult:
    prepared = prepare_inputs(
        request,
        calendar_service=calendar_service,
        futures_service=futures_service,
        index_service=index_service,
    )
    return construct_observations(request, prepared)
