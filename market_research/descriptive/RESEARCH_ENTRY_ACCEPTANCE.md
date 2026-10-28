# RESEARCH-ENTRY-01 acceptance and reconciliation

Date: 2026-10-28. Verdict: **RESEARCH-ENTRY-01 Complete** for the bounded capability,
guide and deterministic HTTP delivery slice. **Live HTTP acceptance was not performed.**
This record owns verification evidence, not Research or HTTP semantics. Owners remain
[capability publication](RESEARCH_CAPABILITY.md), [Plan/Batch](BATCH_EXECUTION.md), the
[case](cases/trailing_return/ARCHITECTURE.md), [Statistics](../../market_statistics/CONTRACT.md)
and [HTTP transport](../../ui_http/products/research/http-contract.md). Human/agent usage
starts at [USAGE.md](../USAGE.md).

## Baseline and sequential delivery

- Repository: `ougachakaaa/hg-market-state-lab`.
- Branch: `reset/market-research-descriptive`; initially clean.
- Exact required baseline: `c4308907921e55df29cefd4d6b4ac579477822e0`.
- Authority commit: `429789100a6d86d280f76efc8e1d2bb97ae004ec`
  (`docs(research,http): freeze research capability and HTTP entry authority`).
- Implementation commit tested: `210413abf7e63960d60818cf5d747ca7e000b472`
  (`feat(research,http): publish agent-discoverable research execution API`).
- This record and readiness/navigation reconciliation land in the third independent
  `docs(research,http): reconcile agent research entry acceptance` commit.

The sequence was semantic decision encoding → authority commit → boundary/runtime
reconciliation → implementation commit → complete verification → this reconciliation.
The first commit included only authority/navigation. Before its commit, 19 topology and
HTTP boundary checks passed. Before the implementation commit, Research/HTTP 1030 tests,
21 topology/boundary checks, Ruff and Mypy passed. Generated sibling contracts were
regenerated and checked, with no content changes. Required final checks below ran against
the committed implementation before this verification/reconciliation commit. Its only
test-code refinement adds complete committed-response comparisons and explicit numerical,
coverage and fingerprint assertions to the standalone acceptance harness; no production
code or schemas change. That harness, Ruff and Mypy were rerun successfully afterward.

The task's referenced `RESEARCH_USAGE_DRAFT.md` was not among the supplied files or found
in the attachment/Downloads lookup. The published guide was authored from current owners,
actual public code, generated OpenAPI and exact tested examples, with no draft-derived
semantic assumptions. The supplied goal attachment was read before repository work.

## Published surfaces and ownership reconciliation

| Existing owner / concern | Resolution | Runtime / evidence |
| --- | --- | --- |
| Research case, formula, index binding, dates, units and partial-fact policy | Remain valid; one explicit supported declaration, no readiness probe or future cases | [capabilities.py](../src/market_research/descriptive/capabilities.py), [publication tests](../tests/test_research_entry.py) |
| Plan, complete pure preflight and expansion | Remain valid; expose frozen PlannedJob/PlanPreview and preview_plan via execution facade | [preview.py](../src/market_research/descriptive/execution/preview.py); original plan/Job/Batch code unchanged |
| Original ResearchPlan / execute_batch | Remain the sole execution owner; HTTP constructs original public request/spec types and delegates once | [endpoint](../../ui_http/src/ui_http/products/research/endpoint.py), [HTTP tests](../../ui_http/tests/test_research_api.py) |
| Observation, conversion, Statistics and association | Remain valid; no calculation, expansion, source selection or failure classifier moved to HTTP | [architecture checks](../../ui_http/tests/test_architecture.py), Research boundary tests and both owners' suites |
| Research publication → Statistics | Narrowly admitted only public QuantileSpec/IntervalCountSpec for declared method identities; no compute, numerical internals or acquisition | Precise allowlist and negative import cases in [boundary tests](../tests/test_conversion_boundaries.py) |
| HTTP resource/safety/error policy | Newly specialized transport concern; acknowledgment, caps, one-process guard, off-loop synchronous execution and safe errors | [HTTP authority](../../ui_http/products/research/http-contract.md), strict [requests](../../ui_http/src/ui_http/products/research/requests.py) |
| Research evidence and richer Python objects | Complete ordered bounded projection; no private object graphs or full duplicate exports | [wire shapes](../../ui_http/src/ui_http/products/research/schemas.py), [projection](../../ui_http/src/ui_http/products/research/projection.py) |
| Rejected raw non-finite numerical result | Explicit reconciliation before its implementation: preserve failed raw coordinates with typed non_finite labels; successful payload/sample numbers remain finite | NaN, positive/negative infinity association-failure HTTP tests; no Statistics semantics changed |
| Existing root RequestValidationError default | Research scope is handled separately, including malformed JSON/UTF-8; sibling mappings unchanged | [shared app](../../ui_http/src/ui_http/app.py) and all existing MO suites |
| Existing global OpenAPI endpoint inventory | Expected expansion from 2 to 6 paths; only the composition assertion adds Research paths | MO response/status/schema tests unchanged; generated product representations unchanged |
| Frontend contracts | No Research consumer admitted; generate/check both current products, add no Research artifacts | Existing per-feature OpenAPI/TypeScript content unchanged |
| DataLake lifecycle and previous isolated Live E2E | Remain valid; ordinary tests use public-service fakes only | No provider access, cache migration or rebuild; default Calendar limitation unchanged |

