# Observed historical ExpiryUniverse Artifact contract

本文件拥有 [cffex_option_expiry_universe](ARCHITECTURE.md) 的 retained Artifact semantic shape、provenance、complete publication 与 acceptance。Inputs / business identity、observed-window definition、derivation 与 validity 由 entry 唯一拥有；不规定 Python class、文件格式或 SQLite schema。

## Semantic shape 与 provenance

| Required area / fact | Meaning |
| --- | --- |
| observation identity | 固定 cffex_option_expiry_universe；与三个 normalized inputs 一起定位 Artifact。 |
| product_code | 请求的 canonical product。 |
| expiry_start_date / expiry_end_date | 请求的 inclusive expiry window；保留 date semantics。 |
| expiries | date 升序序列，unique，每项位于 expiry window 内；每个 date 为一个 empirical unit。 |
| upstream public provenance / coverage context | 实际 Options export 的 dataset、view、export_schema_version、scope、window 和完整 coverage semantic context（Python owned-value projection 见 [IMPLEMENTATION](IMPLEMENTATION.md)，不持有 DataLake CoverageResult object）。 |

Provenance 的 dataset 为 tushare_equity_index_options，view 为 options_daily，scope 仅含 requested product，trade-date window 与请求 expiry window 相同。保留实际 public schema version；不是 SQLite version。不保留 internal IDs、hash、SQLite path、provider transport、private completeness basis 或全量 daily rows；不新增执行审计机制。

Result 是 entry 所定义的 observed historical expiry universe，不是官方未来计划或所有历史 catalog expiries；不包含 target_dte、observation_date、chain rows、PnL 或 statistics。Coverage / rows proof 来自同一 Options committed snapshot，不能声称 provider-current freshness。

## Completeness 与 publication

只有 inputs 合法、entire upstream window 被证明 complete、scope / window 一致、distinct extraction 遵守 canonical derivation、results sorted / unique / in-range，以及 Artifact 与 provenance 一致保留时，才发布 complete。

Complete empty universe 合法，不是 failure；不完整上游的 empty / partial rows 不能证明 empty universe。Interrupted、failed、partial Artifact 不满足 business key，不可作为 complete consumer input，沿用 [framework completion visibility](../ARCHITECTURE.md#completeness-与-public-boundary)。

## Acceptance

| Scenario | Required outcome |
| --- | --- |
| 同一 expiry 在多个 product-days / contracts 出现 | 只保留一次，日期升序；不复制 market rows。 |
| rows 的 expiry 等于 start / end | inclusive 纳入；window 外 expiry 排除。 |
| 完整窗口无 matching expiry | complete empty Artifact。 |
| 完整 Calendar 证明无开市日，Options 零目标 complete | complete empty Artifact。 |
| Cache missing / incomplete / failed ensure / prerequisite 或 operation failure | 必要时 ensure；无法证明 entire-window completeness 时失败，不以部分 rows 发布 complete。 |
| 相同有效 definition 与 key 命中 complete Artifact | 直接复用，无 upstream access / computation，无第二个逻辑 Artifact。 |
| 无效 product / 错误日期类型 / 倒置 window | upstream 前失败，不猜测或修复请求。 |
| expiry 只在请求 trade-date window 外曾挂牌 | 不据此扩大 observed universe；本 Artifact 不声称证明该历史范围。 |
| Consumer / persistence | 只通过 Artifact boundary 消费；一个 Observation-owned SQLite，不由 Study output 管理。 |

本轮 acceptance 是 semantic contract，不表示 producer 或 executable tests 已实现。
