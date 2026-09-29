# CFFEX Equity Index Basis Environment × Forward Return Association retained Study authority

本文档是本 retained Study 的稳定 canonical 入口。Stable public Study ID 为 `cffex-basis-forward-return-association`，对应 runnable package `cffex_basis_forward_return_association`。Authoring 遵循 [Study Authority Authoring](../AUTHORING.md)；Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI 转发、输出位置及覆盖规则见 [Research UI authority](../../ui/ARCHITECTURE.md)。[Method](METHOD.md) 拥有本 Study 的研究统计语义和三个 Observation / 四个 Analysis；[Results](RESULTS.md) 拥有 retained evidence contract。市场确定性事实与执行入口来自 [CFFEX Equity Index Futures Basis History](../../../market-snapshot/src/market_snapshot/products/cffex_equity_index_basis_history/ARCHITECTURE.md)，其共用合约语义见 [Snapshot CFFEX basis authority](../../../market-snapshot/src/market_snapshot/cffex_equity_index_basis/ARCHITECTURE.md)。

Executable [Study package](../../src/market_research/studies/cffex_basis_forward_return_association/) 以 `study.py` 为 orchestration entry；`observations.py` 对应三个具名 Observation，`analyses.py` 对应四个具名 Analysis，`statistics.py` 保存本 Study 的统计 mechanics，`results.py` 对应 retained Results / presentation。共享 Study 常量与错误类型留在 `context.py`。这些是 implementation navigation，不改变 Method 或 Results 语义。

## Question

研究 CFFEX IF、IH、IC、IM 四类股指期货自各自上市以来的历史基差环境，以及该环境与对应标的指数随后 1、3、5、10、20 条实际交易观测收益之间是否存在可观察、跨 family 相似的历史关联。具体回答：各 family 的基差与标的指数经历过怎样的历史变化；该 family 自身较低到较高的基差环境之后，指数收益分布有何差异；相同市场时期内四个 family 的关系是否具有相似方向。

预期产物是可复核的历史 evidence，不预设关联一定存在，也不把 observed basis 当作估值偏离、预测值、交易信号或策略收益。完整有效基差历史是各 family 的主要历史描述 population；需要未来收益的分析另使用具备完整 20D 后续观测的共同 predictor sample。跨 family 对照另外使用四者同日有效的 common-period sample。

## Inputs

V1 固定全部四个 family，不提供 family、underlying 或 contract 选择参数。上市日期之前不属于该 family 的 population，不计为缺失观测。

Family ↔ underlying 与有效上市边界由 [Snapshot CFFEX basis authority](../../../market-snapshot/src/market_snapshot/cffex_equity_index_basis/ARCHITECTURE.md) 唯一定义；本 Study 固定研究这四个 family，不成为这些市场事实的第二 owner。

| Input / option | 用户可见表达 | 必填与默认 | Semantic owner 与消费位置 |
| --- | --- | --- | --- |
| `start_trade_date` | `--start YYYY-MM-DD` | 必填，无默认 | Study population bound；三个 Observation 与全部 Analysis 使用。 |
| `end_trade_date` | `--end YYYY-MM-DD` | 必填，无默认 | Study population 与 forward-support bound；三个 Observation 与全部 Analysis 使用。 |
| `overwrite` | `--overwrite` | 可选，默认 false | Study-owned execution option；仅按 Research UI authority 替换已有完整 run directory，不参与研究语义或 identity。 |

两端均为有效、含端点的 calendar dates，要求 `start_trade_date <= end_trade_date`；不使用 `today`、`latest`、隐式窗口或自动最近 N 年。每个 family 的请求有效起点为 `max(start_trade_date, listing_date)`，终点不超过 `end_trade_date`。请求可以早于某些 family 上市，但成功 run 必须满足 Acceptance 的四 family 样本要求。CLI 示例：

```bash
lab research run cffex-basis-forward-return-association \
  --start 2010-04-16 --end 2026-09-28
```

### Upstream public Product

本 Study 对 `IF`、`IH`、`IC`、`IM` 各调用一次 [CFFEX Equity Index Futures Basis History](../../../market-snapshot/src/market_snapshot/products/cffex_equity_index_basis_history/ARCHITECTURE.md) 的 production execution entry，每次仅提供 family 和同一显式起止日期。Snapshot Product 拥有 family/underlying/listing facts、active universe、四槽、同日 close、合约级 basis、完整性、分类失败与 public result。本 Study 只消费该 Product 的 analysis-ready result，不接触 Tushare credential、Source client、Capture、Raw、私有 Preparation 或 HTTP DTO。上游 Product public execution entry 已实现。

### Retained request identity

V1 的 family、predictor、horizons 和方法均固定。两个日期先校验并规范为 `YYYY-MM-DD`；同一有效日期区间具有同一 semantic request 和 run key：`<start_trade_date>__<end_trade_date>`。改变任一日期必须改变 run key。`--overwrite`、output root、执行时间、随机值和原始命令拼写不参与。共享 Research UI 使用该 key 安排 `<output-root>/<study-id>/<run-key>/`，并在调用 Snapshot 前处理已有目录冲突。

## Limitations

- Association 不证明因果：下跌与套保需求变化也可能共同驱动贴水，basis 可具有内生性。
- 利率、预期分红、剩余期限、资金与流动性等均影响 observed futures basis；它不直接等于指数估值或相对理论 fair basis 的偏离。
- 不同时期的交易制度、参与者、规模和宏观环境会变化；全历史关系未必平稳。common-period 视图只控制比较日期，并不能消除这些变化。
- 全样本分位点含事后信息，不能直接作为实时状态定义或交易阈值。未来 Modeling 若使用此发现，需先另作语义决定与 authority update。
- 5D/10D/20D forward windows 大量重叠，简单 correlation/OLS 不支持 p-value、置信区间或显著性结论；四个相关指数也不是四组独立实验。
- 本 Study 不产生 forecast、expected-return signal、买卖或持仓建议、策略 PnL、理论 fair basis、机器学习模型、盘中数据、HTTP API 或 frontend UI。

## Acceptance

- canonical authority graph 明确四 family、Snapshot-owned 映射与上市界限、必填日期、CLI ID、run identity、上游 Product 与 Research/Snapshot ownership；实现只能使用新 Product 的 public application boundary。
- 三个具名 Observation 的事实、派生值、有效性、尾部 future-support 和独立 Artifact identity 均可从上游 public input 追踪；完整 M0/M1/Q1/Q2 保留，M0 不进入每日 predictor。
- `historical_basis_context` 使用完整 basis history；其他三个 Analysis 使用各自明确的 20D 或同日交集 population，不跨越请求终点。每个 Question aspect 均有 Observation → Analysis → retained evidence 链路。
- 四 family 均须至少有一条完整 20D predictor observation，且 common-period 同日交集非空；否则整次 run 失败，不发布成功 evidence。上游缺失或不完整的必需 basis facts 亦不能被静默丢弃。
- Full-history 与 common-period 分位点各按自身 population 计算；同值不拆桶，空组、零收益、未定义统计与 premium/discount/zero 的分母表达正确。各 family 的 full-history 20D predictor count 等于五个 quintile 在每个 horizon 的 count 之和；common-period 的相应总数等于交集日期数。
- 成功 evidence 含所列逐日 Artifact、provenance、样本和排除计数、阈值、统计表、报告与静态图；表图能从 machine-readable 数值复核，且不会把历史关联陈述为因果、显著性、forecast 或交易建议。
