# Research Publication read-only HTTP contract V1

## Storage transition status

The active [portable SQLite storage](../../../market_research/PUBLICATION_STORAGE.md#portable-sqlite-target)
replaces the retired POSIX adapter. Endpoints, DTOs, Auth, safe projection and error
mapping remain unchanged. Actual platform evidence is recorded in Research storage reconciliation.

This contract specializes [HTTP ownership](../../ARCHITECTURE.md) and the
[product catalog](../../HTTP_PRODUCTS.md). Research owns publication identities and
read semantics; [Visualization](../../../ui_web/VISUALIZATION.md) owns ChartView V1.
All operations require the repository [access gate](../../AUTHENTICATION.md).

## Operations and request bounds

| GET path | operationId | Result |
| --- | --- | --- |
| `/research/publications` | `list_research_publications` | ordered navigation summaries and opaque next cursor |
| `/research/publications/{publication_id}` | `get_research_publication` | safe Manifest |
| `/research/publications/{publication_id}/analyses/{analysis_id}` | `get_research_publication_analysis` | one safe Analysis |
| `/research/publications/{publication_id}/views/{view_id}` | `get_research_publication_view` | complete inline ChartView V1 |

List accepts only one each of `limit` (decimal integer, 1–100, default 50) and
`after` (opaque cursor); other operations accept no query parameters. Order is the
Research reader's ascending publication ID order, with an exclusive cursor. An empty
configured store returns an empty list. Responses use `data` as envelope; list also
uses nullable `next_cursor`. A cursor is an opaque transport encoding of the exclusive
Research reader cursor; clients must not interpret it. There is no promise that a
non-null cursor has a subsequent result.

`LAB_RESEARCH_PUBLICATION_ROOT` is an absolute server-owned path without parent traversal; it may come from the process environment or, for local development, the repository-root `.env` (process environment wins). Missing or invalid configuration and unavailable storage
are isolated to these operations and return 503;
they do not prevent startup or other products. Reads do not create paths. A publication must
be accessible in this runtime's configured store; no synchronization is implied. Tests may
inject a store in the app composition. Blocking reads run in worker threads.

Successful serialized JSON responses are limited to 2 MiB on all four routes; excess
returns 413 without truncation. Detailed reads independently admit at most 4 MiB of actual
source bytes and one concurrent verification per HTTP process; capacity exhaustion returns
503 `verification_budget_exceeded`. This conservative V1 default allows sources beyond
the old response limit while limiting JSON expansion: WP2 observed about 6.48 MB traced
peak for an 854 KB source, with no process RSS or throughput guarantee. The reader bounds
the actual source read before parsing, then retains all integrity and association checks.
Other processes have independent capacity; deployment must size worker count accordingly.
Reader pagination selects ascending identities through SQLite and limits the number of returned
Manifests, not their individual size; a detailed reader verifies its Manifest and then fully verifies the retained source.
These bounds do not cap the memory
or time of the initial Manifest/index read, database I/O, or JSON object expansion. No
cache, timeout, background job or silent partial delivery is implied. This is appropriate
only for a trusted, operationally sized store; capacity must be controlled by the operator.

## Safe projection

The adapter's pure `project_analysis(raw, publication_id)` projects an already verified
public Reader Analysis into the existing `AnalysisResponse` DTO. HTTP uses the same
function after its bounded read. Explicit private offline exports may call it after
the Python Reader verifies retained evidence; they are not HTTP reads or capacity
acceptance and do not change HTTP source/response limits. No business result is computed.

The Manifest exposes schema version, identity, status, declared scope, Jobs, Analysis
identities, exact request/spec, View IDs and measures, and source digest and size. Free-form
publication context, source ID, raw failures, skip reasons, source location, Layer IDs,
source evidence and arbitrary diagnostics are not delivered because these fields may hold
paths or secrets. Their redaction is explicit; no raw exception messages are returned.
Structural Job identity and admitted V1 specs are projected to concrete typed fields.
Subject and request IDs must be 1–128 ASCII letters, digits, `_`, `.` or `-` for
HTTP delivery; a Publication outside this narrower transport boundary returns 413
without changing its Research identity. Identifiers are published verbatim and must
not be used by publishers to carry credentials or private free-form evidence.
Analysis reports status, the same identity and request/spec, and the original typed result
when successful. Failed or not-attempted outcomes have null result and a status-specific
safe reason; they remain HTTP 200. Original failed raw result is not asserted successful.
Quantile and IntervalCount successful numerical facts are transferred unchanged. View data
is the complete Research reader materialization in canonical Visualization V1 shape, with
no LayerDataRef or Plotly transformation.

Analysis includes nullable `coverage`, a Research-owned Job summary shared by its analyses.
It contains candidate/eligible/unavailable/excluded counts and candidate-denominator ratios,
overall/warm-up/sample market fact counts and ratios, observation unit and input profile and
fingerprint. Null denotes absent ObservationSet or inapplicable denominator, never complete
coverage. Other linkage is supplied by the Analysis identity, spec, result and Manifest.

## Closed error projection

Errors use `{"error":{"kind":"...","detail":"...","param":null}}`; detail
is fixed safe text. Authentication failures retain their independent Auth envelope.

| Status | kind | Meaning |
| --- | --- | --- |
| 400 | invalid_request | invalid ID, cursor or strict query |
| 404 | not_found | publication, Analysis or View absent |
| 409 | corrupt | malformed or corrupt stored artifact |
| 409 | inconsistent | stored source/result association mismatch |
| 409 | unsupported_version | unsupported stored schema |
| 413 | response_too_large | serialized response exceeds delivery bound, or an identifier is not deliverable under V1 |
| 503 | verification_budget_exceeded | source verification bytes or concurrent capacity exceeds the per-process budget |
| 503 | unavailable | missing/invalid configuration, unavailable storage/source |
| 500 | internal_error | unexpected transport/runtime failure |

No exception text, storage location or source bytes enter errors. Reader calls never execute
Research, Statistics, acquisition or Workbench and never write the Publication Store.
OpenAPI publishes the four concrete operations, DTOs, Cookie security and these outcomes;
Research Explorer owns its projected OpenAPI and generated consumer contract.
