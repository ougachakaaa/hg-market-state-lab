# Distribution presentation acceptance

Execution evidence for [Presentation authority](PRESENTATION.md), not a second
statistics or wire contract. Task 2 delivered SD-02/SD-03/SD-05; Task 3 closes the
whole five-decision set and records the final reconciliation.

## Task 2 delivery — 2026-11-16

Branch: `feat/futures-basis-research-improvements`;
baseline: `d3de3ddcba2220c8786f0ca880f41b8a5abac00a`.

### Delivered behavior

SD-02, SD-03 and SD-05 are implemented in the shared reader. SD-01's D=0 note and
SD-04's formal four-Slot summary remain. One Frequency comparison replaces the
Count/Frequency primary charts. Metric resets its default width; width changes only
local display bins. Formal Methods remain available by Slot in Offline's six sections.

The feature-local projection matches history Slot IDs and raw coordinates to
Distribution/Accounting identities and successful method sample counts/units.
An inconsistent Slot stops the entire selected Metric comparison. IntervalCount
failures remain visible and cannot yield successful curves. Numerical duplicates,
zero, nulls, extreme values and distinct per-Slot populations retain their meaning.

Edges use zero-anchored rational preset widths and integer indices, direct binary64
edge generation and ordered-edge binary search without tolerance snapping. Intervals
are left-closed/right-open, except the closed final endpoint. Each Slot conserves
Count exactly; Frequency uses that Slot's N. More than 2,000 bins or unsafe edge
representation produces an explicit capacity state without clipping or width changes.

### Verification

All commands run from `ui_web/`, using installed dependencies. Scoped Vitest runs
covered 71 distinct cases across the aggregation, distribution figure, shared Report,
Offline Report, existing summary model and history presentation tests. Direct fixes
were checked with the affected case(s), rather than full repository regression.

| Check | Result |
| --- | --- |
| Scoped Vitest (six directly relevant files) | PASS |
| `npm run build` (TypeScript and Online artifact) | PASS |
| `npm run lint` | PASS; two existing warnings in unrelated Demo tooling |
| `npm run demo:check` | PASS; nine existing Bundles admitted |
| `npm run demo:build` | PASS; committed Bundles reused, no acquisition |
| `node tests/browser/futures_basis_summary_browser.mjs` | PASS; formal Basis Demo |
| `npm run test:futures-basis-static-browser` | PASS; static composition and routing |
| `npm run test:futures-basis-report-browser` | PASS; self-contained file report, no network |
| `npm run test:futures-basis-online-browser` | PASS; real Auth/HTTP with deterministic market fixtures |

Chromium 156.0.8078.4 verified every Metric/preset width, Count/Frequency/N against
raw history and Eligible bindings, exact formal summary cells, independent legends,
real hover, Zoom/Pan/Reset, parent-only resizing, D=0 note and 1440/1024/390 containment.
An initial Online/Offline resize overflow was fixed with observed parent sizing and
chart containment; the affected browser acceptance subsequently passed.

Formal Basis Bundle sample conservation, checked independently for every preset:

| Metric | M0 | M1 | Q1 | Q2 |
| --- | ---: | ---: | ---: | ---: |
| basis_value | 147 | 147 | 147 | 147 |
| basis_ratio | 147 | 147 | 147 | 147 |
| annualized_basis_ratio | 140 | 147 | 147 | 147 |

Formal Demo screenshot: ignored `.build/futures-basis-summary-review/demo.png`.
The summary screenshot path now uses `fileURLToPath()`; native Windows execution is
NOT VERIFIED. Vite retains the existing large Plotly bundle warning. No new dependency,
HTTP/DTO/endpoint, Research/Statistics implementation or Bundle bytes were changed.
Online fixture Runs are test-only; no live market acquisition or research regeneration
was used for the formal Demo. No merge, PR, push or publication was performed.

No known Task 2 implementation gap remains before final reconciliation. Broader
cross-platform/release acceptance is not claimed by this task.

## Task 3 final reconciliation — 2026-11-16

Reviewed baseline `732dbc8d67966080db4b0570b67f0606d1ce90bb`; develop and the
merge-base were both `d504443029c65cf3104769ef4a86465642d4e8a9`, so the branch had no
develop drift before this round. This section records closing evidence and
reconciliation fixes only; it adds no product behavior, contract or Bundle change.

### Semantic Decision status

