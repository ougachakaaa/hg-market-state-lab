# Research usage for humans and agents

This is the stable usage entry, not semantic authority. Start with the Research-owned
[capability contract](descriptive/RESEARCH_CAPABILITY.md), [Plan/Batch contract](descriptive/BATCH_EXECUTION.md)
or [HTTP transport contract](../ui_http/products/research/http-contract.md) for authoritative rules.
Executed verification and live HTTP limits are recorded in
[Research entry acceptance](descriptive/RESEARCH_ENTRY_ACCEPTANCE.md).

## What is available

The first and only admitted Research is descriptive **`trailing_cumulative_return_v1`**:
index trailing cumulative return `close(T) / close(T-H) - 1`, in `decimal_ratio`.
`0.1` means 10%, without percentage conversion in the API. It uses full canonical
index_code identities and the SSE trading-session calendar. `000852.SH` is CSI1000,
verified against public metadata in [isolated Live E2E](descriptive/LIVE_E2E_ACCEPTANCE.md).
It is an example, never a default. A syntactically legal code does not prove current
upstream membership or readiness. Stock returns and Conditional Research are not supported.

All plan fields are required. Supply explicit `metric_parameters={}`, ordered non-empty
subjects/horizons/windows/analysis_requests and `on_job_failure="continue"` or `"stop"`.
Subjects, horizons and exact windows must be unique. Different overlapping windows remain
independent Jobs. Each analysis has an unchanged non-empty request_id, unique within the
plan; identical specs with different IDs remain distinct required analyses.

H is a positive integer excluding bool, measured in **trading sessions**, not calendar
days. Windows select inclusive end-session anchors using date-only bounds, start <= end,
with no future end date in Asia/Shanghai. Warm-up prices precede the window as needed;
their acquisition is part of execution. Missing Calendar is not inferred from weekdays.

Exactly two Statistics specs are available, validated by the public
[Statistics API](../market_statistics/CONTRACT.md):

| Method | Explicit parameters | Result |
| --- | --- | --- |
| quantile | points: non-empty, finite unique strictly increasing probabilities in [0,1] | Type 7 linear (`type7_linear_v1`) ordered point/value pairs, sample_count, unit |
| interval_count | edges: at least two finite strictly increasing coordinates; unit: decimal_ratio | bins in edge order; [left,right), final [left,right]; counts/full-sample frequencies and underflow/overflow |

No automatic binning, sorting, deduplication, clipping, unit conversion, implicit dates,
subject, provider, parameters or policy. Bool and numeric strings are not coordinates.

## Python: pure preview and explicit execution

From the repository root, use the single root Poetry environment. This example constructs
the exact same plan as the HTTP example. `preview_plan` is pure; **execute_batch may
acquire live facts and write DataLake-owned caches**. Execute only after choosing those
inputs and authorizing acquisition. The historical default-cache limitation below applies.

```python
from datetime import date

from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.capabilities import get_capability, list_capabilities
from market_research.descriptive.execution import ResearchPlan, execute_batch, preview_plan
from market_research.descriptive.observation import DateWindow
from market_statistics import IntervalCountSpec, QuantileSpec

assert len(list_capabilities()) == 1
descriptor = get_capability("trailing_cumulative_return_v1")
plan = ResearchPlan(
    metric="trailing_cumulative_return_v1",
    metric_parameters={},
    subjects=["000852.SH"],
    horizons=[2],
    windows=[DateWindow(date(2024, 1, 10), date(2024, 1, 16))],
    analysis_requests=[
        AnalysisRequest("p10_p50_p90", QuantileSpec([0.1, 0.5, 0.9])),
        AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0.0, 0.2], "decimal_ratio")),
    ],
    on_job_failure="continue",
)
preview = preview_plan(plan)
assert (preview.planned_count, preview.analysis_attempt_count) == (1, 2)
# Execution below may perform acquisition/cache writes; it is not part of pure preview.
batch = execute_batch(plan)
print(batch.status, batch.success_count, batch.failed_count, batch.skipped_count)
```

Python Plans have no HTTP size caps or acknowledgment field. Construction and execution
both validate the entire plan before I/O. Preview reuses that preflight and expands Jobs
in subjects → horizons → windows order. It does not probe provider/cache availability.
Two analyses per Job do not add another observation dimension. Stop can reduce actual
analysis attempts from the planned count.

## HTTP: discover, inspect, preview, execute

Start the existing backend from the root:

```powershell
poetry run lab serve backend
```

