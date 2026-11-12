# W2 Futures Roll Long delivery and readiness

## Portable storage follow-up

The original case milestones below retain their original evidence and numbering.
The new, unimplemented storage WP0-WP6 series is tracked in
[Storage reconciliation](../../../market_research/STORAGE_RECONCILIATION.md); its case-owned target is
[Online storage](ONLINE_STORAGE.md). Prior PASS does not establish SQLite readiness
or native Windows storage support.

This document specializes the [case](ARCHITECTURE.md). It owns current delivery
status, remaining work-package acceptance and deferred scope. Current authority
inventory, semantic review and implementation drift belong to
[Reconciliation](RECONCILIATION.md). Financial formulas, result schemas and run
internals remain in their specialized contracts.

## Current status

W2 has three deliverables: strategy-independent Position-Driven Core V1, real Futures
Roll Long research, and the Online/Web workflow. Core is a general finite daily
single-instrument accounting kernel; W2 is its first case.

- Core Authority and implementation include immutable daily return, cumulative PnL,
  equity and cumulative return. D1 is **CLOSED**; there is no open Implementation
  Drift or Blocking semantic decision in the implemented Core/W2 synthetic subset.
- Core Replay, Portfolio/Target/Transition, ordered StateEvents, Accounting and
  Recorder, W2 MechanicalRollPolicy and its synthetic adapter are implemented.
  WP0/WP1 require no further implementation. The original four-session Core oracle
  still passes with daily PnL 0 / 20,000 / 4,000 / 2,000 CNY and total 26,000.
- **Remaining WP2 — PASS (2026-11-11).** The input retains one exactly session-aligned
  immutable Index Close series for both N0 and benchmark. The pure W2 Analyzer
  projects Core accounting and computes benchmark/equity, excess and independent
  drawdowns. Both five-day oracles pass: M1 total PnL 22,000 CNY; Q1 19,000 CNY;
  N0 1,200,000 CNY and benchmark return approximately 0.0125 for both profiles.
- **WP3 — PASS (2026-11-11).** Public Python request/preparation/execution and
  read-only readiness are implemented. Complete public Calendar/Futures/Index exports
  feed the existing Replay → Analyzer path; canonical inputs and ensure diagnostics
  are retained. The published Index SSE Calendar prerequisite is prepared through the
  same public Calendar service, separately from CFFEX replay sessions.
- Bounded real IM acceptance passed for both profiles over 2025-02-17 through
  2025-03-24: 26 real CFFEX sessions, 104 Futures rows, real 2025-03-21 expiry rolls,
  final Flat, reproducible replay and identical input fingerprint across profiles.
  Default caches were not touched. Full-window research/Web evidence is recorded in WP8 below.
