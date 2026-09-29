# Canonical Study Logical Skeleton

本文件只定义新建 retained Study authority 的逻辑呈现顺序与 progressive disclosure 布局。对象含义、必需字段和关系由 [Schema](SCHEMA.md) 唯一定义；创建流程由 [Authoring](AUTHORING.md) 拥有。下列标题是可直接实例化的写作骨架，不要求逐字使用，也不对应固定数量的 Markdown 或 Python 文件。

## Logical presentation shape

```text
# <Study Name>

## Identity
## Question
## Inputs
## Method
### Method Context（仅存在共享研究语义时）
### Observations（具名）
### Analyses（具名）
## Results
### Evidence Products（具名）
## Limitations
## Acceptance
## Authority Navigation
```

按此顺序实例化 [Schema](SCHEMA.md) 的六个 semantic areas。`Identity` 是 Study 的 structural information；`Authority Navigation` 是阅读路径，不是新的 research semantic area。Method Context、Observation、Analysis 与 Evidence Product 的具体 contract 均从 Schema 填写，不在本骨架另设定义。不同 Study 可以使用符合自身术语的标题，但应保持上述逻辑顺序和语义归属。

## Entry and disclosure

每个新 Study 以 `studies/<study_package>/ARCHITECTURE.md` 为稳定 canonical entry。打开 entry 应能快速识别 Study identity、bounded Question、population / major Inputs、具名 Observations 和 Analyses 及主要消费关系、预期 Evidence Products、核心 Limitations、Acceptance overview，并知道下一步应读哪份 authority。Authority Navigation 链接真正拥有详细规则的 specialized authority 与必要的上游 authority，并指出 dependency gaps 和 implementation location；entry 只概述已下沉的契约，不完整重复定义。

简单 Study 可在 entry 中依序写完全部语义，不因骨架自动创建 specialized file。复杂 Study 可把详细 Inputs、Method 或 Results 下沉，例如使用 `INPUTS.md`、`METHOD.md`、`RESULTS.md`；这些文件名与分组都不是模板要求。下沉后，entry 仍按相同逻辑顺序保留可扫描的概述及明确链接。每条语义规则只有一个 canonical owner，所有 specialized owner 都须从 entry 可达。

若使用上述分组，Inputs-like authority 可承载详细 population、external inputs、parameter ownership 与 run identity；Method-like authority 可承载 Method Context、Observation / Analysis contracts、消费关系与 component Artifact identities；Results-like authority 可承载 Evidence Products、retained forms、provenance 与边界状态。这些只说明细节应放在哪里，具体要求仍以 [Schema](SCHEMA.md) 为准。

多个独立 Observation、语义不同的 Analysis、多组参数 owner、复杂 run identity、component Artifact identity 或 Evidence Product contract，均可提示需要拆分；若阅读或实现某个 Analysis 必须加载大量无关组件细节，也应考虑下沉相关部分。按实际阅读边界决定，不按行数、标题数或组件数强制拆分；不创建空文件、只有形式性几行的文件，或 one-object-one-file 布局。
