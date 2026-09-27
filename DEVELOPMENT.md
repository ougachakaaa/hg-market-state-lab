# Repository Development

本文档只描述当前本地开发环境与操作方式，不是架构、CLI、产品或 HTTP 语义 authority。Repository-level Python runtime invariant 与仓库级路由见 [ARCHITECTURE.md](ARCHITECTURE.md)，canonical CLI interface 与 delegation 见 [lab authority](lab/ARCHITECTURE.md)，产品语义从 [market-snapshot/CAPABILITIES.md](market-snapshot/CAPABILITIES.md) 进入，HTTP transport contract 从 [backend-api HTTP catalog](backend-api/HTTP_PRODUCTS.md) 进入。

正式 console command 是 `lab`，由根 canonical Python project 安装。以下命令在 repository root 的 Poetry environment 中运行。

## Codex managed worktree 环境

Codex 使用仓库内的 Local Environment 创建 managed worktree 时，会自动运行：

```bash
bash .codex/scripts/setup.sh
```

运行该脚本的 Bash 环境必须已经提供 `python3.13`、`poetry`、`node` 和 `npm`；脚本不安装或升级这些 machine-level tools。初始化流程必须从仓库根目录使用唯一的 `pyproject.toml` 与 `poetry.lock` 执行 `poetry install`，安装 frontend 依赖，然后运行 `poetry run lab doctor` 检查 readiness；不会启动服务、运行完整测试或调用 Tushare。

每个 worktree 分别使用自己的根 `.venv` 与 `web-ui/node_modules`，不与其他 worktree 共享依赖目录。所有 repository Python packages 与 Python tools 共用该根 `.venv`；module directory 不拥有独立 Poetry environment。Codex managed worktree 会按根目录 `.worktreeinclude` 复制 source checkout 中已忽略的 `market-snapshot/.env`；如果 source checkout 没有该文件，setup 从 `.env.example` 复制一份空模板，不会生成或猜测 secret。

手工执行 `git worktree add` 不会触发 Codex Local Environment，可以在新 worktree 根目录手工运行同一命令完成初始化。

## 当前可运行命令

```bash
poetry run lab doctor
poetry run lab serve backend
poetry run lab serve frontend
poetry run lab research list
poetry run lab research run <study-id> --help
```

安装环境已激活时可直接使用 `lab`；`poetry run lab` 会从根环境调用相同的 console script。

## 当前命令与状态

`doctor` 检查仓库结构、backend launcher、根 Poetry 虚拟环境中的 Python 3.13，以及 Node 和 npm。它报告默认本地地址 `127.0.0.1:8011` 的 backend 状态：未监听为 `stopped`，监听且 `/openapi.json` 有效为 `running / healthy`，否则为 `port occupied / unhealthy`。服务未启动是正常状态。若 `web-ui/package.json` 不存在，frontend 报告 `not initialized`；存在后检查默认 `127.0.0.1:5173` 是否监听，不要求专用 health endpoint。

`doctor` 在必要的仓库结构、backend launcher、Poetry 或 Python 3.13 条件不满足时非零退出；frontend 已初始化但 Node/npm 不可用时也非零退出。frontend 尚未初始化和服务停止本身不使 `doctor` 失败。检查只读，不创建虚拟环境、不安装依赖，也不调用 Tushare 或运行 pytest、Ruff、mypy。

`lab serve backend` 从 repository root 前台执行 `poetry run python backend-api/scripts/api.py`。`lab serve frontend` 在 `web-ui/` 前台执行 `npm run dev`；首次启动前需在 `web-ui/` 自行执行 `npm install`。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。

`lab research list` 列出可运行的 retained Study；`lab research run <study-id> --help` 转发到对应 Study 的帮助。Study ID、runner layout 与转发规则见 [Research UI authority](market-research/ui/ARCHITECTURE.md)，具体参数见对应 retained Study authority。

`web-ui/` 是独立 npm project，使用 Vite + React + TypeScript。Node.js 需满足当前 Vite 要求（20.19+ 或 22.12+）。`npm run dev` 在 `http://127.0.0.1:5173/` 提供可选择日期的 MO Option Chain 页面，与 `doctor` 的本地诊断地址一致；`npm run build` 执行 TypeScript 检查及 production build，`npm run lint` 运行 Oxlint，`npm run test` 运行前端测试。Vite dev proxy 将 frontend origin 的 `/mo-option-chain` 原路径和 query 转发到 `http://127.0.0.1:8011`，不需要 backend CORS policy。默认 provider 已接入真实读取链路；具体响应取决于目标日期与 Source 数据。

`lab doctor` 的 frontend 诊断地址与 Vite 显式绑定的 `127.0.0.1:5173` 一致。CLI ownership 以 [lab authority](lab/ARCHITECTURE.md) 为准。
