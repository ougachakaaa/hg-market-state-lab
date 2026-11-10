# W2 Futures Roll Long work packages, reconciliation and readiness

This document specializes the [case](ARCHITECTURE.md). It owns W2 delivery boundaries,
work-package acceptance, reconciliation and deferred scope. It does not duplicate
strategy formulas, accounting formulas, result schemas or run internals.

Baseline: `46046ff9159824321c39441e89915327711eeb1f`.
Working branch: `feat/w2-futures-roll-backtest`.
WP0 is a documentation/authority gate. WP0–WP8 are sequential; every WP must be
independently reviewable, committable and accepted. A later unfinished WP never fails
an earlier WP's bounded acceptance, but no WP may claim another WP's deliverables.

## Work packages

| WP | Scope and required deliverables | Dependency | Definition of Done / acceptance | Forbidden scope |
| --- | --- | --- | --- | --- |
| WP0 — Semantic Authority & Reconciliation | This authority topology, Strategy, Accounting, Inputs, Result, Online and Roadmap; root/module mapping, dependency direction and navigation; Reconciliation | — | All links/anchors/reachability pass; one semantic owner per concern; formulas/units/manual oracle reviewable; no Blocking; `git diff --check`; Markdown-only commit | Production code, dependency changes, market data, HTTP/Web, runtime |
| WP1 — Strategy & Holding Simulation | Module package skeleton; pure deterministic holding simulation from validated synthetic inputs; real-contract entry/hold/roll/exit; executions/roll events | WP0 | Synthetic five-session fixtures; both profiles; expiry-day inclusion; final-day close-only; W1 Slot mapping change without trade; missing/irregular metadata, missing price, expired-without-roll, invalid target, no silent skip/fill; no PnL or upstream I/O | PnL/accounting, DataLake acquisition, Result/Views, online, HTTP/Web, W1 modification |
| WP2 — PnL & Benchmark Accounting | Initial notional, daily PnL, roll accounting, equity, returns, benchmark, excess, drawdown | WP1 | Independent manual oracle (both profiles) passes; roll contributes no cross-contract gap; entry/final attribution; benchmark and running-peak drawdown; zero/negative equity and multiplier mismatch fail; no market I/O | Strategy rule changes, DataLake I/O, Result/Views, online, HTTP/Web |
| WP3 — DataLake Integration & Real Backtest Python API | Public Calendar/Futures/Index preparation; exact completeness validation; authorized Slot adapter; canonical input fingerprint; read-only preflight; public Python backtest API; bounded real IM acceptance | WP2 | Fake-service completeness/failure matrix; exact scope/window/counters; deterministic fingerprint; public import boundary; complete final exports; bounded real IM evidence; no Snapshot/private access or second cache | W1 observation/report consumption, second provider/cache, HTTP/Web, online store |
| WP4 — Backtest Result, Evidence & Visualization Projection | Stable result profile; evidence summary/package; V2 returns/drawdown views; reader projection; limitations; cross-field invariants | WP3 | Result schema/version; all invariants; V2 validation; manual oracle; deterministic evidence/replay; WP4 PASS = core research capability complete | HTTP/Web, online store, generic visualization schema, W3 financial features |
| WP5 — Online Backtest Application & Run Store | Online composition of the WP3 preflight plus submit/status/result application; owner scope; single worker/busy; disposable file store; atomic result publication; startup recovery; bounded result reads | WP4 | Fake-service state matrix; busy/no queue; owner isolation; restart interruption; orphan result handling; size/corruption/unsupported platform; no HTTP/UI | HTTP/UI, Publication, Workbench, multi-process/queue, W1 store reuse |
| WP6 — HTTP Product & OpenAPI | HTTP contract; strict parsing/limits; run/result DTO projection; Auth/owner/error mapping; OpenAPI; no financial recomputation | WP5 | Strict request/auth/error/limit tests; OpenAPI/freshness prerequisites; result/run/request association; preflight and no-store behavior; Web untouched | Web UI, business logic, W1 product changes, financial recomputation |
| WP7 — Web UI Backtesting Integration | `/backtesting` page: Ant Design controls, preflight/readiness, submit/poll, V2 return/drawdown charts, trades/rolls, evidence/limitations, busy/error/failed/interrupted states; generated contracts | WP6 | `npm run contract:check`, Vitest, build, lint; deterministic browser tests; no fake result/control; no React financial computation; planned page honestly replaced | Financial calculation, backend bypass, generic chart DSL, CSV/export/copy not authorized by W2 v1 |
| WP8 — Real-Market E2E Acceptance & Reconciliation | WSL2 FastAPI + Vite + Windows Chrome real IM workflow; login → preflight → submit → poll → result → charts → trades → evidence; restart/busy/ownership/failure; final reconciliation | WP7 | Explicit real IM window with at least one roll and final exit; real data not substituted by synthetic; all workflow states; Windows Chrome browser → WSL HTTP/Web local end-to-end acceptance; W1 regression; no W3 features; external evidence; WP8 PASS permits W2 completion | W3 fees/slippage/ETF/margin/funding/optimization; production deployment promise; unverified platform claims |

