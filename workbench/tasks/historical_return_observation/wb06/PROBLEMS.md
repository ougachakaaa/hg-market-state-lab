# WB-06 problem report

The complete per-problem expected/actual behavior, impact, evidence, cause, actions,
disposition, remaining risk, owner and next action are in [problems.json](problems.json).
Observed command diagnostic excerpts are preserved in [tooling_failures.json](tooling_failures.json).
The [research report](REPORT.md) summarizes the consequences. No failed check is
reclassified as PASS merely because later acceptance succeeds.

| ID | Problem / observed condition | Disposition |
| --- | --- | --- |
| P01 | Initial console decoding garbled UTF-8 text | RESOLVED: explicit UTF-8 reads |
| P02 | Root .gitattributes probe failed; existing policy was narrower | RESOLVED: located existing file; added scoped snapshot policy |
| P03 | Harness context-manager TypeError and one Ruff E501 | RESOLVED before G5 invocation; frozen workflow retained |
| P04 | Harness read status at wrong result-envelope level after successful computation | RESOLVED; original completed Run recovered read-only |
| P05 | Oracle adapter used wrong window field after successful computation | RESOLVED; original completed Run recovered read-only |
| P06 | Partial fixture supplied invalid whole-range Ensure counters | RESOLVED; public validator correctly rejected it; fake accounting corrected |
| P07 | Inline PowerShell/Python credential probe quoting failed | RESOLVED with ignored local script and secret-safe boolean output |
| P08 | HTTP 93-day limit cannot carry requested 6,145-day interval | WORKAROUND: complete public Python workflow, no split/merge |
| P09 | Artificial calendar/prices; deliberate partial fixture has two unavailable anchors | OPEN environment limitation; not historical market evidence |
| P10 | Later G3 FAIL intentionally injected after completed G5 | RESOLVED expected test condition; historical result intact, current eligibility revoked |
| P11 | Prior 24-call smoke does not verify a full-history budget/control envelope | BLOCKED; DataLake/provider operator must verify exact operational bounds |
| P12 | No genuine consent for any live Workflow ID/hash | BLOCKED; actual user approval required after controls are verified |
| P13 | Current provider permissions/membership/history not probed | BLOCKED; credential presence and historical identity evidence are insufficient |
| P14 | Historical incompatible default Calendar cache remains outside scope | OPEN; no default database opened/repaired/migrated |
| P15 | Existing Starlette TestClient/httpx deprecation warning | OPEN, nonfatal dependency maintenance issue |
| P16 | Draft report contained a mistyped partial-workflow artifact ID | RESOLVED during review against saved structured reference |
| P17 | Initial staged whitespace check failed on two original pasted Markdown lines | RESOLVED: normalized trailing spaces, documented it and repeated the check; ordinary Git CRLF notices do not affect JSON snapshot hashes |

P03-P07 are Agent-authored acceptance tooling mistakes, not production Research,
Statistics or Workbench defects. Two retained computations finished before reporting
errors; [development_runs.json](development_runs.json) preserves both original
Workflow/result references. Each has exactly one invocation and an output identical
to the final complete fixture. Neither was retried or overwritten. The initial P03
failure had no execution intent; it was safe to continue that frozen Run once.
Failed pytest fixture work used temporary storage and never reached a provider.

P09's missing row and P10's Gate failure are explicitly injected. Neither is labeled
a production defect. Missing-data computation success remains data-incomplete. The
separate absent-consent BLOCKED check is the expected safe behavior, not a defect.

No production semantic gap was found. P11-P14 require operator/user action or a narrow
follow-up Goal, not an ad hoc Agent framework, cache repair or calculation change.
