# Futures Basis projection and offline delivery

This specializes the [case](ARCHITECTURE.md). Research owns business projection
from retained observations/findings; rendering belongs to `ui_web` under
[Visualization V1](../../../../ui_web/VISUALIZATION.md) and the independent
[V2 date-series contract](../../../../ui_web/VISUALIZATION_V2.md).
No Research import of `ui_web`, HTTP DTO or Plotly is authorized.

## Projection

Emit one V2 View per product/metric, with a Binding per Slot in M0/M1/Q1/Q2 order,
date x and the metric's unchanged numerical unit y. Keep raw and annualized ratios
in explicitly named separate Views. Binding IDs and segment IDs are deterministic
within the case result; they are opaque rendering identities, not contract codes.

Each Slot's candidate date appears once. Eligible values become the supplied y;
Unavailable/Excluded/Not Applicable outcomes become null y with explanatory point
details. Use [Research segment boundaries](OBSERVATION.md#time-series-and-transitions)
unchanged. A null point's generic segment ID does not authorize a line to its
neighbors. Every valid point retains an outside-Layer association to its Slot-day,
Contract-day and input evidence. No data reduction, smoothing or interpolation.

Populate ordered generic text details with the date, Slot, real contract (when
resolved), selected metric/state or outcome reason, actual prices, DTE and source
association label. These are producer-supplied labels/values, not financial fields
in the generic Layer schema. Full provenance remains in the evidence bundle;
never pass private paths, secrets or raw exception text into tooltip content.
Use round-trip numeric text for evidence-oriented details; coordinate values stay
unchanged. Percent formatting, if displayed, must label its presentation scale
while retaining original decimal values and units in the evidence.

Project each contract Transition as a generic date-axis event at its new mapping
date, with producer-written Slot/old/new contract text. Include events even if
that date's metric is unavailable. Visualization renders the supplied text and
boundaries without financial interpretation. Source association maps event IDs
back to the retained Transition records.

Distribution charts may use valid V1 categorical bars for the original Statistics
counts/frequencies, retaining exact edges/inclusion rules and both outside bins.
They cannot recompute statistics in browser code. Comparison panels identify
their common-date populations; persistence panels distinguish complete runs from
censored fragments. Tables may present numerical results without inventing a
generic Layer for every output.

## Offline report boundary

WP5 produces a self-contained interactive static HTML report plus adjacent
machine-readable evidence and a human-readable reproduction guide. Research
produces findings, text, associations and validated generic Views. `ui_web` owns
HTML/Plotly rendering and asset packaging through an offline entry separate from
the authenticated application and Research Explorer. The supplied report data is
local producer output, not a second HTTP schema or live API. This narrowly scoped
offline path specializes online consumption; it does not bypass an HTTP access gate.

The report opens without a server or external network/CDN dependency, retains
Zoom/Pan/Reset, events and point details, and discloses requested versus observed
dates, exact case/formula versions, price convention, units, populations, quality
and interpretation limits. It neither acquires facts nor recomputes research.
Data/HTML bundling must safely escape producer text; details are plain text.

The evidence package retains the exact explicit requests, final inputs/proofs and
canonical input bytes/fingerprint, observations and transitions, analysis requests,
original Statistics specs/results and ordered bindings, chart Views and source
associations, definition versions, code revision, runtime/dependency versions and
reproduction instructions. Include a versioned manifest of file identities and
SHA-256 digests; retained evidence must suffice to rerun construction/statistics
without mutable upstream caches. HTML alone or hashes without their payloads do
not meet this requirement. Exact packaging implementation belongs to WP5 and
must preserve these obligations without adding a publication/storage framework.

## Compatibility and acceptance

[Publication V1](../../../PUBLICATION_STORAGE.md) admits only Trailing Return
BatchResult evidence; [publication HTTP V1](../../../../ui_http/products/research_publication/http-contract.md)
delivers V1 Views. Neither accepts this case or V2 by implication. This report is
not a PublishedResearchResult, Workbench Run artifact or new capability/HTTP endpoint.
Future integration requires explicit versioned admission and safe transport rules;
it is optional beyond this delivery, not a WP0/WP5 blocker.

WP5 verifies real IM evidence linkage and offline reconstruction, all five research
outputs, no recomputation on rendering, honest partial/empty/failed analysis status,
complete local assets, event/segment/tooltip fidelity and opening without backend
or network. Acquisition failure cannot be replaced by a synthetic real-market report.
Actual inputs and reports remain disposable runtime output outside Git under the
[repository runtime invariant](../../../../ARCHITECTURE.md#naming-and-transition-authority).
