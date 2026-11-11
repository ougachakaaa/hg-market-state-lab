"""W2 synthetic input shape, metadata and price validation; no execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import NoReturn, cast

from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailyUniverseEvidence,
)

from .failures import FuturesRollError
from .models import (
    PRODUCT_CODES,
    STRATEGY_PROFILES,
    ContractClose,
    DecisionSlotEvidence,
    FuturesRollInput,
    IndexClose,
    ProductCode,
    SessionFacts,
    StrategyProfile,
)

_ALLOWED_PRODUCTS = frozenset(PRODUCT_CODES)
_ALLOWED_PROFILES = frozenset(STRATEGY_PROFILES)


@dataclass(frozen=True, slots=True)
class _ValidatedInputs:
    product_code: ProductCode
    sessions: tuple[date, ...]
    metadata: dict[str, ContractMetadata]
    facts: dict[date, dict[str, float]]
    decision_evidence: dict[date, DailyUniverseEvidence]
    strategy_profile: StrategyProfile
    index_closes: tuple[IndexClose, ...]


def _fail(
    category: str,
    reason: str,
    *,
    trade_date: date | None = None,
    contract_code: str | None = None,
    detail: str | None = None,
) -> NoReturn:
    raise FuturesRollError(
        category,
        reason,
        trade_date=trade_date,
        contract_code=contract_code,
        detail=detail,
    )


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_date_only(value: object) -> bool:
    return type(value) is date


def _valid_delivery_month(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 6 or not value.isascii():
        return False
    if not value.isdecimal():
        return False
    year = int(value[:4])
    month = int(value[4:])
    return 1 <= year <= 9999 and 1 <= month <= 12


def _validate_sessions(sessions: object) -> tuple[date, ...]:
    if not isinstance(sessions, tuple) or not sessions:
        _fail("invalid_case_input", "invalid_input_shape", detail="sessions: expected tuple")
    typed_sessions = cast(tuple[object, ...], sessions)
    if len(typed_sessions) < 2:
        _fail(
            "invalid_case_input",
            "insufficient_sessions",
            detail="at least two ordered sessions are required",
        )
    if any(not _is_date_only(value) for value in typed_sessions):
        _fail("invalid_case_input", "invalid_input_shape", detail="sessions: date-only values")
    days = cast(tuple[date, ...], typed_sessions)
    if any(previous == current for previous, current in zip(days, days[1:], strict=False)):
        _fail("invalid_case_input", "duplicate_session")
    if any(previous > current for previous, current in zip(days, days[1:], strict=False)):
        _fail("invalid_case_input", "session_order_not_increasing")
    return days


def _validate_contracts(
    product_code: ProductCode,
    contracts: object,
) -> dict[str, ContractMetadata]:
    if not isinstance(contracts, tuple):
        _fail("invalid_case_input", "invalid_input_shape", detail="contracts: expected tuple")
    metadata: dict[str, ContractMetadata] = {}
    months: set[str] = set()
    underlying: str | None = None
    for index, contract in enumerate(cast(tuple[object, ...], contracts)):
        if not isinstance(contract, ContractMetadata):
            _fail(
                "invalid_contract_lifecycle",
                "invalid_contract_metadata",
                detail=f"contracts[{index}]: expected ContractMetadata",
            )
        code = contract.contract_code
        if not _is_text(code):
            _fail("invalid_contract_lifecycle", "invalid_contract_metadata")
        if code in metadata:
            _fail(
                "invalid_contract_lifecycle",
                "duplicate_contract_code",
                contract_code=code,
            )
        if contract.product_code != product_code:
            _fail(
                "invalid_contract_lifecycle",
                "conflicting_product",
                contract_code=code,
            )
        if not _is_text(contract.underlying_index_code):
            _fail(
                "invalid_contract_lifecycle",
                "invalid_contract_metadata",
                contract_code=code,
            )
        if underlying is None:
            underlying = contract.underlying_index_code
        elif underlying != contract.underlying_index_code:
            _fail(
                "invalid_contract_lifecycle",
                "conflicting_underlying",
                contract_code=code,
            )
        month = contract.delivery_month
        if not _valid_delivery_month(month):
            _fail(
                "invalid_contract_lifecycle",
                "invalid_contract_metadata",
                contract_code=code,
            )
        if month in months:
            _fail(
                "invalid_contract_lifecycle",
                "duplicate_delivery_month",
                contract_code=code,
            )
        months.add(month)
        if not _is_date_only(contract.list_date) or not _is_date_only(contract.delist_date):
            _fail(
                "invalid_contract_lifecycle",
                "invalid_contract_metadata",
                contract_code=code,
            )
        if contract.list_date > contract.delist_date:
            _fail(
                "invalid_contract_lifecycle",
                "invalid_contract_metadata",
                contract_code=code,
            )
        metadata[code] = contract
    return metadata


def _validated_close(contract_code: str, value: object) -> float:
    if type(value) not in (int, float):
        _fail("invalid_price", "non_finite_close", contract_code=contract_code)
    try:
        close = float(cast(float, value))
    except (OverflowError, ValueError):
        _fail("invalid_price", "non_finite_close", contract_code=contract_code)
    if not isfinite(close):
        _fail("invalid_price", "non_finite_close", contract_code=contract_code)
    if close <= 0:
        _fail("invalid_price", "non_positive_close", contract_code=contract_code)
    return close


def _validate_session_facts(
    sessions: tuple[date, ...],
    metadata: dict[str, ContractMetadata],
    session_facts: object,
) -> dict[date, dict[str, float]]:
    if not isinstance(session_facts, tuple):
        _fail(
            "invalid_case_input",
            "invalid_input_shape",
            detail="session_facts: expected tuple",
        )
    facts: dict[date, dict[str, float]] = {}
    known_days = set(sessions)
    for index, item in enumerate(cast(tuple[object, ...], session_facts)):
        if not isinstance(item, SessionFacts):
            _fail(
                "invalid_case_input",
                "invalid_input_shape",
                detail=f"session_facts[{index}]: expected SessionFacts",
            )
        day = item.trade_date
        if not _is_date_only(day):
            _fail(
                "invalid_case_input",
                "invalid_session_facts",
                detail=f"session_facts[{index}]: date-only trade_date required",
            )
        if day not in known_days:
            _fail(
                "invalid_case_input",
                "invalid_session_facts",
                trade_date=day,
                detail="session fact outside the supplied session sequence",
            )
        if day in facts:
            _fail("invalid_case_input", "duplicate_session_facts", trade_date=day)
        if not isinstance(item.closes, tuple):
            _fail(
                "invalid_case_input",
                "invalid_session_facts",
                trade_date=day,
                detail="closes: expected tuple",
            )
        closes: dict[str, float] = {}
        for close_index, close_item in enumerate(item.closes):
            if not isinstance(close_item, ContractClose):
                _fail(
                    "invalid_case_input",
                    "invalid_session_facts",
                    trade_date=day,
                    detail=f"closes[{close_index}]: expected ContractClose",
                )
            code = close_item.contract_code
            if not _is_text(code):
                _fail(
                    "invalid_case_input",
                    "invalid_session_facts",
                    trade_date=day,
                )
            if code not in metadata:
                _fail(
                    "invalid_case_input",
                    "unknown_contract_fact",
                    trade_date=day,
                    contract_code=code,
                )
            if code in closes:
                _fail(
                    "invalid_case_input",
                    "duplicate_contract_close",
                    trade_date=day,
                    contract_code=code,
                )
            closes[code] = _validated_close(code, close_item.close)
        facts[day] = closes
    missing = [day for day in sessions if day not in facts]
    if missing:
        _fail(
            "missing_market_fact",
            "missing_session_facts",
            trade_date=missing[0],
            detail="one synthetic session fact row is required per session",
        )
    return facts


def _validate_decision_slots(
    product_code: ProductCode,
    sessions: tuple[date, ...],
    metadata: dict[str, ContractMetadata],
    decision_slots: object,
) -> dict[date, DailyUniverseEvidence]:
    if not isinstance(decision_slots, tuple):
        _fail(
            "invalid_case_input",
            "invalid_input_shape",
            detail="decision_slots: expected tuple",
        )
    by_day: dict[date, DailyUniverseEvidence] = {}
    known_days = set(sessions)
    for index, item in enumerate(cast(tuple[object, ...], decision_slots)):
        if not isinstance(item, DecisionSlotEvidence):
            _fail(
                "slot_resolution",
                "invalid_decision_evidence",
                detail=f"decision_slots[{index}]: expected DecisionSlotEvidence",
            )
        day = item.trade_date
        if not _is_date_only(day) or day not in known_days:
            _fail(
                "slot_resolution",
                "invalid_decision_evidence",
                detail="decision evidence date is not a supplied session",
            )
        if day in by_day:
            _fail("slot_resolution", "invalid_decision_evidence", trade_date=day)
        evidence = item.evidence
        if not isinstance(evidence, DailyUniverseEvidence):
            _fail("slot_resolution", "invalid_decision_evidence", trade_date=day)
        if (
            evidence.product_code != product_code
            or not _is_date_only(evidence.trade_date)
            or evidence.trade_date != day
            or evidence.complete is not True
            or not _is_text(evidence.source_export_ref)
        ):
            _fail("slot_resolution", "invalid_decision_evidence", trade_date=day)
        codes = evidence.active_contract_codes
        if (
            not isinstance(codes, tuple)
            or any(not _is_text(code) for code in codes)
            or len(set(codes)) != len(codes)
        ):
            _fail("slot_resolution", "invalid_decision_evidence", trade_date=day)
        for code in codes:
            if code not in metadata:
                _fail(
                    "missing_market_fact",
                    "missing_active_contract_metadata",
                    trade_date=day,
                    contract_code=code,
                )
        by_day[day] = evidence
    return by_day


def _validate_index_closes(
    sessions: tuple[date, ...], index_closes: object
) -> tuple[IndexClose, ...]:
    """Validate the sole, immutable capital/benchmark price source without repairing it."""
    if not isinstance(index_closes, tuple):
        _fail("invalid_case_input", "invalid_index_closes")
    rows = cast(tuple[object, ...], index_closes)
    for row in rows:
        if not isinstance(row, IndexClose) or not _is_date_only(row.trade_date):
            _fail("invalid_case_input", "invalid_index_closes")
    typed_rows = cast(tuple[IndexClose, ...], rows)
    if tuple(row.trade_date for row in typed_rows) != sessions:
        _fail("missing_market_fact", "benchmark_session_mismatch")
    for row in typed_rows:
        try:
            _validated_close("benchmark", row.close)
        except FuturesRollError as exc:
            raise FuturesRollError(
                exc.category, exc.reason, trade_date=row.trade_date, detail="index_close"
            ) from exc
    return typed_rows


def _validate_inputs(inputs: object) -> _ValidatedInputs:
    if not isinstance(inputs, FuturesRollInput):
        _fail(
            "invalid_case_input",
            "invalid_input_shape",
            detail="expected FuturesRollInput",
        )
    product = inputs.product_code
    if not isinstance(product, str) or product not in _ALLOWED_PRODUCTS:
        _fail("invalid_case_input", "invalid_product_code")
    product_code = cast(ProductCode, product)
    profile = inputs.strategy_profile
    if not isinstance(profile, str) or profile not in _ALLOWED_PROFILES:
        _fail("invalid_case_input", "invalid_strategy_profile")
    strategy_profile = cast(StrategyProfile, profile)
    sessions = _validate_sessions(inputs.sessions)
    index_closes = _validate_index_closes(sessions, inputs.index_closes)
    metadata = _validate_contracts(product_code, inputs.contracts)
    facts = _validate_session_facts(sessions, metadata, inputs.session_facts)
    decision_evidence = _validate_decision_slots(
        product_code,
        sessions,
        metadata,
        inputs.decision_slots,
    )
    return _ValidatedInputs(
        product_code=product_code,
        sessions=sessions,
        metadata=metadata,
        facts=facts,
        decision_evidence=decision_evidence,
        strategy_profile=strategy_profile,
        index_closes=index_closes,
    )
