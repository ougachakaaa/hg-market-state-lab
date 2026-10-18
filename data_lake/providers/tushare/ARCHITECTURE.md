# DataLake Tushare Provider Runtime authority

本文件是 DataLake 内 Tushare provider execution 的唯一 canonical authority，拥有 credential resolution、client creation、request rate limiting、provider request execution、provider-level exception normalization 与 shared runtime lifecycle。继承 [模块架构](../../ARCHITECTURE.md) 的 ownership / dependency boundary 与 [公共 Application authority](../../APPLICATION.md) 的 lazy Source I/O、read-only 和 failure invariants。具体 Dataset 经 [catalog](../../DATASETS.md) 进入其 Source / domain authority。

## 1. Ownership 与 execution boundary

Tushare Provider Runtime / Executor 属于 DataLake provider-specific shared infrastructure，implementation namespace 为 `data_lake.providers.tushare`，由 `data_lake/providers/tushare/` 独立拥有：本文件为 authority，`src/data_lake/providers/tushare/` 为 implementation，`tests/` 为 Provider verification。Filesystem ownership 不改变该 Python namespace，source root 使用 repository root 唯一 Python project / environment。它不是 provider-agnostic shared kernel，不是 consumer-facing DataLake service，也不拥有任何 Dataset domain semantics。

```text
Dataset public Application Service
    ↓
Dataset Source Adapter
    ↓
Tushare Executor
    ↓
Provider client / HTTP API
```

所有 Tushare-backed Dataset 的 Source adapter 均通过这一内部 execution boundary 执行 Tushare 请求，包括 Calendar、Index、Futures 与 Options 的 metadata / daily requests。Dataset adapter 决定请求什么与 response 的含义；Executor 决定怎样统一、受限地执行请求。

本内部 execution boundary 的 dependency / public access permissions 继承 [模块架构](../../ARCHITECTURE.md)。

Dataset Source Adapter 实现 Kernel 的 [Source Port](../../PORTS.md)，拥有 endpoint selection、provider parameters、request batching、pagination / exhaustion 与 response partition；identity / facts normalization 与 completeness 的规则由 Dataset Domain 拥有，Adapter 调用这些策略。`Provider Request != FetchUnit`；Executor 不接收 FetchUnits，不知道调用方 Dataset，不解释 index_code、trade_date、product、expiry 或 strike。

## 2. 薄请求契约

内部概念接口为：

```text
TushareExecutor.call(endpoint, **provider_parameters) -> provider_response
```

具体 Python naming 与类型载体属于 implementation concern；下列 execution semantics 固定：

1. Caller 显式指定 endpoint，parameters 保持 provider-native transport representation。
2. Executor 统一执行 rate limiting，再调用 Tushare client；caller 不自行 sleep 或协调速度。
3. Provider-level request execution failure 在 Executor 内统一转换。
4. 成功 response 原样交还 Dataset adapter，不 partition、不 normalize、不转换成统一 Record DTO。

不发布 `fetch_index_daily` / `fetch_future_daily` / `fetch_option_daily` 等 endpoint-specific typed facade。Response 解读失败归 Dataset Adapter，identity / normalization / completeness failure 归 Dataset 领域策略与 Kernel Application 的验证编排，不作为 provider transport failure。

Executor 不拥有 retry policy、FetchUnit generation、Dataset batching / pagination policy、instrument catalog、SQLite、coverage、ensure orchestration、export 或 Research / Modeling transformation。V1 不自动 retry，不引入 backoff / retry budget / 自动恢复框架；未来 retry 如有稳定需求须另行设计。

## 3. Credential、client 与 shared lifecycle

Credential resolution 仅在 Provider Runtime 实现一次，稳定 credential identity 为 `TUSHARE_TOKEN`，保持现有 repository convention：

1. 优先读取 process environment 中的 `TUSHARE_TOKEN`。
2. 仅该环境变量不存在时，读取 repository `data_snapshot/.env` 中同名值；不覆盖已有环境变量。
3. 缺失、空字符串或全空白值均为 required credential failure。环境变量存在但为空白时不改用 fallback。

`data_snapshot/.env` 是 repository runtime compatibility convention，不表示 Provider Runtime 属于 Snapshot，也不授权 import Snapshot 私有 Source client / artifact helper。未来 credential source 可独立迁移，Dataset 不自行解析或感知 resolution mechanics；不得为各 Dataset 建立另一套 secret convention。

Provider Runtime 独自创建 Tushare client；Dataset 不直接读取 `TUSHARE_TOKEN` / `.env`，不自行调用 `tushare.pro_api(token)`。Dataset composition 仍组合自己的 adapter / storage / 已声明 prerequisites，通过内部 provider boundary 获取 execution 能力，不把 token 或 Executor 暴露为 consumer semantic argument。

Credential resolution 与 client initialization 遵守 [APPLICATION.md](../../APPLICATION.md) 的 lazy Source I/O invariant，包括 prerequisite 调用链。需要 Source I/O 时，在发起 provider request 前完成必要 initialization。

