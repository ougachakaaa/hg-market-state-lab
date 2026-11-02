# Visualization Core V1

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
