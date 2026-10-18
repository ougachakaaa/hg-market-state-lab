# Observation Implementation Architecture

本文件唯一拥有 Observation framework 的 runnable Python contract、public object ownership、composition、persistence lifecycle / placement、complete publication、窄 shared mechanics 与 implementation verification。继承 [framework semantics](ARCHITECTURE.md) 与 [Research UPSTREAM policy](../UPSTREAM.md)；不重定义 concrete business semantics。具体 Observation 映射进入 [DTE-chain implementation](cffex_option_expiry_dte_chain/IMPLEMENTATION.md)。本文是 runnable contract authority，不把历史 evidence 当 semantic owner。

## Implementation progressive disclosure

Implementation 阅读顺序固定为 concrete semantic entry → ARTIFACT（chain 另读 DATE_RESOLUTION）→ 本文件 → concrete IMPLEMENTATION → 仅实际依赖的 upstream public SERVICE / APPLICATION。Design 从 ARCHITECTURE → SCHEMA / AUTHORING → actual concrete owner 进入，上游选择按需读取 Research UPSTREAM。不扫描 sibling Study / Product，不把 shared helpers 或现有代码当缺失 semantic decision 的替代。

只实现实际 Observation 所需的最小 internal mechanics / common errors，不预建通用框架；Component 不适用 Observation lifecycle。

## Public namespace 与 invocation

Canonical framework namespace 为 `market_research.observations`，多 owner-local source roots 沿用 `pkgutil.extend_path` namespace composition；framework root 只发布 common errors，不聚合 concrete services 或创建 registry。Consumer 直接 import 实际 concrete package 的 `__init__.py`：

| Concrete public package | Required public exports |
| --- | --- |
| market_research.observations.cffex_option_expiry_dte_chain | ExpiryDteChainRequest、ExpiryDteChainArtifact、ExpiryDteChainRow、ExpiryDteChainService、create_service |

普通 consumer 构造 concrete Request，使用无参数 `create_service()`，调用 `service.ensure(request) -> concrete Artifact`。V1 只有 ensure 这一 semantic operation；不提供 resolve、get、lookup、fetch、run、execute、refresh、force 等重叠或未授权 verbs，也不提供 lookup-only operation。未来真实 read-only consumer 需求须独立设计。`market_research.shared`、studies、registry / dynamic plugin 都不是 canonical Observation boundary。

## Python semantic object boundary

Request / Artifact / row / provenance 是 Observation-owned typed immutable values，nested containers 也保持 read-only；日期用 `datetime.date`，不是 timestamp 或 JSON string。具体 carrier 可用合适 value object，不锁定 dataclass / Pydantic。Request 的 fields / semantic domains 和 Artifact 含义继承 concrete authority；其 public Python field mapping 由 concrete IMPLEMENTATION 拥有。

合法 Requests 按 concrete normalized business fields 具有 deterministic value equality。Artifact、rows 与 provenance 在相同 public values 下具有 deterministic value equality；value equality 不替代 semantic identity：同一有效 definition 下 identity 仍只由 Observation identity + normalized business inputs 决定。无 object address、connection、执行时间或 path 参与 identity / value equality。

Miss 只消费 selected public contract 的完整 facts / component results；component-mediated facts 仍保留原 canonical upstream owner / public snapshot proof，不将 helper 变成新的市场事实 owner。具体 invocation sequence 归 concrete IMPLEMENTATION。

Consumer 不需 construct dict、serialize JSON、写文件、构造 SQLite row 或 DataLake request 才能调用。DataLake / Snapshot public objects 仅在 Observation 内部消费，再投影为 Observation-owned values；Artifact 不直接包含 upstream Row / Export / CoverageResult / EnsureResult / service、Repository 或 SQLite object。保留 upstream field meanings / units / nullable rules，不复制其 semantic ownership。Study 无需 import upstream classes 才能理解 Artifact。

Provenance 投影为 concrete Artifact 可消费的 semantic values，描述实际 selected Dataset / Product / component contract 与 concrete 要求的 public context，不穿透 provider / Repository / SQLite；不建立统一 envelope。Timestamp、provider token / endpoint、SQLite path、repository ID、execution UUID 不加入 business key；完整 provenance 不改变 reuse。内部 serialization primitives 不构成 consumer file / JSON protocol。

## Public failures

Framework root 发布以下共同 taxonomy，Study 只需从 `market_research.observations` import 这些 errors：

```text
ObservationError
├── ObservationInvalidRequestError
└── ObservationOperationError
```

| Failure | Contract |
| --- | --- |
| ObservationInvalidRequestError | Caller semantic request invalid：错误 request / field type、缺 required value、invalid canonical product、倒置日期范围、非法 target_dte 或 concrete request-domain violation。Request construction 或 ensure boundary 在任何 upstream mutation 前识别，ensure 验证先于 persistence lookup / dependency access；不通过 trim、default 或修复掩盖错误。 |
| ObservationOperationError | 合法 Observation request 无法形成 / 返回 complete Artifact：选定 dependency execution / completeness failure、persistence unavailable / corrupt、Artifact invariant violation、日期计算 / proof 无法继续、atomic publication failure、合法请求转换后的 upstream request 被拒绝，及非 caller semantic mistake 的 runtime failure。 |

