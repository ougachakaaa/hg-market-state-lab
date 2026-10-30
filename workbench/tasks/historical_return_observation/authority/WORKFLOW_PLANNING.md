# G4 Workflow Planning and Persistence

This Task-specific contract specializes [Task v1](../task.json), the shared
[Gate](../../../contracts/GATE.md) and [storage](../../../contracts/STORAGE.md) contracts.
Research owns
[Plan and expansion](../../../../market_research/descriptive/BATCH_EXECUTION.md) and
[pure Preview](../../../../market_research/descriptive/RESEARCH_CAPABILITY.md); Statistics
owns [spec validation](../../../../market_statistics/CONTRACT.md). Workbench owns no
planner, calculation, acquisition, scheduler or general workflow language.

## Authorization reconciliation

Task v1's required authorization is explicitly **before research execution**; its
allowed capabilities separately permit pure G4 Preview and separately authorized G5.
The G4 phrase "resolved research inputs and authorization" requires an explicit
authorization disposition, not execution approval as a prerequisite for pure planning.
G4 records `pending`, identifying future execution, acquisition, cache writes and
possible paid-data access as requiring explicit user authorization for the exact
frozen artifact identity/hash. Preview grants none. This reconciles the existing
clauses without changing the approved JSON or historical Run snapshots. No Task
amendment is required. WB-02/WB-03 implementation-state statements remain historical.
G5 execution and authorization are governed by the separate G5 contract.

## Agent-authored candidate

Codex / DSH interprets the original natural-language objective, reads actual same-Run
G3 descriptors, asks the user to resolve missing intent, and writes strict finite JSON:

- `schema_version`: integer `1`.
- `original_objective`: exact nonempty original research request, separate from the
  manifest's preliminary G1 readiness request.
- `input_resolution`: `{kind, reference}`; kind is `explicit_user_request`,
  `user_interaction` or `synthetic_test`; reference preserves the supplied request or
  clarification evidence. A synthetic reference never establishes live authorization.
- `capability_id`: actually discovered `trailing_cumulative_return_v1`.
- `execution_surface`: `python`.
- `research_plan`: every explicit public ResearchPlan field: `metric`,
  `metric_parameters`, `subjects`, `horizons`, `windows`, `analysis_requests`,
  `on_job_failure`. Windows contain exactly `start_date/end_date` (YYYY-MM-DD);
  requests exactly `request_id/spec`; quantile specs exactly `method/points`,
  interval_count exactly `method/edges/unit`. No omitted fields or extra keys.

JSON arrays map to public ordered sequences, canonical date strings to public
DateWindow values, specs to public Statistics constructors and requests to public
AnalysisRequest. ResearchPlan construction and public preview_plan perform complete
semantic validation; Workbench only checks the serialization and Task composition.
No default subject, horizon, dates, methods, coordinates, units or failure policy is
provided. `resolved_inputs` in the frozen workflow is the complete candidate plan
plus its explicit resolution provenance; it never replaces manifest inputs.
The agent remains responsible for faithful natural-language interpretation. Deterministic
validation cannot prove that interpretation or general planning quality; interactive
must be assessed through interaction with the user.

## Prerequisites and surface selection

`record_g4.py --run RUN_ID --candidate FILE` accepts only an integrity-verified Run
with the exact canonical approved Task snapshot. Latest G1 must have suitable same-Run
PASS evidence and latest G2 the exact authorized MVP SKIPPED reason, checked by the
existing G3 prerequisite validator. Latest G3 must PASS after those records and cite
actual preserved list/detail exchanges for that same target and those prerequisites.
Revalidate raw exchange digests, public descriptor shapes, list/detail equality, complete
catalog and required supported capability; do not call discovery or synthesize entries.
An older G3 PASS cannot mask a later FAIL. A new G1/G2 attempt requires a new G3 check.
Unmet prerequisites produce BLOCKED without constructing or previewing a plan.

