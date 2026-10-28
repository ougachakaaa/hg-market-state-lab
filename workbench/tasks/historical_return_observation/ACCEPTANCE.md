# WB-02 acceptance and reconciliation

Date: 2026-10-28. Baseline: `develop` at
`ea1b5159df367d4ed534380916c9e9645450f3ef` (reviewed WB-01 foundation).
Root Poetry environment: Python 3.13.11. Verdict: **WB-02 complete** for approved
Task authority, G1 implementation and actual evidence preservation. This document
records actual evidence, not new Task or business semantics.

## Authority topology and changed files

```text
root ARCHITECTURE.md -> workbench/AGENTS.md / ARCHITECTURE.md
  -> tasks/README.md                         navigation only
    -> historical_return_observation/ARCHITECTURE.md
      -> task.json                          canonical approved definition, version 1
      -> DESIGN_REQUEST.md                  user request; trailing whitespace normalized
      -> BACKEND_READY.md                   narrow G1 compatibility/evidence contract
      -> README.md                          usage only
      -> ACCEPTANCE.md                      this delivery record
      -> check_backend.py                   independent read-only Task checker
      -> record_g1.py                       Task-specific Run demonstration
      -> examples/g1-pass.json, g1-fail.json  raw actual smoke outputs, not authority
  -> tests/test_historical_return_g1.py      isolated deterministic acceptance
```

Only Workbench files change. Existing `workbench/AGENTS.md`, `ARCHITECTURE.md` and
`README.md` route to the first approved Task and remove obsolete current-state claims
that none exists. WB-01 acceptance remains historical. Generic contracts and
`run_store.py` are unchanged, as are root project/dependencies, all business modules,
HTTP/CLI implementations and generated contracts. No re-export or package was added.

The user Goal explicitly supplies Task purpose and six Gates and commissions approved
Task authority. Approval is recorded from that request, never inferred from a Run or
certified by the store. Missing research inputs remain unresolved in G1-only Runs.
The Task defines dependency/deferral dispositions; the generic recorder remains unaware
of research semantics. Recording G2/G6 intentional deferral does not evaluate their checks
or imply successful prerequisites.

## Commands and acceptance

Exact independent G1 command from repository root:

```powershell
poetry run python workbench/tasks/historical_return_observation/check_backend.py --base-url http://127.0.0.1:8011 --timeout 2
```

