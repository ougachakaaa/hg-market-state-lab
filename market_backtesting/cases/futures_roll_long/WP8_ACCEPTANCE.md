# WP8 real IM acceptance — 2026-11-12

**WP8 PASS. W2 complete within its declared scope; ready for merge review.**
Real-market, HTTP/Auth, Windows Chrome, controlled recovery/privacy and regression
gates passed. No blocking implementation drift remains. This task does not merge branches.

This is execution evidence, not a financial or workflow authority. Semantics remain in
[Inputs](INPUTS.md), [Strategy](STRATEGY.md), [Performance](PERFORMANCE.md),
[Result](RESULT.md), [Evidence](EVIDENCE.md) and [Online application](ONLINE_APPLICATION.md).
[Roadmap](ROADMAP.md) owns release readiness; [Reconciliation](RECONCILIATION.md) owns drift.

## Environment and exact request

- Baseline: `477e759ad647c95941ce4a010253eb31f480160a`; branch `feat/w2-position-driven-core-reconciliation`. Initial HEAD matched and worktree was clean.
- WSL2 Linux `6.18.58.1-microsoft-standard-WSL2`, Ubuntu 22.04.5; root Python 3.13.15 / Poetry 2.4.3; Node 22.23.2 / npm 10.9.8.
- Actual visible **Windows** Chrome 157.0.8103.39, driven by Windows Node 22.23.2 with Playwright; screenshots are from Windows Chrome, not Linux Chromium.
- IM, inclusive request `2024-01-01` → `2026-10-30`, `expiry_to_M1_v1` and `expiry_to_Q1_v1`; no benchmark override. Public Futures rows resolved CSI 1000 / `000852.SH`.
- Isolated Auth database, random test credentials, independent POSIX Backtesting/Research Run roots, and fresh isolated DataLake storage. No existing auth database or default market cache was used, modified or deleted.
- Only the test harness redirects Dataset factory storage placement, following the existing WP3 real acceptance pattern. Real public factories, provider acquisition, service operations, worker, FastAPI/Auth, Vite and React/Plotly remain active. No fake service, synthetic fact, private SQLite query or provider-client access supplies market facts.

## Real acquisition and input identity

Initial read-only Preflight: CFFEX 0/1,034 successful natural-day units; Futures unknown
(`calendar_target_unknown`), Index unknown (`underlying_unknown`). Separate SSE public
Calendar export was 0/1,034. No database was created by these read-only operations.
The formal Python Run ensured missing inputs; final Preflight was ready=true.

| Public input | Export schema | Final successful / requested | Missing / pending / failed |
| --- | ---: | ---: | --- |
| CFFEX Calendar | 1 | 1,034 / 1,034 natural days | 0 / 0 / 0 |
| IM Futures Daily | 2 | 683 / 683 product-days | 0 / 0 / 0 |
| SSE Calendar prerequisite | 1 | 1,034 / 1,034 natural days | 0 / 0 / 0 |
| CSI 1000 Index Daily | 1 | 683 / 683 index-days | 0 / 0 / 0 |

Sources: Tushare through `tushare_trade_calendar/calendar`,
`tushare_equity_index_futures/futures_daily`, `tushare_index_daily/index_daily` public
Application Services. SSE remains an auxiliary prerequisite, not a fourth fingerprint member.

The retained Futures export contains 2,732 real contract-day rows; Index contains
683 rows. Both index endpoint closes are 5,854.7494 / 6,161.2275.
All Python, HTTP and Windows browser executions retained the same canonical identity:

```text
input_profile = futures_roll_long_inputs_v1
input_fingerprint = b83a38c9bdc83f082eda87e93c1babdb9950dacad1e316b4186a2e07e0ef557c
result_profile = futures_roll_long_result_v1
definition_version = futures_roll_long_definition_v1
```

Complete ordered CFFEX sessions, aligned Index closes, complete active contract sets,
consistent lifecycle/multiplier metadata and finite positive prices passed the producer
input/result validators. Cache completeness does not establish Source freshness or
historical point-in-time metadata availability.

## Financial and execution evidence

