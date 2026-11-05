# Query and result contract

This document specializes [Task version 1](../task.json) and the shared
[Task](../../../contracts/TASK.md), [Run](../../../contracts/RUN.md),
[Gate](../../../contracts/GATE.md) and [storage](../../../contracts/STORAGE.md)
contracts. It owns the detailed input resolution, capability selection, output,
coverage, failure and G2 delivery contract. Market facts, contract lifecycle, slots,
basis values and annualization remain with the
[CFFEX basis shared authority](../../../../data_snapshot/src/data_snapshot/cffex_equity_index_basis/ARCHITECTURE.md)
and the [product read/application contract](../../../../data_snapshot/src/data_snapshot/products/cffex_equity_index_basis_history/read-contract.md).
If this document conflicts with [task.json](../task.json) or an owning authority,
reconcile it explicitly; do not silently create a third semantic.

## 1. Canonical input and resolution

### 1.1 Canonical request

```json
{
  "futures_families": ["IM"],
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}
```

- `futures_families` is a nonempty, unique set of supported family codes or
  unambiguous documented aliases. The canonical set is `IF`, `IH`, `IC`, `IM`.
- Family codes are ASCII case-insensitive and are normalized to uppercase. The
  canonical execution and output order is `IF`, `IH`, `IC`, `IM`, independent of the
  order supplied by the user.
- `start_date` and `end_date` are real `YYYY-MM-DD` calendar dates, inclusive at both
  ends, with `start_date <= end_date`.
- `end_date` must not be later than the execution date in `Asia/Shanghai`. A future
  end date is invalid; if the user supplies an explicit range that includes today,
  that is allowed, but the Task does not assume today's data is already published.
- The requested window is passed to every product call unchanged. The Task does not
  expand, contract, snap to a trading day or fill holidays.

Supported family and alias reference:

| Family | Underlying | Explicit aliases |
| --- | --- | --- |
| `IF` | `000300.SH` | 沪深300, 沪深300指数 |
| `IH` | `000016.SH` | 上证50, 上证50指数 |
| `IC` | `000905.SH` | 中证500, 中证500指数 |
| `IM` | `000852.SH` | 中证1000, 中证1000指数 |

The underlying and listing facts remain owned by the shared CFFEX authority and are
read from the public product result. The `所有股指期货` and `全部股指期货` expressions
resolve to all four families. Unknown, unsupported or ambiguous names must fail
`input_resolution`; never guess from a partial name, an arbitrary index code, a
contract code or another family. A bare `股指期货` without `所有`/`全部` is ambiguous
and must not be treated as all four.

### 1.2 Relative time and anchor

Natural-language interpretation is Agent-driven: the Agent records the original
phrase and the resolved absolute inputs, and the Task runtime validates and freezes
them. A deterministic resolver may support the documented patterns, but it must not
invent aliases, defaults or a trading calendar.

Resolution rules:

- **最近两周**: 14 consecutive natural days ending at the resolved anchor, inclusive.
- **最近 N 个交易日**: N CFFEX open dates ending at the resolved anchor, inclusive.
  N is a strictly positive integer; never replace it with N natural days. The
  documented `最近十个交易日` is N=10 trading sessions, not 10 natural days. The
  calendar lookup range must be wide enough to contain N CFFEX open dates; record the
  exact calendar query range. Expanding only the calendar lookup range (not the basis
  window) to find N sessions is allowed and recorded.
- **指定起止日期**: preserve the explicit dates exactly; do not snap them to a nearby
  trading day.
- Every relative expression is resolved to absolute dates before any market request.
  The Run preserves the original phrase, resolved family set, resolved date range,
  anchor rule, calendar source and coverage, execution instant and data query ranges.

V1 anchor policy:

- The default anchor is the latest CFFEX open date **strictly before** the execution
  date in `Asia/Shanghai`.
- No owner publishes a CFFEX session-completion fact. V1 therefore does not assume
  that the current day's session or data is complete, and does not invent a 15:00
  close-time constant.
