# WP3 static demo acceptance

Verified locally on 2026-11-12 from baseline
`c68ba9af4194a51ceb3f7e06fd8f445d18d7dab6`, on the existing
`feat/github-pages-demo` branch. Initial checkout was clean `develop` at that
baseline; the existing remote demo branch was at the same commit. No history was
reset, rebased or merged. No public deployment was performed.

Environment: Node 22.23.2, npm 10.9.8, Playwright Chromium 156.0.8078.4.

| Check | Result |
| --- | --- |
| `npm run demo:build` | PASS; npm-only type-check/build, static `dist-demo/` output |
| `npm run demo:dev -- --port 5189 --strictPort` | PASS; subpath HTML responds successfully |
| `npm run test:demo-browser` | PASS; real built-static preview at `/hg-market-state-lab/`, refresh and prefixed assets |
| Six shared reader sections and section navigation | PASS; original fixture fingerprint and producer chart coordinates preserved |
| Metric / Slot selection and paired statistics tables | PASS; existing results change with selection; mobile Slot selection also verified |
| Plotly Zoom / Pan / Reset, legend, hover | PASS; mouse interaction through the existing historical acceptance helper |
| Trading Days / Calendar Days | PASS; all three histories, supplied events and legend persistence |
| Synthetic disclosure | PASS; all three WP2 fields verbatim above report, persistent visible label, anchor, no fictional evidence-package links |
| Desktop / mobile | PASS; 1440×900 and 390×844, no page overflow, narrow-screen chart scrolling |
| Requests and authentication isolation | PASS; only same-origin subpath HTML/JS/CSS requested; no Auth, API, external data, Cookie access or stored Cookie |
| Console / resources | PASS; no console errors, page errors, failed resources or HTTP errors |
| Invalid fixture | PASS; injected null enters the real WP2 parser; visible validation error and no report, no uncaught page error |
| `npm run contract:check` | PASS; all existing generated contracts current, none rewritten |
| `npm run test` | PASS; 49 files / 450 tests |
| `npm run build` | PASS; original application output remains `dist/` |
| `npm run lint` | PASS; no warnings in final run |
| `npm run test:futures-basis-report-browser` | PASS; real offline file reader, embedded font, no network, charts / evidence / layouts |
| `npm run test:futures-basis-online-browser` | PASS; existing authenticated online flow, lifecycle/error states, report/chart interaction and logout |

One full unit-suite run while browser/build checks were running concurrently hit
the existing 5-second timeout in an unmodified MO Option Chain color-control test.
The full suite then passed without simultaneous browser gates (450/450), without
changing timeout configuration or the MO tests.

Vite retains its advisory about the existing large Plotly-based bundle. The demo
build succeeds; this is a download-size consideration, not a missing runtime service.
No dependency or lockfile changes were needed. WP2 fixture/validator, production
Vite config, app/Auth code and business/HTTP modules remain unchanged.

The browser gate prints a system temporary directory containing `acceptance.json`
and desktop/mobile, chart, hover and invalid-fixture screenshots. These artifacts
and `dist-demo/` are not committed. Reproduce using the [Demo guide](README.md).

The [WP4 handoff](README.md#deployment-guide-wp4) deploys only the contents of
`ui_web/dist-demo/`. Actions, Pages account configuration and public endpoint
verification are intentionally NOT RUN in WP3 and remain WP4 work. No local
browser acceptance checks were skipped.
