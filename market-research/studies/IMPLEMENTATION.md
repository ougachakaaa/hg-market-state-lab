# Retained Study Implementation Package Contract

本文件是 runnable retained Study 的 Python implementation topology 唯一 canonical owner。[Schema](SCHEMA.md) 定义 Study semantic objects 与关系，[Skeleton](SKELETON.md) 定义 Study authority 文档布局，[Authoring](AUTHORING.md) 定义创建与 implementation handoff，[Review](REVIEW.md) 验证实现，[Compatibility](COMPATIBILITY.md) 处理既有实现。具体研究语义仍由对应 Study authority 拥有。

## Package boundary 与默认拓扑

每个新实现的 runnable retained Study 必须位于 `market-research/src/market_research/studies/<study_package>/`，并以含 `__init__.py` 的真实 Python package 对应 `market-research/studies/<study_package>/` 的 authority unit。不得用 `<study_package>.py` 或一个承担完整实现的大脚本代替 package。默认且必需的 package-level 边界为：

```text
<study_package>/
├── __init__.py
├── cli.py
├── study.py
├── observations.py
├── analyses.py
└── evidence.py
```

| 边界 | 职责 |
| --- | --- |
| `__init__.py` | Package identity、指向当前 Study canonical `ARCHITECTURE.md` 的文档字符串，以及最小必要 public exports；不放 material computation。 |
| `cli.py` | Study-local inbound adapter：参数解析、用户输入校验、Research UI 配置、Snapshot public application composition、调用和退出／错误呈现；不拥有 Observation 或 Analysis 语义。 |
| `study.py` | 可读的 orchestration / composition entry：接收请求与 canonical inputs、构造 Observations、运行 Analyses、组合 Study result 并交给 evidence retention；只保留 Study-level request/result composition、dependency wiring 与小型协调 helper。 |
| `observations.py` | 当前 Study authority 中具名 Observation 的构造、Study-owned derived variables、selection、有效性／排除及其适用的 component artifact semantics。 |
| `analyses.py` | 具名 Analysis 的分组、比较、聚合、证据计算及 Analysis-specific semantics。 |
| `evidence.py` | Results / Evidence Product 的 serialization、表／图／报告、retained provenance representation 与 persistence-facing presentation；不重新定义 Method 的计算或统计语义。 |

实现责任沿 `Inputs → Observation(s) → Analysis / Analyses → Evidence Products` 可追踪。单个 module 不得同时拥有可独立理解且可清晰拆分的多个 material semantic responsibilities。尤其是非平凡的 Observation construction 与 Analysis execution 不得合并在同一个 general-purpose module；`study.py` 不得成为 contract selection、Observation row construction、statistical quantiles、Analysis grouping、plotting、retained serialization 或复杂 provenance hashing 的默认实现位置。打开 `study.py` 应能看懂主要 pipeline，而不必先读这些组件细节。

`observations.py` 与 `analyses.py` 可以各容纳多个内聚的具名组件；不要求一个对象一个文件。当阅读内聚性需要时，可在 Study package 内增加 `inputs.py`、`statistics.py`、`context.py`、`selection.py`、`provenance.py` 或更深的 `observations/`、`analyses/` 等边界。Request canonicalization、run identity 或 input-domain rules 足够复杂时放入 `inputs.py`；多个 Analysis 共用的非平凡数学机制可放入 `statistics.py`。这些模块仍由当前 Study 拥有，不因类似名称创建 cross-Study framework、base class、registry、DAG executor 或 shared statistics layer。

## Implementation progressive disclosure

阅读路径从当前 Study 的 `ARCHITECTURE.md` 进入所需的 `INPUTS.md`、`METHOD.md`、`RESULTS.md` 或其 specialized authority，再进入 `study.py` 的 composition；随后只读相关 `observations.py`、`analyses.py`、`evidence.py` 或更深的 Study-local module 与相关测试。修改一个 Analysis 时，应能沿其 Method contract 到 Analysis implementation、必要的 statistics helper 与测试，而无需理解 CLI parsing、无关 Observation selection、其他 Analysis、报告格式或 output transaction。这是实现验收条件。

按 semantic responsibility 与阅读边界审查拓扑。文件行数只可提示审查，不是拆分的 canonical 阈值；文件、函数、class 数量和每个组件独占文件均不是规则。既有 implementation 的非追溯适用规则见 [Compatibility](COMPATIBILITY.md)。
