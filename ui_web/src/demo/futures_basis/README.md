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

## Deployment guide (WP4)

[`deploy-demo-pages.yml`](../../../../.github/workflows/deploy-demo-pages.yml)
runs on every push to `feat/github-pages-demo`, using a GitHub-hosted Ubuntu
runner and Node 22. It runs `npm ci`, the existing fixture unit checks, and
`npm run demo:build` inside `ui_web/`. Only **the contents of `ui_web/dist-demo/`**
are uploaded: `index.html` and `assets/` are at the artifact root, without another
`hg-market-state-lab/` directory. No production `dist/`, repository files, Python,
Auth, database, runtime cache or secrets are published.

The workflow uses the official checkout, setup-node, configure-pages,
upload-pages-artifact and deploy-pages Actions. Versions were checked against
[official releases](https://github.com/actions/deploy-pages/releases) for WP4;
GitHub's [custom workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
defines the Pages artifact, Environment and OIDC contract. Permissions are only
`contents: read`, `pages: write`, and `id-token: write`. The shared `pages`
concurrency group serializes deployments without cancelling an active deployment.
No PAT or additional Actions Secret is required.

### Repository setup

An administrator must verify these settings; lack of API access is not proof that
they are already enabled:

1. Open repository **Settings → Pages → Build and deployment → Source** and select
   **GitHub Actions**. Do not select a source branch or Jekyll build.
2. Open **Settings → Actions → General → Actions permissions**. Confirm Actions
   and the five official Actions used by the workflow are allowed. If disabled by
   policy, request the necessary access from the administrator; preserve existing
   restrictions. No write access to repository contents or PR permission is needed.
3. Open **Settings → Environments → github-pages → Deployment branches and tags**.
   Inspect the current policy and any required reviewers first. If **Selected
   branches and tags** excludes the demo branch, ask the owner to authorize the
   specific addition, then use **Add deployment branch or tag rule → Branch** and
   enter `feat/github-pages-demo`. Do not switch to **No restriction** or remove
   protections. If **Protected branches only** excludes it, an owner must decide
   how to authorize deployment; do not silently change the policy or branch rules.
   Complete any required Environment review in the Actions run.

### Deploy again and diagnose failures

Push a new commit to the same demo branch, or open **Actions → Deploy demo to
GitHub Pages → select a run → Re-run all jobs** (or **Re-run failed jobs** after
fixing settings). No `workflow_dispatch` is defined: GitHub requires that event's
workflow to exist on the default branch, which is not part of WP4.

Inspect the run's **deploy** job and its **Configure Pages**, **Upload Pages
artifact** and **Deploy to GitHub Pages** steps. The artifact is named
`github-pages`; the Environment link comes from `deployment.outputs.page_url`.
A configure-pages failure usually requires checking Pages Source/permissions;
a rejected or waiting deployment requires checking Environment branch rules and
reviewers. For missing assets, inspect the artifact root and emitted HTML URLs.
The fixed Vite base remains `/hg-market-state-lab/`. This is one page with anchors;
refresh needs no SPA rewrite. No runtime API origin, CDN or remote font is needed.
A build success does not establish that Pages deployed or that public interaction works.

After deployment, record the run, deployment status and returned URL, then check
public HTTP, every HTML-linked asset, disclosure, Historical Basis Reader,
Metric/Slot and chart interactions, refresh/anchors, and network traffic for
API/Auth/external requests. Local preview results must remain separate.
Current evidence and any manual setup blockers: [WP4 acceptance](DEPLOYMENT_ACCEPTANCE.md).

### WP5 release transition

Continue on `feat/github-pages-demo` with independent commits. Do not create a
per-WP branch, rebase, force push or merge into `main`/`develop` in WP4. During
WP5's authorized final reconciliation/release, change `on.push.branches` to
`main`, authorize `main` in the existing Environment policy without weakening
protections, and release the reconciled workflow to `main`. Recheck the production
run and public browser acceptance before labeling a link **Live Demo**. If a manual
trigger is later added, its definition must first be present on the default branch.
