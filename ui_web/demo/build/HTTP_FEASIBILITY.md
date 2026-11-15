# DDB-01 HTTP feasibility

Read through [build authority](ARCHITECTURE.md). Investigation baseline is
`225e7610c318cf7ac8f0fdeaacd747e69292bd56`, branch `feat/demo-bundle-workflow`,
2026-11-14, initially clean worktree. This is source inspection evidence.

## Evidence and status

The [HTTP catalog](../../../ui_http/HTTP_PRODUCTS.md) routes to the six formal product
contracts. Each product's implementation is in
`ui_http/src/ui_http/products/<product>/endpoint.py` and `schemas.py`. The frontend files
below are relative to `ui_web/src/features/`. Their committed OpenAPI paths and schema
names were inspected alongside route response models and pure validators. This task has
not exported OpenAPI, started serving processes, accessed stores/market data or executed
an end-to-end request. Generated-artifact freshness is NOT VERIFIED.

SUPPORTED below means the inspected formal contract and implementation expose the needed
capture boundary. Runtime acquisition is independently NOT VERIFIED for every row.
No missing formal HTTP operation was identified. Missing configuration, unavailable source
data, access failure, oversized responses or unavailable publications can still prevent a
specific capture. A discovered missing operation would be BLOCKED and require explicit
reconciliation before its downstream collection work.

All rows require the existing approved active-user Cookie login. POST operations require
the existing same-origin check. Collector must use the Auth contract's login and renewal
behavior, documented in [Authentication authority](../../../ui_http/AUTHENTICATION.md).

| Bundle | Formal acquisition | Full DTO / static adapter | Reusable validator | Static / runtime |
| --- | --- | --- | --- | --- |
| `chain` | GET `/mo-option-chain` | `OptionChainDTO`, entire body | `mo_option_chain/api/validateOptionChain.ts` | SUPPORTED / NOT VERIFIED |
| `premium` | GET `/mo-option-premium-plane` | `PremiumPlaneResponse`, entire body | `mo_option_premium/api/validatePremiumPlane.ts` | SUPPORTED / NOT VERIFIED |
| `basis` | POST `/research/futures-basis/runs`, GET `/{run_id}`, GET `/{run_id}/report` under that runs path | `FuturesBasisReportResponse`, extract request/data into request/report | `futures_basis_research/api/validateResult.ts`, `validateEmbeddedReport` | SUPPORTED / NOT VERIFIED |
| `catalog` | GET `/research/capabilities`, GET `/research/capabilities/{id}` | array of `CapabilityDescription` and each full descriptor into list/details | `research_catalog/api/validateCatalog.ts`, `validateEmbeddedCatalog` | SUPPORTED / NOT VERIFIED |
| `publications` | GET `/research/publications`, GET `/{publication_id}`, GET `/{publication_id}/analyses/{analysis_id}`, GET `/{publication_id}/views/{view_id}` under that publications path | `PublicationList`, `ManifestResponse.data`, `AnalysisResponse.data`, `ViewResponse.data` | `research_explorer/api/validateEmbeddedPublication.ts`, `validateEmbeddedPublicationSet` | SUPPORTED / NOT VERIFIED |
| `expiry_to_M1_v1` | POST `/backtesting/futures-roll/runs`, GET `/{run_id}`, GET `/{run_id}/result` under that runs path | `FuturesRollResultResponse`, extract request/data into request/result | `backtesting/api/validateResult.ts`, `validateEmbeddedBacktestResult` | SUPPORTED / NOT VERIFIED |
| `expiry_to_Q1_v1` | Same routes with independent Q1 submit | Same DTO, independently acquired result | Same feature validator | SUPPORTED / NOT VERIFIED |

## MO products

[Chain HTTP contract](../../../ui_http/products/mo_option_chain/http-contract.md) requires
`target_trade_date` and `option_product=MO`, with optional `price_type` defaulting to close.
[Premium HTTP contract](../../../ui_http/products/mo_option_premium/http-contract.md)
requires `as_of` and `option_product=MO`, with the same price-type default. Both dates are
explicit canonical YYYY-MM-DD. Accepted price types are open/high/low/close. Both GET
operations have no body or polling. Neither supplies an availability/latest query.

Their feature API OpenAPI files are `moOptionChain.openapi.json` and
`moOptionPremium.openapi.json`, consumed directly by the corresponding pure validators.
HTTP 200 bodies can be retained complete, preserving every expiry, point, metric and
null/zero distinction. Premium validation also rejects an empty points array and returns
`{plane, rawPayload}` for Presentation. The Bundle stores only the original full body.
Both depend on serving provider bindings and source availability for the chosen date.
No prior Demo data or stored Run is required. Real source access remains NOT VERIFIED.

## Futures Basis

