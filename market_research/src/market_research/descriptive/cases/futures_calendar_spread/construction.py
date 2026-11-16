"""Pure per-day public Slot resolution and WP1 financial API composition."""

from collections import defaultdict
from datetime import date
from typing import NoReturn

from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRow
from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailyUniverseEvidence,
    Slot,
    SlotResolutionError,
    resolve_daily_slots,
)

from .financial import (
    CalendarSpreadCalculationError,
    CalendarSpreadValidationError,
    compute_calendar_spread,
)
from .inputs import PreparedCalendarSpreadInputs
from .observations import (
    PAIRS,
    CalendarSpreadDay,
    CalendarSpreadObservationSet,
    ExpiryStage,
    ObservationConstructionError,
    OutcomeAccounting,
    PairDayObservation,
)
from .validation import PublicInputError, validate_prepared


def construct_observations(
    prepared_inputs: PreparedCalendarSpreadInputs,
) -> CalendarSpreadObservationSet:
    """Return every day's ordered pair outcomes or fail without partial success."""
    try:
        validate_prepared(prepared_inputs)
    except (PublicInputError, AttributeError, TypeError) as exc:
        raise ObservationConstructionError(
            "input_contract_error", "prepared_inputs", str(exc), prepared_inputs
        ) from exc
    prepared = prepared_inputs
    product = prepared.request.product_code
    daily_rows: dict[date, list[FuturesDailyRow]] = defaultdict(list)
    for row in prepared.futures_export.records:
        daily_rows[row.trade_date].append(row)
    days = []
    counts = {"valid": 0, "not_applicable": 0, "excluded": 0}
    for session in prepared.calendar_export.records:
        day = session.cal_date
        if session.is_open == 0:
            days.append(CalendarSpreadDay(day, "closed", "non_trading_day", None, ()))
            continue
        rows = daily_rows[day]
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
            product,
            day,
            True,
            tuple(row.contract_code for row in rows),
            "prepared_inputs.futures_export",
        )
        try:
            resolution = resolve_daily_slots(product, day, metadata, evidence=evidence)
        except SlotResolutionError as exc:
            raise ObservationConstructionError(
                "slot_resolution_error", "futures", str(exc), prepared, day
            ) from exc
        by_code = {row.contract_code: row for row in rows}
        by_slot = {mapping.slot: mapping.contract for mapping in resolution.mappings}
        pairs = []
        for near_slot, far_slot in PAIRS:

            def fail(
                reason: str,
                day: date = day,
                near_slot: Slot = near_slot,
                far_slot: Slot = far_slot,
            ) -> NoReturn:
                raise ObservationConstructionError(
                    "input_contract_error", "futures", reason, prepared, day, near_slot, far_slot
                )

            near_contract, far_contract = by_slot[near_slot], by_slot[far_slot]
            if near_contract is None and far_contract is None:
                pair = PairDayObservation(
                    product,
                    day,
                    near_slot,
                    far_slot,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "not_applicable",
                    "no_active_contract",
                    evidence,
                )
            else:
                if near_contract is None or far_contract is None:
                    fail("Partial Slot absence")
                near = by_code.get(near_contract.contract_code)
                far = by_code.get(far_contract.contract_code)
                if near is None or far is None:
                    fail("Missing resolved contract quote")
                if near.contract_code == far.contract_code:
                    fail("Identical near/far contracts")
                delta = (far.delist_date - near.delist_date).days
                dte = (near.delist_date - day).days
                if delta <= 0 or dte < 0:
                    fail("Invalid pair expiry spacing/lifecycle")
                stage: ExpiryStage = "0_7" if dte <= 7 else "8_21" if dte <= 21 else "22_plus"
                if near.close <= 0.0 or far.close <= 0.0:
                    pair = PairDayObservation(
                        product,
                        day,
                        near_slot,
                        far_slot,
                        near,
                        far,
                        delta,
                        dte,
                        stage,
                        None,
                        "excluded",
                        "nonpositive_close",
                        evidence,
                    )
                else:
                    try:
                        metrics = compute_calendar_spread(
                            near.close, far.close, near.delist_date, far.delist_date
                        )
                    except CalendarSpreadCalculationError as exc:
                        raise ObservationConstructionError(
                            "calculation_failure",
                            "financial_core",
                            str(exc),
                            prepared,
                            day,
                            near_slot,
                            far_slot,
                        ) from exc
                    except CalendarSpreadValidationError as exc:
                        raise ObservationConstructionError(
                            "input_contract_error",
                            "financial_core",
                            str(exc),
                            prepared,
                            day,
                            near_slot,
                            far_slot,
                        ) from exc
                    pair = PairDayObservation(
                        product,
                        day,
                        near_slot,
                        far_slot,
                        near,
                        far,
                        metrics.delta_days,
                        dte,
                        stage,
                        metrics,
                        "valid",
                        None,
                        evidence,
                    )
            counts[pair.outcome] += 1
            pairs.append(pair)
        days.append(CalendarSpreadDay(day, "open", None, resolution, tuple(pairs)))
    return CalendarSpreadObservationSet(
        prepared,
        tuple(days),
        OutcomeAccounting(
            6 * len(prepared.candidate_dates),
            counts["valid"],
            counts["not_applicable"],
            counts["excluded"],
        ),
    )
