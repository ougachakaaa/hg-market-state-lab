"""Closed wire DTOs; only selected public business attributes are projected."""

from datetime import date
from typing import Annotated, Literal, Self, cast

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


class DailyUnderlyingIndex(Wire):
    index_code: Literal["000300.SH", "000016.SH", "000905.SH", "000852.SH"]
    trade_date: DateOnly
    close: float | None
    availability: Literal["available", "not_applicable", "unavailable", "error"]
    reason_code: Literal[
        "non_trading_day", "cache_incomplete", "final_export_incomplete",
        "credential_missing", "cache_incompatible", "operation_unavailable",
        "malformed_export", "malformed_ensure_result", "upstream_request_rejected",
    ] | None
    failure_category: Literal[
        "incomplete_inputs", "upstream_unavailable", "input_contract_error",
    ] | None

    @model_validator(mode="after")
    def legal_state(self) -> Self:
        states: dict[str, set[tuple[str | None, str | None]]] = {
            "available": {(None, None)},
            "not_applicable": {("non_trading_day", None)},
            "unavailable": {("cache_incomplete", None)},
            "error": {
                ("final_export_incomplete", "incomplete_inputs"),
                ("credential_missing", "upstream_unavailable"),
                ("cache_incompatible", "upstream_unavailable"),
                ("operation_unavailable", "upstream_unavailable"),
                ("malformed_export", "input_contract_error"),
                ("malformed_ensure_result", "input_contract_error"),
                ("upstream_request_rejected", "input_contract_error"),
            },
        }
        if (self.reason_code, self.failure_category) not in states[self.availability]:
            raise ValueError("Invalid index reference state")
        if (self.close is not None) != (self.availability == "available"):
            raise ValueError("Invalid index reference Close availability")
        return self


class DailyFuturesSpotComparison(Wire):
    product_code: Product
    trade_date: DateOnly
    slot: Slot
    futures: Contract | None
    underlying_index: DailyUnderlyingIndex
    remaining_days: int | None
    expiry_stage: Stage | None
    signed_spread: float | None
    annualized_point_spread: float | None
    annualized_spread_ratio: float | None
    outcome: Literal["valid", "not_applicable", "excluded", "error"]
    reason: Literal[
        "no_active_contract", "index_reference_unavailable", "nonpositive_close",
        "expiry_day", "calculation_failure",
    ] | None
    failure_category: Literal[
        "incomplete_inputs", "upstream_unavailable", "input_contract_error", "calculation_failure",
    ] | None
    definition_version: Literal["daily_futures_spot_definition_v1"]

    @model_validator(mode="after")
    def legal_comparison(self) -> Self:
        metrics = (self.signed_spread, self.annualized_point_spread, self.annualized_spread_ratio)
        if self.underlying_index.trade_date != self.trade_date:
            raise ValueError("Spot reference date mismatch")
        if self.futures is None:
            legal = (self.outcome == "not_applicable" and self.reason == "no_active_contract"
                     and self.remaining_days is None and self.expiry_stage is None
                     and self.failure_category is None and all(m is None for m in metrics))
        else:
            d = self.remaining_days
            if (d is None or d < 0 or self.futures.delist_date < self.trade_date
                    or self.expiry_stage is None):
                raise ValueError("Invalid spot lifecycle")
            ref = self.underlying_index
            if ref.availability != "available":
                legal = (self.outcome == "not_applicable"
                         and self.reason == "index_reference_unavailable"
                         and self.failure_category == ref.failure_category
                         and all(m is None for m in metrics))
            elif self.futures.close <= 0 or (ref.close is not None and ref.close <= 0):
                legal = (self.outcome == "excluded" and self.reason == "nonpositive_close"
                         and self.failure_category is None and all(m is None for m in metrics))
            elif self.outcome == "error":
                legal = (self.reason == "calculation_failure"
                         and self.failure_category == "calculation_failure"
                         and all(m is None for m in metrics))
            elif d == 0:
                legal = (self.outcome == "not_applicable" and self.reason == "expiry_day"
                         and self.failure_category is None and self.signed_spread is not None
                         and self.annualized_point_spread is None
                         and self.annualized_spread_ratio is None)
            else:
                legal = (self.outcome == "valid" and self.reason is None
                         and self.failure_category is None and all(m is not None for m in metrics))
        if not legal:
            raise ValueError("Invalid futures–spot state")
        return self


class DailyResponse(Wire):
    case: Literal["futures_calendar_spread_v1"]
    definition_version: Literal["futures_calendar_spread_definition_v1"]
    request: DailyEcho
    day: Day
    accounting: Accounting
    source_context: SourceContext
    # Default applies to historical omission only; the field type rejects explicit null.
    underlying_index: DailyUnderlyingIndex = Field(
        default_factory=lambda: cast(DailyUnderlyingIndex, None),
        exclude_if=lambda value: value is None,
    )

    futures_spot_comparisons: tuple[DailyFuturesSpotComparison, ...] = Field(
        default_factory=lambda: cast(tuple[DailyFuturesSpotComparison, ...], None),
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def reference_association(self) -> Self:
        if "underlying_index" in self.model_fields_set:
            reference = self.underlying_index
            expected = {"IF": "000300.SH", "IH": "000016.SH",
                        "IC": "000905.SH", "IM": "000852.SH"}
            if (reference.index_code != expected[self.request.product_code]
                    or reference.trade_date != self.request.trade_date):
                raise ValueError("Index reference request association mismatch")
        if "futures_spot_comparisons" in self.model_fields_set:
            if "underlying_index" not in self.model_fields_set:
                raise ValueError("Missing comparison reference")
            items = self.futures_spot_comparisons
            expected_slots = ("M0", "M1", "Q1", "Q2") if self.day.status == "open" else ()
            if tuple(item.slot for item in items) != expected_slots:
                raise ValueError("Invalid comparison population")
            contracts = {}
            for pair in self.day.observations:
                for slot, contract in ((pair.near_slot, pair.near), (pair.far_slot, pair.far)):
                    if slot in contracts and contracts[slot] != contract:
                        raise ValueError("Inconsistent pair contract")
                    contracts[slot] = contract
            for item in items:
                if (item.product_code != self.request.product_code
                        or item.trade_date != self.request.trade_date
                        or item.underlying_index != self.underlying_index
                        or item.futures != contracts[item.slot]):
                    raise ValueError("Comparison association mismatch")
        return self


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


ReasonCode = Literal[
    "cache_incomplete", "final_export_incomplete", "credential_missing",
    "cache_incompatible", "operation_unavailable", "malformed_export",
    "malformed_ensure_result", "upstream_request_rejected",
]


class ErrorBody(Wire):
    kind: ErrorKind
    reason_code: ReasonCode | None = None
    detail: str
    param: Param | None = None


class DailyErrorResponse(Wire):
    error: ErrorBody
