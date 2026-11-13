# W2 portable SQLite online storage contract

This contract specializes [Online application](ONLINE_APPLICATION.md), which owns request,
owner, lifecycle, failure and result semantics. It owns only this case's persistence.
It does not authorize reuse of another case's store, database or execution identity.

## Delivery status and cutover

**Storage WP2 cutover:** the online application exclusively uses the case-owned SQLite
adapter. The POSIX adapter is retired. Historical platform acceptance remains in
[reconciliation](RECONCILIATION.md#storage-wp1-execution-evidence); current WP2 checks
are recorded separately. Storage WP numbering is independent of original case milestones.

Use standard-library `sqlite3`, with no database dependency, ORM, generic store framework,
queue, cross-module persistence abstraction or scheduling change. Existing public Python
operations, HTTP endpoints/DTOs, generated contracts, financial calculations and report
profiles remain unchanged. Scientific result status remains `complete` only; no partial success.

## Ownership, location and initialization

`LAB_BACKTESTING_RUN_ROOT` remains an absolute server-controlled **directory root**, without parent
traversal. Unset configuration keeps `market_backtesting/.runtime/futures_roll_long_online/`, independent of working directory.
Resolve configuration only through root `lab_config`; process environment precedes root
`.env`. The owned database is `<root>/runs.sqlite3`; it is independent of W1/W2's other
store, Publication, Auth, DataLake and Workbench. Database and sidecars stay outside Git.

Only a writing/initialization operation may create the database. Create the schema and
set `PRAGMA user_version=1` in one transaction. An existing database must have version 1
and the expected structure; version 0 is not an invitation to initialize an existing
file. Reject unknown/incompatible versions, missing or malformed structures and corrupt
SQLite explicitly using existing `corrupt`/`unavailable` application categories; ordinary
I/O, permissions and lock/capacity failures are unavailable. Do not repair, replace,
upgrade or silently recreate a database. Run creation is permitted to initialize an
absent database; unavailable initialization isolates this product, not backend startup
or read-only preflight. No operation other than run submission creates a Run. Read operations never initialize
an absent database themselves; an absent owned Run is `run_not_found`. Application startup
initialization/recovery is an explicit writing operation, not a status-read side effect.

Old per-run directories are disposable and ignored, including during recovery. A new
SQLite database may be created inside the existing configured root without reading,
copying, migrating or deleting old files. An old Run ID is not found in the new store.
No automatic cleanup, TTL, quota, deletion API or compatibility path is added.

## Logical records and validation

Maintain separate logical records for small Run metadata/state and large result BLOBs.
Metadata binds run ID, immutable owner/request, creation/start/finish UTC timestamps,
state, safe failure record, result profile/scientific status, exact byte length and
SHA-256 where applicable. Preserve existing request canonicalization, metadata limits
and request association checks. A result record is keyed by Run identity and contains
the exact existing canonical UTF-8 JSON bytes, not re-encoded SQLite JSON values.
Result profile remains `futures_roll_long_result_v1`. SQL layout and connection encapsulation are private
implementation details; parameterize all identity/owner queries and never derive SQL
or file paths from a Run ID.

Reject malformed IDs before storage access. Check immutable owner before returning state
or validating owner-private contents: malformed, absent and foreign IDs all remain
`run_not_found`. Never expose owner, paths, SQL, credentials or arbitrary exception text.
Reads use a consistent database snapshot for the selected state and result association.
Status reads validate metadata/state, and for COMPLETED check result existence and actual
BLOB length against declared length and the 32 MiB bound without selecting/parsing full
payloads, checking their digest or acquiring a result-reader permit. A full read bounds
actual bytes before allocation/parsing, checks exact size and SHA-256, strict JSON,
profile, scientific status and request/result association. Preserve existing oversized
read classifications (`corrupt` for stored oversized results);
status inconsistency remains `corrupt`. Publication above 32 MiB remains
`result_publication/result_too_large`, never truncation. Reads never recompute or repair.

## Transactions, recovery and process concurrency

The application lifecycle is unchanged: PENDING -> RUNNING/FAILED/INTERRUPTED;
RUNNING -> COMPLETED/FAILED/INTERRUPTED; COMPLETED, FAILED and INTERRUPTED are immutable.
Publish only a validated result. Insert its BLOB and length/digest, and transition
RUNNING to COMPLETED **in the same transaction**. Failed validation or commit must leave
no visible completed state or readable partial result. Other metadata/state transitions
are atomic, conditional on the expected nonterminal state. Never overwrite a terminal
row; FAILED/INTERRUPTED serve no result. Commit before reporting success; rollback on
failure. Serialization and computation do not hold long-lived database/state locks.

Startup recovery atomically marks abandoned PENDING/RUNNING rows INTERRUPTED with recovery
finish time and existing safe interruption failure. Initialization/recovery is serialized
with process admission and excludes the actual current-process active Run. Do not resume
work or infer success from orphan bytes. A crash before completion commit recovers as
interrupted; a crash after commit preserves the validated completed result. Corrupt state
fails closed, not repaired as interrupted. Unpersistable terminal state makes the
application unavailable until restart, preventing stale RUNNING responses.

Keep the existing per-product process-wide one-active-run guard and one-full-reader permit.
Busy submission creates no Run; excess full reads remain manual-retry `read_busy`; status
reads remain independent. Do not share SQLite connections across threads unsafely.
Transactions arbitrate storage atomicity only: one backend process, no multi-process
workers, distributed locks, queues or shared network filesystem support is authorized.

## Portable filesystem and trust policy

Support native Windows, Linux, WSL2 and Linux Docker on local filesystems. Ordinary
operation must not require POSIX `dir_fd`, `O_DIRECTORY`, `O_NOFOLLOW` or Unix UID tests.
Require a controlled absolute root, real directory ancestors and a regular database;
reject parent traversal, symlinks/junctions/reparse-point aliases and unexpected hard-link
aliases for the database. Validate existing components before creation/open and recheck
identity when opening; fail closed if the required checks cannot be made. Database and
SQLite journal/WAL/SHM paths must remain within the controlled root; reject unsafe
existing sidecars and never follow user-provided filenames or SQLite URI options.

The operator controls the root and OS account/ACLs, protects its ancestors against
untrusted modification and owns disk capacity. This is not a portable replica of POSIX
race-resistant descriptor access or UID enforcement. Path checks cannot defeat malicious
concurrent path replacement; SQLite and SHA-256 do not protect against a hostile writer
rewriting both metadata and payload. No authenticity, distributed coordination or perfect
power-loss durability claim is made. Permissions/storage errors fail explicitly without
leaking local details; unavailable storage does not disable unrelated products.
