"""Immutable single-position replay contracts; no market-specific dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Generic, Literal, TypeVar


class CoreError(Exception):
    """A deterministic validation/computation failure, never a partial result."""

    def __init__(
        self,
        category: str,
        reason: str,
        *,
        trade_date: date | None = None,
        instrument_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.category = category
        self.reason = reason
        self.trade_date = trade_date
        self.instrument_id = instrument_id
        self.detail = detail
        super().__init__(f"{category}/{reason}")


def finite_number(value: float, name: str, *, positive: bool = False) -> float:
    """Reject bool, non-numeric, overflow and non-finite arithmetic explicitly."""
    if type(value) not in (int, float):
        raise CoreError("invalid_numeric", name)
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise CoreError("invalid_numeric", name) from exc
    if not isfinite(number) or (positive and number <= 0):
        raise CoreError("invalid_numeric", name)
    return number


def require_date(value: date) -> None:
    if type(value) is not date:
        raise CoreError("invalid_input", "date_only_required")


def require_text(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CoreError("invalid_input", "nonempty_identity_required")


@dataclass(frozen=True, slots=True)
class InstrumentReference:
    instrument_id: str
    multiplier: float
    source_ref: str

    def __post_init__(self) -> None:
        require_text(self.instrument_id)
        require_text(self.source_ref)
        finite_number(self.multiplier, "multiplier", positive=True)


@dataclass(frozen=True, slots=True)
class TargetPosition:
    instrument: InstrumentReference
    quantity: float

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentReference):
            raise CoreError("invalid_input", "instrument_reference_required")
        finite_number(self.quantity, "quantity", positive=True)


@dataclass(frozen=True, slots=True)
class Position:
    instrument: InstrumentReference
    quantity: float
    reference_price: float
    valuation_date: date

    def __post_init__(self) -> None:
        TargetPosition(self.instrument, self.quantity)
        finite_number(self.reference_price, "reference_price", positive=True)
        require_date(self.valuation_date)


@dataclass(frozen=True, slots=True)
class Portfolio:
    position: Position | None = None

    def __post_init__(self) -> None:
        if self.position is not None and not isinstance(self.position, Position):
            raise CoreError("invalid_input", "single_position_required")


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    reason: str
    source_ref: str
    selection_role: str | None = None
    previous_role: str | None = None

    def __post_init__(self) -> None:
        require_text(self.reason)
        require_text(self.source_ref)
        for role in (self.selection_role, self.previous_role):
            if role is not None:
                require_text(role)


@dataclass(frozen=True, slots=True)
class TargetPortfolio:
    position: TargetPosition | None = None
    evidence: DecisionEvidence | None = None

    def __post_init__(self) -> None:
        if self.position is not None and not isinstance(self.position, TargetPosition):
            raise CoreError("invalid_input", "single_target_required")
        if self.evidence is not None and not isinstance(self.evidence, DecisionEvidence):
            raise CoreError("invalid_input", "decision_evidence_required")


@dataclass(frozen=True, slots=True)
class CloseQuote:
    instrument_id: str
    close: float

    def __post_init__(self) -> None:
        require_text(self.instrument_id)
        finite_number(self.close, "close", positive=True)


@dataclass(frozen=True, slots=True)
class DailyMarketSnapshot:
    trade_date: date
    quotes: tuple[CloseQuote, ...]
    source_ref: str

    def __post_init__(self) -> None:
        require_date(self.trade_date)
        require_text(self.source_ref)
        if not isinstance(self.quotes, tuple) or any(
            not isinstance(quote, CloseQuote) for quote in self.quotes
        ):
            raise CoreError("invalid_input", "immutable_quotes_required")
        codes = [quote.instrument_id for quote in self.quotes]
        if len(set(codes)) != len(codes):
            raise CoreError("invalid_input", "duplicate_quote", trade_date=self.trade_date)

    def close_for(self, instrument_id: str) -> float:
        for quote in self.quotes:
            if quote.instrument_id == instrument_id:
                return quote.close
        raise CoreError(
            "missing_market_fact",
            "missing_instrument_quote",
            trade_date=self.trade_date,
            instrument_id=instrument_id,
        )


@dataclass(frozen=True, slots=True)
class CloseAssumptions:
    execution: Literal["session_close"]
    valuation: Literal["session_close"]

    def __post_init__(self) -> None:
        if self.execution != "session_close" or self.valuation != "session_close":
            raise CoreError("invalid_input", "unsupported_price_model")


@dataclass(frozen=True, slots=True)
class StateEvent:
    kind: Literal["mark", "close", "open"]
    before: Position | None
    after: Position | None
    price: float


@dataclass(frozen=True, slots=True)
class PricingEvidence:
    instrument: InstrumentReference
    quantity: float
    previous_reference: float
    current_close: float


@dataclass(frozen=True, slots=True)
class TransitionResult:
    trade_date: date
    previous_portfolio: Portfolio
    target: TargetPortfolio
    snapshot: DailyMarketSnapshot
    assumptions: CloseAssumptions
    daily_pnl: float
    pricing: PricingEvidence | None
    events: tuple[StateEvent, ...]
    next_portfolio: Portfolio

    @property
    def position_changes(self) -> tuple[StateEvent, ...]:
        return tuple(event for event in self.events if event.kind != "mark")


@dataclass(frozen=True, slots=True)
class AccountingState:
    initial_capital: float
    cumulative_pnl: float = 0.0
    equity: float = 0.0
    cumulative_return: float = 0.0
    trade_date: date | None = None
    daily_return: float = 0.0

    @classmethod
    def start(cls, initial_capital: float) -> AccountingState:
        finite_number(initial_capital, "initial_capital", positive=True)
        return cls(initial_capital, equity=initial_capital)


@dataclass(frozen=True, slots=True)
class DailyRecord:
    trade_date: date
    transition: TransitionResult
    accounting: AccountingState

    @property
    def previous_portfolio(self) -> Portfolio:
        return self.transition.previous_portfolio

    @property
    def target(self) -> TargetPortfolio:
        return self.transition.target

    @property
    def next_portfolio(self) -> Portfolio:
        return self.transition.next_portfolio


Context = TypeVar("Context")


@dataclass(frozen=True, slots=True)
class ReplaySession(Generic[Context]):
    trade_date: date
    decision_context: Context
    snapshot: DailyMarketSnapshot


@dataclass(frozen=True, slots=True)
class ReplayResult:
    initial_capital: float
    assumptions: CloseAssumptions
    daily: tuple[DailyRecord, ...]

    @property
    def final_portfolio(self) -> Portfolio:
        return self.daily[-1].next_portfolio
