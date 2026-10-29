# WB-07 current acceptance and readiness

Date: 2026-10-29 Asia/Shanghai. Baseline: clean develop at
`3edb363160a79e5c832c7da58bda6b4e28b19e54`, the required predecessor.
[Request](REQUEST.md) preserves the user attachment with trailing whitespace normalized.
[Procedure](SCENARIO.md), [problems](PROBLEMS.md) and [machine evidence](evidence.json)
separate execution procedure, encountered issues and original evidence references.
The [delivery report](REPORT.md) identifies completed and unavailable deliverables.

**Planning verified. Real cold/warm execution NOT RUN, pending exact cold consent.**
No real research matrix or market statistics exist for this acceptance yet. No
synthetic data substitute is supplied. This delivery records the verified preparation
and concrete authorization blocker; it is not successful real-market acceptance.
The exact cold authorization remained absent across three consecutive Goal turns.

Root, Workbench Task/Gates/storage, Research Batch/Job/inputs/identity/publication,
DataLake Application/Persistence/Calendar/Index/Provider and Statistics contracts
were reviewed. Task v1 already permits the complete matrix through Python; HTTP's
8-Job/93-day limits cannot carry it. No Task, public business model, formula,
numerical algorithm, shared recorder or runtime code was changed.

Actual backend from this checkout served G1 OpenAPI and G3 list/detail before a new
candidate was authored from the user's explicit research section. Original objective
is quoted verbatim from that section; full request is retained separately. Public
Preview confirms the requested subject/horizon order, full inclusive dates and all
analysis parameters: 16 Jobs / 32 expected analyses. Fresh G4 read verifies immutable
workflow/Preview hashes. G2/G6 retain their approved SKIPPED reasons.

- Cold Run: `d95b13c5cb554fab9f19e89cdc3c5b78`.
- Workflow: `adcebe33f9b84a33becb16832f7a9ad0`.
- Workflow SHA-256: `14484338f2073b73b9f19dc9e92a4a9727a91923d1975eb53146708c50733a10`.
- Preview: `7cbecef3ac3e42e2885451f14af2c160`, SHA-256
  `d61e85133090af3e6af235f39ed529dc793fc3f81b842cff835b935e04d1f3e6`.
- Original blobs: `workbench/.runs/<Run ID>/<stored_path>` in evidence.json.

## Technical readiness

No-Source preflight verified separate external Calendar/Index storage bindings and
Index's implicit Calendar factory. A disposable empty SQLite connection verified the
connection guard; it supplied no market facts. Initial public Calendar coverage is
302 requested / 302 missing natural days. Actual initial public Index coverage fails
because Calendar cannot yet establish sessions. No weekday/session estimate is used.
The external empty directory is retained in ignored local configuration for cold/warm
use. Re-preparation refuses a nonempty retained cache.

Default public coverage probes ran with sockets forbidden and SQLite `mode=ro`
enforced. Calendar reports rebuild required; Index reports Calendar dependency failure.
No repair, migration, deletion or override occurred. File contents, sizes and mtimes
were unchanged. The credential resolver returned availability only; no secret/hash was
recorded. Permissions and all four actual provider metadata identities remain unknown
until authorized Ensure/Export. Prior live success is not current verification.

Task-local [tool](acceptance_tool.py) controls one ordinary G5/public Batch invocation:
160 provider calls maximum, allowed endpoints trade_cal/index_basic/index_daily,
existing process/credential rate limiter set to 60/minute, 900 seconds wall time,
512 MiB database directory / 256 MiB newly added Run evidence. Storage is sampled
every 250ms and may overshoot during in-flight writes; it is not an OS quota. Deadline
or sampled storage excess terminates the child process with durable uncertainty audit.
Call counts are journaled/fsynced before delegation; calls and SQLite bindings are
guarded, not inferred from declaration strings. No account purchase is authorized.
Interruption requires original intent/result reconciliation, never automatic retry.

The ordinary adapter was exercised with absent consent inside these controls:
G5 BLOCKED / not_invoked, zero intents, zero provider calls, default caches unchanged.
This does not consume execution authority or freeze a false approval. Genuine exact
user approval is still required; no file-based or Agent-generated consent is accepted.

## Current acceptance items

| Item | Disposition |
| --- | --- |
| A full actual matrix | NOT RUN; only public Preview 16/32 verified |
| B real data/metadata | NOT RUN |
| C independent research correctness | NOT RUN |
| D cold cache population | NOT RUN |
| E warm reuse / zero calls | NOT RUN |
| F isolation | Preflight/control tests PASS; actual live invocation NOT RUN |
| G execution evidence | Planning/preflight references verified; Batch/authorization absent |
| H problem reporting | PASS for all problems encountered before the authorization blocker |

Verified checks before the approval checkpoint: 261 Workbench tests passed (93.88s),
including five new control tests; existing Starlette warning retained. Repeated focused
controls: 5 passed (4.08s). Ruff workbench passed. Mypy recorder + Task scripts passed
(9 source files; an earlier invocation including the control test checked 10). Existing
WB-01 storage example passed. Initial topology run found two not-yet-created report
links (20 passed / 1 failed); after completing the documents, all 21 topology/HTTP
architecture checks passed in 12.80s. Whitespace check passed and the complete changed
scope was reviewed before presenting the cold authorization challenge.

Post-challenge read-only revalidation confirmed all eight original artifact hashes,
the same eligible frozen Workflow, zero intents and an empty retained isolated cache.
No user authorization arrived with the automatic continuation. Review found and fixed
the watchdog-failure gap recorded as P16: monitoring/audit failure now terminates the
process even if a final audit cannot be written. All seven focused control tests passed
(6.25s), including two added subprocess fault cases; Ruff passed. This is pre-execution
control verification, not a new market Run or authority change.

Actual commands use repository-root Poetry: existing api.py on loopback port 18071;
record_g1.py with explicit readiness-only request, record_g3.py --run above --timeout 5,
record_g4.py --run above --candidate wb07/candidate.json; acceptance_tool.py
--prepare-run above; trusted host no-consent call; pytest workbench/tests -q;
pytest workbench/tests/test_wb07_controls.py -q; ruff check workbench;
mypy workbench/run_store.py workbench/tasks/historical_return_observation;
python workbench/tests/acceptance_example.py; topology/HTTP architecture checks.
The no-consent host callback returned None; no approval file or live CLI flag was used.

Next: obtain the exact adapter sentence for this frozen cold Workflow and stated
envelope, execute once, inspect saved results and metadata, then determine whether
service-level and separately authorized Research-level warm acceptance are safe.
