# Futures Daily 交易日 prerequisite authority

本文件拥有目标交易日展开与 Calendar public dependency，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [APPLICATION.md](../../APPLICATION.md)。Producer 是 [Calendar SERVICE.md](../tushare_trade_calendar/SERVICE.md)，不在本文件重定义其 facts。

## 1. CFFEX 目标展开

FuturesDailyService 只通过 `data_lake.datasets.tushare_trade_calendar` public service，使用显式 `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`。Window 与 Futures request 完全相同，不按所选产品改变 exchange，不绕过 Calendar 另调 trade_cal。

固定一份 Calendar export（view=calendar），要求 coverage.complete=true、范围内每个自然日恰有一条合法 TradeCalendarRecord。其 is_open==1 的日期为 D：

```text
desired_units = {(p, d) | p in canonical product_codes, d in D}
requested_units = len(canonical product_codes) * len(D)
```

不以 weekday、日行情返回、catalog lifecycle 或 pretrade_date 猜 D。完整 Calendar 的 D 为空时，零目标 complete=true、ensure 零 attempts/records_written、export 空 records 合法；它不同于开市日 expected contracts 已证明为空的零 Records success。

## 2. 调用权限与失败

| Futures operation | Calendar prerequisite |
| --- | --- |
| coverage / export | 只调用 Calendar export；不完整、无法读取或非法 view 时 OperationError |
| ensure | 先 export；仅 incomplete 时 ensure 同一范围，再 export；必须取得合法完整 view |

自身 request 先验证，无效时 InvalidRequestError，不调用 producer。Calendar 不完整时不能展开 Futures 子集、把未知当休市或建立自己的 pending units。Calendar ensure 未补齐、credential 缺失、读写/execution failure、非法 view 或内部合法 request 被 producer 拒绝时，抛带 Calendar context 的 OperationError；无正常 Futures EnsureResult，不尝试 Futures metadata/daily，也不改变自己的 units。

Calendar 先前已提交事实保留，不跨库 rollback。Calendar dates 不进入 Futures UnitFailure；Calendar rows/requests/writes 不计入任何 Futures counters。Calendar 完整后，Futures 自身的 missing/pending/failed 及可恢复 unit failures 才属于正常结果。

完整 Calendar 且所有 Futures 目标已 success 时，ensure 无 Source I/O、不要求 token；Calendar 不完整时即使 Futures 存有行情仍须补齐 prerequisite。Read-only 链无 credential 要求、不创建任一数据库或 rows。

## 3. 独立 state 与一致性

每次 operation 固定 D，不逐 unit 重展开。Futures export 的 coverage、Records 与关联 metadata 来自同一个 Futures committed snapshot，针对这份固定 D；不声称两个 Dataset 共享数据库 snapshot 或 freshness。

Calendar 保留自己的自然日 facts/SQLite；Futures 不复制其 FetchUnits、不读其 Repository/SQLite/adapter，不引用其 persistence IDs。Calendar state 删除不删除 Futures state，但后续 prerequisite 不可用时按本契约失败。
