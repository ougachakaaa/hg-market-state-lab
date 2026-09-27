# hg-market-state-lab

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、市场状态建模与结果展示的实验性仓库。

```text
market-snapshot  → market state data preparation
market-modeling  → market state modeling
market-research  → exploratory and statistical research
backend-api      → repository-wide HTTP inbound delivery and composition
web-ui           → presentation and interaction
```

## Authority 与开发文档

README 是人类开发入口，不是架构或业务语义 authority。

- 仓库架构、Python runtime invariant 与模块路由：[ARCHITECTURE.md](ARCHITECTURE.md)
- Canonical repository CLI 与委托边界：[lab/ARCHITECTURE.md](lab/ARCHITECTURE.md)
- `market-snapshot` 稳定分层：[market-snapshot/ARCHITECTURE.md](market-snapshot/ARCHITECTURE.md)
- `market-snapshot` capability/product catalog：[market-snapshot/CAPABILITIES.md](market-snapshot/CAPABILITIES.md)
- `market-research` exploratory/statistical research 边界：[market-research/ARCHITECTURE.md](market-research/ARCHITECTURE.md)
- `backend-api` HTTP boundary 与 product catalog：[backend-api/ARCHITECTURE.md](backend-api/ARCHITECTURE.md)
- `web-ui` 边界与 visualization 路由：[web-ui/ARCHITECTURE.md](web-ui/ARCHITECTURE.md)
- 根开发命令与 managed worktree 说明：[DEVELOPMENT.md](DEVELOPMENT.md)

任何字段、公式、null/zero、HTTP 或可视化语义均以 catalog 所链接的 canonical authority 为准。

## 环境准备

所有 Python packages 使用根目录唯一的 project、dependency graph、lock 与 worktree-local `.venv`。需要 Python 3.13 与 Poetry，并在仓库根目录执行：

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

目标 CLI 是 `lab`；console-script wiring 尚未实施。当前在仓库根目录执行：

```bash
poetry run python dev.py doctor
poetry run python dev.py backend
poetry run python dev.py frontend
poetry run python dev.py research list
```

目标命令层级见 [lab CLI authority](lab/ARCHITECTURE.md)；当前操作和 readiness 见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## Research CLI

在 repository root 发现并运行 retained Study：

```bash
poetry run python dev.py research list
poetry run python dev.py research run im-basis-baseline --help
```

目标 `lab research` 的 discovery 与 forwarding 行为见 [lab CLI authority](lab/ARCHITECTURE.md) 和 [Research UI authority](market-research/ui/ARCHITECTURE.md)。上面的 `dev.py` 示例仍是当前可运行方式。Study-specific 参数和用法与对应 retained Study authority 共置，并由 `<study-id> --help` 展示。真实运行所需的 Tushare credential 仍由 `market-snapshot` 拥有。

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
