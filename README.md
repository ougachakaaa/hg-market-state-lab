# daily-market-snapshot

## 项目目标

该项目后续用于：从市场数据源获取数据，整理成结构明确、可复现的 Daily Market Snapshot，供 GPT 进行后续分析。

项目架构及架构层面的 authority 定义在 `ARCHITECTURE.md` 中。当前第一版 Daily Snapshot 的具体定义（Dataset、Raw 契约、Snapshot 结构与执行边界）在 `guides/daily-market-snapshot.md` 中。

当前架构定义、第一版 Snapshot Definition 与基础开发环境已就绪，已实现 Raw Dataset Collector（第一版 Daily Snapshot 场景的 `index_daily`、`stock_daily`，以及 CSI1000 分析场景的 CSI1000 历史、MO 期权链与 IM 期货数据）；Snapshot Assembly 尚未实现。

## 基础环境

要求 Python 3.13 与 Poetry。

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

* `ARCHITECTURE.md`：项目架构及架构层面的 authority
* `guides/daily-market-snapshot.md`：第一版 Daily Snapshot Definition（具体 Dataset、Raw 契约、Snapshot 结构与执行边界）
* `guides/csi1000-5d-analysis-data.md`：CSI1000 "未来约 5 个交易日市场状态"分析场景的数据需求与 Raw Dataset 契约 authority（CSI1000 历史、MO 期权链、IM 期货）
* `config/`：配置
* `guides/`：DSH 执行任务使用的 Guide
* `scripts/`：Raw Dataset Collector（`fetch_*.py`）与后续的 `build_snapshot.py`
* `data/raw/`：Raw Dataset 输出目录
* `data/snapshots/`：后续 Snapshot 输出目录
* `tests/`：测试

## 环境变量

复制 `.env.example` 为 `.env` 并填入本地值。`.env` 不进入版本控制。

```bash
TUSHARE_TOKEN=<你的 Tushare token>
```

## 采集 Raw Dataset

两个 Collector 相互独立，都接受显式给出的交易日 `YYYY-MM-DD`：

```bash
poetry run python scripts/fetch_index_daily.py 2026-09-17
poetry run python scripts/fetch_stock_daily.py 2026-09-17
```

输出：

```text
data/raw/
└─ 2026-09-17/
   ├─ index_daily.json
   └─ stock_daily.json
```

数据集语义、字段单位与 Raw 文件形态以 `guides/daily-market-snapshot.md` 为准。给定日期没有数据（非交易日、停市、源无数据）时脚本明确失败，不自动 fallback 到其他日期。

## 采集 CSI1000 分析场景的 Raw Dataset

`guides/csi1000-5d-analysis-data.md` 定义的五个 Raw artifact 由五个相互独立的 Collector 采集，都接受显式给出的目标交易日 `YYYY-MM-DD`：

```bash
poetry run python scripts/fetch_csi1000_index_history.py 2026-09-17
poetry run python scripts/fetch_mo_option_basic.py 2026-09-17
poetry run python scripts/fetch_mo_option_daily.py 2026-09-17
poetry run python scripts/fetch_im_futures_basic.py 2026-09-17
poetry run python scripts/fetch_im_futures_daily.py 2026-09-17
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

这五个文件是 Source 事实的 Raw 落地（`index_daily_history.json` 与 `im_futures_daily.json` 可以包含多个交易日）；Dataset 语义、Universe 与历史窗口要求以 `guides/csi1000-5d-analysis-data.md` 为准。精确选取 120 / 60 个交易日、任何派生指标与 Snapshot Assembly 均不在本阶段范围内。

`data/raw/` 是运行产物，不进入版本控制。
