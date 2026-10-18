# Retained Study Implementation Package Contract

本文件唯一拥有新 runnable retained Study 的 Python implementation topology、implementation acceptance 与 review criteria。Framework 入口见 [Study architecture](ARCHITECTURE.md)，semantic graph 见 [Schema](SCHEMA.md)，文档布局 / semantic gate / handoff 见 [Authoring](AUTHORING.md)。既有实现仅在 [Compatibility](COMPATIBILITY.md) 触发范围内适用；Observation implementation 独立归其 [canonical owner](../observations/ARCHITECTURE.md)。

## Package boundary 与必需拓扑

每个新 runnable Study 位于 `market_research/studies/<study_package>/`，authority 与 implementation 同处该 canonical owner，四份 semantic documents 继承 [四文件布局](AUTHORING.md#mandatory-top-level-topology)。它必须是真实 Python package，不能由单个 `<study_package>.py` 或承担全部责任的大脚本代替。

```text
<study_package>/src/market_research/studies/<study_package>/
├── __init__.py
├── cli.py
└── study.py
```

上述三份为 mandatory。`analyses.py` 仅在 material Analysis 存在时需要，`evidence.py` 仅在 Evidence retention 存在时需要；不为 observation-only Study 创建空 module。复杂 Workflow Artifact serialization / composition 可用 Study-local `artifacts.py` / `workflow.py`，不强制统一文件。

| 边界 | 职责 |
| --- | --- |
| `__init__.py` | Package identity、指向 canonical Study `ARCHITECTURE.md` 的文档字符串与最小必要 public exports；不放 material computation。 |
| `cli.py` | Study-local inbound adapter：参数解析、输入校验、explicit dependency composition、Study invocation 与退出 / 错误呈现；只有 retained-output shape 才使用 UI config / output helpers，不定义 Observation / Analysis semantics。 |
| `study.py` | Orchestration owner：接收 canonical request、绑定 Component / Observation inputs、取得 complete component results / ensure durable Artifacts、驱动 runtime plan / steps、failure continuation、组合 outcome 与 optional Analysis orchestration；Workflow Artifact materialization / run-output publication 仅 actual authority 声明时驱动。 |
| `analyses.py`（conditional） | Study-local computation / sample selection / grouping / comparison / statistics；只消费 workflow 已准备的 complete inputs，可调用 pure component，禁止调用 upstream-backed resolver / reader、DataLake / Snapshot、fetch market data、invoke / resolve / ensure Observation 或读取 persistence。 |
| `evidence.py`（conditional） | 实际 Evidence Products 的 serialization、表 / 图 / 报告、retained provenance 与 presentation；不重定义 computation、Observation semantics 或 dependency resolution。 |

`observations.py` 不再是新 Study 的必需责任边界；Study 不得实现 Observation 本身。其 population、grain、derivation、validity、Artifact construction 与 owned SQLite 属于独立 Observation。Legacy `observations.py` 仅按 Compatibility 处理。

实现责任沿 `Study request → workflow / Component invocation / Observation ensure → runtime state / outcome → optional Analysis / explicit retained outputs` 可追踪，[Workflow contract](WORKFLOW.md) 拥有 runtime / retained distinction 与 complete-input semantics。复杂 request / binding 可放入 `inputs.py`，只有实际声明的 retained run identity / Workflow Artifact serialization 才需相应 helper；多个实际 Analysis 的数学机制可放入 Study-local `statistics.py`。按内聚性增加边界，不创建 cross-Study framework、base class、registry、DAG executor 或大 shared statistics layer。明确跨研究复用的小领域 helper 依 [Component authority](../shared/ARCHITECTURE.md) 判断提升，单个 consumer 的 logic 保持 local。

`study.py` 驱动 runtime orchestration 与明确声明的 materialization，不成为 material statistics、grouping、plotting、复杂 serialization / provenance hashing 的默认位置。Invocation binding / resolution 是 orchestration，重新实现 Observation fact derivation 或复制 rows 建 Study cache 是越界。Study 不通过 DataLake / Snapshot、Source、Raw、Preparation 或 SQLite 补齐 dependency；缺失能力按 Authoring 先 reconciliation。CLI composition 可以构造或显式传入 declared Component / Observation public collaborators，不代替 study.py 驱动 dependency invocation；不能让 eager composition 阻止 complete empty plan 的成功。

## Implementation progressive disclosure

从 Study entry 进入 INPUTS / METHOD / RESULTS 或必要 specialized authority，再读 `study.py` composition；随后只读实际 Analysis、evidence、input helper 或 consumed Observation public contract 与相关测试。修改一个 Analysis 不要求阅读无关 CLI、其他 Analysis、Observation internal persistence 或无关报告格式。

按 semantic responsibility 和阅读边界审查拓扑，LOC、函数 / class 数量或一对象一文件不是阈值。单一 module 不同时承载多个可独立理解且可清晰拆分的 material responsibilities。已有实现非追溯规则见 Compatibility。

Owner 根目录承载 authority 与实际子模块；Python implementation 位于本 owner 的 `src/` 下，按完整 `market_research.*` namespace 落位并在根 `pyproject.toml` 注册 source root。Authority 不进入 namespace/source tree；不存在 framework mechanics 时不创建空 src。源码 docstring 以相对路径指回 owner 根目录的 canonical entry。

## Runnable Study implementation topology review

实现形成后单独执行，不决定 authority complete。历史 implementation 只按 Compatibility 的触发范围适用。

| 检查面 | 不通过条件 |
| --- | --- |
| Package / entry | 新 runnable Study 是单脚本、缺少 Package Contract 必需边界，或 init docstring 不指向 canonical Study entry。 |
| Orchestration | study.py 隐藏 material statistics / plotting / complex serialization，或无法辨认 request → dependency ensure / runtime plan → outcome；实际声明 retained outputs / Analysis / Evidence 时其责任无法辨认。 |
| Observation / Analysis boundary | Study 直接调用 DataLake / Snapshot 或实现 Observation construction、读取 persistence；Analysis invoke / resolve / ensure Observation、调用读取事实的 component、fetch data 或重定义 empirical semantics。Only Study orchestration 的事实 dependency binding / invocation 合法，pure component computation 也可由 Analysis 调用。 |
| Traceability | Dependencies、步骤、runtime completion / failure 无法追踪；实际声明的 retained Workflow Artifacts / publication 或 Analysis / Evidence 无清晰责任。 |
| Focused reading | 修改一个 Analysis 需理解无关 CLI、其他 Analysis、Observation internals、报告格式或 output transaction。 |
| Mixed responsibility | 单 module 承担可独立理解的 input canonicalization、Analysis execution、evidence retention 等多个 substantial responsibilities，无清晰内聚依据。 |
| Authority drift | 实现合并、隐藏或越界重定义语义对象，无法恢复 Schema / Workflow graph；为 orchestration-only Study 强制 directory / config / Artifact，复制 market rows 建 empirical cache，或对无 Analysis / Evidence 的 Study 强制空 module。 |

按 semantic responsibility 和阅读边界处理 findings，不以 LOC、函数 / class 数量或一对象一文件代替审查。结构测试可固定 package / 必需 module / authority pointer，不能替代语义阅读。
