"""Daily-only, independent SSE/Index acquisition and immutable reference evidence."""

from dataclasses import dataclass, fields, replace
from datetime import date
from math import isfinite
from typing import Any, Literal, Protocol, cast

from data_lake import (
    CacheIncompatibleError,
    CredentialMissingError,
    EnsureResult,
    InvalidRequestError,
    OperationError,
)
from data_lake.datasets.tushare_index_daily import (
    IndexDailyExport,
    IndexDailyRange,
    IndexDailyRow,
    IndexDailyScope,
)
from data_lake.datasets.tushare_index_daily import (
    create_service as create_index_service,
)
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
)
from data_lake.datasets.tushare_trade_calendar import (
    create_service as create_calendar_service,
)

from .inputs import UNDERLYING, CalendarSpreadRequest
from .preparation import CalendarService, ExecutionCalendarService
from .validation import (
    PublicInputError,
    _coverage,
    _sequence,
    _Window,
    require,
    validate_calendar,
    validate_ensure,
)


class IndexService(Protocol):
    def export(self, request: IndexDailyRange) -> IndexDailyExport: ...


class ExecutionIndexService(IndexService, Protocol):
    def ensure(self, request: IndexDailyRange) -> EnsureResult: ...


@dataclass(frozen=True, slots=True)
class DailyUnderlyingIndexReference:
    index_code: str
    trade_date: date
    close: float | None
    availability: Literal["available", "not_applicable", "unavailable", "error"]
    reason_code: str | None
    failure_category: str | None


@dataclass(frozen=True, slots=True)
class DailyIndexPreparationAttempt:
    dependency: Literal["sse_calendar", "index"]
    request: TradeCalendarRange | IndexDailyRange
    preliminary_export: TradeCalendarExport | IndexDailyExport | None = None
    ensure_result: EnsureResult | None = None
    final_export: TradeCalendarExport | IndexDailyExport | None = None


@dataclass(frozen=True, slots=True)
class DailyUnderlyingIndexEvidence:
    attempts: tuple[DailyIndexPreparationAttempt, ...]
    dependency: str | None = None
    operation: str | None = None
    reason_code: str | None = None
    failure_category: str | None = None
    exception: Exception | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempts", tuple(self.attempts))


def validate_index_export(raw: Any, request: IndexDailyRange) -> IndexDailyExport:
    require(type(raw.dataset) is str and raw.dataset == "tushare_index_daily", "Wrong dataset")
    require(type(raw.view) is str and raw.view == "index_daily", "Wrong view")
    require(
        type(raw.export_schema_version) is int and raw.export_schema_version == 1,
        "Wrong index schema",
    )
    codes = _sequence(raw.scope.index_codes)
    require(
        all(type(code) is str for code in codes) and codes == request.index_codes,
        "Wrong index scope",
    )
    require(
        type(raw.window.start_date) is date
        and type(raw.window.end_date) is date
        and raw.window.start_date == request.start_date
        and raw.window.end_date == request.end_date,
        "Wrong index window",
    )
    # Reached only after retained complete SSE proof of one open target.
    proof = _coverage(raw.coverage, 1)
    records = []
    for row in _sequence(raw.records):
        values = {}
        for field in fields(IndexDailyRow):
            name = field.name
            value = getattr(row, name)
            if name == "trade_date":
                require(type(value) is date and value == request.start_date, "Wrong index date")
            elif name in {"index_code", "symbol", "name", "market", "publisher", "category"}:
                require(
                    (name in {"publisher", "category"} and value is None)
                    or (type(value) is str and bool(value.strip())),
                    "Invalid index text",
                )
            else:
                require(type(value) is float and isfinite(value), "Invalid index number")
                if name in {"volume", "amount"}:
                    require(value >= 0, "Negative index activity")
            values[name] = value
        require(
            row.index_code == request.index_codes[0] and row.symbol == row.index_code.split(".")[0],
            "Wrong index identity",
        )
        records.append(IndexDailyRow(**values))
    # One selected index/date: count equality proves uniqueness and ordering too.
    require(len(records) == proof.successful_units, "Index row/success mismatch")
    return IndexDailyExport(
        "tushare_index_daily",
        "index_daily",
        1,
        IndexDailyScope(tuple(request.index_codes)),
        _Window(request.start_date, request.end_date),
        proof,
        tuple(records),
    )


