"""Deterministic daily roles and adjacent-CFFEX-candidate identity changes."""

from datetime import date
from typing import NoReturn

from .models import (
    SLOTS,
    AbsenceBoundary,
    CandidateSessions,
    ContractMetadata,
    ContractTransition,
    DailySlotResolution,
    DailyUniverseEvidence,
    SlotMapping,
    SlotResolutionError,
    TransitionResult,
)

# Consumption of the published Futures FACTS.md mapping, not an instrument registry.
_UNDERLYING = {"IF": "000300.SH", "IH": "000016.SH", "IC": "000905.SH", "IM": "000852.SH"}


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def resolve_daily_slots(
    product_code: str,
    trade_date: date,
    contracts: tuple[ContractMetadata, ...],
    *,
    evidence: DailyUniverseEvidence | None,
) -> DailySlotResolution:
    """Resolve one already-proven complete active set; never infer completeness."""

    def fail(category: str, reason: str) -> NoReturn:
        raise SlotResolutionError(category, product_code, trade_date, reason, contracts, evidence)

    if not isinstance(product_code, str) or product_code not in _UNDERLYING:
        fail("invalid_request", "product_code: expected canonical IF/IH/IC/IM")
    if type(trade_date) is not date:
        fail("invalid_request", "trade_date: expected date, not timestamp")
    if evidence is None:
        fail("missing_completeness_evidence", "evidence: complete active-universe proof required")
    if not isinstance(evidence, DailyUniverseEvidence):
        fail("invalid_evidence", "evidence: expected DailyUniverseEvidence")
    if (
        evidence.product_code != product_code
        or type(evidence.trade_date) is not date
        or evidence.trade_date != trade_date
        or evidence.complete is not True
        or not _text(evidence.source_export_ref)
    ):
        fail(
            "invalid_evidence",
            "evidence: wrong product/date, incomplete or missing Export reference",
        )
    codes = evidence.active_contract_codes
    if (
        not isinstance(codes, tuple)
        or any(not _text(code) for code in codes)
        or len(set(codes)) != len(codes)
    ):
        fail("invalid_evidence", "evidence.active_contract_codes: expected unique codes tuple")
    if not isinstance(contracts, tuple):
        fail("invalid_contract_metadata", "contracts: expected immutable metadata tuple")

    seen_codes: set[str] = set()
    months: dict[int, ContractMetadata] = {}
    for index, contract in enumerate(contracts):
        path = f"contracts[{index}]"
        if not isinstance(contract, ContractMetadata):
            fail("invalid_contract_metadata", f"{path}: expected ContractMetadata")
        month = contract.delivery_month
        if (
            not isinstance(month, str)
            or len(month) != 6
            or not month.isascii()
            or not month.isdecimal()
            or not 1 <= int(month[:4]) <= 9999
            or not 1 <= int(month[4:]) <= 12
        ):
            fail("invalid_contract_metadata", f"{path}.delivery_month: expected valid YYYYMM")
        if (
            contract.product_code != product_code
            or contract.underlying_index_code != _UNDERLYING[product_code]
            or contract.contract_code != f"{product_code}{month[2:]}.CFX"
        ):
            fail("invalid_contract_metadata", f"{path}: contract/product/underlying/month conflict")
        if (
            type(contract.list_date) is not date
            or type(contract.delist_date) is not date
            or not contract.list_date <= trade_date <= contract.delist_date
        ):
            fail("invalid_contract_metadata", f"{path}: invalid or inactive inclusive lifecycle")
        if contract.contract_code in seen_codes:
            fail("invalid_contract_metadata", f"{path}.contract_code: duplicate identity")
        seen_codes.add(contract.contract_code)
        maturity = int(month[:4]) * 12 + int(month[4:]) - 1
        if maturity in months:
            fail("invalid_contract_metadata", f"{path}.delivery_month: duplicate month")
        months[maturity] = contract
    if seen_codes != set(codes):
        fail("invalid_evidence", "evidence.active_contract_codes: metadata membership mismatch")

    if not contracts:
        return DailySlotResolution(
            product_code,
            trade_date,
            tuple(
                SlotMapping(s, None, evidence, "not_applicable", "no_active_contract")
                for s in SLOTS
            ),
            evidence,
        )
    if len(contracts) != 4:
        fail(
            "invalid_month_structure", "contracts: nonempty active set must contain four contracts"
        )
    ordered = sorted(months)
    near = ordered[1]
    # Zero-based month indexes 2/5/8/11 are quarter months. Search after M1.
    first_quarter = near + (3 - ((near + 1) % 3))
    if ordered != [ordered[0], ordered[0] + 1, first_quarter, first_quarter + 3]:
        fail(
            "invalid_month_structure",
            "delivery_month: expected consecutive near and next two quarters",
        )
    return DailySlotResolution(
        product_code,
        trade_date,
        tuple(
            SlotMapping(slot, months[month], evidence, "resolved", None)
            for slot, month in zip(SLOTS, ordered, strict=True)
        ),
        evidence,
    )