- An explicitly supplied anchor (for example, a user saying `截至 2026-11-03`) is
  allowed only if it is a CFFEX open date and not later than the execution date. It is
  recorded as `anchor_rule = user_supplied_anchor`; a same-day anchor is still not
  proof that the data was published.
- If the published calendar cannot prove the anchor or its coverage, relative
  resolution is BLOCKED. Never infer the anchor from weekdays, price rows,
  `pretrade_date`, available-price counts or a sibling family.

### 1.3 Frozen resolution record

Before acquisition, the Run freezes at least:

- the verbatim `original_request`;
- resolved `futures_families`, `start_date` and `end_date`;
- the original date phrase (if any), resolution kind, execution instant in UTC and
  `Asia/Shanghai`, anchor date and anchor rule;
- the Calendar source, exact query range, export schema version, coverage status and
  a preserved export or lossless equivalent;
- explicit execution intent and the separate authorization reference for actual
  market access, when present;
- each family's exact product query range.

This record is the same-Run evidence for `input_resolution`; it is not a market result
and does not by itself authorize acquisition. Freeze the same canonical resolved-inputs
object in the Run manifest and mirror it in `result.json`; evidence artifact IDs are
recorded separately so the frozen input object remains identical. If resolution fails,
the Run records the attempted inputs and the explicit blocker instead of inventing
resolved values.

## 2. Capability selection and orchestration

### 2.1 Primary public product

The only market-data product used is
`data_snapshot.products.cffex_equity_index_basis_history`:

```text
run_cffex_equity_index_basis_history(
    CFFEXEquityIndexBasisHistoryRequest(
        futures_family=<one of IF/IH/IC/IM>,
        start_trade_date=<resolved start_date>,
        end_trade_date=<resolved end_date>,
    )
) -> CFFEXEquityIndexBasisHistoryResult
```

or `CFFEXEquityIndexBasisHistoryError` with a stable `reason` in
`invalid_request`, `source_failure`, `no_observations`, `incomplete_panel`.

- Call the public function exactly once per requested family.
- Do not import Capture, Source adapters, Raw artifacts, credentials, private
  Preparation or sibling product artifacts.
- Do not modify the product, add a parallel basis calculator or reuse another
  family's result.
- The product remains request-scoped; the Task owns only the per-family
  orchestration and the Run outputs.

### 2.2 CFFEX Calendar for expected sessions

Expected sessions and the relative-date anchor use only the existing public
Application Service:

```text
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarRange,
    create_service,
)

service = create_service()
request = TradeCalendarRange(
    exchange="CFFEX",
    start_date=<date>,
    end_date=<date>,
)
coverage = service.coverage(request)
result = service.ensure(request)     # only under separate execution authorization
view = service.export(request)       # read-only
```

- Use `exchange="CFFEX"`, view `calendar`, schema version 1. Filter `is_open == 1`
  (integer 1, not boolean) within the effective window.
- The export must cover at least the requested natural-day range, and its coverage
  must be complete. An incomplete export is `unverified`, not a closed day. Do not
  infer a missing day as a holiday.
- Do not call `trade_cal` directly, do not repair the Calendar cache and do not
  redefine calendar facts.
- Calendar `ensure` may write cache and must be covered by the same separate
  execution authorization as the product calls. If only a complete read-only export
  is available, no new cache write is required.

### 2.3 Independence and no substitution

- Each requested family is invoked independently. A failure in one family does not
  invalidate the successful results of other families, but it prevents a complete
  result and makes `basis_acquisition` FAIL.
- If execution authorization is absent, do not invoke any market capability; record
  the acquisition Gate as BLOCKED.
- Do not retry with a different window, family, contract, credential or source to
  manufacture success.

## 3. Output contract

Every acquisition-phase execution that reaches delivery produces three Run-scoped
files:

```text
result.json
basis_daily.csv
REPORT.md
```

The Task also preserves same-Run evidence (`resolution.json`, acquisition evidence,
`verification.json`) as described in section 3.4. G1 produces none of these files.

### 3.1 `result.json`

Shape (all fields required unless stated; placeholders are not data):

