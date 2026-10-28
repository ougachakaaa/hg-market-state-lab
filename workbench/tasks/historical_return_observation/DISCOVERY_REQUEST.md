# Goal: WB-03 — Research Capability Discovery Gate

Repository: `ougachakaaa/hg-market-state-lab`
Baseline: `develop`
Required predecessor: `966d3919b89cb3a87732610f21ac8b2e1e560cf2`

## Objective

Implement G3 — Capability Discovery for the approved Workbench Task:

`historical_return_observation`, version `1`.

An external Codex / DSH agent must be able to discover the actual Research capabilities published by the running Market State Lab backend, inspect their descriptions and constraints, and preserve machine-verifiable discovery evidence in the same Workbench Run.

Deliver Authority + Implementation + Tests + Acceptance + Reconciliation.

## Architectural boundaries

Workbench remains an agent-facing operational contract and evidence facility.

Capability semantics and publication belong to `market_research`.

HTTP paths, DTOs, error behavior and OpenAPI belong to `ui_http`.

Do not introduce a second capability registry, duplicate business validation, or infer support from source-code scanning.

Reuse the existing Workbench RunStore and the approved Research Task.

## Required investigation

Read:

- Root `AGENTS.md` and `ARCHITECTURE.md`.
- `workbench/ARCHITECTURE.md`.
- Workbench Task / Run / Gate / Storage contracts.
- `workbench/tasks/historical_return_observation/task.json`.
- The existing G1 authority and implementation.
- `market_research/USAGE.md`.
- `market_research/descriptive/RESEARCH_CAPABILITY.md`.
- `ui_http/products/research/http-contract.md`.

Inspect actual published OpenAPI and relevant implementation only as necessary.

## G3 semantic contract

G3 discovers currently published Research capabilities using:

- `GET /research/capabilities`
- `GET /research/capabilities/{id}`

The actual HTTP responses are the authority for discovered runtime capability descriptors, within their owning contracts.

The checker must:

1. Require a suitable G1 PASS in the same Run.
2. Allow the Task-specific deferred G2 SKIPPED disposition, without implying authentication.
3. Request the actual capability list.
4. Fetch each returned capability's detail.
5. Validate the responses against their published transport contract.
6. Detect inconsistent list/detail identity or content.
7. Report the actual capability count, IDs, descriptions and published constraints.
8. Preserve the original responses and verification evidence.
9. Distinguish supported capability publication from live market-data readiness.

Do not hardcode a permanent expectation that there is exactly one Research Capability.

The current repository may publish one capability, but that is an observed runtime result, not a Workbench invariant.

## Gate behavior

Use the existing four status values:

PASS / FAIL / BLOCKED / SKIPPED.

PASS requires successful discovery and inspection of all returned capabilities, with preserved same-Run evidence.

FAIL represents an attempted discovery that returned an invalid, incompatible, incomplete or failed response.

BLOCKED represents an unmet prerequisite that prevents discovery.

SKIPPED remains available only when explicitly justified by the Task contract.

An empty but otherwise valid capability list must not be reported as sufficient support for the Historical Return Task. Distinguish successful empty discovery from Task capability readiness, and report the unsupported Task requirement explicitly.

Never synthesize or silently replace a missing capability.

## Implementation

Implement the smallest Task-specific G3 checker and Run integration.

Prefer using existing HTTP tooling and the current root runtime.

Do not create a generic tool framework or another Agent Runtime.

The checker must:

- Use finite timeouts.
- Avoid automatic retries.
- Make read-only HTTP requests.
- Preserve machine-readable observations and errors.
- Use stable result formatting.
- Avoid secrets and raw private exception details.

Integrate with the existing Workbench RunStore.

A Run created during G1 must be able to receive its G3 outcome and evidence without changing the frozen Task snapshot or existing records.

Do not overwrite `manifest.workflow` or create a competing workflow definition.

Do not implement G4 planning in this Goal.

If a genuine generic storage contract limitation blocks G3, reconcile it explicitly rather than working around it with mutable state.

## Acceptance

Automated tests must demonstrate:

1. G1 PASS + Task-authorized G2 SKIPPED permits G3.
2. Missing or failed G1 blocks G3.
3. Compatible capability list and details produce PASS.
4. An empty capability catalog does not falsely establish Task readiness.
5. Unknown or inconsistent capability detail produces FAIL.
6. Malformed JSON, HTTP errors and timeouts produce non-PASS.
7. Capability count is derived from actual responses.
8. Original discovery evidence is preserved in the correct Run.
9. A fresh read verifies the saved artifact and Gate outcome.
10. No Research Preview, Execute, market-data acquisition or cache mutation occurs.

Use deterministic local HTTP fixtures for failure and contract tests.

Also perform a smoke verification against the actual composed backend when the environment permits.

## Scope limits

Do not implement:

- G4 AI Workflow Planning.
- G5 Research Execution.
- G6 Visualization.
- Authentication.
- ResearchPlan construction or preview.
- Statistical calculations.
- Long-period 2010–2026 execution or partitioning.
- Business module modifications.
- A generic capability registry, orchestration engine, MCP server or new official CLI.

## Future objective

Preserve the intended end-user goal:

A user can ask Codex to research the historical N-trading-session cumulative return distribution of an explicitly specified supported index over a period such as 2010–2026.

WB-03 only establishes which relevant capabilities are actually available.

Long-history execution-surface selection, workflow planning and authorization remain for G4/G5.

## Delivery

Follow:

Authority Encoding → Implementation → Tests → Reconciliation.

Report:

- Changed files and authority locations.
- Exact G3 invocation command.
- Actual discovered capability count and IDs.
- One PASS and one failure result.
- Same-Run G1/G3 evidence demonstration.
- Tests executed and their outcomes.
- Any Task or Workbench contract drift.
- Remaining capability gaps for the final research objective.
- Final commit SHA.

## Success criterion

An Agent can discover the actually published Research capabilities through their official HTTP endpoints, prove that discovery succeeded or failed, and preserve the result within an existing Workbench Run without inventing business capabilities or modifying project semantics.
