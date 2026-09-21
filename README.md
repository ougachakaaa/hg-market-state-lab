# hg-market-state-lab

## 项目目标

`hg-market-state-lab` 是用于**市场状态数据准备、市场状态建模与结果展示**的实验性系统：

```text
market state data preparation   （market-snapshot）
+
market state modeling           （market-modeling）
+
presentation / interaction      （web-ui）
```

本仓库的 Python 项目位于 `market-snapshot/`。下文的 `poetry` 命令，以及 `data/raw/`、`output/` 等运行产物路径，都以 `market-snapshot/` 为工作目录。

顶层架构（模块职责边界与数据流）定义在 `ARCHITECTURE.md` 中；`market-snapshot` 模块的架构 authority 定义在 `market-snapshot/ARCHITECTURE.md` 中。当前第一版 Daily Snapshot 的具体定义（Raw Artifact 契约、Snapshot 结构与执行边界）在 `market-snapshot/guides/daily-market-snapshot.md` 中。`web-ui` 模块的架构 authority 定义在 `web-ui/ARCHITECTURE.md` 中；其第一个 Web vertical slice（MO option-chain visualization）的用户体验 / visualization contract 定义在 `web-ui/guides/mo-option-chain-visualization.md` 中。

用户级调用语义（Data Service）与 CLI 契约定义在 `market-snapshot/guides/data-services.md` 中。

当前 `market-snapshot` 的架构定义、第一版 Daily Snapshot 定义与基础开发环境已就绪，已实现 Source Capture（第一版 Daily Snapshot 场景的 `index_daily`、`stock_daily`，以及 CSI1000 分析场景的 CSI1000 历史、MO 期权链与 IM 期货数据）、CSI1000 分析场景的 Analysis Preparation（Raw → analysis-ready `snapshot.json`），以及 Data Service CLI（`market-snapshot/scripts/dms.py`）；第一版 Daily Snapshot 的 Analysis Preparation 尚未实现。

## Development CLI

从仓库根目录检查本地开发状态或启动模块原生开发服务：

```bash
python dev.py doctor
python dev.py backend
python dev.py frontend
```

职责、状态与失败语义见 [DEVELOPMENT.md](DEVELOPMENT.md)。

## Data Service（用户入口）

普通用户和 Agent 的日常主入口是 Data Service CLI，无需知道底层有哪些 Source Capture、它们的执行顺序或 Raw 目录结构。当前 Data Service catalog 声明两项：`csi1000-5d-analysis` 与 `mo-option-chain`，两者均已实现；后者通过 HTTP read contract 服务 `web-ui`，没有 CLI 入口。当前 CLI 用户入口只服务 `csi1000-5d-analysis`。

列出当前支持的 Data Service：

```bash
poetry run python scripts/dms.py list
```

请求某个交易日的 `csi1000-5d-analysis`：

```bash
poetry run python scripts/dms.py get csi1000-5d-analysis --date 2026-09-18
```

两条命令在语义上分别等价于 `dms list` 与 `dms get csi1000-5d-analysis --date 2026-09-18`。`--date` 是显式给出的 `target_trade_date`：不支持 `today` / `latest`，不自动寻找最近交易日，不 fallback。unsupported service 或非 `YYYY-MM-DD` 的日期在任何 Source 请求之前失败。

`get` 自动完成整条链路（采集五个 Raw artifact → deterministic Analysis Preparation），成功时打印 `service`、`target_trade_date` 与 `output_path`，最终 artifact 位于：

```text
output/
└─ csi1000-5d-analysis/
   └─ 2026-09-18/
      └─ snapshot.json
```

任一步骤失败时停止执行、返回非零退出码，并在 stderr 报告 `service`、`date`、失败的 stage 与原因；不会跳过失败的 Capture、自动换日期或产出 partial final output。

Data Service / CLI / output 契约以 `market-snapshot/guides/data-services.md` 为准。

## HTTP API（MO Option Chain read contract）

`mo-option-chain` 没有 CLI 入口，它的 delivery surface 是 HTTP read contract（服务对象是 `web-ui` 等 read consumers）。在 `market-snapshot/` 目录内启动最小 delivery adapter：

```bash
poetry run python scripts/api.py
```

默认监听 `127.0.0.1:8011`，可用 `--host` / `--port` 覆盖：

```bash
poetry run python scripts/api.py --host 127.0.0.1 --port 8012
```

启动后：

* `http://127.0.0.1:8011/openapi.json`：机器可读的 HTTP contract；
* `http://127.0.0.1:8011/docs`：交互式 API 文档；
* endpoint：`GET /mo-option-chain?target_trade_date=YYYY-MM-DD&option_product=MO[&price_type=close]`。

