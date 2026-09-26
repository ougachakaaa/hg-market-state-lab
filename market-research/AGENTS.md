# market-research Agent Rules

## 适用范围

本文件适用于 `market-research/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读根 [repository architecture](../ARCHITECTURE.md)，确认顶层 analytical flow、module boundary 与 repository-level Python runtime ownership。
2. 再读本模块 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 Research identity、Snapshot 消费边界以及 scratch / retained-study distinction。
3. 只有任务需要消费 Snapshot data 时，才进入 [market-snapshot architecture](../market-snapshot/ARCHITECTURE.md) 与 [Capability Catalog](../market-snapshot/CAPABILITIES.md)，选择对应 product/application authority；不默认读取 sibling products。
4. 处理 retained study 时，只读取该 study 的 Question、Inputs、Method、Results、Limitations 及其明确链接的最小 authority。

## 执行规则

- Python dependency installation、resolution 与 tooling 必须从 repository root 使用唯一 Poetry environment；进入本目录只切换 semantic authority，不创建 module-local Python project、lock 或 virtual environment。
- Research 只消费 Snapshot 明确支持的 public application/product result。不得导入 Source Capture、Raw Artifact、product-private Preparation 或 persistence internals，也不得通过 `backend-api`、FastAPI 或 HTTP DTO 获取内部业务语义。
- Scratch 可以快速、低约束和 disposable，但不构成 semantic authority、稳定接口或 production dependency。
- Retained study 至少记录 Question、Inputs、Method、Results 与 Limitations；study-specific 细节与该 study 共置，不上提到 module architecture。
- Research finding 是 evidence。未经 human/agent semantic decision 与 canonical authority update，不得把 finding 当作 Modeling semantics、production contract、forecast、decision、signal 或 recommendation。
- 不为假设需求创建 Experiment Engine、Study Registry、Research Repository、promotion framework、backtest framework、research API 或通用 data interface。
- 若真实 Research consumer 暴露 Snapshot public boundary 缺口，先与对应 Snapshot canonical owner reconciliation；不得以跨越模块内部边界作为临时稳定方案。

## 验证

所有验证从 repository root 执行。按实际变更范围选择检查：文档变更至少运行 authority link/topology test 与 `git diff --check`；Research implementation 运行其直接相关测试与 Ruff/mypy 范围；若修改 Snapshot producer contract，还必须按 [market-snapshot rules](../market-snapshot/AGENTS.md) 完成 producer 与 consumer reconciliation 和验证。
