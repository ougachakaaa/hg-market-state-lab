"""Producer-side immutable shapes conforming to ui_web/VISUALIZATION_V2.md."""

from dataclasses import asdict, dataclass
from datetime import date
from math import isfinite
from typing import Any

from .failures import FuturesRollError
from .models import DailyPerformance, FuturesRollReplay


@dataclass(frozen=True, slots=True)
class DateCoordinate:
    kind: str = "date"
    unit: str = "date"


@dataclass(frozen=True, slots=True)
class NumberCoordinate:
    kind: str = "number"
    unit: str = "decimal_ratio"


@dataclass(frozen=True, slots=True)
class Detail:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class DateMark:
    x: str
    y: float | None
    segment_id: str
    details: tuple[Detail, ...] = ()


@dataclass(frozen=True, slots=True)
class LineV2:
    type: str
    version: int
    x: DateCoordinate
    y: NumberCoordinate
    data: tuple[DateMark, ...]


@dataclass(frozen=True, slots=True)
class AxisV2:
    id: str
    orientation: str
    coordinate: DateCoordinate | NumberCoordinate


@dataclass(frozen=True, slots=True)
class BindingV2:
    id: str
    label: str
    layer: LineV2
    x_axis: str
    y_axis: str


@dataclass(frozen=True, slots=True)
class EventV2:
    id: str
    x_axis: str
    x: str
    label: str
    details: tuple[Detail, ...]


@dataclass(frozen=True, slots=True)
class LayoutV2:
    title: str


@dataclass(frozen=True, slots=True)
class PresentationV2:
    show_legend: bool = True
    zoom: bool = True
    pan: bool = True
    reset: bool = True


@dataclass(frozen=True, slots=True)
class ViewV2:
    version: int
    axes: tuple[AxisV2, ...]
    layers: tuple[BindingV2, ...]
    events: tuple[EventV2, ...]
    layout: LayoutV2
    presentation: PresentationV2


def build_view(
    daily: tuple[DailyPerformance, ...], replay: FuturesRollReplay, *, drawdown: bool
) -> ViewV2:
    events = [
        EventV2(
            "entry",
            "time",
            replay.entry_execution.trade_date.isoformat(),
            "Entry",
            (
                Detail("Contract", replay.entry_execution.contract_code),
                Detail("Profile", replay.strategy_profile),
                Detail("Ideal Close", str(replay.entry_execution.price)),
            ),
        )
    ]
    events.extend(
        EventV2(
            f"roll-{i}",
            "time",
            roll.trade_date.isoformat(),
            "Roll",
            (
                Detail("Old contract", roll.old_contract_code),
                Detail("New contract", roll.new_contract_code),
                Detail("Old Close", str(roll.old_close)),
                Detail("New Close", str(roll.new_close)),
            ),
        )
        for i, roll in enumerate(replay.rolls)
    )
    events.append(
        EventV2(
            "exit",
            "time",
            replay.exit_execution.trade_date.isoformat(),
            "Exit",
            (
                Detail("Contract", replay.exit_execution.contract_code),
                Detail("Ideal Close", str(replay.exit_execution.price)),
            ),
        )
    )
    fields = (
        ("drawdown", "benchmark_drawdown")
        if drawdown
        else ("cumulative_return", "benchmark_cumulative_return")
    )
    view = ViewV2(
        2,
        (AxisV2("time", "x", DateCoordinate()), AxisV2("ratio", "y", NumberCoordinate())),
        tuple(
            BindingV2(
                identity,
                label,
                LineV2(
                    "line",
                    2,
                    DateCoordinate(),
                    NumberCoordinate(),
                    tuple(
                        DateMark(row.trade_date.isoformat(), getattr(row, field), "series")
                        for row in daily
                    ),
                ),
                "time",
                "ratio",
            )
            for identity, label, field in zip(
                ("strategy", "benchmark"), ("Strategy", "Benchmark"), fields, strict=True
            )
        ),
        tuple(events),
        LayoutV2("Drawdown" if drawdown else "Cumulative returns"),
        PresentationV2(),
    )
    validate_view_v2(view)
    return view


