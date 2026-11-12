# R01-A work packages, reconciliation and readiness

## Portable storage follow-up

The original case milestones below retain their original evidence and numbering.
The new, unimplemented storage WP0-WP6 series is tracked in
[Storage reconciliation](../../../STORAGE_RECONCILIATION.md); its case-owned target is
[Online storage](ONLINE_STORAGE.md). Prior PASS does not establish SQLite readiness
or native Windows storage support.

This document specializes the [case entry](ARCHITECTURE.md). It owns delivery
boundaries and reconciliation, not duplicate formulas, schemas or runtime results.
Baseline: `develop` at `3c7db37714443d7717218ee602218e7abfd911ab`.
Working branch: `feat/r01-futures-basis-research`; WP1–WP5 continue on that branch.
R01-A WP5 baseline is `60d607786c3490ae728ccc3493857ef5d0d71f3e`. R02 starts from
the current R01 branch head `e7cc700cb08404bc37b1013697aab2a2e8204f1a`
(WP5 plus the Publication platform isolation fix) on
`feat/r02-futures-basis-online`; no `develop` merge is used.

## Work packages

Every WP must be independently reviewable, committable and verifiable. Runtime
readiness requires its own evidence; later unfinished WPs never fail an earlier
WP's bounded acceptance. These identifiers belong to R01-A, not the unrelated
historical publication project that also used WP numbering.

Authority status: WP0 is complete; WP1 has passed independent artificial-data
runtime and real Chromium acceptance under the exact V2 contract and fixed fixture.
WP2 has passed independent synthetic Slot/Transition acceptance. WP3 has passed
synthetic runtime and bounded real IM acceptance under [its evidence](WP3_ACCEPTANCE.md).
WP4 statistics passed synthetic and bounded real IM acceptance; WP5 offline report and
longer-window delivery are recorded in [WP5 acceptance](WP5_ACCEPTANCE.md). WP1 does not admit V2
into existing Publication/HTTP consumers or implement the offline packager. WP6 encodes
the online application, HTTP and frontend authority in
[Online application](ONLINE_APPLICATION.md); WP7 Python runtime is implemented,
WP8-A HTTP and WP8-B Web Consumer are implemented under synthetic acceptance;
WP9 WSL/real-market acceptance passed; overall WP9 remains PARTIAL because Windows
Chrome has not been run. Deployment is NOT RUN. See [WP9 acceptance](WP9_ACCEPTANCE.md).

| WP | Deliverable and boundary | Dependencies / acceptance |
| --- | --- | --- |
| WP0 — Semantic Authority | This Case topology, SD01–SD09, generic Visualization V2, navigation and reconciliation; documents only | Links/anchors/reachability, unique ownership, formulas/units/accounting, complete diff; no production code, data acquisition or runtime acceptance |
| WP1 — Visualization Enhancement | [V2](../../../../ui_web/VISUALIZATION_V2.md) validation/rendering in the existing generic frontend boundary | WP0; fixed artificial multi-line data, literal details, events, segmentation, null gaps, Zoom/Pan/Reset and V1 regression; no market dependency |
| WP2 — Contract Slot Resolution | Pure metadata/evidence→daily real-contract roles under [Slot resolution](SLOT_RESOLUTION.md) | WP0; independent synthetic lifecycle/month/quarter/expiry/empty-proof fixtures and quote-availability invariance; no visualization or acquisition |
| WP3 — Basis Observation | Independent public preparation and pure Contract-day/Slot-day construction under [Inputs](INPUTS.md) and [Observation](OBSERVATION.md) | WP2; contract fakes, formulas, accounting/provenance/transition tests plus retained real IM validation; no Statistics or charts required |
| WP4 — Descriptive Statistics | [Case adaptation and findings](STATISTICS.md), with Statistics-owned Mean authority/API/backend extension | WP3; independent numerical Mean conformance, Research binding/population/run tests and three-metric results; no renderer required |
| WP5 — Integration & Research Delivery | [Research projection and offline report](DELIVERY.md), with local assets and reproducible real IM evidence | WP1 + WP3 + WP4; offline interaction and evidence/reconstruction verification; no Publication/HTTP admission required |
| WP6 — Online Semantic Authority | [Online application](ONLINE_APPLICATION.md), [HTTP contract](../../../../ui_http/products/futures_basis_research/http-contract.md), [frontend slice](../../../../ui_web/src/features/futures_basis_research/ARCHITECTURE.md), catalogs and this roadmap; documents only | WP5; links/anchors, ownership, DTO/state/error and frontend completeness, reconciliation, `git diff --check`; no runtime code, live data or full matrices |
| WP7 — Online Research Application & Store | Case-specific online facade: standard profile, semantic validation, run lifecycle, single worker, file store, owner scope, atomic result publication, restart recovery and reader projection reuse | WP6; synthetic/fake-service tests, state/recovery/owner/size/corruption acceptance; no HTTP/UI/generated artifacts |
| WP8 — HTTP Product & Web Slice | HTTP adapter/OpenAPI/generated contract; authenticated four-surface navigation, query controls, polling and shared W1 reader; offline reader regression | WP7; strict HTTP/auth/error/limit tests, Vitest/build/lint, deterministic browser tests, `contract:check`; no live data or Publication |
| WP9 — Integrated Acceptance | WSL FastAPI + Vite + Windows Chrome end-to-end: login, query, run, refresh, report, restart interruption, busy, ownership and failure states | WP8; external evidence and bounded real IM acceptance; no performance/SLA promise |

