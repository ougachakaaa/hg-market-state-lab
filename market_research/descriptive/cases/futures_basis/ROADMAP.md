# R01-A work packages, reconciliation and readiness

This document specializes the [case entry](ARCHITECTURE.md). It owns delivery
boundaries and reconciliation, not duplicate formulas, schemas or runtime results.
Baseline: `develop` at `3c7db37714443d7717218ee602218e7abfd911ab`.
Working branch: `feat/r01-futures-basis-research`; WP1–WP5 continue on that branch.

## Work packages

Every WP must be independently reviewable, committable and verifiable. Runtime
readiness requires its own evidence; later unfinished WPs never fail an earlier
WP's bounded acceptance. These identifiers belong to R01-A, not the unrelated
historical publication project that also used WP numbering.

Authority status: WP0 is complete; WP1 has passed independent artificial-data
runtime and real Chromium acceptance under the exact V2 contract and fixed fixture.
WP2 has passed independent synthetic Slot/Transition acceptance. WP3 has passed
synthetic runtime and bounded real IM acceptance under [its evidence](WP3_ACCEPTANCE.md).
WP4/WP5 runtime and report acceptance remain pending. WP1 does not admit V2
into existing Publication/HTTP consumers or implement the offline packager.

| WP | Deliverable and boundary | Dependencies / acceptance |
| --- | --- | --- |
| WP0 — Semantic Authority | This Case topology, SD01–SD09, generic Visualization V2, navigation and reconciliation; documents only | Links/anchors/reachability, unique ownership, formulas/units/accounting, complete diff; no production code, data acquisition or runtime acceptance |
| WP1 — Visualization Enhancement | [V2](../../../../ui_web/VISUALIZATION_V2.md) validation/rendering in the existing generic frontend boundary | WP0; fixed artificial multi-line data, literal details, events, segmentation, null gaps, Zoom/Pan/Reset and V1 regression; no market dependency |
| WP2 — Contract Slot Resolution | Pure metadata/evidence→daily real-contract roles under [Slot resolution](SLOT_RESOLUTION.md) | WP0; independent synthetic lifecycle/month/quarter/expiry/empty-proof fixtures and quote-availability invariance; no visualization or acquisition |
| WP3 — Basis Observation | Independent public preparation and pure Contract-day/Slot-day construction under [Inputs](INPUTS.md) and [Observation](OBSERVATION.md) | WP2; contract fakes, formulas, accounting/provenance/transition tests plus retained real IM validation; no Statistics or charts required |
| WP4 — Descriptive Statistics | [Case adaptation and findings](STATISTICS.md), with Statistics-owned Mean authority/API/backend extension | WP3; independent numerical Mean conformance, Research binding/population/run tests and three-metric results; no renderer required |
| WP5 — Integration & Research Delivery | [Research projection and offline report](DELIVERY.md), with local assets and reproducible real IM evidence | WP1 + WP3 + WP4; offline interaction and evidence/reconstruction verification; no Publication/HTTP admission required |

Default implementation order is WP1 → WP2 → WP3 → WP4 → WP5; WP1 and WP2 have
no dependency on each other's runtime. New runtime tooling/dependencies, if
needed, follow their owning module's normal authority and verification rules.

## Reconciliation

