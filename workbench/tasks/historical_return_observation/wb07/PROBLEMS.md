# WB-07 problem report

Date: 2026-10-29 Asia/Shanghai. Current stage: pre-execution; no market call or G5
intent. [Evidence](evidence.json) and [acceptance](ACCEPTANCE.md) own actual outcomes.

| ID / stage | Expected vs actual; severity / cause | Actions / status | Impact and next action |
| --- | --- | --- | --- |
| P01 / intake | UTF-8 request initially displayed with garbled console decoding; low, PowerShell default encoding | Reread explicitly as UTF-8; RESOLVED | No interpretation used before corrected read |
| P02 / inspection | `rg` Windows wildcard path was treated literally; low, agent command error | Used exact file paths; RESOLVED | No state changes |
| P03 / tool preflight | Expected public serializer named `public`; actual existing function is `public_value`; low, agent script mistake | Corrected before Source or G5; RESOLVED | First unused empty temporary directory retained; no market facts |
| P04 / tool preflight | Expected SQLite context manager to close connection; actual manager only controls transaction; low, agent script mistake | Explicit `closing()`; RESOLVED | Windows refused deleting empty probe file; no real cache affected; unused probe directory retained |
| P05 / lint | Initial import order and two long lines failed Ruff; low | Fixed, Ruff passes; RESOLVED | No business effect |
| P06 / default readiness | Expected compatible Calendar query; actual public OperationError requires rebuild; high, incompatible persisted generation/shape | Enforced read-only probe and unchanged hashes; WORKAROUND for WB-07 via fresh isolation | Default Calendar remains unchanged; operator must separately decide any rebuild |
| P07 / default readiness | Index coverage unavailable because Calendar prerequisite cannot be read; high, dependency on P06 | Preserved separate failure; WORKAROUND via isolated Calendar | Direct Index generation remains unverified, not reported compatible |
| P08 / fresh cache | Index coverage cannot determine target without Calendar; expected prerequisite condition, not production defect | Actual public coverage attempted, OperationError retained; OPEN until authorized acquisition | Never report zero target units; recheck after Calendar acquired |
| P09 / consent | Exact frozen user approval absent; blocking, intentional authorization boundary | Ordinary G5 returned BLOCKED; zero intents and provider calls; BLOCKED | Obtain genuine exact cold-workflow consent; warm requires another approval |
| P10 / provider | Credential resolves but permissions, current metadata and publication completeness unknown; high, not probed | No live call before consent; OPEN | Validate through authorized Dataset Ensure/Export; retain missing 2026-10-29 facts |
| P11 / operational bounds | Storage watchdog samples at 250ms; medium, process-level observation cannot prevent an in-flight overshoot | Explicit ceiling, hard termination and tests; OPEN limitation | Report sampled enforcement honestly; no claim of filesystem quota or account-global rate limit |
| P12 / evidence projection | Registration helper expected artifact payload but received record envelope; low, agent reporting mistake | Inspected already committed registration; recovered read-only; RESOLVED | No G5 result existed; do not repeat registration or execution |
| P13 / topology check | Two newly linked report files not yet created; low, intermediate authoring state | Completed documents; repeated check passed all 21 cases; RESOLVED | No semantic or runtime failure |
| P14 / regression warning | Starlette/httpx deprecation warning; low, existing dependency behavior | Retained warning; OPEN | No failing Workbench tests; dependency maintenance separate |
| P15 / final evidence check | A scratch verifier omitted UTF-8 on a saved Chinese workflow; low, Windows default GBK decoding | Explicit UTF-8, repeat read-only verification; RESOLVED | No artifacts or execution changed |
| P16 / control review | A monitoring or audit exception could stop the watchdog thread without stopping acquisition; high, discovered by pre-execution code review, not a live incident | Fail closed with process exit even when audit cannot be written; two subprocess fault tests added; RESOLVED | No provider request occurred; durable G5 intent remains the uncertainty anchor if audit storage fails |

There were no production provider failures, market gaps or research results observed
yet. Watchdog failures in tests are deliberate control tests and do not describe live
execution. No execution was retried and no historical evidence was deleted.
