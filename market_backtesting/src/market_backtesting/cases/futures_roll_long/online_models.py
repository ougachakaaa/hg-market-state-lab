"""Safe online public values, independent of transport and private storage."""

from dataclasses import dataclass
from typing import Literal

from ...core import CoreError
from .application_models import FuturesRollApplicationError, FuturesRollRequest
from .failures import FuturesRollError

RunState = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"]
TERMINAL = frozenset({"COMPLETED", "FAILED", "INTERRUPTED"})
STAGES = frozenset(
    {
        "request",
        "export",
        "ensure",
        "prepare",
        "replay",
        "analysis",
        "result_validation",
        "result_publication",
        "execution",
    }
)
DEPENDENCIES = frozenset({"calendar_cffex", "calendar_sse", "futures", "index"})
CATEGORIES = frozenset(
    {
        "invalid_request",
        "upstream_operation",
        "incomplete_input",
        "invalid_public_input",
        "invalid_case_input",
        "slot_resolution",
        "missing_market_fact",
        "invalid_price",
        "roll_target_invalid",
        "invalid_contract_lifecycle",
        "invalid_position_state",
        "invalid_input",
        "invalid_target",
        "invalid_numeric",
        "invalid_accounting",
        "accounting_failure",
        "invalid_result",
        "invalid_evidence",
    }
)


@dataclass(frozen=True, slots=True)
class OnlineFailure:
    stage: str
    category: str
    dependency: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class OnlineRunStatus:
    run_id: str
    status: RunState
    request: FuturesRollRequest
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    failure: OnlineFailure | None = None


