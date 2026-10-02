# cffex_option_expiry_dte_chain Observation authority

本文件是 concrete Observation 的 canonical entry，拥有 identity、purpose、inputs / canonicalization、business key、population / grain、upstream dependencies、persistence ownership、limitations 与导航。继承 [Observation framework](../ARCHITECTURE.md)、[Research boundaries](../../ARCHITECTURE.md) 与 [Semantic Schema](../SCHEMA.md)。日期解析进入 [DATE_RESOLUTION.md](DATE_RESOLUTION.md)，retained Artifact、provenance、complete publication 与 acceptance 进入 [ARTIFACT.md](ARTIFACT.md)。

## Identity 与 purpose

Canonical Observation identity 为 `cffex_option_expiry_dte_chain`。给定一个 CFFEX 股指期权产品、一个 expiry date 和一个 target DTE，确定实际 observation trade date，并返回该 expiry 在该日的完整期权链 empirical market facts。

它是 independent reusable retained empirical fact producer，不属于任何 Study；职责终点是一个 complete retained Observation Artifact。Study 可提供业务输入并复用 Artifact，不拥有日期解析、population 或完整性规则。

## Inputs 与 canonicalization

业务输入仅有以下三项，均必填、无默认值：

| Input | Canonical semantic value / constraint |
| --- | --- |
| product_code | 一个 str，遵守 [Options public request](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md) 的 canonical uppercase ASCII product contract；当前支持 IO / HO / MO，产品范围由 [upstream market table](../../../data-lake/datasets/tushare_equity_index_options/FACTS.md) 拥有。 |
| expiry_date | 一个 `datetime.date`，拒绝 datetime timestamp、字符串或缺失值；请求 Source expiry，不从 settlement month 推算。 |
| target_dte | 一个正整数，拒绝 bool、float、字符串或缺失值；自然日 DTE，expiry 当天为 1。 |

Product code 不 trim、不改大小写、不猜名称。已合法 canonical inputs 按原值构成 normalized business inputs；输入层不新增 today default、历史日期限制或 expiry-discovery validation。无效输入在 upstream 操作前失败。有效日期仍须能完成 [日期计算与解析](DATE_RESOLUTION.md)，计算不可表示时失败。

## Business key 与 invocation

```text
business_key = (product_code, expiry_date, target_dte)
Artifact semantic identity
    = cffex_option_expiry_dte_chain + normalized business inputs
```

三个输入任一变化均为不同业务请求；observation_date、actual_dte 是 deterministic derived facts，不进入 key。Source digest、code hash、timestamp、authority version、execution UUID 与 provenance 不进入 business key。

沿用 [framework invocation lifecycle](../ARCHITECTURE.md#business-identity-与-invocation-lifecycle)：同一有效 definition 下，complete Artifact 已存在则直接返回，不重复 upstream access、不重复计算、不产生第二个逻辑 Artifact。没有 complete Artifact 才执行解析、构造与保留。Failed / interrupted / partial execution 不满足 key。Refresh、invalidation、definition evolution 继续遵守 [deferred decisions](../ARCHITECTURE.md#explicitly-deferred-decisions)。

## Population 与 grain

在 resolved observation_date，population 恰为指定 product 的完整 DataLake option product-day 中全部 `row.expiry == expiry_date` 的合法 public rows。包含实际挂牌的全部 strikes、CALL 与 PUT，不做 strike、moneyness、CALL/PUT 或 arbitrary contract subset filters，不补造 catalog 中不存在的合约或对腿。

Empirical row grain 为 `one option contract × one resolved observation_date`。同一 Artifact 每个 contract 恰有一条 row，所有 rows 的 product_code、expiry、trade_date 与请求及解析结果一致。具体 persistence unique key 不在本轮决定。Study / Analysis 可在消费之后选择 sample，不改变这个 Observation 的 invocation population。

## Upstream dependencies 与 public boundary

| Required Dataset | Public capability / canonical owner |
| --- | --- |
| tushare_trade_calendar | [Calendar service](../../../data-lake/datasets/tushare_trade_calendar/SERVICE.md)：显式 CFFEX，coverage / ensure / export 获得完整日历与开市事实。 |
| tushare_equity_index_options | [Options service](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md)：coverage / ensure / export 获得完整单 product-day 及 OptionsDailyRow。强 completeness 由 [contract universe](../../../data-lake/datasets/tushare_equity_index_options/CONTRACT_UNIVERSE.md) 拥有，Calendar prerequisite 由 [trading days](../../../data-lake/datasets/tushare_equity_index_options/TRADING_DAYS.md) 拥有。 |

只消费这两个 Dataset 的 public Application Service / semantic objects，遵守 [DataLake Application contract](../../../data-lake/APPLICATION.md)。不读取 SQLite、Repository、Source Adapter、Tushare transport、private persistence、CLI 或 JSON export；不增加 DataLake private dependency，也不依赖 Snapshot。当前 public contracts 足以支持本 Observation，未发现 capability gap；不据此宣称 Research runtime integration 已实现。

## Persistence ownership

本 concrete Observation exactly owns 一个 SQLite，承载本 Observation 的多个 business requests / Artifacts，不是每次 invocation 一库。继承 [framework persistence boundary](../ARCHITECTURE.md#persistence-ownership)：Study、Analysis 与 external consumer 只消费 complete Artifact，不访问 SQLite；没有 global Artifact DB、cross-Observation FK 或 Study-owned Observation persistence。Runtime SQLite 不进入 Git。Schema、path、unique key、事务、locking、retry 与内部 state machine 留给后续 design，本轮不创建数据库。

## Limitations 与职责边界

Artifact 表达所保留的 empirical facts，不承诺 provider-current freshness、trade_date 当时的历史 metadata，或 upstream 修订后的自动重算。合法 Source 缺席按 upstream contract 保留；不能从 Artifact 推出未观察日期、未包含产品或其他 expiry 的事实。

本 Observation 不拥有 Study date-window → expiry discovery、Study 应调用哪些 expiry、cross-expiry composition / comparison、payoff、PnL、realized return、option risk premium、win rate、mean / median / quantiles、distribution、statistical tests、Analysis、Evidence 或 Study conclusions。“2026-01-01 ~ today 应观察哪些 expiry”属于 Study workflow。

## Semantic ownership 与交接

| Schema area | Canonical owner |
| --- | --- |
| Identity / Purpose / Inputs / Business Key / Canonicalization | 本 entry 的对应 sections |
| Population / Grain / Upstream Facts / Persistence / Limitations | 本 entry 的对应 sections；upstream fields 继续由所链接的 DataLake authority 拥有 |
| Derivation / Validity / Missingness | [Date resolution](DATE_RESOLUTION.md) |
| Artifact Contract / Acceptance | [Artifact contract](ARTIFACT.md) |

Concrete semantics 已锁定；implementation 状态与验证记录见 [Research reconciliation](../../IMPLEMENTATION_RECONCILIATION.md#首个-concrete-observation-authority-落位)。本 entry 不启动 implementation，不预设 public invocation Python topology、CLI 或 HTTP delivery。
