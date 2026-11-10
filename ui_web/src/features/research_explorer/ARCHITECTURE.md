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
