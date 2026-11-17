# Demo collection and build authority

Specializes [Demo authority](../ARCHITECTURE.md) and consumes [Bundle contract](../BUNDLES.md).
Formal acquisition routes are owned by the [HTTP catalog](../../../ui_http/HTTP_PRODUCTS.md);
current Bundle membership and capture bindings are declared in the Registry and Presets.

## Explicit HTTP collection

DDB-03 exposes `poetry run python ui_web/demo/build/collect.py --all --base-url
http://127.0.0.1:8011` and mutually exclusive, repeatable `--only <bundle_id>`. Username can be
provided with `--username`; password is entered with getpass. Poll interval, Run deadline
and HTTP request timeout default to 2, 1800 and 60 seconds and accept finite positive
CLI overrides. Origin comes exclusively from lab_config Auth settings. Requests are
sequential, with no automatic redirects or retries.

The internal Node bridge retains strictly parsed HTTP payloads and assembles canonical
Bundle bytes using DDB-02 JSON tooling. Python receives navigation metadata and response
references, never serializes financial payloads. Complete generated HTTP envelopes are
validated before extraction. Candidate admission always invokes the independent demo:check.

Collection holds the shared atomic directory lock described below. Normal completion
releases ownership; forced termination requires explicit stale-lock recovery.
`pending.json` names one same-root candidate and its exact replacement hashes. Candidate
bytes and journal are flushed before pending publication. Recovery verifies the complete
candidate with Preflight, then repeats selected replacements and replaces Manifest last.
Only explicit Collector invocations recover transactions. DDB-04 must coordinate with this
lock and reject pending.json before loading inputs, as specified below. Corrupt pending
resources fail closed.

The Python Collector runs from repository root in the sole Poetry environment.
It accepts an explicit Bundle ID or all, an HTTP base URL, and the selected committed
Presets. Runtime environment configuration follows root `lab_config` policy. Credentials
are supplied interactively and held in memory. Login uses existing `/auth/login`, a Cookie
jar retaining renewed cookies, and the configured same-origin headers required by Auth.
An approved active user and correctly configured serving app are prerequisites.

Collector validates required fields, formal types, canonical dates and date order, then
calls only published HTTP operations. Backend retains final trading-day, instrument,
availability and strategy-rule decisions. Collector imports no business service,
Repository, Publication Reader, Research Executor, DataLake or Backtesting Core.

For Run products submit the formal body once, poll the owned Run until terminal, then
fetch and validate the complete report/result. Preflight is advisory and optional, with
ready=false preserving the formal submit policy. Failed/interrupted Runs and unavailable
results fail collection. A lost submit response is an explicit failure requiring operator
resolution because POST is non-idempotent. Never blindly resubmit. Polling has an explicit
finite operator-configurable deadline and bounded interval. Timeout leaves active data
untouched. GET failures are reported with safe HTTP status/kind and require explicit retry.

MO responses are stored complete. Basis and Backtesting validate the complete HTTP envelope
and associations before extracting immutable request and data. Static adapters pass
`{request, report: result}` or `{request, result}` to existing embedded validators.
Premium passes the raw body to `validatePremiumPlane` and uses its returned presentation
wrapper only in memory.

Catalog collects list and every listed detail. Publications follows `after` exactly as
returned, from the first page with limit=50 through a null next_cursor, including a final
empty page when returned. Repeated cursors, duplicate identities, failed detail reads or
changing/inconsistent references fail capture. Fetch each Manifest and every Analysis and
View it references, sequentially to respect existing reader capacity. Validate each full
HTTP response before extracting its DTO. No Store snapshot isolation is inferred from
pagination. Collection should target a quiescent Store; association checks reject observed
inconsistency. Empty results are recorded truthfully.

## Dataset update transaction

Acquire an exclusive process-held lock before inspecting or updating active data. Future Build
must coordinate with the Collector lock for admission and input loading. A concurrent operation fails
with a clear busy result. The lock is outside the active Bundle directory and releases on
process exit. A durable pending-transaction marker independently blocks Build after a crash.

Fetch and validate all selected captures in ignored staging on the same filesystem under
`ui_web/.build/demo-collection/`. Before changing active files, construct and validate the
entire candidate dataset, including unchanged files, Manifest and exact hashes. Acquisition,
serialization or validation failure preserves active bytes and publishes no new Manifest.

