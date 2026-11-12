# Web Workspace navigation and layout authority

This specialized authority follows [application.md](application.md) and [ui-system.md](ui-system.md). It owns the application-level business areas, URL navigation and shell behavior. Feature-specific financial display and request semantics remain with the [feature catalog](FEATURES.md).

## Business areas and readiness

- **Daily Data** exposes the implemented MO Option Chain and MO Premium Plane pages for daily data inspection. It may consume published raw or derived products but never calculates their business values in React. Futures Basis Data Product integration is future work.
- **Research** opens on Research Overview, its authenticated landing and topic-oriented discovery surface. Descriptive Research is a non-interactive navigation category; individual navigation pages represent implemented Web consumers. The overview distinguishes published descriptors, local Python cases and offline report workflows. Research Explorer is a secondary technical reader for existing Publications, evidence and views; it does not execute Research or imply that every topic has a publication. Futures Basis Online Research provides an authenticated execution page at `/research/futures-basis`. R01-A offline report remains independently readable when generated locally.
- **Backtesting** exposes the implemented W2 Futures Roll Long consumer. The [feature authority](src/features/backtesting/ARCHITECTURE.md) owns the four-field form, advisory preflight, explicit submit, Run polling/restoration and result rendering. Strategy, execution and financial semantics remain with the [W2 case](../market_backtesting/cases/futures_roll_long/ARCHITECTURE.md). React only renders producer-owned results; full-window real-market, HTTP and Windows Chrome execution evidence is recorded in [WP8 acceptance](../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md).

An online descriptor may be shown as discoverable after its authenticated read consumer is implemented; this does not claim Web execution or live provider readiness. An online execution surface may be shown as available only after its actual consumer and backend are implemented. No false execution controls or mock results are part of Production pages. Static Demo uses explicitly disclosed, producer-validated Examples under the [Demo Runtime authority](src/demo/ARCHITECTURE.md); these do not establish online readiness.

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
| `/backtesting?run_id=<opaque>` | Futures Roll Long; query identity restores the immutable server Run |

In Production, anonymous visitors see only the existing authentication gate, including on deep links. Normal login enters `/research`; authenticated refresh of a known deep link preserves that route. Browser back/forward and direct reload select the same surface. Unknown routes return to `/research` after authentication. Logging out or a protected-request 401 unmounts all business content and isolates old requests, according to [application authentication](application.md#5-application-authentication-g3-implemented).

The shell uses a collapsible sidebar for the three areas and implemented child pages, a header with breadcrumb and composition-supplied identity/actions, and a responsive content region. Production supplies user/logout; Demo supplies anonymous Synthetic disclosure without Auth controls. Research and Daily Data each have one overview destination within their navigation group; area headings only expand/collapse and category labels do not navigate. Visible routes select their corresponding leaf. Research Explorer is an explicit Research leaf, selected at `/research/publications`, in both runtimes; the overview link remains. This D0 navigation decision supersedes the implemented secondary-route/no-leaf treatment and is implemented in D1. Navigation opens its containing group, and collapsing the sidebar must keep every overview and child page accessible. Separate overview buttons outside the menu are not additional navigation entries.

The header breadcrumb identifies the area and current page, linking the parent to its existing overview. It does not repeat a separate page title; the content surface owns its primary heading. The shell only chooses page entrypoints; feature local state, requests, DTOs, charts and financial semantics stay inside each feature. The dark, near-black visual system uses Ant Design Dark Algorithm and shared tokens; Plotly remains the analytical chart renderer. Layout CSS is limited to concerns that Ant Design primitives cannot express cleanly.

`/research/publications` is both a browser page URL and the published backend GET path. Browser API requests therefore use same-origin `/api/research/publications...`; development and deployment gateways strip `/api` before forwarding to the unchanged backend. The published HTTP/OpenAPI path stays `/research/publications...`. The gateway must serve HTML for direct page navigation and forward the `/api` path with Cookie and query intact. This is a deployment prerequisite, not a new HTTP product.

## Static routing specialization

The path table above is the shared seven-page route identity inventory; its Auth and server Run query behavior applies to Production. Demo retains both overviews and every formal business page using hash routes under `/hg-market-state-lab/`, with default/unknown routes resolving to `#/research`. Its local navigation, deep reload, history and breadcrumb hrefs never escape that base. It neither restores server `run_id` nor calls the `/api` gateway. Report section navigation must coexist with routing. The [Demo authority](src/demo/ARCHITECTURE.md) owns this static specialization; Production keeps pathname/history routing and authenticated deep links.
