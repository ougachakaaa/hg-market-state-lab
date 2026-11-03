"""Offline review validates and replays the retained public facts."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import segmentation_review as review
from segmentation_synthetic_fixture import write_evidence


def test_replay_and_repeat_without_io(tmp_path: Path) -> None:
    evidence = write_evidence(tmp_path / "synthetic.json")
    epsilons = [0.005, 0.01, 0.02, 0.03]
    original = review.find_pips
    with patch.object(review, "find_pips", wraps=original) as pip:
        review.generate(evidence, tmp_path / "one", epsilons)
        assert [call.kwargs["epsilon"] for call in pip.call_args_list] == epsilons
    review.generate(evidence, tmp_path / "two", epsilons)
    for name in ("index.html", "comparison.csv", "README.md"):
        assert (tmp_path / "one" / name).read_bytes() == (tmp_path / "two" / name).read_bytes()
    page = (tmp_path / "one" / "index.html").read_text(encoding="utf-8")
    assert page.count("<svg ") == 4
    assert "<script" not in page and "http://" not in page and "https://" not in page
    facts, results = review.review(evidence, epsilons)
    assert all(r["input_fingerprint"] == facts["fingerprint"] for r in results)
    assert len({r["indices"] for r in results}) > 1
    assert results[1]["segment_count"] > 1
    for r in results:
        spans = list(zip(r["indices"], r["indices"][1:], strict=False))
        assert r["average_duration"] == sum(b - a for a, b in spans) / len(spans)
        assert r["up_count"] + r["down_count"] + r["flat_count"] == len(spans)


def test_corrupted_facts_and_g4_result_fail(tmp_path: Path) -> None:
    evidence = write_evidence(tmp_path / "synthetic.json")
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["scenarios"][0]["input_evidence"][1]["final_export"]["records"][0]["close"] += 1
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint"):
        review.review(path, [0.01])
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["scenarios"][0]["diagnostics"]["segment_count"] += 1
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="G4 replay"):
        review.review(path, [0.02])
