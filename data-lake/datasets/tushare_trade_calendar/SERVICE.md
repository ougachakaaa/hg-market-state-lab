# tushare_trade_calendar Public Application Service authority

本文件拥有 Dataset-specific public semantic request/result/view、Python consumption、failures specialization、Dataset runtime composition 与 serialization 边界。继承 [Dataset domain](ARCHITECTURE.md) 与公共 [APPLICATION.md](../../APPLICATION.md)；Tushare provider execution 由 [providers/TUSHARE.md](../../providers/TUSHARE.md) 拥有。不定义 CLI option names、HTTP endpoints、HTTP status codes 或存储实现。

## 1. Canonical service 与 Python boundary

Canonical public Python surface 属于 `data_lake.datasets.tushare_trade_calendar`，至少发布以下概念：

```text
TradeCalendarService
TradeCalendarRange
TradeCalendarRecord
TradeCalendarExport
create_service()
```

Public operations 为：

```text
coverage(request: TradeCalendarRange) → CoverageResult
ensure(request: TradeCalendarRange)   → EnsureResult
export(request: TradeCalendarRange)   → TradeCalendarExport
```

```text
lab CLI / future HTTP API / Research / Snapshot-Preparation / Python consumers
    ↓
data_lake.datasets.tushare_trade_calendar Public Application Service
    ↓
internal Source Adapter / Repository / SQLite
```

Consumer 调用、factory 与 runtime boundary 继承 [APPLICATION.md](../../APPLICATION.md)，依赖权限继承 [模块架构](../../ARCHITECTURE.md)。普通 consumer 使用 `create_service()`；本 Dataset 内部组合 trade_cal adapter 与 owned storage。

`CoverageResult`、`EnsureResult`、`UnitFailure` 与两类 application errors 继承公共 Application authority，可由公共 `data_lake` facade 提供；caller 必须能消费结果并识别错误，无需访问 internals。内部文件拆分、类型载体与共享类型 re-export 方式留给 implementation，不改变 public semantics。

Public Python consumption：

```python
from datetime import date
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange, create_service

service = create_service()
request = TradeCalendarRange(
    exchange="SSE", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)
)
coverage = service.coverage(request)
result = service.ensure(request)
view = service.export(request)
```

## 2. Common semantic request

三个 operation 共享 `TradeCalendarRange`：

| 字段 | Public Python semantic type | 约束 |
| --- | --- | --- |
| exchange | str | 必填、非空的 provider-native canonical identifier，无 provider default |
| start_date | date | 必填，inclusive lower bound |
| end_date | date | 必填，inclusive upper bound，start_date <= end_date |

日期是 Python `datetime.date`，不是 raw strings 或 datetime timestamps。未来自然日 Window 合法，不按 today 裁剪：ensure 可缓存 Source 已发布的未来日历事实；未发布/缺失日期按逐日 completeness failure 返回。Coverage/export 对未来日期继承公共 read-only 与 missing 行为，不引入 refresh 特例。Exchange 不猜测、不改写大小写或建立本地 enum；空白或含首尾空白的输入不是 canonical identifier，不通过 trim 后替换输入。Provider 支持哪些 canonical identifiers 由 Source 决定，不为 request validation 额外访问 Source。

错误 semantic types、缺失值与无效 range 属于 `InvalidRequestError`，不能自动交换日期。Scope / Window expansion 是内部 domain interpretation；caller 只表达 range，无需构造 FetchUnits 或理解 persistence mechanics。Credential、SQLite path、output path、argparse namespace 与 HTTP DTO 不属于 request。

## 3. Coverage 与 ensure specialization

结果字段、互斥计数、complete 与不存在缓存的处理继承 [APPLICATION.md](../../APPLICATION.md)。本 Dataset 的 `requested_units = (end_date - start_date).days + 1`，包括休市日。

Ensure 使用 Tushare `trade_cal`，Source 请求显式指定目标 exchange。Batching 不改变 [domain completeness](ARCHITECTURE.md)；返回 facts 按 identity partition。已有 success units 跳过，即使 batch response 包含它们也不重写。每个 selected unit 独立验证并原子提交。