Default implementation order is WP1 → WP2 → WP3 → WP4 → WP5; WP1 and WP2 have
no dependency on each other's runtime. New runtime tooling/dependencies, if
needed, follow their owning module's normal authority and verification rules.
The R02 online order is WP6 → WP7 → WP8 → WP9. WP6 is an authority gate; its PASS
does not depend on WP7–WP9 being implemented.

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
- **Mean runtime:** implemented and independently tested by Statistics under
  [Mean authority](../../../../market_statistics/MEAN.md).
- **V2 renderer:** WP1 is implemented and independently accepted; see
  [Visualization implementation and verification](../../../../ui_web/src/shared/visualization/README.md).
  Producer projection and offline packaging are delivered under
  [WP5 acceptance](WP5_ACCEPTANCE.md).
- **Independent Case runtime and offline packager:** WP2 pure Slot resolution is
  implemented; WP3 preparation/observation and WP4 statistics are accepted.
  WP5 implements the bounded packager and evidence reader. Acceptance is recorded
  separately; no generic framework is introduced.
- **Publication / capability integration:** R01-A is still not admitted to
  PublishedResearchResult, Publication V1, Research Explorer or the generic
  capability/Plan/Batch path. The separate [online application](ONLINE_APPLICATION.md)
  and [HTTP product](../../../../ui_http/products/futures_basis_research/http-contract.md)
  are defined by WP6; the Python application is implemented in WP7, HTTP/Web delivery in WP8-A/WP8-B,
  and WSL/real-market integrated acceptance is recorded in [WP9 acceptance](WP9_ACCEPTANCE.md),
  with Windows and deployment unverified. Existing quotas, authentication,
  execution guards and source semantics do not disappear.
- **Online evidence/replay:** the online MVP retains the versioned reader projection,
  input fingerprint and coverage; full `evidence.json` / canonical inputs /
  associations / verify-replay remain the WP5 offline package. An online evidence or
  replay endpoint is deferred and requires its own authority.
- **Online operations:** run list/history, delete/cancel, queue/fair scheduling,
  multi-process execution, automatic cleanup and POST idempotency are deferred; the
  first release has one active run and URL-based refresh only.
- **Actual study dates/data:** WP3/WP4 real IM validation uses explicit dates,
  public-source inputs and retained evidence. WP5 preserves the original short-window evidence and adds the explicit
  2024-01-01..2026-10-30 candidate. No default historical window is introduced.

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
The Statistics-owned Mean extension and Case statistics are completed in WP4 below.

## WP4 verification and handoff

