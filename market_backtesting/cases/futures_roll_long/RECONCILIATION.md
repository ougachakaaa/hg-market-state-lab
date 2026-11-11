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
| W2 identity, request constraints and first real research | [Case architecture](ARCHITECTURE.md) | Synthetic product/profile validation; public request/API pending WP3 |
| One-lot M1 entry, expiry M1/Q1 targets, final close, real contract versus Slot | [Strategy](STRATEGY.md) | `cases/futures_roll_long/policy.py::MechanicalRollPolicy`; `cases/futures_roll_long/models.py::DecisionContext` |
| Public market facts, completeness, date-indexed facts, W1 import grant, causality assumptions | [Inputs](INPUTS.md) | Synthetic `cases/futures_roll_long/replay.py::replay_futures_roll`, `cases/futures_roll_long/validation.py`; retained `IndexClose` series; DataLake preparation/preflight pending WP3 |
| W1 pure Slot semantics | [W1 Slot Resolution](../../../market_research/descriptive/cases/futures_basis/SLOT_RESOLUTION.md) | `cases/futures_roll_long/policy.py::_resolve` via the public facade only |
| Calendar / Futures / Index public facts and operations | [Calendar Service](../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md), [Futures Service](../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md), [Index Service](../../../data_lake/datasets/tushare_index_daily/SERVICE.md) | W2 public Input Adapter pending WP3 |
| W2 InitialCapital derivation, multiplier consistency, Benchmark/Excess/Drawdown, case oracles | [Performance](PERFORMANCE.md) | Synthetic capital/equity checks in `cases/futures_roll_long/replay.py`, multiplier checks in `cases/futures_roll_long/policy.py`; `cases/futures_roll_long/performance.py::analyze_futures_roll`; both five-day oracles accepted |
| BacktestResult, trades/roll projections, full evidence/replay, limitations and V2 views | [Result](RESULT.md) | Existing synthetic `DailyProjection`/`Execution`/`RollEvent`; full result/evidence/projection pending WP4 |
| Independent online request/run/store, owner isolation and failure composition | [Online Application](ONLINE_APPLICATION.md) | Pending WP5; consumes Core + Analyzer + Result |
| HTTP/OpenAPI and Web presentation | [HTTP architecture](../../../ui_http/ARCHITECTURE.md), [HTTP catalog](../../../ui_http/HTTP_PRODUCTS.md), [Web workspace](../../../ui_web/workspace.md) | Pending WP6/WP7; no W2 endpoint, DTO or active feature claimed |
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
| 9 | Result / Online execution model | Requires Authority Change | Result consumes Core evidence plus Analyzer; Online composes the same path. Failure stage/category vocabulary follows Policy/Core/case ownership. No separate holding executor or ledger. Implementation remains WP4/WP5. |
| 10 | Completed work versus future Roadmap | Requires Authority Change | Package, Core and W2 synthetic adapter are present. WP2 is accepted and WP3–WP8 remain pending; no package/simulator recreation or dual roadmap. |
| 11 | Duplicate / contradictory authority | Requires Authority Change | Entries navigate; specialized contracts own formulas and workflows. Current audit is separate from Roadmap. No previous-version authority or compatibility chain is maintained. |
| 12 | Residual implementation mismatch | Requires Authority Change | D1 is closed with independent daily-return tests and both Performance oracles. Missing later-WP deliverables are not mislabeled as regressions. |

No Blocking semantic decision is identified. DataLake integration,
Result/Evidence, Online, HTTP/Web and real acceptance are **Deferred** to their assigned
WPs, not evidence of completed W2. Existing DataLake/W1 contracts and HTTP/Web planned
boundaries suffice; this reconciliation changes no producer contract or sibling code.

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

No other mandatory mismatch is identified in the existing Core/W2 synthetic subset.
The register does not weaken full StateEvent reconstruction, causal price isolation,
real-instrument attribution or fail-without-partial-success requirements.

## Deferred and blocking decisions

- **Blocking: none.** D1 is closed and Remaining WP2 is accepted; WP3 can start.
- **Deferred delivery:** public facts integration/preflight (WP3), full Result/Evidence (WP4), Online mapping/store (WP5),
  HTTP/OpenAPI (WP6), Web (WP7), real IM and Windows Chrome → WSL acceptance (WP8).
- Historical metadata availability stays an explicit research limitation. Proving
  point-in-time availability or provider-current freshness is not implied by replay.
- Excluded features and platform/deployment limitations remain in
  [Roadmap](ROADMAP.md#deferred-and-known-limitations); no framework is prebuilt for them.

## Validation evidence

Actual Remaining WP2 validation on 2026-11-11, using the repository-root Poetry
environment. Synthetic fixtures use the real W1 Slot resolver and MechanicalRollPolicy;
they do not claim real Calendar completeness or real-market acceptance.

| Command / review | Actual result |
| --- | --- |
| `poetry run pytest market_backtesting/tests` | PASS — 213 tests, including original Core/Policy regressions, daily accounting, five-day oracles, input validation, causality and architecture/import isolation |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py` | PASS — 21 tests |
| `poetry run ruff check market_backtesting` | PASS |
| `poetry run mypy market_backtesting` | PASS — 22 source files |
| `git diff --check` | PASS |
| Read-only Markdown link/anchor and navigation audit | PASS — 145 local links/anchors; Root → module → case → Inputs/Performance reachable |
| Full diff and ownership review | PASS — Core owns strategy accounting; case owns benchmark/risk; changes confined to `market_backtesting`, with no W1/DataLake producer or Policy changes |

An initial Mypy run identified a missing type annotation in the new accounting test;
it was corrected before the passing run above. Ruff formatting/import fixes were
also applied before final acceptance. No test was skipped or assertion weakened.

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

Real DataLake acquisition/integration, complete BacktestResult/Evidence/Views,
Online/HTTP/Web and Windows Chrome → WSL E2E are **NOT RUN**, pending WP3–WP8.

Reconciliation Summary: **PASS** for Remaining WP2. D1 is closed, no open
Implementation Drift is identified in the implemented subset, and WP3 is the next
implementation entry under [Inputs](INPUTS.md). W2 delivery remains incomplete.
