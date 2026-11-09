# WP8-A HTTP acceptance — 2026-11-09

This is execution evidence for the [HTTP contract](http-contract.md), not a second
semantic contract. The [Research roadmap](../../../market_research/descriptive/cases/futures_basis/ROADMAP.md)
records WP7-R and the WP8-A / WP8-B split.

## Baseline and boundary

Repository: `ougachakaaa/hg-market-state-lab`; remote name `github`.
Branch: `feat/web-ui-workspace-redesign`.
Required initial HEAD: `cec5627dd30387e1daccb3e2293fb5fbd1dff2b5`; clean worktree.
WP7-R commit: `5da7727` (independently verified and committed before WP8-A).
All Python commands used the root `.venv`, Python 3.13.15.

No real Tushare requests, production data changes, React implementation, polling,
offline reader changes, shared reader migration, branch creation, merge or push
were performed. Tests use isolated temporary Auth/Run stores, real registration,
operator approval and Cookie login with synthetic public market services.

## Public delegation and runtime

| HTTP | Operation ID | Research public application method |
| --- | --- | --- |
| POST `/research/futures-basis/runs` | `submit_futures_basis_research_run` | `submit(FuturesBasisRequest, owner_scope)` |
| GET `/research/futures-basis/runs/{run_id}` | `get_futures_basis_research_run` | `get_run(run_id, owner_scope)` |
| GET `/research/futures-basis/runs/{run_id}/report` | `get_futures_basis_research_report` | `get_report(run_id, owner_scope)`; lightweight `get_run` supplies immutable envelope identity |

The facade is imported only from
`market_research.descriptive.cases.futures_basis`. Existing Observation,
Statistics, standard profile and scientific partial/complete classifications are
unchanged. HTTP retains the entire `futures_basis_report_evidence_v1` projection.

The existing Auth Gate validates the Cookie and active identity and applies Origin
checks before product parsing or lookup. Only its server-confirmed
`request.state.auth_user.id` becomes `owner_scope`; caller owner fields are rejected.
The owner remains in server metadata and does not enter DTOs. Unknown, malformed
and foreign IDs return the same safe not-found envelope.

A locked process-wide runtime holder creates one online application, including
startup recovery, and reuses it across app compositions. Lifespan initializes it;
ASGI callers without lifespan use the same holder. Initialization is attempted
once, with failure isolated to this product until backend restart. Offline OpenAPI
construction performs no run-storage I/O. No queue, scheduler or multiple-worker
support is added. The report delivery permit includes envelope serialization and
is released on failure; status reads need neither report permit.

The storage boundary checks POSIX capabilities before filesystem mutation. Native
Windows lacks the required descriptor-relative/no-follow/ownership support and
therefore serves this product as unavailable while other products can start.
Linux runtime and simulated capability failures were tested; a native Windows or
WSL execution was not performed. WSL requires equivalent filesystem capabilities.

## Error and OpenAPI reconciliation

| Operation | Status / kind |
| --- | --- |
| POST | 202 accepted; 400 `invalid_request`, `request_too_large`; 409 `run_busy`; 503 `unavailable`; 500 `internal_error` |
| GET run | 200 status; 400 `invalid_request` (forbidden query); 404 `run_not_found`; 409 `corrupt`, `unsupported_version`; 503 `unavailable`; 500 `internal_error` |
| GET report | 200 complete/partial report; 400 `invalid_request` (forbidden query); 404 `run_not_found`; 409 `result_not_ready`, `result_unavailable`, `corrupt`, `unsupported_version`; 413 `response_too_large`; 503 `unavailable`, `read_busy`; 500 `internal_error` |
| Auth | Existing separate 401 `authentication_required`, POST Origin 403 `origin_forbidden`, and Auth 500 `internal_error` envelopes/behavior retained |

The contract already prohibited GET query parameters; its matrix omitted their
rejection status. The authority now explicitly records 400 `invalid_request`,
matching runtime and OpenAPI. No research parameter or additional endpoint is added.

