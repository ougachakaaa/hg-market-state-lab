# W2 current authority reconciliation

This document specializes the [case](ARCHITECTURE.md). It owns the current
Concern → Authority → Code Consumer inventory, semantic review, implementation drift
register and reconciliation verification. It defines no alternative financial or
execution contract. Follow the linked canonical owner for each requirement;
[Roadmap](ROADMAP.md) owns delivery sequence and readiness. This is a current-state
audit, not an archive of previous designs or implementation stages.

## Authority and consumer inventory

Paths in the consumer column are relative to `market_backtesting/src/market_backtesting/`
unless prefixed with a repository module; test paths are repository-relative. Pending
consumers have no runtime/API yet.

| Concern | Canonical authority | Current / planned code consumer |
| --- | --- | --- |
| Repository module identity, Python runtime and top-level dependencies | [Root architecture](../../../ARCHITECTURE.md) | Root package configuration; architecture checks |
| Module boundary, Core/case dependency direction and navigation | [Module architecture](../../ARCHITECTURE.md) | `core/`, `cases/futures_roll_long/`, package root; `market_backtesting/tests/test_architecture.py` |
| Core identity and bounded single-instrument scope | [Core architecture](../../core/ARCHITECTURE.md) | `core/__init__.py`; pure Core import tests |
| Time advancement, Policy invocation, failure propagation, Recorder | [Core Replay](../../core/REPLAY.md) | `core/replay.py::replay`; `core/models.py::ReplaySession`, `DailyRecord`, `ReplayResult` |
| Actual/Target Portfolio, market quote selection, unique Daily PnL, reference updates, StateEvents | [Portfolio Transition](../../core/PORTFOLIO_TRANSITION.md) | `core/transition.py::transition_portfolio`; `core/models.py::Portfolio`, `TargetPortfolio`, `TransitionResult` |
| Explicit InitialCapital, Daily Return, cumulative PnL/Equity/Return | [Core Accounting](../../core/ACCOUNTING.md) | `core/accounting.py::account`; `core/models.py::AccountingState`; D1 closed below |
| W2 identity, request constraints and first real research | [Case architecture](ARCHITECTURE.md) | `application_models.py::FuturesRollRequest`, `validate_futures_roll_request`; `application.py::FuturesRollService` |
| One-lot M1 entry, expiry M1/Q1 targets, final close, real contract versus Slot | [Strategy](STRATEGY.md) | `cases/futures_roll_long/policy.py::MechanicalRollPolicy`; `cases/futures_roll_long/models.py::DecisionContext` |
| Public market facts, completeness, date-indexed facts, W1 import grant, causality assumptions | [Inputs](INPUTS.md) | Synthetic `cases/futures_roll_long/replay.py::replay_futures_roll`, `cases/futures_roll_long/validation.py`; retained `IndexClose` series; `input_validation.py`, `public_inputs.py`, `fingerprint.py`, `preflight.py` |
| W1 pure Slot semantics | [W1 Slot Resolution](../../../market_research/descriptive/cases/futures_basis/SLOT_RESOLUTION.md) | `cases/futures_roll_long/policy.py::_resolve` via the public facade only |
| Calendar / Futures / Index public facts and operations | [Calendar Service](../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md), [Futures Service](../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md), [Index Service](../../../data_lake/datasets/tushare_index_daily/SERVICE.md) | `application.py::prepare` through the three published factories; retained final exports and separate SSE Calendar prerequisite |
| W2 InitialCapital derivation, multiplier consistency, Benchmark/Excess/Drawdown, case oracles | [Performance](PERFORMANCE.md) | Synthetic capital/equity checks in `cases/futures_roll_long/replay.py`, multiplier checks in `cases/futures_roll_long/policy.py`; `cases/futures_roll_long/performance.py::analyze_futures_roll`; both five-day oracles accepted |
| BacktestResult, trades/roll projections, full evidence/replay, limitations and V2 views | [Result](RESULT.md) | `result_models.py`, `result.py`, `result_validation.py`, `visualization.py`; full portable format under [Evidence](EVIDENCE.md), `evidence_models.py` and `evidence.py` |
| Independent online request/run/store, owner isolation and failure composition | [Online Application](ONLINE_APPLICATION.md) | WP5 implemented; composes existing WP3 + WP4 pipeline |
| HTTP/OpenAPI and Web presentation | [HTTP contract](../../../ui_http/products/backtesting/http-contract.md), [HTTP catalog](../../../ui_http/HTTP_PRODUCTS.md), [Web workspace](../../../ui_web/workspace.md) | WP6 implemented in `ui_http/products/backtesting`; WP7 consumer/generated artifacts in `ui_web/src/features/backtesting` |
| Current completion, remaining WPs and acceptance boundaries | [Roadmap](ROADMAP.md) | Subsequent implementation tasks; no business runtime consumer |
| Execution policy and task navigation | [Root AGENTS](../../../AGENTS.md), [Module AGENTS](../../AGENTS.md) | Agents working in this module |

The module/Core/case entries select the next contract; formulas and detailed state,
input, result and run semantics stay in their narrowest owners. Recorder is the
in-memory construction of immutable daily records, not a new runtime framework.
Analyzer consumes accounting; it never replays transitions or creates a ledger.

## Authority change matrix

