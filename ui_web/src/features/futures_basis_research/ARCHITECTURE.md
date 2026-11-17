# Futures Basis Research frontend authority

This is the implemented WP8-B online Web feature. It specializes the
[ui_web architecture](../../../ARCHITECTURE.md) and
[presentation architecture](../../../presentation-architecture.md), consumes the
[Online Futures Basis Research HTTP contract](../../../../ui_http/products/futures_basis_research/http-contract.md)
through generated types, and renders the R01-A reader owned semantically by
[Research](../../../../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md).
It owns input interaction, presentation state, polling and user-visible empty/error
presentation only. It never acquires market facts, executes Research or recomputes
Basis, Slot, DTE, formal statistics, coverage or run length. The authorized numerical
presentation exception is temporary Histogram Aggregation under
[Distribution presentation](DISTRIBUTION.md), reached through [Presentation authority](PRESENTATION.md).
The existing shared reader implements V1; accepted V2 metric/width and trimming
semantics await WP3/WP4. Research's [Roadmap](../../../../market_research/descriptive/cases/futures_basis/ROADMAP.md#distribution-v2-handoff)
distinguishes Authority readiness from implementation.
WP6 defines this authoritative slice; WP8 implements it and the offline reader regression.

## Application composition

The surface is discovered from Research Overview and directly under Research navigation. Research Explorer remains available as a secondary result reader. Research remains the default entry.
This is a sibling bounded
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