- Current verification and real/synthetic evidence are in
  [Reconciliation](RECONCILIATION.md#validation-evidence).
- **WP4 — PASS (2026-11-11).** Immutable validated BacktestResult, formal trades/rolls,
  fixed limitations, portable versioned Evidence Package, pure offline reproduction
  and producer-owned V2 returns/drawdown Views are implemented. Bounded retained-real
  IM verification passes for both profiles, including frontend V2 conformance and
  complete event reconstruction, without Source acquisition.
- **WP5 — PASS (2026-11-11).** Independent online Python facade, actual single-thread
  execution, owner-isolated POSIX runtime store, bounded validated result encoding,
  result-before-COMPLETED atomic publication and startup interruption recovery are
  implemented. Real process-crash recovery and both unchanged financial oracles pass.
  Its public application boundary is consumed by WP6 without a second execution path.
- **WP6 — PASS (2026-11-11).** The existing authenticated FastAPI runtime publishes
  preflight/submit/status/result with strict bounded requests, full concrete Result/V2
  DTOs, owner isolation, independent bounded HTTP delivery and offline OpenAPI.
  The [HTTP contract](../../../ui_http/products/backtesting/http-contract.md) owns
  transport details; actual acceptance evidence is in
  [WP6 reconciliation](RECONCILIATION.md#wp6-http-product-acceptance--2026-11-11).
  WP7 Web delivery and full-window WP8 acceptance are recorded below.
- **WP7 — PASS (2026-11-12).** The independent authenticated
  [Web consumer](../../../ui_web/src/features/backtesting/ARCHITECTURE.md) provides
  explicit four-field input, advisory preflight, non-replayed submission, polling,
  URL restoration, formal summary, V2 curves, trades/rolls and evidence summary.
  Generated contract belongs to the Web feature. Actual synthetic Chromium and
  regression evidence is recorded in [WP7 acceptance](../../../ui_web/src/features/backtesting/ACCEPTANCE.md).
  No producer financial calculation or HTTP wire contract changed.
- **WP8 — PASS (2026-11-12).** Both real IM profiles completed the full requested
  window with reproducible evidence, actual authenticated HTTP/worker execution and
  visible Windows Chrome → WSL acceptance. The independent
  [WP8 record](WP8_ACCEPTANCE.md) owns Run IDs, coverage, financial/roll evidence,
  observed performance and regression results. W2 is complete within its declared scope.
  A later final acceptance-gate hardening makes PASS the only exit-0 outcome, adds
  token-free exit-code tests and records the retained-evidence cross-check; it changes
  no financial or product semantics. See
  [WP8 acceptance-gate hardening](WP8_ACCEPTANCE.md#final-acceptance-gate-hardening--2026-11-12).

## Accepted work packages

Each WP is independently reviewable, committable and accepted. WP2 through WP8 are
accepted; W2 is complete. No W3 or production deployment deliverable is implied.

| WP | Scope and required deliverables | Dependency | Definition of Done / acceptance | Forbidden scope |
| --- | --- | --- | --- | --- |
| Remaining WP2 — Core daily return and W2 Performance (**PASS**) | Closed D1; consume Core daily/cumulative accounting; Analyzer for benchmark/equity, excess and both drawdowns | Existing Core and W2 Policy | Both five-day Performance oracles; Core daily-return acceptance; benchmark first-day and positive-equity checks; running peaks; final excess; deterministic finite outputs; multiplier/strategy-equity failures preserved | Reimplementing Core PnL/accounting in Case, changing Policy, DataLake I/O, Result/Views, Online, HTTP/Web |
| WP3 — DataLake Integration & Real Backtest Python API (**PASS**) | Public Calendar/Futures/Index preparation; exact completeness validation; authorized Slot adapter; canonical input fingerprint; read-only preflight; public Python backtest API; bounded real IM acceptance | WP2 | Fake-service completeness/failure matrix; exact scope/window/counters; deterministic fingerprint; public import boundary; complete final exports; bounded real IM evidence; no Snapshot/private access or second cache | W1 observation/report consumption, second provider/cache, HTTP/Web, online store |
| WP4 — Backtest Result, Evidence & Visualization Projection (**PASS**) | Stable result profile; evidence summary/package; V2 returns/drawdown views; reader projection; limitations; cross-field invariants | WP3 | Result schema/version; all invariants; V2 validation; manual oracle; deterministic evidence/replay; WP4 PASS = core research capability complete | HTTP/Web, online store, generic visualization schema, W3 financial features |
| WP5 — Online Backtest Application & Run Store (**PASS**) | Online composition of the WP3 preflight plus submit/status/result application; owner scope; single worker/busy; disposable file store; atomic result publication; startup recovery; bounded result reads | WP4 | Fake-service state matrix; busy/no queue; owner isolation; restart interruption; orphan result handling; size/corruption/unsupported platform; no HTTP/UI | HTTP/UI, Publication, Workbench, multi-process/queue, W1 store reuse |
| WP6 — HTTP Product & OpenAPI (**PASS**) | HTTP contract; strict parsing/limits; run/result DTO projection; Auth/owner/error mapping; OpenAPI; no financial recomputation | WP5 | Strict request/auth/error/limit tests; OpenAPI/freshness prerequisites; result/run/request association; preflight and no-store behavior; Web untouched | Web UI, business logic, W1 product changes, financial recomputation |
| WP7 — Web UI Backtesting Integration (**PASS**) | `/backtesting` page: Ant Design controls, preflight/readiness, submit/poll, V2 return/drawdown charts, trades/rolls, evidence/limitations, busy/error/failed/interrupted states; generated contracts | WP6 | `npm run contract:check`, Vitest, build, lint; deterministic browser tests; no fake result/control; no React financial computation; planned page honestly replaced | Financial calculation, backend bypass, generic chart DSL, CSV/export/copy not authorized by W2 v1 |
| WP8 — Real-Market E2E Acceptance & Reconciliation (**PASS**) | WSL2 FastAPI + Vite + Windows Chrome real IM workflow; login → preflight → submit → poll → result → charts → trades → evidence; restart/busy/ownership/failure; final reconciliation | WP7 | Both profiles for IM, 2024-01-01 through 2026-10-30, with real rolls and final exit; real data not substituted by synthetic; all workflow states; Windows Chrome browser → WSL HTTP/Web local end-to-end acceptance; W1 regression; no W3 features; external evidence; [actual acceptance](WP8_ACCEPTANCE.md) closes W2 | W3 fees/slippage/ETF/margin/funding/optimization; production deployment promise; unverified platform claims |

## WP8 acceptance outcome

WP7's [feature authority](../../../ui_web/src/features/backtesting/ARCHITECTURE.md)
and [acceptance evidence](../../../ui_web/src/features/backtesting/ACCEPTANCE.md)
record its first Web consumer and independent generated contract. The separate
[WP8 acceptance](WP8_ACCEPTANCE.md) verifies the real IM window and Windows Chrome
→ WSL topology. Synthetic browser acceptance alone did not close that gate.
No blocking W2 acceptance or implementation drift remains; merging is a separate action.

## Acceptance boundaries

- Core synthetic acceptance verifies pure replay behavior only. The case five-day
  Performance oracles are independent of the four-session Core oracle.
- WP3 must preserve exact DataLake public bindings, W1 symbol-level import isolation
  and decision-time metadata/price separation. No private data access or second cache.
- WP4 PASS means research capability is complete: actual inputs, Core replay, case
  analysis, validated result and evidence/reproduction. It does not complete Online/Web.
- WP5 owns runtime root ignore/config handling through repository `lab_config`, an
  independent run store and online failure composition; no second executor or ledger.
- WP6 publishes the HTTP product contract/catalog/OpenAPI. WP7 replaces the planned
  `/backtesting` destination with real interaction and generated contract coverage.
- WP8 PASS is required for W2 completion. The first real research is both profiles for
  IM over 2024-01-01 through 2026-10-30 inclusive, compared with CSI 1000 Buy & Hold.
  Windows Chrome must access WSL-hosted HTTP/Web through the authenticated workflow.
  Native Windows backend execution is not required.
- All WPs retain the authorized single-position Core boundary, existing public
  DataLake/W1 contracts and sibling module behavior. No order/broker/matching,
  registry, multi-asset or future strategy scaffold is authorized.

## Deferred and known limitations

- Historical metadata and active-set decision-time availability is an explicit replay
  assumption, not proven point-in-time Source freshness. Complete exports and memory
  preload do not grant Policy future information access.
- IF/IH/IC retain semantic/synthetic coverage; real acceptance beyond IM is deferred.
- Fees, slippage, margin, funding, ETF comparison, Sharpe/risk-adjusted metrics,
  annualization, optimization and other exclusions remain outside W2 as defined by
  [Performance](PERFORMANCE.md#exclusions-and-forbidden-interpretations).
- Online list/history, cancel/delete/retry, idempotency keys, queueing, multi-process
  execution, automatic cleanup/TTL, standalone online evidence/replay endpoints,
  result CSV/copy/export and production SLA remain outside this release.
- Full canonical evidence/replay is implemented in WP4; the online result exposes its summary.
- Native Windows store/backend support and Nginx/Docker production deployment are
  Deferred / NOT RUN. Windows Chrome to WSL acceptance passed in [WP8](WP8_ACCEPTANCE.md).
- Provider freshness/correction/TTL semantics remain DataLake-owned. HTTP wire details
  and Web generated artifacts belong to WP6/WP7, not this authority reconciliation.
