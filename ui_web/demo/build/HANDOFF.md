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
eight application pages and local controls. Online entry keeps its own data path. Build loads
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

## UI integration baseline - 2026-11-15

UI-01-R2 source `5342f83058ba9e691a59c5221f42cfbba3f15a6b` was merged with no conflicts using no-ff merge `4dbff6e89bbeb78712d4ae62693a992cc4e8f453`. All seven UI commits and the DDB baseline history are retained. Application owns eight page identities, while the unchanged Registry owns seven Bundles. Overview routes create no Bundle. Explorer stays directly hash-accessible and hidden from the sidebar. M1/Q1 share the Backtesting instance page.

DDB-00, DDB-01 and DDB-02 are complete. DDB-03 Implementation and UI Integration are complete. DDB-04 implementation is delivered; current scoped evidence is recorded below. Real Bundle Capture is NOT VERIFIED. Seven real Bundles and their Manifest remain undelivered. DDB-04 Implementation is PASS; Operational Delivery and publication readiness remain BLOCKED by missing real data. The implemented build fails closed until that dataset exists. The retained UI, Bundle Contract, Validator and Collector provide the DDB-04 integration baseline. Actual capture remains the delivery prerequisite; coordinated Build locking is implemented.

UI-01 Branch Status is CLOSED after successful DDB push and ancestry verification, followed by remote/local UI branch retirement. Continue DDB-04 and DDB-05 directly on `feat/demo-bundle-workflow`. The DDB-04 integration baseline is READY; runtime implementation is delivered and real-data delivery prerequisites remain open.

## DDB-04 implementation evidence - 2026-11-15

Implementation is PASS for the single runtime, Bundle adapter, coordinated offline
build and local preview. Operational Delivery is BLOCKED by absent real captures.
Commits e8bca6e and 804396d introduce orchestration and runtime respectively; the
following acceptance commit completes preview, safeguards and reconciliation.

The retained composition moved to demo/runtime, using all eight current routes and
feature public Presentation entries. Seven Bundles map to chain, premium, Basis,
Catalog, Publications and independent M1/Q1 Results. Identity now reflects the actual
Bundle source, Preset and contract. No fabricated provenance is required.

From ui_web, scoped verification passed:

- Collector tests: 3 cases, including five controlled Python HTTP cases and recovery.
- Build tests: 3 cases, Python/Node exclusion in both directions, pending failure with
  old-output removal, forced process termination retaining exclusion.
- Admission tests: 81 passed, one Windows symlink case skipped due to EPERM.
- Runtime tests: seven directly scoped cases passed across selected invocations,
  covering mappings, missing/hash/Result failures, immutable snapshot after source
  updates, concurrent Build rejection, Vite failure and real Vite artifact generation.
- Both Demo tool/runtime TypeScript checks passed. Online npm run build passed with
  no active Bundles. The moved route tests passed all 12 cases.
- Real Chromium against the generated fixture artifact passed eight routes under
  /hg-market-state-lab/, three overview mounts, direct hidden Explorer, reload/history,
  Basis collapsed introduction and report sections, M1/Q1 selection, Backtesting Plotly
  mounting and static-only network activity. The existing Ant Design List deprecation
  warnings were observed. Basis fixture uses empty Views; nonempty Basis chart
  interactions and real-result browser acceptance remain NOT VERIFIED in this task.

Browser acceptance is explicitly opt-in, not part of routine test execution. On
PowerShell run `$env:DDB_BROWSER_ACCEPTANCE='1'` followed by
`npx vitest run --config demo/build/vitest.config.ts demo/build/runtime.test.ts -t "builds an offline"`.
Temporary synthetic datasets never enter demo/bundles. Build itself never invokes Python.
The local preview server was exercised by this browser acceptance and closed afterward.

Actual npm run demo:build fails closed with missing_directory on the absent real
Dataset. npm run demo:preview rejects absent completed output. Successful fixture
artifacts and private build staging were removed by scoped failure checks.
Cleanup affects only generated Demo output and invocation-specific temporary resources.

Real capture prerequisite inspection found LAB_AUTH_ORIGIN unset through lab_config.
A local 8000 listener returned no valid HTTP response to /auth/me (RemoteProtocolError).
No credentials were printed, no login was attempted and no real dataset was generated.
An approved identity, configured formal HTTP service, real market inputs and Publication
Store readiness remain required. Real source availability and distribution authorization
are NOT VERIFIED. Windows directory exclusion is verified; POSIX is NOT VERIFIED.

