# D7 portfolio release acceptance

**Repository Release: PASS. Public Demo V2: PASS under the owner's updated distribution instruction.**
Executed 2026-11-13 Asia/Shanghai. This snapshot records the first successful V2 release;
subsequent documentation closure commits preserve the application/Example bytes. Final
closure HEADs and the latest workflow receipt are supplied in the delivery response;
a document cannot contain its own commit identity.

## Exact release identities

| Identity | SHA / evidence |
| --- | --- |
| Initial develop | `6e69f362110d2ee8415ca0efd5bde984df69d81e` |
| Initial main | `4c9fea7d99df7e9c8adc37b17298ee5572b02c4f` |
| Accepted candidate | `947f953b68984319ff540659308d14b37b33403b`, `release/portfolio-demo-v2` |
| Shipped develop | `4872508fb7b7f47b2d8f8977942246a3068c0e2c` — [PR #7](https://github.com/ougachakaaa/hg-market-state-lab/pull/7) |
| First shipped main | `94d03b3e5129104e76d67dabc6aab28a68ebcd99` — [Release PR #8](https://github.com/ougachakaaa/hg-market-state-lab/pull/8) |
| Candidate compatibility | [43413912521](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43413912521), all seven jobs PASS |
| Main Release PR compatibility | [43414905849](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43414905849), all seven jobs PASS |
| Exact main compatibility | [43415818397](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43415818397), all seven jobs PASS |
| Exact main build/deploy/online | [43415818422](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43415818422), reusable compatibility + release-build + deploy PASS |

Implementation commits: `b76308e`, `aa60e90`, `035f827`, `b6a20f1`, `947f953`.
Both PRs merged normally with expected-head checks. No force push, protection bypass,
Environment setting change or data cleanup occurred. Main/develop file trees were
identical at release. Public Source Code is the repository's main branch.

## Example inventory and admission

The [canonical owner decision](AUTHENTICITY.md#d7-user-directed-distribution-decision--2026-11-13)
superseded the original third-party-permission prerequisite. Publication Rights is
**USER_DIRECTED**, with third-party permission unverified; no permission PASS is claimed.
The [exact-result review](public/examples/evidence/review.md) and independently admitted
[public package](public/examples/package.json) bind the decision, reviewer/time,
producer revisions and complete result digests. Original private packages were not
modified. Packaging followed fresh MO Verify, Basis Verify/Replay, WP-A Verify, W2
Replay, SQLite Reader and current formal feature validation.

`P` = technical PASS; `U` = USER_DIRECTED distribution. Coverage retains producer gaps
and actual observations; request endpoints are not substituted for observed coverage.

| Example / actual scope | Real Source | Formal Producer | Contract / Identity | Coverage | Publication Rights | Public Data Safety |
| --- | --- | --- | --- | --- | --- | --- |
| MO Chain, 2026-11-11 close, 312 contracts / six expiries / four futures references | P | P | P | P | U | P |
| MO Premium Plane, same observation, 312 points / six expiries | P | P | P | P | U | P |
| IM Basis, 2026-01-01..11-11 request, 206 observed sessions from 01-05, six report sections | P | P | P | P | U | P |
| IM expiry-to-M1, same window / 206 sessions | P | P | P | P | U | P |
| IM expiry-to-Q1, same window / 206 sessions | P | P | P | P | U | P |
| Genuine Capability facade metadata, `not_probed`; no provider readiness claim | P | P | P | P | U | P |
| Genuine Trailing Return Publication, 000852.SH, H20/H60, four Analyses / six Views | P | P | P | P | U | P |

Daily Data landing adds links/descriptions, no financial Example. Public scope includes
embedded source-fact product projections, derived statistics, backtests, Visualization
Views, supported full Copy/JSON/CSV, Git repository and Pages. Original Raw captures,
Publication Source Evidence, Dataset caches, account details, tokens, private envelopes
and private paths are excluded. No backtest export feature was invented.

## Build and exact emitted bytes

Command: `cd ui_web && npm ci && npm run demo:build:public`.
Output: `ui_web/dist-demo-public/site`; asset base `/hg-market-state-lab/`;
default hash `#/research`. Private build/admission remains independent.
The static build/runtime needs no Python, Producer execution, acquisition, backend,
login or token. Separate compatibility jobs use the root Python environment.

Main validation toolchain: CPython **3.13.18**, Poetry **2.2.1**, Node **22.23.4**,
npm **10.9.9**. Local verification used Python 3.13.15 / Poetry 2.4.3 /
Node 22.23.2 / npm 10.9.8. Local and remote site inventories are byte-identical.
Playwright/Chromium identity is retained in browser `acceptance.json` and check logs.
Lockfile SHA-256: `poetry.lock` =
`ffc6965c476825d3855add25061d3a27b67d728fc7904256a0f4f58a13798b7b`;
`ui_web/package-lock.json` =
`0761c9fbf0208fb8828fb14cd3f40105d4d95a9df0a73088dcc4b4b0e92fe46f`.

Sorted site inventory digest:
`2f90512d62b67c6e4570d11bbfcdd66ca6480a3c0846e3d59d6c67204f1a7205`.
This is SHA-256 of the canonical sorted inventory, distinct from the uploaded ZIP hash.

| Emitted public file | Bytes | SHA-256 |
| --- | ---: | --- |
| `assets/index-D4ofWS-H.css` | 2,828 | `7b9fff409b4b0eaa892b9a8fa26c590503c109be3a1c1c8fefca832e1de40f5f` |
| `assets/index-KmBTUQwG.js` | 9,210,404 | `bfbfab9e9a5d3b1537cdf91cef4a5a066382a70e31ed493ba09ea5b3c2ee3396` |
| `index.html` | 592 | `5eb55562cea825df11af4fed174fde5fa2e7c0e2f30f2a8711f1bddffc674f7f` |
| `presentation-dependencies.json` | 5,231 | `6d3b2334abe588c6a3452ccc542ab9fce5a85fad0a0005c572e8b86c4353eef9` |

[Retained public build artifact](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43415818422/artifacts/14032356325)
contains `release.json`, site and local-browser evidence, expires 2027-02-11.
ZIP SHA-256: `17558d67b61346d1f3b37021ebc385a59b9121c5f8e94ef87dcdd162823fbcf5`.
Actual assets were scanned and reverified after transfer, then uploaded without rebuild
or mutation. PR jobs had no Pages/OIDC permissions. The protected deploy job alone had
them. Environment inspection confirmed custom branch-policy protection permitting main
and historical `feat/github-pages-demo`, with no required-reviewer rule; rules were
preserved. The new official workflow triggers only main.

## Actual public browser acceptance

**[Live Demo V2](https://ougachakaaa.github.io/hg-market-state-lab/#/research)**.
Actual public Chromium completed at **2026-11-13 19:25:52 Asia/Shanghai**.
Every public file returned HTTP 200 and matched the approved inventory before browser
checks. [Online evidence and screenshots](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43415818422/artifacts/14031873034)
are retained for 90 days. This is HTTPS Pages acceptance, not loopback-only evidence.

| Route | Online result |
| --- | --- |
| `#/research` | PASS: genuine Catalog and local Detail |
| `#/research/futures-basis` | PASS: all six sections, Slot and date-axis modes |
| `#/research/publications` | PASS: Publication, four Analyses, all six Views |
| `#/data` | PASS: overview and shared navigation |
| `#/data/mo-option-chain` | PASS: real points, expiry/strike selection, Hover, full Copy/Context/CSV/JSON |
| `#/data/mo-premium-plane` | PASS: selectors, Inspector, full Copy/Context/CSV/JSON |
| `#/backtesting` | PASS: M1/Q1, formal coordinates, date axes, Zoom/Pan/Reset and Evidence |

Root/unknown normalization, deep reload, Sidebar, breadcrumbs, Back/Forward and
1440/1024/390 containment passed. Bilingual disclaimer, portfolio identity and genuine
historical source/producer/result disclosure were visible. Corrupt digest injection
correctly refused rendering. Cookie and unexpected API/Auth/Provider/network/error
assertions passed. Static results never perform research or backtesting in the browser.

## Regression and recovery

Local Python: **3,766 passed / four platform skips**, using independent owning suites.
Full Vitest: **84 files / 610 tests PASS**. Contract freshness, Production/V1/public
builds, frontend lint, all owning Python Ruff/mypy scopes, topology/architecture,
actual public/private dependency graphs, tracked credentials/payloads, public asset
safety, diff review and actionlint passed. Production W1/W2 Chromium passed through
real FastAPI/Vite and controlled public-service fixtures. Private seven-page Chromium
and fresh real-result verification passed independently. Native Windows was not run.

A broad root pytest/mypy collection encounters pre-existing same-name test modules;
canonical independent suites pass. Optional `ruff check .` found eight existing issues
in untouched `ui_web/deploy/publish.py`; owning-module Ruff checks all pass. No broad
root-check PASS or unrelated warning-free claim is made. The existing Publication
HTTP 4 MiB verification limit remains unchanged; local Reader success for its larger
retained Source does not claim HTTP detailed-read success.

V1 recovery readiness: **PASS**. The independently reviewed synthetic rebuild is
committed as `futures_basis/rollback-v1.tar.gz`, with its full
[recovery inventory](futures_basis/rollback-inventory.json). Archive SHA-256:
`c3840dca3a94a3050530ac64ad27e239242bb0942e75edbde70a0acd2a3b5081`.
[Retained recovery artifact](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43415818422/artifacts/14031549184)
is available for 90 days; the committed archive survives that expiry. Eight V1 Chromium
groups and recovery URL-code-path checks passed locally. It is explicitly a reviewed
rebuild, not asserted identical to the prior deployed artifact. Automatic protected
recovery is wired and verifies restored bytes/behavior; no rollback was executed,
because V2 online acceptance passed.

Remaining engineering/deployment blockers: **none** for the updated user-authorized
scope. Third-party permission remains unverified, as recorded in the canonical decision;
this report does not invent clearance. This portfolio release is not a declaration
that the project has entered production data-retention status.
