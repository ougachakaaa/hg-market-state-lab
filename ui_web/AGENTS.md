# ui_web Agent Rules

## Directory and Demo routing

[Structure](STRUCTURE.md) owns canonical placement. Current Demo tasks enter
[Demo authority](demo/ARCHITECTURE.md), then its Bundle/build contracts as needed.
[Structural migration](STRUCTURAL_MIGRATION.md) records the superseded transition and
DDB-00 retirement context. Historical inventories are consulted only for a task that
needs their migration evidence.

## 适用范围

本文件适用于 `ui_web/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 presentation ownership、backend contract 依赖方向与下层 authority 路由。
2. Frontend implementation、placement、React hooks、state orchestration、projection、component、chart 或 shared infrastructure 任务读取 [presentation architecture](presentation-architecture.md)。Layer / View contract 或 domain-neutral rendering 还读取 [Visualization authority](VISUALIZATION.md)。
3. Ordinary UI、styling、theme、component selection、layout 或 custom CSS 任务还读取 [UI system authority](ui-system.md)。
4. Application entry、navigation、layout 或 feature composition 任务再读取 [application authority](application.md)；feature 任务从 [frontend feature catalog](FEATURES.md) 进入相关 co-located authority。
5. Generated OpenAPI / TypeScript 或 contract freshness 任务还读取 [contract feedback-loop authority](contracts.md)，再进入 owning feature。
6. 只有 feature authority 明确依赖某项 backend semantics 或 HTTP transport 时，才读取对应 product entry、read/backend authority 或 HTTP contract。

普通 frontend 任务不读取 Source Capture、Raw Artifact、Analysis Preparation internals 或其他无关产品 authority。

## 执行规则

- `ui_web/` 是独立 npm project；依赖、测试、构建和 lint 均在本目录执行。
- frontend 只拥有 request adaptation、presentation state、visual encoding、interaction 与用户可见的 empty/error presentation。
- 不在 frontend 重新推导 product identity、contract universe、price fallback、completeness、financial formula 或 backend null/zero semantics。
- Owning business module authority 定义产品语义，`ui_http` authority 定义 HTTP transport，published OpenAPI 是 wire contract 的机器可读表达；不得手工维护竞争性的 response schema。
- 任一 frontend-consumed product 的 generated artifact 缺失、相对 backend contract 已 stale，或 backend HTTP DTO/OpenAPI 改动时，运行 `npm run contract:generate` 并提交该 product 的 OpenAPI JSON 与 generated TypeScript；其他变更不得无故重写 generated contract。
- Contract freshness covers consumed contracts when selected for a wire/type change; it is not a default gate.

## Scoped verification

Follow the [root verification policy](../AGENTS.md#verification-policy-user-decision-2026-11-14).
Select only directly affected business test files/cases. No default full-module or
cross-module regression, topology, browser, live-data or deployment acceptance.
Retain business invariants and fixtures; record unavailable checks as NOT VERIFIED.
Do not modify real market data or caches to satisfy tests.
