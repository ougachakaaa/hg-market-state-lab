"""Resolve through Options public ensure/export on every invocation."""

from collections.abc import Callable

from data_lake import InvalidRequestError
from data_lake.datasets import tushare_equity_index_options as options

from ._derivation import derive
from ._errors import ExpiryUniverseInvalidRequestError, ExpiryUniverseOperationError
from ._models import ExpiryUniverseRequest, ExpiryUniverseResult
from ._upstream import require_ensure, validate_options_export


class ExpiryUniverseResolver:
    def __init__(self, *, _options_factory: Callable[[], options.OptionsDailyService]):
        """Private composition hook for tests; use create_resolver normally."""
        self._options_factory = _options_factory

    def resolve(self, request: ExpiryUniverseRequest) -> ExpiryUniverseResult:
        if not isinstance(request, ExpiryUniverseRequest):
            raise ExpiryUniverseInvalidRequestError("Expected ExpiryUniverseRequest")
        request.__post_init__()
        try:
            upstream_request = options.OptionsDailyRange(
                (request.product_code,), request.expiry_start_date, request.expiry_end_date
            )
        except InvalidRequestError as error:
            raise ExpiryUniverseInvalidRequestError(str(error)) from error
        try:
            service = self._options_factory()
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
            return derive(request, view)
        except Exception as error:
            raise ExpiryUniverseOperationError(f"ExpiryUniverse resolve failed: {error}") from error


def create_resolver() -> ExpiryUniverseResolver:
    try:
        return ExpiryUniverseResolver(_options_factory=options.create_service)
    except Exception as error:
        raise ExpiryUniverseOperationError(
            f"ExpiryUniverseResolver construction failed: {error}"
        ) from error
