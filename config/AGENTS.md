# config Agent Rules

## 适用范围

本文件适用于 `config/`。它是 repository-level configuration support（Python namespace `lab_config`），不是业务模块；语义边界由根 [architecture](../ARCHITECTURE.md) 拥有。

## 执行规则

- 只拥有 repository 配置文件的加载、来源优先级与格式校验；不拥有 Auth、Tushare、Publication 或任何业务语义、错误分类。
- canonical 本地配置是 repository root `.env`；tracked 模板是根 `.env.example`。process environment 优先于 `.env`，空值不回退。
- 不 import `data_lake`、`data_snapshot`、`market_*`、`ui_*` 或其他 repository 业务包；consumer 通过本 package 的公开函数读取配置。
- 不记录、不打印、不在异常中包含 token、JWT secret 或其他配置值；错误消息只允许包含固定 key 名和文件路径。
- 不在 import 时读取 `.env`；测试通过 `lab_config.ENV_FILE` 隔离真实文件。

## Scoped verification

Follow the [root verification policy](../AGENTS.md#verification-policy-user-decision-2026-11-14).
Select only directly affected business test files/cases. No default full-module or
cross-module regression, topology, browser, live-data or deployment acceptance.
Retain business invariants and fixtures; record unavailable checks as NOT VERIFIED.
Do not modify real market data or caches to satisfy tests.
