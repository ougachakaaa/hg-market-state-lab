# G1 Backend Ready contract

This specializes [Task version 1](task.json), not the generic Workbench Gate contract.
`check_backend.py` uses the root Python runtime. It is read-only: one GET to
`<base-url>/openapi.json`, no startup, process management, retry, redirects,
Research/capability invocation, provider access or cache I/O. Operational default:
`http://127.0.0.1:8011`, timeout 2 seconds (finite, > 0 and <= 30). An explicit target may use HTTP or HTTPS,
with hostname/IP and optional port only: no credentials, path prefix, query or fragment.

## Compatibility and result

PASS requires HTTP 200, JSON media type, strict JSON object, OpenAPI 3.0.x or 3.1.x,
nonempty info title/version and a paths object. The four method/path/operationId
triples must match the [published HTTP contract](../../../ui_http/products/research/http-contract.md).
Each must have a 200 application/json response schema; both POSTs require a required
application/json request schema. The detail GET must declare required path parameter
`id`. OperationIds must be unique across the document. References reachable from
these four operations must resolve locally; external or dangling references fail.
This is a narrow structural compatibility check, not a full OpenAPI validator or
proof that runtime business behavior matches a schema. Do not pin a document digest,
app title, checkout identity or unrelated product inventory as compatibility criteria.

JSON output has fixed schema version 1, Task identity/version, Gate ID, normalized
target, timeout, status/reason code/reason, and observations: HTTP status/media type,
received byte count/SHA-256, parsed OpenAPI version, observed operations and ordered
compatibility issues. Unobserved values remain null/empty. No timestamps, durations,
random IDs, raw exception text or environment secrets enter the checker result;
identical observations yield identical JSON. Run recording supplies timestamp/identity.
Response bodies are capped at 4 MiB. Network requests have finite connect/read/write/pool
timeouts; an overall deadline also bounds the caller's wait, including DNS, headers and
slow response bodies. A timed-out read worker is daemonized and may finish its read-only
request later; it cannot write evidence or perform any business operation.

| Outcome | Reason codes | Exit |
| --- | --- | --- |
| PASS | `compatible_openapi` | 0 |
| FAIL (actual attempt) | `connection_failed`, `request_timeout`, `http_status`, `content_type`, `response_too_large`, `invalid_json`, `incompatible_openapi`, `transport_error` | 1 |
| BLOCKED (request not attempted) | `invalid_target`, `invalid_timeout` | 2 |

CLI argument syntax errors also exit 2 (argparse). The bounded check cannot prove
cryptographic process/checkout identity, authentication, provider/credential/cache
readiness, actual capability discovery or long-history support. `lab doctor` success
and an open port alone never satisfy G1.

## Evidence and safe lifecycle

`record_g1.py` loads the exact approved task.json, creates a readiness-only Run via
the unchanged `run_store.py` public operations, performs the actual check, serializes
the raw result into a temporary source file, registers its bytes, and only then records
G1 with that artifact ID. It records G2/G6 as SKIPPED with Task-defined deferral reasons;
G3/G4/G5 have no outcomes. It reads back and verifies the frozen Task, Gate/evidence
link and preserved JSON after source removal, then prints the result and Run/artifact
locations. A failure or blocked check is preserved with its true non-PASS outcome and
exit code. Storage failure exits nonzero and must never be described as completed
evidence recording. This script is an explicit Task-specific demonstration, not a
generic executor or planner. Missing market inputs stay unresolved.

An Agent may separately start a stopped backend through the official root command
`poetry run lab serve backend` and recheck. Reuse a compatible user-owned process
without claiming ownership. Never kill/replace a user-owned process or silently
restart an incompatible occupied port. For isolated smoke testing, the existing
HTTP launcher supports `poetry run python ui_http/scripts/api.py --host 127.0.0.1 --port PORT`;
the current lab command has no port forwarding. Clean up only the smoke process
created by that acceptance session. No new official CLI command is introduced.
