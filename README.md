# hg-market-state-lab

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、市场状态建模与结果展示的实验性仓库。

```text
data_lake         → reusable source facts and Dataset-owned caches
data_snapshot     → market state data preparation
market_modeling   → market state modeling (reserved; no module authority yet)
market_research   → exploratory and statistical research
market_backtesting → futures roll long strategy backtesting (W2; WP1 pure holding simulation)
market_statistics → independent numerical statistics Python API
ui_cli            → repository CLI (lab)
ui_http           → repository-wide HTTP inbound delivery and composition
ui_web            → presentation and interaction
```

## Canonical module layout

Directories and imports follow [repository authority](ARCHITECTURE.md#naming-and-transition-authority). Run directly with canonical paths: local runtime state is disposable and has no migration or compatibility mechanism. Configure credentials and runtime settings in the current environment or the repository-root `.env` as needed. The executable remains `lab`.

## Authority 与开发文档

README 是人类开发入口，不是架构或业务语义 authority。

Agent-facing Task / Run / Gate contracts and local evidence storage start at the
[Workbench usage guide](workbench/README.md) and [agent entry](workbench/AGENTS.md).
Workbench is a repository-root operational facility, separate from the modules above.

- 仓库架构、Python runtime invariant 与模块路由：[ARCHITECTURE.md](ARCHITECTURE.md)
- `lab` 使用、help discovery 与常见 workflow：[ui_cli/README.md](ui_cli/README.md)（usage-only）
- Canonical repository CLI 与委托边界：[ui_cli/ARCHITECTURE.md](ui_cli/ARCHITECTURE.md)
- DataLake Shared Kernel、自治 Dataset 与 consumer contract 入口：[data_lake/ARCHITECTURE.md](data_lake/ARCHITECTURE.md)
- `data_snapshot` 稳定分层：[data_snapshot/ARCHITECTURE.md](data_snapshot/ARCHITECTURE.md)
- `data_snapshot` capability/product catalog：[data_snapshot/CAPABILITIES.md](data_snapshot/CAPABILITIES.md)
- `market_research` exploratory/statistical research 边界：[market_research/ARCHITECTURE.md](market_research/ARCHITECTURE.md)
- `market_backtesting` 策略回测边界与 W2 case authority：[market_backtesting/ARCHITECTURE.md](market_backtesting/ARCHITECTURE.md)
- `market_statistics` 独立数值统计边界：[market_statistics/ARCHITECTURE.md](market_statistics/ARCHITECTURE.md)
- `ui_http` HTTP boundary 与 product catalog：[ui_http/ARCHITECTURE.md](ui_http/ARCHITECTURE.md)
- `ui_web` 边界与 visualization 路由：[ui_web/ARCHITECTURE.md](ui_web/ARCHITECTURE.md)
- 根开发命令与 managed worktree 说明：[DEVELOPMENT.md](DEVELOPMENT.md)

任何字段、公式、null/zero、HTTP 或可视化语义均以 catalog 所链接的 canonical authority 为准。

## 环境准备

所有 Python packages 使用根目录唯一的 project、dependency graph、lock 与 worktree-local `.venv`。需要 Python 3.13 与 Poetry，并在仓库根目录执行：

Linux 或 WSL：

```bash
bash .codex/scripts/setup.sh
```

Windows native PowerShell：

```powershell
.\.codex\scripts\setup.ps1
```

两个 bootstrap 都安装根 Python project 与 frontend 依赖，并运行 `lab doctor`。若只需手工安装 Python project，可在仓库根目录执行：

```bash
poetry install
```

Python packages 由各 owning module 独立拥有，canonical namespace 见 [repository architecture](ARCHITECTURE.md#3-python-runtime-与-module-boundary)。共享环境不改变 module ownership 或 cross-module dependency rules。每个 worktree 只使用根 `.venv`；module 目录不拥有独立 `.venv` 或 `.env`。

Frontend 需要满足当前 Vite 要求的 Node.js 与 npm：

```bash
cd ui_web
npm install
```

本地 Source 访问凭据与 runtime 配置统一写入 **repository root `.env`**，可从根 `.env.example` 复制模板：

```text
TUSHARE_TOKEN=<your-token>
```

process environment 优先于 `.env`。`.env` 与运行产生的市场数据不进入版本控制；不要在 module 目录建立独立 `.env`。完整 key 与 Auth 配置见 [Repository configuration](DEVELOPMENT.md#repository-configuration)。

## 当前根开发命令

正式 CLI 由根 canonical Python project 安装，从 repository root 使用。命令发现、服务启动与 DataLake lifecycle 的可复制示例统一见 [lab usage guide](ui_cli/README.md)；当前环境和 readiness 见 [DEVELOPMENT.md](DEVELOPMENT.md)，CLI contract 见 [lab authority](ui_cli/ARCHITECTURE.md)。

Windows 上可直接双击仓库根目录的 `market-lab.cmd`，或在仓库根运行 `.\market-lab.cmd start` 一键启动 backend 与 Web；`market-lab.cmd stop` 停止服务，`market-lab.cmd status` 查看状态。实际逻辑位于 `scripts/market-lab.ps1`。原生 Windows 下 Publication 存储返回 503，完整 Publication 需 Linux/WSL。前置条件、审批与日志说明见 [Windows One-Click Development Startup](DEVELOPMENT.md#windows-one-click-development-startup)。

Linux/WSL 可运行 `bash scripts/market-lab.sh start` 一键启动；`status` 查看状态，`stop` 从另一终端停止服务。前置条件与日志说明见 [Linux One-Click Development Startup](DEVELOPMENT.md#linux-one-click-development-startup)。

## Research status

Start with the stable [Research human/agent usage guide](market_research/USAGE.md).
One admitted descriptive capability is discoverable through the existing backend;
its [HTTP contract](ui_http/products/research/http-contract.md) owns the four operations.
Current checks, bounded real-market evidence and release limits are in [Research acceptance and validation evidence](market_research/descriptive/ACCEPTANCE.md).

The [Research semantic foundation](market_research/ARCHITECTURE.md) starts with
Descriptive Research. The independent Python [Single Job Executor](market_research/descriptive/JOB_EXECUTION.md)
composes Observation, conversion, Statistics and association. Previous execution packages
and CLI commands are retired. [ResearchPlan / Batch execution](market_research/descriptive/BATCH_EXECUTION.md)
composes the same Single Job operation with full preflight and continue/stop accounting;
[deterministic examples](market_research/README.md#batch-execution) use public-service fakes.

Research owns observation, sample conversion, execution and interpretation; the independent
[Statistics authority](market_statistics/ARCHITECTURE.md) owns generic numerical statistics.
Statistics publishes an independently installed Python API for Quantile and IntervalCount;
see [public examples](market_statistics/README.md). It has no CLI or HTTP service.

## Backtesting status

W2 Futures Roll Long has completed WP1 Strategy & Holding Simulation: a pure Python
boundary resolves real-contract entry, holding, expiry rolls and final exit from
validated synthetic facts, with both `expiry_to_M1_v1` and `expiry_to_Q1_v1`. There is
still no PnL/accounting (WP2), DataLake integration (WP3), result/evidence (WP4),
online run (WP5), HTTP product (WP6) or Web workflow (WP7); `/backtesting` remains a
planned page with no results. Start from the [W2 case authority](market_backtesting/cases/futures_roll_long/ARCHITECTURE.md)
and its [roadmap](market_backtesting/cases/futures_roll_long/ROADMAP.md). Backtesting is
not a Research capability, Publication or Workbench Run.

## HTTP API

HTTP transport 的 canonical owner 和 implementation owner 都是 [`ui_http`](ui_http/ARCHITECTURE.md)。在仓库根目录启动本地 backend：

```bash
poetry run python ui_http/scripts/api.py
poetry run python ui_http/scripts/api.py --host 127.0.0.1 --port 8012
```

启动前按 [Auth 本机配置](DEVELOPMENT.md) 设置 `LAB_AUTH_JWT_SECRET`、`LAB_AUTH_MODE` 和 `LAB_AUTH_ORIGIN`。所有业务 API、OpenAPI 和交互文档都要求有效登录 Cookie；注册需经 `lab auth approve` 审批，Web 登录/注册流程见 [浏览器注册、审批与登录](DEVELOPMENT.md#浏览器注册审批与登录)。

默认地址为 `127.0.0.1:8011`，OpenAPI 位于 `/openapi.json`，交互文档位于 `/docs`。MO Option Chain 的 HTTP 契约见 [Option Chain authority](ui_http/products/mo_option_chain/http-contract.md)；MO Premium Plane 的 HTTP 契约见 [Premium Plane authority](ui_http/products/mo_option_premium/http-contract.md)。

## Web UI

在 `ui_web/` 目录执行：

```bash
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173/`；登录后进入 `/research` 工作台。Vite 将 `/api/research/*`（去除 `/api` 前缀）、`/auth`、`/mo-option-chain` 与 `/mo-option-premium-plane` 转发到默认 backend 地址；部署网关也需同样转发 `/api` 并为页面路由提供 SPA fallback。导航见 [Workspace authority](ui_web/workspace.md)。

## 验证命令

Data Snapshot（在 repository root）：

```bash
poetry run pytest data_snapshot/tests
poetry run ruff check data_snapshot
poetry run mypy data_snapshot
```

HTTP API（在 repository root）：

```bash
poetry run pytest ui_http/tests
poetry run ruff check ui_http
poetry run mypy ui_http
```

Frontend（在 `ui_web/`）：

```bash
npm run contract:check
npm run test
npm run build
npm run lint
```

`npm run contract:generate` 从 `ui_http` 发布的 product OpenAPI 生成各 consuming feature 自己提交的 OpenAPI representation 与 TypeScript contract；`npm run contract:check` 检查所有 frontend-consumed products 的 committed artifacts 是否可确定性重现。只有 generated artifact 缺失、stale 或 backend HTTP DTO/OpenAPI 改变时才提交生成结果。
