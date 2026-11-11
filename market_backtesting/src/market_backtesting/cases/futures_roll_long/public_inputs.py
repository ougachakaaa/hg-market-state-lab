"""Adapt validated final public rows into the existing pure replay boundary."""

from __future__ import annotations

from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange
from data_lake.datasets.tushare_index_daily import IndexDailyRange
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange
from market_research.descriptive.cases.futures_basis import ContractMetadata, DailyUniverseEvidence

from ...core import InstrumentReference
from .application_models import FuturesRollRequest, PublicInputExports, PublicInputRequests
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


def validate_retained_exports(
    request: FuturesRollRequest, exports: PublicInputExports, auxiliary: TradeCalendarExport
) -> None:
    """Offline validation of the same final public inputs used by preparation."""
    from .application_models import validate_futures_roll_request
    from .failures import FuturesRollError
    from .input_validation import validate_calendar, validate_futures, validate_index

    validate_futures_roll_request(request)
    sessions = validate_calendar(exports.calendar_cffex, request)
    sse = validate_calendar(auxiliary, request, exchange="SSE")
    underlying = validate_futures(exports.futures, request, sessions)
    if (
        len(sessions) < 2
        or underlying is None
        or not all(
            export.coverage.complete
            for export in (exports.calendar_cffex, exports.futures, exports.index, auxiliary)
        )
    ):
        raise FuturesRollError("invalid_evidence", "incomplete_retained_inputs")
    validate_index(exports.index, request, sessions, underlying, sse)


def public_requests_for(
    request: FuturesRollRequest, exports: PublicInputExports
) -> tuple[PublicInputRequests, TradeCalendarRange]:
    """Recover exact public requests from validated retained scope/window facts."""
    return PublicInputRequests(
        TradeCalendarRange("CFFEX", request.start_date, request.end_date),
        FuturesDailyRange((request.product_code,), request.start_date, request.end_date),
        IndexDailyRange(
            (exports.futures.records[0].underlying_index_code,),
            request.start_date,
            request.end_date,
        ),
    ), TradeCalendarRange("SSE", request.start_date, request.end_date)
