"""Pure financial observation construction from prepared input facts."""

from datetime import date
from math import isfinite, log
from typing import NoReturn

from data_lake import CoverageResult
from data_lake.datasets.tushare_index_daily import IndexDailyRange, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, TradeCalendarRecord
from market_research.algorithm.pip import PipResult, find_pips

from .inputs import ExportEvidence, InputAttempt, PreparedSegmentationInputs, SegmentationRequest
from .models import (
    ImportantPoint,
    ObservationConstructionError,
    PriceSegment,
    SegmentationDiagnostics,
    SegmentationObservationSet,
)


def construct_observations(
    request: SegmentationRequest, prepared_inputs: PreparedSegmentationInputs
) -> SegmentationObservationSet:
    """Construct an observation without fetching, modifying, or hashing market facts."""

    def fail(category: str, stage: str, reason: str) -> NoReturn:
        raise ObservationConstructionError(category, stage, reason, request, prepared_inputs)

    stage = "input validation"
    if not isinstance(request, SegmentationRequest) or not isinstance(
        prepared_inputs, PreparedSegmentationInputs
    ):
        fail("invalid_prepared_inputs", stage, "Expected a request and prepared inputs")
    if (
        request != prepared_inputs.request_identity
        or request.research != "price_segmentation_v1"
        or request.price_field != "close"
        or request.transform != "natural_log"
        or request.time_axis != "trading_session_index"
        or request.algorithm_id != "pip_vertical_error_bounded_v1"
        or type(request.epsilon) not in (int, float)
    ):
        fail("invalid_prepared_inputs", stage, "Invalid or inconsistent request identity")
    try:
        epsilon = float(request.epsilon)
    except (OverflowError, ValueError) as exc:
        raise ObservationConstructionError(
            "invalid_prepared_inputs", stage, "Invalid epsilon", request, prepared_inputs
        ) from exc
    if not isfinite(epsilon) or epsilon <= 0:
        fail("invalid_prepared_inputs", stage, "Epsilon must be finite and positive")
    dates, closes, logs = (
        prepared_inputs.session_dates,
        prepared_inputs.closes,
        prepared_inputs.log_prices,
    )
    if (
        type(dates) is not tuple
        or type(closes) is not tuple
        or type(logs) is not tuple
        or len(dates) < 2
        or len(dates) != len(closes)
        or len(dates) != len(logs)
        or type(prepared_inputs.input_point_count) is not int
        or prepared_inputs.input_point_count != len(dates)
    ):
        fail("invalid_prepared_inputs", stage, "Invalid input sequence lengths or types")
    if (
        any(type(d) is not date for d in dates)
        or any(a >= b for a, b in zip(dates, dates[1:], strict=False))
        or type(request.start_date) is not date
        or type(request.end_date) is not date
        or dates[0] < request.start_date
        or dates[-1] > request.end_date
    ):
        fail("invalid_prepared_inputs", stage, "Invalid session dates")
    if (
        any(type(x) is not float or not isfinite(x) or x <= 0 for x in closes)
        or any(type(x) is not float or not isfinite(x) for x in logs)
        or any(log(c) != y for c, y in zip(closes, logs, strict=True))
    ):
        fail("invalid_prepared_inputs", stage, "Invalid close or natural logarithm")
    fingerprint = prepared_inputs.input_fingerprint
    evidence = prepared_inputs.input_provenance
    if (
        type(fingerprint) is not str
        or len(fingerprint) != 64
        or any(c not in "0123456789abcdef" for c in fingerprint)
        or type(evidence) is not tuple
        or len(evidence) != 2
        or any(not isinstance(item, InputAttempt) or item.final_export is None for item in evidence)
    ):
        fail("invalid_prepared_inputs", stage, "Missing input fingerprint or source evidence")
    calendar, index = (item.final_export for item in evidence)
    if (
        not isinstance(calendar, ExportEvidence)
        or not isinstance(index, ExportEvidence)
        or calendar.dataset != "tushare_trade_calendar"
        or calendar.view != "calendar"
        or calendar.scope != ("SSE",)
        or index.dataset != "tushare_index_daily"
        or index.view != "index_daily"
        or index.scope != (request.index_code,)
        or not isinstance(evidence[0].request, TradeCalendarRange)
        or not isinstance(evidence[1].request, IndexDailyRange)
        or evidence[0].request.exchange != "SSE"
        or tuple(evidence[1].request.index_codes) != (request.index_code,)
        or any(
            (attempt.request.start_date, attempt.request.end_date)
            != (request.start_date, request.end_date)
            for attempt in evidence
        )
        or any(
            not isinstance(item.coverage, CoverageResult)
            or item.coverage.complete is not True
            or type(item.records) is not tuple
            for item in (calendar, index)
        )
        or any(
            (item.start_date, item.end_date) != (request.start_date, request.end_date)
            for item in (calendar, index)
        )
        or any(not isinstance(row, TradeCalendarRecord) for row in calendar.records)
        or any(not isinstance(row, IndexDailyRow) for row in index.records)
    ):
        fail("invalid_prepared_inputs", stage, "Invalid retained source identities")
    if (
        tuple(
            row.cal_date
            for row in calendar.records
            if isinstance(row, TradeCalendarRecord) and row.is_open == 1
        )
        != dates
        or tuple(
            (row.trade_date, row.close) for row in index.records if isinstance(row, IndexDailyRow)
        )
        != tuple(zip(dates, closes, strict=True))
        or any(
            row.index_code != request.index_code
            for row in index.records
            if isinstance(row, IndexDailyRow)
        )
    ):
        fail("invalid_prepared_inputs", stage, "Input facts differ from retained evidence")
    try:
        pip = find_pips(logs, epsilon=epsilon)
    except Exception as exc:
        raise ObservationConstructionError(
            "algorithm_failure", "pip", "PIP calculation failed", request, prepared_inputs
        ) from exc
    stage = "pip result validation"
    if not isinstance(pip, PipResult):
        fail("invalid_algorithm_result", stage, "Expected PipResult")
    indices = pip.indices
    error = pip.max_reconstruction_error
    if (
        pip.algorithm_id != request.algorithm_id
        or type(indices) is not tuple
        or len(indices) < 2
        or any(type(i) is not int or i < 0 or i >= len(dates) for i in indices)
        or indices[0] != 0
        or indices[-1] != len(dates) - 1
        or any(a >= b for a, b in zip(indices, indices[1:], strict=False))
        or type(error) is not float
        or not isfinite(error)
        or error < 0
        or error > epsilon
    ):
        fail("invalid_algorithm_result", stage, "Invalid PIP indices, identity or error")
    points = tuple(ImportantPoint(i, dates[i], closes[i]) for i in indices)
    segments = []
    for start, end in zip(points, points[1:], strict=False):
        amplitude = end.close / start.close - 1.0
        if not isfinite(amplitude):
            fail("numerical_failure", "segment construction", "Non-finite segment amplitude")
        direction = (
            "up" if end.close > start.close else "down" if end.close < start.close else "flat"
        )
        segments.append(
            PriceSegment(
                (prepared_inputs.request_identity, start.index, end.index),
                start.index,
                end.index,
                start.date,
                end.date,
                start.close,
                end.close,
                end.index - start.index,
                amplitude,
                direction,
                start.index == 0,
                end.index == len(dates) - 1,
            )
        )
    if (
        len(segments) != len(points) - 1
        or sum(segment.duration_sessions for segment in segments) != len(dates) - 1
        or any(a.end_index != b.start_index for a, b in zip(segments, segments[1:], strict=False))
    ):
        fail("invalid_observation", "result validation", "Segment coverage invariant failed")
    return SegmentationObservationSet(
        prepared_inputs.request_identity,
        points,
        tuple(segments),
        SegmentationDiagnostics(
            len(dates), len(points), len(segments), pip.algorithm_id, epsilon, error
        ),
        prepared_inputs,
    )
