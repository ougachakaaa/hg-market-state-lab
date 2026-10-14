# DataLake Shared Kernel Domain authority

本文件拥有 Shared Kernel Domain 的公共原语、不变量、逻辑 persistence model 与 Scope / Window / FetchUnit 关系，继承 [模块架构](ARCHITECTURE.md) 的 ownership 边界。自治 Dataset 在上层边界内 specialize 或 constrain 这些 invariants；具体 ownership 与 colocation 由模块架构拥有。公共 operation、结果与 application failure 由 [APPLICATION.md](APPLICATION.md) 拥有；具体 Source、identity、Record fields 与 completeness specialization 经 [DATASETS.md](DATASETS.md) 进入 owning Dataset authority。本文不定义 SQL DDL 或 Dataset-specific fields。Application lifecycle 见 [APPLICATION.md](APPLICATION.md)，外部能力契约见 [PORTS.md](PORTS.md)，Dataset 策略接入见 [COMPOSITION.md](COMPOSITION.md)；SQLite 机制见 [PERSISTENCE.md](PERSISTENCE.md)。

Dataset 的数据标准是完整、稳定表达其 reusable source facts。Population、grain 与 completeness 由 owning Dataset authority 决定，不根据单个 Study 的 fact slice 改变；consumer 选择 semantic request / view 或下游样本，不重新定义 Dataset facts。

## 1. 通用领域原语与完整性

Domain 不依赖 Application、Ports、SQL、Provider、具体 Dataset 或任何外部 I/O；canonical serialization/hash 若被原语复用，必须保持纯函数与 provider/storage-neutral。Domain 只定义公共关系，不解释交易日、合约生命周期或市场字段。

| Primitive | 公共语义 |
| --- | --- |
| Scope / Window | Dataset 事实范围与 transient operation 目标；具体业务维度由 Dataset 定义 |
| FetchUnit | Dataset 内稳定 semantic identity、状态与最小同步/完整性/原子写入 ownership；不强制逐日 |
| Record | 一个 owning FetchUnit 的 canonical fact；自然 identity 与字段由 Dataset 定义 |
| Instrument | Dataset-local catalog identity 与事实；可声明 usage: none |
| UnitRecords | 一份 unit 的 canonical Records、相关 Instruments 与必要 completeness basis；结构与 Dataset 无关，内容具有 owning Dataset 业务语义；载体本身不是完整性证明 |
| CachedUnit | 从一致缓存读取的 Unit 与对应 canonical facts / basis；不是 consumer view |

Dataset-independent completeness 要求：Records 唯一归属 owning unit，Instrument association 合法且 Dataset-local，canonical facts 与成功 metadata/hash/count/basis 一致。Dataset Validator 在这些公共约束内定义更强的 predicate；Kernel 不猜 cardinality、expected instruments 或业务 required fields。Validation 的调用与失败分类见 APPLICATION.md，Repository integrity 与 Dataset completeness 的分工见 PORTS.md。

### UnitRecords 载体不变量

UnitRecords 与一个明确 FetchUnit 一起交接，只承载该 unit 的 canonical Records、关联 Instruments 和适用的 completeness basis，不携带跨 unit 的混合成功事实。Records 可为 `0..n`，是否允许零条及其证明由 Dataset completeness predicate 决定；构造空载体、取得 API success 或已有 success status 都不证明完整。

Normalizer 确定性转换得到的载体仍须由 Dataset Completeness Validator 验证业务字段、自然 identity、cardinality、Instrument association 和必要 basis，才可用于成功写入。在验证与提交之间，其事实及 basis 必须保持不变；这不要求新增 validated wrapper、class 或 SQL schema。读取成功缓存时还原的 facts/basis 同样须重新验证，不能信任载体类型或先前验证结果。

Repository 负责公共结构、引用、hash/count 与成功 metadata 的通用数据完整性；Dataset Validator 负责业务完整性。唯一成功事实交接主线与端口责任见 [PORTS.md](PORTS.md)，Application 负责调用顺序；Kernel 不解释 basis 的业务字段或 expected-set 公式。

## 2. 公共逻辑 persistence model

每个 DataSet 的标准模型包含 `dataset_meta`、`fetch_unit`、`instrument` 与 `records` 四个核心实体。以下是逻辑字段与 invariants，不是具体 SQL schema。

### dataset_meta

`dataset_meta` 描述当前 SQLite 自身，至少表达：

```text
dataset_name
schema_version
source_name
created_at
updated_at
```

单独拿到一个 DataSet SQLite 时，必须能够识别其 Dataset identity 与 schema generation；`schema_version` 仅用于 compatibility detection，不驱动 migration。Internal incompatibility 的 Dataset rebuild contract 唯一见 [PERSISTENCE.md](PERSISTENCE.md)。

### fetch_unit

FetchUnit 是 DataSet 的 minimum synchronization unit、minimum reconciliation unit、minimum write ownership boundary 与 coverage state owner。逻辑字段至少包括：

```text
unit_id
unit_key
status
content_hash
record_count
created_at
last_attempt_at
succeeded_at
error_code
error_message
```

