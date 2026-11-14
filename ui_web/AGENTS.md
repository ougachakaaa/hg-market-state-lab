# ui_web Agent Rules

## Structural consolidation routing

Directory ownership is defined by [Structure](STRUCTURE.md); current paths, KEEP/MOVE/MERGE/RETIRE decisions and WP1-WP4 gates are in the [WP0 migration audit](STRUCTURAL_MIGRATION.md) and [baseline inventory](STRUCTURAL_INVENTORY.md). These are target/transition authorities, not evidence that migration has executed. For structural tasks read them before existing Demo or specialized tooling contracts.

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
- Repository-level `npm run contract:check` 必须检查所有 frontend-consumed HTTP products 的 committed OpenAPI representation 与 generated TypeScript freshness。

## 验证

- **Core Verification**：当前变更涉及的 TypeScript、Lint、Unit Tests、Build、Contract 和 Python Tests 必须通过。
- **Scoped Integration**：实际受当前变更影响的 Browser / HTTP / Integration Tests 是任务强制门槛。
- **Extended E2E**：其他完整 Online Browser Suites 是扩展回归诊断，不自动阻塞每个开发任务；正式发布、认证安全、权限隔离、数据完整性及任务明确要求的 E2E 仍须满足对应强制验收。此规则不减免正式 Demo 发布、安全扫描或 Artifact Verification 门槛。
- 失败必须按证据区分 `PRODUCT_REGRESSION`、`HARNESS_FAILURE`、`BASELINE_FLAKY`、`ENVIRONMENT_BLOCKED`、`UNDETERMINED`。失败后最多一次干净环境重试；必要时再做一次同环境、同命令的未修改基线对照，保留命令、版本与失败证据，禁止无限重试求 PASS。`BASELINE_FLAKY` 不能仅凭一次通过判定，必须保留失败证据和基线对照；`UNDETERMINED` 不得自动视为无害。
- 非当前任务的可选扩展测试失败可独立记录而不阻塞当前任务；当前任务的必需测试不能通过简单重新分类获得豁免。

在 `ui_web/` 中按影响范围运行，提交前完整验证默认为：

```bash
npm run contract:check
npm run test
npm run build
npm run lint
```