The formal OpenAPI has the three operation IDs, request/accepted/run/failure/report/
error DTOs, Cookie security and concrete response statuses, including Auth alternatives.
Every declared response carries `Cache-Control: no-store`; there is no 422.
Runtime responses are validated through the same DTOs. Report `data` remains a
versioned producer payload rather than a competing financial schema. All five
existing frontend-consumed OpenAPI/TypeScript artifacts pass freshness checks
without regeneration or drift. R01-A generated frontend artifacts await WP8-B.

## Acceptance evidence

All named tests below are in `ui_http/tests/test_futures_basis_http.py` unless stated.

| Required acceptance | Test evidence | Result |
| --- | --- | --- |
| 1. Anonymous rejected | `test_anonymous_and_origin_gate_precede_product` | PASS |
| 2. Valid user creates persisted Run | `test_completed_payload_dto_and_repeated_lightweight_status` | PASS |
| 3. Invalid request creates no Run | `test_invalid_request_creates_no_run`, `test_strict_raw_body`, `test_request_stream_bound_and_exact_limit` | PASS |
| 4. Concurrent POST Busy | `test_busy_returns_without_waiting_for_worker` | PASS |
| 5. Run status query | `test_completed_payload_dto_and_repeated_lightweight_status` | PASS |
| 6. COMPLETED returns valid full report | `test_completed_payload_dto_and_repeated_lightweight_status` | PASS |
| 7. FAILED/INTERRUPTED deny report | `test_busy_returns_without_waiting_for_worker`, `test_partial_science_and_interrupted_state` | PASS |
| 8. Partial is COMPLETED | `test_partial_science_and_interrupted_state` | PASS |
| 9. Foreign Owner denied | `test_foreign_unknown_malformed_are_indistinguishable` | PASS |
| 10. Unknown/malformed ID privacy | `test_foreign_unknown_malformed_are_indistinguishable` | PASS |
| 11. Corrupt/oversize/read_busy mapping | `test_corrupt_oversized_unknown_and_envelope_limit`, `test_http_report_contention_preserves_status_reads`, `test_report_capacity_includes_serialization_and_releases_after_error` | PASS |
| 12. OpenAPI and runtime DTOs | `test_openapi_exact_operations_and_access`, runtime DTO validation in completed-payload test | PASS |
| 13. Other HTTP products regressions | Entire `ui_http/tests` plus existing Web contract checks | PASS |

Additional tests prove one successful initialization under concurrent compositions,
failed initialization isolation, native-platform capability failure before writes,
no store initialization during offline export, safe operational errors, query
rejection and status response size bounds. Repeated status reads instrument the
full report reader, JSON decoder, Observation and Statistics paths; none are invoked
for report work. Stored oversize uses both a reduced test bound and an actual
32 MiB + 1 byte sparse file; envelope oversize is also independently checked.

## Verification results

| Command (repository root) | Actual result |
| --- | --- |
| `poetry run pytest ui_http/tests` | 476 passed |
| `poetry run pytest market_research/tests` | 1,255 passed, 1 skipped |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py ui_web/scripts/test_export_contracts.py` | 24 passed (21 topology/architecture + 3 exporter) |
| `poetry run ruff check ui_http market_research` | PASS |
| `poetry run mypy ui_http market_research` | PASS, 160 source files |
| `npm --prefix ui_web run contract:check` | PASS, all five existing consumers |
| `git diff --check` | PASS |

The Research skip is the existing native-unsupported-platform subprocess test,
which is skipped on this POSIX-capable Linux host. HTTP reports the existing
FastAPI TestClient/httpx deprecation warning; no dependency changes were made.
Full diff and changed-document relative links were reviewed before commit.

Conclusion: **WP7-R PASS; WP8-A PASS** within synthetic Linux acceptance.
WP8-B requires first-consumer generated OpenAPI/TypeScript and freshness coverage,
React interaction/polling, and the planned reader integration with offline regression.
WP9 retains real browser/WSL/Windows Chrome and bounded live integration acceptance.
Those gates are not claimed here.