| Field | Content |
| --- | --- |
| `schema_version` | Integer `1`. |
| `task_id`, `task_version` | `equity_index_futures_basis_monitor`, `1`. |
| `task_sha256` | SHA-256 of the frozen Task snapshot from the Run manifest. |
| `run_id` | The existing Run's lowercase UUID hex identity. |
| `original_request` | Verbatim user request. |
| `resolved_inputs` | Canonical `futures_families`, `start_date`, `end_date`, and the resolution record from section 1.3. |
| `requested_window` | `{ "start_date": ..., "end_date": ... }`, matching the resolved inputs. |
| `expected_sessions` | Requested-window CFFEX open-date summary: `status` (`verified` or `unverified`), `source`, `trade_date_count`, `first_trade_date`, `last_trade_date`, `unverified_reason`. Per-family effective-window counts are in `families[]`. |
| `overall_status` | `complete`, `partial` or `failed`, using the rule in section 4.3. |
| `coverage_status` | `verified_complete`, `verified_partial`, `unverified`, `mixed` or `not_applicable`, using the rule in section 4.3. |
| `families` | One object per requested family, in canonical order; see below. |
| `failures` | Acquisition failures: `stage` (`acquisition`), `futures_family`, `reason`, `message`, `scope`. Empty if none. |
| `unfinished_scope` | Explicit strings for failed families, missing sessions, unverified coverage and any scope that could not be completed. |
| `limitations` | Run-specific plus static limitations from section 5. |
| `detail_file` | `name` (`basis_daily.csv`), `artifact_id`, `sha256`, `stored_path`, `row_count`; a stable reference to the full contract detail. |

Each `families[]` object contains:

| Field | Content |
| --- | --- |
| `futures_family`, `underlying_code` | Canonical identity; underlying from the public result (or the shared support reference if the family failed before a result). |
| `status` | `success` or `failed`. |
| `product_request` | Exact `{futures_family, start_trade_date, end_trade_date}` sent to the product. |
| `product_error_reason`, `product_error_message` | Product reason and a safe summary for a failed family; `null` for success. Never include credentials, tokens or raw exception traces. |
| `source_identity` | Public result identity for a successful family; `null` for failure. |
| `family_listing_date` | Public result listing date for success; `null` for failure. |
| `first_observation_date`, `last_observation_date` | Actual public result boundaries for success; `null` for failure. Never substitute the requested bounds. |
| `observation_count` | Public result observation count; `0` for failure. |
| `observed_trade_date_count` | Number of distinct `trade_date` values in the public result; `0` for failure. |
| `expected_trade_date_count` | Number of CFFEX open dates in the family's effective window when the family succeeded and calendar verification is available; otherwise `0` (unverified or failed). |
| `missing_expected_trade_dates` | Full ascending list of expected CFFEX sessions absent from observations; empty when none, unverified or failed. |
| `unexpected_observed_trade_dates` | Observed dates outside the requested/effective window or outside expected CFFEX sessions; a contract inconsistency that must be reported. |
| `latest_expected_trade_date` | Latest expected CFFEX session in the effective window; `null` when not applicable/unverified. |
| `latest_expected_session_observed` | `true`/`false` when verifiable; `null` otherwise. |
| `coverage_status` | Per-family state from section 4.2. |
| `coverage_reason` | `null` for `verified_complete`; an explicit reason otherwise. |

`result.json` does not contain its own artifact identity or the later `REPORT.md`
identity. The CSV artifact is registered before `result.json`, so its identity is
stable and included in `detail_file`. The Run and Gate evidence are the authoritative
index of all artifacts and avoid circular hashes.

### 3.2 `basis_daily.csv`

Exact header and column order:

```text
trade_date,futures_family,underlying_code,contract_code,contract_slot,delist_date,days_to_delist,underlying_close,futures_close,basis_pct,annualized_basis_pct
```

- One row per actual `trade_date` x family x contract returned by the public result.
- Ordering: `trade_date` ascending, then canonical family order `IF/IH/IC/IM`, then
  `M0/M1/Q1/Q2`, then `contract_code` ascending.