This recorder supports the local public Python ResearchPlan/preview_plan surface only. It
does not inherit HTTP resource caps; an explicit historical 2010-01-01..2026-10-28
window or H > 20 is accepted only when public preflight succeeds. No default dates
are supplied. HTTP selection is explicitly rejected before preview, including an
oversized 2010-2026 window; no HTTP POST is sent. Bounded HTTP Preview remains an
owner-published alternative for an external agent, but freezing HTTP workflows through
this recorder is not implemented. Adding that path requires its own transport acceptance
under the [HTTP contract](../../../../ui_http/products/research/http-contract.md).
There is no partitioning, aggregation, truncation, metric substitution or execution.

## Frozen evidence and read-back

The recorder preserves the submitted candidate in its G4 attempt evidence, including
failed/blocked attempts. A PASS additionally preserves separate immutable actual Preview
and frozen workflow artifacts in the same Run. Preview serializes the returned public
plan and ordered public PlannedJobs, counts and expected ordered analyses, without
reimplementing expansion. Workflow schema 1 includes Run/Task identity and Task digest,
original objective, resolved inputs/provenance, capability/descriptor reference,
selected public surface, complete ResearchPlan, Preview artifact identity/hash/path,
fixed operational steps/dependencies, pending authorization, expected future outputs,
owner limits and explicit live-readiness gaps. Planned steps are descriptive records,
not an executable graph. They order input preparation, Research observation/conversion,
Statistics and association (delegated to Research Batch), then result/evidence retention.
The workflow also records the selected case's fixed public source binding and
`descriptive_missing_tolerant_v1` policy as a descriptive snapshot with canonical
[case](../../../../market_research/descriptive/cases/trailing_return/ARCHITECTURE.md) and
[input-policy](../../../../market_research/descriptive/cases/trailing_return/INPUTS.md)
references. This grants no direct Workbench access to upstream services and introduces
no selectable policy, source fallback or second validator.

G4 PASS evidence order is exactly workflow, Preview, attempt report. The report binds
all identities/hashes and the exact prerequisite record sequences/evidence. Fresh
`record_g4.py --run RUN_ID --read` locates the sole accepted workflow through G4 PASS,
verifies same-Run registration/digests, report/Preview/plan/prerequisite associations,
and returns that exact artifact reference. It does not accept a mutable candidate as
execution input or treat manifest.workflow (the preliminary G1 steps) as research authority.
Current failed prerequisites or a later G4 failure make read-back ineligible.
This is the current operational eligibility read. For completed G5 evidence retrieval,
the [G5 contract](AUTHORIZED_EXECUTION.md) applies the same verifier to the committed
prefix before that invocation's intent, preserving its exact bound prerequisites.

After any accepted G4 PASS this recorder refuses another planning attempt; changed
plans need a new Run. A Task-local exclusive `.g4-writer` directory serializes G4
recorders, with explicit busy errors and no automatic stale-lock removal. Existing
RunStore publication/locks remain unchanged. Other Run writers must be quiescent during
finalization: the recorder verifies the original record prefix and rejects concurrent
changes before PASS; independent multi-record operations are not a transaction.
Artifacts left by an interrupted attempt have no execution authority without a verified
G4 PASS. Hashes provide local integrity, not hostile-writer authenticity.
Historical examples never substitute PASS evidence for a different Run.

| Outcome | Meaning |
| --- | --- |
| PASS | Required explicit inputs validated by public owners, actual pure Preview and frozen workflow preserved and verified |
| BLOCKED | Prerequisite Task/Gates/evidence prevent planning; no preview |
| FAIL | Candidate shape, selected surface, public plan/spec validation or preview fails; no execution |

Unsupported Task, accepted workflow replacement, storage corruption/busy/publication
failure produce a nonzero operational error without inventing an outcome. Unexpected
runtime defects propagate; never fabricate Preview or PASS. CLI PASS=0, FAIL=1,
BLOCKED=2; storage errors exit 1. No G5 outcome is generated.

Preview does not prove canonical subject membership, historical Calendar completeness,
warm-up sufficiency, Index facts, credentials/permissions, compatible caches or live
availability. These remain explicit G5 readiness gaps, together with sample dependence,
coverage and missing-data limitations. The future executor must require explicit
authorization for the verified artifact and resolve these gaps under owner contracts.
See [usage](../README.md).
