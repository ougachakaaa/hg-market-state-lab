# DataLake Shared Kernel Application authority

本文件拥有 Kernel 的 coverage / ensure / export Use Cases、通用生命周期与 Dataset Public Application Service 的公共 semantic contract，继承 [模块架构](ARCHITECTURE.md) 的职责与依赖边界。Scope / Window、FetchUnit 状态、Record ownership、原子成功由 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 拥有；Dataset-specific request、view、payload 与 specialization 经 [DATASETS.md](DATASETS.md) 进入 owning Dataset authority。CLI topology、serialization 与 file delivery 由 [lab authority](../ui_cli/ARCHITECTURE.md) 拥有。

## 1. Application Service 与公共 operation family

DataSet Application Service 是 transport-neutral canonical consumer boundary，公开 Python semantic request/result/view。它在内部将 Dataset-specific request 解释为 Scope + Window 和目标 FetchUnit identities，查询 coverage、编排 ensure、生成 Dataset-owned export view；caller 不需要理解 persistence mechanics。Dataset-specific consumer contract 经 catalog、Dataset ARCHITECTURE.md 进入 SERVICE.md。

每个 Dataset 自己拥有具体 public semantic service contract；Kernel Application 在目标确定后执行通用机制，依赖 Domain 与 [Outbound Ports](PORTS.md)，不直接依赖 SQLite、Tushare 或具体 Dataset。领域策略及 Adapter 由 [Composition Root](COMPOSITION.md) 绑定；本文件拥有公共 operation family 与 result/error invariants，不建立 generic DataLake facade / gateway / client。Consumer 直接进入具体 Dataset public API，再由 Dataset 使用 shared kernel；内部 Source adapter / Repository composition 与依赖方向继承 [模块架构](ARCHITECTURE.md)。

不得把 arbitrary record-level mutation 发布为公开能力。Consumers 只依赖 Dataset semantic request、public result / export view 与 public completeness / failure contract；不直接依赖 SQLite / filesystem layout、Repository、Source adapter、FetchUnit / Record persistence identity、provider runtime / Tushare client、provider response、internal batching / transaction / schema。Public boundary 不暴露 SQL、SQLite path、unit_id / record_id 等 persistence identity、argparse namespace、provider transport response 或 internal repository object。未来模块应直接消费 public semantic request/result/view，不调用 CLI 或反向解析 JSON export；Research producer permissions 与 capability selection 见 [Research UPSTREAM](../market_research/UPSTREAM.md)，具体 integration implementation 遵循此已冻结 boundary。

第一版公开 semantic operations 固定为 `coverage`、`ensure`、`export`；`read` 与 `sync` 不作为 public product / CLI verbs。公共 operation family 不要求通用 abstract base class、plugin system 或 registry framework；每个 DataSet 拥有自己的 request/result/view contract。

| operation | Source I/O | SQLite mutation | semantic purpose |
| --- | --- | --- | --- |
| coverage | 禁止 | 禁止 | 描述目标 Scope + Window 的当前缓存状态 |
| ensure | 允许 | 允许 | 尽可能补齐目标 Scope + Window |
| export | 禁止 | 禁止 | 生成 Dataset-owned business-oriented view |

`coverage` / `export` 必须真正 read-only：不创建数据库、表或 pending rows，不隐式 ensure，也不因缓存缺失访问 Source。不存在的缓存按目标 units 全部 missing 表达；已经存在但无法读取或无法合法解释的 Dataset 属于 application failure，不冒充 missing。不兼容 persisted schema / generation 在 coverage、ensure、export 中以 `OperationError` 明确失败，诊断标明 owning Dataset 需要 cache rebuild；不能返回普通 missing / incomplete、自动重建或升级。兼容性规则唯一见 [PERSISTENCE.md](PERSISTENCE.md)。两者不要求 Source credential。

### coverage

`coverage(request) → CoverageResult` 回答指定 Scope + Window 当前拥有多少完整成功的 FetchUnits。公共字段为：

```text
requested_units
successful_units
missing_units
pending_units
failed_units
complete
```

计数均为非负整数，`complete` 为 boolean。统计只针对目标 identities：没有 row 为 missing；已有 row 按 success、pending、failed 分类，四类互斥且总和等于 requested_units。Pending 不计入 failed；success 必须满足 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 中 Records 与成功 metadata 一致的 invariant。

