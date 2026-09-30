"""DteCompensationProfile and MoneynessCompensationProfile statistics."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Sequence
from statistics import mean, median
from typing import Any

from .inputs import MOOptionRiskPremiumRequest, decimal_text
from .observations import OutcomeCell

_MEASURES = (
    "entry_premium_proxy",
    "expiry_payoff_proxy",
    "seller_compensation_points",
    "seller_compensation_ratio",
    "annualized_compensation_ratio",
)
_COMPENSATION = (
    "seller_compensation_points",
    "seller_compensation_ratio",
    "annualized_compensation_ratio",
)


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    left = math.floor(position)
    right = math.ceil(position)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def _summarize(
    cells: tuple[OutcomeCell, ...], request: MOOptionRiskPremiumRequest, expiry_count: int
) -> tuple[dict[str, Any], ...]:
    buckets: dict[tuple[int, str, str], list[OutcomeCell]] = defaultdict(list)
    for cell in cells:
        buckets[(cell.target_dte, cell.option_type, cell.moneyness_target)].append(cell)
    summary: list[dict[str, Any]] = []
    for dte in request.dte_targets:
        for kind in ("CALL", "PUT"):
            for target in request.moneyness_targets:
                name = decimal_text(target)
                group = buckets[(dte, kind, name)]
                valid = [cell for cell in group if not cell.exclusion_reasons]
                unique = len({cell.expiry_date for cell in valid})
                reasons = Counter(reason for cell in group for reason in cell.exclusion_reasons)
                record: dict[str, Any] = {
                    "target_dte": dte,
                    "option_type": kind,
                    "moneyness_target": name,
                    "sample_count": len(valid),
                    "unique_expiry_count": unique,
                    "expected_expiry_count": expiry_count,
                    "unique_expiry_coverage_count": unique,
                    "unique_expiry_coverage_ratio": unique / expiry_count,
                    "excluded_cell_count": len(group) - len(valid),
                    "reason_counts": dict(sorted(reasons.items())),
                    "defined_by": ["DteCompensationProfile", "MoneynessCompensationProfile"],
                }
                for field in _MEASURES:
                    values = [getattr(cell, field) for cell in valid]
                    numeric = [value for value in values if value is not None]
                    record[f"{field}_mean"] = mean(numeric) if numeric else None
                    record[f"{field}_median"] = median(numeric) if numeric else None
                    if field in _COMPENSATION:
                        record[f"{field}_min"] = min(numeric) if numeric else None
                        for label, p in (
                            ("p05", 0.05),
                            ("p25", 0.25),
                            ("p50", 0.5),
                            ("p75", 0.75),
                            ("p95", 0.95),
                        ):
                            record[f"{field}_{label}"] = (
                                record[f"{field}_median"]
                                if label == "p50"
                                else _quantile(numeric, p)
                                if numeric
                                else None
                            )
                points = [cell.seller_compensation_points for cell in valid]
                for label, predicate in (
                    ("positive", lambda x: x > 0),
                    ("negative", lambda x: x < 0),
                    ("zero", lambda x: x == 0),
                ):
                    record[f"{label}_frequency"] = (
                        sum(predicate(x) for x in points if x is not None) / len(valid)
                        if valid
                        else None
                    )
                summary.append(record)
    return tuple(summary)
