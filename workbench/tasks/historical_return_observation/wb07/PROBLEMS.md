# WB-07 problem report

Updated 2026-10-30 Asia/Shanghai. Cold real-market execution and independent
verification completed; independently authorized Warm Research and both cache reuse
levels passed. [Evidence](evidence.json) and [acceptance](ACCEPTANCE.md) own actual outcomes.

| ID / stage | Expected vs actual; severity / cause | Actions / status | Impact and next action |
| --- | --- | --- | --- |
| P01 / intake | UTF-8 request initially displayed with garbled console decoding; low, PowerShell default encoding | Reread explicitly as UTF-8; RESOLVED | No interpretation used before corrected read |
| P02 / inspection | `rg` Windows wildcard path was treated literally; low, agent command error | Used exact file paths; RESOLVED | No state changes |
| P03 / tool preflight | Expected public serializer named `public`; actual existing function is `public_value`; low, agent script mistake | Corrected before Source or G5; RESOLVED | First unused empty temporary directory retained; no market facts |
| P04 / tool preflight | Expected SQLite context manager to close connection; actual manager only controls transaction; low, agent script mistake | Explicit `closing()`; RESOLVED | Windows refused deleting empty probe file; no real cache affected; unused probe directory retained |
| P05 / lint | Initial import order and two long lines failed Ruff; low | Fixed, Ruff passes; RESOLVED | No business effect |
| P06 / default readiness | Expected compatible Calendar query; actual public OperationError requires rebuild; high, incompatible persisted generation/shape | Enforced read-only probe and unchanged hashes; WORKAROUND for WB-07 via fresh isolation | Default Calendar remains unchanged; operator must separately decide any rebuild |
| P07 / default readiness | Index coverage unavailable because Calendar prerequisite cannot be read; high, dependency on P06 | Preserved separate failure; WORKAROUND via isolated Calendar | Direct Index generation remains unverified, not reported compatible |
| P08 / fresh cache | Index coverage could not determine target without Calendar; expected prerequisite condition, not production defect | Actual initial failure retained; authorized cold Calendar acquisition enabled complete Index coverage; RESOLVED | Original missing-prerequisite evidence remains; no zero-target invention |
| P09 / cold consent | Exact frozen user approval initially absent; blocking, intentional authorization boundary | Real user supplied exact statement after full challenge; ordinary G5 accepted it and completed once; RESOLVED | Earlier BLOCKED outcome retained; one original cold intent, no retry; no transferable Warm consent |
| P10 / provider | Permissions, metadata and publication completeness initially unknown; high, not probed | Actual authorized Calendar/metadata/daily calls succeeded; four identities and every consumed range verified, including 2026-10-29; RESOLVED for this execution | Does not establish future permissions, freshness or other research windows |
| P11 / operational bounds | Storage watchdog samples at 250ms; medium, process-level observation cannot prevent an in-flight overshoot | Explicit ceiling, hard termination and tests; OPEN limitation | Report sampled enforcement honestly; no claim of filesystem quota or account-global rate limit |
| P12 / evidence projection | Registration helper expected artifact payload but received record envelope; low, agent reporting mistake | Inspected already committed registration; recovered read-only; RESOLVED | No G5 result existed; do not repeat registration or execution |
| P13 / topology check | Two newly linked report files not yet created; low, intermediate authoring state | Completed documents; repeated check passed all 21 cases; RESOLVED | No semantic or runtime failure |
| P14 / regression warning | Starlette/httpx deprecation warning; low, existing dependency behavior | Retained warning; OPEN | No failing Workbench tests; dependency maintenance separate |
| P15 / final evidence check | A scratch verifier omitted UTF-8 on a saved Chinese workflow; low, Windows default GBK decoding | Explicit UTF-8, repeat read-only verification; RESOLVED | No artifacts or execution changed |
| P16 / control review | A monitoring or audit exception could stop the watchdog thread without stopping acquisition; high, discovered by pre-execution code review, not a live incident | Fail closed with process exit even when audit cannot be written; two subprocess fault tests added; RESOLVED | No provider request occurred; durable G5 intent remains the uncertainty anchor if audit storage fails |
| P17 / post-cold inspection | Scratch inspector expected ensure_result on prepared index_slice; actual Ensure is retained in input_attempts; low, agent reporting mistake | KeyError occurred after completed G5; read original saved schema, corrected inspection without execution; RESOLVED | Original result unchanged, no retry or second intent |
| P18 / oracle lint | Two long assertion lines failed Ruff; low, acceptance-script formatting | Split lines; Ruff/mypy pass; RESOLVED | Actual independent oracle had already passed; no business changes |
| P19 / Warm consent | Independent Warm G4 initially lacked its separate real approval; blocking, required boundary | Real user supplied exact new statement; ordinary G5 completed once under zero-Provider ceiling; RESOLVED | Both separate approvals/intents/results retained; all 16 pairs independently verified identical |
| P20 / final reporting | Two documentation patches included nonmatching context lines; low, agent patch error | Tool rejected both patches without modifying any file; used verified context or appended the intended text; RESOLVED | No result or execution changed; no retry |
| P21 / staged whitespace | Final JSON write used Windows CRLF despite the scoped -text byte-preservation policy; low, agent serialization mistake | Staged check rejected CR endings; normalized only committed summary JSON to LF and repeated the check; RESOLVED | Original immutable artifacts and parsed evidence values unchanged; no execution retry |

Cold execution observed no Provider/unit failures or market gaps in the requested
range. All 16 real Jobs and 32 analyses succeeded. Watchdog failures in tests are
deliberate control tests and do not describe live execution. No execution was retried
and no historical evidence was deleted. Warm Research also completed all 16/32,
with zero Provider calls/Ensure/new records and exact Cold input/output equality.
