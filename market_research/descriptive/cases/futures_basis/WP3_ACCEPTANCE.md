# WP3 Basis Observation acceptance

This records bounded implementation evidence, not new business semantics. Enter via
[Case](ARCHITECTURE.md) or [Roadmap](ROADMAP.md). Input semantics remain owned by
[Inputs](INPUTS.md), financial derivation by [Definition](DEFINITION.md), and validity
by [Observation](OBSERVATION.md).

## Runtime acceptance

WP3 Runtime **PASS**, 2026-11-06. Branch `feat/r01-futures-basis-research`, required
baseline `c741c7ca49944b236c999e6b89193c435f3b322c`. One independent Case facade:
`market_research.descriptive.cases.futures_basis` publishes:

- `FuturesBasisRequest`, `PreparedFuturesBasisInputs`, `FuturesBasisResult`.
- `prepare_inputs`, pure `construct_observations`, `observe_futures_basis`.
- Frozen Contract-day / Slot-day, outcome/accounting and source-association carriers;
  explicit `InputPreparationError` / `ObservationConstructionError`.
- Existing WP2 resolution, evidence and transition APIs remain available unchanged.

Verification: **138** focused WP3/WP2 tests and **1201** combined Research /
authority-topology / architecture tests passed. Ruff, MyPy (including explicit
source checking and stricter checking of new test bodies), public import smoke
and `git diff --check` passed.

Synthetic acceptance covers all 16 requested scenarios plus malformed public facts,
nullable listing-day fields, dual-calendar disagreement, illegal proof/ensure,
wrong identities, all four published products, numerical overflow/underflow,
retained stage failures, prepared-input tampering and the live oracle/isolation.
Golden bytes come from an independent public-fake fixture, with fixed SHA-256
`f9990fff3ba3de740e04ae2a0c468dde881ffe70486fa68b8d2351d05e48d224`.
Independent high-precision Decimal calculations distinguish log annualization from
linear annualization. Synthetic evidence is separate from the real run below.

Reproduce from repository root:

```bash
poetry run pytest -q market_research/tests/test_futures_basis_observation.py market_research/tests/test_futures_basis_slot_resolution.py
poetry run pytest -q market_research/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_research
poetry run mypy market_research/src/market_research/descriptive/cases/futures_basis market_research/tests
poetry run python -c 'from market_research.descriptive.cases.futures_basis import FuturesBasisRequest, PreparedFuturesBasisInputs, FuturesBasisResult, prepare_inputs, construct_observations, observe_futures_basis'
git diff --check
```

The second pytest invocation includes authority links/reachability and necessary
Research/architecture regression. No Web E2E, Statistics or Publication/HTTP
functional test matrix is added; existing Research regressions remain included.

## Real IM acceptance

Real-market **PASS**, independently of synthetic acceptance. Scope is explicitly
IM / `000852.SH`, inclusive `2026-10-12..2026-10-23`, without Horizon.
Source facts came from the three selected public DataLake services using the
published Calendar/Futures/Index views. No Snapshot or alternative Source was used.

| Proof / population | Result |
| --- | --- |
| CFFEX Calendar natural dates | 12 / 12 complete |
| SSE Calendar natural dates | 12 / 12 complete |
| Futures product-days | 10 / 10 complete |
| Index sessions | 10 / 10 complete |
| CFFEX candidate dates | 10 |
| Contract-days / Slot-days | 40 / 40 |
| Base / basis_value / basis_ratio eligible | 40 each |
| Annualized eligible / expiry-day Not Applicable | 39 / 1 |
| Unavailable / Excluded | 0 / 0 |
| Contract transitions / absence boundaries | 4 / 0 |

The metadata-defined expiry was 2026-10-16; all four Slot roles changed on
2026-10-19. Decimal oracle samples covered the first session, actual expiry and
first post-transition session. Retained evidence includes the actual metadata,
prices and independently calculated sample values; no market rows are embedded here.

Definition: `futures_basis_definition_v1`. Actual input SHA-256:
`6facf8378a576eb914e8675dfa0d0c8ee54be356e21cabdc7c40d52bdce27154`.

Local evidence directory: `/tmp/hg-market-state-lab-wp3-im-20261106/`:
`acceptance.json`, `inputs.canonical.json`, `inputs.json`, `result.json` and isolated
Dataset caches. These are disposable external runtime outputs; preserve/copy this
directory outside Git if longer retention is required. The audit confirmed default
Dataset cache file metadata unchanged and all SQLite connections isolated.

To repeat, choose a new, nonexistent external output directory (a new acquisition
may produce a different fingerprint; no provider-current freshness is claimed):

```bash
poetry run python market_research/tests/futures_basis_live_acceptance.py --live --output-dir /tmp/hg-market-state-lab-wp3-im-repeat
```

Provider credential resolution remains upstream-owned through the existing runtime
configuration. Neither credentials nor provider-private responses enter evidence.
Failures retain the obtained public evidence and explicit stage/dependency/reason;
they cannot produce a successful input fingerprint or a synthetic replacement.

## Reconciliation and WP4 readiness

1. WP2 resolver/transition implementation is reused unchanged; complete final public
   Futures and Calendar Exports precede evidence handoff.
2. Only Preparation calls selected public export/ensure services. Private composition
   access exists solely in the external live-test storage-isolation fixture.
3. Same-date Close, natural-day DTE, binary64 subtraction/division/log formula,
   decimal units and strict state sign follow Definition without clamp or filling.
4. Contract-day is unique; four ordered Slot-days reference it without duplicate
   derivation. Proven empty sets retain four Not Applicable results.
5. Base and three metrics retain separate disjoint outcome collections/accounting;
   expiry-only annualization does not invalidate the base observation.
6. Complete public evidence, canonical input bytes, fingerprint, definition version,
   source identities and both transition endpoints support reproduction.
7. WP4 can directly consume Slot-day metric outcomes and their Contract-day/source
   references. No scalar Horizon, dispatcher, Statistical API or Publication change
   is introduced. Statistics, chart segmentation and rendering remain WP4/WP5 work.