Base URL: `http://127.0.0.1:8011`; OpenAPI: `/openapi.json`; interactive docs: `/docs`.
Default exposure is loopback only, with no authentication. Acknowledgment is not a security
boundary. No new server/port, CORS, internet deployment or Research CLI command is added.

```text
GET /research/capabilities
GET /research/capabilities/trailing_cumulative_return_v1
POST /research/preview
POST /research/execute
```

The first GET returns an array of one full descriptor. Detail returns the same object:
supported means implemented; `live_readiness="not_probed"` is explicit. Both GETs and
preview create no DataLake service and make zero market I/O.

Exact tested preview JSON body, also published as an OpenAPI example:

```json
{
  "metric": "trailing_cumulative_return_v1",
  "metric_parameters": {},
  "subjects": ["000852.SH"],
  "horizons": [2],
  "windows": [{"start_date": "2024-01-10", "end_date": "2024-01-16"}],
  "analysis_requests": [
    {"request_id": "p10_p50_p90", "spec": {"method": "quantile", "points": [0.1, 0.5, 0.9]}},
    {"request_id": "distribution", "spec": {"method": "interval_count", "edges": [-0.2, 0.0, 0.2], "unit": "decimal_ratio"}}
  ],
  "on_job_failure": "continue"
}
```

The [complete tested preview response](../ui_http/tests/fixtures/research_preview.json)
echoes that normalized plan, one fixed Job and its named structural identity, with
`planned_count=1`, `analysis_attempt_count=2`. Every field, including dates/order/IDs,
is exercised through the real composed app.

Execute accepts the **same top-level fields plus required `"acknowledge_acquisition": true`**.
Use the [exact execute request](../ui_http/tests/fixtures/research_execute.json); false,
missing or numeric acknowledgment fails. Obtain explicit user execution authorization
before sending it. Send once, with no silent retry. The HTTP resource limits apply to both
POSTs: 8 expanded Jobs, 4 analyses per Job, 93 inclusive calendar days per window, H <= 20,
128 coordinates per spec, 128 characters per request_id and a 64 KiB body. Python legality
is independent. Requests exceeding these caps fail before execution; no splitting occurs.

This PowerShell sequence uses the tested files and the existing server. The final call
may acquire real data; run it only with explicit authorization and suitable caches:

```powershell
$base = 'http://127.0.0.1:8011'
Invoke-RestMethod "$base/research/capabilities"
Invoke-RestMethod "$base/research/capabilities/trailing_cumulative_return_v1"
Invoke-RestMethod "$base/research/preview" -Method Post -ContentType 'application/json' -InFile 'ui_http/tests/fixtures/research_plan.json'
# After explicit execution authorization:
Invoke-RestMethod "$base/research/execute" -Method Post -ContentType 'application/json' -InFile 'ui_http/tests/fixtures/research_execute.json'
```

For an immediately runnable **deterministic fake-only acceptance**, without starting a
server, touching caches or acquiring market facts:

```powershell
poetry run python ui_http/tests/research_http_acceptance.py
```

Its [complete tested execution response](../ui_http/tests/fixtures/research_success.json)
uses synthetic public-service facts, not CSI1000 market prices. The exact selected fields
are status `success`, counts 1 planned / 1 Success / 0 Failed / 0 Skipped, 5 Eligible,
observation coverage 1.0 and these numeric outputs:

```json
{
  "method": "quantile",
  "estimator": "type7_linear_v1",
  "points_and_values": [[0.1, -0.18666666666666662], [0.5, 0.0], [0.9, 0.12]],
  "sample_count": 5,
  "unit": "decimal_ratio"
}
```

IntervalCount bins have counts `[2,3]`, frequencies `[0.4,0.6]`, and zero underflow/overflow.
The fixture input fingerprint is
`b6b4cc205d576c84e6d89dc86a214e2592e14814ff08dcfaf0eba1fa17e446b8`.
Actual upstream execution can return different numbers, coverage or failures.

## Agent tool flow

1. Discover with `list_research_capabilities`, then inspect `get_research_capability`.
   Do not treat implementation support as a live-readiness check.
2. Translate the user's question into explicit canonical subject, dates, trading-session
   horizons, method parameters, request IDs and failure policy. Ask for missing inputs or
   ambiguous asset identity; never guess a stock case, provider or a calendar-day horizon.
3. Call `preview_research_plan`. Report the complete Job count/order, windows, horizons,
   analyses and possible live provider/cache I/O, including warm-up acquisition. Preview
   gives no operational readiness guarantee.
