"""Stable public failure classification for the pure holding simulation."""

from __future__ import annotations

from datetime import date


class HoldingSimulationError(Exception):
    """A classified simulation failure that never carries a partial timeline."""

    def __init__(
        self,
        category: str,
        reason: str,
        *,
        trade_date: date | None = None,
        contract_code: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.category = category
        self.reason = reason
        self.trade_date = trade_date
        self.contract_code = contract_code
        self.detail = detail
        super().__init__(f"{category}/{reason}")
