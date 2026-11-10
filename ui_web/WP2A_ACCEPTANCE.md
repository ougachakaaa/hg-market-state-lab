# S2-WP2A — Daily Data Query UX acceptance

Date: 2026-11-10 (Asia/Shanghai). Result: **PASS**.
Branch: `feat/web-ui-ux-polish`. Starting HEAD and required baseline:
`6fbec304f2a25edca6432fcf9ea5783d31c267f7`. Initial working tree was clean.

## A. Implementation

The native date inputs are now feature-owned Ant Design DatePickers, with Chinese
calendar labels and an explicit `YYYY-MM-DD` display. Both query areas use the
same observation-date label, control width and compact Form/Space composition.
Premium retains its price selector, with Chinese/Open/High/Low/Close labels and
unchanged enum values. No Search button or shared DatePicker wrapper was added.

Compared with the previous UI, users now see an automatic-query explanation,
Chinese idle/loading/error feedback, the successful response date/price identity,
and instructions for clearing and reselecting after a failure. Loading announces
its request identity and exposes busy semantics; successful result identity comes
from the validated response. Incomplete/impossible dates do not request data.
Premium's legitimate empty presentation explains how to adjust the local view.

One existing result-layout defect surfaced when the browser repeatedly crossed
the shell breakpoint: Plotly could retain a width measured before the sidebar
transition, overflowing the page. A ResizeObserver now synchronizes the Option
Chain chart's layout width with its frame. This is a container-sizing correction;
chart traces, axes, coordinates, colors and financial encoding are unchanged.

Changed files (relative to `ui_web/`):

- `package.json`, `package-lock.json`: declare the already installed Day.js dependency directly.
- `src/features/mo_option_chain/components/OptionChainControls.tsx`,
  `components/OptionChainResults.tsx`, `page/OptionChainPage.tsx`,
  `charts/CombinedExpiryChart.tsx`: query UI, feedback and sizing correction.
- `src/features/mo_option_premium/components/PremiumControls.tsx`,
  `components/PremiumResults.tsx`, `page/PremiumPlanePage.tsx`: query UI and feedback.
- Both features' `visualization.md`: narrow input/feedback clarifications.
- Both features' Page tests, `src/app/App.test.tsx`, `src/test/datePicker.ts`:
  real DatePicker keyboard/clear interactions and query regression coverage.
- `scripts/auth_browser_smoke.mjs`, `scripts/daily_data_copy_export_browser.mjs`:
  updated interactions, invalid-input/calendar checks and screenshot evidence.
- `WP2A_ACCEPTANCE.md`: this execution report, not semantic authority.

## B. Semantic verification

- Automatic queries remain unchanged: a valid confirmed date loads automatically;
  clearing returns to idle; Premium price changes query only with a selected date.
- HTTP identity/serialization are unchanged: Option Chain uses
  `target_trade_date`, fixed MO/close; Premium uses `as_of`, fixed MO and the
  selected price type. DatePicker formats the local calendar date directly,
  without UTC/ISO conversion or date restrictions.
- Existing hooks and API adapters are unchanged. Abort handling, stale-response
  guards, old-result invalidation and validated-response boundaries are retained.
- Presentation controls remain local. Option Chain expiry resets and preserved
  viewport/colors, and Premium presentation resets, retain their existing behavior.
- Copy/Export remain current-success-only. Complete Raw/Context JSON, CSV order,
  null/zero/absent distinctions, filenames, precision and download lifecycle are
  unchanged. No backend DTO, financial calculation or generated artifact changed.
- Empty projection is distinguished from failure. In particular, HTTP 200 Premium
  with `points=[]` still fails validation and offers no Copy/Export actions.

## C. Executed validation

Commands below ran in `ui_web/`, except Git commands at repository root.

