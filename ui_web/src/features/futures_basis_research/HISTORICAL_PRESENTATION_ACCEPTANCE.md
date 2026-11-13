# Historical Basis presentation acceptance

> Authority note: the Trading Days / Calendar Days behavior recorded here is now the
> repository-wide standard owned by the
> [date-axis presentation authority](../../../DATE_AXIS_PRESENTATION.md). This file is
> implementation and verification evidence for W1, not a second normative standard.

Implementation stays on `feat/web-ui-ux-polish` above `056c72a`, preserving the
existing UI polish, as requested. Develop was verified at `52b31a5`.

## Presentation behavior

- One Ant Design Segmented defaults all history charts to Trading Days. The complete
  candidate-date domain maps marks, null sessions and transition annotations to
  ordinal positions. Calendar Days uses Plotly date coordinates. Switches restore
  the full x range while retaining legend selection.
- Ordinal tick labels are limited to eight and follow the viewport. Full-domain
  label aliases retain real dates in axis hover, including points between ticks.
- Reset uses a stable renderer callback and explicit axis UI revisions: Plotly's
  native reset otherwise retains the first coordinate system's initial range.
  Nulls, segment boundaries, grouping, colors and original coordinates are retained.
- Only the basis-value feature requests a zero-anchored 100-point dashed axis grid.
  Generic Visualization contains no basis-specific rule or financial calculation.
- Explicit decimal_ratio coordinates and statistical results display as percentages
  with one decimal. The shared formatter preserves missing states and removes
  rounded negative zero. Probability, count, frequency and prices retain their units.
- Histogram display labels retain category identities, order and inclusion flags.
  Colliding rounded labels neither merge bars nor change table row identities.
  The result detail adapter belongs to the feature, not the generic renderer.

No Research/Statistics source, HTTP DTO, generated contract, Reader Projection,
scientific values, evidence files, exported values or fingerprint was changed.

## Reproduction and verification

From `ui_web/`:

```bash
npm run contract:check
npm run lint
npm run build
npm test -- --maxWorkers=1 --testTimeout=15000 --reporter=dot
npm run test:visualization-browser
npm run test:futures-basis-online-browser
npm run test:futures-basis-report-browser
```

The build includes TypeScript. Browser gates use real Playwright Chromium and
synthetic public facts; they do not claim live-market acquisition readiness.
Online acceptance includes real authentication/HTTP and lifecycle checks. Offline
acceptance opens a self-contained file with network access disabled. Both exercise
Zoom, Pan, Reset, legend preservation, hover and transition mappings in both modes.
Generic fixtures also cover a multi-year weekday domain, percentage ticks near zero,
and visible positive/negative 100-point dashed grid lines.

From repository root, the existing edge-report gate verifies all-null and failed
statistical results, missing-value disclosure and escaped producer text:

```bash
poetry run python market_research/tests/futures_basis_report_browser_fixtures.py --output /tmp/historical-basis-edge-acceptance
```

Use a new external output directory when reproducing. Artifacts are disposable;
the online gate defaults to `/tmp/wp8b-online-browser`, generic Visualization to
`ui_web/node_modules/.cache/visualization-browser`, and offline gates print their
new temporary report/browser directory. Screenshots cover 1440×900 and 1024×768;
normal online/offline and long-domain/grid/percentage images were inspected.

Validation result: PASS — 42 test files and 378 tests passed in the final serial
run (15-second timeout). Contract freshness, lint, TypeScript/build and all three
Chromium gates passed. Empty/failure edge reports
also passed. Under concurrent build/browser load, existing UI tests intermittently
exceeded their default five-second timeout; the final suite runs serially with a
15-second timeout without changing tests or repository configuration. Existing
Ant Design List deprecation and bundle-size warnings remain outside this task.

No visual acceptance remains unfinished. Browser fixtures are synthetic and do
not verify live-provider readiness. No unresolved presentation regression was found.

## Changed files

- `ui_web/VISUALIZATION.md`
- `ui_web/VISUALIZATION_V2.md`
- `ui_web/scripts/futures_basis_online_browser.mjs`
- `ui_web/scripts/futures_basis_report_browser.mjs`
- `ui_web/scripts/historical_basis_acceptance.mjs`
- `ui_web/scripts/visualization_browser_smoke.mjs`
- `ui_web/src/features/futures_basis_research/ARCHITECTURE.md`
- `ui_web/src/features/futures_basis_research/HISTORICAL_PRESENTATION_ACCEPTANCE.md`
- `ui_web/src/features/futures_basis_research/report/Report.test.tsx`
- `ui_web/src/features/futures_basis_research/report/Report.tsx`
- `ui_web/src/features/futures_basis_research/report/presentation.test.ts`
- `ui_web/src/features/futures_basis_research/report/presentation.ts`
- `ui_web/src/features/research_explorer/ARCHITECTURE.md`
- `ui_web/src/features/research_explorer/page/AnalysisDetails.test.tsx`
- `ui_web/src/features/research_explorer/page/ResearchExplorerPage.tsx`
- `ui_web/src/shared/format/interval.ts`
- `ui_web/src/shared/format/unit.test.ts`
- `ui_web/src/shared/format/unit.ts`
- `ui_web/src/shared/visualization/ChartView.tsx`
- `ui_web/src/shared/visualization/FixtureHarness.tsx`
- `ui_web/src/shared/visualization/figure.ts`
- `ui_web/src/shared/visualization/figureV2.ts`
- `ui_web/src/shared/visualization/index.ts`
- `ui_web/src/shared/visualization/presentation.ts`
