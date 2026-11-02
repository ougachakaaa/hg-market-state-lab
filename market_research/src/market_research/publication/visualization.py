"""Pure adapters and conformance checks for the canonical Visualization V1 contract."""

from datetime import date
from math import isfinite
from typing import Any

from market_statistics import IntervalCountResult, QuantileResult, StatisticalResult

from .errors import InvalidPublicationInput


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise InvalidPublicationInput(reason)


def _object(value: object, fields: set[str], name: str) -> dict[str, Any]:
    _require(type(value) is dict and set(value) == fields, f"{name}: wrong object fields")
    return value  # type: ignore[return-value]


def _coordinate(value: object) -> dict[str, Any]:
    coord = _object(value, {"kind", "unit"}, "coordinate")
    kind, unit = coord["kind"], coord["unit"]
    _require(kind in ("number", "date", "category"), "unknown coordinate kind")
    _require(type(unit) is str and bool(unit), "coordinate unit must be nonempty")
    _require(kind != "date" or unit == "date", "invalid date unit")
    _require(kind != "category" or unit == "category", "invalid category unit")
    return coord


def _value(value: object, coordinate: dict[str, Any]) -> None:
    kind = coordinate["kind"]
    item: Any = value
    if kind == "number":
        try:
            finite = type(value) in (int, float) and isfinite(item)
        except OverflowError:
            finite = False
        _require(finite, "expected finite number")
    elif kind == "category":
        _require(type(value) is str and bool(value), "expected nonempty category")
    else:
        _require(type(value) is str and len(value) == 10, "expected canonical date")
        try:
            # ISO 8601 includes year 0000; date cannot represent it, so validate
            # the equivalent leap-year calendar shape separately.
            candidate = "2000" + item[4:] if item.startswith("0000-") else item
            valid = date.fromisoformat(candidate).isoformat() == candidate
        except ValueError:
            valid = False
        _require(valid, "expected canonical calendar date")


def validate_layer(layer: object) -> None:
    """Reject any violation of the published cross-language Layer V1 shape."""
    obj = _object(layer, {"type", "version", "x", "y", "data"}, "layer")
    _require(type(obj["version"]) is int and obj["version"] == 1, "unknown layer version")
    shapes = {
        "line": ("x", "y"),
        "bar": ("x", "y"),
        "point": ("x", "y"),
        "segment": ("x1", "y1", "x2", "y2"),
        "candlestick": ("x", "open", "high", "low", "close"),
        "area": ("x", "y0", "y1"),
    }
    kind = obj["type"]
    _require(type(kind) is str and kind in shapes, "unknown layer type")
    x, y = _coordinate(obj["x"]), _coordinate(obj["y"])
    if kind in ("area", "candlestick") or (kind == "bar" and x["kind"] == "category"):
        _require(y["kind"] == "number", "layer requires numeric y")
    _require(type(obj["data"]) is list, "layer data must be a list")
    categories: set[str] = set()
    for raw in obj["data"]:
        mark = _object(raw, set(shapes[kind]), "mark")
        for field in shapes[kind]:
            _value(mark[field], x if field.startswith("x") else y)
        if kind == "bar" and x["kind"] == "category":
            _require(mark["x"] not in categories, "duplicate bar category")
            categories.add(mark["x"])
        if kind == "candlestick":
            _require(
                mark["low"] <= mark["open"] <= mark["high"]
                and mark["low"] <= mark["close"] <= mark["high"],
                "invalid candle bounds",
            )


def validate_view(view: object) -> None:
    obj = _object(view, {"version", "axes", "layers", "layout", "presentation"}, "view")
    _require(type(obj["version"]) is int and obj["version"] == 1, "unknown view version")
    layout = _object(obj["layout"], {"title"}, "layout")
    presentation = _object(obj["presentation"], {"show_legend"}, "presentation")
    _require(type(layout["title"]) is str, "invalid title")
    _require(type(presentation["show_legend"]) is bool, "invalid legend setting")
    _require(type(obj["axes"]) is list and type(obj["layers"]) is list, "expected lists")
    axes: dict[str, dict[str, Any]] = {}
    for raw in obj["axes"]:
        axis = _object(raw, {"id", "orientation", "coordinate"}, "axis")
        identity = axis["id"]
        _require(
            type(identity) is str and bool(identity) and identity not in axes, "invalid axis id"
        )
        _require(axis["orientation"] in ("x", "y"), "invalid axis orientation")
        _coordinate(axis["coordinate"])
        axes[identity] = axis
    bindings: set[str] = set()
    for raw in obj["layers"]:
        binding = _object(raw, {"id", "layer", "x_axis", "y_axis"}, "binding")
        identity = binding["id"]
        _require(
            type(identity) is str and bool(identity) and identity not in bindings,
            "invalid binding id",
        )
        bindings.add(identity)
        validate_layer(binding["layer"])
        for direction in ("x", "y"):
            ref = binding[f"{direction}_axis"]
            _require(type(ref) is str and ref in axes, "unknown axis")
            axis = axes[ref]
            _require(axis["orientation"] == direction, "wrong axis orientation")
            _require(axis["coordinate"] == binding["layer"][direction], "coordinate mismatch")


def project(result: StatisticalResult) -> dict[str, dict[str, Any]]:
    """Project already validated associated results, never compute a statistic."""
    category = {"kind": "category", "unit": "category"}
    if type(result) is QuantileResult:
        layers = {
            "quantile": {
                "type": "line",
                "version": 1,
                "x": {"kind": "number", "unit": "probability"},
                "y": {"kind": "number", "unit": result.unit},
                "data": [{"x": point, "y": value} for point, value in result.points_and_values],
            }
        }
    elif type(result) is IntervalCountResult:
        labels = [f"< {result.edges[0]!r}"]
        labels.extend(
            (
                f"{'[' if b.left_inclusive else '('}{b.left!r}, {b.right!r}"
                f"{']' if b.right_inclusive else ')'}"
            )
            for b in result.bins
        )
        labels.append(f"> {result.edges[-1]!r}")
        values: dict[str, list[int | float]] = {
            "count": [
                result.underflow_count,
                *(b.count for b in result.bins),
                result.overflow_count,
            ],
            "frequency": [
                result.underflow_frequency,
                *(b.frequency for b in result.bins),
                result.overflow_frequency,
            ],
        }
        layers = {
            measure: {
                "type": "bar",
                "version": 1,
                "x": category.copy(),
                "y": {"kind": "number", "unit": measure},
                "data": [
                    {"x": label, "y": value} for label, value in zip(labels, sequence, strict=True)
                ],
            }
            for measure, sequence in values.items()
        }
    else:
        raise InvalidPublicationInput("unsupported statistical result")
    for layer in layers.values():
        validate_layer(layer)
    return layers


def materialize(layer: dict[str, Any], binding_id: str) -> dict[str, Any]:
    view = {
        "version": 1,
        "axes": [
            {"id": "x", "orientation": "x", "coordinate": layer["x"].copy()},
            {"id": "y", "orientation": "y", "coordinate": layer["y"].copy()},
        ],
        "layers": [{"id": binding_id, "layer": layer, "x_axis": "x", "y_axis": "y"}],
        "layout": {"title": ""},
        "presentation": {"show_legend": False},
    }
    validate_view(view)
    return view