| Category | Executed command | Result |
| --- | --- | --- |
| Contract | `npm run contract:check` | PASS: all six products' OpenAPI/TypeScript artifacts current |
| Unit/integration | `npm test -- --reporter=dot src/features/mo_option_chain/page/OptionChainPage.test.tsx src/features/mo_option_premium/page/PremiumPlanePage.test.tsx` | PASS: 56 tests before two additional invalid-input/identity cases |
| Unit/integration | `npm test` | Initial full run: 352 passed, one color-control test timed out during concurrent verification |
| Unit/integration | `npm test -- --maxWorkers=2` | Final PASS: 39 files, 353 tests; 61.51 s; assertions/timeouts unchanged |
| Build | `npm run build` | PASS; existing large-bundle warning remains |
| Lint | `npm run lint` | PASS |
| Diff | `git diff --check` | PASS |
| WP1 preflight | `npm run test:auth-browser` | Initially blocked by occupied developer ports; rerun below passed |
| WP1 preflight/final | `node scripts/.wp2-auth-preflight.mjs` | PASS before implementation and after final changes |
| WP2-A browser | `node scripts/.wp2-daily.mjs` | Final PASS: real Chromium 156.0.8078.4, both products, 24 product requests, no page errors |

The existing scripts refuse occupied ports 8011/5173. Existing developer services
were preserved. Temporary copies used backend 18011/frontend 15173 and a copy of
Vite configuration with the corresponding proxy targets/port. No assertions,
fixtures, authentication or lifecycle checks were bypassed. Those copies and
config are retained in `/tmp/wp2a-validation-tools/`; the temporary files were
removed from the repository after execution. They correspond respectively to
`test:auth-browser` and `test:daily-data-copy-export-browser`.

Logs: `/tmp/wp2-contract.log`, `/tmp/wp2-tests-final.log`,
`/tmp/wp2-build-final.log`, `/tmp/wp2-lint-final.log`,
`/tmp/wp2-auth-final.log`, `/tmp/wp2-browser-final.log`.

Browser coverage includes actual calendar selection and clearing at both sizes,
keyboard confirmation, impossible/incomplete input without I/O, price changes
with/without a date, query/result separation, loading/error/recovery, late-response
protection, presentation independence, real Clipboard/download contents and
Copy/Export availability. Auth/Cookie/CLI are real; market providers are deterministic
fixtures. This is not real-market-data validation.

## D. Browser and visual evidence

Before: `/tmp/s2-wp1-shell-TAHh45/`.
After shell regression: `/tmp/s2-wp1-shell-XkyDzf/`.
Final WP2-A evidence: `/tmp/daily-data-evidence-ZUNYOO/`, including
`acceptance.json`, real exports and 20 screenshots.

Screenshot filenames in the final evidence directory are the Cartesian product:

- Prefix: `mo-option-chain` or `mo-premium-plane`.
- State: `idle`, `calendar`, `loading`, `success`, `error`.
- Size suffix: `1440.png` (1440×900) or `1024.png` (1024×768).

For example: `mo-option-chain-success-1440.png`,
`mo-option-chain-calendar-1024.png`, `mo-premium-plane-success-1440.png`,
`mo-premium-plane-error-1024.png`.

Manual inspection covered both products' success screenshots at both sizes and
representative calendar/loading/error screenshots, plus baseline screenshots.
The query area, status and result toolbar remain readable and unclipped. Chinese
calendar typography is correct. Automated overflow checks pass at both widths,
including resizing a loaded result across sidebar transitions. No remaining
blocking query-area visual defects were found. Existing English presentation
controls/summary labels outside the query scope remain for later work. Existing
Ant Design List deprecation and bundle-size warnings are non-blocking.

## E. Authority reconciliation

The stable entry → UI system/presentation → feature authority hierarchy remains
intact. Before implementation, each feature's existing input section received a
small clarification for valid calendar confirmation, incomplete-input suppression,
request/response identity feedback and clear/reselect recovery. Existing lifecycle,
empty-result, financial and Copy/Export semantics already covered this change.
The sizing fix implements the existing containment/responsiveness requirement.
No competing authority, global feature semantics or new UI design document was
introduced. No unresolved authority drift was found.

## F. Assessment

**PASS. No blocking issues. WP2-A can close and WP2-B can start.**
WP2-B was not implemented. No merge into `develop` or remote push was performed.