端口号只是 launcher 细节，不属于 HTTP contract：endpoint 语义、request/query 参数、success / error response 与 status mapping 全部以 `market-snapshot/guides/mo-option-chain-http-contract.md` 为准；V1 不定义 server deployment、CORS、auth 或 API versioning。

真实 `Capture → Raw → MO Option Chain Preparation → read model` 已接入默认 HTTP provider。成功请求返回完整期权链；不可服务的日期或数据不完整时按 HTTP contract 返回相应 error envelope。`service_not_wired` 只保留作 bootstrap / test compatibility。

## Web UI（MO Option Chain 页面）

`web-ui/` 是独立的 npm frontend project，基于官方 Vite `react-ts` template。需要满足 Vite 要求的 Node.js（当前为 20.19+ 或 22.12+）。在 `web-ui/` 目录内执行：

```bash
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173/`，选择目标日期后立即读取 MO 期权链；一张分析图展示选中到期日的 Call / Put 价格与参考线，展开合约明细可查看缺价合约。前端检查：

```bash
npm run contract:check
npm run build
npm run lint
npm run test
```

`contract:check` 无需启动 HTTP 服务；它在 `market-snapshot/` 的 Poetry 环境中重新生成 OpenAPI 并与已提交的前端 JSON 比较，再核对由该 JSON 生成的 TypeScript 类型。后端 HTTP 测试也会检查 OpenAPI 与前端 JSON 一致。修改后端 HTTP DTO / OpenAPI 后，在 `web-ui/` 运行 `npm run contract:generate`，提交更新的 JSON 与 TypeScript，再运行上述检查。生成的类型与 OpenAPI JSON 由前端 client 消费，前端不维护独立的 HTTP wire schema。

开发时 Vite 将 frontend origin 的 `/mo-option-chain` 请求转发到默认监听 `http://127.0.0.1:8011` 的 FastAPI，保留路径与 query。先按上一节启动 backend，再访问：

```text
http://127.0.0.1:5173/mo-option-chain?target_trade_date=2026-09-17&option_product=MO
```

页面请求走同一条 proxy 路径。返回内容取决于目标日期和 Source 数据；无需为本地开发更改 backend 语义或添加 CORS。当前页面展示摘要、选中到期日的合并分析图和可展开明细。

## 基础环境

要求 Python 3.13 与 Poetry。以下命令在 `market-snapshot/` 目录内执行。

```bash
poetry install
```

```bash
poetry run python --version
```

```bash
poetry run pytest
```

```bash
poetry run ruff check .
```

```bash
poetry run mypy .
```

## 目录

* `README.md`：本文件
* `AGENTS.md`：Agent 工作规则
* `ARCHITECTURE.md`：仓库级顶层架构 authority（顶层模块职责边界与数据流）
* `market-snapshot/`：现有 Python 项目（Python 3.13 + Poetry）；`poetry` / `pytest` / `ruff` / `mypy` 命令都在该目录内执行
  * `ARCHITECTURE.md`：market-snapshot 模块架构 authority（Source / Capture / Preparation / Data Service 边界）
  * `pyproject.toml`、`poetry.lock`：Python 项目与工具配置（pytest / Ruff / mypy）
  * `.env.example`：本地环境变量模板
  * `guides/daily-market-snapshot.md`：第一版 Daily Snapshot 定义（具体 Raw Artifact 契约、Snapshot 结构与执行边界）
  * `guides/csi1000-5d-analysis-data.md`：CSI1000 "未来约 5 个交易日市场状态"分析场景的数据需求与 Source Capture / Raw Artifact 契约 authority（CSI1000 历史、MO 期权链、IM 期货）
  * `guides/csi1000-5d-analysis-snapshot.md`：同一场景的 Analysis Preparation Definition authority（Raw → analysis-ready `snapshot.json` 的组织方式）
  * `guides/mo-option-chain.md`：MO Option Chain 独立 deterministic data product authority（入口：产品定位 / ownership / query identity / invariants，与 `csi1000-5d-analysis` 并列）
  * `guides/mo-option-chain-data.md`：MO Option Chain data contract（Source / Raw / universe / completeness）
  * `guides/mo-option-chain-read-contract.md`：MO Option Chain read contract（price / null / grouping / ordering / response / failure）
  * `guides/data-services.md`：Data Service / CLI / output 契约 authority（用户级调用语义）
  * `config/`：配置
  * `guides/`：DSH 执行任务使用的 Guide
  * `src/daily_market_snapshot/`：实现代码，按职责分层（`sources/`、`capture/`、`preparation/`、`services/`、`api/`、`artifacts.py`、`cli.py`）
  * `scripts/`：极薄 executable shim（`dms.py` 转发到 `src/daily_market_snapshot/cli.py`；`api.py` 启动 `src/daily_market_snapshot/api/` 的 HTTP delivery adapter，默认 `127.0.0.1:8011`）
  * `data/raw/`：Raw Artifact 输出目录（内部运行产物）
  * `data/snapshots/`：非 Data Service 的 Snapshot 输出目录（运行产物）
  * `output/`：Data Service 的 canonical user-facing output（运行产物）
  * `tests/`：测试
