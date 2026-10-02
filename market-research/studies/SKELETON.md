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
| `ARCHITECTURE.md` | 稳定入口：Identity、Question、scope / purpose、Limitations、Acceptance、Observation Artifact Dependencies / Analysis / Evidence Product 概览、dependency gaps、implementation location 与 Authority Navigation。 |
| `INPUTS.md` | Study request / configuration、Observation invocation input bindings、parameter owner / consumers / semantic role、用户表达与 CLI 映射、必填性与默认值、规范化、execution-only options、Study run identity 及输入依赖缺口。 |
| `METHOD.md` | Observation Artifact Dependencies 的 canonical owner / identity / contract references、resolve / ensure boundary 与 Analysis consumption；Method Context（若有）、Analysis contract、Study-local sample selection / statistics / exclusions。 |
| `RESULTS.md` | 具名 Evidence Products 与 `defined_by` Analysis、machine-readable structure、表 / 图 / 报告、Artifact provenance references、复核所需样本与排除计数、空 / 缺失状态和 human-readable 呈现。 |

六个必答 semantic areas 仍由 Schema 定义；Identity 是 structural information，Authority Navigation 是阅读路径。Observation empirical population、grain、derivation、validity 和 Artifact schema 不在上述文件重新定义。

## Entry 与 progressive disclosure

Entry 必须直接链接 `INPUTS.md`、`METHOD.md`、`RESULTS.md`，并使必要的 specialized authority 可达。读者可辨认问题、主要依赖、Analyses、预期 evidence、限制和验收，然后只读取相关 owner，不必搜索目录。

Detailed request / run identity 归 INPUTS，Artifact dependency composition 与 Analysis mechanics 归 METHOD，Evidence Product structure 归 RESULTS；引用外部 Observation semantics 时使用 summary + canonical link，不复制定义。Artifact identity 由 dependency 引用其 Observation owner 确定，Inputs 的绑定与 Method 的消费关系相互链接，不双重拥有输入含义。

更深层拆分只依据真实 concern 和阅读需求。例如复杂 Analysis 可从 METHOD 进入 `method/analyses/`；dependency composition 也可有自己的窄文档，但不建立 Study-local `method/observations/` definition。Inputs / Results 按需下沉并保留概览及导航，不机械一对象一文件。
