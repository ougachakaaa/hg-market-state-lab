# D7-P readiness — 2026-11-13

Baseline `e3dce5ebfb48771941e8ac309c18af875d4b60e4`, branch
`feat/github-pages-demo`, initially clean. **Local D7-P engineering PASS; repaired remote CI NOT RUN; Public V2 Release BLOCKED.**
The two original remote failures remain recorded as FAIL, independent of local fixes.
No push, public release, Pages trigger change, merge, acquisition or retained-data
cleanup belongs to this work package. SQLite branch changes are not included.

[Release contract](RELEASE.md) owns future same-revision admission/deploy/rollback;
[authenticity](AUTHENTICITY.md) owns the six independent gates. This report owns
execution evidence and the readiness decision, without repeating D0–D6 history.

## Actual remote failure and CI repair

Reviewed [GitHub Run 43378105290](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43378105290),
for baseline e3dce5e, using actual job metadata and decoded failure logs:

| Actual job | Job ID | Original remote conclusion |
| --- | --- | --- |
| frontend | 131729259105 | FAIL: 593 assertions / 77 files passed, one uncaught error, exit 1; subsequent build/lint/static/safety steps SKIPPED |
| python (market_backtesting/tests) | 131729259473 | FAIL: 539 passed, one failure, missing `node_modules/.bin/vitest` |
| python (market_research/tests) | 131729259554 | PASS, including V1 fixture check |
| python (data_lake) | 131729259455 | PASS |
| python (data_snapshot/tests) | 131729259600 | PASS |
| python (ui_http/tests) | 131729259848 | PASS |
| python (ui_web/scripts) | 131729259523 | PASS |

The Backtesting test constructs genuine synthetic producer Views, then invokes the
canonical TypeScript validator from `ui_web` using its independent Node Vitest config.
The matrix had Python/Poetry but no npm dependencies. Only this collected suite now
conditionally runs setup-node 22 and `npm ci` in `ui_web`; the validator, executable,
working directory and assertions are unchanged. Research's Node-based report/browser
helpers are manual auxiliary scripts, not collected by `pytest market_research/tests`.
The other five Python suites require no npm installation for their collected tests.

The frontend failure is separate from missing dependencies. Its stack was
`Timeout → @rc-component/util/useDelayState → React dispatchSetState → window is not defined`,
attributed to `FuturesBasisPage.test.tsx`. Installed util 1.13.0 retained a delayed
update after consumer unmount; published 1.14.1 cancels pending timeout/RAF in effect
cleanup. The new test uses the actual public hook: schedule one delayed update,
unmount and assert zero outstanding timers. It fails against 1.13.0 (one timer remains)
and passes with 1.14.1, including after a clean install. Its fake clock is scoped and
restored inside that test. No copied hook, global timer drain, ignored exception,
new sleep, relaxed assertion or timeout increase was introduced.

**Repaired remote CI: NOT RUN.** No push or rerun was performed. Local PASS does not
change the original Run's FAIL. The five original remote successes are historical
results for e3dce5e, not verification of the updated lockfile.

## Dependency security disposition

Fresh pre-change `npm audit --json` reproduced three High / three Moderate affected
package entries, representing **21 distinct leaf advisories**. Vitest's aggregate
entry repeats its mocker dependency and is not a twenty-second advisory.

