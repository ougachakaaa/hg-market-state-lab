# Research CLI command manual

本文档是“当前有哪些 runnable retained Study、命令如何调用”的用户入口。CLI ownership、routing 与 output placement 见 [Research UI authority](ui/ARCHITECTURE.md)；配置见 [Research UI configuration](ui/CONFIGURATION.md)。Study method 与统计语义只由对应 retained Study authority 定义，不在此复制。

> Implementation status：本轮只锁定 authority、configuration contract 与 command manual；当前 commit 尚未提供 `market-research` executable 或 config loader。以下命令是下一轮实现必须提供的 canonical V1 surface，不应在该实现完成前被视为已经可执行。

## Invocation

所有命令从 repository root 通过统一 namespace 调用：

```text
poetry run market-research ...
```

V1 不提供每个 Study 的独立 executable，也不通过 root `dev.py` 暴露 Research catalog。

## Discover Studies

```text
poetry run market-research list
```

输出每个 runnable retained Study 的 stable ID 与 short description；不访问 Source，也不执行 Study。

## Inspect Configuration

```text
poetry run market-research config
```

输出实际加载的 canonical config source 与 resolved absolute output root。V1 config 固定为 `market-research/research.toml`，不接受 alternate config path，也不输出 `TUSHARE_TOKEN` 或其他 secret。

## Run a Study

```text
poetry run market-research run <study-id> --start YYYY-MM-DD --end YYYY-MM-DD
```

Required arguments：

- `<study-id>`：下方 catalog 中的 stable ID；
- `--start`：inclusive `YYYY-MM-DD` start trade date；
- `--end`：inclusive `YYYY-MM-DD` end trade date。

日期没有 today/latest/default。若同一 Study 与日期区间的 canonical run directory 已存在，命令默认失败并保留原 evidence；显式增加 `--overwrite` 才会整体替换该目录：

```text
poetry run market-research run <study-id> --start YYYY-MM-DD --end YYYY-MM-DD --overwrite
```

输出目录为：

```text
<resolved-output-root>/<study-id>/<start>__<end>/
```

成功时 CLI 报告 Study ID、requested date range、resolved output directory 与 main artifacts；完整结果保留在文件中。

## Available Study IDs

### `im-basis-baseline`

Purpose：描述 IM `M0`、`M1`、`Q1`、`Q2` 及 `non_front_mean_basis` 的历史年化基差分布与期限结构。

```text
poetry run market-research run im-basis-baseline --start 2024-01-01 --end 2026-01-01
```

Required arguments：显式 `--start` 与 `--end`。

Expected Study-owned artifacts：

```text
result.json
report.md
baseline.png
```

Method、statistics 与 limitations：[IM Annualized Basis Baseline authority](studies/im_annualized_basis_baseline/ARCHITECTURE.md)。

### `im-basis-forward-return-association`

Purpose：评估 IM 非近月整体年化基差与 CSI1000 后续 1/3/5/10/15/20 个交易 observation 收益的探索性关联。

```text
poetry run market-research run im-basis-forward-return-association --start 2024-01-01 --end 2026-01-01
```

Required arguments：显式 `--start` 与 `--end`。

Expected Study-owned artifacts：

```text
result.json
report.md
correlation_by_horizon.png
```

Method、sample rules 与 limitations：[IM Basis Forward Return Association authority](studies/im_basis_forward_return_association/ARCHITECTURE.md)。

## Adding a Runnable Study

每个新 runnable retained Study 必须在同一 change 中增加 Study authority、executable implementation、stable CLI ID、explicit dispatch、本文档条目及 CLI/output tests。CLI catalog 与本手册必须保持一致；不得通过 filesystem scanning、reflection 或 plugin 自动发现 Study。
