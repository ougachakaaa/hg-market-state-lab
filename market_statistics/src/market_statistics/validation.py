"""Sample-free public spec validation, also enforced by compute."""

from .failures import InvalidStatisticalSpec
from .models import IntervalCountSpec, QuantileSpec, StatisticalSpec


def validate_spec(spec: StatisticalSpec) -> None:
    if type(spec) not in (QuantileSpec, IntervalCountSpec):
        raise InvalidStatisticalSpec("Expected QuantileSpec or IntervalCountSpec")
    try:
        spec._validate()
    except AttributeError as exc:
        raise InvalidStatisticalSpec("Incomplete StatisticalSpec") from exc
