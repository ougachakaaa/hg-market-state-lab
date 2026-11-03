"""Price Segmentation input preparation contracts."""

from dataclasses import dataclass
from datetime import date

from data_lake import CoverageResult, EnsureResult
from data_lake.datasets.tushare_index_daily import IndexDailyRange, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, TradeCalendarRecord


@dataclass(frozen=True, slots=True)
class SegmentationRequest:
    index_code: str
    start_date: date
    end_date: date
    epsilon: float
    research: str = "price_segmentation_v1"
    price_field: str = "close"
    transform: str = "natural_log"
    time_axis: str = "trading_session_index"
    algorithm_id: str = "pip_vertical_error_bounded_v1"


@dataclass(frozen=True, slots=True)
class ExportEvidence:
    dataset: str
    view: str
    schema_version: int
    scope: tuple[str, ...]
    start_date: date
    end_date: date
    coverage: CoverageResult
    records: tuple[TradeCalendarRecord | IndexDailyRow, ...]


@dataclass(frozen=True, slots=True)
class InputAttempt:
    request: TradeCalendarRange | IndexDailyRange
    preliminary_export: ExportEvidence | None = None
    ensure_result: EnsureResult | None = None
    final_export: ExportEvidence | None = None


@dataclass(frozen=True, slots=True)
class PreparedSegmentationInputs:
    request_identity: SegmentationRequest
    session_dates: tuple[date, ...]
    closes: tuple[float, ...]
    log_prices: tuple[float, ...]
    input_point_count: int
    input_fingerprint: str
    input_provenance: tuple[InputAttempt, ...]


class InputPreparationError(Exception):
    """Failure with phase, semantic request and available validated public evidence."""

    def __init__(
        self,
        category: str,
        stage: str,
        request: object,
        reason: str,
        evidence: tuple[InputAttempt, ...] = (),
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.stage = stage
        self.request = request
        self.reason = reason
        self.evidence = evidence
