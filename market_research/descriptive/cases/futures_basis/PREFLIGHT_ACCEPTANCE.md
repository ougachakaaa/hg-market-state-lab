# Futures Basis preflight acceptance — 2026-11-10

Evidence for [Preflight](PREFLIGHT.md), not an additional semantic authority.
Implemented on `feat/web-ui-ux-polish`; no live Source calls or real cache mutation
were used for validation. WP-P0–WP-P4 are complete within this synthetic Linux scope.

## Implemented boundaries

- Research publishes independent read-only assessment, shared online L1 and safe
  field feedback. Public Calendar Export and Futures/Index Coverage are the only
  upstream operations; no ensure, Run store or execution permit is used.
- HTTP publishes the protected preflight operation and generated OpenAPI; it can
  assess inputs independently of unavailable Run storage.
- Web defaults end date to Shanghai today, debounces checks, invalidates on edits,
  focus and midnight, rejects stale results, blocks today gaps, and requires
  confirmation for historical gaps. Retry first loads/checks the immutable request.
- Run admission still repeats L1 only; final preparation and the scientific,
  completeness, failure and lifecycle contracts remain unchanged.

## Evidence and reproduction

Run Python checks from repository root and npm checks from `ui_web/` (the commands
below use `--prefix` to select that project).

| Check | Result |
| --- | --- |
| `poetry run pytest market_research/tests ui_http/tests data_snapshot/tests/test_authority_topology.py ui_web/scripts/test_export_contracts.py -q` | PASS, 1,767 passed, 1 skipped (47.96s) |
| `poetry run ruff check market_research ui_http` | PASS |
| `poetry run mypy ui_http market_research` | PASS, 164 source files |
| `npm --prefix ui_web run contract:check` | PASS, all consumer artifacts current |
| `npm --prefix ui_web run test` | PASS, 384 tests in 43 files |
| `npm --prefix ui_web run build` | PASS; existing bundle-size advisory remains |
| `npm --prefix ui_web run lint` | PASS |
| `npm --prefix ui_web run test:futures-basis-online-browser` | PASS, real Chromium → Vite → HTTP → synthetic public services |
| `git diff --check` | PASS |

Python assessment tests cover Shanghai date boundaries, 1,096/1,097 days, today
reuse, distinct history/today coverage, missing calendars and skipped downstream
calls, legal historical gaps, closures/zero targets, malformed Coverage, classified
operation/contract failures, safe logs, and unexpected defects. Real public
factories against test-isolated absent databases prove no file creation and no
Source initialization. Complete assessment followed by malformed final Futures
Export still fails formal preparation without an attempted repair.

HTTP tests cover auth/origin ordering, strict requests/size/query rejection,
field-level L1 errors, protected OpenAPI/no 422/no-store, 200 blocked, unexpected
500, and independence from Run storage. Hook/page/API tests cover debounce,
confirmation reset, cancellation/stale responses including query reversion,
midnight/focus recheck, default date, blocked submission, original-request reuse,
explicit Generate, request association and retained reports.

Chromium evidence is written to `/tmp/wp8b-online-browser/` by the existing runner.
It covers a real successful assessment before explicit Generate, polling/report,
busy, refresh/history, lost submission response and auth recovery. A controlled
blocked assessment verifies disabled Generate and no Run POST; a future query is
rejected by the real preflight HTTP endpoint while retaining the previous report.
The blocked browser result is injected; day-specific aggregation is independently
verified through Python public-service fakes. No provider publication timing or
real-market readiness is claimed.

Concurrent validation exposed an existing terminal-state/worker-release test race
(`run_busy` in a subsequent online test); no production lifecycle change was made.
The final backend suite is rerun without the concurrent browser/frontend workload.
The initial Web suite also hit an existing Option Chain timeout; the full final
Web suite passed without test-policy or dependency changes.
