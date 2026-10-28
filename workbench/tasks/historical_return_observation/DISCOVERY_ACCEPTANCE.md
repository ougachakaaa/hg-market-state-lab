# WB-03 capability discovery acceptance and reconciliation

Date: 2026-10-28. Baseline: `develop`, required predecessor
`966d3919b89cb3a87732610f21ac8b2e1e560cf2`. Root Poetry runtime: Python 3.13.11.
This records actual G3 verification, not capability or business authority.
Approval for this implementation is the preserved [WB-03 Goal](DISCOVERY_REQUEST.md).

## Authority and changed files

The existing root entry routes through `workbench/AGENTS.md` and
`workbench/ARCHITECTURE.md` to `tasks/README.md`, then the Task entry and the narrow
[G3 contract](CAPABILITY_DISCOVERY.md). Workbench architecture, Task catalog and
Workbench/Task usage guides now describe the implemented G1/G3 slices. Existing
files changed: `workbench/ARCHITECTURE.md`, `workbench/README.md`,
`workbench/tasks/README.md`, and this Task's `ARCHITECTURE.md` and `README.md`.

Added files:

- `CAPABILITY_DISCOVERY.md`: Task-specific G3 prerequisites, validation, outcomes,
  limits and append/read-back contract.
- `DISCOVERY_REQUEST.md`: user approval evidence; trailing whitespace normalized.
- `check_capabilities.py`: read-only HTTP list/detail inspection using the already
  published descriptor type; no local capability inventory.
- `record_g3.py`: append artifact/outcome to an existing Run and verify with a fresh
  RunStore reader after temporary source removal.
- `DISCOVERY_ACCEPTANCE.md`: this delivery's evidence and reconciliation.
- `examples/g3-pass.json`, `examples/g3-fail.json`: complete actual smoke results,
  including raw base64 HTTP bodies, not synthetic PASS evidence for future Runs.
- `workbench/tests/test_historical_return_g3.py` and `workbench/tests/fixtures/capability.json`:
  deterministic local HTTP acceptance. The descriptor fixture was captured from
  the composed app; additional test IDs simulate catalog multiplicity only.

Only Workbench files change. `task.json` version 1, shared Task/Run/Gate/Storage
contracts, RunStore, G1 scripts, dependencies, all business/HTTP/CLI implementations
and generated contracts are unchanged. No new package, registry or official CLI.

## Invocation and actual smoke

From repository root, use an existing G1 Run:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g3.py --run aa99527d00c14846bfd22cb59504f832 --timeout 2
```

For a fresh Run, first start the existing backend if stopped and run:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g1.py --original-request 'WB-03 acceptance: backend readiness and read-only capability discovery; no research execution or acquisition'
# Substitute the returned identity in the G3 invocation above.
```

Port 8011 was unoccupied. Started the existing official `poetry run lab serve backend`,
server PID 2748, and performed G1 then G3. Its access log showed exactly:

```text
GET /openapi.json                                             200
GET /research/capabilities                                    200
GET /research/capabilities/trailing_cumulative_return_v1        200
```

Observed capability count: **1**, IDs: **`trailing_cumulative_return_v1`**.
This count is a runtime observation, never a Workbench invariant. List/detail match
in full. Name: Index Trailing Cumulative Return Research. Purpose: describe historical
index end-session trailing returns with explicit analyses. Publication reports
`supported`, `live_readiness=not_probed`, descriptive paradigm, canonical full index
subjects, explicit empty metric parameters, positive non-bool trading-session H,
inclusive date windows, `decimal_ratio`, Quantile and IntervalCount constraints,
failure/status semantics and limitations. Complete published constraints and their
original response bytes are in the [PASS result](examples/g3-pass.json).

G3 PASS exited 0, `discovery_complete=true`, `task_readiness=true`; no live-data
readiness is inferred. Sent Ctrl+C only to the owned smoke session, observed clean
application shutdown and confirmed no listener on 8011. An explicit second G3 check
on the same Run with `--timeout 0.5` returned FAIL/`discovery_failed`, exchange error
`request_timeout`, exit 1. No HTTP response, catalog count or readiness was fabricated;
the [failure result](examples/g3-fail.json) preserves the actual empty received bytes
and incomplete exchange. No user-owned process was terminated or adopted.

## Same-Run evidence and fresh read

Run: `aa99527d00c14846bfd22cb59504f832`, under ignored `workbench/.runs/`.
Frozen Task: `historical_return_observation`, version `1`, SHA-256 unchanged from WB-02:

```text
2865ccf73e5736cb00eef383efad0732602e4e848f4b1ec5b53bef55a2b3cb19
```

| Sequence | Committed record |
| --- | --- |
| 1 | G1 artifact `0facf27b63aa433c98f67ae2a1004074` |
| 2 | G1 PASS citing that same-Run artifact |
| 3 | G2 SKIPPED, explicit MVP authentication deferral |
| 4 | G6 SKIPPED, explicit MVP visualization deferral |
| 5 | G3 PASS evidence artifact `13ba873038f1424e98df2b10cfab4f43` |
| 6 | G3 PASS citing sequence 5 artifact |
| 7 | G3 failure evidence artifact `b50a0996259f43c38e0b6dfd2218f4c6` |
| 8 | G3 FAIL citing sequence 7 artifact; earlier PASS retained |

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| G1 | 1294 | `5ac7c2c23afad19e9540d8aae746a2d7fc1880099a18334f44b119ca460e1eb1` |
| G3 PASS | 11130 | `67b7b6e463fb8c65d36c7dca20f2033302cf597d9f46ff98056a5a9d0462be39` |
| G3 FAIL | 984 | `b7ee0ab430be2c1b4e2786c917ebb718f2c84a296d06aa3cc1cd35f5b7d34464` |

