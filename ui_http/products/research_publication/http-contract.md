# Research Publication read-only HTTP contract V1

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

`LAB_RESEARCH_PUBLICATION_ROOT` is an absolute server-owned path without parent traversal.
Missing or invalid configuration is isolated to these operations and returns 503; it does
not prevent startup or other products. Reads do not create paths. A publication must be
accessible in this runtime's configured store; no synchronization is implied. Tests may
inject a store in the app composition. Blocking reads run in worker threads.

The detailed operations first inspect the selected Manifest's declared source size and
reject sources over 2 MiB with 413. Successful JSON responses are limited to 2 MiB; excess
returns 413 without truncation. Reader pagination limits the number of returned Manifests,
not their size or index scan. WP2 reads each Manifest in full and scans/sorts the entire
index; source preflight itself requires a Manifest read, and the selected detailed reader
then rereads it and fully verifies the retained source. These bounds do not cap the memory
or time of the initial Manifest/index read, filesystem I/O, or JSON object expansion. No
cache, timeout, background job or silent partial delivery is implied. This is appropriate
only for a trusted, operationally sized store; capacity must be controlled by the operator.

## Safe projection

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
| 413 | response_too_large | source or serialized response exceeds delivery bound, or an identifier is not deliverable under V1 |
| 503 | unavailable | missing/invalid configuration or unavailable storage/source |
| 500 | internal_error | unexpected transport/runtime failure |

No exception text, storage location or source bytes enter errors. Reader calls never execute
Research, Statistics, acquisition or Workbench and never write the Publication Store.
OpenAPI publishes the four concrete operations, DTOs, Cookie security and these outcomes;
there is no Research Explorer frontend consumer or generated client in WP3.
