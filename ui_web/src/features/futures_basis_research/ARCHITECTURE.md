# Futures Basis Research frontend authority

This is the implemented WP8-B online Web feature. It specializes the
[ui_web architecture](../../../ARCHITECTURE.md) and
[presentation architecture](../../../presentation-architecture.md), consumes the
[Online Futures Basis Research HTTP contract](../../../../ui_http/products/futures_basis_research/http-contract.md)
through generated types, and renders the R01-A reader owned semantically by
[Research](../../../../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md).
It owns input interaction, presentation state, polling and user-visible empty/error
presentation only. It never acquires market facts, executes Research or recomputes
Basis, Slot, DTE, statistics, coverage or run length. WP6 defines this authoritative
slice; WP8 implements it and the offline reader regression.

## Application composition

The surface is discovered from the authenticated Research workspace
as `Futures Basis Research`, alongside Research Explorer. Research remains the default entry. Adding this surface
must not replace, hide or break an existing surface. It is a sibling bounded
context: it does not read or reinterpret another feature's DTO, state, chart or
result.

Dependency direction:

```text
Research online semantic contract
        ↓
ui_http Online Futures Basis Research contract / OpenAPI
        ↓
generated client types
        ↓
feature API adaptation and validation
        ↓
feature hooks
        ↓
presentation and shared W1 reader
```

The application authentication boundary owns 401 and stale-request isolation. The
feature does not parse, store or refresh tokens; it uses relative same-origin
requests through the existing protected-request mechanism. 401 returns the
application to its anonymous gate and must discard any displayed run/report.

## Query controls

```text
Futures Basis Research
├── Product selector: IM / IC / IF / IH
├── Start date (inclusive)
├── End date (inclusive)
└── Generate Research
```

- The product options come from the published generated enum; the UI does not
  maintain a second product-to-underlying mapping.
- End date initially uses today in Asia/Shanghai; product and start date require
  explicit selection. The default is not a latest-available-date claim. Generate
  requires complete parameters and a matching successful Preflight result.
- Date controls produce date-only `YYYY-MM-DD` values. Browser local time must not
  be treated as the business authority; the server applies the Asia/Shanghai
  future-date rule and the inclusive window bound.
- Client-side format/order hints are presentation only. The server remains the
  authority for product, future date, ordering and the 1,096-day maximum.
- No statistical parameters, strategy inputs, backtest controls, multi-product
  selection or client method selection are exposed.
- Once a run is submitted, the query form is no longer the identity of that run.
  The execution state and report always use the run's immutable request, even if
  the user edits the form for a future run.

## Execution state and polling

The feature owns these presentation states:

```text
IDLE → SUBMITTING → PENDING → RUNNING → REPORT_LOADING → COMPLETED
                                      ↘ FAILED / INTERRUPTED   ↘ REPORT_ERROR
         ↘ BUSY / FORM_ERROR / STATUS_ERROR
```

- `SUBMITTING`: POST in flight; Generate disabled.
- `PENDING`: accepted run, no result yet; show run ID, request identity and created
  time; do not show a report.
- `RUNNING`: same, with an active indicator. No percentage or invented stage list.
- `COMPLETED`: fetch the report; `partial` is a completed scientific result and is
  presented as such, never as an execution failure.
- `FAILED` / `INTERRUPTED`: show the safe failure stage/category/dependency and a
  manual Retry. Retry loads the failed run's immutable request into the query and checks it;
  a subsequent explicit Generate creates a new run. It
  does not reuse the old run ID or silently resubmit.
- `BUSY`: a 409 means another run is active. Show a clear retry-later message; do
  not auto-loop the POST and do not create a local run.
- `FORM_ERROR`: 400 invalid request; show the safe field message and preserve the
  form. Do not clear prior terminal results merely because a new submission failed.
- `STATUS_ERROR`: status polling failed; keep the run ID and offer manual status
  retry. Do not claim completion or recreate the run.
- `REPORT_ERROR`: a completed run's report read failed; offer report retry only, not
  a new execution.
- Unknown/foreign/missing run (`404`): clear the run identity and show one
  indistinguishable inaccessible/not-found message. Do not enumerate.

Polling rules:

- Poll GET run every 1.5 seconds while `PENDING` or `RUNNING`; allow only one
  status request in flight.
- Stop on any terminal state. Fetch GET report once on `COMPLETED`.
- Abort in-flight requests on unmount, feature switch or replacement of the active
  run; ignore all stale responses. A late 401 still closes the application gate
  through the shared auth boundary.
- No background polling after the feature unmounts and no automatic POST retry.
  A lost POST response is an unknown outcome; the UI must not claim success or
  silently create another run.
- No run list/history is provided. The active run is restored after a browser
  refresh from the page URL query `run_id=<opaque>`. On mount, a present ID is read
  once; the feature then resumes status polling or loads the report. No report or
  financial data is stored in local/session storage.
- Switching away from and back to the feature does not recompute anything; the URL
  identity and server state are the source of truth.

## Research result and shared W1 reader

The result region contains exactly the existing six W1 reader sections:

```text
Overview
Historical Basis
Distributions
Term Structure
Discount Persistence
Evidence and Limitations
```

These are not reimplemented in this feature. The R01-A reader presentation is
shared with the offline report: the feature owns a pure `report/` presentation
module, extracted from the existing offline reader in WP8, and the offline entry
composes the same module. The online page supplies an online evidence/disclosure
mode; the financial content, section identities and chart semantics are unchanged.

The reader preserves:

- ChartView Zoom / Pan / Reset, M0/M1/Q1/Q2 bindings, contract transition events
  and point hover details;