WP4 **PASS** (2026-11-06), from baseline
`cc4c4f0212ffd72d356f6476418e7285f56818e7` on the same working branch.
The [typed analysis API](STATISTICS_API.md) implements explicit three-metric
Mean/Quantile/IntervalCount distributions, all six common-date comparisons per
metric, coverage association and complete/censored Slot discount spans.
[WP4 acceptance](WP4_ACCEPTANCE.md) records numerical/synthetic and retained real
IM evidence; [usage](USAGE.md) provides a minimal Python example.

WP5 is **Implementation Ready** to consume the frozen results, original statistical
objects, source association, dropped-date reasons and run boundaries. No WP5
projection, visualization, offline report, CLI/HTTP or persistence is implemented.


## WP5 verification and handoff

WP5 **PASS** (2026-11-06), from baseline
`1b656d7919580a5b668b71d83088574737a37d48`, on the same branch with no develop merge.
[Delivery](DELIVERY.md) and [Evidence](EVIDENCE.md) own the case-specific production
composition, projection, evidence and replay interfaces; [usage](USAGE.md) owns
single-command instructions. ui_web owns the independent offline reader/packager.
No Basis/Slot/Statistics algorithm, generic engine, CLI routing, HTTP/Auth,
Publication admission or backtest was added.

The original 2026-10-12..2026-10-23 IM evidence exactly matches all WP4 statistical
requests/results. The explicit 2024-01-01..2026-10-30 IM candidate also passed full
Calendar/Futures/Index completeness in isolated external storage (683 sessions).
Both report sizes, numerical findings, external paths and reproduction are in
[WP5 acceptance](WP5_ACCEPTANCE.md). Browser verification uses actual Chromium
with file://, offline context and zero external requests; evidence replay forbids
Source/cache access. Synthetic empty/failed/malicious-text reports also pass.

Verification: 1,249 Research/topology/architecture tests and 252 Web tests passed,
as did Ruff, MyPy, contract freshness, TypeScript/Vite build, lint and generic
V1/V2 Chromium regression. The report embeds a licensed Chinese font and uses a
larger generic plot frame; screenshots confirm readable text and four Slot legends.
Links/anchors, full diff and whitespace checks complete the bounded reconciliation.
WP1–WP5 now satisfy R01-A Week 1's descriptive offline delivery gate. HTTP
publication and Week 2 remain outside this acceptance.

## R02 online extension and WP6 handoff

R02 starts from `e7cc700cb08404bc37b1013697aab2a2e8204f1a` on
`feat/r02-futures-basis-online` (WP5 plus the Publication platform isolation fix),
with no `develop` merge. WP6 is authority-only; WP7–WP9 are not implemented by this
change.

WP6 **PASS** (2026-11-06): the online request/profile, lifecycle and storage boundary
are owned by [Online application](ONLINE_APPLICATION.md); transport is owned by the
[HTTP contract](../../../../ui_http/products/futures_basis_research/http-contract.md);
browser interaction and reader reuse are owned by the
[frontend slice](../../../../ui_web/src/features/futures_basis_research/ARCHITECTURE.md).
Existing R01-A formulas, Slot resolution, observations, Statistics and Visualization
semantics are unchanged, and the offline delivery remains valid.

### Reconciliation

Classifications are **Compatible**, **Requires authority extension**, **Implementation gap**
or **Deferred**; parentheticals record secondary consequences for the same finding.

