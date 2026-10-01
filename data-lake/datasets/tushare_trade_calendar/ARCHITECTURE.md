# tushare_trade_calendar Dataset authority

本文件拥有首个交易日历 DataSet 的 Source、Scope、Window、identity、Source fact fields、completeness、public application specialization 与 Dataset-specific CLI arguments。模块 ownership 继承 [DataLake architecture](../../ARCHITECTURE.md)；公共 domain / persistence semantics 继承 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)，公共 operation、结果计数、envelope 与 application failure 继承 [APPLICATION.md](../../APPLICATION.md)。Dataset navigation 见 [catalog](../../DATASETS.md)，CLI topology 与 delivery 见 [lab authority](../../../lab/ARCHITECTURE.md)。

## 1. Identity、Source 与 Scope

Canonical Dataset identity 为 `tushare_trade_calendar`；SQLite ownership 继承模块 invariant。

Source 为 **Tushare `trade_cal`**；Scope 为 `exchange`。Source 请求必须显式指定 exchange，不得依赖 provider default。Exchange 是 calendar 的 Scope / identity，不是 Instrument。

## 2. Window 与 FetchUnit identity

Window 是 transient 日期范围输入：`start_date`、`end_date`，两端 inclusive：

```text
start_date <= cal_date <= end_date
```

Window 的 transient input 与 Source batching 边界继承公共 domain authority。在指定 exchange 下，Window 展开为范围内每个自然日对应的目标 FetchUnit，包括休市日。

FetchUnit identity 为 `(exchange, cal_date)`；unit key 的稳定性、唯一性与 serialization 边界继承公共 domain authority。一个 exchange 下的整个 date range 不是 FetchUnit；即使一次 `trade_cal` 请求返回多日，也必须按上述 identity partition。

## 3. Records 与 completeness

Record identity 同样为 `(exchange, cal_date)`。Records 继承公共 `record_id`、`fetch_unit_id`，保存以下 Tushare Source facts：

```text
exchange
cal_date
is_open
pretrade_date
```

保留自然日完整状态，不能只保存 `is_open = 1` 的交易日，也不能把缺失事实转换成休市状态。Source representation normalization 必须保持这些事实的语义；公开值类型与 null 语义见下文 application contract，具体 SQLite 存储类型留给 implementation design。

本 Dataset 第一版对公共 Record cardinality 作如下约束：

```text
1 successful FetchUnit
    → exactly 1 calendar Record
```

该 Record 的 `(exchange, cal_date)` 必须与其 owning FetchUnit 匹配；同一 identity 不得形成多条 canonical Records。只有满足此 completeness 且成功原子提交 Records 与 metadata 的 unit 才能标记 `success`。

Source response 缺失目标日期时，该 unit 是 incomplete / failed，必须按公共 `failed` 状态处理；`incomplete` 不新增为持久状态。不得静默视为休市、伪造 Record，或因为同批其他日期成功而标记该 unit 成功。

## 4. Instrument 与操作边界

```text
instrument usage: none
```

本 Dataset 没有自然的 tradable instrument；不要求 instrument entries 或 `records.instrument_id` 引用。不得将 exchange 或 synthetic calendar object 伪装成 Instrument。

Operation 的 Source I/O、SQLite mutation 与 read-only 规则继承公共 [Application contract](../../APPLICATION.md)；本 Dataset 的 `ensure` 使用 Tushare `trade_cal`。默认 unit selection 继承公共 domain authority；Refresh / force / invalidation 不属于第一版 public contract。

## 5. Public Application Contract

### Common range request

三个 operation 共享 `TradeCalendarRange`：

| 字段 | Public semantic type | 约束 |
| --- | --- | --- |
| exchange | string | 必填且非空，显式指定 Source exchange，无 provider default |
| start_date | date | 必填，inclusive lower bound |
| end_date | date | 必填，inclusive upper bound，start_date <= end_date |

Date 的 canonical semantic type 为 `date`；argparse namespace、raw date strings、credential、SQLite path 与 output path 不属于 service request。无效 range 为 application failure，不能自动交换日期或猜测 exchange。

### coverage 与 ensure

```text
coverage(TradeCalendarRange) → CoverageResult
ensure(TradeCalendarRange)   → EnsureResult
```

结果字段、计数、complete 与缺失缓存处理继承公共 [Application contract](../../APPLICATION.md)。目标 identities 为指定 exchange 下 inclusive date range 内的每一个自然日，包括休市日；requested_units 为自然日数量。

