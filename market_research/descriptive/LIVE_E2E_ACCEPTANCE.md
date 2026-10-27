# LIVE-E2E-01 isolated real-market acceptance evidence

Verdict: **Verified** on 2026-10-27 at 23:29 Asia/Shanghai (15:29 UTC).
This is execution evidence for the existing contracts, not a second business authority.
The [readiness entry](ACCEPTANCE.md) owns current reconciliation. Complete retained public
requests, preliminary/final Exports, EnsureResults, numerical results and audit counters
are in [the machine-readable execution record](LIVE_E2E_RESULT.json).

## Baseline and environment

- Branch: `reset/market-research-descriptive`; initial worktree clean.
- PLAN-HARD-01 baseline: `d92452ecfdcd351c7d267d1de72eecbe534ce013`, the final
  immutable-parameter/preflight hardening commit, directly following required ancestor
  `8c678c93ebf5dc95781d373b6cc413e08c19f31a`.
- Tested SHA: `14775901dc2c2f202d8c0c59795b4b18c27bab3c` (isolated opt-in harness).
  Production Research, DataLake and Statistics code is unchanged from the baseline.
- Windows; root worktree Poetry environment; Python 3.13.11, Poetry 2.2.1, NumPy 2.5.3.
- Existing provider credential resolution succeeded through its authorized fallback.
  No credential value, credential hash or private filesystem path is retained here.

## Isolation and acquisition

The [explicit acceptance harness](../tests/live_e2e_acceptance.py) created one fresh
system temporary directory outside source and default caches. Before any Source call,
it redirected both owning Dataset composition roots to separate SQLite filenames,
verified their paths and the Index service's implicit Calendar dependency, and verified
that ordinary factories created no storage. Repository construction and every SQLite
connection were guarded against escape. New caches used the existing Generation 3
adapter; no old data was copied or migrated. No Research request model was changed.

The audit observed only `tushare_trade_calendar.sqlite3` and
`tushare_index_daily.sqlite3`: 14 and 4 SQLite connections respectively. Default Dataset
storage file sizes/mtime remained unchanged. No default SQLite/WAL/SHM file or `.env`
was written. Temporary databases were disposed after execution; none are committed.
Private composition imports configure/audit storage only; no repository reads, private
Source calls or provider responses supply Research facts.

Acquisition used `data_lake.datasets.tushare_trade_calendar.create_service()` and
`data_lake.datasets.tushare_index_daily.create_service()`, reached by actual
`execute_job()` → Input Preparation. Index's prerequisite used the Calendar public
service in the same isolated storage context. The original public validation remained
enabled throughout.

| Research public request | Initial Export | Ensure | Final Export |
| --- | --- | --- | --- |
| SSE Calendar 2024-01-10..2024-01-16 | 0 success / 7 missing | 7 attempted, 7 succeeded, 7 records; no failures | 7/7 natural days, complete |
| SSE Calendar discovery 2024-01-08..2024-01-09 | 0 success / 2 missing | 2 attempted, 2 succeeded, 2 records; no failures | 2/2 natural days, complete |
| Index 000852.SH 2024-01-08..2024-01-16 | 0 success / 7 missing | 7 attempted, 7 succeeded, 7 records; no failures | 7/7 open-session facts, complete |

All final missing/pending/failed counters are zero. H=2 required just one backward
discovery block; no earlier calendar request or extra historical backfill was needed.
Batch independently prepared its inputs through export-first public operations from
these newly acquired isolated facts; all Exports were complete, so it needed no ensure.
Both Jobs retained their distinct original InputAttempts and PreparedInputs.

Actual Tushare calls: `trade_cal=2`, `index_basic=8`, `index_daily=2`, total 12.
These include Dataset-owned metadata-market selection and pagination/terminal-page
checks, not retries. The existing provider limiter was configured at 180 calls/minute;
the harness imposed a total bound of 24. No alternate provider, uncontrolled retry,
concurrent Source request or permission bypass was used. The successful operations
establish credential/network/capability availability for this bounded run only.

## Verified target and fixed question

Public Index Daily rows, backed by the fresh Dataset's `index_basic` acquisition, agreed
on `index_code=000852.SH`, `symbol=000852`, `name=中证1000`, `market=SSE`,
`publisher=中证指数有限公司`, `category=规模指数`. Identity was checked before accepting
the result. These are the export snapshot's cached instrument metadata acquired during
this run; they are not historical as-of-2024 metadata.

The fixed metric was `trailing_cumulative_return_v1`, explicit parameters `{}`, H=2
trading sessions, inclusive anchor window 2024-01-10..2024-01-16.
Requests were `live_quantiles: QuantileSpec([0.1, 0.5, 0.9])` and
`live_distribution: IntervalCountSpec([-0.2, 0.0, 0.2], "decimal_ratio")`.
The one-subject/one-horizon/one-window ResearchPlan explicitly used `on_job_failure=continue`.

## Independent observation and sample verification

Published open sessions were Jan 8, 9, 10, 11, 12, 15 and 16. Calendar facts marked Jan
13 and 14 closed. The independent oracle used complete Calendar positions, not price-row
positions or weekday inference, and checked every candidate:

