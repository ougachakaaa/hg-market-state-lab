# WB-07 acceptance and current reconciliation

Updated 2026-10-30 Asia/Shanghai. Cold executed 2026-10-29 at 23:56 Asia/Shanghai.
Original clean develop baseline: `3edb363160a79e5c832c7da58bda6b4e28b19e54`.
Preparation/consent-blocker commit: `a3ab0b586badee0d2eea71a7d902655de870dbfc`.
[Request](REQUEST.md), [procedure](SCENARIO.md), [research report](REPORT.md),
[matrix](MATRIX.md), [intervals](DISTRIBUTIONS.md), [results](results.json),
[problems](PROBLEMS.md) and [artifact index](evidence.json) separate concerns.

**Cold real-market acceptance PASS. Public-service cache reuse PASS. Warm Research
NOT RUN, awaiting separate actual user approval. Full E2E NOT COMPLETE.**

## Frozen inputs and actual cold execution

Existing Task v1 supports the full Python plan; Task digest remains
`2865ccf73e5736cb00eef383efad0732602e4e848f4b1ec5b53bef55a2b3cb19`.
No Task version, shared recorder, public business model, acquisition semantics,
financial formula or Statistics implementation changed. G1/G3 actual discovery
preceded Agent-authored explicit planning; G4 official pure Preview expanded exactly
16 Jobs / 32 analyses in requested order. The research objective was quoted from the
user's research section, with complete request and every parameter separately retained.

Cold Run: `d95b13c5cb554fab9f19e89cdc3c5b78`; Workflow:
`adcebe33f9b84a33becb16832f7a9ad0`; SHA-256:
`14484338f2073b73b9f19dc9e92a4a9727a91923d1975eb53146708c50733a10`.
The exact real user approval arrived after read-only revalidation and display of the
complete challenge, scope and controls. The trusted host callback resolved that actual
chat reply, never a generated approval file. Ordinary G5 preserved authorization
`7eb599b1dda645c69ec14f78b3b56e0c`, intent sequence 16, actual result
`06f9fc648e16494dbf79ab35585a3a09`, completion sequence 18 and G5 PASS sequence 20.
Exactly one intent and one public execute_batch call; no retry. Earlier absent-consent
BLOCKED evidence remains intact. A fresh process validates all original associations.

Result SHA-256: `e59d737f93212b48b934926b19833b7f2fc832327ee726e434deab2b45d40fb1`,
19,113,258 bytes. Batch success; 16 Success / 0 Failed / 0 Skipped; 32 successful
analyses. Each Job: 197 candidates = 197 Eligible + 0 Unavailable + 0 Excluded.
Calendar/Index facts are complete for every consumed range, including 2026-10-29
and all H-specific warm-up sessions. All four actual code/name metadata pairs match.

## Isolation, cold population and successful-unit reuse

Existing external storage was retained; no default cache was copied, repaired,
migrated or overwritten. Repository construction, every actual SQLite connection
and implicit Calendar dependency stayed inside the isolated bindings. Default
file hashes/size/mtime before and after match. Generation 3 Calendar and Index
files total 761,856 bytes. Default Calendar's read-only rebuild-required failure
and Index prerequisite failure remain separate from isolated execution success.

Actual Provider calls: 77 (trade_cal=5/index_basic=32/index_daily=40), under 160.
Existing rate limiter: 60/minute in this process/credential; not account-global.
Wall time 77.846s under 900s; completion evidence growth 19,121,216 bytes under
256 MiB. Database budget 512 MiB; sampled storage controls can overshoot during an
in-flight write. Monitoring/audit failure terminates the process; uncertainty requires
original intent/result inspection, never automatic retry. No ceiling was reached.

Actual Ensure counters and coverage are preserved in the original public InputAttempts
and [cache audit](evidence.json). Calendar: 328 attempts/successes/new records, zero
failures. Index: 828 attempts/successes/new records, zero failures. Repeated overlapping
Ensure ranges are not counted as distinct market facts. Every Dataset Export and
Ensure retains its actual request and public counters in ignored immutable artifacts.

