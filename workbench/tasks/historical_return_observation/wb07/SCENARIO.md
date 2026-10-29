# WB-07 execution procedure

The [user request](REQUEST.md) commissions this real-market acceptance, including a
narrow Task-local opt-in tool. Existing [Task v1](../ARCHITECTURE.md),
[G4](../WORKFLOW_PLANNING.md), [G5](../AUTHORIZED_EXECUTION.md), Research and DataLake
contracts remain unchanged. This document owns only this acceptance procedure.

One Python plan preserves subject order 000852.SH / 000905.SH / 000300.SH /
000016.SH, H=1/3/5/10, inclusive 2026-01-01..2026-10-29, the explicitly requested
quantiles and interval edges, decimal_ratio and continue. Actual G3 discovery precedes
the newly authored candidate. Public Preview must expand 16 Jobs and 32 analyses.
Metadata is unverified until actual provider-backed public Exports confirm each name
and full code. Neither syntax nor Preview establishes this fact.

## Isolated operational envelope

Reuse LIVE-E2E-01's composition redirection and Repository/SQLite connection checks,
extended only to retain the same external directory across separately authorized Runs.
Every implicit Calendar factory must bind the same Calendar file. No data is copied
from default caches. Default storage is inventoried and hashed before/after; default
compatibility probes use public operations with SQLite read-only connections enforced
and sockets forbidden. Never repair default storage.

Proposed per-G5 limits: 160 provider invocations, 60 calls/minute through the existing
process/credential limiter, 900 seconds wall time, 512 MiB isolated database directory,
256 MiB new Workbench evidence. These are acceptance ceilings, not expected usage or
an account-global quota. No account purchases or credential changes are authorized.
The tool must enforce and test controls before requesting cold authorization. A hard
termination leaves execution uncertain: inspect durable intent/result and audit before
any further action; never retry an existing intent or erase evidence.
Loss of the monitoring or audit facility also terminates execution; it must not leave
acquisition running without enforced controls. A failed audit write cannot prevent exit.

Record initial public Calendar coverage; Index coverage can legitimately fail before
its Calendar prerequisite exists. This is not zero Index units. Research alone performs
its ordinary export/ensure/export preparation. Retain public requests, Ensure counters,
final Exports, provider endpoint counts and input fingerprints. Private imports are
limited to storage configuration and execution auditing, never research facts.

After cold completion, inspect its saved results and public read-only cache exports.
Verify successful-unit reuse separately from any remaining non-success units. A warm
Research invocation needs a new G1/G3/G4 Run, its own exact user approval, and the same
retained storage. No cold intent or authorization is transferable. If complete reuse
cannot safely execute, report service-level evidence and Research-level NOT RUN.

Independent numerical verification consumes saved public Exports: SSE open anchors,
H-position lookbacks, endpoint division/subtraction, E/U/X and fact/observation coverage,
Type 7, all interval bins including tails and full-sample frequencies, input-byte hashes
and associations. Preserve actual missing data and the requested end date.

Deliver separate research/cache/market-completeness/E2E conclusions, 16 actual rows
only when results exist, interval distributions, evidence references and all encountered
problems. No synthetic result may substitute for this acceptance.

The implemented post-cold [saved-result oracle](verify_saved.py) forbids network and
SQLite and verifies immutable public Export payloads independently. The
[public-service reuse audit](verify_cache.py) denies Provider/network access, requires
complete coverage before any Ensure, compares full public Exports to cold evidence,
and verifies zero attempts/writes plus unchanged database bytes/hashes/mtimes.
This audit is not a second Research execution or a new G5 intent. The separately
authorized Warm Research uses the same plan/cache with a proposed Provider ceiling
of zero; any unexpected acquisition need must fail rather than fetch.
