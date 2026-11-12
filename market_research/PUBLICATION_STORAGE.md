# Publication V1 implementation and local storage contract

## Contract status

The approved replacement is [Portable SQLite target](#portable-sqlite-target).
Sections from Source eligibility through HTTP delivery describe the currently active
V1 facade and file adapter. Their payload, association, granular-read and public API
contracts continue; their physical layout, hard-link/descriptor publication protocol,
POSIX platform gate and file-layout initialization rules apply **only to that legacy
adapter**, not the SQLite target. WP0 changes authority only, not the active adapter.

This contract specializes [Publication](PUBLICATION.md). The latter remains the owner of
publication semantics, and [Visualization](../ui_web/VISUALIZATION.md) remains the sole
owner of Layer and ChartView semantics. This document specifies the initial Python and
local-file boundary; it does not create an execution lifecycle or a generic artifact store.

## Source eligibility and retention

V1 admits one completed, public Descriptive `BatchResult` from the implemented Index
Trailing Return case per publication. Other cases, result variants, malformed carriers and
unsupported evidence values fail explicitly. The complete Batch, including the original
Plan, fixed Jobs, all outcomes and failures, prepared inputs and attempts, ObservationSets,
projections, original results, provenance, coverage and dependence context, is retained as
versioned source evidence. Its admitted encoding is explicit: only the public carrier
vocabulary used by that case and the two Statistics methods is encoded; dates, binary64,
bytes, ordered tuples, mappings and supported typed failures have documented representations.
It is not an unrestricted object dump. An unsupported exception, value, cyclic reference,
or unrepresentable non-finite value fails rather than being stringified or dropped.
Source evidence must retain failure category, stage, readable reason, attributable request,
original supported exception type, arguments, relevant typed evidence and cause chain.

`retain_source(batch, source_id, path)` is a separate explicit capture of an already
completed in-memory Batch into an exclusively created, durable JSON source file. It returns
an immutable source reference containing a nonempty caller-assigned source identity,
absolute location, SHA-256 and size. It does not execute a Job. `publish` accepts the
actual Batch and reference, revalidates the Batch and associations, encodes it again and
requires exact equality with the retained source bytes, size and digest. It also verifies
case provenance's retained input bytes against the case's published fingerprint. The source
must be a regular file, and missing, changed, malformed or unsupported evidence prevents
publication. A copy is retained in the publication. These checks bind a publication to the
retained material and detect changes; neither a digest nor capture proves that the claimed
historical execution occurred or that upstream market facts were authentic.

V1 supports the Batch's published success, partial success, failure and skip semantics.
A successful Analysis must be revalidated through the existing pure Research association
boundary, not by recomputing Statistics; direct construction of evidence carriers does not
itself establish validity. Revalidate original Plan/Batch accounting and original object
associations. An association-stage failure may retain its raw result but never obtains a
successful projection. Source identities, job identities, requests, specs, scope, provenance,
coverage, failure categories and skip/not-attempted reasons are preserved exactly.

## Identities and content

The caller supplies a nonempty publication creation context and may supply a lowercase UUID4
hex publication ID; otherwise the publisher generates one. An ID is independent of source,
Plan and Workbench identities. Any existing committed ID is a collision, even for equal
content; it is never replaced. Retry after an uncertain result must inspect the existing
publication. `analysis_id` is SHA-256 of canonical JSON encoding of the versioned tuple
`(source_id, complete structural Job identity, request_id, exact spec)`; the publisher checks
for collisions against the full tuple, not a hash alone. IDs are publication-scoped. A View
reference is an opaque ID derived from publication ID, analysis ID and the projection measure; it is valid
only as listed in the selected publication's Manifest. Layer references are similarly opaque.

Manifest V1 contains publication identity and context, exact Plan scope and Batch status,
ordered Job summaries (structural identity, status, failures and analysis references),
ordered Analysis summaries (identity, request/spec, status, source and View references),
and source identity, location, digest and size. Detailed Analysis payloads retain the exact
result, request, complete structural Job identity, source reference, outcome and failure;
the retained source provides the full evidence needed to audit its association. A successful
Quantile has one `quantile` View. A successful IntervalCount has separate `count` and
`frequency` Views. Other outcomes have none. Each stored View definition references only its
own Layer and Analysis; materialization replaces the reference with the verified Layer.

Quantile uses ordered supplied `(probability, value)` pairs and numeric units `probability`
and the exact result unit. IntervalCount emits underflow, each ordered bin, and overflow,
with round-trip binary64 boundary labels and exact published count or frequency, including
zeros. The labels express `<`, `>`, and each stored inclusion flag. Its units are `count`
and `frequency` respectively. No statistic, missing mark or density is computed.

## Local store and integrity

Canonical JSON is UTF-8, sorted object keys, compact separators, ASCII escaping and no
NaN/Infinity. SHA-256 covers exact bytes. Every payload and Manifest has an explicit V1
schema tag; unknown versions are rejected. Storage is rooted at a caller-selected local
directory and independent of Workbench and DataLake:

```text
root/
  bundles/<random-uuid>/source.json
  bundles/<random-uuid>/analyses/<analysis-id>.json
  bundles/<random-uuid>/layers/<layer-id>.json
  bundles/<random-uuid>/views/<view-id>.json
  publications/<publication-id>.json       # atomic commit record / Manifest envelope
```

The publisher writes a unique, private staging bundle, flushes and fsyncs each file, then
publishes a complete Manifest envelope using an exclusive hard link in `publications`.
The envelope contains the exact Manifest, its SHA-256, the generated bundle identity and
SHA-256 and size of each referenced payload. A reader only discovers commit records, so
uncommitted bundles and temporary files are invisible. Competing commits for the same ID
produce one winner and explicit collision failures; interrupted attempts can leave orphan
bundles or temporary files, which are never repaired or automatically deleted. The local
filesystem must support same-filesystem atomic hard links; errors propagate as classified
storage unavailability. This promises atomic visibility on supported local filesystems,
not distributed coordination, power-loss durability, authenticity or hostile-writer protection.
No automatic garbage collection is implied.

IDs used as path components are strictly validated, not caller paths. Every directory/file
is opened relative to a verified directory descriptor with no-follow behavior; regular-file
type is checked. Publication-local references must be declared in the same verified Manifest
and matched to generated paths, never interpreted as paths or accepted from another snapshot.
A payload's size and digest are verified before parsing; a Manifest envelope is checked
before any result is returned. SHA-256 detects accidental corruption, not coordinated
malicious rewriting of both content and metadata. JSON parsing rejects duplicate object keys,
non-finite values, invalid shapes and unknown versions. Reads do not repair or rewrite.

### Platform capability

The descriptor-relative requirement is part of the storage contract, not an implementation
detail. V1 requires `O_DIRECTORY`, `O_NOFOLLOW` and `dir_fd` support for `os.open`,
`os.mkdir`, `os.stat`, `os.unlink` and `os.link`. On a platform without these primitives, the
public facade must remain importable and the composed HTTP app must still start, but every
store read and every `retain_source`/`publish` call fails with `PublicationUnavailable`
before any file or directory is created. A path-based approximation, zero-valued flags or
removal of the no-follow checks is not an admissible fallback. Native Windows storage is
not implemented or validated.

## Public facade and reads

The Research-owned `market_research.publication` facade exposes `retain_source`, `publish`,
`PublicationStore`, typed source reference and classified `PublicationError` subclasses.
Store operations are `list_publications`, `get_publication_manifest`, `get_analysis` and
`get_chart_view`. `publish` returns the publication ID after the commit is visible. The
store returns detached JSON-compatible values; it never reconstructs arbitrary Python objects.
Listing uses ascending publication ID with an explicit bounded limit and exclusive `after`
cursor, and verifies each returned Manifest. Manifest reads do not read Analysis or Layer
payloads. Analysis reads validate its same-publication summary, exact Job/request/spec,
source association and payload digest without loading other Analyses. View reads validate
its Manifest association, View and required Layer digest and contract and materialize a
complete inline-data ChartView; unrelated Layers are not loaded. A missing Analysis is
separate from a recorded unsuccessful outcome. Stored source bytes are integrity checked
when required for detailed association; absence or corruption never triggers reconstruction.
V1 reads the retained source file as a whole for these checks, so detailed reads do not load
unrelated stored Analysis or Layer payloads but their cost grows with the source Batch size.

Detailed reads may take a caller-supplied finite source byte budget. The reader enforces it
on the actual opened source file and bounded read, before JSON parsing, and reports a distinct
verification-capacity failure; this does not replace digest or association checks. Analysis
reads include a detached Job-scoped coverage summary derived from the verified retained
ObservationSet, or null when that evidence is absent. Counts and ratios use Observation's
candidate denominator; fact counts retain overall, warm-up and sample partitions. The
summary carries only the definition unit and input profile/fingerprint alongside these
counts; Job identity, request/spec and successful sample count are already carried by the
Analysis. Fingerprints identify inputs, not their authenticity. A malformed or inconsistent
retained summary fails the read, never becomes zero coverage. No persistence schema changes.

Failures are independent of HTTP: invalid input, not found, corrupt, unsupported version,
inconsistent association, unavailable source/storage, and identity collision have distinct
public categories. No reader or publisher calls Research execution, acquisition, Statistics
computation, HTTP or Workbench. The implemented HTTP delivery consumes this public facade only.

V1 source encoding uses JSON primitives for null, booleans, strings, integers and finite
binary64 numbers; dates use `{"$date": "YYYY-MM-DD"}`, bytes use
`{"$bytes_base64": "..."}`, tuples and lists use `{"$tuple": [...]}` and
`{"$list": [...]}`, and string-keyed mappings use `{"$mapping": {...}}`. Explicitly
admitted public carriers use `{"$type": name, "fields": {...}}`; their fields are a
fixed versioned whitelist, including full nested retained evidence. Dataset public Export
scope and window are encoded structurally because their implementation classes are not
public Dataset imports. Supported typed exceptions use `{"$error": name, "args": ...,
"fields": {...}, "cause": ...}` and retain known typed evidence and causal chains. The
encoder rejects unsupported types instead of importing or constructing classes from JSON.

A View read also compares the selected stored Layer to the pure projection of its retained
source result, including signed-zero representation; it returns the stored Layer only after
that association and all selected integrity checks pass. This is a presentation mapping,
not statistical recomputation or repair.

Minimal usage, with `batch` an already completed public `BatchResult` and distinct
operator-selected paths for evidence and store:

```python
from market_research.publication import PublicationStore, publish, retain_source

source = retain_source(batch, "my-source-id", "/path/to/retained-evidence.json")
store = PublicationStore("/path/to/research-publications")
publication_id = publish(batch, source, "publication context", store)
manifest = store.get_publication_manifest(publication_id)
analysis = store.get_analysis(publication_id, manifest["analyses"][0]["analysis_id"])
# Only successful analyses have views.
view = store.get_chart_view(publication_id, manifest["analyses"][0]["views"][0]["view_id"])
```

For a self-contained example using explicitly synthetic market facts, run
`poetry run python market_research/tests/publication_example.py` from the repository root.

### Empty store and initialization

Listing and exact-identity lookup are read-only, including before the first publish. A
configured root whose existing path components are accessible, real directories and whose
remaining suffix does not yet exist is an uninitialized store: listing returns `[]` and an
exact lookup returns `PublicationNotFound`. An existing empty root, or a root containing
only a real `bundles` directory, is also uninitialized. The latter is a possible transient
or interrupted prefix of the publisher's existing `bundles`-then-`publications` setup;
its orphan bundles are never visible. Listing may observe the state immediately before a
concurrent commit and need not include it.

Once `publications` exists, both it and `bundles` must be real accessible directories.
A root with unrelated entries but no `publications`, a `publications` directory without
`bundles`, a non-directory or a symlink in the configured path or store structure is corrupt;
it is not treated as empty. Permission and other I/O failures are unavailable, not empty.
Empty path, NUL and parent traversal are invalid input. Reads create nothing. An absent
commit in a valid initialized store remains `PublicationNotFound`; malformed existing
commit records remain failures. In the publication index, only UUID4 commit filenames and
regular `.tmp-<UUID4 hex>` staging files are admitted; malformed entries and symlinks
are corrupt, while a staging file removed concurrently may be ignored. These checks do not
claim protection from hostile concurrent filesystem mutation or change the atomic commit
protocol.

### Workbench source handoff

The current G5 result artifact is a Workbench-owned delivery projection, not the original
in-memory Research `BatchResult`. It preserves many public facts and explicit associations,
but deliberately omits exception objects/chains, arbitrary malformed inputs and unknown
values, failure and skip free text, and UnitFailure reasons. RunStore can verify retained
artifact bytes and G5 linkage, but these omissions prevent treating its JSON as the complete
Research V1 source or automatically rebuilding the original typed carriers. Neither artifact
hashes nor an apparently successful report prove historical execution or upstream fact
truth. `retain_source` requires the actual completed public BatchResult and captures the
admitted complete typed evidence; `publish` re-encodes that same evidence and verifies it
against the external retained file before committing. After commit, readers verify the copied
source inside the publication and remain usable if the original external source is removed.

Before WP5 can publish a previously completed Run, it must establish a separately authorized,
versioned ingestion contract that identifies a retained source containing every required
Research V1 carrier, typed failure and association, verifies that source's identity/digest
and its binding to the exact Run and completed execution, and defines explicit failures
when evidence is missing or lossy. A G5 projection alone must be rejected; it cannot be
upgraded by inventing omitted evidence, reconstructing typed results or automatically
re-executing. This requirement does not alter Task v1 or grant authorization to execute.

### HTTP delivery boundary

The Research Manifest and Analysis are internal semantic read models, not approved
browser-facing DTOs. They can contain absolute source locations, filesystem details,
retained source material, original exception messages and provider diagnostics. HTTP owns
an explicit allowlisted safe projection and error mapping; it must not automatically
serialize the Research Manifest, raw source, credentials, private provider diagnostics,
arbitrary exception text or internal filesystem paths. This rule introduces no transport
fields into Research and does not itself define routes or HTTP DTOs.

## Portable SQLite target

Approved in storage WP0 (2026-11-12), unimplemented until storage WP4/WP5. This section
owns Publication's target persistence only; [Publication](PUBLICATION.md) remains the
business authority. [Storage reconciliation](STORAGE_RECONCILIATION.md) owns drift and
work-package readiness, independently of historical Publication/Workbench WP numbering.

### Independent database and breaking cutover

Use standard-library `sqlite3` with no ORM, new database dependency or generic artifact
framework. Preserve `LAB_RESEARCH_PUBLICATION_ROOT` as a directory root, supplied through
root `lab_config` with process environment before root `.env`; Publication still requires
explicit configuration where it does today. A caller-selected root remains supported by
`PublicationStore`. The owned database is `<root>/publications.sqlite3`, independent of
W1/W2 Run Stores, DataLake, Auth and Workbench.

The user explicitly authorizes a development-time breaking cutover: all legacy Publication
data may be abandoned; remove the retired file adapter and POSIX gate in WP4/WP5, without
migration, compatibility, dual reads/writes or an importer. No old publication is visible
in the new store. A missing database is uninitialized even when legacy bundles/publications
remain in that controlled root; legacy contents are never followed or consulted. The new
database may be created in the same root. There is no automatic data deletion, and WP0
performs no filesystem cutover. This exception replaces historical-evidence preservation
requirements for the old backend only; new SQLite publications remain immutable evidence,
not disposable online Run state. No extra abstraction survives merely for legacy support.

Listing and exact lookup remain read-only, create no directory/database, and return `[]`
or `PublicationNotFound` for an uninitialized safe root. Writes initialize only an absent
database: schema creation and `PRAGMA user_version=1` commit together. An existing file,
including a zero-byte/version-0 database, must not be overwritten or silently initialized.
Unknown versions are `UnsupportedPublicationVersion`; incompatible/corrupt structures are
`PublicationCorrupt`; I/O/permissions/lock/capacity failures are `PublicationUnavailable`.
Never automatically repair, upgrade, recreate or discard a database.

### Atomic immutable records and integrity

Store Manifest, retained Source Evidence, Analysis, Layer and View as independently
addressable logical records, with exact existing canonical JSON bytes, original SHA-256
and byte sizes. Schema storage version and existing payload V1 tags are distinct. Keep
publication identity/context, ordered summaries, source identity, Job/request/spec tuple,
analysis/view/layer identity derivation and original failure/coverage semantics unchanged.
Validate admitted source carriers and pure Research result associations without executing
Research, acquiring facts or computing Statistics.

Build and validate the snapshot before a short write transaction. Commit all records and
the discoverable Manifest atomically; an interrupted/failed transaction exposes nothing.
Enforce exclusive publication identity: an existing ID is a collision even for identical
content, never overwrite/update; keep full-tuple collision checks for hashed identities.
A retry after uncertain commit must inspect the ID. SQLite transactions provide local
publication visibility, not worker coordination or a new multi-process deployment model.

Preserve the public `market_research.publication` facade, `retain_source`, `publish`,
`PublicationStore`, source reference, typed errors and all store operations/signatures.
`retain_source(batch, source_id, path)` remains an explicit, exclusive external canonical
JSON evidence delivery to the caller-selected path. Its portable file checks protect that
specific destination; reject traversal and unsafe aliases, and preserve no-overwrite and
complete-write behavior. `publish` re-encodes the actual Batch, validates associations and
matches exact retained bytes, size and digest before copying source into SQLite. Access
only that explicitly supplied source path; a stored reference/location is metadata, never
permission to open arbitrary external files. Post-commit reads use SQLite's retained copy
and remain usable after the original source file is removed.

Listing remains ascending ID with existing bounded limit/exclusive cursor and validates
only selected Manifests. Manifest reads do not load Analysis/Layer/Source BLOBs. Analysis
reads load only the selected Analysis and required Source; View reads load only the
selected View, Layer and required Source, preserving projection equality including signed
zero. Source may still be validated as a whole; do not promise constant-cost detailed
reads or remove source verification capacity limits. Check actual BLOB length and enforce
the caller's finite source byte budget before loading/parsing it. Preserve distinct
verification-capacity failures, strict JSON/unknown-tag rejection, same-publication
association and digest-before-parse checks. Missing, corrupt and inconsistent evidence
must fail explicitly, not trigger repair, recomputation or empty placeholders.

### Portable filesystem, trust and delivery boundaries

Support native Windows, Linux, WSL2 and Linux Docker on local filesystems without requiring
POSIX `dir_fd`, `O_DIRECTORY`, `O_NOFOLLOW`, hard links or UID checks. Use explicit controlled
absolute roots, real directory ancestors and regular database/source files; reject traversal,
symlinks/junctions/reparse-point aliases, unexpected database hard-link aliases and unsafe
sidecars. Check existing components before creating/opening and recheck object identity;
if checks cannot be enforced, fail closed. Keep database/journal/WAL/SHM inside the root;
never accept path components or SQLite URI options from publication IDs or stored refs.
Explicit source capture/read may access only its caller-selected destination/reference.

The operator controls the OS account, root and ancestors through permissions/ACLs. This
portable policy does not reproduce POSIX descriptor race resistance, defeat malicious
concurrent filesystem replacement, authenticate upstream facts, protect against coordinated
rewriting of metadata plus payload, or promise perfect power-loss durability. Shared
network filesystems and multi-process workers are not newly supported. Disk capacity and
retention remain operator responsibilities; errors are explicit, with no silent repair.

Keep HTTP routes, DTOs, error mapping, allowlisted safe projections, budgets and Research
Explorer behavior unchanged. Never leak source material, owner/credentials, SQL or paths
through HTTP. Storage failure remains isolated to this product; import/backend startup
must not require POSIX primitives. WP0 claims no native Windows runtime acceptance.
