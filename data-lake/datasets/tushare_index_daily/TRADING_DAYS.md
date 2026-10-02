# Index Daily 交易日 prerequisite authority

本文件拥有 Index 目标交易日展开、Calendar public dependency 调用与 prerequisite failures，继承 [Dataset architecture](ARCHITECTURE.md) 与公共 [APPLICATION.md](../../APPLICATION.md)。Producer 契约是 [Calendar SERVICE.md](../tushare_trade_calendar/SERVICE.md)，不在本文件重定义 Calendar facts。

## 1. Direction 与日历选择

```text
IndexDailyService
    → tushare_trade_calendar public Application Service
        → Calendar-owned Source / SQLite
```

V1 对本 Dataset 支持的沪深指数使用显式 `exchange="SSE"` 的 TradeCalendarRange，Window 与 Index request 完全相同。这里的 SSE 是本 Dataset 的共同沪深交易日基准，不是 index 的 exchange / publisher 属性，也不从 `.CSI` 后缀推断交易所。Tushare [trade_cal 文档](https://tushare.pro/document/2?doc_id=26) 说明沪深交易日历相同；此项 selection 是本 Dataset 明确的 specialization，不是全仓 calendar default。

只消费 Calendar `export(request)` 的 transport-neutral TradeCalendarExport（view=`calendar`），要求 coverage.complete=true、每个自然日恰有一个合法 TradeCalendarRecord。过滤其中 `is_open == 1` 的日期为 D；休市日不生成 Index unit。不得用 weekday、节假日 heuristic、Index 返回行或 `pretrade_date` 反推完整 D。

```text
desired_units = {(code, d) | code in canonical index_codes, d in D}
requested_units = len(canonical index_codes) * len(D)
```

完整 calendar 中 D 为空时，零 requested units、complete=true、ensure 零 attempts / records_written、export 空 records 均合法。Calendar 不完整时无法判断 D，不能返回上述零目标结果。

## 2. Operations 与失败

| Index operation | Calendar 调用 / prerequisite 行为 |
| --- | --- |
| coverage | 只调用 Calendar export；不完整或无法读取则 OperationError |
| export | 同 coverage，固定合法 Calendar view 后生成 Index committed snapshot view |
| ensure | 先 Calendar export；若 incomplete，调用 Calendar ensure 补齐相同范围，再 export 取得完整 view；否则不调用 Calendar ensure |

Index ensure 必须在完成 prerequisite validation 后才展开/执行自己的 units，不因未知目标建立 pending rows 或请求 index_daily/index_basic。Calendar ensure 返回 complete=false、随后 export 仍 incomplete、credential 缺失、operation failure 或非法 semantic view 时，Index 抛有 Calendar context 的 OperationError。此时没有正常 Index EnsureResult，Calendar 已提交的成功 facts 保留；不跨库 rollback，也不将 Calendar 日期塞进 Index UnitFailure identities。

Index request 自身无效时先抛 InvalidRequestError，不调用 Calendar。合法 request 被 producer 拒绝属于内部 composition failure，映射为 OperationError。Read-only Calendar cache 缺失属于 prerequisite unavailable；绝不能以已有日期子集统计 Index completeness，不能把缺失当休市或绕过 producer 另调 trade_cal。

Calendar 完整以后，Index 自己的 missing/pending/failed 是正常 coverage incompleteness，自己的可恢复 Source/unit failures 按 SERVICE.md 返回。Index 已有 success 默认跳过；如果 prerequisite 完整且目标全部 success，整个 ensure 不需要 token。Calendar 不完整时即使 Index 存有行情，也无法证明完整目标集合，ensure 仍可能需要 Calendar Source I/O。

## 3. Snapshot 与独立 state

每次 Index operation 固定一个 Calendar export semantic snapshot，不在逐 unit execution 中重新展开 D。Index export 的 coverage 与 records 来自同一个 Index committed cache snapshot，并使用同一份 D；不要求两库同一时刻 snapshot，不保证 Source freshness。

Calendar 保持完整自然日事实及自有 SQLite；Index 不复制 Calendar FetchUnits、引用其 unit_id、读其 SQLite / Repository / internal adapter，也不反向更改 Calendar authority。Calendar cache 被删除不会连带删除 Index owned state；后续 Index operation 若 prerequisite 不可用，仍按本契约明确失败。
