# web-ui 模块架构 authority

本文件定义 `web-ui` 的稳定职责、数据依赖方向与 authority 路由。仓库级定位见 [../ARCHITECTURE.md](../ARCHITECTURE.md)；具体 vertical slice 的 authority 与实现共址于 `src/features/`。

## 1. Purpose

`web-ui` 是数据产品与市场状态结果的展示、交互层，负责：

```text
user interaction
requesting explicit read data
presentation
visualization
```

## 2. Responsibility Boundary

`web-ui` 不拥有 Source、Source Capture、Raw Artifact、Analysis Preparation formula、market modeling 或业务计算语义，也不产生交易判断。

前端只消费 backend 明确发布的 read/HTTP contract。它不得为了绘图重新推导产品身份、contract universe、价格 fallback、业务 completeness 或金融指标。

## 3. 数据依赖方向

```text
backend semantic contract
        ↓
HTTP wire contract / generated client types
        ↓
web-ui request adaptation
        ↓
interaction and visualization
```

Markdown authority 定义语义；backend OpenAPI 是 HTTP wire contract 的机器可读表达。前端可以消费生成类型与运行时校验，但不得独立维护一份竞争性的 backend schema。

## 4. Vertical Slice Authority

`web-ui/src/features/*` 中的 feature authority 只拥有对应 vertical slice 的：

```text
user input and presentation state
display scope
visual encoding
interaction
empty and error presentation
```

MO Option Chain vertical slice 的入口是 [src/features/mo_option_chain/ARCHITECTURE.md](src/features/mo_option_chain/ARCHITECTURE.md)。该入口会按需链接 backend 产品、read 与 HTTP authority；普通前端任务无需读取 Source、Raw 或不相关产品文档。

## 5. 维护边界

只有展示层职责、backend contract 消费边界或数据依赖方向变化时更新本文件。框架版本、图表库、component tree、state-management、具体字段和视觉规则属于实现或 vertical slice Guide。
