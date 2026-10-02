# DataLake Tushare Provider Runtime authority

本文件是 DataLake 内 Tushare provider execution 的唯一 canonical authority，拥有 credential resolution、client creation、request rate limiting、provider request execution、provider-level exception normalization 与 shared runtime lifecycle。继承 [模块架构](../ARCHITECTURE.md) 的 ownership / dependency boundary 与 [公共 Application authority](../APPLICATION.md) 的 lazy Source I/O、read-only 和 failure invariants。具体 Dataset 经 [catalog](../DATASETS.md) 进入其 Source / domain authority；当前实现差异见 [implementation reconciliation](../IMPLEMENTATION_RECONCILIATION.md)。

## 1. Ownership 与 execution boundary

Tushare Provider Runtime / Executor 属于 DataLake provider-specific shared infrastructure，目标 implementation namespace 为 `data_lake.providers.tushare`，位于 `data-lake/src/data_lake/providers/tushare/`。它不是 provider-agnostic shared kernel，不是 consumer-facing DataLake service，也不拥有任何 Dataset domain semantics。

```text
Dataset public Application Service
    ↓
Dataset Source Adapter
    ↓
Tushare Executor
    ↓
Tushare SDK / API
```

所有 Tushare-backed Dataset 的 Source adapter 均通过这一内部 execution boundary 执行 Tushare 请求，包括 Calendar、Index、Futures 与 Options 的 metadata / daily requests。Dataset adapter 决定请求什么与 response 的含义；Executor 决定怎样统一、受限地执行请求。

允许 Dataset Source adapter → `data_lake.providers.tushare` → Tushare SDK / HTTP API。Provider infrastructure 只可复用 shared kernel 的 provider-neutral error contracts，不依赖具体 Dataset、Dataset Service、Repository 或 FetchUnit semantics；kernel 不反向依赖 provider infrastructure。Research / Modeling / Snapshot / HTTP / CLI 等 consumers 只进入 Dataset public service，不直接调用 Executor，也不因 namespace 可 import 获得内部 execution permission。

Dataset adapter 继续拥有 endpoint selection、provider parameters、request batching、pagination / exhaustion、response partition、identity validation、Source facts normalization 与 completeness。`Provider Request != FetchUnit`；Executor 不接收 FetchUnits，不知道调用方 Dataset，不解释 index_code、trade_date、product、expiry 或 strike。

## 2. 薄请求契约

内部概念接口为：

```text
TushareExecutor.call(endpoint, **provider_parameters) -> provider_response
```

具体 Python naming 与类型载体属于后续 implementation concern；下列 execution semantics 固定：

1. Caller 显式指定 endpoint，parameters 保持 provider-native transport representation。
2. Executor 统一执行 rate limiting，再调用 Tushare client；caller 不自行 sleep 或协调速度。
3. Provider-level request execution failure 在 Executor 内统一转换。
4. 成功 response 原样交还 Dataset adapter，不 partition、不 normalize、不转换成统一 Record DTO。

不发布 `fetch_index_daily` / `fetch_future_daily` / `fetch_option_daily` 等 endpoint-specific typed facade。Response 解读失败、identity / normalization / completeness failure 仍归 Dataset adapter 与现有 Dataset/Core machinery，不作为 provider transport failure。

Executor 不拥有 retry policy、FetchUnit generation、Dataset batching / pagination policy、instrument catalog、SQLite、coverage、ensure orchestration、export 或 Research / Modeling transformation。V1 不自动 retry，不引入 backoff / retry budget / 自动恢复框架；未来 retry 如有稳定需求须另行设计。

## 3. Credential、client 与 shared lifecycle

Credential resolution 仅在 Provider Runtime 实现一次，稳定 credential identity 为 `TUSHARE_TOKEN`，保持现有 repository convention：

1. 优先读取 process environment 中的 `TUSHARE_TOKEN`。
2. 仅该环境变量不存在时，读取 repository `market-snapshot/.env` 中同名值；不覆盖已有环境变量。
3. 缺失、空字符串或全空白值均为 required credential failure。环境变量存在但为空白时不改用 fallback。

`market-snapshot/.env` 是 repository runtime compatibility convention，不表示 Provider Runtime 属于 Snapshot，也不授权 import Snapshot 私有 Source client / artifact helper。未来 credential source 可独立迁移，Dataset 不自行解析或感知 resolution mechanics；不得为各 Dataset 建立另一套 secret convention。

Provider Runtime 独自创建 Tushare client；Dataset 不直接读取 `TUSHARE_TOKEN` / `.env`，不自行调用 `tushare.pro_api(token)`。Dataset composition 仍组合自己的 adapter / storage / 已声明 prerequisites，通过内部 provider boundary 获取 execution 能力，不把 token 或 Executor 暴露为 consumer semantic argument。

Credential resolution 与 client initialization 必须 lazy：factory、`coverage` / `export`、无需 Source I/O 的 `ensure` 不解析凭据、不创建 Tushare client。包括全 success 或零目标的 ensure；consumer ensure 如实际需要 prerequisite Source I/O，则该 Source 请求仍遵守 lazy initialization。需要 Source I/O 时，在发起 provider request 前完成必要 initialization。

同一 process 中解析为同一 Tushare credential 的所有 Dataset 必须共享 provider execution state，至少共享下一节定义的 request-start schedule。不同 Dataset factory、service instance、Source adapter 或 operation 不能各自创建独立预算，也不能在结束/重建时重置同一 process / credential 的调度状态。Client 的具体复用方式、内部对象与同步机制留给 implementation，不能削弱共享调度、lazy initialization 与并发安全。

