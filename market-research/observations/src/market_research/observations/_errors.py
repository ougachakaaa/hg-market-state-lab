"""Observation-owned failure taxonomy."""


class ObservationError(Exception):
    """An Observation request could not be satisfied."""


class ObservationInvalidRequestError(ObservationError):
    """The caller supplied an invalid semantic request."""


class ObservationOperationError(ObservationError):
    """A valid request could not return a durable complete Artifact."""
