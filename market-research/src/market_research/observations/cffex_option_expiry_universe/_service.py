"""Public ensure orchestration; retained lookup precedes every upstream call."""

from collections.abc import Callable
from pathlib import Path

from data_lake.datasets import tushare_equity_index_options as options

from .. import ObservationInvalidRequestError, ObservationOperationError
from .._sqlite import owned_path
from . import _persistence
from ._derivation import derive, validate
from ._models import ExpiryUniverseArtifact, ExpiryUniverseRequest
from ._upstream import require_ensure, validate_options_export


class ExpiryUniverseService:
    def __init__(self, *, _path: Path, _options_factory: Callable[[], options.OptionsDailyService]):
        """Private composition hook for controlled tests; use create_service normally."""
        self._path = _path
        self._options_factory = _options_factory

    def ensure(self, request: ExpiryUniverseRequest) -> ExpiryUniverseArtifact:
        if not isinstance(request, ExpiryUniverseRequest):
            raise ObservationInvalidRequestError("Expected ExpiryUniverseRequest")
        request.__post_init__()
        try:
            retained = _persistence.load(self._path, request)
            if retained is not None:
                validate(retained, request)
                return retained
            service = self._options_factory()
            upstream_request = options.OptionsDailyRange(
                (request.product_code,),
                request.expiry_start_date,
                request.expiry_end_date,
            )
            require_ensure(
                service.ensure(upstream_request),
                context=(
                    f"tushare_equity_index_options product_code={request.product_code} "
                    f"start_date={request.expiry_start_date.isoformat()} "
                    f"end_date={request.expiry_end_date.isoformat()}"
                ),
            )
            view = service.export(upstream_request)
            validate_options_export(
                view, request.product_code, request.expiry_start_date, request.expiry_end_date
            )
            if view.coverage.complete is not True:
                raise ValueError("Options export is incomplete after ensure")
            artifact = derive(request, view)
            validate(artifact, request)
            retained = _persistence.publish(self._path, request, artifact)
            validate(retained, request)
            return retained
        except Exception as error:
            raise ObservationOperationError(f"ExpiryUniverse ensure failed: {error}") from error


def create_service() -> ExpiryUniverseService:
    try:
        return ExpiryUniverseService(
            _path=owned_path(
                "market-research/observations/cffex_option_expiry_universe",
                "cffex_option_expiry_universe.sqlite3",
            ),
            _options_factory=options.create_service,
        )
    except Exception as error:
        raise ObservationOperationError(
            f"ExpiryUniverseService construction failed: {error}"
        ) from error