具体 DataSet 可以拥有额外 typed identity fields。`unit_key` 必须稳定、确定且唯一表达该 DataSet 内的 FetchUnit identity；不同 DataSet 可以采用不同 identity shape，具体字符串 serialization 留给 implementation design。

第一版持久状态只有 `pending`、`success`、`failed`。`missing` 不是持久状态：`no fetch_unit row = missing`。默认需要执行的条件是：

```text
unit does not exist OR unit.status != success
```

已有 `success` unit 默认不重新 fetch。不引入 stale、dirty、TTL 或其他 refresh state。

`success` 表示 FetchUnit 曾在 `succeeded_at` 时成功取得并原子保存了一份完整合法的 Source Fact set，满足 owning Dataset completeness；不声明当前 provider 事实仍与缓存一致。当前无 TTL、stale-state、background refresh、automatic invalidation 或 refresh engine，不因 future-dated facts 建立特例；真实 upstream revision 需求须另行 semantic decision。

`content_hash` 描述当前 FetchUnit 所拥有的 canonical Record set 的内容 hash，属于 FetchUnit metadata，不属于单条 Record；`record_count` 表达该 unit 所拥有的 Record 数量。Hash 算法与 canonical serialization 留给 implementation design。

FetchUnit 只有在其 Records 成功提交后才能进入 `success`。成功写入必须原子地替换该 unit 拥有的 Records 并更新成功 metadata，使 Records、`content_hash`、`record_count` 与成功状态语义一致；不得在 Records 未成功提交时留下 `success`。事务与失败恢复约束见 [PERSISTENCE.md](PERSISTENCE.md)。

### records

Records 保存该 DataSet 的 Source Facts：

```text
FetchUnit 1
    owns
Records 0..n
```

每条 Record 必须属于且只属于一个 FetchUnit。逻辑公共字段至少为 `record_id`、`fetch_unit_id`，其余字段与自然 Record identity 由 Dataset authority 定义；下层可以对公共 `0..n` cardinality 作更严格的 completeness 约束。

FetchUnit 不要求只拥有一条 Record，例如未来某个 Dataset 的 FetchUnit 可以是一日，而 Records 为当日数千个 instruments 的 Source facts。

只有 owning DataSet 的 FetchUnit execution 可以创建、删除或替换其所拥有的 Records；consumer access 与禁止公开 arbitrary record-level mutation 的规则见 [APPLICATION.md](APPLICATION.md)。

### instrument

`instrument` 是 Dataset-local instrument catalog，不是 repository-wide master instrument table。标准逻辑字段可以表达：

```text
instrument_id
source_code
instrument_type
symbol
exchange
name
valid_from
valid_to
```

具体 required fields 由 Dataset authority 定义。Instrument-addressed Dataset 的 Records 可以通过 `records.instrument_id → instrument.instrument_id` 引用同一 SQLite 内的本地 instrument。

不是所有 Dataset 都具有自然的 tradable instrument。标准模型保留 instrument entity，但 Dataset 必须能够声明 `instrument usage: none`，此时不要求 instrument entries 或 Records 引用，不得人为制造 Instrument 语义。

## 3. Scope、Window 与 Source Request

Scope 由具体 Dataset authority 定义，用于确定该次 operation 所针对的 Source fact 范围。Window 是 transient operation input，描述希望 Dataset 覆盖的范围，第一版只设计一维 Window。

Canonical Scope shape 是否需要多个，由 target model 是否能完整寻址 Dataset fact space 决定，不由 provider API 数量或 transport batching 方式决定；这不引入 generic Scope registry。

Window 不持久化，因为它表达一次操作的目标范围，而非数据库当前 coverage；coverage state 由各 FetchUnit 拥有。Dataset Domain 的 [FetchUnitPlanner](COMPOSITION.md) 根据 Request 中的 Scope + Window 与已验证 Planning Context 确定完整目标 FetchUnit 集合：

```text
Dataset Request (Scope + Window) + Planning Context
    ↓
logically generate desired FetchUnit identities
    ↓
inspect existing fetch_unit state
```

Window 不直接创建 Records，也不定义 Source API request batching。逻辑生成 identity 不等于创建持久 row；哪些 operation 可以改变 persistence state 由 [APPLICATION.md](APPLICATION.md) 定义。

`FetchUnit != Source Request`：FetchUnit 是 DataLake ownership unit；Source Request 是 provider adapter 的传输/调用单位。一个 Source Request 可以返回 `1..n` FetchUnits，返回事实必须按 FetchUnit identity 重新 partition，然后写入各 unit 自己拥有的 Records。不得因为 provider endpoint 支持 date range query，就把整个 range 变成一个 FetchUnit。

## 4. Normalization invariant

Normalization 只稳定表达 Source facts，必须确定且保持 Source 语义；不得生成 analysis-ready 派生结果、补造缺失事实或把缺失当作数值零。逐 unit canonical facts 的业务映射与 completeness 归 Dataset Domain，通过 COMPOSITION.md 的 Normalizer / Validator 接入。

Ensure 的状态协调、Source 执行、验证与提交顺序由 [APPLICATION.md](APPLICATION.md) 拥有，Domain 仅拥有此处的原语与不变量。
