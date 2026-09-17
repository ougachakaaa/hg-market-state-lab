# daily-market-snapshot

## 项目目标

该项目后续用于：从市场数据源获取数据，整理成结构明确、可复现的 Daily Market Snapshot，供 GPT 进行后续分析。

项目架构及架构层面的 authority 定义在 `ARCHITECTURE.md` 中。当前第一版 Daily Snapshot 的具体定义（Dataset、Raw 契约、Snapshot 结构与执行边界）在 `guides/daily-market-snapshot.md` 中。

当前架构定义、第一版 Snapshot Definition 与基础开发环境已就绪，尚未实现市场数据采集与 Snapshot 生成。

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
* `config/`：配置
* `guides/`：DSH 执行任务使用的 Guide
* `scripts/`：后续 Python 执行脚本
* `data/raw/`：后续原始数据输出目录
* `data/snapshots/`：后续 Snapshot 输出目录
* `tests/`：测试

## 环境变量

复制 `.env.example` 为 `.env` 并填入本地值。`.env` 不进入版本控制。