| Reviewed boundary | Finding and resolution |
| --- | --- |
| [DataLake Futures architecture](../../../../data_lake/datasets/tushare_equity_index_futures/ARCHITECTURE.md), facts, universe and service | Publishes source Close/metadata and complete product-day sets, not Basis/DTE/Slots. Research derives those downstream. Complete final Futures evidence is mandatory; no new catalog API, private access or frozen upstream edit. |
| [Snapshot shared basis](../../../../data_snapshot/src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md) and [Basis Monitor Task](../../../../workbench/tasks/equity_index_futures_basis_monitor/ARCHITECTURE.md) / [output contract](../../../../workbench/tasks/equity_index_futures_basis_monitor/authority/QUERY_AND_RESULT.md) | Both already use futures-minus-underlying, not positive discount. Their simple percentage/linear annualization and D=0 clamp differ from the Research log/decimal/D=0 Not Applicable convention. Old outputs are not admitted Research inputs or renamed/recomputed in place; historical Task/results remain frozen. |
| Existing Slot names | M0/M1/Q1/Q2 already mean front active near months and subsequent unoccupied quarters. New Case explicitly uses that role meaning, including post-expiry dates; internal aliases cannot change it. Slot identity is not contract identity. |
| [Scalar Observation](../../OBSERVATION.md) / [conversion](../../SAMPLE_CONVERSION.md) | Positive integer Horizon is incompatible with this instantaneous Case. Use independent Case carriers/adaptation; no fake Horizon, generic contract weakening or automatic Job/Batch/capability admission. |
| [Research upstream](../../../UPSTREAM.md) | Case-specific partial Index permission is explicit. Calendar/Futures remain fail-closed; no runtime Snapshot fallback. CFFEX candidates and independently proven SSE Index dates are not silently conflated. |
| [Statistics public contract](../../../../market_statistics/CONTRACT.md) | Quantile/IntervalCount are reusable scalar capabilities. Required Mean is a WP4 Statistics extension; no Research-owned generic mean, automatic bins or temporal sample framework. |
| [Visualization V1](../../../../ui_web/VISUALIZATION.md) | Strict V1 marks cannot accept details, nulls or segments as extra fields. Separate [V2](../../../../ui_web/VISUALIZATION_V2.md) defines exact shapes/dispatch; no financial fields enter the generic schema. |
| [Publication storage](../../../PUBLICATION_STORAGE.md), [HTTP](../../../../ui_http/products/research_publication/http-contract.md) | Existing source admission is Trailing Return Batch only and transport Views are V1 only. Neither becomes compatible by adding this Authority. WP5 uses an independent offline report; current storage/HTTP/generated contracts remain unchanged. |

There is one canonical owner per new concern, reached through the Case entry.
Snapshot owns its frozen Product computations; Research owns this distinct Case
version, not a replacement implementation of those Product contracts. Unit/formula
labels must accompany any human comparison; old annualized percentages cannot be
converted into the new metric by sign change or division by 100 alone.

## Known gaps and defer

- **Futures partial-date metadata proof:** the public service does not separately
  expose active catalogs for failed dates. Resolved for this version by requiring
  complete Futures; supporting partial Futures would require a future explicit
  upstream capability/consumption decision, never inferred empty sets.
- **Mean runtime:** absent from Statistics V1. Required WP4 work under the Statistics
  owner, not a WP0 blocker or permission to implement the algorithm in Research.
- **V2 renderer:** WP1 is implemented and independently accepted; see
  [Visualization implementation and verification](../../../../ui_web/src/shared/visualization/README.md).
  Producer projection and offline packaging remain WP5 work.
- **Independent Case runtime and offline packager:** WP2 pure Slot resolution is
  implemented; WP3–WP5 preparation, observation, statistics and packaging remain
  pending. Their owner, input/output meaning and bounded acceptance are defined
  here; no generic framework is pre-created.
- **Publication / HTTP / capability integration:** deferred beyond this offline
  delivery. Would need versioned Case evidence admission, V2 read/transport/safe
  projection and generated-contract work. Existing quotas/authentication do not
  disappear and no new routes are implied.
- **Actual study dates/data:** later real IM validation/report uses explicit dates,
  public-source inputs and retained evidence. No default historical window or
  claimed live PASS is created by WP0.

## WP0 verification and handoff

The documentation-only gate checks navigation/relative links/anchors from stable
entries, ownership and upper/lower consistency, formula/sign/unit terminology,
per-metric populations, Gap/Defer location and WP dependencies. Review all changed
and new documents and run `git diff --check`. No full pytest, MyPy/Ruff, frontend
build/E2E, database tests, live acquisition or Research execution is required.

The WP0 commit is independent and contains only necessary Authority/Contract/
Navigation Markdown. Final handoff records branch, baseline, final commit, file
inventory, SD01–SD09, reconciliation, remaining work and WP1 readiness. Mark WP0
`PASS` only after these document checks pass; use `PARTIAL` only for an actual
unresolved semantic/contract blocker, not missing WP1–WP5 implementation.

## WP1 verification and handoff

WP1 **PASS** (2026-11-06), continuing on `feat/r01-futures-basis-research` from
`93536652e3adc807dac91c08afddc6f17c733654`. Implementation is confined to generic
Visualization and its standalone artificial-fixture browser harness; no Research
runtime, financial field, HTTP route, generated contract or Publication change.

