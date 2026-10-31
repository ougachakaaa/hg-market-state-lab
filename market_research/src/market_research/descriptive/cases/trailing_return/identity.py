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


def verify_input_provenance(job: ObservationJobSpec, provenance: TrailingReturnProvenance) -> None:
    """Verify retained final inputs and V2 bytes without constructing observations."""
    from .inputs import job_identity, resolve_calendar, validate_index, validate_job

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    require(type(provenance) is TrailingReturnProvenance, "invalid input provenance")
    validate_job(job, check_current_date=False)
    prepared = provenance.prepared_inputs
    require(
        type(prepared) is PreparedInputs and prepared.job_identity == job_identity(job),
        "prepared input identity mismatch",
    )
    anchors, sessions = resolve_calendar(job, prepared.calendar_slices)
    if anchors:
        item = prepared.index_slice
        require(item is not None, "missing index slice")
        assert item is not None
        require(
            tuple(item.request.index_codes) == (job.subject,)
            and item.request.start_date == sessions[0]
            and item.request.end_date == anchors[-1],
            "index slice scope mismatch",
        )
        rows = validate_index(item.final_export, item.request, sessions).records
    else:
        require(prepared.index_slice is None, "unexpected index slice")
        rows = ()
    expected = tuple((job.subject, day) for day in sessions)
    available = tuple((row.index_code, row.trade_date) for row in rows)
    absent = tuple(key for key in expected if key not in set(available))
    require(
        provenance.expected_daily_keys == expected
        and provenance.available_daily_keys == available
        and provenance.absent_daily_keys == absent,
        "daily key evidence mismatch",
    )
    require(len(provenance.endpoint_requirements) == len(anchors), "endpoint count mismatch")
    positions = {day: index for index, day in enumerate(sessions)}
    for anchor, endpoint in zip(anchors, provenance.endpoint_requirements, strict=True):
        lookback = sessions[positions[anchor] - job.horizon]
        anchor_key, lookback_key = (job.subject, anchor), (job.subject, lookback)
        require(
            endpoint.anchor == anchor
            and endpoint.anchor_daily_key == anchor_key
            and endpoint.lookback_daily_key == lookback_key,
            "endpoint identity mismatch",
        )
        missing = [
            (role, key)
            for role, key in (("anchor", anchor_key), ("lookback", lookback_key))
            if key not in set(available)
        ]
        require(len(endpoint.missing_required_facts) == len(missing), "endpoint absence mismatch")
        for dep, (role, key) in zip(endpoint.missing_required_facts, missing, strict=True):
            fact = dep.fact
            require(
                dep.endpoint_role == role
                and fact.daily_key == key
                and fact.dataset == "tushare_index_daily"
                and fact.view == "index_daily"
                and fact.export_schema_version == 1
                and fact.field == "close"
                and dep.reason == "daily_fact_unavailable",
                "missing fact mismatch",
            )
    rebuilt = input_provenance(job, prepared, expected, available, provenance.endpoint_requirements)
    require(
        provenance.input_profile == PROFILE
        and provenance.canonical_input_bytes == rebuilt.canonical_input_bytes
        and provenance.input_fingerprint == rebuilt.input_fingerprint,
        "input fingerprint mismatch",
    )