4. On explicit user execution authorization, call `execute_research_plan` once with true
   acquisition acknowledgment. Do not automatically retry a transport failure or busy
   result: a disconnected client may have left the synchronous worker running.
5. Report Batch, every Job and analysis status; eligible sample counts, coverage, exact
   numeric values/units, input profile/fingerprint, failures and skips. Explain overlapping
   lookback dependence and missing population. Never present this descriptive output as a
   predictive market-state signal or trading advice.

These are stable OpenAPI operationIds for tool registration. OpenAPI and localhost HTTP
**do not automatically connect a cloud ChatGPT conversation**. An agent needs registered
HTTP/OpenAPI/MCP/connector tooling and network reachability to this server. This delivery
implements no MCP, cloud hosting, plugin installation or automatic cloud connectivity.

## Reading results and failures

HTTP 200 means the request produced a BatchResult; it does not promise Research success.
Batch `success` means all Jobs Success; `partial_success` has successes and failures;
`failed` has no successes. A Job is `Success` only when every required analysis is associated.
Legal partial facts can still produce Success with honest coverage. `Failed` retains all
obtained evidence; all later analyses within that Job are still attempted after an analysis
failure. Stop applies after the complete failed Job, marking later Jobs `Skipped` with the
trigger identity. Continue attempts all Jobs. Analysis statuses are `success`, `failed`,
`not_attempted`; failed association retains its original raw numeric result.
Rejected raw NaN/infinite coordinates are explicitly tagged as
`{"kind":"non_finite","value":"nan"}` (or `positive_infinity` / `negative_infinity`),
preserving order with valid JSON. Successful statistics and sample values remain finite numbers.

Each Job exposes every Eligible observation key/anchor/value, Unavailable dependency and
Excluded offending endpoint, candidate/E/U/X counts, ratios, overall/warm-up/sample fact
coverage, dependence spans, NumericSample values and ordered binding keys. Zero is a number;
null ratios mean not applicable for zero denominators. Zero Eligible fails conversion,
with the observations still present. Incomplete Calendar fails preparation; partial Index
facts do not silently drop candidate anchors.

`prepared_context` and `input_attempts` summarize actual tagged public requests, final and
preliminary dataset/view/schema/coverage/row counts, Ensure accounting and every failed unit
identity. Malformed evidence is explicitly marked `invalid_public_shape`. Successful
observations retain the original profile/fingerprint and all endpoint requirements. Binding
references this same Job/source fingerprint rather than duplicating full exports per analysis.

The fingerprint identifies consumed source inputs; it does not prove hidden numerical origin,
independence or predictive validity. HTTP omits full original Calendar/Index rows, canonical
bytes, original exception chains/text and Python object graphs. Provider failure text is replaced
with safe unit summaries; failure records retain original Research classification/stage/ID
with a safe reason. The richer original typed context remains available through Python.

| HTTP status | error.kind | Action |
| --- | --- | --- |
| 400 | invalid_request | Correct strict JSON or public Plan/Stats legality; preflight failure has no I/O |
| 400 | request_too_large | Choose a smaller explicit request; no automatic splitting |
| 404 | capability_not_found | Discover the sole supported ID |
| 409 | execution_busy | Another execution owns the process; no second execution was submitted |
| 500 | internal_error | Unexpected defect; safe detail, no automatic retry |

Errors have `{"error":{"kind":"invalid_request","detail":"...","param":null}}`.
Completed Failed/partial batches stay 200 with classified records, not transport errors.
One process permits one execution; it has no distributed lock, queue or wall-clock deadline.
Discovery remains responsive while the synchronous worker runs off the event loop.

## Operational limits and current evidence

The existing **isolated Live E2E is Verified** for the Python research chain. The historical
default Trade Calendar cache was incompatible; **default-cache recovery was NOT performed**.
It remains unchanged by this work. Do not test or repair that user cache implicitly. See
[live evidence](descriptive/LIVE_E2E_ACCEPTANCE.md), [DataLake lifecycle](../data_lake/PERSISTENCE.md)
and [local environment](../DEVELOPMENT.md). Upstream availability, credentials, Calendar
completeness and partial Index facts remain operational dependencies. Deterministic HTTP
acceptance does not pass a live HTTP gate.

There is no Research persistence/replay/result cache, historical-run retrieval, persistent
run ID, durable result URL, scheduler, polling/cancellation API, frontend Research page,
prediction/signal feature or new engine. An HTTP server does not add these capabilities.
