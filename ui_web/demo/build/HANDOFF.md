# DDB implementation handoff

Specializes [build authority](ARCHITECTURE.md). This records implementation locations and
completion criteria, without implementing DDB-02 through DDB-05 in DDB-01.
All paths below are relative to `ui_web/` unless explicitly repository-root.

## DDB-02 — Contract and offline validator

Goal is executable offline admission of the [Bundle contract](../BUNDLES.md).
Requires reconciled DDB-01 authorities and the existing feature validators identified in
[HTTP feasibility](HTTP_FEASIBILITY.md). Real Bundle data and a running backend are not
prerequisites for implementing its focused regression fixtures.

Create `demo/build/registry.ts`, `validate.ts`, `preflight.ts` and focused co-located tests.
Registry exports the single table as JSON for Collector consumption. Pure validators
remain under `src/features/*/api/` and reader/Visualization owners. Keep generated artifacts
with those owners. Use current TypeScript execution tooling from the npm project.
Preflight exposes a CLI suitable for later build orchestration and Collector staging
validation; it rejects failure with a nonzero exit status.

Direct verification covers valid seven-Bundle admission, each missing/extra/duplicate ID,
duplicate JSON keys, unsafe paths, absent files, malformed envelope, wrong contract/Preset,
hash mismatch, numeric preservation, request/result mismatch, unsupported profile/View,
Catalog detail omission and Publication missing references/nonterminal pages. Exercise
the actual Preflight CLI exit on invalid input. Completion requires all directly scoped
cases to pass offline and feature-owned validators to perform business validation.

## DDB-03 — Explicit HTTP Collector

Implementation now provides `collect.py`, the internal `collectorBridge.ts` and the
`scripts/demo_collect_bridge.mjs` launcher. CLI details and transaction protocol are in
the build authority. Focused controlled verification runs with
`npx vitest run --config demo/build/vitest.config.ts demo/build/collector.test.ts` from
`ui_web`; it launches the root Python environment and a temporary HTTP fixture server,
and invokes the actual independent DDB-02 Preflight on candidate and active test data.
These test payloads remain temporary and are never active Demo captures.

Real capture remains NOT VERIFIED. The local backend responds with protected HTTP 401,
but the inspected configuration lacks LAB_AUTH_ORIGIN and approved account credentials
must be supplied interactively. No real active Bundle dataset is delivered by these tests.
The tracked real dataset and distribution authorization remain DDB-04 entry conditions.

Goal is local authenticated capture with single-Bundle/all selection. Requires DDB-02
Registry export and admission tooling, an operator-provided serving URL, approved user,
explicit Presets and available source/Run/Publication dependencies for real collection.

Create `demo/build/collect.py` and consume DDB-02's `presets.json`, using repository-root Poetry and
existing HTTP dependencies or standard library. Put focused Python tests alongside this
tool. Invoke the DDB-02 Node validator on staged candidate files. Runtime configuration
uses root lab_config. Extend config authority first only if new environment keys are needed.

Direct verification covers query/body mapping, Cookie renewal and same-origin headers,
M1/Q1 separation, terminal Run failures/timeouts, lost Submit response, complete opaque
pagination, missing details, lossless numeric serialization, single-file byte preservation,
full-generation acquisition failure, lock contention, commit interruption and idempotent
forward completion. Controlled HTTP fixtures verify transport only. Completion requires
the current tracked dataset to be acquired through formal HTTP and independently admitted;
real captures and distribution authorization are reported separately from fixture tests.

## DDB-04 — Single Demo runtime and build

Goal is one static runtime sharing feature Presentation. Requires valid DDB-03 data and
DDB-02 Preflight. Create `demo/runtime/` entry, static Bundle adapter and
`demo/build/vite.config.ts`; connect `package.json` demo:build and a local artifact preview.
Reuse or move the retained `src/demo/shell/hashRoutes.ts`, `src/demo/static/StaticWorkspace.tsx`
and `results.ts` into canonical Demo ownership, updating local consumers. Existing ResultIdentity
fields must be reconciled to actual captured provenance; remove obsolete required assertions
rather than fabricate sourceRevision/fingerprint/evidence provenance absent from HTTP.

Use `src/features/*/presentation.ts` entries and current app route inventory. Preserve all
seven business pages and local controls. Online entry keeps its own data path. Build loads
the exact admitted static input, emits `.build/demo/` and requires no backend or credentials.

Direct verification covers seven-Bundle adapter dispatch, shared Presentation and route
composition, local interactions, missing/corrupt Bundle causing the build command to fail,
and successful offline artifact/preview. Static dependency/browser matrices remain manual
under root policy unless explicitly requested. Completion requires a working sole runtime,
offline build and local preview acceptance with truthful disclosure.

## DDB-05 — CI and release

Goal is independent CI admission/build and verified Pages publication. Requires completed
DDB-02 through DDB-04 and local build/preview acceptance. Inspect the actual repository
`.github/workflows/demo-compatibility.yml` and Pages workflow before modifying them in this
work package. Integrate the shared build entry with existing `scripts/artifact_integrity.mjs`,
`scripts/public_asset_safety.mjs` and `deploy/publish.py` according to their current contracts.

Direct verification covers CI failure for invalid tracked inputs, offline build without
TuShare credentials/backend, artifact integrity failure and deployment of verified exact
bytes. Publication must satisfy applicable real-data distribution authorization and Pages
permissions. Completion requires successful build/artifact evidence and authorized deployment
evidence when publication is requested. Unrun deployment remains NOT VERIFIED. Broad E2E,
platform or browser matrices require explicit user direction.

## DDB-01 completion and entry decision

Document semantic review must reconcile sole ownership, stable navigation, independent
business-result Build admission, current cutover and scoped verification. Historical
`DDB_00_ACCEPTANCE.md` remains evidence of its own execution. Its ignored-artifact cleanup
and platform limitations do not block DDB-02 under the current root policy.

The inspected HTTP surfaces support proceeding to DDB-02. Actual capture, source availability,
Store contents, login and generated-artifact freshness are NOT VERIFIED. They are explicit
DDB-03 prerequisites/evidence, not claimed DDB-01 runtime success. DDB-01 stops after its
independent authority commit.