Both observed windows are **2024-01-02 → 2026-10-30, 683 CFFEX sessions**.
Initial index-equivalent notional is CNY **1,170,949.88**; entry multiplier is 200.
Both enter the actual first-session M1 `IM2402.CFX` at 5,810.6 and finish Flat.
Numeric summaries below format producer output for reading; retained JSON keeps full binary64 values.

| Metric | M1 | Q1 |
| --- | ---: | ---: |
| Total PnL (CNY) | 499,440.00 | 489,040.00 |
| Gross return | 42.6525514482% | 41.7643836302% |
| Benchmark return | 5.2346920263% | 5.2346920263% |
| Excess return | 37.4178594220% | 36.5296916039% |
| Strategy max drawdown | -27.9089656681% | -27.9089656681% |
| Benchmark max drawdown | -31.2013426733% | -31.2013426733% |
| Execution legs | 68 | 24 |
| Rolls | 33 | 11 |

Financial consistency: **PASS**. Producer validation checks every daily Core PnL,
cumulative PnL, equity, daily/cumulative return and Analyzer benchmark/excess/drawdown
projection, chronological accumulation, summary association, executions and V2 data.
Offline replay rebuilds the full daily state/event chain. Initial M1 and expiry targets
use the existing W1 resolver; holding identity remains the real contract. Each observed
roll matches the retained actual delist date and both real Close prices. Old-contract
PnL precedes closure; the replacement reference uses its own Close, excluding the roll gap.
No production calculation or financial oracle changed.

### Actual rolls

Every row below is an actual expiry close/open pair. Prices and all individual legs
are retained in external result/evidence JSON; the tables record identity and dates.

**expiry_to_M1_v1**

| Session | Old contract | New contract |
| --- | --- | --- |
| 2024-02-19 | IM2402.CFX | IM2403.CFX |
| 2024-03-15 | IM2403.CFX | IM2404.CFX |
| 2024-04-19 | IM2404.CFX | IM2405.CFX |
| 2024-05-17 | IM2405.CFX | IM2406.CFX |
| 2024-06-21 | IM2406.CFX | IM2407.CFX |
| 2024-07-19 | IM2407.CFX | IM2408.CFX |
| 2024-08-16 | IM2408.CFX | IM2409.CFX |
| 2024-09-20 | IM2409.CFX | IM2410.CFX |
| 2024-10-18 | IM2410.CFX | IM2411.CFX |
| 2024-11-15 | IM2411.CFX | IM2412.CFX |
| 2024-12-20 | IM2412.CFX | IM2501.CFX |
| 2025-01-17 | IM2501.CFX | IM2502.CFX |
| 2025-02-21 | IM2502.CFX | IM2503.CFX |
| 2025-03-21 | IM2503.CFX | IM2504.CFX |
| 2025-04-18 | IM2504.CFX | IM2505.CFX |
| 2025-05-16 | IM2505.CFX | IM2506.CFX |
| 2025-06-20 | IM2506.CFX | IM2507.CFX |
| 2025-07-18 | IM2507.CFX | IM2508.CFX |
| 2025-08-15 | IM2508.CFX | IM2509.CFX |
| 2025-09-19 | IM2509.CFX | IM2510.CFX |
| 2025-10-17 | IM2510.CFX | IM2511.CFX |
| 2025-11-21 | IM2511.CFX | IM2512.CFX |
| 2025-12-19 | IM2512.CFX | IM2601.CFX |
| 2026-01-16 | IM2601.CFX | IM2602.CFX |
| 2026-02-24 | IM2602.CFX | IM2603.CFX |
| 2026-03-20 | IM2603.CFX | IM2604.CFX |
| 2026-04-17 | IM2604.CFX | IM2605.CFX |
| 2026-05-15 | IM2605.CFX | IM2606.CFX |
| 2026-06-22 | IM2606.CFX | IM2607.CFX |
| 2026-07-17 | IM2607.CFX | IM2608.CFX |
| 2026-08-21 | IM2608.CFX | IM2609.CFX |
| 2026-09-18 | IM2609.CFX | IM2610.CFX |
| 2026-10-16 | IM2610.CFX | IM2611.CFX |