- Values are copied verbatim from the public observation. Use the shortest round-trip
  decimal representation for floats; do not round, reformat with thousands
  separators, or recompute. Preserve signed zero.
- `contract_slot` is exactly `M0`, `M1`, `Q1` or `Q2`; never rename the slots.
- No extra columns, no derived indicators, no filtering by volume, open interest,
  main-contract flag or liquidity.
- If no family succeeds, still write a header-only CSV; the failures are explained in
  `result.json` and `REPORT.md`.

### 3.3 `REPORT.md`

Required sections and content:

1. `## Query and actual range` — original request, resolved families, requested
   window, resolution anchor/basis, and each family's actual first/last observation
   date.
2. `## Latest session by family` — for each family, its latest actual observation
   date and the `M0/M1/Q1/Q2` `annualized_basis_pct`, `contract_code` and
   `days_to_delist`. If family latest dates differ, explicitly state that they are
   different sessions and must not be read as one trading day. A failed family shows
   its failure reason and no invented values.
3. `## Coverage and failures` — expected-session source/status, expected/observed
   counts, recent-gap flag and first/last missing dates, failed families, and the
   exact lines `Overall status: <value>` and `Coverage status: <value>` matching
   `result.json`. The full missing-date list remains in `result.json`.
4. `## Source, formula and units` — the public product and `source_identity`; the
   inherited formulas `basis_pct = (futures_close / underlying_close - 1) * 100` and
   `annualized_basis_pct = basis_pct * 365 / max(days_to_delist, 1)`, attributed to
   the shared authority; percentage-point units; sign convention (negative =
   discount, positive = premium); a statement that this is not an executable
   arbitrage yield or a rolling-hold return.
5. `## Near-expiry sensitivity` — `days_to_delist` and
   `max(days_to_delist, 1)`; annualized values near delivery are highly sensitive and
   are not smoothed.
6. `## Limitations` — no chart, statistical distribution, prediction, trading
   recommendation or backtest; no completeness claim when coverage is unverified or
   partial.

Use the same decimal strings for report values as the CSV. The report is generated from
the same normalized facts as `result.json` and is checked by the delivery verifier; it
must not introduce a value or date that is absent from the machine-readable outputs.

### 3.4 Run evidence, artifact order and storage

Required same-Run evidence:

- `resolution.json`: the frozen record from section 1.3, plus the Calendar export or
  a lossless equivalent and its coverage/digest.
- Acquisition evidence: for each successful family, the lossless actual public result
  payload (including observations) or an equivalent lossless serialization; for each
  failed family, the classified reason and safe message. A digest alone is not
  sufficient to verify every CSV row. One combined artifact or one artifact per family
  is allowed.
- `verification.json`: the delivery checks listed in section 6.3.

Artifact order avoids circular references:

1. Register `resolution.json` and the Calendar evidence; record `input_resolution`.
2. Invoke the product per family and preserve acquisition evidence.
3. Generate and register `basis_daily.csv`.
4. Generate and register the acquisition summary; record `basis_acquisition`.
5. Generate and register `result.json` (references the registered CSV).
6. Generate and register `REPORT.md`.
7. Run delivery verification, register `verification.json`, then record
   `result_delivery`.

All files are copied into immutable Run storage through the existing
`workbench/run_store.py` public operations. Market data is never committed to Git.
Run evidence is operational evidence, not a Research publication or Dataset output.

## 4. Coverage and completeness

### 4.1 Definitions

| Term | Meaning |
| --- | --- |
| Requested window | The exact inclusive `[start_date, end_date]` supplied by the user; never rewritten. |
| Effective window | `[max(start_date, family_listing_date), end_date]` for a family; dates before listing are not missing observations. |
| Observed window | Distinct `trade_date` values in the successful public result; first/last are actual observations. |
| Expected sessions | CFFEX open dates from the published Calendar within the effective window. |
| Missing expected sessions | Expected sessions not present in the observed window. |
| Unexpected observed sessions | Observed dates outside the requested/effective window or outside the expected CFFEX sessions. |
| Recent gap | The latest expected CFFEX session in the requested window is absent from a family's observations. |

