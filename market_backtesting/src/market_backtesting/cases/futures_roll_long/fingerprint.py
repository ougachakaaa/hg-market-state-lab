"""The case-specific futures_roll_long_inputs_v1 canonical encoding."""

from __future__ import annotations

import hashlib
import json
from datetime import date

from data_lake import ExportEnvelope

from .application_models import PublicInputExports
from .input_validation import (
    CALENDAR_FIELDS,
    COVERAGE_FIELDS,
    FUTURES_FIELDS,
    FUTURES_FLOATS,
    INDEX_FIELDS,
    INDEX_FLOATS,
)


def _fields(
    value: object, names: tuple[str, ...], floats: tuple[str, ...] = ()
) -> dict[str, object]:
    result: dict[str, object] = {}
    for name in names:
        item = getattr(value, name)
        if item is not None and name in floats:
            result[name] = ["float64", float(item).hex()]
        elif type(item) is date:
            result[name] = item.isoformat()
        else:
            result[name] = item
    return result


def _header(export: ExportEnvelope, scope_field: str) -> dict[str, object]:
    return {
        "dataset": export.dataset,
        "view": export.view,
        "export_schema_version": export.export_schema_version,
        "scope": _fields(export.scope, (scope_field,)),
        "window": _fields(export.window, ("start_date", "end_date")),
        "coverage": _fields(export.coverage, COVERAGE_FIELDS),
    }


def canonical_input_bytes(exports: PublicInputExports) -> bytes:
    """Internal encoding of already fully validated, complete retained exports."""
    calendar = _header(exports.calendar_cffex, "exchange")
    calendar["records"] = [_fields(row, CALENDAR_FIELDS) for row in exports.calendar_cffex.records]
    futures = _header(exports.futures, "product_codes")
    futures["records"] = [
        _fields(row, FUTURES_FIELDS, FUTURES_FLOATS) for row in exports.futures.records
    ]
    index = _header(exports.index, "index_codes")
    index["records"] = [_fields(row, INDEX_FIELDS, INDEX_FLOATS) for row in exports.index.records]
    return json.dumps(
        {
            "profile": "futures_roll_long_inputs_v1",
            "calendar_cffex": calendar,
            "futures": futures,
            "index": index,
        },
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def input_fingerprint(exports: PublicInputExports) -> str:
    return hashlib.sha256(canonical_input_bytes(exports)).hexdigest()
