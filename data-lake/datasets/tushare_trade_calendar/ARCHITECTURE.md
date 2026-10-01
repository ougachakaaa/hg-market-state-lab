# tushare_trade_calendar Dataset authority

本文件拥有首个交易日历 DataSet 的 Source、Scope、Window、identity、Source fact fields 与 completeness。公共 persistence model 与操作边界继承 [DataLake architecture](../../ARCHITECTURE.md)；Dataset navigation 见 [catalog](../../DATASETS.md)。

## 1. Identity、Source 与 Scope

Canonical Dataset identity 为 `tushare_trade_calendar`。本 DataSet 独立拥有一个 SQLite，不与其他 DataSet 共享数据库。

Source 为 **Tushare `trade_cal`**；Scope 为 `exchange`。Source 请求必须显式指定 exchange，不得依赖 provider default。Exchange 是 calendar 的 Scope / identity，不是 Instrument。

## 2. Window 与 FetchUnit identity

Window 是 transient 日期范围输入：`start_date`、`end_date`，两端 inclusive：

```text
start_date <= cal_date <= end_date
```

Window 只描述希望覆盖的日期范围，不持久化、不表示已有 coverage，也不决定 Source batching。在指定 exchange 下，Window 展开为范围内每个自然日对应的目标 FetchUnit，包括休市日。

FetchUnit identity 为 `(exchange, cal_date)`；unit key 必须稳定、确定且唯一编码这一 identity，但本文不规定具体字符串 serialization。一个 exchange 下的整个 date range 不是 FetchUnit；即使一次 `trade_cal` 请求返回多日，也必须按上述 identity partition。

## 3. Records 与 completeness

Record identity 同样为 `(exchange, cal_date)`。Records 继承公共 `record_id`、`fetch_unit_id`，保存以下 Tushare Source facts：

```text
exchange
cal_date
is_open
pretrade_date
```

保留自然日完整状态，不能只保存 `is_open = 1` 的交易日，也不能把缺失事实转换成休市状态。Source representation normalization 必须保持这些事实的语义；具体存储类型与合法 null 表达留给 implementation design。

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

默认只执行 missing 或非 `success` 的 units，不重新 fetch 成功 units。`ensure / sync` 可访问 Tushare 并写入本 Dataset SQLite；`read` 只读 SQLite，不因日历缺失而隐式访问 Source。Refresh / force / invalidation 与具体 API 留给后续设计。
