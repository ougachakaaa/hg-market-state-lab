# DataLake 模块架构 authority

本文件定义 DataLake 的稳定 ownership、公共逻辑 persistence model、public Application Service 与 operation family。仓库级职责见 [repository architecture](../ARCHITECTURE.md)；具体 DataSet 从 [DATASETS.md](DATASETS.md) 进入。本文不定义 SQL DDL 或内部 Python 文件拆分。

## 1. Ownership 与 persistence boundary

DataLake 持久缓存并管理来自外部 Source 的 reusable source facts。它不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI，也不接管 Snapshot 产品已声明的 Raw Artifact。Public service 的发布不自动建立 Research/Snapshot runtime integration；这些 consumer 的接入须独立设计。

```text
DataLake
    └── DataSet 1..n
            └── exactly one owned SQLite
```

DataSet 是独立的数据与 persistence ownership boundary；canonical Dataset identity 由其 authority 声明。一个 DataSet exactly owns 一个 SQLite database，固定 cardinality 为 `1 DataSet : 1 SQLite`。禁止多个 DataSet 共用 SQLite、一个 DataSet 跨多个 SQLite、cross-Dataset foreign key、DataLake global database 与 global instrument master。

不同 DataSet 必须能够独立存在、独立 refresh、独立删除或重建。这不定义 refresh policy。同一 instrument 可以分别存在于多个 DataSet 自己的 instrument catalog 中；不得据此合并 persistence ownership。具体 filesystem root / filename resolution 留给 implementation design，由 DataLake runtime 自行解析，不由普通 semantic request 或 CLI caller 指定。

这里的 `DataSet` 是 DataLake ownership 概念，不改写 Snapshot 中可能作为产品名称使用的 `Dataset`，也不授权读取或迁移产品私有 Raw。

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

普通 consumer 只通过 owning DataSet 的 public Application Service 消费 cached facts，不直接访问 Records table。只有 owning DataSet 的 FetchUnit execution 可以创建、删除或替换其所拥有的 Records；不得把 arbitrary record-level mutation 发布为公开能力。

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

Window 不持久化，因为它表达一次操作的目标范围，而非数据库当前 coverage；coverage state 由各 FetchUnit 拥有。Window 负责在 Dataset 与 Scope 下确定目标 FetchUnit 集合：

```text
Window
    ↓
logically generate desired FetchUnit identities
    ↓
inspect existing fetch_unit state
```

Window 不直接创建 Records，也不定义 Source API request batching。逻辑生成 identity 不等于创建持久 row；只有 `ensure` 可以创建或更新 FetchUnit persistence state，`coverage` / `export` 不得 materialize missing units。

`FetchUnit != Source Request`：FetchUnit 是 DataLake ownership unit；Source Request 是 provider adapter 的传输/调用单位。一个 Source Request 可以返回 `1..n` FetchUnits，返回事实必须按 FetchUnit identity 重新 partition，然后写入各 unit 自己拥有的 Records。不得因为 provider endpoint 支持 date range query，就把整个 range 变成一个 FetchUnit。

## 4. Application Service 与公共 operation family

DataSet Application Service 是 DataSet 对外发布的 public Python semantic boundary。它接受 Dataset-specific semantic request，根据 Scope + Window 生成目标 FetchUnit identities，查询 coverage、编排 ensure、生成 Dataset-owned export view，并返回稳定 semantic result。

```text
Consumers (lab CLI / future Research / future Snapshot / future consumers)
    ↓
DataSet public Application Service
    ├─ Source Adapter → external API
    └─ Repository → owned SQLite
```

Consumers 不直接操作 SQLite、Repository、FetchUnit / Records tables 或 Source adapter。Public boundary 不暴露 SQL、SQLite path、unit_id / record_id 等 persistence identity、argparse namespace、provider transport response 或 internal repository object。未来模块应直接消费 public semantic request/result/view，不调用 CLI 或反向解析 JSON export；实际 consumer integration 须另行设计。

第一版公开 semantic operations 固定为 `coverage`、`ensure`、`export`；`read` 与 `sync` 不作为 public product / CLI verbs。公共 operation family 不要求通用 abstract base class、plugin system 或 registry framework；每个 DataSet 拥有自己的 request/result/view contract。

| operation | Source I/O | SQLite mutation | semantic purpose |
| --- | --- | --- | --- |
| coverage | 禁止 | 禁止 | 描述目标 Scope + Window 的当前缓存状态 |
| ensure | 允许 | 允许 | 尽可能补齐目标 Scope + Window |
| export | 禁止 | 禁止 | 生成 Dataset-owned business-oriented view |