| File | Change | Reason |
| --- | --- | --- |
| [Root AGENTS](../../../AGENTS.md) | Route current state through module authority | Keep agent entry current without an implementation history |
| [Root architecture](../../../ARCHITECTURE.md) | Current package/runtime identity; remove transitional status | Root owns stable boundaries, not delivery process |
| [Module AGENTS](../../AGENTS.md) | Add current audit navigation and verification rules | Make drift and documentation checks discoverable |
| [Module architecture](../../ARCHITECTURE.md) | Separate Core/case concerns; delegate status and audit | Avoid duplicated strategy details and stale readiness |
| [Core architecture](../../core/ARCHITECTURE.md) | Navigate daily and cumulative accounting | Make Daily Return ownership explicit |
| [Core Replay](../../core/REPLAY.md) | Ordered daily flow and snapshot handoff | One clock and no second market-data selection service |
| [Portfolio Transition](../../core/PORTFOLIO_TRANSITION.md) | Real-ID quote selection; complete events versus trades | Preserve PnL attribution and exact state reconstruction |
| [Core Accounting](../../core/ACCOUNTING.md) | Canonical daily-return output/formula and fixed capital | Core owns all strategy accounting |
| [Case architecture](ARCHITECTURE.md) | First IM research scope, current navigation/status delegation | Fix the acceptance target without request defaults |
| [Strategy](STRATEGY.md) | Current Policy/Core test and failure handoff terminology | No separate holding executor |
| [Inputs](INPUTS.md) | Validated date-queryable facts and adapter/replay/transition split | Maintain price-free Policy and public upstream boundaries |
| [Performance](PERFORMANCE.md) | Consume Core returns; own cumulative excess definition | Eliminate Case-side daily-return computation |
| [Result](RESULT.md) | Projection equality, full event evidence and explicit limitations | Consume canonical values without duplicate formulas |
| [Online Application](ONLINE_APPLICATION.md) | Core/Analyzer composition and current failure vocabulary | Align planned execution with existing public failures |
| [Roadmap](ROADMAP.md) | Single current delivery view and Remaining WP2–WP8 gates | Remove completed-work instructions and duplicated history |
| This reconciliation | Current inventory, review, D1 and validation evidence | Separate implementation differences from semantic contracts |

## Current semantic review

Classifications are **Compatible**, **Requires Authority Change**, **Deferred**, or
**Blocking**. Requires Authority Change identifies a concern resolved by this
consolidation, not an outstanding competing authority. Unimplemented authorized
capabilities are Deferred delivery; a mandatory mismatch in existing code is Drift.

| # | Concern | Classification | Current resolution / evidence |
| --- | --- | --- | --- |
| 1 | Core contamination by W2 | Compatible | Core owns generic single-real-instrument replay; one lot, products and Slots belong to Policy. Architecture tests block case/upstream imports from Core and package root. |
| 2 | Unique Daily PnL owner | Compatible | Transition is the sole owner; independent PnL reconstruction and roll-gap oracle check actual incoming instrument attribution. Accounting/Analyzer consume it. |
| 3 | Daily Return ownership | Requires Authority Change | Core Accounting exclusively defines and exposes it; Case projects it. D1 is closed by immutable Core daily return and unchanged Analyzer projection. |
| 4 | Market snapshot selection | Requires Authority Change | Adapter prepares validated read-only facts, Replay hands off session inputs, Transition selects required real-instrument quotes. No second selector, Accounting lookup or post-roll Slot-based PnL identity. |
| 5 | Event reconstruction | Compatible | Full ordered StateEvents reconstruct reference/date as well as instrument/quantity; `position_changes` is the trade subset. Existing event reconstruction test covers hold and roll. |
| 6 | Case repeats Core accounting | Requires Authority Change | Performance references Core daily/cumulative outputs; Result checks projection equality. Financial formulas have one canonical owner; worked oracles are verification examples. |
| 7 | W1 Slot transitions versus W2 rolls | Compatible | Policy resolves Slots on entry/expiry decisions only. A role change alone is no trade; authorized facade symbols and architecture tests preserve isolation. |
| 8 | Look-ahead risk | Compatible | Price-free current context, configuration-only Policy and current/future Close perturbation tests enforce price isolation. Metadata/active-set point-in-time availability is an explicit assumption, not a historical freshness proof. |
| 9 | Result / Online execution model | Requires Authority Change | Result consumes Core evidence plus Analyzer; Online composes the same path. Failure stage/category vocabulary follows Policy/Core/case ownership. No separate holding executor or ledger. WP4 Result, WP5 Online and WP6 HTTP are implemented. |
| 10 | Completed work versus future Roadmap | Requires Authority Change | Package, Core and W2 adapter are present. WP2–WP8 are accepted; the Roadmap records W2 completion and the separate WP8 record owns actual execution evidence. No package/simulator recreation or dual roadmap. |
| 11 | Duplicate / contradictory authority | Requires Authority Change | Entries navigate; specialized contracts own formulas and workflows. Current audit is separate from Roadmap. No previous-version authority or compatibility chain is maintained. |
| 12 | Residual implementation mismatch | Requires Authority Change | D1 is closed with independent daily-return tests and both Performance oracles. Missing later-WP deliverables are not mislabeled as regressions. |

No Blocking semantic decision is identified. DataLake integration and bounded real
IM input acceptance are complete in WP3. Formal Result/Evidence/Views and retained-real
reproduction are complete in WP4. Online is implemented in WP5 and HTTP in WP6.
Web is implemented in WP7; full-window real E2E acceptance is **PASS** in
[WP8](WP8_ACCEPTANCE.md), completing W2. Existing DataLake/W1 contracts suffice; WP6 changes no producer
contract, financial implementation or sibling HTTP business semantics.

## Implementation drift register

### D1 — Core daily-return output (CLOSED)

