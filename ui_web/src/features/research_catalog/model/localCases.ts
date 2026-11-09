// Presentation summaries trace to the case authorities named in this slice's ARCHITECTURE.md.
// These are local use instructions, never Capability Publication or HTTP response DTOs.
export const localCases = [
  {
    id: 'price_segmentation_v1',
    name: 'Price Segmentation',
    readiness: 'Local / Python only',
    planned: null,
    purpose: 'Observe the shape of one complete historical Index Daily Close series using important points and adjacent price segments.',
    scope: 'One explicit canonical index code, inclusive date window and positive epsilon; Close prices with natural-log fitting and trading-session time.',
    output: 'Important points, adjacent segments, diagnostics and retained input evidence.',
    access: 'Python: market_research.descriptive.cases.price_segmentation.observe_price_segments(SegmentationRequest(...))',
    note: 'May acquire source facts. No Capability Publication, HTTP endpoint or online execution UI.',
  },
  {
    id: 'futures_basis_v1',
    name: 'Futures Basis Research (R01-A)',
    readiness: 'Online Web Consumer · Independent offline report generation',
    planned: 'Online execution available; Provider / Cache readiness unverified',
    purpose: 'Describe historical same-day futures basis, relative tenor structure, distributions and persistence.',
    scope: 'One explicit IM, IC, IF or IH product and inclusive date window. Online execution uses the server-owned standard profile; offline generation requires explicit statistical parameters.',
    output: 'Online Run status and interactive report; independently generated self-contained offline HTML with adjacent evidence.',
    access: 'From repository root: poetry run python market_research/scripts/futures_basis_report.py with explicit product, dates, statistical parameters and a new output directory. Open the generated report.html locally.',
    note: 'Open Futures Basis Research to submit an online Run. Offline reports remain independently generated locally. Online execution availability does not establish actual Provider / Cache readiness.',
  },
] as const
