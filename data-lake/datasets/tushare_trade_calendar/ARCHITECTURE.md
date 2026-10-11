# tushare_trade_calendar Dataset architecture authority

本文件是自治 Dataset 的 bounded-context 入口，拥有本 Dataset 的 semantic / source / test / persistent-state ownership，以及 identity、Source、Scope、Window、FetchUnit / Record identity、facts、completeness、Instrument 与 success specialization。继承 [DataLake architecture](../../ARCHITECTURE.md) 与公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)；catalog 见 [DATASETS.md](../../DATASETS.md)。Public consumer contract 从本文件进入 [SERVICE.md](SERVICE.md)，domain 任务无需加载 service 或 CLI details。

## 1. Identity、Source 与 Scope

Canonical Dataset identity 为 `tushare_trade_calendar`，用于持久缓存 Tushare 交易日历 Source facts，不生成 analysis-ready 派生结果。SQLite ownership 继承模块 invariant。

本 bounded context 位于 `datasets/tushare_trade_calendar/`，authority 为本文件与 [SERVICE.md](SERVICE.md)；`src/`、`tests/` 与 `data/` 的 ownership、colocation 和 Python boundary 继承 [模块架构](../../ARCHITECTURE.md)。SQLite lifecycle 见 [PERSISTENCE.md](../../PERSISTENCE.md)。

Trade-calendar-specific models、Scope / Window interpretation、逐日 completeness、export view、Tushare adapter 与 service composition 都归本 Dataset；依赖方向与 public import compatibility 继承模块架构。Calendar 不依赖其他 Dataset。

Source provider 为 **Tushare**，execution 继承 [providers/tushare/ARCHITECTURE.md](../../providers/tushare/ARCHITECTURE.md)。本 Dataset Source Adapter 拥有 `trade_cal` endpoint / parameters、batching 与 response partition；Calendar facts validation 规则由本文件的 Dataset Domain 拥有。

Source endpoint 为 **`trade_cal`**。第一版只有一个 canonical Scope shape：

```text
TradeCalendarScope
    exchange: str
```

`exchange` 是 provider-native canonical exchange identifier，必须显式指定，不依赖 provider default。DataLake 不建立 exchange master / enum taxonomy，也不将 exchange 伪装成 Instrument。

`exchange × cal_date` 已完整寻址全部 fact space；Scope shape 的判定继承公共 domain authority，因此第一版不引入其他 Scope。

## 2. Window 与 FetchUnit identity

Window 是 transient 日期范围 `start_date..end_date`，两端 inclusive。在指定 Scope 下展开为每个自然日的 FetchUnit，包括交易日与休市日：

```text
(exchange, start_date)
...
(exchange, end_date)
```

FetchUnit identity 为 `(exchange, cal_date)`；unit key 的稳定性、唯一性与 serialization 边界继承公共 domain authority。`FetchUnit != Source Request`：整个 range 不是一个 FetchUnit；provider batching 只是 internal transport / execution concern，不改变逐日 ownership 或 completeness。

## 3. Record facts 与 completeness

Record identity 为 `(exchange, cal_date)`。Records 继承公共 persistence ownership，canonical facts 为：

| Fact | 合法 domain value |
| --- | --- |
| exchange | provider-native canonical identifier，与 owning unit 相同 |
| cal_date | 合法日期，与 owning unit 相同 |
| is_open | 整数 0 或 1，保留 Source 休市 / 开市事实 |
| pretrade_date | 合法日期或 Source 合法缺席 |

Normalization 必须确定且保持 Source 语义。不得将无效日期或缺失 required fact 作为合法缺席；不能只保存交易日，不能将缺失事实转换成休市状态，不能补造 Record。Public Python types 与 wire meaning 由 [SERVICE.md](SERVICE.md) 拥有，具体 SQLite 类型留给 implementation。

```text
1 successful FetchUnit (exchange, cal_date)
    → exactly owns 1 canonical TradeCalendarRecord
```

只有满足这一 completeness 并原子提交 Record 与成功 metadata 的 unit 才能 `success`。目标日期缺失、duplicate / conflicting identity、exchange / cal_date 与目标 unit 不匹配、required Source fact 无法合法 normalize 或 completeness 不满足时均不得成功。即使 duplicate rows 内容相同，也不能静默去重后宣告成功。

失败仍使用公共 `failed` 状态，不新增 `incomplete` persistence state；不能因同批其他日期成功而标记失败 unit 成功。

## 4. Instrument usage

```text
instrument usage: none
```

不要求 instrument entries 或 `records.instrument_id` 引用；不得将 exchange 或 synthetic calendar object 伪装成 Instrument。

## 5. Success 与 freshness

`success` 的历史取得含义继承 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)，本 Dataset 将 completeness 收紧为上述 exactly-one Record invariant。

`coverage.complete` 继承 [APPLICATION.md](../../APPLICATION.md) 的 cache completeness 定义。未来日期 facts 同样适用；freshness policy 继承模块 deferred semantics。

## 6. Dataset Composition 与职责组织

本 Dataset 按公共 [COMPOSITION.md](../../COMPOSITION.md) 接入 Kernel；六角色绑定如下，表中链接是具体规则的 canonical owner：

| Role | 本 Dataset 绑定 |
| --- | --- |
| Target Planner | 本文件第 1–2 节：显式 exchange + inclusive Window 展开全部自然日 `(exchange, cal_date)`；无跨 Dataset prerequisite |
| Source Port / Adapter | Calendar `trade_cal` Adapter；本文件第 1 节拥有 endpoint / 参数选择，Provider 仅按 [Tushare authority](../../providers/tushare/ARCHITECTURE.md) 执行 |
| Normalizer | Calendar Domain；本文件第 3 节的四个 canonical facts，不补造休市事实 |
| Completeness Validator | Calendar Domain；本文件第 3–4 节的 exactly-one Record / identity / required facts / no-instrument predicate |
| Export Projector | Calendar Domain 的业务 view projection；[SERVICE.md](SERVICE.md) 唯一拥有 `calendar` view、字段、ordering 与 wire meaning |
| Repository Port / Adapter | 使用 Kernel 标准 SQLite Adapter，Calendar Composition Root 绑定本 Dataset identity/source/storage context；[PERSISTENCE.md](../../PERSISTENCE.md) 拥有存储机制 |

Calendar Composition Root 发布 TradeCalendarService / create_service()，只绑定上述能力并委托 Kernel 的 coverage/ensure/export；不自行拥有第二套通用同步 engine。Batch Planner 是 Calendar-owned 可选执行策略；现有 trade_cal 按自然年分组、显式 exchange 与日期范围获取，只处理 selected units。共享调度/逐 unit pending 与提交仍由 [EXECUTION.md](../../EXECUTION.md) 拥有。

目标职责为 Dataset Domain（request interpretation / normalization / validation / projection）、Source Adapter（trade_cal 请求和 partition）、Composition Root / Public Service（实例绑定与 delegation）。文件名可按职责调整，不要求机械目录模板；Domain 不调用 Provider 或 SQLite，Source Adapter 不访问 Repository。Python namespace 与 public request/result/view 保持 SERVICE.md 契约。

## 7. 下一份 authority

Consumer contract、public Python surface、operation specialization、failures 与 runtime configuration 见 [SERVICE.md](SERVICE.md)；CLI adapter 再进入 [lab authority](../../../lab/ARCHITECTURE.md)。
