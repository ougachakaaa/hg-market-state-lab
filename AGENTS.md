# AGENTS.md

## 项目

项目名称：`hg-market-state-lab`。

本仓库的 Python 项目位于 `market-snapshot/`：Poetry、pytest、Ruff 与 mypy 都在该目录内执行。Python 目标版本为 3.13。

项目架构及当前架构层面的 authority 定义在 `ARCHITECTURE.md` 中。

架构词汇以 `ARCHITECTURE.md` 第 0 节为准：Source、Source Capture、Raw Artifact、Analysis Preparation、Analysis-ready Artifact、Data Service、CLI。`Dataset` / `Snapshot` 不再是通用架构层概念。

## 工作规则

* 使用 Poetry 管理 Python 依赖和虚拟环境（在 `market-snapshot/` 目录内执行）。
* Python 目标版本为 3.13。
* 使用 pytest 进行测试。
* 使用 Ruff 进行 lint 检查。
* 使用 mypy 进行类型检查。
* 不得提交真实 API Token、密码或其他敏感信息。
* 执行 `market-snapshot/guides/` 中定义的 workflow 前，先阅读相关 Guide。
* 当修改涉及数据语义、Source Capture 职责、Analysis Preparation 组织方式或项目结构时，先阅读 `ARCHITECTURE.md`。
* 采用设计先行的工作方式：当任务涉及数据含义、输出结构、职责边界或 workflow 语义变化时，应先建立或更新相关 authority，再进行实现。
* 实现必须遵循当前项目 authority。若实现与 authority 不一致，应明确指出差异并进行 reconciliation，不得静默选择另一套设计。
* 项目 authority 应遵循渐进式披露（Progressive Disclosure）原则：顶层 authority 只描述理解项目所必需的核心目标、语义和边界；更具体的数据需求、执行规则和实现细节应放在对应的下层文档或 Guide 中，并通过明确引用按需读取。不要要求 Agent 在处理局部任务时默认读取与任务无关的全部 authority。
* 优先采用满足当前 authority 和当前任务要求的最小实现。
* 不得为了未来可能出现的需求，主动引入当前任务不需要的框架、抽象、基础设施或新的业务概念。
* 不得实现当前任务显式范围之外的功能。