Final exit: 2026-10-30, SELL `IM2611.CFX` at 6130.0; no replacement or subsequent position.

**expiry_to_Q1_v1**

| Session | Old contract | New contract |
| --- | --- | --- |
| 2024-02-19 | IM2402.CFX | IM2406.CFX |
| 2024-06-21 | IM2406.CFX | IM2409.CFX |
| 2024-09-20 | IM2409.CFX | IM2412.CFX |
| 2024-12-20 | IM2412.CFX | IM2503.CFX |
| 2025-03-21 | IM2503.CFX | IM2506.CFX |
| 2025-06-20 | IM2506.CFX | IM2509.CFX |
| 2025-09-19 | IM2509.CFX | IM2512.CFX |
| 2025-12-19 | IM2512.CFX | IM2603.CFX |
| 2026-03-20 | IM2603.CFX | IM2606.CFX |
| 2026-06-22 | IM2606.CFX | IM2609.CFX |
| 2026-09-18 | IM2609.CFX | IM2612.CFX |

Final exit: 2026-10-30, SELL `IM2612.CFX` at 6081.0; no replacement or subsequent position.

## Evidence reproduction and actual online workflow

Portable packages were independently replayed in a separate process with an explicitly
empty Tushare credential and an artifact-only directory containing no Dataset caches.
Both report `verified`; full reconstructed Results equal the retained producer Results.
M1 reconstructed 750 StateEvents; Q1 reconstructed 706. This verifies reproducibility
relative to retained facts, not authenticity or Source freshness.

| Execution surface | M1 Run ID | Q1 Run ID |
| --- | --- | --- |
| Actual HTTP/Auth | `7ba4eb4d5f52c29a586384275bc794da` | `3f106620cf565e38327e7781d2c3bffe` |
| Windows Chrome UI | `a68ea2072ee6525cfc370f710355a72b` | `32e85922c651070cc72a1dd3160f1c37` |

HTTP: **PASS**, actual worker and PENDING → RUNNING → COMPLETED for both requests.
202 returned the immutable PENDING admission snapshot. Noncompleted Result reads were
409; completed envelopes matched Run identity/request and the full Python Result.
Actual Result JSON validated against live authenticated OpenAPI. Responses were
no-store; payloads were 645,971 / 625,694 bytes, below 33,554,432 bytes.
Same-owner rereads were identical; foreign and unknown Status/Result both returned
indistinguishable 404 envelopes.

Windows Chrome → WSL: **PASS**. Visible Windows Chrome performed Cookie login,
navigation, explicit exact-window/profile inputs, real Preflight, explicit submission,
polling and both results. Both V2 charts matched producer coordinates/events and
passed mouse zoom, pan and Reset axes. Evidence fingerprint, Trades/Rolls including
last-page final executions/rolls, Back/Forward history, layout
containment, reload without POST, historical deep links, logout and subsequent 401
were checked. No browser page errors were observed. External full-page screenshots
are `windows-expiry_to_M1_v1.png` and `windows-expiry_to_Q1_v1.png`.

## Failure, privacy and recovery classification

These are separate evidence classes; synthetic success never substitutes for the real
market gates above. Controlled failures are not described as Tushare incidents.

| Scenario | Evidence path / classification | Result |
| --- | --- | --- |
| Foreign/unknown privacy, completed reread | Actual real-market HTTP/Auth | PASS |
| Busy, no second task/directory; Result unavailable before completion | Existing actual thread/store and HTTP tests with controlled synthetic public inputs; WP7 browser runtime | PASS |
| Restart converts unfinished/orphan publication to INTERRUPTED; no Result | Existing process-crash/restart test and HTTP recovery test, controlled injection | PASS |
| FAILED has no Result; safe failure vocabulary | Existing worker/HTTP tests, controlled injection | PASS |
| Full Result reader busy; independent status; manual read retry | Actual permit tests plus WP7 response-boundary presentation injection | PASS |
| Expired identity clears protected content | Auth session tests and WP7 protected-read 401 injection | PASS |
| Lost POST response never automatically repeats POST | WP7 browser forwards actual accepted submission, then aborts response; controlled network injection | PASS |

