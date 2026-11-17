# Calendar Spread delivery scope and limitations

Specializes [the case](ARCHITECTURE.md). L1 Daily Data and Historical Relative Value
are implemented through Python, Statistics, HTTP, Web and the static Demo.
Explicit execution now prepares missing required facts under [Inputs](INPUTS.md)
and [Application](APPLICATION.md); read-only query APIs remain export-only.
Completed implementation and acceptance records are available in Git history.

## Current boundaries

- Six Slot pairs and three metrics share the single [Definition](DEFINITION.md).
  Historical sampling, cutoff and interpretation remain in [Relative Value](RELATIVE_VALUE.md).
- [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md)
  and [Historical HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md)
  preserve distinct read-only and explicit execution permissions; synchronous execution
  uses shared capacity two, without a durable Run or generic scheduler.
- [Demo integration](../../../../ui_web/demo/CALENDAR_SPREAD.md) owns formal HTTP
  capture and shared Presentation. Local delivery does not imply publication.

## Deferred and unverified scope

L2 waiting value, L3 strategy validation, generic Plan/Batch/capability/Publication
admission and a CLI remain outside L1. Metadata is not proven point-in-time;
results describe historical Close relationships, not realized returns or trading advice.
Issue #13's bounded WSL/local-chain acceptance does not establish other deployments,
maximum 3660-date windows, prolonged load or cold-cache concurrent Source behavior.
No latency SLA or universal proxy-timeout suitability is claimed.

## DD-02 Daily enhancement work packages

WP-00 encodes accepted target semantics. WP-01 implements Daily reference preparation,
immutable evidence, HTTP projection and generated contracts; Chinese Presentation/export
and cross-layer acceptance remain pending. Use one branch,
`feat/daily-calendar-spread-enhancement`, throughout; each WP has its own commit.
Do not return automatically to develop, create further feature branches, merge,
push or publish. WP-00 stops after its documentation commit for Implementation Review.

| WP | Delivery and acceptance boundary | State |
| --- | --- | --- |
| WP-00 — Authority Encoding | Reconcile upstream selection, Daily-only reference/result, additive HTTP, Chinese/export and Demo omission contracts; review documentation diff only | IMPLEMENTED (authority encoding) |
| WP-01 — Underlying Index Close Integration | Public Dataset consumption, Daily immutable result/evidence, HTTP projection, affected OpenAPI/TypeScript generation and targeted Python/contract verification | IMPLEMENTED; targeted Python, wire and generated-contract checks passed |
| WP-02 — Chinese Presentation & Export | Chinese controls/table/status, index reference, four local actions, pure feature CSV/Context builders and targeted TypeScript/React verification | READY; not started |
| WP-03 — Cross-Layer Acceptance & Reconciliation | Targeted Online/Demo/export integration acceptance, necessary drift fixes and current readiness update | Depends on WP-02 |

Canonical target owners: [Daily Index Reference](DAILY_INDEX_REFERENCE.md),
[Query Results](QUERY_RESULTS.md#daily-underlying-index-result-dd-02-target),
[Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md#dd-02-daily-index-projection-target),
[Daily Presentation](../../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md#dd-02-chinese-presentation-and-index-target),
[Daily Export](../../../../ui_web/src/features/futures_calendar_spread/EXPORT.md) and
[Demo compatibility](../../../../ui_web/demo/CALENDAR_SPREAD.md#dd-02-additive-reference-compatibility-target).
The shared [Daily Data export standard](../../../../ui_web/data-copy-export.md) applies
to all Daily features; only Calendar Spread needs implementation in this work.

### Scoped implementation acceptance

WP-01 tests all four product selections; exact same-date identity; independent SSE
and CFFEX closures (including CFFEX closed/SSE open); empty Futures universe; hot and
cold call bounds; GET zero Ensure; POST conditional Ensure; incomplete final proof;
public factory/operation and malformed Export/Ensure failures. Assert unknown defects
still fail. For identical core facts compare all six results/accounting across every
reference state. Historical queries/current assessment must perform no SSE/Index calls
and retain existing results. Keep validated evidence and fixed safe failures without
leaking diagnostics. Test new GET/POST presence, old omission, explicit-null rejection,
wrong index/date and illegal state combinations. Run only directly relevant Python
cases and wire/type checks; generate contracts under the existing feedback loop.

WP-02 tests Chinese labels, full columns and stages, available/closed/incomplete/error
reference presentation and historical omission. Verify Raw completeness, identical
Context copy/download text, fixed CSV row/header order, all original precision,
zero/null/presence, header-only closure, BOM/CRLF/quoting/formula protection and
filenames. Verify request replacement/loading/error cannot export stale results,
draft changes cannot change response identity, and local Demo actions make no requests.
Use targeted existing/new meaningful TypeScript/React cases; do not broaden regression.

WP-03 uses targeted integration tests for Online response adaptation, the retained
Daily Bundle's strict feature validation/shared Presentation, malformed-present-field
rejection and complete exports. Preserve captured bytes/Manifest hashes. No refresh is
needed; any later explicitly requested capture/build follows the formal Demo workflow.
Browser matrices, live Source checks, services, topology scans and full builds are not
automatic gates; report actual checks and NOT VERIFIED limits under root policy.
Reconcile target/readiness text with implemented behavior and close with commit evidence,
without creating a permanent task diary. No business scope extends to range queries,
Historical population/statistics, unrelated Daily refactors or deployment.

WP-01 preserves shared preparation and pure construction semantics, reusing local
Calendar/Ensure validators with explicit SSE/Index target parameters. Only Daily
adds index_service injection and required reference/evidence carriers. The HTTP field
is optional solely for retained payloads; both online endpoint projections require it.
The feature adapter's additional online-presence assertion and present-object frontend
validation remain WP-02 work. No UI, captured Bundle bytes or Historical contract changed.
Live Source, browser and deployment verification were not performed in WP-01.

### Reconciliation and remaining implementation risks

The prior Inputs/UPSTREAM exclusion of Index/SSE now applies to shared/Historical
preparation only. Core completeness and whole-core failure invariants remain binding;
classified reference errors alone are successful nested outcomes. Query Results owns
immutable carriers; reference authority owns acquisition/availability; HTTP only projects.
Daily export has one shared standard and feature-local mappings. Demo's complete-result
rule now explicitly follows the additive HTTP contract's optional field, without
weakening required validation or introducing a historical schema.

Index prerequisite failures may be wrapped OperationError; do not infer unavailable
SSE dates or deeper Source causes. Independent Calendar snapshots can change between
operations and must fail association explicitly. Optional/non-null wire modeling needs
care to avoid injecting null defaults into old payloads. Daily source-context updates
must not mutate Historical defaults. Source latency and existing synchronous capacity/
cancellation limits remain as documented; WP-00 establishes no runtime or live-data
acceptance. Open-day missing Index rows do not prove legal Source no-quote availability.
