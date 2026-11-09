# Daily Data Copy / Export authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，在 [presentation architecture](presentation-architecture.md) 与 [UI system](ui-system.md) 边界内，拥有 MO Option Chain 与 MO Premium Plane 共同的数据复制交互契约。产品特有的 source、response identity 与 missing-value 阅读说明分别由 [Option Chain visualization](src/features/mo_option_chain/visualization.md#10-daily-data-copy--export) 和 [Premium visualization](src/features/mo_option_premium/visualization.md#10-daily-data-copy--export) 拥有。

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

## 5. CSV Boundary — Deferred to WP2

CSV 是独立的衍生导出视图，不要求与完整 JSON 可逆，也不代替完整证据。各 feature 指定真实的展平对象；不得生成虚构合约或 sparse plane 中不存在的 Point。

字段展开、空值编码、排序、CSV escape 与下载编码必须在 WP2 实施前进一步收束。WP0 只编码本边界，不实现 CSV。
