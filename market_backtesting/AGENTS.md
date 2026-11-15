# market_backtesting Agent Rules

继承根 [AGENTS.md](../AGENTS.md)。先读 [repository architecture](../ARCHITECTURE.md)
与 [module architecture](ARCHITECTURE.md)，再按任务进入最窄 case authority。

## 最小 Authority 路径

| Task | Next authority |
| --- | --- |
| Module ownership、依赖方向、case 边界 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Replay、Portfolio、Transition、Daily PnL、累计核算 | [Core](core/ARCHITECTURE.md) |
| Case identity、request、strategy profile、scope/status | [Futures Roll Long case](cases/futures_roll_long/ARCHITECTURE.md) |
| Real-contract position、entry/hold/roll/exit、contract vs slot、failure matrix | [Strategy](cases/futures_roll_long/STRATEGY.md) |
| Initial notional、benchmark、drawdown、case performance | [Performance](cases/futures_roll_long/PERFORMANCE.md) |
| DataLake public bindings、completeness、W1 slot 复用、fingerprint/readiness | [Inputs](cases/futures_roll_long/INPUTS.md) |
| BacktestResult、evidence、limitations、V2 projection | [Result](cases/futures_roll_long/RESULT.md) |
| Portable evidence package、encoding、pure offline reproduction | [Evidence](cases/futures_roll_long/EVIDENCE.md) |
| Online request、run lifecycle、store、concurrency、HTTP/Web ownership | [Online application](cases/futures_roll_long/ONLINE_APPLICATION.md) |
| 当前状态、剩余 WP、acceptance、deferred | [Roadmap](cases/futures_roll_long/ROADMAP.md) |
| 当前职责映射、语义审查、Implementation Drift | [Reconciliation](cases/futures_roll_long/RECONCILIATION.md) |
| Actual real-market、HTTP、Windows Chrome 执行证据 | [WP8 acceptance](cases/futures_roll_long/WP8_ACCEPTANCE.md) |

## 执行规则

- `market_backtesting` 只实现当前已确认的 `futures_roll_long_v1`；不得预先建立
  order-driven trading framework、broker/matching、plugin/registry、multi-strategy portfolio、optimizer 或未来
  strategy scaffold；允许 [Core V1](core/ARCHITECTURE.md) 明确授权的策略无关日频回放。
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

## Scoped verification

Follow the [root verification policy](../AGENTS.md#verification-policy-user-decision-2026-11-14).
Select only directly affected business test files/cases. No default full-module or
cross-module regression, topology, browser, live-data or deployment acceptance.
Retain business invariants and fixtures; record unavailable checks as NOT VERIFIED.
Do not modify real market data or caches to satisfy tests.
