# market_backtesting Agent Rules

继承根 [AGENTS.md](../AGENTS.md)。先读 [repository architecture](../ARCHITECTURE.md)
与 [module architecture](ARCHITECTURE.md)，再按任务进入最窄 case authority。

## 最小 Authority 路径

| Task | Next authority |
| --- | --- |
| Module ownership、依赖方向、case 边界 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Case identity、request、strategy profile、scope/status | [Futures Roll Long case](cases/futures_roll_long/ARCHITECTURE.md) |
| Real-contract position、entry/hold/roll/exit、contract vs slot、failure matrix | [Strategy](cases/futures_roll_long/STRATEGY.md) |
| Initial notional、daily PnL、benchmark、returns、equity、drawdown | [Accounting](cases/futures_roll_long/ACCOUNTING.md) |
| DataLake public bindings、completeness、W1 slot 复用、fingerprint/readiness | [Inputs](cases/futures_roll_long/INPUTS.md) |
| BacktestResult、evidence、limitations、V2 projection | [Result](cases/futures_roll_long/RESULT.md) |
| Online request、run lifecycle、store、concurrency、HTTP/Web ownership | [Online application](cases/futures_roll_long/ONLINE_APPLICATION.md) |
| WP0–WP8、acceptance、reconciliation、deferred | [Roadmap](cases/futures_roll_long/ROADMAP.md) |

## 执行规则

- `market_backtesting` 只实现当前已确认的 `futures_roll_long_v1`；不得预先建立
  generic strategy engine、plugin/registry、multi-strategy portfolio、optimizer 或未来
  strategy abstraction。
- Strategy/accounting/input/result/online 语义分别只属于上述 narrowest authority。
  修改行为前先更新对应 authority；下层只能 specialize 或 constrain 上层 invariant。
- 不修改 W1 Research 的代码、公式或 public contract。只允许通过 case Inputs 明确列出的
  pure Slot resolution symbols 复用；不得复制第二份 Slot Resolution 算法，也不得消费
  Research Observation / Report / Statistics / Publication / Online run。
- 只通过 DataLake public Application Service 获取市场事实；不得访问 Dataset SQLite、
  private Repository、Source adapter、provider client 或建立第二套行情缓存/Provider。
- 不得静默跳日、补价、猜测到期日、替换合约、reuse W1 basis/annualized basis，或在
  React/HTTP DTO 中重算金融结果。
- Online run 是本 case 独立的应用执行状态；不得复用 W1 run identity/store，不得把它
  当作 Publication、ResearchPlan/Job/Batch 或 Workbench Run。
- 涉及数据含义、输出结构、职责边界或 workflow 语义的变更，先更新 narrowest canonical
  authority，再修改实现；发现 authority 与代码不一致时必须显式 reconciliation。
- 所有 Python tooling 从 repository root 使用唯一根环境；module directory 不建立
  module-local `.env` / `.venv` / Poetry project。

## 验证

WP0 是 authority-only：只运行 Markdown links/anchors/reachability、topology 检查与
`git diff --check`，不要求 Python/HTTP/Web 测试矩阵。

WP1 起在 repository root 按影响范围运行：

```bash
poetry run pytest market_backtesting/tests
poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py
poetry run ruff check market_backtesting
poetry run mypy market_backtesting
git diff --check
```

跨模块 contract 变更同时执行 producer 与 consumer 的相关检查；WP6/WP7 还必须执行
`ui_http` / `ui_web` 的 contract 与浏览器验证。不得用 synthetic fixture 代替 WP8 的
real-market acceptance，也不得声称未运行的矩阵已 PASS。
