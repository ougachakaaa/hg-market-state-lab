"""Bounded R01-A composition; all numerical results come from WP4."""

from dataclasses import dataclass
from typing import Any

from market_statistics import IntervalCountSpec, QuantileSpec, validate_spec

from .inputs import FuturesBasisRequest
from .models import SLOTS
from .observations import FuturesBasisResult
from .statistics import (
    METRICS,
    PAIRS,
    ComparisonRequest,
    ComparisonResult,
    DiscountSummary,
    DistributionRequest,
    DistributionResult,
    analyze_distribution,
    compare_terms,
    discount_runs,
)
from .validation import validate_request


@dataclass(frozen=True, slots=True)
class ReportRequest:
    observation: FuturesBasisRequest
    quantile: QuantileSpec
    histograms: tuple[IntervalCountSpec, ...]

    def validate(self) -> None:
        validate_request(self.observation)
        if type(self.quantile) is not QuantileSpec:
            raise ValueError("Explicit QuantileSpec required")
        validate_spec(self.quantile)
        if len(self.histograms) != 3:
            raise ValueError("Three explicit histogram specifications required")
        for metric, spec in zip(METRICS, self.histograms, strict=True):
            if type(spec) is not IntervalCountSpec:
                raise ValueError("Explicit IntervalCountSpec required")
            validate_spec(spec)
            if spec.unit != ("index_points" if metric == "basis_value" else "decimal_ratio"):
                raise ValueError("Histogram unit differs from metric")


@dataclass(frozen=True, slots=True)
class ReportResult:
    request: ReportRequest
    source: FuturesBasisResult
    distributions: tuple[DistributionResult, ...]
    comparisons: tuple[ComparisonResult, ...]
    persistence: tuple[DiscountSummary, ...]

    @property
    def status(self) -> str:
        methods = [m for d in self.distributions for m in d.methods] + [
            m for c in self.comparisons for m in c.left_methods + c.right_methods
        ]
        return (
            "partial"
            if any(m.failure_category not in (None, "no_eligible_sample") for m in methods)
            else "complete"
        )


def compose_report(source: FuturesBasisResult, request: ReportRequest) -> ReportResult:
    request.validate()
    if source.prepared.request != request.observation:
        raise ValueError("Report request does not match observations")
    start, end = request.observation.start_date, request.observation.end_date
    distributions, comparisons = [], []
    for metric, histogram in zip(METRICS, request.histograms, strict=True):
        for slot in SLOTS:
            distributions.append(
                analyze_distribution(
                    source,
                    DistributionRequest(
                        f"{metric}-{slot}",
                        slot,
                        metric,
                        start,
                        end,
                        request.quantile,
                        histogram,
                    ),
                )
            )
        for pair in PAIRS:
            comparisons.append(
                compare_terms(
                    source,
                    ComparisonRequest(
                        f"{metric}-{pair[0]}-{pair[1]}",
                        pair,
                        metric,
                        start,
                        end,
                        request.quantile,
                        histogram,
                    ),
                )
            )
    return ReportResult(
        request,
        source,
        tuple(distributions),
        tuple(comparisons),
        tuple(discount_runs(source, slot, start, end) for slot in SLOTS),
    )


def project_history(
    source: FuturesBasisResult, metric: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Supply generic segments/events; never make the renderer discover financial rules."""
    if metric not in METRICS:
        raise ValueError("Unknown report metric")
    unit = "index_points" if metric == "basis_value" else "decimal_ratio"
    associations: dict[str, Any] = {"points": {}, "events": {}}
    bindings = []
    for slot in SLOTS:
        marks = []
        segment = 0
        previous = None
        for row in (r for r in source.slot_days if r.slot == slot):
            outcome = row.outcome(metric)
            if (
                previous is None
                or previous.contract_code != row.contract_code
                or previous.outcome(metric).status != "eligible"
                or outcome.status != "eligible"
            ):
                segment += 1
            obs = row.observation
            ref = f"{metric}/{slot}/{row.trade_date.isoformat()}"
            details = [
                ("交易日期", row.trade_date.isoformat()),
                ("Slot", slot),
                ("实际合约", row.contract_code or "无活跃合约"),
                ("Metric", metric),
                ("单位", unit),
                ("结果", repr(outcome.value) if outcome.value is not None else outcome.status),
                ("原因", outcome.reason or ""),
                ("期货 Close", repr(obs.futures_close) if obs else "不可用"),
                ("指数 Close", repr(obs.underlying_close) if obs else "不可用"),
                ("DTE", str(obs.days_to_expiry) if obs else "不适用"),
                ("基差状态", obs.basis_state or outcome.status if obs else outcome.status),
                ("Source Association", ref),
            ]
            marks.append(
                dict(
                    x=row.trade_date.isoformat(),
                    y=outcome.value,
                    segment_id=f"{slot}-{segment}",
                    details=[dict(label=k, value=v) for k, v in details],
                )
            )
            associations["points"][ref] = dict(
                slot_day=row.identity,
                contract_day=obs.identity if obs else None,
                futures_source=obs.futures_source if obs else None,
                underlying_source=obs.underlying_source if obs else None,
            )
            previous = row
        bindings.append(
            dict(
                id=slot,
                label=slot,
                x_axis="date",
                y_axis="value",
                layer=dict(
                    type="line",
                    version=2,
                    x=dict(kind="date", unit="date"),
                    y=dict(kind="number", unit=unit),
                    data=marks,
                ),
            )
        )
    events = []
    for i, transition in enumerate(source.transitions.transitions):
        event_id = f"transition-{i}"
        events.append(
            dict(
                id=event_id,
                x_axis="date",
                x=transition.trade_date.isoformat(),
                label=(
                    f"{transition.slot}: {transition.previous_contract_code}"
                    f" → {transition.contract_code}"
                ),
                details=[
                    dict(label="含义", value="观测到的角色映射变化；不代表交易或移仓收益"),
                    dict(label="Source Association", value=event_id),
                ],
            )
        )
        associations["events"][event_id] = transition
    return dict(
        version=2,
        axes=[
            dict(id="date", orientation="x", coordinate=dict(kind="date", unit="date")),
            dict(id="value", orientation="y", coordinate=dict(kind="number", unit=unit)),
        ],
        layers=bindings,
        events=events,
        layout=dict(title=f"历史基差 · {metric} · {unit}"),
        presentation=dict(show_legend=True, zoom=True, pan=True, reset=True),
    ), associations


LIMITATIONS = [
    "这是同日 Close 基差的描述性研究，不是公允价值、预测、交易信号或收益回测。",
    "Slot 是每日相对期限角色；真实合约切换使图线断开，但不必终止 Slot 的贴水区间。",
    "期限比较仅使用两侧共同有效交易日，未计算 Calendar Spread。",
    "截断片段的交易日数只是已观测持续时间下界，不是完整持续期或持续期估计。",
    "每日观测及 Slots 共享日期和指数价格，不能视作相互独立的抽样。",
    "缺失不补值、不插值；年化在到期日不适用。不同来源的覆盖单位分别报告。",
    "年化值为 365 自然日对数率，不是有效年收益；临近到期时对 DTE 很敏感。",
    "若使用短窗口，仅用于端到端验收，不能据此推断长期分布、市场状态或预测能力。",
    "输入摘要证明保留内容的一致性，不保证来源真实性、最新性或同一获取时刻。",
]
