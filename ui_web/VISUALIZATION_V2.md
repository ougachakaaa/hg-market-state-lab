# Visualization V2 date-series contract

This narrow, domain-neutral contract specializes the ownership and coordinate
rules of the [Visualization entry](VISUALIZATION.md). It is the canonical owner
of V2 date-series Layers and Views, not a Plotly schema. Producers conform without
importing `ui_web`; frontend implementation stays under
[presentation architecture](presentation-architecture.md). V1 shapes, validators,
rendering semantics and delivery permissions remain unchanged.

Status: R01-A WP0 defines the contract; WP1 implements and independently verifies
it with fixed artificial data. No renderer, HTTP support or publication admission
is implied by this document's existence.

## Exact semantic shapes

All fields below are required and objects admit exactly those fields. IDs, labels,
units and segment IDs are nonempty strings. `title` and Detail `value` may be empty.
Lists preserve supplied order. No extra fields, implicit defaults or coercion.

```text
DateCoordinate = {kind: "date", unit: "date"}
NumberCoordinate = {kind: "number", unit: nonempty string}
Detail = {label: nonempty string, value: string}

LineV2 = {type: "line", version: 2, x: DateCoordinate, y: NumberCoordinate,
          data: [DateMark, ...]}
DateMark = {x: date, y: finite number | null, segment_id: string,
            details: [Detail, ...]}

ViewV2 = {version: 2, axes: [AxisV2, ...], layers: [BindingV2, ...],
          events: [EventV2, ...], layout: {title: string},
          presentation: {show_legend: boolean,
                         zoom: boolean, pan: boolean, reset: boolean}}
AxisV2 = {id: string, orientation: "x" | "y",
          coordinate: DateCoordinate | NumberCoordinate}
BindingV2 = {id: string, label: string, layer: LineV2,
             x_axis: axis_id, y_axis: axis_id}
EventV2 = {id: string, x_axis: axis_id, x: date,
           label: string, details: [Detail, ...]}
```

`date` is a valid canonical `YYYY-MM-DD` calendar date, years 0001–9999, not a
timestamp or locale string. Numbers follow V1 finite JSON-number and exact-unit
rules, including bool rejection. Null is permitted only as DateMark.y; it is not
a numeric zero, NaN, omitted field or unitless marker. Details are plain supplied
text, not an arbitrary metadata object, executable template or HTML fragment.

V2 supports only date→number LineV2. Other V1 Layer types remain in V1 Views;
there is no implicit upgrade, mixed-version Layer composition or reserved V2 mark.
Future extensions need explicit versioned admission.

## Validation and composition

Axis IDs and Binding IDs are independently unique within a View; Event IDs are
unique within the event list. There is at most one x axis, with DateCoordinate;
y axes use NumberCoordinate. Each Binding references existing axes of the correct
orientation with exactly matching coordinate kinds and units. Events reference
that existing date x axis, independent of any Layer's points. Different numeric
units require different y axes, never inferred conversion or normalization.
Binding order is rendering and legend order; Event order is annotation order.

Each Line's x values are strictly increasing and unique, including null marks.
The validator never sorts, repairs or drops marks. Segment IDs form contiguous
blocks within a Line: once an ID is left, it cannot recur later in that Line.
IDs are local to their Binding; equality across Bindings does not connect data.
Dates in different Bindings need not coincide. Event dates need not have a point.

Empty data, details, events and an empty View are legal. An empty View may have
empty axes/layers/events; references still require existing valid axes. All-null
Lines are legal missing-data content, not an invented numerical series. Unknown
versions/types, bad references, duplicate identities, noncanonical dates,
non-finite values and wrong/extra fields fail before rendering. Error diagnostics
identify the failing field/element; no partial best-effort rendering.

## Lines, details and events

Connect two adjacent supplied marks only when both have finite y and the same
segment_id. Never connect across null, across segments or across Bindings. Each
finite mark must remain individually inspectable; render a visible point for a
singleton finite segment. Null marks have no invented y marker and split lines;
their date, Binding label and details remain inspectable through a generic
missing-value readout. Do not interpolate, resample, infer omissions from date
distance or automatically insert closed-day/weekend gaps.

A Binding is one logical series and produces one legend entry even when it has
several rendered segments. Legend visibility applies to all its segments/points.
With show_legend=false no entries are shown. Tooltip content identifies Binding
label, supplied date/value and unit, then its ordered Detail labels/values;
null is described as no value, never zero. Text is escaped/literal. Retain
coordinates unchanged; explicit numeric unit formatting follows the Visualization
entry, while business-specific detail adaptation belongs to the caller. Duplicate
Detail labels are legal ordered text, not map keys.