* `market-modeling/`：结构占位目录（当前无实现）
* `web-ui/`：独立 Vite + React + TypeScript frontend project，已具备 MO option-chain 日期选择、读取状态、合并多到期日分析图与可展开明细。模块 authority 见 `ARCHITECTURE.md`，visualization contract 见 `guides/mo-option-chain-visualization.md`

## 环境变量

复制 `market-snapshot/.env.example` 为 `market-snapshot/.env` 并填入本地值。`.env` 不进入版本控制。

```bash
TUSHARE_TOKEN=<你的 Tushare token>
```

## 采集 Raw Artifact

两个 Source Capture 相互独立，都接受显式给出的交易日 `YYYY-MM-DD`：

```bash
poetry run python -m daily_market_snapshot.capture.index_daily 2026-09-17
poetry run python -m daily_market_snapshot.capture.stock_daily 2026-09-17
```

输出：

```text
data/raw/
└─ 2026-09-17/
   ├─ index_daily.json
   └─ stock_daily.json
```

数据集语义、字段单位与 Raw 文件形态以 `market-snapshot/guides/daily-market-snapshot.md` 为准。给定日期没有数据（非交易日、停市、源无数据）时脚本明确失败，不自动 fallback 到其他日期。

## 底层 Source Capture 与 Analysis Preparation（development / debugging entrypoints）

以下模块是 `csi1000-5d-analysis` 的实现层，用于 development、debugging、testing 与 reconciliation；日常数据任务请使用上面的 Data Service CLI，它会自行按顺序执行这些步骤。

`market-snapshot/guides/csi1000-5d-analysis-data.md` 定义的五个 Raw artifact 由五个相互独立的 Source Capture 采集，都接受显式给出的目标交易日 `YYYY-MM-DD`：

```bash
poetry run python -m daily_market_snapshot.capture.csi1000_index_history 2026-09-17
poetry run python -m daily_market_snapshot.capture.mo_option_basic 2026-09-17
poetry run python -m daily_market_snapshot.capture.mo_option_daily 2026-09-17
poetry run python -m daily_market_snapshot.capture.im_futures_basic 2026-09-17
poetry run python -m daily_market_snapshot.capture.im_futures_daily 2026-09-17
```

输出（目录名是目标交易日，不是文件中所有记录共同的 `trade_date`）：

```text
data/raw/
└─ csi1000-5d-analysis/
   └─ 2026-09-17/
      ├─ index_daily_history.json
      ├─ mo_option_basic.json
      ├─ mo_option_daily.json
      ├─ im_futures_basic.json
      └─ im_futures_daily.json
```

这五个文件是 Source 事实的 Raw 落地（`index_daily_history.json` 与 `im_futures_daily.json` 可以包含多个交易日）；Raw Artifact 语义、Universe 与历史窗口要求以 `market-snapshot/guides/csi1000-5d-analysis-data.md` 为准。

`market-snapshot/guides/csi1000-5d-analysis-snapshot.md` 定义的 `snapshot.json` 由 Analysis Preparation（`market-snapshot/src/daily_market_snapshot/preparation/csi1000_5d_analysis.py`）从上面五个 Raw artifact 确定性准备，再由 Data Service（`market-snapshot/src/daily_market_snapshot/services/csi1000_5d_analysis.py`）发布到 canonical 位置。Analysis Preparation 是确定性的数据转换、不是独立 executable；调试时可在同一 Raw 目录上直接调用 `daily_market_snapshot.preparation.csi1000_5d_analysis.build_snapshot(<target_trade_date>)`。

Analysis Preparation 只读取 `data/raw/csi1000-5d-analysis/<target_trade_date>/` 下的五个 Raw artifact：不调用 Tushare、不访问网络、不读取其他日期目录、不自动 fallback。Raw 缺失、形状不合法、120 / 60 日窗口不足、MO 或 IM 无法 join、字段缺失或无法计算派生值时，Data Service 明确失败并返回非零退出码，不跳过记录、不填零、不估算。

窗口选择、join 规则、派生字段公式、排序与失败条件全部以 `market-snapshot/guides/csi1000-5d-analysis-snapshot.md` 为准（该 Guide 是 Analysis Preparation Definition 的 authority）。`snapshot.json` 是 analysis-ready 数据，不含任何市场判断或交易结论。

`data/raw/` 与 `output/` 都是运行产物，不进入版本控制。
