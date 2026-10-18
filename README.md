# hg-market-state-lab

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、市场状态建模与结果展示的实验性仓库。

```text
data-lake        → reusable source facts and Dataset-owned caches
market-snapshot  → market state data preparation
market-modeling  → market state modeling
market-research  → exploratory and statistical research
backend-api      → repository-wide HTTP inbound delivery and composition
web-ui           → presentation and interaction
```

## Authority 与开发文档

README 是人类开发入口，不是架构或业务语义 authority。

- 仓库架构、Python runtime invariant 与模块路由：[ARCHITECTURE.md](ARCHITECTURE.md)
- `lab` 使用、help discovery 与常见 workflow：[lab/README.md](lab/README.md)（usage-only）
- Canonical repository CLI 与委托边界：[lab/ARCHITECTURE.md](lab/ARCHITECTURE.md)
- DataLake Shared Kernel、自治 Dataset 与 consumer contract 入口：[data-lake/ARCHITECTURE.md](data-lake/ARCHITECTURE.md)
- `market-snapshot` 稳定分层：[market-snapshot/ARCHITECTURE.md](market-snapshot/ARCHITECTURE.md)
- `market-snapshot` capability/product catalog：[market-snapshot/CAPABILITIES.md](market-snapshot/CAPABILITIES.md)
- `market-research` exploratory/statistical research 边界：[market-research/ARCHITECTURE.md](market-research/ARCHITECTURE.md)
- `backend-api` HTTP boundary 与 product catalog：[backend-api/ARCHITECTURE.md](backend-api/ARCHITECTURE.md)
- `web-ui` 边界与 visualization 路由：[web-ui/ARCHITECTURE.md](web-ui/ARCHITECTURE.md)
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

Python package namespaces 保持独立，包括 `market_snapshot`、`market_modeling`、`market_research` 与 `backend_api`。共享环境不改变 module ownership 或 cross-module dependency rules。

Frontend 需要满足当前 Vite 要求的 Node.js 与 npm：

```bash
cd web-ui
npm install
```

本地 Source 访问凭据写入 `market-snapshot/.env`，可从 `.env.example` 复制模板：

```text
TUSHARE_TOKEN=<your-token>
```

`.env` 与运行产生的市场数据不进入版本控制。

## 当前根开发命令

正式 CLI 由根 canonical Python project 安装，从 repository root 使用。命令发现、服务启动、DataLake lifecycle 与 Research discovery 的可复制示例统一见 [lab usage guide](lab/README.md)；当前环境和 readiness 见 [DEVELOPMENT.md](DEVELOPMENT.md)，CLI contract 见 [lab authority](lab/ARCHITECTURE.md)。

## Research CLI

发现与查看 Study help 的操作见 [lab usage guide](lab/README.md)。Discovery 与 forwarding contract 见 [lab authority](lab/ARCHITECTURE.md) 和 [Research UI authority](market-research/ui/ARCHITECTURE.md)；Study-specific 参数和语义由对应 retained Study authority 拥有。真实运行所需的 Tushare credential 仍由 `market-snapshot` 拥有。

## HTTP API

HTTP transport 的 canonical owner 和 implementation owner 都是 [`backend-api`](backend-api/ARCHITECTURE.md)。在仓库根目录启动本地 backend：

```bash
poetry run python backend-api/scripts/api.py
poetry run python backend-api/scripts/api.py --host 127.0.0.1 --port 8012
```

默认地址为 `127.0.0.1:8011`，OpenAPI 位于 `/openapi.json`，交互文档位于 `/docs`。MO Option Chain 的 HTTP 契约见 [Option Chain authority](backend-api/products/mo_option_chain/http-contract.md)；MO Premium Plane 的 HTTP 契约见 [Premium Plane authority](backend-api/products/mo_option_premium/http-contract.md)。

## Web UI

在 `web-ui/` 目录执行：

```bash
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173/`。Vite 将 `/mo-option-chain` 转发到默认 backend 地址；具体视觉与交互语义见 [MO Option Chain visualization authority](web-ui/src/features/mo_option_chain/ARCHITECTURE.md)。

## 验证命令

Market Snapshot（在 repository root）：

```bash
poetry run pytest market-snapshot/tests
poetry run ruff check market-snapshot
poetry run mypy market-snapshot
```

Backend API（在 repository root）：

```bash
poetry run pytest backend-api/tests
poetry run ruff check backend-api
poetry run mypy backend-api
```

Frontend（在 `web-ui/`）：

```bash
npm run contract:check
npm run test
npm run build
npm run lint
```

`npm run contract:generate` 从 `backend-api` 发布的 product OpenAPI 生成各 consuming feature 自己提交的 OpenAPI representation 与 TypeScript contract；`npm run contract:check` 检查所有 frontend-consumed products 的 committed artifacts 是否可确定性重现。只有 generated artifact 缺失、stale 或 backend HTTP DTO/OpenAPI 改变时才提交生成结果。
