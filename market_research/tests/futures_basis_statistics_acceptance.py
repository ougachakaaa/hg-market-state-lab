"""Offline WP4 acceptance from retained WP3 caches, with no Source calls.

Run from root: poetry run python market_research/tests/futures_basis_statistics_acceptance.py
  --wp3 /absolute/retained/wp3 --output /absolute/new/evidence
This is test infrastructure, not a Research persistence or public loading API.
"""

import argparse
import hashlib
import json
import math
import shutil
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

from futures_basis_live_acceptance import REQUEST, isolated_storage, public
from market_research.descriptive.cases.futures_basis import (
    SLOTS,
    ComparisonRequest,
    DistributionRequest,
    analyze_distribution,
    compare_terms,
    construct_observations,
    discount_runs,
    prepare_inputs,
)
from market_research.descriptive.cases.futures_basis.statistics import METRICS, PAIRS
from market_statistics import IntervalCountSpec, MeanResult, QuantileResult, QuantileSpec


def run(wp3: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    canonical = (wp3 / "inputs.canonical.json").read_bytes()
    fingerprint = hashlib.sha256(canonical).hexdigest()
    # Copy only retained dataset files into a new isolated test cache. Source is forbidden.
    with isolated_storage(output / "dataset-cache") as audit:
        for path in (wp3 / "dataset-cache").glob("*.sqlite3"):
            shutil.copyfile(path, output / "dataset-cache" / path.name)
        with patch(
            "data_lake.providers.tushare.TushareExecutor.prepare",
            side_effect=AssertionError("No source calls"),
        ):
            prepared = prepare_inputs(REQUEST)
        assert prepared.canonical_bytes == canonical
        assert prepared.input_fingerprint == fingerprint
        source = construct_observations(REQUEST, prepared)
    distributions, comparisons = [], []
    edges: dict[str, list[float]] = {
        "basis_value": [-1000, -500, -100, 0, 100, 500, 1000],
        "basis_ratio": [-1, -0.1, -0.01, 0, 0.01, 0.1, 1],
        "annualized_basis_ratio": [-10, -1, -0.1, 0, 0.1, 1, 10],
    }
    for metric in METRICS:
        unit = "index_points" if metric == "basis_value" else "decimal_ratio"
        quantile, histogram = (
            QuantileSpec([0, 0.25, 0.5, 0.75, 1]),
            IntervalCountSpec(edges[metric], unit),
        )
        for slot in SLOTS:
            req = DistributionRequest(
                f"{metric}-{slot}",
                slot,
                metric,
                REQUEST.start_date,
                REQUEST.end_date,
                quantile,
                histogram,
            )
            result = analyze_distribution(source, req)
            assert all(m.result is not None for m in result.methods)
            distributions.append(result)
        for pair in PAIRS:
            req_pair = ComparisonRequest(
                f"{metric}-{pair[0]}-{pair[1]}",
                pair,
                metric,
                REQUEST.start_date,
                REQUEST.end_date,
                quantile,
                histogram,
            )
            result_pair = compare_terms(source, req_pair)
            expected = tuple(
                d
                for d in prepared.candidate_dates
                if all(
                    any(
                        r.slot == slot
                        and r.trade_date == d
                        and r.outcome(metric).status == "eligible"
                        for r in source.slot_days
                    )
                    for slot in pair
                )
            )
            assert result_pair.common_dates == expected
            assert all(
                m.result is not None for m in result_pair.left_methods + result_pair.right_methods
            )
            comparisons.append(result_pair)
    chosen = distributions[0]
    values: list[float] = []
    for row in chosen.binding:
        scalar = row.outcome(chosen.request.metric).value
        assert scalar is not None
        values.append(scalar)
    with localcontext() as ctx:
        ctx.prec = 60
        independent_mean = float(
            sum((Decimal.from_float(v) for v in values), Decimal(0)) / Decimal(len(values))
        )
    independent_quantiles = []
    ordered = sorted(values)
    for p in chosen.request.quantile.points:
        h = (len(ordered) - 1) * p
        j = int(h)
        value = (
            ordered[j]
            if j == len(ordered) - 1
            else ordered[j] + (h - j) * (ordered[j + 1] - ordered[j])
        )
        independent_quantiles.append((p, value))
    mean_result, quantile_result = chosen.methods[0].result, chosen.methods[1].result
    assert isinstance(mean_result, MeanResult) and isinstance(quantile_result, QuantileResult)
    assert math.isclose(mean_result.value, independent_mean, abs_tol=1e-12)
    assert quantile_result.points_and_values == tuple(independent_quantiles)
    runs = [discount_runs(source, slot, REQUEST.start_date, REQUEST.end_date) for slot in SLOTS]
    report = dict(
        status="PASS",
        input_fingerprint=fingerprint,
        request=public(REQUEST),
        isolation=audit,
        distribution_count=len(distributions),
        comparison_count=len(comparisons),
        independent_mean=independent_mean,
        independent_quantiles=independent_quantiles,
        common_date_sets=[
            dict(analysis_id=r.request.analysis_id, dates=public(r.common_dates))
            for r in comparisons
        ],
        populations=[
            dict(
                analysis_id=r.request.analysis_id,
                candidate=len(r.candidates),
                eligible=len(r.binding),
                mean=public(r.methods[0].result),
            )
            for r in distributions
        ],
        runs=[
            dict(
                slot=r.slot,
                complete=len(r.complete),
                censored=[x.observed_trading_sessions for x in r.censored],
            )
            for r in runs
        ],
    )
    # One shared source plus method/binding evidence, avoiding repeated serialized input trees.
    evidence = dict(
        source=public(source),
        distributions=[
            public({k: getattr(r, k) for k in ("request", "candidates", "binding", "methods")})
            for r in distributions
        ],
        comparisons=[
            public(
                {
                    k: getattr(r, k)
                    for k in (
                        "request",
                        "candidates",
                        "binding",
                        "dropped",
                        "left_methods",
                        "right_methods",
                    )
                }
            )
            for r in comparisons
        ],
        runs=[
            public(
                {
                    k: getattr(r, k)
                    for k in ("slot", "start_date", "end_date", "complete", "censored")
                }
            )
            for r in runs
        ],
    )
    for name, document in (("acceptance", report), ("results", evidence)):
        (output / f"{name}.json").write_text(
            json.dumps(document, indent=2, allow_nan=False), encoding="utf-8"
        )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wp3", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.wp3, args.output)))
