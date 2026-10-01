# equity_index_futures Dataset architecture authority

本文件拥有股指期货自治 bounded-context 的稳定身份、fact / Source / instrument ownership 和待决领域语义，继承 [DataLake architecture](../../ARCHITECTURE.md) 与公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)。稳定入口见 [DATASETS.md](../../DATASETS.md)，public contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity、Source 与 state ownership

Canonical identity 为 `equity_index_futures`。本 Dataset 表达股指期货合约及其 Source market facts，与指数日线、股指期权和 Snapshot products 分离，不合并成 market Dataset。任务尚未锁定 provider/endpoint，因此 identity 不预先绑定 Tushare；具体 provider、metadata/market-fact endpoint 与 field mapping 是下文显式待决项。

本 bounded context 位于 `datasets/equity_index_futures/`，拥有自身 authority、未来 src/、tests/ 与 data/ 中 exactly one owned SQLite，共用 repository root 唯一 Python project/environment。本轮只创建 authority；不生成 source、SQL、adapter、service implementation 或 runtime data。

Source composition、合约 catalog、market facts normalization、FetchUnit/Record specialization、completeness 与 view 由本 Dataset 独立拥有。Provider batching 不决定 canonical Scope 或 FetchUnit；公共 kernel 不知道本 Dataset/provider。尚未确认的 Source contract 不能以已有 Snapshot 产品代码或 Tushare API 请求形态代替业务决策。

## 2. Instrument 与 underlying boundary

Instrument 为 Dataset-local 股指期货合约 catalog，至少具备表达以下 Source semantics 的能力：

| Semantic capability | Boundary |
| --- | --- |
| product | 例如 IF / IH / IC / IM，不与具体 contract 混同 |
| contract code | Source 的稳定合约 identity，具体 canonical shape 待 Source contract 确认 |
| delivery / expiry month | 合约交割/到期月份语义，不从代码猜未确认事实 |
| exchange | 合约所属交易所 |
| lifecycle | listing 与 expiry 的 Source facts，不生成 DTE feature |
| underlying index identity | 带明确 identity namespace 的稳定 semantic identifier，不能使用另一库 instrument_id |

Underlying 的语义目标是指数身份；同一 Index Source namespace 中可使用完整 Tushare ts_code 表达，但具体 product → code 映射与 normalization 须以 Source facts 确认，不猜后缀。Relationship 不要求 Index cache 存在，不建立 SQLite foreign key，也不授予 Futures → Index/Calendar runtime import/service dependency。

下游可通过各 Dataset public service 组合 futures/index/options 后生成 basis、term structure、premium 与 research statistics；本 Dataset 不做跨产品 join、rolling/main-contract synthetic series 或上述 research computation。合约 Source market facts 与 instrument semantics 独立于 Research 所需的比较范围。

## 3. Unresolved / deferred semantic decisions

下表由本 Dataset 唯一拥有，下一轮须人工确认后先更新 authority，再开始实现：

| Concern | 尚待决定；本轮不作选择 |
| --- | --- |
| Source contract | provider/endpoint、合法 contract universe、metadata 与 market facts 的 required fields / units |
| canonical Scope | product selection、明确 contract selection 或其他完整寻址 fact-space 的形态；是否需要多个 Scope |
| Window specialization | 公共一维 transient Window 内的日期/时间含义、端点、历史与 lifecycle 关系、交易日 prerequisite |
| FetchUnit identity | `(contract, trade_date)` 或 `(trade_date)` market cross-section 等候选；不由 batching 推导 |
| Record identity / cardinality | Source market fact 的 natural key、一 unit 拥有的 record set 与 duplicate/conflict rule |
| completeness | 如何确定 expected contracts；上市/到期、缺失/零交易、横截面缺口与 success 条件 |

公共 pending/success/failed、Records 唯一 ownership、原子成功与默认跳过 success 的 invariants 已锁定；本 Dataset 的粒度与 success predicate 尚未锁定。不以空响应、返回行数或 provider request success 宣告 completeness；在这些决策完成前不定义可执行 target expansion、coverage 数值公式或 SQL schema。

## 4. 下一份 authority

Public operation family、已锁定 result/error/export 边界及尚未发布的 request/view details 见 SERVICE.md；所有当前 implementation gaps 见 [reconciliation](../../IMPLEMENTATION_RECONCILIATION.md)。本轮不设计 dependency framework、CLI/HTTP delivery 或 cross-Dataset persistence。
