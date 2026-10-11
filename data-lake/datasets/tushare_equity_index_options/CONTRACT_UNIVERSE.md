# Options 合约全集与 product-day completeness authority

本文件拥有完整期权 catalog、expected contract universe、daily reconciliation 与成功依据保留，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)。Source identity/fields 由 [FACTS.md](FACTS.md) 拥有；public accounting/failures 进入 [SERVICE.md](SERVICE.md)。不定义 SQL、分页算法或事务实现。

## 1. Catalog 证明与冻结

每次 ensure 在 Calendar 已确定目标且存在 missing/non-success units 时，重新从 exchange=CFFEX 的 opt_basic 取得覆盖所选 products 的完整真实股指期权 catalog，包括已退市与尚未上市合约。旧 local catalog 不能替代本次完整取得；不能仅取当前挂牌合约或由 opt_daily 推导 expected。目标全部 success 或为空时不请求 metadata，coverage/export 不访问 Source。

Source 请求成功不等于 catalog 完整。必须证明 provider filtering、limits、分页/截断没有遗漏所选产品 metadata；单页行数、当前样本总数、日行情数量相等均不能独立证明。若运行时无法取得足够证明，受影响 units 失败，不能退回弱 completeness。

按 [FACTS.md](FACTS.md) 显式 normalization 确认 product、exchange、contract identity、underlying、expiry/strike/CALL-PUT 与 lifecycle。排除任何 metadata 前，必须核对完整 ts_code / symbol / opt_code / opt_type / exchange evidence；identity 或产品证据冲突时，所有候选所选产品均失败。无法归属且不能证明 unrelated 的行按 catalog failure 处理，不能丢弃后缩小 expected universe。Duplicate/conflicting identity、缺 required metadata 不得静默去重/丢弃。只有能证明 unrelated 的 defect 才不影响该产品；可隔离产品时其他已证明完整的产品继续。

本次合法 catalog 在 invocation 内冻结，以同一 basis 解释全部本次 attempts。Catalog 为 Dataset-local Instrument facts，不属于 global master；获取与保存的技术细节不改变这一 completeness contract。

## 2. 全部 active contracts

对完整合法 catalog C、所选 product p 和 Calendar 开市日 d：

```text
expected(p, d) = {c.contract_code | c in C,
                 c.exchange == CFFEX, c is real index option,
                 c.product_code == p, c.list_date <= d <= c.delist_date}
```

上界只能是 delist_date，不能用 maturity_date/expiry 或 last_exercise_date 代替。Expected 包含该日所有挂牌 expiry、strike、CALL/PUT 合约，不做 expiry 子集、近月、ATM 或两腿配对 Scope；也不补造 catalog 未列出的对腿或 strike。生命周期、产品 normalization 与 Source facts 冲突时失败，不以日行情修复 metadata。

Observed 是 daily response 归属 (p,d) 的真实股指期权 multiset，按 metadata/稳定代码契约合法 partition。明确属于其他日期、未选产品或非本 family 的 rows 可排除，也不授权写入目标范围外 Records；未知且可能属于 selected product-day 的 row、以及未在 expected 中的所选产品真实合约均使受影响 unit 失败，不静默丢弃。

成功须同时满足完整 catalog 证明、observed set == expected set、每个 expected contract 恰有一条合法 daily row、每条 row 的 identity/日期/product/Instrument 与 required facts 一致。Missing expiry/strike/腿体现为 expected 中任一 contract 缺行；duplicate、conflict、unexpected contract、invalid required value 或无法合法 partition 都使整个 product-day non-success，不能提交部分 chain 成功。

合法无成交合约仍必须有实际 daily row。仅 FACTS.md 确认 volume=amount=0 时允许 open/high/low 个别 None；不把缺行、缺字段、正成交时空价格或其他 required 空值视为无成交成功。

已证明 expected 为空时，开市日仍是目标 unit；只有 observed 也为空且 Source 响应可合法确认才提交零 Records 的 success。未知/截断 catalog 或失败/未发布的 daily 响应不是空集合证明；不能据此减少 requested_units。

## 3. 成功依据与 snapshot

完整 product-day Records、所用合法 metadata/completeness basis 和成功 metadata 在自己的唯一 SQLite 内一致原子提交。Basis 保留到足以解释当次 expected set 与完整 Records；不规定 SQL versioning、audit table 或 hash scheme。失败不暴露不完整 Records 为 success payload。

已有 success 默认跳过；后续 catalog 修订不重判其历史 completeness、不重写成功依据、不单独触发 refresh。Coverage 按保留的成功依据解释 owned cache，不能使用当前 catalog 扩缩旧 expected set。Export 的 expiry/strike/CALL-PUT 及其他 metadata 来自相应 success 保留的合法 Source facts，与 Records/coverage 来自同一个 owned committed snapshot；不宣称 trade_date 当时 metadata 或 provider-current freshness。

Refresh、force、TTL、Source correction/stale semantics 留待独立设计。Source batching/retries/catalog row counts 不改变 product-day ownership 或 public accounting。

冻结 basis 可以在本 Dataset 内去重存储；每个 unit 的历史 basis 不变，内部兼容性与 owning Dataset cache rebuild 见 [PERSISTENCE.md](../../PERSISTENCE.md)。同一 operation 内验证复用见 [EXECUTION.md](../../EXECUTION.md)，仍逐 unit 验证完整 contract universe。