def detect_contract_transitions(
    product_code: str,
    candidate_sessions: CandidateSessions,
    resolutions: tuple[DailySlotResolution, ...],
) -> TransitionResult:
    """Require all candidates; report real changes separately from proven absence."""

    def fail(reason: str, day: object = None) -> NoReturn:
        raise SlotResolutionError(
            "invalid_resolution_sequence",
            product_code,
            day,
            reason,
            resolutions,
            candidate_sessions,
        )

    if not isinstance(product_code, str) or product_code not in _UNDERLYING:
        fail("product_code: expected canonical IF/IH/IC/IM")
    if (
        not isinstance(candidate_sessions, CandidateSessions)
        or not isinstance(candidate_sessions.dates, tuple)
        or not _text(candidate_sessions.calendar_export_ref)
    ):
        fail("candidate_sessions: complete validated CFFEX dates and Calendar reference required")
    dates = candidate_sessions.dates
    if any(type(d) is not date for d in dates) or any(
        a >= b for a, b in zip(dates, dates[1:], strict=False)
    ):
        fail("candidate_sessions.dates: expected strictly increasing unique dates")
    if not isinstance(resolutions, tuple) or len(resolutions) != len(dates):
        fail("resolutions: exactly one result per CFFEX candidate required")
    # Validate the entire sequence before deriving any event, including public
    # dataclasses constructed manually or replaced by a caller.
    for index, (day, result) in enumerate(zip(dates, resolutions, strict=True)):
        if (
            not isinstance(result, DailySlotResolution)
            or result.product_code != product_code
            or type(result.trade_date) is not date
            or result.trade_date != day
            or not isinstance(result.mappings, tuple)
            or any(not isinstance(m, SlotMapping) for m in result.mappings)
        ):
            fail(f"resolutions[{index}]: invalid product/date/mappings", day)
        canonical = resolve_daily_slots(
            product_code,
            day,
            tuple(m.contract for m in result.mappings if m.contract is not None),
            evidence=result.evidence,
        )
        if any(
            not isinstance(m.evidence, DailyUniverseEvidence)
            or m.evidence.complete is not True
            or type(m.evidence.trade_date) is not date
            for m in result.mappings
        ):
            fail(f"resolutions[{index}]: invalid mapping evidence", day)
        if result != canonical:
            fail(
                f"resolutions[{index}]: mappings/status/evidence differ from resolved universe", day
            )

    transitions: list[ContractTransition] = []
    boundaries: list[AbsenceBoundary] = []
    for previous, current in zip(resolutions, resolutions[1:], strict=False):
        for old, new in zip(previous.mappings, current.mappings, strict=True):
            if old.contract is not None and new.contract is not None:
                if old.contract.contract_code != new.contract.contract_code:
                    transitions.append(
                        ContractTransition(
                            product_code,
                            new.slot,
                            previous.trade_date,
                            current.trade_date,
                            old.contract.contract_code,
                            new.contract.contract_code,
                            old.contract,
                            new.contract,
                            old.evidence,
                            new.evidence,
                        )
                    )
            elif (old.contract is None) != (new.contract is None):
                boundaries.append(
                    AbsenceBoundary(
                        product_code,
                        new.slot,
                        previous.trade_date,
                        current.trade_date,
                        "appeared" if old.contract is None else "disappeared",
                        old,
                        new,
                    )
                )
    return TransitionResult(product_code, candidate_sessions, tuple(transitions), tuple(boundaries))