Public errors 可保留 readable dependency / operation context 与 chained internal cause；DataLake internal exceptions、SQLite exception object、provider error object / Tushare response 不是 public error fields 或 handling contract。Study 不 import upstream exception classes。Upstream incomplete / unit failures 映射为 ObservationOperationError，不返回 partial Artifact；runtime failure 不改变来源，详见 [Research UPSTREAM](../UPSTREAM.md)。合法 empty / date resolution 仍由 concrete owner 决定。进程中断不发布 complete，也不要求将系统 cancellation 当普通可恢复业务错误。

## Factory 与 explicit composition

`create_service()` 在 concrete package 内负责 owned persistence + declared public dependencies + concrete service composition。普通 consumer 不传 SQLite path、connection、Repository、DataLake / Snapshot service、token、provider client 或 Source adapter。Factory 不执行 network I/O、不解析 upstream credentials、不创建 provider client；dependency operation 延迟到合法 request 的 complete miss 后。Complete hit 连 upstream factory / coverage / export 都不需要调用，不能因 upstream 此时不可用而阻止 retained return。

Internal / test-only construction 可显式注入 persistence collaborator 与 DataLake public service doubles；future 已选择 Snapshot 的 concrete Observation 可组合其明确 public Product collaborator。Internal construction 不是普通 consumer API；不创建 container、Service Locator、DI framework、generic adapter 或 registry。Factory / ensure 的 runtime construction failures 同样用 ObservationOperationError 表达，不泄漏内部异常契约。

## Owned SQLite placement 与 logical storage

每个 concrete Observation exactly owns one SQLite，production placement 以 repository root 为基准，内部解析，不依赖 consumer cwd：

```text
market_research/observations/<observation-id>/output/<observation-id>.sqlite3
```

Concrete owner 同时拥有 authority、src 与 output；只有 `output/` 中的 SQLite / sidecars 是 ignored runtime state，不把整个 `observations/` 视为 data-only tree。Canonical placement 不授权迁移或重算已有 SQLite。该路径只用于内部 composition，不进入 Request / Artifact / semantic identity。Test-only composition 可用 temporary SQLite。数据库只存该 Observation 的 requests / Artifacts；没有 global research.sqlite / Observation DB / shared Artifact table、cross-Observation FK 或 Study-owned table。Business lookup 依据 normalized business fields；UUID、wall clock、filesystem path、hash alone 不替代这些字段，hash 只可作内部 optimization，存储必须仍能恢复 / 解释 normalized business inputs 本身。

