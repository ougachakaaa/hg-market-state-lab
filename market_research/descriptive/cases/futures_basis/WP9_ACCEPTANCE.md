# WP9 integrated online acceptance — 2026-11-09

**WSL development scope PASS; overall WP9 PARTIAL. Windows Chrome and deployment
are NOT RUN.** This is execution evidence for [the online application](ONLINE_APPLICATION.md),
[HTTP contract](../../../../ui_http/products/futures_basis_research/http-contract.md)
and [Web consumer](../../../../ui_web/src/features/futures_basis_research/ARCHITECTURE.md),
not a new semantic contract. See [Roadmap](ROADMAP.md) for work-package ownership.

## Baseline and environment

- Repository: `ougachakaaa/hg-market-state-lab`.
- Branch: `feat/web-ui-workspace-redesign`; required/observed clean baseline:
  `1e02072c4b0dba09b90cdb2f8c1ffa37b169554d`.
- Final HEAD is the independent delivery commit containing this document; its SHA
  is reported with delivery. No branch creation, merge, push or deployment.
- WSL2 Linux `6.18.54.1-microsoft-standard-WSL2`; root `.venv` Python 3.13.15,
  Poetry 2.4.3, Node 22.23.2, npm 10.9.8, Chromium 156.0.8078.4.
- Real services started through `poetry run lab serve backend` and
  `poetry run lab serve frontend`, using free 8011/5173 ports. Existing unrelated
  listeners, including port 8101, were left running.
- Process environment selected isolated Auth DB, random signing key, Publication
  Root and `/tmp/wp9-20261109/real-runs`. Root/run directories have mode 0700,
  report files 0600, owned by the current user. One backend process at a time.
- `.env` and the user's Auth/Publication stores were not changed. Only the explicit
  candidate window's missing DataLake facts were acquired through Public Services;
  existing successful facts were not refreshed or rebuilt.
- Chromium required
  `LD_LIBRARY_PATH=/tmp/msl-playwright-libs/extracted/usr/lib/x86_64-linux-gnu`.
  An isolated Fontconfig file, `/tmp/wp9-20261109/fonts.conf`, included existing
  `/tmp/msl-fonts/extracted/usr/share/fonts/truetype/wqy`. DevTools confirmed actual
  WenQuanYi CJK glyph rendering. This proves the configured target environment;
  the application still depends on host CJK fonts online. Offline fonts remain embedded.

## Current real IM acceptance

The final browser attempt manually submitted exactly one POST through
Chromium → Vite same-origin proxy → authenticated FastAPI → Research → Run Store.
No market providers or facts were synthetic in this attempt.

```json
{
  "run_id": "9b5a3ee25fe71867b3c4aa46c5ac7d5c",
  "request": {
    "case": "futures_basis_v1",
    "product_code": "IM",
    "start_date": "2026-10-12",
    "end_date": "2026-10-23",
    "analysis_profile": "r01a_standard_v1"
  },
  "status": "COMPLETED",
  "result_available": true,
  "result_status": "complete",
  "created_at": "2026-11-09T08:46:47.152494Z",
  "started_at": "2026-11-09T08:46:47.158420Z",
  "finished_at": "2026-11-09T08:46:47.237918Z"
}
```

POST returned 202/PENDING; browser status reads observed RUNNING and COMPLETED.
Times above are UTC; the run completed at 16:46:47 Asia/Shanghai.
Report Profile: `futures_basis_report_evidence_v1`.
Input fingerprint:
`6facf8378a576eb914e8675dfa0d0c8ee54be356e21cabdc7c40d52bdce27154`.

| Input | Requested / successful units | Result |
| --- | --- | --- |
| CFFEX calendar | 12 / 12 natural dates | complete |
| SSE calendar | 12 / 12 natural dates | complete |
| IM futures | 10 / 10 product-days; 40 rows | complete |
| `000852.SH` index | 10 / 10 sessions | complete |

Preflight calendars had 0/12 success each, preventing Futures/Index planning.
Bounded public `lab datalake ensure` operations acquired the two calendars, IM and
the mapped index using the existing configured Provider. No full-history fetch,
alternate dataset, private storage read or source workaround was used.

There are 10 CFFEX candidates, 2026-10-12 through 2026-10-23, and 40 Slot-days.

