# R01-A offline reader

Specializes [ui_web](../../../ARCHITECTURE.md), its presentation/UI-system rules,
and the [Research delivery](../../../../market_research/descriptive/cases/futures_basis/DELIVERY.md).
This standalone entry consumes only producer-written report-data and complete
Visualization Views. It never acquires inputs, executes Research, infers financial
relationships or calculates numerical findings. The six-section reader presentation
is shared with the online [Futures Basis Research](../../features/futures_basis_research/ARCHITECTURE.md)
feature; the offline entry keeps only its standalone shell, font/asset packaging and
`file://` entry, and imports the pure reader subpath rather than the app/auth/API.
Local TypeScript reader types implement the versioned producer reader contract used
by both readers, not a parallel HTTP contract; the online HTTP envelope is generated
separately under the [HTTP contract](../../../../ui_http/products/futures_basis_research/http-contract.md).

Ordinary controls/tables use Ant Design and the shared application theme;
generic charts use ChartView. Metric/Slot selection is presentation state only.
All scientific text, status, counts, intervals, comparisons and runs come from
Research. Original failed result payloads remain evidence, never successful charts.
The Node packager builds a separate single-chunk Vite entry and embeds its script,
styles and safely encoded JSON. No fetch, CDN, application/auth import or backend.

The reader embeds a licensed subset font for its fixed Chinese copy, reusing the
shared application theme in its standalone ConfigProvider. Scoped CSS only sets
Plotly SVG font fallback; ordinary UI styling remains theme/Ant Design-owned.
A larger generic plot-frame size leaves space for supplied event annotations.
The offline package remains self-contained and network-free; moving the pure reader
presentation into the sibling feature must not import application/auth/network code
into this entry. WP8 preserves the existing offline tests, build and Chromium
acceptance.

WP8-B implements the shared reader under the feature `report/` subpath. The
offline `Report` is now only the standalone theme/font shell, with explicit
`offline` disclosure mode; online composition uses the application theme.
