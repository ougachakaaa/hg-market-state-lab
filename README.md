# daily-market-snapshot

## 项目目标

该项目后续用于：从市场数据源获取数据，整理成结构明确、可复现的 Daily Market Snapshot，供 GPT 进行后续分析。

项目架构及架构层面的 authority 定义在 `ARCHITECTURE.md` 中。当前第一版 Daily Snapshot 的具体定义（Dataset、Raw 契约、Snapshot 结构与执行边界）在 `guides/daily-market-snapshot.md` 中。

当前架构定义、第一版 Snapshot Definition 与基础开发环境已就绪，已实现两个 Raw Dataset Collector（`index_daily`、`stock_daily`）；Snapshot Assembly 尚未实现。

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
* `guides/csi1000-5d-analysis-data.md`：CSI1000 "未来约 5 个交易日市场状态"分析场景的数据需求 authority（CSI1000 历史、MO 期权链、IM 期货期限结构）
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

`data/raw/` 是运行产物，不进入版本控制。
