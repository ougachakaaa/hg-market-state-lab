# Research UI authority

本文档定义 `market-research` 的 human-facing inbound interaction boundary：Research CLI。模块 identity、Research result 与 Snapshot 消费原则见 [market-research architecture](../ARCHITECTURE.md)；配置 schema 与 resolution 见 [configuration authority](CONFIGURATION.md)；面向用户的命令与 Study 目录见 [command manual](../COMMANDS.md)。

## 1. Identity 与职责

Research CLI 的 canonical namespace 是：

```text
poetry run market-research ...
```

它负责 study discovery、command parsing、user input validation、configuration loading、dependency composition、Study invocation、output-directory resolution 与 success/failure presentation。它只把用户意图映射到已有 retained Study application behavior，不拥有：

```text
Snapshot Source/Capture semantics
basis formulas or Research statistics
Study Method or artifact contents
Modeling / Forecasting / Decision
HTTP API or production Web UI
```

Research visualization 继续由 Study 以 Python static output 产生；CLI 只报告生成文件的位置，不拥有 chart semantics，也不提供 plot/PNG configuration options。

## 2. V1 commands

V1 只有一个 executable namespace，不为每个 Study 创建独立 executable：

```text
market-research list
market-research config
market-research run <study-id> --start YYYY-MM-DD --end YYYY-MM-DD [--overwrite]
```

- `list` 只输出所有 runnable retained Study 的 stable ID 与 short description，不读取 Source，也不执行 Study。
- `config` 只输出实际加载的 config source 与 resolved absolute output root；不得输出 credential、token 或 Source configuration。
- `run` 选择一个显式 Study，校验 required `--start` 与 `--end`，调用 Snapshot public application boundary，再执行并保留 Study output。

`start` 与 `end` 是含端点的显式 ISO `YYYY-MM-DD` date。CLI 不从 Research config、当前日期、`latest` 或隐藏默认值推导日期；无效格式或 `start > end` 在 Source 调用前失败。

V1 不定义 interactive prompt、wizard、TUI、Web UI、background execution、scheduler 或 debug/traceback mode。

## 3. Stable Study IDs 与 explicit catalog

V1 runnable catalog 固定为：

| Study ID | Short description | Retained Study authority |
| --- | --- | --- |
| `im-basis-baseline` | 描述 IM 各期限槽及非近月整体年化基差的历史分布 | [IM Annualized Basis Baseline](../studies/im_annualized_basis_baseline/ARCHITECTURE.md) |
| `im-basis-forward-return-association` | 评估非近月整体年化基差与 CSI1000 后续收益的探索性关联 | [IM Basis Forward Return Association](../studies/im_basis_forward_return_association/ARCHITECTURE.md) |

Study ID 是稳定的 public UI routing identity，不替代 Study semantic name、Python module name、result type 或 authority identity；implementation class/function rename 不得顺带改变 ID。

实现可以拥有仅含 `study-id + short description + execution adapter` 的窄义显式 catalog。该 catalog 不是 semantic source of truth、Study/Experiment Registry、Research Repository 或 plugin architecture。V1 禁止 filesystem scanning、reflection、entry-point plugin 或动态 registry 自动发现 Study。

新增 runnable retained Study 必须在同一 change 中具备：

1. retained Study authority；
2. executable Study implementation；
3. stable CLI study ID；
4. explicit CLI dispatch entry；
5. `COMMANDS.md` entry；
6. CLI/output tests。

只有多个真实 Study 证明动态 registration 必要后，才可通过新的 authority decision 重设该策略。

## 4. Snapshot composition boundary

CLI 为 Study 组合依赖，但不得自行组合 Snapshot Source internals：

```text
Research CLI
    ↓ semantic request
CSI1000 IM Basis History production-ready public application entry
    ↓ semantic result or classified application failure
Retained Study
```

`TUSHARE_TOKEN`、`.env`、Tushare client 创建、Capture 与 Preparation composition 均由 Snapshot boundary 拥有。Research UI 不得导入 `market_snapshot.sources`、重复读取 credential，或要求用户在 Research config 中提供 token。对应 Snapshot contract 见 [CSI1000 IM Basis History read/application contract](../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/read-contract.md)。

## 5. Output placement 与 ownership

Research UI configuration 只提供 `output.root`。CLI 为每次 run 确定：

```text
<output-root>/
└── <study-id>/
    └── <start_trade_date>__<end_trade_date>/
```

同一个 `study-id + start + end` 永远映射到同一个 canonical run directory。CLI 把该目录作为 `output_dir` 交给 Study；Study 继续独占目录内 artifact filenames、contents、result/report/plot semantics。

若 canonical run directory 已存在，默认在调用 Snapshot 或 Study 前清晰失败，不修改已有 evidence。只有显式 `--overwrite` 才允许替换；replacement 以整个 canonical run directory 为单位，先移除旧目录再创建新目录，不与旧文件 merge，避免 stale artifact。输出目录创建、替换或写入失败属于 output filesystem failure。

## 6. Presentation 与 failure

成功的 `run` 至少报告：

```text
Study completed
Study ID
requested inclusive date range
resolved absolute output directory
main generated artifacts
```

完整统计结果保留在 Study 的 machine-readable result、`report.md` 与 visualization 中，不要求全部打印到 terminal。

正常用户错误必须转换为简洁消息与 non-zero exit code，概念上区分：

```text
command/input failure
configuration failure
Snapshot/data acquisition failure
Study/sample failure
output filesystem failure
```

V1 不锁定各类别的具体 exit-code number，但不得要求用户阅读 Python traceback 才能识别失败类别。

## 7. Root development CLI boundary

Root `dev.py` 继续只拥有 repository local-development convenience commands，例如 `doctor`、`backend`、`frontend` 与 `data`。Research Study 的 canonical UI 是 `poetry run market-research ...`。

V1 不增加 `dev.py research`。未来若增加，它只能原样 forward 到 canonical Research CLI，不得拥有独立 Study catalog、configuration rule、output placement 或 Study semantics。

## 8. Strict non-goals

```text
CLI implementation or config loader implementation in this authority change
Web Research Viewer / TUI / interactive wizard
HTTP Research API or generic UI framework
dynamic Study plugin system
generic repository configuration framework
database / queue / background execution / scheduler
run registry / artifact registry / result browser
```
