# cffex_option_expiry_universe Observation authority

本文件是 concrete Observation canonical entry，拥有 identity、purpose、inputs / canonicalization、business key、population / grain、upstream dependencies、deterministic derivation、validity / missingness、persistence 与 limitations。继承 [Observation framework](../ARCHITECTURE.md)、[Semantic Schema](../SCHEMA.md) 与 [Research boundaries](../../ARCHITECTURE.md)。Retained shape、provenance、complete publication 与 acceptance 唯一归 [ARTIFACT.md](ARTIFACT.md)。

## Identity 与 empirical purpose

Canonical identity 为 `cffex_option_expiry_universe`。给定一个 CFFEX 股指期权产品和 inclusive expiry window，返回该窗口内完整 historical option daily market facts 中实际观察到、且 expiry 落在该窗口内的 distinct dates。

这是 independent reusable retained empirical fact producer，不属于任何 Study，也不是官方未来合约上市计划。它不决定 Study 是否需要 discovery、应选择哪个 window 或如何驱动 downstream invocations；这些是 Study workflow decisions。

## Inputs 与 business identity

| Required input | Canonical contract |
| --- | --- |
| product_code | 一个 str，引用 [Options public request](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md) 的 canonical uppercase ASCII product domain；当前 IO / HO / MO，由 upstream market table 拥有范围。不 trim、不改大小写、不猜名称。 |
| expiry_start_date | `datetime.date`，inclusive；拒绝 datetime timestamp、字符串或缺失值。 |
| expiry_end_date | `datetime.date`，inclusive；拒绝 datetime timestamp、字符串或缺失值，要求 expiry_start_date <= expiry_end_date。 |

三个 inputs 均必填、无默认值；合法 canonical values 按原值构成 normalized business inputs，倒置范围不交换修复。无效请求在 upstream 操作前失败；没有 today default、hidden historical bound 或 execution-time 截断。

```text
business_key = (product_code, expiry_start_date, expiry_end_date)
Artifact semantic identity
    = cffex_option_expiry_universe + normalized business inputs
```

任一业务输入变化均区分请求；Study identity、timestamp、UUID、path、source hash、code hash 或 authority version 不进入 key。继承 [framework invocation reuse](../ARCHITECTURE.md#business-identity-与-invocation-lifecycle)：同一有效 definition 下 complete Artifact 命中直接返回，零 upstream access / computation，无第二个逻辑 Artifact。失败、中断、partial state 不满足 key；refresh / evolution 沿 [deferred rules](../ARCHITECTURE.md#explicitly-deferred-decisions)。

## Population、grain 与 deterministic derivation

Human 已锁定 historical trade-date window 与 expiry window 相同：

```text
trade_date window = [expiry_start_date, expiry_end_date]  # inclusive
matching_rows = {row in complete Options public export |
                 expiry_start_date <= row.expiry <= expiry_end_date}
expiries = sorted(unique(row.expiry for row in matching_rows))
```

Export 仅选择 requested product，覆盖该 inclusive trade-date window 的全部 CFFEX 开市 product-days。Population 为上述 matching public facts 所证明的 distinct expiry dates，grain 为 `one expiry date`。多个日期或 contracts 重复证明同一 expiry，只产生一个升序结果；不按 strikes、CALL/PUT、成交量或研究问题缩小观察范围。

本定义不声称发现只在 trade-date window 之外曾挂牌的 expiry，不从完整 local / provider catalog 推导另一个 universe。输出完整性是相对于这个 observed-window 定义，不等于所有历史合约 metadata 的全集。

## Upstream public dependency 与 validity

唯一直接 upstream dependency 是 [tushare_equity_index_options public Application Service](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md)。请求 OptionsDailyRange，product_codes 仅含 requested product，start_date / end_date 等于上述 window。

没有 reusable complete Artifact 时，通过 public ensure 补齐窗口，再 export；要求合法 view 的 scope / window 对应请求、coverage.complete=true，coverage 与 records 来自同一 committed Options snapshot。不能用先前 coverage 与另一读取的 rows 拼接 proof。已有 complete coverage 时无需重复 Source fetch；具体 read-only 检查顺序留给设计。

Options 自己通过 [Calendar prerequisite](../../../data-lake/datasets/tushare_equity_index_options/TRADING_DAYS.md) 确定全部 CFFEX 开市日；本 Observation 不重算日历、不直接依赖 Calendar internals。强 product-day completeness 与合法空集合由 [Options contract universe](../../../data-lake/datasets/tushare_equity_index_options/CONTRACT_UNIVERSE.md) 拥有，字段与 nullable semantics 由 [FACTS.md](../../../data-lake/datasets/tushare_equity_index_options/FACTS.md) 拥有。

Incomplete coverage、ensure failure、Calendar prerequisite failure、credential / provider / persistence / integrity failure 或非法 view 使 invocation 失败。Cache missing 不等于 empty universe，不从已成功子集提取 partial expiries 并发布 complete。完整窗口没有 matching rows 时，empty expiry universe 是合法 complete result；完整 Calendar 证明零开市日、Options 零目标 complete 的情况同样适用。

遵守 [Observation upstream policy](../UPSTREAM.md)：已审查的 Options public contract 以 entire-window completeness、同一 snapshot 的合法 expiry rows，完整、确定、可验证地证明本 observed historical universe，不需重新实现 Snapshot-owned prepared Product semantics，因此 DataLake 是 design-time 选定的 canonical upstream。运行失败按上述 validity 使 invocation 失败，不切换来源。未发现 DataLake capability gap；不新增 API，不宣称 Observation runtime 已存在。

## Persistence、limitations 与 semantic ownership

本 Observation exactly owns 一个 SQLite，承载其多个 requests / Artifacts，继承 [framework persistence boundary](../ARCHITECTURE.md#persistence-ownership)。Consumer 不读取数据库，runtime SQLite 不进入 Git；canonical placement / public package / publication mapping 见 [IMPLEMENTATION.md](IMPLEMENTATION.md)；SQL schema、indexes 与 transaction / locking mechanics 留给实现，semantic evolution 继续 deferred。

Artifact 不保证 provider-current freshness，不解释窗口外 facts，不进行 DTE calculation、chain construction、Study selection、cross-expiry comparison、PnL、收益、statistics、Analysis 或 Evidence。未来未发布行情的窗口不能由日历或计划推测为 complete；上游不能证明完整性时失败。

Schema 十三个 areas 的 owner：Identity / Purpose / Inputs / Business Key / Population / Grain / Upstream Facts / Derivation / Validity / Missingness / Persistence / Limitations 在本 entry；Artifact Contract / Acceptance 在 [Artifact authority](ARTIFACT.md)。Framework deferred semantics 不因该 Observation 新增而锁定。