DDB-05 implementation planning may consume this runtime/build entry. Operational
publication readiness remains BLOCKED until a tracked real admitted dataset, successful
formal build/preview and distribution prerequisites are supplied. No CI/release change,
merge, push or Pages publication was performed.

## DDB-04-R1 operational closure - 2026-11-15

DDB-04 Implementation: PASS. Operational Delivery: PASS for the local real-HTTP
Dataset, independent admission, offline build and static browser acceptance below.
Historical fixture evidence above is not the evidence for this real delivery.

The user changed current Presets to IM 2026-03-01 through 2026-09-30 for Basis and
both Backtesting profiles, and MO 2026-09-30 close for Chain/Premium. These replace
the initial dates; Producer coverage is retained without padding.

Formal Auth serving validation passes in loopback-http mode. The formal backend was
started with poetry run lab serve backend at 127.0.0.1:8011. Anonymous requests to
/auth/me, /research/capabilities and /research/publications returned 401. The first
login failed because a trailing input punctuation character was interpreted as part
of the password; after user clarification, formal /auth/login and /auth/me returned
200. The approved identity was used throughout. No bypass or account mutation occurred.
At the user's explicit request, operator credentials were saved only in ignored root
.env; they are absent from Bundles, tracked files and committed evidence.

The existing Collector was invoked with --all and the formal base URL. Interactive
credential input was supplied in memory by a one-off operator wrapper; Collector code
and authentication behavior were unchanged. All seven captures, complete Result
validation and candidate admission passed. The sole active Dataset is demo/bundles/:
seven registered JSON Bundles and one Manifest, with no extra dataset or archive.

| Bundle | Formal HTTP acquisition | Actual result and coverage |
| --- | --- | --- |
| basis | Submit 202; owned polling/report 200 | complete; 147 candidate dates, 2026-03-02 through 2026-09-30; calendar/futures/index coverage complete; two Views |
| catalog | List and every returned detail 200 | Full currently published catalog: one capability and one matching detail |
| chain | GET /mo-option-chain 200 | MO 2026-09-30 close; six expiries, 131 calls and 131 puts |
| expiry_to_M1_v1 | Submit 202; owned polling/result 200 | complete; 147 sessions, 2026-03-02 through 2026-09-30; 14 trades, six rolls, two Views |
| expiry_to_Q1_v1 | Independent Submit 202; owned polling/result 200 | complete; same 147-session window; eight trades, three rolls, two Views |
| premium | GET /mo-option-premium-plane 200 | MO 2026-09-30 close; six expiries, 262 points |
| publications | GET /research/publications?limit=50 200 | One terminal empty page; zero Manifests, Analyses or Views |

Both default case-owned SQLite Run Stores worked for actual execution. TuShare-backed
formal producers supplied the requested market results; their original source and
coverage statements are preserved. HTTP acquisition records third-party results and
does not independently guarantee their truth. The user selected an empty development
Publication Store, configured via root .env under ignored market_research/.runtime/.
It is operationally valid but provides no existing research findings for the portfolio.
No Publication was fabricated, and no market cache or prior Run was deleted.

Scoped acceptance:

- Collector: PASS full authenticated HTTP capture and seven-Bundle admission.
- npm run demo:check: PASS independently against the active Dataset.
- npm run demo:build: PASS source and private-snapshot admission, followed by Vite.
  The unchanged build entry spawns Node admission only and never starts Python,
  Collector or FastAPI. The backend was separately started for collection.
- npm run demo:preview: PASS at the standard /hg-market-state-lab/ base.
- Existing browserAcceptance.mjs invoked directly against the real artifact: PASS
  eight routes, local interactions, direct hidden Explorer, reload/history and
  static-only network requests (business API/Auth requests rejected by the harness).
- Additional real-result browser checks: PASS Chain 12 traces/262 points; Premium
  table 34 displayed rows; nonempty Basis charts; M1/Q1 results and nonempty charts.
  An initial supplemental probe incorrectly expected a Plotly chart on Premium and
  timed out; corrected table-specific verification passed without product changes.
- Online npm run build: PASS. Both builds emit the existing large-chunk warning.
- All eight dataset files: PASS inspection for configured secrets, supplied account
  values, Cookie/auth fields and machine-private paths. Manifest and exact bytes
  pass independent admission. Documentation/configuration diff reviewed.

No financial code, Result Validator, Collector, Demo Runtime, CI or Pages workflow
changed. No PR, merge, push or site publication was performed. DDB-05 formal release
acceptance can now begin as a separate task; this task does not execute it. The empty
Explorer content remains an explicit portfolio limitation.