Exact Run demonstration:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g1.py --original-request 'WB-02 acceptance: G1 backend readiness only; no market research or acquisition'
```

PASS exits 0, attempted FAIL exits 1, invalid configuration BLOCKED exits 2. All emit
machine-readable observations/reasons. Argparse syntax errors also exit 2. The checker
uses the existing root `httpx` dependency, with no new environment or dependency changes.

## Executed verification

All commands ran from repository root:

| Command | Result |
| --- | --- |
| `poetry run pytest workbench/tests -q` | 87 passed (39 existing + 48 Task-specific) |
| `poetry run pytest ui_cli/tests workbench/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py data_lake/tests/test_boundary.py market_statistics/tests/test_statistics_architecture.py -q` | 187 passed in 23.06s |
| `poetry run ruff check workbench` | Passed |
| `poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation/check_backend.py workbench/tasks/historical_return_observation/record_g1.py` | Passed, 3 source files |
| `poetry run python workbench/tests/acceptance_example.py` | Existing synthetic two-Run example passed |
| Independent G1 command above, with actual backend | PASS, exit 0 |
| Run demonstration above, with actual backend | G1 PASS, evidence verified, exit 0 |
| Same demonstration after owned backend shutdown | G1 FAIL/request_timeout, evidence verified, exit 1 |
| `poetry run python workbench/run_store.py read --run b78740bf7ccf462f92aa56993d7f7882` | Snapshot/records/evidence retrievable; hashes verified |
| `git diff --check` | Passed; complete staged diff reviewed before commit |

The isolated HTTP fixtures exercise valid API, reserved non-listening port, wrong HTML
service, non-200/redirect, malformed/duplicate-key/non-finite JSON, unsupported OpenAPI,
wrong/missing operations/IDs, duplicate IDs, response/request schemas, required path
parameter, dangling/external/nested references, oversized body, actual delayed response
and trickle timeouts, plus deterministic injected ConnectTimeout. CLI statuses and
stable serialization, environment proxy isolation, blocked configuration and failure
Runs are checked. The real composed application's OpenAPI passes the same checker.
Round-trip assertions verify exact Task snapshot, byte digest, source removal,
same-Run evidence and rejection from a different Run; deferred G2/G6 never pass and
G3/G4/G5 have no records. Checker file-I/O guards, business-operation guards, request
logs and an empty temporary cwd confirm no market/cache side effects.

The full business suites were not needed: no business contract/implementation changed.
Existing root architecture/boundary suites cover integration with this operational
addition. A draft link check detected incorrect relative navigation and the acceptance
file still being authored; both were corrected before the successful final suite.

## Actual backend smoke and preserved Runs

Default port 8011 had no listener. Started the existing official command
`poetry run lab serve backend`; final smoke server PID was 28920. Used both independent
checker and Run demonstration; server logs showed only two `GET /openapi.json` 200
requests, zero Research endpoints. Sent Ctrl+C only to that session, observed clean
application shutdown and confirmed port 8011 no longer listening. The subsequent
readiness attempt timed out within its configured bound and was recorded as FAIL;
no HTTP response is claimed. No Tushare credentials or market acquisition were required.

Approved Task: `historical_return_observation`, version `1`. Both final Runs preserve
the same exact canonical Task snapshot, SHA-256:

```text
2865ccf73e5736cb00eef383efad0732602e4e848f4b1ec5b53bef55a2b3cb19
```

| Run | Actual G1 | Preserved artifact | Raw JSON SHA-256 |
| --- | --- | --- | --- |
| `b78740bf7ccf462f92aa56993d7f7882` | PASS | `blobs/8022c0a416bf43e4bd9b36531a4a37fe` | `5ac7c2c23afad19e9540d8aae746a2d7fc1880099a18334f44b119ca460e1eb1` |
| `db0b709b4d4d4dd09de0454f720aa7f8` | FAIL/request_timeout | `blobs/d2d3b09f34fd42f7b8eca189c4996074` | `1d4b76efbe3c1eaf80ee370db7bc04094fd3c967c41bf80ef4ec84f5fac5a837` |

Both Runs live under ignored `workbench/.runs/<run_id>/`. Each has sequences 1-4:
raw artifact registration, G1 outcome citing that artifact, G2 SKIPPED, G6 SKIPPED.
Temporary source files were removed before read-back; preserved bytes remained valid.
The PASS raw JSON is 1294 bytes and FAIL raw JSON is 519 bytes. Machine-readable
copies (Git may normalize line endings) are committed as [PASS example](examples/g1-pass.json) and
[failure example](examples/g1-fail.json). These are actual check outputs, not
synthetic PASS fixtures or evidence for a fresh Run.

PASS observed HTTP 200, application/json, OpenAPI 3.1.0 and the four expected
Research operations/operationIds, with no compatibility issues. The response was
50991 bytes, SHA-256 `c5e1b03f689b24b4bd4a001b7dd9b0826cb535770c1b2108e1ca6b5f1f18255d`;
that digest describes observed bytes, not a pinned compatibility rule.

## Gate state and historical objective

| Gate | WB-02 state |
| --- | --- |
| G1 Backend Ready | Implemented and actually checked; per-Run PASS/FAIL evidence |
| G2 Authentication | SKIPPED, explicit MVP deferral; current loopback service has no auth |
| G3 Capability Discovery | Future implementation, unexecuted, no outcome |
| G4 Workflow Planning and Persistence | Future implementation, unexecuted, no outcome |
| G5 Execution | Future implementation, unexecuted, no outcome |
| G6 Visualization | SKIPPED, explicit MVP deferral; no rendered output |

The approved definition expresses the full historical goal, including 2010-2026, without
claiming it executable. HTTP limits remain 93 inclusive calendar days/window, H <= 20,
8 Jobs, 4 analyses/Job, 128 coordinates/spec, 128 request_id characters and 64 KiB body.
One 2010-2026 HTTP Plan is unsupported. Public Python has no HTTP caps/acknowledgment but
still needs legal inputs, whole-plan preflight, complete Calendar/warm-up and available
Index facts. Neither WB-01 nor G1 proves long-history live readiness. Earlier Research
acceptance records an unresolved historical default Calendar cache incompatibility;
WB-02 did not inspect, use or repair that cache.

Future G4/G5 must resolve/freeze a legal complete-window workflow and verify actual live
history under separate execution authorization. Splitting HTTP requests and merging
quantiles/counts/frequencies is not automatically one computation: population accounting,
coverage, overlap/dependence and provenance must also reconcile. No partition, merge,
statistical computation, acquisition or live Research was performed here.

## Limits and reconciliation

G1 establishes narrow published OpenAPI structural compatibility, not a full schema
validator, cryptographic process/checkout identity, runtime business correctness,
capability discovery, authentication or data readiness. Its whole-call deadline bounds
caller waiting including slow responses/DNS; a daemon worker may finish read-only I/O
later, never write evidence or execute Research. The default timeout is 2 seconds and
accepted explicit values are finite, > 0 and <= 30 seconds. False negatives can be
rechecked explicitly with a suitable bounded timeout; there is no retry.

Only actual G1 JSON can produce this demonstration's G1 PASS, and that file is preserved
before Gate recording. `read` verifies digest/ownership and the script verifies bytes
and snapshot after the original source disappears. Storage cannot certify arbitrary
caller-supplied evidence relevance or approval. Existing append-only/locking/local
storage limitations remain under the unchanged shared storage contract.

No shared-contract gap or business-authority drift was discovered. New Task semantics
were encoded before implementation; independent G1 detail stays below the Task entry.
The lab command has no port forwarding, so safe alternate-port smoke uses the existing
HTTP launcher directly, as documented; no official CLI expansion is implied.
No user-owned process was terminated or adopted. Local ignored Runs are disposable and
not present in a fresh checkout; rerun the demonstration to produce new identities.
