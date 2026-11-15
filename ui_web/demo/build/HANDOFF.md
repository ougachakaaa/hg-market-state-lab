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

### Implementation closure

DDB-03 implementation is PASS and may close independently of operational delivery.
Reconciliation reviewed collect.py, collectorBridge.ts and json.ts against build and Bundle
authority. No implementation defect requiring a code change was identified.

| Implementation concern | Status and evidence |
| --- | --- |
| Python Collector | PASS, Registry-driven seven captures and single-Bundle byte preservation |
| Node Bridge | PASS, generated/feature-owned validation and numeric admission, financial payloads retained in Node |
| HTTP Auth/Run orchestration | PASS, controlled Cookie/Origin, submit/poll/result and failure cases |
| Candidate Preflight | PASS, actual independent DDB-02 CLI before transaction admission |
| Transaction / Recovery | PASS, lock contention, interrupted replacement, corrupt candidate rejection and idempotent forward completion |

All business Results enter through formal HTTP. Seven Bundle identities use the DDB-02
Registry. No competing business DTO or historical V1/Public/Private fallback is introduced.
Numeric values outside DDB-02 exact Number round-trip admission are rejected. Unselected
Bundle bytes are copied unchanged. Failed acquisition leaves active bytes intact. Interrupted
replacement retains pending.json until verified forward completion, blocking future Build
admission. Build coordination remains an unimplemented DDB-04 obligation documented in
[build authority](ARCHITECTURE.md#node-build-coordination-constraint).

### Focused verification evidence (2026-11-15)

Executed on baseline 9262eddfc1250a498b9b6b372dc5aadd620f85f0 with the documentation
reconciliation in the working tree, from ui_web using
`npx vitest run --config demo/build/vitest.config.ts demo/build/collector.test.ts demo/build/validate.test.ts`.
Both files passed, with 84 tests passed and one skipped in 63.70 seconds. The Collector
wrapper also ran five Python controlled HTTP cases in the root environment. Coverage includes
numeric fidelity, actual candidate Preflight, failed/interrupted transactions, recovery and
Registry/Bundle admission. The file-symlink rejection case was skipped on Windows for EPERM
and remains NOT VERIFIED in this environment. Existing junction cases passed.

Semantic and complete diff review cover the documentation changes. Verification is limited
to these directly related cases. Real capture, Demo Build, browser checks, deployment and
CI publication were unrun. UI authority review found no known contract conflict in the
current branch. The separate UI branch remains unmerged and its actual diff is unverified.

### Operational delivery

| Delivery concern | Status |
| --- | --- |
| Real authenticated HTTP capture | NOT VERIFIED |
| Seven real Bundles | NOT VERIFIED, no real dataset delivered |
| Git-tracked real Manifest | NOT VERIFIED, remains undelivered |
| Public distribution requirements | NOT VERIFIED, source disclosure, data authorization and artifact integrity remain required |

The prior DDB-03 inspection recorded protected HTTP 401 and missing LAB_AUTH_ORIGIN.
This reconciliation performs no live capture or endpoint probe. Configure LAB_AUTH_ORIGIN
through root lab_config, supply an approved active login identity interactively, and make
real source data, Run services and Publication dependencies available before operational
acceptance. These prerequisites and distribution authorization remain unresolved.
Controlled HTTP Fixture success supplies implementation evidence only. Real capture and a
tracked independently admitted dataset remain DDB-04 delivery prerequisites.

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
forward completion. Controlled HTTP fixtures verify implementation behavior. Implementation closure requires
the scoped cases above to pass. Operational delivery requires a tracked real dataset acquired
through formal authenticated HTTP and independently admitted, plus distribution authorization.

## DDB-04 — Single Demo runtime and build

Goal is one static runtime sharing feature Presentation. Requires valid DDB-03 data and
DDB-02 Preflight. Create `demo/runtime/` entry, static Bundle adapter and
`demo/build/vite.config.ts`; connect `package.json` demo:build and a local artifact preview.
Reuse or move the retained `src/demo/shell/hashRoutes.ts`, `src/demo/static/StaticWorkspace.tsx`
and `results.ts` into canonical Demo ownership, updating local consumers. Existing ResultIdentity
fields must be reconciled to actual captured provenance; remove obsolete required assertions
rather than fabricate sourceRevision/fingerprint/evidence provenance absent from HTTP.

DDB-04 integrates the latest merged UI Composition using
`src/features/*/presentation.ts` entries and the current app route inventory. Bundle IDs and
Result Contracts remain independent of routes, Overview Cards and Tab Composition, whose
ownership stays with Application / Presentation authority. Preserve all
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
