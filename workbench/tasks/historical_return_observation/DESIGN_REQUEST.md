<!-- Approval evidence: user-supplied WB-02 /goal on 2026-10-28. Original wording below, trailing whitespace normalized; historical design intent, not a competing runtime authority. Canonical encoded definition: task.json. -->

# Goal: WB-02 — Historical Return Observation Task + Backend Ready Gate

Repository: `ougachakaaa/hg-market-state-lab`
Working baseline: `develop`
Reviewed foundation commit: `ea1b5159df367d4ed534380916c9e9645450f3ef`

## Objective

Introduce the first user-designed Workbench Task:

`historical_return_observation`

Implement its first operational Gate:

**G1 — Backend Ready**

Deliver Task Authority + G1 Implementation + Tests + Acceptance + Reconciliation.

The task must build on the existing Workbench Task / Run / Gate / Storage foundation without redefining or replacing it.

## Final user objective

The intended end-user workflow is:

A user directly asks Codex / DSH to research the historical N-trading-session cumulative return distribution for a specified supported market subject across a historical period such as 2010–2026.

The Agent should eventually be able to:

1. Establish backend readiness.
2. Discover the actual project capabilities.
3. Translate the user's research goal into a valid capability-composition workflow.
4. Freeze that workflow before execution.
5. Invoke the authorized public operations.
6. Collect statistical results and execution evidence.
7. Report what happened, the results, failures, and artifact locations.

This is the final MVP objective, not the required implementation scope of WB-02.

## Research Task semantics

Task ID:

`historical_return_observation`

Define a versioned, approved Task authority under `workbench/tasks/`.

The Task must specify:

- Task identity and purpose.
- Supported subject requirements.
- Required user inputs.
- Permitted public capabilities.
- Research meaning and limitations.
- Six Task-owned Gate definitions.
- Workflow planning constraints.
- Expected research outputs.
- Acceptance requirements.

The research metric is the existing published trailing cumulative return:

`close(T) / close(T-H) - 1`

H is a strictly positive integer measured in trading sessions.

The historical sample window is inclusive and explicit.

Do not introduce forward returns, market predictions, strategies, or trading recommendations.

Current published Research support is limited to the existing descriptive index case. Do not imply that arbitrary stocks or futures are supported.

The Task must not invent a subject, horizon, date, statistic, bin edges, provider, or missing-data policy.

Missing required user inputs must be resolved explicitly before execution.

## Long-history compatibility

The final user objective includes full historical windows such as 2010–2026.

Inspect and explicitly record the current execution-surface limitations:

- Research HTTP has resource/window limits.
- Research public Python execution has different constraints.
- A single 2010–2026 HTTP ResearchPlan is not currently supported.
- Splitting HTTP calls and merging results is not automatically equivalent to a single research computation.
- Long-history live-data readiness has not been proven by WB-01.

Do not implement long-window execution, automatic partitioning, result merging, or new Research semantics in WB-02.

Preserve this requirement as a future G4/G5 design constraint and acceptance target.

The Task should be capable of expressing the full historical objective without falsely claiming that it is already executable.

## Six Task-owned Gates

Define the following exact Gates in the Research Task:

G1 — Backend Ready
G2 — Authentication
G3 — Capability Discovery
G4 — Workflow Planning and Persistence
G5 — Execution
G6 — Visualization

G2 and G6 are deferred in the current MVP.

Deferred outcomes use `SKIPPED` with explicit reasons.

G3, G4, and G5 are future implementation Goals. Do not fabricate PASS results for them.

Gate criteria and dependencies belong to the Research Task. Outcomes belong exclusively to Runs.

Do not introduce global Workbench Gates.

## G1 Backend Ready contract

An Agent must be able to determine whether the existing Market State Lab backend is correctly running.

The official backend startup entry remains:

`poetry run lab serve backend`

Default address:

`http://127.0.0.1:8011`

G1 must verify:

1. Backend HTTP reachability.
2. Valid OpenAPI response at `/openapi.json`.
3. Presence of the expected Research operations and operationIds.
4. A machine-readable readiness result containing actual observations.
5. Explicit failure reasons and bounded timeouts.