| SD | Status | Reconciled evidence |
| --- | --- | --- |
| SD-01 Expiry day | PASS | `D=0` keeps Not Applicable `expiry_day` while raw values stay applicable; [Definition](../../../../market_research/descriptive/cases/futures_basis/DEFINITION.md) owns the positive-span requirement, the Close/settlement convention difference, the rejected D+1 alternative, precedence preservation and the reusable principle. The reader shows the D=0 explanation only beside the annualized chart, outside disclosures, in every mode; formula, units and status precedence are unchanged. |
| SD-02 Dynamic bins | PASS | Three Metrics expose the four preset widths with percentage-point to decimal_ratio conversion; zero-anchored integer edges, direct binary64 generation, left-closed/right-open intervals with one closed final endpoint, exact Count conservation, per-Slot N denominators, unsafe-index/capacity refusal and no epsilon snapping. Regression cases cover negatives, signed zero, exact/adjacent boundaries, duplicates, singleton and repeated samples, 2,000-bin limit, `1e10`/`MAX_VALUE`. |
| SD-03 Count/Frequency | PASS | One distribution chart in the primary region, defaulting to Frequency; the tooltip supplies Count, one-decimal Frequency and Eligible N from the same bin. The formal producer IntervalCount method, its result and its Offline table are untouched and never recomputed. |
| SD-04 Summary | PASS | `Slot \| N \| Min \| P25 \| Median \| P75 \| Max \| Mean` for M0/M1/Q1/Q2 reads explicit `quantile` points by value and the explicit `mean` result, never array order. Bin Width does not change it. Failed, absent, mismatched and empty methods show `不可用`/`不可用（category）`; only a genuine zero result prints zero. |
| SD-05 Four-Slot comparison | PASS | M0/M1/Q1/Q2 are initially visible, share one explicit edge set and keep independent populations and denominators; legend toggles each Slot alone and reuses its history Binding color; hidden Slots change neither shared edges nor sibling Frequency. No Slot, financial formula or contract mapping is rederived. |

### Drift found and fixed

1. **Statistics-failure contradiction (implementation bug).** A Slot with Eligible
   N>0 whose formal IntervalCount reported `no_eligible_sample` was silently plotted
   as a missing curve with no alert. [Statistics scope](../../../../market_research/descriptive/cases/futures_basis/STATISTICS.md)
   and the [Python analysis contract](../../../../market_research/descriptive/cases/futures_basis/STATISTICS_API.md)
   emit that category only when no Eligible row exists, so the payload is
   self-contradictory. The projection now rejects the whole selected Metric
   (`展示数据不一致：<Slot> Eligible 样本与 no_eligible_sample 矛盾`) while keeping formal
   summaries readable, treats N=0 `no_eligible_sample` as an empty finding rather than
   a failure, and still retains any other formal failure for only its own Slot. The
   formal producer result and the shape-only reader validator are unchanged; no
   recovery or bypass path was added.
2. **Slot color source.** The chart derived colors from a hardcoded Slot order while
   the history renderer colors by Binding order. Colors now come from the Slot's own
   history Binding index, so `its history-series color` holds for any accepted payload
   instead of only for canonically ordered Bindings.
3. **Authority control attribution.** [Feature architecture](ARCHITECTURE.md) claimed
   History chart regions retain the Metric/Bin Width controls. Those controls belong to
   the distribution region; the sentence now separates the retained history controls
   from the distribution controls.

[Presentation authority](PRESENTATION.md) records the empty-finding versus
contradiction rule; no other Authority needed a change. Producer, Statistics, HTTP,
OpenAPI, DTO, Demo Bundle/Manifest and dependency paths are untouched
(`git diff d504443 --name-only` matches none of them), and the committed Bundle stays
byte-identical because no admitted file changed.

### Verification

| Check | Result |
| --- | --- |
| `npx vitest run src/features/futures_basis_research src/offline/futures_basis` | PASS; 13 files, 118 tests (five new regression cases; none removed or weakened) |
| `npm run build` | PASS; `tsc -b` and Vite; only the existing large Plotly chunk warning |
| `npm run lint` | PASS; 0 errors, the same two unrelated Demo-tooling warnings |
| `npm run demo:check` | PASS; 9 Bundles admitted |
| `npm run demo:build` | PASS; committed Bundles reused, no acquisition |
| `node tests/browser/futures_basis_summary_browser.mjs` | PASS; formal Demo, all three Metrics x four widths conserved against raw history, summary cells, hover, Zoom/Pan/Reset, Legend, Date Events, Date axis, 1440/1024/390 |
| `npm run test:futures-basis-report-browser` | PASS; `file://` self-contained report, zero requests, six sections, distribution and summary at 1440x900 and 1024x768 |
| `npm run test:futures-basis-online-browser` | PASS; real Auth/HTTP/Vite/FastAPI with deterministic market fixtures, incl. distribution conservation and summary |
| `npm run test:futures-basis-static` + `test:futures-basis-static-browser` | PASS; static composition, local controls, routing/Back-Forward/reload, ignored `run_id`, rejected payload and zero Auth/API requests |
| `npm run contract:check` | PASS; every consumed OpenAPI and generated TypeScript is current, no regeneration |

Chromium 157.0.8103.51 (system Chrome through `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`;
the Playwright-managed browser is not installed on this host). The Task 2 native
Windows screenshot gap is now verified: the summary script wrote
`.build/futures-basis-summary-review/demo.png` on Windows. The fix was validated
negatively first: the three new failure-consistency cases fail on the pre-fix
implementation and pass after it.

Not verified: Linux/WSL and non-Chromium browsers, and full-repository regression
(out of the scoped verification policy).

### Merge readiness

`feat/futures-basis-research-improvements` was based directly on the current
`develop` tip `d504443`, so the change set is additive with no overlap or conflict.
No rebase, merge, force-push, PR or publication was performed. Conclusion for the
reviewed commit: `MERGE_READY` via a no-ff merge into `develop`.
