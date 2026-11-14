"""Concrete wire projections of W2 values; no financial calculations."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


Product = Literal["IM", "IC", "IF", "IH"]
Profile = Literal["expiry_to_M1_v1", "expiry_to_Q1_v1"]
State = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"]
Dependency = Literal["calendar_cffex", "calendar_sse", "futures", "index"]
RunId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
Timestamp = Annotated[str, Field(json_schema_extra={"format": "date-time"})]


class FuturesRollRunRequest(DTO):
    product_code: Product
    start_date: date
    end_date: date
    strategy_profile: Profile


class FuturesRollImmutableRequest(FuturesRollRunRequest):
    case: Literal["futures_roll_long_v1"]


class FuturesRollFailure(DTO):
    stage: Literal[
        "request",
        "export",
        "ensure",
        "prepare",
        "replay",
        "analysis",
        "result_validation",
        "result_publication",
        "execution",
    ]
    category: Literal[
        "invalid_request",
        "upstream_operation",
        "incomplete_input",
        "invalid_public_input",
        "invalid_case_input",
        "slot_resolution",
        "missing_market_fact",
        "invalid_price",
        "roll_target_invalid",
        "invalid_contract_lifecycle",
        "invalid_position_state",
        "invalid_input",
        "invalid_target",
        "invalid_numeric",
        "invalid_accounting",
        "accounting_failure",
        "invalid_result",
        "invalid_evidence",
        "result_too_large",
        "serialization_failure",
        "storage_failure",
        "interrupted",
        "internal_failure",
    ]
    dependency: Dependency | None
    reason: str


class FuturesRollRunAccepted(DTO):
    run_id: RunId
    status: Literal["PENDING"]
    request: FuturesRollImmutableRequest
    created_at: Timestamp


class FuturesRollRun(DTO):
    run_id: RunId
    request: FuturesRollImmutableRequest
    status: State
    created_at: Timestamp
    started_at: Timestamp | None
    finished_at: Timestamp | None
    result_available: bool
    failure: FuturesRollFailure | None


class FuturesRollCoverage(DTO):
    requested_units: int
    successful_units: int
    missing_units: int
    pending_units: int
    failed_units: int
    complete: bool


class FuturesRollReadinessDependency(DTO):
    dependency: Dependency
    state: Literal["complete", "incomplete", "unavailable", "unknown"]
    reason: Literal[
        "cache_incompatible",
        "public_export_unavailable",
        "cache_complete",
        "cache_incomplete",
        "calendar_target_unknown",
        "underlying_unknown",
    ]
    coverage: FuturesRollCoverage | None


class FuturesRollPreflight(DTO):
    request: FuturesRollImmutableRequest
    ready: bool
    calendar_cffex: FuturesRollReadinessDependency
    futures: FuturesRollReadinessDependency
    index: FuturesRollReadinessDependency


class FuturesRollWindow(DTO):
    first_session: date
    last_session: date
    cffex_session_count: int


class FuturesRollBenchmark(DTO):
    index_code: str
    index_name: str
    first_close: float
    last_close: float


class FuturesRollNotional(DTO):
    index_first_close: float
    multiplier: float
    currency: Literal["CNY"]
    value: float


class FuturesRollDaily(DTO):
    trade_date: date
    daily_pnl: float
    cumulative_pnl: float
    equity: float
    daily_return: float
    cumulative_return: float
    benchmark_close: float
    benchmark_daily_return: float
    benchmark_cumulative_return: float
    benchmark_equity: float
    excess_cumulative_return: float
    drawdown: float
    benchmark_drawdown: float
    position_contract_code: str | None
    pnl_contract_code: str
    previous_close: float | None
    close: float


class FuturesRollTrade(DTO):
    trade_date: date
    side: Literal["BUY", "SELL"]
    contract_code: str
    price: float
    multiplier: float
    reason: Literal["entry", "expiry_close", "expiry_open", "study_end_close"]
    selection_slot: Literal["M1", "Q1"] | None


class FuturesRollRoll(DTO):
    trade_date: date
    old_contract_code: str
    old_slot: Literal["M0"]
    old_close: float
    new_contract_code: str
    new_slot: Literal["M1", "Q1"]
    new_close: float
    reason: Literal["expiry"]


class FuturesRollSummary(DTO):
    initial_notional: float
    total_pnl: float
    gross_return: float
    benchmark_return: float
    excess_return: float
    strategy_max_drawdown: float
    benchmark_max_drawdown: float
    execution_count: int
    roll_count: int


class FuturesRollCalendarRequest(DTO):
    exchange: str
    start_date: date
    end_date: date


class FuturesRollFuturesRequest(DTO):
    product_codes: list[str]
    start_date: date
    end_date: date


class FuturesRollIndexRequest(DTO):
    index_codes: list[str]
    start_date: date
    end_date: date


class FuturesRollPublicRequests(DTO):
    calendar_cffex: FuturesRollCalendarRequest
    futures: FuturesRollFuturesRequest
    index: FuturesRollIndexRequest


class FuturesRollCoverageEvidence(FuturesRollCoverage):
    dependency: str


class FuturesRollSource(DTO):
    dataset: str
    view: str
    export_schema_version: int


class FuturesRollEvidence(DTO):
    input_profile: Literal["futures_roll_long_inputs_v1"]
    input_fingerprint: str
    public_requests: FuturesRollPublicRequests
    coverage: list[FuturesRollCoverageEvidence]
    sources: list[FuturesRollSource]
    slot_resolution_authority: str
    definition_version: Literal["futures_roll_long_definition_v1"]
    result_profile: Literal["futures_roll_long_result_v1"]
    limitations: list[str]


class FuturesRollDateCoordinate(DTO):
    kind: Literal["date"]
    unit: Literal["date"]


class FuturesRollNumberCoordinate(DTO):
    kind: Literal["number"]
    unit: Literal["decimal_ratio"]


class FuturesRollDetail(DTO):
    label: str
    value: str


class FuturesRollMark(DTO):
    x: str = Field(json_schema_extra={"format": "date"})
    y: float | None
    segment_id: str
    details: list[FuturesRollDetail]


class FuturesRollLine(DTO):
    type: Literal["line"]
    version: Literal[2]
    x: FuturesRollDateCoordinate
    y: FuturesRollNumberCoordinate
    data: list[FuturesRollMark]


class FuturesRollAxis(DTO):
    id: str
    orientation: Literal["x", "y"]
    coordinate: FuturesRollDateCoordinate | FuturesRollNumberCoordinate


class FuturesRollBinding(DTO):
    id: str
    label: str
    layer: FuturesRollLine
    x_axis: str
    y_axis: str


class FuturesRollEvent(DTO):
    id: str
    x_axis: str
    x: str = Field(json_schema_extra={"format": "date"})
    label: str
    details: list[FuturesRollDetail]


class FuturesRollLayout(DTO):
    title: str


class FuturesRollPresentation(DTO):
    show_legend: bool
    zoom: bool
    pan: bool
    reset: bool


class FuturesRollView(DTO):
    version: Literal[2]
    axes: list[FuturesRollAxis]
    layers: list[FuturesRollBinding]
    events: list[FuturesRollEvent]
    layout: FuturesRollLayout
    presentation: FuturesRollPresentation


class FuturesRollViews(DTO):
    returns: FuturesRollView
    drawdown: FuturesRollView


class FuturesRollResult(DTO):
    profile: Literal["futures_roll_long_result_v1"]
    case: Literal["futures_roll_long_v1"]
    definition_version: Literal["futures_roll_long_definition_v1"]
    status: Literal["complete"]
    request: FuturesRollImmutableRequest
    window: FuturesRollWindow
    benchmark: FuturesRollBenchmark
    initial_notional: FuturesRollNotional
    daily: list[FuturesRollDaily]
    trades: list[FuturesRollTrade]
    rolls: list[FuturesRollRoll]
    summary: FuturesRollSummary
    evidence: FuturesRollEvidence
    views: FuturesRollViews


class FuturesRollResultResponse(DTO):
    run_id: RunId
    request: FuturesRollImmutableRequest
    data: FuturesRollResult


class FuturesRollHttpError(DTO):
    kind: Literal[
        "invalid_request",
        "request_too_large",
        "run_not_found",
        "run_busy",
        "result_not_ready",
        "corrupt",
        "result_too_large",
        "response_too_large",
        "unavailable",
        "read_busy",
        "internal_error",
    ]
    detail: str
    param: None


class FuturesRollErrorResponse(DTO):
    error: FuturesRollHttpError
