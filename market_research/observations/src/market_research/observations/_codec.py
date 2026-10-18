"""Private safe JSON primitives for owned immutable values; no business schema."""

import json
import types
from dataclasses import fields, is_dataclass
from datetime import date
from typing import Any, get_args, get_origin, get_type_hints


def _encode(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _encode(getattr(value, field.name)) for field in fields(value)}
    if type(value) is date:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError("Unsupported owned value")


def encode(value: object) -> str:
    return json.dumps(_encode(value), allow_nan=False, separators=(",", ":"))


def _decode(expected: Any, value: Any) -> Any:
    if get_origin(expected) is types.UnionType:
        if value is None and type(None) in get_args(expected):
            return None
        return _decode(next(kind for kind in get_args(expected) if kind is not type(None)), value)
    if get_origin(expected) is tuple:
        if not isinstance(value, list):
            raise ValueError("Invalid retained sequence")
        return tuple(_decode(get_args(expected)[0], item) for item in value)
    if expected is date:
        if not isinstance(value, str):
            raise ValueError("Invalid retained date")
        result = date.fromisoformat(value)
        if result.isoformat() != value:
            raise ValueError("Noncanonical retained date")
        return result
    if isinstance(expected, type) and is_dataclass(expected):
        hints = get_type_hints(expected)
        if not isinstance(value, dict) or set(value) != set(hints):
            raise ValueError("Invalid retained fields")
        return expected(**{name: _decode(kind, value[name]) for name, kind in hints.items()})
    if type(value) is not expected:
        raise ValueError("Invalid retained value type")
    return value


def decode[T](expected: type[T], payload: str) -> T:
    return _decode(expected, json.loads(payload))
