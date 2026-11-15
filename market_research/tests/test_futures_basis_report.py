"""WP5 scientific linkage, faithful projection and cache-free evidence replay."""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from futures_basis_observation_fixtures import Services, proof
from market_research.descriptive.cases.futures_basis import (
    ReportRequest,
    compose_report,
    construct_observations,
    load_prepared_inputs,
    project_history,
    replay_delivery,
    verify_delivery,
    write_evidence,
)
from market_research.descriptive.cases.futures_basis.evidence import (
    encode,
    scientific_payload,
    seal_delivery,
    write_json,
)
from market_statistics import CalculationFailure, IntervalCountSpec, QuantileSpec


def report(services=None):
    services = services or Services()
    source = construct_observations(services.request, services.prepare())
    request = ReportRequest(
        services.request,
        QuantileSpec([0, 0.5, 1]),
        (
            IntervalCountSpec([-100, 0, 100], "index_points"),
            IntervalCountSpec([-1, 0, 1], "decimal_ratio"),
            IntervalCountSpec([-10, 0, 10], "decimal_ratio"),
        ),
    )
    return compose_report(source, request)


def package(tmp_path: Path, result):
    write_evidence(
        result,
        tmp_path,
        runtime=dict(
            revision="synthetic",
            dirty=False,
            python="3.13",
            node="synthetic",
            packages={"numpy": "synthetic"},
            frontend_packages={"react": "synthetic", "plotly.js": "synthetic"},
            locks={},
        ),
    )
    reader = (tmp_path / "report-data.json").read_text(encoding="utf-8")
    (tmp_path / "report.html").write_text(
        '<script id="report-data" type="application/json">' + reader + "</script>",
        encoding="utf-8",
    )
    (tmp_path / "REPRODUCE.md").write_text("test reproduction", encoding="utf-8")
    seal_delivery(tmp_path, result.status, result.source.prepared.input_fingerprint)


def test_composition_preserves_wp4_original_objects_and_order():
    result = report()
    assert len(result.distributions) == 12 and len(result.comparisons) == 18
    assert [r.slot for r in result.persistence] == ["M0", "M1", "Q1", "Q2"]
    for distribution in result.distributions:
        assert distribution.source is result.source
        assert distribution.request.quantile is result.request.quantile
        assert all(
            any(r is original for original in result.source.slot_days) for r in distribution.binding
        )
    science, views, associations, reader = scientific_payload(result)
    assert len(science["distributions"]) == 12
    assert len(views["history"]) == 3 and len(views["histograms"]) == 24
    assert reader["distributions"][0]["methods"] == encode(result.distributions[0].methods)
    assert len(associations["basis_value"]["points"]) == len(result.source.slot_days)
    assert "(F_close − S_close) / S_close" in reader["formulas"][1]


def test_segments_events_and_expiry_null_keep_source_values():
    result = report()
    view, associations = project_history(result.source, "annualized_basis_ratio")
    assert [b["label"] for b in view["layers"]] == ["M0", "M1", "Q1", "Q2"]
    marks = view["layers"][0]["layer"]["data"]
    assert marks[0]["y"] is None and marks[1]["y"] is not None
    assert marks[0]["segment_id"] != marks[1]["segment_id"]
    assert "expiry_day" in [d["value"] for d in marks[0]["details"]]
    assert len(view["events"]) == len(result.source.transitions.transitions)
    assert len(associations["events"]) == len(view["events"])
    for binding in view["layers"]:
        rows = [r for r in result.source.slot_days if r.slot == binding["label"]]
        assert [m["y"] for m in binding["layer"]["data"]] == [
            r.outcome("annualized_basis_ratio").value for r in rows
        ]


def test_partial_index_missing_transition_is_retained_and_replays(tmp_path):
    services = Services()
    services.index = replace(
        services.index, records=services.index.records[:1], coverage=proof(2, 1)
    )
    result = report(services)
    view, _ = project_history(result.source, "basis_value")
    assert len(view["events"]) > 0
    assert all(b["layer"]["data"][1]["y"] is None for b in view["layers"])
    package(tmp_path, result)
    with (
        patch(
            "data_lake.providers.tushare.TushareExecutor.prepare",
            side_effect=AssertionError("Source forbidden"),
        ),
        patch("sqlite3.connect", side_effect=AssertionError("Cache forbidden")),
    ):
        assert replay_delivery(tmp_path)["status"] == "PASS"