| Anchor T | T-H | close(T) | close(T-H) | Binary64 close(T)/close(T-H)-1 |
| --- | --- | --- | --- | --- |
| 2024-01-10 | 2024-01-08 | 5512.0686 | 5543.5745 | -0.005683318588033837 |
| 2024-01-11 | 2024-01-09 | 5611.1149 | 5553.3035 | 0.010410272011965427 |
| 2024-01-12 | 2024-01-10 | 5574.4926 | 5512.0686 | 0.011324967907692551 |
| 2024-01-15 | 2024-01-11 | 5559.376 | 5611.1149 | -0.00922078783309166 |
| 2024-01-16 | 2024-01-12 | 5539.4741 | 5574.4926 | -0.0062819170304395655 |

Counts: `candidate=5 = eligible=5 + unavailable=0 + excluded=0`.
Overall Index fact coverage 7/7; warm-up 2/2; sample 5/5; observation coverage 5/5.
Unavailable and excluded ratios are zero; no missing/invalid endpoints occurred.
Nothing was imputed, filtered, truncated or rounded for computation.

NumericSample contains the five table values exactly once in anchor order, count 5 and
unit `decimal_ratio`. Binary64 coordinates were compared using `float.hex()`. Binding
keys match each originating Eligible observation positionally and retain the actual
ObservationSet object. Deterministic safety/oracle regressions additionally exercise a
synthetic partial population and deliberately incorrect quantiles; these are not live
market evidence and no real-cache gaps were manufactured.

## Independent statistics and association verification

The acceptance oracle uses separate Python calculations, without calling Statistics
compute or NumPy, to check Type 7 operation order and every interval membership.

| Quantile point | Verified value |
| --- | --- |
| 0.1 | -0.008045239512030821 |
| 0.5 | -0.005683318588033837 |
| 0.9 | 0.010959089549401701 |

Estimator: `type7_linear_v1`; count 5; unit `decimal_ratio`.
Interval geometry `[-0.2,0.0)` and `[0.0,0.2]` yielded counts 3 and 2, frequencies 0.6
and 0.4. Underflow/overflow counts and frequencies are all zero; counts conserve 5.
Both the direct Job and Batch Job passed these exact checks.

Each successful ResearchAnalysisEvidence retained the exact original AnalysisRequest,
StatisticalSpec, raw StatisticalResult and shared SampleProjection; the projection
retained its actual originating ObservationSet, fixed Job, original MarketFactCoverage,
typed provenance, PreparedInputs and dependence context. Both ordered outcomes succeeded.
These reference assertions check execution traceability, not cryptographic attestation
of a bare externally supplied statistical result.

Original input profile: `trailing_return_inputs_v2`.
Original fingerprint for both independently prepared Jobs:
`5bbb52782df680da17036420bdee777b9c3febaf19cd08e8f09c383b8ecf2bfc`.
The retained canonical bytes' profile and SHA-256 were verified, without implementing
an alternative input-identity serializer. Existing deterministic identity/golden-byte
tests remain the full [canonical identity contract](cases/trailing_return/INPUT_IDENTITY.md)
conformance checks.

Direct Job: **Success**, two success outcomes, zero failures.
Batch: **success**, `planned=1`, one retained JobResult, `success=1`, `failed=0`,
`skipped=0`, two success analysis outcomes. No inputs/projections were shared implicitly
between Jobs; both used independently created public services over the isolated caches.

## Verification and reconciliation

Commands run from the repository root before changes and after the harness change:

```text
poetry run pytest market_research/tests -q
poetry run pytest market_statistics/tests -q
poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q
poetry run ruff check market_research market_statistics
poetry run mypy market_research/src market_research/tests
poetry run pytest -q
poetry check --lock
git diff --check
```

| Check | Baseline | Final harness |
| --- | --- | --- |
| Research | 800 passed | 804 passed |
| Statistics | 171 passed | 171 passed |
| Authority topology / HTTP architecture | 19 passed | 19 passed |
| Full suite | 2118 passed | 2122 passed |
| Ruff / mypy / Poetry lock / diff whitespace | passed | passed |

The full suite emitted one existing Starlette TestClient/httpx deprecation warning.
The final evidence/navigation changes were also checked with the same command set.
The four new tests check isolation refusal/escape guards and full/partial oracle
behavior without network access. Ordinary pytest does not execute the live script.

Explicit live execution (PowerShell; output contains public evidence only):

```powershell
poetry run python market_research/tests/live_e2e_acceptance.py --live --output "$env:TEMP/live-e2e-01-result.json"
```

Omit `--live` for a no-Source isolation check. A fresh temporary directory is used on
each invocation. A separate inspection of the saved public facts rechecked all five
returns, binding anchors, complete seven-row Export and Batch's absence of ensure;
credential/private-path checks passed before copying the factual record into Git.

No product defect, semantic gap, implementation/authority deviation or new business
decision was found. No production fix or authority relaxation was required. The
historical incompatible **default Calendar cache remains unresolved and untouched**;
its earlier Blocked outcome is preserved in [historical evidence](ACCEPTANCE.md#verification-evidence-2026-10-25).
This Verified result applies to fresh isolated Generation 3 storage and this bounded
scenario, not to default-cache recovery, provider freshness or every historical date.
Persistence, Replay, Cache, CLI, HTTP and new-case work remain outside this Goal.