### 4.2 Verification and states

For each successful family:

1. Obtain a complete Calendar export for `CFFEX` covering at least the requested
   natural-day range. Verify the requested window lies within the export window and
   the export coverage is complete; otherwise use `unverified`.
2. Compute the effective window from the public `family_listing_date`.
3. Filter Calendar records with `is_open == 1` inside the effective window to form the
   expected set. The effective window being empty yields `not_applicable`.
4. Compare the expected set with the unique observed `trade_date` set.
5. Compute missing and unexpected dates and the recent-gap flag.

States:

- `verified_complete`: Calendar coverage is complete, expected and observed sets match,
  and there are no unexpected observed dates.
- `verified_partial`: Calendar coverage is complete, but at least one expected session
  is missing or an unexpected observed date exists. List the dates.
- `unverified`: Calendar coverage, authorization or completeness cannot prove the
  expected sessions. Do not list missing dates as facts and do not claim completeness.
- `not_applicable`: Family failed or the effective window is empty.

A successful product result proves a complete `M0/M1/Q1/Q2` panel **only on its actual
observation dates**. It is not evidence that every expected session in the requested
window was observed. The Task must not convert product success into
`verified_complete` without the Calendar check.

### 4.3 Overall status

Overall `coverage_status` over the requested family set:

- `not_applicable` if no requested family succeeded.
- `verified_complete` iff every requested family succeeded and is
  `verified_complete`.
- `verified_partial` iff every requested family succeeded and all are verified
  (complete or partial) with at least one `verified_partial`.
- `unverified` iff every requested family succeeded and all are `unverified`.
- `mixed` otherwise (including any failed family, or a mix of verified and unverified
  successful families).

Failed families are also reported in `failures` / `unfinished_scope`.

Overall status:

- `complete` iff every requested family succeeded and every family coverage is
  `verified_complete`.
- `partial` iff at least one family succeeded but the run is not complete.
- `failed` iff no family succeeded.

A partial or unverified run must never be described as a complete result or a
successful Task run. A failed family prevents `result_delivery` PASS; a partial family
success is preserved but is not a complete result.

### 4.4 Edge cases

- Requested end date is a weekend/holiday: the latest expected session is the prior
  CFFEX open date. If observed, there is no recent gap.
- Requested window starts before a family's listing: the effective window starts at
  listing; pre-listing dates are not reported as missing. The product may return
  `no_observations` if the effective window is empty.
- An expected CFFEX session is absent from observations: `verified_partial`, the date
  is listed, and the report says the panel is incomplete. Do not infer an SSE holiday
  or a product bug.
- An observed date is outside the expected CFFEX sessions or outside the requested
  window: report it as `unexpected_observed_trade_dates`; it is a contract
  inconsistency, not a date to add to expected sessions.
- Calendar unavailable/incomplete for an explicit date range: acquisition may proceed,
  but coverage is `unverified` and `result_delivery` is BLOCKED because completeness
  cannot be established.
- Calendar unavailable/incomplete for a relative expression: `input_resolution` is
  BLOCKED before acquisition; do not guess an anchor.
- Different families have different latest actual observation dates: report each date
  separately and state explicitly that they are not the same session.

## 5. Failure semantics

Product failures keep the public classification:

- `invalid_request`: invalid fields or dates. Do not repair by changing the request.
- `source_failure`: credential/client construction, Source invocation or Source range
  failure. Record a safe summary; do not expose credentials or raw transport.
- `no_observations`: no underlying observation in the effective interval. This is not
  zero basis and must not produce rows.
- `incomplete_panel`: missing, duplicate, conflicting or unusable facts prevent a
  complete `M0/M1/Q1/Q2` panel. Do not delete contracts or dates, fill prices or use
  another family to pass.

Rules:

- Invoke each family independently and retain every actual outcome.
- A failed family contributes no fabricated rows and no zero basis.
- Do not delete missing contracts, synthesize prices, auto-replace contracts,
  substitute another family or change the window to manufacture a complete panel.
- Do not truncate or expand the requested window, change N, snap dates or retry with
  different inputs.