| Field | Current finding |
| --- | --- |
| Authority Requirement | [Core Accounting](../../core/ACCOUNTING.md) owns daily return, cumulative PnL, Equity and cumulative return. Case consumes them unchanged. |
| Status | **CLOSED — 2026-11-11, Remaining WP2 acceptance PASS.** |
| Actual Code Behavior | Frozen `AccountingState.daily_return` starts at zero. `account()` computes and finite-validates it using fixed InitialCapital. Analyzer projects it unchanged. |
| Affected File / Symbol | [core/models.py](../../src/market_backtesting/core/models.py): `AccountingState`; [core/accounting.py](../../src/market_backtesting/core/accounting.py): `account`; [performance.py](../../src/market_backtesting/cases/futures_roll_long/performance.py): `analyze_futures_roll` |
| Acceptance / Test Evidence | `test_core_accounting.py`: initial/flat/entry, positive/negative/zero/roll, fixed capital, immutability, invalid values, cumulative/equity/daily-return overflow and simple-return sum. `test_futures_roll_performance.py`: unchanged Core projections, finite/positive equity and both independent five-day oracles. |
| Remaining Action | None for D1. No other open Implementation Drift is identified in the implemented synthetic subset. |

### D2 — Definition version confused with case identity (CLOSED)

`PreparedFuturesRollInputs.definition_version` now uses the canonical
`futures_roll_long_definition_v1`. Case, definition, result and input identities are
explicitly tested as four distinct values; no compatibility adapter exists.

