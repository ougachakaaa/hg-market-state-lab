"""Check the curated result package without requiring local market data or Runs."""

import hashlib
import json
from pathlib import Path

PACKAGE = (Path(__file__).resolve().parents[1] / "tasks" / "historical_return_observation"
           / "results" / "2026_four_index_returns")


def test_preserved_research_outputs_and_scope():
    hashes = {
        "results.json": "bc7058488cdc1bf9086f2f8418da191441cb9c8075fe92c4d0b6e02a08cecb7d",
        "evidence/evidence.json":
            "ae8f1ec98cd2b4f32873c497f360dd0c91302e584777c34a318aeb085b9ba898",
        "evidence/cache_audit.json":
            "8a4c6e9a094b46774989e2142cad9d518e004fa27932e408080983c6dfc42b7e",
    }
    for name, expected in hashes.items():
        assert hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() == expected
    scope = json.loads((PACKAGE / "scope.json").read_bytes())
    result = json.loads((PACKAGE / "results.json").read_bytes())
    assert scope["schema_version"] == 1
    assert [(j["index"], j["horizon"]) for j in result["jobs"]] == [
        (subject, horizon) for subject in scope["subjects"]
        for horizon in scope["observation"]["horizons"]
    ]
    assert len(result["jobs"]) == 16 and result["analyses_verified"] == 32
    points = scope["analysis"][0]["points"]
    edges = scope["analysis"][1]["edges"]
    for job in result["jobs"]:
        assert [p for p, _ in job["quantiles"]["points_and_values"]] == points
        bins = job["interval_count"]["bins"]
        assert [bins[0]["left"], *(b["right"] for b in bins)] == edges
        assert job["sample_count"] == job["eligible"] + job["unavailable"] + job["excluded"]
