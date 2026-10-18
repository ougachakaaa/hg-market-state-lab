# Futures Source facts 与 Instrument authority

本文件拥有 Source selection、Dataset-local Instrument、canonical fact mapping、normalization 与 underlying relationship，继承 [Dataset architecture](ARCHITECTURE.md)。Catalog 取得/证明与 completeness 见 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，public Python projection/types 见 [SERVICE.md](SERVICE.md)。不定义 SQL schema、adapter 实现或研究公式。

## 1. Source 与 instrument family

Metadata Source 为 Tushare [fut_basic](https://tushare.pro/document/2?doc_id=135)：显式 `exchange="CFFEX", fut_type="1"`。`fut_code` 是 product，`ts_code` 是完整 Source contract identity；不混用两者。普通真实月合约的 symbol representation 为 `product + YYMM`，ts_code 为该 symbol 加 `.CFX`；月份 MM 必须合法。Product 以 fut_code 为准，并与 symbol 前缀交叉核对；delivery month/lifecycle 使用 Source 明确字段，不从代码猜日期。

主力/连续 family 的 `fut_basic(fut_type="2")` 只提供 exclusion classification evidence，不成为本 Dataset instrument catalog 或 Records。明确识别为非普通 family 的批响应 rows 排除；未知的 selected-product 普通月合约不在此排除范围，必须按 CONTRACT_UNIVERSE.md 失败。CFFEX 国债期货也不属于股指产品范围。

## 2. Canonical Instrument facts

每个 contract_code 对应唯一合法 local Instrument。下表除明确 nullable 外均 required；Source 非空 strings 保留原值，数值必须 finite，日期必须合法。Multiplier / per_unit 必须为正；list_date <= delist_date。重复/conflicting identity 不得静默去重。

| Canonical fact | fut_basic field / meaning |
| --- | --- |
| contract_code | ts_code，完整 `.CFX` identity |
| product_code | fut_code，见下方市场契约表 |
| symbol, name, exchange | 同名 Source fields；exchange 固定 CFFEX；symbol 与 contract identity 一致 |
| multiplier | multiplier，保留 Source 合约乘数 |
| trade_unit, per_unit, quote_unit | 同名 fields，分别为计量单位、每手交易单位与报价单位，不合并或互相替代 |
| list_date | list_date，上线交易日期 |
| delist_date | delist_date，最后交易日；两端 inclusive |
| delivery_month | d_month，合法 YYYYMM，与 symbol 的 YYMM 一致；不据此生成 expiry date |
| last_delivery_date | last_ddate，最后交割日，与 delist_date 保留为独立 Source facts |
| underlying_index_code | 下方 authority-owned market contract mapping；identity namespace 为 Tushare index ts_code |

## 3. Underlying market contract ownership

| product_code | Underlying | underlying_index_code |
| --- | --- | --- |
| IF | 沪深300 | 000300.SH |
| IH | 上证50 | 000016.SH |
| IC | 中证500 | 000905.SH |
| IM | 中证1000 | 000852.SH |

本表由本 Dataset 的 Instrument semantic layer 拥有；CFFEX 产品关系是市场契约，例如 [IM 合约交易细则](https://www.cffex.com.cn/cn/ssxz/20220718/43093.html)。具体 index identity 使用 Tushare index ts_code，与 [Index identity namespace](../tushare_index_daily/FACTS.md) 一致。这不是 fut_daily 直接字段，也不授权查询 Index service/SQLite。扩展表必须确认新产品属于 CFFEX 股指期货及其完整 underlying Source identity；不为未来产品预建插件/registry。

## 4. Canonical FuturesDailyRecord

Record identity 为 `(contract_code, trade_date)`；product_code 与 owning unit、Instrument 一致。Primary daily Source 为 [fut_daily](https://tushare.pro/document/2?doc_id=138)。

| Canonical field | Source field / meaning |
| --- | --- |
| contract_code, trade_date | ts_code、trade_date；日期从 YYYYMMDD representation 转为合法 date |
| product_code | 合法 Instrument fut_code，不由中文 name 推导 |
| pre_close, pre_settle | 同名，Source 前收盘/前结算 |
| open, high, low, close, settle | 同名，Source 日行情价格 |
| close_change_from_pre_settle | change1，Source 收盘价相对前结算的变化 |
| settle_change_from_pre_settle | change2，Source 结算价相对前结算的变化 |
| volume, amount | vol（手）、amount（万元） |
| open_interest, open_interest_change | oi（手）、oi_chg（Source 持仓变化，可负） |
| delivery_settlement_price | delv_settle；Source 合法缺席为 None |

除 delivery_settlement_price 外 daily facts required 且数值必须 finite；拒绝 bool、missing、NaN、infinity，volume/amount/open_interest 不得为负。Source 实际提供的零合法，不把零成交当缺行。Delv_settle 必须显式请求；未请求而省略字段不等于已确认 Source 合法缺席，返回的合法空值才表达 None。

例外：Source 明确返回 pre_close / oi_chg 字段但其值合法缺席，且 trade_date == owning Instrument 的 list_date 时，分别为 None，表示首次挂牌没有前收盘价 / 没有前一日持仓变化基准。不用 pre_settle、当前持仓、挂牌基准价或零替代。非上市首日缺席、字段本身缺失、非法数值仍失败；其余价格/变化字段规则不变。该规则优先于上段 general required numeric rule。

保留 Source 统计口径：fut_daily 文档说明 2020-01-01 之前为双边统计、之后为单边统计；不自行统一 volume/oi，也不暗换 amount 为 Index view 的千元或人民币元。不 rounding、fill、重算 change、补造价格或产生 basis/DTE/term structure。

## Bounded Source execution

按日期排列并合并同窗口所有 selected products，每批最多 5 个 selected 交易日，查询自然日跨度同时不超过 31 日，使用 fut_daily 的 exchange/start_date/end_date 查询并完整分页。只提交本次 selected units，逐 unit completeness 与 public accounting 不变。执行、验证复用及单 worker 提前一批见 [EXECUTION.md](../../EXECUTION.md)。

小窗口横截面按日期与产品一次分类；不能因分桶丢弃不可归属的非法行。可归属错误只影响对应产品日，无法归属错误影响对应日期所有 selected products；非目标日期不提交。分类只实现 CONTRACT_UNIVERSE.md 的既定 predicate，不改变分页穷尽或未知活跃合约检查。
