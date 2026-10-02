# Observed historical expiry universe resolver contract

本文件唯一拥有 [component entry](ARCHITECTURE.md) 的 stable I/O、observed-window derivation、DataLake invocation / completeness、failure 与 acceptance。继承 [component boundary](../ARCHITECTURE.md) 与 [public upstream policy](../../UPSTREAM.md)；不继承 Observation retained-artifact lifecycle。不定义 Python package layout、class / operation 名称、serialization 或 SQLite schema。

## Inputs

| Required input | Canonical contract |
| --- | --- |
| product_code | str，引用 [Options public request](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md) 的 canonical uppercase ASCII product domain；当前 IO / HO / MO。不 trim、不改大小写、不猜名称。 |
| expiry_start_date | datetime.date，inclusive；拒绝 datetime timestamp、字符串或缺失值。 |
| expiry_end_date | datetime.date，inclusive；拒绝 datetime timestamp、字符串或缺失值；start <= end。 |

全部必填、无默认值；合法 values 原值使用，倒置范围不修复。无 today default、hidden historical bound 或 execution-time 截断。遵守 Dataset 对未来行情 window 的公开拒绝规则。无效请求在 upstream 操作前失败。Input tuple 用于绑定 / 校验对应请求，不是 persistence business key 或 artifact identity。

## Observed-window derivation

保留基线已确认的业务选择，不因分类改变另造 universe：

```text
trade_date window = [expiry_start_date, expiry_end_date]  # inclusive
matching_rows = {row in complete Options public export |
                 expiry_start_date <= row.expiry <= expiry_end_date}
expiries = sorted(unique(row.expiry for row in matching_rows))
```

Export 仅选择 requested product，覆盖 inclusive trade-date window 全部 CFFEX 开市 product-days。输出每项为一个 expiry date，升序、unique、in-range；不按 strikes、CALL/PUT、成交量或研究问题再筛选。不从完整 catalog 推导另一 universe，不声称覆盖只在 trade-date window 之外曾挂牌的 expiry，亦非官方未来计划。

## Public dependency 与 execution

唯一直接 upstream 为 [Options public Application Service](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md)，请求 `OptionsDailyRange(product_codes=(product_code,), start_date=expiry_start_date, end_date=expiry_end_date)`。Options 的 [Calendar prerequisite](../../../data-lake/datasets/tushare_equity_index_options/TRADING_DAYS.md)、[strong product-day completeness](../../../data-lake/datasets/tushare_equity_index_options/CONTRACT_UNIVERSE.md) 和 [field meaning](../../../data-lake/datasets/tushare_equity_index_options/FACTS.md) 继续归 DataLake；resolver 不直接重算 Calendar 或读取 internals。

已审查 public Options contract：同一 committed export 的 entire-window proof 与合法 expiry rows 足以确定本 observed-window selection，不复制 Snapshot prepared Product，因此 DataLake sufficient，无新 capability gap / API。DataLake-first 是 design-time selection，runtime failure 不换源。

每次调用验证 inputs 后直接使用如下 public sequence；不查任何 component research cache：

1. 调用 Options `ensure(exact range)`，校验 public result / counters / failures；必须 complete=true 且无 unit failures，否则失败。
2. 调用 `export(exact same range)`，验证 dataset=tushare_equity_index_options、view=options_daily、export_schema_version=2、scope 恰为 requested product、window 恰为请求、coverage.complete=true、计数一致与合法 public records。
3. 仅以这一 committed export 的 coverage + records 为 proof，按上述 derivation 产生完整 result，并投影必要 public context；全部合法后返回。

保持基线的 ensure-first selection，无需 preliminary coverage；Dataset ensure 自己跳过已成功 units，不重复 Source fetch。相同 resolver inputs 可再次调用 Dataset service，不保证零 upstream factory / operation / computation；DataLake cache reuse 与 Observation Artifact reuse 是不同边界。EnsureResult 的成功不能替代最终 export proof，不拼接另一次调用的 coverage 与 rows。

## Result、validity 与 failure

| Required result area | Meaning |
| --- | --- |
| product_code、expiry_start_date、expiry_end_date | 对应合法请求，用于核对 binding。 |
| expiries | 不可变有序 date sequence，sorted unique inclusive in-range。 |
| upstream public context | 实际 export 的 dataset / view / export_schema_version、scope / window 与完整 coverage context；Research-owned value projection，保留 public meaning，不向 Study 泄漏 DataLake service / Export / Row / CoverageResult objects。 |

Result 无 observation_identity / semantic artifact identity，不复制 daily rows，不携带 persistence path。其完整性是本次 public snapshot 下 observed-window selection 完整，不表示 durable publication、provider-current freshness 或跨 Dataset snapshot。

完整窗口无 matching rows，包括 Calendar 证明零开市日且 Options 零目标 complete，合法返回 empty result。Cache missing / incomplete、ensure unit failure、prerequisite / credential / provider / persistence / integrity failure 或非法 export 均不能解释为 empty / absent universe，不发布 partial result。

预期错误须区分 invalid caller inputs 与合法请求 operation / completeness failure，映射为 resolver-owned failure，不以 ObservationError inheritance 授予 Observation lifecycle。Concrete Python names / error carriers 留给后续实现；Study 消费其安全 readable context，不 import upstream exception classes。Ensure 未完成的诊断保留 Dataset identity、requested product / inclusive range、requested / attempted / succeeded / failed counts，以及 public failures 原顺序的每项 product_code / trade_date / readable reason；无明细则明确说明，不截断、不用 private IDs / arbitrary object repr 或 provider response。

## Acceptance 与实施交接

| Scenario | Required outcome |
| --- | --- |
| 重复 expiry、多 contracts / product-days、边界日期 | 去重升序，start / end inclusive，窗口外排除；不复制 market rows。 |
| 完整无 matching rows / 零目标 | complete empty result，不要求任何 research publication。 |
| ensure complete 后 export incomplete / invalid | 失败；不以 earlier proof 拼接 / 发布 partial。 |
| invalid product / dates / 倒置范围 | upstream 前失败，无修复或 defaults。 |
| repeated equal inputs / service recreation | 仍通过 Dataset public contract resolve；无 component SQLite / business-key lookup / durable hit 要求。 |
| consumer / dependency boundary | Study / Observation 可显式调用；Analysis 无事实读取；无 provider / upstream private access / CLI JSON；result 为 owned public values。 |
| implementation / state | 撤销 Universe Observation public lifecycle 和新 research persistence，保留 chain Observation；现有 state 不在本轮迁移、删除或重算。 |

Contract complete，已选 DataLake capability sufficient；resolver runtime mapping / wiring / tests 仍需下一轮 reconciliation，不能引用旧 durable-reuse tests 宣称本 component 已实现。具体范围见 [reconciliation](../../IMPLEMENTATION_RECONCILIATION.md#shared-component-semantic-reconciliation)。
