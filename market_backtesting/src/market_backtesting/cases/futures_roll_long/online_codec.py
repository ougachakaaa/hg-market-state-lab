"""Bounded strict JSON for this case's existing immutable result graph only."""

import json
import re
from collections.abc import Sequence
from dataclasses import asdict, fields, is_dataclass
from datetime import date
from math import isfinite
from types import UnionType
from typing import Any, Literal, Union, cast, get_args, get_origin, get_type_hints

from .application_models import FuturesRollRequest, validate_futures_roll_request
from .online_models import FuturesRollOnlineError
from .result_models import DEFINITION_VERSION, LIMITATIONS, RESULT_PROFILE, BacktestResult
from .visualization import DateCoordinate, NumberCoordinate, validate_view_v2

RESULT_LIMIT = 32 * 1024 * 1024
METADATA_LIMIT = 16 * 1024


def json_bytes(value: Any, limit: int = METADATA_LIMIT) -> bytes:
    def default(item: Any) -> str:
        if type(item) is date:
            return item.isoformat()
        raise ValueError("unsupported_json")

    chunks = bytearray()
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False, default=default
    )
    for part in encoder.iterencode(value):
        encoded = part.encode("utf-8")
        if len(chunks) + len(encoded) > limit:
            raise FuturesRollOnlineError("result_too_large")
        chunks.extend(encoded)
    return bytes(chunks)


def strict_json(payload: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise ValueError("nonfinite_json")

    return json.loads(payload.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def decode_value(kind: Any, raw: Any) -> Any:
    """Reconstruct only statically referenced dataclass types; no payload type names."""
    origin, args = get_origin(kind), get_args(kind)
    if origin in (UnionType, Union):
        for choice in args:
            try:
                return decode_value(choice, raw)
            except (ValueError, TypeError):
                pass
        raise ValueError("union_type")
    if origin is Literal:
        if any(type(raw) is type(value) and raw == value for value in args):
            return raw
        raise ValueError("literal")
    if origin is Sequence:
        if type(raw) is not list:
            raise ValueError("sequence_type")
        return tuple(decode_value(args[0], item) for item in raw)
    if origin is tuple:
        if type(raw) is not list or len(args) != 2 or args[1] is not Ellipsis:
            raise ValueError("sequence_type")
        return tuple(decode_value(args[0], item) for item in raw)
    if is_dataclass(kind):
        expected = fields(kind)
        if type(raw) is not dict or set(raw) != {field.name for field in expected}:
            raise ValueError("object_fields")
        hints = get_type_hints(kind)
        values = {
            field.name: decode_value(hints[field.name], raw[field.name]) for field in expected
        }
        instance = cast(Any, kind)(
            **{field.name: values[field.name] for field in expected if field.init}
        )
        if kind in (DateCoordinate, NumberCoordinate) and instance != cast(Any, kind)():
            raise ValueError("coordinate_kind")
        if any(getattr(instance, field.name) != values[field.name] for field in expected):
            raise ValueError("constant_field")
        return instance
    if kind is date:
        if type(raw) is not str:
            raise ValueError("date_type")
        result = date.fromisoformat(raw)
        if result.isoformat() != raw:
            raise ValueError("date_format")
        return result
    if kind is float:
        if type(raw) not in (float, int) or not isfinite(raw):
            raise ValueError("finite_number")
        return raw
    if kind in (str, int, bool, type(None)) and type(raw) is kind:
        return raw
    raise ValueError("scalar_type")


def decode_request(raw: Any) -> FuturesRollRequest:
    request: FuturesRollRequest = decode_value(FuturesRollRequest, raw)
    validate_futures_roll_request(request)
    return request


def validate_stored_result(result: BacktestResult, request: FuturesRollRequest) -> None:
    """Check shape/associations/projections without executing financial formulas."""
    if (
        result.profile != RESULT_PROFILE
        or result.definition_version != DEFINITION_VERSION
        or result.case != request.case
        or result.status != "complete"
        or result.request != request
        or result.evidence.result_profile != RESULT_PROFILE
        or result.evidence.definition_version != DEFINITION_VERSION
        or result.evidence.input_profile != "futures_roll_long_inputs_v1"
        or re.fullmatch("[0-9a-f]{64}", result.evidence.input_fingerprint) is None
        or result.evidence.limitations != LIMITATIONS
        or not result.daily
    ):
        raise ValueError("result_identity")
    dates = tuple(row.trade_date for row in result.daily)
    if (
        dates != tuple(sorted(set(dates)))
        or result.window.cffex_session_count != len(dates)
        or len(dates) < 2
        or (result.window.first_session, result.window.last_session) != (dates[0], dates[-1])
        or not request.start_date <= dates[0] <= dates[-1] <= request.end_date
        or result.daily[-1].position_contract_code is not None
        or result.summary.total_pnl != result.daily[-1].cumulative_pnl
        or result.summary.gross_return != result.daily[-1].cumulative_return
        or result.summary.benchmark_return != result.daily[-1].benchmark_cumulative_return
        or result.summary.excess_return != result.daily[-1].excess_cumulative_return
        or result.summary.initial_notional != result.initial_notional.value
        or result.summary.execution_count != len(result.trades)
        or result.summary.roll_count != len(result.rolls)
        or any(row.equity <= 0 or row.benchmark_equity <= 0 for row in result.daily)
    ):
        raise ValueError("result_association")
    for public_request in (
        result.evidence.public_requests.calendar_cffex,
        result.evidence.public_requests.futures,
        result.evidence.public_requests.index,
    ):
        if (public_request.start_date, public_request.end_date) != (
            request.start_date,
            request.end_date,
        ):
            raise ValueError("public_request")
    public = result.evidence.public_requests
    if (
        public.calendar_cffex.exchange != "CFFEX"
        or public.futures.product_codes != (request.product_code,)
        or public.index.index_codes != (result.benchmark.index_code,)
    ):
        raise ValueError("public_identity")
    if tuple(row.dependency for row in result.evidence.coverage) != (
        "calendar_cffex",
        "futures",
        "index",
    ) or any(
        not row.complete
        or row.requested_units != row.successful_units
        or any((row.missing_units, row.pending_units, row.failed_units))
        for row in result.evidence.coverage
    ):
        raise ValueError("coverage")
    for view, names in (
        (result.views.returns, ("cumulative_return", "benchmark_cumulative_return")),
        (result.views.drawdown, ("drawdown", "benchmark_drawdown")),
    ):
        validate_view_v2(view)
        if len(view.layers) != 2:
            raise ValueError("view_layers")
        for binding, name in zip(view.layers, names, strict=True):
            if tuple((mark.x, mark.y) for mark in binding.layer.data) != tuple(
                (row.trade_date.isoformat(), getattr(row, name)) for row in result.daily
            ):
                raise ValueError("view_association")


def decode_result(payload: bytes, request: FuturesRollRequest) -> BacktestResult:
    if len(payload) > RESULT_LIMIT:
        raise ValueError("result_size")
    result: BacktestResult = decode_value(BacktestResult, strict_json(payload))
    validate_stored_result(result, request)
    return result


def encode_result(result: BacktestResult, request: FuturesRollRequest) -> bytes:
    payload = json_bytes(asdict(result), RESULT_LIMIT)
    if decode_result(payload, request) != result:
        raise ValueError("serialization_roundtrip")
    return payload
