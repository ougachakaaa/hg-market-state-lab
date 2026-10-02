# Options Source facts 与 Instrument authority

本文件拥有 Source selection、Dataset-local Instrument、product normalization、canonical facts 与 underlying relationship，继承 [Dataset architecture](ARCHITECTURE.md)。Catalog 证明与 completeness 见 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，public projection/types 见 [SERVICE.md](SERVICE.md)。不定义 SQL、Source adapter implementation 或研究公式。

## 1. Source identity 与 product normalization

Metadata Source 为 Tushare [opt_basic](https://tushare.pro/document/2?doc_id=158)，exchange 显式 CFFEX。完整 ts_code 是 contract_code，保留 `.CFX`；symbol 是交易代码，二者必须一致。Opt_code 是标的合约代码，不是 product_code，不通过中文 name 识别产品。

根据 [CFFEX 股指期权交易代码契约](https://www.cffex.com.cn/cn/ssxz/20221214/43100.html)，symbol 使用完整 anchored shape `product + YYMM + "-" + C/P + "-" + strike`：product 为 uppercase ASCII letters；YYMM 的 MM 合法；strike token 是正的十进制数，允许小数 representation。Ts_code 必须恰为 symbol + `.CFX`。Product_code 从这一稳定 representation 解析，再按下方市场表确认股指产品 classification。

解析只用于 identity normalization/validation：C/P 与 Source call_put 一致，代码 strike 与 exercise_price numeric value 一致，YYMM 与 Source s_month 的后四位一致。Expiry、list_date/delist_date、行权日期全部来自 Source 明确字段，不从 YYMM 或交易规则推算日期。任何冲突不得使用代码覆盖 metadata。

## 2. Canonical Instrument facts

Contract_code 在 Dataset-local catalog 中唯一。除明确 nullable 外均 required；strings 非空、数值 finite，per_unit/opt_multiplier/strike 为正，list_date <= delist_date；invalid date/number 不作为合法缺席。

| Canonical fact | opt_basic representation / meaning |
| --- | --- |
| contract_code, symbol, name, exchange | ts_code、symbol、name、exchange；exchange 固定 CFFEX |
| product_code | 上方代码 normalization，与市场关系表一致 |
| source_underlying_code | opt_code，Source native 标的 identity，完整保留 |
| underlying_index_code | 从 Source OP + index ts_code representation 提取并核对下方市场表，保留完整 index ts_code namespace |
| option_type, exercise_type | opt_type、exercise_type；本 family 的 option_type 为 Source 指数期权 |
| per_unit, opt_multiplier, quote_unit | 同名，Source 合约单位、调整后合约单位与报价单位；前两者只作合法 numeric representation normalization，不因样本相等而合并 |
| settlement_month | s_month，合法 YYYYMM |
| expiry | maturity_date，Source 到期日；不作为日行情 lifecycle 的上界替代值 |
| strike, call_put | exercise_price、call_put；C → CALL，P → PUT，不根据 name 推导 |
| list_date, delist_date | 开始交易日、最后交易日，两端 inclusive |
| last_exercise_date | last_edate，Source 最后行权日 |
| last_delivery_date | last_ddate，Source 合法缺席允许 None |

## 3. Underlying relationship ownership

| product_code | Underlying | Source opt_code | underlying_index_code |
| --- | --- | --- | --- |
| IO | 沪深300 | OP000300.SH | 000300.SH |
| HO | 上证50 | OP000016.SH | 000016.SH |
| MO | 中证1000 | OP000852.SH | 000852.SH |

CFFEX 产品关系由本 Dataset 的 Instrument market contract table 拥有；opt_basic 提供 source_underlying_code，Source OP representation 的提取是确定性 normalization，不生成衍生 market fact。关系表与 Source value 必须一致；具体 index codes 已通过 index_basic 核对，对齐 [Index namespace](../tushare_index_daily/FACTS.md)。不能伪称 product→underlying 市场关系来自 opt_daily。没有 Index/Futures runtime dependency、跨库 FK 或 instrument_id 引用。

本表是当前可扩展产品分类/关系契约，不是永久 enum whitelist；未来产品先补充市场关系与 Source identity，再使用同一 product Scope，不新增 expiry/strike selection 或 registry。

## 4. Canonical OptionsDailyRecord

Record identity 为 `(contract_code, trade_date)`；product_code 与 unit 一致，Record 同时表达合法 Instrument 的 expiry、strike、call_put。日行情 Source 为 [opt_daily](https://tushare.pro/document/2?doc_id=159)。

| Canonical field | Source field / meaning |
| --- | --- |
| contract_code, trade_date, exchange | ts_code、trade_date、exchange；日期从 YYYYMMDD 转为 date，exchange 与 metadata 同为 CFFEX |
| product_code, expiry, strike, call_put | 本 unit 使用的合法 Instrument facts；不从 daily rows 反推 catalog |
| pre_settle, pre_close | 同名，Source 前结算/前收盘 |
| open, high, low, close, settle | 同名 Source 日行情价格，nullable rule 见下方 |
| volume, amount, open_interest | vol（手）、amount（万元）、oi（手） |

Volume、amount、open_interest required 且 finite/non-negative；pre_settle、pre_close、close、settle required 且 finite。拒绝 bool、非法数值/infinity，不把缺行、缺字段或 required missing value 当零。

仅当 Source 明确 volume=0 且 amount=0 时，open/high/low 中的合法缺席可以分别为 None，其他实际提供值照原值保留；不补零、不前值填充。正成交量或正成交额却缺 open/high/low 时整 unit 失败。该规则允许合法无成交 record，不改变 expected contract set、exactly-one cardinality 或其他 required facts；Source 未提供 required field 本身仍是 contract failure。

不 rounding、补算或暗换单位，不生成 IV、Greeks、moneyness、DTE、option risk premium 或其他 research features。Expiry/strike/call_put 是 metadata Source facts，参与完整横截面解释，不能据此补造 catalog 未声明的合约。

## 5. Source feasibility evidence

2026-10-01 设计阶段只读核对：CFFEX opt_basic 的 offset=0/4000/8000、limit=4000 分页取得 4000/4000/2384 行，未重复；offset=12000 返回空，累计 10384 个不同 contracts，与完整请求一致。产品代码前缀为 IO/HO/MO，call_put 为 C/P，opt_code 与上表一致；last_ddate 样本为合法空。

2026-09-30 的 656 条日行情与 metadata lifecycle expected set 完全一致，其中 70 条 volume=amount=0 且 open/high/low 缺席；2026-07-01 的 666 条亦完整匹配，其中 25 条出现同类缺席。这些是当次 Source evidence，不是日线数量常量、永久分页契约或用日行情证明 catalog 完整的替代办法。
