# Calendar Spread L1 WP7 local acceptance — 2026-11-16

**Implementation Complete; Operational Delivery Complete; READY TO CLOSE.**
Ready for merge review on `feat/calendar-spread-wp5-http`, from exact clean baseline
`29736db8402c29c69ea740c4048ecb5cfa7a4954`. Delivery commit is identified by Git
history and the final task report. No merge, push, Publisher or Pages deployment.

## Actual formal HTTP capture

Both candidates were first checked through authenticated local FastAPI HTTP, then
captured with the existing Collector, Cookie/Origin, Node bridge, independent
Preflight and durable transaction. Only the two new Bundles were selected:

```bash
# repository root; existing approved account, password entered through getpass
poetry run python ui_web/demo/build/collect.py \
  --only calendar_spread_daily --only calendar_spread_relative_value \
  --base-url http://127.0.0.1:8011
```

| Bundle | Method / route / status | Explicit request |
| --- | --- | --- |
| `calendar_spread_daily` | GET `/data/futures-calendar-spread` / 200 | product_code=IM, trade_date=2026-09-30 |
| `calendar_spread_relative_value` | POST `/research/calendar-spread-relative-value/query` / 200 | product_code=IM, history_start=2026-03-01, evaluation_date=2026-09-30, metric=annualized_spread_ratio; histogram_edges omitted |

Complete `DailyResponse` / `HistoricalResponse` bodies retain formal case, definition,
operation/default echo, financial values and array order. Source is the formal
FastAPI projection of retained Tushare/CFFEX Calendar/Futures facts, using real
contract Close. No synthetic test fixture, direct business-service capture, Ensure,
cache change, Run creation, retry, private path or credential was used in a Bundle.

Daily has six valid observations, zero excluded/not-applicable. Real contracts:

| Pair | Near | Far | Near DTE / stage |
| --- | --- | --- | --- |
| M0/M1 | IM2610.CFX | IM2611.CFX | 16 / 8_21 |
| M0/Q1 | IM2610.CFX | IM2612.CFX | 16 / 8_21 |
| M0/Q2 | IM2610.CFX | IM2703.CFX | 16 / 8_21 |
| M1/Q1 | IM2611.CFX | IM2612.CFX | 51 / 22_plus |
| M1/Q2 | IM2611.CFX | IM2703.CFX | 51 / 22_plus |
| Q1/Q2 | IM2612.CFX | IM2703.CFX | 79 / 22_plus |

Research has 876 valid Pair-days (146 per pair), no exclusions/not-applicable
historical observations. Actual sample coverage is 2026-03-02 through 2026-09-29,
strictly before evaluation. All six current observations and both current comparisons
are available. Group sizes in order 0_7 / 8_21 / 22_plus / all_stages:

- M0/M1, M0/Q1, M0/Q2: **41 / 67 / 38 / 146** each.
- M1/Q1, M1/Q2, Q1/Q2: **0 / 0 / 146 / 146** each.

Empty groups remain empty_sample with null statistics; no neutral rank or fallback
is manufactured. Histogram was not requested; the real static page truthfully has
no Histogram. The shared Presentation retains optional Histogram support, verified
by WP6 feature-validator fixtures separately from real-market capture evidence.

## Membership and unchanged data

The sole Registry and Manifest require **nine Bundles**. The sole runtime has
**ten static routes**, preserving all prior eight. New hash routes mirror the formal
Daily/Research paths. Sidebar and overviews now expose both admitted pages.
Production and Demo share the public WP6 Presentations; Demo imports no Production
query hooks, Auth flow or financial/statistical calculation.

All prior files were compared byte-for-byte and by SHA-256 with the baseline:

