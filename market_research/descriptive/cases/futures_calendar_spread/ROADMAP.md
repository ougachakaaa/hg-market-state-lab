# Calendar Spread delivery scope and limitations

Specializes [the case](ARCHITECTURE.md). L1 Daily Data and Historical Relative Value
are implemented through Python, Statistics, HTTP, Web and the static Demo.
Explicit execution now prepares missing required facts under [Inputs](INPUTS.md)
and [Application](APPLICATION.md); read-only query APIs remain export-only.
Completed implementation and acceptance records are available in Git history.

## Current boundaries

- Six Slot pairs and three metrics share the single [Definition](DEFINITION.md).
  Historical sampling, cutoff and interpretation remain in [Relative Value](RELATIVE_VALUE.md).
- [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md)
  and [Historical HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md)
  preserve distinct read-only and explicit execution permissions; synchronous execution
  uses shared capacity two, without a durable Run or generic scheduler.
- [Demo integration](../../../../ui_web/demo/CALENDAR_SPREAD.md) owns formal HTTP
  capture and shared Presentation. Local delivery does not imply publication.

## Deferred and unverified scope

L2 waiting value, L3 strategy validation, generic Plan/Batch/capability/Publication
admission and a CLI remain outside L1. Metadata is not proven point-in-time;
results describe historical Close relationships, not realized returns or trading advice.
Issue #13's bounded WSL/local-chain acceptance does not establish other deployments,
maximum 3660-date windows, prolonged load or cold-cache concurrent Source behavior.
No latency SLA or universal proxy-timeout suitability is claimed.

## DD-02 Daily enhancement work packages

Status: **IMPLEMENTED — READY_FOR_MERGE**. All four work packages are complete.
The Daily-only reference, Chinese presentation and four local copy/export actions
are reconciled across Research, HTTP, Online and the retained static Demo.

| WP | Delivery and acceptance boundary | State |
| --- | --- | --- |
| WP-00 — Authority Encoding | Daily-only reference/result, additive HTTP, Chinese/export and Demo omission contracts | IMPLEMENTED |
| WP-01 — Underlying Index Close Integration | Public Dataset preparation, immutable evidence, HTTP projection and generated contracts | IMPLEMENTED |
| WP-02 — Chinese Presentation & Export | Chinese controls/table/status, reference display and four local actions | IMPLEMENTED |
| WP-03 — Cross-Layer Acceptance & Reconciliation | Online/Demo/export acceptance, known source-note translation and final authority reconciliation | IMPLEMENTED — READY_FOR_MERGE |

Canonical owners remain [Daily Index Reference](DAILY_INDEX_REFERENCE.md),
[Query Results](QUERY_RESULTS.md#daily-underlying-index-result-dd-02-target),
[Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md#dd-02-daily-index-projection-target),
[Daily Presentation](../../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md#dd-02-chinese-presentation-and-index),
[Daily Export](../../../../ui_web/src/features/futures_calendar_spread/EXPORT.md) and
[Demo compatibility](../../../../ui_web/demo/CALENDAR_SPREAD.md#dd-02-additive-reference-compatibility-target).
The shared [Daily Data export standard](../../../../ui_web/data-copy-export.md)
owns common lifecycle and encoding invariants.

Targeted Python/HTTP and TypeScript/React acceptance verifies reference identity,
legal states, null/zero, GET read-only versus POST conditional Ensure, safe HTTP
projection and intact six-pair results. Historical preparation remains independent
of SSE/Index. Online requires reference presence; the retained Daily Bundle passes
the same formal validator with omission and displays the historical disclosure.
Raw/Context preserve the complete response; CSV retains 29 columns, original values,
order and presence. Local copy/download and stale-result isolation are covered.
All nine Bundle hashes match the Manifest; Bundle, Manifest and Registry bytes
remain identical to the reviewed baseline. No capture or publication occurred.

Real browser layout/Clipboard/download behavior, live external Source acquisition,
Windows and deployment are **NOT VERIFIED** by DD-02 acceptance. Deterministic
DOM and download utility tests do not establish those platform results. Existing
synchronous capacity/cancellation and independent-snapshot limitations remain binding;
no latency, freshness or common-snapshot guarantee is added. Merge readiness does
not constitute deployment or publication acceptance. Completed execution details
and commit evidence remain in Git history.
