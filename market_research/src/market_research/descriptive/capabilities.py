"""Read-only publication of the one semantically admitted Research capability."""

from dataclasses import dataclass
from typing import Literal

from market_statistics import IntervalCountSpec, QuantileSpec

from .cases.trailing_return import DEFINITION


class CapabilityNotFound(LookupError):
    """No admitted Research capability has this exact versioned identity."""


@dataclass(frozen=True)
class SubjectDescription:
    kind: Literal["canonical_full_index_code"]
    pattern: str
    verified_example: str
    example_name: str
    example_is_default: Literal[False]
    membership_note: str


@dataclass(frozen=True)
class QuantileDescription:
    method: Literal["quantile"]
    required_parameters: tuple[Literal["points"], ...]
    minimum_points: int
    probability_bounds: tuple[float, float]
    coordinates: str
    estimator: Literal["type7_linear_v1"]


@dataclass(frozen=True)
class IntervalCountDescription:
    method: Literal["interval_count"]
    required_parameters: tuple[Literal["edges", "unit"], ...]
    minimum_edges: int
    coordinates: str
    unit: str
    bins: str


@dataclass(frozen=True)
class EmptyMetricParameters:
    """This admitted case has no legal metric parameter fields."""


@dataclass(frozen=True)
class CapabilityDescription:
    id: str
    name: str
    paradigm: Literal["descriptive"]
    purpose: str
    status: Literal["supported"]
    live_readiness: Literal["not_probed"]
    subject: SubjectDescription
    metric_parameters: EmptyMetricParameters
    metric_parameters_requirement: Literal["explicit_empty_object"]
    ordered_nonempty_fields: tuple[str, ...]
    unique_fields: tuple[str, ...]
    horizon_type: Literal["positive_integer_excluding_bool"]
    horizon_unit: str
    window_constraints: tuple[str, ...]
    formula: str
    unit: str
    calendar: str
    anchor_meaning: str
    bounds: str
    analysis_methods: tuple[QuantileDescription, IntervalCountDescription]
    statistics_validator: Literal["market_statistics.validate_spec"]
    on_job_failure_required: Literal[True]
    on_job_failure_values: tuple[Literal["continue"], Literal["stop"]]
    status_semantics: tuple[str, ...]
    limitations: tuple[str, ...]


_TRAILING_RETURN = CapabilityDescription(
    id=DEFINITION.metric,
    name="Index Trailing Cumulative Return Research",
    paradigm="descriptive",
    purpose="Describe historical index end-session trailing returns with explicit analyses.",
    status="supported",
    live_readiness="not_probed",
    subject=SubjectDescription(
        "canonical_full_index_code",
        r"[0-9]{6}\.(SH|SZ|CSI)",
        "000852.SH",
        "CSI1000",
        False,
        "Example verified in isolated LIVE-E2E-01; syntax does not establish source membership.",
    ),
    metric_parameters=EmptyMetricParameters(),
    metric_parameters_requirement="explicit_empty_object",
    ordered_nonempty_fields=("subjects", "horizons", "windows", "analysis_requests"),
    unique_fields=("subjects", "horizons", "windows", "analysis_requests.request_id"),
    horizon_type="positive_integer_excluding_bool",
    horizon_unit=DEFINITION.horizon_unit,
    window_constraints=(
        "YYYY-MM-DD date-only",
        "inclusive start_date <= end_date",
        "end_date <= today in Asia/Shanghai",
    ),
    formula=DEFINITION.formula,
    unit=DEFINITION.unit,
    calendar=DEFINITION.calendar,
    anchor_meaning=DEFINITION.anchor_meaning,
    bounds=DEFINITION.bounds,
    analysis_methods=(
        QuantileDescription(
            QuantileSpec([0.0]).method,
            ("points",),
            1,
            (0.0, 1.0),
            "finite binary64, strictly increasing and unique; bool/text rejected",
            "type7_linear_v1",
        ),
        IntervalCountDescription(
            IntervalCountSpec([0.0, 1.0], DEFINITION.unit).method,
            ("edges", "unit"),
            2,
            "finite binary64, strictly increasing; bool/text rejected",
            DEFINITION.unit,
            "[left,right), final [left,right]; underflow/overflow use full sample denominator",
        ),
    ),
    statistics_validator="market_statistics.validate_spec",
    on_job_failure_required=True,
    on_job_failure_values=("continue", "stop"),
    status_semantics=(
        "continue attempts all Jobs; stop skips later Jobs after the complete first Failed Job",
        "Batch success: all Success; partial_success: successes and failures; failed: no Success",
        "Job Success: every required analysis associated; Failed: a stage/analysis failed",
        "Skipped: stop policy only; analyses success|failed|not_attempted retain original order",
    ),
    limitations=(
        "Supported implementation is not a live provider/credential/cache readiness claim.",
        "Live upstream may be unavailable; partial Index facts retain coverage and may succeed.",
        "Missing Calendar or no eligible observations may fail; no implicit defaults or provider.",
        "Historical default Calendar cache recovery was not performed; isolated Live E2E verified.",
        "No persistent Research Run, replay, result cache or historical-run retrieval.",
        "Index case only; no stocks, Conditional Research, predictions or trading signals.",
    ),
)


def list_capabilities() -> tuple[CapabilityDescription, ...]:
    """One explicit declaration, without registration, probing or service creation."""
    return (_TRAILING_RETURN,)


def get_capability(id: str) -> CapabilityDescription:
    if id != _TRAILING_RETURN.id:
        raise CapabilityNotFound("Unknown Research capability")
    return _TRAILING_RETURN
