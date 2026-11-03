"""Check the retained historical research scope without local market data."""

import json
from pathlib import Path

PACKAGE = (Path(__file__).resolve().parents[1] / "tasks" / "historical_return_observation"
           / "results" / "2026_four_index_returns")


def test_retained_research_scope():
    scope = json.loads((PACKAGE / "scope.json").read_bytes())
    assert scope["schema_version"] == 1
    assert len(scope["subjects"]) == 4
    assert scope["observation"]["horizons"] == [1, 3, 5, 10]
    assert "16 Jobs and 32 analyses succeeded" in (PACKAGE / "REPORT.md").read_text()
