# DataLake 公共 Application Service authority

本文件拥有 DataSet public Application Service 的公共 semantic contract，继承 [模块架构](ARCHITECTURE.md) 的职责与依赖边界。Scope / Window、FetchUnit 状态、Record ownership、原子成功与 mutation flow 由 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 拥有；Dataset-specific request、view、payload 与 specialization 经 [DATASETS.md](DATASETS.md) 进入 owning Dataset authority。CLI topology、serialization 与 file delivery 由 [lab authority](../lab/ARCHITECTURE.md) 拥有。

## 1. Application Service 与公共 operation family

DataSet Application Service 是 transport-neutral canonical consumer boundary，公开 Python semantic request/result/view。它在内部将 Dataset-specific request 解释为 Scope + Window 和目标 FetchUnit identities，查询 coverage、编排 ensure、生成 Dataset-owned export view；caller 不需要理解 persistence mechanics。Dataset-specific consumer contract 经 catalog、Dataset ARCHITECTURE.md 进入 SERVICE.md。

Consumer → public Application Service → internal Source Adapter / Repository 的依赖方向继承 [模块架构](ARCHITECTURE.md)。

不得把 arbitrary record-level mutation 发布为公开能力。Consumers 不直接操作 SQLite、Repository、FetchUnit / Records tables 或 Source adapter。Public boundary 不暴露 SQL、SQLite path、unit_id / record_id 等 persistence identity、argparse namespace、provider transport response 或 internal repository object。未来模块应直接消费 public semantic request/result/view，不调用 CLI 或反向解析 JSON export；实际 consumer integration 须另行设计。

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

具体 public exception placement 与内部 exception translation 留给 implementation，caller 必须能从 public boundary 识别这两类 failure。现有 core 的 ApplicationFailure 尚未完成此分类，不能据此削弱目标 contract。DataLake 不定义 CLI exit code 或 HTTP status code；adapter 分别映射 request failure 与 execution failure。

## 2. Runtime configuration 与调用边界

Source credential 属于 runtime/provider configuration，不是 Dataset semantic argument；只有需要 Source I/O 时解析凭据。需要 fetch 但 credential 缺失时，在 Source request 前明确失败；全部 success 的 ensure 不需要 credential。不得增加 `--token` 或第二套 secret convention，也不因此授权 import Snapshot 私有 Source client 或 artifact helper。具体 provider credential convention 由 owning Dataset authority 声明。

普通 consumer 创建 Dataset service 不要求提供 SQLite path、Repository、Source Adapter、database connection 或 token；configuration/composition 属于 DataLake internal ownership。Coverage / export 与 factory 不要求 Source credential，ensure 仅在实际 Source I/O 必要时解析。Missing required credential 属于 OperationError。

SQLite location 由 DataLake runtime 自行解析，不接受 semantic request 中的 path 或 CLI `--db`。具体 filesystem root / filename resolution 留给 implementation design；本 authority 不固定 storage-root / filename，也不创建跨模块 config framework。现有本地凭据操作见 [README](../README.md) 与 [DEVELOPMENT](../DEVELOPMENT.md)。
