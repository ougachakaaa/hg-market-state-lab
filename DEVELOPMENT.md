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

`backend` 在 `market-snapshot/` 前台执行 `poetry run python scripts/api.py`。`frontend` 在 `web-ui/` 前台执行 `npm run dev`；目前没有 `package.json`，所以它会明确报告 `frontend not initialized` 并非零退出。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。

## Ownership

`dev.py` 只拥有命令分发、仓库路径解析、开发前提检查、进程调用和人类可读状态。backend 的 bind 配置与 HTTP contract 仍由 backend 自身拥有；frontend 的 React/Vite 配置与开发脚本由 `web-ui` 拥有。`dev.py` 不导入模块内部代码，端口仅用于本地开发诊断，不构成业务契约。

V1 不提供组合启动、后台进程、PID、日志、停止或重启、端口分配、配置框架、环境变量管理、依赖安装、测试运行或部署功能。React Foundation 落地时需提供 `package.json` 与 `npm run dev`，并核对其默认端口与这里的本地诊断地址。
