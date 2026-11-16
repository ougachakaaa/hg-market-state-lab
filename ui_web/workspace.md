# Web Workspace navigation and layout authority

This specialized authority follows [application.md](application.md) and [ui-system.md](ui-system.md). It owns the application-level business areas, URL navigation and shell behavior. Feature-specific financial display and request semantics remain with the [feature catalog](FEATURES.md).

## Business areas and readiness

- **Daily Data** exposes the implemented MO Option Chain and MO Premium Plane pages for daily data inspection. It may consume published raw or derived products but never calculates their business values in React. Futures Basis Data Product integration is future work.
- **Research** opens on Research Overview, its authenticated landing and topic-oriented discovery surface. The overview presents Research Studies as user-facing cards; completion means an independent Web page exists, not backend or provider readiness. Implemented study pages appear directly under Research without methodology categories; studies without a Web page appear only in the overview. Research Explorer is a secondary technical reader for existing Publications, evidence and views; it does not execute Research or imply that every topic has a publication. Futures Basis Online Research provides an authenticated execution page at `/research/futures-basis`. R01-A offline report remains independently readable when generated locally.
- **Backtesting** exposes the implemented W2 Futures Roll Long consumer. The [feature authority](src/features/backtesting/ARCHITECTURE.md) owns the four-field form, advisory preflight, explicit submit, Run polling/restoration and result rendering. Strategy, execution and financial semantics remain with the [W2 case](../market_backtesting/cases/futures_roll_long/ARCHITECTURE.md). React only renders producer-owned results; full-window real-market, HTTP and Windows Chrome execution evidence is recorded in [WP8 acceptance](../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md).

An online descriptor may be shown as discoverable after its authenticated read consumer is implemented; this does not claim Web execution or live provider readiness. An online execution surface may be shown as available only after its actual consumer and backend are implemented. No false execution controls or mock results are part of Production pages. Static Demo presents formal FastAPI HTTP business results after Bundle admission under the [Demo authority](demo/ARCHITECTURE.md). Controlled synthetic fixtures belong only to tests. Runtime delivery remains DDB-04 work and Build/publication remain BLOCKED.

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
| `/backtesting` | Backtesting Overview |
| `/backtesting/futures-roll-long?run_id=<opaque>` | Futures Roll Long; query identity restores the immutable server Run |

In Production, anonymous visitors see only the existing authentication gate, including on deep links. Normal login enters `/research`; authenticated refresh of a known deep link preserves that route. Browser back/forward and direct reload select the same surface. Unknown routes return to `/research` after authentication. Logging out or a protected-request 401 unmounts all business content and isolates old requests, according to [application authentication](application.md#5-application-authentication-g3-implemented).

The shell uses a collapsible sidebar for the three areas and implemented child pages, a header with breadcrumb and composition-supplied identity/actions, and a responsive content region. Production supplies user/logout; Demo supplies anonymous disclosure describing the actual formal HTTP capture and provenance limitations without Auth controls. Research, Daily Data and Backtesting each have one overview destination within their navigation group; area headings only expand/collapse and category labels do not navigate. Visible routes select their corresponding leaf. The top-level order is Daily Data, Research, Backtesting. Research shows only Research Overview and implemented study pages directly. Sidebar visibility is independent of route registration: Research Explorer remains in the canonical route inventory at `/research/publications` but is hidden from the sidebar in both runtimes. The overview contains only its heading, Study cards, completion states, available study navigation and minimal footer disclosure. Explorer has no visible navigation entry in this release. All three overviews share AppstoreOutlined; visible instance pages share FileTextOutlined. Area icons remain distinct. At Explorer, the Research group opens and the breadcrumb identifies Explorer; no unrelated visible leaf is selected. Direct access, reload and browser history remain supported. Navigation opens its containing group, and collapsing the sidebar must keep every overview and child page accessible. Separate overview buttons outside the menu are not additional navigation entries.

The header breadcrumb identifies the area and current page, linking the parent to its existing overview. It does not repeat a separate page title; the content surface owns its primary heading. The shell only chooses page entrypoints; feature local state, requests, DTOs, charts and financial semantics stay inside each feature. The dark, near-black visual system uses Ant Design Dark Algorithm and shared tokens; Plotly remains the analytical chart renderer. Layout CSS is limited to concerns that Ant Design primitives cannot express cleanly.

`/research/publications` is both a browser page URL and the published backend GET path. Browser API requests therefore use same-origin `/api/research/publications...`; development and deployment gateways strip `/api` before forwarding to the unchanged backend. The published HTTP/OpenAPI path stays `/research/publications...`. The gateway must serve HTML for direct page navigation and forward the `/api` path with Cookie and query intact. This is a deployment prerequisite, not a new HTTP product.

## Static routing specialization

The path table above is the shared eight-page route identity inventory; its Auth and server Run query behavior applies to Production. Demo retains all three overviews and every formal business page using hash routes under `/hg-market-state-lab/`, with default/unknown routes resolving to `#/research`. Its local navigation, deep reload, history and breadcrumb hrefs never escape that base. It neither restores server `run_id` nor calls the `/api` gateway. Report section navigation must coexist with routing. The [Demo authority](demo/ARCHITECTURE.md) owns this static specialization; Production keeps pathname/history routing and authenticated deep links.

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

The eight application pages and seven registered business-result Bundles have independent identities. Overview pages create no additional Bundle. Research Explorer remains directly accessible through its hash route with its Publications Bundle retained. Backtesting M1/Q1 remain two independent Results on the same instance page. Bundle identity is owned by [Bundle authority](demo/BUNDLES.md). The retained StaticWorkspace exhaustively composes all eight paths using shared formal Presentation. DDB-04 owns admitted Bundle adapters and the official runtime/build.

## Planned Calendar Spread L1 surfaces

[Daily Presentation](src/features/futures_calendar_spread/ARCHITECTURE.md) plans
`/data/futures-calendar-spread` under Daily Data;
[Historical Relative Value Presentation](src/features/calendar_spread_relative_value/ARCHITECTURE.md)
plans `/research/calendar-spread-relative-value` under Research. Both are authority
only: they are not registered routes, available pages or completed Study cards.
The current route/Bundle inventory above is unchanged by WP0. Register actual
consumers and update the inventory at WP6; Demo adds the corresponding hash routes
only at its coordinated WP7 Bundle cutover. No application-level financial or
statistical computation is introduced.
