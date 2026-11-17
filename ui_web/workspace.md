# Web Workspace navigation and layout authority

This specialized authority follows [application.md](application.md) and [ui-system.md](ui-system.md). It owns the application-level business areas, URL navigation and shell behavior. Feature-specific financial display and request semantics remain with the [feature catalog](FEATURES.md).

## Business areas and readiness

- **Daily Data** exposes the implemented MO Option Chain, MO Premium Plane and Futures Calendar Spread pages for daily data inspection. It may consume published raw or derived products but never calculates their business values in React. Futures Basis Data Product integration is future work.
- **Research** opens on Research Overview, its authenticated landing and topic-oriented discovery surface. The overview presents Research Studies as user-facing cards; completion means an independent Web page exists, not backend or provider readiness. Implemented study pages appear directly under Research without methodology categories; studies without a Web page appear only in the overview. Research Explorer is a secondary technical reader for existing Publications, evidence and views; it does not execute Research or imply that every topic has a publication. Futures Basis Online Research provides an authenticated execution page at `/research/futures-basis`. R01-A offline report remains independently readable when generated locally.
- **Backtesting** exposes the implemented W2 Futures Roll Long consumer. The [feature authority](src/features/backtesting/ARCHITECTURE.md) owns the four-field form, advisory preflight, explicit submit, Run polling/restoration and result rendering. Strategy, execution and financial semantics remain with the [W2 case](../market_backtesting/cases/futures_roll_long/ARCHITECTURE.md). React only renders producer-owned results; manual integrated verification enters
[case Evidence](../market_backtesting/cases/futures_roll_long/EVIDENCE.md#explicit-integrated-verification).

An online descriptor may be shown as discoverable after its authenticated read consumer is implemented; this does not claim Web execution or live provider readiness. An online execution surface may be shown as available only after its actual consumer and backend are implemented. No false execution controls or mock results are part of Production pages. Static Demo presents formal FastAPI HTTP business results after Bundle admission under the [Demo authority](demo/ARCHITECTURE.md). Controlled synthetic fixtures belong only to tests. The Bundle runtime and release pipeline are implemented; each publication requires the [Release Runbook](demo/release/RUNBOOK.md) gates and online acceptance.

## URLs and shell

| Path | Surface |
| --- | --- |
| `/` | Authentication gate, then redirect to `/research` |
| `/research` | Read-only Research Overview |
| `/research/publications` | Research Explorer |
| `/research/futures-basis?run_id=<opaque>` | Futures Basis Research; query identity restores server state |
| `/data` | Daily Data landing |
| `/data/mo-option-chain` | MO Option Chain |
| `/data/mo-premium-plane` | MO Premium Plane |
| `/data/futures-calendar-spread` | Futures Calendar Spread (WP7: both runtimes) |
| `/research/calendar-spread-relative-value` | Calendar Spread Historical Relative Value (WP7: both runtimes) |
| `/backtesting` | Backtesting Overview |
| `/backtesting/futures-roll-long?run_id=<opaque>` | Futures Roll Long; query identity restores the immutable server Run |

In Production, anonymous visitors see only the existing authentication gate, including on deep links. Normal login enters `/research`; authenticated refresh of a known deep link preserves that route. Browser back/forward and direct reload select the same surface. Unknown routes return to `/research` after authentication. Logging out or a protected-request 401 unmounts all business content and isolates old requests, according to [application authentication](application.md#5-application-authentication-g3-implemented).

The shell uses a collapsible sidebar for the three areas and implemented child pages, a header with breadcrumb and composition-supplied identity/actions, and a responsive content region. Production supplies user/logout; Demo supplies anonymous disclosure describing the actual formal HTTP capture and provenance limitations without Auth controls. Research, Daily Data and Backtesting each have one overview destination within their navigation group; area headings only expand/collapse and category labels do not navigate. Visible routes select their corresponding leaf. The top-level order is Daily Data, Research, Backtesting. Research shows only Research Overview and implemented study pages directly. Sidebar visibility is independent of route registration: Research Explorer remains in the canonical route inventory at `/research/publications` but is hidden from the sidebar in both runtimes. The overview contains only its heading, Study cards, completion states, available study navigation and minimal footer disclosure. Explorer has no visible navigation entry in this release. All three overviews share AppstoreOutlined; visible instance pages share FileTextOutlined. Area icons remain distinct. At Explorer, the Research group opens and the breadcrumb identifies Explorer; no unrelated visible leaf is selected. Direct access, reload and browser history remain supported. Navigation opens its containing group, and collapsing the sidebar must keep every overview and child page accessible. Separate overview buttons outside the menu are not additional navigation entries.

The header breadcrumb identifies the area and current page, linking the parent to its existing overview. It does not repeat a separate page title; the content surface owns its primary heading. The shell only chooses page entrypoints; feature local state, requests, DTOs, charts and financial semantics stay inside each feature. The dark, near-black visual system uses Ant Design Dark Algorithm and shared tokens; Plotly remains the analytical chart renderer. Layout CSS is limited to concerns that Ant Design primitives cannot express cleanly.

`/research/publications` is both a browser page URL and the published backend GET path. Browser API requests therefore use same-origin `/api/research/publications...`; development and deployment gateways strip `/api` before forwarding to the unchanged backend. The published HTTP/OpenAPI path stays `/research/publications...`. The gateway must serve HTML for direct page navigation and forward the `/api` path with Cookie and query intact. This is a deployment prerequisite, not a new HTTP product.

## Production Run navigation identity

Run navigation memory belongs to one browser tab and one authenticated frontend
Workspace lifecycle. Leaving a Run page through application navigation remembers only
its opaque, nonempty `run_id`, unchanged, separately for `/research/futures-basis` and
`/backtesting/futures-roll-long`. Read the live URL when leaving, including identity
written by an accepted submission since the last application render. An absent or
empty identity clears that route's previous memory. No other route participates.

Ordinary application navigation back to a Run page restores its remembered identity
into the destination URL. Clicking the current page preserves its complete URL and
does not add history. Explicit deep links, reload and browser Back/Forward instead
use their original URL as authoritative, including a URL without `run_id`; memory
must never rewrite them or substitute another route's identity. Existing legacy URL
normalization remains in force. Run IDs are navigation parameters, not cached results
or frontend interpretations of Run status.

Memory is destroyed when the authenticated Workspace ends, including logout or a
protected-request 401, and is not inherited on subsequent login. Full reload, tab
closure and application termination also discard it. No LocalStorage, SessionStorage,
IndexedDB, DTOs, market data, tokens or credentials are retained by navigation.
Server Run lifetime is independent; refresh with an explicit ID uses existing GET
restoration and does not restore unsubmitted form state.

Navigation restoration never creates or resubmits a Run. Features continue to own
GET/POST, polling, validation, cancellation and result presentation. WP-01 retains
navigation identity; WP-02 retains the first-visited Production Backtesting
page instance with React Activity, within the authenticated Workspace only. Other pages
retain conditional mounting and Static Demo does not participate. Application owns
visibility and instance lifetime; the feature owns its form, Run, Result and chart state.
A validated completed Result with matching identity is reused without Run/Result GET.
Hidden pages stop reads and polling; unfinished reads resume against the backend on return.
Read errors retain manual retry. Unconfirmed POSTs are aborted without replay and show
unknown-outcome feedback on return. Workspace teardown destroys retained state.
Retention keeps state only for the matching identity: an explicit
different URL identity must be recognized by the feature and must hide obsolete
results before restoring the selected Run.

## Static routing specialization

The path table above includes ten Production pages; Auth and server Run query behavior apply to Production. Static retains ten admitted page identities: all three overviews and seven business pages using hash routes under `/hg-market-state-lab/`, with default/unknown routes resolving to `#/research`. Its local navigation, deep reload, history and breadcrumb hrefs never escape that base. It neither restores server `run_id` nor calls the `/api` gateway. Report section navigation must coexist with routing. The [Demo authority](demo/ARCHITECTURE.md) owns this static specialization; Production keeps pathname/history routing and authenticated deep links.

## Overview completion and Backtesting navigation

All overview cards show Web page availability with 已完成 in the theme success text
color or 未完成 in secondary gray text. Text remains explicit. This is independent
of cache readiness, Run lifecycle and scientific result status.
Backtesting is a collapsible area with 回测总览 and 期货展期做多回测 as children.
The overview contains one completed card for the implemented case, its concise purpose
and explicit 查看回测 action. It mounts no execution controller and creates no requests.
Production legacy `/backtesting` URLs containing a `run_id` query key redirect with
history replace to `/backtesting/futures-roll-long`, preserving query and fragment.
Bare `/backtesting` opens the overview. Login and history follow the same normalization.

## Route and Bundle identities

The ten Production pages, ten Static pages and nine registered business-result Bundles have independent identities. Overview pages create no additional Bundle. Research Explorer remains directly accessible through its hash route with its Publications Bundle retained. Backtesting M1/Q1 remain two independent Results on the same instance page. Bundle identity is owned by [Bundle authority](demo/BUNDLES.md). The retained StaticWorkspace exhaustively composes all ten paths using shared formal Presentation. DDB-04 owns admitted Bundle adapters and the official runtime/build.

## WP6 transition (historical; Static extended by WP7 below)

WP6 registers `/data/futures-calendar-spread` and
`/research/calendar-spread-relative-value` as independent authenticated Production
surfaces. Production overviews mark only Web delivery complete. Shared route metadata
explicitly distinguishes Production-only pages; Static keeps its eight admitted pages
and seven Bundles until WP7, including unknown-hash fallback for these new paths.

Daily fetches `/api/data/futures-calendar-spread`; gateways must strip `/api`, preserve
Cookie/query/status/body, and keep browser `/data/*` HTML navigation on SPA fallback.
Research uses the existing `/api/research` gateway. No actual Production Nginx site
configuration is tracked here, so local acceptance does not verify deployed routing.

## WP7 admitted Static Calendar Spread

The two Calendar Spread pages now participate in both runtimes. The sole Demo
Registry/Manifest contains nine Bundles and its hash navigation contains ten routes.
Sidebar and both overviews expose the admitted pages. Static composition uses the
WP6 public Presentations after feature validation, with fixed captured product/date
or history window and source disclosure. It mounts no Production query controller.
The eight existing static routes remain present. Capture and static consumption follow
[Calendar Spread integration](demo/CALENDAR_SPREAD.md); this does not publish Pages.
