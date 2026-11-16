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

## Current implementation differences and reuse review

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
