"""Sample-free public spec validation, also enforced by compute."""

from .failures import InvalidStatisticalSpec
from .models import (
    EmpiricalPercentileSpec,
    IntervalCountSpec,
    MeanSpec,
    QuantileSpec,
    StatisticalSpec,
)


def validate_spec(spec: StatisticalSpec) -> None:
    if type(spec) not in (QuantileSpec, IntervalCountSpec, MeanSpec, EmpiricalPercentileSpec):
        raise InvalidStatisticalSpec(
            "Expected QuantileSpec, IntervalCountSpec, MeanSpec or EmpiricalPercentileSpec"
        )
    try:
        spec._validate()
    except AttributeError as exc:
        raise InvalidStatisticalSpec("Incomplete StatisticalSpec") from exc
