# CSI1000 IM Basis History read/application contract

本文档从属于 [product authority](ARCHITECTURE.md)，拥有 historical Preparation projection、semantic result、public Python application boundary 与 product failure。Source scope 和 completeness 见 [data authority](data.md)；slot、remaining days、basis formula 与 canonical ordering 见 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md)。

## 1. Application request

Public application boundary 接收一个 semantic request：

```text
start_trade_date
end_trade_date
```

两者都是 required `YYYY-MM-DD` date value，含端点，并在调用 Capture 前验证。无默认值，无 latest/today resolution。

## 2. Preparation

对 [data authority](data.md) 确定的每个 observation date：

1. 以 `trade_date` 对齐该日唯一 CSI1000 close。
2. 以 `ts_code` 将每条 IM daily fact 与唯一 active basic fact join。
3. 应用共享 CFFEX basis authority 的四槽 validation、slot mapping、calendar distance 和 basis preparation。
4. 只投影第 3 节锁定的 analysis-ready fields。
5. 完整 panel 验证通过后，再按共享 CFFEX canonical ordering 产生 result。

Preparation 不访问网络、当前时间、Research code、HTTP DTO 或 sibling product artifact。

## 3. Observation shape

每个 `trade_date × active IM contract` observation 恰好包含：

```text
trade_date

ts_code
contract_slot

delist_date
days_to_delist
annualization_days

underlying_close
future_close

basis_points
basis_pct
annualized_basis_pct
```

`future_close` 是 Source IM daily `close` 的 analysis-friendly rename。V1 不输出 `volume`、`oi` 或其他 pass-through market fields；如果未来真实 diagnostic consumer 需要，必须先更新本 contract。

## 4. Semantic result

Public application result 为：

```text
CSI1000IMBasisHistoryResult
    start_trade_date
    end_trade_date
    underlying_ts_code = "000852.SH"
    observations[]
```

`observations` 是第 3 节定义的 flat records，按产品内 canonical order 排序。成功 result 自身可以回答 query bounds、underlying identity、所有 observation dates 与完整期限结构，不依赖 caller local state 或某个文件路径补充语义。

## 5. Public Python boundary

`market-research` 依赖的是本产品公开的 application request/result boundary：

```text
market-research
    ↓
CSI1000 IM Basis History public application service
    ↓
CSI1000IMBasisHistoryResult
```

Public module 暴露 semantic request/result types、可注入 Source client 的 application service，以及下述 production-ready execution entry。Research 不得导入：

```text
Source or Capture internals
Raw Artifact readers or paths
product-private Preparation
output/... persistence layout
backend-api / FastAPI / HTTP DTO
```

该 public boundary 必须提供由本 Snapshot 产品拥有的 production-ready execution/composition entry。调用方只提供 `CSI1000IMBasisHistoryRequest` 语义请求并接收 `CSI1000IMBasisHistoryResult` 或已分类 application failure；entry 自行完成现有 Snapshot Source boundary 规定的 credential loading、Tushare client 创建与 service composition。Research study-local CLI 不得知道或接收 `TUSHARE_TOKEN`、`TushareApi` 或 Capture implementation。

Production-ready entry 从 product-owned public module 暴露为：

```python
run_csi1000_im_basis_history(
    request: CSI1000IMBasisHistoryRequest,
) -> CSI1000IMBasisHistoryResult
```

不得要求 Research 通过 `market_snapshot.sources` 构造 client，也不得借此建立 generic service container、dependency-injection framework 或跨产品 composition framework。Credential 与 Source-client creation failure 必须在本产品 application boundary 转换为 `CSI1000IMBasisHistoryError`，供 consumer 呈现为 classified application failure。

V1 result 可以完全 request-scoped + in-memory，不要求 persisted final artifact 或 HTTP endpoint。

## 6. Success and failure

成功表示：

```text
query is valid
+ at least one CSI1000 observation date exists
+ each date has one usable underlying close
+ each date has a complete and uniquely slotted active IM universe
+ each active contract has one usable daily close
+ every observation is prepared
+ the complete panel is canonically ordered
```

以下为 semantic failure：

```text
invalid date format or start_trade_date > end_trade_date
Source cannot serve the requested interval
no CSI1000 observation date in the interval
missing or duplicate underlying row
missing, duplicate, unknown or out-of-lifecycle IM daily row
missing, conflicting or malformed contract facts
IM active universe cannot map uniquely to M0/M1/Q1/Q2
required close missing, null, malformed or non-finite
underlying_close == 0
any incomplete observation or partial panel
```

具体 exception classes 属于实现，但必须在 product application boundary 被分类并传递。不得使用 fallback date、previous close、zero fill、contract dropping、partial success 或 fabricated slot 隐藏失败。
