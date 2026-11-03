# G5 Authorized execution and delivery

This Task-local contract specializes [Task v1](../task.json), [G4](WORKFLOW_PLANNING.md)
and shared [Run](../../../contracts/RUN.md), [Gate](../../../contracts/GATE.md) and
[storage](../../../contracts/STORAGE.md). Research owns
[Batch](../../../../market_research/descriptive/BATCH_EXECUTION.md),
[Job evidence](../../../../market_research/descriptive/JOB_EXECUTION.md),
[observations](../../../../market_research/descriptive/OBSERVATION.md) and
[input identity](../../../../market_research/descriptive/cases/trailing_return/INPUT_IDENTITY.md).
Statistics owns numerical results. Workbench only authorizes, delegates and preserves.

Current eligibility: this G5 adapter is implemented and completed historical Runs
remain readable, but new execution requires a current G4 PASS, which in turn requires
current G1/G3. V1's anonymous readiness path is blocked by repository authentication, so
a fresh live G5 is currently unreachable. This changes no G5 semantics or historical
evidence; see the
[Task compatibility entry](../ARCHITECTURE.md#current-operational-compatibility).

## Prerequisites and authorization

Before execution, `record_g5.py` consumes `record_g4.read_frozen`: exact canonical Task v1,
latest suitable G1 PASS, explicit authorized G2 SKIPPED, latest suitable G3 PASS,
and exactly one accepted latest G4 PASS with verified workflow/Preview/report linkage.
Reconstruct the public ResearchPlan from that frozen workflow and compare public
Preview again. Never execute the mutable candidate, examples or manifest.workflow.
Retain complete dates, H, parameters, order and Python surface; no HTTP caps apply.

Authorization is separate same-Run evidence; the frozen workflow remains pending.
The authorization challenge contains Run/Task identity, original objective, exact
workflow and Preview references, Python execute_batch surface and acquisition,
cache-write and possible paid-data effects. Live confirmation must also record an
explicit resource budget and isolation description. `resource_budget` and
`data_isolation` are operator declarations, not enforced resource controls. Nonempty
strings do not establish safe isolation or bounded acquisition. Before any long-history
live acceptance, an operator must verify isolation and bounded acquisition through
existing owner-approved facilities, including their actual scope and limits. If those
controls cannot be verified, do not attempt full-history live execution. Workbench does
not enforce provider quotas or redirect caches. An unbounded budget is inappropriate.

For a local human, the CLI requires a TTY and displays the whole challenge before
asking for an exact workflow-bound approval sentence, budget and isolation description.
Noninteractive use without a trusted authorizer returns BLOCKED. There is no
`--approval-file`, `--yes` or synthetic live authorization option.

For Codex / DSH, `record_g5(root, run_id, authorize=callback)` is the local Python
adapter. The callback is a trusted host boundary, not a JSON approval service. It must
resolve an actual user message/approval interaction in the current context and return
`source_kind=user_message`, an actual `source_reference`, verbatim `user_statement`,
`approved_challenge` equal to the displayed challenge, `resource_budget` and
`data_isolation`. The user must return the exact `approval_sentence(challenge)` shown
by this adapter, binding objective, workflow ID/hash, surface and side effects. The
host resolves the real user source before returning; storage
cannot authenticate a speaker or prove natural-language consent. Never implement the
callback by reading an agent-generated approval file or self-asserting consent.
Missing, declined, malformed or mismatched authorization blocks before invocation.

There is no production synthetic execution entry or caller-supplied invocation seam.
The ordinary adapter always validates live authorization and calls the public Research
API. It rejects `source_kind=synthetic_test`. No synthetic artifact is reusable as live permission.
It also rejects frozen workflows with synthetic input-resolution provenance; example
planning Runs cannot become live execution requests by supplying an approval record.
Tests simulate the trusted host interaction only within the test harness, install
public-service fakes and prohibit provider/default-cache access. Historical synthetic
execution evidence remains readable; accepting its context during read grants no
execution permission. Workbench is not a security sandbox and cannot prevent arbitrary
Python callers from bypassing the official Agent workflow.

## One attempt, durable evidence and uncertainty

Use existing RunStore artifact/event/gate operations; shared storage needs no amendment.
A Task-local exclusive `.g5-writer` lock serializes these adapters. Other Run writers
must be quiescent; check unchanged prefixes before intent and after invocation. Busy or
corrupt storage fails explicitly. Never automatically remove a stale lock.

Before invoking, preserve authorization and append `G5 execution intent` with unique
attempt ID, context, exact frozen workflow/Preview and authorization artifact references.
Once any intent exists, this adapter permanently refuses another invocation in that
Run, even if there is no result or a later BLOCKED outcome. Operator reconciliation
must establish the actual outcome; deleting evidence or rerunning is not recovery.
This adapter supplies no retry or reconciliation override. A new execution requires separate
operator reconciliation and fresh authorization/planning in a new Run.

Call the published `market_research.descriptive.execution.execute_batch(plan)` once.
No window splitting, result merging, provider fallback, cache repair or extra acquisition.
Preserve the actual public BatchResult projection, then append `G5 execution completed`,
then a report artifact and Gate. Any exception outside a returned BatchResult, interruption,
invalid/unserializable output or publication failure leaves the committed intent and
requires reconciliation. An ordinary invocation/projection exception records BLOCKED
with `uncertain`; no exception text/repr or fabricated Batch is emitted. BaseException
propagates, leaving the intent for fresh read-back. A disconnected caller proves no failure.
An orphan authorization without intent does not establish invocation; safe reauthorization
may occur. An intent always prevents automatic retry, including a crash before the call.

## Outcomes and preserved output

| G5 | Meaning |
| --- | --- |
| PASS | Actual validated Batch status success, every planned Job/required analysis succeeds; all output and linkage preserved |
| FAIL | Actual Batch partial_success or failed; preserve successful analyses, failures, skipped Jobs and original coverage |
| BLOCKED | Missing prerequisites/authorization, prior intent, or uncertain invocation; no successful research claim |

PASS means completed requested computation under the published missing-tolerant policy,
not complete market data. Legal partial Index facts can PASS with explicit Unavailable /
Excluded populations and partial market/observation coverage. Incomplete Calendar,
insufficient history or no Eligible samples remain Research failures, never repaired.

Output schema 1 retains plan; batch counts/status; ordered fixed Jobs/identities;
actual requests/specs and raw statistical results; analysis statuses/association linkage;
prepared public requests/views/attempt diagnostics; observations, E/U/X and their derived
counts/ratios; fact/warm-up/sample coverage; dependence; numeric sample and ordered keys;
provenance including exact canonical input bytes (base64) and published fingerprint.
Shared in-memory references are represented by explicit links to the same per-Job
observation/projection, avoiding repeated copies. This is delivery JSON, not a new Research
result model or registry. Finite floats retain round-trip values and signed zero.

Only known public value carriers and named public fields are serialized. Exception
objects/chains, arbitrary malformed input objects and unknown values are omitted with an
explicit marker; never stringify them. Failure stage/category/request linkage is retained.
Failure free-text and blocking/skip text are omitted to avoid leaking arbitrary exception
messages; public UnitFailure reasons are likewise omitted while identities/counters remain.
This deliberate safety limitation is explicit in each projection, never invented diagnostics.

Fresh `--read` verifies the entire current store's integrity, then validates exact
Task/G4 and their bound prerequisites against the committed record prefix strictly
before the historical intent. The same strict G4 verifier checks that prefix's latest
suitable G1/G2/G3 and sole accepted latest G4, including frozen artifacts and references.
No caller-supplied cutoff can relax the ordinary pre-execution latest-Gate check.
Read also verifies authorization challenge,
intent ordering/references, result and completion/report/Gate associations, plan and
ordered Job/analysis linkage, accounting and correct G5 outcome. It never invokes
Research or asks for authorization. An unfinished intent reports uncertainty even if
the caller did not record BLOCKED. Later failed G1/G3 (or other Gate attempts) revoke
current eligibility but do not invalidate intact historical evidence. They never erase
preserved results. Corrupt evidence still fails closed, including in the historical
prefix. CLI PASS=0, FAIL=1, BLOCKED=2; corrupt/busy storage=1.

## Reconciliation

Task v1 already requires separate authorization and all requested computation; the
historical Task V1 implementation-state clauses do not prohibit later commissioned slices.
The G5 long-history availability clause means preserve/report actual coverage under the
case policy, not invent a strict-completeness rule. No approved semantic amendment or
Task JSON change is needed. G2/G6 remain deferred. Deterministic acceptance proves the mechanism only, not live readiness or general natural-language planning quality. See [usage](../README.md).
