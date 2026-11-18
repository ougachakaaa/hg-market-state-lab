# Strategy Research Map 契约

[入口](README.md) · [方法论](METHODOLOGY.md) · [地图定义](../../ui_web/research-map/map.json) · [Schema](../../ui_web/research-map/schema.json)

## 节点与状态

`nodes` 按阅读和键盘浏览顺序列出。`id` 稳定且唯一。`kind` 指定概念职责，`strategy-definition` 属于 Strategy，`study` 和 `hypothesis` 同属 Hypothesis & Study。标题、目的、问题、指标和参数说明为研究文档文本。指标 `availability` 明确区分已有页面或样例可参考的指标和待研究指标，`note` 标明具体覆盖范围。

| 字段 | 取值 |
| --- | --- |
| `planning` | `planned` 待规划、`defined` 方向已定义、`in-progress` 研究中 |
| `implementation` | `none` 待实施、`partial` 已有部分能力、`available` 已有对应实现 |
| `evidence` | `pending` 待验收、`available` 已有材料、`accepted` 已验收 |
| `conclusion.status` | `pending`、`supported`、`rejected`、`inconclusive` |

结论的 `summary` 记录当前解释或待办。`accepted` 需要至少一个具体 `result` 或 `report` 证据引用，并给出非 `pending` 的结论和 `review` 验收说明。`available` 同样需要具体材料，结论仍为 `pending`。验收以提交中记录的人工研究判断为准，构建只检验可定位性与一致性。

## 关系与资源

`edges` 使用 `from`、`to`、`kind`，可附 `label`。`dependency` 从前置节点指向依赖节点，且构成有向无环子图；`motivates` 从理由指向被推动的研究；`feedback` 从后续发现指回应重审的节点。动机和反馈可形成跨节点循环。不允许自连、悬空端点和重复的同型同向边。布局由依赖边自动计算。

`references` 使用 `kind`、`label`、`target`、`value`。`workspace` 只用于 `navigation`，目标为共享路由清单中的路径。`repository` 用于 `source`、`result` 或 `report`，目标为仓库相对文件路径。来源限公开 authority Markdown；报告限该研究或回测目录内的 `evidence/` 或 `reports/` 文件；结果可引用这些目录的 JSON 或现有 Demo Manifest 注册的 Bundle。输入应为可随 Git 交付的真实文件，路径不能穿越目录或经符号链接。Demo Bundle 可引用作已存在的材料，节点验收仍需明确适用范围与验收依据。临时 Run、通用页面和数据导航本身不具备证据身份。

## 添加一个 Study

1. 在 `nodes` 追加唯一 ID 和 `kind: "study"`，填写标题、目的、问题及若干 `metrics`，例如 `{"name":"配对样本量","availability":"planned"}`。
2. 为节点填写计划、实现和证据状态。没有验收材料时使用 `evidence: "pending"` 和 `conclusion: {"status":"pending","summary":"待研究"}`。
3. 在 `edges` 追加关系，例如 `{"from":"AT0","to":"A2","kind":"motivates"}` 和 `{"from":"A2","to":"O1","kind":"motivates"}`。确认两个端点都存在。
4. Online 开发页自动更新或重载。用 `npm run demo:build` 重建 Static Demo，在预览打开 `#/roadmap`。两端都在 Vite 读取定义时校验，定位信息会指出无效字段或节点。

以下对象可追加到 `nodes`，配合上面的两条边。示例中的指标是待研究的口径。

```json
{
  "id": "A2",
  "kind": "study",
  "title": "换仓流动性研究",
  "purpose": "描述候选合约的换仓流动性约束。",
  "questions": ["换仓时点的合约流动性是否足以支撑候选规则？"],
  "metrics": [
    {"name": "配对样本量", "availability": "planned"},
    {"name": "日成交量", "availability": "planned"},
    {"name": "持仓量", "availability": "planned"}
  ],
  "planning": "planned",
  "implementation": "none",
  "evidence": "pending",
  "conclusion": {"status": "pending", "summary": "待研究"},
  "references": []
}
```
