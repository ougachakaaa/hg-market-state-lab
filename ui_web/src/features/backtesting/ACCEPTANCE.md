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