class FuturesRollOnlineError(Exception):
    """Only a fixed safe operation classification is public."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def project_failure(exc: BaseException, stage: str = "execution") -> OnlineFailure:
    if isinstance(exc, FuturesRollApplicationError):
        stage = exc.stage
        dependency = exc.dependency
    else:
        dependency = None
    if (
        isinstance(exc, FuturesRollError | CoreError)
        and type(stage) is str
        and stage in STAGES
        and type(exc.category) is str
        and exc.category in CATEGORIES
        and type(exc.reason) is str
        and exc.reason in SAFE_REASONS
        and (dependency is None or (type(dependency) is str and dependency in DEPENDENCIES))
    ):
        return OnlineFailure(stage, exc.category, dependency, exc.reason)
    return OnlineFailure("execution", "internal_failure", None, "internal_failure")


# Fixed public vocabulary audited against WP3/WP4; never derived at runtime.
SAFE_REASONS = frozenset(
    {
        "cache_incompatible",
        "operation_unavailable",
        "credential_missing",
        "upstream_request_rejected",
        "missing_contract_row",
        "entry_multiplier",
        "accounting_failure",
        "accounting_projection_mismatch",
        "accounting_session_mismatch",
        "assumptions_mismatch",
        "assumptions_required",
        "benchmark_cumulative_return",
        "benchmark_daily_return",
        "benchmark_drawdown",
        "benchmark_equity",
        "benchmark_return",
        "benchmark_session_mismatch",
        "calendar_payload_count_mismatch",
        "capital_mismatch",
        "close",
        "close_state_mismatch",
        "conflicting_contract_metadata",
        "conflicting_index_metadata",
        "conflicting_product",
        "conflicting_underlying",
        "contract_attribution_mismatch",
        "cumulative_pnl",
        "cumulative_return",
        "daily_pnl",
        "daily_return",
        "daily_session_mismatch",
        "date_only_required",
        "decision_evidence_required",
        "decision_reason_mismatch",
        "definition_version_mismatch",
        "delist_date_not_session",
        "drawdown",
        "duplicate_contract_close",
        "duplicate_contract_code",
        "duplicate_delivery_month",
        "duplicate_instrument_reference",
        "duplicate_quote",
        "duplicate_session",
        "duplicate_session_facts",
        "entry_multiplier_mismatch",
        "entry_row_mismatch",
        "entry_values_mismatch",
        "equity",
        "event_price_mismatch",
        "event_reference_mismatch",
        "excess_cumulative_return",
        "excess_return",
        "execution_count_mismatch",
        "execution_identity_mismatch",
        "execution_projection_mismatch",
        "expiring_held_contract_not_m0",
        "final_export_incomplete",
        "final_state_not_flat",
        "fingerprint_mismatch",
        "future_window",
        "futures_payload_count_mismatch",
        "held_contract_expired_without_roll",
        "held_contract_inactive",
        "held_contract_missing_from_active_set",
        "held_instrument_conflict",
        "immutable_evidence_required",
        "immutable_quotes_required",
        "immutable_records_required",
        "incomplete_input",
        "incomplete_retained_inputs",
        "inconsistent_coverage",
        "inconsistent_previous_accounting",
        "index_association_mismatch",
        "index_date_outside_sse_sessions",
        "index_payload_count_mismatch",
        "initial_capital",
        "initial_capital_mismatch",
        "initial_notional",
        "input_profile_mismatch",
        "instrument_reference_conflict",
        "instrument_reference_mismatch",
        "instrument_reference_required",
        "instrument_reference_scope_mismatch",
        "insufficient_sessions",
        "invalid_accounting",
        "invalid_calendar_fact",
        "invalid_calendar_identity",
        "invalid_calendar_record",
        "invalid_case",
        "invalid_case_input",
        "invalid_contract_identity",
        "invalid_contract_lifecycle",
        "invalid_contract_metadata",
        "invalid_coverage_counters",
        "invalid_coverage_type",
        "invalid_decision_evidence",
        "invalid_delivery_month",
        "invalid_ensure_result",
        "invalid_evidence",
        "invalid_execution",
        "invalid_export_identity",
        "invalid_export_type",
        "invalid_futures_date",
        "invalid_futures_numeric",
        "invalid_futures_record",
        "invalid_futures_text",
        "invalid_index_closes",
        "invalid_index_identity",
        "invalid_index_metadata",
        "invalid_index_numeric",
        "invalid_index_record",
        "invalid_input",
        "invalid_input_shape",
        "invalid_instrument_references",
        "invalid_json",
        "invalid_numeric",
        "invalid_numeric_type",
        "invalid_performance_identity",
        "invalid_position_state",
        "invalid_price",
        "invalid_product_code",
        "invalid_public_input",
        "invalid_replay_result",
        "invalid_request",
        "invalid_request_type",
        "invalid_result",
        "invalid_result_type",
        "invalid_session_facts",
        "invalid_shape",
        "invalid_strategy_profile",
        "invalid_target",
        "invalid_underlying_identity",
        "invalid_visualization_v2",
        "inverted_window",
        "malformed_evidence",
        "mark_identity_mismatch",
        "missing_active_contract_metadata",
        "missing_cffex_index_close",
        "missing_daily_position",
        "missing_decision",
        "missing_decision_evidence",
        "missing_entry_target",
        "missing_event_position",
        "missing_execution_position",
        "missing_instrument_quote",
        "missing_market_fact",
        "missing_multiplier",
        "missing_pnl_position",
        "missing_pricing",
        "missing_session_facts",
        "missing_underlying",
        "multiplier",
        "multiplier_mismatch",
        "no_position_on_final_session",
        "non_finite_close",
        "non_positive_close",
        "non_positive_equity",
        "nonempty_identity_required",
        "nonempty_sessions_required",
        "nonfinite_output",
        "observed_window_mismatch",
        "open_target_mismatch",
        "performance_association_mismatch",
        "pnl_projection_mismatch",
        "policy_source_mismatch",
        "portfolio_chain_mismatch",
        "portfolio_required",
        "pricing_association_mismatch",
        "public_request_mismatch",
        "quantity",
        "quantity_change_unsupported",
        "record_date_mismatch",
        "reference_price",
        "replay_input_mismatch",
        "replay_session_required",
        "request_mismatch",
        "requested_units_mismatch",
        "result_projection_mismatch",
        "roll_expiry_mismatch",
        "roll_projection_mismatch",
        "roll_slot_mismatch",
        "roll_target_invalid",
        "scope_mismatch",
        "session_already_accounted",
        "session_order_not_increasing",
        "sessions_not_increasing",
        "single_position_required",
        "single_target_required",
        "slot_resolution",
        "snapshot_and_assumptions_required",
        "snapshot_association_mismatch",
        "snapshot_date_mismatch",
        "snapshot_required",
        "state_event_before_mismatch",
        "state_event_order_mismatch",
        "state_reconstruction_mismatch",
        "summary_drawdown_mismatch",
        "summary_return_mismatch",
        "target_equal_held_contract",
        "target_expired",
        "target_inactive",
        "target_not_resolved",
        "target_portfolio_required",
        "target_state_mismatch",
        "target_without_holding_period",
        "total_pnl_mismatch",
        "unexpected_flat_state",
        "unknown_contract_fact",
        "unknown_underlying",
        "unordered_or_duplicate_calendar",
        "unordered_or_duplicate_contract_date",
        "unordered_or_duplicate_index_date",
        "unsupported_price_model",
        "upstream_operation",
        "valuation_date_not_before_session",
        "w1_slot_resolution_error",
        "window_mismatch",
        "window_too_large",
    }
)
