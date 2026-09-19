# Repository Development CLI

仓库根目录的 `dev.py` 是本地开发入口，只负责检查启动条件和转发模块自己的启动命令。它是 developer orchestration surface，不是 Data Service、部署工具或新的业务模块。

```bash
python dev.py doctor
python dev.py backend
python dev.py frontend
```

## 命令与状态

`doctor` 检查仓库结构、backend launcher、Poetry 虚拟环境中的 Python 3.13，以及 Node 和 npm。它报告默认本地地址 `127.0.0.1:8011` 的 backend 状态：未监听为 `stopped`，监听且 `/openapi.json` 有效为 `running / healthy`，否则为 `port occupied / unhealthy`。服务未启动是正常状态。若 `web-ui/package.json` 不存在，frontend 报告 `not initialized`；存在后检查默认 `127.0.0.1:5173` 是否监听，不要求专用 health endpoint。

`doctor` 在必要的仓库结构、backend launcher、Poetry 或 Python 3.13 条件不满足时非零退出；frontend 已初始化但 Node/npm 不可用时也非零退出。frontend 尚未初始化和服务停止本身不使 `doctor` 失败。检查只读，不创建虚拟环境、不安装依赖，也不调用 Tushare 或运行 pytest、Ruff、mypy。

`backend` 在 `market-snapshot/` 前台执行 `poetry run python scripts/api.py`。`frontend` 在 `web-ui/` 前台执行 `npm run dev`；首次启动前需在 `web-ui/` 自行执行 `npm install`。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。

`web-ui/` 是独立 npm project，使用官方 Vite `react-ts` template 建立 React + TypeScript foundation。Node.js 需满足当前 Vite 要求（20.19+ 或 22.12+）。`npm run dev` 在 `http://127.0.0.1:5173/` 提供 React shell，与 `doctor` 的本地诊断地址一致；`npm run build` 执行 TypeScript 检查及 production build，`npm run lint` 运行模板自带的 Oxlint。Vite dev proxy 将 frontend origin 的 `/mo-option-chain` 原路径和 query 转发到 `http://127.0.0.1:8011`，不需要 backend CORS policy。真实 provider 未接线时，该请求返回现有的 `503 service_not_wired`。

## Ownership

`dev.py` 只拥有命令分发、仓库路径解析、开发前提检查、进程调用和人类可读状态。backend 的 bind 配置与 HTTP contract 仍由 backend 自身拥有；frontend 的 React/Vite 配置与开发脚本由 `web-ui` 拥有。`dev.py` 不导入模块内部代码，端口仅用于本地开发诊断，不构成业务契约。

V1 不提供组合启动、后台进程、PID、日志、停止或重启、端口分配、配置框架、环境变量管理、依赖安装、测试运行或部署功能。`dev.py` 的 frontend 诊断地址与 Vite 显式绑定的 `127.0.0.1:5173` 一致。
