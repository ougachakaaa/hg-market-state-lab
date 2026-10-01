# DataLake 公共领域与 persistence authority

本文件拥有 shared kernel 的公共逻辑 persistence model、Scope / Window / FetchUnit 关系、normalization 与 ensure mutation flow，继承 [模块架构](ARCHITECTURE.md) 的 ownership 边界。自治 Dataset 在上层边界内 specialize 或 constrain 这些 invariants；具体 ownership 与 colocation 由模块架构拥有。公共 operation、结果与 application failure 由 [APPLICATION.md](APPLICATION.md) 拥有；具体 Source、identity、Record fields 与 completeness specialization 经 [DATASETS.md](DATASETS.md) 进入 owning Dataset authority。本文不定义 SQL DDL 或 Dataset-specific fields。

## 1. 公共逻辑 persistence model

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

单独拿到一个 DataSet SQLite 时，必须能够识别其 Dataset identity 与 schema generation。这里不设计 migration framework。

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

`success` 表示 FetchUnit 曾在 `succeeded_at` 时成功取得并原子保存了一份完整合法的 Source Fact set，满足 owning Dataset completeness；不声明当前 provider 事实仍与缓存一致。Freshness policy 继续 deferred，不因 future-dated facts 建立特例。

`content_hash` 描述当前 FetchUnit 所拥有的 canonical Record set 的内容 hash，属于 FetchUnit metadata，不属于单条 Record；`record_count` 表达该 unit 所拥有的 Record 数量。Hash 算法与 canonical serialization 留给 implementation design。

FetchUnit 只有在其 Records 成功提交后才能进入 `success`。成功写入必须原子地替换该 unit 拥有的 Records 并更新成功 metadata，使 Records、`content_hash`、`record_count` 与成功状态语义一致；不得在 Records 未成功提交时留下 `success`。事务机制与失败恢复的实现细节留给后续设计。

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

## 2. Scope、Window 与 Source Request

Scope 由具体 Dataset authority 定义，用于确定该次 operation 所针对的 Source fact 范围。Window 是 transient operation input，描述希望 Dataset 覆盖的范围，第一版只设计一维 Window。

Canonical Scope shape 是否需要多个，由 target model 是否能完整寻址 Dataset fact space 决定，不由 provider API 数量或 transport batching 方式决定；这不引入 generic Scope registry。

Window 不持久化，因为它表达一次操作的目标范围，而非数据库当前 coverage；coverage state 由各 FetchUnit 拥有。Window 负责在 Dataset 与 Scope 下确定目标 FetchUnit 集合：

```text
Window
    ↓
logically generate desired FetchUnit identities
    ↓
inspect existing fetch_unit state
```

Window 不直接创建 Records，也不定义 Source API request batching。逻辑生成 identity 不等于创建持久 row；哪些 operation 可以改变 persistence state 由 [APPLICATION.md](APPLICATION.md) 定义。

`FetchUnit != Source Request`：FetchUnit 是 DataLake ownership unit；Source Request 是 provider adapter 的传输/调用单位。一个 Source Request 可以返回 `1..n` FetchUnits，返回事实必须按 FetchUnit identity 重新 partition，然后写入各 unit 自己拥有的 Records。不得因为 provider endpoint 支持 date range query，就把整个 range 变成一个 FetchUnit。

## 3. Ensure mutation flow

`ensure` 的稳定概念 flow 为：

```text
Dataset + Scope + Window
          ↓
      expand Window
          ↓
  desired FetchUnits
          ↓
 inspect existing state
          ↓
select missing / not success
          ↓
 create / update selected
    fetch_unit state
          ↓
     Source request(s)
          ↓
      Source facts
          ↓
partition by FetchUnit
          ↓
normalize source representation
          ↓
canonical Record set
          ↓
compute content_hash
          ↓
atomic persistence
    ├─ replace records owned by unit
    └─ mark unit success
```

Normalization 只稳定表达 Source facts，必须确定且保持 Source 语义；不得生成 analysis-ready 派生结果、补造缺失事实或把缺失当作数值零。每个 unit 的成功必须满足 Dataset-specific completeness，不能用一次请求的成功代替所有目标 units 的成功。
