"""Deterministic storage encoding, without provider-specific type coercion."""

import hashlib
import json
from collections.abc import Iterable

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]


def canonical_json(value: object) -> str:
    def validate(item: object) -> None:
        if item is None or type(item) in (bool, int, float, str):
            return
        if type(item) is list:
            for child in item:
                validate(child)
            return
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("Canonical object keys must be strings")
                validate(child)
            return
        raise ValueError("Dataset must normalize values to JSON primitives")

    validate(value)
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def record_hash(encoded_records: Iterable[str]) -> str:
    # Array framing avoids concatenation ambiguity and preserves multiplicity.
    encoded = "[" + ",".join(sorted(encoded_records)) + "]"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
