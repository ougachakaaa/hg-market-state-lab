# Issue #13 automatic input preparation — reconciliation and work packages

This specialized delivery/change record is reached from [the Case](ARCHITECTURE.md)
and [original Roadmap](ROADMAP.md). It owns Issue #13 reconciliation, current drift
and follow-up readiness; input, application, result, HTTP and presentation semantics
remain in their narrow canonical owners below. Original WP0–WP7 closure records are
historical and are not reinterpreted as Issue #13 acceptance.

## WP0 baseline and scope (2026-11-16)

Source: [Issue #13](https://github.com/ougachakaaa/hg-market-state-lab/issues/13),
reviewed in full, with zero comments at review. The reported behavior is deliberate
read-only preparation under the previous Authority, not established data corruption.
The user confirmed retaining successful Result/request.operation identities and
adding optional error reason_code while keeping existing kind/status categories.

Branch: `fix/issue-13-auto-prepare-research-inputs`.
Locked base: `45b87f779d69290daeb303e535ad22ba3189eab7`.
The initial worktree was clean. The configured remote is `github`, not `origin`;
fetch succeeded and fetched `github/develop` still equals the locked base. No
same-name local or remote branch existed before creation from that base. No remote
was renamed/added and no develop/main ref was advanced. Commit identity belongs in
Git history and the final report, not self-embedded in this document.

WP0 changes Authority/navigation Markdown only. No runtime, test, generated contract,
Bundle, Manifest, market data, cache, credential/configuration or dependency is
changed. No acquisition, PR, merge, push or publication is performed. This is
semantic readiness for implementation, not delivery of automatic preparation.

## Decision ownership and reconciliation

| Concern | Canonical target and review finding | WP0 result |
| --- | --- | --- |
| Formal execution responsibility | [Research UPSTREAM](../../../UPSTREAM.md#execution-oriented-input-preparation) assigns required-fact preparation to owning Case Input Preparation. DataLake retains acquisition, cache management and proof. Backtesting keeps its own Case authority; no new cross-module dependency. | PASS |
| Public capability sufficiency | [DataLake Application](../../../../data_lake/APPLICATION.md), [Calendar Service](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md) and [Futures Service](../../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md) already publish exact semantic requests, legal partial Exports, Ensure diagnostics and typed operation errors. No DataLake change or wider consumer boundary is needed. | PASS |
| Calendar prerequisite order | [Inputs](INPUTS.md#preparation-modes-and-completeness) requires complete CFFEX Calendar before Futures Export. [Futures TRADING_DAYS](../../../../data_lake/datasets/tushare_equity_index_futures/TRADING_DAYS.md) still owns its internal prerequisite; Research neither reimplements it nor retries arbitrary prerequisite OperationError. | PASS |
| Proof and bounded preparation | Inputs validates each initial view before conditional Ensure; one Case Ensure per dependency, final Export after a normal valid EnsureResult, complete proof required before analysis. Hot first Export is final. No coverage round trip, Source fallback, rebuild or unconditional Ensure. | PASS |
| Python compatibility | [Application](APPLICATION.md#explicit-execution-entrypoints-issue-13-target) preserves prepare_inputs and both query_* APIs, including export-only injection. New execution preparation and execute_* entrypoints reuse Case validation/construction/statistical analysis. | PASS |
| Evidence and diagnostics | [Inputs diagnostics](INPUTS.md#execution-preparation-and-diagnostics-boundary) adds immutable attempts and optional operation/reason_code with compatible defaults; [Query Results](QUERY_RESULTS.md#issue-13-compatibility-and-preparation-evidence) retains final evidence association, existing result identities and accurate permission disclosure. No Run Store or new evidence persistence. | PASS |
| Errors and safe feedback | Existing categories remain; confirmed typed credential/cache incompatibility is distinguished without message matching. Legal final incompleteness differs from operation failure or malformed public results. HTTP exposes only fixed safe details and optional recognized reason_code; raw diagnostics remain internal. | PASS |
| GET / POST | [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md) keeps GET read-only and adds explicit POST Query. [Historical HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md) explicitly changes its existing POST to execution, preserving path, operationId and success shape. | PASS |
| Web and offline compatibility | [Daily Web](../../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md) and [Historical Web](../../../../ui_web/src/features/calendar_spread_relative_value/ARCHITECTURE.md) use explicit execution submission, indeterminate feedback, reason-specific advice and cancellation isolation. Static controllers remain Bundle-only; old success identities/disclosures stay valid without Bundle/Manifest edits. | PASS |
| Business invariants | Six Slot pairs, public Slot resolver, three formulas, historical cutoff, Quantile/Percentile/Histogram, Source identity and Export proof remain under their existing authorities. Preparation changes availability, not financial/statistical definitions. | PASS |
| Synchronous model | Existing process-wide capacity two, threadpool, limits and capacity held through worker completion remain; all three routes share the pool. No async job, new Run Store, generic scheduler or worker framework. | PASS — target contract |
| Real execution cost | Cold/hot latency, actual HTTP timeout suitability, concurrent Source/cache behavior and cancellation resource retention require Issue #13 WP3 evidence. Threadpool alone proves no latency SLA. | DEFERRED — operational acceptance |

**WP0 authority reconciliation: PASS. No unresolved critical ownership or interface
decision blocks Issue #13 WP1. READY FOR WP1.** The statuses above concern semantic
review only; they do not label unrun runtime checks as PASS.

## WP0 implementation differences and reuse review

Read-only source inspection at the locked base found:

- Calendar Spread `preparation.py` exposes export-only protocols, validates Calendar
  then Futures once each and fails legal incompleteness. It has no execution
  preparation or Ensure diagnostics. This remains the required read-only path;
  Issue #13 WP1 adds the explicit alternative, not a silent permission change.
- `queries.py` already centralizes preparation/construction and numerical
  association. It needs shared internal composition so execution does not reacquire
  inputs through query_*. `inputs.py` and query errors lack attempts, operation and
  reason_code; `SourceContext` currently hardcodes read-only/separate preparation.
- HTTP endpoints currently delegate to the two query_* functions; there is no Daily
  POST. Existing transport owns two shared process workers and safe kind-only
  errors. WP2 must register the new path with the same composition/Auth/product
  parsing/error/OpenAPI boundaries and preserve capacity through cancellation.
- Both Production controllers currently use original delivery semantics. Their error
  formatting prescribes manual data preparation and must change in WP2, together
  with affected generated artifacts. Pure Presentation remains shared with Demo.

Existing mechanisms reviewed without modification:

| Existing consumer | Authority / implementation finding | Issue #13 action |
| --- | --- | --- |
| Futures Basis | [Inputs](../futures_basis/INPUTS.md) and its public preparation perform validated Export → conditional Ensure → final Export for independent CFFEX/SSE calendars, Futures and Index. It has its own fingerprint/attempts and permits partial Index only. | Reuse the public-operation pattern; do not import/copy Basis preparation, Index/SSE acquisition or fingerprint policy into Calendar Spread. |
| Trailing Return | [Inputs](../trailing_return/INPUTS.md) and preparation already validate initial views, Ensure once per requested range and use final proof; prior-session discovery uses different explicit ranges. Final Calendar is strict, Index explicitly missing-tolerant. | Preserve that policy; it is not permission for partial Calendar Spread inputs. No cross-Case refactor or universal one-Ensure-per-Dataset rule. |
| W2 Backtest | [Inputs](../../../../market_backtesting/cases/futures_roll_long/INPUTS.md) and application already implement legal-view-first conditional Ensure, final completeness, retained diagnostics, read-only advisory preflight, typed credential/cache-incompatible handling and a separate SSE prerequisite. | Reuse existing DataLake typed errors and responsibility pattern. Do not reuse its Replay, stores, input fingerprint or application framework. |

The reviewed consumers already satisfy the scoped preparation responsibility; this
review does not claim exhaustive conformance for unrelated consumers or authorize
changing sibling implementations. No new shared mechanism is required. Public
DataLake errors may be wrapped as generic OperationError by prerequisite boundaries;
only a directly published typed signal supports a specific reason_code.

## Issue #13 implementation sequence

These packages are distinct from the original L1 WP1–WP7. Each produces an
independently reviewable commit on this branch. WP0 stops before any of them.

| Package | Exact boundary | Scoped acceptance |
| --- | --- | --- |
| WP1 — Research Input Preparation and Python execution | Implement Inputs' execution protocols, prepare_inputs_for_execution, immutable attempts/error diagnostics and public facade exports; preserve export-only prepare_inputs/query_* APIs. Add execute_daily_spreads and execute_historical_relative_value with identical analysis parameters and Result types. Share Case-local validation, final-input assembly, Observation and Statistics paths; select truthful source_context by entry. No HTTP/Web/generated artifacts, DataLake changes, caches or sibling runtime edits. | Inject public-service fakes for fresh/hot/mixed caches; exact same-window Calendar-before-Futures sequence; at most one Case Ensure per dependency; complete/partial Ensure followed by final proof; failed/malformed operations; typed errors; immutable success/failure evidence; invalid full request before I/O; closed/empty sessions; read-only zero Ensure; identical analysis for identical final inputs. Select changed input/query tests only. |
| WP2 — HTTP and Web integration | Add Daily POST with exact closed body and operationId; keep GET read-only; switch Historical POST to execute_*; project optional reason_code through existing kind/status envelope. Extend current path/Auth/composition/capacity/OpenAPI handling. Update only the two affected generated contract pairs and Production request/error/loading controllers; keep pure Presentations and existing Bundle bodies compatible. | Target route delegation, strict parsing, authentication/same-origin, safe errors, success/identity projection, shared saturation and worker lifecycle; feature submit/retry, cancellation/stale isolation, reason/fallback guidance, existing Demo fixture validation and no execution in static controllers. Run generation/type/build checks only as required by changed wire/types; no automatic browser matrix or deployment. |
| WP3 — Fresh/Hot Cache, Failure Matrix and Performance Acceptance | Explicitly scoped integration acceptance for both formal execution surfaces and read-only GET. Use identified isolated development cache roots for fresh-cache work; do not delete existing DataLake caches or real source data. Record credentials only as available/unavailable, never values. No new architecture/framework. | Fresh user submission succeeds without manual Ensure where Source is available; hot equivalent has no Ensure/Source I/O. Cover incomplete final proof, absent credential, cache incompatibility, Source/unit/operation failures, malformed public results and busy capacity. Measure cold/hot duration, actual client/Gateway/server timeouts, tested products/windows, concurrent requests and capacity after cancellation. Record unavailable environments as NOT VERIFIED. |

A real failure in changed behavior must be fixed and the failed case rerun. Do not
expand to full-module/repository tests, automatic architecture scans or release
checks. If synchronous cold requests cannot complete within the actual HTTP stack,
record the operational gap and seek a separate decision on the smallest next model;
WP1/WP2 must not preemptively build an async framework. No current evidence justifies
new business limits, timeout defaults or a claimed performance threshold.

## WP0 verification and retained risks

PASS — document diff/semantic review against the selected public contracts and
reviewed source. Manual navigation review confirms stable Case/Roadmap entries
lead to this change record and its narrow canonical contracts. Original historical
acceptance content is retained; only a follow-up navigation section is added to
Roadmap. All changed files are Authority/navigation Markdown.

Business tests, builds, type checks, generated-contract regeneration, automated
link/topology scans, real-data/cache, browser, platform and deployment checks are
**NOT RUN** for documentation-only WP0. Their absence is not runtime PASS or a
WP0 blocker. No generated artifact or Bundle is rewritten to match a future target.

Retained risks and limits:

- Synchronous cold-cache work may exceed actual HTTP timeout settings. Cancellation
  does not cancel an in-flight synchronous operation; it may continue cache writes
  and hold capacity. Independent requests can still contend. These require WP3
  evidence, not an invented cancellation or concurrency guarantee.
- Calendar/Futures Exports are independent snapshots. Concurrent changes can cause
  prerequisite failure or detectable target mismatch; fail without Case retries.
  No shared snapshot, Provider freshness or historical point-in-time metadata proof
  is added. Existing financial/source disclosures remain mandatory.
- A generic public OperationError cannot safely establish a credential, Source or
  storage cause. Preserve the general classification without parsing raw text.
- The existing Historical POST changes acquisition permission and possible latency
  when WP2 lands. Its path/result remain compatible, but callers must understand
  the documented execution semantics. Python read-only alternatives remain intact.

No unresolved semantic decision is deferred to WP1. Runtime delivery and operational
acceptance remain pending the three packages above; this WP0 does not close Issue #13.

## WP1 Python delivery and reconciliation (2026-11-16)

Issue #13 WP1 is implemented on the existing dedicated branch, from required HEAD
`98b6458ed11ca66f100008fff2b1730ee129d637`. Remote `github` fetch succeeded;
the required branch/HEAD matched and the worktree was clean before implementation.
The WP0 inspection above remains historical; its Python differences are resolved
by this delivery. Commit identity remains in Git history and the final report.

- The Case facade publishes `prepare_inputs_for_execution`, `execute_daily_spreads`,
  `execute_historical_relative_value`, execution service protocols and frozen
  `InputPreparationAttempt`. Existing `prepare_inputs` and both `query_*` entrypoints
  retain export-only injection and never Ensure.
- Both modes share Request/Export validation and final-input assembly. Execution
  validates the initial public view before conditional Ensure, permits one Case
  Ensure per dependency and validates a final Export after a normal legal
  EnsureResult, including incomplete/UnitFailure outcomes. Calendar must be complete
  before Futures construction. No coverage round trip, dependency restart, private
  prerequisite, Source fallback or cache rebuild is introduced.
- Attempts retain immutable public requests and separately validated preliminary,
  Ensure and final evidence. Malformed payloads are excluded. Final InputEvidence,
  Prepared Inputs and existing Observation/Result associations remain intact;
  diagnostics do not become financial inputs. Calendar/Futures records_written
  distinctions and public failure identities are validated.
- Input and application errors retain compatible categories and add optional
  reason_code/operation/attempts. Typed credential/cache errors precede OperationError;
  fixed safe messages replace raw upstream text, causes remain attached, and
  unexpected service/programming exceptions propagate.
- Daily/Historical validation, Observation construction and analytical projection
  are shared by the explicit entrypoints. Historical metric and edges are validated
  before factories/I/O. Same final Exports give the same six pairs, historical cutoff
  and numerical results. Result/request.operation identities and SourceContext shape
  remain unchanged; execution discloses preparation permission without claiming an
  Ensure occurred on a hot cache. Existing read-only disclosure remains unchanged.

Verification uses synthetic public-service fakes only, with no real cache or
Tushare calls:

```bash
poetry run pytest -q market_research/tests/test_calendar_spread_inputs.py market_research/tests/test_calendar_spread_queries.py market_research/tests/test_calendar_spread_execution.py
```

**283 passed**, no failures or skips. Two additional focused scenarios then passed:

```bash
poetry run pytest -q market_research/tests/test_calendar_spread_execution.py::test_successful_empty_futures_unit_writes_zero_records market_research/tests/test_calendar_spread_execution.py::test_missing_ensure_fields_are_not_validated_evidence
```

**2 passed**, no failures or skips; **285 distinct cases verified**, including the
199 original input/query cases. Scoped Ruff validation passed for changed Python
files; scoped mypy passed for the six changed production Python files. Complete
diff/semantic review reconciles this delivery with Inputs, Application and Query
Results without a new business decision or contract change.

**WP1 reconciliation: PASS. READY FOR WP2.** HTTP/Web integration and generated
contracts remain unchanged and pending WP2. Real Source/cold-hot latency, concurrent
cache behavior, HTTP timeouts/cancellation capacity, browser, native Windows and
deployment acceptance are **NOT VERIFIED** here; operational acceptance remains WP3.
No data, cache, credential, dependency, Bundle or Manifest was changed. No PR, merge,
push or publication was performed. This delivery stops at WP1 and does not close
Issue #13.


## WP2 HTTP and Web delivery and reconciliation (2026-11-16)

Implemented on `fix/issue-13-auto-prepare-research-inputs` from required HEAD
`e465a050fd57e92cf7f05695db8e76c08198bc88`, with a clean starting worktree.
Fetch succeeded against the configured `github` remote (there is no `origin`).
No branch creation, develop/main integration, PR, push or publication occurred.
WP0/WP1 records above retain their original acceptance facts. Final commit identity
is recorded in Git history and the task report.

| Boundary | Delivered behavior and reconciliation |
| --- | --- |
| Daily GET | `/data/futures-calendar-spread` still selects only `query_daily_spreads`; read-only permission is unchanged. |
| Daily POST | `/data/futures-calendar-spread/query`, operationId `execute_futures_calendar_spread`, accepts the closed DailyRequest body and selects only `execute_daily_spreads`. |
| Historical POST | Existing path, operationId, body and success Result remain unchanged; dependency now selects `execute_historical_relative_value`. |
| Shared HTTP | All three paths use existing Auth, same-origin enforcement, CalendarSpreadRoute, threadpool, two-worker process capacity, streamed 16 KiB request bound, atomic 32 MiB response bound and no-store responses. Cancellation retains capacity through worker completion. No second semaphore or DataLake import/call is added. |
| Errors | Only the eight frozen category/reason pairs are projected, with fixed safe details. Missing reason_code is omitted for legacy compatibility. Unknown categories/reasons and mismatched combinations become safe internal_error; raw exception text, attempts, UnitFailures, tokens and cache paths are never projected. |
| Web | Daily submit/retry explicitly uses the new POST; Historical keeps its POST. Both show the exact indeterminate preparation/calculation message and reason-specific fixed guidance, with kind fallback for old errors. No Ensure request/button, automatic retry, mount execution or progress estimate is added. Existing submitted/draft identity, abort and stale isolation remain intact. |
| Wire | Actual composed FastAPI `.openapi()` remains the sole source. Existing generator regenerated both affected OpenAPI/TypeScript pairs; other generated files are byte-unchanged. Existing operation documents and all success schemas are unchanged; only ErrorBody changes, plus new DailyRequest/POST. Existing request.operation literals remain unchanged. |
| Demo | Existing Bundle bytes, Manifest, captures, producer and collection scripts are unchanged. Static controllers keep the public pure Result validators/Presentations and never mount Production submission hooks. Retained Bundle rendering and local Pair/date-axis interactions pass without HTTP or execution controls. |
| Research/DataLake | No Python business implementation, financial formula, sample policy, statistical result, runtime configuration, dependency or market/cache data changed. APPLICATION's stale target-only status is reconciled with delivered WP1/WP2; no new semantic decision is introduced. |

Changed-file inventory (paths are relative to the repository root):

- Authority/status: this record, case `APPLICATION.md`, both affected HTTP product
  `http-contract.md` files and both Web feature `ARCHITECTURE.md` files.
- HTTP: `ui_http/src/ui_http/products/futures_calendar_spread/{endpoint,transport,schemas}.py`,
  `ui_http/src/ui_http/products/calendar_spread_relative_value/endpoint.py`, and
  `ui_http/tests/test_calendar_spread_http.py`.
- Web: each affected feature's `api/query.ts`, `api/query.test.ts`, generated
  OpenAPI/TypeScript pair, `model/format.ts` and Page implementation/test;
  Daily additionally updates `api/validateResult.ts` to validate the POST responses.
- Tooling/tests: `ui_web/scripts/export_contracts.py`,
  `ui_web/tests/tooling/test_export_contracts.py`,
  `ui_web/tests/fixtures/calendar_spread_browser_app.py` (keeps the new dependency
  injected for later manual browser acceptance), and
  `ui_web/demo/runtime/calendarSpread.test.tsx`.

Scoped verification (synthetic injected public services only):

```bash
# repository root
poetry run pytest ui_http/tests/test_calendar_spread_http.py -q
# 136 passed before the extra POST boundary cases were added.
poetry run pytest ui_http/tests/test_calendar_spread_http.py::test_research_duplicate_and_malformed_json ui_http/tests/test_calendar_spread_http.py::test_research_media_type ui_http/tests/test_calendar_spread_http.py::test_research_rejects_all_query_parameters ui_web/tests/tooling/test_export_contracts.py::test_calendar_spread_exports_preserve_operations_security_and_local_schema_closure -q
# 27 passed, including 13 newly added route cases and one exporter case.
poetry run pytest ui_http/tests/test_calendar_spread_http.py::test_historical_execution_preserves_complete_result_and_analysis_identity ui_http/tests/test_calendar_spread_http.py::test_daily_execution_streamed_body_and_response_bounds -q
# 2 passed. Total: 151 distinct HTTP cases and one exporter case verified.
poetry run pytest ui_http/tests/test_calendar_spread_http.py::test_reason_projection ui_http/tests/test_calendar_spread_http.py::test_classified_errors_safe_and_no_renewal -q
# 45 passed after replacing the reason mapping oracle with explicit contract cases
# and asserting that legacy responses omit reason_code; no additional distinct cases.

# ui_web/; eight explicitly selected feature test files
npm test -- src/features/futures_calendar_spread/api/query.test.ts src/features/futures_calendar_spread/api/validateResult.test.ts src/features/futures_calendar_spread/hooks/useQuery.test.ts src/features/futures_calendar_spread/page/DailyPage.test.tsx src/features/calendar_spread_relative_value/api/query.test.ts src/features/calendar_spread_relative_value/api/validateResult.test.ts src/features/calendar_spread_relative_value/hooks/useQuery.test.ts src/features/calendar_spread_relative_value/page/RelativeValuePage.test.tsx
# 98 passed.
npm test -- demo/runtime/calendarSpread.test.tsx
# 2 passed using retained Bundles, with network calls forbidden by the test.
npm run contract:generate
npm run contract:check
npm run build
```

All listed checks passed. Build includes TypeScript checking; its large-chunk
warning is informational. Scoped Ruff and Oxlint passed for changed Python and
TypeScript/TSX source/test files. Complete diff/semantic review confirms the frozen
ownership boundaries, additive error contract and unchanged success DTOs. No full
regression, Browser Matrix, static isolation build, real-data capture or deployment
check was run. Browser/native Windows/deployed behavior is **NOT VERIFIED** here.
The HTTP tests emit the existing Starlette TestClient/httpx deprecation warning.

**WP2 reconciliation: PASS. READY FOR WP3.** This is implementation readiness for
operational acceptance, not closure of Issue #13 or a production declaration.
WP3 must still measure real cold/hot request durations and actual browser/Gateway/
server timeout settings; verify isolated fresh/hot caches, real credential/Source
failure modes, concurrent cache/Source contention, saturation and post-cancellation
worker occupancy. Capacity remains per process; no distributed coordination or
latency guarantee is claimed. A client cancellation does not guarantee automatic
preparation stops or already committed DataLake units roll back. Synchronous cold
requests exceeding the actual stack's timeout require an explicit follow-up decision,
not an implicit async framework. This delivery stops at WP2.

## WP3 operational acceptance and final reconciliation (2026-11-16)

Continued the existing branch from required HEAD
`010815fedb689b04c0e673765675afd6699647d5`, with a clean worktree. No new branch,
integration, PR, issue closure, push or publication. This acceptance supersedes the
WP2 pending operational status above; original WP0–WP2 and WP7 facts remain historical.
No runtime defect was found and no implementation or wire contract was changed.

### Environment and evidence levels

- WSL2 Linux x86_64, Python 3.13.15 in the root `.venv`, FastAPI 0.141.1,
  Starlette 1.7.0, AnyIO 4.15.1, Uvicorn 0.53.0; Node 22.23.2, Vite 8.3.3,
  installed Playwright Chromium. Source credential available through `lab_config`;
  no credential value was logged and private `.env` was not edited.
- New committed `ui_http/tests/test_calendar_spread_preparation_acceptance.py`
  exercises real Auth/composed FastAPI, unchanged Research execution, real DataLake
  public services, Source adapters, completeness and SQLite. Only provider rows
  are controlled. Dataset-private `_create_service` seams are test facilities,
  not new consumer permissions. Each case has its own pytest temporary cache.
- Real Source acceptance used the same composition seams with `TushareExecutor`,
  unmodified Source adapters and real SQLite. Temporary observer wrappers counted
  public Ensure/Export and provider calls without retaining their parameters or secrets.
  Research factories selected these services; HTTP query dependencies were not replaced.
  Chromium same-origin fetch traversed Vite `5173 /api` → Uvicorn `8011` → the
  actual composed application, using a synthetic approved local Auth account.
  Each scenario began with its own absent cache directory under
  `/tmp/issue13-wp3-live-rvinv17x/{daily,short,representative}`.
  Temporary observers/servers are not application features or a benchmark framework.
- Failure manufacturing and cancellation occupancy use controlled public-service/
  business dependency injection, rather than intentionally damaging real caches or
  credentials. The failure matrix below identifies that evidence level.

### Real fresh/hot results — PASS

All requests used product **IM**, evaluation/trade date **2026-09-30**. Historical
requests explicitly supplied `histogram_edges=[-0.1,0,0.1]`, omitted metric to select
the contractual `annualized_spread_ratio`, and used the start dates below. Daily
used `POST /data/futures-calendar-spread/query`; Historical used
`POST /research/calendar-spread-relative-value/query`. There was no manual Ensure.
Times are measured browser fetch/body durations in seconds, one observation each,
not percentiles, a benchmark average or a latency guarantee. Validator module loading
is outside the measured duration.

| Request | Cold / hot HTTP | Cold / hot seconds | Calendar Ensure | Futures Ensure | Source calls | Final Calendar / Futures coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Daily 2026-09-30 | 200 / 200 | 2.1157 / 0.0125 | 1 / 0 | 1 / 0 | 7 / 0 | 1/1 / 1/1 |
| Historical 2026-09-28..2026-09-30 | 200 / 200 | 2.3127 / 0.0176 | 1 / 0 | 1 / 0 | 7 / 0 | 3/3 / 3/3 |
| Historical 2026-08-17..2026-09-30 | 200 / 200 | 6.3950 / 0.1126 | 1 / 0 | 1 / 0 | 19 / 0 | 45/45 / 32/32 |

Source counts are actual endpoint invocations, including terminal pagination calls:
each cold request made one `trade_cal` and four `fut_basic` calls; `fut_daily`
counts were 2, 2 and 14 respectively. Calendar/Futures Ensure counts are deltas for
each request. Calendar Export counts include Futures' existing public prerequisite
reads (five cold, two hot); they are not additional Research preparation attempts.
No per-date/Pair Ensure or business retry was observed.

Both cold and hot bodies passed the respective formal Web `validateResult` in
Chromium. Cold/hot complete JSON bodies were identical, including every financial
and statistical value. All current days had six valid pairs. Short/representative
history retained 2/44 natural days, with 2/31 all-stage samples per Pair, respectively.
Every actual sample preceded evaluation; latest sample was 2026-09-29. Quantile,
Percentile and explicitly requested Histogram associations passed the validators.
Calendar proved natural-day coverage; Futures proved only CFFEX open-date coverage.

The synthetic SQLite test additionally verified Daily empty-cache GET = 409
`incomplete_inputs/cache_incomplete` without Source or cache creation, then hot GET
= 200 with the same financial results and zero Ensure/Source calls. It checked
closed-weekend coverage, exact final unit counts, no private path/Token-key/internal
attempt disclosure, and only the two Dataset SQLite files plus Auth storage.
Real Uvicorn lifespan separately initialized the already-existing Basis/Backtesting
empty stores before Calendar Spread execution; both retained zero Runs and zero
results. Calendar Spread created no Run identity, business result cache or Publication.

### Failure matrix — PASS at controlled-test level

| Injected condition | Expected HTTP / kind / reason_code | Evidence |
| --- | --- | --- |
| CredentialMissingError | 503 / upstream_unavailable / credential_missing | WP1 typed errors at Export/Ensure/final Export; HTTP reason projection; both Web reason guidance tests |
| CacheIncompatibleError | 503 / upstream_unavailable / cache_incompatible | Same layered tests; no rebuild attempted |
| Source/OperationError | 503 / upstream_unavailable / operation_unavailable | Same layered tests; generic cause is not inferred from text |
| Valid incomplete EnsureResult, complete final Export | 200 / no error | WP1 incomplete-Ensure diagnostic test, including UnitFailure; final proof wins |
| Final Export still incomplete | 409 / incomplete_inputs / final_export_incomplete | WP1 final-incomplete test, HTTP reason projection, both Web guidance tests |
| Malformed Export | 502 / input_contract_error / malformed_export | WP1 preliminary/final malformed tests, HTTP reason projection, Web guidance |
| Malformed EnsureResult | 502 / input_contract_error / malformed_ensure_result | WP1 field/identity/accounting tests, HTTP reason projection, Web guidance |
| Invalid request | 400 / invalid_request / absent | WP1 before-I/O validation, HTTP strict parsing, both Web error tests |
| Saturation | 503 / transport_busy / absent | Controlled shared-worker tests and real browser concurrency below; both Web fallback tests |

HTTP tests inject secret/private-path sentinel text and assert fixed safe details,
correct status/kind/reason, no fabricated successful projection and no leakage.
Web tests discard unsafe backend detail and check fixed reason-specific guidance,
safe legacy fallback and deliberate manual retry. These are layered tests, not claims
that real Source outages or damaged caches were created in the live environment.

### Synchronous performance, capacity and timeout — PASS for selected local chain

Three simultaneous Chromium submissions of the hot representative request returned
200 in 0.0492s, 200 in 0.0735s and 503 `transport_busy` in 0.0098s. The following
request returned 200 in 0.0337s. No automatic resubmission was used.
Existing controlled tests separately proved all three routes/app instances share
capacity two, work runs off the event loop, capacity includes DTO encoding, canceled
clients leave both workers occupied, and completion/failure restores capacity.
Cancellation evidence is an ASGI task cancellation with blocked synchronous workers;
it does not assert that a browser abort terminates Source work or rolls back SQLite.

Inspected installed/local configuration:

- Production Web `protectedRequest` uses fetch/AbortController without an application
  request deadline, polling or automatic retry. Explicit cancel closes client waiting.
- Vite proxy has no configured `timeout`/`proxyTimeout`; installed proxy code applies
  those deadlines only when configured. No additional reverse proxy was in this chain.
- Repository launcher uses Uvicorn without an overall business-request deadline:
  one process, default `limit_concurrency=None`, keep-alive timeout 5s (idle between
  requests, not an execution budget). No settings were changed.
- Installed AnyIO default shared threadpool limiter has 40 tokens; Calendar Spread
  retains its independent two-worker semaphore. Other products can contend for the
  threadpool; this is not distributed capacity or an isolated worker pool.
- Tushare client has a 30s timeout per Source HTTP call, not per Research request.
  Collector default is 60s per HTTP request. Maximum measured cold execution was
  6.395s and completed through the actual browser/Gateway/server chain.

No observed blocking timeout or capacity defect requires a new execution model.
Unobserved Source delays, maximum legal 3660-date requests, cold-cache concurrent
Source contention, long-duration load and deployed proxy/browser limits remain
**NOT VERIFIED**. The selected representative window does not prove every legal
window fits every deployment timeout; these are retained operational risks, not an SLA.

### Demo, Authority and final disposition

**PASS** — corrected only `ui_web/demo/CALENDAR_SPREAD.md`'s unqualified historical
no-acquisition wording. Original WP7 used retained facts without Ensure. Future
explicit Historical Collector POST may now conditionally acquire; Daily Collector
GET remains read-only. Demo/build Authority permits formal HTTP generation and has
no permanent Collector no-Ensure requirement. No semantic conflict or new endpoint
decision remains. Static runtime and offline Preflight retain Bundle-only semantics.

**PASS** — existing nine Bundles admitted twice by `npm run demo:build`; static build
completed. A focused Chromium preview visited both Calendar Spread static routes,
switched Research Calendar Days and Pair Q1/Q2, found no execution buttons, and
recorded three static-resource requests with zero fetch/XHR/external requests.
The targeted static controller test also forbids fetch. Bundles, Manifest and all
captured values remained unchanged; Collector and publication were not invoked.

Scoped commands and actual results (root `.venv/bin/python`, no installation):

```text
pytest -q market_research/tests/test_calendar_spread_execution.py
  market_research/tests/test_calendar_spread_inputs.py
  market_research/tests/test_calendar_spread_queries.py
  ui_http/tests/test_calendar_spread_http.py
  → 436 passed, 15.99s
pytest -q -s ui_http/tests/test_calendar_spread_preparation_acceptance.py
  → 3 passed (real services/SQLite, controlled Source)
pytest -q ui_http/tests/test_calendar_spread_http.py::test_cancelled_requests_hold_shared_capacity
  ui_http/tests/test_calendar_spread_http.py::test_workers_hold_capacity_through_serialization_and_free_after_failure
  ui_http/tests/test_calendar_spread_http.py::test_capacity_includes_projection_encoding
  → 3 passed (already included in the 436 distinct cases)
npm test -- src/features/futures_calendar_spread/api/query.test.ts
  src/features/futures_calendar_spread/api/validateResult.test.ts
  src/features/futures_calendar_spread/hooks/useQuery.test.ts
  src/features/calendar_spread_relative_value/api/query.test.ts
  src/features/calendar_spread_relative_value/api/validateResult.test.ts
  src/features/calendar_spread_relative_value/hooks/useQuery.test.ts
  demo/runtime/calendarSpread.test.tsx
  → 7 files, 93 passed, 13.16s
npm run demo:build → PASS, 9 Bundles; static artifact built
ruff check ui_http/tests/test_calendar_spread_preparation_acceptance.py → PASS
```

The HTTP tests emit the existing TestClient/httpx deprecation warning; Demo build
emits the existing large-chunk warning. Neither is an execution failure. No full
suite, generated-contract rewrite, dependency update or deployment was performed.
Temporary browser/live observations are described above rather than introduced as
a mandatory gate. Temporary Uvicorn/Vite/preview servers were stopped. Cleanup
removed only `/tmp/issue13_wp3_server.py` and the two temporary browser scripts
`ui_web/.build/wp3-live.mjs` / `ui_web/.build/wp3-final-browser.mjs`.
The isolated live cache root and sanitized `/tmp/issue13-wp3-*.json` observations
remain available for local inspection; no existing DataLake cache/user data was deleted.

| Final layer | Status | Remaining limit |
| --- | --- | --- |
| Authority | PASS | One stale Demo statement reconciled; no unresolved critical semantic decision |
| Implementation | PASS | WP1/WP2 scoped tests, real fresh/hot execution, read-only preservation and safe failure feedback |
| Operational, selected WSL/local browser chain | PASS | Real Source cold/hot, coverage, latency, network capacity and static Demo verified; cancellation at controlled ASGI level |
| Other deployments/platforms, maximum windows and prolonged/cold concurrent load | NOT VERIFIED | No extrapolation from this acceptance |

**Issue #13: READY TO CLOSE. Branch: READY TO MERGE INTO DEVELOP for final review.**
These judgments apply to the selected environment and bounded acceptance, with the
unverified risks above retained. There is no observed critical defect, timeout failure,
Authority drift or required semantic decision. Issue remains OPEN; no merge, issue
closure or publication is performed by WP3.