The explicit public-service reuse audit verified 26 distinct consumed ranges with
coverage/export against the original saved Export. It called Ensure only after
complete coverage, with all Provider/network access denied. Every requested unit was
already successful; attempted/succeeded/failed/new records all zero. Final full Exports
match, metadata match, and both database file bytes/hashes/mtimes are unchanged.
This is real cache reuse evidence, not a second Research Batch or synthetic fixture.

## Independent research verification

Saved public Calendar/Index Export records are the only oracle market facts. The
verification process forbids network/SQLite and does not invoke Research, Statistics
compute or provider methods. It independently checks every anchor/H lookback/return,
E/U/X and coverage, sample ordering, Type 7, every interval/tail and denominator,
count conservation, association references, retained input SHA-256 and complete
canonical fingerprint payload against exported facts. All 16 Jobs / 32 analyses pass.
Original BatchResult remains unchanged and can be reread from its immutable artifact.

## Acceptance items and remaining work

| Item | Verified disposition |
| --- | --- |
| A actual full matrix | PASS cold: 16 Jobs / 32 successful analyses, exact identities |
| B real facts/metadata | PASS cold: actual Dataset Exports and four matching metadata identities |
| C independent correctness | PASS cold: saved public Export oracles, no network/SQLite |
| D cache population | PASS cold: original Ensure/Export evidence and guarded SQLite writes |
| E cache reuse | PASS public-service level; Research-level Warm NOT RUN |
| F isolation | PASS cold and service reuse; default contents unchanged |
| G original evidence | PASS cold: real approval/intent/result/audits, immutable digests verified |
| H problem reporting | PASS for encountered issues; limitations and Warm pending status explicit |

New Warm Run: `7ac42795d02f453496b6cc95fc0ec173`; Workflow:
`bde3e79f53824c8896fb0fe4bb1e522a`; SHA-256:
`94e80ee9deba25414d09ab1069f092af54ee513f4bd50f0913f0457515218fa4`.
Actual G1/G3/G4 PASS; G2/G6 exact SKIPPED reasons. Same entire plan, same Preview
hash, same retained cache. No Warm authorization/intent/invocation. Propose zero
Provider calls (enforced rejection of any need), 900s, 512 MiB databases and 256 MiB
new evidence, same sampled-storage limitation. Separate real exact user approval is
required before that new G5. After execution, compare actual observations, statistics,
fingerprints, Export payloads, Ensure counters, Provider count and cache file invariance.

## Commands and checks

All commands ran from repository-root Poetry. Prior preparation: 261 Workbench tests
passed; focused controls later expanded to seven and passed, including lost monitoring
and audit subprocess tests. Ruff, mypy, storage acceptance and 21 topology/HTTP checks
passed. Original preflight hash and absent-consent evidence remain in evidence.json.

This continuation used the actual chat-resolving host callback once with the existing
`acceptance_tool.execute`, then fresh `read_execution`; no execution override or new
business seam was installed. Additional actual commands:

```powershell
poetry run python workbench/tasks/historical_return_observation/wb07/verify_saved.py --run d95b13c5cb554fab9f19e89cdc3c5b78 --output workbench/.runs/wb07-cold-verified.json
poetry run python workbench/tasks/historical_return_observation/wb07/verify_cache.py --run d95b13c5cb554fab9f19e89cdc3c5b78 --output workbench/.runs/wb07-cache-verified.json
poetry run python ui_http/scripts/api.py --host 127.0.0.1 --port 18071
poetry run ruff check workbench
poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation
poetry run pytest workbench/tests -q
```

Continuation checks: 263 Workbench tests passed in 99.94s with the same existing
Starlette warning; 21 topology/HTTP checks passed in 14.33s; Ruff passed; mypy
passed for 11 source files. The Warm zero-Provider ceiling was separately exercised
with a forbidden delegate: it rejected before delegation, with zero Provider calls.
Original intent/result hashes, full-precision committed statistics and the same
eligible Warm Workflow are reverified before presenting its authorization challenge.

Warm G1/G3/G4 used existing record_g1.py, record_g3.py and record_g4.py with the same
candidate, actual newly launched backend and the new Run above. Existing cold Gates
were read, never replanned or repeated. Both pure Preview and G4 evidence remain
unchanged. Verification/reporting code is Task-local acceptance tooling, not new
Workbench or business functionality.