An Event renders a vertical date-axis annotation across the plot with its label
and inspectable ordered details. Multiple events may share a date and must all
remain inspectable in supplied order; do not merge or discard them. Events supply
no numerical y coordinate and neither modify line segments nor trigger business
logic. No business-specific fields or meanings enter this schema.

## Interaction and initial view

The initial view fits all supplied dated marks/events and finite values, preserving
natural date spacing. All-null/empty content has an explicit no-numeric-data
presentation; it does not plot zeros. Visual padding is a renderer concern and
does not become new data. Multiple y axes retain their distinct declared units.

When zoom=true expose box/wheel zoom; when pan=true expose selectable drag pan;
when reset=true expose reset of all axes to the initial full-data view. Initial
drag mode is zoom if enabled, otherwise pan if enabled, otherwise disabled.
False disables that interaction's control/gesture. Reset changes the viewport,
not data, legend selection, events or Details. Zoom/pan may change only viewport;
no acquisition, numerical recomputation, aggregation, smoothing or mutation.

## Fixed WP1 acceptance fixture

The following is a complete non-market fixture. It requires neither Research nor
a backend, publication store, credentials, calendar service or HTTP schema:

```json
{
  "version": 2,
  "axes": [
    {"id": "time", "orientation": "x", "coordinate": {"kind": "date", "unit": "date"}},
    {"id": "value", "orientation": "y", "coordinate": {"kind": "number", "unit": "count"}}
  ],
  "layers": [
    {"id": "a", "label": "Series A", "x_axis": "time", "y_axis": "value",
     "layer": {"type": "line", "version": 2,
       "x": {"kind": "date", "unit": "date"}, "y": {"kind": "number", "unit": "count"},
       "data": [
         {"x": "2026-01-02", "y": 1, "segment_id": "a1", "details": [{"label": "Note", "value": "<b>literal text</b>"}]},
         {"x": "2026-01-05", "y": 2, "segment_id": "a2", "details": []},
         {"x": "2026-01-06", "y": null, "segment_id": "a2", "details": [{"label": "Reason", "value": "Not supplied"}]},
         {"x": "2026-01-07", "y": 3, "segment_id": "a3", "details": []}
       ]}},
    {"id": "b", "label": "Series B", "x_axis": "time", "y_axis": "value",
     "layer": {"type": "line", "version": 2,
       "x": {"kind": "date", "unit": "date"}, "y": {"kind": "number", "unit": "count"},
       "data": [
         {"x": "2026-01-02", "y": 4, "segment_id": "b1", "details": []},
         {"x": "2026-01-05", "y": 5, "segment_id": "b1", "details": []}
       ]}}
  ],
  "events": [{"id": "e1", "x_axis": "time", "x": "2026-01-05", "label": "Boundary", "details": []}],
  "layout": {"title": "Artificial date-series fixture"},
  "presentation": {"show_legend": true, "zoom": true, "pan": true, "reset": true}
}
```

Expect two legend entries, no connecting edges in A, one edge in B across the
date interval, three visible finite A points, one missing-value entry and one
event. Test ordered literal details, same-date events, an event-only date,
different series dates, empty/all-null content, axes/units, no input mutation,
interaction enable/disable and reset after zoom/pan. Invalid fixtures cover every
strict shape/reference/order/version boundary, including a repeated noncontiguous
segment ID. Existing V1 tests/fixtures must retain their behavior and reject V2
fields on V1 marks. Distinguish pure validation/projection tests from actual
renderer interaction verification; WP1 needs both and records their results.

WP1 implementation belongs in the existing `ui_web/src/shared/visualization/`
boundary, extending explicit version dispatch without financial or feature imports.
No CDN/report packager, frontend feature, generated OpenAPI/TypeScript artifact or
WP2–WP5 implementation is needed for its independent acceptance.

## Optional frontend date mapping

Natural date spacing remains the default. A caller may explicitly provide an
ordered unique date domain for ordinal presentation. Every domain date occupies
a position, including dates without finite marks. Every mark and event must
belong to that domain or rendering fails. Marks, shapes and annotations share
the mapping; hover and readouts retain real dates. Labels adapt to the visible
window with bounded density. Changing mapping resets the horizontal viewport
and retains legend selection; Reset restores the full domain. Numeric units and
feature detail adapters follow the Visualization entry's presentation rules.
These frontend options do not change the serialized contract.
