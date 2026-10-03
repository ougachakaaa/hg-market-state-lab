# Options Daily 交易日 prerequisite authority

本文件拥有目标交易日展开与 Calendar public dependency，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [APPLICATION.md](../../APPLICATION.md)。Producer 是 [Calendar SERVICE.md](../tushare_trade_calendar/SERVICE.md)，其 facts 不在本文件重定义。

## 1. CFFEX product-day 目标

OptionsDailyService 只通过 `data_lake.datasets.tushare_trade_calendar` public service 使用显式 `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`，与 Options request 相同 inclusive Window；不按 expiry/strike/product 改变日历，不直接请求 trade_cal。

固定 Calendar export（view=calendar），要求 coverage.complete=true、范围内每个自然日恰有一条合法 TradeCalendarRecord。过滤 is_open==1 得 D：

```text
desired_units = {(p, d) | p in canonical product_codes, d in D}
requested_units = len(canonical product_codes) * len(D)
```

不按 weekday、日行情、产品上市日、expiry 或 pretrade_date 推测 D，不因 catalog 缺口收缩目标。完整 Calendar 中 D 为空时，零目标 complete=true、ensure 零 attempts/records_written、export 空 records；不同于开市日已证明无 active contracts 的零 Records success。

## 2. Operations 与 failure

| Options operation | Calendar prerequisite |
| --- | --- |
| coverage / export | 仅 Calendar export；不完整、读取失败或非法 view 时 OperationError |
| ensure | 先 export；仅 incomplete 时 ensure 同一范围，再 export 取得合法完整 view |

自身无效 request 在 dependency 调用前 InvalidRequestError。Prerequisite 未完整时不能建立自己的 pending units、访问 Options metadata/daily 或按已知日期子集返回正常结果。Calendar ensure 后仍不完整、credential/读写/execution failure、非法 semantic view 或合法内部 request 被 producer 拒绝，均映射为带 Calendar context 的 OperationError；无正常 Options EnsureResult，自身 units 不改变。

Calendar 已提交事实保留，无跨库 rollback。其日期不进入 Options UnitFailure，其 rows/requests/writes 不进入 Options counters。Calendar 完整后，自己的 missing/pending/failed 与可恢复产品日 failure 按 SERVICE.md 表达。

完整 Calendar 与全部 success Options 目标使 ensure 无需 Source/token；Calendar 不完整时不能靠已有 Options 行情绕过 prerequisite。Coverage/export 整条链真正 read-only，不创建库/rows、不隐式 ensure、不要求 credential。

## 3. Snapshot 与 storage lifecycle

每次 operation 固定 D；Options export 的 coverage、Records 和关联 Instrument facts 来自同一个 Options committed snapshot，并针对这份固定目标，不声称 Calendar/Options 跨库同一 snapshot 或 Source freshness。

Calendar 保留自己自然日 facts 与 SQLite；Options 不复制其 FetchUnits、不访问其 internals/persistence IDs。两库独立删除/重建；Calendar 缺失不删除 Options state，但后续 Options operation 在 prerequisite 不可用时明确失败。
