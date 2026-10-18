# CFFEX 股指期货期限结构与基差共享语义 authority

本文件是 `CSI1000 IM Basis History` 与 `CFFEX Equity Index Futures Basis History` 两个真实 Snapshot Product 共用的确定性市场事实的唯一 canonical owner。产品各自拥有请求、Source scope、完整性、结果与执行契约；[Snapshot architecture](../../../ARCHITECTURE.md) 定义共享能力的边界。本能力不提供独立 Product、public request 或通用期货查询接口。

## Family 与标的事实

| `futures_family` | 标的指数 `underlying_code` | family 有效上市起点 |
| --- | --- | --- |
| `IF` | `000300.SH` | `2010-04-16` |
| `IH` | `000016.SH` | `2015-04-16` |
| `IC` | `000905.SH` | `2015-04-16` |
| `IM` | `000852.SH` | `2022-07-22` |

上市前日期不属于该 family 的有效 population。每个产品自行决定请求区间、观测日期及无观测时的失败契约；不得用其他 family、指数或日期代替。

## 合约身份、生命周期与期限位置

V1 只接受对应 family 的 CFFEX 普通月度股指期货合约。`contract_month` 是合约交割年、月的 maturity fact；从 `delist_date` 所在年、月确定，并要求与合约 identity 表达的年月一致，不符时失败而非猜测。`list_date`、`delist_date`、合约代码及月份均须存在、格式有效且自洽。一个合约在实际交易日 `T` active 当且仅当 `list_date <= T <= delist_date`。同一日期保留全部 active contracts；`volume`、`oi`、主力标记、流动性或研究偏好均不参与筛选或排序。

每个有效观测日必须有恰好四个不同合约月份，且每月恰好一个合约。按合约月份升序排列：前两个月份连续，依次为 `M0`、`M1`；后两个月份是严格晚于 `M1` 的前两个季月（3、6、9、12 月），依次为 `Q1`、`Q2`。`M0` 是当日最前端有效月度位置，交割后随 active universe 自然前移；slot 不是固定剩余天数桶。月份缺失、重复、序列不符或无法唯一映射时，产品不得删行、猜测或 fallback。

## 日历距离与合约级基差

必需输入是同一 `trade_date` 的指数 `underlying_close`、合约 `futures_close` 和该合约 `delist_date`。日期为真实 `YYYY-MM-DD`；两个 close 必须为 finite numeric（布尔值不是数值），且 `underlying_close != 0`。这些校验沿用既有 IM 产品边界；不新增会改变旧产品结果的正数限制。任何派生数值也必须 finite，否则该 observation 不可用。

```text
days_to_delist = delist_date - trade_date                 # calendar days, integer >= 0
annualization_days = max(days_to_delist, 1)              # calendar days
basis_points = futures_close - underlying_close          # index points
basis_pct = (futures_close / underlying_close - 1) * 100 # percentage points
annualized_basis_pct = basis_pct * 365 / annualization_days
                                                        # annualized percentage points
```

退市当日的 `days_to_delist = 0`、`annualization_days = 1`；不能为了避免除零而改写日历事实。这里使用简单线性年化，不定义 log basis、理论 fair basis、市场判断或交易含义。

## 规范顺序与失败边界

完整 flat panel 按 `trade_date` 升序、`M0/M1/Q1/Q2` 顺序、合约代码升序排列；合约代码仅为稳定 tie-breaker，不决定 slot。单日存在未知、重复、生命周期外的必需合约事实，或必需 close 缺失、无效、重复时，由消费 Product 将整个请求分类为不完整数据失败，不发布 partial panel。Source 获取范围及无观测日期规则仍由各 Product 拥有。