Reconciliation against V2: strict explicit-version validation preserves supplied
order, units, references and null/segment semantics; each Binding remains one
legend group, Details remain literal ordered text, and Events remain independent
date annotations with individual detail access. Null readouts and empty/all-null
presentation never invent numeric points. Viewport interactions preserve data and
legend selection. Existing V1 validation and rendering remain supported unchanged.

Verification: 94 focused contract/projection/React/V1 tests, TypeScript/Vite build,
Web lint and real Chromium 156.0.8078.4 acceptance passed. Browser assertions cover
actual curves, point hover, null reason, same-day/event-only annotations, grouped
legends, zoom/pan/reset, multiple y axes, disabled shortcuts, empty content and V1.
Reproduction and local screenshot/JSON evidence paths are documented in the
[Visualization README](../../../../ui_web/src/shared/visualization/README.md).
No business-data acquisition or Python test matrix was needed for this WP.

WP2 may start directly under its existing authority: it is independent of WP1
runtime. WP2–WP5 incompleteness does not reduce the bounded WP1 result.

## WP2 verification and handoff

WP2 **PASS** (2026-11-06), on `feat/r01-futures-basis-research` from baseline
`3787252299144b7e87fa248f345b2bc84d62ed13`. Public pure Python entry:
`market_research.descriptive.cases.futures_basis`, with `resolve_daily_slots`
and `detect_contract_transitions`; immutable carriers and evidence handoff are
specified in [Slot resolution](SLOT_RESOLUTION.md#python-boundary-and-evidence-handoff).

Reconciliation: the resolver consumes the day's complete proven active metadata,
checks inclusive lifecycle/identity and exact four-month structure, and retains
per-day metadata and source references. It never truncates, filters, fills,
infers expiry, chooses a main contract or obtains a catalog. The evidence carrier
is a caller-validated Research handoff, not a new DataLake proof or cache check.
WP3 must validate and retain the full final Futures and Calendar Exports before
constructing these carriers; reference strings/complete flags alone are not proof.

Daily results preserve all four ordered Slots, including explicit
`not_applicable / no_active_contract` outcomes. Transition detection requires a
result for every supplied CFFEX candidate; any gap fails the entire call. Real
code changes and proven absence boundaries have separate typed outputs with both
endpoints and evidence. No quote/volume/open-interest input, business derivation,
execution claim, chart segment or Observation outcome computation is introduced.

Verification: 70 WP2 synthetic tests passed. The final required Research suite
and architecture/topology checks passed together (1133 tests):

```bash
poetry run pytest -q market_research/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_research
poetry run mypy market_research/src/market_research/descriptive/cases/futures_basis market_research/tests
```

Direct MyPy of the new package and its two test/fixture files also passed, as did
root-environment public imports, Markdown links/anchors and `git diff --check`.
All acceptance data is synthetic; no live acquisition, historical study run or
Web/browser gate is part of WP2. Existing Case behavior passed regression.

At the WP2 handoff, WP3 was **Implementation Ready** under [Inputs](INPUTS.md) and
[Observation](OBSERVATION.md), consuming this public resolver. Input acquisition,
retention/fingerprint, Basis calculations and real IM acceptance were the remaining
WP3 work, completed below; Statistics and offline packaging remain WP4/WP5.

## WP3 verification and handoff

WP3 **PASS** (2026-11-06), from required baseline
`c741c7ca49944b236c999e6b89193c435f3b322c` on this working branch.
The independent public preparation / pure observation / orchestration interfaces
and failure contracts are specified in [Inputs](INPUTS.md#wp3-python-preparation-boundary)
and [Observation](OBSERVATION.md#wp3-python-observation-boundary).

Runtime acceptance and real-market acceptance both passed independently; exact
coverage, counts, fingerprint, external evidence and reproduction commands are
recorded in [WP3 acceptance](WP3_ACCEPTANCE.md). All market rows and runtime caches
remain outside Git. WP2 resolution and transition APIs are reused unchanged.

WP4 is **Implementation Ready** to consume the retained three-metric outcomes,
Slot-day references, per-Slot accounting and input evidence. WP3 does not implement
sample conversion/statistics, chart segmentation, offline reports or publication.
The pending WP4 Statistics-owned Mean extension remains WP4 work.