A reachable port alone is not sufficient.

A compatible OpenAPI response demonstrates the expected published application contract; do not claim cryptographic process or checkout identity.

A successful `lab doctor` process exit alone is not sufficient to pass G1.

If the backend is stopped, the Agent may explicitly start it through the existing official entry point and recheck readiness.

The readiness checker itself must be read-only.

Never terminate, replace, or silently take ownership of an existing user-owned backend process.

## G1 implementation

Implement the smallest suitable task-specific, deterministic readiness checker.

It should:

- Use the existing repository root runtime.
- Support an explicit target address, defaulting to the current backend address.
- Have finite request timeouts.
- Verify the relevant published API structure.
- Produce a deterministic JSON result.
- Return meaningful process exit status.
- Avoid market acquisition and business execution.
- Require no new official CLI command, backend service, MCP server, database, or orchestration framework.

Do not duplicate or modify `lab doctor` or `ui_http` business behavior.

## Workbench Run integration

Use the existing `workbench/run_store.py` public operations.

Demonstrate the following:

1. Load the approved Research Task definition.
2. Create a Run with the exact Task snapshot.
3. Perform the actual G1 readiness check.
4. Save the raw machine-generated readiness result as an artifact.
5. Record the corresponding G1 Gate outcome with same-Run evidence.
6. Read the Run back and locate the preserved readiness artifact.

G1 PASS must not be recorded without actual supporting evidence.

A failed check must produce an explicit FAIL or BLOCKED outcome, according to the Task's criteria.

Do not modify the generic Workbench Store merely for implementation convenience.

If a real contract incompatibility is discovered, reconcile it explicitly before making a shared-contract change.

## Authority and approval boundaries

The human-defined Task purpose and six-Gate structure are given in this Goal.

Encode them in a narrow Task authority, following Workbench progressive disclosure.

The Goal request is the source of Task design intent, but must not be interpreted as authorization to execute live market research or access paid data.

If a necessary business semantic decision is absent, identify it rather than silently inventing a rule.

Do not create an Agent-controlled Task registry or approval service.

Do not modify Research, Statistics, DataLake, or HTTP semantic contracts.

## Acceptance

Automated tests must cover:

1. Correct backend/OpenAPI → G1 PASS.
2. Backend stopped → non-PASS with explicit reason.
3. Wrong service on the expected port → non-PASS.
4. Malformed or incompatible OpenAPI → non-PASS.
5. Connection timeout → non-PASS.
6. G1 result can be stored in a Workbench Run.
7. Stored Gate evidence can be retrieved and verified.
8. Evidence belongs to the correct Run.
9. Deferred G2/G6 are not misreported as PASS.
10. No unexpected market or cache side effects.

Use isolated local HTTP fixtures for deterministic tests.

Also verify against a real launched backend when the environment permits. Use a safe isolated port if the default port is occupied.

Do not require Tushare credentials or execute live Research.

## Out of scope

Do not implement:

- G2 authentication.
- G3 capability discovery.
- G4 AI workflow planning.
- G5 research execution.
- G6 visualization.
- Long-range execution or HTTP partitioning.
- Statistical calculation or result aggregation.
- A generic Gate framework.
- A second Workbench storage implementation.
- Changes to existing business modules.

## Delivery and reconciliation

Follow:

Authority Encoding → Implementation → Automated Tests → Runtime Smoke Verification → Reconciliation.

At completion report:

- Changed files and authority topology.
- The approved Research Task identity and version.
- Exact G1 execution command.
- One machine-readable PASS example.
- One machine-readable failure example.
- One actual Workbench Run containing G1 evidence.
- Executed tests and results.
- The status of G2–G6.
- Remaining constraints for the 2010–2026 objective.
- Any authority or implementation drift.
- Final commit SHA.

## Success criterion

An external Codex / DSH agent can discover the approved Historical Return Observation Task, start or reuse the existing backend safely, verify the expected API using an actual machine check, and preserve the G1 outcome and evidence in a retrievable Workbench Run.

No Research execution is required in WB-02.