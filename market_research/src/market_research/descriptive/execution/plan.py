"""Immutable explicit plans and complete pure expansion through shared Job preflight."""

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from ..association import AnalysisRequest
from ..observation import DateWindow, JobIdentity, ObservationJobSpec
from .api import _preflight
from .models import InvalidPlan


def _sequence[T](value: Sequence[T], name: str) -> tuple[T, ...]:
    if not isinstance(value, Sequence) or isinstance(
        value, str | bytes | bytearray | Mapping | Set
    ):
        raise InvalidPlan(f"{name} must be an ordered non-empty sequence")
    result = tuple(value)
    if not result:
        raise InvalidPlan(f"{name} must not be empty")
    return result


@dataclass(frozen=True)
class ResearchPlan:
    metric: str
    metric_parameters: Mapping[str, object]
    subjects: Sequence[str]
    horizons: Sequence[int]
    windows: Sequence[DateWindow]
    analysis_requests: Sequence[AnalysisRequest]
    on_job_failure: Literal["continue", "stop"]

    def __post_init__(self) -> None:
        try:
            if not isinstance(self.metric_parameters, Mapping):
                raise ValueError("metric_parameters must be an explicit mapping")
            object.__setattr__(
                self, "metric_parameters", MappingProxyType(dict(self.metric_parameters))
            )
            for name in ("subjects", "horizons", "windows", "analysis_requests"):
                object.__setattr__(self, name, _sequence(getattr(self, name), name))
            preflight_plan(self)
        except InvalidPlan:
            raise
        except Exception as exc:
            raise InvalidPlan(f"{type(exc).__name__}: {exc}") from exc


def preflight_plan(plan: ResearchPlan) -> tuple[tuple[ObservationJobSpec, JobIdentity], ...]:
    """Materialize and validate every fixed Job before the caller can begin execution."""
    try:
        if type(plan) is not ResearchPlan:
            raise ValueError("Expected public ResearchPlan")
        if not isinstance(plan.metric_parameters, Mapping):
            raise ValueError("metric_parameters must be an explicit mapping")
        if not isinstance(plan.on_job_failure, str) or plan.on_job_failure not in (
            "continue",
            "stop",
        ):
            raise ValueError("on_job_failure must be explicitly continue or stop")
        for name in ("subjects", "horizons", "windows", "analysis_requests"):
            values = _sequence(getattr(plan, name), name)
            if type(getattr(plan, name)) is not tuple:
                raise ValueError(f"{name} must retain its immutable tuple snapshot")
            if name != "analysis_requests":
                for index, value in enumerate(values):
                    if value in values[:index]:
                        raise ValueError(f"Duplicate {name}: {value!r}")
        jobs = tuple(
            ObservationJobSpec(subject, plan.metric, plan.metric_parameters, horizon, window)
            for subject in plan.subjects
            for horizon in plan.horizons
            for window in plan.windows
        )
        return tuple((job, _preflight(job, plan.analysis_requests)[0]) for job in jobs)
    except InvalidPlan:
        raise
    except Exception as exc:
        raise InvalidPlan(f"{type(exc).__name__}: {exc}") from exc