| Slot | basis_value n | basis_ratio n | annualized_basis_ratio n |
| --- | --- | --- | --- |
| M0 | 10 | 10 | 9 |
| M1 | 10 | 10 | 10 |
| Q1 | 10 | 10 | 10 |
| Q2 | 10 | 10 | 10 |

One M0 expiry-day annualized outcome is not applicable; it is not a missing input
or execution failure. No unavailable/excluded observations or failed statistical
methods occurred. Four real Slot transitions on 2026-10-19 were displayed.
An independent call to the original public Observation/Report Python path produced
an exactly equal entire reader payload, including all 12 distributions and 18
comparisons. Its fingerprint also equals the historical short-window fingerprint;
the equality was checked against newly acquired facts, not inferred from history.

Real browser PASS: registration/operator approval/login, Workspace navigation,
six sections, producer-exact curves and events, four legends, actual mouse hover,
Zoom/Pan/Reset, requested versus candidate scope, reload, Back/Forward, independent
status/report read retries, empty browser storage and logout with subsequent 401.
There were zero JavaScript page errors. Console output retained expected anonymous
401, two deliberately injected network errors and existing Ant Design deprecations.
After an actual official-launcher backend restart, the same owner Cookie remained
valid, status was unchanged and the complete report JSON payload was identical.

An earlier harness attempt also completed real Run
`d2d96e6589454a4277853e362611f2a1`; its evidence is preserved separately.
The harness initially used a one-shot network fault consumed by React StrictMode's
discarded mount. It was corrected to keep the fault until the retry UI appeared,
then manually rerun in a new isolated Auth store. Neither browser attempt
automatically retried POST. The restart harness additionally needed to wait for
the old launcher child to stop listening before testing the new process.

## Synthetic gates, regressions and reconciliation

All results below were executed in this round using isolated test storage.

| Gate / check | Evidence and result |
| --- | --- |
| POSIX/platform/configuration availability, singleton lifetime and offline OpenAPI without store initialization | Current Research/HTTP tests PASS; unsupported capability simulation returns safe unavailable while sibling discovery remains available |
| Busy and invalid request | Current application/HTTP tests and Chromium PASS; rejected requests create no Run |
| Auth, owner isolation, malformed/unknown IDs | Current HTTP/Auth tests PASS; foreign and unknown IDs share the safe 404 contract |
| Actual process interruption and recovery | New `ui_http/tests/test_futures_basis_process.py` PASS: observe RUNNING, SIGKILL isolated synthetic uvicorn, restart same stores, observe INTERRUPTED; prior COMPLETED status/report survive unchanged |
| Lost POST response | Extended online Chromium test PASS: backend accepted a third synthetic Run, response dropped, previous report/URL retained, Run count remained exactly three after waiting; no automatic retry |
| Status/report read failures | Real browser injected transport faults; Retry status and Retry report each recover through reads, with exactly one POST in the final real attempt |
| Safe failure, corrupt/unsupported payloads and no-store | Current application/HTTP tests PASS, including report digest/association validation and denied interrupted reports; real HTTP records assert no-store |
| Partial/empty scientific findings | Current application/HTTP/hook tests PASS; additional real offline Chromium edge reports verify the same shared reader's all-null data, retained method failures and literal escaped text |
| Frontend | `contract:check`, `test` (32 files / 279 tests), `build`, `lint` PASS |
| Browser regressions | `test:futures-basis-online-browser`, `test:futures-basis-report-browser`, `test:auth-browser`, `test:research-browser` PASS |
| Python combined final run | `pytest ui_http/tests market_research/tests data_snapshot/tests/test_authority_topology.py ui_web/scripts/test_export_contracts.py`: 1749 passed, 1 existing platform skip |
| Static checks | `ruff check market_research ui_http ui_web/scripts` PASS; `mypy ui_http market_research/tests` PASS, 102 source files |

Reconciliation: no public API, HTTP DTO/OpenAPI, financial, scientific-status,
Run Lifecycle, authentication or Storage Authority changed. The initial Python
run had one test-only race: COMPLETED publication precedes worker permit release,
but the empty/oversize test immediately submitted again. The test now waits for
that worker's cleanup using an Event before its separate size-bound scenario.
It does not relax the Busy guard, lengthen an arbitrary sleep or redefine terminal
states. The new process regression covers actual OS process death, beyond the
existing in-process recovery simulations.

