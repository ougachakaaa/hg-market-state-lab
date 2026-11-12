# WP4 deployment acceptance

Local validation and repository preflight on 2026-11-12. This is the evidence
snapshot committed **before the first workflow push**; the WP4 delivery report
records the resulting run and deployment outcome. This document does not claim a
Live Demo or substitute local Vite preview for public Pages acceptance.

## Repository preflight

- Local and remote `feat/github-pages-demo` both at the requested WP3 baseline
  `2c1ed5b8e6e927ed44d69df25cd556c513d7bbd8`; initial worktree clean.
- Repository `ougachakaaa/hg-market-state-lab` is public; default branch `main`.
  Remote `main` and `develop` both at `c68ba9af4194a51ceb3f7e06fd8f445d18d7dab6`.
- Connected GitHub repository metadata reports admin/push permission. SSH remote
  reads succeed. Actual push/workflow permission is established only by the push/run.
- Public Actions API returns HTTP 200 and one active dynamic Dependency Graph
  workflow; no existing Pages workflow. No local `.github/` existed.
- Public `/pages`, `/environments/github-pages` and its branch-policy endpoint
  return HTTP 404. These responses do not establish authenticated settings state.
  Actions permission and branch protection reads return HTTP 401.
- The connected GitHub plugin offers no Pages/Environment settings operation;
  `gh` is unavailable. No settings or protection rules were modified and no PAT
  was created. Pages Source and deployment-branch eligibility require the owner
  to verify the [documented settings](README.md#repository-setup).
- HTTP GET to the target `https://ougachakaaa.github.io/hg-market-state-lab/`
  returns **404** before deployment. Public availability is **BLOCKED** at this
  snapshot; the address is a target, not a verified Deployment URL.

## Implementation and local checks

Node 22.23.2 / npm 10.9.8. Workflow versions checked against the official Actions
release APIs and tagged `action.yml` files: checkout 7.0.1, setup-node 7.1.0,
configure-pages 6.0.0, upload-pages-artifact 5.0.0, deploy-pages 5.0.1.

| Check | Result |
| --- | --- |
| `npm ci` | PASS; lockfile unchanged |
| `npm run demo:build` | PASS; independent npm-only build, fixed subpath retained |
| `npm run test -- src/demo/futures_basis/fixture.test.ts` | PASS; 6 fixture tests |
| `npm run test:demo-browser` | PASS; real Chromium against built local static preview |
| Reader/disclosure/chart interactions | PASS locally; six sections, full synthetic disclosure, history, Plotly zoom/pan/reset/hover/legend, Trading/Calendar Days, Metric/Slot, paired statistics |
| Anchors/refresh/mobile | PASS locally; section anchors, subpath reload, desktop/mobile layouts |
| Network isolation | PASS locally; only HTML and three same-origin subpath assets, no API/Auth/external requests, cookies, resource or console errors |
| Invalid fixture | PASS locally; real validator rejects data and displays error |
| Workflow static validation | PASS; checksum-verified actionlint 1.7.12, `-shellcheck=` (workflow run commands are simple npm invocations) |
| Pages artifact directory/archive inspection | PASS; only regular single-link files, no symlinks, root index and assets; archive listing below |
| HTML resource paths | PASS; `/hg-market-state-lab/assets/` prefix, referenced files exist; no root `/assets/` URLs |
| Public-data/credential review | PASS within scope; committed synthetic fixture retained; no private/runtime inputs added; emitted files checked for credential markers and local addresses/paths |
| `git diff --check` | PASS before commit |
| Formal application regression suite | NOT RUN in WP4; no application, reader, dependency, contract or production build changes |

`npm ci` reported six advisories in the unchanged dependency graph (three moderate,
three high); no dependency upgrade is included in this deployment-only change.
Vite retains its existing Plotly bundle-size advisory; the build succeeds.

Local browser evidence: `/tmp/wp3-demo-browser-fotnHu/acceptance.json` and adjacent
screenshots (temporary, untracked). Simulated Pages tar:
`/tmp/wp4-artifact-ckxYBG/artifact.tar` (temporary, untracked).

```text
./index.html                       656 bytes
./assets/index-rLevCPax.js      5657330 bytes
./assets/index-O9sVkxwP.css         320 bytes
./assets/fixture-Bcc40onc.js     589033 bytes
```

The upload path is exclusively `ui_web/dist-demo/`. No root repository, production
`dist/`, `.env`, database, dataset, Python cache or test evidence is in the artifact.

## Remote acceptance at commit time

| Item | Status |
| --- | --- |
| Workflow run | NOT RUN at commit time; inspect [Demo workflow runs](https://github.com/ougachakaaa/hg-market-state-lab/actions/workflows/deploy-demo-pages.yml) after push |
| Pages Source | UNVERIFIED; owner must check GitHub Actions source |
| Environment deployment restrictions | UNVERIFIED; no protection changed |
| Deployment status / returned Deployment URL | NOT RUN / unavailable at commit time |
| Public HTTP | FAIL preflight: target returns HTTP 404 |
| Public HTML/assets/disclosure/history/chart/Metric/Slot/network browser checks | NOT RUN; no publicly available demo at preflight |

If the first run fails at Configure Pages, the owner must select **Settings →
Pages → Build and deployment → Source → GitHub Actions**, inspect Environment
eligibility without weakening protections, then **Re-run all jobs**. Do not add a
PAT or deploy production application files. See the [Deployment guide](README.md#deployment-guide-wp4)
for exact settings, review/branch restrictions and other failure diagnosis.

WP5 may proceed with portfolio preparation and final reconciliation planning.
Final release/public portfolio acceptance requires successful Pages deployment and
public browser evidence, then an authorized trigger transition to `main` and
release. No merge, rebase, new branch or force push belongs to WP4.