| Reviewed boundary | Finding and classification |
| --- | --- |
| Online Research boundary vs `POST /research/execute` | R01-A remains outside the generic capability/Plan/Batch path. The new specialized routes are independent; existing endpoint semantics are unchanged. **Requires authority extension** (new product; existing compatible). |
| Online results vs Publication V1 | An online run is not a `PublishedResearchResult`, uses no Publication Store and does not alter the Trailing Return-only admission. Publication of R01-A remains deferred. **Compatible** (publication admission deferred). |
| Offline reader vs online reader | Both consume the same `futures_basis_report_evidence_v1` reader projection and six sections. ui_web extracts shared reader presentation while the offline entry remains standalone. **Requires authority extension** (ui_web reader ownership; WP8 implementation gap). |
| Online run vs Workbench Run | The online run is product application execution; Workbench Run is agent operational evidence. IDs, storage, evidence and lifecycle are distinct and unshared. **Compatible**. |
| Existing authentication and ownership | All endpoints use the existing Cookie/same-origin/sliding gate. The Research application receives the authenticated user ID as an opaque owner scope; foreign and unknown runs are both `run_not_found`. Auth contract is unchanged. **Requires authority extension** (application ownership; Auth compatible). |
| DataLake acquisition and retry | The case `prepare_inputs` export/ensure/export sequence, completeness policy and fail-closed behavior are reused unchanged. No new retry, fallback or queue exists. **Compatible**. |
| Result storage, integrity and evidence | A case-specific file-based external runtime store retains request/state/reader payload with atomic publication and digests; it is not a database, Publication or Workbench store. Full offline evidence/replay stays with WP5. **Requires authority extension** (online store; full evidence/replay deferred; WP7 implementation gap). |
| Visualization V1/V2 compatibility | Online reads the existing V2 history and V1 histogram Views through the unchanged generic ChartView contract. Zoom/Pan/Reset, events, hover, null and segment semantics are preserved. **Compatible**. |

The generic `descriptive/JOB_EXECUTION.md` and `BATCH_EXECUTION.md` no-durable-ID /
no-persistence / no-HTTP statements continue to govern the Trailing Return scalar
path. The online run identity is case-specific and does not create a generic Research
execution identity, reopen generic persistence or make ObservationSets/results
generally durable.

### WP6 verification

- Markdown links and relative targets checked across all authority Markdown; new
  documents are reachable from the root through Research, HTTP and Web entries.
- Ownership checked: Research owns online request/profile/lifecycle/report semantics;
  ui_http owns parsing/status/DTO/OpenAPI; ui_web owns interaction/presentation; no
  reverse dependency or duplicated financial interpretation.
- HTTP DTO, status/error, size and authentication obligations checked for
  completeness; execution and scientific status remain separate.
- Frontend controls, polling, refresh, six-section reader reuse, requested-vs-observed
  distinction and empty/failed/partial presentation checked.
- No conflict with existing `POST /research/execute`, Publication V1, Research
  Explorer or the existing authentication boundary. No live market data, runtime
  code or generated artifacts were produced.
- WP6 is PASS even though WP7–WP9 are not implemented. WP7 is
  **Implementation Ready: YES**.

### WP7–WP9

- **WP7 — Online Research Application & Store:** case-owned facade implementing
  `r01a_standard_v1`, semantic request validation, run lifecycle, single worker,
  file store, owner scope, atomic result publication, restart recovery and reader
  projection reuse. Tests use fake public services; no HTTP/UI/live data.
- **WP8 — HTTP Product & Web Slice:** strict adapter/OpenAPI/generated contract,
  authenticated four-surface navigation, query controls, polling/refresh and shared
  W1 reader; offline reader regression and contract freshness. No live data.
- **WP9 — Integrated Acceptance:** WSL FastAPI + Vite + Windows Chrome end-to-end,
  including refresh, restart interruption, busy, ownership and bounded real IM
  acceptance; external evidence only, no performance/SLA promise.

WP7 was implemented under [Online application](ONLINE_APPLICATION.md).

## WP7 handoff

WP7 implements the case-owned `FuturesBasisOnlineApplication` and its bounded file
store. The server-selected `r01a_standard_v1` builds the formal `ReportRequest`;
the worker reuses `observe_futures_basis`, `compose_report` and the WP5 reader
projection. The public Python operations are `submit`, `get_run` and `get_report`.
The store is separate from Publication and Workbench, with one active worker per
application process, owner-scoped reads, startup interruption, bounded atomic
report publication and SHA-256 verification. Its default root is ignored runtime
state; `LAB_FUTURES_BASIS_RUN_ROOT` may select an absolute server-owned root through
`lab_config`.

WP8 must compose one application instance in the backend process, pass the
authenticated user ID as `owner_scope`, strictly parse the HTTP request, and map
the stable `OnlineError.kind` values under the existing HTTP contract. It must
keep a single worker process for this store and deliver the existing reader
projection without recomputation. WP9 remains responsible for the real browser,
restart and bounded live integration gate.