| Bundle | Unchanged SHA-256 |
| --- | --- |
| basis | 33ab2da5a36b8b0b862856322ca7b9f1f1a98bee1913fedc55b3a1dc7db77397 |
| catalog | af90ab7ec17bce2bb24678b6a9a786fa6688d9a4bdff5ed8cb887b3ea2e7982d |
| chain | d0c49192d9094cc4ed839008e3123e57624d2026708fcbb960e176ac28e47294 |
| expiry_to_M1_v1 | 11edb220ed34cf8ea0239bacf55294970a7cfbae86cf6849441657d4dbbb2720 |
| expiry_to_Q1_v1 | 2492ac91e1566e241dd4543df05e42fe3f435794d6d1d91659a538562182475f |
| premium | 15dd54f4a51df1ad82232b11fde4d0b3cfadd7cd18d70f45c18b20324735dd41 |
| publications | 8957b3c07a8b7fa1cd1afd04ec2ffcb5aa444d38c047a8389a2cefe201c22024 |

New Daily SHA-256: `6c2c27f29e92ce0b354b9a7de135d27d8884f3fc1aae5fe7396da013bd24c85b`.
New Research SHA-256: `9db5ae90643e5a8023a077c09db9b5165109725b1d95d5768a4e8a092e7c8c6f`.

## Executed scoped verification

| Check | Result / scope |
| --- | --- |
| Real Collector | PASS; two selected synchronous 200s; entire nine-member candidate/active admission |
| `npm run demo:check` | PASS; independent offline validation, including after stopping the local backend |
| `npm run demo:build` | PASS; actual admitted artifact in `.build/demo/`; existing large-chunk warning |
| `npm run demo:test:browser` | PASS; installed Chromium; ten routes and shared overview layout harness |
| Extended browser helper | PASS; actual Daily Close/metrics/contracts, exact Research chart values/dates, Quantile/Percentile text, both date axes, Zoom/Pan/Reset, Pair selection, sample/disclosure expansion, no query controls or business/Auth network |
| `demo/build/collector.test.ts` | PASS across scoped invocations; wire schema/method/status/request corruption, numeric fidelity, controlled Cookie/Origin, atomic pair selection, 7→9 extension, failed capture preservation and transaction recovery; six Python controlled-server cases |
| `demo/build/validate.test.ts` | PASS; required membership/missing files, canonical bytes/hashes, request/result corruption and existing admission cases |
| `demo/build/release.test.ts` | PASS; nine-member content requirements and formally legal empty Daily rejected only by release content admission |
| `demo/build/runtime.test.ts -t 'maps nine'` | PASS; adapter dispatch/missing/malformed input; unrelated repeated build cases not run |
| Changed route/overview/shell/catalog tests | PASS; failed old visibility expectations alone rerun after correction |
| Two feature `api/validateResult.test.ts` files | PASS; 32 tests, including empty/small, histogram association, null/zero/excluded and nonfinite cases |
| Contract freshness | PASS; nine generated contract pairs current; no generated artifact changed |
| TypeScript | PASS; app, Demo build tooling and runtime configs |
| Changed-source Ruff / Oxlint | PASS |
| Credential inspection | PASS; supplied private password and configured secret absent from changed sources/new Bundles/actual artifact; ignored root `.env` excluded from Git |
| Release content predicates | PASS; real current values, sufficient dated history, both assessments and truthful empty groups |

The local post-commit `npm run demo:release-check` records its exact source SHA,
requirements/Manifest identity and Artifact Receipt in ignored
`.build/demo-release.json`; its final outcome belongs to the task report. This
command is a local check and never authorizes publishing.

Public payload inventory now covers the two new captures, updated Manifest and the
14 existing WP6 synthetic JSON fixtures. Fixture bytes did not change and remain
test-only; they are never admitted as the active real-market delivery.

Browser diagnostics and screenshot: `.build/demo-review/calendar-spread-acceptance.json`
and `calendar-spread-real.png` (ignored). Network isolation rejects any business/Auth,
fetch/XHR or off-site request. The runner closes its temporary previews and browsers.
The local backend started for capture was stopped afterward. No market/cache,
Auth database reset, Run or Publication history cleanup occurred. Only Collector/test
owned temporary staging is cleaned; local Auth serving configuration and the user-
requested login notes remain in ignored root `.env`.

## Reconciliation and remaining limits

