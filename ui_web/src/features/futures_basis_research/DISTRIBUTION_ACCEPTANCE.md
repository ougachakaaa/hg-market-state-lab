# Task 2 distribution acceptance — 2026-11-16

Execution evidence for [Presentation authority](PRESENTATION.md), not a second
statistics or wire contract. Branch: `feat/futures-basis-research-improvements`;
baseline: `d3de3ddcba2220c8786f0ca880f41b8a5abac00a`.

## Delivered behavior

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

## Verification

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