## 4. 平滑限流与并发边界

V1 最大 request-start 频率为 **500 calls / minute**；实际运行额度由 provider runtime 的 `TUSHARE_CALLS_PER_MINUTE` 配置（整数 1..500），默认 **180 calls / minute**，为 2000 积分账号的 200/min 留出余量。配置不是 Dataset semantic argument，不自动推断账号积分或权限。所有 endpoint 合并消费同一 process/credential 额度，统一采用平滑限流：

```text
minimum interval = 60 seconds / configured calls per minute >= 120 ms
request_start[n+1] - request_start[n] >= minimum interval
```

这里的相邻 starts 是同一 process / credential 下所有 Dataset 的合并启动序列；不是各 Dataset 各有独立额度，也不允许瞬时 burst。非法配置在需要 Source I/O 时以 OperationError 明确失败；read-only/factory 不读取该配置。限流约束实际 provider request start，不是 request completion；已经启动的请求即使失败也属于该启动序列。

Limiter 必须对 process 内并发调用安全：同一 Dataset、多个 Dataset、sequential ensure 与后续 concurrent execution 都遵守共享 schedule。Rate-limit 等待依据 request starts，不要求前一请求完成后再额外等待 120ms；慢 response 不增加 rate-limit 强制等待，也不要求 caller 协调速度。

V1 仅保证 **single Python process** 内共享预算。多个 processes、worktrees 或 machines 即使使用同一 credential，也不保证共享 500/min；不得称为 account-global limiter。不引入 Redis、SQLite / file rate-limit lock、distributed token bucket 或 central daemon；未来 cross-process quota coordination 须独立设计。

## 5. Failure boundary

Provider 使用受控 HTTP client 校验 HTTP status、JSON envelope 与 provider code，再返回 SDK-compatible DataFrame；HTTP failure、非法 envelope 不能成为合法空响应或分页结束证明。成功数据不做 Dataset normalization。SDK 历史上把部分非成功 HTTP 响应转成空 DataFrame 的行为不被继承。

请求错误 reason 必须包含 endpoint 与安全分类（rate_limit、quota、permission、timeout、network、http、response、provider、unknown），provider numeric code / HTTP status 可附带；不发布未经处理的远端 message、exception repr、请求 body 或 credential。原有 ExecutionFailure code 保持 source_request。初始化仍为 OperationError，不增加自动 retry。

诊断事件与 delivery 配置见 [DataLake diagnostics](../DIAGNOSTICS.md)。

公共 failure taxonomy 仍由 [APPLICATION.md](../APPLICATION.md) 唯一拥有；本节只固定 Tushare execution 的内部转换位置。

| Failure | 转换位置与结果 |
| --- | --- |
| required credential 缺失 / 空白，client creation 或 SDK initialization 失败 | Provider Runtime 抛 `OperationError`，表示整个 Source operation 无法开始，不伪装成逐 unit failure |
| network failure、provider rejection、SDK request exception、temporary remote failure | Executor 转换为现有 DataLake internal `ExecutionFailure(reason, code="source_request")` |
| 成功 response 的 partition、identity、facts normalization 或 completeness 不合法 | Dataset adapter / Dataset machinery 处理，继承其 authority 与公共 failure contract |

Executor 不把 provider request failure 映射到 FetchUnits；Dataset adapter 与现有 Dataset/Core machinery 根据该请求实际尝试的目标编码 failure。不能合法确定目标集合时，仍按公共及 Dataset authority 的 operation failure boundary 处理。Provider exception object、SDK type、stack 或 provider transport response 不进入 public Application contract；可读 reason 不包含 credential。

## 6. 后续 implementation 验证 invariant

以下是后续 implementation 的验收要求，不表示本轮已经创建或验证 runtime：

1. 所有 Tushare-backed Dataset 复用共享 execution boundary；Dataset 不解析 credential、不创建 `tushare.pro_api()` client。
2. 同一 process / credential 下，跨 Dataset、跨 service / operation 与并发调用共享同一 request-start schedule；任意相邻 starts 至少间隔 120ms。
3. 慢 response 不改变 request-start 限流基准；失败请求仍计入已发生的 starts，且没有隐式 retry。
4. Initialization failure 为 `OperationError`；request failure 统一为 internal `ExecutionFailure` 的 `source_request`，不泄漏 SDK exceptions；Dataset/Core 正确映射受影响目标。
5. 成功 provider response 原样返回；endpoint parameters、batching / pagination、partition、identity、normalization 与 completeness 仍由 adapter 独自拥有。
6. Provider runtime 不依赖 specific Dataset / Service / Repository / FetchUnit semantics；shared kernel 不依赖 provider runtime；consumer 不直接进入 provider boundary。
7. Factory 与整个 coverage / export 调用链无 credential resolution、client creation 或 Source I/O；全缓存 / 零目标且无需 prerequisite Source I/O 的 ensure 同样如此。
8. Environment precedence 与现有 fallback 相容，包括环境变量存在但为空白时失败；不增加 secret convention 或 consumer token argument。

Authority topology checks 后续须显式登记本文档；kernel / provider architecture checks 须按各自 ownership 分开，而不是把整个顶层 src 当作 kernel，或全面放开 SDK import。当前 Calendar drift、test registration 与后续实现输入集中记录在 [reconciliation](../IMPLEMENTATION_RECONCILIATION.md)。