## Performance, regression and remaining limitations

First Python M1 execution including acquisition, validation, replay and evidence encoding
took 122.564s; cached Q1 took 1.656s.
Actual HTTP submit-to-terminal observations were 2.127s / 2.136s.
Browser submit-to-first-result/plot observations were 2.369s / 4.362s.
Complete automated per-profile interaction sequences took 72.593s / 73.845s,
including chart gestures, table pagination, full-page screenshots and reload; these
are not isolated render timings. Offline replay took 1.493s / 1.523s. Substage
acquisition/replay/serialization timings were not independently instrumented.
Full curves remained operable and refresh read the completed Run without another backtest.
No performance repair or SLA is inferred from this one environment.

Regression results (all **PASS**):

| Check | Actual outcome |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | 527 passed; unchanged financial oracles |
| `poetry run pytest ui_http/tests -q` | 588 passed, including architecture and controlled HTTP failures |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py -q` | 13 passed |
| `poetry run pytest data_lake/tests/test_boundary.py market_research/tests/test_boundaries.py -q` | 15 passed |
| `poetry run pytest ui_web/scripts/test_export_contracts.py -q` | 5 passed |
| `npm run contract:check` | All seven OpenAPI/TypeScript pairs current; no generation needed |
| `npm run test` | 47 files, 427 tests passed |
| `npm run build` / `npm run lint` | PASS |
| `npm run test:backtesting-browser` | PASS; Linux Chromium, synthetic inputs and controlled fault injection |
| `npm run test:auth-browser` / `test:research-browser` / `test:visualization-browser` | PASS; Linux Chromium regression |
| `npm run test:daily-data-copy-export-browser` / `test:futures-basis-online-browser` | PASS; Linux Chromium regression |
| Ruff: Backtesting, HTTP, Web Python scripts | PASS |
| Mypy: Backtesting / HTTP | PASS; 49 / 62 source files |
| Markdown links/topology, diff whitespace and full diff review | PASS |

An initial combined pytest invocation hit colliding `test_architecture` module names;
all required suites were then run as separate module invocations successfully.
New-harness lint/type issues were corrected and checks rerun successfully. Existing
FastAPI/Starlette and Ant Design deprecation notices and the Plotly bundle-size warning
remain; no product/financial implementation change was required.

Known limitations: gross ideal Close, one lot, fixed notional, no costs/margin/funding/
dividends; historical metadata availability and cache freshness limitations remain.
Other products' real-market acceptance, native Windows backend/store and production
deployment are **NOT RUN / deferred**, outside this WP8 gate.

## Reproduction and artifact retention

Run Python tooling from repository root; run Node tooling from `ui_web/`. Use an
absolute external artifact directory; the examples use a generic system temporary path.

```bash
poetry run python market_backtesting/tests/wp8_real_acceptance.py --root /tmp/w2-wp8-real-im --mode python
poetry run python market_backtesting/tests/wp8_real_acceptance.py --root /tmp/w2-wp8-real-im --mode reproduce
# In ui_web (after Python acceptance; ports 8011/5173 must be free):
node scripts/wp8_real_acceptance.mjs /tmp/w2-wp8-real-im
```

The browser harness starts the real backend through the Python storage-isolation
wrapper, creates test users through the public Auth service with CLI approval, runs
HTTP acceptance, and invokes Windows Node/Chrome through WSL interop. Existing synthetic
browser scripts remain separate. Private credentials/Auth/Run runtime are removed at exit;
retained results, evidence, coverage, screenshots and logs remain outside Git.
Windows automation failure must be inspected as FAIL or NOT RUN, never substituted
with Linux headless Chromium. Manual fallback: start the isolated harness backend and
Vite with matching loopback Auth origin, register/approve/login, execute both exact
profiles, inspect charts/tables/evidence, reload/deep-link/logout, and record screenshots
and actual statuses before changing any gate to PASS.

External artifacts include `python-acquisition.json`, `python-acceptance.json`,
`offline-reproduction.json`, `http-acceptance.json`, `windows-acceptance.json`,
per-profile Results/Evidence and regression logs. No credentials, runtime databases,
large market payloads or personal local paths are committed.
