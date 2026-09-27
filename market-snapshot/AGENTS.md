# market-snapshot Agent Rules

## 适用范围

本文件适用于 `market-snapshot/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 Product ownership、执行角色、Source Facts / optional persisted Raw 与 public boundary。
2. 通过 [CAPABILITIES.md](CAPABILITIES.md) 选择 owning Product 或真正共享的 capability entry。
3. 从 bounded context 的 `ARCHITECTURE.md` 进入当前任务所需的 specialized authority：
   - 共享 Capture identity 或 Source fact → `src/market_snapshot/capture/ARCHITECTURE.md`；
   - 产品 Source scope、Raw、universe 或 completeness → 产品 `data.md`；
   - 产品专属 formula、read model、Point、null/zero、grouping 或 ordering → 产品 preparation/read/backend authority；已在 catalog 登记的共享 Preparation semantic → 该 shared capability authority；
   - application request/result、orchestration、semantic failure、public Python entry 或产品输出契约 → owning Product authority；
   - endpoint、DTO projection、HTTP error/status 或 OpenAPI → [backend-api authority](../backend-api/ARCHITECTURE.md)。

不要为了局部任务读取 sibling product authority。只有处理跨模块 contract 或 presentation reconciliation 时才进入 `web-ui/` authority；backend Source Capture 任务不需要 frontend Guide。

## 执行规则

- Python 以 3.13 为目标版本；Poetry environment 与 dependency graph 由 repository root 统一拥有。所有 Python tooling 从仓库根目录执行，并以 `market-snapshot/` 路径限定本模块范围。
- 业务语义变更先修改 narrowest canonical authority；共享 Source fact 与产品 scope 必须分别落在其 owning authority，不能在实现注释或 catalog 中创建平行定义。
- 用户或 Agent 请求 Product 结果时，从 [CAPABILITIES.md](CAPABILITIES.md) 进入 owning Product，并遵循其支持的 public/application boundary；不自行逐个编排 Capture。
- 不读取 sibling product 的 Raw Artifact 或最终产物，除非对应产品 authority 明确声明该依赖。
- 不在 Source Capture 中实现 analyzer-specific filtering、join、formula 或市场判断；不在 delivery adapter 中重算 domain semantics。
- `.env`、`data/raw/**`、`data/snapshots/**` 与 `output/**` 是本地 runtime artifacts，不得提交；只保留仓库已跟踪的 placeholder。

## 验证

在 repository root 按影响范围运行，提交前本模块完整验证默认为：

```bash
poetry run pytest market-snapshot/tests
poetry run ruff check market-snapshot
poetry run mypy market-snapshot
```

若 `backend-api` HTTP DTO 或 OpenAPI 发生变化，还必须按 [../backend-api/AGENTS.md](../backend-api/AGENTS.md) 与 [../web-ui/AGENTS.md](../web-ui/AGENTS.md) 执行 transport/frontend contract 检查。