- Do not recompute basis or annualization; copy the public product values.
- Partial successes remain available as Run artifacts with explicit failures, but
  `result_delivery` cannot PASS while any requested family failed. The overall status
  is `partial`, never `complete`.
- If all families fail, the overall status is `failed`, the CSV is header-only, and the
  report explains each failure without inventing observations.

Static limitations to include in every report:

- `annualized_basis_pct` is a simple linear annualization of the market price
  difference, not an executable arbitrage yield, financing-adjusted return or rolling
  strategy return.
- Near-delivery annualization is highly sensitive to `days_to_delist`.
- V1 has no chart, distribution, prediction, trading recommendation or backtest.
- Coverage is a Task-level verification of expected CFFEX sessions, not a redefinition
  of product completeness or a claim about the Source's internal state.

## 6. Gates and evidence

Gate definitions are in [task.json](../task.json); this section specializes evaluation.

### 6.1 `input_resolution`

PASS requires all of:

- the verbatim original request, resolved family set, absolute dates, resolution
  record and execution intent are frozen in the Run and a same-Run artifact;
- dates are real, `start <= end`, and `end` is not later than the execution date in
  `Asia/Shanghai`;
- families are supported or unambiguous aliases, with no unknown or ambiguous name;
- relative expressions have a complete Calendar basis and a proved anchor, and any
  anchor used for a relative resolution is a CFFEX open date not later than the
  execution date; explicit dates need no anchor but must record that the Calendar was
  not used for resolution.

FAIL if a supplied input is invalid, unsupported, ambiguous or future-dated, or a
relative-resolution anchor is not a CFFEX open date. BLOCKED if a required input is
missing, relative resolution cannot prove the Calendar/anchor, or execution intent is
not established. Never guess.

### 6.2 `basis_acquisition`

PASS requires all of:

- `input_resolution` PASS and a separate execution authorization reference;
- exactly one public product invocation per requested family;
- every family returns a successful result;
- lossless actual results, `source_identity`, actual first/last dates, observation
  counts, coverage evidence and family-level failures are preserved;
- no fabricated, zero-filled or substituted values.

FAIL if any family returns a classified error, or the acquisition evidence is missing
or inconsistent. Successful families remain preserved. BLOCKED if `input_resolution`
is not PASS, execution authorization is absent, or a prerequisite prevents an
authorized attempt.

Coverage completeness is recorded here but is not required for `basis_acquisition`
PASS: a successful product call with `verified_partial` coverage still passes
acquisition and fails or blocks delivery later. A failed family makes this Gate FAIL,
not PASS-with-partial.

### 6.3 `result_delivery`

PASS requires all of:

- `result.json`, `basis_daily.csv` and `REPORT.md` exist in the same Run;
- `result.json` is mutually consistent with the acquisition evidence and the CSV;
- every requested family succeeded and every family coverage is `verified_complete`;
- CSV header, row count, rows, dates, slots and values match the lossless acquisition
  data exactly;
- the report contains all required sections, per-family latest dates and four-slot
  values, source/formula/units, near-expiry caveat and limitations;
- no partial or unverified scope is presented as complete;
- `verification.json` records all checks and passes.

FAIL if outputs are missing or inconsistent, coverage is `verified_partial`, slots or
rows are inconsistent, or the report claims unsupported completeness. BLOCKED if
`basis_acquisition` is not PASS or expected-session verification is unavailable
(`unverified` coverage). When `basis_acquisition` PASS and both a known
`verified_partial` family and an `unverified` family exist, FAIL takes precedence over
BLOCKED; report both families explicitly.

`verification.json` must record at least:

- artifact identity/digest checks through a fresh RunStore read;
- exact CSV header and deterministic order;
- CSV row count equals the sum of successful family `observation_count`;
- every CSV row matches a lossless acquisition observation, and no acquisition row for
  a successful family is missing;
- each successful family's observed `trade_date` has exactly one `M0`, `M1`, `Q1` and
  `Q2` row; a missing or duplicate slot is a contract inconsistency and fails delivery;
