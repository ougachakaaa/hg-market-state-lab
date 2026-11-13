# Portable SQLite storage reconciliation and work packages

## Authority, baseline and decision provenance

This Research-owned migration record coordinates readiness, not storage semantics or a
shared database. Canonical owners are [W1 storage](descriptive/cases/futures_basis/ONLINE_STORAGE.md),
[W2 storage](../market_backtesting/cases/futures_roll_long/ONLINE_STORAGE.md) and
[Publication storage](PUBLICATION_STORAGE.md#portable-sqlite-target), beneath their respective
application/business authorities and [repository architecture](../ARCHITECTURE.md).

Storage WP0 baseline: `github/develop` at `c68ba9af4194a51ceb3f7e06fd8f445d18d7dab6`,
fetched and verified 2026-11-12; clean working tree before creating
`feat/sqlite-portable-runtime`. No frontend/demo branch is incorporated. Storage WP0-WP6
numbering below is independent of all earlier case, Publication and Workbench packages.

The user explicitly revised the original proposal's Publication evidence-preserving
cutover: this development-stage project may abandon all old Publication data and directly
replace the file backend, without migration, compatibility, dual reads or dual writes.
The active facade, HTTP and Explorer capabilities and all new-publication integrity and
immutability guarantees remain. WP0 changes no code or runtime data; no automatic deletion
is introduced. This revised decision, not the superseded preservation proposal, is binding.

## Current storage status

W1, W2 and Publication exclusively use independent SQLite databases. Their POSIX
backends are retired. The WP2/WP3 and WP4/WP5 execution summaries below distinguish
implementation closure from actual platform acceptance. WP0 inspection descriptions
and original work-package requirements are historical baselines. The repository remains
pre-production; WP6 final acceptance is recorded in
[Storage WP6 execution evidence](#storage-wp6-execution-evidence).

## Inspected boundaries and reconciliation

Inspection covered repository/module/case authorities; W2 `online.py`, `online_store.py`,
codec/models and online application/store/failure tests; W1 `online.py`, its application,
preflight and HTTP tests; Publication `store.py`, `source.py`, `_platform.py`, errors and
publication/descriptor/closeout tests. Direct consumers include `ui_http` composition,
Futures Basis, Backtesting and Publication HTTP contracts/tests, and their Web feature
contracts. Configuration is owned by `lab_config`, root `.env.example` and DEVELOPMENT.
Historical WP8/WP9 acceptance is evidence of its original backend and platform only.

Severity: **blocking** prevents authority/readiness approval; **required** is a future
implementation gate; **informational** records an implementation choice or excluded scope.
An intended migration difference does not retroactively invalidate legacy acceptance.

| ID / severity | Classification and evidence | Resolution / closure gate |
| --- | --- | --- |
| A1 / required, resolved in WP0 | Genuine authority conflict: both ONLINE_APPLICATION contracts require file layouts/POSIX gates and separate atomic result/state files, conflicting with portable SQLite | Their explicit legacy-adapter status delegates replacement storage to independent ONLINE_STORAGE contracts; WP1-WP3 deliver the target |
| A2 / required, resolved in WP0 | Genuine authority conflict: PUBLICATION.md called the store JSON-based and PUBLICATION_STORAGE required descriptor-relative access/hard-link commits | Upper authority now distinguishes JSON encoding from storage; lower contract explicitly scopes physical requirements to current adapter and owns the SQLite replacement |
| A3 / required, resolved in WP0 | Superseded proposal required preserving legacy Publication evidence, while latest user explicitly permits abandoning it | Breaking cutover recorded above; new immutable evidence contract preserved; WP4/WP5 remove obsolete backend without compatibility |
| M1 / resolved for W2 in WP2 | W2 online_store.py gates on POSIX/UID, reads request/state/result files; online.py imports descriptor helpers and publishes result then state | WP1 adapter is integrated by WP2; descriptor coupling and legacy code removed, atomic result+COMPLETED and unchanged W2 application behavior verified on native Windows |
| M2 / required, intended migration | W1 online.py mixes POSIX persistence and application, separate report/state publication; no SQLite schema/version | WP3 replaces persistence while retaining exact request/report/profile and scientific complete/partial behavior |
| M3 / required, current implementation gap | W1 _execute suppresses final state persistence errors; _recover does not exclude an actual current-process active run or serialize with admission | WP3 must fail closed after unpersistable terminal state and serialize initialization/recovery with active-run exclusion; add failure-injection and simultaneous-initialization regression evidence |
| M4 / implementation closed in WP4/WP5 | Publication now uses independent SQLite records and one immutable snapshot transaction; POSIX backend removed | Native Windows canonical bytes, association, rollback, concurrent collision and real process interruption tests pass; other platform runtime remains WP6 |
| M5 / native implementation tests closed | W1/W2/Publication SQLite tests replace retired file-backend assertions | Native Windows regression, bounded BLOB reads, corruption/schema/alias/sidecar and process interruption evidence below; privileged symlink test skipped; four-platform acceptance remains open |
| M6 / integration closed on native Windows | HTTP no longer gates Publication on POSIX primitives; current documentation reflects SQLite | Stable DTO/OpenAPI, safe errors, native HTTP and real Chrome Explorer pass; Linux/WSL2/Docker runtime evidence remains WP6 |
| M7 / informational, no runtime config drift | lab_config already owns all three root settings; roots have directory meaning and configuration priority is centralized | Keep keys, defaults and lab_config calls. WP0 template/guide comments distinguish target filenames from current behavior |
| M8 / informational, preserved consumer boundary | HTTP consumes owning application/facade; Web consumes HTTP/OpenAPI, not private persistence | No production/generated files changed in WP0. WP2/WP3/WP5 provide HTTP and feature regression; no contract generation unless a separately approved wire change occurs |
| I1 / informational, implementation-only | SQL table names/indexes, connection encapsulation and journal selection are not business decisions | Each owner chooses minimal implementation in its WP; enforce separate metadata/BLOB reads, transactions, finite capacity and controlled sidecars. No shared framework |
| O1 / informational, out of scope | DataLake/Auth/Workbench SQLite, financial formulas, strategy, Statistics and Visualization schemas | No refactoring or semantic changes; run relevant regressions only |
| O2 / informational, out of scope | Queues, multi-process workers, network filesystems, cleanup APIs, legacy migration and distributed locks | Remain unsupported; SQLite does not authorize them |

Additional regression findings from WP0 execution (not newly introduced storage targets):

| Finding / severity | Evidence and classification | Disposition |
| --- | --- | --- |
| R1 / required regression follow-up | Two Demo fixture consistency assertions fail; baseline-exported test/script/fixture reproduce the same byte difference at offset 505845 and View mismatch with unchanged installed producer code | Out of WP0 storage scope; do not regenerate Demo or change calculations to make this documentation task green |
| R2 / required WP3 follow-up | W1 tests intermittently reject a subsequent submit as run_busy after terminal-state polling; different assertions fail across runs | Existing-code/test timing finding; preserve it explicitly and investigate worker completion/admission ordering in WP3 alongside M3, without weakening one-active-run semantics |
| R3 / required regression follow-up | HTTP TLS fixture does not become ready inside its polling window, in full suite and isolated rerun | Out of storage authority scope; no Auth/TLS code changes authorized here and no HTTP full-suite PASS claim |

There is no unresolved high-level storage decision after the approved cutover clarification.
Portable checks deliberately have a weaker hostile-concurrent-writer guarantee than POSIX
no-follow descriptors; this residual limitation is explicit in each owning contract, not
an assertion of perfect security equivalence. An implementation unable to meet these
contracts must report a blocker rather than silently relax them.

## Implementation work packages

All packages use the repository root environment and retain public Python facades, Auth,
owner privacy, safe failures, immutable results and original numerical outputs. Private
store interfaces may change for integration; no package may create a cross-module store.
WP completion must record actual PASS/FAIL/NOT RUN evidence and remaining drift.

### WP1 - W2 SQLite Store

- Inputs: storage WP0, W2 ONLINE_STORAGE and application lifecycle/codec/model contracts.
- Allowed: W2 private store and focused store tests; introduce only stdlib sqlite3.
  Keep production online integration for WP2; a temporarily unconnected new adapter is
  permitted, but do not claim application cutover in WP1.
- Invariants: independent root/database, schema version/structure rejection, immutable
  metadata/terminal states, owner-first reads, 32 MiB/strict JSON/digests, metadata/BLOB
  separation, atomic completion and recovery, portable root/alias/sidecar checks.
- Acceptance: existing W2 regression plus SQLite synthetic tests for create/reopen,
  unknown/version-0/incompatible/corrupt DB, foreign/malformed IDs, duplicate identity,
  illegal/terminal transitions, missing/mismatched/oversized BLOBs, bounded full reads and
  status reads that do not select payloads. Inject rollback/commit failures and real
  process exit before/after commit; verify absent partial visibility and restart recovery.
  Test traversal/symlink/junction/hard-link/unsafe-sidecar failures on capable platforms.
- Dependency: WP0. Non-goals: online wiring, HTTP/Web, financial logic, other stores.

### WP2 - W2 Online Integration and Regression

- Inputs: completed WP1, W2 ONLINE_APPLICATION and HTTP contract; current facade signatures.
- Allowed: W2 online composition/private persistence integration and related tests;
  remove retired W2 POSIX store plumbing when SQLite becomes active.
- Invariants: preflight independent of storage, busy creates no Run, one active execution
  and reader permit, exact result profile/complete-only and failure mapping, product-only
  unavailability, current-process recovery exclusion and terminal-persistence fail-closed.
- Acceptance: W2 full regression, HTTP owner/Auth/status/result/error parity, simultaneous
  submit/initialization, occupied reader versus cheap status, crash/restart and failed
  terminal commit. Verify exact fixture result equality and no generated contract diff.
- Dependency: WP1. Non-goals: W1, Publication, endpoint/DTO or financial changes.

### WP3 - W1 SQLite Cutover

- Inputs: completed WP2, W1 ONLINE_APPLICATION/ONLINE_STORAGE and existing reader evidence.
- Allowed: case-local persistence/application integration, removal of obsolete POSIX
  helpers, W1 and consumer regression tests. Reuse principles, not W2 store code/schema.
- Invariants: scientific complete/partial and empty findings, formal ReportRequest and
  reader profile, original failures, size/read limits, preflight, owner and permits.
  Close M3 without changing public operation signatures.
- Acceptance: full Research and W1 HTTP regression; atomic completion/rollback/recovery,
  fail-closed failed terminal persistence, active-run exclusion during new initialization,
  concurrent submit/read, corruption/schema/path bounds and exact report fixture parity.
- Dependency: WP2. Non-goals: formulas/Statistics, Publication, wire changes or generic engine.

### WP4 - Publication SQLite Persistence

- Inputs: WP0, PUBLICATION and PUBLICATION_STORAGE target; original encoding/projection
  and result association authorities.
- Allowed: private Publication SQLite persistence and focused tests; no compatibility
  abstraction. Transitional wiring is completed and old code removed by WP5.
- Invariants: one immutable atomic snapshot, collision even for equal content, independent
  granular records, exact canonical bytes/digests, source/Job/spec associations and budgets.
- Acceptance: transactional complete visibility/rollback/crash tests, identity collisions,
  strict encoding/version/schema rejection, per-record corruption and same-publication
  reference checks, source budget enforcement before BLOB loading, manifest reads without
  other payloads, selected Analysis/View reads without unrelated records, signed-zero parity.
- Dependency: WP0; independent of W1/W2 code. Non-goals: historical-data import, execution,
  Statistics recomputation, HTTP/Explorer redesign.

### WP5 - Publication Cross-platform Integration

- Inputs: completed WP4, source/facade and HTTP/Explorer contracts.
- Allowed: source capture and facade integration, delete retired file-store/POSIX gates,
  update platform tests and relevant runtime documentation. No dual backend remains.
- Invariants: stable retain_source/publish/read operations, external source verification
  then self-contained SQLite reads, no overwrite, allowlisted HTTP projection, unchanged
  Explorer business capabilities; read-only empty lookup creates nothing.
- Acceptance: Publication and HTTP suites, old-data ignored/same-root new initialization,
  explicit source capture failure/alias safety, original source removed after publish,
  source mismatch/collision/budget failures, import/backend startup without POSIX flags,
  actual Explorer regression and generated-contract freshness without regeneration.
- Dependency: WP4. Non-goals: importer, compatibility, endpoints/DTO changes, Run integration.

### WP6 - Final Platform Acceptance and Reconciliation

- Inputs: completed WP2, WP3 and WP5 with owner-specific evidence.
- Allowed: platform acceptance evidence, necessary portability fixes within approved
  contracts, current documentation and final drift closure; no historical evidence edits.
- Acceptance: actually run native Windows, Linux, WSL2 and Linux Docker on recorded local
  filesystems. Per platform demonstrate W1/W2 submit/status/full read/restart/owner/busy,
  Publication source capture/publish/list/manifest/analysis/view, corruption/schema rejection
  and safe path/sidecar failures. Record identity, SQLite/Python versions, filesystem,
  process model and platform-specific checks not executable without privileges.
  Run full affected Python, HTTP/generated-contract and browser regressions; distinguish
  portable storage fixtures from real-market scientific acceptance.
- Dependency: WP2/WP3/WP5. Non-goals: treating simulated flags, synthetic market data or
  historical Windows Chrome evidence as a newly executed native storage/platform matrix.
  Unexecuted platforms remain NOT RUN and prevent claiming the four-platform gate PASS.

## WP0 validation and verdict

Checks executed on 2026-11-12 in Ubuntu 24.04 WSL, Python 3.13.15, using this worktree's
only root `.venv`, initialized from unchanged `poetry.lock`. `npm ci --ignore-scripts`
installed unchanged frontend lockfile dependencies for the existing producer contract test.
No target adapter or owned SQLite database is delivered; regression tests use temporary
legacy state. This is not the WP6 four-platform acceptance matrix.

| Executed check | Actual outcome |
| --- | --- |
| `poetry run pytest market_backtesting/tests -q --tb=short` | PASS: 540 tests on final rerun; initial run was 539 passed/1 failed because Vitest was absent, then existing dependencies were installed |
| `poetry run pytest market_research/tests -q` | FAIL: 1,271 passed, 1 skipped, 4 failed (two Demo fixture mismatches, intermittent W1 run_busy, Git worktree path parsing) |
| Config + segmentation + W1 + Demo focused rerun with explicit WSL GIT_DIR/GIT_WORK_TREE | FAIL: 54 passed/3 failed; Git parsing failures cleared, two Demo failures and intermittent W1 run_busy remained |
| Baseline-exported Demo tests/script/fixture and W1 tests/fixture | FAIL: 26 passed/2 failed; both Demo consistency failures reproduced. Installed production Python is unchanged from baseline |
| `poetry run pytest market_research/tests/test_futures_basis_online.py -q --tb=short` | FAIL: 20 passed/3 run_busy failures on final focused run; failures vary by test timing, no code/test edits made |
| `poetry run pytest ui_http/tests -q` | FAIL: 587 passed/1 failed (TLS server readiness timeout); isolated test_auth_tls rerun also FAIL |
| `poetry run pytest config/tests -q --tb=short` with WSL Git paths | PASS: 26 tests; initial config/topology invocation had 38 passed/1 Git path failure |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q --tb=short` | PASS: 23 tests |
| `poetry run ruff check market_backtesting market_research ui_http config conftest.py` | PASS |
| `poetry run mypy market_backtesting` | PASS: 50 source files |
| `poetry run mypy ui_http` | PASS: 62 source files |
| `poetry run mypy market_research/tests` | PASS: 49 source files |
| `poetry run mypy config/src config/tests` | PASS: 3 source files |
| `npm run contract:check` in ui_web | PASS: all seven OpenAPI/TypeScript pairs current; no generated artifacts rewritten |
| Changed/new Markdown local links and anchors | PASS: 307 targets checked before this execution record; final check repeated before commit |
| Manual owner/topology/API and full diff review; `git diff --check` | PASS: independent owners, explicit current/target distinction, documentation/template-comment changes only |
| SQLite runtime, native Windows/Linux/Docker platform matrix, browser/real-market rerun | NOT RUN: not implemented or required for documentation-only WP0; no runtime/platform PASS inferred |

The first combined pytest and mypy invocations failed collection due to duplicate
`test_architecture` module names across modules. Checks were rerun separately as above;
no package markers or test changes were introduced to work around collection.
WSL Git subprocesses were supplied explicit Linux-form worktree Git paths because the
Windows `.git` pointer is not directly interpretable by Linux Git; tracked Git metadata
was not rewritten. These invocation/environment failures do not become product defects.

### Acceptance assessment

WP0 authority acceptance: **PASS (authority-only)**. Approved
SQLite-first decisions are discoverable with independent owners; existing normative
physical requirements are scoped to the legacy adapters, current/target delivery is
explicit, APIs and numerical/HTTP/generated contracts are preserved, transactional,
recovery, concurrency and portable trust requirements are encoded, and cutover is
unambiguous. Known implementation drift and regression exceptions are recorded rather
than silently fixed. Runtime regression gate: **FAIL**, for R1/R2/R3 above; this is not a
claim of a fully green repository or SQLite platform acceptance.

WP1 high-level implementation readiness: **READY**. Its independent W2 authority and
acceptance cases leave no missing business/storage decision; W2 regression is green.
Research fixture/timing and TLS findings remain visible and must not be represented as
closed by this documentation commit. Stop after WP0; no WP1 code is started.

### Changed-file roles

| Files (repository-relative) | Authority role |
| --- | --- |
| `ARCHITECTURE.md` | Repository preference, independent storage boundaries and navigation |
| `market_backtesting/ARCHITECTURE.md`, `market_research/ARCHITECTURE.md` | Module navigation and independent ownership |
| `market_backtesting/cases/futures_roll_long/ONLINE_APPLICATION.md`, `market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md` | Application lifecycle owner; scope current file-adapter requirements and delegate target storage |
| `market_backtesting/cases/futures_roll_long/ONLINE_STORAGE.md` | Canonical W2 target persistence contract |
| `market_research/descriptive/cases/futures_basis/ONLINE_STORAGE.md` | Canonical W1 target persistence contract |
| `market_research/PUBLICATION.md` | Business invariants independent of physical backend; breaking-cutover boundary |
| `market_research/PUBLICATION_STORAGE.md` | Current implementation status plus canonical future SQLite persistence/source/read contract |
| `market_research/STORAGE_RECONCILIATION.md` | This drift register, decision provenance, WP0-WP6 readiness and new execution evidence |
| `market_backtesting/cases/futures_roll_long/RECONCILIATION.md` | Append new W2 migration differences without rewriting earlier acceptance |
| `market_backtesting/cases/futures_roll_long/ROADMAP.md`, `market_research/descriptive/cases/futures_basis/ROADMAP.md` | Discoverable storage follow-up, independent of original WP numbering |
| `ui_http/products/backtesting/http-contract.md`, `ui_http/products/futures_basis_research/http-contract.md`, `ui_http/products/research_publication/http-contract.md` | Current-versus-target platform clarification; wire contract unchanged |
| `DEVELOPMENT.md`, `.env.example` | Current runtime guidance versus future directory-root SQLite filenames; comments only for configuration template |


## Storage WP2 execution summary

Baseline `eae9e8fc50b515753c52bd045f11feff2a8efa61`, branch
`feat/sqlite-portable-runtime`, 2026-11-13. W2 uses its independent SQLite database,
with pure record validation moved out of the deleted POSIX adapter. Owner-first reads,
process-wide admission/reader guards and active-aware recovery are retained. SQL type
and byte-length checks precede metadata/state BLOB selection. No data was migrated or
deleted; W1, Publication, Auth, DataLake, Workbench, formulas and public DTOs are unchanged.

**WP2 verdict: PARTIAL**: W2 focused/native-Windows checks pass; full HTTP regression
is blocked by the unchanged W1 POSIX store, and Linux runtime remains NOT RUN.
Detailed commands, platform results, verdict and remaining blockers are owned by the
[W2 WP2 evidence](../market_backtesting/cases/futures_roll_long/RECONCILIATION.md#storage-wp2-execution-evidence).
W1 native-Windows POSIX failures remain WP3 work; this summary does not close them.


## Storage WP3 execution summary

Baseline `5c20aaf03349def4c528a9086280f28d51dbc00e`, branch
`feat/sqlite-portable-runtime`, 2026-11-13, native Windows, root Poetry `.venv` (Python 3.13.7, SQLite 3.50.4, Windows 11 build 22000).
W1 now exclusively uses its independent `runs.sqlite3` (schema user_version 1).
`online.py` orchestrates execution; case-local `online_record.py` owns pure validation
and `online_sqlite_store.py` owns persistence. There is no W1/W2 shared store or schema.
The removed POSIX capability gate, descriptor-relative directory/file helpers and
per-run request/state/report execution paths have no fallback or feature flag.
Old Run files were neither read nor deleted; no market data or other stores were changed.

The metadata table retains immutable owner/request, timestamps, safe failure, execution
and scientific status, profile, length and digest; a separate table retains exact report
BLOB bytes. Short operation-owned connections use parameterized SQL, synchronous FULL,
rollback journaling and conditional transitions. Report validation and bounded canonical
serialization precede the single result-plus-COMPLETED transaction. Owner authorization
precedes the reader permit. SQL type/length inspection precedes payload selection;
status reads neither select report BLOBs nor check their digest.

M2 implementation gap: CLOSED by SQLite integration, atomic publication and scientific
complete/partial/empty parity tests. M3 and R2 implementation gaps: CLOSED by shared
process coordination for recovery/admission/terminal visibility, actual active identity
exclusion, deterministic concurrent-construction/submission tests, terminal admission
checks and explicit failed-terminal-commit injection. A poisoned store is unavailable
across same-root instances until process restart; the admission guard is safely released.
No sleeps/retries were introduced as a concurrency fix. The supported model remains
one backend process and one active W1 execution, independent of W2.

### Executed verification

| Platform / check | Result |
| --- | --- |
| Native Windows W1 storage/application focused tests | PASS: 25 passed, 1 skipped; symlink creation unavailable to OS account. Hard-link and unsafe-sidecar tests execute separately |
| Native Windows full Research regression | PASS: 1240 passed, 38 skipped before the final additional hard-link test; final focused suite covers that addition |
| Native Windows full HTTP regression | PASS: 571 passed, 17 skipped; focused W1 HTTP 37 passed. Previously reported 32 W1 errors and one failure do not recur |
| Native Windows full Backtesting regression | PASS: 590 passed, 2 skipped |
| Architecture/topology checks | PASS: 23 passed; case-specific boundary allowlists updated for the extracted validator and independent SQLite owner |
| Native Windows Mypy / Linux-target Mypy | PASS: Research and HTTP, 174 source files each; target checking is not Linux runtime acceptance |
| Ruff | PASS: Research and HTTP |
| Generated OpenAPI / TypeScript freshness | PASS: all seven pairs unchanged |
| Native Windows Chrome browser E2E | PASS: actual Chrome -> Vite -> FastAPI -> temporary Auth/W1 SQLite; submit/busy/poll/report/refresh/history/partial/error/logout; final exit 0. Browser fixture now counts SQL rows, and Windows cleanup terminates only its own child process trees |
| W1 frontend feature tests | PASS: 6 files, 40 tests |
| Frontend build / lint | PASS; existing large-bundle warning remains |
| Full frontend tests | FAIL: 446 passed, 2 timeouts in unchanged MO Option Chain/Premium Plane tests at 5000 ms. No unrelated product or timeout changes made |
| Demo fixture consistency focused rerun | PASS: five tests; historical WSL byte/View findings are not erased or claimed resolved on WSL |
| HTTP TLS | NOT RUN: native fixture skips because OpenSSL is missing; historical TLS readiness finding remains unverified |
| Linux / WSL2 / Linux Docker runtime | NOT RUN: no compatible root Linux environment exercised; installed WSL distribution is not acceptance evidence |

Real subprocess interruption tests terminate during completion commit: before commit
recovery yields INTERRUPTED with zero result rows; after commit recovery preserves exact
COMPLETED report bytes. Injected commit failure rolls back report/state atomically.
Scientific parity compares the complete accepted reader projection from unchanged
observation/report APIs, including formal specs, fingerprint, numerical results and Views.
Partial method failures and empty findings retain their existing scientific meanings.

WP3 verdict: **PARTIAL**, because the full frontend suite has two unresolved unrelated
timeouts and runtime platform gates outside native Windows remain unexecuted. Publication
migration state is unchanged. WP4 remains ready for its separately scoped implementation;
this commit does not start WP4 or establish WP6 four-platform acceptance.

Final combined W1 application/storage + HTTP rerun after bounded streaming serialization: PASS, 62 passed / 1 skipped. Browser script initially failed on its obsolete directory-count assertion; final SQL-count run passes. Browser server logs include a ClientDisconnect during deliberate lost-response coverage; the test completes successfully.

## Storage WP4-WP5 execution evidence

Baseline `7f0a0693b2c41a5363ecee5b048981f6c1b90113`, branch
`feat/sqlite-portable-runtime`, 2026-11-13. Initial branch/HEAD matched and the working
tree was clean. Execution used native Windows 11 build 22000, Python 3.13.7,
SQLite 3.50.4 and the repository root Poetry `.venv`. No Linux environment was used.

### Persistence and cutover

Publication exclusively uses `<root>/publications.sqlite3`, user_version 1.
`publications` retains the exact Manifest BLOB, its size/SHA-256 and the integrity
index; `records` retains Source, Analysis, View and Layer BLOBs keyed by Publication,
kind and local identity. The integrity index retains original per-record size and
SHA-256. No W1/W2 schema, Run identity, dependency or business lifecycle is reused.
Private `_sqlite.py` owns SQLite operations; `_paths.py` owns portable path checks;
`_records.py` retains the pure evidence/association helpers and `store.py` owns the facade.
No generic framework or second backend is introduced.

A valid empty schema commits before the first snapshot transaction. All snapshot
records then insert in one transaction; primary keys enforce collision even for
identical retries. Failed snapshot commits roll back. Independent-reader observations
and real subprocess `os._exit(73)` immediately before/after commit prove no partial
visibility and persistence of the complete committed snapshot after reopening.
Connections use synchronous FULL, DELETE journaling, parameterized statements and
foreign keys. In-process initialization/operations are serialized; this grants no
multi-process worker or shared-network-filesystem support.

Source capture uses exclusive creation, regular-file/ancestor/identity checks and
flush/fsync. Publication checks exact external source bytes against re-encoded Batch
evidence before retaining its SQLite copy. Reads remain valid after external source
deletion. Caller-selected source access stays explicit. Root, junction/reparse-point,
hard-link and sidecar checks retain the operator-controlled-filesystem trust boundary.
Windows reserved/alternate-stream path names are rejected. No hostile-writer or
perfect power-loss-durability guarantee is added.

Manifest reads select only Manifest/integrity metadata. Detailed reads share a read
transaction and load only required records. SQL type/actual length and source budget
checks precede BLOB selection; digest checks precede strict parsing. Existing source,
Job/request/spec, original failures/outcomes, coverage and projection checks remain.
Signed-zero roundtrip is tested; rewritten Layer bytes/digest with positive zero are
rejected against retained negative-zero evidence. No execution or numerical computation
is invoked by publisher/readers.

The POSIX capability module, descriptor-relative helpers, hard-link commit protocol,
bundle paths and old platform tests are retired. No legacy data was read, migrated or
deleted. The unchanged four HTTP routes retain Auth, allowlisted projection/redaction,
closed errors, response bounds and source verification capacity. Generated contracts
and React product implementation are unchanged. The browser harness now terminates
only its own Windows child process trees during cleanup.

### Actual verification

All runtime results below are native Windows. Synthetic public research fixtures are
used; no real market credentials or default market caches are needed.

| Check | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q --tb=short` (final full run) | PASS: 1279 passed, 3 skipped; includes W1 and Publication |
| `poetry run pytest ui_http/tests -q --tb=short` (final full run) | PASS: 586 passed, 2 skipped; includes W1/W2/Publication HTTP |
| `poetry run pytest market_backtesting/tests -q --tb=short` | PASS: 590 passed, 2 skipped |
| Publication/source/schema/path/atomicity closeout tests | PASS within full Research; junction/hard-link/sidecar, lock failure, canonical-byte and success/partial/failed outcome checks execute; privileged symlink creation unavailable to account and skipped |
| `poetry run python market_research/tests/publication_example.py` | PASS: source capture, publish, Manifest, Analysis and materialized View |
| `poetry run python market_research/tests/publication_read_cost_example.py` | PASS: list/Manifest read one logical Manifest and no source; Analysis reads Manifest/Source/selected Analysis; View reads Manifest/Source/selected View/Layer |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q --tb=short` | PASS: 23 passed |
| `poetry run ruff check market_research ui_http` | PASS |
| `poetry run mypy market_research ui_http` and `--platform linux` | PASS: 175 files each; Linux-target typing is not Linux runtime evidence |
| `npm run contract:check` | PASS: all seven OpenAPI/TypeScript pairs current, no regeneration |
| `npm run test -- src/features/research_explorer src/shared/visualization` | PASS: 10 files, 141 tests |
| `npm run build`; `npm run lint` | PASS; existing large-bundle warning remains |
| `npm run test` | FAIL: 445 passed, 3 timeouts in unchanged MO Option Chain/Premium Plane tests at 5000 ms |
| `npm run test:research-browser` using installed Chrome | PASS: real Chrome -> Vite -> FastAPI -> temporary Auth/Publication SQLite; publication browsing, selected details/Views, refresh/history, errors and logout at desktop/tablet sizes |
| `npm run test:visualization-browser` using installed Chrome | PASS: real Plotly interactions and V1 line/bar rendering |
| HTTP TLS | NOT RUN: fixture skips on native Windows without OpenSSL; previous TLS readiness finding remains unverified |
| Linux / WSL2 / Linux Docker runtime | NOT RUN; reserved for separately authorized WP6 |

Final pure-helper extraction was followed by another full Research PASS (1279 passed,
3 skipped), focused Publication HTTP PASS (16 tests), both Mypy targets and topology
checks. Relative Markdown file targets were checked (125 targets, none missing).

Initial Research run found two architecture allowlist failures for the new owner-local
SQLite dependency. The allowlists were narrowly updated; negative execution-boundary
checks still reject SQLite outside its authorized owners. Initial HTTP focused run
found a new test expecting incorrect safe error wording; the test now asserts the
unchanged existing wording. Linux-target Mypy initially rejected `os.path.isreserved`;
the portable stdlib `ntpath` import resolves typing on both targets. Final checks above
pass. Full frontend timeouts are recorded, with no unrelated product/timeout repairs.
The prior Demo fixture tests pass within native Research; no historical WSL finding is
erased or claimed resolved on another platform.

### Acceptance and remaining work

WP4 persistence: **PASS within the recorded native Windows scope**. Immutable atomic
SQLite snapshots, granular bounded verification and original evidence semantics are
implemented and exercised. This is not four-platform acceptance.

WP5 integration: **PARTIAL**. Native Windows Publication/HTTP, stable generated contracts
and real Explorer browser acceptance pass. The full frontend regression has three
unrelated timeouts; privileged symlink and TLS checks are unexecuted. Combined WP4-WP5
verdict: **PARTIAL**, without a claim of a completely green repository.

M4 is closed by the active SQLite cutover. M5/M6 native implementation/integration gaps
are closed only to the extent recorded above; their unexecuted platform portions remain
open. WP6 is ready for a separate final-platform acceptance task, retaining frontend,
TLS, privileged filesystem and Linux/WSL2/Docker gates. WP6 was not started. No merge
into `develop` or production declaration was made.

### Changed-file inventory

Status is relative to the required baseline; A = added, M = modified, D = deleted.

```text
M	.env.example
M	ARCHITECTURE.md
M	DEVELOPMENT.md
M	market_research/ARCHITECTURE.md
M	market_research/PUBLICATION.md
M	market_research/PUBLICATION_STORAGE.md
M	market_research/STORAGE_RECONCILIATION.md
M	market_research/descriptive/ACCEPTANCE.md
D	market_research/src/market_research/publication/_platform.py
M	market_research/src/market_research/publication/source.py
M	market_research/src/market_research/publication/store.py
M	market_research/tests/publication_read_cost_example.py
M	market_research/tests/test_conversion_boundaries.py
M	market_research/tests/test_observation_api.py
M	market_research/tests/test_publication.py
M	market_research/tests/test_publication_closeout.py
D	market_research/tests/test_publication_descriptor_platform.py
M	ui_http/products/research_publication/http-contract.md
M	ui_http/tests/test_publication_http.py
M	ui_http/tests/test_publication_http_platform.py
M	ui_web/scripts/research_browser_smoke.mjs
A	market_research/src/market_research/publication/_records.py
A	market_research/src/market_research/publication/_paths.py
A	market_research/src/market_research/publication/_sqlite.py
```

## Storage WP6 execution evidence

Baseline `2d769cc042ce270ac6bb0d104022250fc1686a2c`, branch
`feat/sqlite-portable-runtime`, native Windows checkout, 2026-11-13. Branch, HEAD and
clean working tree were verified before execution. `origin/develop` (`4c9fea7`) is an
ancestor of the branch, so a later `develop` merge is a fast-forward without conflicts.
No merge, no production-data operation and no real-market/Tushare/Publication-user
evidence was performed. The final WP6 commit is the commit containing this section
(parent `2d769cc`); its SHA is reported with the WP6 delivery.

### Narrow reconciliation

These are the only runtime changes authorized by WP6. W1/W2/Publication business,
financial, scientific, HTTP and generated-contract semantics are unchanged.

| Finding | Evidence | Fix |
| --- | --- | --- |
| W1 application read path depended on private SQL | `futures_basis/online.py::get_report` opened `_store._connection()` and executed `SELECT owner FROM runs` | Store-owned `authorize(run_id, owner)` performs only the owner existence check without loading metadata or report bytes; `get_report` authorizes before acquiring `_READ_PERMIT`; no SQL remains in `online.py` |
| W1 completion transition did not verify exactly one row | `online_sqlite_store.py::publish` ignored the conditional `UPDATE` rowcount; a zero-row update could commit an orphan result | `RUNNING → COMPLETED` now requires `.rowcount == 1`; otherwise `corrupt` and rollback (no result row, no completed state) |
| W1 recovery misclassified a malformed stored run identity | `recover()` surfaced `run_not_found`; W2 maps the same corruption to `corrupt` and ONLINE_STORAGE requires corrupt structures to fail as corrupt | Stored-ID validation in recovery now raises `corrupt` |
| Windows alternate-stream path bypassed the documented path gate | Probe: `...\source:stream` passed `path_value` and wrote an invisible NTFS stream (`a:b` created file `a`) | Windows-only rejection of `:` in non-drive path components in `publication/_paths.py`; Windows test added |
| Regression coverage | New W1 tests: foreign identity under reader contention, no private SQL in the application module, completion zero-row rollback, malformed stored identity; new Publication reserved/stream-name test | Focused and full suites pass |

No W2 or Publication behavior changed beyond the Windows path-name rejection. No
schema, version, lifecycle, financial, statistical or HTTP contract changed.

### Platform verification matrix

| Platform | OS / version | Python | SQLite | Dependency environment | Filesystem | Backend process model | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Native Windows | Windows 11 (10.0.22000) | 3.13.7 | 3.50.4 | repository root Poetry `.venv`, Poetry 2.3.2 | NTFS (`E:`) | one backend process, in-process worker, process-wide admission/reader guards; real subprocess interruption tests | **PASS** |
| WSL2 Ubuntu | Ubuntu 22.04.5 LTS, kernel 6.18.58.1-microsoft-standard-WSL2 | 3.13.15 | 3.53.1 | isolated `/tmp/wp6-linux` working-tree copy, in-project `.venv`, Poetry 2.4.3 | ext4 (`/tmp`) | same single-process code; real subprocess interruption tests | **PASS** (storage/Python; browser NOT RUN) |
| Linux Docker | Debian GNU/Linux 13 (trixie) container, Docker Desktop Linux engine | 3.13.18 | 3.46.1 | `public.ecr.aws/docker/library/python:3.13-slim`, Poetry 2.3.2 in image | overlayfs | same single-process code; real subprocess interruption tests | **PASS** |
| Linux outside WSL | not available on this host | — | — | — | — | — | **NOT RUN** |

Execution evidence:

- **Native Windows** — `poetry run pytest market_research/tests -q --tb=short`
  (1286 passed, 3 skipped), `market_backtesting/tests` (590 passed, 2 skipped),
  `ui_http/tests` (586 passed, 2 skipped), and
  `config/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py`
  (49 passed). TLS fixture executed separately with the existing Git-for-Windows
  OpenSSL CLI: `$env:PATH="C:\Program Files\Git\usr\bin;"+$env:PATH`,
  `$env:OPENSSL_CONF="C:\Program Files\Git\usr\ssl\openssl.cnf"` and an isolated
  `LAB_AUTH_DB_PATH`, `poetry run pytest ui_http/tests/test_auth_tls.py` → 1 passed,
  three consecutive runs. The host `OPENSSL_CONF` points at a missing PostgreSQL
  config; this is an environment prerequisite, not a repository change.
- **WSL2 Ubuntu** — tracked working-tree content copied to `/tmp/wp6-linux` on ext4
  (the WSL copy also carries `.git` metadata for the segmentation fixture test);
  `POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --sync` used the unchanged lock.
  Focused W1/W2/Publication storage suites: 204 passed, 4 skipped (the four Windows-only
  path/junction tests). Full Research: 1283 passed, 2 failed, 4 skipped; the two failures
  are the historical Demo fixture regeneration/View differences. Full Backtesting:
  591 passed plus one Node-prerequisite failure; rerun with that single test
  explicitly deselected: 591 passed, 1 deselected. Full HTTP: 588 passed, including the
  real TLS fixture with the distribution OpenSSL.
- **Linux Docker** — Docker Desktop Linux engine was started from the existing
  installation. Docker Hub is unreachable from this host; the image was pulled from the
  public ECR mirror `public.ecr.aws/docker/library/python:3.13-slim`. The image was
  built from a temporary staging copy outside the repository and ran
  the same focused storage suites (204 passed, 4 skipped) plus both Publication
  example scripts inside the container.
- **Linux outside WSL** — no non-WSL Linux host or authorized remote is available.
  Minimal completion steps: provision a native Linux host with Python 3.13, Poetry and
  network access; clone the branch; run `poetry install --sync`; execute the same
  focused suites and platform probe; record OS, Python, SQLite, filesystem and process
  model. This is **not** inferred from WSL2 or Docker evidence.

### Functional acceptance

- **W1 Futures Basis online runs — PASS.** Preflight without storage initialization,
  submit plus single-active-run admission, PENDING → RUNNING → COMPLETED, scientific
  `complete`/`partial` and legal empty findings, classified failure, full report
  retrieval with exact canonical bytes, owner isolation, reader permit/`read_busy`,
  restart recovery, actual active-run exclusion, failed terminal persistence,
  corrupt/incompatible/missing database, unsafe root/sidecar and hard-link handling,
  and the new foreign-identity-under-contention regression were exercised. No POSIX-only
  storage capability is required: the POSIX capability module and descriptor helpers are
  absent and the same code executed on Windows, WSL2 and Docker. The historical
  intermittent `run_busy` issue remained closed: 10 consecutive runs of
  `test_futures_basis_online.py` were green (29 passed, 1 skipped each).
- **W2 Futures Roll Long online runs — PASS.** Preflight independence, submit and
  one-active-run guard, successful execution and exact result retrieval, classified
  failures, atomic result plus COMPLETED, abandoned PENDING/RUNNING recovery, preserved
  committed results, owner isolation, full-result reader permit, bounded payload and
  digest checks, corruption/version failures and repeated application construction
  were exercised. Accepted financial fixtures are compared exactly: M1 total PnL
  22,000 CNY and Q1 19,000 CNY with their roll transitions, benchmark/excess,
  performance summary, evidence and V2 Views; no strategy, accounting or numerical
  value changed.
- **Research Publication — PASS.** A complete synthetic workflow (accepted completed
  BatchResult → explicit retained Source Evidence → immutable publish → reopen →
  list → Manifest → selected Analysis → selected Chart View → external source deletion
  → readable publication) ran on all three executed platforms. Tests cover repeated ID
  collision, atomic rollback and real process interruption, corrupt schema/payload,
  unsupported version, missing/mismatched source, digest/association mismatch,
  verification capacity, same-publication references, signed-zero/exact canonical JSON,
  read-only empty store, legacy artifacts ignored without deletion, unsafe
  paths/aliases/sidecars, and the Windows stream-name rejection. Manifest/list reads
  loaded no Source/Analysis/Layer BLOBs and selected detailed reads loaded no unrelated
  records; the read-cost example confirms it. Publication retains immutable evidence
  semantics and has no legacy compatibility backend.

### Regression outcome

| Check | Result |
| --- | --- |
| Native Windows Ruff (configured scopes) | PASS |
| Native Windows Mypy (research+HTTP 175, Backtesting 52, config 3; also `--platform linux`) | PASS; bare `poetry run mypy` still hits the pre-existing duplicate `test_architecture` module-name limitation, so scoped invocations are used as before |
| Generated OpenAPI/TypeScript contract freshness (`npm run contract:check`) | PASS: all seven pairs current, no regeneration |
| Frontend full suite (`npm run test`) | Run 1: 445 passed, 3 timeouts in unchanged MO Option Chain/Premium Plane tests; Run 2: 448 passed. Isolated MO files: 60 passed |
| Frontend build / lint | PASS; existing large-bundle warning remains; build output is ignored |
| Browser acceptance (real Chrome → Vite → FastAPI → temporary SQLite) | PASS: W1 Futures Basis online, W2 Backtesting, Research Explorer, Visualization |
| Publication examples / read-cost / Demo fixture | PASS (`publication_example.py`, `publication_read_cost_example.py`, five Demo fixture tests) |
| WSL2 focused/full suites | PASS with two pre-existing Demo fixture failures and one Node prerequisite; see matrix |
| Docker focused suites and examples | PASS |
| Markdown authority links/anchors/reachability (`data_snapshot/tests/test_authority_topology.py`) | PASS after documentation reconciliation |

### Previously recorded exceptions

| Finding | Classification | Disposition |
| --- | --- | --- |
| MO Option Chain / Premium Plane tests timing out at 5000 ms in one full frontend run | Pre-existing unrelated intermittent test timing under full-suite load (MO/Premium files untouched by this branch; second full run and isolated files pass) | Recorded; no timeout/test change |
| WSL Demo fixture byte/View mismatch | Pre-existing unrelated cross-platform numerical determinism (R1): Linux produced `0.03393217204082061` for annualized basis where the committed Windows-generated fixture has `0.0339321720408206` (same offset 505845 recorded in WP0); Demo producer and fixture are untouched by this branch | Recorded, not repaired or hidden |
| TLS fixture previously skipped/failing | Environment prerequisite: host `OPENSSL_CONF` points at a missing PostgreSQL config. With the existing Git OpenSSL CLI and valid config it passes on Windows; it also passes on WSL2 using the distribution OpenSSL | Executed, not skipped |
| Privileged symlink tests | Windows account cannot create symlinks; W2 falls back to a junction, Publication has a separate junction test, and W1's directory-symlink test skips. WSL2 ext4 executed the symlink tests. Hard-link and sidecar tests executed on Windows | Recorded; no privilege elevation attempted |
| WSL `/tmp` Backtesting Node test | Environment prerequisite: WSL has no Node runtime. Full run shows one failure; explicit single-test deselection run is 591 passed | Recorded; no test weakening |
| `ruff check .` reports 8 findings in `ui_web/deploy/publish.py` | Pre-existing, outside the repository's configured Ruff scopes and untouched by this branch; canonical scoped Ruff passes | Recorded; no unrelated cleanup |
| Docker Hub unreachable | Environment/network prerequisite; public ECR mirror used instead | Recorded |

### Post-WP6 test hygiene

2026-11-13, follow-up to WP6. No runtime, schema, DTO or generated-contract
change.

- `ui_http/tests/test_futures_basis_process.py` no longer skips on non-POSIX:
  the test uses the SQLite runtime and now executes on Windows. It passed three
  consecutive Windows runs. With the TLS fixture enabled through the existing
  Git OpenSSL, Windows full HTTP is 588 passed; without it, 587 passed and one
  TLS skip.
- `market_backtesting/tests/test_result_v2_contract.py` and
  `real_result_acceptance.py` decode Node/Vitest subprocess output as UTF-8.
  This removes the Windows GBK reader-thread warning; the accepted Windows
  Backtesting result remains 590 passed, 2 skipped.

### Remaining known risks and unverified claims

- The complete four-platform gate is **PARTIAL**: native Linux outside WSL was not
  executed. WSL2 and Docker evidence do not substitute for it.
- WSL2 and Docker browser end-to-end acceptance is **NOT RUN** (WSL has no Node/Chromium;
  Docker acceptance is scoped to the Python storage runtime). Native Windows browser
  acceptance passed.
- Windows symlink creation was unavailable to this account; W2's junction fallback,
  Publication's separate junction test and the hard-link/sidecar checks ran, but a
  separately provisioned Windows developer-mode/admin account is required to execute the
  W1 directory-symlink branch and file-symlink variants.
- Unsupported deployment modes remain unsupported and unchanged: multiple backend
  processes sharing a root, distributed workers/locks, queues, shared network
  filesystems and production multi-worker serving. No production deployment or SLA is
  claimed.
- Portable path checks remain weaker than POSIX descriptor-race resistance; a hostile
  concurrent writer or coordinated metadata-plus-payload rewrite is outside the stated
  contract. No perfect power-loss durability or authenticity claim is made.
- Synthetic fixtures are acceptance evidence only; they do not establish real-market
  readiness, upstream-data correctness or per-user Publication data.

### WP6 verdict

- **A. Functional storage acceptance: PASS.** W1, W2 and Publication meet their own
  persistence, lifecycle, integrity, isolation and bounded-read contracts on the
  executed platforms.
- **B. Cross-platform acceptance: PARTIAL.** Native Windows PASS, WSL2 Ubuntu PASS,
  Linux Docker PASS, native Linux outside WSL NOT RUN.
- **WP6: PARTIAL.** Implementation reconciliation, functional acceptance and three of
  four runtime platforms are complete; the four-platform gate cannot be declared PASS.
- **C. Merge readiness: RECOMMENDED for pre-production `develop`.** `origin/develop` is
  an ancestor, the merge is conflict-free, no branch-introduced semantic or regression
  drift was found, and the remaining failures are pre-existing/environmental. Unverified
  claims when merging: native non-WSL Linux runtime, WSL2/Docker browser end-to-end, and
  Windows privileged symlink execution. This is not a production-readiness declaration.
  No merge was performed.

### Changed-file inventory (WP6)

Status is relative to baseline `2d769cc...`; A = added, M = modified, D = deleted.
Only the first five files change runtime behavior or tests; the rest is reconciliation
documentation.

```text
M	market_research/src/market_research/descriptive/cases/futures_basis/online.py
M	market_research/src/market_research/descriptive/cases/futures_basis/online_sqlite_store.py
M	market_research/src/market_research/publication/_paths.py
M	market_research/tests/test_futures_basis_online.py
M	market_research/tests/test_publication_closeout.py
M	market_research/STORAGE_RECONCILIATION.md
M	README.md
M	market_backtesting/cases/futures_roll_long/ROADMAP.md
M	market_backtesting/cases/futures_roll_long/RECONCILIATION.md
M	market_research/descriptive/cases/futures_basis/ROADMAP.md
M	market_research/descriptive/cases/futures_basis/WP9_ACCEPTANCE.md
M	ui_http/products/futures_basis_research/ACCEPTANCE.md
M	ui_web/src/features/futures_basis_research/ACCEPTANCE.md
```
