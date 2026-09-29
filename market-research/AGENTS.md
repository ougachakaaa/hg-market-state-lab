# market-research Agent Rules

## 适用范围

本文件适用于 `market-research/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读根 [repository architecture](../ARCHITECTURE.md)，确认顶层 analytical flow、module boundary 与 repository-level Python runtime ownership。
2. 再读本模块 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 Research identity、UI 与 visualization ownership、Snapshot 消费边界以及 scratch / retained-study distinction。
3. 涉及 study-local CLI convention、Research configuration 或 run-directory placement 时，进入 [Research UI authority](ui/ARCHITECTURE.md)；配置 schema 与 resolution 再进入其链接的 specialized authority，具体参数与用法只读对应 Study authority。
4. 只有任务需要消费 Snapshot data 时，才进入 [market-snapshot architecture](../market-snapshot/ARCHITECTURE.md) 与 [Capability Catalog](../market-snapshot/CAPABILITIES.md)，选择对应 product/application authority；不默认读取 sibling products。
5. 新建 Study 时，从 [Study Authority Authoring](studies/AUTHORING.md) 进入 [Schema](studies/SCHEMA.md)，再建立当前 `studies/<study_package>/ARCHITECTURE.md`，沿其导航仅按需读取 specialized、上游数据或机制 authority；不为寻找可复用研究语义而搜索 sibling Studies、`shared/*` 或 implementation。审查 Study 时按需读 [Review](studies/REVIEW.md)；处理既有 Study 的 reconciliation 时按需读 [Compatibility](studies/COMPATIBILITY.md)。处理已有 Study 时，从本模块 architecture 的 retained Study 入口选择其 canonical authority，并沿其 implementation 链接定位 `src/market_research/studies/<study_package>/`；从 implementation 进入时，先读 package `__init__.py` 文档字符串指向的 canonical authority。Study 语义或 artifact 内容只读取对应 Study authority 及其明确链接的最小 authority。

## 执行规则

- Python dependency installation、resolution 与 tooling 必须从 repository root 使用唯一 Poetry environment；进入本目录只切换 semantic authority，不创建 module-local Python project、lock 或 virtual environment。
- Research 只消费 Snapshot 明确支持的 public application/product result。不得导入 Source Capture、Raw Artifact、product-private Preparation 或 persistence internals，也不得通过 `backend-api`、FastAPI 或 HTTP DTO 获取内部业务语义。
- Scratch 可以快速、低约束和 disposable，但不构成 semantic authority、稳定接口或 production dependency。
- 新建 retained Study authority 遵循 Authoring → Schema → 当前 Study 的最小阅读路径；语义审查与未决事项按 Review 处理，既有 Study 的触发式 reconciliation 按 Compatibility 处理。Study-specific 细节留在对应 Study authority，不上提到 module architecture。
- 将每个 retained Study implementation directory 视为小型 bounded module，按 [Study schema](studies/SCHEMA.md) 的 semantic graph 组织实现；不默认把所有逻辑放入 `study.py`。简单 Study 可使用单个 module；复杂 Study 主动检查 semantic cohesion，优先 Study-local decomposition，并保留易读的 orchestration / composition entry。不机械地为每个 Observation / Analysis 建文件，不按行数拆分，也不因 helper 相似而修改 sibling Studies、shared authority 或创建 generic framework。
- Implementation topology review 应能从 Study authority 清晰定位主要 Observation、Analysis、Results 与 orchestration 责任。若修改一个 material component 必须阅读大量无关 Study implementation，应在当前 Study 内 reconciliation；检查不引入固定目录模板或 LOC 限制。
- 当前 Research visualization 由 `market-research` 拥有，默认通过 Python study output 生成并优先保留静态图片；具体图形形式由真实 Study 的研究问题决定。
- Repository `lab research` 是 Research 的 canonical 人类操作入口，只发现并转发到 study-local CLI；参数、Snapshot public-boundary composition、Study invocation、artifact 与 result semantics 由具体 Study 拥有。当前可运行入口见根 [DEVELOPMENT.md](../DEVELOPMENT.md)。
- 新增 runnable retained Study 时，必须同步提供稳定 CLI study ID、符合 [Research UI authority](ui/ARCHITECTURE.md) 的 study-local `cli.py`、记录用法的 canonical Study authority 与 CLI/output tests；不得创建中央 catalog/registry、reflection、entry-point plugin 或动态 registration framework。
- Python static visualization 是阶段性但正式有效的默认策略。除非多个真实 Study 已形成稳定、重复的 visualization pattern，且新的 canonical authority 已明确重新划分责任，否则不得自行迁移至 `backend-api`、`web-ui` 或 Research Viewer。
- Research finding 是 evidence。未经 human/agent semantic decision 与 canonical authority update，不得把 finding 当作 Modeling semantics、production contract、forecast、decision、signal 或 recommendation。
- 不为假设需求创建 Experiment Engine、Study Registry、Research Repository、promotion framework、backtest framework、research API、Research Chart API、generic chart DTO、dashboard / visualization framework 或通用 data interface。
- 未来 Frontend 只消费 Research 定义的 result semantics；不得让 canonical Research Result 输出 Plotly、ECharts、React 或其他 frontend-library configuration。
- 若真实 Research consumer 暴露 Snapshot public boundary 缺口，先与对应 Snapshot canonical owner reconciliation；不得以跨越模块内部边界作为临时稳定方案。

## 验证

所有验证从 repository root 执行。按实际变更范围选择检查：文档变更至少运行 authority link/topology test 与 `git diff --check`；Research implementation 运行其直接相关测试与 Ruff/mypy 范围；若修改 Snapshot producer contract，还必须按 [market-snapshot rules](../market-snapshot/AGENTS.md) 完成 producer 与 consumer reconciliation 和验证。