Ensure 可以按日期范围 batch 调用 Tushare `trade_cal`，但返回事实必须重新按 `(exchange, cal_date)` partition。已有 success units 跳过；即使 batch response 包含它们，也不能重写这些成功 units。每个选中 unit 独立验证 exactly one canonical Record、identity 匹配与字段合法性，再原子提交 Records + hash + metadata。

缺失目标日期、冲突或重复 identity、无法合法规范化的字段不能形成 success，按对应 unit failure 返回，不补造事实；其他可完整验证的 units 继续成功写入。`failures` 每项定位 `(exchange, cal_date)` 并给出可读原因。可恢复的 Source request failure 应映射到该请求尝试的目标 units；无法执行整个 operation 的错误按公共 application failure 边界处理。正常 EnsureResult 的 records_written 等于本次 succeeded_units，因为每个成功 unit exactly owns one Record。

### calendar export view

```text
export(TradeCalendarRange) → TradeCalendarExport
```

第一版唯一 semantic view 为 `calendar`，export_schema_version 为整数 `1`。Export envelope 结构固定为：

```text
dataset: "tushare_trade_calendar"
view: "calendar"
export_schema_version: 1
scope:
    exchange: <requested exchange>
window:
    start_date: <requested start_date>
    end_date: <requested end_date>
coverage: <CoverageResult for this scope + window>
records:
    [
        {
            exchange
            cal_date
            is_open
            pretrade_date
        }
    ]
```

`records` 是 public export records，不是 persistence rows。每项恰好包含以下四个公开字段：

| 字段 | Public semantic type | JSON representation |
| --- | --- | --- |
| exchange | string | 与 requested exchange 相同的字符串 |
| cal_date | date | YYYY-MM-DD 字符串 |
| is_open | integer，值仅为 0 或 1 | JSON integer 0 或 1，不是 boolean |
| pretrade_date | date 或 None | YYYY-MM-DD 字符串或 JSON null |

Window 日期同样以 YYYY-MM-DD 序列化。`pretrade_date = None` 只表达 Source 合法缺席；不能将无效日期、缺失 required fact 或整条 Record 的缺失转换成 null。公开 `is_open` 必须保持 Source 开市/休市事实，不把缺失视为 0；存储表示不得反向改变这些 public types。

Records 的可导出 facts 与 public representation 边界继承公共 Application contract；本 calendar view 还不得包含 unit_key、content_hash 或 SQLite metadata。按 cal_date ascending 稳定排序，保留目标 exchange 与日期范围内的自然日 calendar facts，包括休市日，不增加 is_open filter。

Incomplete coverage、成功 facts 的选择与 service/file delivery 边界继承公共 Application contract；无成功 units 时 records 为 `[]`。本 view 不补齐缺失日期。

## 6. Dataset-specific CLI arguments

`lab datalake coverage/ensure/export tushare_trade_calendar` 的 semantic arguments 固定为：

| 参数 | Delivery parsing |
| --- | --- |
| --exchange | 必填，转换为 range.exchange |
| --start-date | 必填，严格 YYYY-MM-DD 日期字符串，解析为 date |
| --end-date | 必填，严格 YYYY-MM-DD 日期字符串，解析为 date |

Service 仍负责验证 semantic range。CLI 不把 raw strings 或 argparse namespace 传入 service。Export 的必填 `--output` 及文件 delivery 由 lab authority 拥有，不进入 TradeCalendarRange；不增加 `--view`、is_open filter、`--token` 或 `--db`。

```bash
lab datalake coverage tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-12-31
lab datalake ensure tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-12-31
lab datalake export tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-12-31 --output calendar.json
```

以上为正式目标 contract，不声明当前 runtime 已实现。Credential 的按需解析与 internal storage resolution 继承公共 [Application contract](../../APPLICATION.md)。

## 7. Source runtime configuration

后续 Tushare implementation 复用仓库已有约定：环境变量 `TUSHARE_TOKEN` 优先，本地 `market-snapshot/.env` 仅作 fallback，加载不覆盖已有环境变量。Token 的按需解析、缺失时的失败边界与禁止私有 Snapshot import 的规则继承公共 [Application contract](../../APPLICATION.md)。现有本地凭据操作见 [README](../../../README.md) 与 [DEVELOPMENT](../../../DEVELOPMENT.md)。
