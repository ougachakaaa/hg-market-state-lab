"""Stable public statistical failure categories."""


class StatisticalFailure(Exception):
    """Family of Statistics failures, identified by concrete category."""


class InvalidSample(StatisticalFailure, ValueError):
    """The public numerical sample is illegal."""


class InvalidStatisticalSpec(StatisticalFailure, ValueError):
    """The method, parameters or sample compatibility is illegal."""


class CalculationFailure(StatisticalFailure):
    """Legal inputs failed numerical execution or result validation."""

    def __init__(self, method: str, reason: str) -> None:
        self.method = method
        self.reason = reason
        super().__init__(f"{method}: {reason}")
