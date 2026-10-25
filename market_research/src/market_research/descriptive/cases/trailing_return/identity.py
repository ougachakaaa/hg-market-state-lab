"""Exact trailing_return_inputs_v2 bytes; no acquisition or persistence."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date

from data_lake import CoverageResult

from ...observation.models import DailyKey, MissingDependency, ObservationJobSpec
from .inputs import FLOAT_FIELDS, POLICY, PROFILE, PreparedInputs


@dataclass(frozen=True)
class EndpointRequirement:
    anchor: date
    anchor_daily_key: DailyKey
    lookback_daily_key: DailyKey
    missing_required_facts: tuple[MissingDependency, ...]


@dataclass(frozen=True)
class TrailingReturnProvenance:
    prepared_inputs: PreparedInputs
    endpoint_requirements: tuple[EndpointRequirement, ...]
    expected_daily_keys: tuple[DailyKey, ...]
    available_daily_keys: tuple[DailyKey, ...]
    absent_daily_keys: tuple[DailyKey, ...]
    canonical_input_bytes: bytes
    input_fingerprint: str
    input_profile: str = PROFILE


def _coverage(value: CoverageResult) -> list[int | bool]:
    return [
        value.requested_units,
        value.successful_units,
        value.missing_units,
        value.pending_units,
        value.failed_units,
        value.complete,
    ]


def _key(value: DailyKey) -> list[str]:
    return [value[0], value[1].isoformat()]


def input_provenance(
    job: ObservationJobSpec,
    prepared: PreparedInputs,
    expected: tuple[DailyKey, ...],
    available: tuple[DailyKey, ...],
    endpoints: tuple[EndpointRequirement, ...],
) -> TrailingReturnProvenance:
    """Called only after complete public validation by pure construction."""
    window = job.historical_sample_window
    question = [
        job.metric,
        job.subject,
        [],
        job.horizon,
        "trading_sessions",
        window.start_date.isoformat(),
        window.end_date.isoformat(),
        "end_session",
        "inclusive",
    ]
    calendars = []
    for item in sorted(
        prepared.calendar_slices,
        key=lambda s: (s.request.start_date, s.request.end_date, s.request.exchange),
    ):
        view = item.final_export
        rows = [
            [
                row.exchange,
                row.cal_date.isoformat(),
                row.is_open,
                row.pretrade_date.isoformat() if row.pretrade_date is not None else None,
            ]
            for row in view.records
        ]
        calendars.append(
            [
                view.dataset,
                view.view,
                view.export_schema_version,
                item.request.exchange,
                item.request.start_date.isoformat(),
                item.request.end_date.isoformat(),
                _coverage(view.coverage),
                rows,
            ]
        )
    index_slice = None
    if prepared.index_slice is not None:
        item_index = prepared.index_slice
        index = item_index.final_export
        index_rows = [
            [
                row.index_code,
                row.symbol,
                row.name,
                row.market,
                row.publisher,
                row.category,
                row.trade_date.isoformat(),
                *(getattr(row, field).hex() for field in FLOAT_FIELDS),
            ]
            for row in index.records
        ]
        index_slice = [
            index.dataset,
            index.view,
            index.export_schema_version,
            list(item_index.request.index_codes),
            item_index.request.start_date.isoformat(),
            item_index.request.end_date.isoformat(),
            _coverage(index.coverage),
            index_rows,
        ]
    available_set = set(available)
    absent = tuple(key for key in expected if key not in available_set)
    requirements = [
        [
            item.anchor.isoformat(),
            _key(item.anchor_daily_key),
            _key(item.lookback_daily_key),
            [
                [dep.endpoint_role, _key(dep.fact.daily_key), dep.fact.field, dep.reason]
                for dep in item.missing_required_facts
            ],
        ]
        for item in endpoints
    ]
    payload = [
        PROFILE,
        POLICY,
        question,
        calendars,
        index_slice,
        [_key(key) for key in expected],
        [_key(key) for key in absent],
        requirements,
    ]
    canonical = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return TrailingReturnProvenance(
        prepared,
        endpoints,
        expected,
        available,
        absent,
        canonical,
        hashlib.sha256(canonical).hexdigest(),
    )
