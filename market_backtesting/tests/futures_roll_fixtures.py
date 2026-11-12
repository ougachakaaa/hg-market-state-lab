"""Fixed artificial futures facts for holding-simulation tests; no market I/O."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

from market_backtesting.cases.futures_roll_long.models import (
    ContractClose,
    DecisionSlotEvidence,
    FuturesRollInput,
    IndexClose,
    SessionFacts,
)
from market_backtesting.core import InstrumentReference
from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailySlotResolution,
    DailyUniverseEvidence,
    resolve_daily_slots,
)

UNDERLYING = {
    "IF": "000300.SH",
    "IH": "000016.SH",
    "IC": "000905.SH",
    "IM": "000852.SH",
}

JAN5 = date(2026, 1, 5)
JAN20 = date(2026, 1, 20)
FEB5 = date(2026, 2, 5)
FEB20 = date(2026, 2, 20)
FEB25 = date(2026, 2, 25)
MAR5 = date(2026, 3, 5)
MAR20 = date(2026, 3, 20)
APR6 = date(2026, 4, 6)
APR20 = date(2026, 4, 20)
MAY6 = date(2026, 5, 6)
MAY20 = date(2026, 5, 20)
JUN5 = date(2026, 6, 5)
JUN19 = date(2026, 6, 19)
JUN22 = date(2026, 6, 22)

SESSIONS = (
    JAN5,
    JAN20,
    FEB5,
    FEB20,
    MAR5,
    MAR20,
    APR6,
    APR20,
    MAY6,
    MAY20,
    JUN5,
    JUN19,
    JUN22,
)

ACTIVE_MONTHS: dict[date, tuple[str, ...]] = {
    JAN5: ("202601", "202602", "202603", "202606"),
    JAN20: ("202601", "202602", "202603", "202606"),
    FEB5: ("202602", "202603", "202606", "202609"),
    FEB20: ("202602", "202603", "202606", "202609"),
    MAR5: ("202603", "202604", "202606", "202609"),
    MAR20: ("202603", "202604", "202606", "202609"),
    APR6: ("202604", "202605", "202606", "202609"),
    APR20: ("202604", "202605", "202606", "202609"),
    MAY6: ("202605", "202606", "202609", "202612"),
    MAY20: ("202605", "202606", "202609", "202612"),
    JUN5: ("202606", "202607", "202609", "202612"),
    JUN19: ("202606", "202607", "202609", "202612"),
    JUN22: ("202607", "202608", "202609", "202612"),
}

DELIST_DATES: dict[str, date] = {
    "202601": JAN20,
    "202602": FEB20,
    "202603": MAR20,
    "202604": APR20,
    "202605": MAY20,
    "202606": JUN19,
    "202607": date(2026, 7, 20),
    "202608": date(2026, 8, 20),
    "202609": date(2026, 9, 18),
    "202612": date(2026, 12, 18),
}

ALL_MONTHS = (
    "202601",
    "202602",
    "202603",
    "202604",
    "202605",
    "202606",
    "202607",
    "202608",
    "202609",
    "202612",
)

EXPECTED_DAILY: dict[str, tuple[tuple[date, str, str | None], ...]] = {
    "expiry_to_M1_v1": (
        (JAN5, "IM2602.CFX", "IM2602.CFX"),
        (JAN20, "IM2602.CFX", "IM2602.CFX"),
        (FEB5, "IM2602.CFX", "IM2602.CFX"),
        (FEB20, "IM2602.CFX", "IM2603.CFX"),
        (MAR5, "IM2603.CFX", "IM2603.CFX"),
        (MAR20, "IM2603.CFX", "IM2604.CFX"),
        (APR6, "IM2604.CFX", "IM2604.CFX"),
        (APR20, "IM2604.CFX", "IM2605.CFX"),
        (MAY6, "IM2605.CFX", "IM2605.CFX"),
        (MAY20, "IM2605.CFX", "IM2606.CFX"),
        (JUN5, "IM2606.CFX", "IM2606.CFX"),
        (JUN19, "IM2606.CFX", "IM2607.CFX"),
        (JUN22, "IM2607.CFX", None),
    ),
    "expiry_to_Q1_v1": (
        (JAN5, "IM2602.CFX", "IM2602.CFX"),
        (JAN20, "IM2602.CFX", "IM2602.CFX"),
        (FEB5, "IM2602.CFX", "IM2602.CFX"),
        (FEB20, "IM2602.CFX", "IM2606.CFX"),
        (MAR5, "IM2606.CFX", "IM2606.CFX"),
        (MAR20, "IM2606.CFX", "IM2606.CFX"),
        (APR6, "IM2606.CFX", "IM2606.CFX"),
        (APR20, "IM2606.CFX", "IM2606.CFX"),
        (MAY6, "IM2606.CFX", "IM2606.CFX"),
        (MAY20, "IM2606.CFX", "IM2606.CFX"),
        (JUN5, "IM2606.CFX", "IM2606.CFX"),
        (JUN19, "IM2606.CFX", "IM2609.CFX"),
        (JUN22, "IM2609.CFX", None),
    ),
}

EXPECTED_ROLLS: dict[str, tuple[tuple[date, str, str, str, str], ...]] = {
    "expiry_to_M1_v1": (
        (FEB20, "IM2602.CFX", "IM2603.CFX", "M0", "M1"),
        (MAR20, "IM2603.CFX", "IM2604.CFX", "M0", "M1"),
        (APR20, "IM2604.CFX", "IM2605.CFX", "M0", "M1"),
        (MAY20, "IM2605.CFX", "IM2606.CFX", "M0", "M1"),
        (JUN19, "IM2606.CFX", "IM2607.CFX", "M0", "M1"),
    ),
    "expiry_to_Q1_v1": (
        (FEB20, "IM2602.CFX", "IM2606.CFX", "M0", "Q1"),
        (JUN19, "IM2606.CFX", "IM2609.CFX", "M0", "Q1"),
    ),
}

EXPECTED_RESOLVER_CALLS: dict[str, tuple[date, ...]] = {
    "expiry_to_M1_v1": (JAN5, FEB20, MAR20, APR20, MAY20, JUN19),
    "expiry_to_Q1_v1": (JAN5, FEB20, JUN19),
}

_MONTH_INDEX = {month: index for index, month in enumerate(ALL_MONTHS)}


def contract_for(
    month: str,
    *,
    product: str = "IM",
    list_date: date = date(2025, 1, 1),
    delist_date: date | None = None,
) -> ContractMetadata:
    return ContractMetadata(
        contract_code=f"{product}{month[2:]}.CFX",
        product_code=product,
        underlying_index_code=UNDERLYING[product],
        delivery_month=month,
        list_date=list_date,
        delist_date=DELIST_DATES[month] if delist_date is None else delist_date,
    )


def contracts_for(
    months: tuple[str, ...] = ALL_MONTHS,
    *,
    product: str = "IM",
) -> tuple[ContractMetadata, ...]:
    return tuple(contract_for(month, product=product) for month in months)


def price(day: date, month: str) -> float:
    return 5000.0 + _MONTH_INDEX[month] * 100.0 + float(day.day)


def session_facts(
    day: date,
    months: tuple[str, ...],
    *,
    product: str = "IM",
) -> SessionFacts:
    return SessionFacts(
        trade_date=day,
        closes=tuple(
            ContractClose(
                contract_code=f"{product}{month[2:]}.CFX",
                close=price(day, month),
            )
            for month in months
        ),
    )


def evidence_for(
    day: date,
    months: tuple[str, ...],
    *,
    product: str = "IM",
) -> DailyUniverseEvidence:
    return DailyUniverseEvidence(
        product_code=product,
        trade_date=day,
        complete=True,
        active_contract_codes=tuple(f"{product}{month[2:]}.CFX" for month in months),
        source_export_ref=f"synthetic-final-futures-export:{product}:{day.isoformat()}",
    )


def decision_for(
    day: date,
    months: tuple[str, ...],
    *,
    product: str = "IM",
) -> DecisionSlotEvidence:
    return DecisionSlotEvidence(
        trade_date=day,
        evidence=evidence_for(day, months, product=product),
    )


def resolution_for(
    day: date,
    months: tuple[str, ...] | None = None,
    *,
    product: str = "IM",
) -> DailySlotResolution:
    selected = ACTIVE_MONTHS[day] if months is None else months
    contracts = contracts_for(selected, product=product)
    return resolve_daily_slots(
        product,
        day,
        contracts,
        evidence=evidence_for(day, selected, product=product),
    )


def long_input(profile: str = "expiry_to_M1_v1") -> FuturesRollInput:
    return make_input(
        product_code="IM",
        sessions=SESSIONS,
        contracts=contracts_for(),
        session_facts=tuple(session_facts(day, ACTIVE_MONTHS[day]) for day in SESSIONS),
        decision_slots=tuple(decision_for(day, ACTIVE_MONTHS[day]) for day in SESSIONS),
        strategy_profile=profile,  # type: ignore[arg-type]
    )


def expiry_on_final_input() -> FuturesRollInput:
    sessions = (JAN5, FEB20)
    return make_input(
        product_code="IM",
        sessions=sessions,
        contracts=contracts_for(),
        session_facts=tuple(session_facts(day, ACTIVE_MONTHS[day]) for day in sessions),
        decision_slots=tuple(decision_for(day, ACTIVE_MONTHS[day]) for day in sessions),
        strategy_profile="expiry_to_M1_v1",
    )


def expiry_after_final_input() -> FuturesRollInput:
    sessions = (JAN5, JAN20)
    return make_input(
        product_code="IM",
        sessions=sessions,
        contracts=contracts_for(),
        session_facts=tuple(session_facts(day, ACTIVE_MONTHS[day]) for day in sessions),
        decision_slots=tuple(decision_for(day, ACTIVE_MONTHS[day]) for day in sessions),
        strategy_profile="expiry_to_M1_v1",
    )


def expiry_skipped_input() -> FuturesRollInput:
    return make_input(
        product_code="IM",
        sessions=(JAN5, FEB25),
        contracts=contracts_for(),
        session_facts=(
            session_facts(JAN5, ACTIVE_MONTHS[JAN5]),
            SessionFacts(
                trade_date=FEB25,
                closes=(ContractClose("IM2602.CFX", price(FEB25, "202602")),),
            ),
        ),
        decision_slots=(decision_for(JAN5, ACTIVE_MONTHS[JAN5]),),
        strategy_profile="expiry_to_M1_v1",
    )


def simple_input(product: str = "IM") -> FuturesRollInput:
    months = ("202601", "202602", "202603", "202606")
    sessions = (JAN5, JAN20)
    contracts = contracts_for(months, product=product)
    return make_input(
        product_code=product,  # type: ignore[arg-type]
        sessions=sessions,
        contracts=contracts,
        session_facts=tuple(session_facts(day, months, product=product) for day in sessions),
        decision_slots=tuple(decision_for(day, months, product=product) for day in sessions),
        strategy_profile="expiry_to_M1_v1",
    )


def non_m0_expiry_input() -> FuturesRollInput:
    sessions = (JAN5, FEB20, JUN19, JUN22)
    contracts = contracts_for()
    contracts = replace_contract(contracts, "IM2605.CFX", delist_date=JUN19)
    active = {
        JAN5: ACTIVE_MONTHS[JAN5],
        FEB20: ACTIVE_MONTHS[FEB20],
        JUN19: ("202605", "202606", "202609", "202612"),
        JUN22: ACTIVE_MONTHS[JUN22],
    }
    return make_input(
        product_code="IM",
        sessions=sessions,
        contracts=contracts,
        session_facts=tuple(session_facts(day, active[day]) for day in sessions),
        decision_slots=tuple(decision_for(day, active[day]) for day in sessions),
        strategy_profile="expiry_to_Q1_v1",
    )


def replace_input(inputs: FuturesRollInput, **changes: Any) -> FuturesRollInput:
    return replace(inputs, **changes)


def replace_contract(
    contracts: tuple[ContractMetadata, ...],
    contract_code: str,
    **changes: Any,
) -> tuple[ContractMetadata, ...]:
    return tuple(
        replace(contract, **changes) if contract.contract_code == contract_code else contract
        for contract in contracts
    )


def replace_session_facts(
    inputs: FuturesRollInput,
    day: date,
    closes: tuple[ContractClose, ...],
) -> FuturesRollInput:
    return replace_input(
        inputs,
        session_facts=tuple(
            SessionFacts(trade_date=day, closes=closes) if item.trade_date == day else item
            for item in inputs.session_facts
        ),
    )


def drop_contract_close(
    inputs: FuturesRollInput,
    day: date,
    contract_code: str,
) -> FuturesRollInput:
    for item in inputs.session_facts:
        if item.trade_date == day:
            return replace_session_facts(
                inputs,
                day,
                tuple(close for close in item.closes if close.contract_code != contract_code),
            )
    return inputs


def set_contract_close(
    inputs: FuturesRollInput,
    day: date,
    contract_code: str,
    close: Any,
) -> FuturesRollInput:
    for item in inputs.session_facts:
        if item.trade_date == day:
            return replace_session_facts(
                inputs,
                day,
                tuple(
                    ContractClose(
                        contract_code=entry.contract_code,
                        close=close if entry.contract_code == contract_code else entry.close,
                    )
                    for entry in item.closes
                ),
            )
    return inputs


def drop_decision_slot(
    inputs: FuturesRollInput,
    day: date,
) -> FuturesRollInput:
    return replace_input(
        inputs,
        decision_slots=tuple(item for item in inputs.decision_slots if item.trade_date != day),
    )


def replace_decision_slot(
    inputs: FuturesRollInput,
    day: date,
    evidence: DailyUniverseEvidence,
) -> FuturesRollInput:
    return replace_input(
        inputs,
        decision_slots=tuple(
            DecisionSlotEvidence(trade_date=day, evidence=evidence)
            if item.trade_date == day
            else item
            for item in inputs.decision_slots
        ),
    )


def drop_session_facts(
    inputs: FuturesRollInput,
    day: date,
) -> FuturesRollInput:
    return replace_input(
        inputs,
        session_facts=tuple(item for item in inputs.session_facts if item.trade_date != day),
    )


def make_input(**kwargs: Any) -> FuturesRollInput:
    contracts = kwargs["contracts"]
    return FuturesRollInput(
        **kwargs,
        instrument_refs=tuple(
            InstrumentReference(c.contract_code, 200.0, "synthetic-metadata") for c in contracts
        ),
        index_closes=tuple(IndexClose(day, 6000.0) for day in kwargs["sessions"]),
    )


def performance_oracle_input(profile: str = "expiry_to_M1_v1") -> FuturesRollInput:
    """Five artificial sessions with legal W1 entry/expiry universes; no real-calendar claim."""
    days = (JAN5, FEB5, FEB20, FEB25, date(2026, 2, 26))
    entry_months = ("202601", "202602", "202603", "202606")
    roll_months = ("202602", "202603", "202606", "202609")
    after_months = ("202603", "202604", "202606", "202609")
    months_by_day = (entry_months, roll_months, roll_months, after_months, after_months)
    prices = (
        {"202602": 5900},
        {"202602": 5950},
        {"202602": 6000, "202603": 6010, "202606": 6025},
        {"202603": 6030, "202606": 6030},
        {"202603": 6020, "202606": 6020},
    )
    inputs = make_input(
        product_code="IM",
        sessions=days,
        contracts=contracts_for(),
        session_facts=tuple(
            SessionFacts(
                day,
                tuple(
                    ContractClose(f"IM{month[2:]}.CFX", closes.get(month, 6000)) for month in months
                ),
            )
            for day, months, closes in zip(days, months_by_day, prices, strict=True)
        ),
        decision_slots=tuple(
            decision_for(day, months) for day, months in zip(days, months_by_day, strict=True)
        ),
        strategy_profile=profile,
    )
    return replace(
        inputs,
        index_closes=tuple(
            IndexClose(day, close)
            for day, close in zip(days, (6000, 6060, 6030, 6090, 6075), strict=True)
        ),
    )
