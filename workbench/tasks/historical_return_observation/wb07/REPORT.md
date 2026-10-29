# WB-07 real research and cache acceptance report

Updated 2026-10-30 Asia/Shanghai. **Cold real-market research PASS; independent
numerical verification PASS; public-service cache reuse PASS; Warm Research NOT RUN,
awaiting separate exact user authorization.** Full WB-07 E2E remains incomplete until
its independently authorized Warm Research and cold/warm result comparison complete.
The requested sample window remains inclusive 2026-01-01..2026-10-29.

## Actual research findings

The [16-row matrix](MATRIX.md), [complete interval distributions](DISTRIBUTIONS.md)
and [full-precision statistical results](results.json) come from the immutable actual
Research BatchResult, never fixtures. All 16 Jobs and 32 analyses succeeded. Each Job
has 197 samples / Eligible observations, zero Unavailable and zero Excluded, 100%
observation coverage and complete sample/warm-up market fact coverage.

Actual Dataset Exports confirm the four full codes and names: 000852.SH / CSI1000,
000905.SH / CSI500, 000300.SH / CSI300 and 000016.SH / SSE50. Exact provider names,
market, publisher and category are retained in results.json. First candidate anchor
is 2026-01-05; last is 2026-10-29. H=10 requires prices from 2025-12-18; Calendar
backward discovery also retains padding, never a weekday-derived schedule.

Across all four indices, the P5-to-P95 spread is wider at H=10 than at H=1. The
CSI1000/CSI500 spreads are wider than the CSI300/SSE50 spreads at each requested H.
H=10 medians range from -0.5547% (CSI1000) to -0.8747% (CSI300); the matrix provides
all intermediate horizons and quantiles. These are descriptive historical endpoint
returns with overlapping inputs, not annualized returns, forecasts or trading findings.

## Cold acquisition and cache evidence

The real user's exact cold-workflow approval was resolved from their actual chat
reply, preserved separately and validated by the ordinary G5 adapter. Exactly one
execution intent preceded exactly one public execute_batch invocation. Fresh-process
read_execution verifies original authorization/workflow/intent/Batch/report linkage.
The earlier absent-consent BLOCKED outcome remains in history and is not rewritten.

| Cold resource / operation | Actual |
| --- | --- |
| Provider calls | 77: trade_cal 5, index_basic 32, index_daily 40 |
| Wall time / configured rate | 77.846 seconds / 60 calls per minute, process/credential scope |
| Isolated databases | 761,856 bytes total; two Generation 3 owned files |
| New Run evidence through completion | 19,121,216 bytes |
| Immutable BatchResult blob | 19,113,258 bytes |
| Calendar Ensure calls / requested / already successful | 5 / 342 / 14 |
| Calendar attempted / succeeded / failed / records written | 328 / 328 / 0 / 328 |
| Index Ensure calls / requested / already successful | 16 / 3,228 / 2,400 |
| Index attempted / succeeded / failed / records written | 828 / 828 / 0 / 828 |
| Final Index targets by H, per index | H=1: 198; H=3: 200; H=5: 202; H=10: 207; all complete |
| Isolation | All Repository/SQLite bindings guarded; implicit Calendar isolated; default hashes/size/mtime unchanged |

Requested/already-successful totals above sum actual public Ensure calls with overlapping
ranges; unique writes are the attempted/succeeded counts, not 3,228 distinct Index facts.
Both caches persist in the same external directory for Warm Research. No existing
user cache was copied, repaired or migrated. Default Calendar still requires rebuild;
that condition did not block the fresh-isolation route.

After cold completion, 26 distinct actual public requests were independently reread
via coverage/export, compared in full with the saved cold public Exports, then passed
to ordinary Ensure only after complete coverage was established. Provider and sockets
were forbidden throughout: zero Provider calls/attempts, zero attempted units, zero
new records, unchanged exported payloads/metadata and unchanged database bytes,
hashes and mtimes. This proves service-level successful-unit reuse. It does not
substitute for a separately authorized Research-level Warm Run.

## Independent verification and evidence

The saved-result oracle forbids network and SQLite. For each Job it reconstructs SSE
open anchors, exact H-position lookbacks and close(T)/close(T-H)-1 from saved public
Exports, then verifies E/U/X, all fact/observation coverage, positional sample mapping,
Type 7, every interval/tail count and full-sample frequency, conservation, original
request association, retained canonical input bytes and SHA-256. It also compares the
full fingerprint payload to the actual saved public facts. All 16/32 checks pass.

Cold Run: `d95b13c5cb554fab9f19e89cdc3c5b78`. Actual result artifact:
`06f9fc648e16494dbf79ab35585a3a09`; SHA-256:
`e59d737f93212b48b934926b19833b7f2fc832327ee726e434deab2b45d40fb1`.
Local original: `workbench/.runs/d95b13c5cb554fab9f19e89cdc3c5b78/blobs/06f9fc648e16494dbf79ab35585a3a09`.
[Evidence index](evidence.json) records all original artifacts, authorization, cold
operational audit, independent oracle and complete cache-operation evidence references.
Large original blobs and cache files remain outside Git; committed results contain
only public metadata, statistics, coverage, fingerprints and references.

## Separate Warm Research authorization

A new independent Run `7ac42795d02f453496b6cc95fc0ec173` has actual G1/G3 PASS,
G2/G6 SKIPPED and G4 PASS. Its Preview has the identical digest and full 16/32 plan.
Workflow `bde3e79f53824c8896fb0fe4bb1e522a`, SHA-256:
`94e80ee9deba25414d09ab1069f092af54ee513f4bd50f0913f0457515218fa4`.
It has no execution intent or authorization and has not invoked Research.

Warm will reuse the existing cache and enforce **zero Provider calls** with the
existing control wrapper, plus 900 seconds, 512 MiB database storage and 256 MiB new
Run evidence. Storage checks sample every 250ms; an in-flight overshoot remains an
explicit limitation. The generic G5 challenge lists potential acquisition/paid-data
side effects, but this Warm operational ceiling rejects any attempted Provider call.
No cold authorization or intent is transferable. The exact new approval sentence is
in evidence.json at `warm.approval_sentence` and is presented in the chat.

The [acceptance record](ACCEPTANCE.md) and [problem report](PROBLEMS.md) distinguish
completed work from the remaining Warm authorization/execution/comparison. Business,
financial and numerical contracts remain unchanged. The original full Goal continues.
