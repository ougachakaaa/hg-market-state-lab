# WP5 integration and research delivery acceptance

Contracts: [Delivery](DELIVERY.md), [Evidence](EVIDENCE.md),
[usage](USAGE.md), and [offline reader](../../../../ui_web/src/offline/futures_basis/ARCHITECTURE.md).

Branch: `feat/r01-futures-basis-research`; required baseline:
`1b656d7919580a5b668b71d83088574737a37d48`. Independent WP5 commit, no develop merge.
Acceptance date: 2026-11-06 (Asia/Shanghai).

## Implemented boundary and reconciliation

Research composes one WP3 result, all 12 distributions, 18 paired comparisons
and four Slot persistence summaries. The original WP4 API owns all numerical
outputs. The formal report request and evidence are distinct from WP3/WP4 test
JSON. Canonical inputs decode through public carriers and existing final Export /
prepared-input validation; replay never reads Dataset storage or calls Source.

Research projects three separate V2 history Views, preserving values, nulls,
contract-change/gap/absence segments, four ordered Slot bindings, real events and
source associations. Successful IntervalCount results produce V1 count/frequency
categorical bars, including exact inclusion labels and both outside bins.
Tables retain common-date populations, dropped reasons and complete/censored runs.
Composition/evidence may import public Statistics spec types/validation only;
`compute` stays in the unchanged statistics adapter. Architecture tests specialize
this precise permission, without opening private or reverse dependencies.

ui_web owns its separate offline React entry, Ant Design presentation, embedded
assets and generic ChartView consumption. No financial computation, fetch, HTTP,
authentication change, Publication admission or Workbench Run is introduced.
The only shared renderer addition is optional plot-frame sizing, with the old
default preserved. An OFL-licensed Chinese font subset is embedded for offline
readability on systems without Chinese fonts. Browser numerical data is exactly
the producer's retained report payload.

## Real IM short-window gate

Window: `2026-10-12..2026-10-23`, IM / `000852.SH`.
Input SHA-256: `6facf8378a576eb914e8675dfa0d0c8ee54be356e21cabdc7c40d52bdce27154`.
The original WP3 canonical input bytes are retained unchanged. All original WP4
requests and original Statistics method outputs matched exactly for all 12
Distributions and 18 Comparisons, not merely rounded summary values.

Coverage: CFFEX and SSE each 12/12 natural dates; Futures 10/10 product-days;
Index 10/10 sessions. 40 Slot-days; each raw metric has 40 eligible values,
annualized has 39 plus one `expiry_day`. All four observed role transitions on
2026-10-19 retain old/new real contracts. Annualized M0 comparisons use 9 common
dates; other populations retain their WP4-defined dates.

| Slot | Mean basis_value (index_points) | Raw / annualized n |
| --- | --- | --- |
| M0 | -19.01426 | 10 / 9 |
| M1 | -75.07426 | 10 / 10 |
| Q1 | -184.79426 | 10 / 10 |
| Q2 | -350.37426 | 10 / 10 |

M0 retains two complete discount spans and a five-session censored fragment.
M1/Q1/Q2 retain ten-session censored fragments. These are E2E observations,
not long-term or predictive claims.

## Longer portfolio candidate

The explicit `2024-01-01..2026-10-30` IM request succeeded through existing public
DataLake acquisition, in new isolated external Dataset caches. The acceptance
harness confirmed default user caches were unchanged; no partial Futures override,
substitution, private Research data access, retry framework or source workaround.

Input SHA-256: `6b96f3846b69d44341e69a4f2f6c64c2a0d96615ff9b7b5504384ef08457f3d8`.
Each calendar covers 1,034/1,034 natural dates. Futures and Index each cover
683/683 sessions. All 2,732 Slot-days have eligible raw metrics; annualized has
2,698 eligible values and 34 M0 expiry-day Not Applicable outcomes.

| Slot | Mean basis_value (index_points) | Mean basis_ratio (decimal_ratio) | Mean annualized_basis_ratio (decimal_ratio) | Raw / annualized n |
| --- | --- | --- | --- | --- |
| M0 | -30.42622518301613 | -0.004683730570821132 | -0.13425773193379814 | 683 / 649 |
| M1 | -89.75038330893118 | -0.01374436208675794 | -0.1160394652695716 | 683 / 683 |
| Q1 | -204.26780644216691 | -0.03093246050300252 | -0.10884857850566146 | 683 / 683 |
| Q2 | -358.15916808199125 | -0.053783059174968166 | -0.10260270864260472 | 683 / 683 |

