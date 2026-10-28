# Goal: WB-04 — AI Research Workflow Planning and Persistence

Repository: `ougachakaaa/hg-market-state-lab`
Working baseline: `develop`
Required predecessor: `9d06542f711a42412d40b1e20c6e7e473be73a96`

## Objective

Implement G4 — Workflow Planning and Persistence for the approved Workbench Task:

`historical_return_observation`, version `1`.

Enable Codex / DSH to translate an explicit natural-language historical-return research goal into a valid composition of published Market State Lab capabilities, perform pure Research Preview, and freeze a machine-readable workflow in the existing Workbench Run.

Complete Authority Encoding + Implementation + Tests + Acceptance + Reconciliation.

Do not implement actual research execution.

## End-user objective

The eventual user experience is:

"Study the N-trading-session cumulative return distribution of an explicitly specified index over the historical period 2010–2026, using the existing Research and Statistics capabilities. Preserve the results and tell me where they are."

N, the canonical index code, exact dates, analysis methods and method parameters must be explicitly supplied or resolved through user interaction.

Never silently invent missing inputs.

## Ownership

The Agent performs natural-language reasoning and capability composition.

The Research module owns ResearchPlan, Job expansion, Preview, observation semantics and execution.

Statistics owns statistical methods and parameter validation.

HTTP owns transport and its additional resource bounds.

Workbench owns the Task-specific planning contract, verification procedure, frozen workflow artifact and operational evidence.

Do not introduce another Research engine, statistical algorithm, planning DSL framework, generic Agent Runtime or scheduler.

## Prerequisites

G4 requires:

- The exact approved Task snapshot.
- A suitable latest G1 PASS.
- The explicitly deferred G2 SKIPPED disposition.
- A latest G3 PASS with preserved same-Run capability discovery evidence.

An earlier G3 PASS must not override a later G3 FAIL.

Fail closed on unmet prerequisites.

## Planning semantics

The Agent must:

1. Interpret the user's original research goal.
2. Identify the actually discovered supported Research capability.
3. Resolve all required research inputs explicitly.
4. Select an execution surface consistent with the published contracts.
5. Construct the complete ResearchPlan using the public Research types.
6. Perform pure preflight and preview.
7. Persist the resulting validated workflow and evidence.
8. Record the G4 outcome in the same Run.

A workflow must identify:

- Exact original research objective and resolved inputs.
- Selected capability and execution surface.
- Explicit ResearchPlan fields.
- Statistical analysis requests and parameters.
- Planned operation order and dependencies.
- Preview result, planned Jobs and expected analyses.
- Required future execution authorization.
- Expected outputs and evidence artifacts.
- Relevant limits and known readiness gaps.

Use existing public Research and Statistics validators. Do not duplicate numerical or business validation.

## Historical-range execution surface

The full historical objective, such as 2010–2026, is essential.

Research HTTP currently limits each window to 93 inclusive calendar days and H to 20 trading sessions.

The published Python Research API does not inherit these HTTP-specific caps.

For a complete long historical window, evaluate the public Python ResearchPlan/preview_plan surface as the candidate execution path.

Select it only if public preflight succeeds.

Do not silently split HTTP requests, merge summary statistics, truncate dates or substitute another metric.

Preview legality does not prove that historical Calendar and Index facts are available.

Preserve those uncertainties explicitly for G5.

For bounded requests where HTTP is legally supported, the workflow may select HTTP Preview under the HTTP contract.

## Workflow persistence

Existing Run manifests are immutable.

Do not overwrite `manifest.workflow`, `resolved_inputs` or any historical record.

For G4, the authoritative frozen research workflow must be stored as an immutable same-Run artifact, with its identity, hash and association to the G4 PASS outcome.

Distinguish this artifact from the preliminary G1 operational steps stored in the original manifest.

The future G5 executor must be able to identify the exact authorized workflow artifact unambiguously.

Do not execute a mutable draft or silently replace a frozen workflow.

If the plan needs to change after finalization, use a new Run rather than editing previously accepted evidence.

Define a narrow Task-specific workflow contract, not a general-purpose workflow engine.

## Authorization boundary

Pure planning and preview do not authorize market-data acquisition.

G4 must record which future operations require authorization and whether authorization remains pending.

G5 will require explicit user authorization before actual execution.

Reconcile the existing Task v1 language about "authorization" with this separation.

Do not silently modify the approved `task.json`.

If the existing approved Task semantics genuinely conflict with this separation, propose the smallest explicitly versioned semantic change and identify the approval requirement rather than rewriting historical snapshots.

## Implementation

Implement the minimum Task-specific machinery for:

- Accepting an Agent-authored candidate workflow.
- Checking its Task/Gate prerequisites.
- Validating its complete ResearchPlan using published public types.
- Performing pure Research Preview.
- Checking that the selected surface is legal for the complete requested window.
- Preserving the final workflow and Preview as Run artifacts.
- Recording G4 PASS / FAIL / BLOCKED with meaningful evidence.
- Reading back and verifying the exact frozen workflow.

Natural-language planning remains the responsibility of Codex / DSH. Do not embed an LLM SDK or build another Agent planner into Workbench.

Do not call execute_batch, POST /research/execute, provider services or DataLake acquisition operations.

## Acceptance

Implement deterministic automated acceptance for:

1. Latest G1/G3 PASS and authorized G2 SKIPPED permit G4.
2. Missing/failed prerequisites block G4 without preview.
3. Explicit valid index/H/window/analyses produce a legal ResearchPlan.
4. A 2010–2026 historical window can be evaluated under the public Python Preview surface without HTTP-specific truncation.
5. An oversized HTTP window is rejected for HTTP selection rather than silently split.
6. Missing inputs or unsupported methods never receive invented defaults.
7. Invalid statistical parameters fail through public validation.
8. Preview performs no market acquisition or cache mutation.
9. The frozen workflow and actual Preview are preserved in the same Run.
10. A fresh read can locate and verify the exact workflow and its evidence.
11. Historical records and the Task snapshot remain unchanged.
12. The future execution authorization requirement remains explicit.
13. No G5 execution is performed or reported.

Include one direct Codex / DSH agent-facing planning example based on a fully specified synthetic or test-only historical-return request.

Do not claim that deterministic validation tests alone prove general natural-language planning quality. Interactive natural-language acceptance belongs to the final Workbench E2E Goal.

## Scope restrictions

Do not implement:

- G5 execution.
- G6 visualization.
- Authentication.
- Automatic HTTP partitioning or statistical aggregation.
- A new business calculation.
- Long-history market acquisition.
- A generic workflow language or scheduler.
- Changes to Research, Statistics, DataLake or HTTP semantics.

## Delivery

Follow:

Authority Encoding → Implementation → Tests → Reconciliation.

Report:

- Authority files added or changed.
- Exact G4 invocation and agent usage instructions.
- Supported execution surfaces and selection constraints.
- One validated 2010–2026 Preview example.
- One frozen workflow artifact with its identity and SHA-256.
- One failed/blocked planning example.
- Same-Run G1/G3/G4 evidence.
- Executed tests and results.
- Remaining live execution/data-readiness blockers.
- Whether Task version 1 requires an explicitly approved amendment.
- Final commit SHA.

## Success criterion

Codex / DSH can translate an explicitly specified historical-return research objective into a valid capability-composed plan, verify it using the correct public Research Preview surface, and freeze an independently inspectable workflow in the existing Workbench Run, without acquiring market data or executing research.
