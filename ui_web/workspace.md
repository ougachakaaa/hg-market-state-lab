# Web Workspace navigation and layout authority

This specialized authority follows [application.md](application.md) and [ui-system.md](ui-system.md). It owns the application-level business areas, URL navigation and shell behavior. Feature-specific financial display and request semantics remain with the [feature catalog](FEATURES.md).

## Business areas and readiness

- **Daily Data** exposes the implemented MO Option Chain and MO Premium Plane pages for daily data inspection. It may consume published raw or derived products but never calculates their business values in React. Futures Basis Data Product integration is future work.
- **Research** is the authenticated default workspace. Research Explorer browses existing Publications, evidence and views; it does not execute Research. Futures Basis Online Research has frontend authority but no implemented page in this baseline. R01-A offline report remains independently readable.
- **Backtesting** is a Planned destination. It has no strategy engine, simulated trades, or result data.

A later online capability may be shown as available only after its actual consumer and backend are implemented. No false execution controls or mock results are part of these landing pages.

## URLs and shell

| Path | Surface |
| --- | --- |
| `/` | Authentication gate, then redirect to `/research` |
| `/research` | Research workspace landing |
| `/research/publications` | Research Explorer |
| `/data` | Daily Data landing |
| `/data/mo-option-chain` | MO Option Chain |
| `/data/mo-premium-plane` | MO Premium Plane |
| `/backtesting` | Planned page |

Anonymous visitors see only the existing authentication gate, including on deep links. Normal login enters `/research`; authenticated refresh of a known deep link preserves that route. Browser back/forward and direct reload select the same surface. Unknown routes return to `/research` after authentication. Logging out or a protected-request 401 unmounts all business content and isolates old requests, according to [application authentication](application.md#5-application-authentication-g3-implemented).

The shell uses a collapsible sidebar for the three areas and implemented child pages, a header with current title/breadcrumb and user/logout controls, and a responsive content region. It only chooses page entrypoints; feature local state, requests, DTOs, charts and financial semantics stay inside each feature. The dark, near-black visual system uses Ant Design Dark Algorithm and shared tokens; Plotly remains the analytical chart renderer. Layout CSS is limited to concerns that Ant Design primitives cannot express cleanly.

`/research/publications` is both a browser page URL and the published backend GET path. Browser API requests therefore use same-origin `/api/research/publications...`; development and deployment gateways strip `/api` before forwarding to the unchanged backend. The published HTTP/OpenAPI path stays `/research/publications...`. The gateway must serve HTML for direct page navigation and forward the `/api` path with Cookie and query intact. This is a deployment prerequisite, not a new HTTP product.