Persist all replacement bytes plus a durable forward-completion journal before the first
active replacement. Replace selected Bundle files atomically per file, then replace the
Manifest last. The lock prevents cooperating readers seeing the intermediate set. Build
fails closed while a pending marker exists. This protocol provides transaction admission
across files; filesystem rename alone supplies only per-file atomicity.

On an interrupted commit the next explicit Collector invocation acquires the lock, verifies
the staged candidate hashes, completes the same replacements and Manifest, validates the
active set, and removes the marker before beginning another request. Recovery is idempotent.
Missing/corrupt staging requires an explicit reported repair, and Build stays fail-closed.
Successful completion removes staging/journal. These are temporary transaction resources
with no historical dataset selection, backup retention or previous-generation rollback.
No startup-time data deletion is introduced.

## Build admission

DDB-02 implements the standalone offline `demo:check` command and `demo:registry`
export described in the [Bundle interface](../BUNDLES.md#offline-admission-interface).
It validates a quiescent local dataset without Collector or serving dependencies.
DDB-03 implements Collector locking, pending-transaction recovery and candidate staging.
DDB-04 implements coordinated snapshot admission and Vite integration. The default
build admits the current nine-Bundle dataset and fails closed on missing/corrupt input.

### Node Build coordination constraint

#### Shared directory coordination

Collector and Node Build exclusively create `.build/demo-collection/dataset.lock/`
with atomic mkdir. Contention fails immediately. Both release in finally on normal
completion or caught failure. Forced termination leaves the directory and fails closed.
There is no timeout-based or PID-based lock stealing. Stop all Collector/Build processes
and confirm no holder remains before explicitly removing this exact lock directory.
Keep pending.json and candidate staging intact; the next Collector completes recovery.
Before the protocol cutover stop old Collector processes and remove the old dataset.lock
file only after confirming no process holds it. A file at the new lock path fails closed.

Build holds a separate `.build/demo-output.lock/` for its entire invocation to serialize
output replacement. The same explicit stale-lock procedure applies. After acquiring it,
Build removes prior formal output. Under the dataset lock it rejects pending.json, copies
all dataset files to private staging and independently runs DDB-02 Preflight there.
Only after admission fixes the snapshot does it release the dataset lock. Vite consumes
that snapshot exclusively. Build never runs Python, Collector or business HTTP.
Vite writes private output, checked before promotion to `.build/demo/`; errors remove
formal output and never publish a completion marker. Platform claims require actual tests.

Build tooling accepts an internal `outputRoot`, restricted to `.build` or a child of it.
The default remains `.build`; output, output lock and invocation staging are derived
from that root. Dataset coordination still defaults to the canonical Collector work
directory independently of output placement. Tests supply their own dataset work
directory and unique child output root, never developer-owned Demo output or locks.
Output paths and their existing ancestors must be unlinked at acquisition, cleanup,
artifact completion/promotion and lock release. A detected redirection fails closed;
never follow it to remove output or release another directory's lock. This protects
against observed filesystem redirection, not arbitrary concurrent hostile filesystem
mutation between a check and a filesystem operation.
Success, admission failure and compile failure clean only that invocation's resources. Actual Vite build tests are
an explicit `npm run demo:test:build` specialist check, excluded from ordinary `npm test`.
Pure runtime adaptation and Bundle admission remain independently selectable tests.

Snapshot loader generation follows the admitted Manifest's canonical Bundle order;
each Bundle is emitted as its own dynamically imported static JS module. All modules
come from the frozen snapshot, with complete DTOs and no runtime business acquisition.
Filesystem enumeration never defines output order. Runtime dependency inventories
normalize paths and sort them lexically before serialization. These rules do not change Bundle bytes,
Manifest identity, release admission or the requirement to validate all Bundles.

Both source and private snapshot run independent DDB-02 Preflight. Source admission
preserves path/reparse protections across copying. Admission verifies Registry, Manifest,
complete membership, deterministic exact bytes, SHA-256, envelopes, Presets and feature
Result contracts. Catalog details and Publication reference closure remain mandatory.
Bundle admission owns packaging/integrity; feature validators own formal Result semantics.
Failure reports a safe Bundle/stage diagnostic before Vite. No repair or generation occurs.

From ui_web run `npm run demo:build`, then `npm run demo:preview` at
http://127.0.0.1:4173/hg-market-state-lab/. Preview requires the completion marker and
no output lock. Online npm run build retains its independent configuration.

### Local UI review (no publication)

For Demo UI changes, reuse committed Bundles and run from `ui_web/`:

```powershell
npm run demo:build
npm run demo:preview
```

Open http://127.0.0.1:4173/hg-market-state-lab/#/research for visual review;
stop preview with Ctrl+C. Rebuild and reload after editing; preview serves the built
artifact, without hot reload. No backend, collection, remote push, Actions build
or Pages publication is needed.

Run `npm run demo:test:browser` after the build for local Playwright review. It starts
temporary loopback previews and closes them afterward, checks all ten Demo routes
and existing interactions, and checks Research Overview at 1280, 1024 and 768px.
Focused checks cover full disclosure, horizontal containment, card alignment,
Production-mode shared Presentation and Chinese/unbroken-English stress inputs in
a test-only harness. Screenshots are saved to ignored `.build/demo-review/`.
Production coverage here verifies Presentation, not authenticated backend flows.
For isolated acceptance, `previewDemo(port, { outputRoot })` and
`verifyBrowser(url, { outputRoot, reviewRoot })` consume the chosen build without
rebuilding or replacing developer output. `localReview.mjs --output-root <root>`
uses that root for preview and review artifacts; the default invocation is unchanged.
Use installed Playwright Chromium or set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`
to a compatible existing browser. An unavailable browser is NOT VERIFIED.
These checks are explicit commands, not a default gate for unrelated development.

After stopping all relevant processes and verifying no lock holder remains, run from
repository root only for the identified stale lock. For a directory lock use
`Remove-Item -LiteralPath '.\ui_web\.build\demo-collection\dataset.lock'`.
For the output lock use
`Remove-Item -LiteralPath '.\ui_web\.build\demo-output.lock'`.
Run either command only after confirming that every process holding that lock has stopped.
These empty-directory operations preserve pending transactions and their candidates.
Never delete pending.json, candidate data or valid Bundles to clear a stale lock.
The same first command removes an identified old protocol lock file after all old
Collector processes have exited. Never remove a lock while its holder is running.

## Static loading and release

Vite emits one anonymous application under `ui_web/.build/demo/`. Runtime adapters consume
validated static results through feature public `presentation.ts` entries. Shared code,
local interactions and existing formal routes are reused. Run IDs are never fabricated.
Online imports no Demo data/tooling. Browser requests are restricted to static resources.

Local build and GitHub Actions use the same entry, data and standards. Static preview uses
the emitted directory. UI-only work can build existing valid data. Release requires local
build/preview acceptance before commit, then independent Actions admission and artifact
verification. Deploy consumes verified artifact bytes and never regenerates business data.
Artifact integrity, publication permission and source disclosure remain applicable release
requirements. DDB-05 owns their integration with existing deploy tooling.

Release specializes this build contract through [deployment authority](../../deploy/ARCHITECTURE.md).
The root personal-study policy supersedes former authorization gates.

## WP7 synchronous captures and coordinated extension

Calendar Spread uses the two complete HTTP 200 DTOs specified by
[its integration contract](../CALENDAR_SPREAD.md#wp7-delivery-contract).
Repeated `--only` arguments select a set in one candidate transaction. Unselected
files must match the existing Manifest hashes before copying, including during
seven-to-nine membership extension. Independent complete candidate admission remains
mandatory; no partial membership is allowed by Build or Preflight. Response schema
validation precedes feature-owned association validation and payload reference retention.

### Explicit loading measurements

`node demo/build/browserPerformance.mjs <outputRoot> <evidenceRoot>` measures an
already-built local artifact with installed Chromium, a fresh context and cache-enabled
same-document navigation. It records actual Resource Timing/CDP transfer and body sizes,
content encoding, result-ready duration and script execution duration, separately from
Bundle load/validation measures. It does not intercept requests or rebuild data. An old
artifact without Bundle measures has no isolated validation timing; never substitute
result-ready duration for validation time. Store generated evidence in ignored temporary
output, not tracked historical reports. Compare artifacts only with identical inputs,
browser and serving conditions; uncompressed preview transfers are not gzip transfers.
