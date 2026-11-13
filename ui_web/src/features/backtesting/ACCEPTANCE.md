# WP7 acceptance evidence

**WP7 PASS — 2026-11-12.** No open WP7 implementation drift or blocking semantic decision.

Verification uses Linux Chromium, synthetic public-service inputs and temporary Auth
and Run stores. No real-market WP8 acceptance is claimed. The feature and generated
contract owner are [Backtesting](ARCHITECTURE.md).

## Verified behavior

`npm run test:backtesting-browser` exercises real Chromium → Vite same-origin proxy →
FastAPI → actual online worker → public-service fixtures → producer BacktestResult →
React/shared ChartView/Plotly. Auth uses real registration, CLI approval and Cookie;
a second owner is provisioned through the public Auth service, approved by CLI and
logs in through HTTP. It does not bypass the Auth gate.

Both profiles use the accepted artificial five-session public-service fixtures from
`market_backtesting/tests/public_input_fixtures.py`, including real-format contract
identities IM2503.CFX → IM2504.CFX (M1) / IM2506.CFX (Q1). Producer total PnL is
22,000 / 19,000 CNY respectively. These fixtures are not a real market calendar.
The feature-local JSON test fixture is a serialized producer build_backtest_result
from the same accepted public-service fixture, never production page content.

The browser verifies four empty required controls; no Run from Preflight or Enter;
explicit submission and PENDING admission; real RUNNING/COMPLETED polling; both
actual Plotly Views with unchanged numerical coordinates, percent axes and events;
Trades/Rolls and fingerprint; URL refresh/Back/Forward; busy without a second Run;
advisory incomplete readiness; accepted-but-lost POST without replay; read_busy and
manual Result retry; authenticated foreign/missing indistinguishability; small-screen
containment; expired 401 gate and empty browser storage.

Terminal FAILED/INTERRUPTED, status network failure, corrupt/oversize/unavailable
Result and invalid HTTP body are additionally injected at the HTTP response boundary
to verify safe presentation and manual GET recovery. This fault injection is separate
from the successful worker-driven pipeline. Synthetic success does not prove provider
freshness, real-market completeness, Windows backend support or production deployment.

Reproducible evidence defaults to `/tmp/wp7-backtesting-browser/`: `acceptance.json`
and M1/Q1/mobile screenshots. Temporary credentials, Auth database and Run store are
removed when the script exits. No runtime result or credentials are committed.

## Verification record — 2026-11-12

| Check | Actual result |
| --- | --- |
| `npm run contract:generate` / `contract:check` | PASS; all seven OpenAPI/TypeScript pairs current, six existing pairs unchanged |
| `npm run test` | PASS; 47 files, 427 tests, including 42 feature tests |
| `npm run build` / `lint` | PASS |
| `poetry run pytest ui_http/tests -q` | PASS; 588 tests |
| `poetry run pytest market_backtesting/tests -q` | PASS; 527 tests |
| Snapshot authority topology + HTTP architecture + Web contract exporter | PASS; 28 tests |
| DataLake / Research boundary regression | PASS; 15 tests |
| Ruff (`market_backtesting`, `ui_http`, `ui_web/scripts`) | PASS |
| Mypy (`market_backtesting` / `ui_http`) | PASS; 48 / 62 source files |
| `npm run test:backtesting-browser` | PASS; real Chromium, both profiles and failure/ownership/recovery matrix |
| Auth / Research / Visualization browser scripts | PASS; real Chromium |
| Daily Data copy/export / Futures Basis online browser scripts | PASS; real Chromium |

The browser scripts retain ordinary pre-existing Ant Design List deprecation notices;
build retains the existing large Plotly/application bundle warning. Neither changed
wire or financial semantics. Narrow chart containers allow horizontal scrolling on
phones to preserve readable plotting geometry without document overflow.

`git diff --check` and final authority navigation checks pass.
Full diff review includes generated ownership, no sibling semantic imports, no
financial computation, no production fixture import, no credentials/runtime results,
and unchanged producer/HTTP implementation.

## Remaining boundary

WP7 did not execute the real IM 2024-01-01 through 2026-10-30 or Windows Chrome → WSL
gate. Subsequent actual results belong to the independent
[WP8 acceptance record](../../../../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md).
No JSON/CSV export, Copy for GPT, offline evidence
download, new financial metrics, costs, margin or strategy changes were introduced.

## UI-WP01 date-axis presentation acceptance — 2026-11-13

The cumulative return and drawdown charts now share one default `Trading Days` /
`Calendar Days` control as required by the
[date-axis presentation authority](../../../DATE_AXIS_PRESENTATION.md). The domain is
`BacktestResult.daily[].trade_date` in result order, memoized once per Result; both charts
receive the same `RenderOptions.ordinalDates`. This is local presentation state: no Run
identity/request change, no GET/POST/preflight, no URL/browser storage, and no change to
producer values or evidence. A different Run remounts `Result` and restores the default.

Executed in `ui_web/`, on Windows with Chrome 157.0.8103.39 through the existing
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` override because Playwright's bundled Chromium was
not installed (the browser install was not added to the repository).

| Check | Actual result |
| --- | --- |
| `npm run contract:check` | PASS; all seven committed OpenAPI/TypeScript pairs current |
| `npm run lint` | PASS; 0 warnings, 0 errors |
| `npm run build` | PASS; TypeScript + Vite; existing large-bundle warning remains |
| `npm test -- --maxWorkers=1 --testTimeout=15000` | PASS; 52 files, 457 tests |
| `npm run test:backtesting-browser` | PASS; full pre-existing lifecycle matrix plus the new date-axis checks |
| `npm run test:futures-basis-online-browser` | PASS; W1 historical date axis unchanged |
| `npm run test:futures-basis-report-browser` | PASS; offline W1 reader unchanged |
| `npm run test:visualization-browser` | PASS; generic renderer defaults and interactions unchanged |

A plain parallel `npm test` twice hit the pre-existing MO Premium Plane 5-second timeout
under concurrent suite load; that file passes in isolation and the documented serial run
above passes all 457 tests. No test or timeout configuration was changed.

The running development services occupied default ports 8011/5173, so browser gates used
temporary copies with backend 18011 / frontend 15173 and a corresponding Vite config,
following the [WP2A precedent](../../../WP2A_ACCEPTANCE.md). Assertions, fixtures,
authentication and lifecycle checks were not modified; the port-adjusted copies were
deleted after execution and the developer services were preserved. The committed
`backtesting_browser_acceptance.mjs` keeps the canonical 8011/5173 ports.

Date-axis browser evidence: both charts use ordinal `linear` x positions in Trading Days
and raw dates with a `date` axis in Calendar Days; entry/roll/exit shapes and annotations
align; the 31-day non-session interval spans one equal step in Trading Days but more than
5× a one-day interval in Calendar Days; mode switches reset the horizontal viewport to
the full new-coordinate-system range, preserve legend selection, keep tooltip dates and
support Zoom/Pan/Reset; repeated switching produced no extra request, no state change and
identical y values. Evidence: `acceptance.json` with `status: PASS` and `errors: []`,
plus `date-axis-trading.png` and `date-axis-calendar.png` in the disposable output
directory (`/tmp/wp7-backtesting-browser` by default).
