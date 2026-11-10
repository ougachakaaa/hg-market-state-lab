# Visualization layer contract authority

This is the repository's canonical, domain-neutral cross-language semantic contract for
Visualization, navigated from [repository architecture](../ARCHITECTURE.md). Visualization
is initially a logical capability, not a top-level module or a Python dependency on
`ui_web`. This document is technology-neutral authority, not an importable package.
Frontend implementation belongs to [presentation architecture](presentation-architecture.md);
transport serialization belongs to ui_http. Producers may conform to this contract without
importing any UI code. No schema in Python, OpenAPI, or TypeScript is a competing owner.

## Version navigation

The V1 Layer and View contracts below remain unchanged. The independently defined
[V2 date-series extension](VISUALIZATION_V2.md) owns exact date-line, point-detail,
event, segmentation, missing-value and interaction shapes for future implementation.
Version support is explicit; V2 does not authorize extra fields/nulls in V1, imply
current renderer support, or extend a producer's publication/HTTP admission.

## Layer data contract V1

A Layer is an ordered collection of marks of one declared type, its version, explicit
coordinate descriptors and data. V1's JSON-compatible semantic shape is:

```text
Layer = {type, version: 1, x: Coordinate, y: Coordinate, data: [Mark, ...]}
Coordinate = {kind: "number" | "date" | "category", unit: nonempty string}
```

`type` is one of the types below. `x` and `y` describe the coordinate values used by
the corresponding mark fields. `date` is a valid ISO 8601 calendar date in canonical
`YYYY-MM-DD` form; `number` is a finite JSON number; `category` is a nonempty string
whose identity is exact string equality. A category is never parsed as a number or date,
trimmed, case-folded or otherwise normalized. A coordinate's unit is an explicit,
case-sensitive producer-defined string; equality is exact, never inferred from a label
or converted. A date coordinate uses unit `date`, and the generic category descriptor is
`{kind: "category", unit: "category"}`. Numeric units must name their meaning
(e.g. `decimal_ratio`, `count`), and must not be silently rescaled. All objects have
exactly the fields listed; no missing fields, nulls, non-finite values or extra fields
are accepted. Empty data is valid and expresses no marks. Data order is retained; a
renderer must not sort or interpolate missing values. Distinct Layer versions require
explicit support; unknown types or versions fail validation, never guessed or coerced.

| type | Mark fields | Additional validation |
| --- | --- | --- |
| `line` | `{x, y}` | coordinates conform to x and y |
| `bar` | `{x, y}` | coordinates conform to x and y; when x is category, y is number and x values are unique within the Layer |
| `point` | `{x, y}` | coordinates conform to x and y |
| `segment` | `{x1, y1, x2, y2}` | endpoints conform to their corresponding coordinate |
| `candlestick` | `{x, open, high, low, close}` | x conforms to x; all prices conform to numeric y; `low <= open <= high` and `low <= close <= high` |
| `area` | `{x, y0, y1}` | reserved extension; y is numeric and both values conform to y |

Each row is the V1 public contract even where no renderer exists. `area` is reserved:
consumers must explicitly advertise support before accepting it for rendering. A valid
contract does not promise implementation of any renderer. Validation rejects invalid
inputs before publication or rendering and reports failure rather than dropping marks.
Layer identity for composition is supplied by the View binding, not inferred from data.
No Layer computes a statistic, discovers a business relationship or knows its producer.

A categorical bar maps one category to one finite numerical value in its declared y unit.
The renderer preserves supplied values, including zero; it never fills, combines, scales,
normalizes or computes them. Categories need not be numerical intervals. Equal visual
bar widths express categories, not numerical interval widths or density. Numeric-width
histograms are not part of V1; a future range Layer requires its own contract.

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
For each category axis, visit bound Layers in View order, then marks in their supplied
order; within a mark visit that axis's coordinate fields in the order listed in its
Layer row (for example x1 before x2). The axis displays each distinct exact category at
its first occurrence. Later occurrences share that position, including across Layers;
no alphabetical sorting, value parsing or category normalization occurs. This defines
axis positions only: marks are never removed, reordered, merged or deduplicated.
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

The V1 Binding contains inline Layer data, not a reference. A renderer accepts a complete,
validated ChartView and does not resolve publication IDs, storage paths, URLs or artifacts.
Producer-aware readers or authorized delivery projections resolve and validate their own
references before supplying the View. Python and HTTP representations and generated
TypeScript implement this single semantic contract; a Plotly trace is an internal rendering
structure, not another public Layer schema.

## Frontend presentation adapters

Renderer-only options may supply ordinal date positions, axis grid styling,
category display labels and point-detail presentation. They are not serialized
View fields and introduce no financial semantics. Explicit numeric decimal_ratio
coordinates display as one-decimal percentages without negative zero; original
coordinate values remain unchanged. Other units retain their scale. Category
labels never replace identities or reorder marks. Details stay literal by default.
