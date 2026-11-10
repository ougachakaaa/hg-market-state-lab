# Web Workspace navigation and layout authority

This specialized authority follows [application.md](application.md) and [ui-system.md](ui-system.md). It owns the application-level business areas, URL navigation and shell behavior. Feature-specific financial display and request semantics remain with the [feature catalog](FEATURES.md).

## Business areas and readiness

- **Daily Data** exposes the implemented MO Option Chain and MO Premium Plane pages for daily data inspection. It may consume published raw or derived products but never calculates their business values in React. Futures Basis Data Product integration is future work.
- **Research** opens on Research Overview, its authenticated landing and topic-oriented discovery surface. Descriptive Research is a non-interactive navigation category; individual navigation pages represent implemented Web consumers. The overview distinguishes published descriptors, local Python cases and offline report workflows. Research Explorer is a secondary technical reader for existing Publications, evidence and views; it does not execute Research or imply that every topic has a publication. Futures Basis Online Research provides an authenticated execution page at `/research/futures-basis`. R01-A offline report remains independently readable when generated locally.
- **Backtesting** is a Planned destination for the W2 Futures Roll Long workflow. Strategy, real-contract holding simulation, PnL, benchmark and result semantics belong to the [W2 case authority](../market_backtesting/cases/futures_roll_long/ARCHITECTURE.md); `ui_web` will own only interaction and rendering after WP7. Until then it has no strategy engine, simulated trades or result data, and no fake controls/results are shown. React must never calculate PnL, returns, benchmark or drawdown from raw data; it renders producer-owned values.

An online descriptor may be shown as discoverable after its authenticated read consumer is implemented; this does not claim Web execution or live provider readiness. An online execution surface may be shown as available only after its actual consumer and backend are implemented. No false execution controls or mock results are part of these pages.

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
| `/backtesting` | Planned page; W2 WP7 will integrate the producer-backed workflow |

Anonymous visitors see only the existing authentication gate, including on deep links. Normal login enters `/research`; authenticated refresh of a known deep link preserves that route. Browser back/forward and direct reload select the same surface. Unknown routes return to `/research` after authentication. Logging out or a protected-request 401 unmounts all business content and isolates old requests, according to [application authentication](application.md#5-application-authentication-g3-implemented).

The shell uses a collapsible sidebar for the three areas and implemented child pages, a header with breadcrumb and user/logout controls, and a responsive content region. Research and Daily Data each have one overview destination within their navigation group; area headings only expand/collapse and category labels do not navigate. Visible routes select their corresponding leaf. The secondary Explorer route keeps Research active without selecting a leaf. Navigation opens its containing group, and collapsing the sidebar must keep every overview and child page accessible. Separate overview buttons outside the menu are not additional navigation entries.

The header breadcrumb identifies the area and current page, linking the parent to its existing overview. It does not repeat a separate page title; the content surface owns its primary heading. The shell only chooses page entrypoints; feature local state, requests, DTOs, charts and financial semantics stay inside each feature. The dark, near-black visual system uses Ant Design Dark Algorithm and shared tokens; Plotly remains the analytical chart renderer. Layout CSS is limited to concerns that Ant Design primitives cannot express cleanly.

`/research/publications` is both a browser page URL and the published backend GET path. Browser API requests therefore use same-origin `/api/research/publications...`; development and deployment gateways strip `/api` before forwarding to the unchanged backend. The published HTTP/OpenAPI path stays `/research/publications...`. The gateway must serve HTML for direct page navigation and forward the `/api` path with Cookie and query intact. This is a deployment prerequisite, not a new HTTP product.
