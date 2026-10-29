# Goal: WB-05 — Authorized Research Execution and Evidence Delivery

Repository: `ougachakaaa/hg-market-state-lab`
Working baseline: `develop`
Required predecessor: `495e69893f98e6a6f1b6c5cdd6ed74bd9a7dc039`

## Objective

Implement G5 — Authorized Execution for the approved Workbench Task:

`historical_return_observation`, version `1`.

Allow Codex / DSH to execute the exact frozen and verified G4 Research Workflow through the published Research Python API, preserve actual research results and operational evidence, and report execution status and artifact locations.

Deliver Authority Encoding + Implementation + Tests + Acceptance + Reconciliation.

## Final user objective

The intended final experience is:

A user asks Codex to study the historical N-trading-session trailing cumulative return distribution for an explicitly specified supported index over a period such as 2010–2026.

Codex discovers the published capability, creates and freezes the full-window ResearchPlan, obtains explicit authorization, executes that exact plan and delivers the actual statistical observations with evidence and file locations.

WB-05 implements the execution mechanism and deterministic acceptance. Interactive end-to-end natural-language acceptance and separately authorized full-history live execution remain for WB-06.

## Required authority investigation

Read the relevant Workbench and Historical Return Task authorities, including:

- `workbench/contracts/TASK.md`
- `workbench/contracts/RUN.md`
- `workbench/contracts/GATE.md`
- `workbench/contracts/STORAGE.md`
- `workbench/tasks/historical_return_observation/task.json`
- `workbench/tasks/historical_return_observation/WORKFLOW_PLANNING.md`
- `workbench/tasks/historical_return_observation/PLANNING_ACCEPTANCE.md`

Read the public Research execution, evidence, observation, input preparation and Statistics contracts needed for actual execution.

Use progressive disclosure; do not read unrelated modules by default.

## Ownership

Workbench owns the G5 operational contract, authorization evidence, invocation tracking and output delivery.

Research owns ResearchPlan, execute_batch, observation construction, execution statuses, coverage, provenance and Research evidence.

Statistics owns statistical computation and numerical meaning.

DataLake owns facts, acquisition, caching and storage lifecycle.

Do not move business semantics into Workbench.

Do not introduce a new engine, scheduler, persistent Research registry, provider adapter or statistical implementation.

## G5 prerequisites

G5 requires:

1. An integrity-verified Run of the exact approved Task version.
2. Suitable latest G1 PASS.
3. Explicit Task-authorized G2 SKIPPED.
4. Suitable latest G3 PASS.
5. Exactly one accepted, latest G4 PASS.
6. The exact frozen G4 Workflow and Preview verified through the established read-back contract.
7. Explicit user authorization for actual execution.

Never execute a mutable Candidate, an example fixture or the preliminary manifest.workflow.

Never silently change the frozen ResearchPlan.

## Authorization semantics

The existing frozen Workflow records execution authorization as pending.

G5 must obtain and preserve explicit authorization **before** invoking Research.

Authorization must identify:

- The user-approved research objective.
- The exact frozen Workflow artifact ID.
- Its SHA-256.
- The intended execution surface.
- The potential acquisition, cache writes and paid-data side effects.

The Agent must not grant itself execution permission merely by generating an approval JSON file.

Record the actual user authorization source/reference. If trustworthy authorization cannot be established in the current execution context, return BLOCKED without invoking Research.

Synthetic authorization is permitted only inside explicitly isolated deterministic tests and must not be reusable as live execution authorization.

Do not modify the frozen Workflow to change pending into granted. Store authorization as a separate same-Run record or artifact.

## Execution semantics

Use the published Python ResearchPlan and execute_batch boundary.

Reconstruct the exact validated ResearchPlan from the frozen Workflow using public types.

Verify that reconstructed inputs and public Preview match the frozen G4 evidence.

Invoke execute_batch at most once for the authorized execution attempt.

Before invocation, durably record an execution-start/intent record associated with the exact Workflow and authorization.

After execution, preserve the actual BatchResult and relevant public evidence.

Do not silently:

- Retry uncertain or interrupted executions.
- Split windows.
- Merge independent statistical summaries.
- Truncate requested dates.
- Change H.
- Change statistical parameters.
- Substitute providers.
- Repair or rebuild default caches.
- Modify Research/Statistics calculations.

If process termination or unknown execution outcome prevents confirmation, preserve or report the uncertain state and require explicit operator reconciliation before any further invocation.

