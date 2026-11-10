"""Transport envelope only; report data remains the versioned producer projection."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


Product = Literal["IM", "IC", "IF", "IH"]
Status = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"]
ScientificStatus = Literal["complete", "partial"]
RunId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]


class FuturesBasisRunRequest(DTO):
    product_code: Product
    start_date: date
    end_date: date


class FuturesBasisImmutableRequest(DTO):
    case: Literal["futures_basis_v1"]
    product_code: Product
    start_date: date
    end_date: date
    analysis_profile: Literal["r01a_standard_v1"]


class FuturesBasisFailure(DTO):
    stage: Literal[
        "input_preparation",
        "observation_construction",
        "report_composition",
        "result_publication",
        "execution",
    ]
    category: Literal[
        "invalid_request",
        "upstream_operation",
        "invalid_public_input",
        "invalid_prepared_inputs",
        "slot_resolution",
        "numerical_failure",
        "invalid_report_request",
        "composition_failure",
        "result_too_large",
        "serialization_failure",
        "interrupted",
        "internal_failure",
    ]
    dependency: Literal["request", "calendar_cffex", "calendar_sse", "futures", "index"] | None
    reason: str


class FuturesBasisRunAccepted(DTO):
    run_id: RunId
    status: Literal["PENDING"]
    request: FuturesBasisImmutableRequest
    created_at: str = Field(json_schema_extra={"format": "date-time"})


class FuturesBasisRun(DTO):
    run_id: RunId
    request: FuturesBasisImmutableRequest
    status: Status
    created_at: str = Field(json_schema_extra={"format": "date-time"})
    started_at: str | None = Field(json_schema_extra={"format": "date-time"})
    finished_at: str | None = Field(json_schema_extra={"format": "date-time"})
    result_available: bool
    result_status: ScientificStatus | None
    failure: FuturesBasisFailure | None


class FuturesBasisReportResponse(DTO):
    run_id: RunId
    request: FuturesBasisImmutableRequest
    result_status: ScientificStatus
    data: dict[str, JsonValue] = Field(
        description="Complete Research-owned futures_basis_report_evidence_v1 reader projection."
    )


class FuturesBasisError(DTO):
    kind: Literal[
        "invalid_request",
        "request_too_large",
        "run_busy",
        "unavailable",
        "internal_error",
        "run_not_found",
        "corrupt",
        "unsupported_version",
        "result_not_ready",
        "result_unavailable",
        "response_too_large",
        "read_busy",
    ]
    detail: str
    param: Literal["product_code", "start_date", "end_date"] | None = None


class FuturesBasisErrorResponse(DTO):
    error: FuturesBasisError


class FuturesBasisCoverage(DTO):
    requested_units: int = Field(ge=0)
    successful_units: int = Field(ge=0)
    missing_units: int = Field(ge=0)
    pending_units: int = Field(ge=0)
    failed_units: int = Field(ge=0)
    complete: bool


class FuturesBasisPreflightDependency(DTO):
    dependency: Literal["calendar_cffex", "calendar_sse", "futures", "index"]
    scope: Literal["window", "today"]
    state: Literal["complete", "needs_fetch", "unknown", "operation_error", "contract_error"]
    coverage: FuturesBasisCoverage | None
    reason_code: (
        Literal[
            "cache_incomplete",
            "prerequisite_incomplete",
            "prerequisite_unavailable",
            "operation_failed",
            "invalid_evidence",
        ]
        | None
    )
    message: str


class FuturesBasisPreflightResponse(DTO):
    request: FuturesBasisImmutableRequest
    checked_at: str = Field(json_schema_extra={"format": "date-time"})
    market_date: date
    submission: Literal["allowed", "confirm_required", "blocked"]
    today_gate: Literal["not_applicable", "ready", "not_ready", "unknown"]
    dependencies: list[FuturesBasisPreflightDependency]
