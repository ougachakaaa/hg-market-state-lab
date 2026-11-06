"""Strict wire types; public Research/Statistics constructors own semantic legality."""

from datetime import date
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    StrictFloat,
    StrictInt,
)

from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.execution import ResearchPlan
from market_research.descriptive.observation import DateWindow
from market_statistics import IntervalCountSpec, QuantileSpec, StatisticalSpec


class WireModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        from_attributes=True,
        allow_inf_nan=False,
    )


def date_only(value: object) -> date:
    if type(value) is date:
        return value
    if not isinstance(value, str):
        raise ValueError("Expected YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Expected YYYY-MM-DD")
    return parsed


DateOnly = Annotated[date, BeforeValidator(date_only)]


class EmptyParameters(WireModel):
    pass


class WindowBody(WireModel):
    start_date: DateOnly
    end_date: DateOnly


class QuantileBody(WireModel):
    method: Literal["quantile"]
    points: list[StrictFloat] = Field(
        description="Required finite probabilities, strictly increasing, non-empty, in [0,1]; "
        "validated by market_statistics. HTTP maximum 128 coordinates.",
    )


class IntervalCountBody(WireModel):
    method: Literal["interval_count"]
    edges: list[StrictFloat] = Field(
        description="Required finite strictly increasing boundaries, at least two; "
        "validated by market_statistics. HTTP maximum 128 coordinates.",
    )
    unit: Literal["decimal_ratio"]


SpecBody = Annotated[QuantileBody | IntervalCountBody, Field(discriminator="method")]


class AnalysisBody(WireModel):
    request_id: str = Field(
        description="Required non-empty unchanged ID; HTTP maximum 128 characters."
    )
    spec: SpecBody


PLAN_EXAMPLE: dict[str, JsonValue] = {
    "metric": "trailing_cumulative_return_v1",
    "metric_parameters": {},
    "subjects": ["000852.SH"],
    "horizons": [2],
    "windows": [{"start_date": "2024-01-10", "end_date": "2024-01-16"}],
    "analysis_requests": [
        {"request_id": "p10_p50_p90", "spec": {"method": "quantile", "points": [0.1, 0.5, 0.9]}},
        {
            "request_id": "distribution",
            "spec": {
                "method": "interval_count",
                "edges": [-0.2, 0.0, 0.2],
                "unit": "decimal_ratio",
            },
        },
    ],
    "on_job_failure": "continue",
}


class PlanBody(WireModel):
    model_config = ConfigDict(json_schema_extra={"examples": [PLAN_EXAMPLE]})

    metric: Literal["trailing_cumulative_return_v1"]
    metric_parameters: EmptyParameters
    subjects: list[str] = Field(description="Ordered, non-empty unique canonical full index_codes.")
    horizons: list[StrictInt] = Field(description="Positive trading sessions; HTTP maximum 20.")
    windows: list[WindowBody] = Field(
        description="Ordered unique inclusive date-only windows; "
        "no future end; HTTP maximum 93 days each."
    )
    analysis_requests: list[AnalysisBody] = Field(
        description="Ordered unique IDs; all required; HTTP maximum 4 per Job."
    )
    on_job_failure: Literal["continue", "stop"]

    def to_plan(self) -> ResearchPlan:
        return ResearchPlan(
            metric=self.metric,
            metric_parameters=self.metric_parameters.model_dump(),
            subjects=self.subjects,
            horizons=self.horizons,
            windows=[DateWindow(w.start_date, w.end_date) for w in self.windows],
            analysis_requests=[
                AnalysisRequest(r.request_id, to_spec(r.spec)) for r in self.analysis_requests
            ],
            on_job_failure=self.on_job_failure,
        )


def true_acknowledgment(value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError("acknowledge_acquisition must be explicitly true")
    return value


class ExecuteBody(PlanBody):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {**PLAN_EXAMPLE, "acknowledge_acquisition": True},
            ]
        }
    )
    acknowledge_acquisition: Annotated[
        Literal[True],
        BeforeValidator(true_acknowledgment),
    ] = Field(
        description="Must be explicitly true; DataLake source-fact caches may be written. "
        "This acknowledgment is not authentication or an authorization boundary.",
    )


def to_spec(body: SpecBody) -> StatisticalSpec:
    if isinstance(body, QuantileBody):
        return QuantileSpec(body.points)
    return IntervalCountSpec(body.edges, body.unit)


def spec_body(spec: StatisticalSpec) -> SpecBody:
    if isinstance(spec, QuantileSpec):
        return QuantileBody(method=spec.method, points=list(spec.points))
    if not isinstance(spec, IntervalCountSpec):
        raise TypeError("Unsupported statistical spec for research projection")
    return IntervalCountBody.model_validate(
        {
            "method": spec.method,
            "edges": list(spec.edges),
            "unit": spec.unit,
        }
    )


def plan_body(plan: ResearchPlan) -> PlanBody:
    return PlanBody.model_validate(
        {
            "metric": plan.metric,
            "metric_parameters": dict(plan.metric_parameters),
            "subjects": list(plan.subjects),
            "horizons": list(plan.horizons),
            "windows": [WindowBody.model_validate(w) for w in plan.windows],
            "analysis_requests": [
                AnalysisBody(request_id=r.request_id, spec=spec_body(r.spec))
                for r in plan.analysis_requests
            ],
            "on_job_failure": plan.on_job_failure,
        }
    )