def test_empty_samples_never_compute_and_all_null_report(tmp_path):
    services = Services()
    services.futures = replace(services.futures, records=())
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
        side_effect=AssertionError("Empty sample"),
    ):
        result = report(services)
    assert all(
        m.failure_category == "no_eligible_sample" for r in result.distributions for m in r.methods
    )
    package(tmp_path, result)
    assert replay_delivery(tmp_path)["status"] == "PASS"
    assert scientific_payload(result)[1]["histograms"] == {}


def test_statistics_failure_retained_partial_not_drawn_as_success():
    with patch(
        "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
        side_effect=CalculationFailure("mean", "synthetic failure"),
    ):
        result = report()
    assert result.status == "partial"
    science, views, _, reader = scientific_payload(result)
    assert all(
        m["failure_category"] == "CalculationFailure"
        for r in science["distributions"]
        for m in r["methods"]
    )
    assert views["histograms"] == {} and reader["status"] == "partial"


def test_evidence_cache_free_replay_and_corruption_rejection(tmp_path):
    result = report()
    package(tmp_path, result)
    with patch("sqlite3.connect", side_effect=AssertionError("Cache forbidden")):
        assert (
            replay_delivery(tmp_path)["input_fingerprint"]
            == result.source.prepared.input_fingerprint
        )
    (tmp_path / "views.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        verify_delivery(tmp_path)


def test_resealed_scientific_mutation_cannot_replay(tmp_path):
    result = report()
    package(tmp_path, result)
    data = json.loads((tmp_path / "evidence.json").read_bytes())
    data["science"]["distributions"][0]["methods"][0]["result"]["value"] = -987.0
    write_json(tmp_path / "evidence.json", data)
    seal_delivery(tmp_path, result.status, result.source.prepared.input_fingerprint)
    with pytest.raises(ValueError, match="mismatch"):
        replay_delivery(tmp_path)


def test_canonical_reader_rejects_altered_profile_and_request(tmp_path):
    result = report()
    p = tmp_path / "inputs.canonical.json"
    p.write_bytes(result.source.prepared.canonical_bytes)
    assert load_prepared_inputs(p, result.request.observation).canonical_bytes == p.read_bytes()
    with pytest.raises(ValueError):
        load_prepared_inputs(p, replace(result.request.observation, product_code="IF"))
    data = json.loads(p.read_bytes())
    data["profile"] = "unknown"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="profile"):
        load_prepared_inputs(p, result.request.observation)


def test_manifest_rejects_traversal_symlink_and_extra_files(tmp_path):
    result = report()
    package(tmp_path, result)
    (tmp_path / "extra").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="Unexpected"):
        verify_delivery(tmp_path)
    (tmp_path / "extra").unlink()
    (tmp_path / "report.html").unlink()
    try:
        (tmp_path / "report.html").symlink_to(tmp_path / "REPRODUCE.md")
    except OSError as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")
    with pytest.raises(ValueError, match="Unsafe"):
        verify_delivery(tmp_path)


@pytest.mark.diagnostic
def test_operator_retained_input_failure_sealed_without_success(tmp_path):
    import runpy
    import sys

    root = Path(__file__).resolve().parents[2]
    namespace = runpy.run_path(str(root / "market_research/scripts/futures_basis_report.py"))
    output = tmp_path / "delivery"
    command = [
        "futures_basis_report.py",
        "--product",
        "IM",
        "--start",
        "2024-10-18",
        "--end",
        "2024-10-21",
        "--quantile-points",
        "[0,0.5,1]",
        "--basis-value-edges",
        "[-100,0,100]",
        "--basis-ratio-edges",
        "[-1,0,1]",
        "--annualized-basis-ratio-edges",
        "[-10,0,10]",
        "--inputs",
        str(tmp_path / "absent.json"),
        "--output",
        str(output),
    ]
    with patch.object(sys, "argv", command):
        assert namespace["main"]() == 1
    manifest = verify_delivery(output)
    assert manifest["status"] == "failed" and manifest["input_fingerprint"] is None
    assert not (output / "report.html").exists()
    failure = json.loads((output / "failure.json").read_bytes())
    assert failure["stage"] == "input_preparation"
    assert failure["dependency"] == "canonical_inputs"
    with pytest.raises(ValueError, match="no successful inputs"):
        replay_delivery(output)


def test_resealed_html_cannot_disagree_with_evidence(tmp_path):
    result = report()
    package(tmp_path, result)
    (tmp_path / "report.html").write_text(
        '<script id="report-data" type="application/json">{}</script>'
    )
    seal_delivery(tmp_path, result.status, result.source.prepared.input_fingerprint)
    with pytest.raises(ValueError, match="HTML reader payload"):
        verify_delivery(tmp_path)