### Work-package boundaries

- WP4 PASS means the core research capability is complete. It does not mean the HTTP
  product or Web workflow is complete.
- WP8 PASS is required before W2 is declared complete. It includes a Windows Chrome
  browser accessing the WSL-hosted HTTP/Web service in a local end-to-end workflow.
  Running the backend natively on Windows is not required. Nginx/Docker production
  deployment is recorded as NOT RUN/Deferred and is not part of the W2 completion claim.
- WP1 creates the Python package and must update the root package manifest, pytest
  testpaths/pythonpath, Ruff/Mypy source lists and the repository package-list
  architecture assertion at that time. WP0 intentionally does not pre-create these.
- WP5 adds the runtime root ignore rule and the `LAB_BACKTESTING_RUN_ROOT` handling.
  WP0 defines the semantic/config boundary but creates no runtime.
- WP6 creates the HTTP product contract and catalog entry. WP7 creates the frontend
  feature, generated OpenAPI/TypeScript artifacts and contract-freshness coverage.
  WP0 creates neither a fake contract nor a fake feature.
- No WP may introduce a generic backtesting engine, plugin/registry, portfolio
  framework, multi-strategy abstraction or future strategy scaffold.
- Every WP must keep W1 public contracts, DataLake public contracts, Snapshot,
  Statistics and Modeling behavior unchanged unless its own explicit authority change
  is approved.

## Mandatory reconciliation

Classifications are exactly **Compatible**, **Requires Authority Change**, **Deferred**
or **Blocking**.

| # | Reviewed boundary | Classification | Resolution |
| --- | --- | --- | --- |
| 1 | Root Architecture ↔ new `market_backtesting` module | **Requires Authority Change** | WP0 adds the module mapping, runtime-layout entry, ownership section, dependency direction, analytical/HTTP topology and navigation. Reverse dependency is prohibited. |
| 2 | `market_research` ↔ Strategy/Backtesting | **Compatible** | Research already excludes strategies/backtests from its ownership. W2 owns strategy/position/PnL/result. W2 consumes only the pure Slot boundary, not Research observations, reports, statistics, publications or online runs. |
| 3 | `market_modeling` reserved status | **Compatible** | Modeling remains reserved; W2 is a sibling analytical module. No model/signal/backtest abstraction is inferred into or from Modeling. |
| 4 | DataLake public facts ↔ Backtest inputs | **Compatible** | Existing Calendar/Futures/Index public services and completeness proofs are sufficient. W2 requires complete final exports and adds no Dataset, cache, provider or private persistence access. |
| 5 | W1 Slot Resolver reuse | **Requires Authority Change** | Root Architecture and [Inputs](INPUTS.md) grant a symbol-level consumer permission for the existing public pure Slot boundary. W1 code/contracts/behavior are unchanged. WP1/WP3 must add an import-name architecture test. If the facade cannot preserve the intended isolation, WP1 must escalate; copying the algorithm is forbidden. |
| 6 | PnL Accounting ↔ W1 Basis Definition | **Compatible** | W2 uses real contract Close-to-Close × multiplier and an index-equivalent denominator. W1 basis/annualized basis is not a W2 input or return. No shared formula is reinterpreted. |
| 7 | Online Run ↔ W1 Run Store | **Compatible** | W2 reuses validated lifecycle principles but has an independent run ID, store, owner scope and result. W1 store semantics and data are unchanged. The run is not Publication or Workbench. |
| 8 | HTTP Auth, OpenAPI and Web Workspace | **Requires Authority Change** (Auth itself is **Compatible**) | WP0 fixes ownership and planned status in repository/`ui_http`/`ui_web` authorities. WP6 authors the HTTP contract/DTO/OpenAPI; WP7 authors the frontend feature/generated contract. Existing Auth is reused unchanged; no fake contract/feature is created in WP0. |
| 9 | Visualization V2 ↔ Backtest projection | **Compatible** | W2 projects producer values into existing V2 date-series line/event/detail structures. No V2 schema change, financial field or frontend recomputation. |
| 10 | W2 ↔ W3 completion boundary | **Compatible** | W2 explicitly excludes fees, slippage, taxes, margin, funding, settlement cash flow, dividends, ETF comparison, roll-yield decomposition and optimization. W3 requires a new authority/version; W2 creates no placeholders or generic framework. |

