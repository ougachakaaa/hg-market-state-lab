"""Offline full-history review exercises public validation without provider access."""

import json
import sys
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

import segmentation_full_history as full
import segmentation_full_history_live as live
from data_lake.providers.tushare import TushareExecutor
from market_research.descriptive.cases.price_segmentation import InputPreparationError
from segmentation_synthetic_fixture import write_evidence


def test_offline_replay_and_corruption(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = json.loads(write_evidence(tmp_path / "synthetic.json").read_text(encoding="utf-8"))
    source = report["scenarios"][0]
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
        page = (tmp_path / "review" / "index.html").read_text(encoding="utf-8")
        assert page.count("<svg ") == 24
        assert 'stroke-width="0.7"' in page and 'stroke-width="1.2"' in page
        assert 'r="1.5"' in page and "Light experimental" in page
        assert "<script" not in page and "https://" not in page and "http://" not in page
        corrupt = deepcopy(data)
        corrupt["input_evidence"][0]["request"]["exchange"] = "SZSE"
        evidence.write_text(json.dumps(corrupt), encoding="utf-8")
        with pytest.raises(AssertionError, match="request mismatch"):
            full.replay(evidence)
        corrupt = deepcopy(data)
        corrupt["input_evidence"][0]["final_export"]["scope"].append("SZSE")
        evidence.write_text(json.dumps(corrupt), encoding="utf-8")
        with pytest.raises(AssertionError, match="Calendar scope"):
            full.replay(evidence)
        corrupt = deepcopy(data)
        corrupt["input_evidence"][0]["ensure_result"]["requested_units"] += 1
        evidence.write_text(json.dumps(corrupt), encoding="utf-8")
        with pytest.raises(InputPreparationError, match="Ensure accounting mismatch"):
            full.replay(evidence)
        data["input_evidence"][1]["final_export"]["records"][0]["close"] += 1
        evidence.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(AssertionError, match="Fingerprint"):
            full.replay(evidence)


def test_live_budget_stops_before_excess_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    @contextmanager
    def isolated(_path: Path):
        yield {}

    calls: list[str] = []

    def provider_call(_self: object, endpoint: str, **_kwargs: object) -> None:
        calls.append(endpoint)

    def prepare(_request: object) -> None:
        executor = object.__new__(TushareExecutor)
        executor.call("trade_cal")
        executor.call("trade_cal")

    monkeypatch.setattr(
        sys, "argv", ["runner", "--live", "--output", str(tmp_path), "--max-calls", "1"]
    )
    monkeypatch.setattr(live, "isolated_storage", isolated)
    monkeypatch.setattr(live, "prepare_inputs", prepare)
    monkeypatch.setattr(TushareExecutor, "call", provider_call)
    assert live.main() == 1
    report = json.loads((tmp_path / "acquisition_status.json").read_text(encoding="utf-8"))
    assert report["verdict"] == "BLOCKED"
    assert report["failure"]["category"] == "provider_budget_exceeded"
    assert report["provider_calls"] == {"trade_cal": 1}
    assert calls == ["trade_cal"]
    assert not (tmp_path / "input_evidence.json").exists()


def test_live_requires_explicit_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "not-created"
    monkeypatch.setattr(sys, "argv", ["runner", "--output", str(output)])
    with patch.object(TushareExecutor, "call", side_effect=AssertionError("provider access")):
        with pytest.raises(SystemExit):
            live.main()
    assert not output.exists()
