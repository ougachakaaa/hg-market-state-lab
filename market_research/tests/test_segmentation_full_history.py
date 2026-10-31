"""Offline full-history review exercises public validation without provider access."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import segmentation_full_history as full
import segmentation_review
from data_lake.providers.tushare import TushareExecutor


def test_offline_replay_and_corruption(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = json.loads(segmentation_review.EVIDENCE.read_text(encoding="utf-8"))["scenarios"][1]
    data = {key: source[key] for key in ("request", "input_fingerprint", "input_evidence")}
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(full, "START_DATE", "2024-01-08")
    monkeypatch.setattr(full, "END_DATE", "2024-02-29")
    with patch.object(TushareExecutor, "call", side_effect=AssertionError("provider access")):
        full.generate(evidence, tmp_path / "review")
        first = (tmp_path / "review" / "result_evidence.json").read_bytes()
        full.generate(evidence, tmp_path / "review")
        assert first == (tmp_path / "review" / "result_evidence.json").read_bytes()
        assert (tmp_path / "review" / "index.html").read_text(encoding="utf-8").count("<svg ") == 8
        data["input_evidence"][1]["final_export"]["records"][0]["close"] += 1
        evidence.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(AssertionError, match="Fingerprint"):
            full.replay(evidence)