This is a genuine longer-window descriptive portfolio candidate. Mean negative
basis is not a strategy return; annualized log rates near expiry are sensitive to
DTE. No independence, stationarity, causal or predictive claim is established.

## Verification and reproduction

Passed: 1,249 Python Research/topology/architecture tests, Ruff, MyPy (102 files),
Web contract freshness, 252 Vitest tests, TypeScript/Vite build and lint. Generic
V1/V2 real Chromium regression also passed.
Targeted tests cover original result linkage, expiry/transition/null segments,
legal partial Index, empty/all-null populations, method failures, input failures,
canonical decoding, cache-free replay, file corruption, resealed scientific/HTML
mismatch and unsafe package files. Existing Basis/Slot/Statistics algorithms stay
unchanged; V1/V2 regression remains required.

Actual Chromium 156.0.8078.4 opens the self-contained file with offline context,
without starting any server. Short and long reports verify embedded producer data,
three metric plots, every finite point, all four Slot legends/events, actual Hover,
Zoom/Pan/Reset, missing reasons, paired dates and evidence sections. Synthetic
browser reports additionally exercise all-null/empty data, numerical failure and
literal script-ending text. No external requests or browser errors are accepted.
The report embeds its Chinese font; screenshots are reviewed for readable glyphs
and usable chart/legend space. The horizontal directory stays fixed with an
opaque theme background, so scroll-spy updates cannot pull the reader back to the
top. Browser gestures wait for stable plot layout and use actual viewport pixels.
SHA-256 inventory and scientific replay are separate
checks from browser rendering, and both must pass.

Final external deliveries (not Git artifacts):

- Short report: `/tmp/hg-market-state-lab-wp5-im-20261106-accepted/report.html`.
- Portfolio: `/tmp/hg-market-state-lab-wp5-im-long-20261106-accepted/report.html`.
- Adjacent evidence, manifest, SHA256SUMS and REPRODUCE.md belong to each delivery.
- Browser results/screenshots: corresponding `-accepted-browser/` directories.
- Live long-window isolation evidence: `/tmp/hg-market-state-lab-wp5-im-long-20261106/acceptance.json`.
- Synthetic edge browser evidence: `/tmp/hg-market-state-lab-wp5-edge-browser-20261106-final/`.

These disposable paths require external preservation. Final delivery runtime
metadata records the clean WP5 Git revision; earlier development packages record
the baseline revision with dirty=true and are not the final handoff.

Generate a new report using [USAGE](USAGE.md). From repository root:

```bash
poetry run pytest -q market_research/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_research
poetry run mypy market_research/src market_research/tests market_research/scripts/futures_basis_report.py
poetry run python market_research/scripts/futures_basis_report.py verify /tmp/hg-market-state-lab-wp5-im-long-20261106-accepted
poetry run python market_research/scripts/futures_basis_report.py replay /tmp/hg-market-state-lab-wp5-im-long-20261106-accepted
```

From `ui_web` run `npm run contract:check`, `npm run test`, `npm run build`,
`npm run lint`, `npm run test:visualization-browser` and
`npm run test:futures-basis-report-browser -- /absolute/delivery`.
Chromium/system libraries must be installed; the existing
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` and `LD_LIBRARY_PATH` options are supported.
Explicit isolated live reproduction:
`poetry run python market_research/tests/futures_basis_report_acceptance.py --output /absolute/new/external-directory`.
Synthetic browser reproduction:
`poetry run python market_research/tests/futures_basis_report_browser_fixtures.py --output /absolute/new/external-directory`.

## Limits and decision

No source freshness or hash authenticity certification, Windows execution gate,
generic Research CLI, HTTP/Publication extension, backtest or Week 2 work is
claimed. HTML is deliberately self-contained (roughly 6 MB short / 13 MB long),
not a paginated remote-data application. All original numerical failures remain
evidence; a transient failure need not reproduce identically. Font coverage is
bounded to current report copy, with OS fallback for arbitrary new characters.

WP5 **PASS**: the recorded checks, real IM results, offline interaction and
scientific reproduction gates pass for both deliveries above.
With WP1–WP4 accepted and these WP5 gates passed, R01-A Week 1 is complete for
its defined descriptive/offline delivery scope, including a real longer-window
portfolio candidate. This does not authorize publication or trading conclusions.