```text
complete = successful_units == requested_units
           AND missing_units == 0
           AND pending_units == 0
           AND failed_units == 0
```

`complete = false` 是合法查询结果，不是 operation failure。Coverage 查询不得为了统计 missing 而创建 rows。

`coverage.complete` 只表达 cache completeness，不表达 provider-current freshness；success 的历史取得含义由公共 domain authority 拥有。

### ensure

`ensure(request) → EnsureResult` 尽可能使所有目标 FetchUnits 达到 success。默认 selection 与成功 unit 的跳过规则继承 [DOMAIN_MODEL.md](DOMAIN_MODEL.md)。公共字段为：

```text
requested_units
already_successful_units
attempted_units
succeeded_units
failed_units
records_written
complete
failures
```

计数均为非负整数，`complete` 为 boolean。`already_successful_units` 是调用开始时跳过的成功 units；`attempted_units` 是本次实际尝试执行的不同 units，不是 Source request 或 retry 次数。`succeeded_units` / `failed_units` 统计这些 attempts 的最终结果，二者之和等于 attempted_units；`records_written` 只计本次成功提交的 Records，不含已有成功缓存。

`complete` 根据操作结束后的目标 CoverageResult 决定，仍有 missing、pending 或 failed unit 即为 false。`failures` 中每项至少包含对应 FetchUnit semantic identity 与 human-readable reason，不使用 persistence identity 定位。可恢复的 unit failure 应作为失败结果返回，并继续尽可能补齐其他 units；无效 request、无法读取/写入 Dataset 或无法执行 operation 属于 application failure，不伪装成正常 EnsureResult。不能用一次 provider request 的成功代替逐 unit completeness。

### export

`export(request)` 返回 Dataset-owned semantic Export Envelope / Export View，不接受 filesystem output path，也不负责写文件。Export 是为实际 consumer/use-case 定义的 business-oriented view，不是 SQLite / Records generic dump；internal persistence schema 不构成 export authority，即使第一版字段相近。

所有 Dataset export 的最小公共 envelope 为：

```text
dataset
view
export_schema_version
scope
window
coverage
<payload owned by Dataset>
```

`dataset` 是 canonical Dataset identity；`view` 是 Dataset authority 定义的 semantic view identity；`export_schema_version` 是 export contract version，不等于 SQLite schema_version；scope/window 表达此次 view 的目标，coverage 为同一目标的 CoverageResult。Payload 名称、shape、字段与 ordering 由 Dataset authority 定义，不加入 SQLite path、internal unit/record IDs 或 provider transport metadata。

Coverage 不完整时仍可返回当前可用 view，准确声明 coverage.complete = false。Payload 只能包含目标范围内成功 FetchUnits 的合法 cached facts，不能把 failed / pending units 的不完整 Records 当作成功数据；无可用事实时返回 Dataset 定义的空 payload。

**Export consistency invariant**：返回的 coverage 与 payload 必须来自同一个逻辑 committed cache snapshot。不能因并发 ensure 或其他 committed mutation 而将不同缓存状态拼接为一个 view；不存在缓存时也必须一致表达 missing 与空 payload。此处只定义 semantic invariant，不指定 SQLite transaction implementation。

Dataset owns export semantics；CLI / HTTP adapter owns serialization 与 delivery，lab 的 file delivery 见其 authority。Python consumer 直接消费 semantic view，无需先写 JSON 再读取。Service types 与 wire representation 分离：例如 Python date / None 对应 JSON 日期字符串 / null；Dataset 可规定稳定 wire meaning，序列化动作不属于 service。只有出现真实第二个 view 时再扩展 selection mechanism，不预建 generic view registry。

### Application failure taxonomy

公共稳定 failure categories 为：

| Failure | Semantic boundary |
| --- | --- |
| InvalidRequestError | caller-side semantic validation failure：无效日期范围、空 / 非法输入或错误 request types |
| OperationError | Dataset 无法读取、persistence integrity / execution failure、required credential 缺失、Source operation 无法执行或无法生成合法 view |

可恢复的单 FetchUnit failure 进入 `EnsureResult.failures`，不抛整个 operation exception；可恢复的批请求失败按所尝试 units 编码。无法执行整个 operation 时抛 OperationError，不能伪装成正常 incomplete result。OperationError 不保证回滚此前已成功提交的其他 units；重试按既有成功缓存跳过规则进行。Provider response、SQLite exception 或 internal object 不构成 public error contract。