Application menu navigation may restore this page's opaque Run ID under
[Workspace identity rules](../../../workspace.md#production-run-navigation-identity).
The feature restores that URL through existing reads, never automatic POST. Explicit
URL identity remains authoritative over retained state; future page-instance retention
must recognize identity changes and cannot display another Run's retained report.

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
  requires complete, format/order-valid parameters; Preflight is advisory.
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
  time in collapsed details; do not show a report.
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

Online and Demo compose one compact Report Card in the shared reader. Reading order is
research question (`summary`), initially collapsed producer formulas, history and
distribution visualizations with a four-Slot summary of the selected Metric.
[Presentation authority](PRESENTATION.md) owns expiry explanation and full-sample
summary, and routes distribution controls, validation and audit to its specialized owner.
Summary presentation selects explicit `mean` / `quantile` methods and quantile
points, preserving units, zero and unavailable states. No formal statistics are recomputed.
Compact delivery omits section navigation, coverage/fingerprint/runtime metadata,
detailed evidence tables, Methods cards and request JSON. Partial retains a short warning;
empty findings and validation errors remain explicit. Full payload validation still applies.

Offline retains the complete six-section report, evidence, navigation and reproduction
instructions. History chart regions retain ChartView options, producer Views, transition
annotations, null breaks, hover and the date-axis contract; the distribution region owns
the Metric and Bin Width controls over its temporary presentation bins.

## Error, empty and retry presentation

- Idle/no run: controls plus a short explanation; no fabricated preview.
- Submitting: button busy state; controls disabled only as needed.
- Pending/running: run identity and an honest wait state; no progress percentage.
- Completed: reader or explicit "no numeric data" presentation from the payload.
- Partial: completed presentation with a partial-status warning and producer method
  failures retained in the payload; compact delivery shows a concise warning.
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

The public static demo (retired; Git history) also composes
this pure reader with `demo` disclosure mode and horizontally scrollable chart
frames on narrow screens. Online/Demo use compact composition; Offline retains all six sections. Chart controls and producer facts stay shared. Online and offline modes retain their delivery instructions.
WP8 must preserve the existing offline Vitest, build and real-Chromium offline
report acceptance.

## Generated contract and non-goals

This feature owns its committed OpenAPI representation and generated TypeScript
under its own API boundary and is included in repository `contract:check`. The
HTTP envelope is generated; the `data` field is the versioned producer reader
payload, validated against the shared reader types and the generic Visualization
validators. This does not create a competing backend response schema.

Non-goals: executing Research in the browser, recomputing formal statistics or progress,
storing tokens/results, adding a router/query framework, adding a second
visualization DSL, exposing offline evidence files through the Web app, and
changing sibling features or the HTTP contract.

## WP8-B implementation reconciliation

URL search changes and popstate replace the active run lifecycle. A valid 202 pushes
a new run identity; unknown IDs remove the query with replace. Submission feedback
is independent of the current terminal report, which survives rejected submissions.
The shared reader accepts explicit online/offline disclosure mode; only the offline
shell supplies standalone theme, font and adjacent-file evidence instructions.


## Historical presentation controls

The history charts expose the repository-wide
[date-axis presentation authority](../../../DATE_AXIS_PRESENTATION.md): the shared
online/offline reader defaults to Trading Days, all candidate_dates define equally
spaced positions including missing sessions, and Calendar Days retains natural spacing.
One local control changes all four V2 charts, resets the horizontal viewport and preserves
legend selection. Marks and events share the mapping; dates absent from the domain are
errors. Null and segment boundaries remain unchanged. This feature is the reference
application of that authority, not a second owner of the policy.

Only basis_value requests a zero-anchored 100 index_points dashed axis grid.
Display formatting follows the [presentation formatting authority](../../../PRESENTATION_FORMATTING.md):
explicit decimal_ratio, probability and frequency values display as one-decimal
percentages without negative zero, except the centrally owned narrow Histogram
boundary exception; non-integer index points and statistical values display
with two decimals; count values remain integers. Layer/result units determine formatting.
The feature adapts result details using mark values and units. Current producer Histogram
labels use supplied IntervalCount boundaries and inclusion flags; rounded labels never
replace category identity or order. Raw Views, reader projection, evidence, exports and
fingerprints remain unchanged.


## Read-only input preflight

Consume Research [Preflight](../../../../market_research/descriptive/cases/futures_basis/PREFLIGHT.md)
through generated HTTP types. Check complete, format/order-valid queries after
400ms without edits and support manual refresh. Query changes immediately invalidate
results, cancel requests and ignore stale responses. Recheck on window focus and
Shanghai date rollover. The server market_date is authoritative. Inspection state
is independent of Run/report state; checking never clears a report.

UI-05 supersedes the old Web gate: complete format/order-valid inputs permit explicit
Generate regardless of unchecked/checking/error/unknown or producer submission
classification. No confirmation checkbox or canSubmit gate remains. Preserve
`allowed` / `confirm_required` / `blocked` as producer assessment, never rewrite them.
Run API remains final validation/execution authority. No implicit POST or POST retry.
Show compact overall and dependency status plus successful/requested coverage,
natural-day / 品种×日期 / 指数×日期 units, and window/today scope only as returned.
Normal complete states have no boilerplate; exceptions get short actionable guidance.
Refresh, cancellation, stale isolation and Shanghai rollover remain unchanged.

Run summary follows UI-04: immutable 品种/window, confirmed backend status Tag
(PENDING 等待执行 gold; RUNNING 运行中 gold; COMPLETED 已完成 green;
FAILED 失败 red; INTERRUPTED 已中断 red), Started/Finished Beijing timestamps
with — for absence, secondary wrapping Run ID. Read phases remain separate and
never imply execution failure. Default-closed 运行详情 contains Created, raw status,
phase and failure fields. User-facing failure reasons and manual actions stay visible.

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature authority describe the Production controller. The same feature-owned Presentation also serves [Static Demo Runtime](../../../demo/ARCHITECTURE.md) using validated embedded Examples (retired; Git history), fixed visible request parameters and local presentation state. Static composition never mounts the production controller or fabricates its lifecycle; it preserves this feature's result/visualization semantics and applicable local Copy/Export. Shared presentation remains here, not in parallel Demo pages.

## Shared page presentation and static composition (D2-E)

`page/FuturesBasisPresentation.tsx` is the single formal page presentation. It owns the
feature header, the Research parameter region shell, immutable request facts, the Result
region and the Report composition. Production supplies only its execution regions (query
form, preflight, explicit Submit, accepted Run identity, status/errors and manual retries)
through the `production` composition input. Static composition supplies a validated fixed
request and Embedded Report through the `static` input; Preflight, Submit, polling and Run
status are never simulated or hidden behind disabled controls.

`presentation.ts` is the transport-free public entry. `api/validateResult.ts` owns the pure
generated-contract boundary: `matchesResponse`, `validateImmutableRequest`,
`validateReaderReport` (shared with Production report reading) and `validateEmbeddedReport`.
Production transport retains URL construction, protected Auth and HTTP error mapping.
`static/useStaticFuturesBasis.ts` validates the fixed request plus the complete producer
reader payload once and exposes only validated facts; it owns no Run, polling, fetch or
`run_id` restore. Page-level requested-window facts remain separate from the producer's
actual observed coverage, and static success means the Embedded Report passed formal
validation, not that a server Run executed.

The shared `report/Report.tsx` selects Compact for online/demo and Full for offline
using its existing mode. Compact has no section navigation and local interactions preserve
static hash routes. Offline retains its section links. Demo fixed parameters and accepted
Online request facts show only product and inclusive request range. Demo shows only the
static alert title and this fixed paragraph:

本页面为静态研究成果展示。数据不保证准确，不构成任何投资建议，仅供项目功能演示。

Source provenance and Bundle metadata remain owned by admission. Compact Demo retains
the exact supplied sourceDisclosure in the default-closed 数据来源 disclosure, owned by
[Presentation authority](PRESENTATION.md). Invalid embedded payloads retain the existing error path.

## V2 origin policy reconciliation

Demo Example authority (retired; Git history) owns formal V2 real-market dates and
packaging; authenticity and rights (retired; Git history) owns evidence and admission.
This feature owns only their presentation. Static delivery is not a Synthetic source label
or proof of authenticity. Preserve historical V1/test disclosures, use actual real-market
origin for V2, and never promote regression inputs to formal Examples. WP-B propagates an explicit validated Example source statement from static composition
through UI-only `sourceDisclosure` (compact Demo displays it on explicit expansion); delivery mode never
infers real-market origin. Historical Synthetic defaults and Production/Offline evidence
remain unchanged. Admission and provenance ownership stay in the
private build contract (retired; Git history).

## Research introduction

Shared FuturesBasisPresentation shows 关于本研究 below the heading and above parameters
in both runtimes, collapsed by default, with exactly two fields.

- 研究目的 — 观察股指期货相对现货指数的价格偏离，理解不同合约期限下的贴水特征及其历史变化。
- 研究方式 — 基于历史交易日数据，统计并可视化不同期限合约的基差、分布和贴水持续区间。

Expansion is local UI state preserving HTTP requests, Run, report, chart state, URL and
section navigation. It contains no internal identities, endpoints or configuration.

Compact Demo/Online history charts all enable the shared initially closed 日期事件（Date Events） disclosure. Its description is: 标记不同期限 Slot 所对应的期货合约发生切换的日期，仅用于描述合约映射变化，不代表实际交易。 These are producer Contract Transition events; all Slot mappings and chart markers remain unchanged. Offline Full keeps the existing event list; distribution charts are unaffected.
