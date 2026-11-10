# R01-A online research application and run lifecycle

This contract specializes the [Futures Basis case](ARCHITECTURE.md), its
[offline delivery](DELIVERY.md), [evidence](EVIDENCE.md) and
[roadmap](ROADMAP.md). It owns the case-specific online request, standard analysis
profile, run lifecycle, runtime result store and report-read boundary. HTTP
transport belongs to [ui_http](../../../../ui_http/products/futures_basis_research/http-contract.md);
browser interaction belongs to [ui_web](../../../../ui_web/src/features/futures_basis_research/ARCHITECTURE.md).
It does not redefine Basis formulas, Slot resolution, Observation, Statistics or
Visualization semantics.

## Scope and non-goals

The first online release accepts exactly one product, one inclusive date-only
window and one server-selected analysis profile per execution. It returns one
validated R01-A result and one browser-readable report projection.

The online application is not [Publication V1](../../../PUBLICATION.md). A run is
not a `PublishedResearchResult`, does not enter the Publication Store and does not
change its Trailing Return-only admission. It is also not a ResearchPlan, Job,
BatchResult, Workbench Run or generic durable execution identity. No queue,
message broker, Celery/Redis, scheduler, database migration, generic task
framework or distributed execution is introduced.

## Request and standard analysis profile

The semantic request is:

```text
case              = futures_basis_v1
product_code      = IM | IC | IF | IH
start_date        = date (inclusive)
end_date          = date (inclusive)
analysis_profile  = r01a_standard_v1
```

