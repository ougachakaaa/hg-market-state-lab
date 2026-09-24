# hg-market-state-lab

`hg-market-state-lab` 是用于市场状态数据准备、市场状态建模与结果展示的实验性仓库。

```text
market-snapshot  → market state data preparation
market-modeling  → market state modeling
web-ui           → presentation and interaction
```

## Authority 与开发文档

README 是人类开发入口，不是架构或业务语义 authority。

- 仓库架构与模块路由：[ARCHITECTURE.md](ARCHITECTURE.md)
- `market-snapshot` 稳定分层：[market-snapshot/ARCHITECTURE.md](market-snapshot/ARCHITECTURE.md)
- `market-snapshot` capability/product catalog：[market-snapshot/CAPABILITIES.md](market-snapshot/CAPABILITIES.md)
- `web-ui` 边界与 visualization 路由：[web-ui/ARCHITECTURE.md](web-ui/ARCHITECTURE.md)
- 根开发命令与 managed worktree 说明：[DEVELOPMENT.md](DEVELOPMENT.md)

任何字段、公式、null/zero、HTTP 或可视化语义均以 catalog 所链接的 canonical authority 为准。

## 环境准备

Backend 需要 Python 3.13 与 Poetry：

```bash
cd market-snapshot
poetry install
```

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

## 根开发入口

在仓库根目录执行：

```bash
python dev.py doctor
python dev.py backend
python dev.py frontend
```

命令转发、readiness 和失败行为见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## Data Service CLI

在 `market-snapshot/` 目录执行：

```bash
poetry run python scripts/dms.py list
poetry run python scripts/dms.py get csi1000-5d-analysis --date 2026-09-18
```

CLI、service orchestration 与 output contract 见 [Data Service authority](market-snapshot/src/daily_market_snapshot/services/ARCHITECTURE.md)。产品数据语义从 [Capability Catalog](market-snapshot/CAPABILITIES.md) 进入。

## HTTP API

在 `market-snapshot/` 目录启动本地 backend：

```bash
poetry run python scripts/api.py
poetry run python scripts/api.py --host 127.0.0.1 --port 8012
```

默认地址为 `127.0.0.1:8011`，OpenAPI 位于 `/openapi.json`，交互文档位于 `/docs`。MO Option Chain 的 endpoint、query、response 与错误契约见 [HTTP authority](market-snapshot/src/daily_market_snapshot/products/mo_option_chain/http-contract.md)。

## Web UI

在 `web-ui/` 目录执行：

```bash
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173/`。Vite 将 `/mo-option-chain` 转发到默认 backend 地址；具体视觉与交互语义见 [MO Option Chain visualization authority](web-ui/src/features/mo_option_chain/ARCHITECTURE.md)。

## 验证命令

Backend（在 `market-snapshot/`）：

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy .
```

Frontend（在 `web-ui/`）：

```bash
npm run contract:check
npm run test
npm run build
npm run lint
```

修改 backend HTTP DTO/OpenAPI 后，在 `web-ui/` 运行 `npm run contract:generate` 并提交更新后的 OpenAPI JSON 与生成类型，再执行上述检查。
