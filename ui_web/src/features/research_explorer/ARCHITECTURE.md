# Research Explorer authority

This read-only surface consumes the [Publication HTTP contract](../../../../ui_http/products/research_publication/http-contract.md) and the shared [Visualization contract](../../../VISUALIZATION.md). Research owns publication, results, coverage and provenance; this feature owns navigation and presentation only. It never executes research or computes statistics or coverage.

The user discovers publications in explicitly requested cursor pages, selects a publication to inspect its declared scope and published-order Jobs, and selects an Analysis by its published ID within its Job. Show actual statuses, requests, parameters and available View references, distinguishing declared scope from computed, failed and not-attempted outcomes. The HTTP-redacted context is not a title. Source digest and input fingerprint identify evidence, not market-data authenticity.

A selected Analysis presents its original statistical result and Job coverage/provenance, preserving nulls and zeroes. Quantile probability/value pairs and estimator and IntervalCount boundaries, inclusion flags, counts and frequencies are displayed without recomputation. Published Quantile and categorical IntervalCount ChartViews use the shared renderer; Count and Frequency select their respective published View IDs. Unsupported results or Views are explicit.

List, Manifest, Analysis and View each expose loading, success and failure states; the list distinguishes empty store and empty pages, and missing coverage or views is explicit. Safe transport failures, including integrity, size and capacity failures, remain distinguishable and manually retryable. Detail reads are lazy: only an explicit selection requests its Manifest, Analysis or View; no bulk prefetch or automatic retry. Changing selection or unmounting cancels or invalidates obsolete requests so source identity and visible results remain consistent. The application authentication boundary controls 401 and session isolation.

Explicit result-unit decimal_ratio values and IntervalCount boundaries display as
one-decimal percentages with the shared formatter. Probability, frequency, counts
and coverage retain their own semantics; observation_unit does not assign units
to coverage fields. Histogram labels preserve category identity, order and
inclusion. Raw request and evidence payloads remain unchanged.

This reader renders arbitrary published Views and therefore has no authoritative
trading-session domain for a date View. Following the
[date-axis presentation authority](../../../DATE_AXIS_PRESENTATION.md), it does not
invent a market calendar and exposes no Trading Days default; published date Views keep
the generic natural date spacing.

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../demo/ARCHITECTURE.md) using [validated embedded Examples](../../demo/EXAMPLES.md), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature’s result/visualization semantics and applicable local Copy/Export. Shared presentation remains here, not in parallel Demo pages.

D2-D implements this boundary. `presentation.ts` exposes the feature-owned `ResearchExplorerPresentation`, `AnalysisDetails`, pure generated-contract validators (`validateResearch`, `validateEmbeddedPublication`) and a feature-local `useStaticExplorer` controller. Production `useExplorer` retains the initial list GET, opaque cursor pagination, lazy Manifest/Analysis/View GETs, four independent load states, manual retry, cancellation plus request-token stale isolation, protected Auth and HTTP error mapping; `ResearchExplorerPage` is a thin composition root. The View validator preserves the distinct `invalid_view` failure while requiring both the generated response shape and the shared ChartView contract. Static composition validates the embedded list/pages, Manifests, Analyses and ChartViews plus their cross-record identities, then performs only local pagination and Publication/Analysis/View selection. A missing embedded Manifest, Analysis or ChartView is an explicit missing state, never a fabricated success or HTTP fallback. Static disclosure distinguishes the embedded Example from the online Publication Store and does not treat source metadata as market-source authenticity. [`tests/static/research_explorer/`](../../../tests/static/research_explorer/) is a verification harness using test-only regression data, not an official D3 Example or public Demo entry.

The embedded page set is a contiguous prefix of the online cursor chain: every non-final
page must declare continuation, no embedded page may follow a page whose `next_cursor` is
null, and declared opaque cursor bytes are preserved unchanged. A non-null cursor on the
final embedded page means subsequent online pages are not embedded; it is presented as an
explicit unembedded continuation and never as the online list's last page. Every embedded
ChartView must have a formal View reference in its own Publication Manifest; a published
reference without an embedded View stays an explicit missing detail, while an embedded View
without a published reference rejects the embedded set.

## V2 origin policy reconciliation

[Demo Example authority](../../demo/EXAMPLES.md) owns formal V2 real-market dates and
packaging; [authenticity and rights](../../demo/AUTHENTICITY.md) owns evidence and admission.
This feature owns only their presentation. Static delivery is not a Synthetic source label
or proof of authenticity. Preserve historical V1/test disclosures, use actual real-market
origin for V2, and never promote regression inputs to formal Examples. WP-B implements explicit validated source disclosure through the same Presentation;
[private acceptance](../../demo/WP_B_ACCEPTANCE.md) records integration evidence.
Current engineering verification and release boundaries enter through the
[implementation handoff](../../demo/IMPLEMENTATION.md).