The Batch authority's pre-existing “seven fields” wording was reconciled to the actual
eight explicit fields; no Plan field or validation behavior changed. New semantic
publication and HTTP transport remain separate narrow authorities discoverable from
module entries/catalogs. The guide is usage-only. No unresolved semantic decision is
hidden behind a default, generic registry or deferred document split.

Public Python additions:

```text
market_research.descriptive.capabilities
    CapabilityDescription, CapabilityNotFound, list_capabilities(), get_capability(id)
market_research.descriptive.execution
    PlannedJob, PlanPreview, preview_plan(plan)
```

Four mounted operations and exact operation IDs:

```text
GET  /research/capabilities       list_research_capabilities
GET  /research/capabilities/{id}  get_research_capability
POST /research/preview            preview_research_plan
POST /research/execute            execute_research_plan
```

## Required verification actually executed

All Python commands ran from the repository root in the unique root Poetry environment.

| Command | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | 811 passed |
| `poetry run pytest ui_http/tests -q` | 219 passed |
| `poetry run pytest market_statistics/tests -q` | 171 passed |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | 21 passed |
| `poetry run ruff check market_research ui_http market_statistics` | Passed |
| `poetry run mypy market_research/src market_research/tests ui_http` | Passed, 77 source files |
| `poetry run pytest -q` | 2255 passed |
| `poetry check --lock` | Passed; no dependency/lock change |
| `git diff --check` | Passed; complete new/tracked diff reviewed before each commit |

From `ui_web/`:

| Command | Result |
| --- | --- |
| `npm run contract:generate` | Both sibling products reproduced; no committed content change |
| `npm run contract:check` | Both sibling OpenAPI and generated TypeScript current |
| `npm run test` | 15 files, 66 tests passed |
| `npm run build` | Passed |
| `npm run lint` | Passed |

One existing Starlette TestClient/httpx deprecation warning was emitted by Python tests.
Vite's existing large-bundle warning was non-failing; no frontend feature/build changes
were made for Research.

## Independent HTTP acceptance and generated schema

Executed from root:

```powershell
poetry run python ui_http/tests/research_http_acceptance.py
```

This is self-contained TestClient/ASGI against the real composed FastAPI app, using
deterministic public-service fakes and the original public execute_batch. It asserts:

- Discover exactly one descriptor; detail equals that descriptor. Select its exact ID and
  construct the explicit body from the live OpenAPI PlanBody example/required schema.
- Preview returns one Job and two planned analysis attempts; normalized identity/order
  match the response from execution. No service creation or source operation before execute.
- Execute delegates to execute_batch exactly once. Operations during execute are
  create_calendar → export → export → create_index → export. These are fake operations;
  no real provider/network/cache access occurs, and the complete-fact fixture needs no ensure.
