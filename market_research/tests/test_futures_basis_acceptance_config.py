"""Offline acceptance configuration checks, without acquisition or HTML packaging."""

import runpy
import sys
from pathlib import Path

import pytest

from futures_basis_observation_fixtures import Services
from futures_basis_report_acceptance import report_command
from futures_basis_statistics_acceptance import metric_specs
from market_research.descriptive.cases.futures_basis import (
    SLOTS,
    AnalysisRequestError,
    ComparisonRequest,
    DistributionRequest,
    ReportRequest,
    analyze_distribution,
    compare_terms,
    construct_observations,
)
from market_research.descriptive.cases.futures_basis.statistics import METRICS, PAIRS
from market_statistics import IntervalCountSpec, validate_spec

EXPECTED = (
    ("basis_value", (-1000, -500, -100, 0, 100, 500, 1000), "index_points"),
    ("basis_ratio", (-1, -0.1, -0.01, 0, 0.01, 0.1, 1), "decimal_ratio"),
    ("annualized_basis_ratio", (-10, -1, -0.1, 0, 0.1, 1, 10), "decimal_ratio"),
    ("annualized_basis_value", (-1000, -500, -100, 0, 100, 500, 1000), "index_points_per_year"),
)


def test_report_acceptance_command_parses_four_specs_before_io(monkeypatch):
    command = report_command(Path("unused-acceptance-output"))
    namespace = runpy.run_path(command[0])
    validate = ReportRequest.validate
    captured = []

    class Parsed(Exception):
        pass

    def stop_before_io(request):
        validate(request)
        captured.append(request)
        raise Parsed

    monkeypatch.setattr(ReportRequest, "validate", stop_before_io)
    monkeypatch.setattr(sys, "argv", command)
    with pytest.raises(Parsed):
        namespace["main"]()
    (request,) = captured
    assert request.observation.product_code == "IM"
    assert str(request.observation.start_date) == "2024-01-01"
    assert str(request.observation.end_date) == "2026-10-30"
    assert request.quantile.points == (0, 0.25, 0.5, 0.75, 1)
    assert tuple((h.edges, h.unit) for h in request.histograms) == tuple(
        (e, u) for _, e, u in EXPECTED
    )


@pytest.mark.parametrize("metric,edges,unit", EXPECTED)
def test_statistics_acceptance_specs_validate_all_slots_and_pairs(metric, edges, unit):
    assert tuple(m for m, _, _ in EXPECTED) == METRICS
    quantile, histogram = metric_specs(metric)
    assert histogram.edges == edges and histogram.unit == unit
    assert quantile.points == (0, 0.25, 0.5, 0.75, 1)
    validate_spec(quantile)
    validate_spec(histogram)
    services = Services()
    source = construct_observations(services.request, services.prepare())
    start, end = services.request.start_date, services.request.end_date
    for slot in SLOTS:
        result = analyze_distribution(
            source,
            DistributionRequest(f"{metric}-{slot}", slot, metric, start, end, quantile, histogram),
        )
        assert all(m.failure_category is None for m in result.methods)
    for pair in PAIRS:
        result = compare_terms(
            source,
            ComparisonRequest(f"{metric}-{pair}", pair, metric, start, end, quantile, histogram),
        )
        assert all(m.failure_category is None for m in result.left_methods + result.right_methods)


@pytest.mark.parametrize("unit", ("index_points", "decimal_ratio"))
def test_annualized_points_reject_other_metric_units(unit):
    services = Services()
    source = construct_observations(services.request, services.prepare())
    quantile, histogram = metric_specs("annualized_basis_value")
    wrong = IntervalCountSpec(histogram.edges, unit)
    start, end = services.request.start_date, services.request.end_date
    with pytest.raises(AnalysisRequestError):
        analyze_distribution(
            source,
            DistributionRequest(
                "wrong-unit", "M0", "annualized_basis_value", start, end, quantile, wrong
            ),
        )
    with pytest.raises(AnalysisRequestError):
        compare_terms(
            source,
            ComparisonRequest(
                "wrong-unit", ("M0", "M1"), "annualized_basis_value", start, end, quantile, wrong
            ),
        )
