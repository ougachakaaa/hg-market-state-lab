# R01-A offline reader

Specializes [ui_web](../../../ARCHITECTURE.md), its presentation/UI-system rules,
and the [Research delivery](../../../../market_research/descriptive/cases/futures_basis/DELIVERY.md).
This standalone entry consumes only producer-written report-data and complete
Visualization Views. It never acquires inputs, executes Research, infers financial
relationships or calculates numerical findings. Local TypeScript reader types
implement the versioned offline evidence contract, not a parallel HTTP contract.

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
