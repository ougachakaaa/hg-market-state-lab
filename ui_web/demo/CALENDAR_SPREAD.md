# Calendar Spread L1 Demo integration plan

Status: WP0 planning only; no registered Bundle, Preset, capture, static route or
release requirement is added. Specializes [Demo](ARCHITECTURE.md),
[Bundle](BUNDLES.md), [Build](build/ARCHITECTURE.md) and
[Release Requirements](release/ARCHITECTURE.md).

## Formal sources and future identities

WP7 follows the implemented WP5 HTTP products and WP6 public Presentation:

| Planned Bundle ID | Formal source | Presentation owner |
| --- | --- | --- |
| `calendar_spread_daily` | [Daily formal HTTP 200 Result](../../ui_http/products/futures_calendar_spread/http-contract.md) | `futures_calendar_spread` |
| `calendar_spread_relative_value` | [Research formal HTTP 200 Result](../../ui_http/products/calendar_spread_relative_value/http-contract.md) | `calendar_spread_relative_value` |

Each captures one complete Result with explicit request identity. No direct Python
service, DataLake access, copied financial calculation or fabricated Run envelope
is allowed. The Collector uses normal HTTP authentication, preserves formal values
and outcomes and never repairs cache gaps itself. Choose explicit available
product/date/history Presets during WP7 from actual formal results; WP0 invents no
market data or historical readiness evidence. Actual DTO-based result_contract
identities are fixed only after OpenAPI delivery, not guessed in this document.

## Bundle/build integration

WP7 adds both entries to the single Registry, Presets, Manifest and canonical Bundle
catalog together with actual captures, formal validator dispatch and static
composition. Existing unrelated Bundle bytes need no regeneration. Generation uses
the existing staging/admission/transaction protocol; failed collection preserves
active data. No optional pretend entry may make a missing required Result pass.
Until that coordinated cutover the existing seven-Bundle dataset is unchanged.

Shared Presentation renders the complete captured Results through read-only static
controllers, using hash routes corresponding to the two formal Web pages. No Auth,
business HTTP, query submission, ensure, polling or financial/statistical computation
runs in the browser.
Backend-independent local pair selection/formatting remains permitted.
Keep source disclosure, small/empty-sample explanations, metadata limitations and
investment disclaimers identical in meaning to the formal Presentation.

## Acceptance and release boundary

Verify each new formal Result, request association, envelope, exact bytes/hash,
Manifest membership, invalid/missing Bundle rejection and failed-collection
preservation. Build validates the enlarged dataset offline and must produce an
actual artifact before claiming build readiness. Extend release content requirements
for the actual new captures at WP7; no automatic release occurs. Existing Auth,
artifact integrity, credential safety and truthful disclosure remain in force.
Per the root personal-study decision, do not add distribution-authorization research
or a permission gate. Any later publication follows the existing release Runbook
only when explicitly requested. WP0 runs no build, collection or publication.
