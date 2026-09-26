# Repository Development CLI

本文档只描述本地开发编排与操作方式，不是架构、产品或 HTTP 语义 authority。仓库级路由见 [ARCHITECTURE.md](ARCHITECTURE.md)，产品语义从 [market-snapshot/CAPABILITIES.md](market-snapshot/CAPABILITIES.md) 进入，HTTP transport contract 从 [backend-api HTTP catalog](backend-api/HTTP_PRODUCTS.md) 进入。

仓库根目录的 `dev.py` 是本地开发入口，只负责检查启动条件和转发模块自己的命令。它是 developer orchestration surface 和 repository-level convenience forwarding surface，不是 Data Service、部署工具或新的业务模块。

## Codex managed worktree 环境

Codex 使用仓库内的 Local Environment 创建 managed worktree 时，会自动运行：

```bash
bash .codex/scripts/setup.sh
```

运行该脚本的 Bash 环境必须已经提供 `python3.13`、`poetry`、`node` 和 `npm`；脚本不安装或升级这些 machine-level tools。它使用已提交的 lock files 安装 backend 与 frontend 依赖，然后运行 `python3.13 dev.py doctor` 检查 readiness；不会启动服务、运行完整测试或调用 Tushare。

每个 worktree 分别使用自己的 `market-snapshot/.venv`、`backend-api/.venv` 和 `web-ui/node_modules`，不与其他 worktree 共享依赖目录。Codex managed worktree 会按根目录 `.worktreeinclude` 复制 source checkout 中已忽略的 `market-snapshot/.env`；如果 source checkout 没有该文件，setup 从 `.env.example` 复制一份空模板，不会生成或猜测 secret。

手工执行 `git worktree add` 不会触发 Codex Local Environment，可以在新 worktree 根目录手工运行同一命令完成初始化。

```bash
python dev.py doctor
python dev.py backend
python dev.py frontend
python dev.py data csi1000-5d-analysis
python dev.py data csi1000-5d-analysis --date 2026-09-18
```

## 命令与状态

`doctor` 检查仓库结构、backend launcher、两个 Poetry 虚拟环境中的 Python 3.13，以及 Node 和 npm。它报告默认本地地址 `127.0.0.1:8011` 的 backend 状态：未监听为 `stopped`，监听且 `/openapi.json` 有效为 `running / healthy`，否则为 `port occupied / unhealthy`。服务未启动是正常状态。若 `web-ui/package.json` 不存在，frontend 报告 `not initialized`；存在后检查默认 `127.0.0.1:5173` 是否监听，不要求专用 health endpoint。

`doctor` 在必要的仓库结构、backend launcher、Poetry 或 Python 3.13 条件不满足时非零退出；frontend 已初始化但 Node/npm 不可用时也非零退出。frontend 尚未初始化和服务停止本身不使 `doctor` 失败。检查只读，不创建虚拟环境、不安装依赖，也不调用 Tushare 或运行 pytest、Ruff、mypy。

`backend` 在 `backend-api/` 前台执行 `poetry run python scripts/api.py`。`frontend` 在 `web-ui/` 前台执行 `npm run dev`；首次启动前需在 `web-ui/` 自行执行 `npm install`。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。

`data` 是 repository-level Data Service convenience command：

```text
python dev.py data <service_id> [--date YYYY-MM-DD]
```

`service_id` 必须显式提供，当前只接受 CLI-supported persisted-artifact Data Service `csi1000-5d-analysis`；`mo-option-chain` 的 canonical delivery surface 是 HTTP，不由此命令暴露。显式提供 `--date` 时，值原样作为 `target_trade_date` 转发。未提供时，使用 UTC+8 / `Asia/Shanghai` 的当天自然日，格式为 `YYYY-MM-DD`。

该默认值只属于 repository convenience CLI，并且 `today != latest trading day`：`dev.py` 不查询交易日历、不寻找最近交易日，也不在周末、节假日或数据未就绪时 fallback。上述情况保持底层 Data Service 的失败语义。

`data` 在 `market-snapshot/` 前台执行：

```text
poetry run python scripts/dms.py get <service_id> --date <resolved-date>
```

它继承标准输入输出并传递子进程退出码。`dms get <service_id> --date YYYY-MM-DD` 仍是 canonical Data Service interface，其 `--date` 仍必须显式提供；`dev.py` 只在调用前解析 convenience default，不成为 Data Service semantic owner。

`web-ui/` 是独立 npm project，使用 Vite + React + TypeScript。Node.js 需满足当前 Vite 要求（20.19+ 或 22.12+）。`npm run dev` 在 `http://127.0.0.1:5173/` 提供可选择日期的 MO Option Chain 页面，与 `doctor` 的本地诊断地址一致；`npm run build` 执行 TypeScript 检查及 production build，`npm run lint` 运行 Oxlint，`npm run test` 运行前端测试。Vite dev proxy 将 frontend origin 的 `/mo-option-chain` 原路径和 query 转发到 `http://127.0.0.1:8011`，不需要 backend CORS policy。默认 provider 已接入真实读取链路；具体响应取决于目标日期与 Source 数据。

## Ownership

`dev.py` 只拥有 CLI parsing、命令分发、仓库路径解析、开发前提检查、Data Service `service_id` 转发、convenience default date resolution、进程调用、exit-code propagation 和人类可读状态。HTTP bind/runtime composition 与 contract 的 owner 是 `backend-api`；Data Service CLI 仍由 `market-snapshot` 拥有。Frontend 的 React/Vite 配置与开发脚本由 `web-ui` 拥有。`dev.py` 不导入模块内部代码，不拥有 Source Capture orchestration、Analysis Preparation、Data Service business semantics、dataset schema 或 trading-calendar resolution；端口仅用于本地开发诊断，不构成业务契约。

V1 不提供组合启动、后台进程、PID、日志、停止或重启、端口分配、配置框架、环境变量管理、依赖安装、测试运行或部署功能。`dev.py` 的 frontend 诊断地址与 Vite 显式绑定的 `127.0.0.1:5173` 一致。
