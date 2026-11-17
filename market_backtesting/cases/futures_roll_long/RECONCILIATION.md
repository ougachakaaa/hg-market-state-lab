# W2 current authority reconciliation

This document specializes the [case](ARCHITECTURE.md). It owns the current
Concern → Authority → Code Consumer inventory, semantic review, implementation drift
register and links to reconciliation verification. It defines no alternative financial or
execution contract. Follow the linked canonical owner for each requirement;
[Roadmap](ROADMAP.md) owns delivery sequence and readiness. This is a current-state
audit. Dated implementation and validation records are preserved separately in
[Acceptance history](ACCEPTANCE_HISTORY.md); [WP8 acceptance](WP8_ACCEPTANCE.md)
records the original real-market delivery. Neither is a rerun of current code.

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

## Storage WP6 final status (2026-11-13)

The [Storage WP2 verdict](ACCEPTANCE_HISTORY.md#storage-wp2-execution-evidence) is historical execution evidence. WP3 subsequently replaced
the W1 POSIX store, so the full-HTTP-red and W1 follow-up statements it records no longer
describe current behavior. Storage WP6 executed W1, W2 and Publication storage acceptance
on native Windows, WSL2 Ubuntu and Linux Docker; native Linux outside WSL remains
**NOT RUN**. W2 financial oracles, owner/isolation, atomic result+COMPLETED, recovery,
bounded reads and HTTP projection were re-exercised without semantic change.

Current evidence, cross-platform matrix, remaining risks and the merge recommendation are
owned by
[Storage reconciliation](../../../market_research/STORAGE_RECONCILIATION.md#storage-wp6-execution-evidence).
This section does not rewrite the historical WP1/WP2 evidence or the original W2 delivery
numbering.
