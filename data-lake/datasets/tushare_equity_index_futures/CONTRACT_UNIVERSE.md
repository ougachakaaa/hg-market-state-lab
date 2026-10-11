# Futures 合约全集与 product-day completeness authority

本文件拥有 expected contract universe、catalog 完整性证明、daily reconciliation 与成功依据保留，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)。Source fields/classification 由 [FACTS.md](FACTS.md) 拥有；公共结果与 failures 进入 [SERVICE.md](SERVICE.md)。不规定分页实现、SQL schema 或事务技术。

## 1. 完整 catalog 与 invocation basis

每次 ensure 在 Calendar 已确定目标、且存在 missing/non-success units 时，重新从 fut_basic 取得覆盖所选 products 的完整 ordinary catalog，包括已退市和尚未上市合约；不能只取当前挂牌合约、复用旧 catalog 假定完整，或以 fut_daily rows 生成 catalog。全部目标已 success 或目标为空时，不请求 metadata。Coverage/export 永不刷新 catalog。

请求显式使用 exchange=CFFEX、fut_type=1。取得完整 catalog 意味着已证明所选 products 的所有 Source metadata 都已取得且可合法解释，包括 provider limits、分页/截断与 Source filtering 的完整性；单次 API success、非空响应、少于某个经验行数或当前样本数量都不是独立证明。分页和批量 strategy 留给实现，但若不能证明无截断，必须将受影响 units 判为 failure，不能降低 completeness。

Catalog 按 [FACTS.md](FACTS.md) 验证 identity、ordinary classification、product、required facts 与 lifecycle。排除任何 metadata 前，必须核对完整 ts_code / symbol / fut_code / exchange evidence；identity 或产品证据冲突时，所有候选所选产品均失败。无法归属且不能证明 unrelated 的行按 catalog failure 处理，不能丢弃后缩小 expected universe。重复或冲突不能静默去重；只有能证明与某产品无关的缺陷才不影响该产品。失败可以隔离到产品时，其他已证明完整的产品继续执行。

本次合法 catalog 在 invocation 内冻结，所有本次尝试的 product-day 共用这一 basis，不逐日重新决定 expected set。它是本 Dataset-local metadata，不建立 global instrument master；后续 catalog 不自动重判已 success units。

## 2. Expected 与 observed

对已证明完整的 catalog C、所选 product p、Calendar 开市日 d：

```text
expected(p, d) = {c.contract_code | c in C,
                 c.exchange == CFFEX, c is ordinary fut_type=1,
                 c.product_code == p, c.list_date <= d <= c.delist_date}
```

生命周期由 Source list_date/delist_date 两端 inclusive 确定，不从 delivery month、last_delivery_date、日行情或产品上市知识猜日期。Catalog 证明先于 expected set；缺 metadata 是未知，不是空。

Observed 是 daily response 中归属于 (p,d) 的普通合约 multiset。可批量获取和 partition，但不得删除重复行以使集合相等。明确归属其他日期/未选产品的 rows 不影响该 unit，也不授权写入目标范围外 Records；CFFEX 国债产品等须有明确 classification 才排除。主力/连续 rows 只可依据 fut_basic(fut_type=2) 的合法 exclusion evidence 排除；该辅助 metadata 不成为 persisted instruments 或 Records。无法确认 family、且可能属于所选 product-day 的 row 使受影响 unit 失败；新出现的所选产品普通月合约不能按“不在 catalog”静默丢弃。

成功 predicate 同时要求：

- expected set 的 catalog basis 完整且合法。
- observed contract set 与 expected set 恰好相等，每个 expected contract 恰有一条 daily row。
- 每条 row 的日期、contract/product/metadata 关联一致，required Source facts 满足 FACTS.md；没有 duplicate、conflict 或 unexpected ordinary contract。

任一 missing contract、重复、额外普通合约、非法 required value 或不可合法 partition 的响应使整个 product-day non-success，不提交部分合约成功。合法 volume=0 的实际 row 满足正常 exactly-one 要求，不能把缺行解释为零成交。Source 尚未发布当天数据也不是空集合证明。

已证明 expected 为空时仍保留该开市日目标 unit：只有 observed 也为空且 Source 响应可合法确认，才提交零 Records 的 success。Source 请求失败或未知 catalog 不提供空集合证明。此规则支持产品上市前或其他确无 active contracts 的日期，不缩小 requested_units。

## 3. 原子成功与历史含义

一个 product-day 的完整 Records、所用合法 instrument metadata/completeness basis 和成功 metadata 必须在 owning SQLite 内一致原子提交；失败不暴露部分 Records 为成功事实。保留 basis 必须足以解释当次 expected set 与 Records 的一致性，但不指定 audit table、catalog version schema 或 hash 技术。

已有 success 默认跳过，不因下一次 Source catalog 增加、修订或移除合约而重新取得日行情、替换其成功依据或回溯 invalidation。覆盖查询按成功时保留的依据判断合法缓存；不能拿当前 catalog 重新定义过去成功的 expected set。Export 中关联 metadata 采用成功时保留的合法 facts，参与同一 owned-cache snapshot；不宣称是 trade_date 当时的历史 metadata 或 provider-current freshness。

Refresh/force/TTL、Source correction policy 与 stale semantics 留待独立设计。Catalog 获取批次、daily 请求次数和重试次数均不改变 FetchUnit grain 或 public counters。

冻结 basis 可以在本 Dataset 内去重存储；每个 unit 的历史 basis 不变，内部兼容性与 owning Dataset cache rebuild 见 [PERSISTENCE.md](../../PERSISTENCE.md)。同一 operation 内验证复用见 [EXECUTION.md](../../EXECUTION.md)，仍逐 unit 验证完整 contract universe。

合约生命周期索引是本 Dataset Domain 的内部策略，只索引已验证且保持不变的同一 catalog，精确实现上述 inclusive list_date/delist_date predicate；日期倒序访问仍须得到相同全集。索引不改变 expected/observed、未知活跃合约或分页完整性检查。
