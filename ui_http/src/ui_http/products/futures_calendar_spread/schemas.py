"""Closed wire DTOs; only selected public business attributes are projected."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

Product = Literal["IF", "IH", "IC", "IM"]
Slot = Literal["M0", "M1", "Q1", "Q2"]
Stage = Literal["0_7", "8_21", "22_plus"]
Metric = Literal["signed_spread", "annualized_point_spread", "annualized_spread_ratio"]
Unit = Literal["index_points", "index_points_per_365_natural_days", "decimal_ratio"]


class Wire(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        from_attributes=True,
        allow_inf_nan=False,
    )


def canonical_date(value: object) -> date:
    if type(value) is date:
        return value
    if type(value) is not str:
        raise ValueError("Expected canonical date")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Expected canonical date")
    return parsed


DateOnly = Annotated[date, BeforeValidator(canonical_date)]


class DailyRequest(Wire):
    product_code: Product
    trade_date: DateOnly


class DailyEcho(DailyRequest):
    operation: Literal["query_daily_spreads"]


class Accounting(Wire):
    candidate_count: int
    valid_count: int
    not_applicable_count: int
    excluded_count: int


class Contract(Wire):
    contract_code: str
    close: float
    delist_date: DateOnly = Field(description="Real last trading date, not delivery date.")


class FinancialMetric(Wire):
    metric_id: Metric
    value: float
    unit: Unit


class FinancialMetrics(Wire):
    signed_spread: FinancialMetric
    annualized_point_spread: FinancialMetric
    annualized_spread_ratio: FinancialMetric
    delta_days: int
    definition_version: Literal["futures_calendar_spread_definition_v1"]


class PairObservation(Wire):
    product_code: Product
    trade_date: DateOnly
    near_slot: Slot
    far_slot: Slot
    near: Contract | None
    far: Contract | None
    delta_days: int | None
    near_dte_days: int | None
    expiry_stage: Stage | None
    metrics: FinancialMetrics | None
    outcome: Literal["valid", "not_applicable", "excluded"]
    reason: Literal["no_active_contract", "nonpositive_close"] | None


class DaySummary(Wire):
    trade_date: DateOnly
    status: Literal["open", "closed"]
    reason: Literal["non_trading_day"] | None


class Day(DaySummary):
    observations: tuple[PairObservation, ...]

    @model_validator(mode="after")
    def complete_day(self) -> Self:
        expected = 6 if self.status == "open" else 0
        if len(self.observations) != expected:
            raise ValueError("Incomplete Calendar Spread day projection")
        return self


class SourceContext(Wire):
    provider: str
    exchange: str
    price_field: str
    limitations: tuple[str, ...]


class DailyResponse(Wire):
    case: Literal["futures_calendar_spread_v1"]
    definition_version: Literal["futures_calendar_spread_definition_v1"]
    request: DailyEcho
    day: Day
    accounting: Accounting
    source_context: SourceContext


ErrorKind = Literal[
    "invalid_request",
    "incomplete_inputs",
    "upstream_unavailable",
    "input_contract_error",
    "slot_resolution_error",
    "calculation_failure",
    "statistical_failure",
    "internal_error",
    "transport_busy",
    "request_too_large",
    "response_too_large",
]
Param = Literal[
    "product_code",
    "trade_date",
    "history_start",
    "evaluation_date",
    "metric",
    "histogram_edges",
]


class ErrorBody(Wire):
    kind: ErrorKind
    detail: str
    param: Param | None = None


class DailyErrorResponse(Wire):
    error: ErrorBody
