# WB-06 acceptance and final reconciliation

Date: 2026-10-29 Asia/Shanghai. Baseline: clean `develop` at the exact required
predecessor `2611c18e21208282f3b7da130e67160998816509`. Root Poetry environment,
Python 3.13.11. The [original request](REQUEST.md), with trailing whitespace normalized,
authorizes this acceptance and
delivery commit, not live acquisition. [Scenario/procedure](SCENARIO.md),
[human report](REPORT.md), [problems](PROBLEMS.md) and
[live readiness](LIVE_READINESS.md) separate independently consumable concerns.

**Declared deterministic E2E scope: VERIFIED AND COMPLETE. Full-history live objective:
BLOCKED / NOT EXECUTED. WB-06 is not a successful live 2010-2026 research acceptance.**

The Agent read root/module entries, Task v1 and G1/G3/G4/G5 contracts, WB-05R,
Research capability/Plan/Job/input/identity and Statistics method contracts, existing
implementation/tests and prior isolated real-market acceptance before execution.
The approved Task digest remains
`2865ccf73e5736cb00eef383efad0732602e4e848f4b1ec5b53bef55a2b3cb19`.
The Task JSON, shared contracts/recorder, all business implementations and financial/
statistical semantics are unchanged.

Natural-language acceptance used the fully specified Phase A example verbatim.
Actual G1/G3 discovery on a backend launched from this checkout preceded authoring
`candidate.json`; no older candidate fixture was copied. The full explicit plan maps
index `000852.SH`, H=10 trading sessions, inclusive 2010-01-01..2026-10-28, metric
`trailing_cumulative_return_v1`, `{}`, ordered quantile points 0.1/0.5/0.9, interval
edges [-0.15,-0.05,0,0.05,0.15], decimal_ratio and continue policy without defaults.
Only request IDs were assigned. Public Preview and fresh-process G4 read match it.
No research-intent interpretation mistake was found. One explicit example does not
establish general planning quality or a missing-parameter dialogue acceptance.

The final retained runs use actual backend OpenAPI and capability publication, not
a copied HTTP fixture. G5 uses the existing test-only simulated-host helper and
public-service fixtures, with network/SQLite forbidden. It calls the ordinary adapter
and actual public `execute_batch` once per Run; both Statistics methods actually run.
The `live` adapter context means production adapter mechanics, not actual provider
execution or genuine user approval. No production synthetic seam/callback was added.

| Acceptance criterion | Verified disposition |
| --- | --- |
| A: G1/G3/G4/G5 approved interfaces | PASS: actual OpenAPI/list/detail, public Preview, immutable freeze, ordinary G5/public Batch |
| B: G2/G6 | SKIPPED with exact approved MVP reasons; no authentication/visualization claim |
| C: faithful natural-language plan | PASS for one Agent-composed fully specified request; not general NLP validation |
| D: complete dates/H/statistics | PASS: unchanged full explicit inputs in workflow and actual Batch |
| E: Preview/frozen agreement | PASS: official public Preview, independent fresh-process G4 read |
| F: precisely authorized isolated execution | PASS: simulated test interaction, guards, one exact Plan call; no transferable real consent |
| G: original Research/Statistics output | PASS: actual saved Batch/Job/analysis/association/public input projections |
| H: independent read and historical results | PASS: fresh-process G5 plus independent endpoint/Type 7/interval oracles and fingerprint verification |
| I: later operational failure | PASS: expected later G3 FAIL; G4 current eligibility rejected; completed G5 result remains unchanged/readable |
| J: no unauthorized live I/O | PASS safety boundary: no provider access, no default cache access, no-consent check writes no intent |
| K: explicit problem dispositions | PASS: resolved and unresolved issues, warnings, fixture conditions and live blockers logged |
| L: useful final report | PASS: actual fixture statistics, coverage, limitations, execution history, exact evidence locations |
| M: no false live claim | PASS: all outputs identified synthetic; full live objective BLOCKED |
| N: regression suites | PASS: full root pytest plus lint/type/storage checks below |

At completion both final Runs had G1/G3/G4/G5 PASS and G2/G6 SKIPPED. Their subsequent
test-injected latest G3 is **FAIL**, explicitly retained. This is not a concealed
production failure: the historical completed result passes, but neither Run is currently
eligible for a new G5 invocation. No automatic retry or second intent was attempted.