| Package / role and dependency path | Before | Fixed floor | Installed candidate | Application reachability / disposition |
| --- | --- | --- | --- | --- |
| Vite, direct dev tool | 8.3.0 | 8.3.3 | 8.3.3 | Dev-server file/editor middleware is relevant to developer exposure; it is not shipped as a static server. All six advisories patched. |
| Vitest, direct dev tool → mocker | 5.0.1 | 5.0.3 | 5.0.3, mocker/spy 5.0.3 | Browser mock registration/redirect attacks require the relevant exposed dev tooling; the suite uses Node/JSDOM run mode. Patched rather than dismissed as dev-only. |
| Ajv → fast-uri, runtime validator dependency | 3.1.8 | 3.1.9 | 3.1.9 | Generated schemas are embedded and controlled; the app does not accept user-supplied schemas or remote schema URLs. URI normalization bugs are still patched and all contract validators retested. |
| PostCSS/Vite and JSDOM/css-tree → source-map-js, dev | 1.2.1 | 1.2.2 | 1.2.2 | Malformed indexed maps target build/test parsing. Public/private outputs have no source maps; developer input-chain risk is nevertheless patched. |
| JSDOM → undici, dev | 8.10.2 | 8.12.2 | 8.12.4 | No untrusted external resource loading is enabled in these JSDOM tests; Chromium and Python have separate network stacks. Compatible 8.12 patch selected by normal resolution, all eight advisories patched. |
| Ant Design/icons → rc util, runtime | 1.13.0 | 1.14.1 for this fix | 1.14.1 | Actual delayed React update survives unmount in the old hook; upstream cleanup fix and failing-before/passing-after regression confirmed. Not an npm advisory. |

The following rows are individually FIXED in the local candidate. Each GHSA link
is the advisory evidence; affected ranges are from the retained npm audit response.
Group role/path/reachability and fixed versions are defined above, including Windows
and developer-host exposure; none is silently waived.

