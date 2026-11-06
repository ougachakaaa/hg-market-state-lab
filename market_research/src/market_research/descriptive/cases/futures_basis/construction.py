"""Pure deterministic Contract-day derivation and Slot-day association."""

from datetime import date
from math import isfinite, log
from typing import Literal, cast

from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange, FuturesDailyRow
from data_lake.datasets.tushare_index_daily import IndexDailyRange
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange

from .inputs import DEFINITION_VERSION, UNDERLYING, FuturesBasisRequest, PreparedFuturesBasisInputs
from .models import (
    SLOTS,
    CandidateSessions,
    ContractMetadata,
    DailyUniverseEvidence,
    SlotResolutionError,
)
from .observations import (
    METRICS,
    OUTCOMES,
    ContractDayObservation,
    FuturesBasisResult,
    ObservationConstructionError,
    ObservationOutcome,
    Outcome,
    OutcomeAccounting,
    OutcomeCollection,
    SlotDayObservation,
    SourceIssue,
    SourceReference,
)
from .resolution import detect_contract_transitions, resolve_daily_slots
from .validation import input_identity, require, validate_export, validate_request


def _validate_prepared(request: FuturesBasisRequest, prepared: PreparedFuturesBasisInputs) -> None:
    validate_request(request, check_today=False)
    require(prepared.request == request, "Prepared request mismatch")
    require(prepared.definition_version == DEFINITION_VERSION, "Wrong definition version")
    require(len(prepared.attempts) == 4, "Missing public requests")
    exports = (prepared.calendar_cffex, prepared.calendar_sse, prepared.futures, prepared.index)
    names = ("calendar_cffex", "calendar_sse", "futures", "index")
    for i, (attempt, export) in enumerate(zip(prepared.attempts, exports, strict=True)):
        query = attempt.request
        require(attempt.dependency == names[i], "Wrong dependency sequence")
        require(
            type(query.start_date) is date
            and type(query.end_date) is date
            and query.start_date == request.start_date
            and query.end_date == request.end_date,
            "Public request window mismatch",
        )
        if i < 2:
            require(
                isinstance(query, TradeCalendarRange)
                and query.exchange == ("CFFEX" if i == 0 else "SSE"),
                "Calendar request mismatch",
            )
            sessions: tuple[date, ...] = ()
        elif i == 2:
            require(
                isinstance(query, FuturesDailyRange)
                and tuple(query.product_codes) == (request.product_code,),
                "Futures request mismatch",
            )
            sessions = prepared.candidate_dates
        else:
            require(
                isinstance(query, IndexDailyRange)
                and tuple(query.index_codes) == (UNDERLYING[request.product_code],),
                "Index request mismatch",
            )
            sessions = prepared.underlying_sessions
        checked = validate_export(export, query, sessions)
        require(attempt.final_export == checked, "Final Export association mismatch")
        require(i == 3 or checked.coverage.complete, "Incomplete required input")
    require(
        prepared.candidate_dates
        == tuple(row.cal_date for row in prepared.calendar_cffex.records if row.is_open == 1),
        "Candidate dates mismatch",
    )
    require(
        prepared.underlying_sessions
        == tuple(row.cal_date for row in prepared.calendar_sse.records if row.is_open == 1),
        "Index sessions mismatch",
    )
    data, digest = input_identity(*exports)
    require(
        data == prepared.canonical_bytes and digest == prepared.input_fingerprint,
        "Prepared input identity mismatch",
    )


