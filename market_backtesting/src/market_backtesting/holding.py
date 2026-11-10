"""Pure deterministic real-contract entry, hold, roll and exit simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import NoReturn, cast

from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailySlotResolution,
    DailyUniverseEvidence,
    SlotResolutionError,
    resolve_daily_slots,
)

from .failures import HoldingSimulationError
from .models import (
    PRODUCT_CODES,
    STRATEGY_PROFILES,
    ContractClose,
    DailyHolding,
    DecisionSlotEvidence,
    Execution,
    ExecutionReason,
    HoldingSimulationInput,
    ProductCode,
    RollEvent,
    SelectionSlot,
    SessionFacts,
    Side,
    Slot,
    StrategyProfile,
    StrategyTimeline,
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


def _fail(
    category: str,
    reason: str,
    *,
    trade_date: date | None = None,
    contract_code: str | None = None,
    detail: str | None = None,
) -> NoReturn:
    raise HoldingSimulationError(
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
        _fail("invalid_holding_input", "invalid_input_shape", detail="sessions: expected tuple")
    typed_sessions = cast(tuple[object, ...], sessions)
    if len(typed_sessions) < 2:
        _fail(
            "invalid_holding_input",
            "insufficient_sessions",
            detail="at least two ordered sessions are required",
        )
    if any(not _is_date_only(value) for value in typed_sessions):
        _fail("invalid_holding_input", "invalid_input_shape", detail="sessions: date-only values")
    days = cast(tuple[date, ...], typed_sessions)
    if any(previous == current for previous, current in zip(days, days[1:], strict=False)):
        _fail("invalid_holding_input", "duplicate_session")
    if any(previous > current for previous, current in zip(days, days[1:], strict=False)):
        _fail("invalid_holding_input", "session_order_not_increasing")
    return days


def _validate_contracts(
    product_code: ProductCode,
    contracts: object,
) -> dict[str, ContractMetadata]:
    if not isinstance(contracts, tuple):
        _fail("invalid_holding_input", "invalid_input_shape", detail="contracts: expected tuple")
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
            "invalid_holding_input",
            "invalid_input_shape",
            detail="session_facts: expected tuple",
        )
    facts: dict[date, dict[str, float]] = {}
    known_days = set(sessions)
    for index, item in enumerate(cast(tuple[object, ...], session_facts)):
        if not isinstance(item, SessionFacts):
            _fail(
                "invalid_holding_input",
                "invalid_input_shape",
                detail=f"session_facts[{index}]: expected SessionFacts",
            )
        day = item.trade_date
        if not _is_date_only(day):
            _fail(
                "invalid_holding_input",
                "invalid_session_facts",
                detail=f"session_facts[{index}]: date-only trade_date required",
            )
        if day not in known_days:
            _fail(
                "invalid_holding_input",
                "invalid_session_facts",
                trade_date=day,
                detail="session fact outside the supplied session sequence",
            )
        if day in facts:
            _fail("invalid_holding_input", "duplicate_session_facts", trade_date=day)
        if not isinstance(item.closes, tuple):
            _fail(
                "invalid_holding_input",
                "invalid_session_facts",
                trade_date=day,
                detail="closes: expected tuple",
            )
        closes: dict[str, float] = {}
        for close_index, close_item in enumerate(item.closes):
            if not isinstance(close_item, ContractClose):
                _fail(
                    "invalid_holding_input",
                    "invalid_session_facts",
                    trade_date=day,
                    detail=f"closes[{close_index}]: expected ContractClose",
                )
            code = close_item.contract_code
            if not _is_text(code):
                _fail(
                    "invalid_holding_input",
                    "invalid_session_facts",
                    trade_date=day,
                )
            if code not in metadata:
                _fail(
                    "invalid_holding_input",
                    "unknown_contract_fact",
                    trade_date=day,
                    contract_code=code,
                )
            if code in closes:
                _fail(
                    "invalid_holding_input",
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
            "invalid_holding_input",
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


def _validate_inputs(inputs: object) -> _ValidatedInputs:
    if not isinstance(inputs, HoldingSimulationInput):
        _fail(
            "invalid_holding_input",
            "invalid_input_shape",
            detail="expected HoldingSimulationInput",
        )
    product = inputs.product_code
    if not isinstance(product, str) or product not in _ALLOWED_PRODUCTS:
        _fail("invalid_holding_input", "invalid_product_code")
    product_code = cast(ProductCode, product)
    profile = inputs.strategy_profile
    if not isinstance(profile, str) or profile not in _ALLOWED_PROFILES:
        _fail("invalid_holding_input", "invalid_strategy_profile")
    strategy_profile = cast(StrategyProfile, profile)
    sessions = _validate_sessions(inputs.sessions)
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
    )


def _resolve_decision(
    validated: _ValidatedInputs,
    day: date,
) -> DailySlotResolution:
    evidence = validated.decision_evidence.get(day)
    if evidence is None:
        _fail("slot_resolution", "missing_decision_evidence", trade_date=day)
    contracts = tuple(
        validated.metadata[code] for code in evidence.active_contract_codes
    )
    try:
        return resolve_daily_slots(
            validated.product_code,
            day,
            contracts,
            evidence=evidence,
        )
    except SlotResolutionError as exc:
        raise HoldingSimulationError(
            "slot_resolution",
            "w1_slot_resolution_error",
            trade_date=day,
            detail=f"{exc.category}: {exc.reason}",
        ) from exc


def _target_for_slot(
    resolution: DailySlotResolution,
    target_slot: SelectionSlot,
) -> ContractMetadata:
    for mapping in resolution.mappings:
        if mapping.slot == target_slot:
            if mapping.status != "resolved" or mapping.contract is None:
                _fail(
                    "roll_target_invalid",
                    "target_not_resolved",
                    trade_date=resolution.trade_date,
                )
            return mapping.contract
    _fail(
        "roll_target_invalid",
        "target_not_resolved",
        trade_date=resolution.trade_date,
    )


def _old_slot_for_held(
    resolution: DailySlotResolution,
    held: ContractMetadata,
) -> Slot:
    for mapping in resolution.mappings:
        if mapping.contract_code == held.contract_code:
            if mapping.slot != "M0":
                _fail(
                    "invalid_contract_lifecycle",
                    "expiring_held_contract_not_m0",
                    trade_date=resolution.trade_date,
                    contract_code=held.contract_code,
                )
            return mapping.slot
    _fail(
        "invalid_contract_lifecycle",
        "held_contract_missing_from_active_set",
        trade_date=resolution.trade_date,
        contract_code=held.contract_code,
    )


def _close(
    validated: _ValidatedInputs,
    day: date,
    contract_code: str,
) -> float:
    session_facts = validated.facts.get(day)
    if session_facts is None:
        _fail(
            "missing_market_fact",
            "missing_session_facts",
            trade_date=day,
        )
    close = session_facts.get(contract_code)
    if close is None:
        _fail(
            "missing_market_fact",
            "missing_contract_row",
            trade_date=day,
            contract_code=contract_code,
        )
    return close


def _validate_target(
    validated: _ValidatedInputs,
    day: date,
    target: ContractMetadata,
    selected_slot: SelectionSlot,
    *,
    held_contract_code: str | None,
) -> tuple[float, SelectionSlot]:
    if held_contract_code is not None and target.contract_code == held_contract_code:
        _fail(
            "roll_target_invalid",
            "target_equal_held_contract",
            trade_date=day,
            contract_code=target.contract_code,
        )
    if not (_is_date_only(target.list_date) and _is_date_only(target.delist_date)):
        _fail(
            "invalid_contract_lifecycle",
            "invalid_contract_metadata",
            trade_date=day,
            contract_code=target.contract_code,
        )
    if target.delist_date < day:
        _fail(
            "roll_target_invalid",
            "target_expired",
            trade_date=day,
            contract_code=target.contract_code,
        )
    if target.delist_date <= day:
        _fail(
            "roll_target_invalid",
            "target_without_holding_period",
            trade_date=day,
            contract_code=target.contract_code,
        )
    if target.list_date > day:
        _fail(
            "roll_target_invalid",
            "target_inactive",
            trade_date=day,
            contract_code=target.contract_code,
        )
    return _close(validated, day, target.contract_code), selected_slot


def _execute(
    executions: list[Execution],
    day: date,
    side: Side,
    contract_code: str,
    price: float,
    reason: ExecutionReason,
    selection_slot: SelectionSlot | None,
) -> None:
    executions.append(
        Execution(
            trade_date=day,
            side=side,
            contract_code=contract_code,
            price=price,
            reason=reason,
            selection_slot=selection_slot,
        )
    )


def simulate_holding(inputs: HoldingSimulationInput) -> StrategyTimeline:
    """Simulate the fixed real-contract long-only holding rule without PnL.

    The function performs no I/O and either returns a complete immutable timeline or
    raises a classified :class:`HoldingSimulationError`. It never returns a partial
    result and never mutates the caller's inputs.
    """

    validated = _validate_inputs(inputs)
    sessions = validated.sessions
    final_index = len(sessions) - 1
    position: ContractMetadata | None = None
    daily: list[DailyHolding] = []
    executions: list[Execution] = []
    rolls: list[RollEvent] = []

    for index, day in enumerate(sessions):
        is_final = index == final_index

        if position is None:
            if is_final:
                _fail(
                    "invalid_position_state",
                    "no_position_on_final_session",
                    trade_date=day,
                )
            if index != 0:
                _fail(
                    "invalid_position_state",
                    "unexpected_flat_state",
                    trade_date=day,
                )
            resolution = _resolve_decision(validated, day)
            target = _target_for_slot(resolution, "M1")
            target_close, target_slot = _validate_target(
                validated,
                day,
                target,
                "M1",
                held_contract_code=None,
            )
            _execute(
                executions,
                day,
                "BUY",
                target.contract_code,
                target_close,
                "entry",
                target_slot,
            )
            position = target
            daily.append(
                DailyHolding(
                    trade_date=day,
                    pnl_contract_code=target.contract_code,
                    position_contract_code=target.contract_code,
                )
            )
            continue

        held = position
        if not (_is_date_only(held.list_date) and _is_date_only(held.delist_date)):
            _fail(
                "invalid_contract_lifecycle",
                "invalid_contract_metadata",
                trade_date=day,
                contract_code=held.contract_code,
            )
        if day > held.delist_date:
            _fail(
                "invalid_position_state",
                "held_contract_expired_without_roll",
                trade_date=day,
                contract_code=held.contract_code,
            )
        if day < held.list_date:
            _fail(
                "invalid_contract_lifecycle",
                "held_contract_inactive",
                trade_date=day,
                contract_code=held.contract_code,
            )
        held_close = _close(validated, day, held.contract_code)

        if is_final:
            _execute(
                executions,
                day,
                "SELL",
                held.contract_code,
                held_close,
                "study_end_close",
                None,
            )
            daily.append(
                DailyHolding(
                    trade_date=day,
                    pnl_contract_code=held.contract_code,
                    position_contract_code=None,
                )
            )
            position = None
            continue

        if day == held.delist_date:
            resolution = _resolve_decision(validated, day)
            old_slot = _old_slot_for_held(resolution, held)
            profile_target_slot: SelectionSlot = (
                "M1" if validated.strategy_profile == "expiry_to_M1_v1" else "Q1"
            )
            target = _target_for_slot(resolution, profile_target_slot)
            target_close, selected_slot = _validate_target(
                validated,
                day,
                target,
                profile_target_slot,
                held_contract_code=held.contract_code,
            )
            _execute(
                executions,
                day,
                "SELL",
                held.contract_code,
                held_close,
                "expiry_close",
                None,
            )
            _execute(
                executions,
                day,
                "BUY",
                target.contract_code,
                target_close,
                "expiry_open",
                selected_slot,
            )
            rolls.append(
                RollEvent(
                    trade_date=day,
                    old_contract_code=held.contract_code,
                    old_slot=old_slot,
                    old_close=held_close,
                    new_contract_code=target.contract_code,
                    new_slot=selected_slot,
                    new_close=target_close,
                    reason="expiry",
                )
            )
            daily.append(
                DailyHolding(
                    trade_date=day,
                    pnl_contract_code=held.contract_code,
                    position_contract_code=target.contract_code,
                )
            )
            position = target
            continue

        daily.append(
            DailyHolding(
                trade_date=day,
                pnl_contract_code=held.contract_code,
                position_contract_code=held.contract_code,
            )
        )

    if position is not None:
        _fail("invalid_position_state", "final_state_not_flat")

    return StrategyTimeline(
        product_code=validated.product_code,
        strategy_profile=validated.strategy_profile,
        sessions=sessions,
        daily=tuple(daily),
        executions=tuple(executions),
        rolls=tuple(rolls),
    )