Demo entry → Bundle/Calendar Spread contract → build/release contracts → runtime
and evidence are consistent on nine Bundles/ten routes. Workspace and Research
case Roadmap point here. Business/HTTP DTO meaning and the shared Presentations'
source/financial limitations are unchanged. No separate Demo financial logic exists.

Provider accuracy, point-in-time metadata, future freshness, other browsers/platforms
and deployed Production Gateway remain **NOT VERIFIED**. The capture proves formal
HTTP provenance, not independent verification of exchange facts. No Pages/Actions
publication, remote gate, merge or release-branch push was performed. These limits
do not prevent local WP7 closure or review; actual publication needs its own request.

## Final reconciliation and Develop integration — 2026-11-16

**Final Reconciliation PASS; WP0–WP7 CLOSED; READY_TO_MERGE.** This section
supersedes the earlier package-local pending integration/readiness statements.

- Requested delivery baseline: `10a2743119d20a60e7ea143e49abbc96670bb58d`.
- Tested and pushed feature Source: `73778750676a5ff8ed5a4a1e4d1ead181b88de6a`.
- Corrected task/Develop integration base: `5190d66ee8e5b47c14a59e447b4c4b8cdc9abbf5`.
- Exact corrected `--no-ff` Develop merge: `08725627b58cc9771b9b769a8c3cc86417ecd521`.
  Its parents are the above Develop base and feature Source, and its tree equals
  the tested feature tree. WP5 `e18c52c`, WP6 `29736db` and WP7 `10a2743`
  remain original commits. This evidence-only follow-up changes two Markdown files.
  The final checkout SHA and fresh Receipt are recorded by `demo:release-check`
  in ignored `.build/demo-release.json` and the final task report; no commit embeds
  its own hash. Develop promotion requires that final committed checkout to pass.

History correction requested by the user: the six commits after `5190d66` through
`6e20f1e` belong on the feature side, together with WP5–WP7. The corrected merge's
first parent is `5190d66`, so those six commits leave Develop's first-parent chain
while remaining reachable through its merged feature parent. Their original SHAs
and all implementation/Bundle bytes are preserved. The earlier merge `0c1f4d2`
and closure `993331c` describe the superseded integration attempt, whose incorrect
first-parent base was `6e20f1e`. Replacing the already-pushed Develop ref requires
an explicitly approved lease-protected non-fast-forward push; preparing this
candidate does not itself advance that remote ref. Main/release refs are unchanged.

Authority/source review confirms one WP1 financial implementation, WP2 export-only
preparation without Ensure, WP3 public Statistics dispatch and WP4's strict
`history_start <= trade_date < evaluation_date` population. Both WP5 products are
registered in the composed app, with Auth and explicit business 422 responses.
WP6 consumers own separate generated contracts and query state. WP7 uses the
single Registry/Manifest/Collector/build/release path and shared feature Presentation.
Demo owns no financial/statistical algorithm. Dependency review found no reverse
or cyclic dependency in the added paths. Backtesting and existing business result
contracts are unchanged; Basis's adjacent Spec narrowing preserves its behavior.
The Pages workflow still runs only after an explicit release-branch push through
the existing Publisher; Develop pushes do not publish.

### Executed final checks

Every successful command below exited **0**. Commands run at repository root,
except npm/Node/Vitest commands, which run in `ui_web/`.

