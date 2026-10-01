# equity_index_options Dataset architecture authority

本文件拥有股指期权自治 bounded-context 的稳定身份、fact / Source / instrument ownership 和待决领域语义，继承 [DataLake architecture](../../ARCHITECTURE.md) 与公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)。稳定入口见 [DATASETS.md](../../DATASETS.md)，public contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity、Source 与 state ownership

Canonical identity 为 `equity_index_options`。本 Dataset 表达股指期权合约及其 Source market facts，与指数日线、股指期货和 Snapshot option-chain 产品分离。Provider/endpoint 尚未锁定，identity 不预先绑定 Tushare；Source ownership 属于本 Dataset，具体 provider/endpoint/field mapping 明确留作下一轮。

本 bounded context 位于 `datasets/equity_index_options/`，独立拥有 authority、未来 src/、tests/ 及 data/ 中 exactly one SQLite，共用 repository root 唯一 Python project/environment。本轮只创建 authority，不创建 code、SQL schema、adapter、tests implementation 或 runtime data。

Option instrument catalog、Source normalization、Scope/Window、FetchUnit/Record、completeness 与 business view 均为本 Dataset responsibility。Provider 返回 option chain 或按 contract/date batching 不决定 canonical FetchUnit，不消费 Snapshot product-private Source/Capture 或 persisted Raw，也不复用其业务 contract 代替新 Dataset 决策。

## 2. Instrument 与 underlying boundary

Instrument 是 Dataset-local 股指期权合约 catalog，至少具备表达以下 Source semantics 的能力：

| Semantic capability | Boundary |
| --- | --- |
| product | 例如 IO / HO / MO，与 contract identity 分开 |
| contract code | 稳定 Source 合约 identity，canonical shape 待 Source contract 确认 |
| expiry | Source 到期语义，不据此生成 DTE feature |
| strike | Source 行权价，具体 units/representation 待确认 |
| CALL / PUT | Source 看涨/看跌语义；provider-native marker 到 canonical 值的 mapping 待确认 |
| exchange | 合约所属交易所 |
| underlying index identity | 带明确 namespace 的稳定 semantic identifier，不能使用另一库 instrument_id |
| lifecycle | 上市/到期等 Source facts，不猜尚未确认的有效区间 |

Underlying relationship 的语义目标为指数身份；使用 Tushare identity namespace 时保留完整 Source ts_code，具体 product → underlying mapping 尚须 Source facts 确认。Relationship 不依赖 Index cache 存在、不建立跨 SQLite foreign key，也不授予 Options → Index/Futures/Calendar runtime dependency。

下游 Research / Modeling 可通过 public services 组合各 Dataset 后生成 IV、moneyness、DTE derived features、option risk premium、premium 或 research statistics。本 Dataset 不计算这些派生结果，不将 Source 未提供的 Greeks/波动率补算为 Source facts；不为了研究便利合并 storage ownership。

## 3. Unresolved / deferred semantic decisions

本 Dataset 唯一拥有下表待决项；下一轮须人工确认后先更新 authority，再实现：

| Concern | 尚待决定；本轮不作选择 |
| --- | --- |
| Source contract | provider/endpoint、合法 option universe、metadata 与 market facts 的 required fields / units / marker mapping |
| canonical Scope | contract/product/expiry/chain selection 或其他完整寻址形态；是否需要多个 Scope |
| Window specialization | 一维 transient Window 的日期/时间含义、端点、交易日 prerequisite 与 lifecycle 关系 |
| FetchUnit identity | contract × date、expiry × date、product × date、整个 option chain × date 等候选，均未被选定 |
| Record identity / cardinality | natural key、一 unit 的合法 record set、重复/conflict / call-put pairing 语义 |
| completeness | market-cross-section / option-chain expected membership、缺腿/缺 strike、上市/到期、零交易、缺行或空响应的处理 |

公共 pending/success/failed、逐 Record 唯一 FetchUnit ownership、原子成功、默认跳过 success 已锁定。Option-chain completeness 与 FetchUnit 粒度尚未锁定；不能以 Source 返回的 chain 自证“链完整”，不能将 API success、返回行数或空响应作为 success predicate。上述决策未完成前，不定义可执行 expansion、coverage 公式或 persistence schema。

## 4. 下一份 authority

Public operation family、已锁定 result/error/export 边界及未决 consumer contract details 见 SERVICE.md；当前 implementation gap 统一见 [reconciliation](../../IMPLEMENTATION_RECONCILIATION.md)。本轮不设计 registry、dependency framework、CLI/HTTP integration 或跨 Dataset persistence。
