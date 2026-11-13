"""The committed public demo fixture is deterministic synthetic producer output."""

import copy
import json
import math
import runpy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "market_research/scripts/futures_basis_demo_fixture.py"
FIXTURE = ROOT / "ui_web/src/demo/futures_basis/report.v1.json"


@pytest.fixture(scope="module")
def module() -> dict[str, Any]:
    return runpy.run_path(str(SCRIPT))


@pytest.fixture(scope="module")
def payload() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_committed_fixture_is_a_deterministic_regeneration(module: dict[str, Any]) -> None:
    assert FIXTURE.exists()
    committed = FIXTURE.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    module["assert_fixture_matches"](json.loads(committed), json.loads(module["fixture_bytes"]()))
    assert (
        json.dumps(json.loads(committed), ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode() == committed
    assert len(committed) < 1_000_000


def test_fixture_is_labelled_synthetic_without_runtime_metadata(
    payload: dict[str, Any],
) -> None:
    assert payload["fixture_profile"] == "futures_basis_demo_fixture_v1"
    assert payload["classification"] == "synthetic"
    assert payload["report_profile"] == "futures_basis_report_evidence_v1"
    assert payload["generated_by"] == "market_research/scripts/futures_basis_demo_fixture.py"
    assert payload["disclosure"]["label"] == "Synthetic Demo"
    assert "Synthetic Demo" in payload["disclosure"]["notice"]
    assert "no Tushare" in payload["disclosure"]["data_source"]
    assert "runtime" not in payload["report"]
    assert "Tushare" not in json.dumps(payload["report"], ensure_ascii=False)


def test_report_is_producer_output_except_the_synthetic_source_label(
    module: dict[str, Any], payload: dict[str, Any]
) -> None:
    report = payload["report"]
    producer = module["producer_reader"]()
    assert report["sources"] == module["SYNTHETIC_SOURCES"]
    producer["sources"] = report["sources"]
    module["assert_fixture_matches"]({"report": report}, {"report": producer})


def test_fixture_covers_all_reader_sections(payload: dict[str, Any]) -> None:
    report = payload["report"]
    assert report["profile"] == "futures_basis_report_evidence_v1"
    assert report["status"] == "complete"
    assert report["request"]["observation"] == {
        "case": "futures_basis_v1",
        "product_code": "IM",
        "start_date": "2024-09-02",
        "end_date": "2024-10-31",
    }
    assert len(report["candidate_dates"]) == 44
    assert all(coverage["complete"] for coverage in report["coverage"].values())
    assert len(report["distributions"]) == 12
    assert len(report["comparisons"]) == 18
    assert len(report["persistence"]) == 4
    assert set(report["views"]["history"]) == {
        "basis_value",
        "basis_ratio",
        "annualized_basis_ratio",
    }
    assert len(report["views"]["histograms"]) == 24
    for metric, view in report["views"]["history"].items():
        assert view["version"] == 2
        assert len(view["layers"]) == 4
        assert all(
            len(binding["layer"]["data"]) == len(report["candidate_dates"])
            for binding in view["layers"]
        )
        assert view["events"], metric
    nulls = [
        mark
        for view in report["views"]["history"].values()
        for binding in view["layers"]
        for mark in binding["layer"]["data"]
        if mark["y"] is None
    ]
    assert len(nulls) == 2
    assert all(
        mark["details"]
        for view in report["views"]["history"].values()
        for binding in view["layers"]
        for mark in binding["layer"]["data"]
    )
    assert any(
        summary["complete"] for summary in report["persistence"] for _run in summary["complete"]
    )
    assert any(summary["censored"] for summary in report["persistence"])


def test_fixture_contains_no_credentials_or_local_paths() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    for pattern in (
        "C:\\\\",
        "/home/",
        "/Users/",
        "AppData",
        "file://",
        "TUSHARE_TOKEN",
        "LAB_AUTH",
        "password",
        "secret",
        "Authorization",
        "Bearer",
        "we-architects",
        "192.168.",
        "127.0.0.1",
    ):
        assert pattern not in raw, pattern


@pytest.mark.parametrize("change", ["large_ulp", "detail", "date", "fingerprint", "statistic"])
def test_fixture_comparison_rejects_real_drift(module: dict[str, Any], change: str) -> None:
    expected = module["build_fixture"]()
    altered = copy.deepcopy(expected)
    point = altered["report"]["views"]["history"]["annualized_basis_ratio"]["layers"][1]["layer"][
        "data"
    ][36]
    if change == "large_ulp":
        point["y"] += 8 * math.ulp(point["y"])
        point["details"][5]["value"] = repr(point["y"])
    elif change == "detail":
        point["details"][5]["value"] = "0"
    elif change == "date":
        point["x"] = "2024-10-23"
    elif change == "fingerprint":
        altered["report"]["fingerprint"] = "0" * 64
    else:
        altered["report"]["distributions"][0]["changed"] = True
    with pytest.raises(AssertionError):
        module["assert_fixture_matches"](altered, expected)