| Evidence | Run / reference |
| --- | --- |
| Complete fixture | `35ab3cf0064444feac135d9cac29ac8e`; one successful Batch/Job, 4,389 Eligible, complete fixture facts |
| Injected partial facts | `d2400af9382540daabe06da074fba33d`; computation successful, E/U/X=4,387/2/0; facts incomplete |
| No-consent check | `407cf8e7450e43afb059077c64ab4b08`; G5 BLOCKED, zero intents/calls |
| Earlier completed Runs with reporting failures | [development_runs.json](development_runs.json): two preserved successful outputs recovered read-only, equal to complete fixture |
| Every workflow/Preview/result/report hash | [results.json](results.json); locations join `workbench/.runs/`, Run ID and stored_path |
| Live isolation / credential prerequisites | [isolation.json](isolation.json), [prerequisites.json](prerequisites.json); no provider access |

The complete result is 23,478,144 bytes; partial result is 23,477,204 bytes. Public
committed summaries carry statistics, counters, exact references and hashes. Full
immutable blobs remain in ignored local storage. No paid response, secret, credential
hash, private source path or ignored Run directory is committed. Safe projection omits
free-text failure diagnostics under the existing G5 contract; public classifications,
requests, coverage and provenance remain available. No mutable cache is replay evidence.

Commands actually run from repository root:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
poetry run python ui_http/scripts/api.py --host 127.0.0.1 --port 18061
poetry run python workbench/tasks/historical_return_observation/record_g1.py --base-url http://127.0.0.1:18061 --timeout 5 --original-request "WB-06 G1 readiness only; subsequent read-only discovery and isolated synthetic acceptance; no live authorization"
poetry run python workbench/tasks/historical_return_observation/record_g3.py --run b7c51707882347e28ea1c72d8f8ae231 --timeout 5
poetry run python workbench/tests/wb06_e2e_example.py --base-url http://127.0.0.1:18061 --candidate workbench/tasks/historical_return_observation/wb06/candidate.json --output workbench/tasks/historical_return_observation/wb06/results.json
poetry run python market_research/tests/live_e2e_acceptance.py --output workbench/.runs/wb06-isolation.json
poetry run pytest workbench/tests/test_wb06_e2e.py -q
poetry run pytest -q
poetry run ruff check workbench
poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation
poetry run python workbench/tests/acceptance_example.py
git diff --check
```

The explicit original Run also exercised the early harness errors; no successful
execution was rerun. Final command without `--run` creates independent test scenarios.
The no-Source isolation probe returns JSON verdict `Blocked` because live I/O was not
requested; its factory-isolation checks **passed**, not live readiness. A separate
ignored probe used the existing provider credential resolver with sockets forbidden,
recording only its availability boolean. No `--live` command was run.

| Actual check | Result |
| --- | --- |
| New dense full-window/partial/no-consent regression | Initial fixture-accounting failure retained in problems; corrected: 1 passed in 16.84s |
| Full root suite | **2,511 passed**, 1 existing Starlette warning, 157.67s |
| Standalone WB-06 final run | Both expected fixture completions and absent-consent BLOCKED; independent fresh-process reads/oracles passed |
| Ruff, entire workbench | Passed |
| mypy shared recorder + Task scripts | Passed, 8 source files |
| Existing WB-01 storage example | Passed; distinct synthetic Runs and all statuses |
| Final authority topology / HTTP architecture | 21 passed; no navigation or module-boundary regression |
| Independent original evidence verification | Four completed Runs; 36 original artifact hashes verified with Research/network/SQLite forbidden; all files unchanged |
| Document navigation / report references | Local link targets, all displayed Run/artifact IDs, candidate hash and 17 complete problem records verified |
| Whitespace / full diff / snapshot integrity | Verified at delivery; [delivery index](delivery.json) retains exact same-Run document/evidence references |

Final reconciliation follows Scenario → Evidence → Problem Analysis → Acceptance →
Reconciliation. Existing Task v1 permits separate pure planning and separately authorized
execution; no version amendment is required. The G5 missing-tolerant rule permits the
partial-facts computation to PASS with retained U/coverage, without accepting full market
completeness. Financial formulas, Statistics algorithms, upstream ownership and public
capability semantics remain their canonical owners'. No framework, Gate, scheduler,
cache repair or new business semantics was introduced. Entry navigation reaches this
acceptance and each specialized evidence concern without expanding general authority.

The only OPEN/BLOCKED research requirements are listed in [live readiness](LIVE_READINESS.md)
and [problems](problems.json): real intent/identity/permissions/history, verified
full-window operational bounds/isolation and genuine exact-workflow consent, followed
by one actual full-history G5 invocation and honest inspection of its saved results.
Nothing in this deterministic PASS closes those conditions.