No **Blocking** item remains after WP0. The only pre-resolution blocking candidate was
the cross-module Slot reuse (#5); it is resolved by the explicit root/Inputs consumer
grant, the unchanged W1 public boundary and the WP1/WP3 import-name check. WP1 may begin
without guessing business semantics.

## Deferred and known limitations

- Real-market acceptance for IF/IH/IC beyond IM is not required by WP8; those products
  must retain semantic/synthetic coverage and may be bounded real-verified later.
- Full online evidence/replay is not part of W2 v1. The result carries evidence summary,
  fingerprint, coverage and limitations; the complete canonical package/replay belongs
  to the WP4 case-owned evidence boundary.
- Windows-native backend/online-store execution and Nginx/Docker production deployment
  are not W2 completion requirements; they are recorded as NOT RUN/Deferred. Windows
  Chrome accessing the WSL service is required by WP8.
- Run list/history, cancel, delete, retry, idempotency keys, queueing, multi-process
  execution, automatic cleanup/TTL and production SLA remain out of scope.
- CSV/copy/export of backtest results, strategy optimization, ETF comparison, margin
  account return and risk-adjusted metrics are not part of W2 v1.
- DataLake provider-current freshness, correction/TTL policy and stale semantics remain
  owned by DataLake; W2's complete cache coverage is not a freshness claim.
- The exact HTTP paths/DTOs/statuses and the Web feature/generated artifacts are WP6/WP7
  deliverables, not WP0 claims.

## WP0 verification and handoff

WP0 is documentation-only. Required checks:

- Markdown relative links resolve and changed/new anchors match their headings;
- the new module, case and specialized authorities are reachable from the root entry;
- no link points to a file that does not yet exist;
- one canonical semantic owner per formula/state/result/run concern;
- W1 public code/docs are unchanged; no production code, config, test or runtime state
  was added;
- `git diff --check` passes;
- the committed diff consists only of Markdown/Authority/Navigation files.

The existing topology test may be run with the system pytest without a project virtual
environment using `--noconftest`; the full Python/HTTP/Web matrices, real acquisition,
browser E2E and WP1–WP8 implementation tests are **NOT RUN** in WP0 and must not be
reported as passing.

WP0 PASS means this authority gate is complete and WP1 is implementation-ready. It does
not mean any runtime, HTTP, Web or real-market capability exists. WP0 stops after its
independent commit; WP1 is not started automatically.

## WP1 implementation readiness

WP1 is **Implementation Ready** once WP0 passes. Its minimal starting point is:

1. create the `market_backtesting` package skeleton and root build/test registrations;
2. implement the pure real-contract state machine from
   [Strategy](STRATEGY.md) using synthetic session/contract inputs;
3. implement executions/rolls and the failure matrix, without PnL/accounting, public
   DataLake I/O, result/views, online store, HTTP or Web;
4. add the architecture test that restricts W2's Research imports to the authorized
   pure Slot symbols;
5. keep W1 and all sibling module behavior unchanged.

WP2 accounting, WP3 upstream integration and WP4 result projection remain later,
separate work packages. No WP1 coding agent may invent strategy/PnL/result semantics
outside this authority.