The lost-response browser extension initially had an ambiguous Ant Design `title`
selector when a value was already selected; it now targets the actual option.
These failed attempts and final passing logs remain available. Existing Plotly
bundle-size, Ant Design and FastAPI TestClient deprecation notices are not new
product defects. No unresolved semantic conflict was found.

## Evidence, deployment and remaining acceptance

External local artifacts are under `/tmp/wp9-20261109/`; they are disposable host
files, not committed publications or remotely durable evidence. Credential files
are outside `evidence/` and must not be included when sharing artifacts.

- `evidence/accepted.json`, `real-run-status.json`, `real-report.json`,
  `real-browser.json`, `real-restart.json`, `independent-comparison.json`.
- `evidence/real-overview.png`, `real-report.png`, `real-hover.png`.
- `evidence/independent-offline/` retains current canonical input bytes, original
  Python report payload, scientific results and associations for comparison.
- `evidence/synthetic-online/` contains screenshots and `http-evidence.json`,
  including lost-response acceptance and Run count.
- `evidence/offline-edges/{empty,failure}-browser/` contains screenshots and
  acceptance JSON. The normal offline regression is in
  `/tmp/r01a-offline-browser-ZZRt9d/`.
- `logs/pytest-final.log`, `process-restart-test.log`, `npm-*.log`,
  `browser-online-final.log`, `browser-{futures-basis-report,auth,research}.log`,
  `browser-offline-edges.log`, `ruff-final.log`, `mypy-final.log`.
- `logs/topology-final.log` records 21 passing topology/architecture tests after
  the final acceptance/navigation updates; `artifact-manifest.json` at the evidence
  root inventories shareable evidence files with sizes and SHA-256 digests.
- `initial-attempt/` retains the first real attempt's artifacts/logs; earlier
  failing Python/browser logs are also retained under `logs/`.
- External harnesses: `run-real.py`, `real-browser.mjs`, `restart-real.py`.
  They are evidence tooling, not new repository launchers or public commands.

**Windows Chrome: NOT RUN**, as selected for this round. Minimal manual procedure:

1. Start the existing backend/frontend commands on WSL using an isolated Auth DB,
   a persistent isolated Run Root and stable local signing key. For the retained
   real Run, use `/tmp/wp9-20261109/real-final-auth.sqlite3` and its original
   key/approved owner. The restricted `private-runtime.json` at that root retains
   the test key/password for local reproduction; do not share it. Configure
   `LAB_AUTH_ORIGIN=http://127.0.0.1:5173`; do not mix localhost and 127.0.0.1.
2. Open `http://127.0.0.1:5173/research/futures-basis` in Windows Chrome. Register,
   approve with `lab auth approve` against that isolated DB, and log in. An existing
   Run is readable only by its original owner; a new user cannot inherit it.
3. Select IM / 2026-10-12 / 2026-10-23 and Generate once, or open the retained
   owner URL `http://127.0.0.1:5173/research/futures-basis?run_id=9b5a3ee25fe71867b3c4aa46c5ac7d5c`.
4. Expect six readable Chinese report sections, four legends, actual hover details,
   transitions, working Zoom/Pan/Reset, and clearly distinct requested/candidate
   scope. Reload and Back/Forward must preserve the Run without new POSTs.
5. Logout must remove the report; reading its `/api/research/futures-basis/runs/<id>/report`
   endpoint then returns 401. Record Chrome version, console, screenshots and outcome.

**Nginx/Docker deployment: NOT RUN.** Docker is available but its container list
was empty; no controlled application gateway/deployment configuration was found,
and Nginx was unavailable. No containers or gateways were changed. Vite verified
SPA deep links, `/api/research/*` stripping `/api`, and Cookie/Origin forwarding.
Production still needs verified SPA fallback, equivalent API rewrite, HTTPS
Cookie/origin configuration and trusted proxy/entry limits under the existing
Auth deployment boundary. One backend process, an owned writable POSIX persistent
Run volume and stable Auth storage/key are prerequisites; multiple workers sharing
one Run Store remain unsupported. No deployment/SLA claim follows from this run.

All processes created for this round were stopped; isolated real stores and
evidence were retained. Windows acceptance is the remaining platform gap; production
deployment is a separate unexecuted boundary. No unresolved WSL functional blocker.
Recommendation: suitable for merging into `develop` for the accepted single-process
WSL development workflow, with these boundaries explicit; not a production or
Windows acceptance declaration. No merge was performed. Daily Data WP5, visual WP6,
Run History, new algorithms and automated deployment were not implemented.
