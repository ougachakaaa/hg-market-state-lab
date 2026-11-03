# Historical Return Observation Task

Task `historical_return_observation` version 1 is defined by the immutable
[task.json](task.json); its original approval evidence remains
[DESIGN_REQUEST.md](DESIGN_REQUEST.md). Task approval does not authorize live Research.
The shared [Task](../../contracts/TASK.md), [Run](../../contracts/RUN.md),
[Gate](../../contracts/GATE.md) and [storage](../../contracts/STORAGE.md) contracts apply.

Current Task-specific contracts: [G1 backend readiness](authority/BACKEND_READY.md),
[G3 capability discovery](authority/CAPABILITY_DISCOVERY.md),
[G4 workflow planning](authority/WORKFLOW_PLANNING.md),
[G5 authorized execution](authority/AUTHORIZED_EXECUTION.md), and
[research results](authority/RESULTS.md). G2 and G6 remain deferred for version 1 and
its frozen Runs. Addressing G6 requires an explicitly user-approved new Task version or
another separately authorized extension under the shared Task contract; existing
snapshots and evidence are never rewritten, and an authority change itself grants no
approval or execution permission. Future publication uses the
[Research boundary](../../../market_research/PUBLICATION.md), not Workbench storage. The
[usage guide](README.md) identifies runtime entry points;
[results](results/2026_four_index_returns/README.md) are organized research findings,
not execution authorization. RunStore owns actual execution history and original
evidence.

## Current operational compatibility

Repository HTTP now applies
[Authentication MVP V1](../../../ui_http/AUTHENTICATION.md) to every path except the
three public Auth POSTs. In particular, anonymous `GET /openapi.json` and all Research
operations return HTTP 401 before routing. Task V1 was approved under the earlier
anonymous loopback assumption and has no implemented G2.

| Gate | Task-local implementation | Current repository compatibility |
| --- | --- | --- |
| G1 | Read-only `GET /openapi.json` checker and Run recorder | **Blocked.** The checker sends no Cookie or credentials and requires HTTP 200. A correctly configured current backend returns 401, so a fresh G1 attempt records FAIL with `http_status`; it cannot establish PASS. |
| G2 | Deferred in V1 | No implementation. Repository authentication exists in `ui_http`, but this Task has no authenticated G2 recorder and must not record PASS. |
| G3 | Anonymous capability list/detail discovery | **Blocked.** Requires latest G1 PASS and sends anonymous GETs; current Research endpoints require authentication. Deterministic fixture tests validate decoding and evidence behavior only. |
| G4 | Public Python ResearchPlan/Preview and workflow freezing | **Blocked for a fresh Run.** The mechanism is implemented and historical/fixture Runs remain readable, but a new PASS requires current G1/G3. |
| G5 | Authorized public Python Batch execution and result retention | **Blocked for new execution.** The mechanism is implemented and completed historical Runs remain readable, but execution requires current G4 and separate user authorization. |
| G6 | Deferred | No visualization implementation or claim. |

The exact G2 deferral reason
`Authentication deferred in current MVP; loopback backend has no authentication.` is
frozen approval/provenance text in `task.json`, the G1 recorder and the G3 prerequisite
validator. It remains required when reading existing V1 evidence, but it is not a
current factual claim about the backend. Do not change it in place; a new Task version
must define a new deferral or authentication disposition.

Existing Runs, frozen Task snapshots and retained [results](results/2026_four_index_returns/README.md)
remain valid historical evidence. They cannot authorize current execution or prove
current integration. A fresh G1 attempt may create a Run and preserve its real FAIL;
that is not a successful readiness claim. G3/G4/G5 must not be reached by bypassing
authentication, fabricating a G1 PASS, adding an unauthenticated OpenAPI route,
persisting credentials, or substituting fixture evidence for live evidence.

### Required future decision

Resolving the gap requires a new user-approved Task version or another explicit
authorization decision. This entry documents options but implements none:

1. **Authenticated new version (recommended direction).** Define an explicit
   authentication prerequisite/handshake and let a trusted host supply an in-memory
   authenticated session to read-only G1/G3 checks. Preserve the existing OpenAPI
   compatibility criteria; never persist cookies, tokens or passwords in Run evidence.
2. **Split transport and contract checks in a new version.** Let anonymous G1 recognize
   a well-formed 401 Auth envelope as service/auth-boundary reachability, then perform
   authenticated OpenAPI and capability verification under G2/G3. This changes G1 PASS
   semantics and needs explicit approval.
3. **Retire V1 for new live execution.** Keep V1 and its evidence historical and defer
   new live Runs until a future Task version is approved.

The current workflow is **not runnable without changes** against the authenticated
backend. This is a documented compatibility gap, not authorization to weaken HTTP
security or silently redefine V1.

Research owns the [published capability](../../../market_research/descriptive/RESEARCH_CAPABILITY.md),
[trailing return case](../../../market_research/descriptive/cases/trailing_return/ARCHITECTURE.md)
and [Batch contract](../../../market_research/descriptive/BATCH_EXECUTION.md); HTTP owns
its [transport contract](../../../ui_http/products/research/http-contract.md). Only the
published descriptive index case is admitted. This Task owns neither financial
formulas, statistics, provider selection, missing-data policy, acquisition, cache
repair nor service lifecycle. Long historical questions do not imply live readiness.