公共 `data_lake` facade 发布这两类错误；core 与 Dataset service 保留 InvalidRequestError，并将 storage / execution failures 转换为 OperationError。Caller 无需访问 internals 即可识别这两类 failure。DataLake 不定义 CLI exit code 或 HTTP status code；adapter 分别映射 request failure 与 execution failure。

Public facade also exports `CredentialMissingError(OperationError)`: a backward-compatible typed signal only for confirmed absent/blank required credentials. Consumers may distinguish it without inspecting messages or provider internals; other operation failures retain their existing classification.

## 2. Runtime configuration 与调用边界

Source credential 属于 runtime/provider configuration，不是 Dataset semantic argument。不得增加 `--token` 或第二套 secret convention，也不因此授权 import Snapshot 私有 Source client 或 artifact helper。Provider-specific credential convention 与 execution 由对应 provider authority 拥有，Dataset authority 声明 Source provider 并链接 execution authority，不重复实现 resolution；Tushare contract 见 [providers/tushare/ARCHITECTURE.md](providers/tushare/ARCHITECTURE.md)。

普通 consumer 创建 Dataset service 不要求提供 SQLite path、Repository、Source Adapter、database connection 或 token；Dataset-specific configuration/composition 属于 owning Dataset，generic runtime/storage resolution machinery 属于 DataLake shared kernel，provider-specific execution 属于 provider infrastructure；三者均为 consumer boundary 内部能力。Coverage / export 与 factory 不解析 Source credential、不创建 provider client；ensure 仅在实际 Source I/O 必要时解析凭据并初始化 client。全部目标 success 或零目标且无需 prerequisite Source I/O 时不进入 provider initialization。Missing required credential 在 Source request 前以 OperationError 明确失败；provider execution authority 不改变公共 failure taxonomy，也不负责将请求失败映射到 FetchUnits。

SQLite location 由 owning Dataset 内部 composition 使用 shared runtime/storage machinery 解析，不接受 semantic request 中的 path 或 CLI `--db`。Persistent state ownership 由模块架构拥有，SQLite lifecycle / generation compatibility 见 [PERSISTENCE.md](PERSISTENCE.md)；shared machinery 不得内置具体 Dataset 知识，也不创建跨模块 config framework。现有本地凭据操作见 [README](../README.md) 与 [DEVELOPMENT](../DEVELOPMENT.md)。

## 3. 已声明的 Dataset public service dependency

本节只约束模块架构已允许的 dependency，不建立 dependency graph engine 或通用 orchestration framework。可选 Prerequisite Resolver 的角色、输入输出、权限和复用生命周期由 [COMPOSITION.md](COMPOSITION.md) 拥有；本节拥有它与 planning / Use Case 的调用顺序和公共失败边界。Consumer Dataset 必须在自己的 narrowest authority 声明 prerequisite request、读取方式、ensure 权限及失败语义；Resolver 只能通过 producer 的 public semantic service 消费事实。Relationship identity 本身不构成 dependency permission。

- Consumer 的 `coverage` / `export` 只允许调用 prerequisite 的 read-only public operations；整个调用链禁止 Source I/O 与 SQLite mutation，不隐式 ensure。
- Consumer 的 `ensure` 可以按已声明契约调用 prerequisite 的 `ensure`，但每个 Dataset 只由自己的 service 写自己的 state，没有跨库原子提交或 rollback 保证。
- 当 prerequisite 不完整，导致目标 FetchUnit 集合无法合法确定时，consumer 抛 `OperationError`；不能把未知日期当休市、以已知子集缩小 requested_units，或伪造正常 incomplete CoverageResult / EnsureResult。Prerequisite cache incompleteness 与 consumer 已知目标 units 的 incompleteness 是不同情形。
- Prerequisite operation failure 映射为 consumer `OperationError`，保留可读的 dependency context，不泄漏 persistence / provider objects；consumer 自身输入错误仍是 `InvalidRequestError`。合法 consumer request 经内部转换后被 prerequisite 拒绝属于 composition/execution failure。
- Consumer 每次 operation 固定一份合法 prerequisite semantic view 以展开目标集合。Export coverage 与 payload 仍须来自 consumer 同一个 committed cache snapshot，并针对这份固定目标；不声称多个 Dataset 共享同一数据库 snapshot 或 provider-current freshness。

