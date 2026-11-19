# Strategy Research Map V1 契约

[入口](README.md) · [可选方法论](METHODOLOGY.md) · [地图定义](map.json) · [Schema](schema.json)

## 节点与关系

`nodes` 的顺序用于选择默认 Strategy 和键盘浏览。ID 使用类型前缀及描述性的小写 kebab-case，例如 `study-basis-historical`，创建后应保持稳定。节点记录标题、目的、问题、状态、结论和引用。Study 至少有一个研究问题和一项 `analyses`，每项记录名称、描述和计划或可用状态。Strategy 与 Baseline 可附参数说明。

| 关系 | 方向与约束 |
| --- | --- |
| `branch` | Strategy → Baseline → Dimension。每个 Baseline 与 Dimension 恰有一个结构父节点。Strategy 可以在没有回测或 Baseline 时建立。结构边无环。 |
| `attach` | Dimension → Study。独立 Study 可先定义，后续可由多项维度或策略引用。 |
| `derived_from` | Study → Finding。显著、可独立复用的结论可在验收后建立 Finding，至少关联一个已验收 Study。 |

`edges` 使用 `from`、`to`、`kind`，可附 `label`。禁止重复节点 ID、同型同向重复边、自连和悬空端点。地图至少有一个 Strategy。

## 状态与证据

| 字段 | 取值 |
| --- | --- |
| `planning` | `planned` 待开展、`defined` 方向已定义、`in-progress` 研究中 |
| `implementation` | `none` 待实施、`partial` 部分能力可用、`available` 已有实现 |
| `evidence` | `pending` 待研究或验收、`available` 已有材料、`accepted` 已验收 |
| `conclusion.status` | `pending`、`supported`、`rejected`、`inconclusive` |

`conclusion.summary` 记录当前解释或待办。一般节点的 `available` 与 `accepted` 需要至少一个具体 `result` 或 `report`。只有 `accepted` 可以记录正式结论，并必须附 `conclusion.review`。结论默认保留在 Study 内。独立 Finding 必须为 `accepted` 且记录自己的结论与审阅说明，证据链接从关联的已验收 Study 取得。每条 `derived_from` 都必须从具备具体证据的已验收 Study 出发。构建校验证据可定位性与记录一致性，研究结论及其适用范围由人工审阅。

`references` 使用 `kind`、`label`、`target`、`value`。 `workspace` 用于共享路由清单中的 `navigation`。 `repository` 使用仓库相对文件路径。 `source` 引用公开 authority Markdown，`report` 引用研究或回测目录下的 `evidence/` 或 `reports/` 文件，`result` 引用这些目录中的 JSON 或 Demo Manifest 已注册的 Bundle。引用应指向可随 Git 交付的真实文件，禁止路径穿越或符号链接。临时 Run、页面导航和 authority 文档只提供上下文，结果与报告的内容和生命周期由原业务模块负责。

## 添加 Study

将下列对象加入 [地图定义](map.json) 的 `nodes`：

```json
{
  "id": "study-roll-liquidity",
  "kind": "study",
  "title": "换仓流动性研究",
  "purpose": "描述固定换仓窗口内的成交条件。",
  "questions": ["现有策略的换仓窗口内成交量如何分布？"],
  "analyses": [
    {"name": "换仓窗口成交量分布", "note": "按合约与换仓窗口整理样本并比较分位数。", "availability": "planned"}
  ],
  "planning": "planned",
  "implementation": "none",
  "evidence": "pending",
  "conclusion": {"status": "pending", "summary": "待构建样本。"},
  "references": []
}
```

在 `edges` 加入 `{"from":"dimension-futures-long-trading-cost","to":"study-roll-liquidity","kind":"attach"}`。在另一维度复用同一 Study 时，只追加引用该 ID 的边。Online 开发页重新加载并校验定义，Static Demo 重建后在 `#/roadmap` 展示。