- Batch `success`, counts `(planned,success,failed,skipped)=(1,1,0,0)`; Job `Success`,
  ordered analyses `success,success`; 5 Eligible, observation coverage 1.0; 7/7 overall
  facts, 2/2 warm-up and 5/5 sample facts.
- NumericSample values retain declared anchor order, approximately
  `[0.2,-0.2,-1/6,0,0]` with original binary64 coordinates.
  Quantiles `(0.1,-0.18666666666666662),(0.5,0.0),(0.9,0.12)`;
  interval counts `[2,3]`, frequencies `[0.4,0.6]`, all outside counts/frequencies zero.
- Original profile `trailing_return_inputs_v2`, binding/source fingerprint
  `b6b4cc205d576c84e6d89dc86a214e2592e14814ff08dcfaf0eba1fa17e446b8`, exact ordered keys,
  public attempts/coverage, dependence spans, finite successful JSON values and nulls.

The exact request/response examples are committed as
[preview request](../../ui_http/tests/fixtures/research_plan.json),
[execute request](../../ui_http/tests/fixtures/research_execute.json),
[preview response](../../ui_http/tests/fixtures/research_preview.json) and
[execute response](../../ui_http/tests/fixtures/research_success.json).
The HTTP suite asserts the complete execution payload equals its example, plus independent
status, numeric, coverage and fingerprint assertions against the actual BatchResult.
`--write-examples` was used during implementation to generate these explicitly synthetic
examples. They are documentation fixtures, not a Research result cache or live market output.

Additional HTTP cases exercise late eighth-Job preflight failure without I/O, exact caps
and boundary acceptance, malformed/extra/duplicate/wrong-type inputs, units/methods,
partial batches, continue/stop, all-failed/Skipped, retained original failed-association
results, zero candidates/null ratios, zero Eligible, unavailable/excluded diagnostics,
malformed obtained evidence, provider/exception text suppression, lock release after
defects, two app instances sharing one guard, and discovery responsiveness on the **same**
ASGI event loop during execution. Root/feature sibling validation and freshness tests pass.

Generated `/openapi.json` with TestClient from `ui_http.app.create_app()` and canonicalized
using Python `json.dumps(document, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
allow_nan=False).encode()`: OpenAPI **3.1.0**, **6 paths**, **81 schemas**, SHA-256
`09f33df83197df0b16c0f0eb5797904b34a858dae307f8c863fc7f9d534e1b3d`.
Stable unique IDs, required strict request models, method discriminators, examples, typed
result/evidence/errors and actual 200/400/404/409/500 route-specific responses were checked.
No Research frontend contract was generated. The global unused 422 convention is not
published as a real Research response; POST 400 schemas describe its actual validation.

## Release readiness and operational limits

Capability discovery, pure preview, bounded explicit execution, guide, machine schemas,
deterministic adapter acceptance and complete repository checks are **Verified**.
There is no implementation blocker for this delivery scope.

Live HTTP acceptance is **Not Run**; no live readiness claim is made. The previously
[isolated Python Live E2E](LIVE_E2E_ACCEPTANCE.md) remains Verified on its own evidence.
**The historical incompatible default Trade Calendar cache remains unresolved and unchanged;
default-cache recovery was NOT performed.** Default user caches were not used for this goal's
acceptance. Providers/credentials, Calendar completeness and partial or absent Index facts
remain operational dependencies; a new live smoke needs explicit authorization and isolated
storage discipline, not implicit repair or default-cache experiments.

Default launch remains `poetry run lab serve backend`, loopback `127.0.0.1:8011`, with no
auth. Acknowledgment is not a security boundary. Registered reachable agent tooling is
still required; this work does not connect a cloud conversation automatically. No Research
persistence/replay/cache/historical retrieval, retry, queue, scheduler, durable run ID,
frontend, MCP, cloud hosting, CLI expansion or new Research engine/case was delivered.
The process guard is not a distributed lock or wall-clock deadline. Stop at this Goal.