Runtime SQLite 及其 WAL / journal 不进入 Git。实施阶段必须在首次创建 state 前配置并验证 ignore；Ignore 必须覆盖 Observation-owned output，包括 SQLite / WAL / SHM / journal。目录变更遵循 [repository disposable runtime policy](../../ARCHITECTURE.md#naming-and-transition-authority)，不检测或继承历史路径；canonical SQLite 内的 durable reuse、schema failure 与 atomic publication 契约保持不变。SQL DDL、indexes、serialization encoding、connection / transaction algorithm 属于实现 mechanics，不在此锁定。

## Complete publication 与 concurrency

```text
validate request → normalized business key → lookup complete retained Artifact
    ├── hit → return existing complete value; zero upstream / recomputation
    └── miss → execute canonical public upstream plan
             → derive / construct / validate whole Artifact in memory
             → atomic SQLite publication → return complete Artifact
```

Persistence lookup 只返回合法 complete Artifact；corrupt / unreadable / incompatible state 抛 ObservationOperationError，不能伪装 miss。只有整份 Artifact 完整且通过 concrete invariants 后才原子发布；durable publication 成功是正常 return 的前提，不能先 return 后异步保存，不能把仅存在于 service memory 的 Artifact 当作成功。Partial、failed、interrupted state 不满足 key，也不对 consumer 可见。Upstream 已成功 commits 不承诺跨库 rollback。

V1 不预建 persisted pending state machine、job / attempt history、execution / retry queue 或 scheduler。必要 internal temporary / staging mechanics 不改变 complete boundary。V1 不承诺 single-flight：两个 concurrent misses 可重复 upstream computation，但 persistence 必须保证同 key 最多一个 logical complete Artifact。竞争 loser 读取 / 返回 winner 的 complete Artifact；若无法合法读取则 operation failure，不能发布第二个 Artifact。具体 uniqueness / transaction mechanics 由实现落实；cross-process locking optimization 延后，无 distributed lock framework 或 cross-Observation transaction。

允许 internal SQLite schema versioning，但不解决 Artifact definition evolution / source refresh。无法合法读取当前 schema 时 ObservationOperationError；不得自动执行未授权 migration、old Artifact rewrite、TTL、force overwrite 或 generation history。[Deferred semantic decisions](ARCHITECTURE.md#explicitly-deferred-decisions) 保持未决。

## Package topology 与 shared mechanics

Framework authority 与 source colocate 于 `market_research/observations/`；每个 concrete Observation 的 authority / specialized contracts 位于 owner 根目录，implementation 位于该 owner 的 src/ 下，遵守根唯一 Python project / environment。Framework source package `__init__.py` 和同名 concrete package `__init__.py` 是 public boundaries；intentional re-exports 使用 explicit redundant aliases，不以 `__all__` 定义边界。Init docstring 指向对应 authority entry / implementation handoff。

Concrete package 内 public contract、service / orchestration、owned persistence、deterministic derivation 必须可辨认；chain 另有 date-resolution mechanism。按内聚性拆分，避免 giant module，不一对象一文件，不锁 private filenames。

Observation 可复用非常窄的 framework-internal mechanics：path resolution、connection / transaction、atomic publication primitive、safe serialization primitive 与 common error definitions。Shared helper 接收显式 context / mechanics 参数，不知道 expiry、DTE、chain、product_code semantics、Dataset / Product identity 或 concrete Artifact business fields / schema；concrete service 继续拥有业务映射。不创建 BaseObservation、GenericObservationService、generic Repository domain model、ObservationExecutor、ArtifactRegistry、Provider / DataSource abstraction 或 WorkflowEngine。

## Implementation acceptance 与 handoff

后续 implementation 至少验证三层，全部使用 root canonical environment：

| Layer | Required checks |
| --- | --- |
| Framework / topology | canonical packages 可 import、concrete exports / common errors、public owned types、无 registry / plugin；Study 无 DataLake / Snapshot / persistence imports，Observation 无 direct provider / private upstream imports；runtime SQLite / WAL / journal 被 ignore。 |
| Concrete service | temp SQLite + controlled public dependency doubles：invalid request 在 upstream mutation 前失败，miss / success、incomplete / operation failure、corrupt / incompatible DB、Artifact invariant / publication failure、repeat ensure 与重建 service 后 durable reuse；complete hit 所有 upstream calls 为零。验证并发至多一个 complete logical Artifact、失败不可见，无真实 Tushare 调用。 |
| Concrete semantics | 复用具体 ARTIFACT acceptance：chain exact DTE、周末假日、proven absence、missing 后 ensure、upstream failure 停止、actual_dte、完整 population / ordering 与合法 None。 |

### Durable reuse acceptance

每个 concrete Observation 都必须验证：service instance A 对合法 request ensure 成功，整份 Artifact 已 durable / atomic persisted；关闭 connections 并丢弃 A 及其 in-memory state（process recreation equivalent），重新创建 instance B，使用同一 Observation-owned SQLite 与相同 normalized request。B 必须返回同一 semantic identity / logical complete Artifact、相同 owned public values，所有上游 factory / coverage / ensure / export calls 为零，且不 recompute。B 使用不可用 upstream doubles 仍能命中；多个不同业务请求共存于该 concrete 唯一 SQLite，不建立 Study cache。

测试只用 temporary owned persistence 与受控 public dependency doubles；不依赖 Python object address、共享内存、SQLite path 的 consumer knowledge 或真实 provider。Publication / persistence failure 不返回成功，重建实例也不能读出 failed / partial state 为 complete。该验收适用于 concrete Observation，不适用于无 retained lifecycle 的 component。

Concrete semantics complete、implementation mapping complete、实际 public upstream dependencies 可用且无 conflict / capability gap 后，才标记 concrete **Implementation Ready**。Framework mechanics contract 完整可标为 Authority Complete / Implementation Architecture Complete / Implementation Ready；这些是设计状态，不等于 runtime implemented。Study 的 design readiness 与实际 runtime dependency reconciliation 继承 [Study handoff definition](../studies/AUTHORING.md#publication-与-dependency-handoff)：producer runtime 缺失须单独记录，实际 Study runtime dependency reconciliation 需 actual declared dependency runtime 完成及 bindings 复核；当前 readiness 只在实际 concrete handoff 记录。

V1 Python application boundary 不增加 Observation CLI、HTTP / REST；human execution 继续通过 Study。除此还排除 generic DataLake / Snapshot adapter、plugin、DAG、queue、background worker、run registry、global Research DB、retry / refresh engine 与 automatic migration。

Owner 根目录承载 authority 与实际子模块；Python implementation 位于本 owner 的 `src/` 下，按完整 `market_research.*` namespace 落位并在根 `pyproject.toml` 注册 source root。Authority 不进入 namespace/source tree；不存在 framework mechanics 时不创建空 src。源码 docstring 以相对路径指回 owner 根目录的 canonical entry。
