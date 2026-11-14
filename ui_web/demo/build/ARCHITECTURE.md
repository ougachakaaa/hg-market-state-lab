# Demo collection and build authority

Specializes [Demo authority](../ARCHITECTURE.md) and consumes [Bundle contract](../BUNDLES.md).
Implementation is assigned in [handoff](HANDOFF.md). HTTP evidence is in
[feasibility](HTTP_FEASIBILITY.md).

## Explicit HTTP collection

The future Python Collector runs from repository root in the sole Poetry environment.
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

Acquire an exclusive process-held lock before inspecting or updating active data. Build
uses the same lock protocol for admission and input loading. A concurrent operation fails
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
The lock, pending-transaction handling, byte staging and Vite integration below remain
assigned to DDB-03/DDB-04. The current `demo:build` entry remains BLOCKED.

The future single `npm run demo:build` entry executes offline Preflight before Vite. It
acquires the dataset lock, rejects pending transactions, verifies Registry/Manifest/file
completeness, paths, identity, envelope, deterministic bytes and SHA-256, then invokes
feature-owned generated-contract and semantic validators. Producer success is never an
admission input. Preflight copies its validated input bytes into ignored build staging
while locked so Vite consumes exactly those bytes even if later collection starts.

Bundle validation owns packaging/integrity. Feature validators own business shapes,
profiles, Visualization and request/result associations. Preflight schedules both and
checks complete Catalog details and Publication reference closure. Existing embedded
validators deliberately allow missing local detail states; complete Bundle admission
must additionally reject those omissions and nonterminal Publication pagination.

Any required failure terminates the whole build before Vite output is accepted. Diagnostics
name Bundle ID and validation stage. Build never silently repairs or regenerates input.
Build loads generated contracts already committed with their owning feature and has no
backend, Collector, Auth or market-data dependency. No TuShare token is required.

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
