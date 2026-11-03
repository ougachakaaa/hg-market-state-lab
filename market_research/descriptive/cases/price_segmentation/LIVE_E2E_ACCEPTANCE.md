# Price Segmentation V1 isolated real-market acceptance

Verdict: **PASS**, 2026-10-31 19:27 Asia/Shanghai. This is bounded execution evidence,
not business authority. The full machine-readable execution record is retained outside the repository; the
summary and bounded verification below are historical evidence.

## Execution and isolation

Baseline HEAD was `b825cd81ec9e3348fb1139552bdb8dcb2d42795f`; the live run used a dirty
working tree containing the G4 numerical/type fix and acceptance harness. At execution,
Git blob hashes were `c09696f4a6c165055750a1769fc99f0f674b4c05` for `construction.py`
and `c6c16457b32c0c2df5caf081aefaa7be1b29e391` for the live harness. The final commit
containing them follows this baseline. Windows, Python 3.13.11, Poetry 2.2.1, root `.venv`.

Command from repository root:

```powershell
poetry run python market_research/tests/segmentation_live_e2e.py --live --long --output "$env:TEMP/segmentation-live-g4-final.json"
```

Before Source access, the existing isolated-storage gate established separate fresh
system-temporary Calendar and Index SQLite paths, including Index's implicit Calendar.
It guarded Repository construction and every SQLite connection against escape, and checked
that factories created no storage. Only the two isolated SQLite filenames were materialized;
18 Calendar and 12 Index connections were observed. Default Dataset file size/mtime metadata
was unchanged. No default database was opened, modified, migrated or repaired; the historical
Calendar cache limitation remains. Temporary storage was disposed. Credential resolution used
existing configuration; no credential is recorded.

The actual chain was `observe_price_segments` → public Calendar/Index Export → Ensure when
incomplete → final Export → PIP → construction. The same limiter remained enabled at the
configured 180 calls/minute. Short/long scenarios had budgets of 24 Source calls each;
actual counts were 11 and 3 respectively in the final execution (`trade_cal=2`, `index_basic=8`, `index_daily=4`
total). Repeating each request made zero Source calls. No retry or alternate Source was used.
A prior identical isolated run produced the same fingerprints, points, segments and diagnostics;
the final run retained the full public input evidence for review. Public Index Daily metadata identified `000852.SH`, symbol `000852`, name 中证1000,
market SSE, publisher 中证指数有限公司 and category 规模指数. This is acquired metadata,
not a claim about metadata historical as of 2024.

## Results

| Scope (inclusive) | epsilon | Calendar complete | Index complete | Points | Segments | Maximum log error | Fingerprint |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| 2024-01-08–2024-01-16 | 0.005 | 9/9 natural days | 7/7 sessions | 4 | 3 | 0.004603231652222206 | `64b2b9cc9ab212442a248cedd1188c3ba0b372f2404674ba7b7baf09bbc49103` |
| 2024-01-08–2024-02-29 | 0.01 | 53/53 natural days | 33/33 sessions | 21 | 20 | 0.0087081168442662 | `bfc446b97e0422c276920605049651cacb311cf523ec2aa39916b53b3c195095` |

Short-scope important points `(index, date, close)` are `(0, 2024-01-08, 5543.5745)`,
`(2, 2024-01-10, 5512.0686)`, `(3, 2024-01-11, 5611.1149)`, and
`(6, 2024-01-16, 5539.4741)`. Complete short-scope segments:

| Start | End | Session intervals | Signed amplitude | Direction | Boundary |
| --- | --- | ---: | ---: | --- | --- |
| 2024-01-08 | 2024-01-10 | 2 | -0.005683318588033837 | down | start |
| 2024-01-10 | 2024-01-11 | 1 | 0.017968988992626 | up | neither |
| 2024-01-11 | 2024-01-16 | 3 | -0.01276765870540264 | down | end |

The separate oracle checked every calendar date and SSE open session against final public
exports, metadata and positive finite closes, natural logs and an independently serialized
canonical SHA-256 fingerprint. It checked every original point, segment identity, endpoint,
duration, return, direction, boundary flag, count and coverage, then reconstructed each
piece in the specified binary64 order. Actual maximum error exactly equalled diagnostics
and was below epsilon in each scope. Repeated complete calls preserved request, fingerprint,
points, segments and diagnostics. The longer scope includes consecutive same-direction
segments. Deterministic tests cover flat segments and deliberately corrupted results.

## Verification and limitations

```text
poetry run pytest market_research/tests                                      988 passed
poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py    21 passed
poetry run ruff check market_research                                         passed
poetry run mypy market_research/tests                                            passed
poetry run mypy market_research/src/market_research/descriptive/cases/price_segmentation market_research/tests    passed
git diff --check                                                               passed
```

The live harness is explicit and is never invoked by default pytest. This proves the two
specified bounded scopes in fresh isolated storage, not provider freshness, arbitrary
history or readiness of the user's default cache. Segmentation Statistics, Converter,
ResearchPlan, Capability Publication, HTTP and Workbench integrations remain out of scope.
