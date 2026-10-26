"""Conversion failures are Research failures, separate from statistical computation."""


class InvalidObservationSet(ValueError):
    """The source violates the published scalar Observation structure."""

    stage = "conversion"
    category = "InvalidObservationSet"


class NoEligibleObservations(ValueError):
    """A valid population has no Eligible values to project."""

    stage = "conversion"
    category = "NoEligibleObservations"


class UnmappableSample(ValueError):
    """A legal source cannot be represented by the Statistics public sample."""

    stage = "conversion"
    category = "UnmappableSample"