具体 Index / Futures / Options → Calendar contract 经 [catalog](DATASETS.md) 进入各自 Dataset 的 TRADING_DAYS.md；允许的 dependency edges 由模块 architecture 唯一声明。Calendar 自己的 request/result/view 与 domain semantics 保持不变。

内部 batching / 单 worker 提前一批 / operation 内验证复用由 [EXECUTION.md](EXECUTION.md) 约束，SQLite 生命周期与 generation 兼容由 [PERSISTENCE.md](PERSISTENCE.md) 约束；这些执行机制不扩展 consumer boundary。

## 4. Use Case lifecycle 与职责分工

三个 operation 共享以下进入 Kernel 前的顺序，由 owning Dataset Public Service / Composition 负责：

```text
validate Dataset Request
    → determine Operation Permission from operation + authorized dependency
    → invoke zero / one / multiple Prerequisite Resolvers in owning Composition order
    → validate and fix Planning Context (empty if no prerequisite)
    → Dataset Domain FetchUnitPlanner(Request, Context) → complete desired FetchUnits
    → delegate fixed target to Kernel Use Case
```

无效 request 在 prerequisite 调用前抛 InvalidRequestError；Resolver 无法获得合法完整前置事实时按第 3 节抛 OperationError，在目标确定前不查询 consumer units 来猜目标、不建立 consumer pending、不准备 consumer Source。必要 prerequisite ensure 可以写 producer 自己的 state，先前已提交事实不跨库 rollback，且不计入 consumer counters。合法前置事实证明零目标时才可按既有零目标语义进入 Use Case。

Planning Context 和完整目标在本次 operation 固定；Kernel 不调用 Resolver、不解释这些业务维度，也不按缓存状态重规划目标。进入 Kernel 后，三个 Use Cases 复用以下机制：

| Use Case | Kernel Application responsibility |
| --- | --- |
| coverage | 对固定目标经 Repository Port 取 committed snapshot，校验每个成功 unit 的 Dataset completeness，发布公共互斥计数与 complete；不准备 Source |
| ensure | 验证既有成功缓存，选择 missing / non-success，惰性准备 Source、验证 batch partition，协调 pending / fetch / normalize / validate / commit / failure，最后按同一目标计算结束 coverage 与 EnsureResult |
| export | 对固定目标取一个 committed snapshot，验证成功事实与 completeness，以该 snapshot 的 coverage / facts 调用 Dataset Projector 并校验公共 envelope 一致性；不再次查询拼接另一份缓存状态 |

Ensure 的稳定概念顺序为：

```text
validated Request → authorized prerequisite resolution → fixed Planning Context
    → FetchUnitPlanner → complete desired FetchUnits
    → read / validate existing state
    → select missing / non-success units
    → prepare Source only if selected is non-empty
    → validate batch plan
    → commit selected units pending before their requests
    → Source Port fetch / partition
    → Dataset Normalizer → UnitRecords (not a completeness proof)
    → Dataset Completeness Validator
    → Repository Port atomic success (Records / instruments / basis / hash / count / status)
    → final target coverage / EnsureResult
```

可恢复的 batch/unit failure 由 Application 协调 Repository failure state 与公共 UnitFailure；初始化、缓存完整性或整个 operation failure 按第 1 节分类。Content hash / SQL 事务由 persistence adapter 实现公共领域不变量，Application 不执行 SQL，也不解释 completeness basis。无 selected units 时不准备 Source、不进入写生命周期。

Source facts 的唯一成功写入交接契约见 [PORTS.md](PORTS.md)；Application 必须在 atomic success 前调用 Dataset Validator，即使 Source Adapter 已提前调用 Dataset normalization。所有成功缓存读路径也经过相应业务验证，缓存不合法时 OperationError，不转成 silent refetch；Repository 的通用 integrity 检查不能替代业务验证。Read-only operations 从 Resolver 到 Kernel / Projector 均不获得写权限。

Application 不接管 Dataset endpoint、metadata reuse eligibility、合约全集证明、calendar selection 或 Export payload；也不复制 Provider credential / limiter / request execution。内部调度、取消与验证复用见 [EXECUTION.md](EXECUTION.md)，SQLite transactions / snapshot 的实现约束见 [PERSISTENCE.md](PERSISTENCE.md)。
