# Research UI configuration authority

本文档从属于 [Research UI authority](ARCHITECTURE.md)，拥有 study-local CLI 共用的 V1 configuration location、schema、resolution 与 failure contract。它不拥有 Study request、Study semantics 或 Snapshot Source configuration。

## 1. Canonical file 与 schema

V1 只读取 repository 内固定的 canonical config：

```text
<repository-root>/market-research/research.toml
```

完整 V1 schema 为：

```toml
[output]
root = "market-research/output"
```

`output.root` 是唯一配置项且必须存在，其 semantic type 是 filesystem path represented as a non-empty TOML string。V1 不定义 `--config`、environment override、user-home config、machine-local overlay 或多层 precedence。未来若真实需求需要显式 config-file selection，必须保持同一 schema 并先更新本 authority。

## 2. Resolution

- absolute `output.root` 直接进行 filesystem path normalization；
- relative `output.root` 必须相对 repository root 解析，不相对当前工作目录或 config file directory；
- loader 返回的 output root 必须是 normalized absolute path；
- output root 与目标 run directory 都不要求在 configuration loading 时预先存在；
- directory creation 与 replacement 属于 run/output handling，不属于 config parsing。

Repository root 必须由 canonical project/config location 确定，不得通过调用者碰巧所在的 current working directory 猜测。

## 3. Ownership exclusions

Research configuration 只拥有 output location，不得包含：

```text
Study start/end dates or hidden date defaults
horizons, formulas, quantiles or statistical methods
Study-specific semantic parameters
TUSHARE_TOKEN or any credential
Snapshot Source/Capture configuration
artifact filenames or visualization options
```

日期属于显式 Study request；Study method 和 artifact 内容属于对应 Study authority；credential 与 Source composition 属于 Snapshot boundary。

## 4. Loader contract 与 failure

Loader 位于 `market_research.ui`，负责 locate canonical config、使用 Python 3.13 标准库 `tomllib` 解析 TOML、验证完整 schema、解析 output root，并返回 typed immutable Research UI config。不得仅为 TOML parsing 增加第三方 dependency。

以下情况必须成为 user-facing configuration failure，不得静默 fallback、猜测或修复：

```text
canonical file unreadable
invalid TOML
missing [output] section
missing output.root
wrong value type
empty path string
invalid filesystem representation
path cannot be normalized to an absolute result
```

Configuration 只由 study-local runner 加载；repository CLI 不提供独立 `research config` command。Runner 不得输出任何 environment value、credential 或 secret。
