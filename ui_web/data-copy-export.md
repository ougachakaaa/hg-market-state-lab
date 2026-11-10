# Daily Data Copy / Export authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，在 [presentation architecture](presentation-architecture.md) 与 [UI system](ui-system.md) 边界内，拥有 MO Option Chain 与 MO Premium Plane 共同的数据复制与 CSV 导出交互契约。产品特有的 source、response identity 与 missing-value 阅读说明分别由 [Option Chain visualization](src/features/mo_option_chain/visualization.md#10-daily-data-copy--export) 和 [Premium visualization](src/features/mo_option_premium/visualization.md#10-daily-data-copy--export) 拥有。

本契约不定义 HTTP schema、金融 DTO 或通用 Export Framework，也不授予 sibling feature 互相依赖或把金融语义移入 `shared` 的权限。HTTP shape 与业务含义继续由各 feature 链接的 owning contracts 决定。

## 1. Copy JSON

复制来源只能是当前成功请求实际收到、通过 runtime contract validation 的完整 HTTP 业务响应。各 feature 指定其成功状态中的 canonical copy source；不得使用展示投影、当前图表可见子集或按控件重建的对象。

使用无损的 JSON value serialization，例如 `JSON.stringify(payload, null, 2)`；不要求恢复 HTTP 字节、空白或数字的原始字面写法。必须保留完整响应的字段、数组顺序与数值事实，包括未选中的 expiry、Call/Put 合约、Premium Point 和全部 metric。不得进行金融计算、单位转换、数值四舍五入、补值、删除 null 或静默截断；JSON null、numeric zero 与不存在的 Point 必须保持区别。

## 2. Copy for GPT

复制一份完整、可粘贴的 Markdown，按顺序只包含：

1. 产品名称。
2. 已校验响应中的 observation/trade date、option product、resolved price type 与 underlying identity。
3. 简短的数据阅读说明，内容限于 owning contract 已确认的语义。
4. 一个标记为 `json`、包含与 Copy JSON 相同完整 JSON 的 Markdown code fence。

身份字段由 feature authority 指定，必须从该次成功响应读取，不得从可能已经变化的输入控件、当前日期或 presentation state 猜测。阅读说明不得推断行情、提供投资建议、补充金融公式或猜测未定义的单位。

Copy for GPT 只写入浏览器剪贴板，不自动调用外部 GPT API。

## 3. Current-result Lifecycle

- 只有当前成功、已校验结果允许复制。Idle、loading、error/failure 或 contract-invalid response 不得暴露上一笔结果作为当前查询的复制内容。
- 新 query 开始或日期清空时，旧结果与对应 copy source 同时退出 current-result 状态。较早请求不得覆盖较新请求的 loading、success 或 failure。
- 当前结果身份来自已返回的响应；输入控件是 request intent，不能替代 response identity。
- Presentation state 只改变展示，不影响两种复制内容。复制不得发起新 HTTP 请求或触发 backend recomputation。

## 4. Clipboard UX and Content Boundary

两个页面均须在成功结果区域顶部显著提供 `Copy JSON` 与 `Copy for GPT`，不依赖展开 Inspector 才能访问。使用现有 Ant Design 6 普通 UI 组件及 application 共享主题，不新增通用 UI 组件库。

复制成功或失败必须有可见反馈；仅在 Clipboard 写入成功后报告成功。访问被拒、Clipboard 不可用或写入失败均必须报告失败，不得误报成功或把内部异常详情放入复制文本。大 payload 仍须完整复制，不得静默截断；可以提示大小或字符数。

复制文本只包含业务响应及本契约允许的上下文；不得加入 JWT、Cookie、认证头、Tushare Token、运行配置或内部异常详情。不得序列化 request、transport/auth state 或 error object 作为复制内容。

Premium 的完整 Raw HTTP Response Inspector 继续遵循其 feature authority；顶部复制入口不改变 Inspector 的查看范围或当前响应语义。

## 5. CSV V1 Contract

CSV 是当前完整、已校验成功响应的衍生 tabular representation，不要求 JSON 可逆，不代替完整 JSON evidence。第 3 节 lifecycle 同样适用：idle/loading/failure/contract-invalid 不提供导出，新 query 清除旧源，迟到请求不能覆盖当前源。Presentation filters 不影响内容，导出不请求 HTTP。

每行只对应 feature 指定的真实 analytical entity。固定 header、列序和 backend 稳定行序；不生成合约、Point 或占位记录，不做金融计算、fallback、补值或插值。无真实记录时为 header-only。产品 column mapping 归 feature visualization authority。

Nullable value 使用字面量 `null`，numeric zero 使用 `0`，boolean 使用 `true` / `false`。缺席 futures 的 identity/price 均为 `null`，以 `futures_present=false` 表达 object absence。数值使用 JavaScript number 字符串表示，不做 display rounding，不恢复 HTTP 原始数字字面写法；yield 保持 decimal ratio。

CSV 使用 UTF-8 BOM、逗号分隔、CRLF，每条记录（含 header）以 CRLF 结束。包含逗号、双引号或 CR/LF 的 cell 用双引号包裹，内部双引号加倍。文本以 `= + - @`、TAB、CR 或 LF 开头，或去除前导空白/控制字符后以 `= + - @` 开头时，在完整原文本前加单引号，再执行 CSV quoting。此 spreadsheet formula protection 仅作用于风险字符串，不改变 numeric facts，普通文本保持原样。

成功结果顶部动作依次为 `Copy JSON | Copy for GPT | Export CSV`。下载独立于 Clipboard；复制 pending 时整个动作区禁用。构建 `text/csv;charset=utf-8` Blob、Object URL 和临时 anchor，触发一次下载；成功后下一事件循环释放 URL/DOM，失败也清理资源。正常触发反馈 `Download started`，异常反馈 `Export failed`，不声称浏览器已保存文件，不暴露内部异常。

文件名由 feature 指定的 response date 与 resolved price type 生成；路径分隔符、控制字符及不安全文件名字符替换为 `_`。CSV 只包含业务字段，不序列化 HTTP header、JWT、Cookie、Token、request/auth state 或内部运行信息。

Shared CSV utility 仅拥有 ordered header、scalar encoding、quoting、BOM/CRLF、安全文件名和 browser download/resource lifecycle；feature-local pure projection 拥有 flattening，不在 shared 定义金融字段、并行 DTO 或 Export Framework。
