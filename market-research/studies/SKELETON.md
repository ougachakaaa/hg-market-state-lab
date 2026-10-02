# Canonical Study Authority Skeleton

本文件只定义新 retained Study authority 的呈现拓扑与阅读路径。对象、cardinality、必需字段和关系由 [Schema](SCHEMA.md) 唯一定义；创建流程由 [Authoring](AUTHORING.md) 拥有。标题可调整，以下四文件边界不可省略。

## Mandatory top-level topology

```text
studies/<study_package>/
├── ARCHITECTURE.md
├── INPUTS.md
├── METHOD.md
└── RESULTS.md
```

四个顶层文件均须有实质内容，单个 `ARCHITECTURE.md` 或空占位文件不能代表完整 authority。布局不要求 Python implementation 同构，也不限制必要的下层 specialized authority。

| 文件 | Canonical responsibility |
| --- | --- |
| `ARCHITECTURE.md` | 稳定入口：Identity、Question / Objective、scope / purpose、Limitations、Acceptance、workflow / dependencies / execution outcome 与明确声明的 retained outputs / optional Analysis / Evidence 概览、dependency gaps、implementation location 与导航。 |
| `INPUTS.md` | Study request / configuration、Observation invocation bindings、parameter owner / consumers / semantic role、用户表达与 CLI 映射、必填性与默认值、规范化、semantic request identity；retained run identity / output execution-only options 仅适用时定义。 |
| `METHOD.md` | Required workflow / steps、Observation dependency owner / identity / contract references、invocation bindings、resolve / ensure orchestration、Workflow Artifact production / consumption 与 failure / empty semantics；optional Method Context / Analysis。 |
| `RESULTS.md` | Execution outcome / human output、counts / success / empty / failure；明确保留 Workflow Artifact 时另定义 shape / completeness / retention / provenance，Evidence 若存在再定义 `defined_by`、结构 / 表 / 图 / 报告、样本与排除计数。 |

六个必答 semantic areas 仍由 Schema 定义；Identity 是 structural information，Authority Navigation 是阅读路径。Observation empirical population、grain、derivation、validity 和 Artifact schema 不在上述文件重新定义。

## Entry 与 progressive disclosure

Entry 必须直接链接 `INPUTS.md`、`METHOD.md`、`RESULTS.md`，并使必要 specialized authority 可达。读者可辨认 objective、workflow、主要依赖、execution outcome、实际声明的 retained results / optional Analysis / Evidence、限制与验收，再只读相关 owner。Orchestration-only Study 保留四文件，以有实质内容的 runtime RESULTS 回答结果契约，不创建假 Workflow Artifact / Analysis / Evidence。

Detailed request / identity 归 INPUTS，workflow / step order、dependency composition 与 optional Analysis mechanics 归 METHOD，runtime outcome 与实际声明的 Workflow Artifact / retained result / Evidence structure 归 RESULTS。通用 runtime / materialization boundary 见 [Workflow](WORKFLOW.md)。Concrete implementation handoff 可以是独立 specialized authority，继承 [Package Contract](IMPLEMENTATION.md)，不替代四文件语义 owner。引用外部 Observation semantics 时使用 summary + canonical link，不复制定义；Inputs 绑定与 Method 消费关系相互链接，不双重拥有输入含义。

更深层拆分只依据真实 concern 和阅读需求。例如复杂 Analysis 可从 METHOD 进入 `method/analyses/`；dependency composition 也可有自己的窄文档，但不建立 Study-local `method/observations/` definition。Inputs / Results 按需下沉并保留概览及导航，不机械一对象一文件。
