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