def validate_view_v2(view: ViewV2) -> None:
    """Validate exact V2 shapes/references/order; never sort or coerce content."""

    def fail() -> Any:
        raise FuturesRollError("invalid_result", "invalid_visualization_v2")

    def obj(value: Any, names: str) -> Any:
        if not isinstance(value, dict) or set(value) != set(names.split()):
            fail()
        return value

    def text(value: Any, empty: bool = False) -> None:
        if type(value) is not str or (not empty and not value):
            fail()

    def day(value: Any) -> None:
        text(value)
        try:
            if date.fromisoformat(value).isoformat() != value:
                fail()
        except ValueError:
            fail()

    def coordinate(value: Any, kind: str) -> Any:
        obj(value, "kind unit")
        if value["kind"] != kind or (kind == "date" and value["unit"] != "date"):
            fail()
        text(value["unit"])
        return value

    def details(values: Any) -> None:
        if not isinstance(values, tuple):
            fail()
        for value in values:
            obj(value, "label value")
            text(value["label"])
            text(value["value"], True)

    if not isinstance(view, ViewV2):
        fail()
    v = asdict(view)
    obj(v, "version axes layers events layout presentation")
    if type(v["version"]) is not int or v["version"] != 2:
        fail()
    text(obj(v["layout"], "title")["title"], True)
    controls = obj(v["presentation"], "show_legend zoom pan reset")
    if any(type(value) is not bool for value in controls.values()):
        fail()
    axes: dict[str, Any] = {}
    if any(not isinstance(v[key], tuple) for key in ("axes", "layers", "events")):
        fail()
    for a in v["axes"]:
        obj(a, "id orientation coordinate")
        text(a["id"])
        if a["id"] in axes or a["orientation"] not in ("x", "y"):
            fail()
        coordinate(a["coordinate"], "date" if a["orientation"] == "x" else "number")
        axes[a["id"]] = a
    if sum(a["orientation"] == "x" for a in axes.values()) > 1:
        fail()

    def reference(identity: Any, orientation: str) -> Any:
        text(identity)
        if identity not in axes or axes[identity]["orientation"] != orientation:
            fail()
        return axes[identity]["coordinate"]

    ids: set[str] = set()
    for b in v["layers"]:
        obj(b, "id label layer x_axis y_axis")
        text(b["id"])
        text(b["label"])
        if b["id"] in ids:
            fail()
        ids.add(b["id"])
        line = obj(b["layer"], "type version x y data")
        if line["type"] != "line" or type(line["version"]) is not int or line["version"] != 2:
            fail()
        for orientation in ("x", "y"):
            c = coordinate(line[orientation], "date" if orientation == "x" else "number")
            if reference(b[f"{orientation}_axis"], orientation) != c:
                fail()
        previous = ""
        segment = None
        seen: set[str] = set()
        if not isinstance(line["data"], tuple):
            fail()
        for m in line["data"]:
            obj(m, "x y segment_id details")
            day(m["x"])
            if m["x"] <= previous:
                fail()
            previous = m["x"]
            if m["y"] is not None:
                try:
                    if type(m["y"]) not in (int, float) or not isfinite(m["y"]):
                        fail()
                except OverflowError:
                    fail()
            text(m["segment_id"])
            if segment != m["segment_id"]:
                if m["segment_id"] in seen:
                    fail()
                segment = m["segment_id"]
                seen.add(segment)
            details(m["details"])
    ids = set()
    for e in v["events"]:
        obj(e, "id x_axis x label details")
        text(e["id"])
        text(e["label"])
        day(e["x"])
        reference(e["x_axis"], "x")
        if e["id"] in ids:
            fail()
        ids.add(e["id"])
        details(e["details"])