| Command / selected scope | Actual result |
| --- | --- |
| `poetry run pytest -q` with the four Calendar Spread financial/input/Observation/query files, `market_statistics/tests/test_empirical_percentile.py`, HTTP Calendar Spread/Auth files, exporter file and Collector Python file | 610 passed, 6 skipped; skipped Collector cases require the Vitest-supplied fixtures below |
| `poetry run pytest -q ui_http/tests/test_api_application.py market_research/tests/test_futures_basis_statistics.py` | 50 passed; existing application/OpenAPI and Basis association regression |
| `npm test -- src/features/futures_calendar_spread src/features/calendar_spread_relative_value` | 76 passed in 9 files |
| `npm test -- src/app/App.test.tsx src/app/ApplicationShell.test.tsx src/app/Overview.test.tsx src/app/routes.test.tsx src/features/research_catalog/page/ResearchOverviewPresentation.test.tsx` | 55 passed in 5 files |
| `npx vitest run --config demo/build/vitest.config.ts demo/build/collector.test.ts demo/build/validate.test.ts demo/build/release.test.ts demo/build/runtime.test.ts` | 111 passed in 4 files, including controlled HTTP execution of all 6 Python Collector cases |
| `npm run contract:check` | All 9 generated contract pairs current |
| `npm run build`; `npm run lint` | PASS; existing large-chunk warning and two unrelated lint warnings retained |
| `poetry run mypy` over Calendar Spread Research, Statistics, both new HTTP packages and `ui_http/app.py` | No issues in 29 source files, including followed imports |
| `poetry run ruff check` on all 19 changed Python files relative to fetched Develop | Initial exit 1: 17 style/closure diagnostics in 3 WP6 test helpers; minimal test-only fixes committed in Source; recheck exit 0 |
| `poetry run pytest -q ui_web/tests/tooling/test_export_contracts.py` after those fixes | 7 passed |
| In-memory fixture regeneration and browser-service delegation check | All 14 fixture values equal committed JSON; no fixture writes or market access |
| `npm run demo:check`; `npm run demo:build` | 9 admitted; actual offline artifact built |
| `npm run demo:test:browser` | Installed Chromium PASS: 10 routes, exact captured values, both date axes, local interactions, history, no business/Auth network; shared Overview layout harness PASS |
| `npm run demo:release-check` on clean Source | PASS: Requirements, admission, public safety, offline build and Receipt verification |
| `node --input-type=module -e "import { verifyBrowser } from './demo/build/browserAcceptance.mjs'; await verifyBrowser()"` on the fresh Source gate artifact | PASS: 10 routes and Calendar Spread interactions/network isolation |

Source gate Artifact Receipt digest:
`f718c5e7acadec46c73cca7a7ccdee8a8b6f80be65cf8590712e7a608453fb35`
(5 artifact files). The post-closure gate generates a new source-bound Receipt;
its exact identity belongs to the final task report, not this earlier Source receipt.
Local detailed logs are retained in `/tmp/calendar-spread-final-evidence/` for this
session; generated gate/Receipt/browser evidence remains ignored under `.build/`.

### Dataset integrity and limits

Manifest SHA-256:
`5c26a15dd4465debe061403f797a65af36632a37fb49c0c44b2ae23a44e9db9b`.
Requirements SHA-256:
`558d4db4a5538e01f024a48e9daf91416073082d7eb8a752e5be7fed6288e7f0`.
Independent byte/hash comparison against WP6 `29736db` confirms all seven prior
Bundles unchanged. Admission verifies exactly nine canonical JSON Bundle files,
their exact hashes, Presets and formal Result associations under one Manifest.
Daily's six valid IM observations on 2026-09-30 equal Historical's current_day.
Each Pair retains 146 samples from 2026-03-02 through 2026-09-29. Stage counts,
genuine empty stages, Matching-stage/All-stages association and absent Histogram
agree with the earlier actual capture evidence. No HTTP recollection occurred.
Configured credential values were checked in memory and were absent from changed
files and the artifact; no secret values were emitted. No private-path/test-data
mislabeling was found in the new captures. Market caches and user configuration
were unchanged. No development history store was deleted.

Defer: real-market/provider authenticity and point-in-time metadata verification,
freshness, workload performance, UI refinement, Production Gateway and other
browsers/platforms. These are **NOT VERIFIED**, without fabricated PASS claims.
No new functionality, financial metric, distribution-authorization gate, release
workflow or Publication lifecycle was introduced. Main and release/demo-pages
remain at `5190d66ee8e5b47c14a59e447b4c4b8cdc9abbf5` during integration.
L1 is prepared to enter the existing Release Runbook on a later explicit request;
actual main promotion, publication, Actions/Pages and online acceptance are unrun.
