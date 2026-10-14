# Index Daily 交易日 prerequisite authority

本文件拥有 Index Calendar Prerequisite Resolver 的具体 request、目标交易日 context、调用权限与 prerequisite failures，继承 [Dataset architecture](ARCHITECTURE.md)、公共 [COMPOSITION.md](../../COMPOSITION.md) 的 Resolver / FetchUnitPlanner 角色和 [APPLICATION.md](../../APPLICATION.md) 的执行顺序。Producer 契约是 [Calendar SERVICE.md](../tushare_trade_calendar/SERVICE.md)，不在本文件重定义 Calendar facts。

## 1. Direction 与日历选择

```text
IndexDailyService
    → tushare_trade_calendar public Application Service
        → Calendar-owned Source / SQLite
```

V1 对本 Dataset 支持的沪深指数使用显式 `exchange="SSE"` 的 TradeCalendarRange，Window 与 Index request 完全相同。这里的 SSE 是本 Dataset 的共同沪深交易日基准，不是 index 的 exchange / publisher 属性，也不从 `.CSI` 后缀推断交易所。Tushare [trade_cal 文档](https://tushare.pro/document/2?doc_id=26) 说明沪深交易日历相同；此项 selection 是本 Dataset 明确的 specialization，不是全仓 calendar default。

Resolver 只消费 Calendar `export(request)` 的 transport-neutral TradeCalendarExport（view=`calendar`），按第 4 节验证完整合法 view。过滤其中 `is_open == 1` 的日期为 D；休市日不生成 Index unit。不得用 weekday、节假日 heuristic、Index 返回行或 `pretrade_date` 反推完整 D。

```text
desired_units = {(code, d) | code in canonical index_codes, d in D}
requested_units = len(canonical index_codes) * len(D)
```

完整 calendar 中 D 为空时，零 requested units、complete=true、ensure 零 attempts / records_written、export 空 records 均合法。Calendar 不完整时无法判断 D，不能返回上述零目标结果。

## 2. Operations 与失败

| Index operation / Resolver permission | Calendar 调用 / prerequisite 行为 |
| --- | --- |
| coverage / Read-only | 只调用 Calendar export；不完整或无法读取则 OperationError |
| export / Read-only | 同 coverage，固定合法 Calendar view 后生成 Index committed snapshot view |
| ensure / Authorized prerequisite ensure | 先 Calendar export；若 incomplete，调用 Calendar ensure 补齐相同范围，再 export 取得完整 view；否则不调用 Calendar ensure |

Index ensure 必须在完成 prerequisite validation 后才展开/执行自己的 units，不因未知目标建立 pending rows 或请求 index_daily/index_basic。Calendar ensure 返回 complete=false、随后 export 仍 incomplete、credential 缺失、operation failure 或非法 semantic view 时，Index 抛有 Calendar context 的 OperationError。此时没有正常 Index EnsureResult，Calendar 已提交的成功 facts 保留；不跨库 rollback，也不将 Calendar 日期塞进 Index UnitFailure identities。

Index request 自身无效时先抛 InvalidRequestError，不调用 Calendar。合法 request 被 producer 拒绝属于内部 composition failure，映射为 OperationError。Read-only Calendar cache 缺失属于 prerequisite unavailable；绝不能以已有日期子集统计 Index completeness，不能把缺失当休市或绕过 producer 另调 trade_cal。

Calendar 完整以后，Index 自己的 missing/pending/failed 是正常 coverage incompleteness，自己的可恢复 Source/unit failures 按 SERVICE.md 返回。Index 已有 success 默认跳过；如果 prerequisite 完整且目标全部 success，整个 ensure 不需要 token。Calendar 不完整时即使 Index 存有行情，也无法证明完整目标集合，ensure 仍可能需要 Calendar Source I/O。

## 3. Snapshot 与独立 state

每次 Index operation 固定一个 Calendar export semantic snapshot，不在逐 unit execution 中重新展开 D。Index export 的 coverage 与 records 来自同一个 Index committed cache snapshot，并使用同一份 D；不要求两库同一时刻 snapshot，不保证 Source freshness。

Calendar 保持完整自然日事实及自有 SQLite；Index 不复制 Calendar FetchUnits、引用其 unit_id、读其 SQLite / Repository / internal adapter，也不反向更改 Calendar authority。Calendar cache 被删除不会连带删除 Index owned state；后续 Index operation 若 prerequisite 不可用，仍按本契约明确失败。

## 4. Resolver 验证与 Planning Context

本 Dataset Composition 绑定一个 Calendar Resolver；输入为已验证 IndexDailyRange + 第 2 节 operation permission。Resolver 校验 Calendar envelope 的 dataset、view、export_schema_version 与 producer SERVICE.md 一致，scope.exchange 为 SSE，window 与请求两端完全匹配；不能仅凭 complete flag 接受另一范围或另一 view。

初次 export 即使 incomplete，也须先符合 producer 的合法 partial-view contract：计数类型、互斥总和与 complete 公式一致，已有 rows 只属于请求范围内的 success 自然日、唯一且合法，数量与 successful_units 一致。合法 missing cache 的空 view 可触发已授权 ensure；错误 envelope、计数或非法 cached facts 直接 OperationError，不先请求补齐。

Coverage 必须是合法互斥计数、complete=true，requested_units / successful_units 都等于 Window 的自然日数，missing/pending/failed 都为零。Records 按 producer ordering 精确覆盖每个自然日且恰一条，exchange 与日期匹配、is_open 为合法整数 0/1、pretrade_date 为合法 date 或 None；所有 semantic types 与事实符合 producer contract。非法 view 抛有 Calendar context 的 OperationError，不通过 ensure 修复格式/身份错误；第 2 节的 prerequisite ensure 仅用于合法但 incomplete 的同范围 view。

输出是本次匹配 request 的 Validated Planning Context：携带匹配的 exchange / Window 与从完整合法 Calendar view 得到、按 cal_date 排序固定的开市日 D；可以保留该 view，也可以只保留已验证的必要事实，不要求复制全部 Calendar rows。FetchUnitPlanner 只消费此 context 与 canonical index_codes 生成上文完整目标，不调用 Calendar、不读 Index cache、不决定 Source batches。Resolver 与 Planner 不处理 index_basic membership/metadata 或 daily completeness；这些继续由 FACTS.md 和 Dataset Validator 拥有。

Context 在本次 operation 内固定，不逐 unit 或 batch 重取，不跨 operation 信任旧 view；Composition 负责其生命周期与 permission。Calendar producer service 可复用，Resolver 逻辑也可复用，但 SSE selection、同范围验证与调用权限仍归 Index，不因 Futures/Options 使用 CFFEX 而扩展。
