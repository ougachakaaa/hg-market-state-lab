# Options Daily 交易日 prerequisite authority

本文件拥有 Options Calendar Prerequisite Resolver 的具体 request、目标交易日 context、调用权限与失败，继承 [Dataset architecture](ARCHITECTURE.md)、公共 [COMPOSITION.md](../../COMPOSITION.md) 的 Resolver / FetchUnitPlanner 角色和 [APPLICATION.md](../../APPLICATION.md) 的执行顺序。Producer 是 [Calendar SERVICE.md](../tushare_trade_calendar/SERVICE.md)，其 facts 不在本文件重定义。

## 1. CFFEX product-day 目标

OptionsDailyService 只通过 `data_lake.datasets.tushare_trade_calendar` public service 使用显式 `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`，与 Options request 相同 inclusive Window；不按 expiry/strike/product 改变日历，不直接请求 trade_cal。

Resolver 固定 Calendar export（view=calendar），按第 4 节验证完整合法 view。过滤 is_open==1 得 D：

```text
desired_units = {(p, d) | p in canonical product_codes, d in D}
requested_units = len(canonical product_codes) * len(D)
```

不按 weekday、日行情、产品上市日、expiry 或 pretrade_date 推测 D，不因 catalog 缺口收缩目标。完整 Calendar 中 D 为空时，零目标 complete=true、ensure 零 attempts/records_written、export 空 records；不同于开市日已证明无 active contracts 的零 Records success。

## 2. Operations 与 failure

| Options operation / Resolver permission | Calendar prerequisite |
| --- | --- |
| coverage / export / Read-only | 仅 Calendar export；不完整、读取失败或非法 view 时 OperationError |
| ensure / Authorized prerequisite ensure | 先 export；仅 incomplete 时 ensure 同一范围，再 export 取得合法完整 view |

自身无效 request 在 dependency 调用前 InvalidRequestError。Prerequisite 未完整时不能建立自己的 pending units、访问 Options metadata/daily 或按已知日期子集返回正常结果。Calendar ensure 后仍不完整、credential/读写/execution failure、非法 semantic view 或合法内部 request 被 producer 拒绝，均映射为带 Calendar context 的 OperationError；无正常 Options EnsureResult，自身 units 不改变。

Calendar 已提交事实保留，无跨库 rollback。其日期不进入 Options UnitFailure，其 rows/requests/writes 不进入 Options counters。Calendar 完整后，自己的 missing/pending/failed 与可恢复产品日 failure 按 SERVICE.md 表达。

完整 Calendar 与全部 success Options 目标使 ensure 无需 Source/token；Calendar 不完整时不能靠已有 Options 行情绕过 prerequisite。Coverage/export 整条链真正 read-only，不创建库/rows、不隐式 ensure、不要求 credential。

## 3. Snapshot 与 storage lifecycle

每次 operation 固定 D；Options export 的 coverage、Records 和关联 Instrument facts 来自同一个 Options committed snapshot，并针对这份固定目标，不声称 Calendar/Options 跨库同一 snapshot 或 Source freshness。

Calendar 保留自己自然日 facts 与 SQLite；Options 不复制其 FetchUnits、不访问其 internals/persistence IDs。两库独立删除/重建；Calendar 缺失不删除 Options state，但后续 Options operation 在 prerequisite 不可用时明确失败。

## 4. Resolver 验证与 Planning Context

本 Dataset Composition 绑定一个 Calendar Resolver；输入为已验证 OptionsDailyRange + 第 2 节 operation permission。Resolver 校验 Calendar envelope 的 dataset、view、export_schema_version 与 producer SERVICE.md 一致，scope.exchange 为 CFFEX，window 与请求两端完全匹配；不能仅凭 complete flag 接受另一范围或另一 view。

初次 export 即使 incomplete，也须先符合 producer 的合法 partial-view contract：计数类型、互斥总和与 complete 公式一致，已有 rows 只属于请求范围内的 success 自然日、唯一且合法，数量与 successful_units 一致。合法 missing cache 的空 view 可触发已授权 ensure；错误 envelope、计数或非法 cached facts 直接 OperationError，不先请求补齐。

Coverage 必须是合法互斥计数、complete=true，requested_units / successful_units 都等于 Window 的自然日数，missing/pending/failed 都为零。Records 按 producer ordering 精确覆盖每个自然日且恰一条，exchange 与日期匹配、is_open 为合法整数 0/1、pretrade_date 为合法 date 或 None；所有 semantic types 与事实符合 producer contract。非法 view 抛有 Calendar context 的 OperationError，不通过 ensure 修复格式/身份错误；第 2 节的 prerequisite ensure 仅用于合法但 incomplete 的同范围 view。

输出为本次匹配 request 的 Validated Planning Context：匹配的 exchange / Window 与从完整合法 Calendar view 得到、按 cal_date 排序固定的 D；可以保留该 view，也可以只保留已验证的必要事实，不要求复制全部 Calendar rows。FetchUnitPlanner 消费此 context 与 canonical product_codes 生成 products × D，不调用 Calendar、不读 Options cache、不决定 batches。Opt_basic catalog、lifecycle 和全部 active expiry/strike/CALL-PUT expected set 是 selected units 的 Source/Validator completeness basis，继续归 CONTRACT_UNIVERSE.md，不进入本 Resolver、不裁剪 FetchUnits。

Context 在本次 operation 内固定，不逐 unit/batch 重取，不跨 operation 信任旧 view；Composition 负责生命周期与 permission。可以复用 Calendar producer service 或 Resolver 逻辑，但必须保留 Options 的 request、CFFEX selection 和权限，不新增对 Index/Futures 的依赖。