同一 process 中解析为同一 Tushare credential 的所有 Dataset 必须共享 provider execution state，至少共享下一节定义的 request-start schedule。不同 Dataset factory、service instance、Source adapter 或 operation 不能各自创建独立预算，也不能在结束/重建时重置同一 process / credential 的调度状态。Client 的具体复用方式、内部对象与同步机制留给 implementation，不能削弱共享调度、lazy initialization 与并发安全。

## 4. 平滑限流与并发边界

V1 最大 request-start 频率为 **500 calls / minute**；实际运行额度由 provider runtime 的 `TUSHARE_CALLS_PER_MINUTE` 配置（整数 1..500），默认 **180 calls / minute**，为 2000 积分账号的 200/min 留出余量。配置不是 Dataset semantic argument，不自动推断账号积分或权限。所有 endpoint 合并消费同一 process/credential 额度，统一采用平滑限流：

```text
minimum interval = 60 seconds / configured calls per minute >= 120 ms
request_start[n+1] - request_start[n] >= minimum interval
```

这里的相邻 starts 是同一 process / credential 下所有 Dataset 的合并启动序列；不是各 Dataset 各有独立额度，也不允许瞬时 burst。非法配置在需要 Source I/O 时以 OperationError 明确失败；read-only/factory 不读取该配置。同一 process / credential 已建立 execution state 后，rate 配置变更以 OperationError 拒绝，不能静默重置 schedule。限流约束实际 provider request start，不是 request completion；已经启动的请求即使失败也属于该启动序列。

Request start 以实际 HTTP headers/body 发送边界为准，不能只限制上层 call 或提前预留的调度时间。共享 credential-local gate 保护实际发送，发送结束或失败后更新调度时间并释放 gate；线程延迟不能将已放行请求积压成 burst。连接建立、日志、响应等待与解析不持有 gate。

Limiter 必须对 process 内并发调用安全：同一 Dataset、多个 Dataset、sequential ensure 与后续 concurrent execution 都遵守共享 schedule。Rate-limit 等待不要求前一请求完成响应后再额外等待 120ms；慢 response 不增加 rate-limit 强制等待，也不要求 caller 协调速度。

V1 仅保证 **single Python process** 内共享预算。多个 processes、worktrees 或 machines 即使使用同一 credential，也不保证共享 500/min；不得称为 account-global limiter。不引入 Redis、SQLite / file rate-limit lock、distributed token bucket 或 central daemon；未来 cross-process quota coordination 须独立设计。

## 5. Failure boundary

Provider 使用受控 HTTP client 校验 HTTP status、JSON envelope 与 provider code，再返回 SDK-compatible DataFrame；HTTP failure、非法 envelope 不能成为合法空响应或分页结束证明。成功数据不做 Dataset normalization。SDK 历史上把部分非成功 HTTP 响应转成空 DataFrame 的行为不被继承。

请求错误 reason 必须包含 endpoint 与安全分类（rate_limit、quota、permission、timeout、network、http、response、provider、unknown），provider numeric code / HTTP status 可附带；不发布未经处理的远端 message、exception repr、请求 body 或 credential。原有 ExecutionFailure code 保持 source_request。初始化仍为 OperationError，不增加自动 retry。

诊断事件与 delivery 配置见 [DataLake diagnostics](../../DIAGNOSTICS.md)。

公共 failure taxonomy 仍由 [APPLICATION.md](../../APPLICATION.md) 唯一拥有；本节只固定 Tushare execution 的内部转换位置。

| Failure | 转换位置与结果 |
| --- | --- |
| required credential 缺失 / 空白，client creation 或 SDK initialization 失败 | Provider Runtime 抛 `OperationError`，表示整个 Source operation 无法开始，不伪装成逐 unit failure |
| network failure、provider rejection、SDK request exception、temporary remote failure | Executor 转换为现有 DataLake internal `ExecutionFailure(reason, code="source_request")` |
| 成功 response 的 partition、identity、facts normalization 或 completeness 不合法 | Dataset adapter / Dataset machinery 处理，继承其 authority 与公共 failure contract |

Executor 不把 provider request failure 映射到 FetchUnits；Dataset adapter 与现有 Dataset/Core machinery 根据该请求实际尝试的目标编码 failure。不能合法确定目标集合时，仍按公共及 Dataset authority 的 operation failure boundary 处理。Provider exception object、SDK type、stack 或 provider transport response 不进入 public Application contract；可读 reason 不包含 credential。

## 6. Cancellation boundary

内部 execution 可用 cancellation guard 包裹 Executor：取消后拒绝后续 call，已进入的 call 按既有 timeout/限流/错误契约收束。Guard 不重试、不取消已发出的 HTTP、不改变 quota 计数，也不解释 FetchUnits；Dataset Source 的分页停止遵守 Adapter lifecycle，取消触发与等待属于 [bounded execution](../../EXECUTION.md)。
