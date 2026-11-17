# DDB implementation handoff

## Current delivery and historical evidence

The implemented pipeline admits nine registered Bundles and composes ten static pages.
Current identities belong to [Demo authority](../ARCHITECTURE.md) and
[workspace navigation](../../workspace.md#route-and-bundle-identities).
[WP7](#wp7--calendar-spread-local-delivery-2026-11-16) records the nine-Bundle local
capture/build/browser delivery; [Issue #13 follow-up](../../../market_research/descriptive/cases/futures_calendar_spread/AUTO_PREPARATION_RECONCILIATION.md#current-delivery-and-evidence)
records later bounded execution acceptance. Neither record implies a new Pages publication.

[DDB-06 first public execution](#first-public-execution-and-online-acceptance) records
eight-route online acceptance for its exact original source SHA. It does not verify
that today's public deployment matches this checkout. This documentation review does
not rerun deployment or browser acceptance.

Earlier DDB package instructions, missing-data blockers, seven/eight-member counts
and manual-main release procedures below retain their original historical scope.
Current publication follows the [Release Runbook](../release/RUNBOOK.md).

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

Git blob hashes were checked against every Manifest entry after data commit.
The active Bundle/Manifest JSON paths pin checkout to LF in .gitattributes, preventing
Windows autocrlf from invalidating canonical bytes on a subsequent checkout.

## DDB-05 closure - 2026-11-15

Current status supersedes earlier undelivered-data/publication-gate statements above.
DDB-04-R1 delivered the real Dataset. Root AGENTS.md now records the user's personal
study/research policy; data authorization investigation is not an execution/publication
gate unless explicitly requested. Original sources and disclaimers remain unchanged.

DDB-05 Implementation: PASS. Deployment: NOT VERIFIED (intentionally not requested).
No PR, merge, Pages dispatch, Environment change or real market-data collection occurred.
The existing feature branch was pushed with explicit user authorization for Linux CI.

### Implementation and evidence

- 2695e36: policy reconciliation and narrow deployment authority.
- 774cbe7: receipt, Git/Manifest identity, exact file inventory, safety and isolation.
- b25f16c: manual offline CI, cross-job byte verification and confirmed-main Pages flow.
- 5938932: classify Presets as configuration; eight active data files stay hash-reviewed.

[Ubuntu Actions run 43722528491](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43722528491)
PASS on 5938932f27199030e1efeb7407e52152cbfa2539. demo-build and demo-reverify succeeded;
ordinary frontend/manual regression jobs were skipped. Node 22/npm installed from lock,
Public Safety passed (25 reviewed payloads), seven-Bundle admission passed, all 82
admission tests passed on Linux, the offline Vite build passed, and receipt scan,
verification, upload/download and independent second-job verification passed. No Python,
backend, Collector, TuShare credentials or account secrets were supplied to these jobs.
The existing large-chunk build warning remains informational.

Receipt: five files; Manifest SHA-256
179f1fe0681e7902eb3030f1bd2b93e5a31b0a42ff1256d62f4e9e8ce98f7dff;
artifact digest ee564a4ffe09f5a0b9502c14e209f105cf54bff8f219682262aacf48ac8a02e1.
The receipt and exact site are retained as separate Actions artifacts for 14 days.
This is contract/safety/integrity evidence, not independent financial accuracy proof.

The initial run 43722402638 failed closed on an extra Presets inventory entry: local
CRLF bytes differed from Git/Linux LF bytes. No Dataset change occurred. The fix removes
that configuration entry and uses an exact-path config exemption, like the two Demo
TypeScript configs. The eight Bundle/Manifest entries match actual Git blob SHA-256.
Presets are still checked by formal admission and unchanged from the baseline.

Local scoped verification passed receipt identity/tamper/reference/isolation failure
cases, existing artifact symlink/credential/private-path tests, and Public Safety tests.
Combined admission/runtime tests: 88 passed, one Windows symlink case skipped for EPERM;
that admission case passed in Linux CI. Actual workflow guard executed with Bash:
feature ref rejected, matching main accepted, mismatching SHA rejected. Local real-Dataset
build and existing browserAcceptance passed eight routes, local interactions, history
and static-only network activity. No broad Browser Matrix or business regression ran.
A standalone YAML-parser check was unavailable (no installed yaml package); GitHub
accepted the dispatched CI workflow. Pages execution remains unverified.

### Release handoff

Read-only GitHub API inspection confirmed Pages build_type=workflow, Actions enabled
with allowed_actions=all, and github-pages custom branch policy allowing main plus the
historical feat/github-pages-demo branch. No protections were modified. The new release
workflow itself rejects every non-main dispatch before checkout/build and requires the
confirmed full SHA to equal the dispatch SHA. Pages/OIDC write permissions are confined
to the protected deploy job; verification failure prevents deployment through needs.
Actual Environment rejection and the Pages upload/deploy path are NOT VERIFIED.
The deployment job's automatic token permissions are validated only by actual release.

The DDB-05 manual entry described here is historical and superseded by DDB-06;
current commands are in the [deployment guide](../../deploy/README.md#verified-demo-pages-release-ddb-06).
After Final Reconciliation and user-reviewed merge to main, the user explicitly starts
Manual Demo Pages release on main with its full confirmed SHA. Push main does not
publish. No further data-rights approval is required by current project policy.
The current branch is ready for Final Reconciliation and merge preparation; neither
merge nor publication is performed by DDB-05. The empty Publication Bundle is preserved.

Git diff against baseline 2ca1d52782b3ffcaf42ebac0299fad0e6c7c267b confirms no change to
seven Bundles, Manifest, Presets or .gitattributes. No historical Demo fallback exists.
Generated local build/receipt files remain ignored; no business store or cache was deleted.

## DDB-06 — Dedicated release publication

Supersedes DDB-05 manual main dispatch. Release Requirements enter
[release authority](../release/ARCHITECTURE.md); publication enters
[deployment guide](../../deploy/README.md#verified-demo-pages-release-ddb-06).
Only release/demo-pages push deploys; candidate must already be on remote main.
DDB-00–05 collection, Bundle ownership and artifact transfer remain intact.
Actual first-release evidence is recorded after execution, never inferred from local PASS.

### First public execution and online acceptance

On 2026-11-15, source cdf697d0f37f5eee08a8f4406440d78b4ece563c passed the Linux
release gate and independent deployment-job artifact verification in
[Actions run 43726003773](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43726003773).
Pages deployed to https://ougachakaaa.github.io/hg-market-state-lab/.
Online eight-route browser acceptance passed, including MO results, Basis charts,
M1/Q1 interaction, direct hidden Explorer and truthful empty Publication capture.
Every public file matched the downloaded CI Receipt by size and SHA-256 when read
through the browser network stack. Node fetch timed out in this environment; the
publisher correction uses the verified browser path without weakening byte checks.
The subsequent user-authorized history repair replaces the original integration
commits. This run remains historical evidence for its original source SHA; any
replacement release requires its own gate, deployment and online acceptance.

## WP7 — Calendar Spread local delivery (2026-11-16)

The current dataset extends DDB-02–06 to nine required Bundles and ten static
routes. Two real synchronous authenticated FastAPI captures use shared WP6
Presentation and feature-owned validation. Existing seven Bundle bytes/hashes are
unchanged. Local capture/admission/build/Chromium acceptance is complete; no
publication occurred. Current evidence, exact requests, sample coverage, tests and
limits enter [Calendar Spread acceptance](../CALENDAR_SPREAD_ACCEPTANCE.md).
Earlier seven/eight-member counts above are historical DDB evidence.
