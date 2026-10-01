# Canonical Study Authority Skeleton

本文件只定义新建 retained Study authority 的标准呈现拓扑与阅读路径。对象含义、cardinality、必需字段和关系由 [Schema](SCHEMA.md) 唯一定义；创建流程由 [Authoring](AUTHORING.md) 拥有。标题和措辞可依 Study 调整，以下文件边界不可省略。

## Mandatory top-level topology

每个新建 retained Study，无论研究复杂度，均须建立以下四个有实质内容的顶层 authority 文件：

```text
studies/<study_package>/
├── ARCHITECTURE.md
├── INPUTS.md
├── METHOD.md
└── RESULTS.md
```

`ARCHITECTURE.md` 不能独自承载新 Study 的完整 authority。四个文件是稳定的顶层导航边界，不要求 Python implementation 具有相同文件布局，也不限制 Study 继续建立下层 specialized authority。

| 文件 | Canonical responsibility |
| --- | --- |
| `ARCHITECTURE.md` | 稳定入口：Identity、Question、scope / purpose、Limitations、Acceptance、具名 Observation / Analysis 与 Evidence Product 的高层概览、dependency gaps 概览、implementation location 和 Authority Navigation。它保持简洁，不重复详细契约。 |
| `INPUTS.md` | 详细 Inputs：目标 population、外部输入与上游 canonical facts、可配置参数及 owner / consumers / semantic role、必填性与默认值、runnable Study 的 CLI / 用户映射、规范化、execution-only options、retained run identity，以及获取输入所需的 dependency gaps。 |
| `METHOD.md` | Method Context（若有）、具名 Observation / Analysis 及其 contract、Observation → Analysis 消费关系、组件有效性与排除规则、Study-local 统计约定，以及适用的 component Artifact identity。 |
| `RESULTS.md` | retained evidence contract：具名 Evidence Products 及其 `defined_by` Analysis、machine-readable 结构、表／图／报告、provenance、复核所需样本与排除计数、空／缺失／排除状态、适用的组件 Artifact 保留方式及 human-readable 呈现。 |

六个 semantic areas 仍由 Schema 定义：Question、Inputs、Method、Results、Limitations、Acceptance。Identity 是 structural information；Authority Navigation 是阅读路径。顶层文件安排不改变这些对象或关系，也不建立新的研究语义。

## Entry and progressive disclosure

打开 `ARCHITECTURE.md` 应能识别 Study 问题与范围、主要输入、具名组件、预期证据、限制和验收，并知道详细契约应读哪里。它必须直接链接 `INPUTS.md`、`METHOD.md`、`RESULTS.md`，并使其他必要的 specialized authority 沿链接可达；读者再按问题进入相关下层文档，不必搜索目录寻找 canonical owner。

Entry 可列出组件和证据名称、概述 dependency gaps，但详细参数与 run identity 只在 `INPUTS.md` 定义，Observation / Analysis mechanics 和统计只在 `METHOD.md` 定义，Evidence Product 结构只在 `RESULTS.md` 定义。每条语义规则只有一个 canonical owner；概览使用 summary + link，不复制完整 contract。

四个顶层文件始终存在；只有更深层的拆分由语义复杂度和阅读边界决定。例如复杂 Method 可从 `METHOD.md` 继续链接 `method/observations/` 与 `method/analyses/` 中的组件 authority；Inputs 或 Results 也可在确有需要时下沉细节。下沉后，顶层 owner 保留清晰概览及导航，所有 specialized owner 均须可达。不得建立空文件、仅作占位的文件或机械的 one-object-one-file 布局。
