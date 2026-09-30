# MO Option Risk Premium Baseline — Inputs

本文件是当前 Study 的 Inputs canonical owner。研究问题与验收从 [Study entry](ARCHITECTURE.md) 进入；Observation 如何使用这些输入见 [Method](METHOD.md)。

## Population 与固定选择

V1 population 为 MO 中证1000股指期权及其 CSI1000（`000852.SH`）标的指数；MO → CSI1000 映射由 [MO Option Chain](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) 拥有。CALL 与 PUT 均纳入，但分别呈现。`start_expiry_date` 与 `end_expiry_date` 是含端点的到期日范围，不是 entry 日范围；只能纳入该范围内由上游 canonical facts 确认的真实 MO expiry。每个 expiry 是一次 terminal risk event。

固定而不可配置的语义是 `option_product=MO`、`underlying=CSI1000`、CALL 与 PUT、entry high／low 均值 proxy、expiry-day index close payoff proxy；具体选择和计算由 [Method](METHOD.md) 定义。

## 用户输入与参数归属

| 输入或选项 | CLI 表达与契约 | Semantic owner；consumers；作用 |
| --- | --- | --- |
| `start_expiry_date` | `--start-expiry YYYY-MM-DD`，必填、有效日期 | Study；`ExpiryDteOptionOutcome` 与两个 Analysis；限定 expiry population，改变 evidence identity。 |
| `end_expiry_date` | `--end-expiry YYYY-MM-DD`，必填、有效日期且不早于起点 | Study；同上；限定 expiry population，改变 evidence identity。 |
| `dte_targets` | `--dte-targets`，可选的逗号分隔正整数；默认 `10,20,30,40,50,60`；非空 | `ExpiryDteOptionOutcome`；两个 Analysis 消费其 observation 的 target 轴；改变 entry 选择和 evidence identity。 |
| `moneyness_targets` | `--moneyness-targets`，可选的逗号分隔有限十进制数；默认 `0,0.05,0.10,0.15,0.20`；非空，可含负值 | `ExpiryDteOptionOutcome`；两个 Analysis 消费其 observation 的 target 轴；改变合约选择和 evidence identity。负值表示 ITM target。 |
| `overwrite` | `--overwrite`，可选布尔开关，默认 false | Study-owned execution-only option；CLI／output handling 消费，不进入 semantic request 或 run identity。 |

输入列表经解析、验证、去重、数值升序排序后成为 resolved target sets；省略参数与显式给出相同默认集合等价，原始空格和顺序不影响研究请求。`-0` 与 `0` 规范为同一 target。无效日期、倒置区间、空集合、非正 DTE、非有限 moneyness 或不可解析值均为输入失败。

从 repository root 的预期调用方式：

```bash
lab research run mo-option-risk-premium-baseline \
  --start-expiry 2024-01-01 --end-expiry 2026-01-01 \
  --dte-targets 10,20,30,40,50,60 \
  --moneyness-targets 0,0.05,0.10,0.15,0.20
```

当前没有 Study-local CLI；上述是预期调用契约，不表示命令已经可运行。共享 output placement、目录冲突与事务性覆盖沿用 [Research UI authority](../../ui/ARCHITECTURE.md)。

## Canonical upstream facts and dependency gaps

[MO Option Chain read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 的公开单日结果具有 expiry group、CALL／PUT、instrument identity、strike、所选 `price_type` 的 option price 及 CSI1000 price。对同一 entry 日分别请求 `price_type=high` 和 `low`，按日期、expiry、type、instrument identity 配对，才能形成所需 high／low facts；不能把不同合约或日期的价格拼接。合法的 selected option price `null` 保留合约结构，由本 Study 的 cell validity 处理。该产品不公开 option volume。

[Index Daily History public contract](../../../market-snapshot/src/market_snapshot/products/index_daily_history/read-contract.md) 可按 `000852.SH`、显式到期日期范围和 `pre_start_observation_count=0` 提供实际存在的 index close；本 Study 只用 expiry 当日 close，不以前一日或邻近日期替代。该产品不提供 MO expiry／entry-date 发现能力。

现有 MO Chain 的单日查询不能发现给定历史 expiry 范围内的全部真实 expiry，也不能给出各 expiry 上市 MO 合约的可观察历史 entry 交易日。所需的是由 Snapshot owner 发布、足以确定上述两个集合的公共历史发现能力；在其 contract 与 public execution boundary reconciliation 前，本 Study 不进入 implementation，不读取 Source、Raw、私有 Preparation、persistence layout 或 HTTP DTO 自行补足。这里记录上游 dependency gap，不在 Study 中定义新的 Snapshot Product contract。

若未来 Snapshot public result 提供 canonical option volume，所选合约的 `entry_volume` 可作为 liquidity／quality metadata 保留；它不参与 premium 加权、样本自动排除或 baseline 计算，缺失不阻止研究。Exact option settlement、Delta、IV、Greeks 不是 V1 所需能力。

## Retained run identity

整次 semantic request identity 由规范化的 `start_expiry_date`、`end_expiry_date`、resolved `dte_targets` 与 resolved `moneyness_targets` 构成。日期用 `YYYY-MM-DD`；DTE 在 JSON 中是十进制整数；moneyness 在 JSON 中是不用指数或浮点显示文本、无多余前后零的规范十进制字符串。四个具名字段按上述顺序、不含额外空白地编码为 UTF-8 JSON，两个 target 数组按数值升序。例如：

```json
{"start_expiry_date":"2024-01-01","end_expiry_date":"2026-01-01","dte_targets":[10,20],"moneyness_targets":["0","0.05"]}
```

Run key 为 `<start_expiry_date>__<end_expiry_date>__<该 JSON 的 SHA-256 小写十六进制摘要>`。同一规范请求得到同一 key；任一 identity-changing input 的不同规范值产生不同请求摘要。`--overwrite`、output root、运行时间、临时路径和用户原始拼写不参与。实际上游结果及其 provenance 随 [retained evidence](RESULTS.md) 保留，不以运行时间或路径代替语义 identity。
