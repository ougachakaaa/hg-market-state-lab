# hg-market-state-lab

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、市场状态建模与结果展示的实验性仓库。

```text
data_lake        → reusable source facts and Dataset-owned caches
data_snapshot    → market state data preparation
market_modeling  → market state modeling
market_research  → exploratory and statistical research
market_analyze   → generic numerical statistics (authority only)
ui_cli           → repository CLI (lab)
ui_http          → repository-wide HTTP inbound delivery and composition
ui_web           → presentation and interaction
```

## Canonical module layout

Directories, imports and disposable local runtime state follow [repository authority](ARCHITECTURE.md#naming-and-transition-authority). Run directly with canonical paths; no local data or token migration is required. Configure credentials in the current environment or `data_snapshot/.env` as needed. The executable remains `lab`.

## Authority 与开发文档

README 是人类开发入口，不是架构或业务语义 authority。

- 仓库架构、Python runtime invariant 与模块路由：[ARCHITECTURE.md](ARCHITECTURE.md)
- `lab` 使用、help discovery 与常见 workflow：[ui_cli/README.md](ui_cli/README.md)（usage-only）
- Canonical repository CLI 与委托边界：[ui_cli/ARCHITECTURE.md](ui_cli/ARCHITECTURE.md)
- DataLake Shared Kernel、自治 Dataset 与 consumer contract 入口：[data_lake/ARCHITECTURE.md](data_lake/ARCHITECTURE.md)
- `data_snapshot` 稳定分层：[data_snapshot/ARCHITECTURE.md](data_snapshot/ARCHITECTURE.md)
- `data_snapshot` capability/product catalog：[data_snapshot/CAPABILITIES.md](data_snapshot/CAPABILITIES.md)
- `market_research` exploratory/statistical research 边界：[market_research/ARCHITECTURE.md](market_research/ARCHITECTURE.md)
- `market_analyze` 独立数值统计边界（仅 authority）：[market_analyze/ARCHITECTURE.md](market_analyze/ARCHITECTURE.md)
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

Python package namespaces 保持独立，包括 `data_snapshot`、`market_modeling`、`market_research` 与 `ui_http`。共享环境不改变 module ownership 或 cross-module dependency rules。

Frontend 需要满足当前 Vite 要求的 Node.js 与 npm：

```bash
cd ui_web
npm install
```

本地 Source 访问凭据写入 `data_snapshot/.env`，可从 `.env.example` 复制模板：

```text
TUSHARE_TOKEN=<your-token>
```

`.env` 与运行产生的市场数据不进入版本控制。

## 当前根开发命令

正式 CLI 由根 canonical Python project 安装，从 repository root 使用。命令发现、服务启动与 DataLake lifecycle 的可复制示例统一见 [lab usage guide](ui_cli/README.md)；当前环境和 readiness 见 [DEVELOPMENT.md](DEVELOPMENT.md)，CLI contract 见 [lab authority](ui_cli/ARCHITECTURE.md)。

## Research status

The [Research semantic foundation](market_research/ARCHITECTURE.md) starts with
Descriptive Research. Previous execution packages and CLI commands are retired;
no Research execution capability is currently published.

Research owns observation, sample conversion, execution and interpretation; the independent
[Analyze authority](market_analyze/ARCHITECTURE.md) owns generic numerical statistics.
Analyze currently has no runnable Python package, installed API, CLI or HTTP service.

## HTTP API

HTTP transport 的 canonical owner 和 implementation owner 都是 [`ui_http`](ui_http/ARCHITECTURE.md)。在仓库根目录启动本地 backend：

```bash
poetry run python ui_http/scripts/api.py
poetry run python ui_http/scripts/api.py --host 127.0.0.1 --port 8012
```

默认地址为 `127.0.0.1:8011`，OpenAPI 位于 `/openapi.json`，交互文档位于 `/docs`。MO Option Chain 的 HTTP 契约见 [Option Chain authority](ui_http/products/mo_option_chain/http-contract.md)；MO Premium Plane 的 HTTP 契约见 [Premium Plane authority](ui_http/products/mo_option_premium/http-contract.md)。

## Web UI

在 `ui_web/` 目录执行：

```bash
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173/`。Vite 将 `/mo-option-chain` 转发到默认 backend 地址；具体视觉与交互语义见 [MO Option Chain visualization authority](ui_web/src/features/mo_option_chain/ARCHITECTURE.md)。

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
