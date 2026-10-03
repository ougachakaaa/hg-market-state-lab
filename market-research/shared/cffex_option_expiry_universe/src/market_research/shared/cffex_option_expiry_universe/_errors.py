"""Resolver-owned failures; no Observation lifecycle inheritance."""


class ExpiryUniverseError(Exception):
    """The requested expiry universe could not be resolved."""


class ExpiryUniverseInvalidRequestError(ExpiryUniverseError):
    """Invalid caller inputs; no upstream operations have started."""


class ExpiryUniverseOperationError(ExpiryUniverseError):
    """A valid request could not produce a complete resolver result."""