### WP7-R acceptance (2026-11-09)

PASS on `feat/web-ui-workspace-redesign`, baseline
`cec5627dd30387e1daccb3e2293fb5fbd1dff2b5`. Status reads now inspect result
metadata only; full report reads retain integrity/association validation and classify
stored oversize as `response_too_large`. Synthetic tests cover concurrent submissions
and readers, status independence, atomic publication/failure, recovery with orphan
results, ownership, versions, corruption and nonregular files. No market I/O occurred.

Verification: `poetry run pytest market_research/tests` — 1,254 passed, 1 skipped;
`poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py`
— 21 passed; `poetry run ruff check market_research`, `poetry run mypy market_research`
(106 files), and `git diff --check` passed. WP8 HTTP delivery remains pending.


### WP8-A HTTP handoff (2026-11-09)

WP8 is delivered in two independent parts: **WP8-A HTTP Product** and **WP8-B Web
Consumer**. WP8-A is PASS under synthetic Linux acceptance; WP8-B remains pending.
The [HTTP acceptance](../../../../ui_http/products/futures_basis_research/ACCEPTANCE.md)
records all 13 acceptance items, error mapping, authentication/ownership, singleton
startup, storage/platform isolation, OpenAPI/DTO reconciliation and exact checks.
HTTP verification passed 476 tests; Research passed 1,255 tests with one existing
platform-specific skip; topology/architecture/export checks passed 24 tests.
Ruff, MyPy (160 files), existing frontend contract freshness and whitespace checks
passed. Native Windows capability failure is simulated, not a native-platform run.

The adapter uses the public case facade only. Repeated status reads do not execute
Research or parse full reports. All responses are no-store; HTTP publication and
response bounds remain independent, and report capacity includes serialization.
The existing prohibition on GET query parameters now has explicit 400 rejection
rows in the HTTP status matrix. Existing product contracts/artifacts did not drift.

WP8-B first introduces the consumer, its generated OpenAPI/TypeScript artifacts and
freshness coverage; React interaction, polling and shared reader migration remain
unimplemented. No offline reader or live market workflow changed. WP9 retains the
real browser and bounded live integration gates.

### WP8-B Web handoff (2026-11-09)

WP8-B implements the authenticated `/research/futures-basis` consumer, its generated
OpenAPI/TypeScript freshness loop, query form, bounded status polling, URL restoration
and the shared six-section online/offline reader. Research numerical semantics and
HTTP contracts are unchanged. The frontend-owned
[WP8-B acceptance](../../../../ui_web/src/features/futures_basis_research/ACCEPTANCE.md)
records synthetic Chromium/Vite/FastAPI acceptance, offline regressions and exact
checks. Online execution availability does not establish Provider/Cache readiness.
WP9 remains unexecuted; no real market data, production cache, Daily Data WP5 or
Backtesting work is part of this handoff.

### WP9 integrated acceptance (2026-11-09)

[WP9 acceptance](WP9_ACCEPTANCE.md) records current WSL2 FastAPI/Vite/Chromium
integration, bounded real IM execution, original Python-path equivalence, restart
recovery, authentication/isolation and synthetic failure acceptance. Windows Chrome
and Nginx/Docker deployment are NOT RUN; overall WP9 is PARTIAL, with the WSL scope
PASS. The changes add process-restart/lost-response regression coverage and fix a
test synchronization race; no product, financial, lifecycle or HTTP contract changes.

## Input preflight work packages

[PREFLIGHT.md](PREFLIGHT.md) owns the approved bounded semantics. WP-P0 encodes
authority; WP-P1 publishes Research assessment and shared online L1; WP-P2 exposes
HTTP/OpenAPI; WP-P3 implements Web admission and generated contracts; WP-P4 records
integrated synthetic acceptance. No live-source check occurs implicitly.

WP-P0–WP-P4 are implemented under synthetic Linux acceptance; see
[verification evidence](PREFLIGHT_ACCEPTANCE.md). This adds no live Source or
platform/deployment acceptance claim beyond existing WP9 evidence.