`coverage` / `export` 必须真正 read-only：不创建数据库、表或 pending rows，不隐式 ensure，也不因缓存缺失访问 Source。不存在的缓存按目标 units 全部 missing 表达；已经存在但无法读取或无法合法解释的 Dataset 属于 application failure，不冒充 missing。两者不要求 Source credential。

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

计数均为非负整数，`complete` 为 boolean。统计只针对目标 identities：没有 row 为 missing；已有 row 按 success、pending、failed 分类，四类互斥且总和等于 requested_units。Pending 不计入 failed；success 必须满足 Records 与成功 metadata 一致的 invariant。

```text
complete = successful_units == requested_units
           AND missing_units == 0
           AND pending_units == 0
           AND failed_units == 0
```

`complete = false` 是合法查询结果，不是 operation failure。Coverage 查询不得为了统计 missing 而创建 rows。

### ensure

`ensure(request) → EnsureResult` 尽可能使所有目标 FetchUnits 达到 success。默认 selection 为 missing 或 status != success；已有 success units 默认 skip。公共字段为：

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

Coverage 不完整时仍可返回当前可用 view，准确声明 coverage.complete = false。Payload 只能包含目标范围内成功 FetchUnits 的合法 cached facts，不能把 failed / pending units 的不完整 Records 当作成功数据；无可用事实时返回 Dataset 定义的空 payload。Coverage 与 payload 必须描述同一缓存状态，不得产生互相矛盾的完整性声明。

Dataset owns export semantics；lab owns JSON serialization 与 file delivery。未来 consumer 可以直接消费返回的 view，无需先写 JSON 再读取。只有出现真实第二个 view 时再扩展 selection mechanism，不预建 generic view registry。

## 5. Ensure mutation flow

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

## 6. Canonical Python boundary 与 runtime configuration

Canonical Python namespace 为 `data_lake`，源码 ownership 位于 `data-lake/src/data_lake/`。遵守 repository root 唯一 Python project、dependency graph 与 worktree-local 根 `.venv` invariant，不创建 module-local Python project。公开 consumer 只进入 DataSet public Application Service；Repository、SQLite adapter 与 Source adapter 是 internal implementation surface，具体内部文件拆分留给 implementation。

Source credential 属于 runtime/provider configuration，不是 Dataset semantic argument。后续 Tushare implementation 复用仓库已有约定：环境变量 `TUSHARE_TOKEN` 优先，本地 `market-snapshot/.env` 仅作 fallback，加载不覆盖已有环境变量；只有需要 Source I/O 时解析凭据。需要 fetch 但 token 缺失时，在 Source request 前明确失败；全部 success 的 ensure 不需要 token。不得增加 `--token` 或第二套 secret convention，也不因此授权 import Snapshot 私有 Source client 或 artifact helper。

SQLite location 由 DataLake runtime 自行解析，不接受 semantic request 中的 path 或 CLI `--db`。本 authority 不固定 storage-root / filename，也不创建跨模块 config framework。现有本地凭据操作见 [README](../README.md) 与 [DEVELOPMENT](../DEVELOPMENT.md)。

## 7. Authority 导航与 deferred design

```text
repository ARCHITECTURE.md
    ↓
data-lake/ARCHITECTURE.md
    ↓
DATASETS.md
    ↓
datasets/<dataset>/ARCHITECTURE.md
```

模块 authority 拥有稳定公共 Application Service / operation / envelope 边界和 persistence invariants；[catalog](DATASETS.md) 只提供 Dataset navigation，不复制 schema。Dataset authority 在这些边界内拥有 Source、Scope、Window shape、FetchUnit / Record identity、Record fields、instrument usage、completeness、具体 request/result/view 与 Dataset-specific CLI arguments。Repository CLI topology 与 delivery 由 [lab authority](../lab/ARCHITECTURE.md) 拥有，不在本文复制完整 CLI contract。

本次变更仅编码 authority，不实现 Python、SQLite DDL、migration、Tushare client、CLI 或 HTTP。后续 implementation 必须实现已声明的 public contract；内部文件、具体存储类型、key serialization、canonicalization/hash、事务机制、失败恢复与 adapter batching 留给 implementation design，不得重新决定已固定的 semantic request、结果计数或 export contract。Research/Snapshot integration 须独立设计。

Refresh / force / invalidation policy、TTL、stale state、多维 Window、Dataset dependency graph、cross-Dataset query engine、Source request audit table、plugin framework 与 generic workflow engine 均不在本轮设计范围内。