[Formal HTTP contract](../../../ui_http/products/futures_basis_research/http-contract.md)
publishes `FuturesBasisRunRequest` with exactly `product_code`, `start_date`, `end_date`.
Product is IM/IC/IF/IH. Backend enforces ordered dates, future-date and 1,096-day limits.
The immutable response request additionally includes case and analysis_profile selected
by the server. POST returns `FuturesBasisRunAccepted` at 202. GET Run returns
`FuturesBasisRun`; poll to COMPLETED, then GET report returns
`{run_id, request, result_status, data}`. FAILED/INTERRUPTED cannot supply an admitted result.
Optional POST `/research/futures-basis/preflight` uses the same body and stays advisory.

`futuresBasis.openapi.json` publishes these operations. Report data uses the existing
producer reader profile `futures_basis_report_evidence_v1`; its nested schema is represented
generically in OpenAPI. Generated-envelope shape alone cannot validate the reader report.
`validateEmbeddedReport({request, report: data})` calls immutable-request validation and
`validateReaderReport`, which delegates to `report/validate.ts` for profile, definition,
status and Visualization checks and verifies request/observation association. Capture also
checks result_status/data.status before dropping the transport envelope. Partial scientific
status remains a valid formal result and is preserved truthfully.

Execution needs usable source dependencies, configured writable Run storage and the same
authenticated owner throughout collection. A previous Run is unnecessary. Report delivery
has a 32 MiB response bound and one reader permit per process. Actual data/readiness,
execution and report delivery remain NOT VERIFIED.

## Backtesting

[Formal HTTP contract](../../../ui_http/products/backtesting/http-contract.md) publishes
`FuturesRollRunRequest` with exactly `product_code`, `start_date`, `end_date`,
`strategy_profile`. Product is IM/IC/IF/IH. The two Bundles submit separate requests using
`expiry_to_M1_v1` and `expiry_to_Q1_v1`; all parameters are explicit. Backend owns date and
strategy rules. Optional POST `/backtesting/futures-roll/preflight` remains advisory.

Submit returns `FuturesRollRunAccepted` at 202. Poll `FuturesRollRun` to COMPLETED and read
`FuturesRollResultResponse` as `{run_id, request, data}`. `backtesting.openapi.json`
concretely represents the full `FuturesRollResult` and nested Views.
`validateResultResponse` checks the full response and request association before extraction.
`validateEmbeddedBacktestResult({request, result: data})` checks the complete Result,
immutable request, exact profile/case/definition/status and V2 Views. Financial values are
preserved. Source dependencies, owner-isolated writable Run storage and actual execution
remain NOT VERIFIED. Historical notes of an Online 401 do not prove this path's current
runtime state or remove its existing Auth requirement.

## Research Catalog

[Research HTTP contract](../../../ui_http/products/research/http-contract.md) supplies
the complete discovery list without request parameters and a full detail by returned ID.
GET discovery creates no DataLake service or market I/O. `catalog.openapi.json` contains
both GET operations and `CapabilityDescription`. Capture the entire array, then every
returned detail, validating each formal body. `validateEmbeddedCatalog` validates both
generated shapes, duplicate IDs and membership. It permits a missing detail, so complete
Bundle admission additionally requires exact detail coverage. Discovery has no Publication
Store or Run prerequisite and no Submit/Poll lifecycle. Authenticated serving remains
NOT VERIFIED.

## Research Publications

[Publication HTTP contract](../../../ui_http/products/research_publication/http-contract.md)
and `research.openapi.json` publish all four GET operations in the matrix. The list accepts
only `limit` (1–100, default 50) and `after`. Other routes accept no query parameters.
List returns `{data, next_cursor}`. Detailed responses return `{data}`. Scope and results
are already published in the configured server Store; HTTP reads never generate research.
`LAB_RESEARCH_PUBLICATION_ROOT` must resolve to an accessible configured store. A missing
configuration returns 503. An empty configured store returns an empty terminal list.

User-selected capture scope is the entire Store. Start with limit=50 and no after, follow
each opaque next_cursor unchanged to null. A full page may advertise a continuation whose
next page is empty. Keep that actual terminal page. Enumerate Manifest analyses and all
declared View references. Validate full responses and retain their complete data DTOs in
the embedded assembly, with View publication_id/view_id supplied from the requested
formal reference. No Publication Reader invocation is permitted in Collector.

`api/validateResearch.ts` checks generated response shapes and ChartView contracts.
`validateEmbeddedPublicationSet` adds duplicate checks, list/Manifest status agreement,
scope/job/Analysis ownership, exact Analysis summaries and outcomes, View ownership and
orphan rejection. It accepts a contiguous pagination prefix and missing embedded details
for local missing states. Build additionally requires null terminal continuation and
complete Manifest/Analysis/View coverage. It must not silently accept those missing states.

Responses are bounded to 2 MiB each; detailed verification admits 4 MiB source bytes and
one verification per HTTP process. Oversize, missing, corrupt, unsupported or unavailable
records fail capture without truncation. The complete Store's content, capture size,
consistency during pagination and authenticated read success remain NOT VERIFIED.
