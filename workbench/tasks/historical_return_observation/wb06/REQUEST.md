# Goal: WB-06 — Natural Language Historical Research E2E Acceptance

Repository: `ougachakaaa/hg-market-state-lab`
Working baseline: `develop`
Required predecessor: `2611c18e21208282f3b7da130e67160998816509`

## Objective

Complete the end-to-end acceptance of the existing `historical_return_observation` Workbench Task.

The primary goal is to prove that a user can directly communicate a historical return research objective to Codex / DSH and obtain a trustworthy, traceable result using the existing Market State Lab capabilities.

Deliver:

- Natural-language-to-Workflow acceptance.
- G1/G3/G4/G5 integration verification.
- Actual Research/Statistics result inspection.
- Complete Run evidence and artifact references.
- A human-readable research report.
- An explicit record of problems encountered and their disposition.
- Final authority/implementation reconciliation.

Do not create a new Agent framework or change financial calculation semantics.

## Final user objective

The desired user interaction is:

"Analyze the historical N-trading-session cumulative return distribution for my specified supported index over 2010–2026. Use the existing Research capabilities, give me the statistical observations, report data coverage and limitations, and show me where the results are stored."

The user should not need to manually construct ResearchPlan JSON, invoke internal APIs, or understand implementation details.

Codex must interpret the request, resolve missing parameters with the user, and produce the valid candidate workflow itself.

The user remains responsible for research intent and actual execution authorization.

## Required preparation

Read the repository's stable agent entry and only the relevant Workbench/Research contracts.

In particular:

- The approved Historical Return Task v1.
- G1 Backend Ready.
- G3 Capability Discovery.
- G4 Workflow Planning.
- G5 Authorized Execution.
- WB-05R reconciliation.
- Current Research and Statistics public contracts.
- Existing isolated real-market E2E acceptance and its known cache limitations.

Inspect the actual implementation and tests before executing.

Confirm the repository checkout and exact baseline. Do not silently run against a different Task version or branch.

## Phase A — Natural-language E2E acceptance

Use a genuinely Agent-composed planning workflow rather than copying a prebuilt Candidate as the main acceptance result.

A fully specified synthetic acceptance request may be used to test the planning path, for example:

"Study the 10-trading-session trailing cumulative returns of index 000852.SH for inclusive dates 2010-01-01 through 2026-10-28. Compute quantiles at 0.1, 0.5 and 0.9, and interval counts with decimal_ratio edges [-0.15, -0.05, 0, 0.05, 0.15]. Use trailing_cumulative_return_v1, empty metric parameters and continue-on-failure policy. Preserve all results and limitations."

These values are explicit test inputs, not defaults for future users and not authorization for live acquisition.

Codex must:

1. Interpret the request independently.
2. Identify the approved Task.
3. Establish G1 through the official checker.
4. Discover the actual G3 capability catalog.
5. Use the discovered descriptor to compose the complete ResearchPlan.
6. Validate the plan using public Research Preview.
7. Freeze and independently read back the G4 Workflow.
8. Demonstrate the authorized G5 path under deterministic isolated testing.
9. Retrieve the resulting Run and inspect the real Research/Statistics output produced against controlled service fixtures.

Compare the Agent-composed plan with the original research request and record any interpretation mistakes.

Do not treat copying an existing JSON fixture as proof of natural-language planning.

## Phase B — Real-market execution readiness

The user ultimately wants a complete historical research interval such as 2010–2026.

Investigate whether actual live execution can be performed safely using existing owner-approved mechanisms.

Verify, before any live invocation:

- The selected index is supported and its canonical identity is correct.
- The entire requested date range and H-session warm-up are preserved.
- Provider permissions and data-access prerequisites are available.
- Data/cache isolation is actually configured and verified.
- Default user caches remain protected.
- A bounded acquisition/cost/resource budget is technically or operationally verifiable.
- The expected result size and execution implications are understood.
- No existing execution intent creates a duplicate-execution risk.

Use the previous isolated Research LIVE-E2E acceptance as reference for already established safety mechanisms.

Do not assume those mechanisms automatically scale to a 2010–2026 backfill.

Do not repair or migrate default Calendar/Index caches as part of Workbench acceptance.

If resource or isolation constraints cannot be verified, mark live readiness BLOCKED, preserve the evidence and clearly state the missing condition.

Do not fabricate a complete live result.

## Phase C — Authorization and optional live execution

Actual paid-data acquisition or cache mutation requires a new explicit user authorization for the exact frozen Workflow ID and SHA-256.

The WB-06 Goal request itself is not live execution authorization.

Do not generate user consent in Agent-authored JSON or synthesize a trusted-host callback.

If trustworthy consent cannot be established, stop at the authorization boundary and report BLOCKED.

When both operational controls and genuine authorization are available, run only the approved full-window workflow through the official G5 public execution path.

Invoke the frozen ResearchPlan once.

No automatic retries, silent partitioning, statistical merging, data truncation or provider fallback.

If actual full-history execution would exceed the verified budget, do not substitute a shorter window and claim the original goal succeeded.

A separately approved bounded live smoke may be performed as an additional diagnostic, but it must be identified as a smaller test, not evidence of full-history completion.

## Phase D — Research output inspection

For every completed execution, report:

- Exact index identity.
- Full requested historical window.
- Horizon in trading sessions.
- Research metric and formula.
- Statistical methods and their parameters.
- Actual quantile values and interval counts/frequencies.
- Batch, Job and analysis statuses.
- Eligible, Unavailable and Excluded populations.
- Observation and market-fact coverage.
- Warm-up and dependence limitations.
- Relevant Research provenance and input fingerprint.
- Exact Run ID, Workflow ID/hash and result artifact locations.

Use actual saved Research outputs.

Do not invent statistical results, infer missing values or report a synthetic fixture as real historical market evidence.

Clearly distinguish:

1. Workflow validation success.
2. Research computation success.
3. Completeness of market data.
4. Full historical objective acceptance.

These are not equivalent.

## Phase E — Problem Reporting (mandatory)

Evidence preservation alone is not sufficient.

Create a dedicated problem report in the WB-06 acceptance artifacts, and summarize its findings in the final human-facing report.

For every encountered problem, record:

- Problem ID.
- Stage or Gate.
- Expected behavior.
- Actual observed behavior.
- Severity and effect on the research objective.
- Evidence location (log, command result, artifact or test).
- Root cause, or explicitly "unknown" if unconfirmed.
- Actions taken.
- Whether the problem is RESOLVED, WORKAROUND, OPEN or BLOCKED.
- Remaining risk.
- Recommended owner and next action when unresolved.

Include problems that were eventually resolved. Do not report only the final errors.

Also record nonfatal warnings, unexpected assumptions, resource/isolation limitations, partial-market-data observations and limitations of the acceptance environment.

Do not classify an expected test-injected failure as a production defect.

Do not hide a genuine failed check inside a final PASS summary.

If no problems are encountered, explicitly record that no problems were observed and state the verification scope.

## Phase F — Human-readable final research report

Produce a concise report that answers:

1. What did the user ask?
2. What did Codex understand and plan?
3. Which Market State Lab capabilities were used?
4. What operations actually ran?
5. What statistical results were produced?
6. What was the data coverage and what are its limitations?
7. What problems were encountered, and how were they handled?
8. Which requirements remain unverified or BLOCKED?
9. Where are the exact original results and evidence?
10. Can the user repeat the same type of request without manually constructing a plan?

Do not merely print RunStore JSON.

The report must communicate the research result and the execution history in ordinary language while remaining traceable to original structured artifacts.

## Artifacts

Follow the existing Workbench Storage contract.

Persist the appropriate Run evidence and produce Task-local E2E acceptance documentation.

Include a machine-readable problem log and a human-readable report.

Prefer separate acceptance concerns, for example:

- E2E acceptance record.
- Problem/issue log.
- Research result summary.
- References to original immutable Run artifacts.

Do not create new Workbench Gates.

Do not put new business semantics into general Workbench authority.

Do not commit provider credentials, private file paths, paid-data responses outside published public evidence, or local ignored Run storage.

## Acceptance criteria

A. G1, G3, G4 and G5 can be exercised through the approved Task's existing interfaces.

B. G2/G6 remain explicitly SKIPPED under current MVP policy.

C. Codex can generate a faithful plan from natural-language instructions.

D. The resulting workflow preserves the complete explicit date range, horizon and statistical parameters.

E. Public Preview agrees with the frozen workflow.

F. G5 executes precisely the authorized frozen workflow; deterministic fixture execution requires no market-provider access.

G. Saved output contains actual public Research and Statistics results, not Agent-generated substitutes.

H. Read-back verifies stored evidence and historical results independently.

I. A completed Run remains readable after later operational Gate failures.

J. Live data access is never attempted without genuine authorization and verified operational conditions.

K. Every encountered problem has an explicit recorded disposition.

L. The final report explains both statistical results and unresolved limitations.

M. Synthetic acceptance is never described as successful live 2010–2026 research.

N. Existing Workbench and business regression suites remain passing.

## Scope limits

Do not implement authentication or visualization.

Do not change the Research return formula, Statistics implementation, DataLake ownership or published capability semantics.

Do not add a generic Agent orchestrator, new database, scheduler, provider abstraction or Workbench framework.

Do not perform unrestricted historical backfills or automatic cache repairs.

If the E2E reveals a genuine semantic gap, record it, identify the owning authority and recommend a separate follow-up Goal rather than inventing an ad hoc implementation.

## Final reconciliation

Perform:

E2E Scenario → Evidence Collection → Problem Analysis → Acceptance → Reconciliation.

Compare the final result against Task v1 and the published Research/Statistics contracts.

Distinguish:

- Verified and complete.
- Verified but data-incomplete.
- Failed.
- Blocked by authorization or environment.
- Not executed.

Do not label WB-06 complete unless the explicitly declared acceptance scope actually passed.

If deterministic E2E passes but live full-history acceptance is blocked, report those as separate conclusions.

## Delivery

Provide:

- Final commit SHA and changed files.
- Actual commands/tests and results.
- One natural-language-to-frozen-workflow acceptance example.
- One complete deterministic E2E Run with results.
- Live-readiness findings and actual authorization status.
- Statistical output summary and artifact paths.
- Full Problem Report with resolved and unresolved issues.
- Authority/implementation reconciliation findings.
- Exact remaining work, if any, to satisfy the 2010–2026 live-history objective.

## Success criterion

Codex can accept a natural-language Historical Return Observation Task request, use Market State Lab's approved capabilities and Workbench contracts to create and execute a verified workflow, deliver traceable statistical observations, and accurately report both the research findings and encountered problems.

Actual full-history live completion may be claimed only when separately authorized and supported by real execution evidence.