class _ReferenceFailure(Exception):
    def __init__(self, code: str, category: str | None) -> None:
        self.code, self.category = code, category


def prepare_daily_index(
    product_code: str,
    trade_date: date,
    *,
    calendar_service: CalendarService | None,
    index_service: IndexService | None,
    execution: bool,
) -> tuple[DailyUnderlyingIndexReference, DailyUnderlyingIndexEvidence]:
    """Called only after the full Daily request and core construction succeeded."""
    index_code = UNDERLYING[product_code]
    context = CalendarSpreadRequest(product_code, trade_date, trade_date)
    attempts: list[DailyIndexPreparationAttempt] = []
    dependency: Literal["sse_calendar", "index"] = "sse_calendar"
    operation = "export"

    def obtain(dep: Literal["sse_calendar", "index"]) -> Any:
        nonlocal dependency, operation
        dependency, operation = dep, "export"
        calendar = dep == "sse_calendar"
        request = (
            TradeCalendarRange("SSE", trade_date, trade_date)
            if calendar
            else IndexDailyRange((index_code,), trade_date, trade_date)
        )
        attempts.append(DailyIndexPreparationAttempt(dep, request))
        service = (
            (calendar_service if calendar_service is not None else create_calendar_service())
            if calendar
            else (index_service if index_service is not None else create_index_service())
        )

        def export() -> Any:
            raw = (
                cast(CalendarService, service).export(cast(TradeCalendarRange, request))
                if calendar
                else cast(IndexService, service).export(cast(IndexDailyRange, request))
            )
            try:
                return (
                    validate_calendar(raw, context, exchange="SSE")
                    if calendar
                    else validate_index_export(raw, cast(IndexDailyRange, request))
                )
            except (PublicInputError, AttributeError, TypeError) as exc:
                raise _ReferenceFailure("malformed_export", "input_contract_error") from exc

        initial = export()
        attempts[-1] = replace(attempts[-1], preliminary_export=initial)
        if execution and not initial.coverage.complete:
            operation = "ensure"
            raw = (
                cast(ExecutionCalendarService, service).ensure(cast(TradeCalendarRange, request))
                if calendar
                else cast(ExecutionIndexService, service).ensure(cast(IndexDailyRange, request))
            )
            try:
                ensured = validate_ensure(
                    raw,
                    context,
                    "calendar" if calendar else "index",
                    (trade_date,),
                    target_code="SSE" if calendar else index_code,
                    one_record_per_unit=True,
                )
            except (PublicInputError, AttributeError, TypeError) as exc:
                raise _ReferenceFailure("malformed_ensure_result", "input_contract_error") from exc
            attempts[-1] = replace(attempts[-1], ensure_result=ensured)
            operation = "final_export"
            final = export()
        else:
            final = initial
        attempts[-1] = replace(attempts[-1], final_export=final)
        if not final.coverage.complete:
            raise _ReferenceFailure(
                "final_export_incomplete" if execution else "cache_incomplete",
                "incomplete_inputs" if execution else None,
            )
        return final

    try:
        calendar = obtain("sse_calendar")
        if calendar.records[0].is_open == 0:
            return (
                DailyUnderlyingIndexReference(
                    index_code, trade_date, None, "not_applicable", "non_trading_day", None
                ),
                DailyUnderlyingIndexEvidence(tuple(attempts)),
            )
        index = obtain("index")
        return (
            DailyUnderlyingIndexReference(
                index_code, trade_date, index.records[0].close, "available", None, None
            ),
            DailyUnderlyingIndexEvidence(tuple(attempts)),
        )
    except _ReferenceFailure as exc:
        code, category, cause = exc.code, exc.category, cast(Exception | None, exc.__cause__)
    except CredentialMissingError as exc:
        code, category, cause = "credential_missing", "upstream_unavailable", exc
    except CacheIncompatibleError as exc:
        code, category, cause = "cache_incompatible", "upstream_unavailable", exc
    except InvalidRequestError as exc:
        code, category, cause = "upstream_request_rejected", "input_contract_error", exc
    except OperationError as exc:
        code, category, cause = "operation_unavailable", "upstream_unavailable", exc
    return (
        DailyUnderlyingIndexReference(
            index_code,
            trade_date,
            None,
            "unavailable" if category is None else "error",
            code,
            category,
        ),
        DailyUnderlyingIndexEvidence(tuple(attempts), dependency, operation, code, category, cause),
    )
