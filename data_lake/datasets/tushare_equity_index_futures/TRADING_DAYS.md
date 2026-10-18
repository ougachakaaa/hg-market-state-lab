# Futures Daily 交易日 prerequisite authority

本文件拥有 Futures Calendar Prerequisite Resolver 的具体 request、目标交易日 context、调用权限与失败，继承 [Dataset architecture](ARCHITECTURE.md)、公共 [COMPOSITION.md](../../COMPOSITION.md) 的 Resolver / FetchUnitPlanner 角色和 [APPLICATION.md](../../APPLICATION.md) 的执行顺序。Producer 是 [Calendar SERVICE.md](../tushare_trade_calendar/SERVICE.md)，不在本文件重定义其 facts。

## 1. CFFEX 目标展开

FuturesDailyService 只通过 `data_lake.datasets.tushare_trade_calendar` public service，使用显式 `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`。Window 与 Futures request 完全相同，不按所选产品改变 exchange，不绕过 Calendar 另调 trade_cal。

Resolver 固定一份 Calendar export（view=calendar），按第 4 节验证完整合法 view。其 is_open==1 的日期为 D：

```text
desired_units = {(p, d) | p in canonical product_codes, d in D}
requested_units = len(canonical product_codes) * len(D)
```

不以 weekday、日行情返回、catalog lifecycle 或 pretrade_date 猜 D。完整 Calendar 的 D 为空时，零目标 complete=true、ensure 零 attempts/records_written、export 空 records 合法；它不同于开市日 expected contracts 已证明为空的零 Records success。

## 2. 调用权限与失败

| Futures operation / Resolver permission | Calendar prerequisite |
| --- | --- |
| coverage / export / Read-only | 只调用 Calendar export；不完整、无法读取或非法 view 时 OperationError |
| ensure / Authorized prerequisite ensure | 先 export；仅 incomplete 时 ensure 同一范围，再 export；必须取得合法完整 view |

自身 request 先验证，无效时 InvalidRequestError，不调用 producer。Calendar 不完整时不能展开 Futures 子集、把未知当休市或建立自己的 pending units。Calendar ensure 未补齐、credential 缺失、读写/execution failure、非法 view 或内部合法 request 被 producer 拒绝时，抛带 Calendar context 的 OperationError；无正常 Futures EnsureResult，不尝试 Futures metadata/daily，也不改变自己的 units。

Calendar 先前已提交事实保留，不跨库 rollback。Calendar dates 不进入 Futures UnitFailure；Calendar rows/requests/writes 不计入任何 Futures counters。Calendar 完整后，Futures 自身的 missing/pending/failed 及可恢复 unit failures 才属于正常结果。

完整 Calendar 且所有 Futures 目标已 success 时，ensure 无 Source I/O、不要求 token；Calendar 不完整时即使 Futures 存有行情仍须补齐 prerequisite。Read-only 链无 credential 要求、不创建任一数据库或 rows。

## 3. 独立 state 与一致性

每次 operation 固定 D，不逐 unit 重展开。Futures export 的 coverage、Records 与关联 metadata 来自同一个 Futures committed snapshot，针对这份固定 D；不声称两个 Dataset 共享数据库 snapshot 或 freshness。

Calendar 保留自己的自然日 facts/SQLite；Futures 不复制其 FetchUnits、不读其 Repository/SQLite/adapter，不引用其 persistence IDs。Calendar state 删除不删除 Futures state，但后续 prerequisite 不可用时按本契约失败。

## 4. Resolver 验证与 Planning Context

本 Dataset Composition 绑定一个 Calendar Resolver；输入为已验证 FuturesDailyRange + 第 2 节 operation permission。Resolver 校验 Calendar envelope 的 dataset、view、export_schema_version 与 producer SERVICE.md 一致，scope.exchange 为 CFFEX，window 与请求两端完全匹配；不能仅凭 complete flag 接受另一范围或另一 view。

初次 export 即使 incomplete，也须先符合 producer 的合法 partial-view contract：计数类型、互斥总和与 complete 公式一致，已有 rows 只属于请求范围内的 success 自然日、唯一且合法，数量与 successful_units 一致。合法 missing cache 的空 view 可触发已授权 ensure；错误 envelope、计数或非法 cached facts 直接 OperationError，不先请求补齐。

Coverage 必须是合法互斥计数、complete=true，requested_units / successful_units 都等于 Window 的自然日数，missing/pending/failed 都为零。Records 按 producer ordering 精确覆盖每个自然日且恰一条，exchange 与日期匹配、is_open 为合法整数 0/1、pretrade_date 为合法 date 或 None；所有 semantic types 与事实符合 producer contract。非法 view 抛有 Calendar context 的 OperationError，不通过 ensure 修复格式/身份错误；第 2 节的 prerequisite ensure 仅用于合法但 incomplete 的同范围 view。

输出为本次匹配 request 的 Validated Planning Context：匹配的 exchange / Window 与从完整合法 Calendar view 得到、按 cal_date 排序固定的 D；可以保留该 view，也可以只保留已验证的必要事实，不要求复制全部 Calendar rows。FetchUnitPlanner 消费此 context 与 canonical product_codes 生成 products × D，不调用 Calendar、不读 Futures cache、不决定 batches。Fut_basic ordinary catalog、type-2 exclusion evidence 与 lifecycle expected set 是 selected units 的 Source/Validator completeness basis，继续归 CONTRACT_UNIVERSE.md，不进入本 Resolver、不裁剪 FetchUnits。

Context 在本次 operation 内固定，不逐 unit/batch 重取，不跨 operation 信任旧 view；Composition 负责生命周期与 permission。可以复用 Calendar producer service 或 Resolver 逻辑，但必须保留 Futures 的 request、CFFEX selection 和权限，不新增对 Index/Options 的依赖。