Both G3 reports have `evidence_verified=true`, `manifest_unchanged=true` and
`previous_records_unchanged=true`. Each references G1 sequence 2, G2 sequence 3 and
the actual G1 artifact. Artifact bytes survive source removal; the store verifies
digests/ownership and the recorder checks exact saved result and Gate outcome with
a new reader. `manifest.workflow` remains the original G1 workflow; G3 appends
read-only operational evidence, without constructing a competing research workflow.
G4/G5 have no records.

Fresh public read command:

```powershell
poetry run python workbench/run_store.py read --run aa99527d00c14846bfd22cb59504f832
```

Local Runs are disposable ignored evidence, absent in a fresh checkout. Committed
examples preserve result content but do not substitute for a newly executed check.

## Automated verification

All commands ran from repository root:

| Command | Result |
| --- | --- |
| `poetry run pytest workbench/tests ui_http/tests ui_cli/tests data_snapshot/tests/test_authority_topology.py data_lake/tests/test_boundary.py market_statistics/tests/test_statistics_architecture.py -q` | 456 passed in 39.23s; includes all 145 Workbench tests, 58 for G3 |
| `poetry run ruff check workbench` | Passed |
| `poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation/check_backend.py workbench/tasks/historical_return_observation/record_g1.py workbench/tasks/historical_return_observation/check_capabilities.py workbench/tasks/historical_return_observation/record_g3.py` | Passed, 5 files |
| `poetry run python workbench/tests/acceptance_example.py` | Existing synthetic two-Run example passed |
| Actual composed backend G1/G3 smoke | PASS; G3 count 1, actual list and detail preserved |
| Same-Run G3 after owned server shutdown | FAIL/request_timeout, exit 1, evidence verified |
| Public fresh `run_store.py read` command above | Passed, 8 ordered records and all 3 artifact digests verified |
| `git diff --check` and complete staged diff review | Passed before commit |

The suite emitted the existing FastAPI/Starlette httpx TestClient deprecation warning.
The initial broad suite reported 454 passed and one broken-link failure because this
acceptance document was still being authored; the final suite above resolves it.

The G3 tests exercise successful G1 plus deferred G2; missing/failed/latest-failed
G1, irrelevant G1 artifacts and invalid G2 dispositions; zero/one/multiple entries;
missing Task support; strict nested DTOs, numeric boolean coercion, unsupported tags,
duplicate/unsafe IDs; unknown detail, differing identity/description/constraints or
additional fields; malformed/duplicate-key/non-finite JSON, HTTP errors/redirects,
encoding and body-size failures, slow headers/trickle deadlines and transport errors.
They verify original bytes, per-exchange hashes, stable formatting, exact immutable
manifest and record prefix, repeated attempts, same-Run ownership, fresh CLI reads,
corruption rejection and rejection of a Run changed during inspection.

The actual composed app's OpenAPI list/detail schemas, including nested definitions,
match the checker TypeAdapters. Actual endpoint responses pass those checks.
Business acquisition, preview, execution and Python catalog functions are guarded
against invocation by the checker; request logs allow only the three read-only GETs
including G1. A temporary working directory contains only the intended Run store.
No provider, credential lookup, market acquisition or cache mutation is needed.

## Reconciliation and remaining gaps

The prospective approved v1 G3 already permits discovery and requires actual evidence,
supported index case and published constraints. WB-03 supplies that implementation
and its narrow operational contract under explicit user approval. The exact snapshot
is preserved, including WB-02 historical scope/status statements; those are reconciled
here and in the Task entry as WB-02 state, not rewritten as new version-1 semantics.
No business or shared Workbench contract drift, or generic storage limitation, was found.
Append-only storage already supports same-Run G3; no mutable workflow workaround is used.

G3 requires the Task's index capability and inspects all other returned entries. A
valid empty or unrelated catalog has successful discovery but insufficient Task
support and G3 FAIL. Importing the published descriptor type for HTTP validation
does not consult the local catalog, manufacture missing entries or validate research
plans. Future incompatible descriptor schemas require explicit client/contract
reconciliation; G1 is not cryptographic process/checkout identity or schema attestation.

Authentication and visualization remain explicitly deferred; G4 planning, G5 execution,
ResearchPlan/preview construction and statistical calculations remain unimplemented.
The desired full historical N-session distribution, e.g. 2010-2026, still needs explicit
supported index, H, windows, analyses, failure policy and acquisition authorization.
HTTP's 93-day/window cap prevents a single long-history HTTP plan; Python has no HTTP
caps but long-history Calendar, warm-up, Index facts and current upstream/cache readiness
remain unproven here. G4/G5 must choose and freeze a legal complete-window surface;
no silent truncation, assumed partition/merge equivalence or default-cache repair.