- the distinction between valid, unavailable, excluded and not-applicable samples,
  including null points and missing-value details;
- producer-supplied distribution counts, frequencies, bins, underflow/overflow and
  exact inclusion labels;
- common-date comparison populations, dropped-date outcomes and Slot pairs;
- separate complete and censored discount runs, with observed session counts as
  lower bounds.

Metric and Slot selection is presentation state only. It never changes the HTTP
request, triggers statistics, recomputes a distribution or invents a chart point.
All numbers, text, events, intervals, comparisons and limitations come from the
producer reader payload. No financial interpretation may be added in React.

The page must clearly separate the requested window (from the run request) from
the actual observed coverage (from candidate dates and coverage in the report).
An empty candidate set is displayed as empty, never as the requested range. A
`complete` report with `no_eligible_sample` is an empty finding; it is not a failed
execution. A `partial` report keeps its failed-method evidence visible.

## Error, empty and retry presentation

- Idle/no run: controls plus a short explanation; no fabricated preview.
- Submitting: button busy state; controls disabled only as needed.
- Pending/running: run identity and an honest wait state; no progress percentage.
- Completed: reader or explicit "no numeric data" presentation from the payload.
- Partial: completed presentation with a partial-status warning and producer method
  failures visible.
- Failed/interrupted: classified failure, no report, manual Retry.
- Busy: active-run message; manual retry only.
- Invalid request: field-level safe message; no run created.
- Status/report/network failure: distinguishable manual retry contexts.
- Corrupt/unsupported version: report/run cannot be read; no automatic repair.
- Response too large: report exceeds the display bound; no truncation.
- Storage/read capacity unavailable: retry may be possible; no queue.
- 401: application gate; stale results are discarded.
- 403 origin failure: show access denied without treating the account as invalid.
- Unknown/foreign run: same not-found presentation; no ownership disclosure.

The UI never displays internal filesystem paths, owner IDs, provider credentials,
raw exception text, private source metadata or a second interpretation of the
research result.

## Shared reader ownership and offline compatibility

WP8 extracts the pure reader content from
[the existing offline reader](../../offline/futures_basis/ARCHITECTURE.md)
into this feature-internal presentation boundary:

```text
features/futures_basis_research/report/    pure reader content + reader types
features/futures_basis_research/page/      online shell
offline/futures_basis/                     standalone shell + packager entry
```

The offline entry continues to bundle a self-contained report with no fetch, CDN,
application/auth import or backend. It may import only the pure reader subpath.
The online page uses the same reader under the application theme. No second
six-section implementation and no second financial projection is authorized.
WP8 must preserve the existing offline Vitest, build and real-Chromium offline
report acceptance.

## Generated contract and non-goals

This feature owns its committed OpenAPI representation and generated TypeScript
under its own API boundary and is included in repository `contract:check`. The
HTTP envelope is generated; the `data` field is the versioned producer reader
payload, validated against the shared reader types and the generic Visualization
validators. This does not create a competing backend response schema.

Non-goals: executing Research in the browser, recomputing statistics or progress,
storing tokens/results, adding a router/query framework, adding a second
visualization DSL, exposing offline evidence files through the Web app, and
changing sibling features or the HTTP contract.

## WP8-B implementation reconciliation

URL search changes and popstate replace the active run lifecycle. A valid 202 pushes
a new run identity; unknown IDs remove the query with replace. Submission feedback
is independent of the current terminal report, which survives rejected submissions.
The shared reader accepts explicit online/offline disclosure mode; only the offline
shell supplies standalone theme, font and adjacent-file evidence instructions.

Execution evidence and reproduction: [WP8-B acceptance](ACCEPTANCE.md).

## Historical presentation controls

The shared online/offline reader defaults to Trading Days: all candidate_dates
define equally spaced positions, including missing sessions. Calendar Days retains
natural spacing. One local control changes all three charts, resets the horizontal
viewport and preserves legend selection. Marks and events share the mapping; dates
absent from the domain are errors. Null and segment boundaries remain unchanged.
Only basis_value requests a zero-anchored 100 index_points dashed axis grid.
Explicit decimal_ratio values display as one-decimal percentages without negative
zero. Layer/result units determine formatting; probabilities, frequency, count and
prices retain their own semantics. The feature adapts result details using mark
values and units. Histogram labels use supplied IntervalCount boundaries and
inclusion flags; rounded labels never replace category identity or order.
Raw Views, reader projection, evidence, exports and fingerprints remain unchanged.

Verification and reproduction: [Historical presentation acceptance](HISTORICAL_PRESENTATION_ACCEPTANCE.md).

## Read-only input preflight

Consume Research [Preflight](../../../../market_research/descriptive/cases/futures_basis/PREFLIGHT.md)
through generated HTTP types. Check complete, format/order-valid queries after
400ms without edits and support manual refresh. Query changes immediately invalidate
results and confirmation, cancel requests and ignore stale responses. Recheck on
window focus and Shanghai date rollover. The server market_date is authoritative.
Inspection state is independent of Run/report state; checking never clears a report.

Show all window dependencies and the today gate; disclose that no data was acquired
and execution can still fail. Disable Generate while unchecked/checking/blocked or
on check failure. confirm_required needs an explicit checkbox acknowledging that
execution will attempt acquisition; reset it on query/result changes. Only an
explicit Generate posts a Run; check completion never submits. End-date changes
remain user-controlled; today blocks offer editing and recheck, no hidden ensure
or automatic shift to yesterday. Failed-Run retry first loads/checks its request.
