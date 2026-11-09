# Web Workspace work packages

This execution plan follows [Workspace authority](workspace.md). Implement WP0–WP2 on a branch from `2d0cfcff6d61bfd6a557dd578aa272437eabcf70`, with one reviewed commit per WP. Do not implement WP3–WP6 in this round.

| WP | Work | Acceptance |
| --- | --- | --- |
| WP0 — Authority | Reconcile application default, readiness, dark shell and routing; establish this plan. | Workspace discoverable from module authority; no competing DTO, calculation or HTTP semantics. |
| WP1 — Shell | Dark Ant Design shell, route lifecycle, Auth Gate and honest area landing pages. | Anonymous gate, `/research` login default, direct refresh, back/forward, sidebar collapse, logout and 401 isolation; build and focused tests pass. |
| WP2 — Integration | Mount the three implemented pages; use `/api` proxy for Research Publication API; retain feature internals. | All pages and their data states work; charts fit; Chromium navigation and static SPA route checks pass; offline report remains readable. |
| WP3 — Research Catalog & Workspace | Discover supported online/local/report-only research capabilities. | Every catalog entry traces to a real capability or report; no fake execution; Explorer accessible. |
| WP4 — Futures Basis Online Research | Implement existing frontend authority against real HTTP runtime and share R01-A reader. | Genuine run/status/report lifecycle and offline regression pass. If HTTP runtime is unavailable, report dependency without frontend success simulation. |
| WP5 — Daily Data Query & Export | Complete public Futures Basis Data Product path and JSON/CSV query/export experience. | CLI and HTTP delegate to the same owning Application Service with consistent result semantics and no React financial computation. |
| WP6 — Polish & E2E | Refine Planned page, desktop responsiveness, browser and deployment coverage. | Primary pages, empty/error states and offline artifact pass browser regression; build serves from existing static deployment path. |

Deployment gateway configuration is outside this repository. Before WP2 is marked fully deployed, verify its same-origin `/api` rewrite and SPA fallback on the actual gateway. An unavailable gateway makes deployment verification PARTIAL, not PASS.