- every successful family's `source_identity`, first/last date, counts and missing
  dates match `result.json`;
- `original_request`, `resolved_inputs`, `task_id`, `task_version` and `task_sha256`
  in `result.json` match the frozen Run manifest;
- overall/coverage status matches section 4.3;
- report required sections are present, each successful family's latest date and four
  slot values appear with the same decimal strings as the CSV, and its `Overall
  status:` / `Coverage status:` lines match `result.json`.

A Gate PASS is valid only with same-Run registered evidence. The recorder hashes bytes;
the executor remains responsible for truthfulness and criteria evaluation. No Gate
outcome is created by G1.

## 7. G2 implementation contract and status

G2 implements Task-local `runtime/run_monitor.py` and deterministic tests under
the existing `workbench/tests/` layout. Live acceptance has not been performed.
The frozen Task scope retains the G1 approval-stage status; it does not deny the
subsequent G2 implementation or authorize live execution.
Use the existing root Python environment; do not
create a package, environment, server, database, CLI command or scheduler.

Required sequence:

1. Load the exact [task.json](../task.json) and resolve the canonical inputs,
   including the Calendar anchor/coverage when required. Resolution that needs
   market access happens only under the separate execution authorization.
2. Create the Run with the frozen snapshot, verbatim `original_request` and the
   canonical resolved inputs. If resolution was blocked or failed, freeze the
   attempted inputs and explicit blocker; do not invent resolved values.
3. Register `resolution.json` and Calendar evidence; record `input_resolution`.
4. Verify the separate execution authorization for acquisition; if absent, record
   `basis_acquisition` and `result_delivery` BLOCKED and perform no market request.
5. Invoke the public product once per family; preserve lossless results and classified
   failures.
6. Build and register `basis_daily.csv`; build the acquisition summary and record
   `basis_acquisition`.
7. Build and register `result.json` and `REPORT.md`; run the consistency checks and
   register `verification.json`; record `result_delivery`.
8. Read the Run back with the existing public `read` operation and verify the frozen
   Task, same-Run evidence, artifact digests and Gate outcomes.

G2 tests must be deterministic and use fake public product/Calendar services; they
must not call Tushare. Cover at least:

- complete success with all families and `verified_complete` coverage;
- one family failing while others succeed (acquisition FAIL, delivery BLOCKED,
  successful data preserved);
- all families failing (overall failed, header-only CSV, explicit failures);
- an expected session missing, including the latest expected session (verified
  partial, delivery FAIL, recent gap explicit);
- incomplete/unavailable Calendar for an explicit range (unverified, delivery
  BLOCKED);
- relative input without a complete Calendar (input_resolution BLOCKED);
- unknown/ambiguous family, invalid date and future end date (input_resolution FAIL);
- window starting before listing (effective window intersection, pre-listing not
  missing);
- CSV/result/report inconsistency detection and same-Run artifact ownership;
- no Git-visible market data and no mutation of the Task snapshot.

G2 acceptance is not satisfied by a successful Python call alone. It requires the
actual public results, exact CSV/result/report consistency, coverage classification
with evidence, and same-Run Gate outcomes. Live smoke with real Tushare data is a
separate, explicitly authorized activity and is not part of G1.

## 8. Non-goals and versioning

The G1 approval stage implemented no runtime and authorized no Tushare request
or Calendar cache write. G2 implements only the Task-local runtime described in
section 7; actual market access still requires separate explicit user authorization.
These stage distinctions do not modify the frozen `task.json` or existing Runs.

V1 does not implement or authorize:

- a repository CLI command, HTTP endpoint or UI;
- a new Dataset, Snapshot Product, generic Task engine, scheduler or orchestration
  framework;
- charts, statistical distributions, predictions, trading advice, backtests or
  strategies;
- Research Publication or a Research Case;
- a second basis calculator, alternative slot naming, main-contract filtering or
  derived financial indicators.

Any semantic change to the input, output, coverage, failure or Gate contract requires a
new Task version and explicit user approval. Existing Run snapshots and evidence are
never rewritten. Task approval remains separate from execution authorization.
