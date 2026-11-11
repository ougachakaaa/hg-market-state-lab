"""Adapt validated final public rows into the existing pure replay boundary."""

from __future__ import annotations

from market_research.descriptive.cases.futures_basis import ContractMetadata, DailyUniverseEvidence

from ...core import InstrumentReference
from .application_models import FuturesRollRequest, PublicInputExports
from .models import ContractClose, DecisionSlotEvidence, FuturesRollInput, IndexClose, SessionFacts


def build_replay_input(
    request: FuturesRollRequest,
    exports: PublicInputExports,
    fingerprint: str,
) -> FuturesRollInput:
    """Each day's evidence uses exactly its proven rows, never a reconstructed catalog."""
    sessions = tuple(row.cal_date for row in exports.calendar_cffex.records if row.is_open == 1)
    contracts: dict[str, ContractMetadata] = {}
    references: dict[str, InstrumentReference] = {}
    daily: dict[object, list[ContractClose]] = {day: [] for day in sessions}
    for row in exports.futures.records:
        contracts[row.contract_code] = ContractMetadata(
            row.contract_code,
            row.product_code,
            row.underlying_index_code,
            row.delivery_month,
            row.list_date,
            row.delist_date,
        )
        references[row.contract_code] = InstrumentReference(
            row.contract_code,
            row.multiplier,
            f"tushare_equity_index_futures/futures_daily/2:{fingerprint}:{row.contract_code}",
        )
        daily[row.trade_date].append(ContractClose(row.contract_code, row.close))
    closes = {row.trade_date: row.close for row in exports.index.records}
    return FuturesRollInput(
        product_code=request.product_code,
        sessions=sessions,
        contracts=tuple(contracts.values()),
        session_facts=tuple(SessionFacts(day, tuple(daily[day])) for day in sessions),
        decision_slots=tuple(
            DecisionSlotEvidence(
                day,
                DailyUniverseEvidence(
                    request.product_code,
                    day,
                    True,
                    tuple(row.contract_code for row in daily[day]),
                    f"tushare_equity_index_futures/futures_daily/2:{fingerprint}:{day.isoformat()}",
                ),
            )
            for day in sessions
        ),
        strategy_profile=request.strategy_profile,
        instrument_refs=tuple(references.values()),
        index_closes=tuple(IndexClose(day, closes[day]) for day in sessions),
    )