No open mandatory mismatch is identified in Core/W2/HTTP/Web after WP8 acceptance.
The Web authority now accurately distinguishes Run phases (including STATUS_LOADING
and UNKNOWN_RUN), the independent SUBMITTING flag and RUN_BUSY submission feedback.
This documentation correction introduces no backend execution state.
The Index SSE Calendar prerequisite discovered in fresh-cache real acceptance is
explicitly reconciled in [Inputs](INPUTS.md#reconciled-index-calendar-prerequisite)
and implemented through the Calendar public service, without producer changes.
The register does not weaken full StateEvent reconstruction, causal price isolation,
real-instrument attribution or fail-without-partial-success requirements.

## Deferred and blocking decisions

- **Blocking: none.** D1/D2 are closed; WP2–WP8 are accepted. Full-window real IM,
  Windows Chrome → WSL and final regression evidence belongs to [WP8](WP8_ACCEPTANCE.md).
- Historical metadata availability stays an explicit research limitation. Proving
  point-in-time availability or provider-current freshness is not implied by replay.
- Excluded features and platform/deployment limitations remain in
  [Roadmap](ROADMAP.md#deferred-and-known-limitations); no framework is prebuilt for them.

## Validation evidence

Actual WP3 validation on 2026-11-11, using the repository-root Poetry
environment. Synthetic fixtures use the real W1 Slot resolver and MechanicalRollPolicy;
they do not claim real Calendar completeness or real-market acceptance.

| Command / review | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests` | PASS — 319 tests, including all 213 prior tests, public-service failure matrix, SSE prerequisite, canonical fingerprint, read-only preflight and both financial oracles |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py` | PASS — 21 tests |
| `poetry run ruff check market_backtesting` | PASS |
| `poetry run mypy market_backtesting` | PASS — 32 source files |
| `poetry run pytest data_lake/tests/test_boundary.py market_research/tests/test_boundaries.py` | PASS — 15 tests |
| `git diff --check` | PASS |
| Read-only Markdown link/anchor and navigation audit | PASS — 127 local links/anchors; Root → module → case → Inputs navigation checked |
| Full diff and ownership review | PASS — Core owns strategy accounting; case owns benchmark/risk; changes confined to `market_backtesting`, with no W1/DataLake producer, Core or Policy changes |

All 213 prior Core/Policy/Performance tests remain in the passing suite. No test was
skipped and no financial oracle or isolation assertion was removed.

### Actual five-day oracle results

The independent expected tables are in [Performance](PERFORMANCE.md#manual-independent-oracle).
The synthetic entry active months are 202601/202602/202603/202606; expiry active
months are 202602/202603/202606/202609. The February contract enters as M1 and
expires as M0; the actual resolver selects March M1 or June Q1. No resolver is mocked.

| Measure | M1 actual | Q1 actual |
| --- | ---: | ---: |
| Initial notional (CNY) | 1,200,000 | 1,200,000 |
| Daily PnL (CNY) | 0 / 10,000 / 10,000 / 4,000 / -2,000 | 0 / 10,000 / 10,000 / 1,000 / -2,000 |
| Total PnL (CNY) | 22,000 | 19,000 |
| Gross return | 0.018333333333333333 | 0.015833333333333335 |
| Benchmark return | 0.012499999999999956 | 0.012499999999999956 |
| Excess return | 0.005833333333333378 | 0.003333333333333379 |
| Strategy maximum drawdown | -0.0016339869281045694 | -0.0016380016380016515 |
| Benchmark maximum drawdown | -0.004950495049505177 | -0.004950495049505177 |

Return/drawdown comparisons use absolute tolerance 1e-15; benchmark equity uses
absolute tolerance 1e-9 CNY, with no intermediate rounding. Tests verify roll gap
exclusion, replacement reference prices, final-session PnL and flat termination,
separate running peaks and holding-period excess rather than summed daily excess.

## WP3 fake-service failure matrix

Tests use real published Export/Row/Coverage/Ensure types and documented immutable
scope/window shapes, with the actual W1 resolver and MechanicalRollPolicy.
`test_public_inputs.py` and `test_readiness.py` cover every requested matrix entry:

| Requested cases | Actual coverage |
| --- | --- |
| 1, 22 — complete inputs, M1/Q1 real-ID roll attribution | Five-session public-service executions: 22,000 / 19,000 CNY; old-contract roll PnL; replacement Close reference; terminal Flat |
| 2–3 — missing Calendar, scope/schema | Missing/duplicate dates, wrong exchange/window/schema, bool flags/counters, inconsistent coverage |
| 4–7 — Futures completeness/duplicates/metadata/delist | Final incomplete export; duplicate contract/date; identity/month/product conflicts; invalid/non-session expiry |
| 8–10 — entry/roll/Slot/Close | Missing decision/held rows, irregular active set, missing/non-finite/non-positive Close; no ensure for malformed facts |
| 11–14 — Index | Incomplete proof; wrong underlying/scope/row identity; missing CFFEX Close; duplicate/date/numeric failures; SSE-only rows retained but not replayed |
| 15–17 — operation/ensure/final export | Both public error types; ensure OperationError; malformed EnsureResult; incomplete ensure retained; final complete succeeds, final incomplete/malformed fails |
| 18–19 — fingerprint | Golden synthetic digest; full public field enumeration; ISO/float64 hex/Unicode; signed-zero and fact/proof changes; profile-independent input identity |
| 20–21 — read-only/no credential | Read-only services without ensure; poisoned preparation/replay/analyzer; missing real public caches for each dependency; Source initialization forbidden, no cache directory created |
| 23 — no successful partial result | Every failure raises typed error without replay/fingerprint success; pure category/reason/date/contract preserved |
| Additional prerequisite/boundary checks | SSE exact-window export/ensure/export; malformed SSE fails without ensure; at most one ensure; no redundant coverage; request/span validation before I/O; frozen retained inputs; authorized symbols only |

## WP3 bounded real IM acceptance

**PASS — 2026-11-11**, public production factories and API, fresh isolated temporary
Dataset storage, real Tushare data. The first attempt exposed the missing independent
SSE Calendar prerequisite; that contract gap is closed in Inputs and the successful
fresh-cache acceptance includes it. No default cache was read, changed or rebuilt.

| Proof | Actual result |
| --- | --- |
| Requested / observed window | 2025-02-17 through 2025-03-24, inclusive |
| CFFEX Calendar / auxiliary SSE Calendar | 36/36 natural-day units each, complete, zero missing/pending/failed |
| Futures / Index coverage | 26/26 product-day / index-day units, complete, zero missing/pending/failed |
| Futures rows / replay sessions | 104 real contract rows / 26 actual CFFEX sessions |
| Actual held expiry / old Close | IM2503.CFX, Source delist_date 2025-03-21, Close 6414.2 |
| M1 replacement / roll Close | IM2504.CFX / 6318.2 |
| Q1 replacement / roll Close | IM2506.CFX / 6177.4 |
| Fixed initial notional | 1,256,313.1600000001 CNY |
| M1 total PnL / gross return | 31,360.00000000003 CNY / 0.024961929078256274 |
| Q1 total PnL / gross return | 32,080.000000000102 CNY / 0.025535034592808134 |
| Benchmark return, both profiles | 0.012540726708617722 |
| Roll attribution / replacement reference / final Flat | PASS for both profiles |
| Retained-input replay and Analyzer / repeated cached execution | PASS, identical replay/performance/fingerprint |

Real canonical fingerprint (both profiles):
`0ff0446fa3f534139dc1c1d4ed3c1667fce68821e9670aa9a7116f96c9022e7b`.
Synthetic golden fingerprint:
`5edcf4bad7ff0232471cda6d83bfbf423ac27ad659bd04659863d9621377b480`.
The profile is `futures_roll_long_inputs_v1`; credentials, local paths and ensure
outcomes do not enter canonical bytes. Full final public facts were retained locally
as canonical JSON along with the acceptance summary at
`/tmp/w2-wp3-real-im-24g0cxfw/` (disposable local evidence); API results also retain typed
exports and the separate SSE prerequisite. This is not a WP4 Evidence Package.

Reproduce bounded real acceptance from the root with
`poetry run python market_backtesting/tests/real_market_acceptance.py`.
This explicit opt-in script prints its temporary artifact location, uses test-only
storage redirection permitted by DEVELOPMENT.md, and never runs in pytest. Missing
credential/Source/network yields a truthful NOT RUN report. Synthetic tests remain
independent of that environment.

## WP4 verification — 2026-11-11

**WP4 PASS.** Formal BacktestResult, complete portable evidence and offline
reproduction are implemented within the case; Core/Policy/Analyzer remain the single
execution and financial owners. Ordinary projection never reruns Replay/Analyzer.
`prepare`, `run` and `preflight` retain their WP3 behavior.

[Result](RESULT.md) owns the immutable payload and cross-field checks;
[Evidence](EVIDENCE.md) owns the separately consumable portable format/API. The only
financial-contract clarification is that Σ Daily PnL uses Core's chronological
binary64 addition order. Python 3.13's compensated `sum()` differs on real retained
inputs; validation now compares the authoritative ordered sum without rounding or
tolerance. A fixed independent binary64 sentinel test covers the distinction.

| Verification category | Actual outcome |
| --- | --- |
| Synthetic Oracle | **PASS** — M1 22,000 CNY, Q1 19,000 CNY; exact daily Core projections, unchanged Analyzer outputs, entry/hold/roll/final attribution |
| Fake-Service Integration | **PASS** — public WP3 preparation to validated Result/Evidence, request versus observed dates, final-expiry close-only, event order, immutable safe output |
| Offline Evidence Reproduction | **PASS** — both profiles, canonical fingerprint, complete ordered marks/close/open, portfolios, pricing/accounting/performance/result equality, missing/reordered/tampered/invalid evidence rejection |
| Visualization V2 | **PASS** — producer validation plus unchanged frontend `validateViewV2`; four dynamically generated synthetic views and four retained-real views, eight Vitest assertions per fixture set |
| Actual Real-Market Acceptance (bounded WP4) | **PASS** — retained real IM inputs, 2025-02-17 through 2025-03-24, both profiles, no Source acquisition |
| Online/HTTP/Web and full-window WP8 | **NOT RUN** — deferred WP5–WP8 |

Bounded IM verification uses the WP3 retained canonical JSON and public SSE Calendar
export from its isolated acceptance cache, not direct SQLite access. Both runs retain
26 sessions, 4 executions, 1 roll, 29 complete StateEvents and final Flat. Actual
M1/Q1 PnL is 31,360.00000000003 / 32,080.000000000102 CNY; gross return is
0.024961929078256274 / 0.025535034592808134; benchmark return remains
0.012540726708617722. Real contract IDs and the three-export fingerprint remain
unchanged: `0ff0446fa3f534139dc1c1d4ed3c1667fce68821e9670aa9a7116f96c9022e7b`.
SSE is retained independently and remains outside that fingerprint.

Portable packages, formal results, generated views, frontend conformance output and
acceptance report are retained outside Git at `/tmp/w2-wp4-real-im-61h8srkx/`.
This disposable verification location is not an API dependency or online store.
Repeat against any retained WP3 root with:

```bash
poetry run python market_backtesting/tests/real_result_acceptance.py --retained-root PATH
```

Missing retained inputs report NOT RUN; inconsistent evidence fails. The script
never invokes Source acquisition. Tests preserve all 319 previous regressions and
add independent Result/Evidence/V2 acceptance.

| Final required check | Outcome |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | **430 passed**, including 319 prior regressions and the isolated frontend validator subprocess |
| Snapshot authority topology / HTTP architecture / DataLake boundary / Research boundaries | **36 passed** |
| `poetry run ruff check market_backtesting` | **PASS** |
| `poetry run mypy market_backtesting` | **PASS**, 41 source files |
| `git diff --check` | **PASS** |

No architecture guard was weakened; decoder imports fit the existing authorized
public-symbol whitelist. No sibling production code or frontend schema changed.

Reconciliation Summary: **WP4 PASS**. No open Implementation Drift or blocking
semantic decision. **WP5 may start**; this delivery stops before WP5. W2 remains
incomplete pending Online/HTTP/Web and full-window WP8 acceptance.


## WP5 online application acceptance — 2026-11-11

**WP5 PASS.** The independent case-owned online facade composes the unchanged
`FuturesRollService.run` → `build_backtest_result` → `validate_backtest_result` path.
It adds no replay, PnL, return or drawdown engine. RESULT/EVIDENCE, Policy/Core,
DataLake and W1 implementation/contracts are unchanged.

### Failure reconciliation and implementation drift

The preliminary reconciliation is encoded only in [Online Application](ONLINE_APPLICATION.md#failure-classification):
`incomplete_input` retains its published name; `calendar_sse` is legal; actual
`request/export/ensure/prepare/replay/analysis` stages are retained rather than guessed
from category. Result construction/validation adds `result_validation`, publication
adds `result_publication`. Core/Case category/reason, including `invalid_numeric`,
`invalid_accounting`, `invalid_result` and `invalid_evidence`, survive safe projection.
Unknown failures become fixed `execution/internal_failure` without diagnostics/text.
There is no remaining WP5 Implementation Drift or blocking semantic decision.

### Public boundary and runtime behavior

The case package exports `FuturesRollOnlineApplication`, its factory,
`OnlineRunStatus`, `OnlineFailure` and `FuturesRollOnlineError`.
The four operations accept caller owner_scope; result returns the existing immutable
BacktestResult. Preflight remains read-only and available independently of store failure.
One process-wide guard admits one active thread across application instances; excess
submissions return run_busy before run directory creation. No queue/retry/cancel exists.
Full-result reads have one nonblocking permit; status never parses result/digest or
holds an execution-duration lock. Unknown/malformed/foreign IDs share run_not_found;
owner is excluded from public carriers and errors.

`lab_config.backtesting_run_root()` reads optional `LAB_BACKTESTING_RUN_ROOT` using
existing root configuration precedence. The CWD-independent default is the ignored
`market_backtesting/.runtime/futures_roll_long_online/` directory. POSIX capabilities
are checked before tree creation. Descriptor-relative/no-follow opens, ownership,
permissions, regular-file/nlink validation and bounded reads protect private records.
Strict JSON preserves full Result/V2 shape; the exact limit is 33,554,432 bytes.
Result bytes and SHA-256 are committed before COMPLETED, with file and directory fsync.
Terminal writes are immutable. Unpersistable failure makes reads unavailable instead
of reporting a dead worker as RUNNING; restart interrupts unfinished runs.

### Acceptance evidence

- Actual thread + fake public services + temporary POSIX store: PENDING → RUNNING →
  COMPLETED, both financial oracles (M1 22,000 / Q1 19,000 CNY), unchanged real-contract
  PnL attribution and full V2 projections; historical reads perform no service call.
- Concurrency: cross-instance busy/no directory (including admission before metadata creation), guard release, thread-start failure,
  status during execution/publication, one full reader, read_busy without queuing.
- Privacy/security: foreign/missing consistency, foreign corrupt-state isolation,
  malformed IDs before filesystem access, no public owner, root/run/result/request/state
  symlinks and unsafe permissions, wrong uid, FIFO/directory/hardlink, corrupt JSON/schema/
  versions, missing/oversized result, digest mismatch and malformed full Result/V2.
- Recovery: persisted PENDING/RUNNING interruption, all terminal states unchanged,
  orphan result hidden, failed atomic replace retains old state, terminal-persistence
  failure unavailable until restart. A separate Python process executes the actual
  pipeline and exits after result write before COMPLETED; fresh initialization reports
  INTERRUPTED and refuses the orphan result without recomputation.
- Platform/config: missing flags/dir_fd/native-Windows capability simulation before
  tree creation, absolute/no-traversal root, configuration precedence and CWD-independent
  default. Actual runtime verification is Linux; native Windows/WSL deployment NOT RUN.

### Final validation

| Command | Result |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | PASS — 527 tests |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | PASS — 21 tests |
| `poetry run pytest data_lake/tests/test_boundary.py market_research/tests/test_boundaries.py -q` | PASS — 15 tests |
| `poetry run pytest config/tests -q` | PASS — 26 tests |
| `poetry run ruff check market_backtesting config` | PASS |
| `poetry run ruff check config conftest.py` | PASS |
| `poetry run mypy market_backtesting` | PASS — 48 files |
| `poetry run mypy config/src config/tests` | PASS — 3 files |
| `git diff --check` | PASS |
| Local Markdown links/anchors and full-diff ownership review | PASS |

WP6 Python application prerequisites are satisfied. HTTP/OpenAPI, Web, real-market
online E2E and Windows Chrome → WSL acceptance remain WP6–WP8, NOT RUN here. No runtime
results, secrets or personal paths are committed. This delivery stops after WP5.

## WP6 HTTP product acceptance — 2026-11-11

**WP6 PASS.** The existing FastAPI composition root publishes the four authenticated
Backtesting operations. The catalog routes to the narrow
[HTTP contract](../../../ui_http/products/backtesting/http-contract.md); endpoint,
concrete transport schemas and runtime composition are owned by `ui_http`.
No Backtesting producer, W1 business implementation, DataLake internals or financial
formula changed. The existing composed-OpenAPI route inventory was extended by four
paths without removing any sibling assertion.

### Reconciliation and runtime

- WP5's facade and all requested public carriers were inspected before HTTP coding.
  Every non-COMPLETED result read preserves result_not_ready, including FAILED and
  INTERRUPTED. No result_unavailable or unsupported_version category was imported
  from W1. Submit preserves its persisted PENDING admission snapshot, including a
  thread-start failure whose subsequent Status is FAILED.
- The existing Auth gate runs before product parsing and supplies active user ID as
  owner_scope. Foreign/missing/malformed runs remain indistinguishable. Fixed error
  text, no-store responses and Auth's success-only Cookie renewal are preserved.
- One locked runtime holder initializes the public application once per process.
  Store initialization failure retains its usable read-only preflight facade;
  unexpected factory failure is isolated and not retried. Offline schema building
  creates neither Auth runtime nor Online Store. HTTP imports no private Store/Codec.
- Preflight projects only existing CFFEX/Futures/Index readiness, including unknown
  and unavailable. It neither acquires facts nor gates subsequent Submit.
- Metadata-only Status consumes neither reader permit. Result authorizes ownership
  before the independent nonblocking HTTP delivery permit, which spans producer
  get_result, full DTO projection/validation and bounded serialization. The producer
  retains its separate Store permit. Both busy conditions require manual retry.
- Producer result-size failures remain run failures. A tampered oversized stored
  file is already corrupt under WP5's metadata check and remains HTTP 409 corrupt;
  the complete HTTP envelope's 32 MiB delivery bound is HTTP 413 response_too_large.
  HTTP does not inspect private files or invent a different application category.

### Actual acceptance evidence

The 106 new HTTP/contract tests use actual ASGI requests with real SQLite/Argon2/JWT
Cookie Auth, temporary Store, actual worker and synthetic public services. Coverage
includes strict four-field input, canonical enums/dates and semantic validation before
runtime access; valid-shaped duplicate keys, missing/ambiguous headers, compressed
body rejection and streamed 4 KiB limit independent of Content-Length; active-user
and origin ordering; owner privacy; five states and startup/recovery failures;
busy before a second Run; both reader permits and serialization-time contention;
corrupt metadata/results, request association, exact and real 32 MiB response bounds,
permit release after exceptions and metadata-only Status reads.

Both M1/Q1 financial oracles pass through HTTP: 22,000 / 19,000 CNY, unchanged real
contract roll attribution, session dates, daily/summary/returns/drawdown, decimal-ratio
units and evidence fingerprint. The complete parsed Result equals the producer's
full dataclass projection, not an independently computed HTTP result.
Offline OpenAPI tests resolve the complete concrete DTO graph, including V2 axes,
bindings/lines/marks/events/layout/presentation, Cookie security, statuses, no-store
headers, strict request fields and absence of 422. Architecture tests enforce the
public facade and prohibit reverse dependencies. Existing generated contracts remain
byte-current; no Backtesting frontend schema or consumer was created.

| Verification | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | PASS — 527 tests, retaining all WP2–WP5 financial/security/concurrency/recovery regressions |
| `poetry run pytest ui_http/tests -q` | PASS — 588 tests, including 106 new Backtesting HTTP/contract tests |
| Snapshot authority topology, DataLake boundary, Research boundary, config and Web contract-export tests | PASS — 58 tests |
| Snapshot authority topology + HTTP architecture after navigation updates | PASS — 23 tests |
| `poetry run ruff check market_backtesting ui_http config` | PASS |
| `poetry run mypy market_backtesting` / `poetry run mypy ui_http` | PASS — 48 / 62 files |
| `npm run contract:check` in ui_web | PASS — all six existing OpenAPI and TypeScript contract pairs unchanged |
| Existing `npm run test:auth-browser`, with isolated Backtesting runtime root | PASS — real Chromium registration, CLI approval, login, both MO fixture products, reload, logout and Cookie/privacy checks |
| Markdown navigation/relative links, full diff and `git diff --check` | PASS |

Runtime verification is Linux and synthetic HTTP acceptance. Native Windows Store
support, W2 Web/real-market online E2E, full-window IM and Windows Chrome → WSL
acceptance are not claimed; the latter delivery gates remain WP7/WP8. Existing
Starlette/httpx and browser Ant Design deprecation notices do not affect acceptance.
No open WP6 implementation drift or blocking semantic decision remains.
**WP7 may begin.** This delivery stops after WP6.


## WP7 Web integration — 2026-11-12

**WP7 PASS.** No open WP7 implementation drift or blocking semantic decision remains.

The formal [Backtesting Web feature](../../../ui_web/src/features/backtesting/ARCHITECTURE.md)
now owns interaction and rendering at `/backtesting`. It independently consumes the
four unchanged WP6 endpoints through same-origin protectedRequest and feature-owned
generated OpenAPI/TypeScript. The other six consumers retain byte-current artifacts.
No Core/Policy/Performance/Input/Result/Online implementation, W1 business semantics,
DataLake boundary or generic V2 schema was changed.

Reconciliation explicitly keeps preflight advisory: unlike the Research consumer,
ready=false never gates Submit. Form state and accepted immutable Run request stay
separate. Only an explicit click submits; admission is guarded synchronously and
POST is never replayed. Status/result failures have separate manual GET recovery.
URL refresh/history cancel obsolete reads; request, Run, profile/definition and V2
validation precede rendering. 401 belongs to the application authentication boundary.

Result Summary, returns/drawdown, formal executions/rolls and online evidence are
producer-owned projections. The Web formats ratios/CNY without financial computation.
Evidence is a read-only summary; no full offline package/download is implied.

Actual commands, counts, synthetic Chromium evidence and known limits are recorded
once in [WP7 acceptance](../../../ui_web/src/features/backtesting/ACCEPTANCE.md).
At the WP7 gate, full-window real IM and Windows Chrome → WSL acceptance were NOT RUN;
their subsequent result is recorded in [WP8](WP8_ACCEPTANCE.md). WP7 alone made no W2
completion or provider freshness claim. No new semantic decision was needed for this consumer.

## WP8 final reconciliation — 2026-11-12

**WP8 PASS; W2 complete within its declared scope.** The independent
[WP8 acceptance record](WP8_ACCEPTANCE.md) owns actual environment, exact requests,
real coverage, Run IDs, financial/roll summaries, input identity, offline reproduction,
Windows screenshots, performance observations and regression results.

The full-window Python, actual authenticated HTTP worker and visible Windows Chrome
runs use the same public exports and fingerprint. Pure offline reproduction rebuilds
both complete Results and StateEvent chains. Core remains the sole Transition/PnL/
Accounting owner; Analyzer owns benchmark/excess/drawdown; HTTP and React project
producer outputs. No financial implementation, W1/DataLake public contract, HTTP DTO,
OpenAPI or generated Web contract changed. No synthetic fixture supplies WP8 market facts.

Controlled busy/reader/failure/crash/401/network tests and synthetic browser regressions
remain explicitly distinct from actual real-market executions. All required regressions,
module checks and authority navigation checks pass. No blocking semantic decision or
implementation drift remains. Windows-native backend/store, production deployment,
other-product real acceptance and W3 remain outside this delivery. The branch is ready
for merge review; this task does not merge it.

## W2 final acceptance gate hardening — 2026-11-12

**Exit-code defect fixed; no production financial, HTTP or Web behavior changed.**
The final review found a harness defect, not a product defect: PASS was not the only
exit-0 outcome. The Python harness exited 0 for `PARTIAL`/`NOT RUN`, and `--mode
reproduce` exited 0 without retained evidence. The Node orchestrator could exit 0 after
a FAILED/NOT RUN HTTP stage, wrote `http-acceptance.json` PASS before a later Windows
failure, and did not require Python/offline-reproduction prerequisites. A failed Python
attempt could also read a prior `python-acceptance.json` PASS.

### Implemented acceptance contract

- Both harnesses map PASS → 0, FAIL → 1, PARTIAL → 2, NOT RUN → 3; unknown status or
  missing required evidence is nonzero.
- Python writes a fresh `RUNNING` report with `run_id`/`generated_at` before any market
  operation, clears the previous round's per-profile evidence/result files, and fails
  closed on unexpected errors. A previous PASS is never silently preserved.
- `--mode reproduce` requires a PASS Python acceptance with `same_input`, revalidates
  both evidence packages and retained Results, checks the accepted fingerprint, writes
  `offline-reproduction.json` with the same acceptance `run_id`, and exits nonzero on
  missing evidence or mismatch.
- The Node gate validates Python and reproduction prerequisites before starting HTTP,
  removes stale HTTP/Windows artifacts before those stages, requires authenticated HTTP
  PASS and an actual Windows Chrome process (exit 0, version present, no page errors,
  both profiles PASS and both full-page screenshots regenerated), and combines the four
  stages so no later success can mask an earlier failure.
- Provider/credential unavailability remains `NOT RUN` rather than a product failure;
  it is still nonzero because the gate is not closed.

### Automated verification

| Check | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests/test_wp8_acceptance_exit.py -q` | PASS — 13 tests; PASS 0, FAIL/PARTIAL/NOT RUN nonzero, stale-PASS invalidation, missing/corrupt evidence, credential-free reproduction |
| `npx vitest run scripts/wp8_acceptance_status.test.mjs` (in `ui_web`) | PASS — 15 tests; exit mapping, stage combination, stale/missing Python acceptance, reproduction identity, HTTP and Windows evidence completeness, Windows-not-executed cannot PASS |

### Retained evidence cross-check

The retained WSL artifact directory `/tmp/w2-wp8-real-im` still exists and was inspected
read-only. The full fact table and NOT RUN scope are recorded in
[WP8 acceptance](WP8_ACCEPTANCE.md#final-acceptance-gate-hardening--2026-11-12). This
review independently confirmed:

- window `2024-01-02` → `2026-10-30`, 683 CFFEX sessions, 2,732 Futures rows, 683 Index
  rows and both index closes;
- M1 33 rolls / Q1 11 rolls, final exits 6130.0 / 6081.0, and both financial summaries;
- the single input fingerprint `b83a38c9bdc83f082eda87e93c1babdb9950dacad1e316b4186a2e07e0ef557c`;
- HTTP Result payload `data` equality with the retained producer Result and the recorded
  HTTP/Windows Run IDs; valid Windows full-page PNG evidence for both profiles;
- offline reproduction from a copy of the retained evidence: PASS (exit 0), 750 / 706
  StateEvents, same fingerprint.

Real acquisition, authenticated HTTP worker execution and Windows Chrome were **NOT RUN**
again in this review. They remain the historical WP8 evidence; this is not a new
real-market run or a Source-freshness claim.

### Final architecture reconciliation

| Requirement | Evidence | Result |
| --- | --- | --- |
| Core Position-Driven Replay/Transition/Accounting ownership stable | Core architecture tests, pure-Core import isolation, 540 backtesting tests | PASS |
| Policy does not calculate PnL/returns/drawdown | `policy.py` contains no such computations; Core owns Transition/PnL and Accounting | PASS |
| Input Preparation uses only DataLake public Application Services | `test_source_uses_only_authorized_datalake_public_boundaries` enumerates the three services and input-module whitelist | PASS |
| W1 Slot Resolver is a pure function dependency only | `test_only_authorized_w1_symbols_are_imported` symbol whitelist; no Observation/Report/Statistics/Publication/Online consumption | PASS |
| Analyzer consumes only formal Performance/accounting | `analyze_futures_roll` projects Core records and owns only benchmark/excess/drawdown | PASS |
| Result/Evidence do not repeat financial calculation | projection equality, evidence reproduction and `result_validation` checks; WP8 cross-check matched payload `data` exactly | PASS |
| Online Store isolated from Research/Publication/Workbench | independent case-owned store and application tests; no W1 identity/store reuse | PASS |
| HTTP is transport only; Web is interaction/display only | 588 HTTP tests; HTTP DTO fields inspected; React formatting only (`presentation.ts`, `Result.tsx`) | PASS |
| Auth/Owner isolation not regressed | authenticated HTTP/owner tests plus retained WP8 privacy evidence | PASS |
| Generated OpenAPI/TypeScript freshness | `npm run contract:check`: all seven pairs current | PASS |
| Progressive Disclosure navigation | root → module → case navigation now routes EVIDENCE and WP8 evidence; topology 13 tests | PASS |
| No Holding V0 / stale design / duplicate authority | architecture test asserts `holding.py`/legacy pipeline absent; stale README and ONLINE_APPLICATION "planned page" statements corrected | PASS |

The only documentation drift found was outside the specialized contracts: README still
described W2 as WP1-only with no PnL/HTTP/Web, and `ONLINE_APPLICATION.md` still called
`/backtesting` a planned page. Both were corrected; no historical execution evidence was
rewritten.

### Regression and merge readiness

| Check | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q` | PASS — 540 tests (WSL Linux) |
| `poetry run pytest ui_http/tests -q` | PASS — 588 tests |
| `poetry run pytest market_research/tests -q` (W1) | PASS — 1,270 tests, 1 skipped (WSL Linux) |
| `poetry run pytest config/tests -q` | PASS — 26 tests |
| Snapshot authority topology / DataLake boundary / Research boundary | PASS — 13 / 15 tests |
| `poetry run ruff check market_backtesting ui_http config` | PASS |
| `poetry run mypy market_backtesting` / `poetry run mypy ui_http` | PASS — 50 / 62 files |
| `npm run contract:check` | PASS — seven OpenAPI/TypeScript pairs current |
| `npm run test` | PASS — 48 files, 442 tests (WSL Linux) |
| `npm run build` / `npm run lint` | PASS |
| `npm run test:backtesting-browser` | PASS — Linux Chromium, synthetic public-service fixtures |
| `git diff --check` | PASS |
| Secret/large-file/personal-path diff scan | PASS |

`origin/develop` remains `42cfd38ba4bfbedf3cd37ee975557dfc3be7793d`; the merge base is
that commit, and the branch was 13 commits ahead / 0 behind before this commit (14 / 0
after it). The merge is a fast-forward with no textual or semantic conflict. W1 and the
other products' regressions pass; no secrets, Auth database, runtime store or real
market payload enters Git.

**Merge readiness: PASS.** The exit-code/exit-artifact defect is closed, retained WP8
evidence is consistent, regression and architecture checks pass, and no blocking
authority or implementation drift remains. The current review's real-market/HTTP/Windows
re-execution is explicitly NOT RUN and does not invalidate the recorded WP8 PASS.
