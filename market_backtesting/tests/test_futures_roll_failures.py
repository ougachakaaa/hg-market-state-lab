"""Migrated WP1 failure matrix against the W2/Core replay boundary."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from math import inf, nan
from typing import Any

import pytest

import market_backtesting.cases.futures_roll_long.policy as policy_module
from futures_roll_fixtures import (
    ACTIVE_MONTHS,
    EXPECTED_RESOLVER_CALLS,
    FEB5,
    FEB20,
    JAN5,
    JAN20,
    SESSIONS,
    decision_for,
    drop_contract_close,
    drop_decision_slot,
    drop_session_facts,
    evidence_for,
    expiry_skipped_input,
    long_input,
    non_m0_expiry_input,
    replace_contract,
    replace_decision_slot,
    replace_input,
    replace_session_facts,
    set_contract_close,
)
from market_backtesting.cases.futures_roll_long import (
    ContractClose,
    FuturesRollError,
    FuturesRollInput,
    SessionFacts,
    replay_futures_roll,
)
from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailySlotResolution,
    DailyUniverseEvidence,
    SlotMapping,
)


def assert_failure(
    inputs: FuturesRollInput,
    category: str,
    reason: str,
) -> FuturesRollError:
    with pytest.raises(FuturesRollError) as exc:
        replay_futures_roll(inputs)
    assert exc.value.category == category
    assert exc.value.reason == reason
    return exc.value


def test_bad_input_carrier_fails_explicitly() -> None:
    assert_failure(
        object(),  # type: ignore[arg-type]
        "invalid_case_input",
        "invalid_input_shape",
    )


def test_invalid_product_code() -> None:
    assert_failure(
        replace_input(long_input(), product_code="XX"),
        "invalid_case_input",
        "invalid_product_code",
    )


def test_invalid_strategy_profile() -> None:
    assert_failure(
        replace_input(long_input(), strategy_profile="expiry_to_X"),
        "invalid_case_input",
        "invalid_strategy_profile",
    )


def test_insufficient_sessions() -> None:
    assert_failure(
        replace_input(long_input(), sessions=(JAN5,)),
        "invalid_case_input",
        "insufficient_sessions",
    )


def test_session_order_is_not_inferred_or_repaired() -> None:
    assert_failure(
        replace_input(long_input(), sessions=tuple(reversed(SESSIONS))),
        "invalid_case_input",
        "session_order_not_increasing",
    )


def test_duplicate_session() -> None:
    assert_failure(
        replace_input(long_input(), sessions=(JAN5, JAN5, JAN20)),
        "invalid_case_input",
        "duplicate_session",
    )


def test_missing_session_facts_do_not_skip_a_day() -> None:
    assert_failure(
        drop_session_facts(long_input(), JAN20),
        "missing_market_fact",
        "missing_session_facts",
    )


def test_duplicate_session_facts() -> None:
    inputs = long_input()
    January = next(item for item in inputs.session_facts if item.trade_date == JAN5)
    assert_failure(
        replace_input(inputs, session_facts=inputs.session_facts + (January,)),
        "invalid_case_input",
        "duplicate_session_facts",
    )


def test_session_fact_outside_sessions() -> None:
    inputs = long_input()
    assert_failure(
        replace_input(
            inputs,
            session_facts=inputs.session_facts + (SessionFacts(date(2026, 1, 6), ()),),
        ),
        "invalid_case_input",
        "invalid_session_facts",
    )


def test_unknown_contract_fact() -> None:
    inputs = long_input()
    extra = ContractClose(contract_code="IM9999.CFX", close=5000.0)
    assert_failure(
        replace_session_facts(
            inputs,
            JAN5,
            next(item for item in inputs.session_facts if item.trade_date == JAN5).closes
            + (extra,),
        ),
        "invalid_case_input",
        "unknown_contract_fact",
    )


def test_duplicate_contract_close() -> None:
    inputs = long_input()
    closes = next(item for item in inputs.session_facts if item.trade_date == JAN5).closes
    assert_failure(
        replace_session_facts(inputs, JAN5, closes + (closes[0],)),
        "invalid_case_input",
        "duplicate_contract_close",
    )


@pytest.mark.parametrize("value", (nan, inf, -inf))
def test_non_finite_close(value: float) -> None:
    assert_failure(
        set_contract_close(long_input(), JAN5, "IM2602.CFX", value),
        "invalid_price",
        "non_finite_close",
    )


@pytest.mark.parametrize("value", (0, -1, True, "5000"))
def test_non_positive_or_non_numeric_close(value: Any) -> None:
    category = "invalid_price"
    reason = "non_positive_close" if value in (0, -1) else "non_finite_close"
    assert_failure(
        set_contract_close(long_input(), JAN5, "IM2602.CFX", value),
        category,
        reason,
    )


def test_missing_held_contract_close_fails_instead_of_skipping() -> None:
    assert_failure(
        drop_contract_close(long_input(), FEB5, "IM2602.CFX"),
        "missing_market_fact",
        "missing_contract_row",
    )


def test_missing_entry_target_close() -> None:
    assert_failure(
        drop_contract_close(long_input(), JAN5, "IM2602.CFX"),
        "missing_market_fact",
        "missing_contract_row",
    )


def test_missing_decision_slot_evidence() -> None:
    assert_failure(
        drop_decision_slot(long_input(), JAN5),
        "slot_resolution",
        "missing_decision_evidence",
    )


def test_initial_m1_cannot_be_selected_from_a_proven_empty_universe() -> None:
    inputs = long_input()
    assert_failure(
        replace_decision_slot(inputs, JAN5, evidence_for(JAN5, ())),
        "roll_target_invalid",
        "target_not_resolved",
    )


def test_incomplete_decision_evidence() -> None:
    inputs = long_input()
    original = next(item for item in inputs.decision_slots if item.trade_date == JAN5)
    evidence = replace(original.evidence, complete=False)
    assert_failure(
        replace_decision_slot(inputs, JAN5, evidence),
        "slot_resolution",
        "invalid_decision_evidence",
    )


def test_decision_evidence_with_unknown_contract() -> None:
    inputs = long_input()
    original = next(item for item in inputs.decision_slots if item.trade_date == JAN5)
    evidence = replace(
        original.evidence,
        active_contract_codes=(
            "IM2602.CFX",
            "IM2603.CFX",
            "IM2606.CFX",
            "IM9999.CFX",
        ),
    )
    assert_failure(
        replace_decision_slot(inputs, JAN5, evidence),
        "missing_market_fact",
        "missing_active_contract_metadata",
    )


def test_w1_slot_resolution_failure_is_classified() -> None:
    inputs = long_input()
    irregular = decision_for(
        JAN5,
        ("202601", "202602", "202605", "202608"),
    )
    assert_failure(
        replace_decision_slot(inputs, JAN5, irregular.evidence),
        "slot_resolution",
        "w1_slot_resolution_error",
    )


def test_entry_target_without_remaining_holding_period() -> None:
    inputs = long_input()
    contracts = replace_contract(
        inputs.contracts,
        "IM2602.CFX",
        delist_date=JAN5,
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "roll_target_invalid",
        "target_without_holding_period",
    )


@pytest.mark.parametrize(
    ("profile", "roll_contract"),
    (
        ("expiry_to_M1_v1", "IM2603.CFX"),
        ("expiry_to_Q1_v1", "IM2606.CFX"),
    ),
)
def test_roll_target_without_remaining_holding_period(
    profile: str,
    roll_contract: str,
) -> None:
    inputs = long_input(profile)
    contracts = replace_contract(
        inputs.contracts,
        roll_contract,
        delist_date=FEB20,
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "roll_target_invalid",
        "target_without_holding_period",
    )


def test_duplicate_contract_metadata() -> None:
    inputs = long_input()
    assert_failure(
        replace_input(inputs, contracts=inputs.contracts + (inputs.contracts[0],)),
        "invalid_contract_lifecycle",
        "duplicate_contract_code",
    )


def test_duplicate_delivery_month() -> None:
    inputs = long_input()
    contracts = replace_contract(
        inputs.contracts,
        "IM2603.CFX",
        delivery_month="202602",
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "invalid_contract_lifecycle",
        "duplicate_delivery_month",
    )


def test_invalid_delivery_month() -> None:
    inputs = long_input()
    contracts = replace_contract(
        inputs.contracts,
        "IM2603.CFX",
        delivery_month="202613",
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "invalid_contract_lifecycle",
        "invalid_contract_metadata",
    )


def test_conflicting_product_metadata() -> None:
    inputs = long_input()
    contracts = replace_contract(
        inputs.contracts,
        "IM2603.CFX",
        product_code="IF",
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "invalid_contract_lifecycle",
        "conflicting_product",
    )


def test_conflicting_underlying_metadata() -> None:
    inputs = long_input()
    contracts = replace_contract(
        inputs.contracts,
        "IM2603.CFX",
        underlying_index_code="000300.SH",
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "invalid_contract_lifecycle",
        "conflicting_underlying",
    )


def test_invalid_lifecycle_ordering() -> None:
    inputs = long_input()
    contracts = replace_contract(
        inputs.contracts,
        "IM2603.CFX",
        list_date=date(2027, 1, 1),
        delist_date=date(2026, 1, 1),
    )
    assert_failure(
        replace_input(inputs, contracts=contracts),
        "invalid_contract_lifecycle",
        "invalid_contract_metadata",
    )


def test_held_contract_expired_without_roll() -> None:
    assert_failure(
        expiry_skipped_input(),
        "invalid_position_state",
        "held_contract_expired_without_roll",
    )


def test_expiring_held_contract_must_resolve_to_m0() -> None:
    assert_failure(
        non_m0_expiry_input(),
        "invalid_contract_lifecycle",
        "expiring_held_contract_not_m0",
    )


def test_expiring_held_contract_must_be_in_decision_universe() -> None:
    inputs = long_input()
    replacement = decision_for(FEB20, ("202603", "202604", "202606", "202609"))
    assert_failure(
        replace_decision_slot(inputs, FEB20, replacement.evidence),
        "invalid_contract_lifecycle",
        "held_contract_missing_from_active_set",
    )


def test_extra_decision_evidence_is_not_treated_as_a_trade() -> None:
    inputs = long_input()
    decision_days = EXPECTED_RESOLVER_CALLS["expiry_to_M1_v1"]
    trimmed = replace_input(
        inputs,
        decision_slots=tuple(
            item for item in inputs.decision_slots if item.trade_date in decision_days
        ),
    )
    extra = decision_for(FEB5, ACTIVE_MONTHS[FEB5])
    timeline = replay_futures_roll(
        replace_input(
            trimmed,
            decision_slots=trimmed.decision_slots + (extra,),
        )
    )
    assert all(execution.trade_date != FEB5 for execution in timeline.executions)


def controlled_roll_resolution(
    inputs: FuturesRollInput,
    target: ContractMetadata,
) -> DailySlotResolution:
    evidence = next(item for item in inputs.decision_slots if item.trade_date == FEB20).evidence
    by_code = {contract.contract_code: contract for contract in inputs.contracts}
    old = by_code["IM2602.CFX"]
    q1 = by_code["IM2606.CFX"]
    q2 = by_code["IM2609.CFX"]
    return DailySlotResolution(
        "IM",
        FEB20,
        (
            SlotMapping("M0", old, evidence, "resolved", None),
            SlotMapping("M1", target, evidence, "resolved", None),
            SlotMapping("Q1", q1, evidence, "resolved", None),
            SlotMapping("Q2", q2, evidence, "resolved", None),
        ),
        evidence,
    )


def test_expired_roll_target_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = long_input()
    target = dict((contract.contract_code, contract) for contract in inputs.contracts)["IM2603.CFX"]
    target = replace(target, delist_date=JAN5)
    controlled = controlled_roll_resolution(inputs, target)
    real_resolver = policy_module.resolve_daily_slots

    def wrapper(
        product_code: str,
        trade_date: date,
        contracts: tuple[ContractMetadata, ...],
        *,
        evidence: DailyUniverseEvidence,
    ) -> DailySlotResolution:
        if trade_date == FEB20:
            return controlled
        return real_resolver(product_code, trade_date, contracts, evidence=evidence)

    monkeypatch.setattr(policy_module, "resolve_daily_slots", wrapper)
    assert_failure(
        inputs,
        "roll_target_invalid",
        "target_expired",
    )


def test_roll_target_equal_to_held_contract_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = long_input()
    held = dict((contract.contract_code, contract) for contract in inputs.contracts)["IM2602.CFX"]
    controlled = controlled_roll_resolution(inputs, held)
    real_resolver = policy_module.resolve_daily_slots

    def wrapper(
        product_code: str,
        trade_date: date,
        contracts: tuple[ContractMetadata, ...],
        *,
        evidence: DailyUniverseEvidence,
    ) -> DailySlotResolution:
        if trade_date == FEB20:
            return controlled
        return real_resolver(product_code, trade_date, contracts, evidence=evidence)

    monkeypatch.setattr(policy_module, "resolve_daily_slots", wrapper)
    assert_failure(
        inputs,
        "roll_target_invalid",
        "target_equal_held_contract",
    )