Do not infer that an execution failed solely because a caller disconnected.

## Result and evidence contract

Preserve enough actual public output to identify:

- Exact subject, H and requested historical window.
- Actual Job identities and execution outcomes.
- Batch status and success/failed/skipped counts.
- Requested statistical methods and parameters.
- Numeric results and their units.
- Eligible, Unavailable and Excluded populations.
- Relevant observation and market fact coverage.
- Warm-up and overlapping-lookback dependence.
- Actual provenance and source-input fingerprints where published.
- Failure classifications and missing-data limitations.
- Run and artifact identities, hashes and locations.

Use the public owners' result/evidence definitions.

Do not fabricate missing business evidence or serialize arbitrary private exceptions, credentials, internal repositories, provider responses or unsafe object representations.

A transport/runtime invocation completing is not equivalent to a successful Research Batch.

Do not treat a legitimate incomplete Index fact population as fully available. Report actual coverage without silently changing Research's missing-tolerant policy.

The exact meaning of G5 PASS versus a successful invocation containing failed Jobs must be defined explicitly in narrow Task authority and exercised through tests.

## Historical-window requirement

Preserve the complete requested date range, including long windows such as 2010–2026.

The frozen Workflow selects the public Python Research surface rather than HTTP.

Do not apply HTTP-specific 93-day/H20 bounds to that Python execution.

However, legal Preview does not prove live Calendar, Index or provider readiness.

Default WB-05 acceptance must use isolated deterministic public-service fakes and must not acquire paid market data.

Any optional live execution requires separate explicit opt-in, a defined resource budget and safe data/cache isolation. Do not perform a large live backfill automatically.

If full-history live readiness remains unverified, report the limitation for WB-06 rather than claiming success.

## Workbench Run integration

Reuse existing RunStore operations and immutable G4 artifacts.

G5 must append its authorization, execution evidence, actual results and Gate outcome to the same Run.

Read-back must verify:

- Task identity/version.
- Frozen Workflow artifact identity and hash.
- Execution authorization reference.
- Actual execution attempt and result linkage.
- Preserved result integrity.
- Correct Gate outcome.

Do not overwrite prior G1/G3/G4 records.

If a shared Workbench contract gap genuinely prevents safe execution, perform explicit reconciliation before modifying shared code.

## Acceptance

Deterministic acceptance must cover:

1. Missing or failed G4 prevents execution.
2. Altered workflow/hash/Preview prevents execution.
3. Missing or inappropriate authorization prevents execution.
4. Authorized execution uses the exact frozen ResearchPlan.
5. Public execute_batch is invoked exactly once.
6. Actual successful Batch results are preserved faithfully.
7. Failed/partial Batch results preserve failures and coverage without false PASS.
8. Legal partial Index facts are distinguished from full market-data coverage.
9. An exception or uncertain result never triggers an automatic retry.
10. Original G1/G3/G4 evidence remains unchanged.
11. Fresh Run read-back verifies authorization, invocation and output artifacts.
12. Synthetic tests do not access real providers or default user caches.
13. A long-window Plan is not silently partitioned or truncated.
14. No G6 visualization or unrelated business functionality is added.

Use controlled public-service fakes and existing Research acceptance patterns.

Test output preservation without relying on conversation history.

## Scope restrictions

Do not implement:

- G2 authentication.
- G6 visualization.
- New Research formulas or Statistics methods.
- Automatic data backfills unrelated to the authorized Research invocation.
- Default-cache rebuilding.
- Statistical merging across separate plans.
- A new official lab CLI command.
- A generic Agent framework.
- Background jobs, queues, polling or automatic retries.

## Delivery

Follow:

Authority Encoding → Implementation → Tests → Reconciliation.

Report:

- Modified authority and implementation files.
- Exact authorized G5 invocation procedure.
- How the user authorization is established and preserved.
- Exact frozen Workflow consumed.
- One successful deterministic Research execution.
- One failed/partial execution case.
- Actual artifact identities and paths.
- Execution call-count verification.
- Tests and checks actually run.
- Remaining limitations for full-history live execution.
- Whether Task v1 requires any explicitly approved semantic amendment.
- Final commit SHA.

## Success criterion

A Codex / DSH agent can execute an explicitly authorized, frozen G4 Historical Return Workflow through the official Research public Python API, preserve the actual results and evidence in the same Workbench Run, and accurately report the outcome and artifact locations without changing business semantics or inventing missing results.
