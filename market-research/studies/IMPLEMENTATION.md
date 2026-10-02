# Retained Study Implementation Package Contract

本文件是未来 runnable retained Study 的 Python implementation topology 唯一 canonical owner。[Schema](SCHEMA.md) 定义 semantic graph，[Skeleton](SKELETON.md) 定义文档布局，[Authoring](AUTHORING.md) 定义交接，[Review](REVIEW.md) 验证实现，[Compatibility](COMPATIBILITY.md) 保护既有实现。Observation implementation 独立归其 [canonical owner](../observations/ARCHITECTURE.md)，不由 Study 实现。

## Package boundary 与必需拓扑

每个新 runnable Study 位于 `market-research/src/market_research/studies/<study_package>/`，与 `market-research/studies/<study_package>/` authority 同名对应。它必须是真实 Python package，不能由单个 `<study_package>.py` 或承担全部责任的大脚本代替。

```text
<study_package>/
├── __init__.py
├── cli.py
└── study.py
```

上述三份为 mandatory。`analyses.py` 仅在 material Analysis 存在时需要，`evidence.py` 仅在 Evidence retention 存在时需要；不为 observation-only Study 创建空 module。复杂 Workflow Artifact serialization / composition 可用 Study-local `artifacts.py` / `workflow.py`，不强制统一文件。

| 边界 | 职责 |
| --- | --- |
| `__init__.py` | Package identity、指向 canonical Study `ARCHITECTURE.md` 的文档字符串与最小必要 public exports；不放 material computation。 |
| `cli.py` | Study-local inbound adapter：参数解析、输入校验、Research UI 配置、dependency composition、Study invocation 与退出 / 错误呈现；不定义 Observation / Analysis semantics。 |
| `study.py` | Orchestration owner：接收 canonical request、绑定 Observation inputs、resolve / ensure complete Artifacts、驱动步骤与 Workflow Artifact materialization、调用 optional Analysis、组合 result 并驱动 run-output publication。 |
| `analyses.py`（conditional） | Study-local computation / sample selection / grouping / comparison / statistics；只消费 workflow 已准备的 complete Artifacts，禁止调用 DataLake / Snapshot、fetch market data、invoke / resolve / ensure Observation 或读取 persistence。 |
| `evidence.py`（conditional） | 实际 Evidence Products 的 serialization、表 / 图 / 报告、retained provenance 与 presentation；不重定义 computation、Observation semantics 或 dependency resolution。 |

`observations.py` 不再是新 Study 的必需责任边界；Study 不得实现 Observation 本身。其 population、grain、derivation、validity、Artifact construction 与 owned SQLite 属于独立 Observation。Legacy `observations.py` 仅按 Compatibility 处理。

实现责任沿 `Study request → workflow / Observation dependencies → materialized Workflow Artifacts → optional Analysis / Evidence` 可追踪，[Workflow contract](WORKFLOW.md) 拥有 materialization / complete-input semantics。复杂 request / run identity / binding 可放入 `inputs.py`，复杂 Workflow Artifact serialization 可放入 `artifacts.py`；多个实际 Analysis 的数学机制可放入 Study-local `statistics.py`。按内聚性增加边界，不创建 cross-Study framework、base class、registry、DAG executor 或 shared statistics layer。

`study.py` 驱动物化，不成为 material statistics、grouping、plotting、复杂 serialization / provenance hashing 的默认位置。Invocation binding / resolution 是 orchestration，重新实现 Observation fact derivation 是越界。Study 不通过 DataLake / Snapshot、Source、Raw、Preparation 或 SQLite 补齐 dependency；缺失能力按 Authoring 先 reconciliation。CLI composition 可以构造 runtime collaborators，不代替 study.py 驱动 empirical invocation。

## Implementation progressive disclosure

从 Study entry 进入 INPUTS / METHOD / RESULTS 或必要 specialized authority，再读 `study.py` composition；随后只读实际 Analysis、evidence、input helper 或 consumed Observation public contract 与相关测试。修改一个 Analysis 不要求阅读无关 CLI、其他 Analysis、Observation internal persistence 或无关报告格式。

按 semantic responsibility 和阅读边界审查拓扑，LOC、函数 / class 数量或一对象一文件不是阈值。单一 module 不同时承载多个可独立理解且可清晰拆分的 material responsibilities。已有实现非追溯规则见 Compatibility；当前 implementation / test drift 见 [reconciliation](../IMPLEMENTATION_RECONCILIATION.md)。
