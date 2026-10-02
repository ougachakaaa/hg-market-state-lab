# Index Daily Source facts 与 Instrument authority

本文件拥有本 Dataset 的 Source representation → canonical facts mapping、instrument catalog 与 normalization，继承 [Dataset architecture](ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)。Public projection/types 由 [SERVICE.md](SERVICE.md) 拥有；本文件不定义 SQLite schema。

## 1. Source identity 与 index selection

完整 `index_basic.ts_code` 是 canonical `index_code` 和 local instrument 的稳定 semantic identity；保留大小写与后缀，不从名称猜 code，不把 `.CSI` 改成 `.SH`，不将相似名称或跨 Source code 视为别名。Tushare 明确要求 index_daily 的 code 来自 index_basic，后缀可表达所属公司而非交易所；见 [index_daily Source documentation](https://tushare.pro/document/2?doc_id=95)。

V1 接受以沪深交易日语义发布、由 index_basic 确认且 index_daily 提供日线的中国指数；canonical code representation 为六位数字加 `.SH` / `.SZ` / `.CSI`。这不是九个常用指数的 whitelist。其他 Source family / calendar 的接入须先扩展本 Dataset 的窄契约；不能仅凭 index_basic 有一行就声称所有指数 Source 均已支持（例如 index_daily 不包含申万行业行情）。

代表性选择包括上证综指、上证50、沪深300、中证500、中证1000、中证2000、深证成指、创业板指、科创50。它们是 consumer selection 示例，不是 service 隐式 defaults、fact-space 上限或固定代码表。各自完整 canonical ts_code 必须以 index_basic Source facts 确认；本轮没有读取 authenticated catalog，不将猜测的后缀固化为 authority。名称不作为 public request identity。

`index_codes` 解释为非空 set：重复 code 合并，canonical scope 按完整 code lexicographic ascending 排序。不 trim、改写大小写、补后缀或把六位裸 symbol 转成 code。Source 不存在的 code 与合法请求格式是不同问题；read-only operation 不额外访问 Source 来验证 membership。

## 2. Dataset-local instrument catalog

`instrument usage: Dataset-local index catalog`。Source 为 [index_basic](https://tushare.pro/document/2?doc_id=94)，查询显式选择相关 market，不依赖其默认 SSE 而漏掉 SZSE / CSI。Catalog 只拥有本 Dataset instrument facts；不保管全仓 instrument master。

| Canonical semantic fact | Provider representation / meaning |
| --- | --- |
| index_code / source_code | 完整 ts_code，必需且唯一 |
| symbol | ts_code 的六位 code 部分；仅确定性拆分 representation，不是第二套身份 |
| name | Source name，必需非空，不从推荐名称表生成 |
| market | Source market，必需非空；可表达交易所或服务商，不伪装为统一 exchange taxonomy |
| publisher | Source publisher；合法缺席为 None |
| category | Source category；合法缺席为 None |
| published_on | Source list_date，合法日期或合法缺席；不是首个行情交易日 |
| terminated_on | Source exp_date，合法日期或合法缺席；不自行推导生命周期 |

Publisher/category/lifecycle 只保留 Source 已提供且合法的语义；格式错误不作为合法缺席。Instrument identity 与 daily record identity 必须一致，local record 可以引用同库 instrument；不得引用 Calendar、Futures 或 Options 的 instrument_id。

Ensure 对缺少本地合法 instrument metadata 的 selected index，通过 index_basic 确认唯一匹配的 metadata 后，才允许该指数 selected daily units 成功。Metadata 不存在、重复/conflict 或无效时，受影响 selected units 失败；可恢复的 metadata Source request failure 同样按这些 units 返回，不创建假 instrument。完整合法 metadata 可复用；V1 不另行设计 refresh。只处理已有 success 或零目标 unit 时，不为更新 catalog 调用 Source。

## 3. Canonical daily Record facts

下表为本 Dataset 必需的 Source facts；canonical 字段名与 provider 字段名明确分离。

| Canonical field | index_daily field | Semantic value / unit |
| --- | --- | --- |
| index_code | ts_code | 完整 Source identity |
| trade_date | trade_date | 合法目标交易日 |
| open | open | 开盘点位 |
| high | high | 最高点位 |
| low | low | 最低点位 |
| close | close | 收盘点位 |
| pre_close | pre_close | Source 前收盘点位 |
| change | change | Source 涨跌点位 |
| pct_change | pct_chg | Source 百分数；1.5 表示 1.5%，不转换为 0.015 |
| volume | vol | 成交量，保留 Source 单位手 |
| amount | amount | 成交额，保留 Source 单位千元 |

日期由 provider YYYYMMDD representation 确定性转换为 date；数值必须可合法转换为 finite numeric value，不接受 bool、缺失值、NaN 或 infinity。Volume / amount 不接受负值；零仅在 Source 实际报告零时合法。禁止 rounding、fill、重算 change/pct_change、单位暗换或将 None 当零。

成交量与成交额表达该指数 Source 的统计范围，不用全市场股票成交替代；不将不同 Source 的成交口径“修正”为行情软件口径。以上 Source units 参见 index_daily 文档；本 Dataset 不生成衍生指标或 research features。