No subject, source, date, Horizon, method or statistical-parameter defaults exist.
The profile is an explicit application-level preset selected by this case; it is
not an implicit default inside the existing `ReportRequest` API. The profile
constructs the formal [ReportRequest](DELIVERY.md#wp5-executable-delivery)
explicitly:

```text
QuantileSpec((0.0, 0.25, 0.5, 0.75, 1.0))

IntervalCountSpec(
    (-1000, -500, -100, 0, 100, 500, 1000), "index_points")
IntervalCountSpec(
    (-1, -0.1, -0.01, 0, 0.01, 0.1, 1), "decimal_ratio")
IntervalCountSpec(
    (-10, -1, -0.1, 0, 0.1, 1, 10), "decimal_ratio")
```

The histogram order is `basis_value`, `basis_ratio`, `annualized_basis_ratio`,
matching the existing `ReportRequest` validation. These values exactly match the
accepted WP4/WP5 request in [usage](USAGE.md) and
[WP5 acceptance](WP5_ACCEPTANCE.md); no adjustment was required. The profile name
is immutable: a changed quantile, edge or unit requires a new profile version and
new run request identity. Historical runs retain the formal `ReportRequest` in
their stored reader projection, so a later code revision cannot silently
reinterpret them.

Validation before any run creation or upstream I/O:

- product must be exactly one canonical member of `IM / IC / IF / IH`;
- dates must be date-only and inclusive, with `start_date <= end_date`;
- `end_date` must not be after the current date in `Asia/Shanghai`;
- inclusive span `(end_date - start_date).days + 1` must be at most `1,096`
  calendar days, i.e. at most three calendar years including leap days;
- the accepted `2024-01-01..2026-10-30` candidate is `1,034` inclusive days and is
  supported;
- no minimum start date, source default, window split,
  multi-product expansion or client-controlled method selection exists.

Read-only [Preflight](PREFLIGHT.md) supplies Web admission guidance before explicit
submission; it does not gate the Run API or change final preparation.

The source-data and completeness rules are unchanged from [Inputs](INPUTS.md) and
[Observation](OBSERVATION.md). A legal partial Index export may produce
`underlying_fact_unavailable` outcomes; incomplete Calendar or Futures exports fail
input preparation. No Snapshot substitution, retry framework or synthetic fallback
is authorized.

## Run identity, ownership and lifecycle

A run has an opaque `run_id`: a server-generated 128-bit value rendered as 32
lowercase hexadecimal characters. It contains no product, date, owner, sequence or
filesystem information; clients must not parse it. A malformed ID is treated as
not found before any storage access.

Each run is bound to an immutable request and to an `owner_scope`, which is the
authenticated user identity supplied by `ui_http`. The scope is an application
privacy key, not a second authentication mechanism. It is stored only in
server-owned run metadata and is never returned by any HTTP or report projection.
A run is readable only when the caller's scope matches; unknown, malformed and
foreign IDs all classify as `run_not_found` so that existence is not disclosed.

Execution states are `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` and `INTERRUPTED`.
Terminal states are immutable. The scientific result status is the existing
`complete` / `partial` value from `ReportResult.status`:

| State | Result available | Scientific status | Transitions |
| --- | --- | --- | --- |
| `PENDING` | no | none | `RUNNING`, `FAILED`, `INTERRUPTED` (restart) |
| `RUNNING` | no | none | `COMPLETED`, `FAILED`, `INTERRUPTED` |
| `COMPLETED` | yes | `complete` or `partial` | terminal |
| `FAILED` | no | none | terminal |
| `INTERRUPTED` | no | none | terminal |

A `COMPLETED` run always has a validated result. `FAILED` and `INTERRUPTED` never
serve a report. Method failures make the scientific status `partial`; they do not
fail execution. `no_eligible_sample` is an empty finding, not a statistical
execution failure.

Only one execution may be active across the process. A submission while one is
active is rejected as busy before any run directory is created; there is no queue.
The HTTP request is accepted and returned immediately. A single in-process worker
performs the existing `observe_futures_basis` and `compose_report` calls; the
browser polls status. No HTTP request remains open during acquisition or
computation. No wall-clock deadline or cancellation is provided; provider
availability and long-running work are not promised.

Startup recovery marks every persisted `PENDING` or `RUNNING` run
`INTERRUPTED`, with `finished_at` set to the recovery time. A run that is not the
current process's active run is never reported as running. If the process stops
after a result file is written but before the completed state is committed, the
result is not served; recovery remains conservative and the run is interrupted.
No partial or orphaned result may appear completed.

## Execution, result validation and publication

The worker executes the accepted public path:

```text
FuturesBasisRequest(product, start, end)
    → observe_futures_basis (existing public preparation + construction)
    → ReportRequest(observation, r01a_standard_v1 specs)
    → compose_report (existing WP4 analysis)
    → existing case-owned reader projection (no recomputation)
    → validate profile, status, request, fingerprint and serialization
    → atomically publish report payload
    → atomically publish COMPLETED state
```

The result payload is the existing `futures_basis_report_evidence_v1` reader
projection defined by [Evidence](EVIDENCE.md) and produced by the same case-owned
projection logic as the offline report. It includes the formal `ReportRequest`
with its explicit quantile/histograms, fingerprint, definition version, coverage,
accounting, candidate dates, formulas, sources, summary, limitations,
distributions, comparisons, persistence and generic Views. It is not a second
financial interpretation and does not require a new HTTP-only schema.

Validation before publication checks at least: the `ReportResult` status is
`complete` or `partial`; the reader profile is exact; `reader.status` equals the
result status; `reader.request.observation` matches the run request;
`reader.fingerprint` is present and belongs to the prepared inputs; the payload is
finite canonical JSON; and the serialized payload is at most `32 MiB`. Exceeding
the size bound fails execution with the classified
`result_publication/result_too_large` failure; it never truncates.

Publication order is result bytes first, completed state last, both by atomic
replacement in the run directory. A reader sees only complete files. A storage
failure is classified and never silently repaired.

## Failure classification

Run failures expose a safe `{stage, category, dependency, reason}` record. HTTP
owns only the transport projection; it does not reclassify.

| Stage | Categories | Dependency | Meaning |
| --- | --- | --- | --- |
| `input_preparation` | `invalid_request`, `upstream_operation`, `invalid_public_input` | `request`, `calendar_cffex`, `calendar_sse`, `futures`, `index` | Existing public preparation failure, incomplete required final export or source operation failure |
| `observation_construction` | `invalid_prepared_inputs`, `slot_resolution`, `numerical_failure` | null | Existing construction or Slot failure |
| `report_composition` | `invalid_report_request`, `composition_failure` | null | Report request/composition failure |
| `result_publication` | `result_too_large`, `serialization_failure` | null | Result serialization or bounded publication failure |
| `execution` | `interrupted`, `internal_failure` | null | Process interruption or unexpected worker failure |

Reasons must be fixed safe text or sanitized with the existing case policy; no
paths, provider credentials, URLs, raw exception text or traceback may enter a run
or HTTP projection. Missing market facts that are legal under the case policy stay
observation outcomes, not execution failures. Actual statistical method failures
stay `partial`; they are retained in the report as failures.

## Runtime storage and retention

The case owns a file-based external runtime root, independent of DataLake,
Publication and Workbench storage:

```text
<run_root>/<run_id>/
    request.json   immutable request, owner scope and creation time
    state.json     atomic current status, timestamps, failure and result digest
    report.json    validated reader projection, only when COMPLETED
```

The optional server configuration `LAB_FUTURES_BASIS_RUN_ROOT` is an absolute
server-owned path without parent traversal. When unset, the default is the module
runtime directory `market_research/.runtime/futures_basis_online/` (WP7 must ensure
the runtime tree is outside Git); it is resolved without depending on the process
working directory. Invalid, unavailable
or unwritable storage makes the online product unavailable; it does not prevent
server startup or other products. The store requires POSIX descriptor-relative
file operations, no-follow directory/file opens and user ownership checks. Missing
platform capabilities (including native Windows) classify as `unavailable` before
creating the runtime tree; WSL/Linux must provide those capabilities. No Windows
filesystem emulation is provided. Server paths, owner scopes and storage
configuration are never exposed.

The store is deliberately disposable runtime state under the
[repository runtime invariant](../../../../ARCHITECTURE.md#naming-and-transition-authority).
There is no automatic cleanup, TTL, quota, migration, compatibility promise or
deletion API; operators own retention and disk capacity. Completed runs survive
browser refresh and server restart. The store does not make ObservationSets or
research results generally durable and does not change the existing
[execution](../../../descriptive/EXECUTION.md) contracts.

MVP support is a single backend process. Multiple processes or workers sharing a
root are unsupported because the in-process active-run guard and restart recovery
would conflict. No distributed lock, external queue or durable worker is
introduced.

Run status reads check run ID format, containment, no symlink, request/state schema,
owner scope and state consistency. For COMPLETED they open the result safely and
check only presence, regular-file type and size (at most 32 MiB); an invalid result
file is `corrupt`. They never read report bytes, verify a digest, parse the report
or acquire a report-reader permit. Full report reads alone perform digest and
payload association validation. Stored reports above 32 MiB classify as
`response_too_large`; publication above that bound remains the execution failure
`result_publication/result_too_large`. Neither path truncates.

Full report read-path checks cover run ID format, containment in the root, no symlink,
request/state schema, owner scope, state consistency, result presence, size and
SHA-256, reader profile, status and request association. Corrupt or unknown state
is never silently repaired and never recomputed. A report read is bounded to one
reader permit per process; excess capacity is a manual-retry `read_busy` condition,
not a queue.

## Report-read boundary and evidence scope

`GET` report returns the existing reader projection without acquiring inputs,
executing observations, invoking Statistics or recomputing anything. Research owns
the projection and its meaning; `ui_http` only validates/transports it, and
`ui_web` only renders it. The reader projection keeps the requested window and the
actual candidate/coverage evidence distinct; neither the browser nor HTTP may
relabel requested dates as observed dates.

The online MVP intentionally does not expose the full offline evidence package
(`evidence.json`, canonical input bytes, associations, HTML, manifest, verify/replay).
Those remain the WP5 offline boundary. Full online evidence/replay and any
Publication admission are deferred; the reader projection, fingerprint, coverage
and limitations are the online boundary.

## WP7 entry conditions

WP7 implements this contract inside
`market_research.descriptive.cases.futures_basis`; it must not change existing
Basis/Slot/Observation/Statistics/Visualization behavior, add a generic execution
framework, or implement HTTP/UI. Its tests use fake public services and synthetic
data, cover all state transitions and recovery, owner isolation, size bounds,
corrupt/unknown storage and partial/empty results, and retain the existing R01-A
regression suite. Full evidence/replay, Publication and deployment are not WP7
requirements.