def _contract(
    row: FuturesDailyRow,
    metadata: ContractMetadata,
    underlying: float | None,
    missing_reason: str | None,
    prepared: PreparedFuturesBasisInputs,
) -> ContractDayObservation:
    day, code = row.trade_date, row.contract_code
    prefix = prepared.input_fingerprint
    fut_ref = SourceReference(prefix + ":futures", (code, day))
    idx_ref = SourceReference(prefix + ":index", (row.underlying_index_code, day))
    issues = []
    if row.close <= 0:
        issues.append(SourceIssue("nonpositive_futures_close", fut_ref, row.close))
    if underlying is not None and underlying <= 0:
        issues.append(SourceIssue("nonpositive_underlying_close", idx_ref, underlying))
    if missing_reason:
        issues.append(SourceIssue(missing_reason, idx_ref, None))
    dte = (row.delist_date - day).days
    state: Literal["Premium", "Parity", "Discount"] | None = None
    if any(issue.reason.startswith("nonpositive_") for issue in issues):
        status: Outcome = "excluded"
        reason = issues[0].reason
    elif missing_reason:
        status, reason = "unavailable", missing_reason
    else:
        status, reason = "eligible", None
    base = ObservationOutcome(status, reason=reason)
    value = ObservationOutcome(status, unit="index_points", reason=reason)
    ratio = ObservationOutcome(status, unit="decimal_ratio", reason=reason)
    annualized = ratio
    if status == "eligible":
        spot = cast(float, underlying)
        try:
            difference = row.close - spot
            relative = difference / spot
            require(isfinite(difference) and isfinite(relative), "Nonfinite raw basis")
            if dte > 0:
                quotient = row.close / spot
                require(isfinite(quotient) and quotient > 0, "Invalid binary64 log argument")
                annual = (365 / dte) * log(quotient)
                require(isfinite(annual), "Nonfinite log annualization")
                annualized = ObservationOutcome("eligible", annual, "decimal_ratio")
            else:
                annualized = ObservationOutcome(
                    "not_applicable", unit="decimal_ratio", reason="expiry_day"
                )
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            raise ObservationConstructionError(
                "numerical_failure", str(exc), prepared, (code, day)
            ) from exc
        state = "Premium" if difference > 0 else "Discount" if difference < 0 else "Parity"
        value = ObservationOutcome("eligible", difference, "index_points")
        ratio = ObservationOutcome("eligible", relative, "decimal_ratio")
    return ContractDayObservation(
        row.product_code,
        row.underlying_index_code,
        day,
        metadata,
        row.close,
        underlying,
        dte,
        base,
        value,
        ratio,
        annualized,
        state,
        tuple(issues),
        fut_ref,
        idx_ref,
        prefix,
        prepared.definition_version,
    )


def construct_observations(
    request: FuturesBasisRequest, prepared: PreparedFuturesBasisInputs
) -> FuturesBasisResult:
    try:
        _validate_prepared(request, prepared)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ObservationConstructionError("invalid_prepared_inputs", str(exc), prepared) from exc
    contracts: list[ContractDayObservation] = []
    slots: list[SlotDayObservation] = []
    resolutions = []
    by_day: dict[date, list[FuturesDailyRow]] = {}
    for row in prepared.futures.records:
        by_day.setdefault(row.trade_date, []).append(row)
    indices = {row.trade_date: row.close for row in prepared.index.records}
    underlying_sessions = set(prepared.underlying_sessions)
    try:
        for day in prepared.candidate_dates:
            rows = by_day.get(day, [])
            metadata = tuple(
                ContractMetadata(
                    row.contract_code,
                    row.product_code,
                    row.underlying_index_code,
                    row.delivery_month,
                    row.list_date,
                    row.delist_date,
                )
                for row in rows
            )
            evidence = DailyUniverseEvidence(
                request.product_code,
                day,
                True,
                tuple(row.contract_code for row in rows),
                prepared.input_fingerprint + ":futures",
            )
            resolved = resolve_daily_slots(request.product_code, day, metadata, evidence=evidence)
            resolutions.append(resolved)
            missing = (
                "underlying_session_closed"
                if day not in underlying_sessions
                else "underlying_fact_unavailable"
                if day not in indices
                else None
            )
            observations = {
                row.contract_code: _contract(row, meta, indices.get(day), missing, prepared)
                for row, meta in zip(rows, metadata, strict=True)
            }
            contracts.extend(observations.values())
            slots.extend(
                SlotDayObservation(
                    request.product_code,
                    day,
                    mapping.slot,
                    mapping,
                    observations.get(mapping.contract_code)
                    if mapping.contract_code is not None
                    else None,
                )
                for mapping in resolved.mappings
            )
        transitions = detect_contract_transitions(
            request.product_code,
            CandidateSessions(
                prepared.candidate_dates, prepared.input_fingerprint + ":calendar_cffex"
            ),
            tuple(resolutions),
        )
    except SlotResolutionError as exc:
        raise ObservationConstructionError("slot_resolution", exc.reason, prepared) from exc
    accounting = []
    for slot in SLOTS:
        selected = tuple(item for item in slots if item.slot == slot)
        for metric in METRICS:
            collections = []
            for outcome in OUTCOMES:
                keys = tuple(
                    item.identity for item in selected if item.outcome(metric).status == outcome
                )
                collections.append(
                    OutcomeCollection(
                        outcome, keys, len(keys) / len(selected) if selected else None
                    )
                )
            accounting.append(OutcomeAccounting(slot, metric, len(selected), tuple(collections)))
    return FuturesBasisResult(
        prepared, tuple(contracts), tuple(slots), tuple(resolutions), transitions, tuple(accounting)
    )
