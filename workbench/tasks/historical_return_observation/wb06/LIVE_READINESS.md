# WB-06 full-history live readiness

Verdict: **BLOCKED / NOT EXECUTED**, 2026-10-29 Asia/Shanghai. No live request,
provider call, paid acquisition, default-cache mutation, repair or migration occurred.
The [Goal](REQUEST.md) explicitly withholds live authorization. Deterministic fixture
approval and the adapter field `execution_context=live` do not represent real consent.

| Condition | Evidence and disposition |
| --- | --- |
| Supported identity | Actual backend G3 publishes the implemented index case and `000852.SH` / CSI1000 example. Prior [published live evidence](../../../../market_research/descriptive/LIVE_E2E_ACCEPTANCE.md) verified provider metadata for 中证1000. Current membership/metadata is **not reverified** with the provider. Syntax alone is insufficient. |
| Full window and warm-up | Candidate, Preview, Workflow and result preserve inclusive 2010-01-01..2026-10-28 and H=10. Fixture calendar discovery requests 2009-12-22..31 then 2009-12-02..21; exact fixture Index span is 2009-12-18..2026-10-28. Actual earliest session/warm-up must be resolved by complete SSE Calendar, never weekday inference. |
| Public execution surface | Python `ResearchPlan` / `preview_plan` / `execute_batch`, one Job and two required analyses. No HTTP POST, 93-day truncation, partition, merge or provider fallback. |
| Credential availability | [Current secret-safe probe](prerequisites.json): credential resolution succeeds without network. No credential value/hash is retained. Availability is not entitlement. |
| Provider permissions | Current trade_cal, index_basic, index_daily permissions, quota and history availability **unverified**. Prior short live success is historical evidence only. |
| Isolation mechanism | [No-Source probe](isolation.json) verifies the existing owner-approved fresh external temporary directory, separate Generation 3 paths and Index's implicit Calendar dependency; factories create no storage. No SQLite connection or Source call occurred; default cache size/mtime remained unchanged. |
| Exact full-workflow isolation | The existing live harness is hardcoded to H=2, 2024-01-10..16 and calls direct Job then Batch. It is **not** an executable full-window G5 wrapper. Its no-Source factory binding is reusable evidence, not proof of guarded full-window invocation. |
| Budget/control envelope | Existing short harness caps TushareExecutor calls at 24; provider rate limiting alone is not a total budget or cross-process quota. G5 budget/isolation strings enforce no controls. A finite full-window call/cost/wall-time/disk envelope is **not established**. |
| Output/resource implications | Requested sample interval contains 6,145 natural dates. At most one anchor per date plus H preceding sessions; actual count requires Calendar. Dense fixture produced 4,389 anchors, 4,399 Index rows and a 23,478,144-byte saved result, plus other artifacts. JSON retention repeats some public context; simultaneous projection/read-back needs additional memory. This measurement is not an actual market-resource bound. |
| Duplicate execution | No-consent Run `407cf8e7450e43afb059077c64ab4b08` has zero intents and zero invocations. Completed synthetic Runs each have one intent and are never reused for execution. Two earlier reporting-failure Runs were recovered read-only; see [development evidence](development_runs.json). |
| Genuine authorization | **Absent**. The no-consent G5 check returns BLOCKED before intent. No Agent-created approval grants permission. |

Source inspection explains why the prior 24-call smoke cannot simply be scaled:
Calendar batches by year; Index groups by index/year and at most 250 units per batch.
Index pagination asks for up to 4,000 rows per page and requires an empty terminal page,
even after a short page; it has a 10,000-page guard. Metadata also paginates. These are
algorithm limits, not an approved affordable full-history budget. Real session counts,
cached metadata, publication gaps and provider behavior affect work. No precise live
call count/cost is asserted. The [provider authority](../../../../data_lake/providers/tushare/ARCHITECTURE.md)
and Dataset contracts retain ownership; Workbench adds no limiter or acquisition policy.

The previously reported incompatible default Calendar cache remains a historical OPEN
problem; its present generation was deliberately not probed. No default cache needs to
be repaired for the verified fresh-isolation route, and WB-06 does not authorize repair.

Exact remaining work for actual 2010-2026 acceptance:

1. Establish real user intent for this index/H/window/analyses and compose a fresh
   real-intent G4 workflow. The saved candidate is a synthetic acceptance example;
   no test approval or completed Run can become reusable live permission.
2. With DataLake/provider ownership, verify a finite budget and actual isolation around
   **one official G5 call** of that exact frozen plan. Reuse existing owner-approved
   mechanisms only within verified limits; the hardcoded live smoke is not this wrapper.
   If a new bounded operational harness is necessary, commission a narrow follow-up
   rather than adding a framework or bypassing public execution.
3. Verify current identity/permissions and actual calendar/history prerequisites inside
   the approved operational envelope. Do not shorten dates based on index list_date,
   manufacture missing facts or treat missing early history as zero return.
4. Present the real frozen Workflow artifact ID and SHA-256, objective, surface, side
   effects and verified controls to the user. Obtain genuine verbatim approval through
   the trusted session/terminal. The pending no-consent example has Workflow ID
   `a4423d4c94f84cb6ba7975e8827a4c8f`, hash
   `d8e7f97ea4cfb71bce93c322aae0a7f06076805b4677f42e3af65846eb333f47`;
   it has no permission and is not offered as a ready live workflow.
5. Execute the authorized full plan once, preserve its original Run outputs, inspect
   actual E/U/X, market/observation/warm-up coverage, all statistics and provenance.
   No automatic retries, alternate provider, silent partition/merge or shortened test
   may substitute for full-history acceptance. Classify data-incomplete computation
   separately from complete market coverage.
