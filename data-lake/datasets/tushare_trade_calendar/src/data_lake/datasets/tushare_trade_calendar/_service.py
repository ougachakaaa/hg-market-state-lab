"""Calendar interpretation composed with the existing cache execution core."""

from collections.abc import Callable

from data_lake.ports import Repository, Source
from data_lake.results import CoverageResult, EnsureResult, InvalidRequestError, OperationError

from ._composition import _compose, create_repository
from ._models import (
    TradeCalendarExport,
    TradeCalendarRange,
)
from ._source import prepare_source


def _validate_request(request: TradeCalendarRange, operation: str) -> None:
    try:
        if not isinstance(request, TradeCalendarRange):
            raise InvalidRequestError("request must be a TradeCalendarRange")
        request.__post_init__()
    except (InvalidRequestError, OperationError):
        raise
    except Exception as exc:
        raise OperationError(f"{operation} operation could not be executed") from exc


class TradeCalendarService:
    def __init__(self) -> None:
        self._core = _compose(create_repository(), prepare_source)

    def coverage(self, request: TradeCalendarRange) -> CoverageResult:
        _validate_request(request, "Coverage")
        return self._core.coverage(request)

    def ensure(self, request: TradeCalendarRange) -> EnsureResult:
        _validate_request(request, "Ensure")
        return self._core.ensure(request)

    def export(self, request: TradeCalendarRange) -> TradeCalendarExport:
        _validate_request(request, "Export")
        return self._core.export(request)


def _create_service(
    repository: Repository, source_factory: Callable[[], Source]
) -> TradeCalendarService:
    """Internal test/composition seam, excluded from the consumer facade."""
    service = TradeCalendarService.__new__(TradeCalendarService)
    service._core = _compose(repository, source_factory)
    return service


def create_service() -> TradeCalendarService:
    return TradeCalendarService()
