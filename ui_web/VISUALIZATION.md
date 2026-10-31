# Visualization layer contract authority

This is the repository's canonical, domain-neutral cross-language semantic contract for
Visualization, navigated from [repository architecture](../ARCHITECTURE.md). Visualization
is initially a logical capability, not a top-level module or a Python dependency on
`ui_web`. This document is technology-neutral authority, not an importable package.
Frontend implementation belongs to [presentation architecture](presentation-architecture.md);
transport serialization belongs to ui_http. Producers may conform to this contract without
importing any UI code. No schema in Python, OpenAPI, or TypeScript is a competing owner.

## Layer data contract V1

A Layer is an ordered collection of marks of one declared type, its version, explicit
coordinate descriptors and data. V1's JSON-compatible semantic shape is:

```text
Layer = {type, version: 1, x: Coordinate, y: Coordinate, data: [Mark, ...]}
Coordinate = {kind: "number" | "date", unit: nonempty string}
```

`type` is one of the types below. `x` and `y` describe the coordinate values used by
the corresponding mark fields. `date` is a valid ISO 8601 calendar date in canonical
`YYYY-MM-DD` form; `number` is a finite JSON number. A coordinate's unit is an explicit,
case-sensitive producer-defined string; equality is exact, never inferred from a label
or converted. A date coordinate uses unit `date`; numeric units must name their meaning
(e.g. `decimal_ratio`, `count`), and must not be silently rescaled. All objects have
exactly the fields listed; no missing fields, nulls, non-finite values or extra fields
are accepted. Empty data is valid and expresses no marks. Data order is retained; a
renderer must not sort or interpolate missing values. Distinct Layer versions require
explicit support; unknown types or versions fail validation, never guessed or coerced.

| type | Mark fields | Additional validation |
| --- | --- | --- |
| `line` | `{x, y}` | coordinates conform to x and y |
| `bar` | `{x, y}` | coordinates conform to x and y |
| `point` | `{x, y}` | coordinates conform to x and y |
| `segment` | `{x1, y1, x2, y2}` | endpoints conform to their corresponding coordinate |
| `candlestick` | `{x, open, high, low, close}` | x conforms to x; all prices conform to numeric y; `low <= open, close <= high` and `low <= high` |
| `area` | `{x, y0, y1}` | reserved extension; y is numeric and both values conform to y |

Each row is the V1 public contract even where no renderer exists. `area` is reserved:
consumers must explicitly advertise support before accepting it for rendering. A valid
contract does not promise implementation of any renderer. Validation rejects invalid
inputs before publication or rendering and reports failure rather than dropping marks.
Layer identity for composition is supplied by the View binding, not inferred from data.
No Layer computes a statistic, discovers a business relationship or knows its producer.

## View composition and presentation

A V1 ChartView has the following JSON-compatible semantic shape; all fields are required,
objects have exactly the listed fields, IDs are nonempty strings, and lists retain order:

```text
View = {version: 1, axes: [Axis, ...], layers: [Binding, ...],
        layout: {title: string}, presentation: {show_legend: boolean}}
Axis = {id, orientation: "x" | "y", coordinate: Coordinate}
Binding = {id, layer: Layer, x_axis: axis_id, y_axis: axis_id}
```

The title may be empty; `show_legend` explicitly controls legend display. Axis IDs and
binding IDs are each unique within a View. A binding is valid only when
both referenced axes exist, have the correct orientation, and have the same kind and
exact unit as the corresponding Layer coordinate. Layer order is rendering order. An
empty View is valid. Unknown versions, duplicate IDs or incompatible bindings fail
validation. No implicit axis selection, unit conversion or normalization is permitted.
Further presentation controls may control visibility, labels, colors, viewport and interaction
but must not modify data, calculate business values or infer mappings. Additional public
layout or style fields require a new explicitly validated contract version; this authority does not define a chart programming language.

A ChartTemplate is an optional reusable View composition definition. It may specify
explicit bindings, layout and presentation choices for supplied Layers; it cannot
calculate, acquire data, infer relationships, or be required for a ChartView to work.
No plugin runtime, universal registry, calculation DSL or generic chart DSL is authorized.

## Adaptation and delivery

The producer or an explicitly authorized producer-aware publication boundary maps its
results into valid Layer data, selecting coordinates, units and ordering using producer
semantics. It preserves source identity, coverage and limitations outside the generic
Layer as appropriate. Visualization only validates and presents those data; it never imports
or understands Research, Statistics, Study, PIP or financial models. Research's initial
boundary is [PublishedResearchResult](../market_research/PUBLICATION.md). Statistics stays
numerical and UI-independent. HTTP projects the canonical Layer meaning without introducing
an alternative schema; OpenAPI generates consumer TypeScript through the
[feedback loop](contracts.md). Feature-specific presentation stays in the feature;
only domain-neutral mechanisms may be shared.

Implementation order: WP1 core contracts/renderer; WP2 Research publication; WP3 read-only
HTTP delivery; WP4 Research Explorer; WP5 authorized Workbench integration and real E2E;
WP6 multi-layer/time-series extension. Each WP must preserve these boundaries and publish
its actual runtime readiness separately. This authority alone implements none of them.
