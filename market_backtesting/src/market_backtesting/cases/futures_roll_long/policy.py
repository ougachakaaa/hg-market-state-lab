"""Price-free W2 Mechanical Roll Policy and authorized W1 Slot adapter."""

from dataclasses import dataclass
from datetime import date

from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailySlotResolution,
    SlotResolutionError,
    resolve_daily_slots,
)

from ...core import DecisionEvidence, Portfolio, TargetPortfolio, TargetPosition
from .failures import FuturesRollError
from .models import (
    PRODUCT_CODES,
    STRATEGY_PROFILES,
    DecisionContext,
    ProductCode,
    SelectionSlot,
    StrategyProfile,
)
from .validation import _fail


def _resolve(product: ProductCode, day: date, context: DecisionContext) -> DailySlotResolution:
    evidence = context.evidence
    if evidence is None:
        _fail("slot_resolution", "missing_decision_evidence", trade_date=day)
    metadata = {contract.contract_code: contract for contract in context.contracts}
    if (
        evidence.trade_date != day
        or evidence.product_code != product
        or evidence.complete is not True
    ):
        _fail("slot_resolution", "invalid_decision_evidence", trade_date=day)
    if any(code not in metadata for code in evidence.active_contract_codes):
        _fail("missing_market_fact", "missing_active_contract_metadata", trade_date=day)
    try:
        return resolve_daily_slots(
            product,
            day,
            tuple(metadata[code] for code in evidence.active_contract_codes),
            evidence=evidence,
        )
    except SlotResolutionError as exc:
        raise FuturesRollError(
            "slot_resolution",
            "w1_slot_resolution_error",
            trade_date=day,
            detail=f"{exc.category}: {exc.reason}",
        ) from exc


def _target_for_slot(resolution: DailySlotResolution, slot: SelectionSlot) -> ContractMetadata:
    for mapping in resolution.mappings:
        if mapping.slot == slot and mapping.status == "resolved" and mapping.contract is not None:
            return mapping.contract
    _fail("roll_target_invalid", "target_not_resolved", trade_date=resolution.trade_date)


@dataclass(frozen=True, slots=True)
class MechanicalRollPolicy:
    product_code: ProductCode
    strategy_profile: StrategyProfile

    def __post_init__(self) -> None:
        if self.product_code not in PRODUCT_CODES:
            _fail("invalid_case_input", "invalid_product_code")
        if self.strategy_profile not in STRATEGY_PROFILES:
            _fail("invalid_case_input", "invalid_strategy_profile")

    def __call__(
        self, session: date, previous: Portfolio, context: DecisionContext
    ) -> TargetPortfolio:
        metadata = {contract.contract_code: contract for contract in context.contracts}
        references = {ref.instrument_id: ref for ref in context.instrument_refs}
        held = previous.position
        held_metadata = None
        if held is not None:
            held_metadata = metadata.get(held.instrument.instrument_id)
            if held_metadata is None:
                _fail("invalid_contract_lifecycle", "invalid_contract_metadata", trade_date=session)
            if session > held_metadata.delist_date:
                _fail(
                    "invalid_position_state",
                    "held_contract_expired_without_roll",
                    trade_date=session,
                )
            if session < held_metadata.list_date:
                _fail("invalid_contract_lifecycle", "held_contract_inactive", trade_date=session)
            if (
                held.quantity != 1
                or references.get(held.instrument.instrument_id) != held.instrument
            ):
                _fail("invalid_position_state", "held_instrument_conflict", trade_date=session)
        if context.is_final:
            if held is None:
                _fail("invalid_position_state", "no_position_on_final_session", trade_date=session)
            return TargetPortfolio(
                evidence=DecisionEvidence("study_end_close", held.instrument.source_ref)
            )
        if held is not None and held_metadata is not None and session < held_metadata.delist_date:
            return TargetPortfolio(
                TargetPosition(held.instrument, 1),
                DecisionEvidence("hold", held.instrument.source_ref),
            )
        if held is None and not context.is_first:
            _fail("invalid_position_state", "unexpected_flat_state", trade_date=session)
        resolution = _resolve(self.product_code, session, context)
        old_role = None
        if held is not None:
            mapping = next(
                (
                    m
                    for m in resolution.mappings
                    if m.contract_code == held.instrument.instrument_id
                ),
                None,
            )
            if mapping is None:
                _fail(
                    "invalid_contract_lifecycle",
                    "held_contract_missing_from_active_set",
                    trade_date=session,
                )
            if mapping.slot != "M0":
                _fail(
                    "invalid_contract_lifecycle",
                    "expiring_held_contract_not_m0",
                    trade_date=session,
                )
            old_role = mapping.slot
        slot: SelectionSlot = (
            "M1" if held is None or self.strategy_profile == "expiry_to_M1_v1" else "Q1"
        )
        target = _target_for_slot(resolution, slot)
        if held is not None and target.contract_code == held.instrument.instrument_id:
            _fail(
                "roll_target_invalid",
                "target_equal_held_contract",
                trade_date=session,
                contract_code=target.contract_code,
            )
        if type(target.list_date) is not date or type(target.delist_date) is not date:
            _fail("invalid_contract_lifecycle", "invalid_contract_metadata", trade_date=session)
        if target.delist_date < session:
            _fail(
                "roll_target_invalid",
                "target_expired",
                trade_date=session,
                contract_code=target.contract_code,
            )
        if target.delist_date == session:
            _fail(
                "roll_target_invalid",
                "target_without_holding_period",
                trade_date=session,
                contract_code=target.contract_code,
            )
        if target.list_date > session:
            _fail(
                "roll_target_invalid",
                "target_inactive",
                trade_date=session,
                contract_code=target.contract_code,
            )
        reference = references.get(target.contract_code)
        if reference is None:
            _fail(
                "invalid_contract_lifecycle",
                "missing_multiplier",
                trade_date=session,
                contract_code=target.contract_code,
            )
        if held is not None and reference.multiplier != held.instrument.multiplier:
            _fail(
                "accounting_failure",
                "multiplier_mismatch",
                trade_date=session,
                contract_code=target.contract_code,
            )
        return TargetPortfolio(
            TargetPosition(reference, 1),
            DecisionEvidence(
                "entry" if held is None else "expiry",
                resolution.evidence.source_export_ref,
                slot,
                old_role,
            ),
        )
