# Visualization Core V1 / V2

The semantic authority is [VISUALIZATION.md](../../../VISUALIZATION.md). Import
`ChartView` and the `ChartViewContract` type from this directory's `index.ts`, then
render `<ChartView view={view} />` inside a sized container. The complete View is supplied
by the caller; validation and unsupported-renderer errors propagate to its error boundary.
`validateLayer`, `validateChartView`, and `chartViewToPlotly` are also available for
validation and inspection without mounting React. None fetches data.

Line and point render for all coordinate kinds. Bar renders with categorical x and
numeric y; other contract-valid bars and segment, candlestick and area are explicitly
unsupported for rendering. The runtime validates all six V1 shapes before projecting.

Business-neutral examples live in `fixtures.ts`. Run
`VITE_VISUALIZATION_FIXTURES=1 npx vitest run src/shared/visualization/visualization.test.ts --disableConsoleIntercept`
from `ui_web` to print their Plotly projections and the invalid View's error, alongside
the focused tests. No backend is needed.

## V2 date series

The sole V2 semantic owner is [VISUALIZATION_V2.md](../../../VISUALIZATION_V2.md).
`ViewV2` supplies complete inline date-series data, ordered point Details, nulls,
contiguous segment IDs, independent date Events and explicit interaction controls.
`ChartView` and `chartViewToPlotly` dispatch on the explicit version; the latter
returns V2 Plotly `data`, `layout` **and `config`**, which must be supplied together
when rendering directly. Neither entry fetches data or computes business values.
Use `ChartView` for the complete V2 renderer: it also supplies the missing/event
readouts and guards Plotly's native shortcuts, which figure projection alone
cannot install.

`validateVisualizationView` / `validateVisualizationLayer` accept explicitly supported
versions. `validateViewV2` / `validateLineV2` are V2-only. The existing
`ChartViewContract`, `Layer`, `validateChartView` and `validateLayer` remain V1-only;
adding the renderer does not admit V2 into Publication or HTTP consumers.

Each Binding has one grouped legend entry and a shared color across segment traces.
Finite singleton points are visible. Date hover includes coincident series points;
Details retain order and custom Plotly text is escaped. The **Missing values**
disclosures expose Binding/date/reason without numeric markers. **Date events**
disclosures expose each Event's ID/date/label and ordered Details, including events
on the same date or a date with no data point. Empty/all-null content explicitly
reports **No numeric data**. A null-only internal trace retains empty-series legend
identity without introducing a plotted point.

Zoom supports horizontal-only box zoom (drag horizontally), ordinary box zoom and
wheel zoom. Pan is selectable in the modebar. Reset restores all initial axis ranges
without changing legend selection. Disabled controls also disable related wheel,
modifier-key, axis-end scaling and double-click shortcuts. Numeric y axes remain
independently scalable when zoom is enabled. Date viewport strings avoid local-time
interpretation of numeric Plotly ranges. No range slider is included.

## Verification and development harness

From `ui_web`:

```bash
npx vitest run src/shared/visualization
npm run build
npm run lint
npm run test:visualization-browser
```

`npm run dev` serves `/visualization-harness.html`, a standalone development/test
entry with the unchanged fixed acceptance fixture, derived generic edge cases and
V1 regressions. It is outside application navigation and needs no backend.
The browser script starts its own Vite server on an available loopback port and
uses real Chromium/Plotly DOM rendering, mouse hover, drag, wheel and modebar
interaction, plus viewport and no-data-request assertions. It checks Asia/Shanghai
explicitly. It does not substitute mocked Plotly or JSON inspection for rendering.

Install Chromium with `npx playwright install chromium` and provision its OS libraries
if needed. `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` optionally selects an executable;
`LD_LIBRARY_PATH` can supply user-local runtime libraries when system installation
is unavailable. Screenshots and `acceptance.json` (including failures) default to
`node_modules/.cache/visualization-browser/`, outside Git; override with
`WP1_BROWSER_EVIDENCE_DIR`.

WP1 verification on 2026-11-06: 94 focused contract/projection/React/V1 tests passed;
TypeScript/Vite build and Web lint passed. Real Chromium 156.0.8078.4 acceptance
passed for the fixed fixture, literal hover/details, null readout, date events,
legend grouping, multi-axis interaction, disabled interactions, empty/all-null
content and V1 line/point/bar rendering. Vite reports a non-blocking large-bundle
build warning; bundling/layout redesign and offline packaging are outside WP1.

`ChartView` accepts optional `minPlotHeight` (default 320 CSS pixels) for the V2
plot frame, independently of missing/event disclosure height. This is frontend
sizing only, not a new Visualization semantic field. The offline report uses a
larger frame so same-date event annotations leave room for all four legends.
