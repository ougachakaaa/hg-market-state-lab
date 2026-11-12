# Backend-free Historical Basis Demo

WP3 provides one static page for **股指期货历史基差研究**. It consumes the
committed WP2 `futuresBasisDemoFixture`, validated through `validateReportData`,
and reuses the six-section Futures Basis `Report`, ChartView / Plotly and shared
Ant Design application theme. Financial values are never calculated in the browser.

The page contains a public header, case introduction, prominent synthetic notice,
interactive report and source / README footer. The synthetic label remains visible
while scrolling. Narrow screens can scroll within chart frames and tables. All
three fixture disclosure fields appear verbatim above the report. Loading and
invalid fixture states display no report; a reader error boundary provides an
explicit rendering error.

## Local commands

From `ui_web/`, with the repository's existing Node/npm requirements:

```bash
npm ci
npm run demo:dev
# Open http://127.0.0.1:5173/hg-market-state-lab/

npm run demo:build
npm run demo:preview
# Open http://127.0.0.1:4173/hg-market-state-lab/

npm run test:demo-browser
```

`demo:build` type-checks the demo dependency graph and builds with
`vite.demo.config.ts`. It does not execute Python, generate the fixture, configure
Auth, access Tushare, open a database or start a backend. `dist-demo/` is ignored by
Git and is separate from the formal application's `dist/`. The original `dev`,
`build`, authentication and HTTP proxies are unchanged.

The browser gate builds first and owns a temporary static preview on
`127.0.0.1:4179` (the port must be free). It uses the existing Playwright Chromium
installation, with optional `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`. It writes
screenshots and `acceptance.json` to a printed system temporary directory and
stops its preview/browser. No backend or fixture generator is involved.

## Browser acceptance

The real browser checks built assets at `/hg-market-state-lab/`, refresh, all six
sections, section navigation, original fingerprint, disclosure fields, Metric /
Slot selection, paired tables, Plotly Zoom / Pan / Reset, hover, legend selection
and Trading Days / Calendar Days. Desktop 1440×900 and mobile 390×844 must avoid
page overflow, retain the visible synthetic indicator and support chart scrolling
and selection. Network monitoring rejects non-static, Auth, API and external
requests; console errors, failed resources and Cookie access fail the gate.
A separate fault-injected browser context passes invalid data into the real WP2
parser in the built fixture chunk and checks the visible error and absent report.
There is no failure mode or test-only data path in the application.

Current WP3 results and regression evidence: [Acceptance](ACCEPTANCE.md).

## WP4 deployment handoff

- Continue on the existing long-lived `feat/github-pages-demo` branch; append
  independent WP commits. No per-WP branch, rebase, merge, force push or automatic
  merge to `develop` / `main`.
- From `ui_web/`, run `npm ci` and `npm run demo:build` using a Node version
  supported by the pinned dependencies (locally verified with Node 22.23.2).
- Publish **the contents of `ui_web/dist-demo/`** as the static Pages artifact:
  `index.html` and its `assets/` directory belong at the artifact root. Do not nest
  an extra `hg-market-state-lab/` directory inside the artifact.
- Vite's fixed base is `/hg-market-state-lab/`; emitted assets already include
  that prefix. Keep it when deploying to the repository's Pages subpath.
- This is one HTML page with section anchors, without SPA history routing or
  server rewrite requirements. Refresh at the Pages subpath loads `index.html`.
- Deploy no Python service, Auth configuration, database, secrets or Tushare token.
  The committed fixture is the complete report input. No runtime API origin is needed.
- WP4 owns Actions, Pages configuration, public deployment and deployed-site
  verification. WP3 creates no workflow, performs no deployment and adds no final
  public demo link to the repository README.