| Package | Advisory | Severity | Affected range | Local status |
| --- | --- | --- | --- | --- |
| @vitest/mocker | [GHSA-qxg6-89mg-rqv8](https://github.com/advisories/GHSA-qxg6-89mg-rqv8) — Vitest: Code injection via unauthenticated manual mock registration | moderate | `>=5.0.0-beta.1 <5.0.3` | FIXED |
| @vitest/mocker | [GHSA-xp26-3454-mjgp](https://github.com/advisories/GHSA-xp26-3454-mjgp) — Vitest: Windows backslash traversal bypasses the @vitest/mocker redirect allowlist fix | moderate | `>=5.0.0-rc.2 <5.0.3` | FIXED |
| fast-uri | [GHSA-w74x-v6f9-j3xg](https://github.com/advisories/GHSA-w74x-v6f9-j3xg) — fast-uri vulnerable to URI scheme spoofing via percent-encoded scheme decoding | moderate | `>=3.0.0 <3.1.9` | FIXED |
| fast-uri | [GHSA-xhq7-xmqj-769h](https://github.com/advisories/GHSA-xhq7-xmqj-769h) — fast-uri vulnerable to improper path equivalence in relative reference normalization | low | `>=3.0.0 <3.1.9` | FIXED |
| fast-uri | [GHSA-wjr9-j795-jxcr](https://github.com/advisories/GHSA-wjr9-j795-jxcr) — fast-uri vulnerable to host confusion via unchecked WHATWG host canonicalization | moderate | `>=3.1.3 <3.1.9` | FIXED |
| fast-uri | [GHSA-333x-w4r6-6crp](https://github.com/advisories/GHSA-333x-w4r6-6crp) — fast-uri vulnerable to scheme injection via an unescaped first-segment colon in suffix references | low | `>=3.0.0 <3.1.9` | FIXED |
| source-map-js | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) — source-map-js allows event-loop denial of service through indexed source-map section offsets | high | `>=1.0.0 <1.2.2` | FIXED |
| undici | [GHSA-4qv8-2p9j-2685](https://github.com/advisories/GHSA-4qv8-2p9j-2685) — undici vulnerable to Denial of Service via unbounded memory in the EventSource parser | moderate | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-f72v-6w45-q472](https://github.com/advisories/GHSA-f72v-6w45-q472) — undici vulnerable to Subresource Integrity bypass via non-lowercase algorithm tokens | moderate | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-xjj6-f33q-929c](https://github.com/advisories/GHSA-xjj6-f33q-929c) — undici vulnerable to Denial of Service via unhandled error on excessive content-encodings | high | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-4w7w-5xrc-9h26](https://github.com/advisories/GHSA-4w7w-5xrc-9h26) — undici vulnerable to cache poisoning and cross-user disclosure via cross-origin redirects | high | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-2m5v-pch6-74hx](https://github.com/advisories/GHSA-2m5v-pch6-74hx) — undici vulnerable to TLS certificate validation bypass via dropped tls options in Agent | high | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-qrxm-fqhp-jwvm](https://github.com/advisories/GHSA-qrxm-fqhp-jwvm) — undici vulnerable to Denial of Service via TLS 1.2 certificate-changing renegotiation | high | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-9fm3-97px-rjf6](https://github.com/advisories/GHSA-9fm3-97px-rjf6) — undici WebSocket client vulnerable to Denial of Service via unbounded automatic PONG buffering | moderate | `>=8.0.0 <8.12.2` | FIXED |
| undici | [GHSA-55wc-3pg8-jfw6](https://github.com/advisories/GHSA-55wc-3pg8-jfw6) — undici vulnerable to Denial of Service via unhandled exception in the decompress interceptor | moderate | `>=8.0.0 <8.12.2` | FIXED |
| vite | [GHSA-698v-4r3x-3vcv](https://github.com/advisories/GHSA-698v-4r3x-3vcv) — launch-editor: escapeCmdArgs() omits % escaping on Windows | moderate | `>=8.3.0 <=8.3.2` | FIXED |
| vite | [GHSA-r825-w8mm-5pxw](https://github.com/advisories/GHSA-r825-w8mm-5pxw) — launch-editor: Editor CLI flag misinterpretation causing arbitrary command execution for some editors | moderate | `>=8.3.0 <=8.3.2` | FIXED |
| vite | [GHSA-587h-7wmj-h5pm](https://github.com/advisories/GHSA-587h-7wmj-h5pm) — launch-editor: `fs.existsSync()` existence check can be bypassed on Windows | high | `>=8.3.0 <=8.3.2` | FIXED |
| vite | [GHSA-9jrq-w75r-8gcw](https://github.com/advisories/GHSA-9jrq-w75r-8gcw) — Vite: Cross origin script execution through Vite custom middleware | low | `>=8.3.0 <=8.3.2` | FIXED |
| vite | [GHSA-rq7h-c2jc-7f22](https://github.com/advisories/GHSA-rq7h-c2jc-7f22) — Vite: Files outside `server.fs.allow` could be served when project paths match system paths on non-Windows machine | moderate | `>=8.3.0 <=8.3.2` | FIXED |
| vite | [GHSA-vfpm-58rq-9qcg](https://github.com/advisories/GHSA-vfpm-58rq-9qcg) — Vite: First 4 bytes of files outside of `server.fs` setting is exposed by `?vite-wasm-instance` | moderate | `>=8.3.0 <=8.3.2` | FIXED |

Post-upgrade audit: **0 known vulnerabilities**, including after standard npm 10
`npm ci`. No retained High/Moderate exception is required. This is a dated registry
result for the candidate, not a guarantee of absence of vulnerabilities or a claim
that the unchanged deployed V1 has been patched.

Only Vite/Vitest minimum versions change in package.json; React, Ant Design, Ajv,
JSDOM, Playwright, formulas and result schemas do not change. Vite requires a newer
compatible Rolldown patch/native bindings, and Vitest updates its matching mocker/spy
and diagnostic dependencies. Normal transitive resolution also updates compatible
mapping/URI packages; no overrides, new runtime framework or peer-check bypass was
added. The rc util and URI fixes stay within the existing parent ranges.

Npm 10.9.8 and 10.9.9 hit an Arborist `edgesOut` internal error while updating Vitest's
peer graph, also with lock-only resolution. Clean-installing the old lockfile permitted
the separate Vite update but did not fix Vitest resolution. Npm **11.21.2**, invoked
through npx without changing the global/project npm requirement, resolved the new
lockfile normally. No `--force` or `--legacy-peer-deps` was used. The resulting lockfile
is independently installed by the original npm **10.9.8** and all checks use that clean
installation; the temporary resolver is not a CI prerequisite.

Local toolchain: Python **3.13.15**, Node **22.23.2**, npm **10.9.8**, Poetry **2.4.3**,
NumPy **2.5.3**, Pydantic **2.13.5**, FastAPI **0.141.1**, pytest **8.4.2**.
CI keeps Python **3.13**, Node **22**, Poetry **2.2.1**. The actual original remote
frontend used Ubuntu **26.04.1**, Python **3.13.18**, Node **22.23.4**, npm **10.9.9**.
The upgraded undici requires Node >=22.19.0, satisfied locally and by that remote
Node 22 runner. Local and remote patch versions are explicitly different.

## Local verification matrix

Python tooling runs from repository root; npm commands run in `ui_web`. Exact output,
exit codes, before/after audits, tool versions and remote failure extracts are retained
outside Git. No skipped job or nonzero exit is treated as PASS.

| Command / gate | Actual local result |
| --- | --- |
| Original failing Backtesting validator test, `poetry run pytest market_backtesting/tests/test_result_v2_contract.py::test_generated_views_pass_canonical_frontend_validator -q` | PASS before dependency upgrade; final matrix repeats the same test after upgrade |
| `poetry run pytest market_backtesting/tests -q` | PASS: 540 |
| `poetry run pytest market_research/tests -q` | PASS: 1280, one existing platform skip |
| `poetry run pytest data_lake -q` | PASS: 686 |
| `poetry run pytest data_snapshot/tests -q` | PASS: 287 |
| `poetry run pytest ui_http/tests -q` | PASS: 589 |
| `poetry run pytest ui_web/scripts -q` | PASS: 15 |
| `poetry run python market_research/scripts/futures_basis_demo_fixture.py --check` | PASS; original fixture unchanged |
| `poetry run ruff check market_backtesting` / `poetry run mypy market_backtesting` | PASS / PASS: 50 source files |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | PASS: 23; final documentation check repeated before delivery |
| New lifecycle test against old/new dependency | Expected FAIL before; PASS after, also clean-install focused suite 9/9 |
| `npm ci` | PASS with unchanged default npm 10.9.8; zero audit findings |
| `npm run contract:check` | PASS: all seven generated boundaries current |
| `npm run build` / `npm run lint` | PASS / PASS |
| `npm run demo:build` | PASS: public V1 Synthetic, fixed Pages base |
| `npm run test:static-compatibility` | PASS: actual V1/private module graphs and exhaustive route typing |
| `npm run test:public-safety` | PASS; tracked payload/credential and actual V1 artifact guards |
| Complete Vitest repeat 1 | PASS: 594 tests / 78 files, 230.40s, no reported unhandled errors |
| Complete Vitest repeat 2 | PASS: 594 tests / 78 files, 233.53s, no reported unhandled errors |
| Actionlint on both workflows / full Git diff check | PASS / PASS |
| Original-input offline verification / new private build / Chromium | PASS / PASS / PASS |

The original [WP-C report](WP_C_ACCEPTANCE.md) transposed the Snapshot/Backtesting
counts. Its retained raw logs prove 287/540 respectively; the table now has an explicit
D7-P erratum. This run independently reproduces both counts and does not invent a new
historical execution. The initial remote frontend failure also confirms that WP-C's
local zero-error repeats could not establish remote reliability; this task fixes the
upstream mechanism instead of reclassifying that failed run.

Compatibility retains independent Python processes, fail-fast false, normal failure
exit codes, per-job 20-minute limits and frontend file isolation/default deadlines.
There is no continue-on-error, token, acquisition, private-directory prerequisite,
private upload or test-data promotion. Dependency caching is not used to replace
installation or validation. Pages deploy remains a distinct unchanged V1 workflow.

## Private technical reproduction and current public V1

Use the existing external R2/R3/WP-A handoffs for input locations. Required operations:

```bash
# repository root; PRIVATE_R3 is the package containing delivery/
poetry run python ui_web/scripts/private_mo_examples.py verify --output "$PRIVATE_R2"
poetry run python market_research/scripts/futures_basis_report.py verify "$PRIVATE_R3/delivery"
poetry run python market_research/scripts/futures_basis_report.py replay "$PRIVATE_R3/delivery"
poetry run python ui_web/scripts/private_wpa_examples.py verify --output "$PRIVATE_WPA"
poetry run python ui_web/scripts/private_wpa_examples.py replay-w2 --output "$PRIVATE_WPA"
# ui_web; all output arguments must be fresh absolute external paths
npm run demo:build:private -- --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" --output "$NEW_PRIVATE_BUILD"
npm run test:private-demo-data -- --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" --output "$NEW_PRIVATE_NEGATIVES"
npm run test:private-demo-browser -- --build "$NEW_PRIVATE_BUILD" --evidence "$NEW_PRIVATE_BROWSER" --r2 "$PRIVATE_R2" --wpa "$PRIVATE_WPA"
```

All five formal Verify/Replay operations PASS, including guarded W2 reproduction.
New private build from committed code `39a5f467ff1a8fb5c062137c32a7cc02018464d6`
PASS; all selected Example identities equal the accepted WP-C identities. The final
report commit changes documentation only. Nineteen private admission negative probes
PASS. Actual Chromium **156.0.8078.4** PASS: seven routes, 11 acceptance groups,
21 viewport screenshots plus the corrupt-digest error screenshot, nine local static
requests, zero browser errors and zero warnings. Screenshots at desktop and narrow
widths were also inspected. The gate verifies all formal Presentations, M1/Q1,
Publication/Analysis/View association, full Raw/Context JSON and exact CSV bytes after
local filters, genuine chart interaction, navigation, loading and fail-closed errors.
No Auth/API/Provider/XHR/fetch, unexpected origins or cookies are admitted. The real
Publication has one page; pagination bounds are tested and multi-page behavior remains
covered separately by existing synthetic contract tests, not fabricated market records.

Final independent scan verifies every private emitted file against its admission hash,
no credentials/private/source paths/maps, no complete original Publication Source in
JS, and no private identity digests in any of the four actual V1 public files. The
original fixture and Pages workflow are byte-identical to baseline. No package/result/
evidence is replaced, no acquisition is requested and no synthetic fallback is used.
Formal replay is admission verification before static bundling, not browser financial
calculation. The 8,297,891-byte Publication Source still exceeds the unchanged 4 MiB
HTTP detailed-read verification budget; safe Python static-reader PASS is not a claim
that Production HTTP Analysis/View supports this object (expected 503). No capacity or
storage redesign was made.

Existing [public V1 URL](https://ougachakaaa.github.io/hg-market-state-lab/) returned
HTTP 200, as did its HTML-linked JS/CSS assets, on 2026-11-13. That read-only HTTP check
is not a V2 browser/deployment acceptance and does not update the live site. Current
V1 deploy trigger and `ui_web/dist-demo` upload root remain unchanged. Dependency
updates affect the new local candidate; no public redeployment occurred.

## Rights review and exact public admission

Reviewer: Codex; review date: **2026-11-13 Asia/Shanghai**. Re-read official
[Tushare service agreement, II(2)(5)](https://tushare.pro/document/1?doc_id=405),
[user agreement](https://tushare.pro/document/1?doc_id=409) and
[access/entitlement table](https://tushare.pro/document/1?doc_id=290).
Retrieval timestamps and SHA-256 identify the retained versions; no explicit effective
version date was found. The service text grants personal viewing/use scope, without
an evidenced license for this repository/Pages redistribution. Access tiers establish
API access, not permission for the intended public output. The user agreement's brand
conditions also need consideration when agreeing attribution/presentation conditions.
No account-specific permission or upstream exchange/index redistribution clearance was
provided. This is an evidence gap/BLOCKED finding, not a legal infringement verdict.

`B` = BLOCKED, exact proposed public output/channel not cleared. `N/A` = not a supported
output of that feature, not a waiver for underlying facts. Raw inputs are privately
retained; a B in that column does not mean they are bundled. ChartViews and embedded
JSON are publicly retrievable data even without a visible Download button.

| Required Example | Raw/source facts | Provider/identity metadata | Derived statistics/performance | ChartView data | Complete Copy/JSON/CSV | GitHub repository | Public Pages |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MO Option Chain | B | B | N/A | B | B | B | B |
| MO Premium Plane | B | B | B | B | B | B | B |
| Historical Basis | B | B | B | B | B for embedded/readable result; no invented export feature | B | B |
| W2 M1 | B | B | B | B | B for embedded Result; no new CSV/Copy feature | B | B |
| W2 Q1 | B | B | B | B | B for embedded Result; no new CSV/Copy feature | B | B |
| Research Publication/Analysis | B | B | B | B | B for embedded reader data; original Source excluded | B | B |
| Capability Catalog / presentation metadata | N/A | No provider facts; repository-authored text has limited license basis | N/A | N/A | Exact new package B | B for new package | B for new package |

R1's limited PASS for repository-authored Capability descriptions under the root
[AGPL-3.0 license](../../../LICENSE) is retained as a copyright/licensing basis, not
silently revoked and not promoted into public admission of this new package. Metadata
must still be reviewed for precise contents, license obligations, attribution and the
intended channels. Source licensing never relicenses market facts. Existing V1 remains
an independently synthetic, previously public artifact; no real V2 Example is newly
approved by this report.

For the retained private results, Real Source/Formal Producer/Contract-Identity/Coverage
have technical evidence, subject to their formal fresh verification. Publication Rights
remain BLOCKED. Public Data Safety for a future exact V2 artifact is BLOCKED until that
artifact and its reviewed rights bindings exist; private isolation or V1 safety PASS
cannot substitute. Personal/noncommercial purpose, processing, attribution or public
availability alone does not clear any B above.

## Final D7 execution instructions — future, not executed here

The [release contract](RELEASE.md) fixes the dependency and approval boundaries. Execute
these steps only in a separately approved D7 package, in this order:

1. Obtain written permission covering each source/output and both repository and Pages
   channels, full embedded/downloadable JSON/CSV, derived metrics/backtests/Views,
   attribution/brand conditions, expiry and any upstream-rights limits. Record the
   actual license/evidence, permitted scope, reviewer/time and each of six gate results.
   Unresolved rights stop full V2; do not change values, hide origin or replace it with
   Synthetic or a reduced page set.
2. Admit the exact cleared seven-page Example set through a reviewed public package
   and separate public admission entry reusing the existing Presentations. Preserve
   original identities, request dates/windows, coverage, complete Results and digests.
   The public V2 loader/build/admission gate is **not implemented by D7-P**; it cannot
   be obtained by copying the private build or flipping its rights fields.
3. Implement compatibility as a reusable validation workflow and the main release
   workflow with explicit same-SHA `needs` dependencies, followed by public admission,
   build, complete asset scanning and local browser checks. Keep untrusted PR jobs
   unprivileged. Define a distinct public V2 output/upload root and explicit guard;
   do not weaken the existing V1 fixture guard, which deliberately rejects V2 inputs.
4. Prepare the release receipt: exact source SHA/revision, lockfile digests, toolchain,
   Example/result digests, review bindings and full file-size/SHA-256 inventory. Retain
   and verify the previous approved V1 rollback artifact plus its deployment identity;
   if unavailable, rebuild its cleared revision and independently review that recovery
   artifact. Current HTTP availability alone is not a ready rollback package.
5. Land the reviewed candidate via develop, perform Release Review, then merge the
   approved release to main. Only this separate D7 change switches the Pages trigger
   from the feature branch to main and reconciles the github-pages Environment's main
   branch/reviewer protection. Re-run every required gate on the actual main revision;
   prior branch/PR success is not a substitute. Approval is bound to that exact artifact.
6. Upload the verified inventory without a rebuild/mutation and deploy using scoped
   Pages/OIDC permission. Record actual run, artifact, deployment and URL. Validate
   `https://ougachakaaa.github.io/hg-market-state-lab/#/research` and every route in
   `workspaceRoutes`: base-path assets, normalization, deep reload, navigation,
   disclosures, controls/charts, full exports and absence of business network/cookies
   or unhandled errors. Only actual public acceptance can establish V2 availability.
7. On pre-upload failure stop without deployment. On post-deploy acceptance failure,
   restore the preverified previous artifact through the protected workflow, verify
   its public assets/behavior and record failed candidate plus recovery deployment.
   A restored V1 is explicitly V1, never a passing substitute for full real-market V2.

This preparatory work leaves no usable public V2 package or executable public V2
cutover pipeline while rights are blocked. Release architecture is specified; actual
public implementation, review and cutover remain D7 work. No project production
announcement is inferred; the user's pre-production retention policy remains in force.

## Remote verification handoff and human decisions

No new remote run is authorized/performed in D7-P. To validate later without invoking
the existing feature-branch V1 deploy, obtain explicit authorization for this concrete
CI-only procedure:

```bash
# From the final reviewed D7-P HEAD; no merge or force push
# Execute only after separate authorization:
git push github HEAD:refs/heads/ci/d7-p-validation
```

Create a draft PR with base `feat/github-pages-demo`, head `ci/d7-p-validation` using
[the comparison page](https://github.com/ougachakaaa/hg-market-state-lab/compare/feat/github-pages-demo...ci/d7-p-validation?expand=1).
The existing `pull_request` event runs compatibility, while Pages' push-to-Demo event
is not invoked. Do not merge the PR. Record candidate HEAD, actual checkout/PR merge
SHA, base revision, Run URL and every job conclusion; a changed base requires explicit
reconciliation. Inspect all seven jobs and all frontend downstream steps, not just
assertion totals. Any failed/unhandled/skipped required check prevents Remote CI PASS.
Alternatively, pushing the Demo branch itself needs explicit authorization acknowledging
that it also redeploys current V1; this task does neither.

Human decisions still required: authorize a remote validation route; supply/obtain and
review missing source/output/channel permissions; approve the exact future public
artifact and protected main cutover/recovery plan. No outward authorization request is
sent. Full D7 Public Release remains BLOCKED without these prerequisites.

### Optional authorization-request draft — not sent

拟向数据提供方申请书面确认：本项目为个人非商业作品集，拟在上述 GitHub 仓库和
Pages 地址公开展示固定历史窗口的七页面结果。请分别确认 MO 完整期权链及 Premium
数据、IM/指数/日历及元数据、Basis 统计、M1/Q1 回测、Publication/ChartViews 的展示、
仓库再分发及完整 JSON/CSV 复制下载是否获准；浏览器内嵌数据即使无下载按钮仍可提取。
请明确允许的范围、署名/品牌条件、有效期、撤回及留存要求，及是否需要交易所、指数
提供方等另行授权或能由贵方转授权。原始账户、Token、缓存和私有 Source Evidence 不拟
公开。收到并完成逐项审查前不发布真实市场 V2。此草稿不表示已有许可，也未经发送。

## Final readiness decision and delivery

| Question / boundary | Decision |
| --- | --- |
| Seven-page shared architecture / complete formal retained evidence | PASS |
| Private reproduction, contracts, local CI command matrix and safety | PASS |
| Dependency advisories in the clean local candidate | PASS: zero currently reported; all 21 original leaf advisories patched |
| Original GitHub Run | FAIL: Frontend and Backtesting jobs |
| Updated remote CI closure | NOT RUN: no authorized push; cannot declare remote engineering closure |
| Current public V1 local build / HTTP availability | PASS within the checks recorded above; no new deployment |
| Release architecture / approval and rollback design | PASS as the documented contract and execution plan |
| Actual public V2 package, public loader/build/gate, protected main release implementation | BLOCKED pending the separately approved D7 work and asset admission; not implemented here |
| Exact public V2 rights/admission / Pages cutover | BLOCKED |

Known Ant Design List deprecation remains a development diagnostic, not a suppressed
error or an npm advisory; actual production private Chromium recorded zero warnings.
Vite chunk-size and existing Starlette/httpx deprecation warnings remain informational.
No zero-warning or zero-vulnerability claim is made for unrelated/deployed environments.

Commit list:

- `27de5dccf29685cd9f44180399f044df5ef35439` — conditional CI dependency repair.
- `39a5f467ff1a8fb5c062137c32a7cc02018464d6` — patched dependencies and real lifecycle regression.
- Final documentation commit — `docs(demo): complete d7 release readiness assessment`.

The final commit contains this readiness evidence, release contract/navigation and the
explicit WP-C count erratum. All source/runtime changes are in the two commits above.
Final HEAD is supplied in the delivery response and external D7-P handoff; the commit
containing this report can be obtained with `git log -1 --format=%H -- ui_web/src/demo/D7_READINESS.md`.
No engineering PASS is intended to mean remote CI or Public V2 Release PASS.