缺失目标日期、duplicate / conflicting identity、目标 identity 不匹配、非法 normalization 或 completeness failure 按受影响 unit 返回 failure，其他可完整验证 units 继续尽可能写入。外来 identity 不能替代目标 unit，也不能写入目标之外的 units。可恢复的 Source request failure 映射到该请求实际尝试的目标 units；不能确定合法目标归属的 Source response 不得用于宣告所尝试 units 成功。

`EnsureResult.failures` 每项使用公共 `UnitFailure` 语义：`identity` 为 `(exchange: str, cal_date: date)`，`reason` 为可读字符串；每个最终 failed attempt 恰有一项，不使用 persistence ID 或 transport response。`records_written = succeeded_units`，因为每个成功 unit exactly owns one Record。Complete 仍按操作结束后的 coverage 决定。不可执行的整个 operation 按下文抛 application failure。

## 4. TradeCalendarRecord 与 semantic export view

`export` 遵循 [APPLICATION.md](../../APPLICATION.md) 的 semantic view、read-only 与 delivery boundary。唯一 view 为 `calendar`，不引入 view selector。

`TradeCalendarRecord` 恰有四个 public semantic fields：

| 字段 | Public Python semantic type |
| --- | --- |
| exchange | str |
| cal_date | date |
| is_open | int，值为 0 或 1，不是 bool |
| pretrade_date | date 或 None |

Facts 合法性与 Source 合法缺席由 [Dataset domain](ARCHITECTURE.md) 拥有；`None` 只表达该合法缺席。Internal persistence fields 不进入 Record。

`TradeCalendarExport` 至少拥有以下 semantic fields：

| 字段 | Semantic value / type |
| --- | --- |
| dataset | str，固定 `tushare_trade_calendar` |
| view | str，固定 `calendar` |
| export_schema_version | int，固定 `1`，不是 SQLite schema version |
| scope | TradeCalendarScope，exchange 等于 request.exchange |
| window | 日期范围值，start_date / end_date 为 request 对应的 date |
| coverage | CoverageResult，针对该 request |
| records | TradeCalendarRecord 有序序列，按 cal_date ascending |

Scope 与 window 是 view context，caller 不必预先构造它们；Python 容器类型留给 implementation，但其字段与值必须可直接消费，不能要求 caller 解析 JSON。

Records 只包含目标 exchange / inclusive range 内成功 units 的合法 facts，包括休市日，不增加 is_open filter，不补齐缺失日期。每个成功 unit 对应一条 Record，因此 `len(records) = coverage.successful_units`；无成功 facts 时为空序列。Incomplete coverage 仍是合法 view。

Coverage 与 records 遵守公共 Application authority 的 export consistency / public view invariant。

## 5. Semantic objects 与 wire meaning

Service 返回 semantic objects，JSON 只是一种 adapter representation。稳定 JSON meaning 为：日期成为 `YYYY-MM-DD`；`None` 成为 `null`；`is_open` 成为 integer 0 / 1；coverage 计数为 JSON integers、complete 为 boolean；records 成为有序 array。Scope 表达 `{exchange}`，window 表达 `{start_date, end_date}`，envelope / Record 字段名与上述 contract 一致。

Serialization 与 delivery boundary 继承 [APPLICATION.md](../../APPLICATION.md)；CLI parsing、JSON file delivery 与 exit-code mapping 见 [lab authority](../../../lab/ARCHITECTURE.md)。

## 6. Application failures 与 runtime configuration

Failure taxonomy 与 lazy Source I/O 继承 [APPLICATION.md](../../APPLICATION.md)，本 Dataset 不增加公共 failure category；输入错误见第 2 节，可恢复逐日 failures 见第 3 节。

Calendar composition 提供自己的 storage context，adapter 通过共享 Executor 执行 trade_cal。Provider execution 继承 [TUSHARE.md](../../providers/TUSHARE.md)，storage lifecycle 与 compatibility 继承 [PERSISTENCE.md](../../PERSISTENCE.md)。
