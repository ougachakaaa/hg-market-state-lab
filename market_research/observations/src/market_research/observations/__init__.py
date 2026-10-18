"""Public failures; authority: IMPLEMENTATION.md and ../../../ARCHITECTURE.md (owner root)."""

from pkgutil import extend_path

from ._errors import ObservationError as ObservationError
from ._errors import ObservationInvalidRequestError as ObservationInvalidRequestError
from ._errors import ObservationOperationError as ObservationOperationError

__path__ = extend_path(__path__, __name__)
